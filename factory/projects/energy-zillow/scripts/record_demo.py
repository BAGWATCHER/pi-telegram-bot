#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


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


def wait_health(url: str, timeout_s: int = 45) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url.rstrip("/") + "/health", timeout=2)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"server did not become healthy in {timeout_s}s: {url}/health")


def ffmpeg_convert(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dst),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
    p = argparse.ArgumentParser(description="Auto-record Energy Zillow demo via Playwright")
    p.add_argument("--base-url", default="http://127.0.0.1:8099")
    p.add_argument("--port", type=int, default=8099)
    p.add_argument("--output", default="artifacts/demo-recording-v1.mp4")
    p.add_argument("--zips", default="78701,78702")
    p.add_argument("--solar-model", default="pvwatts-cell-blend", choices=["proxy", "pvwatts-cell-blend"])
    p.add_argument("--skip-prep", action="store_true")
    args = p.parse_args()

    env = load_env_file(ROOT / ".env")

    if not args.skip_prep:
        # best-effort key check; don't block proxy mode fallback path
        try:
            run(["python3", "scripts/check_pvwatts_key.py"], env=env)
        except subprocess.CalledProcessError:
            if args.solar_model == "pvwatts-cell-blend":
                print("[record_demo] key check failed; falling back to proxy")
                args.solar_model = "proxy"

        run(
            [
                "python3",
                "eval/run_multi_zip_regression.py",
                "--zips",
                args.zips,
                "--min-records-per-zip",
                "80",
                "--solar-model",
                args.solar_model,
            ],
            env=env,
        )

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

    tmp_video_dir = Path(tempfile.mkdtemp(prefix="energy-zillow-video-"))
    video_path = None

    try:
        wait_health(args.base_url)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1600, "height": 900},
                record_video_dir=str(tmp_video_dir),
                record_video_size={"width": 1600, "height": 900},
            )
            page = context.new_page()
            page.goto(args.base_url, wait_until="networkidle", timeout=60000)

            page.wait_for_selector("#zip-select", timeout=30000)
            page.wait_for_function("document.querySelectorAll('#zip-select option').length > 0", timeout=30000)
            page.wait_for_timeout(1500)

            # Let auto-loaded first hex/site render.
            page.wait_for_function("document.querySelectorAll('#site-list-body tr').length > 0", timeout=30000)
            page.wait_for_timeout(1200)

            # Interact with rows to show detail updates.
            rows = page.locator("#site-list-body tr")
            count = rows.count()
            if count > 0:
                rows.nth(0).click()
                page.wait_for_timeout(900)
            if count > 1:
                rows.nth(1).click()
                page.wait_for_timeout(900)
            if count > 2:
                rows.nth(2).click()
                page.wait_for_timeout(900)

            # Switch ZIP if available to demonstrate multi-area flow.
            options = page.locator("#zip-select option")
            opt_count = options.count()
            if opt_count > 1:
                value = options.nth(1).get_attribute("value")
                if value:
                    page.select_option("#zip-select", value=value)
                    page.wait_for_timeout(2200)

            # Reload action.
            page.click("#reload-btn")
            page.wait_for_timeout(2000)

            # Small map movement for visible activity.
            page.mouse.move(1180, 320)
            page.mouse.wheel(0, -600)
            page.wait_for_timeout(1000)
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(1200)

            video = page.video
            page.close()
            context.close()
            browser.close()

            if video is None:
                raise RuntimeError("Playwright did not produce video handle")
            video_path = Path(video.path())

        if video_path is None or not video_path.exists():
            raise RuntimeError("Recorded video file missing")

        out_mp4 = ROOT / args.output
        ffmpeg_convert(video_path, out_mp4)

        raw_copy = out_mp4.with_suffix(".webm")
        shutil.copy2(video_path, raw_copy)

        print(f"recorded: {out_mp4}")
        print(f"raw: {raw_copy}")
        return 0

    except PlaywrightTimeoutError as e:
        print(f"recording failed: timeout: {e}")
        return 1
    except Exception as e:
        print(f"recording failed: {e}")
        return 1
    finally:
        try:
            os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        except Exception:
            pass
        try:
            shutil.rmtree(tmp_video_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
