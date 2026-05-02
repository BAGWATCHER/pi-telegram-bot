#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clean_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _slug(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return token or "na"


def _parse_rss_items(xml_text: str) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_text)
    out: List[Dict[str, Any]] = []

    channel = root.find("channel")
    if channel is None:
        return out

    for item in channel.findall("item"):
        title = _clean_text(item.findtext("title", default=""))
        link = str(item.findtext("link", default="")).strip()
        guid = str(item.findtext("guid", default="")).strip()
        description = _clean_text(item.findtext("description", default=""))
        pub_date = str(item.findtext("pubDate", default="")).strip()

        out.append(
            {
                "title": title,
                "link": link,
                "guid": guid,
                "description": description,
                "pub_date": pub_date,
            }
        )
    return out


def _posting_id_from_link(link: str) -> str:
    text = str(link or "")
    m = re.search(r"/(\d{6,})\.html", text)
    if m:
        return m.group(1)
    m = re.search(r"([0-9]{6,})", text)
    if m:
        return m.group(1)
    return _slug(text)


def _extract_company_hint(title: str, description: str) -> str:
    title_text = str(title or "")
    for sep in [" - ", " | ", " @ ", " at "]:
        if sep in title_text:
            rhs = title_text.split(sep, 1)[1].strip()
            if rhs and len(rhs) > 1:
                return rhs

    desc = str(description or "")
    m = re.search(r"(?:company|employer)\s*[:\-]\s*([A-Za-z0-9&.,'()\- ]{2,80})", desc, flags=re.I)
    if m:
        return m.group(1).strip()

    return "unknown"


def _extract_contact_hints(description: str) -> Tuple[List[str], List[str]]:
    text = str(description or "")
    emails = sorted({e.lower() for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)})
    phones = sorted({p for p in re.findall(r"\+?1?[\s\-.]?(?:\(?\d{3}\)?[\s\-.]?)\d{3}[\s\-.]?\d{4}", text)})
    phones = [re.sub(r"\s+", "", p) for p in phones]
    return emails[:3], phones[:3]


def _build_role_classifier(config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    rules = []
    for raw in config.get("role_rules") or []:
        if not isinstance(raw, dict):
            continue
        role_family = str(raw.get("role_family") or "").strip() or "unclassified"
        keywords = [str(k).strip().lower() for k in (raw.get("keywords") or []) if str(k).strip()]
        hypotheses = [str(h).strip() for h in (raw.get("automation_hypotheses") or []) if str(h).strip()]
        rules.append({"role_family": role_family, "keywords": keywords, "automation_hypotheses": hypotheses})

    negatives = [str(k).strip().lower() for k in (config.get("negative_keywords") or []) if str(k).strip()]
    return rules, negatives


def _classify_role(text: str, rules: List[Dict[str, Any]], negatives: List[str]) -> Tuple[str, float, List[str], List[str]]:
    hay = str(text or "").lower()
    for token in negatives:
        if token and token in hay:
            return "non_target", 0.1, [], [token]

    best_role = "unclassified"
    best_hits: List[str] = []
    best_hypotheses: List[str] = []
    for rule in rules:
        hits = [kw for kw in (rule.get("keywords") or []) if kw in hay]
        if len(hits) > len(best_hits):
            best_role = str(rule.get("role_family") or "unclassified")
            best_hits = hits
            best_hypotheses = list(rule.get("automation_hypotheses") or [])

    if best_role == "unclassified":
        return best_role, 0.35, [], []

    # Heuristic confidence: strong role keywords + repeated signal in text.
    base = 0.56
    confidence = min(0.97, base + (0.09 * len(best_hits)))
    return best_role, round(confidence, 3), best_hypotheses[:3], best_hits


def _recommended_channel(emails: List[str], phones: List[str]) -> str:
    if emails:
        return "email"
    if phones:
        return "calling"
    return "manual_research"


def _build_outreach_angle(role_family: str, hypotheses: List[str]) -> str:
    role_label = role_family.replace("_", " ").strip() or "back-office"
    if hypotheses:
        top = hypotheses[0]
        return f"Offer a fast AI ops audit for {role_label} and lead with {top}."
    return f"Offer a fast AI ops audit for {role_label} workflows."


def _fetch_rss(url: str, timeout: int) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DemandGridSignals/0.1 (+https://demandgrid.local)",
            "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _build_search_url(base: str, query: str) -> str:
    parsed = urllib.parse.urlparse(base)
    q = urllib.parse.parse_qs(parsed.query)
    q["query"] = [query]
    q["format"] = ["rss"]
    query_string = urllib.parse.urlencode(q, doseq=True)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, query_string, parsed.fragment))


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch Craigslist job RSS signals for AI automation outreach")
    p.add_argument("--config", default="config/craigslist_job_signal_config.json")
    p.add_argument("--output-csv", default="data/raw/craigslist_job_signals.csv")
    p.add_argument("--output-json", default="data/processed/craigslist_job_signals.json")
    p.add_argument("--summary-md", default="artifacts/craigslist-job-signal-summary.md")
    p.add_argument("--summary-json", default="artifacts/craigslist-job-signal-summary.json")
    p.add_argument("--limit-per-query", type=int, default=30)
    p.add_argument("--timeout", type=int, default=20)
    args = p.parse_args()

    config_path = ROOT / args.config
    if not config_path.exists():
        raise SystemExit(f"missing config: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    markets = [m for m in (config.get("markets") or []) if isinstance(m, dict)]
    if not markets:
        raise SystemExit("config has no markets")

    rules, negatives = _build_role_classifier(config)
    fetched_at = _now_iso()

    signals_by_id: Dict[str, Dict[str, Any]] = {}
    query_stats: List[Dict[str, Any]] = []

    for market in markets:
        market_id = str(market.get("market_id") or "").strip() or "unknown"
        market_label = str(market.get("label") or market_id).strip()
        base = str(market.get("rss_search_base") or "").strip()
        if not base:
            continue
        queries = [str(q).strip() for q in (market.get("queries") or []) if str(q).strip()]

        for query in queries:
            search_url = _build_search_url(base, query)
            fetched_count = 0
            kept_count = 0
            errors: str | None = None

            try:
                rss = _fetch_rss(search_url, timeout=max(5, args.timeout))
                items = _parse_rss_items(rss)
                fetched_count = len(items)
            except Exception as exc:
                errors = str(exc)
                items = []

            for item in items[: max(1, args.limit_per_query)]:
                title = str(item.get("title") or "").strip()
                link = str(item.get("link") or "").strip()
                desc = str(item.get("description") or "").strip()
                post_id = _posting_id_from_link(link)

                composite_text = f"{title} {desc}"
                role_family, confidence, hypotheses, hits = _classify_role(composite_text, rules, negatives)
                if role_family == "non_target":
                    continue

                automation_score = confidence
                company_hint = _extract_company_hint(title, desc)
                emails, phones = _extract_contact_hints(desc)
                channel = _recommended_channel(emails, phones)

                opportunity_id = f"clj_{post_id}"
                prev = signals_by_id.get(opportunity_id)

                row = {
                    "opportunity_id": opportunity_id,
                    "source": "craigslist_rss",
                    "market_id": market_id,
                    "market_label": market_label,
                    "query": query,
                    "posting_id": post_id,
                    "title": title,
                    "company_name_guess": company_hint,
                    "role_family": role_family,
                    "automation_score": round(automation_score, 3),
                    "confidence": round(confidence, 3),
                    "matched_keywords": hits,
                    "automation_hypotheses": hypotheses,
                    "recommended_channel": channel,
                    "outreach_angle": _build_outreach_angle(role_family, hypotheses),
                    "contact_hint_emails": emails,
                    "contact_hint_phones": phones,
                    "posting_url": link,
                    "posting_description": desc[:1200],
                    "posted_at": str(item.get("pub_date") or "").strip() or None,
                    "fetched_at": fetched_at,
                    "status": "new",
                    "matched_queries": [query],
                }

                if prev:
                    merged_queries = sorted(set((prev.get("matched_queries") or []) + [query]))
                    if float(row.get("automation_score") or 0) > float(prev.get("automation_score") or 0):
                        row["matched_queries"] = merged_queries
                        signals_by_id[opportunity_id] = row
                    else:
                        prev["matched_queries"] = merged_queries
                else:
                    signals_by_id[opportunity_id] = row
                    kept_count += 1

            query_stats.append(
                {
                    "market_id": market_id,
                    "market_label": market_label,
                    "query": query,
                    "search_url": search_url,
                    "fetched_items": fetched_count,
                    "new_opportunities": kept_count,
                    "error": errors,
                }
            )

    opportunities = sorted(
        signals_by_id.values(),
        key=lambda item: (float(item.get("automation_score") or 0), str(item.get("posted_at") or "")),
        reverse=True,
    )

    output_csv = ROOT / args.output_csv
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "opportunity_id",
        "source",
        "market_id",
        "market_label",
        "query",
        "posting_id",
        "title",
        "company_name_guess",
        "role_family",
        "automation_score",
        "confidence",
        "matched_keywords",
        "automation_hypotheses",
        "recommended_channel",
        "outreach_angle",
        "contact_hint_emails",
        "contact_hint_phones",
        "posting_url",
        "posted_at",
        "fetched_at",
        "status",
        "matched_queries",
    ]
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in opportunities:
            flattened = dict(row)
            for key in ["matched_keywords", "automation_hypotheses", "contact_hint_emails", "contact_hint_phones", "matched_queries"]:
                flattened[key] = "|".join([str(v) for v in (row.get(key) or [])])
            writer.writerow(flattened)

    output_json = ROOT / args.output_json
    output_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": fetched_at,
        "config_version": str(config.get("version") or "v0"),
        "source_policy": config.get("source_policy") or {},
        "count": len(opportunities),
        "opportunities": opportunities,
        "query_stats": query_stats,
    }
    output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    role_counts: Dict[str, int] = {}
    channel_counts: Dict[str, int] = {}
    for item in opportunities:
        role = str(item.get("role_family") or "unclassified")
        channel = str(item.get("recommended_channel") or "manual_research")
        role_counts[role] = role_counts.get(role, 0) + 1
        channel_counts[channel] = channel_counts.get(channel, 0) + 1

    summary = {
        "generated_at": fetched_at,
        "config": str(config_path),
        "output_json": str(output_json),
        "output_csv": str(output_csv),
        "total_opportunities": len(opportunities),
        "role_counts": role_counts,
        "channel_counts": channel_counts,
        "query_stats": query_stats,
    }

    summary_json = ROOT / args.summary_json
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Craigslist Job Signal Summary",
        "",
        f"- generated_at: `{fetched_at}`",
        f"- config: `{config_path}`",
        f"- opportunities: **{len(opportunities)}**",
        f"- output json: `{output_json}`",
        f"- output csv: `{output_csv}`",
        "",
        "## Role counts",
        "",
    ]
    for key in sorted(role_counts.keys()):
        lines.append(f"- `{key}`: {role_counts[key]}")

    lines += ["", "## Recommended channel counts", ""]
    for key in sorted(channel_counts.keys()):
        lines.append(f"- `{key}`: {channel_counts[key]}")

    lines += ["", "## Query fetch stats", ""]
    for stat in query_stats:
        err = f" error={stat['error']}" if stat.get("error") else ""
        lines.append(
            f"- `{stat['market_id']}` `{stat['query']}` fetched={stat['fetched_items']} new={stat['new_opportunities']}{err}"
        )

    summary_md = ROOT / args.summary_md
    summary_md.parent.mkdir(parents=True, exist_ok=True)
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "opportunities": len(opportunities),
                "output_json": str(output_json),
                "output_csv": str(output_csv),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
