#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import html
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_JSON = ROOT / "data/processed/craigslist_job_signals.json"
DEFAULT_OUTPUT_JSON = ROOT / "data/processed/craigslist_company_research.json"
DEFAULT_CONFIG_JSON = ROOT / "config/craigslist_job_signal_config.json"
DEFAULT_FEEDBACK_JSON = ROOT / "data/processed/craigslist_research_feedback.json"

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+?1[\s.\-]?)?(?:\(?\d{3}\)?[\s.\-]?)\d{3}[\s.\-]?\d{4}")
SCRIPT_LD_JSON_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
WHITESPACE_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[a-z0-9]+")
CONTACT_LINK_RE = re.compile(r"(?:contact|connect|inquire|inquiry|get-in-touch)", re.I)
ABOUT_LINK_RE = re.compile(r"(?:about|company|team|story|who-we-are)", re.I)
SERVICE_LINK_RE = re.compile(r"(?:service|services|solutions|what-we-do|capabilities)", re.I)
BAD_HOST_HINTS = (
    "craigslist.org",
    "facebook.com",
    "linkedin.com",
    "instagram.com",
    "x.com",
    "twitter.com",
    "youtube.com",
    "yellowpages.com",
    "yelp.com",
    "mapquest.com",
    "angi.com",
    "angieslist.com",
    "bbb.org",
    "indeed.com",
    "ziprecruiter.com",
    "glassdoor.com",
    "zoominfo.com",
    "manta.com",
)
STOPWORDS = {
    "the",
    "and",
    "for",
    "inc",
    "llc",
    "co",
    "corp",
    "corporation",
    "company",
    "services",
    "service",
    "solutions",
    "group",
    "of",
    "at",
    "a",
    "an",
    "in",
    "to",
    "heating",
    "cooling",
}


@dataclass
class SearchCandidate:
    title: str
    url: str
    snippet: str
    provider: str
    query: str
    rank: int
    score: float = 0.0
    score_reasons: List[str] | None = None


@dataclass
class PageSnapshot:
    url: str
    final_url: str
    title: str
    meta_description: str
    text: str
    emails: List[str]
    phones: List[str]
    links: List[Tuple[str, str]]
    jsonld: List[Any]
    contact_links: List[str]
    about_links: List[str]
    service_links: List[str]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._in_title = False
        self._current_href: str | None = None
        self._current_link_parts: List[str] = []
        self.title_parts: List[str] = []
        self.text_parts: List[str] = []
        self.links: List[Tuple[str, str]] = []
        self.meta_description = ""

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                content = clean_text(attrs_dict.get("content", ""))
                if content and not self.meta_description:
                    self.meta_description = content
        if tag == "a":
            self._current_href = attrs_dict.get("href") or ""
            self._current_link_parts = []
        if tag in {"p", "div", "section", "article", "br", "li", "h1", "h2", "h3", "h4"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            if self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
        if tag == "a":
            href = clean_text(self._current_href or "")
            text = clean_text(" ".join(self._current_link_parts))
            if href:
                self.links.append((href, text))
            self._current_href = None
            self._current_link_parts = []
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "h4"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        text = clean_text(data)
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        self.text_parts.append(text)
        if self._current_href is not None:
            self._current_link_parts.append(text)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_text(value: Any) -> str:
    return WHITESPACE_RE.sub(" ", html.unescape(str(value or "")).strip())


def truncate_text(value: str, limit: int = 280) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def dedupe_keep_order(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for value in values:
        item = clean_text(value)
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def slug(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return token or "na"


def tokenize(value: str) -> List[str]:
    return [tok for tok in TOKEN_RE.findall((value or "").lower()) if tok and tok not in STOPWORDS and len(tok) > 2]


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_feedback_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"updated_at": None, "records": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"updated_at": None, "records": []}
    if not isinstance(payload, dict):
        return {"updated_at": None, "records": []}
    records = payload.get("records")
    return {
        "updated_at": payload.get("updated_at"),
        "records": list(records) if isinstance(records, list) else [],
    }


def parse_market_city(label: str) -> str:
    text = clean_text(label)
    if not text:
        return ""
    return text.split("/", 1)[0].strip()


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return clean_text(value)


def company_feedback_key(value: Any) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
    return token or "unknown"


def url_host(url: str) -> str:
    try:
        netloc = urllib.parse.urlparse(url).netloc.lower().strip()
    except Exception:
        return ""
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def same_host(a: str, b: str) -> bool:
    return url_host(a) == url_host(b)


def unwrap_duckduckgo_redirect(url: str) -> str:
    raw = clean_text(url)
    if raw.startswith("//"):
        raw = "https:" + raw
    parsed = urllib.parse.urlparse(raw)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        query = urllib.parse.parse_qs(parsed.query)
        target = clean_text(query.get("uddg", [""])[0])
        if target:
            return target
    return raw


def is_probably_directory(url: str) -> bool:
    host = url_host(url)
    return any(hint in host for hint in BAD_HOST_HINTS)


def fetch_text_url(url: str, timeout: int) -> Tuple[str, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DemandGridResearch/0.1 (+https://optimizedworkflow.dev)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        final_url = str(getattr(resp, "geturl", lambda: url)())
        charset = getattr(resp.headers, "get_content_charset", lambda: None)() or "utf-8"
        data = resp.read(1_500_000)
    return data.decode(charset, errors="replace"), final_url


async def fetch_crawl4ai_markdown(url: str, timeout_seconds: int) -> str:
    try:
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig, CacheMode, CrawlerRunConfig
    except Exception as exc:
        raise RuntimeError("crawl4ai is not installed") from exc

    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=timeout_seconds * 1000)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if not bool(getattr(result, "success", False)):
            raise RuntimeError(clean_text(getattr(result, "error_message", "crawl4ai crawl failed")))
        markdown = getattr(result, "markdown", None)
        if isinstance(markdown, str):
            return clean_text(markdown)
        if markdown is not None:
            return clean_text(getattr(markdown, "fit_markdown", "") or getattr(markdown, "raw_markdown", "") or str(markdown))
    return ""


def maybe_trafilatura_text(html_text: str) -> str:
    try:
        import trafilatura  # type: ignore
    except Exception:
        return ""
    try:
        extracted = trafilatura.extract(html_text, include_links=False, include_formatting=False)
        return clean_text(extracted or "")
    except Exception:
        return ""


def parse_jsonld_blocks(html_text: str) -> List[Any]:
    blocks: List[Any] = []
    for raw in SCRIPT_LD_JSON_RE.findall(html_text or ""):
        payload = clean_text(raw)
        if not payload:
            continue
        try:
            blocks.append(json.loads(payload))
        except Exception:
            continue
    return blocks


def collect_jsonld_contacts(blocks: Iterable[Any]) -> Dict[str, List[str]]:
    names: List[str] = []
    emails: List[str] = []
    phones: List[str] = []
    addresses: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            node_type = str(node.get("@type") or "")
            if node_type:
                pass
            name = clean_text(node.get("name"))
            email_value = clean_text(node.get("email"))
            phone_value = clean_text(node.get("telephone"))
            address = node.get("address")
            if name:
                names.append(name)
            if email_value:
                emails.append(email_value.replace("mailto:", ""))
            if phone_value:
                phones.append(normalize_phone(phone_value))
            if isinstance(address, dict):
                address_text = clean_text(
                    " ".join(
                        str(address.get(part) or "")
                        for part in (
                            "streetAddress",
                            "addressLocality",
                            "addressRegion",
                            "postalCode",
                        )
                    )
                )
                if address_text:
                    addresses.append(address_text)
            elif address:
                addresses.append(clean_text(address))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for block in blocks:
        walk(block)
    return {
        "names": dedupe_keep_order(names),
        "emails": dedupe_keep_order(emails),
        "phones": dedupe_keep_order(phones),
        "addresses": dedupe_keep_order(addresses),
    }


def classify_internal_links(links: Iterable[Tuple[str, str]], base_url: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    internal: List[str] = []
    contact: List[str] = []
    about: List[str] = []
    services: List[str] = []
    seen: set[str] = set()
    base_host = url_host(base_url)

    for href, label in links:
        full_url = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(full_url)
        if parsed.scheme not in {"http", "https"}:
            continue
        normalized = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        if url_host(normalized) != base_host:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        internal.append(normalized)
        hay = f"{label} {parsed.path}".strip()
        if CONTACT_LINK_RE.search(hay):
            contact.append(normalized)
        if ABOUT_LINK_RE.search(hay):
            about.append(normalized)
        if SERVICE_LINK_RE.search(hay):
            services.append(normalized)
    return internal, contact, about, services


def page_text_summary(page: PageSnapshot) -> str:
    if page.meta_description:
        return truncate_text(page.meta_description, 280)
    text = clean_text(page.text)
    if not text:
        return ""
    return truncate_text(text, 280)


def fetch_page_snapshot(url: str, timeout: int, text_provider: str) -> PageSnapshot:
    html_text, final_url = fetch_text_url(url, timeout=timeout)
    parser = PageParser()
    parser.feed(html_text)
    jsonld_blocks = parse_jsonld_blocks(html_text)
    internal_links, contact_links, about_links, service_links = classify_internal_links(parser.links, final_url)
    visible_text = clean_text(" ".join(parser.text_parts))

    if text_provider in {"auto", "trafilatura"}:
        trafilatura_text = maybe_trafilatura_text(html_text)
        if trafilatura_text:
            visible_text = trafilatura_text
    if text_provider == "crawl4ai":
        crawl_text = asyncio.run(fetch_crawl4ai_markdown(final_url, timeout))
        if crawl_text:
            visible_text = crawl_text

    emails = dedupe_keep_order(list(EMAIL_RE.findall(html_text)) + list(EMAIL_RE.findall(visible_text)))
    phones = dedupe_keep_order([normalize_phone(v) for v in PHONE_RE.findall(html_text)] + [normalize_phone(v) for v in PHONE_RE.findall(visible_text)])

    return PageSnapshot(
        url=url,
        final_url=final_url,
        title=clean_text(" ".join(parser.title_parts)),
        meta_description=parser.meta_description,
        text=visible_text,
        emails=emails,
        phones=phones,
        links=internal_links and [(u, "") for u in internal_links] or [],
        jsonld=jsonld_blocks,
        contact_links=contact_links,
        about_links=about_links,
        service_links=service_links,
    )


def ddg_html_search(query: str, limit: int, timeout: int) -> List[SearchCandidate]:
    search_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
    html_text = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="ignore")
    titles = list(re.finditer(r'<a rel="nofollow" class="result__a" href="(.*?)">(.*?)</a>', html_text))
    snippet_matches = re.findall(r'<(?:a|div) class="result__snippet".*?>(.*?)</(?:a|div)>', html_text, re.S)
    flat_snippets = [clean_text(re.sub(r"<.*?>", "", raw)) for raw in snippet_matches]
    out: List[SearchCandidate] = []
    for idx, match in enumerate(titles[: max(1, limit)]):
        href = unwrap_duckduckgo_redirect(match.group(1))
        title = clean_text(re.sub(r"<.*?>", "", match.group(2)))
        snippet = flat_snippets[idx] if idx < len(flat_snippets) else ""
        if not href:
            continue
        out.append(SearchCandidate(title=title, url=href, snippet=snippet, provider="duckduckgo_html", query=query, rank=idx + 1))
    return out


def ddgs_search(query: str, limit: int) -> List[SearchCandidate]:
    try:
        from ddgs import DDGS  # type: ignore
    except Exception as exc:
        raise RuntimeError("ddgs is not installed") from exc

    out: List[SearchCandidate] = []
    with DDGS() as client:
        for idx, row in enumerate(client.text(query, max_results=max(1, limit))):
            url = clean_text(row.get("href") or row.get("url") or "")
            title = clean_text(row.get("title") or "")
            snippet = clean_text(row.get("body") or row.get("snippet") or "")
            if not url:
                continue
            out.append(SearchCandidate(title=title, url=url, snippet=snippet, provider="ddgs", query=query, rank=idx + 1))
    return out


def search_candidates_for_queries(queries: List[str], provider: str, limit_per_query: int, timeout: int) -> List[SearchCandidate]:
    merged: List[SearchCandidate] = []
    seen: set[str] = set()
    for query in queries:
        try:
            if provider == "ddgs":
                batch = ddgs_search(query, limit_per_query)
            elif provider == "duckduckgo_html":
                batch = ddg_html_search(query, limit_per_query, timeout)
            elif provider == "auto":
                try:
                    batch = ddgs_search(query, limit_per_query)
                except Exception:
                    batch = ddg_html_search(query, limit_per_query, timeout)
            else:
                raise RuntimeError(f"unsupported search provider: {provider}")
        except Exception:
            batch = []
        for candidate in batch:
            key = candidate.url.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(candidate)
    return merged


def extract_hint_domains(opportunity: Dict[str, Any]) -> List[str]:
    domains: List[str] = []
    for email in opportunity.get("contact_hint_emails") or []:
        value = clean_text(email)
        if "@" in value:
            domains.append(value.split("@", 1)[1].lower())
    return dedupe_keep_order(domains)


def build_search_queries(opportunity: Dict[str, Any]) -> List[str]:
    company = clean_text(opportunity.get("company_name_guess"))
    title = clean_text(opportunity.get("title"))
    market_label = parse_market_city(clean_text(opportunity.get("market_label")))
    simplified_title = clean_text(re.sub(r"[^A-Za-z0-9 ]+", " ", title))
    queries = []
    if company and market_label:
        queries.append(f"{company} {market_label} official site")
        queries.append(f"{company} {simplified_title} {market_label}")
    if company:
        queries.append(f"{company} contact")
        queries.append(f"{company} official site")
    if simplified_title and market_label:
        queries.append(f"{simplified_title} {market_label} {company}")
    return dedupe_keep_order(queries)


def score_candidate(candidate: SearchCandidate, opportunity: Dict[str, Any]) -> SearchCandidate:
    company = clean_text(opportunity.get("company_name_guess"))
    title = clean_text(opportunity.get("title"))
    market_label = parse_market_city(clean_text(opportunity.get("market_label")))
    hint_domains = extract_hint_domains(opportunity)
    hay = f"{candidate.title} {candidate.snippet} {candidate.url}".lower()
    company_tokens = tokenize(company)
    title_tokens = tokenize(title)
    market_tokens = tokenize(market_label)
    score = 0.15
    reasons: List[str] = []

    if is_probably_directory(candidate.url):
        score -= 0.2
        reasons.append("directory_penalty")

    for token in company_tokens[:5]:
        if token in hay:
            score += 0.12
            reasons.append(f"company:{token}")

    for token in title_tokens[:3]:
        if token in hay:
            score += 0.05
            reasons.append(f"title:{token}")

    for token in market_tokens[:2]:
        if token in hay:
            score += 0.05
            reasons.append(f"market:{token}")

    candidate_host = url_host(candidate.url)
    if any(domain == candidate_host for domain in hint_domains):
        score += 0.45
        reasons.append("hint_domain_exact")
    elif any(domain.endswith(candidate_host) or candidate_host.endswith(domain) for domain in hint_domains):
        score += 0.35
        reasons.append("hint_domain_partial")

    if candidate.rank == 1:
        score += 0.06
        reasons.append("rank1")
    elif candidate.rank == 2:
        score += 0.03
        reasons.append("rank2")

    candidate.score = round(max(0.0, min(score, 0.99)), 3)
    candidate.score_reasons = reasons
    return candidate


def choose_best_candidate(candidates: List[SearchCandidate], opportunity: Dict[str, Any]) -> SearchCandidate | None:
    if not candidates:
        return None
    scored = [score_candidate(candidate, opportunity) for candidate in candidates]
    scored.sort(key=lambda item: (item.score, -item.rank), reverse=True)
    return scored[0]


def suppressed_feedback_entries(opportunity: Dict[str, Any], feedback_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    company_key = company_feedback_key(opportunity.get("company_name_guess"))
    opportunity_id = clean_text(opportunity.get("opportunity_id"))
    out: List[Dict[str, Any]] = []
    for item in feedback_payload.get("records") or []:
        if not isinstance(item, dict) or not bool(item.get("active")):
            continue
        if str(item.get("company_key") or "") == company_key or (opportunity_id and str(item.get("opportunity_id") or "") == opportunity_id):
            out.append(dict(item))
    return out


def role_context_summary(opportunity: Dict[str, Any]) -> str:
    company = clean_text(opportunity.get("company_name_guess") or "this company")
    title = clean_text(opportunity.get("title") or "an operations role")
    description = truncate_text(clean_text(opportunity.get("posting_description") or ""), 180)
    if description:
        return f"{company} appears to be hiring for {title}. Posting context: {description}"
    return f"{company} appears to be hiring for {title}."


def likely_operational_pain(opportunity: Dict[str, Any]) -> str:
    role_family = clean_text(opportunity.get("role_family")).lower()
    description = clean_text(opportunity.get("posting_description") or "").lower()
    if role_family == "payroll_finance_admin":
        return "Payroll, billing, AP/AR, reconciliation, and recurring finance admin work likely rely on too much manual coordination."
    if role_family == "customer_support_ops":
        return "Repeat customer questions, routing, inbox handling, and operator follow-up likely consume too much manual time."
    if "schedule" in description or "dispatch" in description:
        return "Scheduling, dispatch, inbox cleanup, and handoffs likely require too much manual operator effort."
    return "Data entry, admin handoffs, scheduling, and inbox follow-up likely need more manual work than they should."


def likely_first_automation_win(opportunity: Dict[str, Any]) -> str:
    hypotheses = [clean_text(v) for v in (opportunity.get("automation_hypotheses") or []) if clean_text(v)]
    if hypotheses:
        return hypotheses[0]
    role_family = clean_text(opportunity.get("role_family")).lower()
    if role_family == "payroll_finance_admin":
        return "invoice and payroll reconciliation workflow automation"
    if role_family == "customer_support_ops":
        return "AI-assisted inbox triage and response drafting"
    return "intake-to-CRM and scheduling workflow automation"


def infer_industry(opportunity: Dict[str, Any], business_summary: str, resolved_name: str, website_url: str) -> str:
    hay = " ".join(
        [
            clean_text(opportunity.get("title")),
            clean_text(opportunity.get("posting_description")),
            clean_text(opportunity.get("company_name_guess")),
            clean_text(resolved_name),
            clean_text(business_summary),
            clean_text(website_url),
        ]
    ).lower()
    if any(token in hay for token in ["plumb", "hvac", "heating", "cooling", "electrical", "contractor", "dispatch", "service call"]):
        return "field services / skilled trades"
    if any(token in hay for token in ["dental", "medical", "clinic", "patient", "health"]):
        return "healthcare operations"
    if any(token in hay for token in ["warehouse", "logistics", "freight", "shipping", "inventory"]):
        return "logistics / distribution"
    if any(token in hay for token in ["property", "real estate", "leasing", "apartment", "maintenance"]):
        return "property operations"
    if any(token in hay for token in ["manufactur", "fabricat", "machine shop", "industrial"]):
        return "manufacturing / industrial operations"
    return "general business operations"


def infer_hiring_signal(opportunity: Dict[str, Any], pain_line: str) -> str:
    title = clean_text(opportunity.get("title") or "this role")
    desc = clean_text(opportunity.get("posting_description") or "").lower()
    if any(token in desc for token in ["immediate", "asap", "urgent", "right away"]):
        return f"The post suggests {title} is a live urgency hire rather than future planning, which usually means the team already feels the operational strain." 
    if any(token in desc for token in ["manage", "coordinate", "follow up", "schedule", "dispatch"]):
        return f"The post reads like a coordination-heavy role. That usually means workflow volume has grown past what the current team or systems can comfortably absorb."
    return f"The hiring signal points to repeated operational work that is important enough to hire around. {pain_line}"


def business_model_read(opportunity: Dict[str, Any], business_summary: str, resolved_name: str, industry: str) -> str:
    summary = clean_text(business_summary)
    company = clean_text(resolved_name or opportunity.get("company_name_guess") or "This company")
    if summary:
        return f"{company} appears to operate in {industry}. Public site language suggests: {truncate_text(summary, 200)}"
    title = clean_text(opportunity.get("title") or "the posted role")
    return f"{company} appears to operate in {industry}. Even without a strong website read, the role {title} implies recurring workflow load around coordination, admin, or customer operations."


def role_analysis(opportunity: Dict[str, Any]) -> str:
    title = clean_text(opportunity.get("title") or "the posted role")
    desc = clean_text(opportunity.get("posting_description") or "")
    role_family = clean_text(opportunity.get("role_family")).lower()
    if role_family == "payroll_finance_admin":
        return f"{title} is likely being hired to absorb payroll, invoice, AP/AR, reconciliation, and deadline-driven finance admin work that is still too manual today."
    if role_family == "customer_support_ops":
        return f"{title} is likely being hired to absorb inbound questions, routing, follow-up, and customer communication volume that currently requires too much human handling."
    if any(token in desc.lower() for token in ["schedule", "dispatch", "calendar"]):
        return f"{title} looks like a scheduling and coordination role. That usually means the business is spending too much human effort on handoffs, calendar management, and status chasing."
    return f"{title} looks like a role meant to absorb repetitive admin, follow-up, and process coordination work that probably sits between systems today."


def likely_bottlenecks(opportunity: Dict[str, Any], pain_line: str, first_win: str, industry: str) -> List[Dict[str, str]]:
    role_family = clean_text(opportunity.get("role_family")).lower()
    desc = clean_text(opportunity.get("posting_description") or "").lower()
    items: List[Dict[str, str]] = []

    def add(name: str, why: str, evidence: str) -> None:
        items.append({"name": name, "why": why, "evidence": evidence})

    if role_family == "payroll_finance_admin":
        add("Finance admin backlog", pain_line, "Role family maps to payroll / finance admin and the first automation win points at invoice or reconciliation work.")
        add("Cross-system data re-entry", "Payroll, billing, and reconciliation work often forces one person to move data between inboxes, spreadsheets, and accounting systems.", f"Recommended first win: {first_win}.")
        add("Operator dependence on one person", "Deadline-driven back-office work becomes fragile when too much context sits with one admin hire.", "Hiring around the pain suggests the business needs throughput and reliability right now.")
    elif role_family == "customer_support_ops":
        add("Inbound volume and repeat questions", pain_line, "Role family maps to customer support operations.")
        add("Slow routing and follow-up", "When a team hires for support ops, they usually need help triaging, routing, and following up faster.", f"Recommended first win: {first_win}.")
        add("Inconsistent customer response quality", "High-volume support tends to create uneven response quality unless there is system support.", "The post implies human bandwidth is the current control point.")
    else:
        add("Coordination overhead", pain_line, "The posting reads like the company is hiring around repeated process work rather than one-off specialist output.")
        add("Manual handoffs between tools", "A lot of businesses add admin roles because inbox, spreadsheet, and scheduling work does not flow cleanly end to end.", f"Recommended first win: {first_win}.")
        evidence = "The post mentions scheduling / dispatch style work." if any(token in desc for token in ["schedule", "dispatch", "calendar"]) else f"Industry read: {industry}."
        add("Slow response or status chasing", "Businesses in this pattern usually lose time to chasing updates, confirming information, and keeping work moving manually.", evidence)
    return items[:3]


def recommended_ai_workflow(opportunity: Dict[str, Any], first_win: str) -> Dict[str, Any]:
    role_family = clean_text(opportunity.get("role_family")).lower()
    workflow = first_win
    stays_human = "final approvals, exceptions, and relationship-sensitive decisions"
    impact = "less operator load, faster throughput, and fewer dropped handoffs"
    if role_family == "payroll_finance_admin":
        workflow = first_win or "invoice ingestion and reconciliation workflow"
        stays_human = "final accounting approval, payment release, and exception handling"
        impact = "faster back-office throughput and fewer finance admin bottlenecks"
    elif role_family == "customer_support_ops":
        workflow = first_win or "AI-assisted inbox triage and response drafting"
        stays_human = "escalations, sensitive customer issues, and final relationship calls"
        impact = "faster response times and less repetitive support load"
    return {
        "workflow": workflow,
        "what_ai_does": f"Uses AI to handle the repetitive parts of {workflow}, prepare structured outputs, and move work into the right next step.",
        "what_stays_human": stays_human,
        "expected_business_impact": impact,
    }


def recommendation_ladder(opportunity: Dict[str, Any], workflow: str) -> List[Dict[str, str]]:
    title = clean_text(opportunity.get("title") or "the posted role")
    return [
        {
            "level": "smallest_useful_win",
            "recommendation": f"Audit the current {title} workflow and automate the highest-volume step first.",
        },
        {
            "level": "better_system",
            "recommendation": f"Add a structured AI-assisted {workflow} lane with handoff rules, queueing, and review points.",
        },
        {
            "level": "operator_system",
            "recommendation": "Connect intake, routing, follow-up, and reporting so the business gets one cleaner operating loop instead of isolated automations.",
        },
    ]


def outreach_strategy(opportunity: Dict[str, Any], what_matters: str, workflow: str) -> Dict[str, Any]:
    title = clean_text(opportunity.get("title") or "the role you posted")
    return {
        "main_angle": what_matters,
        "best_hook": f"Use the hiring post for {title} as proof that this workflow matters right now.",
        "tone": "practical, evidence-based, not hypey",
        "cta": f"Offer 2-3 concrete workflow ideas around {workflow} rather than pitching a generic AI agent.",
        "what_not_to_say": "Do not lead with model names, AGI language, or broad transformation claims.",
    }


def opportunity_scores(opportunity: Dict[str, Any], research_confidence: float, contact_score: float) -> Dict[str, float]:
    automation_score = float(opportunity.get("automation_score") or 0.0)
    confidence = float(opportunity.get("confidence") or 0.0)
    pain = round(min(10.0, 4.5 + automation_score * 5.0), 1)
    ai_fit = round(min(10.0, 4.0 + automation_score * 5.5), 1)
    urgency = round(min(10.0, 3.5 + confidence * 4.0 + (1.5 if contact_score >= 0.5 else 0.0)), 1)
    ease = round(min(10.0, 4.0 + automation_score * 3.0), 1)
    commercial = round(min(10.0, 3.5 + research_confidence * 4.0 + contact_score * 2.0), 1)
    overall = round((pain + ai_fit + urgency + commercial) / 4.0, 1)
    return {
        "pain_severity": pain,
        "ai_fit": ai_fit,
        "urgency": urgency,
        "ease_of_implementation": ease,
        "commercial_potential": commercial,
        "overall_priority": overall,
    }


def build_superhuman_sales_brief(opportunity: Dict[str, Any], base_record: Dict[str, Any], business_summary: str, resolved_name: str, contact_score: float, research_confidence: float) -> Dict[str, Any]:
    industry = infer_industry(opportunity, business_summary, resolved_name, str(base_record.get("website_url") or ""))
    pain_line = clean_text(base_record.get("likely_operational_pain"))
    first_win = clean_text(base_record.get("likely_first_automation_win"))
    signal = infer_hiring_signal(opportunity, pain_line)
    business_read = business_model_read(opportunity, business_summary, resolved_name, industry)
    role_read = role_analysis(opportunity)
    bottlenecks = likely_bottlenecks(opportunity, pain_line, first_win, industry)
    workflow = recommended_ai_workflow(opportunity, first_win)
    what_matters = f"The role likely exists because {pain_line.lower().rstrip('.')} The strongest first AI wedge appears to be {workflow['workflow']}, which should matter because it can create {workflow['expected_business_impact']}."
    return {
        "lead_snapshot": {
            "opportunity_id": clean_text(opportunity.get("opportunity_id")),
            "company": clean_text(resolved_name or opportunity.get("company_name_guess")),
            "industry": industry,
            "role": clean_text(opportunity.get("title")),
            "market": clean_text(opportunity.get("market_label") or opportunity.get("market_id")),
            "posting_url": clean_text(opportunity.get("posting_url")),
        },
        "hiring_signal": signal,
        "company_business_read": business_read,
        "role_analysis": role_read,
        "likely_operational_bottlenecks": bottlenecks,
        "highest_leverage_ai_opportunity": workflow,
        "why_this_matters_now": what_matters,
        "recommendation_ladder": recommendation_ladder(opportunity, workflow["workflow"]),
        "outreach_strategy": outreach_strategy(opportunity, what_matters, workflow["workflow"]),
        "scores": opportunity_scores(opportunity, research_confidence, contact_score),
    }


def contactability_score(emails: List[str], phones: List[str], contact_page_url: str, candidate: SearchCandidate | None) -> float:
    score = 0.2
    if candidate and candidate.score:
        score += min(0.35, candidate.score * 0.4)
    if emails:
        score += 0.25
    if phones:
        score += 0.2
    if contact_page_url:
        score += 0.15
    return round(min(score, 0.99), 3)


def summarize_pages(homepage: PageSnapshot | None, pages: List[PageSnapshot]) -> Tuple[List[str], List[str], str, str, List[str], List[str]]:
    all_pages = [page for page in [homepage, *pages] if page is not None]
    emails: List[str] = []
    phones: List[str] = []
    contact_forms: List[str] = []
    source_refs: List[str] = []
    names: List[str] = []
    addresses: List[str] = []
    snippets: List[str] = []

    for page in all_pages:
        source_refs.append(page.final_url)
        emails.extend(page.emails)
        phones.extend(page.phones)
        contact_forms.extend(page.contact_links)
        snippets.append(page_text_summary(page))
        jsonld_contacts = collect_jsonld_contacts(page.jsonld)
        names.extend(jsonld_contacts.get("names") or [])
        emails.extend(jsonld_contacts.get("emails") or [])
        phones.extend(jsonld_contacts.get("phones") or [])
        addresses.extend(jsonld_contacts.get("addresses") or [])

    business_summary = ""
    for snippet in snippets:
        if snippet:
            business_summary = snippet
            break

    return (
        dedupe_keep_order(emails),
        dedupe_keep_order([normalize_phone(v) for v in phones]),
        business_summary,
        dedupe_keep_order(addresses)[0] if addresses else "",
        dedupe_keep_order(contact_forms),
        dedupe_keep_order(source_refs),
    )


def research_opportunity(opportunity: Dict[str, Any], search_provider: str, text_provider: str, limit_per_query: int, timeout: int, max_fetch_pages: int, feedback_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    opportunity_id = clean_text(opportunity.get("opportunity_id"))
    queries = build_search_queries(opportunity)
    candidates = search_candidates_for_queries(queries, search_provider, limit_per_query, timeout)
    active_feedback = suppressed_feedback_entries(opportunity, feedback_payload or {"records": []})
    suppressed_hosts = {str(item.get("resolved_host") or "").strip().lower() for item in active_feedback if str(item.get("resolved_host") or "").strip()}
    candidate_host_map = {candidate.url: url_host(candidate.url) for candidate in candidates}
    filtered_candidates = [candidate for candidate in candidates if candidate_host_map.get(candidate.url, "") not in suppressed_hosts]
    suppressed_candidates = [candidate for candidate in candidates if candidate_host_map.get(candidate.url, "") in suppressed_hosts]
    best = choose_best_candidate(filtered_candidates, opportunity)

    base_record: Dict[str, Any] = {
        "opportunity_id": opportunity_id,
        "market_id": clean_text(opportunity.get("market_id")),
        "market_label": clean_text(opportunity.get("market_label")),
        "company_name_guess": clean_text(opportunity.get("company_name_guess")),
        "title": clean_text(opportunity.get("title")),
        "role_family": clean_text(opportunity.get("role_family")),
        "posting_url": clean_text(opportunity.get("posting_url")),
        "search_queries": queries,
        "search_provider": search_provider,
        "research_generated_at": now_iso(),
        "role_context_summary": role_context_summary(opportunity),
        "likely_operational_pain": likely_operational_pain(opportunity),
        "likely_first_automation_win": likely_first_automation_win(opportunity),
        "search_candidates": [
            {
                "title": candidate.title,
                "url": candidate.url,
                "snippet": truncate_text(candidate.snippet, 220),
                "provider": candidate.provider,
                "query": candidate.query,
                "rank": candidate.rank,
                "score": candidate.score,
                "score_reasons": candidate.score_reasons or [],
            }
            for candidate in sorted(candidates, key=lambda item: (item.score, -item.rank), reverse=True)[:10]
        ],
        "suppressed_feedback_hosts": sorted(suppressed_hosts),
        "suppressed_feedback_count": len(active_feedback),
        "suppressed_candidates": [
            {
                "title": candidate.title,
                "url": candidate.url,
                "query": candidate.query,
                "host": candidate_host_map.get(candidate.url, ""),
            }
            for candidate in suppressed_candidates[:10]
        ],
    }

    if best is None:
        base_record.update(
            {
                "research_status": "unresolved",
                "research_error": "all_candidates_suppressed_by_feedback" if candidates and not filtered_candidates and suppressed_hosts else "no_search_candidates",
                "resolved_company_name": clean_text(opportunity.get("company_name_guess")),
                "website_url": "",
                "contact_page_url": "",
                "about_page_url": "",
                "services_page_urls": [],
                "emails": dedupe_keep_order(opportunity.get("contact_hint_emails") or []),
                "phones": dedupe_keep_order([normalize_phone(v) for v in (opportunity.get("contact_hint_phones") or [])]),
                "contact_forms": [],
                "business_summary": "",
                "address": "",
                "contactability_score": 0.1,
                "research_confidence": 0.15,
                "source_refs": [],
            }
        )
        brief = build_superhuman_sales_brief(opportunity, base_record, "", clean_text(opportunity.get("company_name_guess")), 0.1, 0.15)
        base_record["what_matters_summary"] = brief.get("why_this_matters_now")
        base_record["recommended_ai_workflow"] = ((brief.get("highest_leverage_ai_opportunity") or {}).get("workflow"))
        base_record["superhuman_sales_brief"] = brief
        return base_record

    try:
        homepage = fetch_page_snapshot(best.url, timeout=timeout, text_provider=text_provider)
        fetch_targets: List[str] = []
        for url in homepage.contact_links + homepage.about_links + homepage.service_links:
            if url not in fetch_targets:
                fetch_targets.append(url)
        page_snapshots: List[PageSnapshot] = []
        for url in fetch_targets[: max(0, max_fetch_pages)]:
            try:
                page_snapshots.append(fetch_page_snapshot(url, timeout=timeout, text_provider=text_provider))
            except Exception:
                continue

        emails, phones, business_summary, address, contact_forms, source_refs = summarize_pages(homepage, page_snapshots)
        email_hints = dedupe_keep_order(opportunity.get("contact_hint_emails") or [])
        phone_hints = dedupe_keep_order([normalize_phone(v) for v in (opportunity.get("contact_hint_phones") or [])])
        emails = dedupe_keep_order(email_hints + emails)
        phones = dedupe_keep_order(phone_hints + phones)
        jsonld_contacts = collect_jsonld_contacts(homepage.jsonld)
        resolved_name = clean_text(jsonld_contacts.get("names", [""])[0] if jsonld_contacts.get("names") else homepage.title or best.title or opportunity.get("company_name_guess"))
        contact_page_url = homepage.contact_links[0] if homepage.contact_links else ""
        about_page_url = homepage.about_links[0] if homepage.about_links else ""
        services_page_urls = homepage.service_links[:3]
        contact_score = contactability_score(emails, phones, contact_page_url, best)
        research_confidence = round(min(0.99, 0.35 + (best.score * 0.45) + (contact_score * 0.2)), 3)

        base_record.update(
            {
                "research_status": "ok",
                "research_error": "",
                "resolved_company_name": resolved_name,
                "website_url": homepage.final_url,
                "contact_page_url": contact_page_url,
                "about_page_url": about_page_url,
                "services_page_urls": services_page_urls,
                "emails": emails,
                "phones": phones,
                "contact_forms": contact_forms,
                "business_summary": business_summary,
                "address": address,
                "contactability_score": contact_score,
                "research_confidence": research_confidence,
                "best_match_score": best.score,
                "best_match_url": best.url,
                "best_match_title": best.title,
                "source_refs": source_refs,
            }
        )
        brief = build_superhuman_sales_brief(opportunity, base_record, business_summary, resolved_name, contact_score, research_confidence)
        base_record["what_matters_summary"] = brief.get("why_this_matters_now")
        base_record["recommended_ai_workflow"] = ((brief.get("highest_leverage_ai_opportunity") or {}).get("workflow"))
        base_record["superhuman_sales_brief"] = brief
        return base_record
    except Exception as exc:
        fallback_contact_score = contactability_score(
            dedupe_keep_order(opportunity.get("contact_hint_emails") or []),
            dedupe_keep_order([normalize_phone(v) for v in (opportunity.get("contact_hint_phones") or [])]),
            "",
            best,
        )
        fallback_confidence = round(min(0.75, 0.2 + best.score * 0.5), 3)
        base_record.update(
            {
                "research_status": "error",
                "research_error": clean_text(str(exc)) or "research_failed",
                "resolved_company_name": clean_text(opportunity.get("company_name_guess")),
                "website_url": best.url,
                "contact_page_url": "",
                "about_page_url": "",
                "services_page_urls": [],
                "emails": dedupe_keep_order(opportunity.get("contact_hint_emails") or []),
                "phones": dedupe_keep_order([normalize_phone(v) for v in (opportunity.get("contact_hint_phones") or [])]),
                "contact_forms": [],
                "business_summary": "",
                "address": "",
                "contactability_score": fallback_contact_score,
                "research_confidence": fallback_confidence,
                "best_match_score": best.score,
                "best_match_url": best.url,
                "best_match_title": best.title,
                "source_refs": [best.url],
            }
        )
        brief = build_superhuman_sales_brief(opportunity, base_record, "", clean_text(opportunity.get("company_name_guess")), fallback_contact_score, fallback_confidence)
        base_record["what_matters_summary"] = brief.get("why_this_matters_now")
        base_record["recommended_ai_workflow"] = ((brief.get("highest_leverage_ai_opportunity") or {}).get("workflow"))
        base_record["superhuman_sales_brief"] = brief
        return base_record


def filter_opportunities(payload: Dict[str, Any], market_ids: List[str], opportunity_ids: List[str], limit: int) -> List[Dict[str, Any]]:
    opportunities = list(payload.get("opportunities") or [])
    if market_ids:
        allow = {item.strip().lower() for item in market_ids if item.strip()}
        opportunities = [row for row in opportunities if clean_text(row.get("market_id")).lower() in allow]
    if opportunity_ids:
        allow_ids = {item.strip() for item in opportunity_ids if item.strip()}
        opportunities = [row for row in opportunities if clean_text(row.get("opportunity_id")) in allow_ids]
    opportunities.sort(key=lambda row: float(row.get("automation_score") or 0), reverse=True)
    if limit > 0:
        opportunities = opportunities[:limit]
    return opportunities


def write_summary_markdown(path: Path, output_json: Path, records: List[Dict[str, Any]]) -> None:
    ok = sum(1 for row in records if row.get("research_status") == "ok")
    unresolved = sum(1 for row in records if row.get("research_status") == "unresolved")
    errors = sum(1 for row in records if row.get("research_status") == "error")
    top = sorted(records, key=lambda row: float(row.get("research_confidence") or 0), reverse=True)[:10]
    lines = [
        "# Craigslist company research summary",
        "",
        f"- generated_at: `{now_iso()}`",
        f"- output_json: `{output_json}`",
        f"- records: `{len(records)}`",
        f"- ok: `{ok}`",
        f"- unresolved: `{unresolved}`",
        f"- errors: `{errors}`",
        "",
        "## Top records",
        "",
    ]
    for row in top:
        lines.extend(
            [
                f"### {clean_text(row.get('opportunity_id'))}",
                f"- status: `{clean_text(row.get('research_status'))}`",
                f"- company: `{clean_text(row.get('resolved_company_name') or row.get('company_name_guess'))}`",
                f"- website: `{clean_text(row.get('website_url'))}`",
                f"- confidence: `{row.get('research_confidence')}`",
                f"- first_win: `{clean_text(row.get('likely_first_automation_win'))}`",
                f"- what_matters: {clean_text(row.get('what_matters_summary')) or 'n/a'}",
                f"- summary: {clean_text(row.get('business_summary')) or 'n/a'}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve and enrich Craigslist opportunities into Chow research packets.")
    parser.add_argument("--input-json", default=str(DEFAULT_INPUT_JSON))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_JSON))
    parser.add_argument("--feedback-json", default=str(DEFAULT_FEEDBACK_JSON))
    parser.add_argument("--summary-md", default=str(ROOT / "artifacts/craigslist-company-research-summary.md"))
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--limit-per-query", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-fetch-pages", type=int, default=3)
    parser.add_argument("--search-provider", choices=["auto", "ddgs", "duckduckgo_html"], default="auto")
    parser.add_argument("--text-provider", choices=["auto", "html", "trafilatura", "crawl4ai"], default="auto")
    parser.add_argument("--market-ids", default="")
    parser.add_argument("--opportunity-ids", default="")
    args = parser.parse_args()

    input_json = Path(args.input_json)
    output_json = Path(args.output_json)
    summary_md = Path(args.summary_md)
    config_json = Path(args.config)
    feedback_json = Path(args.feedback_json)
    if not input_json.exists():
        raise SystemExit(f"missing input json: {input_json}")

    payload = load_json(input_json)
    config = load_json(config_json) if config_json.exists() else {}
    feedback_payload = load_feedback_json(feedback_json)
    market_ids = [clean_text(v) for v in args.market_ids.split(",") if clean_text(v)]
    opportunity_ids = [clean_text(v) for v in args.opportunity_ids.split(",") if clean_text(v)]
    selected = filter_opportunities(payload, market_ids, opportunity_ids, args.limit)

    refreshed_records = [
        research_opportunity(
            opportunity,
            search_provider=args.search_provider,
            text_provider=args.text_provider,
            limit_per_query=args.limit_per_query,
            timeout=max(5, args.timeout),
            max_fetch_pages=max(0, args.max_fetch_pages),
            feedback_payload=feedback_payload,
        )
        for opportunity in selected
    ]

    existing_records: List[Dict[str, Any]] = []
    if output_json.exists():
        try:
            existing_payload = load_json(output_json)
            existing_records = [dict(row) for row in (existing_payload.get("records") or []) if isinstance(row, dict)]
        except Exception:
            existing_records = []

    refreshed_ids = {clean_text(row.get("opportunity_id")) for row in refreshed_records if clean_text(row.get("opportunity_id"))}
    merged_records = [row for row in existing_records if clean_text(row.get("opportunity_id")) not in refreshed_ids]
    merged_records.extend(refreshed_records)
    merged_records.sort(key=lambda row: float(row.get("research_confidence") or 0.0), reverse=True)

    out_payload = {
        "generated_at": now_iso(),
        "input_json": str(input_json),
        "config_version": clean_text(config.get("version")),
        "search_provider": args.search_provider,
        "text_provider": args.text_provider,
        "count": len(merged_records),
        "feedback_updated_at": feedback_payload.get("updated_at"),
        "feedback_record_count": len(feedback_payload.get("records") or []),
        "markets": market_ids,
        "opportunity_ids": opportunity_ids,
        "refreshed_count": len(refreshed_records),
        "refreshed_opportunity_ids": sorted(refreshed_ids),
        "records": merged_records,
        "summary": {
            "ok": sum(1 for row in merged_records if row.get("research_status") == "ok"),
            "unresolved": sum(1 for row in merged_records if row.get("research_status") == "unresolved"),
            "errors": sum(1 for row in merged_records if row.get("research_status") == "error"),
        },
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(out_payload, indent=2), encoding="utf-8")
    write_summary_markdown(summary_md, output_json, merged_records)
    print(json.dumps({**out_payload["summary"], "refreshed_count": len(refreshed_records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
