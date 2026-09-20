"""Persistence layer for The 529 Network Content Hub.

Supports Google Sheets when configured, with local CSV/JSON fallback for easy
first-run deployment.  The module owns schemas and backward-compatible
migration so UI/business logic do not need to know how data are stored.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import uuid
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

SCHEMAS = {
    "calendar": [
        "item_id", "content_id", "date", "channel", "pillar", "audience",
        "headline", "template_type", "status", "campaign", "owner", "notes",
        "created_at",
    ],
    "campaign": [
        "campaign_id", "campaign_name", "order", "content_id", "headline",
        "status", "target_week", "owner", "start_date", "end_date",
    ],
    "content_status": [
        "content_id", "status", "owner", "verified_by", "verified_date",
        "approved_by", "approved_date", "last_action", "last_action_date", "notes",
    ],
    "custom_content": [
        "content_id", "headline", "approved_statement", "full_context", "qualifier",
        "source", "source_url", "source_year", "pillar", "primary_audience",
        "template_type", "primary_cta", "content_type", "campaign", "timing",
        "state", "program", "created_at",
    ],
    "performance": [
        "item_id", "content_id", "date", "channel", "pillar", "audience", "format",
        "impressions", "reach", "engagements", "clicks", "shares", "saves", "comments",
        "video_views", "member_reposts", "website_sessions", "notes",
    ],
    "audit_log": [
        "timestamp", "content_id", "action", "actor", "from_status", "to_status", "notes",
    ],
}

DEFAULT_SETTINGS = {
    "posts_per_week": 3,
    "recency_days": 21,
    "active_platforms": ["Instagram", "LinkedIn", "Facebook"],
    "primary_website_url": "",
    "plan_finder_url": "",
    "report_url": "",
    "employer_url": "",
    "utm_campaign": "529_network_content",
    "default_owner": "",
    "pillar_targets": {
        "1. 529 Made Simple": 30,
        "2. Proof in Numbers": 20,
        "3. Across the States": 20,
        "4. Education Paths": 15,
        "5. People & Partnerships": 15,
    },
}


def _sheets_client():
    try:
        if "gcp_service_account" not in st.secrets or "sheet_id" not in st.secrets:
            return None
        import gspread
        gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
        return gc.open_by_key(st.secrets["sheet_id"])
    except Exception as exc:
        st.session_state["_storage_error"] = str(exc)
        return None


def backend_name() -> str:
    return "Google Sheets" if _sheets_client() else "Local files (prototype / ephemeral on Streamlit Cloud)"


def _schema(name: str) -> list[str]:
    if name not in SCHEMAS:
        raise KeyError(f"Unknown table: {name}")
    return SCHEMAS[name]


def _read_raw(name: str) -> pd.DataFrame:
    sh = _sheets_client()
    if sh:
        try:
            ws = sh.worksheet(name)
            return pd.DataFrame(ws.get_all_records())
        except Exception:
            return pd.DataFrame()
    fp = DATA / f"{name}.csv"
    if fp.exists():
        try:
            return pd.read_csv(fp)
        except Exception as exc:
            st.session_state["_storage_error"] = f"Could not read {name}: {exc}"
    return pd.DataFrame()


def _migrate_calendar(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # Original prototype used fact_id and approval_lane and had no content-level item id.
    if "content_id" not in df.columns and "fact_id" in df.columns:
        df["content_id"] = df["fact_id"].astype(str)
    if "item_id" not in df.columns:
        def legacy_id(row):
            date = str(row.get("date", ""))
            cid = str(row.get("content_id", row.get("fact_id", "content")))
            # Same content/date on several channels represents one content idea.
            return f"legacy-{date}-{cid}"
        df["item_id"] = df.apply(legacy_id, axis=1)
    if "campaign" not in df.columns:
        df["campaign"] = ""
    if "owner" not in df.columns:
        df["owner"] = ""
    if "created_at" not in df.columns:
        df["created_at"] = ""
    if "status" in df.columns:
        df["status"] = df["status"].replace({"Planned": "Scheduled", "Drafting": "Draft", "In review": "Communications review"})
    return df


def _migrate_campaign(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "campaign_id" not in df.columns:
        df["campaign_id"] = "national-effort-2026"
    if "campaign_name" not in df.columns:
        df["campaign_name"] = "A National Effort, State by State"
    if "content_id" not in df.columns and "fact_id" in df.columns:
        df["content_id"] = df["fact_id"].astype(str)
    for c in ["owner", "start_date", "end_date"]:
        if c not in df.columns:
            df[c] = ""
    return df


def load_df(name: str) -> pd.DataFrame:
    cols = _schema(name)
    df = _read_raw(name)
    if name == "calendar":
        df = _migrate_calendar(df)
    elif name == "campaign":
        df = _migrate_campaign(df)
    if df.empty:
        return pd.DataFrame(columns=cols)
    return df.reindex(columns=cols).fillna("")


def save_df(name: str, df: pd.DataFrame) -> bool:
    cols = _schema(name)
    clean = df.reindex(columns=cols).fillna("")
    sh = _sheets_client()
    if sh:
        try:
            try:
                ws = sh.worksheet(name)
            except Exception:
                ws = sh.add_worksheet(title=name, rows=max(200, len(clean) + 20), cols=len(cols))
            ws.clear()
            ws.update([cols] + clean.astype(str).values.tolist())
            _stamp(name)
            return True
        except Exception as exc:
            st.session_state["_storage_error"] = str(exc)
            return False
    try:
        clean.to_csv(DATA / f"{name}.csv", index=False)
        _stamp(name)
        return True
    except Exception as exc:
        st.session_state["_storage_error"] = str(exc)
        return False


def _stamp(name: str) -> None:
    try:
        st.session_state["_last_save"] = {"table": name, "at": now_iso()}
    except Exception:
        pass


def new_item_id(prefix: str = "content") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_settings() -> dict:
    settings = json.loads(json.dumps(DEFAULT_SETTINGS))
    sh = _sheets_client()
    if sh:
        try:
            ws = sh.worksheet("settings")
            rows = ws.get_all_records()
            payload = {str(r.get("key")): r.get("value") for r in rows if r.get("key")}
            if payload.get("json"):
                user = json.loads(payload["json"])
                _deep_update(settings, user)
                return settings
        except Exception:
            pass
    fp = DATA / "settings.json"
    if fp.exists():
        try:
            _deep_update(settings, json.loads(fp.read_text()))
        except Exception as exc:
            st.session_state["_storage_error"] = f"Could not read settings: {exc}"
    return settings


def save_settings(settings: dict) -> bool:
    sh = _sheets_client()
    if sh:
        try:
            try:
                ws = sh.worksheet("settings")
            except Exception:
                ws = sh.add_worksheet(title="settings", rows=20, cols=2)
            ws.clear()
            ws.update([["key", "value"], ["json", json.dumps(settings)]])
            return True
        except Exception as exc:
            st.session_state["_storage_error"] = str(exc)
            return False
    try:
        (DATA / "settings.json").write_text(json.dumps(settings, indent=2))
        return True
    except Exception as exc:
        st.session_state["_storage_error"] = str(exc)
        return False


def _deep_update(base: dict, incoming: dict) -> dict:
    for k, v in incoming.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
    return base



def append_audit(content_id: str, action: str, actor: str = "", from_status: str = "", to_status: str = "", notes: str = "") -> bool:
    """Append a single audit row. Append-only so concurrent writers do not clobber
    each other the way a full-table rewrite would."""
    cols = _schema("audit_log")
    row = {"timestamp": now_iso(), "content_id": content_id, "action": action,
           "actor": actor, "from_status": from_status, "to_status": to_status, "notes": notes}
    values = [str(row[c]) for c in cols]
    sh = _sheets_client()
    if sh:
        try:
            try:
                ws = sh.worksheet("audit_log")
            except Exception:
                ws = sh.add_worksheet(title="audit_log", rows=1000, cols=len(cols))
                ws.update([cols])
            ws.append_row(values)
            return True
        except Exception as exc:
            st.session_state["_storage_error"] = str(exc)
            return False
    fp = DATA / "audit_log.csv"
    try:
        new = not fp.exists()
        import csv
        with fp.open("a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(cols)
            w.writerow(values)
        return True
    except Exception as exc:
        st.session_state["_storage_error"] = str(exc)
        return False


BACKUP_TABLES = ["calendar", "campaign", "content_status", "custom_content", "performance", "audit_log"]


def export_all_bytes() -> bytes:
    """Full backup of every table plus settings and the fact bank, as one zip."""
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in BACKUP_TABLES:
            z.writestr(f"{name}.csv", load_df(name).to_csv(index=False))
        z.writestr("settings.json", json.dumps(load_settings(), indent=2))
        fb = ROOT / "fact_bank.json"
        if fb.exists():
            z.writestr("fact_bank.json", fb.read_text())
        z.writestr("BACKUP_INFO.txt", f"Content Hub backup taken {now_iso()}.\nRestore from Settings > Backup and restore.")
    return buf.getvalue()


def import_all_bytes(data: bytes) -> list[str]:
    """Restore tables and settings from a backup zip. Returns the list restored."""
    import io, zipfile
    restored = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        for name in BACKUP_TABLES:
            fn = f"{name}.csv"
            if fn in names:
                df = pd.read_csv(io.BytesIO(z.read(fn)))
                if save_df(name, df):
                    restored.append(name)
        if "settings.json" in names:
            try:
                save_settings(json.loads(z.read("settings.json")))
                restored.append("settings")
            except Exception as exc:
                st.session_state["_storage_error"] = str(exc)
    return restored

def ensure_content_status(content_ids: list[str], imported_approved: bool = True) -> pd.DataFrame:
    """Ensure one workflow row per content id.

    Bundled fact-bank records are imported as Approved because the supplied fact bank
    explicitly identifies its wording as final/approved. Custom records start Draft.
    """
    df = load_df("content_status")
    existing = set(df["content_id"].astype(str)) if not df.empty else set()
    rows = []
    for cid in content_ids:
        if cid not in existing:
            rows.append({
                "content_id": cid,
                "status": "Approved" if imported_approved else "Draft",
                "owner": "",
                "verified_by": "Imported fact bank" if imported_approved else "",
                "verified_date": "",
                "approved_by": "Imported fact bank" if imported_approved else "",
                "approved_date": "",
                "last_action": "Imported controlled copy" if imported_approved else "Created",
                "last_action_date": now_iso(),
                "notes": "",
            })
    if rows:
        df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
        save_df("content_status", df)
    return df
