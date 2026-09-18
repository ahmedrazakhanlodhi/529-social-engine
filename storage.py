"""Persistence for the living calendar and campaign tracker.

Two backends, chosen automatically:
  1. Google Sheets  -> used when a service account and sheet id are in secrets.
     This is the durable, shared store for the two-person team.
  2. Local CSV      -> fallback so the app runs on first deploy with no setup.
     Note: Streamlit Community Cloud disk is ephemeral, so the CSV resets on
     reboot. Add the service account to secrets to switch to Sheets for real
     shared persistence.
"""
from pathlib import Path
import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

CALENDAR_COLS = ["date", "channel", "pillar", "audience", "fact_id",
                 "headline", "template_type", "approval_lane", "status", "notes"]
CAMPAIGN_COLS = ["order", "fact_id", "headline", "approved_statement", "status", "target_week"]

def _sheets_client():
    try:
        if "gcp_service_account" not in st.secrets or "sheet_id" not in st.secrets:
            return None
        import gspread
        gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
        return gc.open_by_key(st.secrets["sheet_id"])
    except Exception as e:  # never crash the app on a storage hiccup or missing secrets
        st.session_state["_storage_error"] = str(e)
        return None

def backend_name():
    return "Google Sheets" if _sheets_client() else "Local CSV (ephemeral)"

def _cols(name):
    return CALENDAR_COLS if name == "calendar" else CAMPAIGN_COLS

def load_df(name):
    cols = _cols(name)
    sh = _sheets_client()
    if sh:
        try:
            ws = sh.worksheet(name)
            rows = ws.get_all_records()
            df = pd.DataFrame(rows)
            return df.reindex(columns=cols) if not df.empty else pd.DataFrame(columns=cols)
        except Exception:
            try:
                sh.add_worksheet(title=name, rows=200, cols=len(cols))
            except Exception:
                pass
            return pd.DataFrame(columns=cols)
    fp = DATA / f"{name}.csv"
    if fp.exists():
        return pd.read_csv(fp).reindex(columns=cols)
    return pd.DataFrame(columns=cols)

def save_df(name, df):
    cols = _cols(name)
    df = df.reindex(columns=cols).fillna("")
    sh = _sheets_client()
    if sh:
        try:
            try:
                ws = sh.worksheet(name)
            except Exception:
                ws = sh.add_worksheet(title=name, rows=max(200, len(df) + 10), cols=len(cols))
            ws.clear()
            ws.update([cols] + df.astype(str).values.tolist())
            return True
        except Exception as e:
            st.session_state["_storage_error"] = str(e)
            return False
    df.to_csv(DATA / f"{name}.csv", index=False)
    return True
