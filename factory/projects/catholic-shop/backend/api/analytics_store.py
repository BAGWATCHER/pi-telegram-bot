"""
Analytics event store for Catholic Shop.
Writes JSONL to data/processed/analytics_events.jsonl with privacy guardrails.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
ANALYTICS_PATH = ROOT / "data" / "processed" / "analytics_events.jsonl"

_write_lock = threading.Lock()

# Fields to strip from payloads for privacy
_PRIVACY_BLACKLIST = {
    "password", "passwd", "token", "auth", "secret", "api_key", "apikey",
    "stripe", "credit_card", "card_number", "ccv", "cvv", "cvc",
    "authorization", "bearer", "access_token", "refresh_token",
    "private_key", "ssh_key", "credential",
}

# Maximum length for any string value before truncation
_MAX_STRING_LENGTH = 500


def _sanitize_value(value: Any, key: str = "") -> Any:
    """Recursively sanitize a value for privacy."""
    key_lower = str(key or "").lower()

    # Check if the key itself is blacklisted
    for bl in _PRIVACY_BLACKLIST:
        if bl in key_lower:
            return "[REDACTED]"

    if isinstance(value, str):
        return value[:_MAX_STRING_LENGTH]
    elif isinstance(value, dict):
        return {str(k): _sanitize_value(v, k) for k, v in value.items()}
    elif isinstance(value, list):
        return [_sanitize_value(item, key) for item in value]
    else:
        return value


def _sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize an entire payload dict."""
    out: Dict[str, Any] = {}
    for k, v in payload.items():
        key_lower = str(k).lower()
        if any(bl in key_lower for bl in _PRIVACY_BLACKLIST):
            out[k] = "[REDACTED]"
        else:
            out[k] = _sanitize_value(v, k)
    return out


def log_event(
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    path: Optional[str] = None,
    source: Optional[str] = "backend",
) -> Optional[str]:
    """
    Append a sanitized event to the JSONL analytics log.
    Returns the event_id on success, None on failure.
    Does NOT raise — tolerates write errors.
    """
    event_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    sanitized = _sanitize_payload(payload or {})

    record: Dict[str, Any] = {
        "event_id": event_id,
        "event_type": str(event_type),
        "timestamp": timestamp,
    }
    if session_id:
        record["session_id"] = str(session_id)[:200]
    if user_id:
        record["user_id"] = str(user_id)[:200]
    if path:
        record["path"] = str(path)[:500]
    if source:
        record["source"] = str(source)[:100]
    if sanitized:
        record["payload"] = sanitized

    line = json.dumps(record, default=str, separators=(",", ":"))
    line_bytes = (line + "\n").encode("utf-8", errors="replace")

    try:
        with _write_lock:
            ANALYTICS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(ANALYTICS_PATH, "ab") as f:
                f.write(line_bytes)
        return event_id
    except Exception:
        return None


def read_all_events() -> list:
    """Read all events from the JSONL file. Returns empty list on failure."""
    events = []
    if not ANALYTICS_PATH.exists():
        return events

    try:
        with open(ANALYTICS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return events


def compute_summary() -> Dict[str, Any]:
    """Compute summary statistics from stored events."""
    events = read_all_events()

    total = len(events)
    type_counts: Dict[str, int] = {}
    product_ids: Dict[str, int] = {}
    shop_ids: Dict[str, int] = {}
    recent_chat_queries: list = []
    recent_no_result_queries: list = []

    for ev in events:
        # Count by event_type
        et = str(ev.get("event_type") or "unknown")
        type_counts[et] = type_counts.get(et, 0) + 1

        pl = ev.get("payload") or {}

        # Track product IDs
        pid = str(pl.get("product_id") or "")
        if pid:
            product_ids[pid] = product_ids.get(pid, 0) + 1

        # Track shop IDs
        sid = str(pl.get("shop_id") or "")
        if sid:
            shop_ids[sid] = shop_ids.get(sid, 0) + 1

        # Recent chat queries
        if et == "chat_message":
            msg = str(pl.get("message") or "")
            if msg:
                recent_chat_queries.append({
                    "event_id": ev.get("event_id"),
                    "timestamp": ev.get("timestamp"),
                    "message": msg[:_MAX_STRING_LENGTH],
                    "conversation_id": pl.get("conversation_id"),
                })

        # No-result queries from AI recommend with 0 results
        if et == "ai_recommend":
            rc = pl.get("result_count")
            if rc is not None and int(rc) == 0:
                recent_no_result_queries.append({
                    "event_id": ev.get("event_id"),
                    "timestamp": ev.get("timestamp"),
                    "intent": str(pl.get("intent") or "")[:_MAX_STRING_LENGTH],
                })

    # Top N by count
    top_products = sorted(product_ids.items(), key=lambda x: -x[1])[:10]
    top_shops = sorted(shop_ids.items(), key=lambda x: -x[1])[:10]

    # Most recent chat queries (last 20)
    recent_chat_queries.sort(key=lambda x: str(x.get("timestamp") or ""), reverse=True)
    recent_chat_queries = recent_chat_queries[:20]

    # Most recent no-result queries (last 20)
    recent_no_result_queries.sort(key=lambda x: str(x.get("timestamp") or ""), reverse=True)
    recent_no_result_queries = recent_no_result_queries[:20]

    return {
        "total_events": total,
        "event_type_counts": type_counts,
        "top_product_ids": [{"product_id": pid, "count": cnt} for pid, cnt in top_products],
        "top_shop_ids": [{"shop_id": sid, "count": cnt} for sid, cnt in top_shops],
        "recent_chat_queries": recent_chat_queries,
        "recent_no_result_queries": recent_no_result_queries,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
