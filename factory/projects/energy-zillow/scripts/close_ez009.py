#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "queue.yaml"
DECISION_LOG = ROOT / "decision-log.md"


def update_queue(queue_path: Path) -> bool:
    lines = queue_path.read_text(encoding="utf-8").splitlines()
    out = []

    in_ez009 = False
    updated_status = False
    updated_ts = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("updated_at:"):
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            out.append(f"updated_at: {ts}")
            updated_ts = True
            continue

        if stripped.startswith("- id: EZ-009") or stripped.startswith("id: EZ-009"):
            in_ez009 = True
            out.append(line)
            continue

        if in_ez009 and stripped.startswith("- id:") and "EZ-009" not in stripped:
            in_ez009 = False

        if in_ez009 and stripped.startswith("status:"):
            indent = line[: len(line) - len(line.lstrip(" "))]
            out.append(f"{indent}status: done-local")
            updated_status = True
            continue

        out.append(line)

    if not updated_ts:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        out.insert(0, f"updated_at: {ts}")

    queue_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return updated_status


def append_decision_log(decision_log_path: Path, recording_name: str) -> None:
    marker = "EZ-009 closed"
    content = decision_log_path.read_text(encoding="utf-8")
    if marker in content:
        return

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    line = (
        f"- EZ-009 closed ({stamp}): demo recording captured (`{recording_name}`); "
        "narrative bundle complete and queue status moved to done-local."
    )
    decision_log_path.write_text(content.rstrip() + "\n" + line + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Close EZ-009 when recording artifact exists")
    p.add_argument("--recording", default="artifacts/demo-recording-v1.mp4")
    args = p.parse_args()

    recording_path = ROOT / args.recording
    if not recording_path.exists():
        print(f"missing recording: {recording_path}")
        return 1

    status_updated = update_queue(QUEUE)
    if not status_updated:
        print("warning: EZ-009 status line not found; queue left mostly unchanged")

    append_decision_log(DECISION_LOG, args.recording)
    print(f"EZ-009 closed with recording: {recording_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
