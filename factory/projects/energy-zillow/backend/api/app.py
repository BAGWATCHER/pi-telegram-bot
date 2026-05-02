from __future__ import annotations

import csv
import imaplib
import io
import json
import math
import os
import re
import subprocess
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import h3
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
BOT_ROOT = ROOT.parents[2]
SITE_SCORES_CSV = ROOT / "data/processed/site_scores.csv"
SITES_CSV = ROOT / "data/processed/sites.csv"
PROPERTY_TRIGGERS_CSV = ROOT / "data/processed/property_triggers.csv"
ZIP_PRIORITY_CSV = ROOT / "artifacts/new-england-zip-priority.csv"
OPERATOR_STATUS_JSON = ROOT / "data/processed/operator_status.json"
LEAD_OUTCOME_JSON = ROOT / "data/processed/lead_outcomes.json"
LEAD_CONTACTS_JSON = ROOT / "data/processed/lead_contacts.json"
LEAD_INTERACTIONS_JSON = ROOT / "data/processed/lead_interactions.json"
COMPILED_PLAYBOOKS_JSON = ROOT / "data/processed/compiled_playbooks.json"
OUTREACH_JOBS_JSON = ROOT / "data/processed/outreach_jobs.json"
CALLING_SESSIONS_JSON = ROOT / "data/processed/calling_sessions.json"
ORCHESTRATOR_RUNS_JSON = ROOT / "data/processed/orchestrator_runs.json"
LEARNING_JOBS_JSON = ROOT / "data/processed/learning_jobs.json"
AGENT_TASKS_JSON = ROOT / "data/processed/agent_tasks.json"
EMAIL_THREADS_JSON = ROOT / "data/processed/email_threads.json"
MAILBOX_SYNC_STATE_JSON = ROOT / "data/processed/mailbox_sync_state.json"
FRONTEND_INDEX = ROOT / "frontend/index.html"
OUTREACH_POLICY_JSON = ROOT / "config/outreach_policy.json"
GOVERNANCE_POLICY_JSON = ROOT / "config/governance_policy.json"
DISPATCH_ADAPTERS_JSON = ROOT / "config/dispatch_adapters.json"
PILOT_SCOPE_JSON = ROOT / "config/pilot_scope.json"
DEMANDGRID_PI_AGENT_SCRIPT = BOT_ROOT / "scripts" / "demandgrid_pi_reply.ts"
DEMANDGRID_PI_PROVIDER = os.environ.get("DEMANDGRID_PI_PROVIDER", "openai-codex").strip() or "openai-codex"
DEMANDGRID_PI_MODEL = os.environ.get("DEMANDGRID_PI_MODEL", "gpt-5.4").strip() or "gpt-5.4"
DEMANDGRID_PI_THINKING = os.environ.get("DEMANDGRID_PI_THINKING", "medium").strip() or "medium"
RESEND_API_BASE = "https://api.resend.com/emails"
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
EMAIL_FROM = os.environ.get("EMAIL_FROM", "").strip()
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO", "").strip()
MAILBOX_PROVIDER = os.environ.get("MAILBOX_PROVIDER", "manual").strip() or "manual"
MAILBOX_IMAP_HOST = os.environ.get("MAILBOX_IMAP_HOST", "").strip()
MAILBOX_IMAP_PORT = os.environ.get("MAILBOX_IMAP_PORT", "993").strip() or "993"
MAILBOX_IMAP_USERNAME = os.environ.get("MAILBOX_IMAP_USERNAME", "").strip()
MAILBOX_IMAP_PASSWORD = os.environ.get("MAILBOX_IMAP_PASSWORD", "").strip()
MAILBOX_IMAP_MAILBOX = os.environ.get("MAILBOX_IMAP_MAILBOX", "INBOX").strip() or "INBOX"

ALLOWED_OPERATOR_STATUSES = {"unworked", "visited", "contacted", "follow_up", "closed", "skip"}
ALLOWED_LEAD_OUTCOME_STATUSES = {"unknown", "contacted", "responded", "qualified", "won", "lost"}
AGENT_FRAMEWORK = "pi-tool-router-v1"
CHOW_AGENT_FRAMEWORK = "dg-chow-mode-v1"
INVESTIGATION_FRAMEWORK = "pi-investigation-v1"
OUTREACH_FRAMEWORK = "pi-outreach-router-v1"
PLAYBOOK_COMPILER_FRAMEWORK = "dg-playbook-compiler-v1"
OUTREACH_AGENT_FRAMEWORK = "dg-agent-outreach-v1"
CALLING_AGENT_FRAMEWORK = "dg-agent-calling-v1"
VOICE_AGENT_FRAMEWORK = "dg-voice-bridge-v1"
ORCHESTRATOR_FRAMEWORK = "dg-orchestrator-v1"
LEARNING_FRAMEWORK = "dg-learning-loop-v1"
DEFAULT_AUTO_OUTREACH_CONFIDENCE_MIN = 0.65
DEFAULT_OUTREACH_POLICY: Dict[str, Any] = {
    "version": "2026-04-17-v1",
    "default": {
        "confidence_min": DEFAULT_AUTO_OUTREACH_CONFIDENCE_MIN,
        "confidence_high_min": 0.82,
        "channel_map": {
            "hot": "phone",
            "warm": "email",
            "cold": "partner",
            "skip": "review",
            "default": "email",
        },
        "block_operator_statuses": ["closed", "skip"],
        "block_lead_temperatures": ["skip"],
        "block_risk_flags": [],
        "review_risk_flags": ["requires_site_survey", "proxy_only_readiness", "multi_address_merged"],
    },
    "products": {
        "solar": {
            "confidence_min": 0.62,
            "confidence_high_min": 0.82,
            "channel_map": {"hot": "phone", "warm": "email", "default": "email"},
        },
        "roofing": {
            "confidence_min": 0.67,
            "confidence_high_min": 0.84,
            "channel_map": {"hot": "phone", "warm": "email", "default": "email"},
        },
        "hvac_heat_pump": {
            "confidence_min": 0.60,
            "confidence_high_min": 0.79,
            "channel_map": {"hot": "phone", "warm": "sms", "default": "email"},
        },
        "battery_backup": {
            "confidence_min": 0.68,
            "confidence_high_min": 0.85,
            "channel_map": {"hot": "phone", "warm": "phone", "default": "email"},
        },
    },
}
DEFAULT_GOVERNANCE_POLICY: Dict[str, Any] = {
    "version": "2026-04-18-v1",
    "approvals": {
        "roles_allowed": {
            "create_outreach_job": ["manager", "owner", "admin"],
            "create_calling_session": ["manager", "owner", "admin"],
            "default": ["manager", "owner", "admin"],
        },
        "require_actor_id": True,
    },
    "autonomy": {
        "allow_auto_execute_when_approval_required": False,
        "require_audit_record": True,
    },
    "manager_command": {
        "risk_alert_thresholds": {
            "low_attribution_pct": 60.0,
            "low_confidence": 0.65,
        }
    },
}
DEFAULT_DISPATCH_ADAPTER_POLICY: Dict[str, Any] = {
    "version": "2026-04-22-v1",
    "supervision": {
        "require_actor_id": True,
        "roles_allowed": {
            "email": ["manager", "owner", "admin"],
            "calling": ["manager", "owner", "admin"],
            "default": ["manager", "owner", "admin"],
        },
    },
    "email": {
        "enabled": True,
        "allow_live_dispatch": True,
        "default_provider": "resend",
        "providers": {
            "resend": {
                "mode": "live_api",
                "label": "Resend email adapter",
            },
            "mock": {
                "mode": "mock",
                "label": "Mock email adapter",
            },
            "disabled": {
                "mode": "disabled",
                "label": "Disabled email adapter",
            },
        },
    },
    "calling": {
        "enabled": True,
        "allow_live_dispatch": False,
        "default_provider": "mock",
        "providers": {
            "mock": {
                "mode": "mock",
                "label": "Mock calling adapter",
            },
            "disabled": {
                "mode": "disabled",
                "label": "Disabled calling adapter",
            },
        },
    },
}

app = FastAPI(title="DemandGrid API", version="0.1.0")


class OperatorStatusPayload(BaseModel):
    status: str
    note: str | None = None


class LeadOutcomePayload(BaseModel):
    status: str
    note: str | None = None
    objection: str | None = None
    reason: str | None = None
    product: str | None = None
    realized_revenue_usd: float | None = None
    realized_profit_usd: float | None = None


class AgentChatPayload(BaseModel):
    message: str
    zip: str | None = None
    h3_cell: str | None = None
    site_id: str | None = None
    max_results: int = 8


class AgentTaskClaimPayload(BaseModel):
    agent_id: str | None = None
    actor_role: str = "agent"
    note: str | None = None


class AgentTaskResultPayload(BaseModel):
    status: str
    note: str | None = None
    operator_status: str | None = None
    outcome_status: str | None = None
    channel: str = "workspace"
    interaction_type: str = "agent_task"
    next_follow_up_at: str | None = None
    next_best_action: str | None = None
    objection: str | None = None
    reason: str | None = None
    product: str | None = None
    realized_revenue_usd: float | None = None
    realized_profit_usd: float | None = None
    agent_id: str | None = None


class LeadContactPayload(BaseModel):
    entity_type: str | None = None
    role: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    organization_name: str | None = None
    owner_occupancy: str | None = None
    residency_confidence: float | None = None
    preferred_channel: str | None = None
    contactability_score: float | None = None
    contactability_label: str | None = None
    do_not_contact: bool | None = None
    primary_phone: str | None = None
    phone_numbers: List[str] | None = None
    primary_email: str | None = None
    emails: List[str] | None = None
    website_url: str | None = None
    contact_form_url: str | None = None
    mailing_address: str | None = None
    contact_paths: List[Dict[str, Any]] | None = None
    best_contact_window: str | None = None
    dedupe_key: str | None = None
    identity_sources: List[str] | None = None
    source_record_ids: List[str] | None = None
    verified_at: str | None = None
    freshness_days: int | None = None
    notes: str | None = None


class LeadInteractionCreatePayload(BaseModel):
    site_id: str
    contact_id: str | None = None
    channel: str
    direction: str | None = None
    interaction_type: str
    started_at: str | None = None
    ended_at: str | None = None
    result_status: str
    objection: str | None = None
    reason: str | None = None
    transcript_excerpt: str | None = None
    note: str | None = None
    script_id: str | None = None
    playbook_id: str | None = None
    orchestrator_run_id: str | None = None
    outreach_job_id: str | None = None
    calling_session_id: str | None = None
    outcome_id: str | None = None
    next_follow_up_at: str | None = None
    next_best_action: str | None = None
    rep_id: str | None = None
    agent_id: str | None = None
    attribution_signal_keys: List[str] | None = None


class PlaybookCompilePayload(BaseModel):
    site_id: str
    objective: str | None = None
    execution_mode: str = "rep_assist"
    preferred_channels: List[str] | None = None
    strict_guardrails: bool = True


class OutreachJobCreatePayload(BaseModel):
    site_id: str
    playbook_id: str | None = None
    idempotency_key: str | None = None
    requested_channel: str | None = None
    execution_mode: str = "agent_assist"
    objective: str | None = None
    preferred_channels: List[str] | None = None
    strict_guardrails: bool = True
    dry_run: bool = True


class OutreachJobEventPayload(BaseModel):
    job_id: str
    event_type: str
    detail: str | None = None
    provider_message_id: str | None = None
    event_at: str | None = None
    metadata: Dict[str, Any] | None = None


class CallingSessionCreatePayload(BaseModel):
    site_id: str
    playbook_id: str | None = None
    execution_mode: str = "agent_assist"
    objective: str | None = None
    preferred_channels: List[str] | None = None
    strict_guardrails: bool = True
    call_direction: str = "outbound"


class CallingSessionEventPayload(BaseModel):
    session_id: str
    event_type: str
    detail: str | None = None
    event_at: str | None = None
    transcript_excerpt: str | None = None
    objection: str | None = None
    outcome_status: str | None = None
    reason: str | None = None
    realized_revenue_usd: float | None = None
    realized_profit_usd: float | None = None
    metadata: Dict[str, Any] | None = None


class DispatchRequestPayload(BaseModel):
    actor_id: str
    actor_role: str = "manager"
    note: str | None = None
    provider: str | None = None
    promote_to_live: bool = False


class InboxMessagePayload(BaseModel):
    external_message_id: str | None = None
    provider_message_id: str | None = None
    direction: str = "inbound"
    from_email: str | None = None
    to_emails: List[str] | None = None
    cc_emails: List[str] | None = None
    bcc_emails: List[str] | None = None
    subject: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    sent_at: str | None = None
    received_at: str | None = None
    in_reply_to: str | None = None
    references: List[str] | None = None
    metadata: Dict[str, Any] | None = None


class InboxImportPayload(BaseModel):
    actor_id: str | None = None
    actor_role: str = "manager"
    source: str = "manual"
    thread_id: str | None = None
    outreach_job_id: str | None = None
    queue_id: str | None = None
    site_id: str | None = None
    mark_reply_received: bool = True
    messages: List[InboxMessagePayload]


class MailboxPollPayload(BaseModel):
    actor_id: str
    actor_role: str = "manager"
    provider: str | None = None
    mailbox: str | None = None
    limit: int = 20
    unseen_only: bool = True
    dry_run: bool = True


class VoiceCallStatusPayload(BaseModel):
    site_id: str
    session_id: str | None = None
    provider_call_id: str | None = None
    status: str
    detail: str | None = None
    transcript_excerpt: str | None = None
    metadata: Dict[str, Any] | None = None


class VoiceCallResultPayload(BaseModel):
    site_id: str
    session_id: str | None = None
    provider_call_id: str | None = None
    disposition: str
    detail: str | None = None
    transcript_excerpt: str | None = None
    objection: str | None = None
    reason: str | None = None
    outcome_status: str | None = None
    callback_at: str | None = None
    needs_human: bool = False
    next_best_action: str | None = None
    human_transfer_target: str | None = None
    realized_revenue_usd: float | None = None
    realized_profit_usd: float | None = None
    metadata: Dict[str, Any] | None = None


class OrchestratorRunCreatePayload(BaseModel):
    site_id: str
    idempotency_key: str | None = None
    approval_required: bool = True
    auto_execute: bool = False
    execution_mode: str = "agent_assist"
    objective: str | None = None
    preferred_channels: List[str] | None = None
    strict_guardrails: bool = True
    call_direction: str = "outbound"


class OrchestratorActionApprovalPayload(BaseModel):
    approver: str
    actor_role: str = "manager"
    note: str | None = None


class GovernanceValidationPayload(BaseModel):
    run_id: str
    action_id: str
    actor_id: str
    actor_role: str = "manager"


class OutcomeWritePayload(BaseModel):
    site_id: str
    status: str
    note: str | None = None
    objection: str | None = None
    reason: str | None = None
    product: str | None = None
    realized_revenue_usd: float | None = None
    realized_profit_usd: float | None = None
    attribution_channel: str | None = None
    attribution_playbook_id: str | None = None
    attribution_orchestrator_run_id: str | None = None
    attribution_signal_keys: List[str] | None = None
    attribution_source_session_id: str | None = None
    attribution_source_job_id: str | None = None


class LearningRetrainJobPayload(BaseModel):
    dry_run: bool = True
    minimum_outcomes: int = 5
    minimum_attribution_completeness_pct: float = 60.0
    approver: str | None = None
    note: str | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge_dict(out.get(key) or {}, value)
        else:
            out[key] = value
    return out


@lru_cache(maxsize=1)
def _pilot_scope_config() -> Dict[str, Any]:
    default = {
        "pilot_id": "default",
        "label": "DemandGrid Pilot",
        "summary": "Current focused DemandGrid pilot scope.",
        "primary_zip": None,
        "zips": [],
        "chat_example_zip": None,
    }
    if not PILOT_SCOPE_JSON.exists():
        return default
    try:
        raw = json.loads(PILOT_SCOPE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return default
    if not isinstance(raw, dict):
        return default
    zips = [str(v).strip() for v in (raw.get("zips") or []) if str(v).strip()]
    primary_zip = str(raw.get("primary_zip") or "").strip() or (zips[0] if zips else None)
    chat_example_zip = str(raw.get("chat_example_zip") or "").strip() or primary_zip
    return {
        "pilot_id": str(raw.get("pilot_id") or "default").strip() or "default",
        "label": str(raw.get("label") or "DemandGrid Pilot").strip() or "DemandGrid Pilot",
        "summary": str(raw.get("summary") or "Current focused DemandGrid pilot scope.").strip(),
        "primary_zip": primary_zip,
        "zips": zips,
        "chat_example_zip": chat_example_zip,
    }


@lru_cache(maxsize=1)
def _outreach_policy_config() -> Dict[str, Any]:
    policy = _deep_merge_dict(DEFAULT_OUTREACH_POLICY, {})
    source = "default"
    if OUTREACH_POLICY_JSON.exists():
        try:
            loaded = json.loads(OUTREACH_POLICY_JSON.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                policy = _deep_merge_dict(policy, loaded)
                source = str(OUTREACH_POLICY_JSON)
        except Exception:
            source = "default_parse_error"
    policy["_source"] = source
    return policy


@lru_cache(maxsize=1)
def _governance_policy_config() -> Dict[str, Any]:
    policy = _deep_merge_dict(DEFAULT_GOVERNANCE_POLICY, {})
    source = "default"
    if GOVERNANCE_POLICY_JSON.exists():
        try:
            loaded = json.loads(GOVERNANCE_POLICY_JSON.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                policy = _deep_merge_dict(policy, loaded)
                source = str(GOVERNANCE_POLICY_JSON)
        except Exception:
            source = "default_parse_error"
    policy["_source"] = source
    return policy


@lru_cache(maxsize=1)
def _dispatch_adapter_config() -> Dict[str, Any]:
    policy = _deep_merge_dict(DEFAULT_DISPATCH_ADAPTER_POLICY, {})
    source = "default"
    if DISPATCH_ADAPTERS_JSON.exists():
        try:
            loaded = json.loads(DISPATCH_ADAPTERS_JSON.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                policy = _deep_merge_dict(policy, loaded)
                source = str(DISPATCH_ADAPTERS_JSON)
        except Exception:
            source = "default_parse_error"
    policy["_source"] = source
    return policy


def _effective_outreach_policy(primary_product: str | None) -> Dict[str, Any]:
    policy = _outreach_policy_config()
    default_cfg = dict(policy.get("default") or {})
    products_cfg = dict(policy.get("products") or {})
    key = str(primary_product or "").strip().lower()
    product_cfg = dict(products_cfg.get(key) or {})
    merged = _deep_merge_dict(default_cfg, product_cfg)

    confidence_min = _to_float(merged.get("confidence_min"), DEFAULT_AUTO_OUTREACH_CONFIDENCE_MIN)
    confidence_high_min = _to_float(merged.get("confidence_high_min"), max(confidence_min, 0.82))
    if confidence_high_min < confidence_min:
        confidence_high_min = confidence_min

    channel_map = merged.get("channel_map")
    if not isinstance(channel_map, dict):
        channel_map = dict(DEFAULT_OUTREACH_POLICY.get("default", {}).get("channel_map") or {})

    def _normalize_str_list(value: Any) -> List[str]:
        if not isinstance(value, list):
            return []
        return [str(v).strip() for v in value if str(v).strip()]

    return {
        "product": key or "default",
        "confidence_min": confidence_min,
        "confidence_high_min": confidence_high_min,
        "channel_map": channel_map,
        "block_operator_statuses": _normalize_str_list(merged.get("block_operator_statuses")),
        "block_lead_temperatures": _normalize_str_list(merged.get("block_lead_temperatures")),
        "block_risk_flags": _normalize_str_list(merged.get("block_risk_flags")),
        "review_risk_flags": _normalize_str_list(merged.get("review_risk_flags")),
        "policy_source": str(policy.get("_source") or "default"),
        "policy_version": str(policy.get("version") or DEFAULT_OUTREACH_POLICY.get("version") or "v1"),
    }


def _confidence_band(confidence: float, confidence_min: float, confidence_high_min: float) -> str:
    if confidence >= confidence_high_min:
        return "high"
    if confidence >= confidence_min:
        return "medium"
    return "low"


def _suppression_reasons_from_policy(
    *,
    confidence: float,
    lead_temperature: str,
    operator_status: str,
    risk_flags: List[str],
    policy: Dict[str, Any],
) -> List[str]:
    reasons: List[str] = []
    if confidence < _to_float(policy.get("confidence_min"), DEFAULT_AUTO_OUTREACH_CONFIDENCE_MIN):
        reasons.append("low_confidence")

    block_operator_statuses = {str(v).strip().lower() for v in (policy.get("block_operator_statuses") or [])}
    if str(operator_status or "").strip().lower() in block_operator_statuses:
        reasons.append(f"workflow_{operator_status}")

    block_lead_temperatures = {str(v).strip().lower() for v in (policy.get("block_lead_temperatures") or [])}
    if str(lead_temperature or "").strip().lower() in block_lead_temperatures:
        reasons.append(f"lead_{lead_temperature}")

    block_risk_flags = {str(v).strip().lower() for v in (policy.get("block_risk_flags") or [])}
    for risk_flag in risk_flags:
        if str(risk_flag).strip().lower() in block_risk_flags:
            reasons.append(f"risk_{risk_flag}")

    # Preserve order while deduplicating.
    return list(dict.fromkeys(reasons))


def _read_operator_status_store() -> Dict[str, Dict[str, Any]]:
    if not OPERATOR_STATUS_JSON.exists():
        return {}
    try:
        raw = json.loads(OPERATOR_STATUS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for site_id, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "unworked").strip()
        note = str(payload.get("note") or "").strip()
        updated_at = str(payload.get("updated_at") or "")
        if status not in ALLOWED_OPERATOR_STATUSES:
            status = "unworked"
        out[str(site_id)] = {"status": status, "note": note, "updated_at": updated_at or None}
    return out


def _write_operator_status_store(data: Dict[str, Dict[str, Any]]) -> None:
    OPERATOR_STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = OPERATOR_STATUS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OPERATOR_STATUS_JSON)


@lru_cache(maxsize=1)
def _operator_status_cache() -> Dict[str, Dict[str, Any]]:
    return _read_operator_status_store()


def _operator_status_for(site_id: str) -> Dict[str, Any]:
    status = _operator_status_cache().get(str(site_id), {})
    return {
        "status": status.get("status", "unworked"),
        "note": status.get("note", ""),
        "updated_at": status.get("updated_at"),
    }


def _read_lead_outcome_store() -> Dict[str, Dict[str, Any]]:
    if not LEAD_OUTCOME_JSON.exists():
        return {}
    try:
        raw = json.loads(LEAD_OUTCOME_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for site_id, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "unknown").strip()
        if status not in ALLOWED_LEAD_OUTCOME_STATUSES:
            status = "unknown"
        note = str(payload.get("note") or "").strip()
        objection = str(payload.get("objection") or "").strip()
        reason = str(payload.get("reason") or "").strip()
        product = str(payload.get("product") or "").strip()
        updated_at = str(payload.get("updated_at") or "")
        won_at = str(payload.get("won_at") or "")
        lost_at = str(payload.get("lost_at") or "")
        attribution_channel = str(payload.get("attribution_channel") or "").strip()
        attribution_playbook_id = str(payload.get("attribution_playbook_id") or "").strip()
        attribution_orchestrator_run_id = str(payload.get("attribution_orchestrator_run_id") or "").strip()
        attribution_source_session_id = str(payload.get("attribution_source_session_id") or "").strip()
        attribution_source_job_id = str(payload.get("attribution_source_job_id") or "").strip()
        signal_keys_raw = payload.get("attribution_signal_keys")
        attribution_signal_keys = []
        if isinstance(signal_keys_raw, list):
            attribution_signal_keys = [str(v).strip() for v in signal_keys_raw if str(v).strip()]
        revenue = payload.get("realized_revenue_usd")
        profit = payload.get("realized_profit_usd")
        try:
            revenue = float(revenue) if revenue not in (None, "", "None") else None
        except Exception:
            revenue = None
        try:
            profit = float(profit) if profit not in (None, "", "None") else None
        except Exception:
            profit = None
        out[str(site_id)] = {
            "status": status,
            "note": note,
            "objection": objection,
            "reason": reason,
            "product": product,
            "realized_revenue_usd": revenue,
            "realized_profit_usd": profit,
            "updated_at": updated_at or None,
            "won_at": won_at or None,
            "lost_at": lost_at or None,
            "attribution_channel": attribution_channel,
            "attribution_playbook_id": attribution_playbook_id,
            "attribution_orchestrator_run_id": attribution_orchestrator_run_id,
            "attribution_signal_keys": attribution_signal_keys,
            "attribution_source_session_id": attribution_source_session_id,
            "attribution_source_job_id": attribution_source_job_id,
        }
    return out


def _read_lead_contact_store() -> Dict[str, Dict[str, Any]]:
    if not LEAD_CONTACTS_JSON.exists():
        return {}
    try:
        raw = json.loads(LEAD_CONTACTS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for contact_id, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        out[str(contact_id)] = dict(payload)
    return out


def _write_lead_contact_store(data: Dict[str, Dict[str, Any]]) -> None:
    LEAD_CONTACTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEAD_CONTACTS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(LEAD_CONTACTS_JSON)


@lru_cache(maxsize=1)
def _lead_contact_cache() -> Dict[str, Dict[str, Any]]:
    return _read_lead_contact_store()


def _read_lead_interaction_store() -> Dict[str, Dict[str, Any]]:
    if not LEAD_INTERACTIONS_JSON.exists():
        return {}
    try:
        raw = json.loads(LEAD_INTERACTIONS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for interaction_id, payload in raw.items():
        if not isinstance(payload, dict):
            continue
        out[str(interaction_id)] = dict(payload)
    return out


def _write_lead_interaction_store(data: Dict[str, Dict[str, Any]]) -> None:
    LEAD_INTERACTIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEAD_INTERACTIONS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(LEAD_INTERACTIONS_JSON)


@lru_cache(maxsize=1)
def _lead_interaction_cache() -> Dict[str, Dict[str, Any]]:
    return _read_lead_interaction_store()


def _write_lead_outcome_store(data: Dict[str, Dict[str, Any]]) -> None:
    LEAD_OUTCOME_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEAD_OUTCOME_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(LEAD_OUTCOME_JSON)


@lru_cache(maxsize=1)
def _lead_outcome_cache() -> Dict[str, Dict[str, Any]]:
    return _read_lead_outcome_store()


def _lead_outcome_for(site_id: str) -> Dict[str, Any]:
    outcome = _lead_outcome_cache().get(str(site_id), {})
    return {
        "status": outcome.get("status", "unknown"),
        "note": outcome.get("note", ""),
        "objection": outcome.get("objection", ""),
        "reason": outcome.get("reason", ""),
        "product": outcome.get("product", ""),
        "realized_revenue_usd": outcome.get("realized_revenue_usd"),
        "realized_profit_usd": outcome.get("realized_profit_usd"),
        "updated_at": outcome.get("updated_at"),
        "won_at": outcome.get("won_at"),
        "lost_at": outcome.get("lost_at"),
        "attribution_channel": outcome.get("attribution_channel", ""),
        "attribution_playbook_id": outcome.get("attribution_playbook_id", ""),
        "attribution_orchestrator_run_id": outcome.get("attribution_orchestrator_run_id", ""),
        "attribution_signal_keys": outcome.get("attribution_signal_keys", []),
        "attribution_source_session_id": outcome.get("attribution_source_session_id", ""),
        "attribution_source_job_id": outcome.get("attribution_source_job_id", ""),
    }


def _owner_name_for_row(row: Dict[str, Any]) -> str:
    for key in ("owner_name", "owner", "owner1", "OWNER1"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    address = _clean_address_text(row.get("address"))
    return f"Owner for {address}" if address else "Owner"


def _owner_mailing_for_row(row: Dict[str, Any]) -> str:
    for key in ("owner_mailing_address", "own_addr", "OWN_ADDR", "mailing_address"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return _clean_address_text(row.get("address"))


def _default_contactability_score(row: Dict[str, Any], preferred_channel: str) -> float:
    score = 0.38
    mailing_address = _owner_mailing_for_row(row)
    if mailing_address:
        score += 0.17
    if preferred_channel in {"phone", "sms"}:
        score += 0.09
    confidence = max(0.0, min(1.0, float(row.get("confidence") or 0.0)))
    score += confidence * 0.2
    return round(min(score, 0.95), 3)


def _contactability_label(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def _default_contact_record(row: Dict[str, Any]) -> Dict[str, Any]:
    site_id = str(row.get("site_id") or "")
    account_id = _account_id_for_row(row)
    contact_id = _contact_id_for_row(row)
    investigation = _build_investigation_payload(_attach_operator_status(row))
    outreach = _build_outreach_payload(investigation)
    preferred_channel = str(outreach.get("recommended_channel") or "mail")
    owner_name = _owner_name_for_row(row)
    mailing_address = _owner_mailing_for_row(row)
    score = _default_contactability_score(row, preferred_channel)
    now = _utc_now_iso()
    contact_paths: List[Dict[str, Any]] = []
    if mailing_address:
        contact_paths.append({"type": "mailing_address", "value": mailing_address, "label": "Mailing address", "priority": 4})
    return {
        "contact_id": contact_id,
        "account_id": account_id,
        "site_id": site_id,
        "entity_type": "person",
        "role": "owner_operator_proxy",
        "display_name": owner_name,
        "first_name": None,
        "last_name": None,
        "organization_name": None,
        "owner_occupancy": "unknown",
        "residency_confidence": None,
        "preferred_channel": preferred_channel,
        "contactability_score": score,
        "contactability_label": _contactability_label(score),
        "do_not_contact": False,
        "primary_phone": None,
        "phone_numbers": [],
        "primary_email": None,
        "emails": [],
        "website_url": None,
        "contact_form_url": None,
        "contact_paths": contact_paths,
        "mailing_address": mailing_address or None,
        "best_contact_window": None,
        "dedupe_key": f"{site_id}:{_slug_token(owner_name)}",
        "identity_sources": ["site_proxy"],
        "source_record_ids": [site_id] if site_id else [],
        "verified_at": None,
        "freshness_days": None,
        "notes": "Bootstrap contact generated from current site/property record.",
        "created_at": now,
        "updated_at": now,
    }


def _contact_record_for_site(site_id: str) -> Dict[str, Any] | None:
    row = _data_cache().get("by_site", {}).get(str(site_id or ""))
    if not row:
        return None
    contact_id = _contact_id_for_row(row)
    return _lead_contact_for(contact_id, fallback_row=row)


def _lead_contact_for(contact_id: str, fallback_row: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    stored = _lead_contact_cache().get(str(contact_id))
    if isinstance(stored, dict):
        return dict(stored)
    row = fallback_row
    if row is None:
        rows = _data_cache().get("rows") or []
        row = next((r for r in rows if _contact_id_for_row(r) == str(contact_id)), None)
    if not row:
        return None
    return _default_contact_record(row)


def _persist_lead_contact(record: Dict[str, Any]) -> Dict[str, Any]:
    contact_id = str(record.get("contact_id") or "").strip()
    if not contact_id:
        raise HTTPException(status_code=400, detail="contact_id is required")
    store = _read_lead_contact_store()
    store[contact_id] = dict(record)
    _write_lead_contact_store(store)
    _lead_contact_cache.cache_clear()
    return dict(store[contact_id])


def _interactions_for_site(site_id: str) -> List[Dict[str, Any]]:
    interactions = [
        dict(item)
        for item in _lead_interaction_cache().values()
        if str(item.get("site_id") or "") == str(site_id or "")
    ]
    interactions.sort(key=lambda item: str(item.get("started_at") or ""), reverse=True)
    return interactions


def _calling_sessions_for_site(site_id: str) -> List[Dict[str, Any]]:
    sessions = [
        dict(item)
        for item in _calling_session_cache().values()
        if str(item.get("site_id") or "") == str(site_id or "")
    ]
    sessions.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
    return sessions


def _latest_calling_session_for_site(site_id: str) -> Dict[str, Any] | None:
    sessions = _calling_sessions_for_site(site_id)
    return dict(sessions[0]) if sessions else None


def _outreach_jobs_for_site(site_id: str) -> List[Dict[str, Any]]:
    jobs = [
        dict(item)
        for item in _outreach_job_cache().values()
        if str(item.get("site_id") or "") == str(site_id or "")
    ]
    jobs.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
    return jobs


def _latest_outreach_job_for_site(site_id: str) -> Dict[str, Any] | None:
    jobs = _outreach_jobs_for_site(site_id)
    return dict(jobs[0]) if jobs else None


def _orchestrator_runs_for_site(site_id: str) -> List[Dict[str, Any]]:
    runs = [
        dict(item)
        for item in _orchestrator_run_cache().values()
        if str(item.get("site_id") or "") == str(site_id or "")
    ]
    runs.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
    return runs


def _latest_orchestrator_run_for_site(site_id: str) -> Dict[str, Any] | None:
    runs = _orchestrator_runs_for_site(site_id)
    return dict(runs[0]) if runs else None


def _dispatch_adapter_descriptor(channel: str, provider: str | None = None) -> Dict[str, Any]:
    normalized_channel = _slug_token(channel).replace("-", "_") or "default"
    policy = _dispatch_adapter_config()
    channel_cfg = dict(policy.get(normalized_channel) or {})
    providers = dict(channel_cfg.get("providers") or {})
    default_provider = _slug_token(channel_cfg.get("default_provider") or "mock") or "mock"
    provider_key = _slug_token(provider or default_provider) or default_provider
    provider_cfg = dict(providers.get(provider_key) or providers.get(default_provider) or providers.get("mock") or {})
    mode = _slug_token(provider_cfg.get("mode") or provider_key).replace("-", "_") or "disabled"
    return {
        "channel": normalized_channel,
        "enabled": bool(channel_cfg.get("enabled", False)),
        "allow_live_dispatch": bool(channel_cfg.get("allow_live_dispatch", False)),
        "provider": provider_key,
        "mode": mode,
        "label": str(provider_cfg.get("label") or provider_key).strip() or provider_key,
        "config_source": str(policy.get("_source") or "default"),
        "policy_version": str(policy.get("version") or DEFAULT_DISPATCH_ADAPTER_POLICY.get("version") or "v1"),
    }


def _dispatch_actor_validation(payload: DispatchRequestPayload, channel: str) -> Dict[str, Any]:
    policy = _dispatch_adapter_config()
    supervision = dict(policy.get("supervision") or {})
    role_map = dict(supervision.get("roles_allowed") or {})
    normalized_channel = _slug_token(channel).replace("-", "_") or "default"
    normalized_role = _slug_token(payload.actor_role).replace("-", "_") or "unknown"
    actor_id = str(payload.actor_id or "").strip()
    allowed_roles = [
        str(v).strip().lower()
        for v in (role_map.get(normalized_channel) or role_map.get("default") or [])
        if str(v).strip()
    ]
    reasons: List[str] = []
    allowed = True
    if bool(supervision.get("require_actor_id", True)) and not actor_id:
        allowed = False
        reasons.append("missing_actor_id")
    if allowed_roles and normalized_role not in set(allowed_roles):
        allowed = False
        reasons.append(f"role_not_allowed:{normalized_role}")
    return {
        "allowed": allowed,
        "channel": normalized_channel,
        "actor_id": actor_id,
        "actor_role": normalized_role,
        "allowed_roles": allowed_roles,
        "reasons": reasons,
    }


def _resend_email_subject(job: Dict[str, Any], contact: Dict[str, Any]) -> str:
    site = dict(job.get("site") or {})
    product = str(site.get("primary_product") or "opportunity").strip().replace("_", " ")
    address = str(site.get("address") or "").strip()
    if address:
        return f"{product.title()} opportunity for {address}"
    return f"{product.title()} opportunity"


def _resend_email_text(job: Dict[str, Any], contact: Dict[str, Any]) -> str:
    site = dict(job.get("site") or {})
    send_context = dict(job.get("send_context") or {})
    product = str(site.get("primary_product") or "opportunity").strip().replace("_", " ")
    address = str(site.get("address") or "").strip()
    next_action = str(send_context.get("next_best_action") or "follow up").strip().replace("_", " ")
    hint = str(send_context.get("message_hint") or "").strip()
    recipient = (
        str(contact.get("display_name") or "").strip()
        or str(contact.get("organization_name") or "").strip()
        or "there"
    )
    lines = [
        f"Hi {recipient},",
        "",
        f"I am reaching out about a potential {product} opportunity{f' for {address}' if address else ''}.",
    ]
    if hint:
        lines.extend(["", hint])
    lines.extend(
        [
            "",
            f"The best next step from our side is to {next_action}.",
            "",
            "If this is relevant, reply here and we can coordinate the right next step.",
        ]
    )
    return "\n".join(lines).strip()


def _send_resend_email(*, to_email: str, subject: str, text: str) -> Dict[str, Any]:
    if not RESEND_API_KEY:
        raise HTTPException(status_code=409, detail="RESEND_API_KEY is not configured")
    if not EMAIL_FROM:
        raise HTTPException(status_code=409, detail="EMAIL_FROM is not configured")

    payload: Dict[str, Any] = {
        "from": EMAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "text": text,
    }
    if EMAIL_REPLY_TO:
        payload["reply_to"] = EMAIL_REPLY_TO

    request = urllib.request.Request(
        RESEND_API_BASE,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "DemandGrid/0.1 (+https://optimizedworkflow.dev)",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=409, detail={"message": "Resend rejected dispatch", "status": exc.code, "body": body})
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=409, detail={"message": "Resend request failed", "reason": str(exc.reason)})

    provider_message_id = str(data.get("id") or "").strip()
    if not provider_message_id:
        raise HTTPException(status_code=409, detail={"message": "Resend response missing message id", "body": data})
    return {"id": provider_message_id}


def _dispatch_resend_email(job: Dict[str, Any], adapter: Dict[str, Any], validation: Dict[str, Any], note: str, live_requested: bool) -> Dict[str, Any]:
    site_id = str(job.get("site_id") or "").strip()
    contact = _contact_record_for_site(site_id) or {}
    to_email = str(contact.get("primary_email") or "").strip()
    if not to_email:
        raise HTTPException(status_code=409, detail="Lead has no primary_email for live email dispatch")

    subject = _resend_email_subject(job, contact)
    body_text = _resend_email_text(job, contact)
    data = _send_resend_email(
        to_email=to_email,
        subject=subject,
        text=body_text,
    )
    provider_message_id = str(data.get("id") or "").strip()

    updated = dict(job)
    dispatch_state = dict(updated.get("dispatch") or {})
    event_log = list(updated.get("event_log") or [])
    event_at = _utc_now_iso()
    dispatch_state["status"] = "provider_accepted"
    dispatch_state["provider_message_id"] = provider_message_id
    dispatch_state["dispatched_at"] = event_at
    dispatch_state["provider_response"] = {"id": provider_message_id}
    updated["dispatch_mode"] = "supervised_live" if live_requested else str(updated.get("dispatch_mode") or "queued")
    updated["dispatch"] = dispatch_state
    updated["event_log"] = event_log
    updated = _apply_outreach_job_event(
        updated,
        OutreachJobEventPayload(
            job_id=str(updated.get("job_id") or ""),
            event_type="sent",
            detail=note or "Resend accepted the supervised dispatch request.",
            provider_message_id=provider_message_id,
            metadata={
                "provider": adapter.get("provider"),
                "provider_mode": adapter.get("mode"),
                "actor_id": validation.get("actor_id"),
                "actor_role": validation.get("actor_role"),
                "live_requested": live_requested,
                "to_email": to_email,
            },
        ),
    )
    thread = _record_outbound_email_thread(
        source="outreach_dispatch_resend",
        links=_outreach_job_email_links(updated),
        from_email=_normalize_email_address(EMAIL_REPLY_TO) or _normalize_email_address(EMAIL_FROM),
        to_emails=[to_email],
        subject=subject,
        body_text=body_text,
        provider_message_id=provider_message_id,
        event_at=event_at,
    )
    return _apply_inbox_summary(updated, thread)


def _execution_summary_for_site(site_id: str) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    task = _build_agent_task_payload(row)
    voice = _voice_ready_summary(site_id)
    latest_job = _latest_outreach_job_for_site(site_id)
    latest_session = _latest_calling_session_for_site(site_id)
    latest_run = _latest_orchestrator_run_for_site(site_id)
    email_adapter = _dispatch_adapter_descriptor("email")
    calling_adapter = _dispatch_adapter_descriptor("calling")
    pending_actions = [
        {
            "action_id": str(action.get("action_id") or ""),
            "action_type": str(action.get("action_type") or ""),
            "title": str(action.get("title") or ""),
            "status": str(action.get("status") or ""),
            "requires_approval": bool(action.get("requires_approval")),
            "resource_ref": action.get("resource_ref"),
        }
        for action in (latest_run.get("actions") or [])
        if str(action.get("status") or "") == "awaiting_approval"
    ] if latest_run else []

    blockers: List[str] = []
    if not bool(task.get("ready_for_supervised_outreach")):
        blockers.append("task_not_ready_for_supervised_outreach")
    if not bool(voice.get("voice_ready")) and not any(
        str(voice.get(key) or "").strip() for key in ["email", "contact_form_url", "website_url"]
    ):
        blockers.append("no_live_contact_path")
    if bool((latest_job or {}).get("policy", {}).get("block_reasons")):
        blockers.extend([str(v) for v in ((latest_job or {}).get("policy", {}).get("block_reasons") or []) if str(v).strip()])
    if not bool(calling_adapter.get("enabled")):
        blockers.append("calling_adapter_disabled")
    if not bool(email_adapter.get("enabled")):
        blockers.append("email_adapter_disabled")

    recommended_next_step = "prepare_supervised_run"
    if pending_actions:
        recommended_next_step = "approve_pending_actions"
    elif latest_session and str(latest_session.get("status") or "") == "ready":
        if str(((latest_session.get("dispatch") or {}).get("status") or "")).strip() in {"provider_queued", "provider_accepted", "dry_run_preview_ready"}:
            recommended_next_step = "log_supervised_call_result"
        else:
            recommended_next_step = "dispatch_supervised_call"
    elif latest_job and str(latest_job.get("status") or "") == "queued":
        if str(((latest_job.get("dispatch") or {}).get("status") or "")).strip() in {"provider_queued", "provider_accepted", "dry_run_preview_ready"}:
            recommended_next_step = "review_email_dispatch_state"
        else:
            recommended_next_step = "dispatch_email_preview"

    return {
        "framework": CHOW_AGENT_FRAMEWORK,
        "site_id": site_id,
        "task": task,
        "voice": voice,
        "calling_session": latest_session,
        "outreach_job": latest_job,
        "orchestrator_run": latest_run,
        "adapters": {
            "email": email_adapter,
            "calling": calling_adapter,
        },
        "supervision": {
            "ready_for_supervised_outreach": bool(task.get("ready_for_supervised_outreach")),
            "awaiting_approval": bool(pending_actions),
            "pending_actions": pending_actions,
            "blockers": list(dict.fromkeys([item for item in blockers if item])),
            "recommended_next_step": recommended_next_step,
        },
        "refs": {
            "create_run_ref": "/api/v1/orchestrator/runs",
            "approve_action_ref": "/api/v1/orchestrator/actions/{action_id}/approve",
            "calling_events_ref": "/api/v1/agents/calling/events",
            "outreach_events_ref": "/api/v1/agents/outreach/events",
            "dispatch_call_ref": "/api/v1/agents/calling/sessions/{session_id}/dispatch",
            "dispatch_outreach_ref": "/api/v1/agents/outreach/jobs/{job_id}/dispatch",
        },
    }


def _upsert_interaction_record(payload: LeadInteractionCreatePayload) -> Dict[str, Any]:
    site_id = str(payload.site_id or "").strip()
    row = _data_cache().get("by_site", {}).get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    contact = _lead_contact_for(str(payload.contact_id or "").strip(), fallback_row=row) if payload.contact_id else _contact_record_for_site(site_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Unable to resolve contact for site_id {site_id}")

    interaction_id = f"interaction_{_slug_token(site_id)}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    started_at = str(payload.started_at or "").strip() or _utc_now_iso()
    ended_at = str(payload.ended_at or "").strip() or None
    now = _utc_now_iso()
    record = {
        "interaction_id": interaction_id,
        "site_id": site_id,
        "contact_id": contact.get("contact_id"),
        "account_id": contact.get("account_id"),
        "channel": str(payload.channel or "").strip(),
        "direction": str(payload.direction or "").strip() or None,
        "interaction_type": str(payload.interaction_type or "").strip(),
        "started_at": started_at,
        "ended_at": ended_at,
        "result_status": str(payload.result_status or "").strip(),
        "objection": str(payload.objection or "").strip() or None,
        "reason": str(payload.reason or "").strip() or None,
        "transcript_excerpt": str(payload.transcript_excerpt or "").strip() or None,
        "note": str(payload.note or "").strip() or None,
        "script_id": str(payload.script_id or "").strip() or None,
        "playbook_id": str(payload.playbook_id or "").strip() or None,
        "orchestrator_run_id": str(payload.orchestrator_run_id or "").strip() or None,
        "outreach_job_id": str(payload.outreach_job_id or "").strip() or None,
        "calling_session_id": str(payload.calling_session_id or "").strip() or None,
        "outcome_id": str(payload.outcome_id or "").strip() or None,
        "next_follow_up_at": str(payload.next_follow_up_at or "").strip() or None,
        "next_best_action": str(payload.next_best_action or "").strip() or None,
        "rep_id": str(payload.rep_id or "").strip() or None,
        "agent_id": str(payload.agent_id or "").strip() or None,
        "attribution_signal_keys": [str(v).strip() for v in (payload.attribution_signal_keys or []) if str(v).strip()],
        "created_at": now,
        "updated_at": now,
    }
    store = _read_lead_interaction_store()
    store[interaction_id] = record
    _write_lead_interaction_store(store)
    _lead_interaction_cache.cache_clear()
    return dict(record)


def _lead_next_action_payload(site_id: str) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    row = _attach_operator_status(row)
    contact = _contact_record_for_site(site_id)
    interactions = _interactions_for_site(site_id)
    latest = interactions[0] if interactions else None
    decision = decision_site(site_id)
    recommended_channel = str((contact or {}).get("preferred_channel") or (decision.get("recommended_offer") or {}).get("recommended_channel") or "mail")
    action_type = str(decision.get("next_best_action") or row.get("operator_next_step") or "work_now")
    if action_type == "follow_up":
        normalized_action = "follow_up"
    elif action_type == "deprioritize":
        normalized_action = "suppress"
    else:
        normalized_action = "contact"
    return {
        "site_id": site_id,
        "contact_id": (contact or {}).get("contact_id"),
        "account_id": (contact or {}).get("account_id"),
        "action_type": normalized_action,
        "action_rank": 1,
        "reason": latest.get("next_best_action") if latest and latest.get("next_best_action") else f"Work the {row.get('primary_product')} lane now based on current score and workflow state.",
        "confidence": round(float(row.get("confidence") or 0.0), 3),
        "recommended_channel": recommended_channel,
        "recommended_script_angle": str(row.get("operator_pitch_angle") or row.get("recommended_pitch") or "").strip() or None,
        "recommended_timing": latest.get("next_follow_up_at") if latest else None,
        "recommended_sequence_step": decision.get("next_best_action"),
        "expected_value_usd": row.get("gross_profit_estimate_usd") or row.get("estimated_profit_usd") or row.get("annual_savings_usd"),
        "risk_flags": list((_build_investigation_payload(row).get("review_flags") or [])),
        "review_required": bool((_build_investigation_payload(row).get("review_flags") or [])),
        "policy_decision": "manual_review" if bool((contact or {}).get("do_not_contact")) else "allow",
        "source_refs": [
            f"/api/v1/decision/site/{site_id}",
            f"/api/v1/revenue-graph/site/{site_id}",
        ],
        "generated_at": _utc_now_iso(),
        "expires_at": None,
    }


def _agent_task_id_for_site(site_id: str) -> str:
    return f"task_{_slug_token(site_id)}"


def _agent_task_row_from_id(task_id: str) -> Dict[str, Any]:
    site_id = str(task_id or "").strip()
    if site_id.startswith("task_"):
        site_id = site_id[5:]
    row = _data_cache().get("by_site", {}).get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown task_id {task_id}")
    return row


def _agent_task_primary_action(row: Dict[str, Any], contact: Dict[str, Any], voice_readiness: Dict[str, Any]) -> str:
    work_queue = row.get("work_queue") or {}
    queue_bucket = str(work_queue.get("bucket") or "park").strip().lower()
    if queue_bucket == "verify_first":
        return "verify_lead"
    if str((row.get("operator_status") or {}).get("status") or "").strip().lower() == "follow_up":
        return "follow_up"
    if bool(voice_readiness.get("voice_ready")):
        return "queue_call"
    if str(contact.get("primary_email") or "").strip() or str(contact.get("contact_form_url") or "").strip() or str(contact.get("website_url") or "").strip():
        return "queue_email"
    if queue_bucket == "work_now":
        return "research_contact"
    return "review"


def _agent_task_action_options(row: Dict[str, Any], contact: Dict[str, Any], voice_readiness: Dict[str, Any]) -> List[str]:
    options = ["open_lead"]
    if bool(voice_readiness.get("voice_ready")):
        options.append("queue_call")
    if str(contact.get("primary_email") or "").strip() or str(contact.get("contact_form_url") or "").strip() or str(contact.get("website_url") or "").strip():
        options.append("queue_email")
    if str((row.get("work_queue") or {}).get("bucket") or "").strip().lower() == "verify_first":
        options.append("verify_lead")
    options.extend(["log_result", "next_lead"])
    return list(dict.fromkeys(options))


def _build_agent_task_payload(row: Dict[str, Any], *, zip: str | None = None, h3_cell: str | None = None) -> Dict[str, Any]:
    row = _attach_operator_status(row)
    site_id = str(row.get("site_id") or "")
    task_id = _agent_task_id_for_site(site_id)
    contact = _contact_record_for_site(site_id) or {}
    voice_readiness = _voice_ready_summary(site_id)
    next_action = _lead_next_action_payload(site_id)
    work_queue = row.get("work_queue") or {}
    existing = _agent_task_for(task_id) or {}
    primary_action = _agent_task_primary_action(row, contact, voice_readiness)
    available_actions = _agent_task_action_options(row, contact, voice_readiness)
    ready_for_supervised_outreach = primary_action in {"queue_call", "queue_email", "follow_up"} and str((row.get("operator_status") or {}).get("status") or "unworked") not in {"closed", "skip"}
    ready_reasons: List[str] = []
    if primary_action == "queue_call" and voice_readiness.get("voice_ready"):
        ready_reasons.append("voice_ready")
    if primary_action == "queue_email" and (str(contact.get("primary_email") or "").strip() or str(contact.get("contact_form_url") or "").strip() or str(contact.get("website_url") or "").strip()):
        ready_reasons.append("digital_contact_path")
    if str((row.get("work_queue") or {}).get("bucket") or "").strip().lower() == "work_now":
        ready_reasons.append("work_now_queue")
    return {
        "framework": CHOW_AGENT_FRAMEWORK,
        "task_id": task_id,
        "site_id": site_id,
        "scope": {"zip": zip, "h3_cell": h3_cell},
        "status": str(existing.get("status") or "ready"),
        "claimed_by": existing.get("claimed_by"),
        "claimed_at": existing.get("claimed_at"),
        "completed_at": existing.get("completed_at"),
        "updated_at": existing.get("updated_at"),
        "primary_action": primary_action,
        "available_actions": available_actions,
        "ready_for_supervised_outreach": ready_for_supervised_outreach,
        "ready_reasons": ready_reasons,
        "site": _site_card(row),
        "work_queue": work_queue,
        "next_action": next_action,
        "contact": {
            "contact_id": contact.get("contact_id"),
            "display_name": contact.get("display_name"),
            "preferred_channel": contact.get("preferred_channel"),
            "contactability_score": contact.get("contactability_score"),
            "contactability_label": contact.get("contactability_label"),
            "primary_phone": contact.get("primary_phone"),
            "primary_email": contact.get("primary_email"),
            "contact_form_url": contact.get("contact_form_url"),
            "website_url": contact.get("website_url"),
        },
        "voice": {
            "voice_ready": voice_readiness.get("voice_ready"),
            "phone_number": voice_readiness.get("phone_number"),
            "fallback_channel": voice_readiness.get("fallback_channel"),
            "missing_requirements": voice_readiness.get("missing_requirements") or [],
        },
        "refs": {
            "lead_ref": f"/api/v1/site/{site_id}",
            "task_result_ref": f"/api/v1/agent/tasks/{task_id}/result",
            "task_claim_ref": f"/api/v1/agent/tasks/{task_id}/claim",
            "call_ref": "/api/v1/agents/calling/sessions",
            "outreach_ref": "/api/v1/agents/outreach/jobs",
        },
    }


def _scored_agent_task_rows(zip: str | None = None, h3_cell: str | None = None) -> List[Dict[str, Any]]:
    rows = _scoped_rows(zip, h3_cell)
    rows = [
        _attach_operator_status(row)
        for row in rows
        if str((row.get("operator_status") or {}).get("status") or "unworked").strip().lower() not in {"closed", "skip"}
    ]
    bucket_order = {"work_now": 0, "follow_up": 1, "verify_first": 2, "park": 3}
    rows.sort(
        key=lambda r: (
            bucket_order.get(str(((r.get("work_queue") or {}).get("bucket") or "park")).strip().lower(), 9),
            -int(((r.get("work_queue") or {}).get("rank") or 0)),
            -_route_priority_score(r),
            -float(r.get("annual_savings_usd") or 0.0),
            str(r.get("site_id") or ""),
        )
    )
    return rows


def _next_agent_task(zip: str | None = None, h3_cell: str | None = None, agent_id: str | None = None) -> Dict[str, Any] | None:
    claimed_by = str(agent_id or "").strip()
    if claimed_by:
        for task in _agent_task_cache().values():
            if str(task.get("claimed_by") or "").strip() != claimed_by:
                continue
            if str(task.get("status") or "").strip() not in {"claimed", "ready"}:
                continue
            site_id = str(task.get("site_id") or "").strip()
            row = _data_cache().get("by_site", {}).get(site_id)
            if row:
                return _build_agent_task_payload(row, zip=zip, h3_cell=h3_cell)
    rows = _scored_agent_task_rows(zip, h3_cell)
    return _build_agent_task_payload(rows[0], zip=zip, h3_cell=h3_cell) if rows else None


def _ensure_calling_session(site_id: str, session_id: str | None = None) -> Dict[str, Any]:
    if str(session_id or "").strip():
        existing = _calling_session_for(str(session_id))
        if not existing:
            raise HTTPException(status_code=404, detail=f"Unknown calling session {session_id}")
        return existing
    existing = _latest_calling_session_for_site(site_id)
    if existing and str(existing.get("status") or "") not in {"completed", "cancelled", "failed"}:
        return existing
    payload = CallingSessionCreatePayload(site_id=site_id, preferred_channels=["phone"], call_direction="outbound")
    return calling_session_create(payload)


def _voice_ready_summary(site_id: str) -> Dict[str, Any]:
    row = _data_cache().get("by_site", {}).get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    contact = _contact_record_for_site(site_id) or {}
    phone = str(contact.get("primary_phone") or "").strip()
    email = str(contact.get("primary_email") or "").strip()
    website_url = str(contact.get("website_url") or "").strip()
    contact_form_url = str(contact.get("contact_form_url") or "").strip()
    preferred_channel = str(contact.get("preferred_channel") or "mail").strip() or "mail"
    missing_requirements: List[str] = []
    if bool(contact.get("do_not_contact")):
        missing_requirements.append("do_not_contact")
    if not phone:
        missing_requirements.append("missing_primary_phone")
    fallback_channel = "website_form" if contact_form_url else ("email" if email else ("website" if website_url else "door"))
    voice_ready = "missing_primary_phone" not in missing_requirements and "do_not_contact" not in missing_requirements
    return {
        "voice_ready": voice_ready,
        "preferred_channel": preferred_channel,
        "phone_number": phone or None,
        "email": email or None,
        "website_url": website_url or None,
        "contact_form_url": contact_form_url or None,
        "fallback_channel": fallback_channel,
        "missing_requirements": missing_requirements,
    }


def _build_voice_brief(site_id: str) -> Dict[str, Any]:
    row = _data_cache().get("by_site", {}).get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    row = _attach_operator_status(row)
    contact = _contact_record_for_site(site_id) or {}
    voice_readiness = _voice_ready_summary(site_id)
    next_action = _lead_next_action_payload(site_id)
    playbook = _compile_playbook(row=row, preferred_channels=["phone"], execution_mode="agent_assist", strict_guardrails=True)
    latest_session = _latest_calling_session_for_site(site_id)
    brief = {
        "framework": VOICE_AGENT_FRAMEWORK,
        "site_id": site_id,
        "contact_id": contact.get("contact_id"),
        "account_id": contact.get("account_id"),
        "voice_ready": voice_readiness.get("voice_ready"),
        "phone_number": voice_readiness.get("phone_number"),
        "fallback_channel": voice_readiness.get("fallback_channel"),
        "missing_requirements": voice_readiness.get("missing_requirements"),
        "contact": {
            "display_name": contact.get("display_name"),
            "role": contact.get("role"),
            "preferred_channel": contact.get("preferred_channel"),
            "mailing_address": contact.get("mailing_address"),
            "primary_phone": contact.get("primary_phone"),
            "primary_email": contact.get("primary_email"),
            "website_url": contact.get("website_url"),
            "contact_form_url": contact.get("contact_form_url"),
            "contact_paths": contact.get("contact_paths") or [],
            "contactability_label": contact.get("contactability_label"),
            "contactability_score": contact.get("contactability_score"),
        },
        "site": {
            "address": row.get("address"),
            "zip": row.get("zip"),
            "primary_product": row.get("primary_product"),
            "secondary_product": row.get("secondary_product"),
            "lead_temperature": row.get("lead_temperature"),
            "confidence": round(float(row.get("confidence") or 0.0), 3),
        },
        "call_objective": playbook.get("objective"),
        "desired_outcome": next_action.get("recommended_sequence_step") or row.get("operator_next_step"),
        "opener": (playbook.get("pre_call_brief") or {}).get("opener") if isinstance(playbook.get("pre_call_brief"), dict) else (((playbook.get("playbook") or {}).get("steps") or [{}])[1] or {}).get("instruction"),
        "why_now": row.get("why_now_summary"),
        "script_angle": next_action.get("recommended_script_angle"),
        "proof_points": (((playbook.get("playbook") or {}).get("steps") or [])[:2]),
        "objection_map": (playbook.get("playbook") or {}).get("objection_map") or [],
        "transfer_rules": {
            "human_handoff_when": [
                "prospect explicitly asks for a person",
                "prospect sounds qualified and wants pricing or inspection now",
                "agent detects complex objection or negotiation that needs a closer",
            ],
            "default_transfer_target": "human_closer",
        },
        "stop_conditions": list(playbook.get("stop_conditions") or []),
        "session": {
            "session_id": latest_session.get("session_id") if latest_session else None,
            "status": latest_session.get("status") if latest_session else "not_started",
            "last_event": ((latest_session.get("event_log") or [])[-1] if latest_session else None),
        },
        "refs": {
            "status_ref": "/api/v1/voice/calls/status",
            "result_ref": "/api/v1/voice/calls/result",
            "lead_ref": f"/api/v1/site/{site_id}",
            "next_action_ref": f"/api/v1/lead/{site_id}/next-action",
            "contactability_ref": f"/api/v1/lead/{site_id}/contactability",
        },
    }
    return brief


def _voice_status_transition(session: Dict[str, Any], payload: VoiceCallStatusPayload) -> Dict[str, Any]:
    status = _slug_token(payload.status).replace("-", "_")
    event_at = _utc_now_iso()
    next_status = {
        "queued": "ready",
        "dialing": "ready",
        "ringing": "ready",
        "answered": "live",
        "live": "live",
        "in_progress": "live",
        "voicemail": "completed",
        "busy": "completed",
        "no_answer": "completed",
        "completed": "completed",
        "cancelled": "cancelled",
        "failed": "failed",
    }.get(status)
    if not next_status:
        raise HTTPException(status_code=400, detail=f"Unsupported voice status: {payload.status}")
    updated = dict(session)
    updated["status"] = next_status
    updated["updated_at"] = event_at
    updated["provider_call_id"] = str(payload.provider_call_id or updated.get("provider_call_id") or "").strip() or None
    live_assist = dict(updated.get("live_assist") or {})
    if payload.transcript_excerpt:
        live_assist["latest_transcript_excerpt"] = str(payload.transcript_excerpt).strip()
    updated["live_assist"] = live_assist
    event_log = list(updated.get("event_log") or [])
    event_log.append(
        {
            "event_type": f"voice_status_{status}",
            "status": next_status,
            "detail": str(payload.detail or "").strip() or f"Voice provider status updated to {status}.",
            "event_at": event_at,
            "transcript_excerpt": str(payload.transcript_excerpt or "").strip() or None,
            "provider_call_id": str(payload.provider_call_id or "").strip() or None,
            "metadata": payload.metadata if isinstance(payload.metadata, dict) else {},
        }
    )
    updated["event_log"] = event_log
    return updated


def _voice_result_to_call_event(payload: VoiceCallResultPayload, session_id: str) -> CallingSessionEventPayload:
    disposition = _slug_token(payload.disposition).replace("-", "_")
    event_type = {
        "no_answer": "no_answer",
        "voicemail": "no_answer",
        "busy": "no_answer",
        "follow_up": "follow_up_needed",
        "callback": "follow_up_needed",
        "qualified": "qualified",
        "won": "won",
        "lost": "lost",
        "completed": "completed",
        "transferred_human": "follow_up_needed",
    }.get(disposition)
    if not event_type:
        raise HTTPException(status_code=400, detail=f"Unsupported voice disposition: {payload.disposition}")
    metadata = dict(payload.metadata or {})
    if payload.provider_call_id:
        metadata["provider_call_id"] = payload.provider_call_id
    if payload.callback_at:
        metadata["callback_at"] = payload.callback_at
    if payload.needs_human:
        metadata["needs_human"] = True
    if payload.human_transfer_target:
        metadata["human_transfer_target"] = payload.human_transfer_target
    if payload.next_best_action:
        metadata["next_best_action"] = payload.next_best_action
    return CallingSessionEventPayload(
        session_id=session_id,
        event_type=event_type,
        detail=payload.detail,
        event_at=_utc_now_iso(),
        transcript_excerpt=payload.transcript_excerpt,
        objection=payload.objection,
        outcome_status=payload.outcome_status,
        reason=payload.reason,
        realized_revenue_usd=payload.realized_revenue_usd,
        realized_profit_usd=payload.realized_profit_usd,
        metadata=metadata,
    )


def _upsert_lead_outcome_record(
    *,
    site_id: str,
    status_value: str,
    note: str = "",
    objection: str = "",
    reason: str = "",
    product: str = "",
    realized_revenue_usd: float | None = None,
    realized_profit_usd: float | None = None,
    attribution_channel: str = "",
    attribution_playbook_id: str = "",
    attribution_orchestrator_run_id: str = "",
    attribution_signal_keys: List[str] | None = None,
    attribution_source_session_id: str = "",
    attribution_source_job_id: str = "",
) -> Dict[str, Any]:
    status_value = str(status_value or "").strip()
    if status_value not in ALLOWED_LEAD_OUTCOME_STATUSES:
        raise HTTPException(status_code=400, detail=f"Unsupported lead outcome status: {status_value}")

    store = _read_lead_outcome_store()
    now_iso = _utc_now_iso()
    existing = dict(store.get(site_id) or {})
    won_at = existing.get("won_at")
    lost_at = existing.get("lost_at")
    if status_value == "won":
        won_at = won_at or now_iso
        lost_at = None
    elif status_value == "lost":
        lost_at = lost_at or now_iso
        won_at = None
    else:
        won_at = None
        lost_at = None

    revenue = realized_revenue_usd
    profit = realized_profit_usd
    existing_signal_keys = existing.get("attribution_signal_keys") if isinstance(existing.get("attribution_signal_keys"), list) else []
    signal_keys = [str(v).strip() for v in (attribution_signal_keys or existing_signal_keys or []) if str(v).strip()]
    store[site_id] = {
        "status": status_value,
        "note": str(note or "").strip(),
        "objection": str(objection or "").strip(),
        "reason": str(reason or "").strip(),
        "product": str(product or "").strip(),
        "realized_revenue_usd": float(revenue) if revenue is not None else None,
        "realized_profit_usd": float(profit) if profit is not None else None,
        "updated_at": now_iso,
        "won_at": won_at,
        "lost_at": lost_at,
        "attribution_channel": str(attribution_channel or existing.get("attribution_channel") or "").strip(),
        "attribution_playbook_id": str(attribution_playbook_id or existing.get("attribution_playbook_id") or "").strip(),
        "attribution_orchestrator_run_id": str(attribution_orchestrator_run_id or existing.get("attribution_orchestrator_run_id") or "").strip(),
        "attribution_signal_keys": signal_keys,
        "attribution_source_session_id": str(attribution_source_session_id or existing.get("attribution_source_session_id") or "").strip(),
        "attribution_source_job_id": str(attribution_source_job_id or existing.get("attribution_source_job_id") or "").strip(),
    }
    _write_lead_outcome_store(store)
    _lead_outcome_cache.cache_clear()
    return _lead_outcome_for(site_id)


def _read_compiled_playbook_store() -> Dict[str, Dict[str, Any]]:
    if not COMPILED_PLAYBOOKS_JSON.exists():
        return {}
    try:
        raw = json.loads(COMPILED_PLAYBOOKS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for playbook_id, payload in raw.items():
        if isinstance(payload, dict):
            out[str(playbook_id)] = payload
    return out


def _write_compiled_playbook_store(data: Dict[str, Dict[str, Any]]) -> None:
    COMPILED_PLAYBOOKS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = COMPILED_PLAYBOOKS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(COMPILED_PLAYBOOKS_JSON)


@lru_cache(maxsize=1)
def _compiled_playbook_cache() -> Dict[str, Dict[str, Any]]:
    return _read_compiled_playbook_store()


def _compiled_playbook_for(playbook_id: str) -> Dict[str, Any] | None:
    payload = _compiled_playbook_cache().get(str(playbook_id), {})
    return dict(payload) if payload else None


def _persist_compiled_playbook(playbook: Dict[str, Any]) -> Dict[str, Any]:
    store = _read_compiled_playbook_store()
    store[str(playbook.get("playbook_id") or "")] = playbook
    _write_compiled_playbook_store(store)
    _compiled_playbook_cache.cache_clear()
    return playbook


def _read_outreach_job_store() -> Dict[str, Dict[str, Any]]:
    if not OUTREACH_JOBS_JSON.exists():
        return {}
    try:
        raw = json.loads(OUTREACH_JOBS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for job_id, payload in raw.items():
        if isinstance(payload, dict):
            out[str(job_id)] = payload
    return out


def _write_outreach_job_store(data: Dict[str, Dict[str, Any]]) -> None:
    OUTREACH_JOBS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTREACH_JOBS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(OUTREACH_JOBS_JSON)


@lru_cache(maxsize=1)
def _outreach_job_cache() -> Dict[str, Dict[str, Any]]:
    return _read_outreach_job_store()


def _outreach_job_for(job_id: str) -> Dict[str, Any] | None:
    payload = _outreach_job_cache().get(str(job_id), {})
    return dict(payload) if payload else None


def _find_outreach_job_by_idempotency(site_id: str, idempotency_key: str) -> Dict[str, Any] | None:
    key = str(idempotency_key or "").strip()
    if not key:
        return None
    for job in _outreach_job_cache().values():
        if str(job.get("site_id") or "") != str(site_id or ""):
            continue
        if str(job.get("idempotency_key") or "") == key:
            return dict(job)
    return None


def _persist_outreach_job(job: Dict[str, Any]) -> Dict[str, Any]:
    store = _read_outreach_job_store()
    store[str(job.get("job_id") or "")] = job
    _write_outreach_job_store(store)
    _outreach_job_cache.cache_clear()
    return job


def _read_calling_session_store() -> Dict[str, Dict[str, Any]]:
    if not CALLING_SESSIONS_JSON.exists():
        return {}
    try:
        raw = json.loads(CALLING_SESSIONS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for session_id, payload in raw.items():
        if isinstance(payload, dict):
            out[str(session_id)] = payload
    return out


def _write_calling_session_store(data: Dict[str, Dict[str, Any]]) -> None:
    CALLING_SESSIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = CALLING_SESSIONS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(CALLING_SESSIONS_JSON)


@lru_cache(maxsize=1)
def _calling_session_cache() -> Dict[str, Dict[str, Any]]:
    return _read_calling_session_store()


def _calling_session_for(session_id: str) -> Dict[str, Any] | None:
    payload = _calling_session_cache().get(str(session_id), {})
    return dict(payload) if payload else None


def _persist_calling_session(session: Dict[str, Any]) -> Dict[str, Any]:
    store = _read_calling_session_store()
    store[str(session.get("session_id") or "")] = session
    _write_calling_session_store(store)
    _calling_session_cache.cache_clear()
    return session


def _read_email_thread_store_payload() -> Dict[str, Any]:
    default = {"updated_at": None, "threads": {}}
    if not EMAIL_THREADS_JSON.exists():
        return default
    try:
        raw = json.loads(EMAIL_THREADS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return default
    if not isinstance(raw, dict):
        return default
    threads = raw.get("threads") if isinstance(raw.get("threads"), dict) else raw
    if not isinstance(threads, dict):
        threads = {}
    out: Dict[str, Dict[str, Any]] = {}
    for thread_id, payload in threads.items():
        if isinstance(payload, dict):
            out[str(thread_id)] = payload
    return {
        "updated_at": str(raw.get("updated_at") or "").strip() or None,
        "threads": out,
    }


def _write_email_thread_store_payload(data: Dict[str, Any]) -> None:
    EMAIL_THREADS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = EMAIL_THREADS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(EMAIL_THREADS_JSON)


@lru_cache(maxsize=1)
def _email_thread_store_cache() -> Dict[str, Any]:
    return _read_email_thread_store_payload()


def _email_threads() -> Dict[str, Dict[str, Any]]:
    payload = _email_thread_store_cache()
    threads = payload.get("threads") if isinstance(payload.get("threads"), dict) else {}
    return {str(thread_id): dict(value) for thread_id, value in threads.items() if isinstance(value, dict)}


def _email_thread_for(thread_id: str) -> Dict[str, Any] | None:
    payload = _email_threads().get(str(thread_id), {})
    return dict(payload) if payload else None


def _persist_email_thread(thread: Dict[str, Any]) -> Dict[str, Any]:
    payload = _read_email_thread_store_payload()
    threads = dict(payload.get("threads") or {})
    threads[str(thread.get("thread_id") or "")] = thread
    updated = {
        "updated_at": str(thread.get("updated_at") or _utc_now_iso()),
        "threads": threads,
    }
    _write_email_thread_store_payload(updated)
    _email_thread_store_cache.cache_clear()
    return thread


def _read_mailbox_sync_state() -> Dict[str, Any]:
    default = {"updated_at": None, "last_poll": None, "runs": []}
    if not MAILBOX_SYNC_STATE_JSON.exists():
        return default
    try:
        raw = json.loads(MAILBOX_SYNC_STATE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return default
    if not isinstance(raw, dict):
        return default
    runs = [item for item in (raw.get("runs") or []) if isinstance(item, dict)]
    last_poll = raw.get("last_poll") if isinstance(raw.get("last_poll"), dict) else (runs[0] if runs else None)
    return {
        "updated_at": str(raw.get("updated_at") or "").strip() or None,
        "last_poll": last_poll,
        "runs": runs[:25],
    }


def _write_mailbox_sync_state(data: Dict[str, Any]) -> None:
    MAILBOX_SYNC_STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = MAILBOX_SYNC_STATE_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(MAILBOX_SYNC_STATE_JSON)


@lru_cache(maxsize=1)
def _mailbox_sync_state_cache() -> Dict[str, Any]:
    return _read_mailbox_sync_state()


def _persist_mailbox_poll_run(run: Dict[str, Any]) -> Dict[str, Any]:
    payload = _read_mailbox_sync_state()
    runs = [item for item in (payload.get("runs") or []) if isinstance(item, dict)]
    runs = [dict(run)] + runs[:24]
    updated = {
        "updated_at": str(run.get("polled_at") or _utc_now_iso()),
        "last_poll": dict(run),
        "runs": runs,
    }
    _write_mailbox_sync_state(updated)
    _mailbox_sync_state_cache.cache_clear()
    return run


def _clean_message_ref(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.startswith("<") and text.endswith(">"):
        text = text[1:-1].strip()
    return text or None


def _normalize_email_address(value: Any) -> str | None:
    values = []
    if isinstance(value, list):
        values = [str(v) for v in value if str(v).strip()]
    elif value not in (None, ""):
        values = [str(value)]
    for _, email in getaddresses(values):
        cleaned = str(email or "").strip().lower()
        if cleaned:
            return cleaned
    text = str(value or "").strip().lower()
    return text if text and "@" in text else None


def _normalize_email_list(value: Any) -> List[str]:
    source: List[str] = []
    if isinstance(value, list):
        source = [str(v) for v in value if str(v).strip()]
    elif value not in (None, ""):
        source = [str(value)]
    out: List[str] = []
    seen: set[str] = set()
    for _, email in getaddresses(source):
        cleaned = str(email or "").strip().lower()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        out.append(cleaned)
    return out


def _normalize_iso_datetime(value: Any, fallback: str | None = None) -> str:
    text = str(value or "").strip()
    if text:
        try:
            candidate = text.replace("Z", "+00:00") if text.endswith("Z") else text
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            try:
                dt = parsedate_to_datetime(text)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass
    return str(fallback or _utc_now_iso())


def _email_subject_key(subject: Any) -> str:
    text = str(subject or "").strip().lower()
    while True:
        stripped = re.sub(r"^(re|fw|fwd)\s*:\s*", "", text, flags=re.IGNORECASE)
        if stripped == text:
            break
        text = stripped.strip()
    return re.sub(r"\s+", " ", text).strip()


def _html_to_text(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _email_body_preview(text: Any) -> str | None:
    body = str(text or "").strip()
    if not body:
        return None
    body = re.sub(r"\s+", " ", body)
    return body[:280]


def _normalize_inbox_message(raw: Dict[str, Any], source: str) -> Dict[str, Any]:
    direction = _slug_token(raw.get("direction") or "inbound").replace("-", "_") or "inbound"
    if direction not in {"inbound", "outbound"}:
        direction = "inbound"
    subject = str(raw.get("subject") or "").strip()
    body_text = str(raw.get("body_text") or "").strip()
    body_html = str(raw.get("body_html") or "").strip()
    if not body_text and body_html:
        body_text = _html_to_text(body_html)
    occurred_at = _normalize_iso_datetime(raw.get("received_at") or raw.get("sent_at"), _utc_now_iso())
    from_email = _normalize_email_address(raw.get("from_email"))
    to_emails = _normalize_email_list(raw.get("to_emails"))
    cc_emails = _normalize_email_list(raw.get("cc_emails"))
    bcc_emails = _normalize_email_list(raw.get("bcc_emails"))
    external_message_id = _clean_message_ref(raw.get("external_message_id"))
    provider_message_id = str(raw.get("provider_message_id") or "").strip() or None
    in_reply_to = _clean_message_ref(raw.get("in_reply_to"))
    references = []
    for item in (raw.get("references") or []):
        cleaned = _clean_message_ref(item)
        if cleaned:
            references.append(cleaned)
    fingerprint = "|".join(
        [
            direction,
            from_email or "",
            "|".join(to_emails[:3]),
            _email_subject_key(subject),
            occurred_at[:19],
            (_email_body_preview(body_text) or "")[:80].lower(),
        ]
    )
    message_id = external_message_id or provider_message_id or f"email_msg_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    return {
        "message_id": message_id,
        "external_message_id": external_message_id,
        "provider_message_id": provider_message_id,
        "direction": direction,
        "from_email": from_email,
        "to_emails": to_emails,
        "cc_emails": cc_emails,
        "bcc_emails": bcc_emails,
        "subject": subject or None,
        "subject_key": _email_subject_key(subject),
        "body_text": body_text or None,
        "body_preview": _email_body_preview(body_text),
        "occurred_at": occurred_at,
        "in_reply_to": in_reply_to,
        "references": references,
        "source": str(source or "manual").strip() or "manual",
        "metadata": dict(raw.get("metadata") or {}),
        "fingerprint": fingerprint,
    }


def _email_message_identity_tokens(message: Dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for key in ("message_id", "external_message_id", "provider_message_id"):
        value = str(message.get(key) or "").strip().lower()
        if value:
            tokens.add(value)
    fingerprint = str(message.get("fingerprint") or "").strip().lower()
    if fingerprint:
        tokens.add(f"fp:{fingerprint}")
    return tokens


def _email_message_reference_tokens(message: Dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for key in ("in_reply_to",):
        value = str(message.get(key) or "").strip().lower()
        if value:
            tokens.add(value)
    for item in (message.get("references") or []):
        value = str(item or "").strip().lower()
        if value:
            tokens.add(value)
    return tokens


def _email_thread_links(thread: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [dict(item) for item in (thread.get("links") or []) if isinstance(item, dict)]


def _email_thread_for_link(entity_type: str, entity_id: str) -> Dict[str, Any] | None:
    normalized_type = _slug_token(entity_type).replace("-", "_")
    normalized_id = str(entity_id or "").strip()
    if not normalized_type or not normalized_id:
        return None
    for thread in _email_threads().values():
        for link in _email_thread_links(thread):
            if _slug_token(link.get("entity_type") or "").replace("-", "_") != normalized_type:
                continue
            if str(link.get("entity_id") or "") != normalized_id:
                continue
            return dict(thread)
    return None


def _merge_email_links(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in existing + incoming:
        if not isinstance(item, dict):
            continue
        entity_type = _slug_token(item.get("entity_type") or "").replace("-", "_")
        entity_id = str(item.get("entity_id") or "").strip()
        if not entity_type or not entity_id:
            continue
        key = f"{entity_type}:{entity_id}"
        if key in seen:
            continue
        seen.add(key)
        merged = dict(item)
        merged["entity_type"] = entity_type
        merged["entity_id"] = entity_id
        out.append(merged)
    return out


def _refresh_email_thread(thread: Dict[str, Any]) -> Dict[str, Any]:
    messages = [dict(item) for item in (thread.get("messages") or []) if isinstance(item, dict)]
    messages.sort(key=lambda item: str(item.get("occurred_at") or ""))
    participants: List[str] = []
    seen: set[str] = set()
    inbound_count = 0
    outbound_count = 0
    last_inbound_at = None
    last_outbound_at = None
    for item in messages:
        if str(item.get("direction") or "") == "inbound":
            inbound_count += 1
            last_inbound_at = str(item.get("occurred_at") or "") or last_inbound_at
        elif str(item.get("direction") or "") == "outbound":
            outbound_count += 1
            last_outbound_at = str(item.get("occurred_at") or "") or last_outbound_at
        for email in [item.get("from_email")] + list(item.get("to_emails") or []) + list(item.get("cc_emails") or []):
            cleaned = str(email or "").strip().lower()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            participants.append(cleaned)
    last_message = messages[-1] if messages else {}
    subject = str(thread.get("subject") or "").strip() or str(last_message.get("subject") or "").strip()
    if inbound_count and outbound_count:
        status = "reply_received" if str(last_message.get("direction") or "") == "inbound" else "active_thread"
    elif outbound_count:
        status = "awaiting_reply"
    elif inbound_count:
        status = "inbound_only"
    else:
        status = "empty"
    updated = dict(thread)
    updated["subject"] = subject or None
    updated["subject_key"] = _email_subject_key(subject)
    updated["messages"] = messages
    updated["participants"] = participants
    updated["message_count"] = len(messages)
    updated["inbound_count"] = inbound_count
    updated["outbound_count"] = outbound_count
    updated["reply_count"] = inbound_count
    updated["first_message_at"] = str((messages[0] or {}).get("occurred_at") or "").strip() or None
    updated["last_message_at"] = str((last_message or {}).get("occurred_at") or "").strip() or None
    updated["last_inbound_at"] = last_inbound_at
    updated["last_outbound_at"] = last_outbound_at
    updated["latest_message_preview"] = _email_body_preview((last_message or {}).get("body_text"))
    updated["status"] = status
    updated["updated_at"] = updated.get("last_message_at") or _utc_now_iso()
    return updated


def _email_thread_summary(thread: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not thread:
        return None
    payload = _refresh_email_thread(dict(thread))
    return {
        "thread_id": payload.get("thread_id"),
        "status": payload.get("status"),
        "subject": payload.get("subject"),
        "message_count": int(payload.get("message_count") or 0),
        "inbound_count": int(payload.get("inbound_count") or 0),
        "outbound_count": int(payload.get("outbound_count") or 0),
        "reply_count": int(payload.get("reply_count") or 0),
        "first_message_at": payload.get("first_message_at"),
        "last_message_at": payload.get("last_message_at"),
        "last_inbound_at": payload.get("last_inbound_at"),
        "last_outbound_at": payload.get("last_outbound_at"),
        "participants": list(payload.get("participants") or []),
        "latest_message_preview": payload.get("latest_message_preview"),
        "has_reply": bool(payload.get("inbound_count") or 0),
    }


def _queue_email_links(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    queue_id = str(record.get("queue_id") or "").strip()
    if not queue_id:
        return []
    opportunity = dict(record.get("opportunity") or {})
    return [
        {
            "entity_type": "craigslist_outreach_queue",
            "entity_id": queue_id,
            "site_id": None,
            "opportunity_id": str(opportunity.get("opportunity_id") or record.get("opportunity_id") or "").strip() or None,
        }
    ]


def _outreach_job_email_links(job: Dict[str, Any]) -> List[Dict[str, Any]]:
    job_id = str(job.get("job_id") or "").strip()
    if not job_id:
        return []
    return [
        {
            "entity_type": "outreach_job",
            "entity_id": job_id,
            "site_id": str(job.get("site_id") or "").strip() or None,
        }
    ]


def _find_email_thread_for_messages(messages: List[Dict[str, Any]], links: List[Dict[str, Any]] | None = None, thread_id: str | None = None) -> Dict[str, Any] | None:
    explicit_thread_id = str(thread_id or "").strip()
    if explicit_thread_id:
        thread = _email_thread_for(explicit_thread_id)
        if thread:
            return thread
    for link in (links or []):
        thread = _email_thread_for_link(str(link.get("entity_type") or ""), str(link.get("entity_id") or ""))
        if thread:
            return thread
    threads = list(_email_threads().values())
    reference_tokens: set[str] = set()
    for message in messages:
        reference_tokens.update(_email_message_reference_tokens(message))
        for key in ("external_message_id", "provider_message_id"):
            value = str(message.get(key) or "").strip().lower()
            if value:
                reference_tokens.add(value)
    if reference_tokens:
        for thread in threads:
            existing_tokens: set[str] = set()
            for message in (thread.get("messages") or []):
                existing_tokens.update(_email_message_identity_tokens(dict(message)))
            if reference_tokens & existing_tokens:
                return dict(thread)
    for message in messages:
        subject_key = str(message.get("subject_key") or "").strip()
        participants = {
            email
            for email in [message.get("from_email")] + list(message.get("to_emails") or []) + list(message.get("cc_emails") or [])
            if str(email or "").strip()
        }
        if not subject_key or not participants:
            continue
        for thread in threads:
            if str(thread.get("subject_key") or "").strip() != subject_key:
                continue
            thread_participants = {str(email or "").strip() for email in (thread.get("participants") or []) if str(email or "").strip()}
            if participants & thread_participants:
                return dict(thread)
    return None


def _upsert_email_thread(*, source: str, messages: List[Dict[str, Any]], links: List[Dict[str, Any]] | None = None, thread_id: str | None = None) -> Dict[str, Any]:
    normalized_messages = [_normalize_inbox_message(item, source) for item in messages if isinstance(item, dict)]
    if not normalized_messages:
        raise HTTPException(status_code=400, detail="messages is required")
    existing = _find_email_thread_for_messages(normalized_messages, links=links or [], thread_id=thread_id)
    now = _utc_now_iso()
    created = False
    if existing:
        thread = dict(existing)
    else:
        created = True
        thread = {
            "thread_id": str(thread_id or "").strip() or f"email_thread_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}",
            "created_at": now,
            "updated_at": now,
            "links": [],
            "messages": [],
        }
    thread["links"] = _merge_email_links(_email_thread_links(thread), list(links or []))
    existing_tokens: set[str] = set()
    for message in (thread.get("messages") or []):
        existing_tokens.update(_email_message_identity_tokens(dict(message)))
    added_messages: List[Dict[str, Any]] = []
    deduped_count = 0
    for message in normalized_messages:
        tokens = _email_message_identity_tokens(message)
        if tokens and tokens & existing_tokens:
            deduped_count += 1
            continue
        added_messages.append(message)
        thread.setdefault("messages", []).append(message)
        existing_tokens.update(tokens)
    thread = _refresh_email_thread(thread)
    _persist_email_thread(thread)
    return {
        "thread": thread,
        "created": created,
        "added_messages": added_messages,
        "deduped_count": deduped_count,
    }


def _apply_inbox_summary(record: Dict[str, Any], thread: Dict[str, Any] | None) -> Dict[str, Any]:
    updated = dict(record)
    updated["inbox"] = _email_thread_summary(thread)
    return updated


def _outreach_job_for_provider_message_id(provider_message_id: str) -> Dict[str, Any] | None:
    key = str(provider_message_id or "").strip()
    if not key:
        return None
    for job in _outreach_job_cache().values():
        dispatch = dict(job.get("dispatch") or {})
        delivery = dict(job.get("delivery") or {})
        if str(dispatch.get("provider_message_id") or "") == key or str(delivery.get("provider_message_id") or "") == key:
            return dict(job)
    return None


def _cl_queue_record_for_provider_message_id(provider_message_id: str) -> Dict[str, Any] | None:
    key = str(provider_message_id or "").strip()
    if not key:
        return None
    for record in _cl_outreach_queue_cache().values():
        if not isinstance(record, dict):
            continue
        dispatch = dict(record.get("dispatch") or {})
        if str(dispatch.get("provider_message_id") or "") == key:
            return dict(record)
    return None


def _resolve_inbox_links(payload: InboxImportPayload, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    links: List[Dict[str, Any]] = []
    outreach_job = None
    queue_record = None
    queue_id = str(payload.queue_id or "").strip()
    outreach_job_id = str(payload.outreach_job_id or "").strip()
    if queue_id:
        queue_record = _cl_queue_record_for(queue_id)
        if not queue_record:
            raise HTTPException(status_code=404, detail=f"Unknown Craigslist outreach queue record {queue_id}")
        links.extend(_queue_email_links(queue_record))
    if outreach_job_id:
        outreach_job = _outreach_job_for(outreach_job_id)
        if not outreach_job:
            raise HTTPException(status_code=404, detail=f"Unknown outreach job {outreach_job_id}")
        links.extend(_outreach_job_email_links(outreach_job))
    if not queue_record or not outreach_job:
        for message in messages:
            refs = list(_email_message_reference_tokens(message))
            provider_message_id = str(message.get("provider_message_id") or "").strip()
            if provider_message_id:
                refs.append(provider_message_id.lower())
            for ref in refs:
                if not queue_record:
                    maybe_queue = _cl_queue_record_for_provider_message_id(ref)
                    if maybe_queue:
                        queue_record = maybe_queue
                        links.extend(_queue_email_links(maybe_queue))
                if not outreach_job:
                    maybe_job = _outreach_job_for_provider_message_id(ref)
                    if maybe_job:
                        outreach_job = maybe_job
                        links.extend(_outreach_job_email_links(maybe_job))
            if queue_record and outreach_job:
                break
    return {
        "links": _merge_email_links([], links),
        "queue_record": queue_record,
        "outreach_job": outreach_job,
    }


def _apply_outreach_job_inbox_message(job: Dict[str, Any], thread: Dict[str, Any], message: Dict[str, Any], source: str, actor_id: str | None) -> Dict[str, Any]:
    updated = _apply_inbox_summary(job, thread)
    if str(message.get("direction") or "") != "inbound":
        return updated
    for item in (updated.get("event_log") or []):
        metadata = dict(item.get("metadata") or {})
        if str(item.get("event_type") or "") == "reply_received" and str(metadata.get("message_id") or "") == str(message.get("message_id") or ""):
            return updated
    updated = _apply_outreach_job_event(
        updated,
        OutreachJobEventPayload(
            job_id=str(updated.get("job_id") or ""),
            event_type="reply_received",
            detail=f"Imported inbound email reply from {str(message.get('from_email') or 'unknown sender').strip() or 'unknown sender'}.",
            provider_message_id=str(message.get("provider_message_id") or "").strip() or None,
            event_at=str(message.get("occurred_at") or _utc_now_iso()),
            metadata={
                "message_id": message.get("message_id"),
                "thread_id": thread.get("thread_id"),
                "source": source,
                "actor_id": actor_id,
                "from_email": message.get("from_email"),
                "subject": message.get("subject"),
            },
        ),
    )
    return _apply_inbox_summary(updated, thread)


def _apply_cl_queue_inbox_message(record: Dict[str, Any], thread: Dict[str, Any], message: Dict[str, Any], source: str, actor_id: str | None) -> Dict[str, Any]:
    updated = _apply_inbox_summary(record, thread)
    updated["reply_state"] = dict(updated.get("reply_state") or {})
    if str(message.get("direction") or "") != "inbound":
        updated["reply_state"]["thread_id"] = thread.get("thread_id")
        return updated
    event_log = list(updated.get("event_log") or [])
    for item in event_log:
        metadata = dict(item.get("metadata") or {})
        if str(item.get("event_type") or "") == "reply_received" and str(metadata.get("message_id") or "") == str(message.get("message_id") or ""):
            updated["reply_state"].update(
                {
                    "reply_received": True,
                    "last_reply_at": str(message.get("occurred_at") or _utc_now_iso()),
                    "thread_id": thread.get("thread_id"),
                }
            )
            return updated
    event_at = str(message.get("occurred_at") or _utc_now_iso())
    updated["status"] = "replied" if str(updated.get("status") or "") not in {"cancelled", "suppressed"} else str(updated.get("status") or "")
    updated["updated_at"] = event_at
    updated["reply_state"].update(
        {
            "reply_received": True,
            "last_reply_at": event_at,
            "thread_id": thread.get("thread_id"),
            "last_from_email": message.get("from_email"),
            "last_message_id": message.get("message_id"),
        }
    )
    event_log.append(
        {
            "event_type": "reply_received",
            "status": str(updated.get("status") or "replied"),
            "detail": f"Imported inbound email reply from {str(message.get('from_email') or 'unknown sender').strip() or 'unknown sender'}.",
            "event_at": event_at,
            "metadata": {
                "message_id": message.get("message_id"),
                "thread_id": thread.get("thread_id"),
                "source": source,
                "actor_id": actor_id,
                "from_email": message.get("from_email"),
                "subject": message.get("subject"),
            },
        }
    )
    updated["event_log"] = event_log
    return updated


def _import_inbox_messages(payload: InboxImportPayload) -> Dict[str, Any]:
    actor_id = str(payload.actor_id or "").strip() or None
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages is required")
    normalized_messages = [_normalize_inbox_message(item.model_dump(), payload.source) for item in payload.messages]
    resolved = _resolve_inbox_links(payload, normalized_messages)
    upserted = _upsert_email_thread(
        source=payload.source,
        messages=[dict(item) for item in normalized_messages],
        links=list(resolved.get("links") or []),
        thread_id=payload.thread_id,
    )
    thread = dict(upserted.get("thread") or {})
    added_messages = [dict(item) for item in (upserted.get("added_messages") or []) if isinstance(item, dict)]
    outreach_job = dict(resolved.get("outreach_job") or {}) if resolved.get("outreach_job") else None
    queue_record = dict(resolved.get("queue_record") or {}) if resolved.get("queue_record") else None

    updated_outreach_job = None
    if outreach_job:
        current = dict(outreach_job)
        current = _apply_inbox_summary(current, thread)
        if bool(payload.mark_reply_received):
            for message in added_messages:
                current = _apply_outreach_job_inbox_message(current, thread, message, payload.source, actor_id)
        updated_outreach_job = _persist_outreach_job(current)

    updated_queue_record = None
    if queue_record:
        current = dict(queue_record)
        current = _apply_inbox_summary(current, thread)
        if bool(payload.mark_reply_received):
            for message in added_messages:
                current = _apply_cl_queue_inbox_message(current, thread, message, payload.source, actor_id)
        updated_queue_record = _persist_cl_queue_record(_cl_enrich_queue_record(current))

    return {
        "framework": "dg-inbox-v1",
        "source": str(payload.source or "manual").strip() or "manual",
        "thread": _refresh_email_thread(thread),
        "thread_summary": _email_thread_summary(thread),
        "added_count": len(added_messages),
        "deduped_count": int(upserted.get("deduped_count") or 0),
        "matched_links": list(resolved.get("links") or []),
        "outreach_job": _apply_inbox_summary(updated_outreach_job, thread) if updated_outreach_job else None,
        "queue_record": _cl_enrich_queue_record(updated_queue_record) if updated_queue_record else None,
    }


def _extract_text_from_email_message(message: Any) -> str:
    text_parts: List[str] = []
    html_parts: List[str] = []
    parts = message.walk() if getattr(message, "is_multipart", lambda: False)() else [message]
    for part in parts:
        if str(part.get_content_disposition() or "").lower() == "attachment":
            continue
        content_type = str(part.get_content_type() or "").lower()
        try:
            content = part.get_content()
        except Exception:
            payload = part.get_payload(decode=True) or b""
            charset = str(part.get_content_charset() or "utf-8")
            try:
                content = payload.decode(charset, errors="replace")
            except Exception:
                content = payload.decode("utf-8", errors="replace")
        text = str(content or "").strip()
        if not text:
            continue
        if content_type == "text/plain":
            text_parts.append(text)
        elif content_type == "text/html":
            html_parts.append(text)
    if text_parts:
        return "\n\n".join(text_parts).strip()
    if html_parts:
        return _html_to_text("\n\n".join(html_parts))
    return ""


def _imap_provider_descriptor(provider: str | None = None) -> Dict[str, Any]:
    normalized = _slug_token(provider or MAILBOX_PROVIDER or "manual").replace("-", "_") or "manual"
    host = MAILBOX_IMAP_HOST
    if not host and normalized in {"zoho", "zoho_imap"}:
        host = "imap.zoho.com"
    missing: List[str] = []
    if normalized in {"imap", "zoho", "zoho_imap"}:
        if not host:
            missing.append("MAILBOX_IMAP_HOST")
        if not MAILBOX_IMAP_USERNAME:
            missing.append("MAILBOX_IMAP_USERNAME")
        if not MAILBOX_IMAP_PASSWORD:
            missing.append("MAILBOX_IMAP_PASSWORD")
    ready = normalized in {"imap", "zoho", "zoho_imap"} and not missing
    last_poll = (_mailbox_sync_state_cache().get("last_poll") or None) if isinstance(_mailbox_sync_state_cache(), dict) else None
    return {
        "provider": normalized,
        "poll_supported": normalized in {"imap", "zoho", "zoho_imap"},
        "ready": ready,
        "host": host or None,
        "port": int(MAILBOX_IMAP_PORT or "993"),
        "mailbox": MAILBOX_IMAP_MAILBOX,
        "reply_to": EMAIL_REPLY_TO or None,
        "email_from": EMAIL_FROM or None,
        "missing_requirements": missing,
        "last_poll": last_poll,
    }


def _imap_fetch_messages(payload: MailboxPollPayload) -> Dict[str, Any]:
    descriptor = _imap_provider_descriptor(payload.provider)
    if not bool(descriptor.get("poll_supported")):
        raise HTTPException(status_code=409, detail={"message": "Mailbox polling is not configured", **descriptor})
    if not bool(descriptor.get("ready")):
        raise HTTPException(status_code=409, detail={"message": "Mailbox provider is missing requirements", **descriptor})

    mailbox = str(payload.mailbox or descriptor.get("mailbox") or MAILBOX_IMAP_MAILBOX).strip() or "INBOX"
    limit = max(1, min(100, int(payload.limit or 20)))
    unseen_only = bool(payload.unseen_only)
    polled_at = _utc_now_iso()
    search_criteria = "UNSEEN" if unseen_only else "ALL"
    imported = []
    candidates = []

    try:
        client = imaplib.IMAP4_SSL(str(descriptor.get("host") or ""), int(descriptor.get("port") or 993))
        client.login(MAILBOX_IMAP_USERNAME, MAILBOX_IMAP_PASSWORD)
        status, _ = client.select(mailbox)
        if status != "OK":
            raise HTTPException(status_code=409, detail={"message": f"Failed to open mailbox {mailbox}"})
        status, data = client.search(None, search_criteria)
        if status != "OK":
            raise HTTPException(status_code=409, detail={"message": "IMAP search failed", "search_criteria": search_criteria})
        ids = [item for item in str((data or [b""])[0], "utf-8", errors="ignore").split() if item][-limit:]
        for msg_id in ids:
            status, fetched = client.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue
            raw_bytes = b""
            for part in fetched or []:
                if isinstance(part, tuple) and len(part) >= 2 and isinstance(part[1], (bytes, bytearray)):
                    raw_bytes = bytes(part[1])
                    break
            if not raw_bytes:
                continue
            parsed = BytesParser(policy=policy.default).parsebytes(raw_bytes)
            from_email = _normalize_email_address(parsed.get("From"))
            to_emails = _normalize_email_list(parsed.get_all("To", []))
            cc_emails = _normalize_email_list(parsed.get_all("Cc", []))
            subject = str(parsed.get("Subject") or "").strip()
            body_text = _extract_text_from_email_message(parsed)
            date_value = _normalize_iso_datetime(parsed.get("Date"), polled_at)
            references: List[str] = []
            for item in re.split(r"\s+", str(parsed.get("References") or "").strip()):
                cleaned = _clean_message_ref(item)
                if cleaned:
                    references.append(cleaned)
            direction = "outbound" if from_email and from_email in {(_normalize_email_address(EMAIL_REPLY_TO) or ""), (_normalize_email_address(EMAIL_FROM) or "")} else "inbound"
            candidate = {
                "external_message_id": _clean_message_ref(parsed.get("Message-ID")),
                "direction": direction,
                "from_email": from_email,
                "to_emails": to_emails,
                "cc_emails": cc_emails,
                "subject": subject,
                "body_text": body_text,
                "received_at": date_value,
                "in_reply_to": _clean_message_ref(parsed.get("In-Reply-To")),
                "references": references,
                "metadata": {
                    "mailbox": mailbox,
                    "imap_message_id": msg_id,
                    "unseen_only": unseen_only,
                },
            }
            candidates.append(candidate)
            if not bool(payload.dry_run):
                imported.append(candidate)
        try:
            client.logout()
        except Exception:
            pass
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=409, detail={"message": "IMAP poll failed", "reason": str(exc)})

    result = {
        "framework": "dg-inbox-v1",
        "provider": descriptor.get("provider"),
        "mailbox": mailbox,
        "dry_run": bool(payload.dry_run),
        "unseen_only": unseen_only,
        "limit": limit,
        "polled_at": polled_at,
        "candidate_count": len(candidates),
        "candidates": [
            {
                "from_email": item.get("from_email"),
                "subject": item.get("subject"),
                "received_at": item.get("received_at"),
                "in_reply_to": item.get("in_reply_to"),
            }
            for item in candidates
        ],
        "imports": [],
    }
    if imported:
        for item in imported:
            import_result = _import_inbox_messages(
                InboxImportPayload(
                    actor_id=payload.actor_id,
                    actor_role=payload.actor_role,
                    source=f"imap_{descriptor.get('provider')}",
                    messages=[InboxMessagePayload(**item)],
                )
            )
            result["imports"].append(
                {
                    "thread_id": ((import_result.get("thread") or {}).get("thread_id") if isinstance(import_result.get("thread"), dict) else None),
                    "matched_links": import_result.get("matched_links") or [],
                    "added_count": int(import_result.get("added_count") or 0),
                }
            )
    _persist_mailbox_poll_run(
        {
            "provider": descriptor.get("provider"),
            "mailbox": mailbox,
            "dry_run": bool(payload.dry_run),
            "unseen_only": unseen_only,
            "limit": limit,
            "polled_at": polled_at,
            "candidate_count": len(candidates),
            "import_count": len(result.get("imports") or []),
        }
    )
    return result


def _record_outbound_email_thread(*, source: str, links: List[Dict[str, Any]], from_email: str | None, to_emails: List[str], subject: str, body_text: str, provider_message_id: str | None, event_at: str) -> Dict[str, Any]:
    result = _upsert_email_thread(
        source=source,
        links=links,
        messages=[
            {
                "provider_message_id": provider_message_id,
                "direction": "outbound",
                "from_email": from_email,
                "to_emails": to_emails,
                "subject": subject,
                "body_text": body_text,
                "sent_at": event_at,
                "metadata": {"source": source},
            }
        ],
    )
    return dict(result.get("thread") or {})


def _read_orchestrator_run_store() -> Dict[str, Dict[str, Any]]:
    if not ORCHESTRATOR_RUNS_JSON.exists():
        return {}
    try:
        raw = json.loads(ORCHESTRATOR_RUNS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for run_id, payload in raw.items():
        if isinstance(payload, dict):
            out[str(run_id)] = payload
    return out


def _write_orchestrator_run_store(data: Dict[str, Dict[str, Any]]) -> None:
    ORCHESTRATOR_RUNS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = ORCHESTRATOR_RUNS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(ORCHESTRATOR_RUNS_JSON)


@lru_cache(maxsize=1)
def _orchestrator_run_cache() -> Dict[str, Dict[str, Any]]:
    return _read_orchestrator_run_store()


def _orchestrator_run_for(run_id: str) -> Dict[str, Any] | None:
    payload = _orchestrator_run_cache().get(str(run_id), {})
    return dict(payload) if payload else None


def _find_orchestrator_run_by_idempotency(site_id: str, idempotency_key: str) -> Dict[str, Any] | None:
    key = str(idempotency_key or "").strip()
    if not key:
        return None
    for run in _orchestrator_run_cache().values():
        if str(run.get("site_id") or "") != str(site_id or ""):
            continue
        if str(run.get("idempotency_key") or "") == key:
            return dict(run)
    return None


def _read_learning_job_store() -> Dict[str, Dict[str, Any]]:
    if not LEARNING_JOBS_JSON.exists():
        return {}
    try:
        raw = json.loads(LEARNING_JOBS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for job_id, payload in raw.items():
        if isinstance(payload, dict):
            out[str(job_id)] = payload
    return out


def _write_learning_job_store(data: Dict[str, Dict[str, Any]]) -> None:
    LEARNING_JOBS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEARNING_JOBS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(LEARNING_JOBS_JSON)


@lru_cache(maxsize=1)
def _learning_job_cache() -> Dict[str, Dict[str, Any]]:
    return _read_learning_job_store()


def _persist_learning_job(job: Dict[str, Any]) -> Dict[str, Any]:
    store = _read_learning_job_store()
    store[str(job.get("job_id") or "")] = job
    _write_learning_job_store(store)
    _learning_job_cache.cache_clear()
    return job


def _read_agent_task_store() -> Dict[str, Dict[str, Any]]:
    if not AGENT_TASKS_JSON.exists():
        return {}
    try:
        raw = json.loads(AGENT_TASKS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for task_id, payload in raw.items():
        if isinstance(payload, dict):
            out[str(task_id)] = dict(payload)
    return out


def _write_agent_task_store(data: Dict[str, Dict[str, Any]]) -> None:
    AGENT_TASKS_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = AGENT_TASKS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(AGENT_TASKS_JSON)


@lru_cache(maxsize=1)
def _agent_task_cache() -> Dict[str, Dict[str, Any]]:
    return _read_agent_task_store()


def _agent_task_for(task_id: str) -> Dict[str, Any] | None:
    task = _agent_task_cache().get(str(task_id) or "")
    return dict(task) if task else None


def _persist_agent_task(task: Dict[str, Any]) -> Dict[str, Any]:
    store = _read_agent_task_store()
    store[str(task.get("task_id") or "")] = task
    _write_agent_task_store(store)
    _agent_task_cache.cache_clear()
    return dict(task)


def _clean_address_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "Unknown address"
    text = re.sub(r"\s+", " ", text)
    if ";" in text:
        text = text.replace(";", "-")
        text = re.sub(r"-{2,}", "-", text)
    text = text.replace(" ,", ",")
    return text


def _address_quality_penalty(address: Any) -> float:
    text = str(address or "").strip()
    if not text:
        return 12.0
    penalty = 0.0
    if ";" in text:
        penalty += 8.0
    if text.lower().startswith("unknown"):
        penalty += 6.0
    if len(text) < 10:
        penalty += 3.0
    return penalty


def _attach_operator_status(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    out["address"] = _clean_address_text(row.get("address"))
    out["operator_status"] = _operator_status_for(str(row.get("site_id") or ""))
    out["lead_outcome"] = _lead_outcome_for(str(row.get("site_id") or ""))
    out["work_queue"] = _classify_work_queue(out)
    return out


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def _route_priority_score(row: Dict[str, Any]) -> float:
    lead = str(row.get("lead_temperature") or "warm")
    lead_boost = {"hot": 15.0, "warm": 6.0, "skip": -20.0}.get(lead, 0.0)

    op = row.get("operator_status") or {}
    status = str(op.get("status") or "unworked")
    status_adj = {
        "unworked": 4.0,
        "visited": 2.0,
        "contacted": 5.0,
        "follow_up": 8.0,
        "closed": -100.0,
        "skip": -100.0,
    }.get(status, 0.0)

    quality_penalty = _address_quality_penalty(row.get("address"))
    return float(row.get("sales_route_score") or row.get("priority_score") or 0.0) + lead_boost + status_adj - quality_penalty


def _classify_work_queue(row: Dict[str, Any]) -> Dict[str, Any]:
    operator_status = str((row.get("operator_status") or {}).get("status") or "unworked").strip().lower()
    outcome_status = str((row.get("lead_outcome") or {}).get("status") or "unknown").strip().lower()
    readiness = str(row.get("primary_product_readiness") or "proxy-only").strip().lower()
    lead_temperature = str(row.get("lead_temperature") or "warm").strip().lower()
    lane = str(row.get("operator_lane") or row.get("primary_product") or "solar").replace("_", " ")
    lane_key = str(row.get("operator_lane") or row.get("primary_product") or "solar").strip().lower()
    confidence = str(row.get("confidence_label") or "medium").strip().lower()
    sales_route_score = float(row.get("sales_route_score") or row.get("priority_score") or 0.0)
    annual_savings_usd = float(row.get("annual_savings_usd") or 0.0)

    if operator_status in {"closed", "skip"} or outcome_status in {"won", "lost"}:
        return {
            "bucket": "park",
            "label": "Park",
            "reason_key": "resolved",
            "reason_label": "Resolved",
            "action": "Closed or resolved. Keep only for learning or recordkeeping.",
            "rank": 0,
        }

    if readiness in {"proxy-only", "missing", ""}:
        return {
            "bucket": "verify_first",
            "label": "Verify First",
            "reason_key": "needs_evidence",
            "reason_label": "Needs evidence",
            "action": f"Confirm fit and evidence for {lane} before pushing the offer.",
            "rank": 1,
        }

    if operator_status in {"contacted", "follow_up"} or outcome_status in {"contacted", "responded", "qualified"}:
        follow_up_reason_key = "advance_decision"
        follow_up_reason_label = "Advance decision"
        follow_up_action = "Advance this lead to a real answer: responded, qualified, won, or lost."
        if outcome_status == "contacted":
            follow_up_reason_key = "awaiting_reply"
            follow_up_reason_label = "Awaiting reply"
            follow_up_action = "Follow up on the first touch and force a yes, no, or meeting."
        elif outcome_status == "responded":
            follow_up_reason_key = "book_meeting"
            follow_up_reason_label = "Book meeting"
            follow_up_action = "Turn the response into a scheduled inspection, quote, or next call."
        elif outcome_status == "qualified":
            follow_up_reason_key = "close_or_quote"
            follow_up_reason_label = "Close or quote"
            follow_up_action = "Move this qualified lead to pricing, site visit, or close."
        elif operator_status == "follow_up":
            follow_up_reason_key = "scheduled_follow_up"
            follow_up_reason_label = "Scheduled follow up"
            follow_up_action = "Run the next follow-up touch and update the outcome immediately."
        return {
            "bucket": "follow_up",
            "label": "Follow Up",
            "reason_key": follow_up_reason_key,
            "reason_label": follow_up_reason_label,
            "action": follow_up_action,
            "rank": 2,
        }

    if lead_temperature in {"hot", "warm"}:
        return {
            "bucket": "work_now",
            "label": "Work Now",
            "reason_key": "hot_lead" if lead_temperature == "hot" else "ready_to_work",
            "reason_label": "Hot lead" if lead_temperature == "hot" else "Ready to work",
            "action": f"Make first contact now and lead with {lane}.",
            "rank": 3 if lead_temperature == "hot" else 2,
        }

    if operator_status == "visited":
        return {
            "bucket": "park",
            "label": "Park",
            "reason_key": "visited_stale",
            "reason_label": "Visited, no result",
            "action": "Do not keep this half-done. Either set a follow up or leave it parked until a new trigger appears.",
            "rank": 1,
        }

    if sales_route_score >= 58.0 or annual_savings_usd >= 6500.0:
        return {
            "bucket": "park",
            "label": "Park",
            "reason_key": "backlog",
            "reason_label": "Backlog",
            "action": "Still a good lead, but not urgent enough to beat active work-now or follow-up addresses.",
            "rank": 1,
        }

    if lane_key in {"roofing", "battery_backup"}:
        return {
            "bucket": "park",
            "label": "Park",
            "reason_key": "watch_trigger",
            "reason_label": "Watch for trigger",
            "action": f"Keep this {lane} lead on watch until storm, outage, or timing signals improve.",
            "rank": 0,
        }

    if confidence == "low" or annual_savings_usd < 2000.0 or sales_route_score < 45.0 or lead_temperature == "skip":
        return {
            "bucket": "park",
            "label": "Park",
            "reason_key": "low_roi",
            "reason_label": "Low ROI",
            "action": "Lower-value lead. Spend time on stronger route-score and savings opportunities first.",
            "rank": 0,
        }

    return {
        "bucket": "park",
        "label": "Park",
        "reason_key": "hold",
        "reason_label": "Hold",
        "action": "Not urgent yet. Revisit after higher-priority outreach is worked.",
        "rank": 0,
    }


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 1)


def _top_counts(counter: Dict[str, int], *, limit: int = 5) -> List[Dict[str, Any]]:
    ranked = sorted(counter.items(), key=lambda item: (-int(item[1]), str(item[0])))
    return [{"label": label, "count": int(count)} for label, count in ranked[:limit] if int(count) > 0]


def _attribution_snapshot_for_outcome(outcome: Dict[str, Any]) -> Dict[str, Any]:
    signal_keys = outcome.get("attribution_signal_keys") if isinstance(outcome.get("attribution_signal_keys"), list) else []
    signal_keys = [str(v).strip() for v in signal_keys if str(v).strip()]
    present = {
        "channel": bool(str(outcome.get("attribution_channel") or "").strip()),
        "playbook_id": bool(str(outcome.get("attribution_playbook_id") or "").strip()),
        "orchestrator_run_id": bool(str(outcome.get("attribution_orchestrator_run_id") or "").strip()),
        "signal_keys": bool(signal_keys),
    }
    present_count = sum(1 for value in present.values() if value)
    return {
        "present": present,
        "present_count": present_count,
        "completeness_pct": round((present_count / 4.0) * 100.0, 1),
        "signal_keys": signal_keys,
    }


def _build_outcome_scope_summary(rows: List[Dict[str, Any]], *, label: str) -> Dict[str, Any]:
    status_counts: Dict[str, int] = defaultdict(int)
    product_counts: Dict[str, int] = defaultdict(int)
    objections: Dict[str, int] = defaultdict(int)
    reasons: Dict[str, int] = defaultdict(int)
    channel_counts: Dict[str, int] = defaultdict(int)
    signal_counts: Dict[str, int] = defaultdict(int)
    profit_total = 0.0
    revenue_total = 0.0
    win_count = 0
    attributed_count = 0
    attribution_completeness_total = 0.0

    for row in rows:
        outcome = row.get("lead_outcome") or {}
        status = str(outcome.get("status") or "unknown").strip().lower()
        if status == "unknown":
            continue
        status_counts[status] += 1
        product = str(outcome.get("product") or row.get("primary_product") or "unknown").strip().lower() or "unknown"
        product_counts[product] += 1

        objection = str(outcome.get("objection") or "").strip()
        if objection:
            objections[objection] += 1
        reason = str(outcome.get("reason") or "").strip()
        if reason:
            reasons[reason] += 1

        revenue = outcome.get("realized_revenue_usd")
        profit = outcome.get("realized_profit_usd")
        if revenue is not None:
            revenue_total += float(revenue)
        if profit is not None:
            profit_total += float(profit)
        if status == "won":
            win_count += 1

        attribution = _attribution_snapshot_for_outcome(outcome)
        attribution_completeness_total += float(attribution.get("completeness_pct") or 0.0)
        if int(attribution.get("present_count") or 0) > 0:
            attributed_count += 1
        channel = str(outcome.get("attribution_channel") or "").strip().lower()
        if channel:
            channel_counts[channel] += 1
        for signal_key in attribution.get("signal_keys") or []:
            signal_counts[str(signal_key)] += 1

    total = sum(status_counts.values())
    lost_count = int(status_counts.get("lost", 0))
    contacted_count = int(status_counts.get("contacted", 0))
    responded_count = int(status_counts.get("responded", 0))
    qualified_count = int(status_counts.get("qualified", 0))

    return {
        "label": label,
        "outcome_count": total,
        "won_count": win_count,
        "lost_count": lost_count,
        "contacted_count": contacted_count,
        "responded_count": responded_count,
        "qualified_count": qualified_count,
        "win_rate_pct": _safe_pct(win_count, total),
        "loss_rate_pct": _safe_pct(lost_count, total),
        "response_rate_pct": _safe_pct(responded_count + qualified_count + win_count, total),
        "profit_total_usd": round(profit_total, 2),
        "revenue_total_usd": round(revenue_total, 2),
        "avg_profit_per_win_usd": round((profit_total / win_count), 2) if win_count else None,
        "avg_revenue_per_win_usd": round((revenue_total / win_count), 2) if win_count else None,
        "status_counts": {key: int(value) for key, value in sorted(status_counts.items())},
        "top_products": _top_counts(product_counts, limit=4),
        "top_objections": _top_counts(objections, limit=4),
        "top_reasons": _top_counts(reasons, limit=4),
        "top_channels": _top_counts(channel_counts, limit=4),
        "top_signal_keys": _top_counts(signal_counts, limit=6),
        "attributed_outcome_count": attributed_count,
        "attribution_completeness_pct": _safe_pct(attributed_count, total),
        "avg_attribution_field_completeness_pct": round((attribution_completeness_total / total), 1) if total else 0.0,
    }


def _build_operator_next_action(
    row: Dict[str, Any],
    learning_scopes: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    learning_scopes = learning_scopes or {}
    operator_status = str((row.get("operator_status") or {}).get("status") or "unworked").strip().lower()
    outcome = row.get("lead_outcome") or {}
    outcome_status = str(outcome.get("status") or "unknown").strip().lower()
    lane = human_lane = str(row.get("operator_lane") or row.get("primary_product") or "solar").strip().lower()
    human_lane = human_lane.replace("_", " ")
    action_summary = str(row.get("operator_action_summary") or "Review and contact").strip()
    why_now = str(row.get("why_now_summary") or "").strip()

    if outcome_status == "won":
        headline = "Lock in the win pattern"
        rationale = "This lead is already won. Capture the economics and why it closed so DemandGrid can reinforce the right lane."
        steps = [
            "Confirm realized revenue and profit are saved.",
            "Write the real reason the deal closed.",
            "Use this win pattern when working similar leads in the same lane.",
        ]
    elif outcome_status == "lost":
        headline = "Record the loss and move on"
        rationale = "Treat this as a learning lead, not an active pursuit. The useful output now is an honest loss reason or objection."
        steps = [
            "Save the real loss reason and main objection.",
            "Mark follow-up only if there is a concrete re-entry date.",
            "Shift effort to the next higher-ranked lead.",
        ]
    elif outcome_status == "qualified":
        headline = "Advance to quote or inspection"
        rationale = "This lead is already qualified. The operator should stop re-screening and push toward a concrete closing step."
        steps = [
            "Set the inspection, quote, or decision call now.",
            "Use the pitch angle and proof points to reinforce urgency.",
            "Log the result as won or lost after the decision.",
        ]
    elif outcome_status == "responded":
        headline = "Turn the response into qualification"
        rationale = "The hard part is done. Use the response window to verify fit, timing, and decision path."
        steps = [
            "Ask qualification questions tied to the lane and trigger evidence.",
            "Confirm budget, timing, and who makes the decision.",
            "Move the workflow to follow up or qualified immediately after the conversation.",
        ]
    elif outcome_status == "contacted" or operator_status in {"contacted", "follow_up"}:
        headline = "Push this lead to a real answer"
        rationale = "The lead is already in motion, so the next value is a response, qualification, or a clear loss reason."
        steps = [
            "Follow up using the saved opener and why-now proof.",
            "Ask for a concrete next step instead of repeating the full pitch.",
            "Log responded, qualified, or lost right after the touch.",
        ]
    elif operator_status == "visited":
        headline = "Convert the visit into contact"
        rationale = "A visit without a contact outcome is still incomplete. Finish the first-touch workflow while the lead is fresh."
        steps = [
            "Use the opener for the primary lane.",
            "Mark contacted if you reached them, or save a note if not.",
            "Do not leave this lead in visited without an outcome.",
        ]
    else:
        headline = f"Make first contact on {human_lane}"
        rationale = why_now or f"Lead with {human_lane} and convert this screening score into a real response."
        steps = [
            f"Use the opener and lead with {human_lane}.",
            f"{action_summary}.",
            "Right after the touch, log contacted, responded, qualified, won, or lost.",
        ]

    zip_product_scope = learning_scopes.get("same_zip_product") or {}
    zip_scope = learning_scopes.get("same_zip") or {}
    global_scope = learning_scopes.get("global") or {}
    learning_note = "No closed-loop wins are logged yet. Start capturing real results so the board can learn."
    if int(zip_product_scope.get("won_count") or 0) > 0:
        avg_profit = zip_product_scope.get("avg_profit_per_win_usd")
        learning_note = (
            f"{zip_product_scope.get('won_count')} wins already logged for {human_lane} in this ZIP"
            + (f", averaging ${avg_profit:,.0f} profit." if avg_profit not in (None, 0) else ".")
        )
    elif int(zip_scope.get("won_count") or 0) > 0:
        learning_note = f"This ZIP has {zip_scope.get('won_count')} logged wins across all lanes. Use the local objection and reason patterns before pitching."
    elif int(global_scope.get("won_count") or 0) > 0:
        learning_note = f"DemandGrid has {global_scope.get('won_count')} wins logged overall. The system can already start learning what closes."

    return {
        "headline": headline,
        "rationale": rationale,
        "steps": steps,
        "learning_note": learning_note,
    }


def _cards_summary(cards: List[Dict[str, Any]], *, limit: int = 4) -> List[Dict[str, Any]]:
    summary: List[Dict[str, Any]] = []
    for card in list(cards or [])[:limit]:
        item: Dict[str, Any] = {}
        for key in [
            "site_id",
            "address",
            "zip",
            "primary_product",
            "lead_temperature",
            "sales_route_score",
            "annual_savings_usd",
            "confidence",
            "h3_cell",
            "site_count",
            "avg_priority_score",
            "operator_next_step",
            "route_score",
        ]:
            if key in card and card.get(key) not in (None, "", "None"):
                item[key] = card.get(key)
        if item:
            summary.append(item)
    return summary


def _agent_live_summary(zip: str | None = None, h3_cell: str | None = None, agent_id: str | None = None) -> Dict[str, Any]:
    agent_key = str(agent_id or "chow").strip() or "chow"
    rows = _scored_agent_task_rows(zip, h3_cell)
    counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        queue_bucket = str(((row.get("work_queue") or {}).get("bucket") or "park")).strip().lower() or "park"
        counts[queue_bucket] += 1

    current_task = _next_agent_task(zip=zip, h3_cell=h3_cell, agent_id=agent_key)
    current_site_id = str((current_task or {}).get("site_id") or "").strip()
    if not current_site_id and rows:
        current_site_id = str(rows[0].get("site_id") or "").strip()

    latest_run = _latest_orchestrator_run_for_site(current_site_id) if current_site_id else None
    latest_call = _latest_calling_session_for_site(current_site_id) if current_site_id else None
    latest_email = _latest_outreach_job_for_site(current_site_id) if current_site_id else None

    pending_actions: List[Dict[str, Any]] = []
    for action in list((latest_run or {}).get("actions") or []):
        if str(action.get("status") or "").strip() != "awaiting_approval":
            continue
        pending_actions.append(
            {
                "action_id": action.get("action_id"),
                "action_type": action.get("action_type"),
                "label": humanize_label(str(action.get("action_type") or "approval")),
                "blocked_reason": action.get("blocked_reason"),
            }
        )

    calling_adapter = _dispatch_adapter_descriptor("calling")
    email_adapter = _dispatch_adapter_descriptor("email")
    task_site = (current_task or {}).get("site") if isinstance((current_task or {}).get("site"), dict) else {}

    state = "idle"
    headline = "Chow is idle"
    rationale = "No claimed Chow work is active in this scope yet."
    if pending_actions:
        state = "awaiting_approval"
        headline = "Chow is waiting on approval"
        rationale = f"{len(pending_actions)} supervised action(s) are blocked until you approve them."
    elif current_task:
        task_status = str(current_task.get("status") or "ready").strip().lower()
        if task_status == "claimed":
            state = "claimed"
            headline = f"Chow is working {task_site.get('address') or current_task.get('task_id')}"
            rationale = "A live task is already claimed in this scope. Open the lead or supervise the next execution step."
        else:
            state = "ready"
            headline = f"Next Chow task is ready: {task_site.get('address') or current_task.get('task_id')}"
            rationale = "Claim it from the dashboard or ask Chow to work the next task."

    if latest_call and str(((latest_call.get("dispatch") or {}).get("status") or "")).strip() in {"provider_queued", "provider_accepted"}:
        state = "call_dispatched"
        headline = f"Chow call is active for {task_site.get('address') or current_site_id}"
        rationale = "Monitor the call lane, then log the result or human handoff immediately."
    elif latest_email and str(((latest_email.get("dispatch") or {}).get("status") or "")).strip() in {"provider_accepted", "dry_run_preview_ready"}:
        state = "email_ready"
        headline = f"Chow email lane is active for {task_site.get('address') or current_site_id}"
        rationale = "Review the email preview or dispatch state, then log sent/replied outcomes."

    return {
        "framework": CHOW_AGENT_FRAMEWORK,
        "agent_id": agent_key,
        "scope": {"zip": zip, "h3_cell": h3_cell},
        "state": state,
        "headline": headline,
        "rationale": rationale,
        "counts": {key: int(counts.get(key, 0)) for key in ["work_now", "follow_up", "verify_first", "park"]},
        "current_task": current_task,
        "pending_approvals": pending_actions,
        "pending_approval_count": len(pending_actions),
        "execution": {
            "latest_run": latest_run,
            "calling_session": latest_call,
            "outreach_job": latest_email,
        },
        "adapters": {
            "calling": calling_adapter,
            "email": email_adapter,
        },
    }


def _maybe_gpt_enhance_agent_response(
    *,
    user_message: str,
    response_payload: Dict[str, Any],
) -> Dict[str, Any]:
    if not DEMANDGRID_PI_AGENT_SCRIPT.exists():
        response_payload["agent_mode"] = "tool-routed-fallback"
        return response_payload

    prompt_payload = {
        "user_message": user_message,
        "intent": response_payload.get("intent"),
        "scope": response_payload.get("scope"),
        "tool_calls": response_payload.get("tool_calls"),
        "suggested_actions": response_payload.get("suggested_actions"),
        "grounded_reply": response_payload.get("reply"),
        "cards": _cards_summary(list(response_payload.get("cards") or [])),
    }

    try:
        proc = subprocess.run(
            [
                "node",
                "--import",
                "tsx/esm",
                str(DEMANDGRID_PI_AGENT_SCRIPT),
            ],
            input=json.dumps(prompt_payload),
            text=True,
            capture_output=True,
            timeout=90,
            cwd=str(BOT_ROOT),
        )
        if proc.returncode != 0:
            response_payload["agent_mode"] = "tool-routed-fallback"
            response_payload["agent_error"] = (proc.stderr or proc.stdout or "").strip()[:400]
            return response_payload

        parsed = json.loads(proc.stdout or "{}")
        polished = str(parsed.get("reply") or "").strip()
        if polished:
            response_payload["reply"] = polished
            response_payload["framework"] = CHOW_AGENT_FRAMEWORK
            response_payload["agent_mode"] = "gpt-grounded-synthesis"
            response_payload["model"] = f"{DEMANDGRID_PI_PROVIDER}/{DEMANDGRID_PI_MODEL}"
            response_payload["thinking_level"] = DEMANDGRID_PI_THINKING
        else:
            response_payload["agent_mode"] = "tool-routed-fallback"
        return response_payload
    except Exception as exc:
        response_payload["agent_mode"] = "tool-routed-fallback"
        response_payload["agent_error"] = str(exc)[:400]
        return response_payload


def _finalize_agent_response(user_message: str, response_payload: Dict[str, Any]) -> Dict[str, Any]:
    response_payload.setdefault("framework", AGENT_FRAMEWORK)
    return _maybe_gpt_enhance_agent_response(user_message=user_message, response_payload=response_payload)


def _read_scored_rows() -> List[Dict[str, Any]]:
    if not SITE_SCORES_CSV.exists():
        return []
    with SITE_SCORES_CSV.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["lat"] = float(r["lat"])
        r["lon"] = float(r["lon"])
        r["annual_kwh_solar"] = float(r["annual_kwh_solar"])
        r["zip_priority_score"] = float(r["zip_priority_score"])
        r["roof_usable_area_m2"] = float(r["roof_usable_area_m2"])
        r["estimated_system_kw"] = float(r["estimated_system_kw"])
        r["roof_complexity_score"] = float(r["roof_complexity_score"])
        r["solar_access_proxy"] = float(r["solar_access_proxy"])
        r["profit_score"] = float(r["profit_score"])
        r["close_probability"] = float(r["close_probability"])
        r["fit_score"] = float(r["fit_score"])
        r["effort_score"] = float(r["effort_score"])
        r["priority_score"] = float(r["priority_score"])
        r["sales_route_score"] = float(r["sales_route_score"])
        r["roofing_score"] = float(r["roofing_score"])
        r["solar_score"] = float(r["solar_score"])
        r["hvac_score"] = float(r["hvac_score"])
        r["battery_score"] = float(r["battery_score"])
        r["primary_product_score"] = float(r["primary_product_score"])
        r["secondary_product_score"] = float(r["secondary_product_score"])
        r["install_cost_solar_usd"] = float(r["install_cost_solar_usd"])
        r["annual_savings_usd"] = float(r["annual_savings_usd"])
        r["payback_years"] = float(r["payback_years"])
        r["npv_15y_usd"] = float(r["npv_15y_usd"])
        r["confidence"] = float(r["confidence"])
        r["pvwatts_ratio"] = None if r.get("pvwatts_ratio") in ("", "None") else float(r["pvwatts_ratio"])
        r["nsrdb_ghi_annual"] = None if r.get("nsrdb_ghi_annual") in ("", "None") else float(r["nsrdb_ghi_annual"])
        r["nsrdb_dni_annual"] = None if r.get("nsrdb_dni_annual") in ("", "None") else float(r["nsrdb_dni_annual"])
        r["nsrdb_confidence_adjustment"] = None if r.get("nsrdb_confidence_adjustment") in ("", "None") else float(r["nsrdb_confidence_adjustment"])
        r["annual_kwh_wind"] = None if r.get("annual_kwh_wind") in ("", "None") else float(r["annual_kwh_wind"])
        r["annual_kwh_hybrid"] = None if r.get("annual_kwh_hybrid") in ("", "None") else float(r["annual_kwh_hybrid"])
        r["wind_confidence"] = None if r.get("wind_confidence") in ("", "None") else float(r["wind_confidence"])
        r["wind_viability"] = r.get("wind_viability") or "low"
        r["data_source"] = r.get("data_source") or "unknown"
        r["source_type"] = r.get("source_type") or "unknown"
        r["data_quality_tier"] = r.get("data_quality_tier") or "unknown-screening"
        r["footprint_area_m2"] = (
            None if r.get("footprint_area_m2") in ("", "None") else float(r["footprint_area_m2"])
        )
        r["footprint_perimeter_m"] = (
            None if r.get("footprint_perimeter_m") in ("", "None") else float(r["footprint_perimeter_m"])
        )
        r["footprint_compactness"] = (
            None if r.get("footprint_compactness") in ("", "None") else float(r["footprint_compactness"])
        )
        r["footprint_vertex_count"] = int(float(r.get("footprint_vertex_count") or 0))
        r["install_cost_hybrid_usd"] = (
            None if r.get("install_cost_hybrid_usd") in ("", "None") else float(r["install_cost_hybrid_usd"])
        )
        r["confidence_label"] = r.get("confidence_label") or "low"
        r["easy_win_label"] = r.get("easy_win_label") or "Medium effort"
        r["lead_temperature"] = r.get("lead_temperature") or "warm"
        r["operator_next_step"] = r.get("operator_next_step") or "follow_up"
        r["operator_lane"] = r.get("operator_lane") or r["primary_product"]
        r["operator_pitch_angle"] = r.get("operator_pitch_angle") or ""
        r["why_now_summary"] = r.get("why_now_summary") or ""
        r["operator_action_summary"] = r.get("operator_action_summary") or ""
        r["primary_product"] = r.get("primary_product") or "solar"
        r["secondary_product"] = r.get("secondary_product") or "roofing"
        r["primary_product_reason"] = r.get("primary_product_reason") or ""
        r["secondary_product_reason"] = r.get("secondary_product_reason") or ""
        r["primary_product_readiness"] = r.get("primary_product_readiness") or "proxy-only"
        r["secondary_product_readiness"] = r.get("secondary_product_readiness") or "proxy-only"
        r["primary_product_trigger_gap"] = r.get("primary_product_trigger_gap") or ""
        r["secondary_product_trigger_gap"] = r.get("secondary_product_trigger_gap") or ""
        r["storm_trigger_status"] = r.get("storm_trigger_status") or "missing"
        r["outage_trigger_status"] = r.get("outage_trigger_status") or "missing"
        r["equipment_age_trigger_status"] = r.get("equipment_age_trigger_status") or "missing"
        r["flood_risk_trigger_status"] = r.get("flood_risk_trigger_status") or "missing"
        r["permit_trigger_status"] = r.get("permit_trigger_status") or "missing"
        r["storm_trigger_score"] = None if r.get("storm_trigger_score") in ("", "None") else float(r["storm_trigger_score"])
        r["outage_trigger_score"] = None if r.get("outage_trigger_score") in ("", "None") else float(r["outage_trigger_score"])
        r["equipment_age_trigger_score"] = None if r.get("equipment_age_trigger_score") in ("", "None") else float(r["equipment_age_trigger_score"])
        r["flood_risk_trigger_score"] = None if r.get("flood_risk_trigger_score") in ("", "None") else float(r["flood_risk_trigger_score"])
        r["permit_trigger_score"] = None if r.get("permit_trigger_score") in ("", "None") else float(r["permit_trigger_score"])
        r["permit_recent_count"] = None if r.get("permit_recent_count") in ("", "None") else int(float(r["permit_recent_count"]))
        r["permit_recent_types"] = r.get("permit_recent_types") or ""
        r["permit_last_date"] = r.get("permit_last_date") or ""
        r["permit_last_type"] = r.get("permit_last_type") or ""
        r["has_storm_trigger_data"] = str(r.get("has_storm_trigger_data", "")).strip().lower() in {"1", "true", "yes"}
        r["has_outage_trigger_data"] = str(r.get("has_outage_trigger_data", "")).strip().lower() in {"1", "true", "yes"}
        r["has_equipment_age_data"] = str(r.get("has_equipment_age_data", "")).strip().lower() in {"1", "true", "yes"}
        r["has_flood_risk_data"] = str(r.get("has_flood_risk_data", "")).strip().lower() in {"1", "true", "yes"}
        r["has_permit_trigger_data"] = str(r.get("has_permit_trigger_data", "")).strip().lower() in {"1", "true", "yes"}
        r["trigger_data_gaps"] = r.get("trigger_data_gaps") or ""
        r["trigger_notes"] = r.get("trigger_notes") or ""
        r["recommended_pitch"] = r.get("recommended_pitch") or ""
        r["requires_site_survey"] = str(r.get("requires_site_survey", "")).strip().lower() in {"1", "true", "yes"}
        r["reasons"] = json.loads(r.pop("reasons_json", "[]"))
    return rows


def _read_property_triggers() -> Dict[str, Dict[str, Any]]:
    if not PROPERTY_TRIGGERS_CSV.exists():
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    with PROPERTY_TRIGGERS_CSV.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            site_id = str(row.get("site_id") or "").strip()
            if not site_id:
                continue
            out[site_id] = {
                "storm_trigger_status": str(row.get("storm_trigger_status") or "missing"),
                "outage_trigger_status": str(row.get("outage_trigger_status") or "missing"),
                "equipment_age_trigger_status": str(row.get("equipment_age_trigger_status") or "missing"),
                "flood_risk_trigger_status": str(row.get("flood_risk_trigger_status") or "missing"),
                "permit_trigger_status": str(row.get("permit_trigger_status") or "missing"),
                "storm_trigger_score": None if row.get("storm_trigger_score") in ("", "None", None) else float(row["storm_trigger_score"]),
                "outage_trigger_score": None if row.get("outage_trigger_score") in ("", "None", None) else float(row["outage_trigger_score"]),
                "equipment_age_trigger_score": None if row.get("equipment_age_trigger_score") in ("", "None", None) else float(row["equipment_age_trigger_score"]),
                "flood_risk_trigger_score": None if row.get("flood_risk_trigger_score") in ("", "None", None) else float(row["flood_risk_trigger_score"]),
                "permit_trigger_score": None if row.get("permit_trigger_score") in ("", "None", None) else float(row["permit_trigger_score"]),
                "permit_recent_count": None if row.get("permit_recent_count") in ("", "None", None) else int(float(row["permit_recent_count"])),
                "permit_recent_types": str(row.get("permit_recent_types") or ""),
                "permit_last_date": str(row.get("permit_last_date") or ""),
                "permit_last_type": str(row.get("permit_last_type") or ""),
                "trigger_notes": str(row.get("trigger_notes") or ""),
            }
    return out


def _read_zip_priors() -> Dict[str, float]:
    if not ZIP_PRIORITY_CSV.exists():
        return {}
    out: Dict[str, float] = {}
    with ZIP_PRIORITY_CSV.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            zip_code = str(row.get("zip") or "").strip()
            if not zip_code:
                continue
            try:
                out[zip_code] = round(float(row.get("priority_score") or 0.5) * 100.0, 1)
            except Exception:
                out[zip_code] = 50.0
    return out


def _fallback_rows_from_sites() -> List[Dict[str, Any]]:
    if not SITES_CSV.exists():
        return []

    from backend.scoring.solar import ScoringAssumptions, score_site
    from scripts.score_sites import build_state_utility_rate_medians, load_manual_utility_mappings, load_official_utility_rate_overrides, load_site_utility_rates, load_state_rate_overrides, resolve_site_rate_context

    with SITES_CSV.open("r", encoding="utf-8") as f:
        sites = list(csv.DictReader(f))

    trigger_lookup = _read_property_triggers()
    zip_priors = _read_zip_priors()
    assumptions = ScoringAssumptions()
    state_rate_overrides = load_state_rate_overrides(ROOT / "data" / "raw" / "eia_state_residential_rates.csv")
    site_utility_rates = load_site_utility_rates(ROOT / "data" / "processed" / "site_utility_tariff.csv")
    state_utility_rate_medians = build_state_utility_rate_medians(sites, site_utility_rates)
    official_utility_rate_overrides = load_official_utility_rate_overrides(ROOT / "data" / "raw" / "official_utility_residential_rates.csv")
    manual_utility_mappings = load_manual_utility_mappings(ROOT / "data" / "raw" / "manual_utility_map.csv")
    rows: List[Dict[str, Any]] = []

    for site in sites:
        site_assumptions, rate_context = resolve_site_rate_context(
            site,
            assumptions,
            state_rate_overrides,
            site_utility_rates,
            state_utility_rate_medians,
            official_utility_rate_overrides,
            manual_utility_mappings,
        )
        scored = score_site(site, site_assumptions)
        scored.update(rate_context)
        zip_code = str(scored.get("zip") or "")
        footprint_area = scored.get("footprint_area_m2")
        compactness = scored.get("footprint_compactness")
        estimated_kw = round(float(scored.get("install_cost_solar_usd") or 0.0) / assumptions.install_cost_usd_per_kw, 2)
        roof_area = float(footprint_area) * 0.42 if footprint_area not in (None, "", "None") else estimated_kw * 8.5
        solar_access = max(0.55, min(0.92, 0.72 + (0.12 * ((compactness or 0.7) - 0.5)))) if compactness not in (None, "", "None") else 0.72
        roof_complexity = round(max(25.0, min(85.0, 90.0 - (float(compactness or 0.7) * 45.0))), 1)
        zip_priority = zip_priors.get(zip_code, 50.0)
        annual_savings = float(scored.get("annual_savings_usd") or 0.0)
        confidence = float(scored.get("confidence") or 0.7)

        storm = trigger_lookup.get(str(scored.get("site_id") or ""), {})
        storm_score = storm.get("storm_trigger_score")
        outage_score = storm.get("outage_trigger_score")
        equipment_score = storm.get("equipment_age_trigger_score")
        flood_score = storm.get("flood_risk_trigger_score")

        solar_score = round(min(100.0, 45.0 + (annual_savings / 180.0) + ((zip_priority - 50.0) * 0.22)), 1)
        roofing_score = round(min(100.0, 28.0 + (float(storm_score or 0.0) * 0.7)), 1)
        hvac_score = round(min(100.0, 24.0 + (float(equipment_score or 0.0) * 0.75)), 1)
        battery_score = round(min(100.0, 20.0 + (float(outage_score or 0.0) * 0.8)), 1)

        ranked_products = sorted(
            [
                ("solar", solar_score),
                ("roofing", roofing_score),
                ("hvac_heat_pump", hvac_score),
                ("battery_backup", battery_score),
            ],
            key=lambda item: item[1],
            reverse=True,
        )
        primary_product, primary_product_score = ranked_products[0]
        secondary_product, secondary_product_score = ranked_products[1]

        lane_close_bonus = {
            "solar": min(14.0, (annual_savings / 700.0) + (solar_access * 6.0)),
            "roofing": min(16.0, float(storm_score or 0.0) * 0.16),
            "hvac_heat_pump": min(16.0, (float(equipment_score or 0.0) * 0.14) + min(6.0, roof_area / 80.0)),
            "battery_backup": min(16.0, (float(outage_score or 0.0) * 0.18) + (float(flood_score or 0.0) * 0.06)),
        }.get(primary_product, 0.0)
        lane_fit_bonus = {
            "solar": min(18.0, (estimated_kw * 1.6) + (solar_access * 8.0)),
            "roofing": min(18.0, 4.0 + (float(storm_score or 0.0) * 0.14)),
            "hvac_heat_pump": min(18.0, 4.0 + (float(equipment_score or 0.0) * 0.12) + min(5.0, roof_area / 100.0)),
            "battery_backup": min(18.0, 4.0 + (float(outage_score or 0.0) * 0.16)),
        }.get(primary_product, 0.0)

        profit_score = round(min(100.0, 30.0 + (annual_savings / 160.0) + (0.08 * primary_product_score)), 1)
        close_probability = round(min(100.0, 34.0 + ((zip_priority - 50.0) * 0.28) + (confidence * 16.0) + lane_close_bonus), 1)
        fit_score = round(min(100.0, 36.0 + lane_fit_bonus), 1)
        effort_score = round(max(5.0, min(100.0, 55.0 - ((confidence - 0.6) * 35.0))), 1)
        priority_score = round((profit_score * 0.45) + (close_probability * 0.35) + (fit_score * 0.20), 1)
        urgency_bonus = {
            "solar": min(8.0, annual_savings / 1200.0),
            "roofing": min(14.0, float(storm_score or 0.0) * 0.18),
            "hvac_heat_pump": min(12.0, float(equipment_score or 0.0) * 0.14),
            "battery_backup": min(12.0, (float(outage_score or 0.0) * 0.18) + (float(flood_score or 0.0) * 0.05)),
        }.get(primary_product, 0.0)
        sales_route_score = round(
            min(
                100.0,
                (primary_product_score * 0.38)
                + (close_probability * 0.27)
                + (profit_score * 0.18)
                + urgency_bonus
                - (effort_score * 0.08),
            ),
            1,
        )
        lead_temperature = "hot" if sales_route_score >= 74 else "warm"
        operator_next_step = "work_now" if sales_route_score >= 78 else "follow_up"

        reasons = list(scored.get("reasons") or [])
        reasons.append("Fallback lightweight scoring is active while full scored export catches up to wider New England coverage.")

        pitch_angle = {
            "solar": "Lead with savings, utility pain, and roof-fit screening.",
            "roofing": "Lead with storm exposure and condition-driven urgency screening.",
            "hvac_heat_pump": "Lead with equipment age, comfort pain, and upgrade timing.",
            "battery_backup": "Lead with outage resilience and backup-power value.",
        }.get(primary_product, "Lead with the best available screening angle.")
        why_now = {
            "solar": f"Solar economics lead here: about ${annual_savings:,.0f}/yr savings with strong roof-fit screening.",
            "roofing": f"Roofing urgency leads here: storm exposure proxy is {float(storm_score or 0.0):.1f}/100.",
            "hvac_heat_pump": f"HVAC timing leads here: equipment-age proxy is {float(equipment_score or 0.0):.1f}/100.",
            "battery_backup": f"Backup-power need leads here: outage proxy is {float(outage_score or 0.0):.1f}/100.",
        }.get(primary_product, f"{primary_product.replace('_', ' ')} is the current best lightweight lane for this property.")
        action_summary = {
            "solar": "Open with bill reduction, then confirm ownership horizon and roof condition before routing.",
            "roofing": "Open with storm exposure, then confirm roof age, leaks, or visible damage before routing.",
            "hvac_heat_pump": "Open with comfort and replacement timing, then confirm system age and hot/cold room pain.",
            "battery_backup": "Open with outage pain, then confirm whether outages disrupt work, sleep, or refrigeration.",
        }.get(primary_product, "Open the site card, review the top lane, and queue it for routing if it still looks clean.")

        row = {
            **scored,
            "zip_priority_score": zip_priority,
            "roof_usable_area_m2": round(roof_area, 1),
            "estimated_system_kw": estimated_kw,
            "roof_complexity_score": roof_complexity,
            "solar_access_proxy": round(solar_access, 3),
            "profit_score": profit_score,
            "close_probability": close_probability,
            "fit_score": fit_score,
            "effort_score": effort_score,
            "priority_score": priority_score,
            "sales_route_score": sales_route_score,
            "easy_win_label": "Easy win" if sales_route_score >= 72 else "Medium effort",
            "lead_temperature": lead_temperature,
            "operator_next_step": operator_next_step,
            "operator_lane": primary_product,
            "operator_pitch_angle": pitch_angle,
            "why_now_summary": why_now,
            "operator_action_summary": action_summary,
            "roofing_score": roofing_score,
            "solar_score": solar_score,
            "hvac_score": hvac_score,
            "battery_score": battery_score,
            "primary_product": primary_product,
            "secondary_product": secondary_product,
            "primary_product_score": primary_product_score,
            "secondary_product_score": secondary_product_score,
            "primary_product_reason": "Fallback board favors the highest lightweight lane score while wider exports catch up.",
            "secondary_product_reason": "Secondary lane is the next highest lightweight score.",
            "primary_product_readiness": "proxy-only",
            "secondary_product_readiness": "proxy-only",
            "primary_product_trigger_gap": "Full lane export still rebuilding for expanded New England coverage.",
            "secondary_product_trigger_gap": "Full lane export still rebuilding for expanded New England coverage.",
            "storm_trigger_status": storm.get("storm_trigger_status", "missing"),
            "outage_trigger_status": storm.get("outage_trigger_status", "missing"),
            "equipment_age_trigger_status": storm.get("equipment_age_trigger_status", "missing"),
            "flood_risk_trigger_status": storm.get("flood_risk_trigger_status", "missing"),
            "permit_trigger_status": storm.get("permit_trigger_status", "missing"),
            "storm_trigger_score": storm_score,
            "outage_trigger_score": outage_score,
            "equipment_age_trigger_score": equipment_score,
            "flood_risk_trigger_score": flood_score,
            "permit_trigger_score": storm.get("permit_trigger_score"),
            "permit_recent_count": storm.get("permit_recent_count"),
            "permit_recent_types": storm.get("permit_recent_types", ""),
            "permit_last_date": storm.get("permit_last_date", ""),
            "permit_last_type": storm.get("permit_last_type", ""),
            "has_storm_trigger_data": storm_score is not None,
            "has_outage_trigger_data": outage_score is not None,
            "has_equipment_age_data": equipment_score is not None,
            "has_flood_risk_data": flood_score is not None,
            "has_permit_trigger_data": str(storm.get("permit_trigger_status") or "missing") != "missing",
            "trigger_data_gaps": "Expanded board is using lightweight fallback scoring until full export finishes.",
            "trigger_notes": storm.get("trigger_notes", ""),
            "recommended_pitch": "Start with a screening conversation, not a quote-grade claim.",
            "reasons": reasons,
        }
        rows.append(row)

    rows.sort(key=lambda r: (-float(r.get("sales_route_score") or 0.0), -float(r.get("priority_score") or 0.0), str(r.get("site_id") or "")))
    zip_rank: Dict[str, int] = defaultdict(int)
    for row in rows:
        zip_code = str(row.get("zip") or "")
        zip_rank[zip_code] += 1
        rank = zip_rank[zip_code]
        lane_gap = round(float(row.get("primary_product_score") or 0.0) - float(row.get("secondary_product_score") or 0.0), 1)
        row["why_now_summary"] = f"{row['why_now_summary']} Top {rank} in ZIP {zip_code}; lead over next lane is {lane_gap:.1f}."
    return rows


@lru_cache(maxsize=1)
def _data_cache() -> Dict[str, Any]:
    rows = _read_scored_rows()
    source_mode = "scored_csv"
    if SITES_CSV.exists():
        with SITES_CSV.open("r", encoding="utf-8") as f:
            site_count = sum(1 for _ in f) - 1
        if site_count > 0 and len(rows) < int(site_count * 0.8):
            rows = _fallback_rows_from_sites()
            source_mode = "lightweight_fallback"
    by_site = {r["site_id"]: r for r in rows}
    by_h3 = defaultdict(list)
    by_zip = defaultdict(list)
    for r in rows:
        by_h3[r["h3_cell"]].append(r)
        by_zip[str(r.get("zip"))].append(r)
    return {"rows": rows, "by_site": by_site, "by_h3": by_h3, "by_zip": by_zip, "source_mode": source_mode}


def _zip_cells(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["h3_cell"]].append(r)

    cells = []
    for h3_cell, items in grouped.items():
        cells.append(
            {
                "h3_cell": h3_cell,
                "site_count": len(items),
                "avg_priority_score": round(sum(i["priority_score"] for i in items) / len(items), 2),
                "avg_annual_savings_usd": round(sum(i["annual_savings_usd"] for i in items) / len(items), 2),
                "avg_payback_years": round(sum(i["payback_years"] for i in items) / len(items), 2),
                "avg_confidence": round(sum(i["confidence"] for i in items) / len(items), 3),
            }
        )
    cells.sort(key=lambda c: c["avg_priority_score"], reverse=True)
    return cells


def _aggregate_rows_to_resolution(rows: List[Dict[str, Any]], target_resolution: int) -> List[Dict[str, Any]]:
    grouped = defaultdict(list)
    for r in rows:
        cell = str(r["h3_cell"])
        try:
            parent = h3.cell_to_parent(cell, target_resolution)
        except Exception:
            parent = cell
        grouped[parent].append(r)

    cells = []
    for h3_cell, items in grouped.items():
        cells.append(
            {
                "h3_cell": h3_cell,
                "site_count": len(items),
                "avg_priority_score": round(sum(i["priority_score"] for i in items) / len(items), 2),
                "avg_annual_savings_usd": round(sum(i["annual_savings_usd"] for i in items) / len(items), 2),
                "avg_payback_years": round(sum(i["payback_years"] for i in items) / len(items), 2),
                "avg_confidence": round(sum(i["confidence"] for i in items) / len(items), 3),
            }
        )
    cells.sort(key=lambda c: c["avg_priority_score"], reverse=True)
    return cells


def _extract_zip(text: str) -> str | None:
    m = re.search(r"\b(\d{5})\b", text)
    return m.group(1) if m else None


def _extract_site_id(text: str) -> str | None:
    m = re.search(r"\b(site_[a-z0-9]+)\b", text.lower())
    return m.group(1) if m else None


def _extract_h3_cell(text: str) -> str | None:
    for token in re.findall(r"\b[0-9a-f]{12,20}\b", text.lower()):
        try:
            h3.get_resolution(token)
            return token
        except Exception:
            continue
    return None


def _scoped_rows(zip_code: str | None, h3_cell: str | None) -> List[Dict[str, Any]]:
    data = _data_cache()
    rows = list(data["rows"])

    if zip_code and zip_code not in {"__all__", "all"}:
        rows = [r for r in rows if str(r.get("zip") or "") == str(zip_code)]

    if h3_cell:
        scoped = [r for r in rows if str(r.get("h3_cell") or "") == str(h3_cell)]
        if not scoped:
            try:
                target_res = h3.get_resolution(h3_cell)
                for r in rows:
                    child = str(r.get("h3_cell") or "")
                    try:
                        if child and h3.cell_to_parent(child, target_res) == h3_cell:
                            scoped.append(r)
                    except Exception:
                        continue
            except Exception:
                scoped = []
        rows = scoped

    return [_attach_operator_status(r) for r in rows]


def _infer_product_filter(message: str) -> str | None:
    m = message.lower()
    if "roof" in m:
        return "roofing"
    if "hvac" in m or "heat pump" in m:
        return "hvac_heat_pump"
    if "battery" in m or "backup" in m or "resilien" in m:
        return "battery_backup"
    if "solar" in m:
        return "solar"
    return None


def _infer_status_update(message: str) -> str | None:
    m = message.lower()
    if "unworked" in m:
        return "unworked"
    if "visited" in m:
        return "visited"
    if "contacted" in m:
        return "contacted"
    if "follow up" in m or "follow_up" in m:
        return "follow_up"
    if "closed" in m:
        return "closed"
    if " skip" in f" {m}" or m.startswith("skip"):
        return "skip"
    return None


def _site_card(row: Dict[str, Any]) -> Dict[str, Any]:
    work_queue = row.get("work_queue") or {}
    return {
        "site_id": row.get("site_id"),
        "address": row.get("address"),
        "zip": row.get("zip"),
        "h3_cell": row.get("h3_cell"),
        "primary_product": row.get("primary_product"),
        "secondary_product": row.get("secondary_product"),
        "lead_temperature": row.get("lead_temperature"),
        "operator_next_step": row.get("operator_next_step"),
        "operator_status": (row.get("operator_status") or {}).get("status", "unworked"),
        "work_queue": work_queue,
        "sales_route_score": round(float(row.get("sales_route_score") or 0.0), 1),
        "priority_score": round(float(row.get("priority_score") or 0.0), 1),
        "annual_savings_usd": round(float(row.get("annual_savings_usd") or 0.0), 2),
        "confidence": round(float(row.get("confidence") or 0.0), 3),
    }


def _extract_asof_from_notes(notes: str) -> str:
    text = str(notes or "")
    m = re.search(r"asof=([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}Z)", text)
    return m.group(1) if m else ""


def _status_quality(status: str) -> str:
    normalized = str(status or "missing").strip().lower()
    if normalized in {"verified", "event_detected", "high"}:
        return "verified"
    if normalized in {"medium", "proxy", "low"}:
        return "proxy"
    return "missing"


def _signal_keys_for_row(row: Dict[str, Any]) -> List[str]:
    keys: List[str] = []
    for key in ["storm", "outage", "equipment_age", "flood_risk", "permit"]:
        status = str(row.get(f"{key}_trigger_status") or "missing").strip().lower()
        if status != "missing":
            keys.append(key)
    return keys


def _build_investigation_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    operator_status = (row.get("operator_status") or {}).get("status", "unworked")
    confidence = float(row.get("confidence") or 0.0)
    readiness = str(row.get("primary_product_readiness") or "").strip()
    lead_temperature = str(row.get("lead_temperature") or "warm").strip()
    trigger_notes = str(row.get("trigger_notes") or "").strip()
    trigger_asof = _extract_asof_from_notes(trigger_notes)

    evidence: List[Dict[str, Any]] = []

    utility_source = str(row.get("utility_rate_source") or "").strip()
    utility_as_of = str(row.get("utility_rate_as_of") or "").strip()
    utility_value = row.get("utility_rate_override_usd_per_kwh")
    if utility_source or utility_value not in (None, "", "None"):
        evidence.append(
            {
                "source": utility_source or "utility_rate_context",
                "field": "utility_rate_override_usd_per_kwh",
                "value": utility_value,
                "as_of": utility_as_of,
                "quality": "proxy",
            }
        )

    for lane, status_key, score_key in [
        ("storm", "storm_trigger_status", "storm_trigger_score"),
        ("outage", "outage_trigger_status", "outage_trigger_score"),
        ("equipment", "equipment_age_trigger_status", "equipment_age_trigger_score"),
        ("flood", "flood_risk_trigger_status", "flood_risk_trigger_score"),
        ("permit", "permit_trigger_status", "permit_trigger_score"),
    ]:
        status = str(row.get(status_key) or "missing")
        score = row.get(score_key)
        if status != "missing" or score not in (None, "", "None"):
            evidence.append(
                {
                    "source": f"trigger_{lane}",
                    "field": status_key,
                    "value": status,
                    "score": score,
                    "as_of": trigger_asof,
                    "quality": _status_quality(status),
                }
            )

    permit_last_date = str(row.get("permit_last_date") or "").strip()
    permit_last_type = str(row.get("permit_last_type") or "").strip()
    permit_recent_types = str(row.get("permit_recent_types") or "").strip()
    permit_recent_count = row.get("permit_recent_count")
    if any(v not in ("", None, "None") for v in (permit_last_date, permit_last_type, permit_recent_types, permit_recent_count)):
        evidence.append(
            {
                "source": "trigger_permit",
                "field": "permit_history",
                "value": {
                    "last_date": permit_last_date,
                    "last_type": permit_last_type,
                    "recent_count": permit_recent_count,
                    "recent_types": permit_recent_types.split("|") if permit_recent_types else [],
                },
                "as_of": permit_last_date or trigger_asof,
                "quality": _status_quality(str(row.get("permit_trigger_status") or "missing")),
            }
        )

    if trigger_notes:
        evidence.append(
            {
                "source": "trigger_notes",
                "field": "trigger_notes",
                "value": trigger_notes,
                "as_of": trigger_asof,
                "quality": "proxy",
            }
        )

    primary_product = str(row.get("primary_product") or "").strip().lower()
    policy = _effective_outreach_policy(primary_product)

    risk_flags: List[str] = []
    if str(row.get("lead_temperature") or "") == "hot":
        risk_flags.append("high_priority_lead")
    if str(row.get("flood_risk_trigger_status") or "") in {"verified", "event_detected", "high"}:
        risk_flags.append("flood_exposure_high")
    if str(row.get("outage_trigger_status") or "") in {"verified", "event_detected", "high"}:
        risk_flags.append("outage_exposure_high")
    if str(row.get("permit_trigger_status") or "") in {"verified", "event_detected", "high"}:
        risk_flags.append("recent_permit_activity")
    if str(row.get("requires_site_survey") or "").strip().lower() in {"1", "true", "yes"}:
        risk_flags.append("requires_site_survey")
    if readiness in {"", "proxy-only", "unknown"}:
        risk_flags.append("proxy_only_readiness")
    if ";" in str(row.get("address") or ""):
        risk_flags.append("multi_address_merged")

    suppression_reasons = _suppression_reasons_from_policy(
        confidence=confidence,
        lead_temperature=lead_temperature,
        operator_status=operator_status,
        risk_flags=risk_flags,
        policy=policy,
    )

    review_flags = [
        flag
        for flag in risk_flags
        if str(flag).strip().lower() in {str(v).strip().lower() for v in (policy.get("review_risk_flags") or [])}
    ]

    return {
        "framework": INVESTIGATION_FRAMEWORK,
        "site_id": row.get("site_id"),
        "address": row.get("address"),
        "zip": row.get("zip"),
        "h3_cell": row.get("h3_cell"),
        "primary_product": row.get("primary_product"),
        "secondary_product": row.get("secondary_product"),
        "priority_score": round(float(row.get("priority_score") or 0.0), 1),
        "confidence": round(confidence, 3),
        "lead_temperature": row.get("lead_temperature"),
        "operator_next_step": row.get("operator_next_step"),
        "operator_status": operator_status,
        "why_now_summary": str(row.get("why_now_summary") or ""),
        "operator_action_summary": str(row.get("operator_action_summary") or ""),
        "evidence": evidence,
        "risk_flags": risk_flags,
        "review_flags": review_flags,
        "suppression_reasons": suppression_reasons,
        "policy": {
            "product": policy.get("product"),
            "confidence_min": policy.get("confidence_min"),
            "confidence_high_min": policy.get("confidence_high_min"),
            "policy_version": policy.get("policy_version"),
            "policy_source": policy.get("policy_source"),
        },
    }


def _build_outreach_payload(investigation: Dict[str, Any]) -> Dict[str, Any]:
    site_id = str(investigation.get("site_id") or "")
    lead_temperature = str(investigation.get("lead_temperature") or "warm").strip().lower()
    confidence = float(investigation.get("confidence") or 0.0)
    suppression_reasons = list(investigation.get("suppression_reasons") or [])
    review_flags = list(investigation.get("review_flags") or [])

    inv_policy = investigation.get("policy") or {}
    if isinstance(inv_policy, dict) and inv_policy.get("confidence_min") is not None:
        confidence_min = _to_float(inv_policy.get("confidence_min"), DEFAULT_AUTO_OUTREACH_CONFIDENCE_MIN)
        confidence_high_min = _to_float(inv_policy.get("confidence_high_min"), max(confidence_min, 0.82))
        if confidence_high_min < confidence_min:
            confidence_high_min = confidence_min
        effective_policy = _effective_outreach_policy(str(investigation.get("primary_product") or ""))
        channel_map = dict(effective_policy.get("channel_map") or {})
        policy_version = str(inv_policy.get("policy_version") or effective_policy.get("policy_version") or "v1")
        policy_source = str(inv_policy.get("policy_source") or effective_policy.get("policy_source") or "default")
        product_key = str(inv_policy.get("product") or effective_policy.get("product") or "default")
    else:
        effective_policy = _effective_outreach_policy(str(investigation.get("primary_product") or ""))
        confidence_min = _to_float(effective_policy.get("confidence_min"), DEFAULT_AUTO_OUTREACH_CONFIDENCE_MIN)
        confidence_high_min = _to_float(effective_policy.get("confidence_high_min"), max(confidence_min, 0.82))
        if confidence_high_min < confidence_min:
            confidence_high_min = confidence_min
        channel_map = dict(effective_policy.get("channel_map") or {})
        policy_version = str(effective_policy.get("policy_version") or "v1")
        policy_source = str(effective_policy.get("policy_source") or "default")
        product_key = str(effective_policy.get("product") or "default")

    confidence_band = _confidence_band(confidence, confidence_min, confidence_high_min)

    if suppression_reasons:
        channel = "review"
    else:
        channel = str(channel_map.get(lead_temperature) or channel_map.get("default") or "email")

    message_angles = [
        str(investigation.get("why_now_summary") or "").strip(),
        str(investigation.get("operator_action_summary") or "").strip(),
    ]
    message_angles = [m for m in message_angles if m]
    if not message_angles:
        message_angles = ["Review evidence package and initiate best-fit outreach."]

    auto_outreach_eligible = (confidence >= confidence_min) and (not suppression_reasons)

    return {
        "framework": OUTREACH_FRAMEWORK,
        "site_id": site_id,
        "target_segment": lead_temperature,
        "recommended_channel": channel,
        "message_angles": message_angles,
        "cta": str(investigation.get("operator_action_summary") or "Review and contact").strip() or "Review and contact",
        "offer_priority": "primary",
        "auto_outreach_eligible": auto_outreach_eligible,
        "confidence_band": confidence_band,
        "compliance_flags": suppression_reasons,
        "review_flags": review_flags,
        "policy": {
            "product": product_key,
            "confidence_min": confidence_min,
            "confidence_high_min": confidence_high_min,
            "policy_version": policy_version,
            "policy_source": policy_source,
        },
        "handoff_context": {
            "why_now_summary": str(investigation.get("why_now_summary") or ""),
            "operator_action_summary": str(investigation.get("operator_action_summary") or ""),
            "investigation_ref": f"/api/v1/investigation/site/{site_id}",
            "outreach_policy_ref": "/api/v1/outreach/policy",
        },
    }


def _set_operator_status(site_id: str, status: str, note: str | None = None) -> Dict[str, Any]:
    status_value = str(status or "").strip()
    if status_value not in ALLOWED_OPERATOR_STATUSES:
        raise HTTPException(status_code=400, detail=f"Unsupported status: {status_value}")

    store = _read_operator_status_store()
    store[site_id] = {
        "status": status_value,
        "note": str(note or "").strip(),
        "updated_at": _utc_now_iso(),
    }
    _write_operator_status_store(store)
    _operator_status_cache.cache_clear()
    return _operator_status_for(site_id)


@app.get("/")
def frontend_index() -> FileResponse:
    if not FRONTEND_INDEX.exists():
        raise HTTPException(status_code=404, detail="frontend not built")
    return FileResponse(FRONTEND_INDEX)


@app.get("/health")
def health() -> Dict[str, Any]:
    data = _data_cache()
    return {"ok": True, "sites": len(data["rows"]), "source": str(SITE_SCORES_CSV), "source_mode": data["source_mode"]}


@app.post("/api/v1/admin/reload")
def reload_data() -> Dict[str, Any]:
    _data_cache.cache_clear()
    _operator_status_cache.cache_clear()
    _lead_contact_cache.cache_clear()
    _lead_interaction_cache.cache_clear()
    _lead_outcome_cache.cache_clear()
    _agent_task_cache.cache_clear()
    _outreach_policy_config.cache_clear()
    _dispatch_adapter_config.cache_clear()
    _pilot_scope_config.cache_clear()
    data = _data_cache()
    return {"ok": True, "sites": len(data["rows"]), "reloaded": True, "source_mode": data["source_mode"]}


@app.get("/api/v1/pilot-scope")
def pilot_scope() -> Dict[str, Any]:
    scope = _pilot_scope_config()
    return {
        **scope,
        "available_zips": [{"zip": str(zip_code)} for zip_code in (scope.get("zips") or [])],
    }


@app.get("/api/v1/zips")
def list_zips() -> Dict[str, Any]:
    data = _data_cache()
    payload = []
    for zip_code, rows in data["by_zip"].items():
        if zip_code in ("", "None", None):
            continue
        payload.append({"zip": str(zip_code), "count": len(rows)})
    payload.sort(key=lambda x: x["zip"])
    return {"count": len(payload), "zips": payload, "source_mode": data["source_mode"]}


@app.get("/api/v1/zip/{zip_code}/heatmap")
def zip_heatmap(zip_code: str) -> Dict[str, Any]:
    data = _data_cache()
    rows = list(data["by_zip"].get(str(zip_code), []))
    if not rows:
        raise HTTPException(status_code=404, detail=f"No scored sites for zip {zip_code}")

    cells = _zip_cells(rows)
    return {"zip": zip_code, "cell_count": len(cells), "cells": cells, "source_mode": data["source_mode"]}


@app.get("/api/v1/heatmap")
def all_heatmap() -> Dict[str, Any]:
    data = _data_cache()
    rows = list(data["rows"])
    if not rows:
        raise HTTPException(status_code=404, detail="No scored sites available")

    # Keep overview readable, but avoid collapsing a multi-state board into too few cells.
    overview_resolution = 7
    cells = _aggregate_rows_to_resolution(rows, target_resolution=overview_resolution)
    return {
        "scope": "all",
        "h3_resolution": overview_resolution,
        "zip_count": len([z for z in data["by_zip"].keys() if z not in ("", "None", None)]),
        "site_count": len(rows),
        "cell_count": len(cells),
        "cells": cells,
        "source_mode": data["source_mode"],
    }


@app.get("/api/v1/hex/{h3_cell}/sites")
def hex_sites(h3_cell: str, limit: int = 50) -> Dict[str, Any]:
    data = _data_cache()
    rows = list(data["by_h3"].get(h3_cell, []))

    # Support parent-cell queries (used by coarser all-ZIP overview heatmap).
    if not rows:
        try:
            target_res = h3.get_resolution(h3_cell)
            if target_res < 15:
                for child_cell, items in data["by_h3"].items():
                    try:
                        if h3.cell_to_parent(child_cell, target_res) == h3_cell:
                            rows.extend(items)
                    except Exception:
                        continue
        except Exception:
            pass

    if not rows:
        raise HTTPException(status_code=404, detail=f"No sites for h3 {h3_cell}")

    rows.sort(key=lambda r: (-_route_priority_score(r), -r["annual_savings_usd"], str(r["site_id"])))
    payload_rows = [_attach_operator_status(r) for r in rows[: max(1, min(limit, 200))]]
    return {"h3": h3_cell, "count": len(rows), "sites": payload_rows}


@app.get("/api/v1/site/{site_id}")
def site_detail(site_id: str) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    return _attach_operator_status(row)


@app.get("/api/v1/investigation/site/{site_id}")
def investigation_site(site_id: str) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    enriched = _attach_operator_status(row)
    return _build_investigation_payload(enriched)


@app.get("/api/v1/outreach/policy")
def outreach_policy() -> Dict[str, Any]:
    policy = _outreach_policy_config()
    return {
        "framework": OUTREACH_FRAMEWORK,
        "version": policy.get("version"),
        "source": policy.get("_source"),
        "default": policy.get("default") or {},
        "products": policy.get("products") or {},
    }


@app.get("/api/v1/outreach/site/{site_id}")
def outreach_site(site_id: str) -> Dict[str, Any]:
    investigation = investigation_site(site_id)
    payload = _build_outreach_payload(investigation)
    return {
        "site_id": site_id,
        "investigation": investigation,
        "outreach": payload,
    }


@app.get("/api/v1/outreach/payloads")
def outreach_payloads(
    zip: str | None = None,
    h3_cell: str | None = None,
    limit: int = 50,
    include_suppressed: bool = False,
) -> Dict[str, Any]:
    rows = _scoped_rows(zip, h3_cell)
    rows = [
        r
        for r in rows
        if str((r.get("operator_status") or {}).get("status") or "unworked") not in {"closed", "skip"}
    ]

    rows.sort(key=lambda r: (-_route_priority_score(r), -float(r.get("annual_savings_usd") or 0.0), str(r.get("site_id") or "")))
    total_candidates = len(rows)

    limit = max(1, min(limit, 200))
    payloads: List[Dict[str, Any]] = []
    for row in rows:
        investigation = _build_investigation_payload(row)
        payload = _build_outreach_payload(investigation)
        if not include_suppressed and not payload.get("auto_outreach_eligible"):
            continue
        payloads.append(payload)
        if len(payloads) >= limit:
            break

    policy = _outreach_policy_config()
    default_policy = dict(policy.get("default") or {})

    return {
        "framework": OUTREACH_FRAMEWORK,
        "count": len(payloads),
        "total_candidates": total_candidates,
        "scope": {"zip": zip, "h3_cell": h3_cell},
        "policy": {
            "version": policy.get("version"),
            "source": policy.get("_source"),
            "auto_outreach_confidence_min": _to_float(
                default_policy.get("confidence_min"), DEFAULT_AUTO_OUTREACH_CONFIDENCE_MIN
            ),
            "include_suppressed": include_suppressed,
            "product_overrides": len(dict(policy.get("products") or {})),
        },
        "items": payloads,
    }


@app.get("/api/v1/operator/status")
def list_operator_status(status: str | None = None, zip: str | None = None, h3_cell: str | None = None, limit: int = 200) -> Dict[str, Any]:
    data = _data_cache()
    rows = list(data["rows"])

    if zip:
        rows = [r for r in rows if str(r.get("zip") or "") == str(zip)]

    if h3_cell:
        filtered = [r for r in rows if str(r.get("h3_cell") or "") == str(h3_cell)]
        if not filtered:
            try:
                target_res = h3.get_resolution(h3_cell)
                for r in rows:
                    child = str(r.get("h3_cell") or "")
                    try:
                        if child and h3.cell_to_parent(child, target_res) == h3_cell:
                            filtered.append(r)
                    except Exception:
                        continue
            except Exception:
                filtered = []
        rows = filtered

    payload: List[Dict[str, Any]] = []
    status_filter = str(status).strip() if status else None
    if status_filter and status_filter not in ALLOWED_OPERATOR_STATUSES:
        raise HTTPException(status_code=400, detail=f"Unsupported status filter: {status_filter}")

    for row in rows:
        enriched = _attach_operator_status(row)
        current_status = enriched["operator_status"]["status"]
        if status_filter and current_status != status_filter:
            continue
        payload.append(
            {
                "site_id": enriched["site_id"],
                "address": enriched.get("address"),
                "zip": enriched.get("zip"),
                "h3_cell": enriched.get("h3_cell"),
                "priority_score": enriched.get("priority_score"),
                "lead_temperature": enriched.get("lead_temperature"),
                "operator_status": enriched.get("operator_status"),
            }
        )

    payload.sort(key=lambda x: (-(x.get("priority_score") or 0), str(x.get("site_id") or "")))
    trimmed = payload[: max(1, min(limit, 500))]
    return {"count": len(trimmed), "total": len(payload), "items": trimmed}


@app.get("/api/v1/operator/work-queue")
def operator_work_queue(
    zip: str | None = None,
    h3_cell: str | None = None,
    bucket: str | None = None,
    limit: int = 100,
) -> Dict[str, Any]:
    rows = _scoped_rows(zip, h3_cell)
    allowed_buckets = {"work_now", "follow_up", "verify_first", "park"}
    bucket_filter = str(bucket or "").strip().lower()
    if bucket_filter and bucket_filter not in allowed_buckets:
        raise HTTPException(status_code=400, detail=f"Unsupported work queue bucket: {bucket_filter}")

    counts: Dict[str, int] = defaultdict(int)
    filtered: List[Dict[str, Any]] = []
    for row in rows:
        work_queue = row.get("work_queue") or {}
        queue_bucket = str(work_queue.get("bucket") or "park")
        counts[queue_bucket] += 1
        if bucket_filter and queue_bucket != bucket_filter:
            continue
        filtered.append(row)

    filtered.sort(
        key=lambda r: (
            -int(((r.get("work_queue") or {}).get("rank") or 0)),
            -_route_priority_score(r),
            -float(r.get("annual_savings_usd") or 0.0),
            str(r.get("site_id") or ""),
        )
    )
    items = [_site_card(r) for r in filtered[: max(1, min(limit, 250))]]
    return {
        "scope": {"zip": zip, "h3_cell": h3_cell},
        "counts": {key: int(counts.get(key, 0)) for key in ["work_now", "follow_up", "verify_first", "park"]},
        "bucket": bucket_filter or None,
        "count": len(items),
        "items": items,
    }


@app.get("/api/v1/operator/today-brief")
def operator_today_brief(
    zip: str | None = None,
    h3_cell: str | None = None,
) -> Dict[str, Any]:
    rows = _scoped_rows(zip, h3_cell)
    counts: Dict[str, int] = defaultdict(int)
    lane_counts: Dict[str, int] = defaultdict(int)
    actionable_rows: List[Dict[str, Any]] = []
    known_outcomes: List[Dict[str, Any]] = []

    for row in rows:
        work_queue = row.get("work_queue") or {}
        queue_bucket = str(work_queue.get("bucket") or "park")
        counts[queue_bucket] += 1
        if queue_bucket != "park":
            actionable_rows.append(row)
            lane = str(row.get("primary_product") or row.get("operator_lane") or "unknown").strip().lower()
            if lane:
                lane_counts[lane] += 1
        if str(((row.get("lead_outcome") or {}).get("status") or "unknown")).strip().lower() != "unknown":
            known_outcomes.append(row)

    actionable_rows.sort(
        key=lambda r: (
            -int(((r.get("work_queue") or {}).get("rank") or 0)),
            -_route_priority_score(r),
            -float(r.get("annual_savings_usd") or 0.0),
            str(r.get("site_id") or ""),
        )
    )
    route_rows = [
        r
        for r in actionable_rows
        if str((r.get("operator_status") or {}).get("status") or "unworked") not in {"closed", "skip"}
    ]
    route_rows.sort(key=lambda r: (_route_priority_score(r), float(r.get("priority_score") or 0.0)), reverse=True)

    best_row = actionable_rows[0] if actionable_rows else (rows[0] if rows else None)
    focus_bucket = str(((best_row or {}).get("work_queue") or {}).get("bucket") or "park")
    focus_lane = str((best_row or {}).get("primary_product") or (best_row or {}).get("operator_lane") or "solar").strip().lower()
    learning_summary = _build_outcome_scope_summary(known_outcomes, label="current_scope")
    next_action = _build_operator_next_action(best_row, {"global": learning_summary}) if best_row else None

    top_lanes = [
        {"lane": lane, "count": int(count)}
        for lane, count in sorted(lane_counts.items(), key=lambda item: (-int(item[1]), str(item[0])))[:4]
        if int(count) > 0
    ]

    route_preview = None
    if route_rows:
        first = route_rows[0]
        route_preview = {
            "count": min(len(route_rows), 20),
            "first_stop": _site_card(first),
        }

    command_mode = "prospect_now"
    command_label = "Prospect now"
    command_reason = "Start with the strongest live lead in this scope and push to a real outcome."
    command_target = {
        "zip": str((best_row or {}).get("zip") or zip or "") or None,
        "h3_cell": str((best_row or {}).get("h3_cell") or h3_cell or "") or None,
        "site_id": str((best_row or {}).get("site_id") or "") or None,
        "bucket": focus_bucket,
    }
    if counts.get("follow_up", 0) > 0 and counts.get("follow_up", 0) >= max(counts.get("work_now", 0) // 4, 1):
        command_mode = "clear_follow_ups"
        command_label = "Clear follow-ups first"
        command_reason = "There are leads already in motion. Convert them before spending time on colder prospecting."
    elif focus_bucket == "verify_first":
        command_mode = "verify_before_pitch"
        command_label = "Verify before pitch"
        command_reason = "The best opportunities in this scope need a quick evidence check before you push the offer."
    elif focus_bucket == "park":
        command_mode = "switch_territory"
        command_label = "Switch territory"
        command_reason = "This scope is mostly parked work. Move to a stronger ZIP before spending time here."

    headline = "Work the best live leads first"
    rationale = "DemandGrid already ranked the next addresses. Start with the first lead and push every touch to a real outcome."
    if focus_bucket == "follow_up":
        headline = "Clear follow-ups before prospecting"
        rationale = "You already have leads in motion. Convert them to responded, qualified, won, or lost before opening colder work."
    elif focus_bucket == "verify_first":
        headline = "Verify evidence before you pitch"
        rationale = "The current scope has promising leads, but some need a quick reality check before you push the offer."
    elif focus_bucket == "park":
        headline = "No urgent leads in this scope"
        rationale = "This territory is mostly backlog or low-ROI work. Change ZIP or click a different hex for a better lane."

    territory_recommendations: List[Dict[str, Any]] = []
    if not zip and not h3_cell:
        by_zip: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            zip_code = str(row.get("zip") or "").strip()
            if not zip_code:
                continue
            slot = by_zip.setdefault(
                zip_code,
                {
                    "zip": zip_code,
                    "counts": defaultdict(int),
                    "lane_counts": defaultdict(int),
                    "best_row": None,
                    "route_score_sum": 0.0,
                    "savings_sum": 0.0,
                },
            )
            queue_bucket = str(((row.get("work_queue") or {}).get("bucket") or "park")).strip().lower()
            slot["counts"][queue_bucket] += 1
            slot["route_score_sum"] += float(row.get("sales_route_score") or 0.0)
            slot["savings_sum"] += float(row.get("annual_savings_usd") or 0.0)
            lane = str(row.get("primary_product") or row.get("operator_lane") or "unknown").strip().lower()
            if queue_bucket != "park" and lane:
                slot["lane_counts"][lane] += 1
            best_row = slot.get("best_row")
            if best_row is None or (
                int(((row.get("work_queue") or {}).get("rank") or 0)),
                _route_priority_score(row),
                float(row.get("annual_savings_usd") or 0.0),
            ) > (
                int((((best_row or {}).get("work_queue") or {}).get("rank") or 0)),
                _route_priority_score(best_row),
                float((best_row or {}).get("annual_savings_usd") or 0.0),
            ):
                slot["best_row"] = row

        ranked_territories: List[Tuple[Tuple[float, float, float], Dict[str, Any]]] = []
        for zip_code, slot in by_zip.items():
            counts_slot = slot["counts"]
            best_row = slot.get("best_row")
            lane_counts_slot = slot["lane_counts"]
            focus_lane_slot = None
            if lane_counts_slot:
                focus_lane_slot = sorted(lane_counts_slot.items(), key=lambda item: (-int(item[1]), str(item[0])))[0][0]
            score = (
                float(counts_slot.get("follow_up", 0)) * 8.0
                + float(counts_slot.get("work_now", 0)) * 5.0
                + float(counts_slot.get("verify_first", 0)) * 2.0
                - float(counts_slot.get("park", 0)) * 0.1
            )
            route_score = float(_route_priority_score(best_row)) if best_row else 0.0
            ranked_territories.append(
                (
                    (score, route_score, float(slot["savings_sum"])),
                    {
                        "zip": zip_code,
                        "counts": {key: int(counts_slot.get(key, 0)) for key in ["work_now", "follow_up", "verify_first", "park"]},
                        "focus_lane": focus_lane_slot or "solar",
                        "best_lead": _site_card(best_row) if best_row else None,
                        "avg_route_score": round((slot["route_score_sum"] / max(sum(counts_slot.values()), 1)), 1),
                        "total_savings_usd": round(float(slot["savings_sum"]), 2),
                    },
                )
            )
        ranked_territories.sort(key=lambda item: item[0], reverse=True)
        territory_recommendations = [payload for _, payload in ranked_territories[:3]]
        if command_mode == "switch_territory" and territory_recommendations:
            command_target = {
                "zip": str((territory_recommendations[0] or {}).get("zip") or "") or None,
                "h3_cell": str(((((territory_recommendations[0] or {}).get("best_lead") or {}).get("h3_cell")) or "")) or None,
                "site_id": str((((territory_recommendations[0] or {}).get("best_lead") or {}).get("site_id") or "")) or None,
                "bucket": "work_now",
            }
            command_reason = f"Best current move is to switch into ZIP {command_target['zip']} and work the strongest lane there."

    return {
        "scope": {"zip": zip, "h3_cell": h3_cell},
        "counts": {key: int(counts.get(key, 0)) for key in ["work_now", "follow_up", "verify_first", "park"]},
        "headline": headline,
        "rationale": rationale,
        "command": {
            "mode": command_mode,
            "label": command_label,
            "reason": command_reason,
            "target": command_target,
        },
        "focus_lane": focus_lane,
        "top_lanes": top_lanes,
        "best_lead": _site_card(best_row) if best_row else None,
        "next_action": next_action,
        "route_preview": route_preview,
        "learning_summary": {
            "won_count": int(learning_summary.get("won_count") or 0),
            "win_rate_pct": float(learning_summary.get("win_rate_pct") or 0.0),
            "avg_profit_per_win_usd": learning_summary.get("avg_profit_per_win_usd"),
            "top_objections": learning_summary.get("top_objections") or [],
            "top_reasons": learning_summary.get("top_reasons") or [],
        },
        "territory_recommendations": territory_recommendations,
    }


@app.get("/api/v1/agent/live-summary")
def agent_live_summary(
    zip: str | None = None,
    h3_cell: str | None = None,
    agent_id: str | None = None,
) -> Dict[str, Any]:
    return _agent_live_summary(zip=zip, h3_cell=h3_cell, agent_id=agent_id)


@app.get("/api/v1/operator/route-plan")
def operator_route_plan(
    zip: str | None = None,
    h3_cell: str | None = None,
    max_stops: int = 20,
    include_warm: bool = True,
) -> Dict[str, Any]:
    data = _data_cache()
    rows = [_attach_operator_status(r) for r in data["rows"]]

    if zip:
        rows = [r for r in rows if str(r.get("zip") or "") == str(zip)]

    if h3_cell:
        scoped = [r for r in rows if str(r.get("h3_cell") or "") == str(h3_cell)]
        if not scoped:
            try:
                target_res = h3.get_resolution(h3_cell)
                for r in rows:
                    child = str(r.get("h3_cell") or "")
                    try:
                        if child and h3.cell_to_parent(child, target_res) == h3_cell:
                            scoped.append(r)
                    except Exception:
                        continue
            except Exception:
                scoped = []
        rows = scoped

    rows = [
        r
        for r in rows
        if str((r.get("operator_status") or {}).get("status") or "unworked") not in {"closed", "skip"}
    ]

    if not include_warm:
        rows = [r for r in rows if str(r.get("lead_temperature") or "") == "hot"]

    if not rows:
        return {"count": 0, "stops": [], "notes": "No eligible stops in scope."}

    candidate_count = min(len(rows), 300)
    rows.sort(key=lambda r: (_route_priority_score(r), float(r.get("priority_score") or 0.0)), reverse=True)
    candidates = rows[:candidate_count]

    max_stops = max(1, min(max_stops, 100))
    ordered: List[Dict[str, Any]] = []

    current = candidates.pop(0)
    ordered.append(current)

    while candidates and len(ordered) < max_stops:
        prev = ordered[-1]
        prev_lat = float(prev.get("lat") or 0.0)
        prev_lon = float(prev.get("lon") or 0.0)

        best_idx = 0
        best_cost = None
        for idx, cand in enumerate(candidates):
            d_km = _haversine_km(prev_lat, prev_lon, float(cand.get("lat") or 0.0), float(cand.get("lon") or 0.0))
            score_penalty = max(0.0, 120.0 - (_route_priority_score(cand) * 1.2))
            cost = (d_km * 2.0) + (score_penalty * 0.03)
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_idx = idx

        ordered.append(candidates.pop(best_idx))

    stops = []
    for idx, row in enumerate(ordered, start=1):
        stops.append(
            {
                "rank": idx,
                "site_id": row.get("site_id"),
                "address": row.get("address"),
                "zip": row.get("zip"),
                "lat": row.get("lat"),
                "lon": row.get("lon"),
                "priority_score": row.get("priority_score"),
                "lead_temperature": row.get("lead_temperature"),
                "operator_next_step": row.get("operator_next_step"),
                "operator_status": row.get("operator_status"),
                "route_score": round(_route_priority_score(row), 2),
            }
        )

    return {
        "count": len(stops),
        "scope": {"zip": zip, "h3_cell": h3_cell, "include_warm": include_warm},
        "stops": stops,
    }


@app.get("/api/v1/operator/route-plan.csv")
def operator_route_plan_csv(
    zip: str | None = None,
    h3_cell: str | None = None,
    max_stops: int = 20,
    include_warm: bool = True,
) -> PlainTextResponse:
    plan = operator_route_plan(zip=zip, h3_cell=h3_cell, max_stops=max_stops, include_warm=include_warm)
    stops = list(plan.get("stops") or [])

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "rank",
            "site_id",
            "address",
            "zip",
            "lat",
            "lon",
            "priority_score",
            "lead_temperature",
            "operator_next_step",
            "operator_status",
            "route_score",
        ],
    )
    writer.writeheader()
    for row in stops:
        writer.writerow(
            {
                "rank": row.get("rank"),
                "site_id": row.get("site_id"),
                "address": row.get("address"),
                "zip": row.get("zip"),
                "lat": row.get("lat"),
                "lon": row.get("lon"),
                "priority_score": row.get("priority_score"),
                "lead_temperature": row.get("lead_temperature"),
                "operator_next_step": row.get("operator_next_step"),
                "operator_status": (row.get("operator_status") or {}).get("status"),
                "route_score": row.get("route_score"),
            }
        )

    scope_bits = []
    if zip:
        scope_bits.append(f"zip-{zip}")
    if h3_cell:
        scope_bits.append(f"h3-{h3_cell}")
    scope_slug = "_".join(scope_bits) if scope_bits else "all"
    filename = f"demandgrid-route-{scope_slug}.csv"

    return PlainTextResponse(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/v1/agent/capabilities")
def agent_capabilities() -> Dict[str, Any]:
    return {
        "framework": CHOW_AGENT_FRAMEWORK,
        "mode": "tool-routed + gpt-grounded-synthesis",
        "description": "Chow mode for DemandGrid: an execution-oriented operator loop grounded in live platform tools and polished with a pinned GPT model.",
        "model": f"{DEMANDGRID_PI_PROVIDER}/{DEMANDGRID_PI_MODEL}",
        "thinking_level": DEMANDGRID_PI_THINKING,
        "tools": [
            "list_zips",
            "heatmap_summary",
            "top_leads",
            "site_detail",
            "route_plan",
            "set_operator_status",
            "agent_task_next",
            "agent_task_claim",
            "execution_summary",
            "create_supervised_run",
            "dispatch_calling_session",
            "dispatch_outreach_job",
            "create_calling_session",
            "create_outreach_job",
        ],
        "examples": [
            "What should I work next?",
            "Claim next task",
            "Prepare supervised outreach for this site",
            "Show execution state for this site",
            "Queue a call for this site",
            "Queue an email for this site",
            "Dispatch the supervised call from the dashboard",
            "Dispatch the email preview from the dashboard",
            "Give me a 20 second pitch",
        ],
    }


@app.post("/api/v1/agent/chat")
def agent_chat(payload: AgentChatPayload) -> Dict[str, Any]:
    message_raw = str(payload.message or "").strip()
    if not message_raw:
        raise HTTPException(status_code=400, detail="message is required")

    message = message_raw.lower()
    max_results = max(1, min(int(payload.max_results or 8), 20))

    scope_zip = str(payload.zip).strip() if payload.zip else None
    if scope_zip in {"", "all", "__all__"}:
        scope_zip = None
    scope_h3 = str(payload.h3_cell).strip().lower() if payload.h3_cell else None
    if scope_h3 == "":
        scope_h3 = None

    zip_from_text = _extract_zip(message_raw)
    if zip_from_text:
        scope_zip = zip_from_text

    h3_from_text = _extract_h3_cell(message_raw)
    if h3_from_text:
        scope_h3 = h3_from_text

    site_id = (payload.site_id or _extract_site_id(message_raw) or "").strip().lower() or None

    tool_calls: List[Dict[str, Any]] = []
    cards: List[Dict[str, Any]] = []

    # Help / capability path
    if any(k in message for k in ["help", "capabilities", "what can you do", "how do i use"]):
        tool_calls.append({"tool": "agent_capabilities", "args": {}, "result_count": 8})
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "help",
            "reply": (
                "I'm Chow inside DemandGrid. I can pull the next task, rank top leads, explain a site, plan a route, prepare a supervised outreach run, queue a supervised call, queue a dry-run email job, and update workflow or outcomes. Dispatching the actual call/email adapter stays approval-gated in the dashboard execution lane. "
                "Try: 'what should I work next', 'claim next task', 'prepare supervised outreach for this site', 'queue a call for this site', or 'give me a 20 second pitch'."
            ),
            "tool_calls": tool_calls,
            "cards": [],
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "suggested_actions": [
                "What should I work next?",
                "Claim next task",
                "Queue a call for this site",
                "Queue an email for this site",
            ],
        })

    rows = _scoped_rows(scope_zip, scope_h3)
    tool_calls.append(
        {
            "tool": "scope_rows",
            "args": {"zip": scope_zip or "all", "h3_cell": scope_h3},
            "result_count": len(rows),
        }
    )

    if not rows:
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "empty_scope",
            "reply": "I could not find scored rows in that scope. Try another ZIP or clear the hex/site selection.",
            "tool_calls": tool_calls,
            "cards": [],
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "suggested_actions": ["Top leads in 03253", "Why this site", "Plan route"],
        })

    if any(k in message for k in ["what should i work next", "what should i do next", "next task", "work next"]):
        task = _next_agent_task(zip=scope_zip, h3_cell=scope_h3, agent_id="chow")
        tool_calls.append({"tool": "agent_task_next", "args": {"zip": scope_zip or "all", "h3_cell": scope_h3, "agent_id": "chow"}, "result_count": 1 if task else 0})
        cards = [task.get("site")] if task and isinstance(task.get("site"), dict) else []
        if not task:
            reply = "No open Chow tasks are available in this scope right now."
        else:
            site = task.get("site") or {}
            action = str(task.get("primary_action") or "review").replace("_", " ")
            reply = (
                f"Work `{site.get('address')}` next. Primary action: {action}. "
                f"Queue bucket is {str(((task.get('work_queue') or {}).get('reason_label') or (task.get('work_queue') or {}).get('bucket') or 'park')).replace('_', ' ')}. "
                f"{str(((task.get('next_action') or {}).get('reason') or '')).strip()}"
            )
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "task_next",
            "reply": reply,
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "task": task,
            "suggested_actions": ["Claim next task", "Give me a 20 second pitch", "Plan route for today"],
        })

    if any(k in message for k in ["claim next task", "claim this task"]):
        task = _next_agent_task(zip=scope_zip, h3_cell=scope_h3, agent_id="chow")
        if not task:
            return _finalize_agent_response(message_raw, {
                "framework": CHOW_AGENT_FRAMEWORK,
                "intent": "task_claim",
                "reply": "No claimable Chow task is available in this scope right now.",
                "tool_calls": tool_calls,
                "cards": [],
                "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
                "suggested_actions": ["Top hot leads", "Plan route"],
            })
        claimed = agent_task_claim(str(task.get("task_id") or ""), AgentTaskClaimPayload(agent_id="chow", note="claimed_via_chat")).get("task")
        tool_calls.append({"tool": "agent_task_claim", "args": {"task_id": task.get("task_id"), "agent_id": "chow"}, "result_count": 1})
        cards = [claimed.get("site")] if claimed and isinstance(claimed.get("site"), dict) else []
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "task_claim",
            "reply": f"Claimed `{(claimed or {}).get('task_id')}` for Chow. Open the lead, use the opener, then either queue the call/email step or log the result.",
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "task": claimed,
            "suggested_actions": ["Give me a 20 second pitch", "Queue a call for this site", "Queue an email for this site"],
        })

    if site_id and any(k in message for k in ["prepare supervised outreach", "prepare supervised run", "supervised run", "approval run"]):
        run = orchestrator_run_create(OrchestratorRunCreatePayload(site_id=site_id, approval_required=True, auto_execute=False, execution_mode="agent_assist", strict_guardrails=True, call_direction="outbound"))
        summary = _execution_summary_for_site(site_id)
        row = _data_cache()["by_site"].get(site_id)
        cards = [_site_card(_attach_operator_status(row))] if row else []
        tool_calls.append({"tool": "create_supervised_run", "args": {"site_id": site_id, "approval_required": True}, "result_count": 1})
        pending_actions = list(((summary.get("supervision") or {}).get("pending_actions") or []))
        pending_text = ", ".join([str(action.get("action_type") or "").replace("_", " ") for action in pending_actions]) or "no pending approvals"
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "prepare_supervised_outreach",
            "reply": f"Prepared a supervised Chow run for {site_id}. Pending approvals: {pending_text}.",
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "orchestrator_run": run,
            "execution": summary,
            "suggested_actions": ["Approve the call step", "Approve the email step", "Why this site"],
        })

    if site_id and any(k in message for k in ["execution state", "approval state", "supervision state", "show supervised state"]):
        summary = _execution_summary_for_site(site_id)
        row = _data_cache()["by_site"].get(site_id)
        cards = [_site_card(_attach_operator_status(row))] if row else []
        tool_calls.append({"tool": "execution_summary", "args": {"site_id": site_id}, "result_count": 1})
        supervision = summary.get("supervision") or {}
        blockers = ", ".join([str(v).replace("_", " ") for v in (supervision.get("blockers") or [])]) or "none"
        pending_actions = ", ".join([str(action.get("action_type") or "").replace("_", " ") for action in (supervision.get("pending_actions") or [])]) or "none"
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "execution_state",
            "reply": f"Supervised execution for {site_id}: pending approvals = {pending_actions}; blockers = {blockers}; recommended next step = {str(supervision.get('recommended_next_step') or 'prepare_supervised_run').replace('_', ' ')}.",
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "execution": summary,
            "suggested_actions": ["Prepare supervised outreach", "Queue a call for this site", "Queue an email for this site"],
        })

    if site_id and any(k in message for k in ["queue a call", "queue call", "call this lead", "start call", "queue chow call"]):
        session = calling_session_create(CallingSessionCreatePayload(site_id=site_id, preferred_channels=["phone"], execution_mode="agent_assist", strict_guardrails=True, call_direction="outbound"))
        row = _data_cache()["by_site"].get(site_id)
        cards = [_site_card(_attach_operator_status(row))] if row else []
        tool_calls.append({"tool": "create_calling_session", "args": {"site_id": site_id}, "result_count": 1})
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "queue_call",
            "reply": f"Queued a supervised Chow calling session for {site_id}. This creates the call brief + session state in DemandGrid; it does not place a live call by itself yet.",
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "calling_session": session,
            "suggested_actions": ["Give me a 20 second pitch", "Why this site", "Mark site contacted"],
        })

    if site_id and any(k in message for k in ["queue an email", "queue email", "email this lead", "send email"]):
        job = outreach_job_create(OutreachJobCreatePayload(site_id=site_id, requested_channel="email", execution_mode="agent_assist", strict_guardrails=True, dry_run=True))
        row = _data_cache()["by_site"].get(site_id)
        cards = [_site_card(_attach_operator_status(row))] if row else []
        tool_calls.append({"tool": "create_outreach_job", "args": {"site_id": site_id, "requested_channel": "email", "dry_run": True}, "result_count": 1})
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "queue_email",
            "reply": f"Queued a Chow email job for {site_id} in dry-run mode. DemandGrid now has the playbook, policy decision, and job lifecycle state — but it has not sent a real email yet.",
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "outreach_job": job,
            "suggested_actions": ["Why this site", "Give me a 20 second pitch", "Plan route"],
        })

    # Write intent: operator status update
    status_update = _infer_status_update(message)
    if status_update and site_id and any(k in message for k in ["mark", "set", "update"]):
        data = _data_cache()
        row = data["by_site"].get(site_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
        updated = _set_operator_status(site_id=site_id, status=status_update, note="via agent chat")
        enriched = _attach_operator_status(row)
        cards = [_site_card(enriched)]
        tool_calls.append(
            {
                "tool": "set_operator_status",
                "args": {"site_id": site_id, "status": status_update},
                "result_count": 1,
            }
        )
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "set_status",
            "reply": f"Updated {site_id} to `{status_update}`.",
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "updated_status": updated,
            "suggested_actions": ["Explain this site", "Plan route", "Top hot leads"],
        })

    # Pitch intent for a selected site
    if site_id and any(k in message for k in ["pitch", "script", "opener", "what do i say", "20 second"]):
        data = _data_cache()
        row = data["by_site"].get(site_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

        enriched = _attach_operator_status(row)
        investigation = _build_investigation_payload(enriched)
        outreach = _build_outreach_payload(investigation)
        cards = [_site_card(enriched)]
        tool_calls.append({"tool": "site_detail", "args": {"site_id": site_id}, "result_count": 1})
        tool_calls.append({"tool": "site_pitch", "args": {"site_id": site_id}, "result_count": 1})

        opener = (
            str(enriched.get("recommended_pitch") or "").strip()
            or next((str(v).strip() for v in (outreach.get("message_angles") or []) if str(v).strip()), "")
            or str(enriched.get("operator_pitch_angle") or "").strip()
            or "Start with the strongest fit signal and ask for the next step."
        )
        why_now = (
            str(enriched.get("why_now_summary") or "").strip()
            or "This address is ranking well enough to justify immediate outreach."
        )
        cta = (
            str(outreach.get("cta") or "").strip()
            or str(enriched.get("operator_action_summary") or "").strip()
            or "Ask for the inspection, quote, or follow-up conversation."
        )
        review_flags = [str(flag).strip() for flag in (outreach.get("review_flags") or []) if str(flag).strip()]
        warning = ""
        if review_flags:
            warning = f" Before pushing hard, verify: {', '.join(review_flags[:2]).replace('_', ' ')}."

        reply = (
            f"20-second pitch for {enriched.get('address')}: {opener} "
            f"Why now: {why_now} "
            f"Close with: {cta}.{warning}"
        ).strip()

        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "site_pitch",
            "reply": reply,
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "suggested_actions": ["Why this site", "Mark site contacted", "Plan route"],
        })

    # Explain single site
    if site_id and any(k in message for k in ["why", "explain", "this site", "details", "reason"]):
        data = _data_cache()
        row = data["by_site"].get(site_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
        enriched = _attach_operator_status(row)
        cards = [_site_card(enriched)]
        reasons = list(enriched.get("reasons") or [])[:3]
        tool_calls.append({"tool": "site_detail", "args": {"site_id": site_id}, "result_count": 1})

        reason_text = " ".join([f"- {r}" for r in reasons]) if reasons else "No reason codes available."
        reply = (
            f"{enriched.get('address')} is ranked `{enriched.get('lead_temperature')}` with route score "
            f"{float(enriched.get('sales_route_score') or 0.0):.1f}. Primary product is "
            f"{str(enriched.get('primary_product') or 'solar').replace('_', ' ')}. "
            f"Estimated savings are ${float(enriched.get('annual_savings_usd') or 0.0):,.0f}/yr and confidence is "
            f"{float(enriched.get('confidence') or 0.0) * 100:.0f}%. Reasons: {reason_text}"
        )
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "site_explain",
            "reply": reply,
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "suggested_actions": ["Mark site contacted", "Plan route", "Show similar top leads"],
        })

    # Route plan intent
    if "route" in message:
        include_warm = "hot only" not in message
        plan = operator_route_plan(zip=scope_zip, h3_cell=scope_h3, max_stops=max_results, include_warm=include_warm)
        stops = list(plan.get("stops") or [])
        for s in stops[:max_results]:
            cards.append(
                {
                    "site_id": s.get("site_id"),
                    "address": s.get("address"),
                    "zip": s.get("zip"),
                    "lead_temperature": s.get("lead_temperature"),
                    "operator_next_step": s.get("operator_next_step"),
                    "route_score": s.get("route_score"),
                }
            )
        tool_calls.append(
            {
                "tool": "route_plan",
                "args": {"zip": scope_zip or "all", "h3_cell": scope_h3, "max_stops": max_results, "include_warm": include_warm},
                "result_count": len(stops),
            }
        )

        if not stops:
            reply = "No eligible route stops in this scope."
        else:
            first = stops[0]
            reply = (
                f"Route ready with {len(stops)} stops. First stop: {first.get('address')} "
                f"({first.get('lead_temperature')}, route score {float(first.get('route_score') or 0.0):.1f})."
            )

        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "route_plan",
            "reply": reply,
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "suggested_actions": ["Export route CSV", "Mark first stop visited", "Explain first stop"],
        })

    # Heatmap / cell intent
    if "heatmap" in message or "hex" in message or "cell" in message:
        if scope_zip:
            cells = _zip_cells([r for r in rows if str(r.get("zip") or "") == scope_zip])
        else:
            cells = _aggregate_rows_to_resolution(rows, target_resolution=6)

        top_cells = cells[: max_results]
        cards = [
            {
                "h3_cell": c.get("h3_cell"),
                "site_count": c.get("site_count"),
                "avg_priority_score": c.get("avg_priority_score"),
                "avg_annual_savings_usd": c.get("avg_annual_savings_usd"),
            }
            for c in top_cells
        ]
        tool_calls.append({"tool": "heatmap_summary", "args": {"zip": scope_zip or "all"}, "result_count": len(top_cells)})
        reply = (
            f"Top {len(top_cells)} opportunity cells in scope `{scope_zip or 'all'}` loaded. "
            f"Highest avg-priority cell is {top_cells[0]['h3_cell']} at {float(top_cells[0]['avg_priority_score']):.1f}/100."
            if top_cells
            else "No heatmap cells found in this scope."
        )
        return _finalize_agent_response(message_raw, {
            "framework": CHOW_AGENT_FRAMEWORK,
            "intent": "heatmap_summary",
            "reply": reply,
            "tool_calls": tool_calls,
            "cards": cards,
            "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
            "suggested_actions": ["Open top hex", "Top hot leads", "Plan route"],
        })

    # Default: ranked leads intent
    product_filter = _infer_product_filter(message)
    wants_hot_only = "hot" in message and "warm" not in message

    requires_outage = "outage" in message
    requires_flood = "flood" in message
    requires_storm = "storm" in message or "hail" in message
    requires_equipment = "equipment" in message or "hvac" in message or "age" in message

    filtered = [
        r
        for r in rows
        if str((r.get("operator_status") or {}).get("status") or "unworked") not in {"closed", "skip"}
    ]

    if wants_hot_only:
        filtered = [r for r in filtered if str(r.get("lead_temperature") or "") == "hot"]

    if product_filter:
        filtered = [r for r in filtered if str(r.get("primary_product") or "") == product_filter]

    if requires_outage:
        filtered = [r for r in filtered if str(r.get("outage_trigger_status") or "missing") != "missing"]
    if requires_flood:
        filtered = [r for r in filtered if str(r.get("flood_risk_trigger_status") or "missing") != "missing"]
    if requires_storm:
        filtered = [r for r in filtered if str(r.get("storm_trigger_status") or "missing") != "missing"]
    if requires_equipment:
        filtered = [r for r in filtered if str(r.get("equipment_age_trigger_status") or "missing") != "missing"]

    filtered.sort(key=lambda r: (-_route_priority_score(r), -float(r.get("annual_savings_usd") or 0.0), str(r.get("site_id") or "")))
    picks = filtered[:max_results]
    cards = [_site_card(r) for r in picks]

    tool_calls.append(
        {
            "tool": "top_leads",
            "args": {
                "zip": scope_zip or "all",
                "h3_cell": scope_h3,
                "product": product_filter,
                "hot_only": wants_hot_only,
                "requires_outage": requires_outage,
                "requires_flood": requires_flood,
                "requires_storm": requires_storm,
                "requires_equipment": requires_equipment,
            },
            "result_count": len(picks),
        }
    )

    if not picks:
        reply = "No matching leads in this scope with those filters. Try relaxing trigger/product constraints."
    else:
        sample_bits = []
        for i, p in enumerate(picks[:3], start=1):
            sample_bits.append(
                f"{i}) {p.get('address')} [{str(p.get('primary_product') or '').replace('_', ' ')} / {p.get('lead_temperature')}] "
                f"route {float(p.get('sales_route_score') or 0.0):.1f}"
            )
        reply = (
            f"Top {len(picks)} leads in scope `{scope_zip or 'all'}` ready. "
            + " | ".join(sample_bits)
            + ""
        )

    return _finalize_agent_response(message_raw, {
        "framework": CHOW_AGENT_FRAMEWORK,
        "intent": "top_leads",
        "reply": reply,
        "tool_calls": tool_calls,
        "cards": cards,
        "scope": {"zip": scope_zip or "all", "h3_cell": scope_h3, "site_id": site_id},
        "suggested_actions": ["Why this site", "Plan route", "Mark site contacted"],
    })


@app.get("/api/v1/operator/status/{site_id}")
def get_operator_status(site_id: str) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    return {
        "site_id": site_id,
        "address": row.get("address"),
        "zip": row.get("zip"),
        "h3_cell": row.get("h3_cell"),
        "operator_status": _operator_status_for(site_id),
    }


@app.put("/api/v1/operator/status/{site_id}")
def upsert_operator_status(site_id: str, payload: OperatorStatusPayload) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    status_value = str(payload.status or "").strip()
    if status_value not in ALLOWED_OPERATOR_STATUSES:
        raise HTTPException(status_code=400, detail=f"Unsupported status: {status_value}")

    note = str(payload.note or "").strip()

    store = _read_operator_status_store()
    store[site_id] = {
        "status": status_value,
        "note": note,
        "updated_at": _utc_now_iso(),
    }
    _write_operator_status_store(store)
    _operator_status_cache.cache_clear()

    return {
        "ok": True,
        "site_id": site_id,
        "operator_status": _operator_status_for(site_id),
    }


@app.get("/api/v1/operator/outcome/{site_id}")
def get_lead_outcome(site_id: str) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    return {
        "site_id": site_id,
        "address": row.get("address"),
        "zip": row.get("zip"),
        "h3_cell": row.get("h3_cell"),
        "lead_outcome": _lead_outcome_for(site_id),
    }


@app.put("/api/v1/operator/outcome/{site_id}")
def upsert_lead_outcome(site_id: str, payload: LeadOutcomePayload) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    lead_outcome = _upsert_lead_outcome_record(
        site_id=site_id,
        status_value=str(payload.status or "").strip(),
        note=str(payload.note or ""),
        objection=str(payload.objection or ""),
        reason=str(payload.reason or ""),
        product=str(payload.product or ""),
        realized_revenue_usd=payload.realized_revenue_usd,
        realized_profit_usd=payload.realized_profit_usd,
    )

    return {
        "ok": True,
        "site_id": site_id,
        "lead_outcome": lead_outcome,
    }


@app.get("/api/v1/operator/outcomes")
def list_lead_outcomes(
    status: str | None = None,
    zip: str | None = None,
    h3_cell: str | None = None,
    limit: int = 200,
) -> Dict[str, Any]:
    status_filter = str(status or "").strip()
    if status_filter and status_filter not in ALLOWED_LEAD_OUTCOME_STATUSES:
        raise HTTPException(status_code=400, detail=f"Unsupported lead outcome status: {status_filter}")

    rows = _scoped_rows(zip, h3_cell)
    payload_rows: List[Dict[str, Any]] = []
    for row in rows:
        outcome = row.get("lead_outcome") or {}
        current_status = str(outcome.get("status") or "unknown")
        if status_filter and current_status != status_filter:
            continue
        if not status_filter and current_status == "unknown":
            continue
        payload_rows.append(
            {
                "site_id": row.get("site_id"),
                "address": row.get("address"),
                "zip": row.get("zip"),
                "h3_cell": row.get("h3_cell"),
                "primary_product": row.get("primary_product"),
                "lead_temperature": row.get("lead_temperature"),
                "sales_route_score": round(float(row.get("sales_route_score") or 0.0), 1),
                "operator_status": row.get("operator_status"),
                "lead_outcome": outcome,
            }
        )

    payload_rows.sort(
        key=lambda item: (
            str((item.get("lead_outcome") or {}).get("updated_at") or ""),
            float(item.get("sales_route_score") or 0.0),
        ),
        reverse=True,
    )
    limited = payload_rows[: max(1, min(limit, 500))]
    return {
        "count": len(limited),
        "total_matching": len(payload_rows),
        "status_filter": status_filter or None,
        "items": limited,
    }


@app.get("/api/v1/operator/outcomes/summary")
def lead_outcome_summary(
    zip: str | None = None,
    h3_cell: str | None = None,
    site_id: str | None = None,
) -> Dict[str, Any]:
    rows = _scoped_rows(zip, h3_cell)
    site_row = None
    if site_id:
        data = _data_cache()
        site_row = data["by_site"].get(site_id)
        if not site_row:
            raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
        if not zip:
            zip = str(site_row.get("zip") or "").strip() or None
        if not h3_cell:
            h3_cell = str(site_row.get("h3_cell") or "").strip() or None
        if site_row not in rows:
            rows = rows + [site_row]

    known_outcomes = [row for row in rows if str(((row.get("lead_outcome") or {}).get("status") or "unknown")).strip().lower() != "unknown"]
    global_summary = _build_outcome_scope_summary(known_outcomes, label="global_scope")

    same_zip_rows: List[Dict[str, Any]] = []
    same_product_rows: List[Dict[str, Any]] = []
    same_zip_product_rows: List[Dict[str, Any]] = []
    site_context: Dict[str, Any] | None = None
    next_action = None
    if site_row:
        site_zip = str(site_row.get("zip") or "").strip()
        site_product = str(site_row.get("primary_product") or "").strip().lower()
        same_zip_rows = [row for row in known_outcomes if str(row.get("zip") or "").strip() == site_zip]
        same_product_rows = [row for row in known_outcomes if str((row.get("lead_outcome") or {}).get("product") or row.get("primary_product") or "").strip().lower() == site_product]
        same_zip_product_rows = [
            row
            for row in same_zip_rows
            if str((row.get("lead_outcome") or {}).get("product") or row.get("primary_product") or "").strip().lower() == site_product
        ]
        site_context = {
            "site_id": str(site_row.get("site_id") or ""),
            "zip": site_zip,
            "primary_product": site_product,
            "operator_status": (site_row.get("operator_status") or {}).get("status"),
            "lead_outcome_status": (site_row.get("lead_outcome") or {}).get("status"),
        }
        next_action = _build_operator_next_action(
            site_row,
            {
                "global": global_summary,
                "same_zip": _build_outcome_scope_summary(same_zip_rows, label="same_zip"),
                "same_product": _build_outcome_scope_summary(same_product_rows, label="same_product"),
                "same_zip_product": _build_outcome_scope_summary(same_zip_product_rows, label="same_zip_product"),
            },
        )

    same_zip_summary = _build_outcome_scope_summary(same_zip_rows, label="same_zip") if site_row else None
    same_product_summary = _build_outcome_scope_summary(same_product_rows, label="same_product") if site_row else None
    same_zip_product_summary = _build_outcome_scope_summary(same_zip_product_rows, label="same_zip_product") if site_row else None

    return {
        "scope": {
            "zip": zip,
            "h3_cell": h3_cell,
            "site_id": site_id,
        },
        "site_context": site_context,
        "global": global_summary,
        "same_zip": same_zip_summary,
        "same_product": same_product_summary,
        "same_zip_product": same_zip_product_summary,
        "next_action": next_action,
    }


@app.post("/api/v1/outcomes")
def outcome_write(payload: OutcomeWritePayload) -> Dict[str, Any]:
    site_id = str(payload.site_id or "").strip()
    if not site_id:
        raise HTTPException(status_code=400, detail="site_id is required")

    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    signal_keys = [str(v).strip() for v in (payload.attribution_signal_keys or []) if str(v).strip()]
    if not signal_keys:
        signal_keys = _signal_keys_for_row(row)

    lead_outcome = _upsert_lead_outcome_record(
        site_id=site_id,
        status_value=str(payload.status or "").strip(),
        note=str(payload.note or ""),
        objection=str(payload.objection or ""),
        reason=str(payload.reason or ""),
        product=str(payload.product or row.get("primary_product") or ""),
        realized_revenue_usd=payload.realized_revenue_usd,
        realized_profit_usd=payload.realized_profit_usd,
        attribution_channel=str(payload.attribution_channel or ""),
        attribution_playbook_id=str(payload.attribution_playbook_id or ""),
        attribution_orchestrator_run_id=str(payload.attribution_orchestrator_run_id or ""),
        attribution_signal_keys=signal_keys,
        attribution_source_session_id=str(payload.attribution_source_session_id or ""),
        attribution_source_job_id=str(payload.attribution_source_job_id or ""),
    )

    return {
        "framework": LEARNING_FRAMEWORK,
        "site_id": site_id,
        "lead_outcome": lead_outcome,
    }


@app.get("/api/v1/outcomes/summary")
def outcomes_summary(zip: str | None = None, h3_cell: str | None = None) -> Dict[str, Any]:
    return _build_learning_summary(zip, h3_cell)


@app.post("/api/v1/learning/retrain-jobs")
def learning_retrain_job(payload: LearningRetrainJobPayload) -> Dict[str, Any]:
    job = _build_learning_job_result(payload)
    _persist_learning_job(job)
    return job


@app.get("/api/v1/governance/policies")
def governance_policies() -> Dict[str, Any]:
    policy = _governance_policy_config()
    return {
        "framework": ORCHESTRATOR_FRAMEWORK,
        "policy": {key: value for key, value in policy.items() if key != "_source"},
        "policy_source": str(policy.get("_source") or "default"),
    }


@app.post("/api/v1/governance/policies/validate")
def governance_validate(payload: GovernanceValidationPayload) -> Dict[str, Any]:
    run = _orchestrator_run_for(str(payload.run_id or "").strip())
    if not run:
        raise HTTPException(status_code=404, detail=f"Unknown orchestrator run {payload.run_id}")
    action = next((a for a in (run.get("actions") or []) if str(a.get("action_id") or "") == str(payload.action_id or "").strip()), None)
    if not action:
        raise HTTPException(status_code=404, detail=f"Unknown action_id {payload.action_id}")
    result = _governance_validation_result(
        run=run,
        action=action,
        actor_id=str(payload.actor_id or ""),
        actor_role=str(payload.actor_role or "manager"),
    )
    run = _append_governance_audit(run, {"event": "policy_validate", **result})
    _persist_orchestrator_run(run)
    return result


@app.get("/api/v1/manager/command")
def manager_command(site_id: str | None = None, run_id: str | None = None) -> Dict[str, Any]:
    if not site_id and not run_id:
        raise HTTPException(status_code=400, detail="site_id or run_id is required")
    return _manager_command_payload(site_id=site_id, run_id=run_id)


def _slug_token(value: Any) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return token or "unknown"


def _account_id_for_row(row: Dict[str, Any]) -> str:
    site_id = str(row.get("site_id") or "")
    zip_code = _slug_token(row.get("zip"))
    stem = site_id[-8:] if len(site_id) >= 8 else _slug_token(site_id)
    return f"acct_{zip_code}_{stem}"


def _contact_id_for_row(row: Dict[str, Any]) -> str:
    site_id = str(row.get("site_id") or "")
    stem = site_id[-10:] if len(site_id) >= 10 else _slug_token(site_id)
    return f"contact_{stem}"


def _playbook_default_objective(primary_product: str, lead_temperature: str) -> str:
    product = str(primary_product or "opportunity").replace("_", " ").strip() or "opportunity"
    temperature = str(lead_temperature or "warm").strip().lower() or "warm"
    if temperature == "hot":
        return f"Qualify and convert the {product} opportunity while urgency is high."
    if temperature == "skip":
        return f"Resolve whether the {product} opportunity should stay suppressed or be reactivated."
    return f"Advance the {product} opportunity to a concrete next step."


def _ordered_channel_sequence(recommended_channel: Any, preferred_channels: List[str] | None = None) -> List[str]:
    allowed = {"phone", "sms", "email", "partner", "review", "field_visit"}
    order: List[str] = []
    for raw in list(preferred_channels or []) + [recommended_channel, "phone", "sms", "email"]:
        channel = _slug_token(raw).replace("-", "_")
        if channel in allowed and channel not in order:
            order.append(channel)
    return order or ["email"]


def _playbook_objection_defaults(primary_product: str) -> List[Dict[str, str]]:
    key = str(primary_product or "").strip().lower()
    defaults: Dict[str, List[Dict[str, str]]] = {
        "solar": [
            {"objection": "too expensive", "handling_angle": "Lead with modeled annual savings, utility-rate pressure, and next-step options instead of opening on system price."},
            {"objection": "not interested", "handling_angle": "Use the best evidence-backed why-now trigger and ask for a light qualification, not a hard close."},
            {"objection": "timing", "handling_angle": "Anchor on current bill pain, outage/flood risk, or permit history and ask for a scheduled follow-up window."},
        ],
        "roofing": [
            {"objection": "already have a roofer", "handling_angle": "Position as a fast second-look inspection with trigger-backed urgency and no-friction next step."},
            {"objection": "timing", "handling_angle": "Use storm/flood/permit evidence to frame why delay increases risk and offer a narrow booking window."},
            {"objection": "too expensive", "handling_angle": "Focus first on inspection findings and loss prevention before full replacement economics."},
        ],
        "hvac_heat_pump": [
            {"objection": "system still works", "handling_angle": "Use equipment-age or permit history to frame efficiency and replacement-timing risk without overstating failure certainty."},
            {"objection": "too expensive", "handling_angle": "Lead with operating-cost reduction and comfort/resilience benefits before quote detail."},
            {"objection": "call me later", "handling_angle": "Offer a specific seasonal follow-up tied to a concrete trigger rather than a vague future touch."},
        ],
        "battery_backup": [
            {"objection": "power rarely goes out", "handling_angle": "Use outage/reliability evidence and critical-load framing instead of generic backup-power fear."},
            {"objection": "already have generator", "handling_angle": "Position battery as quieter, automatic, and solar-compatible rather than arguing against the generator."},
            {"objection": "too expensive", "handling_angle": "Tie value to outage frequency, continuity, and stacked benefits instead of sticker price alone."},
        ],
    }
    return list(defaults.get(key) or defaults.get("solar") or [])


def _learning_rows_for_playbooks() -> List[Dict[str, Any]]:
    data = _data_cache()
    by_site = data.get("by_site") or {}
    store = _lead_outcome_cache()
    rows: List[Dict[str, Any]] = []
    for site_id, outcome in store.items():
        if str((outcome or {}).get("status") or "unknown").strip().lower() == "unknown":
            continue
        row = by_site.get(str(site_id))
        if not row:
            continue
        enriched = dict(row)
        enriched["address"] = _clean_address_text(row.get("address"))
        enriched["operator_status"] = _operator_status_for(str(site_id))
        enriched["lead_outcome"] = outcome
        rows.append(enriched)
    return rows


def _playbook_learning_context(row: Dict[str, Any]) -> Dict[str, Any]:
    learning_rows = _learning_rows_for_playbooks()
    zip_code = str(row.get("zip") or "").strip()
    product = str((row.get("primary_product") or "")).strip().lower()
    same_zip = [r for r in learning_rows if str(r.get("zip") or "").strip() == zip_code]
    same_product = [r for r in learning_rows if str((r.get("lead_outcome") or {}).get("product") or r.get("primary_product") or "").strip().lower() == product]
    same_zip_product = [
        r
        for r in same_zip
        if str((r.get("lead_outcome") or {}).get("product") or r.get("primary_product") or "").strip().lower() == product
    ]
    preferred_scope = same_zip_product or same_product or same_zip or learning_rows
    return {
        "global": _build_outcome_scope_summary(learning_rows, label="global_scope") if learning_rows else None,
        "same_zip": _build_outcome_scope_summary(same_zip, label="same_zip") if same_zip else None,
        "same_product": _build_outcome_scope_summary(same_product, label="same_product") if same_product else None,
        "same_zip_product": _build_outcome_scope_summary(same_zip_product, label="same_zip_product") if same_zip_product else None,
        "preferred_scope": _build_outcome_scope_summary(preferred_scope, label="preferred_scope") if preferred_scope else None,
    }


def _compile_playbook(
    *,
    row: Dict[str, Any],
    objective: str | None = None,
    execution_mode: str = "rep_assist",
    preferred_channels: List[str] | None = None,
    strict_guardrails: bool = True,
) -> Dict[str, Any]:
    site_id = str(row.get("site_id") or "")
    row = _attach_operator_status(row)
    investigation = _build_investigation_payload(row)
    outreach = _build_outreach_payload(investigation)
    decision = decision_site(site_id)
    signals = _signal_snapshot_for_row(row)
    learning = _playbook_learning_context(row)
    next_action = _build_operator_next_action(
        row,
        learning_scopes={
            "same_zip": learning.get("same_zip") or {},
            "same_product": learning.get("same_product") or {},
            "same_zip_product": learning.get("same_zip_product") or {},
        },
    )

    recommended_channel = outreach.get("recommended_channel")
    channel_order = _ordered_channel_sequence(recommended_channel, preferred_channels)
    compile_mode = _slug_token(execution_mode).replace("-", "_") or "rep_assist"
    compiled_at = _utc_now_iso()
    playbook_nonce = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    playbook_id = f"playbook_{_slug_token(site_id)}_{playbook_nonce}"
    resolved_objective = str(objective or _playbook_default_objective(row.get("primary_product"), row.get("lead_temperature"))).strip()

    guardrail_flags = ["capture_outcome", "stop_on_terminal_state"]
    if strict_guardrails:
        guardrail_flags.extend(["respect_outreach_policy", "require_manual_review_on_flags"])
    if outreach.get("compliance_flags"):
        guardrail_flags.append("blocked_auto_send")
    if investigation.get("review_flags"):
        guardrail_flags.append("review_flag_present")
    guardrail_flags = list(dict.fromkeys([flag for flag in guardrail_flags if flag]))

    stop_conditions = [
        "lead outcome becomes won or lost",
        "operator status becomes closed or skip",
        "prospect gives explicit do-not-contact or hard no",
    ]
    if strict_guardrails:
        stop_conditions.append("policy/compliance flags require manual review before send")

    first_channel = channel_order[0] if channel_order else "email"
    second_channel = channel_order[1] if len(channel_order) > 1 else first_channel
    auto_send_allowed = bool(outreach.get("auto_outreach_eligible")) and not bool(outreach.get("compliance_flags"))
    message_angles = [str(v).strip() for v in (outreach.get("message_angles") or []) if str(v).strip()]
    first_touch_instruction = message_angles[0] if message_angles else str(outreach.get("cta") or "Make contact").strip()

    steps: List[Dict[str, Any]] = [
        {
            "step_id": "review_context",
            "title": "Review the evidence pack and choose the opener",
            "channel": "workspace",
            "mode": "human",
            "instruction": str(next_action.get("rationale") or investigation.get("why_now_summary") or "Review why now before touching the lead.").strip(),
            "success_signal": "Rep or agent can explain why this lead is ranked now and what proof supports the move.",
            "stop_conditions": stop_conditions,
            "guardrail_flags": guardrail_flags,
        }
    ]

    if auto_send_allowed:
        steps.append(
            {
                "step_id": "first_touch",
                "title": f"Run the first touch on {first_channel}",
                "channel": first_channel,
                "mode": "agent" if compile_mode != "rep_assist" else "human",
                "instruction": first_touch_instruction,
                "success_signal": "Lead responds, books next step, or is marked contacted with a clear next action.",
                "stop_conditions": stop_conditions,
                "guardrail_flags": guardrail_flags,
            }
        )
        steps.append(
            {
                "step_id": "follow_up_touch",
                "title": f"If no reply, run the follow-up on {second_channel}",
                "channel": second_channel,
                "mode": "agent" if compile_mode == "agent_autonomous" else "human",
                "instruction": str(outreach.get("cta") or "Follow up with a tighter ask and a concrete next step.").strip(),
                "success_signal": "Lead is qualified, scheduled, suppressed, or moved to a later dated follow-up.",
                "stop_conditions": stop_conditions,
                "guardrail_flags": guardrail_flags,
            }
        )
    else:
        steps.append(
            {
                "step_id": "manual_review",
                "title": "Resolve suppression or review flags before any send",
                "channel": "review",
                "mode": "human",
                "instruction": "Do not auto-send. Resolve the policy/compliance/review flags, then decide whether to proceed or suppress.",
                "success_signal": "Lead is either cleared for outreach with a justified reason or intentionally left suppressed.",
                "stop_conditions": stop_conditions,
                "guardrail_flags": guardrail_flags,
            }
        )

    steps.append(
        {
            "step_id": "log_outcome",
            "title": "Capture the real outcome and economics",
            "channel": "workspace",
            "mode": "human",
            "instruction": "After the touch, update status, outcome, objection, reason, and realized value so ranking and policy can learn.",
            "success_signal": "Outcome record is complete enough to explain what happened and whether the lane made money.",
            "stop_conditions": stop_conditions,
            "guardrail_flags": guardrail_flags,
        }
    )

    preferred_scope = learning.get("preferred_scope") or {}
    objection_defaults = _playbook_objection_defaults(str(row.get("primary_product") or ""))
    learned_objections = [
        {
            "objection": item.get("label"),
            "handling_angle": f"Observed in {preferred_scope.get('label') or 'historical scope'} ({item.get('count')} occurrences). Handle directly and log whether the angle worked.",
        }
        for item in (preferred_scope.get("top_objections") or [])
        if item.get("label")
    ]
    objection_map = learned_objections + [item for item in objection_defaults if item.get("objection") not in {x.get("objection") for x in learned_objections}]

    return {
        "framework": PLAYBOOK_COMPILER_FRAMEWORK,
        "playbook_id": playbook_id,
        "compiled_at": compiled_at,
        "site_id": site_id,
        "objective": resolved_objective,
        "execution_mode": compile_mode,
        "channel_order": channel_order,
        "strict_guardrails": strict_guardrails,
        "guardrail_flags": guardrail_flags,
        "stop_conditions": stop_conditions,
        "opportunity": {
            "address": row.get("address"),
            "zip": row.get("zip"),
            "primary_product": row.get("primary_product"),
            "secondary_product": row.get("secondary_product"),
            "lead_temperature": row.get("lead_temperature"),
            "operator_status": (row.get("operator_status") or {}).get("status"),
            "opportunity_score": decision.get("opportunity_score"),
            "win_probability_proxy": decision.get("win_probability_proxy"),
            "confidence": decision.get("confidence"),
        },
        "playbook": {
            "objective": resolved_objective,
            "steps": steps,
            "objection_map": objection_map[:6],
            "next_best_action": decision.get("next_best_action"),
            "recommended_channel": recommended_channel,
        },
        "learning_context": learning,
        "refs": {
            "decision_ref": f"/api/v1/decision/site/{site_id}",
            "revenue_graph_ref": f"/api/v1/revenue-graph/site/{site_id}",
            "signals_ref": f"/api/v1/signals/site/{site_id}",
            "outreach_ref": f"/api/v1/outreach/site/{site_id}",
            "investigation_ref": f"/api/v1/investigation/site/{site_id}",
        },
        "policy_snapshot": outreach.get("policy"),
        "signal_summary": signals.get("summary"),
        "notes": {
            "auto_send_allowed": auto_send_allowed,
            "compliance_flags": outreach.get("compliance_flags") or [],
            "review_flags": investigation.get("review_flags") or [],
        },
    }


def _normalize_outreach_channel(value: Any) -> str | None:
    channel = _slug_token(value).replace("-", "_") if value not in (None, "", "None") else ""
    allowed = {"phone", "sms", "email", "partner", "review", "field_visit"}
    return channel if channel in allowed else None


def _build_outreach_job_record(
    *,
    site_id: str,
    playbook: Dict[str, Any],
    requested_channel: str | None,
    idempotency_key: str | None,
    dry_run: bool,
) -> Dict[str, Any]:
    outreach_ref = str((playbook.get("refs") or {}).get("outreach_ref") or "")
    recommended_channel = str((playbook.get("playbook") or {}).get("recommended_channel") or "email")
    normalized_requested_channel = _normalize_outreach_channel(requested_channel)
    resolved_channel = normalized_requested_channel or recommended_channel
    compliance_flags = list(((playbook.get("notes") or {}).get("compliance_flags") or []))
    review_flags = list(((playbook.get("notes") or {}).get("review_flags") or []))
    auto_send_allowed = bool((playbook.get("notes") or {}).get("auto_send_allowed"))

    policy_decision = "allow"
    block_reasons: List[str] = []
    if compliance_flags:
        policy_decision = "blocked"
        block_reasons.extend([str(flag) for flag in compliance_flags if str(flag).strip()])
    elif resolved_channel == "review":
        policy_decision = "blocked"
        block_reasons.append("review_channel_only")
    elif not auto_send_allowed:
        policy_decision = "manual_review"
        block_reasons.append("auto_send_not_allowed")

    created_at = _utc_now_iso()
    job_id = f"outreach_job_{_slug_token(site_id)}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    initial_status = "blocked" if policy_decision == "blocked" else "queued"
    dispatch_mode = "dry_run" if dry_run else "live_stub"
    event_type = "blocked" if initial_status == "blocked" else "queued"
    event_detail = "Job blocked by policy." if initial_status == "blocked" else "Job accepted into outreach queue."

    return {
        "framework": OUTREACH_AGENT_FRAMEWORK,
        "job_id": job_id,
        "site_id": site_id,
        "playbook_id": playbook.get("playbook_id"),
        "idempotency_key": str(idempotency_key or "").strip() or None,
        "status": initial_status,
        "dispatch_mode": dispatch_mode,
        "requested_channel": normalized_requested_channel,
        "resolved_channel": resolved_channel,
        "created_at": created_at,
        "updated_at": created_at,
        "site": dict(playbook.get("opportunity") or {}),
        "objective": playbook.get("objective"),
        "policy": {
            "decision": policy_decision,
            "block_reasons": block_reasons,
            "compliance_flags": compliance_flags,
            "review_flags": review_flags,
            "strict_guardrails": bool(playbook.get("strict_guardrails")),
            "policy_snapshot": playbook.get("policy_snapshot") or {},
        },
        "send_context": {
            "channel_order": list(playbook.get("channel_order") or []),
            "recommended_channel": recommended_channel,
            "resolved_channel": resolved_channel,
            "next_best_action": (playbook.get("playbook") or {}).get("next_best_action"),
            "message_hint": (((playbook.get("playbook") or {}).get("steps") or [{}])[1] or {}).get("instruction")
            if len((playbook.get("playbook") or {}).get("steps") or []) > 1
            else None,
            "outreach_ref": outreach_ref or f"/api/v1/outreach/site/{site_id}",
        },
        "delivery": {
            "attempt_count": 0,
            "provider_message_id": None,
            "last_event_type": event_type,
            "last_event_at": created_at,
            "reply_received": False,
        },
        "event_log": [
            {
                "event_type": event_type,
                "status": initial_status,
                "detail": event_detail,
                "event_at": created_at,
                "metadata": {"dispatch_mode": dispatch_mode},
            }
        ],
    }


def _apply_outreach_job_event(job: Dict[str, Any], payload: OutreachJobEventPayload) -> Dict[str, Any]:
    event_type = _slug_token(payload.event_type).replace("-", "_")
    if not event_type:
        raise HTTPException(status_code=400, detail="event_type is required")

    status_map = {
        "queued": "queued",
        "dispatch_requested": "queued",
        "provider_queued": "queued",
        "sent": "sent",
        "delivered": "delivered",
        "reply_received": "replied",
        "replied": "replied",
        "bounced": "failed",
        "failed": "failed",
        "cancelled": "cancelled",
        "completed": "completed",
    }
    next_status = status_map.get(event_type)
    if not next_status:
        raise HTTPException(status_code=400, detail=f"Unsupported outreach event_type: {payload.event_type}")

    current_status = str(job.get("status") or "queued")
    if current_status in {"blocked", "cancelled", "completed"} and next_status not in {current_status, "cancelled", "completed"}:
        raise HTTPException(status_code=409, detail=f"Cannot apply {event_type} to terminal/blocked job state {current_status}")

    event_at = str(payload.event_at or "").strip() or _utc_now_iso()
    detail = str(payload.detail or "").strip()
    metadata = payload.metadata if isinstance(payload.metadata, dict) else {}

    delivery = dict(job.get("delivery") or {})
    if event_type in {"sent", "delivered", "reply_received", "replied", "bounced", "failed"}:
        delivery["attempt_count"] = int(delivery.get("attempt_count") or 0) + (1 if event_type == "sent" else 0)
    if payload.provider_message_id:
        delivery["provider_message_id"] = payload.provider_message_id
    delivery["last_event_type"] = event_type
    delivery["last_event_at"] = event_at
    if event_type in {"reply_received", "replied"}:
        delivery["reply_received"] = True

    event_log = list(job.get("event_log") or [])
    event_log.append(
        {
            "event_type": event_type,
            "status": next_status,
            "detail": detail or f"Lifecycle updated via {event_type}.",
            "event_at": event_at,
            "provider_message_id": payload.provider_message_id,
            "metadata": metadata,
        }
    )

    updated = dict(job)
    updated["status"] = next_status
    updated["updated_at"] = event_at
    updated["delivery"] = delivery
    updated["event_log"] = event_log
    return updated


def _build_calling_session_record(
    *,
    site_id: str,
    playbook: Dict[str, Any],
    call_direction: str,
) -> Dict[str, Any]:
    playbook_steps = list((playbook.get("playbook") or {}).get("steps") or [])
    opener = None
    if len(playbook_steps) > 1:
        opener = playbook_steps[1].get("instruction")
    if not opener and playbook_steps:
        opener = playbook_steps[0].get("instruction")

    objection_map = list((playbook.get("playbook") or {}).get("objection_map") or [])
    created_at = _utc_now_iso()
    session_id = f"call_session_{_slug_token(site_id)}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    direction = _slug_token(call_direction).replace("-", "_") or "outbound"
    if direction not in {"outbound", "inbound", "callback"}:
        direction = "outbound"

    return {
        "framework": CALLING_AGENT_FRAMEWORK,
        "session_id": session_id,
        "site_id": site_id,
        "playbook_id": playbook.get("playbook_id"),
        "status": "ready",
        "call_direction": direction,
        "created_at": created_at,
        "updated_at": created_at,
        "site": dict(playbook.get("opportunity") or {}),
        "pre_call_brief": {
            "objective": playbook.get("objective"),
            "recommended_channel": (playbook.get("playbook") or {}).get("recommended_channel"),
            "opener": opener,
            "next_best_action": (playbook.get("playbook") or {}).get("next_best_action"),
            "proof_points": [
                item.get("instruction")
                for item in playbook_steps[:2]
                if isinstance(item, dict) and str(item.get("instruction") or "").strip()
            ][:2],
            "objection_map": objection_map[:4],
        },
        "live_assist": {
            "recommended_talk_track": opener,
            "guardrail_flags": list(playbook.get("guardrail_flags") or []),
            "stop_conditions": list(playbook.get("stop_conditions") or []),
        },
        "outcome_sync": {
            "lead_outcome_ref": f"/api/v1/operator/outcome/{site_id}",
            "status": "pending",
            "last_synced_at": None,
        },
        "event_log": [
            {
                "event_type": "session_created",
                "status": "ready",
                "detail": "Calling session created from compiled playbook.",
                "event_at": created_at,
            }
        ],
    }


def _apply_calling_session_event(session: Dict[str, Any], payload: CallingSessionEventPayload) -> Dict[str, Any]:
    event_type = _slug_token(payload.event_type).replace("-", "_")
    if not event_type:
        raise HTTPException(status_code=400, detail="event_type is required")

    status_map = {
        "session_created": "ready",
        "dispatch_requested": "ready",
        "provider_queued": "ready",
        "session_started": "live",
        "live_assist_requested": "live",
        "transcript_note": "live",
        "objection_logged": "live",
        "no_answer": "completed",
        "follow_up_needed": "completed",
        "qualified": "completed",
        "won": "completed",
        "lost": "completed",
        "completed": "completed",
        "cancelled": "cancelled",
        "failed": "failed",
    }
    next_status = status_map.get(event_type)
    if not next_status:
        raise HTTPException(status_code=400, detail=f"Unsupported calling event_type: {payload.event_type}")

    current_status = str(session.get("status") or "ready")
    if current_status in {"cancelled", "completed", "failed"} and next_status not in {current_status}:
        raise HTTPException(status_code=409, detail=f"Cannot apply {event_type} to terminal session state {current_status}")

    event_at = str(payload.event_at or "").strip() or _utc_now_iso()
    detail = str(payload.detail or "").strip()
    transcript_excerpt = str(payload.transcript_excerpt or "").strip()
    objection = str(payload.objection or "").strip()
    reason = str(payload.reason or "").strip()
    metadata = payload.metadata if isinstance(payload.metadata, dict) else {}

    lead_outcome_status = str(payload.outcome_status or "").strip().lower()
    if not lead_outcome_status and event_type in {"qualified", "won", "lost"}:
        lead_outcome_status = event_type
    elif not lead_outcome_status and event_type == "follow_up_needed":
        lead_outcome_status = "responded"
    elif not lead_outcome_status and event_type == "no_answer":
        lead_outcome_status = "contacted"

    outcome_sync = dict(session.get("outcome_sync") or {})
    synced_outcome = None
    if lead_outcome_status:
        signal_keys = []
        row = _data_cache().get("by_site", {}).get(str(session.get("site_id") or ""))
        if row:
            signal_keys = _signal_keys_for_row(row)
        synced_outcome = _upsert_lead_outcome_record(
            site_id=str(session.get("site_id") or ""),
            status_value=lead_outcome_status,
            note=detail or transcript_excerpt,
            objection=objection,
            reason=reason,
            product=str(((session.get("site") or {}).get("primary_product") or "")),
            realized_revenue_usd=payload.realized_revenue_usd,
            realized_profit_usd=payload.realized_profit_usd,
            attribution_channel="phone",
            attribution_playbook_id=str(session.get("playbook_id") or ""),
            attribution_orchestrator_run_id=str(session.get("orchestrator_run_id") or ""),
            attribution_signal_keys=signal_keys,
            attribution_source_session_id=str(session.get("session_id") or ""),
        )
        outcome_sync["status"] = "synced"
        outcome_sync["last_synced_at"] = event_at
        outcome_sync["lead_outcome"] = synced_outcome

    event_log = list(session.get("event_log") or [])
    event_log.append(
        {
            "event_type": event_type,
            "status": next_status,
            "detail": detail or f"Calling session updated via {event_type}.",
            "event_at": event_at,
            "transcript_excerpt": transcript_excerpt or None,
            "objection": objection or None,
            "reason": reason or None,
            "outcome_status": lead_outcome_status or None,
            "metadata": metadata,
        }
    )

    live_assist = dict(session.get("live_assist") or {})
    if transcript_excerpt:
        live_assist["latest_transcript_excerpt"] = transcript_excerpt
    if objection:
        live_assist["latest_objection"] = objection

    updated = dict(session)
    updated["status"] = next_status
    updated["updated_at"] = event_at
    updated["live_assist"] = live_assist
    updated["outcome_sync"] = outcome_sync
    updated["event_log"] = event_log
    return updated


def _dispatch_outreach_job(job: Dict[str, Any], payload: DispatchRequestPayload) -> Dict[str, Any]:
    validation = _dispatch_actor_validation(payload, "email")
    if not bool(validation.get("allowed")):
        raise HTTPException(status_code=403, detail={"message": "Dispatch actor not allowed", **validation})

    current_status = str(job.get("status") or "queued")
    if current_status in {"blocked", "cancelled", "completed", "failed"}:
        raise HTTPException(status_code=409, detail=f"Cannot dispatch outreach job in state {current_status}")

    adapter = _dispatch_adapter_descriptor("email", payload.provider)
    event_at = _utc_now_iso()
    updated = dict(job)
    event_log = list(updated.get("event_log") or [])
    dispatch_state = dict(updated.get("dispatch") or {})
    live_requested = bool(payload.promote_to_live) or str(updated.get("dispatch_mode") or "") not in {"", "dry_run"}

    event_log.append(
        {
            "event_type": "dispatch_requested",
            "status": current_status,
            "detail": str(payload.note or "").strip() or "Supervisor requested outreach dispatch.",
            "event_at": event_at,
            "metadata": {
                "actor_id": validation.get("actor_id"),
                "actor_role": validation.get("actor_role"),
                "provider": adapter.get("provider"),
                "provider_mode": adapter.get("mode"),
                "promote_to_live": bool(payload.promote_to_live),
            },
        }
    )

    dispatch_state.update(
        {
            "channel": "email",
            "status": "requested",
            "requested_at": event_at,
            "requested_by": validation.get("actor_id"),
            "requested_role": validation.get("actor_role"),
            "provider": adapter.get("provider"),
            "provider_mode": adapter.get("mode"),
            "live_requested": live_requested,
            "live_allowed": bool(adapter.get("allow_live_dispatch")),
            "note": str(payload.note or "").strip(),
        }
    )

    if not bool(adapter.get("enabled")) or str(adapter.get("mode") or "") == "disabled":
        dispatch_state["status"] = "blocked"
        dispatch_state["error"] = "email_adapter_disabled"
        updated["dispatch"] = dispatch_state
        updated["event_log"] = event_log
        updated["updated_at"] = event_at
        return updated

    if live_requested and not bool(adapter.get("allow_live_dispatch")):
        dispatch_state["status"] = "blocked"
        dispatch_state["error"] = "live_email_dispatch_disabled"
        updated["dispatch"] = dispatch_state
        updated["event_log"] = event_log
        updated["updated_at"] = event_at
        return updated

    if str(updated.get("dispatch_mode") or "") == "dry_run" and not bool(payload.promote_to_live):
        dispatch_state["status"] = "dry_run_preview_ready"
        dispatch_state["preview"] = {
            "channel": str(updated.get("resolved_channel") or "email"),
            "message_hint": str(((updated.get("send_context") or {}).get("message_hint") or "")).strip() or None,
            "next_best_action": str(((updated.get("send_context") or {}).get("next_best_action") or "")).strip() or None,
        }
        updated["dispatch"] = dispatch_state
        updated["event_log"] = event_log
        updated["updated_at"] = event_at
        return updated

    updated["dispatch"] = dispatch_state
    updated["event_log"] = event_log

    if str(adapter.get("provider") or "") == "resend":
        return _dispatch_resend_email(
            updated,
            adapter=adapter,
            validation=validation,
            note=str(payload.note or "").strip(),
            live_requested=live_requested,
        )

    contact = _contact_record_for_site(str(updated.get("site_id") or "")) or {}
    to_email = str(contact.get("primary_email") or "").strip()
    subject = _resend_email_subject(updated, contact)
    body_text = _resend_email_text(updated, contact)
    provider_message_id = f"mock_email_{_slug_token(str(updated.get('site_id') or 'lead'))}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    dispatch_state["status"] = "provider_accepted"
    dispatch_state["provider_message_id"] = provider_message_id
    dispatch_state["dispatched_at"] = event_at
    updated["dispatch_mode"] = "supervised_live" if live_requested else str(updated.get("dispatch_mode") or "queued")
    updated["dispatch"] = dispatch_state
    updated["event_log"] = event_log
    updated = _apply_outreach_job_event(
        updated,
        OutreachJobEventPayload(
            job_id=str(updated.get("job_id") or ""),
            event_type="sent",
            detail="Mock email adapter accepted the supervised dispatch request.",
            provider_message_id=provider_message_id,
            metadata={
                "provider": adapter.get("provider"),
                "provider_mode": adapter.get("mode"),
                "actor_id": validation.get("actor_id"),
                "actor_role": validation.get("actor_role"),
                "live_requested": live_requested,
            },
        ),
    )
    thread = _record_outbound_email_thread(
        source="outreach_dispatch_mock",
        links=_outreach_job_email_links(updated),
        from_email=_normalize_email_address(EMAIL_REPLY_TO) or _normalize_email_address(EMAIL_FROM),
        to_emails=[to_email] if to_email else [],
        subject=subject,
        body_text=body_text,
        provider_message_id=provider_message_id,
        event_at=event_at,
    )
    return _apply_inbox_summary(updated, thread)


def _dispatch_calling_session(session: Dict[str, Any], payload: DispatchRequestPayload) -> Dict[str, Any]:
    validation = _dispatch_actor_validation(payload, "calling")
    if not bool(validation.get("allowed")):
        raise HTTPException(status_code=403, detail={"message": "Dispatch actor not allowed", **validation})

    current_status = str(session.get("status") or "ready")
    if current_status in {"cancelled", "completed", "failed"}:
        raise HTTPException(status_code=409, detail=f"Cannot dispatch calling session in state {current_status}")

    site_id = str(session.get("site_id") or "")
    voice = _voice_ready_summary(site_id)
    if not bool(voice.get("voice_ready")):
        raise HTTPException(status_code=409, detail={"message": "Voice path not ready", "missing_requirements": voice.get("missing_requirements") or []})

    adapter = _dispatch_adapter_descriptor("calling", payload.provider)
    event_at = _utc_now_iso()
    updated = dict(session)
    event_log = list(updated.get("event_log") or [])
    dispatch_state = dict(updated.get("dispatch") or {})

    event_log.append(
        {
            "event_type": "dispatch_requested",
            "status": current_status,
            "detail": str(payload.note or "").strip() or "Supervisor requested call dispatch.",
            "event_at": event_at,
            "metadata": {
                "actor_id": validation.get("actor_id"),
                "actor_role": validation.get("actor_role"),
                "provider": adapter.get("provider"),
                "provider_mode": adapter.get("mode"),
            },
        }
    )

    dispatch_state.update(
        {
            "channel": "calling",
            "status": "requested",
            "requested_at": event_at,
            "requested_by": validation.get("actor_id"),
            "requested_role": validation.get("actor_role"),
            "provider": adapter.get("provider"),
            "provider_mode": adapter.get("mode"),
            "live_allowed": bool(adapter.get("allow_live_dispatch")),
            "phone_number": voice.get("phone_number"),
            "note": str(payload.note or "").strip(),
        }
    )

    if not bool(adapter.get("enabled")) or str(adapter.get("mode") or "") == "disabled":
        dispatch_state["status"] = "blocked"
        dispatch_state["error"] = "calling_adapter_disabled"
        updated["dispatch"] = dispatch_state
        updated["event_log"] = event_log
        updated["updated_at"] = event_at
        return updated

    provider_call_id = f"mock_call_{_slug_token(site_id or 'lead')}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    dispatch_state["status"] = "provider_queued"
    dispatch_state["provider_call_id"] = provider_call_id
    dispatch_state["dispatched_at"] = event_at
    updated["dispatch"] = dispatch_state
    updated["provider_call_id"] = provider_call_id
    updated["event_log"] = event_log
    updated = _apply_calling_session_event(
        updated,
        CallingSessionEventPayload(
            session_id=str(updated.get("session_id") or ""),
            event_type="provider_queued",
            detail="Mock calling adapter queued the supervised outbound call.",
            metadata={
                "provider": adapter.get("provider"),
                "provider_mode": adapter.get("mode"),
                "actor_id": validation.get("actor_id"),
                "actor_role": validation.get("actor_role"),
                "phone_number": voice.get("phone_number"),
            },
        ),
    )
    return updated


def _persist_orchestrator_run(run: Dict[str, Any]) -> Dict[str, Any]:
    store = _read_orchestrator_run_store()
    store[str(run.get("run_id") or "")] = run
    _write_orchestrator_run_store(store)
    _orchestrator_run_cache.cache_clear()
    return run


def _append_governance_audit(run: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
    audit = list(run.get("governance_audit") or [])
    audit.append(record)
    run["governance_audit"] = audit
    return run


def _governance_validation_result(
    *,
    run: Dict[str, Any],
    action: Dict[str, Any],
    actor_id: str,
    actor_role: str,
) -> Dict[str, Any]:
    policy = _governance_policy_config()
    approvals = dict(policy.get("approvals") or {})
    role_map = dict(approvals.get("roles_allowed") or {})
    action_type = str(action.get("action_type") or "")
    allowed_roles = [str(v).strip().lower() for v in (role_map.get(action_type) or role_map.get("default") or []) if str(v).strip()]
    normalized_role = _slug_token(actor_role).replace("-", "_") or "unknown"
    normalized_actor_id = str(actor_id or "").strip()

    reasons: List[str] = []
    allowed = True
    if bool(action.get("requires_approval")) and normalized_role not in set(allowed_roles):
        allowed = False
        reasons.append(f"role_not_allowed:{normalized_role}")
    if bool(approvals.get("require_actor_id")) and not normalized_actor_id:
        allowed = False
        reasons.append("missing_actor_id")
    if str(action.get("status") or "") != "awaiting_approval":
        allowed = False
        reasons.append(f"action_not_awaiting_approval:{str(action.get('status') or '')}")

    return {
        "framework": ORCHESTRATOR_FRAMEWORK,
        "run_id": run.get("run_id"),
        "action_id": action.get("action_id"),
        "action_type": action_type,
        "actor_id": normalized_actor_id,
        "actor_role": normalized_role,
        "allowed": allowed,
        "reasons": reasons,
        "policy_source": str(policy.get("_source") or "default"),
        "policy_version": str(policy.get("version") or "v1"),
        "allowed_roles": allowed_roles,
        "evaluated_at": _utc_now_iso(),
    }


def _orchestrator_action_status(action_type: str, *, approval_required: bool) -> str:
    if action_type == "compile_playbook":
        return "completed"
    if action_type in {"create_outreach_job", "create_calling_session"}:
        return "awaiting_approval" if approval_required else "ready"
    return "pending"


def _orchestrator_status_from_actions(actions: List[Dict[str, Any]]) -> str:
    statuses = {str(action.get("status") or "pending") for action in actions}
    if "awaiting_approval" in statuses:
        return "awaiting_approval"
    if statuses and statuses.issubset({"completed", "blocked", "skipped"}):
        return "completed"
    if "failed" in statuses:
        return "attention_required"
    if "ready" in statuses or "pending" in statuses:
        return "in_progress"
    return "planned"


def _refresh_orchestrator_run(run: Dict[str, Any]) -> Dict[str, Any]:
    actions = [dict(action) for action in (run.get("actions") or [])]
    by_type = {str(action.get("action_type") or ""): action for action in actions}
    follow_up = by_type.get("schedule_follow_up_review")
    outreach_action = by_type.get("create_outreach_job")
    calling_action = by_type.get("create_calling_session")
    if follow_up and outreach_action and calling_action:
        ready_inputs = {
            str(outreach_action.get("status") or ""),
            str(calling_action.get("status") or ""),
        }
        if ready_inputs.issubset({"completed", "blocked", "skipped"}) and str(follow_up.get("status") or "") == "pending":
            follow_up["status"] = "ready"
            follow_up["note"] = "Review outreach/calling outcomes and decide follow-up." 
    run["actions"] = actions
    run["status"] = _orchestrator_status_from_actions(actions)
    run["updated_at"] = _utc_now_iso()
    return run


def _build_orchestrator_run(
    *,
    row: Dict[str, Any],
    playbook: Dict[str, Any],
    payload: OrchestratorRunCreatePayload,
) -> Dict[str, Any]:
    created_at = _utc_now_iso()
    run_id = f"orchestrator_run_{_slug_token(str(row.get('site_id') or ''))}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    action_specs = [
        ("compile_playbook", "Compile playbook", False, []),
        ("create_outreach_job", "Create outreach job", bool(payload.approval_required), ["compile_playbook"]),
        ("create_calling_session", "Create calling session", bool(payload.approval_required), ["compile_playbook"]),
        ("schedule_follow_up_review", "Schedule follow-up review", False, ["create_outreach_job", "create_calling_session"]),
    ]
    actions: List[Dict[str, Any]] = []
    for index, (action_type, title, requires_approval, depends_on_types) in enumerate(action_specs, start=1):
        action_id = f"action_{_slug_token(run_id)}_{index:02d}_{action_type}"
        status = _orchestrator_action_status(action_type, approval_required=requires_approval)
        action: Dict[str, Any] = {
            "action_id": action_id,
            "action_type": action_type,
            "title": title,
            "status": status,
            "requires_approval": requires_approval,
            "depends_on": [
                f"action_{_slug_token(run_id)}_{i:02d}_{dep}"
                for i, (dep, _, _, _) in enumerate(action_specs, start=1)
                if dep in set(depends_on_types)
            ],
        }
        if action_type == "compile_playbook":
            action["playbook_id"] = playbook.get("playbook_id")
            action["resource_ref"] = f"/api/v1/playbooks/{playbook.get('playbook_id')}"
        if requires_approval:
            action["blocked_reason"] = "approval_required"
        actions.append(action)

    governance_policy = _governance_policy_config()
    run = {
        "framework": ORCHESTRATOR_FRAMEWORK,
        "run_id": run_id,
        "site_id": row.get("site_id"),
        "idempotency_key": str(payload.idempotency_key or "").strip() or None,
        "created_at": created_at,
        "updated_at": created_at,
        "approval_required": bool(payload.approval_required),
        "auto_execute": bool(payload.auto_execute),
        "execution_mode": str(payload.execution_mode or "agent_assist"),
        "strict_guardrails": bool(payload.strict_guardrails),
        "status": _orchestrator_status_from_actions(actions),
        "site": {
            "address": row.get("address"),
            "zip": row.get("zip"),
            "primary_product": row.get("primary_product"),
            "secondary_product": row.get("secondary_product"),
            "lead_temperature": row.get("lead_temperature"),
            "opportunity_score": round(float(row.get("priority_score") or 0.0), 1),
            "confidence": round(float(row.get("confidence") or 0.0), 3),
        },
        "playbook_id": playbook.get("playbook_id"),
        "actions": actions,
        "refs": {
            "playbook_ref": f"/api/v1/playbooks/{playbook.get('playbook_id')}",
            "decision_ref": f"/api/v1/decision/site/{row.get('site_id')}",
            "signals_ref": f"/api/v1/signals/site/{row.get('site_id')}",
        },
        "policy": {
            "approval_required": bool(payload.approval_required),
            "auto_execute": bool(payload.auto_execute),
            "call_direction": str(payload.call_direction or "outbound"),
            "governance_policy_version": str(governance_policy.get("version") or "v1"),
            "governance_policy_source": str(governance_policy.get("_source") or "default"),
        },
        "governance_audit": [
            {
                "event": "run_created",
                "run_id": run_id,
                "allowed": True,
                "policy_version": str(governance_policy.get("version") or "v1"),
                "policy_source": str(governance_policy.get("_source") or "default"),
                "evaluated_at": created_at,
            }
        ],
    }
    return _refresh_orchestrator_run(run)


def _execute_orchestrator_action(run: Dict[str, Any], action_id: str) -> Dict[str, Any]:
    site_id = str(run.get("site_id") or "")
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    playbook = _compiled_playbook_for(str(run.get("playbook_id") or ""))
    if not playbook:
        raise HTTPException(status_code=404, detail=f"Unknown playbook_id {run.get('playbook_id')}")

    actions = [dict(action) for action in (run.get("actions") or [])]
    action = next((item for item in actions if str(item.get("action_id") or "") == action_id), None)
    if not action:
        raise HTTPException(status_code=404, detail=f"Unknown action_id {action_id}")

    action_type = str(action.get("action_type") or "")
    if action_type == "compile_playbook":
        action["status"] = "completed"
        action["resource_ref"] = f"/api/v1/playbooks/{playbook.get('playbook_id')}"
    elif action_type == "create_outreach_job":
        job = _build_outreach_job_record(
            site_id=site_id,
            playbook=playbook,
            requested_channel=None,
            idempotency_key=f"{run.get('run_id')}:{action_id}",
            dry_run=True,
        )
        job["orchestrator_run_id"] = str(run.get("run_id") or "")
        _persist_outreach_job(job)
        action["status"] = "blocked" if str(job.get("status") or "") == "blocked" else "completed"
        action["resource_ref"] = f"/api/v1/agents/outreach/jobs/{job.get('job_id')}"
        action["result"] = {"job_id": job.get("job_id"), "job_status": job.get("status")}
        run.setdefault("refs", {})["outreach_job_ref"] = action["resource_ref"]
    elif action_type == "create_calling_session":
        session = _build_calling_session_record(
            site_id=site_id,
            playbook=playbook,
            call_direction=str((run.get("policy") or {}).get("call_direction") or "outbound"),
        )
        session["orchestrator_run_id"] = str(run.get("run_id") or "")
        _persist_calling_session(session)
        action["status"] = "completed"
        action["resource_ref"] = f"/api/v1/agents/calling/sessions/{session.get('session_id')}"
        action["result"] = {"session_id": session.get("session_id"), "session_status": session.get("status")}
        run.setdefault("refs", {})["calling_session_ref"] = action["resource_ref"]
    elif action_type == "schedule_follow_up_review":
        action["status"] = "completed"
        action["note"] = "Follow-up review action acknowledged."
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported orchestrator action_type {action_type}")

    action["updated_at"] = _utc_now_iso()
    run["actions"] = actions
    run = _append_governance_audit(
        run,
        {
            "event": "action_executed",
            "run_id": run.get("run_id"),
            "action_id": action_id,
            "action_type": action_type,
            "allowed": True,
            "mode": "auto" if not bool(action.get("requires_approval")) else "approved",
            "evaluated_at": action["updated_at"],
        },
    )
    return _refresh_orchestrator_run(run)


def _apply_orchestrator_approval(run: Dict[str, Any], action_id: str, payload: OrchestratorActionApprovalPayload) -> Dict[str, Any]:
    actions = [dict(action) for action in (run.get("actions") or [])]
    action = next((item for item in actions if str(item.get("action_id") or "") == action_id), None)
    if not action:
        raise HTTPException(status_code=404, detail=f"Unknown action_id {action_id}")
    if not bool(action.get("requires_approval")):
        raise HTTPException(status_code=400, detail=f"Action {action_id} does not require approval")
    if str(action.get("status") or "") != "awaiting_approval":
        raise HTTPException(status_code=409, detail=f"Action {action_id} is not awaiting approval")

    action["approved_by"] = str(payload.approver or "").strip()
    action["approved_at"] = _utc_now_iso()
    action["approved_role"] = str(payload.actor_role or "manager").strip()
    action["approval_note"] = str(payload.note or "").strip()
    action["status"] = "ready"
    action.pop("blocked_reason", None)
    run["actions"] = actions
    run = _refresh_orchestrator_run(run)
    return _execute_orchestrator_action(run, action_id)


def _auto_execute_orchestrator_run(run: Dict[str, Any]) -> Dict[str, Any]:
    for action in list(run.get("actions") or []):
        if str(action.get("status") or "") == "ready":
            run = _execute_orchestrator_action(run, str(action.get("action_id") or ""))
    return _refresh_orchestrator_run(run)


def _find_orchestrator_run_by_action(action_id: str) -> Dict[str, Any] | None:
    for run in _orchestrator_run_cache().values():
        for action in (run.get("actions") or []):
            if str(action.get("action_id") or "") == str(action_id or ""):
                return dict(run)
    return None


def _known_outcome_rows(zip: str | None = None, h3_cell: str | None = None) -> List[Dict[str, Any]]:
    rows = [_attach_operator_status(row) for row in _scoped_rows(zip, h3_cell)]
    return [row for row in rows if str(((row.get("lead_outcome") or {}).get("status") or "unknown")).strip().lower() != "unknown"]


def _build_learning_summary(zip: str | None = None, h3_cell: str | None = None) -> Dict[str, Any]:
    rows = _known_outcome_rows(zip, h3_cell)
    summary = _build_outcome_scope_summary(rows, label="learning_scope")
    threshold = 75.0
    return {
        "framework": LEARNING_FRAMEWORK,
        "scope": {"zip": zip, "h3_cell": h3_cell},
        "summary": summary,
        "promotion_readiness": {
            "minimum_recommended_attribution_pct": threshold,
            "current_avg_attribution_field_completeness_pct": summary.get("avg_attribution_field_completeness_pct"),
            "passes_recommended_threshold": float(summary.get("avg_attribution_field_completeness_pct") or 0.0) >= threshold,
        },
    }


def _build_learning_job_result(payload: LearningRetrainJobPayload) -> Dict[str, Any]:
    rows = _known_outcome_rows()
    summary = _build_outcome_scope_summary(rows, label="global_learning_scope")
    total = int(summary.get("outcome_count") or 0)
    completeness = float(summary.get("avg_attribution_field_completeness_pct") or 0.0)
    min_outcomes_ok = total >= max(1, int(payload.minimum_outcomes))
    attribution_ok = completeness >= float(payload.minimum_attribution_completeness_pct)
    promotion_safe = bool(payload.dry_run) or (min_outcomes_ok and attribution_ok and bool(str(payload.approver or "").strip()))
    status = "dry_run_complete" if bool(payload.dry_run) else ("ready_for_review" if promotion_safe else "blocked")
    checks = [
        {
            "check": "minimum_outcomes",
            "required": int(payload.minimum_outcomes),
            "actual": total,
            "pass": min_outcomes_ok,
        },
        {
            "check": "attribution_completeness",
            "required_pct": float(payload.minimum_attribution_completeness_pct),
            "actual_pct": completeness,
            "pass": attribution_ok,
        },
        {
            "check": "approver_present_for_live_promotion",
            "required": not bool(payload.dry_run),
            "actual": bool(str(payload.approver or "").strip()),
            "pass": bool(payload.dry_run) or bool(str(payload.approver or "").strip()),
        },
    ]
    job = {
        "framework": LEARNING_FRAMEWORK,
        "job_id": f"learning_job_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}",
        "created_at": _utc_now_iso(),
        "status": status,
        "dry_run": bool(payload.dry_run),
        "note": str(payload.note or "").strip(),
        "approver": str(payload.approver or "").strip() or None,
        "checks": checks,
        "summary": summary,
        "promotion_safe": promotion_safe,
    }
    return job


def _manager_command_payload(site_id: str | None = None, run_id: str | None = None) -> Dict[str, Any]:
    policy = _governance_policy_config()
    thresholds = ((policy.get("manager_command") or {}).get("risk_alert_thresholds") or {})
    low_attr_threshold = float(thresholds.get("low_attribution_pct") or 60.0)
    low_conf_threshold = float(thresholds.get("low_confidence") or 0.65)

    run = _orchestrator_run_for(str(run_id or "")) if run_id else None
    site_row = None
    resolved_site_id = str(site_id or "").strip()
    if run and not resolved_site_id:
        resolved_site_id = str(run.get("site_id") or "")
    if resolved_site_id:
        site_row = _data_cache().get("by_site", {}).get(resolved_site_id)

    learning = _build_learning_summary()
    learning_summary = learning.get("summary") or {}
    risk_alerts: List[Dict[str, Any]] = []
    coaching_actions: List[str] = []

    if run:
        if str(run.get("status") or "") == "awaiting_approval":
            risk_alerts.append({"level": "high", "code": "approval_queue", "message": "Run is waiting on approval for downstream autonomous actions."})
            coaching_actions.append("Review queued outreach/calling actions and approve only the ones that match policy and field reality.")
        blocked = [a for a in (run.get("actions") or []) if str(a.get("status") or "") == "blocked"]
        if blocked:
            risk_alerts.append({"level": "medium", "code": "blocked_actions", "message": f"{len(blocked)} orchestrator actions are blocked and need review."})
            coaching_actions.append("Check blocked actions for suppression/compliance reasons before trying to force execution.")

    if site_row:
        confidence = float(site_row.get("confidence") or 0.0)
        if confidence < low_conf_threshold:
            risk_alerts.append({"level": "medium", "code": "low_confidence", "message": f"Site confidence {confidence:.2f} is below the manager threshold."})
            coaching_actions.append("Use manual review or extra investigation before widening autonomous execution on this lead.")
        outcome = _lead_outcome_for(str(site_row.get("site_id") or ""))
        if str(outcome.get("status") or "unknown") == "unknown":
            coaching_actions.append("Make sure outreach/calling touches log a structured outcome so the learning loop can trust this lane.")

    avg_attr = float(learning_summary.get("avg_attribution_field_completeness_pct") or 0.0)
    if avg_attr < low_attr_threshold:
        risk_alerts.append({"level": "medium", "code": "low_attribution", "message": f"Average attribution completeness {avg_attr:.1f}% is below target {low_attr_threshold:.1f}%."})
        coaching_actions.append("Push reps/agents to log channel, playbook, orchestrator run, and signal attribution on every meaningful outcome.")

    if not coaching_actions:
        coaching_actions.append("System is within current guardrails. Keep logging honest outcomes and review promotion gates before widening autonomy.")

    return {
        "framework": ORCHESTRATOR_FRAMEWORK,
        "site_id": resolved_site_id or None,
        "run_id": str(run.get("run_id") or "") if run else None,
        "risk_alerts": risk_alerts,
        "coaching_actions": coaching_actions,
        "pipeline_truth": {
            "run_status": str(run.get("status") or "") if run else None,
            "site_confidence": round(float(site_row.get("confidence") or 0.0), 3) if site_row else None,
            "lead_outcome_status": _lead_outcome_for(resolved_site_id).get("status") if resolved_site_id else None,
            "learning_avg_attribution_field_completeness_pct": avg_attr,
        },
        "policy_source": str(policy.get("_source") or "default"),
        "policy_version": str(policy.get("version") or "v1"),
    }


def _signal_snapshot_for_row(row: Dict[str, Any]) -> Dict[str, Any]:
    trigger_asof = _extract_asof_from_notes(str(row.get("trigger_notes") or ""))
    signals = []
    for key, source in [
        ("storm", "nws"),
        ("outage", "utility_state"),
        ("equipment_age", "census_proxy"),
        ("flood_risk", "fema_or_nws"),
        ("permit", "municipal_permit"),
    ]:
        status_key = f"{key}_trigger_status"
        score_key = f"{key}_trigger_score"
        status = str(row.get(status_key) or "missing")
        score_raw = row.get(score_key)
        score = None
        try:
            if score_raw is not None and str(score_raw).strip() != "":
                score = round(float(score_raw), 3)
        except Exception:
            score = None
        signals.append(
            {
                "signal_key": key,
                "status": status,
                "quality": _status_quality(status),
                "score": score,
                "source": source,
                "as_of": trigger_asof or None,
            }
        )

    quality_counts: Dict[str, int] = {"verified": 0, "proxy": 0, "missing": 0}
    for item in signals:
        quality_counts[item["quality"]] = quality_counts.get(item["quality"], 0) + 1

    return {
        "site_id": row.get("site_id"),
        "zip": row.get("zip"),
        "signals": signals,
        "summary": {
            "quality_counts": quality_counts,
            "trigger_data_gaps": row.get("trigger_data_gaps"),
            "has_actionable_outage_data": bool(row.get("has_actionable_outage_data")),
            "utility_name": row.get("utility_name"),
            "utility_rate_method": row.get("utility_rate_method"),
            "utility_rate_as_of": row.get("utility_rate_as_of") or None,
        },
    }


@app.get("/api/v1/revenue-graph/site/{site_id}")
def revenue_graph_site(site_id: str) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    site_scope = _attach_operator_status(row)
    investigation = _build_investigation_payload(site_scope)
    outreach = _build_outreach_payload(investigation)

    account_id = _account_id_for_row(site_scope)
    contact = _contact_record_for_site(site_id)

    return {
        "framework": "dg-revenue-graph-v1",
        "site": {
            "site_id": site_scope.get("site_id"),
            "address": site_scope.get("address"),
            "zip": site_scope.get("zip"),
            "h3_cell": site_scope.get("h3_cell"),
            "primary_product": site_scope.get("primary_product"),
            "secondary_product": site_scope.get("secondary_product"),
            "opportunity_score": round(float(site_scope.get("priority_score") or 0.0), 1),
            "confidence": round(float(site_scope.get("confidence") or 0.0), 3),
        },
        "account": {
            "account_id": account_id,
            "name": f"Account {str(site_scope.get('zip') or 'unknown')} {str(site_scope.get('site_id') or '')[-6:]}",
            "segment": site_scope.get("primary_product"),
            "tier": site_scope.get("lead_temperature"),
            "owner_mode": "unassigned",
        },
        "primary_contact": {
            "contact_id": (contact or {}).get("contact_id"),
            "role": (contact or {}).get("role", "owner_operator_proxy"),
            "preferred_channel": (contact or {}).get("preferred_channel") or outreach.get("recommended_channel"),
            "contactability_confidence": (contact or {}).get("contactability_label") or outreach.get("confidence_band"),
            "display_name": (contact or {}).get("display_name"),
            "mailing_address": (contact or {}).get("mailing_address"),
        },
        "workflow": {
            "operator_status": (site_scope.get("operator_status") or {}).get("status"),
            "operator_next_step": site_scope.get("operator_next_step"),
            "lead_outcome": site_scope.get("lead_outcome"),
            "last_interaction_at": ((_interactions_for_site(site_id) or [{}])[0]).get("started_at") if _interactions_for_site(site_id) else None,
        },
        "payload_refs": {
            "investigation_ref": f"/api/v1/investigation/site/{site_id}",
            "outreach_ref": f"/api/v1/outreach/site/{site_id}",
            "signals_ref": f"/api/v1/signals/site/{site_id}",
            "decision_ref": f"/api/v1/decision/site/{site_id}",
        },
        "provenance": {
            "source_mode": data.get("source_mode"),
            "site_score_source": str(SITE_SCORES_CSV),
            "trigger_source": str(PROPERTY_TRIGGERS_CSV),
            "operator_status_source": str(OPERATOR_STATUS_JSON),
            "lead_outcome_source": str(LEAD_OUTCOME_JSON),
            "lead_contact_source": str(LEAD_CONTACTS_JSON),
            "lead_interaction_source": str(LEAD_INTERACTIONS_JSON),
        },
    }


@app.get("/api/v1/revenue-graph/account/{account_id}")
def revenue_graph_account(account_id: str) -> Dict[str, Any]:
    rows = _data_cache()["rows"]
    matched: List[Dict[str, Any]] = []
    for row in rows:
        if _account_id_for_row(row) == account_id:
            matched.append(row)

    if not matched:
        raise HTTPException(status_code=404, detail=f"Unknown account_id {account_id}")

    ranked = sorted(matched, key=lambda r: float(r.get("priority_score") or 0.0), reverse=True)
    top = ranked[0]
    return {
        "framework": "dg-revenue-graph-v1",
        "account": {
            "account_id": account_id,
            "site_count": len(matched),
            "zip": top.get("zip"),
            "segment": top.get("primary_product"),
            "avg_opportunity_score": round(sum(float(r.get("priority_score") or 0.0) for r in matched) / len(matched), 2),
            "avg_confidence": round(sum(float(r.get("confidence") or 0.0) for r in matched) / len(matched), 3),
        },
        "top_sites": [_site_card(_attach_operator_status(r)) for r in ranked[:5]],
    }


@app.get("/api/v1/revenue-graph/contact/{contact_id}")
def revenue_graph_contact(contact_id: str) -> Dict[str, Any]:
    contact = _lead_contact_for(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Unknown contact_id {contact_id}")
    row = _data_cache()["by_site"].get(str(contact.get("site_id") or ""))
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site for contact_id {contact_id}")
    row = _attach_operator_status(row)
    investigation = _build_investigation_payload(row)
    outreach = _build_outreach_payload(investigation)

    return {
        "framework": "dg-revenue-graph-v1",
        "contact": {
            **contact,
            "message_angles": outreach.get("message_angles") or [],
            "cta": outreach.get("cta"),
        },
        "policy": outreach.get("policy"),
    }


@app.get("/api/v1/signals/site/{site_id}")
def signals_site(site_id: str) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    return {
        "framework": "dg-signal-mesh-v1",
        **_signal_snapshot_for_row(row),
    }


@app.get("/api/v1/signals/coverage")
def signals_coverage(zip: str | None = None, h3_cell: str | None = None) -> Dict[str, Any]:
    rows = _scoped_rows(zip, h3_cell)
    if not rows:
        return {
            "framework": "dg-signal-mesh-v1",
            "scope": {"zip": zip, "h3_cell": h3_cell},
            "row_count": 0,
            "signals": {},
        }

    signals: Dict[str, Dict[str, int]] = {}
    signal_keys = ["storm", "outage", "equipment_age", "flood_risk", "permit"]
    for key in signal_keys:
        signals[key] = {"verified": 0, "proxy": 0, "missing": 0}

    for row in rows:
        snapshot = _signal_snapshot_for_row(row)
        for item in snapshot.get("signals") or []:
            key = str(item.get("signal_key") or "")
            quality = str(item.get("quality") or "missing")
            if key not in signals:
                signals[key] = {"verified": 0, "proxy": 0, "missing": 0}
            signals[key][quality] = signals[key].get(quality, 0) + 1

    coverage: Dict[str, Any] = {}
    total = len(rows)
    for key, counts in signals.items():
        verified = int(counts.get("verified", 0))
        proxy = int(counts.get("proxy", 0))
        missing = int(counts.get("missing", 0))
        coverage[key] = {
            "verified": verified,
            "proxy": proxy,
            "missing": missing,
            "verified_pct": round(verified / total, 4),
            "proxy_or_better_pct": round((verified + proxy) / total, 4),
        }

    return {
        "framework": "dg-signal-mesh-v1",
        "scope": {"zip": zip, "h3_cell": h3_cell},
        "row_count": total,
        "signals": coverage,
    }


@app.get("/api/v1/decision/site/{site_id}")
def decision_site(site_id: str) -> Dict[str, Any]:
    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    row = _attach_operator_status(row)
    investigation = _build_investigation_payload(row)
    outreach = _build_outreach_payload(investigation)

    signal_snapshot = _signal_snapshot_for_row(row)
    verified_count = int(signal_snapshot["summary"]["quality_counts"].get("verified", 0))
    proxy_count = int(signal_snapshot["summary"]["quality_counts"].get("proxy", 0))

    opportunity_score = round(float(row.get("priority_score") or 0.0), 1)
    confidence = round(float(row.get("confidence") or 0.0), 3)
    win_proxy = round(
        min(
            0.99,
            max(0.02, 0.25 * confidence + 0.45 * (opportunity_score / 100.0) + 0.06 * verified_count + 0.02 * proxy_count),
        ),
        3,
    )

    return {
        "framework": "dg-decision-engine-v1",
        "site_id": row.get("site_id"),
        "opportunity_score": opportunity_score,
        "confidence": confidence,
        "win_probability_proxy": win_proxy,
        "next_best_action": row.get("operator_next_step"),
        "recommended_offer": {
            "primary_product": row.get("primary_product"),
            "secondary_product": row.get("secondary_product"),
            "recommended_channel": outreach.get("recommended_channel"),
            "confidence_band": outreach.get("confidence_band"),
            "auto_outreach_eligible": outreach.get("auto_outreach_eligible"),
        },
        "decision_factors": {
            "lead_temperature": row.get("lead_temperature"),
            "operator_status": (row.get("operator_status") or {}).get("status"),
            "signal_quality_counts": signal_snapshot["summary"].get("quality_counts"),
            "suppression_reasons": investigation.get("suppression_reasons") or [],
        },
        "refs": {
            "revenue_graph_ref": f"/api/v1/revenue-graph/site/{site_id}",
            "signals_ref": f"/api/v1/signals/site/{site_id}",
            "outreach_ref": f"/api/v1/outreach/site/{site_id}",
            "investigation_ref": f"/api/v1/investigation/site/{site_id}",
        },
    }


@app.post("/api/v1/decision/batch")
def decision_batch(site_ids: List[str]) -> Dict[str, Any]:
    data = _data_cache()
    requested = [str(v).strip() for v in (site_ids or []) if str(v).strip()]
    if not requested:
        raise HTTPException(status_code=400, detail="site_ids body cannot be empty")

    items: List[Dict[str, Any]] = []
    missing: List[str] = []
    for site_id in requested[:250]:
        row = data["by_site"].get(site_id)
        if not row:
            missing.append(site_id)
            continue
        row = _attach_operator_status(row)
        signal_snapshot = _signal_snapshot_for_row(row)
        opportunity_score = round(float(row.get("priority_score") or 0.0), 1)
        confidence = round(float(row.get("confidence") or 0.0), 3)
        verified_count = int(signal_snapshot["summary"]["quality_counts"].get("verified", 0))
        proxy_count = int(signal_snapshot["summary"]["quality_counts"].get("proxy", 0))
        win_proxy = round(
            min(
                0.99,
                max(0.02, 0.25 * confidence + 0.45 * (opportunity_score / 100.0) + 0.06 * verified_count + 0.02 * proxy_count),
            ),
            3,
        )
        items.append(
            {
                "site_id": site_id,
                "opportunity_score": opportunity_score,
                "confidence": confidence,
                "win_probability_proxy": win_proxy,
                "next_best_action": row.get("operator_next_step"),
                "primary_product": row.get("primary_product"),
                "lead_temperature": row.get("lead_temperature"),
            }
        )

    items.sort(key=lambda r: (float(r.get("opportunity_score") or 0.0), float(r.get("confidence") or 0.0)), reverse=True)
    return {
        "framework": "dg-decision-engine-v1",
        "requested": len(requested),
        "returned": len(items),
        "missing": missing,
        "items": items,
    }


@app.get("/api/v1/schema/sales-core")
def schema_sales_core() -> Dict[str, Any]:
    return {
        "schema_id": "dg-sales-core-v1",
        "version": "2026-04-21",
        "entities": {
            "site": [
                "site_id",
                "address",
                "zip",
                "h3_cell",
                "primary_product",
                "secondary_product",
                "priority_score",
                "confidence",
            ],
            "account": ["account_id", "name", "segment", "tier", "owner_mode"],
            "contact": [
                "contact_id",
                "account_id",
                "site_id",
                "entity_type",
                "role",
                "display_name",
                "preferred_channel",
                "contactability_score",
                "contactability_label",
                "mailing_address",
            ],
            "interaction": [
                "interaction_id",
                "site_id",
                "contact_id",
                "account_id",
                "channel",
                "interaction_type",
                "result_status",
                "started_at",
                "next_follow_up_at",
                "next_best_action",
            ],
            "opportunity": [
                "opportunity_score",
                "win_probability_proxy",
                "next_best_action",
                "recommended_channel",
                "auto_outreach_eligible",
            ],
            "outcome": [
                "status",
                "reason",
                "objection",
                "product",
                "realized_revenue_usd",
                "realized_profit_usd",
                "updated_at",
            ],
        },
        "notes": "Universal schema contract for multi-vertical extension (energy + non-energy packs).",
    }


@app.get("/api/v1/contacts/{contact_id}")
def get_contact(contact_id: str) -> Dict[str, Any]:
    contact = _lead_contact_for(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Unknown contact_id {contact_id}")
    return contact


@app.put("/api/v1/contacts/{contact_id}")
def upsert_contact(contact_id: str, payload: LeadContactPayload) -> Dict[str, Any]:
    existing = _lead_contact_for(contact_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Unknown contact_id {contact_id}")
    now = _utc_now_iso()
    updated = dict(existing)
    updated.update(
        {
            "entity_type": str(payload.entity_type or updated.get("entity_type") or "person"),
            "role": str(payload.role or updated.get("role") or "owner_operator_proxy"),
            "display_name": str(payload.display_name or updated.get("display_name") or ""),
            "first_name": payload.first_name if payload.first_name is not None else updated.get("first_name"),
            "last_name": payload.last_name if payload.last_name is not None else updated.get("last_name"),
            "organization_name": payload.organization_name if payload.organization_name is not None else updated.get("organization_name"),
            "owner_occupancy": payload.owner_occupancy if payload.owner_occupancy is not None else updated.get("owner_occupancy"),
            "residency_confidence": payload.residency_confidence if payload.residency_confidence is not None else updated.get("residency_confidence"),
            "preferred_channel": str(payload.preferred_channel or updated.get("preferred_channel") or "mail"),
            "contactability_score": payload.contactability_score if payload.contactability_score is not None else updated.get("contactability_score"),
            "contactability_label": payload.contactability_label if payload.contactability_label is not None else updated.get("contactability_label"),
            "do_not_contact": bool(payload.do_not_contact) if payload.do_not_contact is not None else bool(updated.get("do_not_contact")),
            "primary_phone": payload.primary_phone if payload.primary_phone is not None else updated.get("primary_phone"),
            "phone_numbers": [str(v).strip() for v in (payload.phone_numbers or updated.get("phone_numbers") or []) if str(v).strip()],
            "primary_email": payload.primary_email if payload.primary_email is not None else updated.get("primary_email"),
            "emails": [str(v).strip() for v in (payload.emails or updated.get("emails") or []) if str(v).strip()],
            "website_url": payload.website_url if payload.website_url is not None else updated.get("website_url"),
            "contact_form_url": payload.contact_form_url if payload.contact_form_url is not None else updated.get("contact_form_url"),
            "mailing_address": payload.mailing_address if payload.mailing_address is not None else updated.get("mailing_address"),
            "contact_paths": [
                {
                    "type": str(item.get("type") or "").strip(),
                    "value": str(item.get("value") or "").strip(),
                    "label": str(item.get("label") or "").strip() or None,
                    "priority": int(item.get("priority")) if item.get("priority") not in (None, "", "None") else None,
                }
                for item in (payload.contact_paths or updated.get("contact_paths") or [])
                if isinstance(item, dict) and str(item.get("type") or "").strip() and str(item.get("value") or "").strip()
            ],
            "best_contact_window": payload.best_contact_window if payload.best_contact_window is not None else updated.get("best_contact_window"),
            "dedupe_key": payload.dedupe_key if payload.dedupe_key is not None else updated.get("dedupe_key"),
            "identity_sources": [str(v).strip() for v in (payload.identity_sources or updated.get("identity_sources") or []) if str(v).strip()],
            "source_record_ids": [str(v).strip() for v in (payload.source_record_ids or updated.get("source_record_ids") or []) if str(v).strip()],
            "verified_at": payload.verified_at if payload.verified_at is not None else updated.get("verified_at"),
            "freshness_days": payload.freshness_days if payload.freshness_days is not None else updated.get("freshness_days"),
            "notes": payload.notes if payload.notes is not None else updated.get("notes"),
            "updated_at": now,
        }
    )
    return _persist_lead_contact(updated)


@app.get("/api/v1/contacts/{contact_id}/timeline")
def contact_timeline(contact_id: str, limit: int = 50) -> Dict[str, Any]:
    contact = _lead_contact_for(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Unknown contact_id {contact_id}")
    items = [
        dict(item)
        for item in _lead_interaction_cache().values()
        if str(item.get("contact_id") or "") == str(contact_id)
    ]
    items.sort(key=lambda item: str(item.get("started_at") or ""), reverse=True)
    return {
        "contact": contact,
        "count": len(items),
        "items": items[: max(1, min(limit, 200))],
    }


@app.post("/api/v1/interactions")
def create_interaction(payload: LeadInteractionCreatePayload) -> Dict[str, Any]:
    return _upsert_interaction_record(payload)


@app.get("/api/v1/interactions")
def list_interactions(site_id: str | None = None, contact_id: str | None = None, limit: int = 100) -> Dict[str, Any]:
    if not str(site_id or "").strip() and not str(contact_id or "").strip():
        raise HTTPException(status_code=400, detail="site_id or contact_id is required")
    items = [dict(item) for item in _lead_interaction_cache().values()]
    if str(site_id or "").strip():
        items = [item for item in items if str(item.get("site_id") or "") == str(site_id or "").strip()]
    if str(contact_id or "").strip():
        items = [item for item in items if str(item.get("contact_id") or "") == str(contact_id or "").strip()]
    items.sort(key=lambda item: str(item.get("started_at") or ""), reverse=True)
    return {
        "count": len(items),
        "items": items[: max(1, min(limit, 500))],
    }


@app.get("/api/v1/lead/{site_id}/contactability")
def lead_contactability(site_id: str) -> Dict[str, Any]:
    row = _data_cache().get("by_site", {}).get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")
    contact = _contact_record_for_site(site_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"No contact resolved for site_id {site_id}")
    return {
        "site_id": site_id,
        "contact_id": contact.get("contact_id"),
        "display_name": contact.get("display_name"),
        "preferred_channel": contact.get("preferred_channel"),
        "contactability_score": contact.get("contactability_score"),
        "contactability_label": contact.get("contactability_label"),
        "primary_email": contact.get("primary_email"),
        "website_url": contact.get("website_url"),
        "contact_form_url": contact.get("contact_form_url"),
        "mailing_address": contact.get("mailing_address"),
        "contact_paths": contact.get("contact_paths") or [],
        "identity_sources": contact.get("identity_sources") or [],
        "source_record_ids": contact.get("source_record_ids") or [],
    }


@app.get("/api/v1/lead/{site_id}/next-action")
def lead_next_action(site_id: str) -> Dict[str, Any]:
    return _lead_next_action_payload(site_id)


@app.get("/api/v1/agent/tasks/next")
def agent_tasks_next(zip: str | None = None, h3_cell: str | None = None, agent_id: str | None = None) -> Dict[str, Any]:
    task = _next_agent_task(zip=zip, h3_cell=h3_cell, agent_id=agent_id)
    rows = _scored_agent_task_rows(zip=zip, h3_cell=h3_cell)
    counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        queue_bucket = str(((row.get("work_queue") or {}).get("bucket") or "park")).strip().lower() or "park"
        counts[queue_bucket] += 1
    return {
        "framework": CHOW_AGENT_FRAMEWORK,
        "scope": {"zip": zip, "h3_cell": h3_cell},
        "counts": {key: int(counts.get(key, 0)) for key in ["work_now", "follow_up", "verify_first", "park"]},
        "task": task,
    }


@app.post("/api/v1/agent/tasks/{task_id}/claim")
def agent_task_claim(task_id: str, payload: AgentTaskClaimPayload) -> Dict[str, Any]:
    row = _agent_task_row_from_id(task_id)
    current = _build_agent_task_payload(row)
    now = _utc_now_iso()
    claim_count = int((current.get("claim_count") or (_agent_task_for(task_id) or {}).get("claim_count") or 0)) + 1
    claimed = dict(current)
    claimed.update(
        {
            "status": "claimed",
            "claimed_by": str(payload.agent_id or "chow").strip() or "chow",
            "claimed_at": now,
            "updated_at": now,
            "claim_note": str(payload.note or "").strip() or None,
            "claim_count": claim_count,
            "actor_role": str(payload.actor_role or "agent").strip() or "agent",
        }
    )
    persisted = _persist_agent_task(claimed)
    return {"framework": CHOW_AGENT_FRAMEWORK, "task": persisted}


@app.post("/api/v1/agent/tasks/{task_id}/result")
def agent_task_result(task_id: str, payload: AgentTaskResultPayload) -> Dict[str, Any]:
    status_value = str(payload.status or "").strip().lower()
    if status_value not in {"completed", "deferred", "blocked"}:
        raise HTTPException(status_code=400, detail="status must be one of completed, deferred, blocked")
    row = _agent_task_row_from_id(task_id)
    current = _build_agent_task_payload(row)
    site_id = str(row.get("site_id") or "")
    now = _utc_now_iso()

    operator_status = None
    if payload.operator_status:
        operator_status = _set_operator_status(site_id, payload.operator_status, note=payload.note or f"task_result_{status_value}")
    elif status_value == "deferred":
        operator_status = _set_operator_status(site_id, "follow_up", note=payload.note or "task_deferred")

    outcome = None
    if payload.outcome_status:
        outcome = _upsert_lead_outcome_record(
            site_id=site_id,
            status_value=payload.outcome_status,
            note=str(payload.note or "").strip(),
            objection=str(payload.objection or "").strip(),
            reason=str(payload.reason or "").strip(),
            product=str(payload.product or row.get("primary_product") or "").strip(),
            realized_revenue_usd=payload.realized_revenue_usd,
            realized_profit_usd=payload.realized_profit_usd,
            attribution_channel=str(payload.channel or "workspace").strip(),
            attribution_signal_keys=_signal_keys_for_row(row),
        )

    interaction = _upsert_interaction_record(
        LeadInteractionCreatePayload(
            site_id=site_id,
            contact_id=(_contact_record_for_site(site_id) or {}).get("contact_id"),
            channel=str(payload.channel or "workspace").strip() or "workspace",
            direction="outbound",
            interaction_type=str(payload.interaction_type or "agent_task").strip() or "agent_task",
            started_at=str((current or {}).get("claimed_at") or now),
            ended_at=now,
            result_status=status_value,
            objection=payload.objection,
            reason=payload.reason,
            note=payload.note,
            next_follow_up_at=payload.next_follow_up_at,
            next_best_action=payload.next_best_action,
            agent_id=str(payload.agent_id or (current.get("claimed_by") or "chow")).strip() or "chow",
            attribution_signal_keys=_signal_keys_for_row(row),
        )
    )

    updated = dict(current)
    updated.update(
        {
            "status": status_value,
            "updated_at": now,
            "completed_at": now if status_value == "completed" else updated.get("completed_at"),
            "result_note": str(payload.note or "").strip() or None,
            "last_result_status": status_value,
            "last_operator_status": (operator_status or {}).get("status") if operator_status else ((row.get("operator_status") or {}).get("status")),
            "last_outcome_status": (outcome or {}).get("status") if outcome else ((row.get("lead_outcome") or {}).get("status")),
            "next_follow_up_at": str(payload.next_follow_up_at or "").strip() or None,
            "next_best_action": str(payload.next_best_action or "").strip() or None,
        }
    )
    persisted = _persist_agent_task(updated)
    return {
        "framework": CHOW_AGENT_FRAMEWORK,
        "task": persisted,
        "operator_status": operator_status or _operator_status_for(site_id),
        "lead_outcome": outcome or _lead_outcome_for(site_id),
        "interaction": interaction,
    }


@app.get("/api/v1/voice/site/{site_id}/brief")
def voice_site_brief(site_id: str) -> Dict[str, Any]:
    return _build_voice_brief(site_id)


@app.post("/api/v1/voice/calls/status")
def voice_call_status(payload: VoiceCallStatusPayload) -> Dict[str, Any]:
    site_id = str(payload.site_id or "").strip()
    if not site_id:
        raise HTTPException(status_code=400, detail="site_id is required")
    session = _ensure_calling_session(site_id, payload.session_id)
    updated = _voice_status_transition(session, payload)
    persisted = _persist_calling_session(updated)
    return {
        "framework": VOICE_AGENT_FRAMEWORK,
        "site_id": site_id,
        "session_id": persisted.get("session_id"),
        "status": persisted.get("status"),
        "provider_call_id": persisted.get("provider_call_id"),
        "last_event": ((persisted.get("event_log") or [])[-1] if persisted.get("event_log") else None),
    }


@app.post("/api/v1/voice/calls/result")
def voice_call_result(payload: VoiceCallResultPayload) -> Dict[str, Any]:
    site_id = str(payload.site_id or "").strip()
    if not site_id:
        raise HTTPException(status_code=400, detail="site_id is required")
    session = _ensure_calling_session(site_id, payload.session_id)
    call_event = _voice_result_to_call_event(payload, str(session.get("session_id") or ""))
    updated = _apply_calling_session_event(dict(session), call_event)
    updated["provider_call_id"] = str(payload.provider_call_id or updated.get("provider_call_id") or "").strip() or None
    if payload.callback_at or payload.needs_human or payload.human_transfer_target:
        live_assist = dict(updated.get("live_assist") or {})
        if payload.callback_at:
            live_assist["callback_at"] = str(payload.callback_at)
        if payload.needs_human:
            live_assist["needs_human"] = True
        if payload.human_transfer_target:
            live_assist["human_transfer_target"] = str(payload.human_transfer_target)
        if payload.next_best_action:
            live_assist["next_best_action"] = str(payload.next_best_action)
        updated["live_assist"] = live_assist
    persisted = _persist_calling_session(updated)

    interaction = _upsert_interaction_record(
        LeadInteractionCreatePayload(
            site_id=site_id,
            contact_id=_contact_record_for_site(site_id).get("contact_id") if _contact_record_for_site(site_id) else None,
            channel="phone",
            direction="outbound",
            interaction_type="call",
            started_at=str(session.get("created_at") or _utc_now_iso()),
            ended_at=_utc_now_iso(),
            result_status=str(payload.outcome_status or payload.disposition or "completed"),
            objection=payload.objection,
            reason=payload.reason,
            transcript_excerpt=payload.transcript_excerpt,
            note=payload.detail,
            playbook_id=str(session.get("playbook_id") or ""),
            orchestrator_run_id=str(session.get("orchestrator_run_id") or ""),
            calling_session_id=str(session.get("session_id") or ""),
            next_follow_up_at=payload.callback_at,
            next_best_action=payload.next_best_action,
            attribution_signal_keys=_signal_keys_for_row(_data_cache().get("by_site", {}).get(site_id, {})),
        )
    )

    disposition = _slug_token(payload.disposition).replace("-", "_")
    if disposition in {"won"}:
        _set_operator_status(site_id, "closed", note="voice_result_won")
    elif disposition in {"qualified", "follow_up", "callback", "transferred_human"} or payload.needs_human or payload.callback_at:
        _set_operator_status(site_id, "follow_up", note="voice_result_follow_up")
    elif disposition in {"voicemail", "no_answer", "busy"}:
        _set_operator_status(site_id, "contacted", note="voice_result_attempted")

    return {
        "framework": VOICE_AGENT_FRAMEWORK,
        "site_id": site_id,
        "session_id": persisted.get("session_id"),
        "session_status": persisted.get("status"),
        "interaction_id": interaction.get("interaction_id"),
        "operator_status": _operator_status_for(site_id),
        "lead_outcome": _lead_outcome_for(site_id),
        "last_event": ((persisted.get("event_log") or [])[-1] if persisted.get("event_log") else None),
    }


@app.get("/api/v1/schema/vertical/{vertical_id}")
def schema_vertical_pack(vertical_id: str) -> Dict[str, Any]:
    vid = _slug_token(vertical_id)
    packs = {
        "energy": {
            "required_signal_keys": ["permit", "flood_risk", "outage", "utility_rate"],
            "offer_types": ["solar", "roofing", "hvac_heat_pump", "battery_backup"],
            "primary_kpis": ["annual_savings_usd", "payback_years", "npv_15y_usd"],
        },
        "roofing": {
            "required_signal_keys": ["permit", "storm", "flood_risk"],
            "offer_types": ["roof_replacement", "roof_repair", "roof_inspection"],
            "primary_kpis": ["urgency_score", "estimated_ticket_value_usd", "win_probability_proxy"],
        },
        "saas": {
            "required_signal_keys": ["intent", "engagement", "firmographic_fit"],
            "offer_types": ["trial", "demo", "pilot"],
            "primary_kpis": ["pipeline_value_usd", "activation_rate", "expansion_probability"],
        },
    }
    if vid not in packs:
        raise HTTPException(status_code=404, detail=f"Unknown vertical pack {vertical_id}")
    return {
        "schema_id": "dg-vertical-pack-v1",
        "vertical_id": vid,
        "pack": packs[vid],
    }


@app.post("/api/v1/playbooks/compile")
def playbook_compile(payload: PlaybookCompilePayload) -> Dict[str, Any]:
    site_id = str(payload.site_id or "").strip()
    if not site_id:
        raise HTTPException(status_code=400, detail="site_id is required")

    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    compiled = _compile_playbook(
        row=row,
        objective=payload.objective,
        execution_mode=payload.execution_mode,
        preferred_channels=payload.preferred_channels,
        strict_guardrails=bool(payload.strict_guardrails),
    )

    store = _read_compiled_playbook_store()
    store[str(compiled.get("playbook_id") or "")] = compiled
    _write_compiled_playbook_store(store)
    _compiled_playbook_cache.cache_clear()
    return compiled


@app.get("/api/v1/playbooks/{playbook_id}")
def playbook_get(playbook_id: str) -> Dict[str, Any]:
    playbook = _compiled_playbook_for(playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail=f"Unknown playbook_id {playbook_id}")
    return playbook


@app.post("/api/v1/agents/outreach/jobs")
def outreach_job_create(payload: OutreachJobCreatePayload) -> Dict[str, Any]:
    site_id = str(payload.site_id or "").strip()
    if not site_id:
        raise HTTPException(status_code=400, detail="site_id is required")

    existing = _find_outreach_job_by_idempotency(site_id, str(payload.idempotency_key or ""))
    if existing:
        return {"reused": True, **existing}

    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    playbook: Dict[str, Any] | None = None
    if payload.playbook_id:
        playbook = _compiled_playbook_for(str(payload.playbook_id))
        if not playbook:
            raise HTTPException(status_code=404, detail=f"Unknown playbook_id {payload.playbook_id}")
        if str(playbook.get("site_id") or "") != site_id:
            raise HTTPException(status_code=400, detail="playbook_id does not match site_id")

    if playbook is None:
        playbook = _compile_playbook(
            row=row,
            objective=payload.objective,
            execution_mode=payload.execution_mode,
            preferred_channels=payload.preferred_channels,
            strict_guardrails=bool(payload.strict_guardrails),
        )
        playbook_store = _read_compiled_playbook_store()
        playbook_store[str(playbook.get("playbook_id") or "")] = playbook
        _write_compiled_playbook_store(playbook_store)
        _compiled_playbook_cache.cache_clear()

    job = _build_outreach_job_record(
        site_id=site_id,
        playbook=playbook,
        requested_channel=payload.requested_channel,
        idempotency_key=payload.idempotency_key,
        dry_run=bool(payload.dry_run),
    )
    store = _read_outreach_job_store()
    store[str(job.get("job_id") or "")] = job
    _write_outreach_job_store(store)
    _outreach_job_cache.cache_clear()
    return {"reused": False, **job}


@app.get("/api/v1/agents/outreach/jobs/{job_id}")
def outreach_job_get(job_id: str) -> Dict[str, Any]:
    job = _outreach_job_for(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Unknown outreach job {job_id}")
    return job


@app.post("/api/v1/agents/outreach/jobs/{job_id}/dispatch")
def outreach_job_dispatch(job_id: str, payload: DispatchRequestPayload) -> Dict[str, Any]:
    job = _outreach_job_for(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Unknown outreach job {job_id}")
    updated = _dispatch_outreach_job(dict(job), payload)
    return _persist_outreach_job(updated)


@app.post("/api/v1/agents/outreach/events")
def outreach_job_event(payload: OutreachJobEventPayload) -> Dict[str, Any]:
    job_id = str(payload.job_id or "").strip()
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    store = _read_outreach_job_store()
    current = store.get(job_id)
    if not isinstance(current, dict):
        raise HTTPException(status_code=404, detail=f"Unknown outreach job {job_id}")

    updated = _apply_outreach_job_event(dict(current), payload)
    store[job_id] = updated
    _write_outreach_job_store(store)
    _outreach_job_cache.cache_clear()
    return updated


@app.get("/api/v1/inbox/status")
def inbox_status() -> Dict[str, Any]:
    return {
        "framework": "dg-inbox-v1",
        "mailbox": _imap_provider_descriptor(),
    }


@app.get("/api/v1/inbox/threads")
def inbox_thread_list(limit: int = 50) -> Dict[str, Any]:
    limit = max(1, min(200, int(limit)))
    rows = [_refresh_email_thread(item) for item in _email_threads().values()]
    rows.sort(key=lambda item: str(item.get("last_message_at") or item.get("updated_at") or ""), reverse=True)
    return {
        "framework": "dg-inbox-v1",
        "count": len(rows),
        "items": rows[:limit],
    }


@app.get("/api/v1/inbox/threads/{thread_id}")
def inbox_thread_get(thread_id: str) -> Dict[str, Any]:
    thread = _email_thread_for(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Unknown inbox thread {thread_id}")
    return {
        "framework": "dg-inbox-v1",
        "thread": _refresh_email_thread(thread),
    }


@app.post("/api/v1/inbox/import")
def inbox_import(payload: InboxImportPayload) -> Dict[str, Any]:
    return _import_inbox_messages(payload)


@app.post("/api/v1/inbox/poll")
def inbox_poll(payload: MailboxPollPayload) -> Dict[str, Any]:
    return _imap_fetch_messages(payload)


@app.post("/api/v1/agents/calling/sessions")
def calling_session_create(payload: CallingSessionCreatePayload) -> Dict[str, Any]:
    site_id = str(payload.site_id or "").strip()
    if not site_id:
        raise HTTPException(status_code=400, detail="site_id is required")

    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    playbook: Dict[str, Any] | None = None
    if payload.playbook_id:
        playbook = _compiled_playbook_for(str(payload.playbook_id))
        if not playbook:
            raise HTTPException(status_code=404, detail=f"Unknown playbook_id {payload.playbook_id}")
        if str(playbook.get("site_id") or "") != site_id:
            raise HTTPException(status_code=400, detail="playbook_id does not match site_id")

    if playbook is None:
        playbook = _compile_playbook(
            row=row,
            objective=payload.objective,
            execution_mode=payload.execution_mode,
            preferred_channels=payload.preferred_channels,
            strict_guardrails=bool(payload.strict_guardrails),
        )
        playbook_store = _read_compiled_playbook_store()
        playbook_store[str(playbook.get("playbook_id") or "")] = playbook
        _write_compiled_playbook_store(playbook_store)
        _compiled_playbook_cache.cache_clear()

    session = _build_calling_session_record(
        site_id=site_id,
        playbook=playbook,
        call_direction=payload.call_direction,
    )
    store = _read_calling_session_store()
    store[str(session.get("session_id") or "")] = session
    _write_calling_session_store(store)
    _calling_session_cache.cache_clear()
    return session


@app.get("/api/v1/agents/calling/sessions/{session_id}")
def calling_session_get(session_id: str) -> Dict[str, Any]:
    session = _calling_session_for(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Unknown calling session {session_id}")
    return session


@app.post("/api/v1/agents/calling/sessions/{session_id}/dispatch")
def calling_session_dispatch(session_id: str, payload: DispatchRequestPayload) -> Dict[str, Any]:
    session = _calling_session_for(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Unknown calling session {session_id}")
    updated = _dispatch_calling_session(dict(session), payload)
    return _persist_calling_session(updated)


@app.get("/api/v1/agents/site/{site_id}/execution")
def site_execution_summary(site_id: str) -> Dict[str, Any]:
    return _execution_summary_for_site(site_id)


@app.post("/api/v1/agents/calling/events")
def calling_session_event(payload: CallingSessionEventPayload) -> Dict[str, Any]:
    session_id = str(payload.session_id or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    store = _read_calling_session_store()
    current = store.get(session_id)
    if not isinstance(current, dict):
        raise HTTPException(status_code=404, detail=f"Unknown calling session {session_id}")

    updated = _apply_calling_session_event(dict(current), payload)
    store[session_id] = updated
    _write_calling_session_store(store)
    _calling_session_cache.cache_clear()
    return updated


@app.post("/api/v1/orchestrator/runs")
def orchestrator_run_create(payload: OrchestratorRunCreatePayload) -> Dict[str, Any]:
    site_id = str(payload.site_id or "").strip()
    if not site_id:
        raise HTTPException(status_code=400, detail="site_id is required")

    existing = _find_orchestrator_run_by_idempotency(site_id, str(payload.idempotency_key or ""))
    if existing:
        return {"reused": True, **existing}

    data = _data_cache()
    row = data["by_site"].get(site_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown site_id {site_id}")

    playbook = _compile_playbook(
        row=row,
        objective=payload.objective,
        execution_mode=payload.execution_mode,
        preferred_channels=payload.preferred_channels,
        strict_guardrails=bool(payload.strict_guardrails),
    )
    _persist_compiled_playbook(playbook)

    run = _build_orchestrator_run(row=row, playbook=playbook, payload=payload)
    if not bool(payload.approval_required) and bool(payload.auto_execute):
        run = _auto_execute_orchestrator_run(run)
    _persist_orchestrator_run(run)
    return {"reused": False, **run}


@app.get("/api/v1/orchestrator/runs/{run_id}")
def orchestrator_run_get(run_id: str) -> Dict[str, Any]:
    run = _orchestrator_run_for(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Unknown orchestrator run {run_id}")
    return run


@app.post("/api/v1/orchestrator/actions/{action_id}/approve")
def orchestrator_action_approve(action_id: str, payload: OrchestratorActionApprovalPayload) -> Dict[str, Any]:
    approver = str(payload.approver or "").strip()
    if not approver:
        raise HTTPException(status_code=400, detail="approver is required")

    run = _find_orchestrator_run_by_action(action_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Unknown action_id {action_id}")

    action = next((a for a in (run.get("actions") or []) if str(a.get("action_id") or "") == str(action_id or "")), None)
    if not action:
        raise HTTPException(status_code=404, detail=f"Unknown action_id {action_id}")

    validation = _governance_validation_result(
        run=run,
        action=action,
        actor_id=approver,
        actor_role=str(payload.actor_role or "manager"),
    )
    run = _append_governance_audit(run, {"event": "approval_validation", **validation})
    if not bool(validation.get("allowed")):
        _persist_orchestrator_run(run)
        raise HTTPException(status_code=403, detail={"message": "Governance validation failed", **validation})

    updated = _apply_orchestrator_approval(run, action_id, payload)
    _persist_orchestrator_run(updated)
    return updated


CRAIGSLIST_SIGNAL_FRAMEWORK = "dg-craigslist-signal-v1"
CRAIGSLIST_OUTREACH_FRAMEWORK = "dg-craigslist-outreach-v1"
CRAIGSLIST_SIGNAL_JSON = ROOT / "data/processed/craigslist_job_signals.json"
CRAIGSLIST_COMPANY_RESEARCH_JSON = ROOT / "data/processed/craigslist_company_research.json"
CRAIGSLIST_RESEARCH_FEEDBACK_JSON = ROOT / "data/processed/craigslist_research_feedback.json"
CRAIGSLIST_OUTREACH_QUEUE_JSON = ROOT / "data/processed/craigslist_outreach_queue.json"
CRAIGSLIST_FETCH_SCRIPT = ROOT / "scripts/fetch_craigslist_job_signals.py"
CRAIGSLIST_ENRICH_SCRIPT = ROOT / "scripts/enrich_craigslist_opportunities.py"


class CraigslistSignalRefreshPayload(BaseModel):
    limit_per_query: int = 30
    timeout_sec: int = 45


class CraigslistOutreachQueuePayload(BaseModel):
    actor_id: str
    actor_role: str = "manager"
    channel: str | None = None
    note: str | None = None
    force: bool = False


class CraigslistManualSignalPayload(BaseModel):
    title: str
    company_name_guess: str | None = None
    market_id: str = "manual"
    query: str = "manual"
    posting_url: str | None = None
    posting_description: str | None = None
    role_family: str = "backoffice_data_ops"
    automation_score: float = 0.7
    confidence: float = 0.7
    recommended_channel: str = "manual_research"
    contact_hint_emails: List[str] | None = None
    contact_hint_phones: List[str] | None = None
    automation_hypotheses: List[str] | None = None
    outreach_angle: str | None = None
    posted_at: str | None = None


class CraigslistManualImportPayload(BaseModel):
    actor_id: str
    actor_role: str = "manager"
    opportunities: List[CraigslistManualSignalPayload]


class CraigslistOutreachQueueReviewPayload(BaseModel):
    actor_id: str
    actor_role: str = "manager"
    note: str | None = None
    email_subject: str | None = None
    email_body: str | None = None
    call_opening: str | None = None
    recipient_email: str | None = None
    research_quality: str | None = None
    company_match: str | None = None
    contact_path_status: str | None = None
    draft_status: str | None = None


class CraigslistResearchRefreshPayload(BaseModel):
    actor_id: str
    actor_role: str = "manager"
    search_provider: str = "auto"
    text_provider: str = "auto"
    timeout_sec: int = 45
    max_fetch_pages: int = 3
    limit_per_query: int = 5
    note: str | None = None


def _cl_read_signal_payload() -> Dict[str, Any]:
    default = {
        "generated_at": None,
        "config_version": "v0",
        "source_policy": {"mode": "rss_only"},
        "count": 0,
        "opportunities": [],
        "query_stats": [],
    }
    if not CRAIGSLIST_SIGNAL_JSON.exists():
        return default
    try:
        raw = json.loads(CRAIGSLIST_SIGNAL_JSON.read_text(encoding="utf-8"))
    except Exception:
        return default
    if not isinstance(raw, dict):
        return default
    out = dict(default)
    out.update(raw)
    opportunities = raw.get("opportunities")
    if not isinstance(opportunities, list):
        out["opportunities"] = []
    return out


@lru_cache(maxsize=1)
def _cl_signal_payload_cache() -> Dict[str, Any]:
    return _cl_read_signal_payload()


def _cl_opportunities() -> List[Dict[str, Any]]:
    payload = _cl_signal_payload_cache()
    return [dict(item) for item in (payload.get("opportunities") or []) if isinstance(item, dict)]


def _cl_find_opportunity(opportunity_id: str) -> Dict[str, Any] | None:
    key = str(opportunity_id or "").strip()
    if not key:
        return None
    for item in _cl_opportunities():
        if str(item.get("opportunity_id") or "") == key:
            return item
    return None


def _cl_read_company_research_payload() -> Dict[str, Any]:
    default = {
        "generated_at": None,
        "config_version": "v0",
        "count": 0,
        "records": [],
        "summary": {},
    }
    if not CRAIGSLIST_COMPANY_RESEARCH_JSON.exists():
        return default
    try:
        raw = json.loads(CRAIGSLIST_COMPANY_RESEARCH_JSON.read_text(encoding="utf-8"))
    except Exception:
        return default
    if not isinstance(raw, dict):
        return default
    out = dict(default)
    out.update(raw)
    records = raw.get("records")
    if not isinstance(records, list):
        out["records"] = []
    return out


@lru_cache(maxsize=1)
def _cl_company_research_cache() -> Dict[str, Any]:
    return _cl_read_company_research_payload()


def _cl_research_record_for(opportunity_id: str) -> Dict[str, Any] | None:
    key = str(opportunity_id or "").strip()
    if not key:
        return None
    for item in (_cl_company_research_cache().get("records") or []):
        if isinstance(item, dict) and str(item.get("opportunity_id") or "") == key:
            return dict(item)
    return None


def _cl_read_research_feedback_payload() -> Dict[str, Any]:
    default = {"updated_at": None, "records": []}
    if not CRAIGSLIST_RESEARCH_FEEDBACK_JSON.exists():
        return default
    try:
        raw = json.loads(CRAIGSLIST_RESEARCH_FEEDBACK_JSON.read_text(encoding="utf-8"))
    except Exception:
        return default
    if not isinstance(raw, dict):
        return default
    records = raw.get("records")
    return {
        "updated_at": raw.get("updated_at"),
        "records": list(records) if isinstance(records, list) else [],
    }


@lru_cache(maxsize=1)
def _cl_research_feedback_cache() -> Dict[str, Any]:
    return _cl_read_research_feedback_payload()


def _cl_write_research_feedback_payload(payload: Dict[str, Any]) -> None:
    CRAIGSLIST_RESEARCH_FEEDBACK_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = CRAIGSLIST_RESEARCH_FEEDBACK_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(CRAIGSLIST_RESEARCH_FEEDBACK_JSON)
    _cl_research_feedback_cache.cache_clear()


def _cl_company_feedback_key(value: Any) -> str:
    return _slug_token(str(value or "")).replace("-", "_") or "unknown"


def _cl_feedback_host(value: Any) -> str:
    try:
        parsed = urllib.parse.urlparse(str(value or "").strip())
        host = str(parsed.netloc or "").lower().strip()
    except Exception:
        host = ""
    if host.startswith("www."):
        host = host[4:]
    return host


def _cl_research_feedback_for(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    payload = _cl_research_feedback_cache()
    company_key = _cl_company_feedback_key(opportunity.get("company_name_guess"))
    opportunity_id = str(opportunity.get("opportunity_id") or "").strip()
    host = _cl_feedback_host((research or {}).get("website_url") or (research or {}).get("best_match_url"))
    for item in payload.get("records") or []:
        if not isinstance(item, dict) or not bool(item.get("active")):
            continue
        item_company_key = str(item.get("company_key") or "")
        item_opportunity_id = str(item.get("opportunity_id") or "")
        item_host = str(item.get("resolved_host") or "")
        if host and item_host and item_host != host:
            continue
        if item_opportunity_id and opportunity_id and item_opportunity_id == opportunity_id:
            return dict(item)
        if item_company_key and company_key and item_company_key == company_key:
            return dict(item)
    return None


def _cl_upsert_research_feedback(record: Dict[str, Any]) -> Dict[str, Any] | None:
    opportunity = dict(record.get("opportunity") or {})
    research = dict(record.get("research") or {})
    review = dict(record.get("review") or {})
    company_key = _cl_company_feedback_key(opportunity.get("company_name_guess"))
    opportunity_id = str(opportunity.get("opportunity_id") or "").strip()
    host = _cl_feedback_host(research.get("website_url") or research.get("best_match_url"))
    if not host:
        return None

    company_match = str(review.get("company_match") or "").strip()
    research_quality = str(review.get("research_quality") or "").strip()
    active = company_match == "wrong" or research_quality == "bad"
    reason_parts = [part for part in [company_match or None, research_quality or None] if part]
    note = " / ".join(reason_parts) if reason_parts else None

    payload = _cl_read_research_feedback_payload()
    records = [dict(item) for item in (payload.get("records") or []) if isinstance(item, dict)]
    updated_at = _utc_now_iso()
    target = None
    for item in records:
        if str(item.get("company_key") or "") == company_key and str(item.get("resolved_host") or "") == host:
            target = item
            break
    if target is None:
        target = {
            "feedback_id": f"clf_{company_key}_{_slug_token(host)}",
            "company_key": company_key,
            "company_name_guess": str(opportunity.get("company_name_guess") or "").strip() or None,
            "opportunity_id": opportunity_id or None,
            "resolved_host": host,
        }
        records.append(target)

    target.update(
        {
            "active": active,
            "resolved_company_name": str(research.get("resolved_company_name") or "").strip() or None,
            "website_url": str(research.get("website_url") or research.get("best_match_url") or "").strip() or None,
            "company_match": company_match or None,
            "research_quality": research_quality or None,
            "contact_path_status": str(review.get("contact_path_status") or "").strip() or None,
            "draft_status": str(review.get("draft_status") or "").strip() or None,
            "reason": note,
            "updated_at": updated_at,
            "reviewed_by": str(review.get("reviewed_by") or "").strip() or None,
            "reviewed_role": str(review.get("reviewed_role") or "").strip() or None,
        }
    )
    payload["updated_at"] = updated_at
    payload["records"] = records
    _cl_write_research_feedback_payload(payload)
    return dict(target)


def _cl_read_outreach_queue_store() -> Dict[str, Dict[str, Any]]:
    if not CRAIGSLIST_OUTREACH_QUEUE_JSON.exists():
        return {}
    try:
        raw = json.loads(CRAIGSLIST_OUTREACH_QUEUE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for queue_id, payload in raw.items():
        if isinstance(payload, dict):
            out[str(queue_id)] = dict(payload)
    return out


def _cl_write_outreach_queue_store(data: Dict[str, Dict[str, Any]]) -> None:
    CRAIGSLIST_OUTREACH_QUEUE_JSON.parent.mkdir(parents=True, exist_ok=True)
    tmp = CRAIGSLIST_OUTREACH_QUEUE_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(CRAIGSLIST_OUTREACH_QUEUE_JSON)


@lru_cache(maxsize=1)
def _cl_outreach_queue_cache() -> Dict[str, Dict[str, Any]]:
    return _cl_read_outreach_queue_store()


def _cl_queue_record_for(queue_id: str) -> Dict[str, Any] | None:
    payload = _cl_outreach_queue_cache().get(str(queue_id), {})
    return dict(payload) if isinstance(payload, dict) and payload else None


def _persist_cl_queue_record(record: Dict[str, Any]) -> Dict[str, Any]:
    queue_id = str(record.get("queue_id") or "").strip()
    if not queue_id:
        raise HTTPException(status_code=400, detail="queue_id is required")
    store = _cl_read_outreach_queue_store()
    store[queue_id] = dict(record)
    _cl_write_outreach_queue_store(store)
    _cl_outreach_queue_cache.cache_clear()
    return dict(store[queue_id])


def _cl_company_identity_tokens(value: Any) -> set[str]:
    stop = {"the", "and", "for", "inc", "llc", "co", "corp", "company", "services", "service", "group", "test", "home"}
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(value or "").lower())
        if len(token) > 2 and token not in stop
    }


def _cl_research_identity_is_trustworthy(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> bool:
    payload = dict(research or {})
    if not payload or str(payload.get("research_status") or "") != "ok":
        return False
    if _cl_research_feedback_for(opportunity, payload):
        return False
    raw_guess = str(opportunity.get("company_name_guess") or "").strip().lower()
    raw_resolved = str(payload.get("resolved_company_name") or "").strip().lower()
    guess_tokens = _cl_company_identity_tokens(raw_guess)
    resolved_tokens = _cl_company_identity_tokens(raw_resolved)
    overlap = guess_tokens & resolved_tokens
    if raw_guess and raw_resolved and (raw_guess in raw_resolved or raw_resolved in raw_guess):
        return True
    if len(overlap) >= 2:
        return True
    if not guess_tokens and float(payload.get("research_confidence") or 0.0) >= 0.8:
        return True
    return False


def _cl_research_is_trustworthy(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> bool:
    payload = dict(research or {})
    if not payload:
        return False
    if _cl_research_feedback_for(opportunity, payload):
        return False
    if _cl_research_identity_is_trustworthy(opportunity, payload):
        return True
    if str(payload.get("research_status") or "") != "ok":
        return False
    guess_tokens = _cl_company_identity_tokens(opportunity.get("company_name_guess"))
    website_url = str(payload.get("website_url") or "").lower()
    if guess_tokens and any(token in website_url for token in guess_tokens if len(token) >= 5):
        return True
    return False


def _cl_company_name(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> str:
    trusted = dict(research or {}) if _cl_research_identity_is_trustworthy(opportunity, research) else {}
    company = str(trusted.get("resolved_company_name") or opportunity.get("company_name_guess") or "your team").strip()
    return company or "your team"


def _cl_pain_line(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> str:
    trusted = dict(research or {}) if _cl_research_is_trustworthy(opportunity, research) else {}
    research_pain = str(trusted.get("likely_operational_pain") or "").strip()
    if research_pain:
        return research_pain

    role_family = str(opportunity.get("role_family") or "back office").replace("_", " ").strip().lower()
    pain_line = "Usually when a team is hiring for a role like that, it means too much repetitive work is still sitting on one person or falling between systems."
    if role_family == "payroll finance admin":
        pain_line = "Usually when a team is hiring for that kind of role, it means payroll, billing, AP/AR, or reconciliation work is eating more time than it should."
    elif role_family == "backoffice data ops":
        pain_line = "Usually when a team is hiring for that kind of role, it means scheduling, data entry, inbox follow-up, or handoffs are taking more manual work than they should."
    elif role_family == "customer support ops":
        pain_line = "Usually when a team is hiring for that kind of role, it means repeat customer questions and routing work are consuming too much operator time."
    return pain_line


def _cl_first_win(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> str:
    trusted = dict(research or {}) if _cl_research_is_trustworthy(opportunity, research) else {}
    research_win = str(trusted.get("likely_first_automation_win") or "").strip()
    if research_win:
        return research_win
    hypotheses = [str(v).strip() for v in (opportunity.get("automation_hypotheses") or []) if str(v).strip()]
    return hypotheses[0] if hypotheses else "one repeatable workflow that is currently manual"


def _cl_outreach_contact_emails(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> List[str]:
    trusted = dict(research or {}) if _cl_research_is_trustworthy(opportunity, research) else {}
    emails = [str(v).strip() for v in (opportunity.get("contact_hint_emails") or []) if str(v).strip()]
    emails.extend(str(v).strip() for v in (trusted.get("emails") or []) if str(v).strip())
    out: List[str] = []
    seen: set[str] = set()
    for email in emails:
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(email)
    return out


def _cl_recipient_preview(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None, record: Dict[str, Any] | None = None) -> Dict[str, Any]:
    review = dict((record or {}).get("review") or {})
    override_email = str(review.get("recipient_email") or "").strip()
    hint_emails = [str(v).strip() for v in (opportunity.get("contact_hint_emails") or []) if str(v).strip()]
    trusted = dict(research or {}) if _cl_research_is_trustworthy(opportunity, research) else {}
    research_emails = [str(v).strip() for v in (trusted.get("emails") or []) if str(v).strip()]
    combined: List[str] = []
    seen: set[str] = set()
    for email in ([override_email] if override_email else []) + hint_emails + research_emails:
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        combined.append(email)
    selected = combined[0] if combined else ""
    if override_email:
        source = "operator_override"
    elif selected and any(selected.lower() == email.lower() for email in hint_emails):
        source = "opportunity_hint"
    elif selected:
        source = "research"
    else:
        source = "none"
    return {
        "selected_email": selected or None,
        "source": source,
        "hint_emails": hint_emails,
        "research_emails": research_emails,
        "all_emails": combined,
    }


def _cl_enrich_queue_record(record: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(record or {})
    opportunity = dict(out.get("opportunity") or {})
    research = dict(out.get("research") or {})
    thread = _email_thread_for_link("craigslist_outreach_queue", str(out.get("queue_id") or "")) if str(out.get("queue_id") or "").strip() else None
    if not research and opportunity:
        research = _cl_research_record_for(str(opportunity.get("opportunity_id") or "")) or {}
    feedback = _cl_research_feedback_for(opportunity, research)
    identity_trustworthy = _cl_research_identity_is_trustworthy(opportunity, research)
    research_trustworthy = _cl_research_is_trustworthy(opportunity, research)
    out["research"] = research or None
    out["research_feedback"] = feedback
    out["research_identity_trustworthy"] = identity_trustworthy
    out["research_trustworthy"] = research_trustworthy
    if not isinstance(out.get("generated_drafts"), dict) or not out.get("generated_drafts"):
        out["generated_drafts"] = {
            "email_subject": _cl_email_subject(opportunity, research),
            "email_body": _cl_email_body(opportunity, research),
            "call_opening": _cl_call_opening(opportunity, research),
        }
    if not isinstance(out.get("drafts"), dict) or not out.get("drafts"):
        out["drafts"] = dict(out.get("generated_drafts") or {})
    out["recipient_preview"] = _cl_recipient_preview(opportunity, research, out)
    if not isinstance(out.get("review"), dict):
        out["review"] = {}
    out["inbox"] = _email_thread_summary(thread) or dict(out.get("inbox") or {}) or None
    if not isinstance(out.get("reply_state"), dict):
        out["reply_state"] = {
            "reply_received": bool((out.get("inbox") or {}).get("has_reply")),
            "last_reply_at": (out.get("inbox") or {}).get("last_inbound_at"),
            "thread_id": (out.get("inbox") or {}).get("thread_id"),
        }
    elif out.get("inbox"):
        out["reply_state"] = {
            **dict(out.get("reply_state") or {}),
            "thread_id": ((out.get("inbox") or {}).get("thread_id")),
            "reply_received": bool(((out.get("reply_state") or {}).get("reply_received")) or ((out.get("inbox") or {}).get("has_reply"))),
            "last_reply_at": ((out.get("reply_state") or {}).get("last_reply_at")) or ((out.get("inbox") or {}).get("last_inbound_at")),
        }
    return out


def _cl_email_subject(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> str:
    title = str(opportunity.get("title") or "your recent role posting").strip()
    company = _cl_company_name(opportunity, research)
    return f"Saw your {title} post — quick idea for {company}"


def _cl_email_body(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> str:
    trusted = dict(research or {}) if _cl_research_is_trustworthy(opportunity, research) else {}
    company = _cl_company_name(opportunity, trusted)
    title = str(opportunity.get("title") or "your recent role posting").strip()
    pain_line = _cl_pain_line(opportunity, trusted)
    first_win = _cl_first_win(opportunity, trusted)
    context_line = str(trusted.get("role_context_summary") or "").strip()

    lines = [
        f"Hi {company},",
        "",
        f"I saw your post for {title} and wanted to reach out with one practical idea.",
        pain_line,
        "",
        f"A good first place to look would be {first_win}.",
        "",
        "We usually start by identifying 1–2 tasks that can be automated without changing your whole stack.",
    ]
    if context_line:
        lines += [
            "",
            f"From the role context, it looks like this may be a live priority right now rather than a nice-to-have.",
        ]
    lines += [
        "",
        "If helpful, I can send over a few concrete workflow ideas based on the role you posted.",
        "",
        "— Chow",
    ]
    return "\n".join(lines).strip()


def _cl_call_opening(opportunity: Dict[str, Any], research: Dict[str, Any] | None = None) -> str:
    company = _cl_company_name(opportunity, research)
    title = str(opportunity.get("title") or "your recent role posting").strip()
    first_win = _cl_first_win(opportunity, research)
    return f"Hi, this is Chow — quick question for {company} about {title}. We help automate repetitive back-office tasks with AI, and one area that stood out was {first_win}."


def _cl_dispatch_queue_email(record: Dict[str, Any], payload: DispatchRequestPayload) -> Dict[str, Any]:
    validation = _dispatch_actor_validation(payload, "email")
    if not bool(validation.get("allowed")):
        raise HTTPException(status_code=403, detail={"message": "Dispatch actor not allowed", **validation})

    current_status = str(record.get("status") or "queued_review")
    if current_status in {"sent", "replied", "cancelled", "suppressed"}:
        raise HTTPException(status_code=409, detail=f"Cannot dispatch Craigslist queue record in state {current_status}")

    adapter = _dispatch_adapter_descriptor("email", payload.provider)
    if not bool(adapter.get("enabled")) or str(adapter.get("mode") or "") == "disabled":
        raise HTTPException(status_code=409, detail="email_adapter_disabled")
    if not bool(payload.promote_to_live):
        raise HTTPException(status_code=409, detail="Craigslist queue dispatch requires promote_to_live=true")
    if not bool(adapter.get("allow_live_dispatch")):
        raise HTTPException(status_code=409, detail="live_email_dispatch_disabled")

    enriched = _cl_enrich_queue_record(record)
    opportunity = dict(enriched.get("opportunity") or {})
    research = dict(enriched.get("research") or {})
    recipient_preview = dict(enriched.get("recipient_preview") or {})
    to_email = str(recipient_preview.get("selected_email") or "").strip()
    if not to_email:
        raise HTTPException(status_code=409, detail="No contact email available on this Craigslist opportunity or research packet")

    drafts = dict(enriched.get("drafts") or {})
    subject = str(drafts.get("email_subject") or _cl_email_subject(opportunity, research)).strip()
    body = str(drafts.get("email_body") or _cl_email_body(opportunity, research)).strip()
    provider_response = _send_resend_email(to_email=to_email, subject=subject, text=body)
    provider_message_id = str(provider_response.get("id") or "").strip()
    event_at = _utc_now_iso()

    updated = dict(enriched)
    dispatch_state = dict(updated.get("dispatch") or {})
    dispatch_state.update(
        {
            "status": "provider_accepted",
            "provider": adapter.get("provider"),
            "provider_mode": adapter.get("mode"),
            "provider_message_id": provider_message_id,
            "provider_response": provider_response,
            "recipient_email": to_email,
            "dispatched_at": event_at,
            "requested_by": validation.get("actor_id"),
            "requested_role": validation.get("actor_role"),
            "note": str(payload.note or "").strip() or None,
        }
    )
    event_log = list(updated.get("event_log") or [])
    event_log.append(
        {
            "event_type": "email_sent",
            "status": "sent",
            "detail": str(payload.note or "").strip() or "Craigslist outreach email sent via Chow.",
            "event_at": event_at,
            "provider_message_id": provider_message_id,
            "metadata": {
                "provider": adapter.get("provider"),
                "provider_mode": adapter.get("mode"),
                "actor_id": validation.get("actor_id"),
                "actor_role": validation.get("actor_role"),
                "recipient_email": to_email,
                "recipient_email_source": recipient_preview.get("source") or "unknown",
            },
        }
    )
    updated["status"] = "sent"
    updated["updated_at"] = event_at
    updated["sent_at"] = event_at
    updated["dispatch"] = dispatch_state
    updated["event_log"] = event_log
    updated["reply_state"] = {
        "reply_received": False,
        "last_reply_at": None,
        "thread_id": None,
    }
    thread = _record_outbound_email_thread(
        source="craigslist_dispatch_resend",
        links=_queue_email_links(updated),
        from_email=_normalize_email_address(EMAIL_REPLY_TO) or _normalize_email_address(EMAIL_FROM),
        to_emails=[to_email],
        subject=subject,
        body_text=body,
        provider_message_id=provider_message_id,
        event_at=event_at,
    )
    return _apply_inbox_summary(updated, thread)


def _cl_refresh_signals(payload: CraigslistSignalRefreshPayload) -> Dict[str, Any]:
    if not CRAIGSLIST_FETCH_SCRIPT.exists():
        raise HTTPException(status_code=404, detail=f"Missing fetch script: {CRAIGSLIST_FETCH_SCRIPT}")

    timeout_sec = max(10, min(300, int(payload.timeout_sec)))
    limit_per_query = max(1, min(100, int(payload.limit_per_query)))
    cmd = [
        "python3",
        str(CRAIGSLIST_FETCH_SCRIPT),
        "--limit-per-query",
        str(limit_per_query),
    ]
    try:
        run = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Craigslist signal refresh timed out")

    _cl_signal_payload_cache.cache_clear()
    result = _cl_read_signal_payload()
    return {
        "framework": CRAIGSLIST_SIGNAL_FRAMEWORK,
        "ok": run.returncode == 0,
        "exit_code": run.returncode,
        "limit_per_query": limit_per_query,
        "stdout_tail": "\n".join((run.stdout or "").strip().splitlines()[-20:]),
        "stderr_tail": "\n".join((run.stderr or "").strip().splitlines()[-20:]),
        "generated_at": result.get("generated_at"),
        "count": int(result.get("count") or len(result.get("opportunities") or [])),
        "query_stats": result.get("query_stats") or [],
    }


def _cl_update_queue_records_for_research(opportunity_id: str, research: Dict[str, Any] | None) -> None:
    key = str(opportunity_id or "").strip()
    if not key:
        return
    store = _cl_read_outreach_queue_store()
    changed = False
    for queue_id, record in list(store.items()):
        if not isinstance(record, dict):
            continue
        opportunity = dict(record.get("opportunity") or {})
        if str(opportunity.get("opportunity_id") or "") != key:
            continue
        updated = dict(record)
        updated["research"] = dict(research or {}) if research else None
        updated.pop("generated_drafts", None)
        store[queue_id] = _cl_enrich_queue_record(updated)
        changed = True
    if changed:
        _cl_write_outreach_queue_store(store)
        _cl_outreach_queue_cache.cache_clear()


def _cl_refresh_research(opportunity_id: str, payload: CraigslistResearchRefreshPayload) -> Dict[str, Any]:
    actor_id = str(payload.actor_id or "").strip()
    if not actor_id:
        raise HTTPException(status_code=400, detail="actor_id is required")
    opportunity = _cl_find_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail=f"Unknown Craigslist opportunity {opportunity_id}")
    if not CRAIGSLIST_ENRICH_SCRIPT.exists():
        raise HTTPException(status_code=404, detail=f"Missing enrich script: {CRAIGSLIST_ENRICH_SCRIPT}")

    timeout_sec = max(15, min(300, int(payload.timeout_sec)))
    max_fetch_pages = max(0, min(10, int(payload.max_fetch_pages)))
    limit_per_query = max(1, min(10, int(payload.limit_per_query)))
    search_provider = str(payload.search_provider or "auto").strip() or "auto"
    text_provider = str(payload.text_provider or "auto").strip() or "auto"
    cmd = [
        "python3",
        str(CRAIGSLIST_ENRICH_SCRIPT),
        "--opportunity-ids",
        str(opportunity_id),
        "--limit",
        "1",
        "--timeout",
        str(timeout_sec),
        "--max-fetch-pages",
        str(max_fetch_pages),
        "--limit-per-query",
        str(limit_per_query),
        "--search-provider",
        search_provider,
        "--text-provider",
        text_provider,
    ]
    try:
        run = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout_sec + 30)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Craigslist research refresh timed out")
    if run.returncode != 0:
        raise HTTPException(status_code=500, detail={
            "message": "Craigslist research refresh failed",
            "stdout_tail": "\n".join((run.stdout or "").strip().splitlines()[-20:]),
            "stderr_tail": "\n".join((run.stderr or "").strip().splitlines()[-20:]),
        })

    _cl_company_research_cache.cache_clear()
    research = _cl_research_record_for(opportunity_id)
    _cl_update_queue_records_for_research(opportunity_id, research)
    queue_records = [
        _cl_enrich_queue_record(item)
        for item in _cl_outreach_queue_cache().values()
        if isinstance(item, dict) and str(((item.get("opportunity") or {}).get("opportunity_id") or "")) == str(opportunity_id)
    ]
    return {
        "framework": CRAIGSLIST_SIGNAL_FRAMEWORK,
        "opportunity_id": opportunity_id,
        "actor_id": actor_id,
        "actor_role": _slug_token(payload.actor_role).replace("-", "_") or "manager",
        "search_provider": search_provider,
        "text_provider": text_provider,
        "stdout_tail": "\n".join((run.stdout or "").strip().splitlines()[-20:]),
        "stderr_tail": "\n".join((run.stderr or "").strip().splitlines()[-20:]),
        "research": research,
        "linked_queue_records": queue_records,
    }


def _cl_append_manual_opportunities(payload: CraigslistManualImportPayload) -> Dict[str, Any]:
    source = _cl_read_signal_payload()
    current = [dict(item) for item in (source.get("opportunities") or []) if isinstance(item, dict)]
    by_id: Dict[str, Dict[str, Any]] = {str(item.get("opportunity_id") or ""): item for item in current if str(item.get("opportunity_id") or "")}

    now = _utc_now_iso()
    created_ids: List[str] = []

    for raw in payload.opportunities:
        market_id = _slug_token(raw.market_id).replace("-", "_") or "manual"
        role_family = _slug_token(raw.role_family).replace("-", "_") or "backoffice_data_ops"
        title = str(raw.title or "").strip()
        if not title:
            continue

        email_hints = [str(v).strip().lower() for v in (raw.contact_hint_emails or []) if str(v).strip()]
        phone_hints = [str(v).strip() for v in (raw.contact_hint_phones or []) if str(v).strip()]
        score = max(0.0, min(0.99, float(raw.automation_score or 0.0)))
        confidence = max(0.0, min(0.99, float(raw.confidence or score)))
        opportunity_id = f"clj_manual_{_slug_token(f'{title}-{raw.company_name_guess or market_id}')[:36]}"
        if opportunity_id in by_id:
            opportunity_id = f"{opportunity_id}_{datetime.now(timezone.utc).strftime('%H%M%S')}"

        row = {
            "opportunity_id": opportunity_id,
            "source": "manual_seed",
            "market_id": market_id,
            "market_label": market_id.replace("_", " ").title(),
            "query": _slug_token(raw.query).replace("-", "_") or "manual",
            "posting_id": opportunity_id,
            "title": title,
            "company_name_guess": str(raw.company_name_guess or "unknown").strip() or "unknown",
            "role_family": role_family,
            "automation_score": round(score, 3),
            "confidence": round(confidence, 3),
            "matched_keywords": [],
            "automation_hypotheses": [str(v).strip() for v in (raw.automation_hypotheses or []) if str(v).strip()],
            "recommended_channel": _slug_token(raw.recommended_channel).replace("-", "_") or "manual_research",
            "outreach_angle": str(raw.outreach_angle or "").strip() or "Offer a fast AI ops audit for repetitive workflow steps.",
            "contact_hint_emails": email_hints,
            "contact_hint_phones": phone_hints,
            "posting_url": str(raw.posting_url or "").strip() or None,
            "posting_description": str(raw.posting_description or "").strip()[:1200] or None,
            "posted_at": str(raw.posted_at or "").strip() or None,
            "fetched_at": now,
            "status": "new",
            "matched_queries": ["manual"],
            "seeded_by": str(payload.actor_id or "").strip(),
        }
        by_id[opportunity_id] = row
        created_ids.append(opportunity_id)

    merged = sorted(
        by_id.values(),
        key=lambda item: (float(item.get("automation_score") or 0.0), str(item.get("posted_at") or "")),
        reverse=True,
    )

    updated = {
        "generated_at": now,
        "config_version": str(source.get("config_version") or "manual"),
        "source_policy": source.get("source_policy") or {"mode": "mixed"},
        "count": len(merged),
        "opportunities": merged,
        "query_stats": source.get("query_stats") or [],
    }
    CRAIGSLIST_SIGNAL_JSON.parent.mkdir(parents=True, exist_ok=True)
    CRAIGSLIST_SIGNAL_JSON.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
    _cl_signal_payload_cache.cache_clear()

    return {
        "framework": CRAIGSLIST_SIGNAL_FRAMEWORK,
        "created": len(created_ids),
        "created_ids": created_ids,
        "count": len(merged),
        "generated_at": now,
    }


@app.post("/api/v1/signals/jobs/craigslist/refresh")
def craigslist_signal_refresh(payload: CraigslistSignalRefreshPayload) -> Dict[str, Any]:
    return _cl_refresh_signals(payload)


@app.get("/api/v1/signals/jobs/craigslist")
def craigslist_signal_list(
    min_score: float = 0.55,
    limit: int = 50,
    market_id: str | None = None,
    channel: str | None = None,
) -> Dict[str, Any]:
    payload = _cl_signal_payload_cache()
    opportunities = _cl_opportunities()

    min_score = max(0.0, min(1.0, float(min_score)))
    limit = max(1, min(500, int(limit)))
    market_filter = _slug_token(market_id).replace("-", "_") if market_id else ""
    channel_filter = _slug_token(channel).replace("-", "_") if channel else ""

    filtered = []
    for item in opportunities:
        score = float(item.get("automation_score") or 0.0)
        if score < min_score:
            continue
        if market_filter and _slug_token(item.get("market_id") or "").replace("-", "_") != market_filter:
            continue
        if channel_filter and _slug_token(item.get("recommended_channel") or "").replace("-", "_") != channel_filter:
            continue
        filtered.append(item)

    blocked_stats = [
        stat
        for stat in (payload.get("query_stats") or [])
        if isinstance(stat, dict) and str(stat.get("error") or "").strip()
    ]

    return {
        "framework": CRAIGSLIST_SIGNAL_FRAMEWORK,
        "generated_at": payload.get("generated_at"),
        "source_policy": payload.get("source_policy") or {},
        "config_version": payload.get("config_version"),
        "filters": {
            "min_score": min_score,
            "market_id": market_filter or None,
            "channel": channel_filter or None,
            "limit": limit,
        },
        "count": len(filtered),
        "total": len(opportunities),
        "items": filtered[:limit],
        "query_stats": payload.get("query_stats") or [],
        "ingest_warnings": blocked_stats,
    }


@app.get("/api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}")
def craigslist_signal_get(opportunity_id: str) -> Dict[str, Any]:
    item = _cl_find_opportunity(opportunity_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Unknown Craigslist opportunity {opportunity_id}")
    return {
        "framework": CRAIGSLIST_SIGNAL_FRAMEWORK,
        "item": item,
        "research": _cl_research_record_for(opportunity_id),
    }


@app.post("/api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}/research-refresh")
def craigslist_signal_research_refresh(opportunity_id: str, payload: CraigslistResearchRefreshPayload) -> Dict[str, Any]:
    return _cl_refresh_research(opportunity_id, payload)


@app.post("/api/v1/signals/jobs/craigslist/import")
def craigslist_signal_import(payload: CraigslistManualImportPayload) -> Dict[str, Any]:
    actor = str(payload.actor_id or "").strip()
    if not actor:
        raise HTTPException(status_code=400, detail="actor_id is required")
    if not payload.opportunities:
        raise HTTPException(status_code=400, detail="opportunities is required")
    return _cl_append_manual_opportunities(payload)


@app.get("/api/v1/signals/jobs/craigslist/outreach-queue")
def craigslist_outreach_queue_list(status: str | None = None, limit: int = 100) -> Dict[str, Any]:
    rows = [_cl_enrich_queue_record(item) for item in _cl_outreach_queue_cache().values()]
    rows.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    normalized_status = _slug_token(status).replace("-", "_") if status else ""
    if normalized_status:
        rows = [row for row in rows if _slug_token(row.get("status") or "").replace("-", "_") == normalized_status]
    limit = max(1, min(500, int(limit)))
    return {
        "framework": CRAIGSLIST_OUTREACH_FRAMEWORK,
        "count": len(rows),
        "items": rows[:limit],
    }


@app.get("/api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}")
def craigslist_outreach_queue_get(queue_id: str) -> Dict[str, Any]:
    record = _cl_queue_record_for(queue_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Unknown Craigslist outreach queue record {queue_id}")
    enriched = _cl_enrich_queue_record(record)
    return {
        "framework": CRAIGSLIST_OUTREACH_FRAMEWORK,
        "record": enriched,
        "thread": _refresh_email_thread(_email_thread_for_link("craigslist_outreach_queue", queue_id) or {}) if _email_thread_for_link("craigslist_outreach_queue", queue_id) else None,
        "mailbox": _imap_provider_descriptor(),
    }


@app.put("/api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}/review")
def craigslist_outreach_queue_review(queue_id: str, payload: CraigslistOutreachQueueReviewPayload) -> Dict[str, Any]:
    record = _cl_queue_record_for(queue_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Unknown Craigslist outreach queue record {queue_id}")

    actor_id = str(payload.actor_id or "").strip()
    if not actor_id:
        raise HTTPException(status_code=400, detail="actor_id is required")

    updated = _cl_enrich_queue_record(record)
    drafts = dict(updated.get("drafts") or {})
    review = dict(updated.get("review") or {})
    changed_fields: List[str] = []

    if payload.email_subject is not None:
        drafts["email_subject"] = str(payload.email_subject or "").strip()
        changed_fields.append("email_subject")
    if payload.email_body is not None:
        drafts["email_body"] = str(payload.email_body or "").strip()
        changed_fields.append("email_body")
    if payload.call_opening is not None:
        drafts["call_opening"] = str(payload.call_opening or "").strip()
        changed_fields.append("call_opening")
    if payload.recipient_email is not None:
        review["recipient_email"] = str(payload.recipient_email or "").strip() or None
        changed_fields.append("recipient_email")
    if payload.research_quality is not None:
        review["research_quality"] = _slug_token(payload.research_quality).replace("-", "_") or None
        changed_fields.append("research_quality")
    if payload.company_match is not None:
        review["company_match"] = _slug_token(payload.company_match).replace("-", "_") or None
        changed_fields.append("company_match")
    if payload.contact_path_status is not None:
        review["contact_path_status"] = _slug_token(payload.contact_path_status).replace("-", "_") or None
        changed_fields.append("contact_path_status")
    if payload.draft_status is not None:
        review["draft_status"] = _slug_token(payload.draft_status).replace("-", "_") or None
        changed_fields.append("draft_status")

    review["reviewed_by"] = actor_id
    review["reviewed_role"] = _slug_token(payload.actor_role).replace("-", "_") or "manager"
    review["reviewed_at"] = _utc_now_iso()
    updated["drafts"] = drafts
    updated["review"] = review
    updated["updated_at"] = review["reviewed_at"]
    updated["event_log"] = list(updated.get("event_log") or [])
    updated["event_log"].append(
        {
            "event_type": "review_updated",
            "status": str(updated.get("status") or "queued_review"),
            "detail": str(payload.note or "").strip() or "Craigslist queue review updated from dashboard.",
            "event_at": review["reviewed_at"],
            "metadata": {
                "actor_id": actor_id,
                "actor_role": review["reviewed_role"],
                "changed_fields": changed_fields,
            },
        }
    )
    feedback_entry = _cl_upsert_research_feedback(updated)
    if feedback_entry:
        updated["research_feedback"] = feedback_entry if bool(feedback_entry.get("active")) else None
    persisted = _persist_cl_queue_record(_cl_enrich_queue_record(updated))
    return {
        "framework": CRAIGSLIST_OUTREACH_FRAMEWORK,
        "record": _cl_enrich_queue_record(persisted),
    }


@app.post("/api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}/dispatch")
def craigslist_outreach_queue_dispatch(queue_id: str, payload: DispatchRequestPayload) -> Dict[str, Any]:
    record = _cl_queue_record_for(queue_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Unknown Craigslist outreach queue record {queue_id}")
    updated = _cl_dispatch_queue_email(record, payload)
    persisted = _persist_cl_queue_record(_cl_enrich_queue_record(updated))
    return {
        "framework": CRAIGSLIST_OUTREACH_FRAMEWORK,
        "record": _cl_enrich_queue_record(persisted),
    }


@app.post("/api/v1/signals/jobs/craigslist/opportunity/{opportunity_id}/queue-outreach")
def craigslist_outreach_queue_create(opportunity_id: str, payload: CraigslistOutreachQueuePayload) -> Dict[str, Any]:
    actor_id = str(payload.actor_id or "").strip()
    if not actor_id:
        raise HTTPException(status_code=400, detail="actor_id is required")

    opportunity = _cl_find_opportunity(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail=f"Unknown Craigslist opportunity {opportunity_id}")

    score = float(opportunity.get("automation_score") or 0.0)
    if score < 0.55 and not bool(payload.force):
        raise HTTPException(status_code=409, detail={"message": "Opportunity score below outreach threshold", "automation_score": score})

    queue_store = _cl_read_outreach_queue_store()
    now = _utc_now_iso()
    normalized_channel = _slug_token(payload.channel or opportunity.get("recommended_channel") or "manual_research").replace("-", "_")
    if not normalized_channel:
        normalized_channel = "manual_research"

    queue_id = f"clq_{_slug_token(opportunity_id)}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    research = _cl_research_record_for(str(opportunity.get("opportunity_id") or opportunity_id))
    research_trustworthy = _cl_research_is_trustworthy(opportunity, research)
    record = {
        "queue_id": queue_id,
        "framework": CRAIGSLIST_OUTREACH_FRAMEWORK,
        "status": "queued_review",
        "requires_compliance_review": True,
        "source": "craigslist_job_signal",
        "opportunity_id": str(opportunity.get("opportunity_id") or opportunity_id),
        "actor_id": actor_id,
        "actor_role": _slug_token(payload.actor_role).replace("-", "_") or "manager",
        "channel": normalized_channel,
        "note": str(payload.note or "").strip() or None,
        "created_at": now,
        "updated_at": now,
        "opportunity": opportunity,
        "research": research,
        "research_trustworthy": research_trustworthy,
        "review": {
            "research_quality": None,
            "company_match": None,
            "contact_path_status": None,
            "draft_status": "needs_review",
            "recipient_email": None,
        },
        "generated_drafts": {
            "email_subject": _cl_email_subject(opportunity, research),
            "email_body": _cl_email_body(opportunity, research),
            "call_opening": _cl_call_opening(opportunity, research),
        },
        "drafts": {
            "email_subject": _cl_email_subject(opportunity, research),
            "email_body": _cl_email_body(opportunity, research),
            "call_opening": _cl_call_opening(opportunity, research),
        },
        "policy": {
            "automation_score": score,
            "threshold": 0.55,
            "forced": bool(payload.force),
            "source_policy": (_cl_signal_payload_cache().get("source_policy") or {}),
        },
        "reply_state": {
            "reply_received": False,
            "last_reply_at": None,
            "thread_id": None,
        },
        "event_log": [
            {
                "event_type": "queued_review",
                "status": "queued_review",
                "detail": "Craigslist opportunity queued for supervised outreach review.",
                "event_at": now,
                "metadata": {
                    "actor_id": actor_id,
                    "actor_role": _slug_token(payload.actor_role).replace("-", "_") or "manager",
                    "channel": normalized_channel,
                    "contact_hint_emails": [str(v).strip() for v in (opportunity.get("contact_hint_emails") or []) if str(v).strip()],
                    "research_emails": [str(v).strip() for v in ((research or {}).get("emails") or []) if str(v).strip()],
                    "research_confidence": (research or {}).get("research_confidence"),
                    "research_trustworthy": research_trustworthy,
                },
            }
        ],
        "refs": {
            "dispatch_ref": f"/api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}/dispatch",
            "record_ref": f"/api/v1/signals/jobs/craigslist/outreach-queue/{queue_id}",
        },
    }
    enriched_record = _cl_enrich_queue_record(record)
    queue_store[queue_id] = enriched_record
    _cl_write_outreach_queue_store(queue_store)
    _cl_outreach_queue_cache.cache_clear()

    return {
        "queued": True,
        "record": enriched_record,
        "queue_size": len(queue_store),
    }
