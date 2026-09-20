"""Content-library helpers and workflow rules."""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import storage

ROOT = Path(__file__).parent
WORKFLOW = ["Draft", "Fact checked", "Communications review", "Approved", "Scheduled", "Published", "Archived", "Retired"]
TEMPLATES = ["BIG NUMBER", "MYTH / FACT", "STATE SPOTLIGHT", "ACCESS", "PEOPLE & PARTNERSHIPS", "EVENT / TIMELY", "SIMPLE EXPLAINER"]
CONTENT_TYPES = ["Compendium", "Evergreen FAQ", "Member Story", "Event / Timely", "Employer", "Media & Research", "Other"]


def load_fact_bank() -> tuple[dict, list[dict]]:
    data = json.loads((ROOT / "fact_bank.json").read_text())
    items = []
    for group_key, group_label in [("campaign_findings", "Campaign finding"), ("state_spotlights", "State spotlight"), ("credibility_facts", "Credibility")]:
        for raw in data.get(group_key, []):
            f = dict(raw)
            f["_group"] = group_label
            f["content_type"] = "Compendium"
            f["campaign"] = "A National Effort, State by State" if group_key == "campaign_findings" else ""
            f["timing"] = "Evergreen"
            # Normalize the one legacy label to a supported dedicated template.
            if f.get("template_type") in ("PARTNERSHIPS", "PEOPLE & PARTNERSHIPS"):
                f["template_type"] = "PEOPLE & PARTNERSHIPS"
            items.append(f)
    return data, items


def load_library() -> tuple[dict, list[dict], dict[str, dict]]:
    data, facts = load_fact_bank()
    custom = storage.load_df("custom_content")
    custom_items = []
    for _, row in custom.iterrows():
        f = row.to_dict()
        f["id"] = str(f.get("content_id", ""))
        f["_group"] = "Custom"
        custom_items.append(f)
    all_items = facts + custom_items
    status = storage.ensure_content_status([f["id"] for f in facts], imported_approved=True)
    custom_ids = [f["id"] for f in custom_items]
    if custom_ids:
        storage.ensure_content_status(custom_ids, imported_approved=False)
        status = storage.load_df("content_status")
    status_map = {str(r["content_id"]): r.to_dict() for _, r in status.iterrows()}
    for f in all_items:
        wf = status_map.get(str(f["id"]), {})
        f["workflow_status"] = wf.get("status", "Draft")
        f["owner"] = wf.get("owner", "")
    return data, all_items, {str(f["id"]): f for f in all_items}


def norm(f: dict) -> dict:
    return {
        "id": f.get("id") or f.get("content_id"),
        "template_type": f.get("template_type", "BIG NUMBER"),
        "headline": f.get("headline", ""),
        "approved_statement": f.get("approved_statement", ""),
        "statement": f.get("approved_statement", ""),
        "source": f.get("source", ""),
        "source_url": f.get("source_url", ""),
        "primary_cta": f.get("primary_cta", ""),
        "cta": f.get("primary_cta", ""),
        "qualifier": f.get("qualifier", ""),
        "primary_audience": f.get("primary_audience", ""),
        "pillar": f.get("pillar", ""),
        "state": f.get("state", ""),
        "program": f.get("program", ""),
        "campaign": f.get("campaign", ""),
        "content_type": f.get("content_type", "Compendium"),
        "timing": f.get("timing", "Evergreen"),
    }


def label(f: dict) -> str:
    return f"{f.get('headline','Untitled')} — {f.get('id','')}"


def save_custom(record: dict) -> bool:
    df = storage.load_df("custom_content")
    cid = record.get("content_id") or storage.new_item_id("custom")
    record = dict(record)
    record["content_id"] = cid
    record.setdefault("created_at", storage.now_iso())

    existing = df[df["content_id"].astype(str) == str(cid)]
    factual_fields = ["approved_statement", "qualifier", "source", "source_url", "source_year"]
    factual_changed = False
    if not existing.empty:
        old = existing.iloc[0].to_dict()
        factual_changed = any(str(old.get(k, "")) != str(record.get(k, "")) for k in factual_fields)

    df = pd.concat([df[df["content_id"].astype(str) != str(cid)], pd.DataFrame([record])], ignore_index=True)
    ok = storage.save_df("custom_content", df)
    if ok:
        storage.ensure_content_status([cid], imported_approved=False)
        storage.append_audit(cid, "Custom content updated" if not existing.empty else "Custom content created", "", notes="Factual fields changed" if factual_changed else "")
        if factual_changed:
            statuses = storage.load_df("content_status")
            idx = statuses.index[statuses["content_id"].astype(str) == str(cid)]
            if len(idx):
                i = idx[0]
                old_status = str(statuses.at[i, "status"])
                if old_status not in ("Draft", "Retired"):
                    statuses.at[i, "status"] = "Draft"
                    statuses.at[i, "last_action"] = "Material factual edit — review reset"
                    statuses.at[i, "last_action_date"] = storage.now_iso()
                    statuses.at[i, "verified_by"] = ""
                    statuses.at[i, "verified_date"] = ""
                    statuses.at[i, "approved_by"] = ""
                    statuses.at[i, "approved_date"] = ""
                    storage.save_df("content_status", statuses)
                    storage.append_audit(cid, "Approval reset after factual edit", "", old_status, "Draft", "Material factual fields changed")
    return ok


def update_workflow(content_id: str, new_status: str, actor: str = "", notes: str = "") -> bool:
    df = storage.load_df("content_status")
    if content_id not in set(df["content_id"].astype(str)):
        storage.ensure_content_status([content_id], imported_approved=False)
        df = storage.load_df("content_status")
    idx = df.index[df["content_id"].astype(str) == str(content_id)]
    if len(idx) == 0:
        return False
    i = idx[0]
    old_status = str(df.at[i, "status"])
    df.at[i, "status"] = new_status
    df.at[i, "last_action"] = f"Status changed to {new_status}"
    df.at[i, "last_action_date"] = storage.now_iso()
    if notes:
        df.at[i, "notes"] = notes
    if actor:
        df.at[i, "owner"] = df.at[i, "owner"] or actor
    if new_status == "Fact checked":
        df.at[i, "verified_by"] = actor
        df.at[i, "verified_date"] = storage.now_iso()
    if new_status == "Approved":
        df.at[i, "approved_by"] = actor
        df.at[i, "approved_date"] = storage.now_iso()
    ok = storage.save_df("content_status", df)
    if ok:
        storage.append_audit(content_id, "Workflow status changed", actor, old_status, new_status, notes)
    return ok


def ensure_campaign(data: dict) -> pd.DataFrame:
    camp = storage.load_df("campaign")
    if not camp.empty:
        return camp
    rows = []
    for i, f in enumerate(data.get("campaign_findings", []), 1):
        rows.append({
            "campaign_id": "national-effort-2026",
            "campaign_name": "A National Effort, State by State",
            "order": i,
            "content_id": f["id"],
            "headline": f["headline"],
            "status": "Not started",
            "target_week": f"Week {i}",  # fix original Week-2 initialization bug
            "owner": "",
            "start_date": "",
            "end_date": "",
        })
    camp = pd.DataFrame(rows)
    storage.save_df("campaign", camp)
    return camp
