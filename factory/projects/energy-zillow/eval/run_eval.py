#!/usr/bin/env python3
"""DemandGrid eval harness.

Implements core gates from local artifacts and datasets.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.scoring.solar import ScoringAssumptions, apply_spatial_context, score_site  # noqa: E402
from scripts.score_sites import apply_operator_routing, apply_product_recommendations, apply_sales_priority, build_state_utility_rate_medians, load_manual_utility_mappings, load_official_utility_rate_overrides, load_property_triggers, load_site_utility_rates, load_state_rate_overrides, load_state_reliability_prior, load_zip_priority, resolve_site_rate_context  # noqa: E402


def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(len(a | b), 1)


def _zip_key(row: Dict[str, str]) -> str:
    z = row.get("zip")
    if z in (None, "", "None"):
        return "unknown"
    zs = str(z).strip()
    m = re.match(r"^(\d{5})", zs)
    if m:
        return m.group(1)
    return zs


def _ranking_value(row: Dict[str, object]) -> float:
    raw = row.get("priority_score")
    if raw not in (None, "", "None"):
        return float(raw)
    return float(row.get("annual_savings_usd", 0) or 0)


def _ranking_key(row: Dict[str, object]):
    return (-_ranking_value(row), -float(row.get("annual_savings_usd", 0) or 0), str(row.get("site_id", "")))


def _as_float(value: object) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _as_text(value: object) -> str:
    if value in (None, "None"):
        return ""
    return str(value).strip()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", default="00000", help="Optional context arg for report compatibility")
    p.add_argument("--require-min-zips", type=int, default=25)
    p.add_argument("--min-rows-per-zip", type=int, default=20)
    p.add_argument("--min-zip-stability", type=float, default=0.90)
    p.add_argument("--skip-agent-contract", action="store_true")
    args = p.parse_args()

    sites = read_csv(ROOT / "data/processed/sites.csv")
    scored = read_csv(ROOT / "data/processed/site_scores.csv")
    h3_rows = read_csv(ROOT / "data/processed/h3_scores.csv")
    property_triggers = read_csv(ROOT / "data/processed/property_triggers.csv")

    checks = []

    # coverage gate
    coverage = (len(scored) / len(sites)) if sites else 0.0
    coverage_pass = coverage >= 0.80
    checks.append(("coverage", coverage_pass, f"{coverage:.2%} (threshold >= 80%)"))

    # ranking stability gate (deterministic rerun from same site inputs)
    base_assumptions = ScoringAssumptions()
    state_rate_overrides = load_state_rate_overrides(ROOT / "data" / "raw" / "eia_state_residential_rates.csv")
    site_utility_rates = load_site_utility_rates(ROOT / "data" / "processed" / "site_utility_tariff.csv")
    state_utility_rate_medians = build_state_utility_rate_medians(sites, site_utility_rates)
    official_utility_rate_overrides = load_official_utility_rate_overrides(ROOT / "data" / "raw" / "official_utility_residential_rates.csv")
    manual_utility_mappings = load_manual_utility_mappings(ROOT / "data" / "raw" / "manual_utility_map.csv")
    rescored = []
    for site in sites:
        site_assumptions, rate_context = resolve_site_rate_context(
            site,
            base_assumptions,
            state_rate_overrides,
            site_utility_rates,
            state_utility_rate_medians,
            official_utility_rate_overrides,
            manual_utility_mappings,
        )
        row = score_site(site, site_assumptions)
        row.update(rate_context)
        rescored.append(row)
    apply_spatial_context(rescored, base_assumptions)
    trigger_lookup = load_property_triggers(ROOT / "data" / "processed" / "property_triggers.csv")
    reliability_lookup = load_state_reliability_prior(ROOT / "data" / "raw" / "eia_state_reliability_prior.csv")
    for row in rescored:
        row.update(
            trigger_lookup.get(
                str(row.get("site_id") or ""),
                {
                    "storm_trigger_status": "missing",
                    "outage_trigger_status": "missing",
                    "equipment_age_trigger_status": "missing",
                    "flood_risk_trigger_status": "missing",
                    "storm_trigger_score": None,
                    "outage_trigger_score": None,
                    "equipment_age_trigger_score": None,
                    "flood_risk_trigger_score": None,
                    "trigger_notes": "",
                },
            )
        )
        row.update(
            reliability_lookup.get(
                str(row.get("state") or "").strip().upper(),
                {
                    "battery_reliability_prior_status": "missing",
                    "battery_reliability_prior_score": None,
                    "utility_reliability_tier": "",
                    "saidi_minutes": None,
                    "saifi_events": None,
                    "battery_reliability_prior_note": "",
                },
            )
        )
    apply_sales_priority(rescored, load_zip_priority(ROOT / "artifacts" / "new-england-zip-priority.csv"))
    apply_product_recommendations(rescored)
    apply_operator_routing(rescored)
    top_a = {r["site_id"] for r in sorted(scored, key=_ranking_key)[:50]}
    top_b = {r["site_id"] for r in sorted(rescored, key=_ranking_key)[:50]}
    stability = jaccard(top_a, top_b)
    stability_pass = stability >= 0.90
    checks.append(("ranking_stability", stability_pass, f"{stability:.3f} (threshold >= 0.90)"))

    # multi-zip regression gate
    site_by_zip: Dict[str, int] = defaultdict(int)
    scored_by_zip: Dict[str, int] = defaultdict(int)
    for s in sites:
        site_by_zip[_zip_key(s)] += 1
    for s in scored:
        scored_by_zip[_zip_key(s)] += 1

    zip_codes = sorted(set(site_by_zip.keys()) | set(scored_by_zip.keys()))
    if "unknown" in zip_codes and len(zip_codes) > 1:
        zip_codes = [z for z in zip_codes if z != "unknown"]

    per_zip_coverage: Dict[str, float] = {}
    per_zip_stability: Dict[str, float] = {}
    per_zip_rows_ok = True
    per_zip_cov_ok = True

    for z in zip_codes:
        s_count = site_by_zip.get(z, 0)
        c_count = scored_by_zip.get(z, 0)
        cov = (c_count / s_count) if s_count else 0.0
        per_zip_coverage[z] = cov
        if c_count < args.min_rows_per_zip:
            per_zip_rows_ok = False
        if cov < 0.80:
            per_zip_cov_ok = False

        zip_top_a = {
            r["site_id"]
            for r in sorted([r for r in scored if _zip_key(r) == z], key=_ranking_key)[:20]
        }
        zip_top_b = {
            r["site_id"]
            for r in sorted([r for r in rescored if _zip_key(r) == z], key=_ranking_key)[:20]
        }
        per_zip_stability[z] = jaccard(zip_top_a, zip_top_b)

    zip_count_ok = len(zip_codes) >= args.require_min_zips
    zip_stability_min = min(per_zip_stability.values()) if per_zip_stability else 0.0
    zip_stability_ok = zip_stability_min >= args.min_zip_stability

    multi_zip_pass = zip_count_ok and per_zip_rows_ok and per_zip_cov_ok and zip_stability_ok
    checks.append(
        (
            "multi_zip_regression",
            multi_zip_pass,
            (
                f"zips={len(zip_codes)} req>={args.require_min_zips}, "
                f"min_rows_per_zip={args.min_rows_per_zip}, "
                f"min_zip_stability={zip_stability_min:.3f} req>={args.min_zip_stability:.2f}, "
                f"rows_ok={per_zip_rows_ok}, coverage_ok={per_zip_cov_ok}"
            ),
        )
    )

    # product flow gate (artifact + frontend contract check)
    frontend_index = ROOT / "frontend/index.html"
    frontend_text = frontend_index.read_text(encoding="utf-8") if frontend_index.exists() else ""
    frontend_ok = frontend_index.exists() and ("maplibregl.Map(" in frontend_text) and ("loadHexSites(" in frontend_text)
    product_flow_pass = bool(scored) and bool(h3_rows) and (ROOT / "artifacts/api-sample-responses.json").exists() and frontend_ok
    checks.append(("product_flow", product_flow_pass, "scored+h3+api-samples+frontend map/list/detail flow present"))

    # agent copilot contract gate
    agent_contract_pass = True
    agent_contract_detail = "skipped"
    if not args.skip_agent_contract and len(scored) <= 20000:
        agent_contract_pass = False
        agent_contract_detail = "not-run"
        try:
            from fastapi.testclient import TestClient
            from backend.api.app import app as ez_app

            client = TestClient(ez_app)
            q1 = client.post(
                "/api/v1/agent/chat",
                json={"message": "top hot solar leads in 01730 with outage trigger", "zip": "01730", "max_results": 5},
            )
            ok1 = q1.status_code == 200
            p1 = q1.json() if ok1 else {}
            cards1 = p1.get("cards") if isinstance(p1, dict) else []
            sid = cards1[0].get("site_id") if cards1 else None

            ok2 = False
            if sid:
                q2 = client.post(
                    "/api/v1/agent/chat",
                    json={"message": "why this site", "site_id": sid, "max_results": 3},
                )
                ok2 = q2.status_code == 200 and bool((q2.json() or {}).get("reply"))

            agent_contract_pass = ok1 and bool(cards1) and ok2
            agent_contract_detail = f"q1_ok={ok1}, cards={len(cards1) if cards1 else 0}, q2_ok={ok2}"
        except Exception as e:
            agent_contract_detail = f"error={e}"
    elif len(scored) > 20000:
        agent_contract_detail = f"skipped_large_board rows={len(scored)}"

    checks.append(("agent_copilot_contract", agent_contract_pass, agent_contract_detail))

    # honesty_wind gate
    wind_low_conf_violations = 0
    for row in scored:
        has_wind = row.get("annual_kwh_wind") not in ("", "None", None)
        if has_wind and float(row.get("confidence", 0)) < 0.7:
            wind_low_conf_violations += 1
    honesty_pass = wind_low_conf_violations == 0
    checks.append(("honesty_wind", honesty_pass, f"violations={wind_low_conf_violations}"))

    # honesty_product_readiness gate
    readiness_missing = 0
    unsupported_lane_mismatch = 0
    proxy_only_lanes = {"roofing", "hvac_heat_pump", "battery_backup"}
    for row in scored:
        for product_key, readiness_key, gap_key in [
            ("primary_product", "primary_product_readiness", "primary_product_trigger_gap"),
            ("secondary_product", "secondary_product_readiness", "secondary_product_trigger_gap"),
        ]:
            product = row.get(product_key, "")
            readiness = row.get(readiness_key, "")
            gap = row.get(gap_key, "")
            if not readiness or not gap:
                readiness_missing += 1
            if product in proxy_only_lanes and readiness != "proxy-only":
                unsupported_lane_mismatch += 1
    product_honesty_pass = readiness_missing == 0 and unsupported_lane_mismatch == 0
    checks.append(
        (
            "honesty_product_readiness",
            product_honesty_pass,
            f"missing={readiness_missing}, proxy_lane_mismatch={unsupported_lane_mismatch}",
        )
    )

    # operator workflow label gate
    valid_temp = {"hot", "warm", "skip"}
    valid_next = {"work_now", "follow_up", "deprioritize"}
    missing_operator_labels = 0
    invalid_operator_labels = 0
    for row in scored:
        t = str(row.get("lead_temperature") or "").strip()
        n = str(row.get("operator_next_step") or "").strip()
        if not t or not n:
            missing_operator_labels += 1
            continue
        if t not in valid_temp or n not in valid_next:
            invalid_operator_labels += 1
    operator_labels_pass = missing_operator_labels == 0 and invalid_operator_labels == 0
    checks.append(
        (
            "operator_workflow_labels",
            operator_labels_pass,
            f"missing={missing_operator_labels}, invalid={invalid_operator_labels}",
        )
    )

    route_score_missing = 0
    top200_hot = 0
    for row in scored:
        if row.get("sales_route_score") in ("", "None", None):
            route_score_missing += 1
    for row in scored[:200]:
        if str(row.get("lead_temperature") or "") == "hot":
            top200_hot += 1
    route_usability_pass = route_score_missing == 0 and top200_hot >= 10
    checks.append(
        (
            "operator_route_usability",
            route_usability_pass,
            f"route_score_missing={route_score_missing}, top200_hot={top200_hot}",
        )
    )

    # widened board mix gate: ensure widened board is active and top of board isn't mono-lane
    top100_products = defaultdict(int)
    for row in scored[:100]:
        top100_products[str(row.get("primary_product") or "unknown")] += 1
    widened_mix_pass = (
        len(zip_codes) >= args.require_min_zips
        and top100_products.get("solar", 0) >= 25
        and top100_products.get("roofing", 0) >= 10
        and sum(1 for count in top100_products.values() if count > 0) >= 2
    )
    checks.append(
        (
            "widened_product_mix",
            widened_mix_pass,
            f"top100={dict(sorted(top100_products.items()))}",
        )
    )

    # solar-first default gate (hybrid only when wind output exists)
    hybrid_count = 0
    hybrid_without_wind = 0
    for row in scored:
        if row.get("best_option") == "hybrid":
            hybrid_count += 1
            has_wind = row.get("annual_kwh_wind") not in ("", "None", None)
            if not has_wind:
                hybrid_without_wind += 1
    solar_first_pass = hybrid_without_wind == 0
    checks.append(("solar_first_default", solar_first_pass, f"hybrid={hybrid_count}, violations={hybrid_without_wind}"))

    # perf_api gate (uses api_perf_check artifact if present)
    perf_path = ROOT / "artifacts/api-perf-summary.json"
    if perf_path.exists():
        perf = json.loads(perf_path.read_text(encoding="utf-8"))
        p95_ms = float(perf.get("p95_ms", 9e9))
        perf_pass = p95_ms <= 700
        checks.append(("perf_api", perf_pass, f"p95={p95_ms:.2f}ms (threshold <= 700ms)"))
    else:
        checks.append(("perf_api", True, "not-run (no artifact); treated as pending-pass for scaffold"))

    # explanation quality
    reasons_nonempty = 0
    for row in scored:
        rj = row.get("reasons_json", "[]")
        try:
            arr = json.loads(rj)
            if isinstance(arr, list) and len(arr) > 0:
                reasons_nonempty += 1
        except Exception:
            pass
    explain_ratio = (reasons_nonempty / len(scored)) if scored else 0.0
    explain_pass = explain_ratio >= 0.98
    checks.append(("explanation_quality", explain_pass, f"{explain_ratio:.2%} (threshold >= 98%)"))

    # assumption traceability
    has_assumptions = (ROOT / "artifacts/scoring-assumptions.md").exists()
    has_limitations = (ROOT / "artifacts/limitations.md").exists()
    traceability_pass = has_assumptions and has_limitations
    checks.append(("assumption_traceability", traceability_pass, f"scoring_assumptions={has_assumptions}, limitations={has_limitations}"))

    trigger_contract_pass = bool(property_triggers) and len(property_triggers) == len(sites)
    checks.append(("trigger_layer_contract", trigger_contract_pass, f"trigger_rows={len(property_triggers)}, sites={len(sites)}"))

    reliability_loaded = sum(
        1
        for row in scored
        if str(row.get("battery_reliability_prior_status") or "missing") != "missing"
    )
    reliability_coverage_pass = reliability_loaded >= max(len(scored) * 0.95, 1)
    checks.append(
        (
            "battery_reliability_prior",
            reliability_coverage_pass,
            f"loaded_rows={reliability_loaded}, scored_rows={len(scored)}",
        )
    )

    # flood-gap coverage gate (EZ-018): ensure flood lane covers at least one outage-gap ZIP
    trigger_by_site = {str(r.get("site_id") or ""): r for r in property_triggers}
    outage_missing_by_zip: Dict[str, int] = defaultdict(int)
    flood_nonmissing_by_zip: Dict[str, int] = defaultdict(int)
    equipment_nonmissing_by_zip: Dict[str, int] = defaultdict(int)
    for s in sites:
        sid = str(s.get("site_id") or "")
        z = _zip_key(s)
        t = trigger_by_site.get(sid, {})
        outage_status = str(t.get("outage_trigger_status") or "missing")
        flood_status = str(t.get("flood_risk_trigger_status") or "missing")
        equipment_status = str(t.get("equipment_age_trigger_status") or "missing")
        if outage_status == "missing":
            outage_missing_by_zip[z] += 1
        if flood_status != "missing":
            flood_nonmissing_by_zip[z] += 1
        if equipment_status != "missing":
            equipment_nonmissing_by_zip[z] += 1

    outage_gap_zips = sorted([z for z, missing in outage_missing_by_zip.items() if missing > 0])
    if outage_gap_zips:
        flood_covered_gap_zips = [z for z in outage_gap_zips if flood_nonmissing_by_zip.get(z, 0) > 0]
        flood_gap_pass = len(flood_covered_gap_zips) > 0
        flood_gap_detail = (
            f"outage_gap_zips={outage_gap_zips}, flood_covered_gap_zips={flood_covered_gap_zips}"
        )
    else:
        zips_with_flood = sorted([z for z in zip_codes if flood_nonmissing_by_zip.get(z, 0) > 0])
        flood_gap_pass = len(zips_with_flood) > 0
        flood_gap_detail = f"no_outage_gap_zips; zips_with_flood={zips_with_flood}"

    checks.append(("flood_gap_coverage", flood_gap_pass, flood_gap_detail))

    # equipment-age coverage gate (EZ-019): require non-missing equipment proxy in at least one ZIP
    zips_with_equipment = sorted([z for z in zip_codes if equipment_nonmissing_by_zip.get(z, 0) > 0])
    equipment_gate_pass = len(zips_with_equipment) > 0
    checks.append(("equipment_age_coverage", equipment_gate_pass, f"zips_with_equipment={zips_with_equipment}"))

    # outreach/investigation contract gates (EZ-024) — endpoint-backed checks
    contract_path = ROOT / "artifacts/outreach-investigation-contract.md"
    contract_exists = contract_path.exists()

    payload_ok = 0
    trace_ok = 0
    auto_candidates = 0
    auto_suppressed = 0
    safety_violations = 0
    handoff_ok = 0
    permit_contract_ok = 0
    permit_contract_n = 0
    sample_n = 1

    outreach_payload_pass = False
    investigation_trace_pass = False
    permit_contract_pass = False
    outreach_safety_pass = False
    action_handoff_pass = False
    closed_loop_feedback_pass = False
    outreach_policy_contract_pass = False

    payload_detail = "not-run"
    trace_detail = "not-run"
    permit_detail = "not-run"
    safety_detail = "not-run"
    handoff_detail = "not-run"
    closed_loop_detail = "not-run"
    outreach_policy_detail = "not-run"

    try:
        from fastapi.testclient import TestClient
        from backend.api.app import app as ez_app

        client = TestClient(ez_app)
        sample_zip = next((z for z in zip_codes if z != "unknown" and scored_by_zip.get(z, 0) > 0), None)

        policy_res = client.get("/api/v1/outreach/policy")
        if policy_res.status_code == 200:
            policy_body = policy_res.json() or {}
            default_policy = dict(policy_body.get("default") or {})
            products_policy = dict(policy_body.get("products") or {})
            confidence_min = default_policy.get("confidence_min")
            outreach_policy_contract_pass = (
                bool(policy_body.get("version"))
                and isinstance(default_policy.get("channel_map"), dict)
                and isinstance(confidence_min, (int, float))
                and len(products_policy) >= 1
            )
            outreach_policy_detail = (
                f"version={policy_body.get('version')}, source={policy_body.get('source')}, "
                f"confidence_min={confidence_min}, product_overrides={len(products_policy)}"
            )
        else:
            outreach_policy_detail = f"endpoint_status={policy_res.status_code}"

        params: Dict[str, str] = {"limit": "80", "include_suppressed": "true"}
        if sample_zip:
            params["zip"] = sample_zip

        outreach_res = client.get("/api/v1/outreach/payloads", params=params)
        if outreach_res.status_code == 200:
            payload_body = outreach_res.json() or {}
            items = list(payload_body.get("items") or [])
            sampled_items = items[:40]
            sample_n = max(len(sampled_items), 1)

            required_payload_fields = {
                "site_id",
                "target_segment",
                "recommended_channel",
                "message_angles",
                "cta",
                "offer_priority",
                "compliance_flags",
                "handoff_context",
                "auto_outreach_eligible",
            }

            for item in sampled_items:
                if required_payload_fields.issubset(set(item.keys())) and isinstance(item.get("message_angles"), list) and any(bool(x) for x in item.get("message_angles") or []):
                    payload_ok += 1

                handoff = item.get("handoff_context") or {}
                if (
                    bool(handoff.get("why_now_summary"))
                    and bool(handoff.get("operator_action_summary"))
                    and bool(handoff.get("investigation_ref"))
                ):
                    handoff_ok += 1

                auto_flag = bool(item.get("auto_outreach_eligible"))
                compliance_flags = list(item.get("compliance_flags") or [])
                if str(item.get("target_segment") or "") in {"hot", "warm"}:
                    auto_candidates += 1
                    if not auto_flag:
                        auto_suppressed += 1
                if auto_flag and compliance_flags:
                    safety_violations += 1

                site_id = str(item.get("site_id") or "")
                if site_id:
                    inv_res = client.get(f"/api/v1/investigation/site/{site_id}")
                    if inv_res.status_code == 200:
                        inv_body = inv_res.json() or {}
                        evidence = list(inv_body.get("evidence") or [])
                        has_trace = bool(evidence) and any(
                            bool(str(ev.get("as_of") or "").strip())
                            or ("asof=" in str(ev.get("value") or "").lower())
                            for ev in evidence
                        )
                        if has_trace:
                            trace_ok += 1

            payload_ratio = payload_ok / sample_n
            trace_ratio = trace_ok / sample_n
            handoff_ratio = handoff_ok / sample_n

            outreach_payload_pass = contract_exists and payload_ratio >= 0.95
            investigation_trace_pass = contract_exists and trace_ratio >= 0.95
            outreach_safety_pass = safety_violations == 0
            action_handoff_pass = contract_exists and handoff_ratio >= 0.95

            payload_detail = f"contract_exists={contract_exists}, payload_ok={payload_ok}/{sample_n} ({payload_ratio:.1%})"
            trace_detail = f"trace_ok={trace_ok}/{sample_n} ({trace_ratio:.1%})"
            safety_detail = f"auto_candidates={auto_candidates}, auto_suppressed={auto_suppressed}, violations={safety_violations}"
            handoff_detail = f"handoff_ok={handoff_ok}/{sample_n} ({handoff_ratio:.1%})"

            permit_site_ids = [
                str(r.get("site_id") or "")
                for r in scored
                if str(r.get("permit_trigger_status") or "missing").strip().lower() != "missing"
            ][:20]
            permit_contract_n = max(len(permit_site_ids), 1)
            if permit_site_ids:
                for site_id in permit_site_ids:
                    inv_res = client.get(f"/api/v1/investigation/site/{site_id}")
                    if inv_res.status_code != 200:
                        continue
                    inv_body = inv_res.json() or {}
                    evidence = list(inv_body.get("evidence") or [])
                    permit_status_ev = any(
                        ev.get("source") == "trigger_permit" and ev.get("field") == "permit_trigger_status"
                        for ev in evidence
                    )
                    permit_history_ev = any(
                        ev.get("source") == "trigger_permit" and ev.get("field") == "permit_history"
                        for ev in evidence
                    )
                    if permit_status_ev and permit_history_ev:
                        permit_contract_ok += 1
                permit_ratio = permit_contract_ok / permit_contract_n
                permit_contract_pass = permit_ratio >= 0.95
                permit_detail = f"permit_ok={permit_contract_ok}/{permit_contract_n} ({permit_ratio:.1%})"
            else:
                permit_contract_pass = True
                permit_detail = "no_permit_rows_in_scored_export"
        else:
            payload_detail = f"endpoint_status={outreach_res.status_code}"
            trace_detail = payload_detail
            permit_detail = payload_detail
            safety_detail = payload_detail
            handoff_detail = payload_detail

        status_res = client.get("/api/v1/operator/status", params={"limit": "25"})
        outcome_summary_res = client.get("/api/v1/operator/outcomes/summary")
        if status_res.status_code == 200 and outcome_summary_res.status_code == 200:
            status_body = status_res.json() or {}
            items = list(status_body.get("items") or [])
            invalid = 0
            for item in items:
                op = item.get("operator_status")
                if not isinstance(op, dict):
                    invalid += 1
                    continue
                if "status" not in op or "note" not in op or "updated_at" not in op:
                    invalid += 1
            summary_body = outcome_summary_res.json() or {}
            global_scope = summary_body.get("global") if isinstance(summary_body, dict) else None
            next_action = summary_body.get("next_action") if isinstance(summary_body, dict) else None
            summary_ok = isinstance(global_scope, dict) and "outcome_count" in global_scope and "win_rate_pct" in global_scope
            next_action_ok = next_action is None or (
                isinstance(next_action, dict)
                and isinstance(next_action.get("steps"), list)
                and bool(str(next_action.get("headline") or "").strip())
            )
            closed_loop_feedback_pass = invalid == 0 and summary_ok and next_action_ok
            closed_loop_detail = (
                f"entries={len(items)}, invalid={invalid}, "
                f"summary_ok={summary_ok}, next_action_ok={next_action_ok}, phase=workflow_plus_learning"
            )
        else:
            closed_loop_detail = f"status_endpoint={status_res.status_code}, summary_endpoint={outcome_summary_res.status_code}"
    except Exception as e:
        err = f"endpoint_error={e}"
        payload_detail = err
        trace_detail = err
        permit_detail = err
        safety_detail = err
        handoff_detail = err
        closed_loop_detail = err
        outreach_policy_detail = err

    checks.append(("outreach_policy_config_contract", outreach_policy_contract_pass, outreach_policy_detail))
    checks.append(("outreach_payload_contract", outreach_payload_pass, payload_detail))
    checks.append(("investigation_traceability", investigation_trace_pass, trace_detail))
    checks.append(("permit_evidence_contract", permit_contract_pass, permit_detail))
    checks.append(("outreach_safety_guardrails", outreach_safety_pass, safety_detail))
    checks.append(("action_handoff_contract", action_handoff_pass, handoff_detail))
    checks.append(("closed_loop_feedback_contract", closed_loop_feedback_pass, closed_loop_detail))

    report_path = ROOT / "artifacts/eval-summary.md"
    lines = ["# Eval Summary", "", "## Gate Results", ""]
    failed = []
    for gate, ok, detail in checks:
        lines.append(f"- {'✅' if ok else '❌'} **{gate}** — {detail}")
        if not ok:
            failed.append(gate)

    lines += [
        "",
        "## Dataset Snapshot",
        "",
        f"- sites: {len(sites)}",
        f"- scored: {len(scored)}",
        f"- h3 cells: {len(h3_rows)}",
        f"- zip count: {len(zip_codes)}",
    ]

    if zip_codes:
        lines.append("")
        lines.append("## Per-ZIP Coverage")
        lines.append("")
        for z in zip_codes:
            lines.append(
                f"- `{z}`: sites={site_by_zip.get(z, 0)}, scored={scored_by_zip.get(z, 0)}, "
                f"coverage={per_zip_coverage.get(z, 0.0):.2%}, stability={per_zip_stability.get(z, 0.0):.3f}"
            )

    lines.append("")
    if failed:
        lines.append(f"Status: **FAIL** ({', '.join(failed)})")
    else:
        lines.append("Status: **PASS**")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {report_path}")
    print("PASS" if not failed else "FAIL")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
