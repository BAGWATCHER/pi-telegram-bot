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
OUT = ROOT / "artifacts" / "ui-check"


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
    OUT.mkdir(parents=True, exist_ok=True)
    port = 8104
    base_url = f"http://127.0.0.1:{port}"
    app_url = f"{base_url}/"
    result: dict[str, object] = {"ok": False}
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
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            page = browser.new_page(viewport={"width": 1600, "height": 1100})
            page.goto(app_url, wait_until="networkidle", timeout=60000)
            page.wait_for_selector("#today-plan", timeout=30000)
            page.wait_for_function("document.querySelectorAll('#site-list-body tr').length > 0", timeout=30000)
            page.screenshot(path=str(OUT / "desktop-home.png"), full_page=False)

            mobile = browser.new_page(
                viewport={"width": 430, "height": 932},
                is_mobile=True,
                has_touch=True,
            )
            mobile.goto(app_url, wait_until="networkidle", timeout=60000)
            mobile.wait_for_selector("#today-plan", timeout=30000)
            mobile.wait_for_selector("#tab-list", timeout=30000)
            mobile.locator("#tab-list").click()
            mobile.wait_for_timeout(1200)
            mobile.screenshot(path=str(OUT / "mobile-workspace.png"), full_page=False)

            mobile.locator("#tab-map").click()
            mobile.wait_for_timeout(1200)
            mobile.screenshot(path=str(OUT / "mobile-map.png"), full_page=False)

            result = {
                "ok": True,
                "desktop": str(OUT / "desktop-home.png"),
                "mobile_workspace": str(OUT / "mobile-workspace.png"),
                "mobile_map": str(OUT / "mobile-map.png"),
            }
            browser.close()
    finally:
        try:
            os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        except Exception:
            pass

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
