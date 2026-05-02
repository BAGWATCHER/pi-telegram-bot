#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path

import requests
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


def main() -> int:
    base_url = "http://127.0.0.1:8103"
    port = 8103
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
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )

    try:
        wait_health(base_url)
        result: dict[str, object] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            requests_seen: list[str] = []
            page.on(
                "request",
                lambda req: requests_seen.append(req.url) if "/api/v1/operator/route-plan" in req.url else None,
            )
            page.goto(base_url, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("#zip-select", timeout=30000)
            page.wait_for_function("document.querySelectorAll('#site-list-body tr').length > 0", timeout=30000)
            page.wait_for_function(
                "() => { const btn = document.querySelector('#route-btn-inline'); return btn && !btn.disabled; }",
                timeout=15000,
            )
            page.wait_for_timeout(1000)

            before = page.evaluate(
                """
                () => {
                  const btn = document.querySelector('#route-btn-inline');
                  const rect = btn.getBoundingClientRect();
                  const cx = rect.left + (rect.width / 2);
                  const cy = rect.top + (rect.height / 2);
                  const topEl = document.elementFromPoint(cx, cy);
                  return {
                    disabled: !!btn.disabled,
                    attrDisabled: btn.getAttribute('disabled'),
                    text: btn.textContent,
                    onclickType: typeof btn.onclick,
                    onclickSource: String(btn.onclick),
                    helperType: typeof window.__demandGridRunRoutePlan,
                    status: document.querySelector('#status')?.textContent || '',
                    pointerEvents: getComputedStyle(btn).pointerEvents,
                    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                    topElementTag: topEl ? topEl.tagName : null,
                    topElementId: topEl ? topEl.id : null,
                    sameTopElement: topEl === btn,
                  };
                }
                """
            )

            page.locator("#route-btn-inline").click()
            page.wait_for_timeout(2500)

            after_click = page.evaluate(
                """
                () => ({
                  status: document.querySelector('#status')?.textContent || '',
                  helperType: typeof window.__demandGridRunRoutePlan,
                })
                """
            )

            dom_click = page.evaluate(
                """
                async () => {
                  const btn = document.querySelector('#route-btn-inline');
                  btn.click();
                  await new Promise(resolve => setTimeout(resolve, 1500));
                  return {
                    status: document.querySelector('#status')?.textContent || '',
                  };
                }
                """
            )

            dispatch_click = page.evaluate(
                """
                async () => {
                  const btn = document.querySelector('#route-btn-inline');
                  btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                  await new Promise(resolve => setTimeout(resolve, 1500));
                  return {
                    status: document.querySelector('#status')?.textContent || '',
                  };
                }
                """
            )

            awaited = page.evaluate(
                """
                async () => {
                  try {
                    await window.__demandGridRunRoutePlan();
                    return { ok: true, status: document.querySelector('#status')?.textContent || '' };
                  } catch (err) {
                    return { ok: false, error: String(err), status: document.querySelector('#status')?.textContent || '' };
                  }
                }
                """
            )

            page.wait_for_timeout(1500)
            after_await = page.evaluate(
                "() => ({ status: document.querySelector('#status')?.textContent || '' })"
            )

            result = {
                "before": before,
                "after_click": after_click,
                "dom_click": dom_click,
                "dispatch_click": dispatch_click,
                "awaited": awaited,
                "after_await": after_await,
                "requests_seen": requests_seen,
            }
            browser.close()

        print(json.dumps(result, indent=2))
        return 0
    finally:
        try:
            os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
