#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def load_env_file(path: Path) -> dict[str, str]:
    env = os.environ.copy()
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def wait_health(base_url: str, timeout_s: int = 45) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(base_url.rstrip("/") + "/health", timeout=2)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"server did not become healthy in {timeout_s}s")


def api(base_url: str, path: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    url = base_url.rstrip("/") + path
    r = requests.request(method, url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def text(locator) -> str:
    return (locator.text_content() or "").strip()


def expect(cond: bool, message: str) -> None:
    if not cond:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate a DemandGrid operator flow with Playwright")
    parser.add_argument("--base-url", default="http://127.0.0.1:8102")
    parser.add_argument("--port", type=int, default=8102)
    args = parser.parse_args()

    env = load_env_file(ROOT / ".env")

    server = subprocess.Popen(
        [
            "python3",
            "-m",
            "uvicorn",
            "backend.api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(args.port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )

    result: dict[str, object] = {"ok": False}
    original_workflow = None
    original_outcome = None
    site_id = None

    try:
        wait_health(args.base_url)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            page.goto(args.base_url, wait_until="networkidle", timeout=60000)

            page.wait_for_selector("#zip-select", timeout=30000)
            page.wait_for_function("document.querySelectorAll('#site-list-body tr').length > 0", timeout=30000)
            page.wait_for_timeout(1500)

            first_row = page.locator("#site-list-body tr").first
            site_id = first_row.get_attribute("data-site-id")
            expect(bool(site_id), "No site row loaded in list")

            all_count_text = text(page.locator("[data-queue-filter='all']"))
            park_count_text = text(page.locator("[data-queue-filter='park']"))
            expect("Park" in park_count_text, "Park filter chip missing")
            expect(all_count_text != park_count_text, "Queue chips did not render distinct counts")
            guide_text = text(page.locator("#workflow-guide"))
            expect("auto-loads the best hex and first lead" in guide_text, f"Guide text did not explain first-use workflow: {guide_text}")
            today_plan_text = text(page.locator("#today-plan"))
            expect(
                "Best Lead" in today_plan_text and "Today’s Objective" in today_plan_text and "Manager Mode" in today_plan_text and "Daily Command" in today_plan_text,
                f"Today's plan panel did not render actionable summary: {today_plan_text[:500]}",
            )
            page.evaluate("document.querySelector('#today-run-command-btn').click()")
            page.wait_for_function(
                """
                () => {
                  const status = (document.querySelector('#status')?.textContent || '').trim();
                  return status.includes('Manager mode:');
                }
                """,
                timeout=15000,
            )
            manager_status = text(page.locator("#status"))
            expect("Manager mode:" in manager_status, f"Daily command did not run: {manager_status}")
            site_id = page.evaluate(
                """
                () => {
                  if (window.state && window.state.selectedSiteId) return window.state.selectedSiteId;
                  const row = document.querySelector('#site-list-body tr');
                  return row ? row.getAttribute('data-site-id') : null;
                }
                """
            )
            expect(bool(site_id), "Manager mode did not leave an active site")

            site_payload = api(args.base_url, f"/api/v1/site/{site_id}")
            original_workflow = site_payload.get("operator_status", {}).get("status")
            original_outcome = api(args.base_url, f"/api/v1/operator/outcome/{site_id}").get("lead_outcome", {})

            page.wait_for_function(
                "() => { const btn = document.querySelector('#route-btn-inline'); return btn && !btn.disabled; }",
                timeout=10000,
            )
            route_ui_state = page.evaluate(
                """
                async () => {
                  const inlineBtn = document.querySelector('#route-btn-inline');
                  const topbarBtn = document.querySelector('#route-btn');
                  return {
                    inlineEnabled: !!inlineBtn && !inlineBtn.disabled,
                    topbarEnabled: !!topbarBtn && !topbarBtn.disabled,
                    inlineHandlerType: inlineBtn ? typeof inlineBtn.onclick : 'missing',
                    topbarHandlerType: topbarBtn ? typeof topbarBtn.onclick : 'missing',
                    helperType: typeof window.__demandGridRunRoutePlan,
                  };
                }
                """
            )
            expect(route_ui_state.get("inlineEnabled") is True, f"Inline route button not enabled: {route_ui_state}")
            expect(route_ui_state.get("topbarEnabled") is True, f"Topbar route button not enabled: {route_ui_state}")
            expect(route_ui_state.get("inlineHandlerType") == "function", f"Inline route button not wired: {route_ui_state}")
            expect(route_ui_state.get("topbarHandlerType") == "function", f"Topbar route button not wired: {route_ui_state}")
            expect(route_ui_state.get("helperType") == "function", f"Route helper missing: {route_ui_state}")

            route_result = page.evaluate(
                """
                async () => {
                  await window.__demandGridRunRoutePlan();
                  return {
                    status: document.querySelector('#status')?.textContent || '',
                  };
                }
                """
            )
            route_status = route_result.get("status", "")
            expect("Route ready:" in route_status, f"Route planning failed: {route_status}")
            topbar_route_status = route_status

            page.locator("[data-queue-filter='park']").click()
            page.wait_for_timeout(1000)
            meta_text = text(page.locator("#list-meta"))
            expect("park" in meta_text.lower(), f"Queue filter did not update list meta: {meta_text}")

            page.locator("[data-queue-filter='all']").click()
            page.wait_for_timeout(1000)

            page.evaluate(f"document.querySelector(\"#site-list-body tr[data-site-id='{site_id}']\")?.click()")
            page.wait_for_function(
                """
                () => {
                  const el = document.querySelector('#detail-card');
                  const text = (el && el.textContent) ? el.textContent : '';
                  return text.includes('Outcome Capture') && text.includes('Queue action');
                }
                """,
                timeout=10000,
            )

            detail_text = text(page.locator("#detail-card"))
            expect("Outcome Capture" in detail_text, f"Detail card did not render outcome capture: {detail_text[:500]}")
            expect("Queue action" in detail_text, f"Detail card missing queue action: {detail_text[:500]}")

            page.locator("[data-workflow-status='contacted']").click()
            page.wait_for_timeout(1000)
            status_text = text(page.locator("#status"))
            workflow_after_click = api(args.base_url, f"/api/v1/operator/status/{site_id}").get("operator_status", {})
            expect(
                workflow_after_click.get("status") == "contacted",
                f"Workflow quick action failed: status_text={status_text!r} api={workflow_after_click!r}",
            )

            page.locator("#outcome-status-select").select_option("contacted")
            page.locator("#outcome-note-input").fill("operator smoke test")
            page.locator("#outcome-save-btn").click()
            page.wait_for_timeout(1800)
            status_text = text(page.locator("#status"))
            expect("Saved lead outcome" in status_text, f"Outcome save failed: {status_text}")

            page.locator("#ask-ai-pitch-btn").click()
            page.wait_for_function(
                """
                () => {
                  const msgs = Array.from(document.querySelectorAll('#chat-log .chat-msg'));
                  const copilot = msgs.filter(el => {
                    const strong = el.querySelector('strong');
                    return strong && strong.textContent && strong.textContent.includes('Copilot:');
                  });
                  return copilot.length >= 2;
                }
                """,
                timeout=15000,
            )
            chat_text = text(page.locator("#chat-log"))
            expect("Error:" not in chat_text, f"AI pitch returned error: {chat_text[-400:]}")
            expect("Give me a 20 second pitch" in chat_text, "AI pitch request was not added to chat")
            expect(chat_text.count("Copilot:") >= 2, f"AI pitch did not produce a visible assistant reply: {chat_text[-500:]}")

            updated_outcome = api(args.base_url, f"/api/v1/operator/outcome/{site_id}").get("lead_outcome", {})
            expect(updated_outcome.get("status") == "contacted", f"Outcome API did not persist smoke update: {updated_outcome}")

            mobile = browser.new_page(viewport={"width": 430, "height": 932})
            mobile.goto(args.base_url, wait_until="networkidle", timeout=60000)
            mobile.wait_for_selector("#tab-list", timeout=30000)
            mobile.locator("#tab-list").click()
            mobile.wait_for_timeout(1200)
            body_class = mobile.locator("body").get_attribute("class") or ""
            expect("mobile-list" in body_class, f"Mobile list mode did not activate: {body_class}")
            mobile.wait_for_function("document.querySelectorAll('#site-cards .site-card').length > 0 || document.querySelectorAll('#site-list-body tr').length > 0", timeout=30000)
            mobile_guide_text = text(mobile.locator("#workflow-guide"))
            expect("auto-loads the best hex and first lead" in mobile_guide_text, f"Mobile guide text missing first-use copy: {mobile_guide_text}")
            mobile_detail = text(mobile.locator("#detail-card"))
            expect("Outcome Capture" in mobile_detail or "Run the lead" in mobile_detail, f"Mobile workspace detail did not load actionable content: {mobile_detail[:400]}")
            mobile.close()

            result = {
                "ok": True,
                "site_id": site_id,
                "all_chip": all_count_text,
                "park_chip": park_count_text,
                "guide_text": guide_text,
                "today_plan_text": today_plan_text[:400],
                "manager_status": manager_status,
                "route_ui_state": route_ui_state,
                "route_status": route_status,
                "topbar_route_status": topbar_route_status,
                "list_meta": meta_text,
                "status_after_save": status_text,
                "chat_tail": chat_text[-400:],
            }

            browser.close()

        return 0
    except PlaywrightTimeoutError as exc:
        result = {"ok": False, "error": f"timeout: {exc}"}
        return 1
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
        return 1
    finally:
        if site_id:
            try:
                if original_workflow:
                    requests.put(
                        args.base_url.rstrip("/") + f"/api/v1/operator/status/{site_id}",
                        json={"status": original_workflow},
                        timeout=20,
                    )
            except Exception:
                pass
            try:
                payload = {
                    "status": (original_outcome or {}).get("status", "unknown"),
                    "product": (original_outcome or {}).get("product", ""),
                    "objection": (original_outcome or {}).get("objection", ""),
                    "reason": (original_outcome or {}).get("reason", ""),
                    "realized_revenue_usd": (original_outcome or {}).get("realized_revenue_usd"),
                    "realized_profit_usd": (original_outcome or {}).get("realized_profit_usd"),
                    "note": (original_outcome or {}).get("note", ""),
                }
                requests.put(
                    args.base_url.rstrip("/") + f"/api/v1/operator/outcome/{site_id}",
                    json=payload,
                    timeout=20,
                )
            except Exception:
                pass

        print(json.dumps(result, indent=2))
        try:
            os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
