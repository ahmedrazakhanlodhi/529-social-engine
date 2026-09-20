"""The 529 Network Content Hub.

A lightweight, source-controlled content operations system for planning,
creating, approving, amplifying, and learning from communications content.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

import atomize
import brand
import content_ops
import planner
import quality
import render
import storage

ROOT = Path(__file__).parent
st.set_page_config(page_title="The 529 Network Content Hub", page_icon="🎓", layout="wide")

# ---------- restrained UI ----------
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1280px;}
      h1, h2, h3 {letter-spacing: -0.02em;}
      div[data-testid="stMetric"] {background: #F4F6F1; border: 1px solid #e4e9df; padding: 12px 14px; border-radius: 8px;}
      .small-muted {color:#708686; font-size:0.9rem;}
      .hub-kicker {font-weight:700; color:#3A8916; letter-spacing:.08em; font-size:.78rem;}
      .hub-title {font-size:2rem; font-weight:800; margin:.1rem 0 0; color:#242A24;}
      .hub-sub {color:#708686; margin-bottom:1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def _has_secret(key):
    try:
        return key in st.secrets
    except Exception:
        return False


def gate():
    if not _has_secret("app_password"):
        return True
    if st.session_state.get("_auth"):
        return True
    st.image(brand.LOGOS["529_color"], width=260)
    st.title("Content Hub")
    pw = st.text_input("Password", type="password")
    if st.button("Enter", type="primary"):
        if pw == st.secrets["app_password"]:
            st.session_state["_auth"] = True
            st.rerun()
        st.error("Incorrect password.")
    return False


if not gate():
    st.stop()

DATA, CONTENT, CONTENT_BY_ID = content_ops.load_library()
SETTINGS = storage.load_settings()
CAMPAIGN = content_ops.ensure_campaign(DATA)


def refresh_library():
    st.cache_data.clear()
    st.rerun()


def status_map():
    df = storage.load_df("content_status")
    return {str(r["content_id"]): r.to_dict() for _, r in df.iterrows()}


def make_graphic_bytes(fact: dict, size_name: str, graphic_text: str | None = None, theme: str = "green", photo=None) -> bytes:
    f = content_ops.norm(fact)
    spec = {
        "template_type": f["template_type"],
        "headline": f["headline"],
        "statement": f["approved_statement"],
        "graphic_text": graphic_text or f["approved_statement"],
        "source": f["source"],
        "cta": f["primary_cta"],
        "qualifier": f["qualifier"],
        "state": f["state"],
        "program": f["program"],
        "theme": theme,
        "size": brand.SIZES[size_name],
    }
    if photo is not None:
        spec["photo"] = photo
    if "MYTH" in f["template_type"].upper():
        spec["myth_text"] = "“I need a lot of money to start.”"
    if "ACCESS" in f["template_type"].upper():
        spec["stats"] = [
            {"num": "34", "label": "states report targeted rural outreach"},
            {"num": "32", "label": "accept ITINs as account-owner ID"},
            {"num": "23", "label": "provide plan information in Spanish"},
        ]
    img = render.render(spec)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def content_package(fact: dict, outputs: dict[str, str], graphic_text: str, theme: str = "green", photo=None, rights_note: str = "") -> bytes:
    f = content_ops.norm(fact)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        md = [f"# Content package: {f['headline']}", "", "## Controlled factual core", f["approved_statement"], "", f"Source: {f['source']}"]
        if f.get("qualifier"):
            md += [f"Qualifier: {f['qualifier']}"]
        md += ["", "## Channel copy"]
        for name, text in outputs.items():
            md += ["", f"### {name}", text]
        z.writestr("content_package.md", "\n".join(md))
        z.writestr("source_control.txt", f"CONTENT ID: {f['id']}\nFACTUAL CORE (LOCKED): {f['approved_statement']}\nQUALIFIER: {f['qualifier']}\nSOURCE: {f['source']}\n")
        z.writestr("photo_rights.txt", rights_note or "No external photo included in package.")
        core_sizes = ["Instagram portrait (1080x1350)", "Instagram / Facebook square (1080x1080)", "LinkedIn (1200x627)"]
        for sn in core_sizes:
            z.writestr(f"graphics/{sn.split('(')[0].strip().replace(' ','_').replace('/','-')}.png", make_graphic_bytes(fact, sn, graphic_text, theme, photo))
    return out.getvalue()


# ---------- sidebar ----------
st.sidebar.image(brand.LOGOS["529_color"], width="stretch")
st.sidebar.markdown("**CONTENT HUB**")
st.sidebar.caption("Plan • Create • Approve • Amplify • Learn")
PAGE = st.sidebar.radio(
    "Navigation",
    ["Home", "Plan", "Content Library", "Create", "Calendar", "Approvals", "Member Toolkits", "Performance", "Settings"],
    label_visibility="collapsed",
)
st.sidebar.caption(f"Storage: {storage.backend_name()}")
_ls = st.session_state.get("_last_save")
if _ls:
    st.sidebar.caption(f"Last saved: {_ls['table']} at {_ls['at'][11:19]}")
if st.session_state.get("_storage_error"):
    st.sidebar.warning(st.session_state["_storage_error"])


# ================= HOME =================
if PAGE == "Home":
    st.markdown('<div class="hub-kicker">THE 529 NETWORK</div><div class="hub-title">Content Hub</div><div class="hub-sub">Plan • Create • Approve • Amplify • Learn</div>', unsafe_allow_html=True)
    cal = storage.load_df("calendar")
    wf = storage.load_df("content_status")
    today = dt.date.today()
    cal_dates = pd.to_datetime(cal["date"], errors="coerce") if not cal.empty else pd.Series(dtype="datetime64[ns]")
    week_end = today + dt.timedelta(days=7)
    this_week = cal[(cal_dates.dt.date >= today) & (cal_dates.dt.date <= week_end)] if not cal.empty else cal
    pending = wf[wf["status"].isin(["Draft", "Fact checked", "Communications review"])] if not wf.empty else wf
    approved = wf[wf["status"] == "Approved"] if not wf.empty else wf
    published = cal[cal["status"] == "Published"] if not cal.empty else cal

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Planned next 7 days", len(this_week.drop_duplicates("item_id")) if not this_week.empty else 0)
    c2.metric("Needs review", len(pending))
    c3.metric("Approved library items", len(approved))
    c4.metric("Published executions", len(published))

    notes = DATA.get("meta", {}).get("known_discrepancies", [])
    if notes:
        with st.expander("Source-control decisions"):
            for nte in notes:
                st.caption(nte)

    st.subheader("What needs attention")
    warnings = planner.repetition_warnings(cal, int(SETTINGS.get("recency_days", 21)))
    if warnings:
        for w in warnings[:5]:
            st.warning(w)
    elif pending.empty:
        st.success("No urgent workflow or repetition issues are currently flagged.")
    if not pending.empty:
        st.write(f"**{len(pending)} item(s)** are still in Draft, Fact checked, or Communications review.")

    st.subheader("This week")
    if this_week.empty:
        st.info("Nothing is scheduled for the next seven days. Open **Plan** to build the week.")
    else:
        show = this_week[["date", "headline", "channel", "pillar", "audience", "status"]].sort_values("date")
        st.dataframe(show, hide_index=True, width="stretch")

    st.subheader("Recommended next action")
    recs = planner.recommend(CONTENT, cal, SETTINGS, today=today, n=1)
    if recs:
        r = recs[0]
        st.write(f"**Build:** {r['content']['headline']} — {r['content'].get('pillar','')}")
        st.caption("Why: " + r["reason"])
    else:
        st.info("No recommendable content is available yet.")

    with st.expander("Active Compendium campaign"):
        camp = storage.load_df("campaign")
        if not camp.empty:
            done = (camp["status"] == "Published").sum()
            st.progress(done / max(len(camp), 1), text=f"{done} of {len(camp)} campaign findings published")
            st.dataframe(camp[["target_week", "headline", "status"]], hide_index=True, width="stretch")


# ================= PLAN =================
elif PAGE == "Plan":
    st.header("Plan the week")
    st.caption("The planner recommends a balanced slate using approved content, recent use, audience coverage, and monthly pillar targets.")
    today = dt.date.today()
    cal = storage.load_df("calendar")
    recs = planner.recommend(CONTENT, cal, SETTINGS, today=today, n=int(SETTINGS.get("posts_per_week", 3)))
    slots = planner.DEFAULT_SLOTS[:len(recs)]
    planned = []

    for i, ((day, wd), rec) in enumerate(zip(slots, recs)):
        target_date = planner.next_weekday(today, wd)
        st.subheader(f"{day} • {target_date:%b %d}")
        cols = st.columns([1.2, 1, 1])
        recommended_id = str(rec["content"]["id"])
        approved_ids = [str(x["id"]) for x in CONTENT if x.get("workflow_status") == "Approved"]
        if not approved_ids:
            approved_ids = [str(x["id"]) for x in CONTENT]
        default_idx = approved_ids.index(recommended_id) if recommended_id in approved_ids else 0
        cid = cols[0].selectbox(
            "Content",
            approved_ids,
            index=default_idx,
            format_func=lambda x: content_ops.label(CONTENT_BY_ID[x]),
            key=f"plan_content_{i}",
        )
        item = CONTENT_BY_ID[cid]
        channels = cols[1].multiselect("Channels", SETTINGS.get("active_platforms", ["Instagram", "LinkedIn"]), default=[x for x in ["Instagram", "LinkedIn"] if x in SETTINGS.get("active_platforms", [])], key=f"plan_channels_{i}")
        owner = cols[2].text_input("Owner", SETTINGS.get("default_owner", ""), key=f"plan_owner_{i}")
        st.write(item.get("approved_statement", ""))
        st.caption(f"Pillar: {item.get('pillar','')} • Audience: {item.get('primary_audience','')} • Status: {item.get('workflow_status','')}")
        if cid == recommended_id:
            st.info("Why this was recommended: " + rec["reason"])
        else:
            st.caption("Replacement selected manually.")
        planned.append((target_date, item, channels, owner))
        st.divider()

    if st.button("Add recommended week to calendar", type="primary", disabled=not planned):
        cal = storage.load_df("calendar")
        rows = []
        for target_date, item, channels, owner in planned:
            item_id = storage.new_item_id("idea")
            for channel in channels:
                rows.append({
                    "item_id": item_id,
                    "content_id": item["id"],
                    "date": str(target_date),
                    "channel": channel,
                    "pillar": item.get("pillar", ""),
                    "audience": item.get("primary_audience", ""),
                    "headline": item.get("headline", ""),
                    "template_type": item.get("template_type", ""),
                    "status": "Scheduled",
                    "campaign": item.get("campaign", ""),
                    "owner": owner,
                    "notes": "Added by Smart Planner",
                    "created_at": storage.now_iso(),
                })
        if rows:
            cal = pd.concat([cal, pd.DataFrame(rows)], ignore_index=True)
            if storage.save_df("calendar", cal):
                st.success(f"Added {len(set(r['item_id'] for r in rows))} content ideas / {len(rows)} channel executions.")
            else:
                st.error("Could not save the calendar.")

    st.subheader("Content balance this month")
    ideas, channels = planner.mix_tables(cal, today.strftime("%Y-%m"))
    a, b = st.columns(2)
    with a:
        st.caption("Content mix — unique ideas")
        if ideas.empty:
            st.info("No content ideas scheduled this month.")
        else:
            st.dataframe(ideas, hide_index=True, width="stretch")
    with b:
        st.caption("Channel distribution — executions")
        if channels.empty:
            st.info("No channel executions scheduled this month.")
        else:
            st.dataframe(channels, hide_index=True, width="stretch")

    with st.expander("Manage the 12-part Compendium campaign"):
        camp = storage.load_df("campaign")
        edited = st.data_editor(
            camp,
            hide_index=True,
            width="stretch",
            column_config={"status": st.column_config.SelectboxColumn(options=["Not started", "Drafted", "Scheduled", "Published"])},
        )
        if st.button("Save campaign tracker"):
            st.success("Campaign tracker saved.") if storage.save_df("campaign", edited) else st.error("Save failed.")


# ================= CONTENT LIBRARY =================
elif PAGE == "Content Library":
    st.header("Content Library")
    st.caption("Compendium facts are controlled source copy. Add evergreen FAQs, member stories, events, employer content, and other approved sources here as the program grows.")
    for note in DATA.get("meta", {}).get("known_discrepancies", []):
        st.warning(note)

    qcol, pcol, scol = st.columns([2, 1, 1])
    q = qcol.text_input("Search")
    pillars = ["All"] + list(brand.PILLARS.keys())
    p = pcol.selectbox("Pillar", pillars)
    statuses = ["All"] + brand.WORKFLOW
    s = scol.selectbox("Workflow", statuses)

    filtered = []
    for f in CONTENT:
        blob = " ".join(str(v) for v in f.values()).lower()
        if q and q.lower() not in blob:
            continue
        if p != "All" and f.get("pillar") != p:
            continue
        if s != "All" and f.get("workflow_status") != s:
            continue
        filtered.append(f)

    st.caption(f"{len(filtered)} item(s)")
    for f in filtered:
        with st.expander(f"{f.get('headline','Untitled')} — {f.get('pillar','')} — {f.get('workflow_status','')}"):
            st.write(f.get("approved_statement", ""))
            if f.get("qualifier"):
                st.caption("Qualifier: " + str(f["qualifier"]))
            st.caption(f"Source: {f.get('source','')} • Audience: {f.get('primary_audience','')} • Type: {f.get('content_type','')}")
            issues = quality.content_checks(content_ops.norm(f))
            if issues:
                quality.show_issues(st, issues)

    st.divider()
    st.subheader("Add a new content item")
    st.caption("New items start as Draft and must move through review before the Smart Planner will recommend them.")
    with st.form("new_content"):
        headline = st.text_input("Headline")
        statement = st.text_area("Factual core / approved statement", height=100)
        full_context = st.text_area("Context / notes", height=80)
        qualifier = st.text_input("Qualifier")
        source = st.text_input("Source with page / section reference")
        source_url = st.text_input("Source URL (optional)")
        c1, c2, c3 = st.columns(3)
        pillar = c1.selectbox("Pillar", list(brand.PILLARS.keys()))
        audience = c2.text_input("Primary audience", "Parents & caregivers")
        template = c3.selectbox("Suggested template", content_ops.TEMPLATES)
        c4, c5, c6 = st.columns(3)
        content_type = c4.selectbox("Content type", content_ops.CONTENT_TYPES)
        timing = c5.selectbox("Timing", ["Evergreen", "Timely"])
        cta = c6.text_input("CTA", "Learn more")
        state = st.text_input("State (only if state-specific)")
        submitted = st.form_submit_button("Create Draft")
    if submitted:
        rec = {
            "content_id": storage.new_item_id("custom"),
            "headline": headline,
            "approved_statement": statement,
            "full_context": full_context,
            "qualifier": qualifier,
            "source": source,
            "source_url": source_url,
            "source_year": "",
            "pillar": pillar,
            "primary_audience": audience,
            "template_type": template,
            "primary_cta": cta,
            "content_type": content_type,
            "campaign": "",
            "timing": timing,
            "state": state,
            "program": "",
            "created_at": storage.now_iso(),
        }
        issues = quality.content_checks({"approved_statement": statement, "source": source, "primary_cta": cta, "state": state, "qualifier": qualifier})
        hard = [x for x in issues if x[0] == "error"]
        if hard:
            quality.show_issues(st, issues)
        elif content_ops.save_custom(rec):
            st.success("Draft created. Move it through Approvals when ready.")
            st.rerun()

    custom_items = [f for f in CONTENT if f.get("_group") == "Custom"]
    if custom_items:
        with st.expander("Edit an existing custom item"):
            ecid = st.selectbox("Custom item", [f["id"] for f in custom_items], format_func=lambda x: content_ops.label(CONTENT_BY_ID[x]), key="edit_custom_choice")
            existing = CONTENT_BY_ID[ecid]
            with st.form("edit_custom_form"):
                e_headline = st.text_input("Headline", existing.get("headline", ""))
                e_statement = st.text_area("Factual core / approved statement", existing.get("approved_statement", ""), height=100)
                e_context = st.text_area("Context / notes", existing.get("full_context", ""), height=80)
                e_qualifier = st.text_input("Qualifier", existing.get("qualifier", ""))
                e_source = st.text_input("Source with page / section reference", existing.get("source", ""))
                e_source_url = st.text_input("Source URL", existing.get("source_url", ""))
                e1, e2, e3 = st.columns(3)
                e_pillar = e1.selectbox("Pillar", list(brand.PILLARS.keys()), index=list(brand.PILLARS.keys()).index(existing.get("pillar")) if existing.get("pillar") in brand.PILLARS else 0)
                e_audience = e2.text_input("Primary audience", existing.get("primary_audience", ""))
                e_template = e3.selectbox("Suggested template", content_ops.TEMPLATES, index=content_ops.TEMPLATES.index(existing.get("template_type")) if existing.get("template_type") in content_ops.TEMPLATES else 0)
                e4, e5 = st.columns(2)
                e_type = e4.selectbox("Content type", content_ops.CONTENT_TYPES, index=content_ops.CONTENT_TYPES.index(existing.get("content_type")) if existing.get("content_type") in content_ops.CONTENT_TYPES else 0)
                e_cta = e5.text_input("CTA", existing.get("primary_cta", ""))
                e_state = st.text_input("State", existing.get("state", ""))
                save_edit = st.form_submit_button("Save changes")
            if save_edit:
                updated = {
                    "content_id": ecid, "headline": e_headline, "approved_statement": e_statement,
                    "full_context": e_context, "qualifier": e_qualifier, "source": e_source,
                    "source_url": e_source_url, "source_year": existing.get("source_year", ""),
                    "pillar": e_pillar, "primary_audience": e_audience, "template_type": e_template,
                    "primary_cta": e_cta, "content_type": e_type, "campaign": existing.get("campaign", ""),
                    "timing": existing.get("timing", "Evergreen"), "state": e_state,
                    "program": existing.get("program", ""), "created_at": existing.get("created_at", storage.now_iso()),
                }
                if content_ops.save_custom(updated):
                    st.success("Changes saved. If factual fields changed, approval was automatically reset to Draft for re-checking.")
                    st.rerun()


# ================= CREATE =================
elif PAGE == "Create":
    st.header("Create")
    st.caption("Turn one controlled content item into coordinated channel copy and graphics. The factual core stays locked; creative framing remains editable.")
    approved = [f for f in CONTENT if f.get("workflow_status") in {"Approved", "Scheduled", "Published"}]
    choices = approved or CONTENT
    if not choices:
        st.info("No content is available yet.")
        st.stop()
    cid = st.selectbox("Approved content", [f["id"] for f in choices], format_func=lambda x: content_ops.label(CONTENT_BY_ID[x]))
    fact = CONTENT_BY_ID[cid]
    f = content_ops.norm(fact)
    st.text_area("Controlled factual core", f["approved_statement"], height=100, disabled=True)
    st.caption(f"Source: {f['source']}")
    if f.get("qualifier"):
        st.caption(f"Qualifier: {f['qualifier']}")

    outputs = atomize.all_formats(f, SETTINGS)
    st.subheader("Channel copy")
    edited_outputs = {}
    tabs = st.tabs(["LinkedIn", "Instagram", "Facebook", "Carousel / video", "Website / email"])
    groups = [
        ["LinkedIn"],
        ["Instagram"],
        ["Facebook", "Short-form copy"],
        ["Instagram carousel", "30-second video script", "Alt text"],
        ["Website / newsletter paragraph", "Email block", "Member toolkit"],
    ]
    for tab, names in zip(tabs, groups):
        with tab:
            for name in names:
                edited_outputs[name] = st.text_area(name, outputs[name], height=170, key=f"create_{cid}_{name}")

    st.subheader("Graphic")
    c1, c2 = st.columns(2)
    graphic_text = c1.text_area("Graphic text (keep this short; caption carries the detail)", f["approved_statement"], height=100)
    theme = c2.selectbox("Theme", ["green", "light"])
    photo = None
    rights_note = ""
    if any(x in f["template_type"].upper() for x in ["STATE", "PEOPLE", "PARTNER"]):
        upload = st.file_uploader("Optional approved photo", type=["png", "jpg", "jpeg"])
        rights_note = st.text_input("Photo rights / source")
        if upload:
            photo = Image.open(upload)
    alt = edited_outputs.get("Alt text", outputs.get("Alt text", ""))
    quality.show_issues(st, quality.creative_checks(f["headline"], graphic_text, f["source"], f["primary_cta"], alt, photo is not None, rights_note))
    preview_size = st.selectbox("Preview size", list(brand.SIZES.keys()), index=0)
    if st.button("Render preview"):
        img_bytes = make_graphic_bytes(fact, preview_size, graphic_text, theme, photo)
        st.image(img_bytes, caption=preview_size, width="stretch")

    package = content_package(fact, edited_outputs, graphic_text, theme, photo, rights_note)
    st.download_button("Download publication-ready package (.zip)", package, f"{cid}_content_package.zip", "application/zip", type="primary")


# ================= CALENDAR =================
elif PAGE == "Calendar":
    st.header("Calendar")
    st.caption("One content idea can have multiple channel executions. item_id keeps the strategic content mix separate from channel volume.")
    cal = storage.load_df("calendar")
    filters = st.columns(4)
    fp = filters[0].selectbox("Platform", ["All"] + brand.CHANNELS)
    fstatus = filters[1].selectbox("Status", ["All", "Scheduled", "Published", "Archived"])
    fpillar = filters[2].selectbox("Pillar", ["All"] + list(brand.PILLARS.keys()))
    faudience = filters[3].text_input("Audience contains")
    view = cal.copy()
    if fp != "All": view = view[view["channel"] == fp]
    if fstatus != "All": view = view[view["status"] == fstatus]
    if fpillar != "All": view = view[view["pillar"] == fpillar]
    if faudience: view = view[view["audience"].astype(str).str.contains(faudience, case=False, na=False)]
    st.dataframe(view.sort_values("date") if not view.empty else view, hide_index=True, width="stretch")

    st.subheader("Edit calendar")
    edited = st.data_editor(
        cal,
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "channel": st.column_config.SelectboxColumn(options=brand.CHANNELS),
            "status": st.column_config.SelectboxColumn(options=["Scheduled", "Published", "Archived"]),
            "pillar": st.column_config.SelectboxColumn(options=list(brand.PILLARS.keys())),
        },
    )
    if st.button("Save calendar", type="primary"):
        st.success("Calendar saved.") if storage.save_df("calendar", edited) else st.error("Save failed.")

    warnings = planner.repetition_warnings(edited, int(SETTINGS.get("recency_days", 21)))
    if warnings:
        st.subheader("Repetition checks")
        for w in warnings:
            st.warning(w)


# ================= APPROVALS =================
elif PAGE == "Approvals":
    st.header("Approvals")
    st.caption("Draft → Fact checked → Communications review → Approved → Scheduled → Published. Approved factual copy remains controlled.")
    wf = storage.load_df("content_status")
    if wf.empty:
        st.info("No workflow records.")
        st.stop()
    cols = st.columns([2, 1, 1])
    filter_status = cols[0].multiselect("Show statuses", brand.WORKFLOW, default=["Draft", "Fact checked", "Communications review", "Approved"])
    actor = cols[1].text_input("Your name / initials")
    owner_filter = cols[2].text_input("Owner contains")
    view = wf[wf["status"].isin(filter_status)] if filter_status else wf
    if owner_filter:
        view = view[view["owner"].astype(str).str.contains(owner_filter, case=False, na=False)]

    for _, row in view.iterrows():
        cid = str(row["content_id"])
        item = CONTENT_BY_ID.get(cid, {"headline": cid, "approved_statement": "", "source": ""})
        with st.expander(f"{item.get('headline',cid)} — {row.get('status','')}"):
            st.write(item.get("approved_statement", ""))
            st.caption(f"Source: {item.get('source','')} • Owner: {row.get('owner','') or 'Unassigned'}")
            if row.get("verified_by"):
                st.caption(f"Fact checked by {row.get('verified_by')} {row.get('verified_date','')}")
            if row.get("approved_by"):
                st.caption(f"Approved by {row.get('approved_by')} {row.get('approved_date','')}")
            new_status = st.selectbox("Move to", brand.WORKFLOW, index=brand.WORKFLOW.index(row.get("status")) if row.get("status") in brand.WORKFLOW else 0, key=f"status_{cid}")
            notes = st.text_input("Review note", str(row.get("notes", "")), key=f"note_{cid}")
            if st.button("Update", key=f"update_{cid}"):
                if new_status in ["Fact checked", "Approved"] and not actor.strip():
                    st.error("Enter your name / initials before recording a fact check or approval.")
                elif content_ops.update_workflow(cid, new_status, actor.strip(), notes):
                    st.success("Workflow updated.")
                    st.rerun()

    with st.expander("Audit trail"):
        audit = storage.load_df("audit_log")
        if audit.empty:
            st.info("No audit events yet.")
        else:
            st.dataframe(audit.sort_values("timestamp", ascending=False), hide_index=True, width="stretch")


# ================= MEMBER TOOLKITS =================
elif PAGE == "Member Toolkits":
    st.header("Member Toolkits")
    st.caption("Create a coordinated package members can localize without changing the national factual core.")
    approved = [f for f in CONTENT if f.get("workflow_status") in {"Approved", "Scheduled", "Published"}]
    if not approved:
        st.info("No approved content is available.")
        st.stop()
    cid = st.selectbox("Approved content", [f["id"] for f in approved], format_func=lambda x: content_ops.label(CONTENT_BY_ID[x]))
    fact = CONTENT_BY_ID[cid]
    f = content_ops.norm(fact)
    kit = atomize.member_toolkit(f, SETTINGS)
    st.text_area("Toolkit copy", kit, height=420)
    graphic_text = st.text_area("Graphic text", f["approved_statement"], height=90, key="member_graphic")
    bundle = io.BytesIO()
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("member_toolkit.md", kit)
        z.writestr("README_FIRST.txt", "Localize only bracketed placeholders with verified state-specific information. Do not alter the national factual core without review.")
        for sn in ["Instagram portrait (1080x1350)", "Instagram / Facebook square (1080x1080)", "LinkedIn (1200x627)"]:
            z.writestr(f"graphics/{sn.split('(')[0].strip().replace(' ','_').replace('/','-')}.png", make_graphic_bytes(fact, sn, graphic_text))
    st.download_button("Download member toolkit (.zip)", bundle.getvalue(), f"{cid}_member_toolkit.zip", "application/zip", type="primary")
    st.info("State-specific placeholders intentionally remain blank unless verified information exists in the content library.")


# ================= PERFORMANCE =================
elif PAGE == "Performance":
    st.header("Performance")
    st.caption("Record post-publication results. The system separates early signals from conclusions and does not optimize only for engagement.")
    perf = storage.load_df("performance")
    cal = storage.load_df("calendar")
    published = cal[cal["status"] == "Published"] if not cal.empty else cal
    if not published.empty:
        missing = []
        existing_keys = set((perf["item_id"].astype(str) + "|" + perf["channel"].astype(str)).tolist()) if not perf.empty else set()
        for _, r in published.iterrows():
            key = f"{r['item_id']}|{r['channel']}"
            if key not in existing_keys:
                missing.append({
                    "item_id": r["item_id"], "content_id": r["content_id"], "date": r["date"], "channel": r["channel"],
                    "pillar": r["pillar"], "audience": r["audience"], "format": r["template_type"],
                    "impressions": "", "reach": "", "engagements": "", "clicks": "", "shares": "", "saves": "", "comments": "",
                    "video_views": "", "member_reposts": "", "website_sessions": "", "notes": "",
                })
        if missing and st.button(f"Add {len(missing)} published execution(s) to performance tracker"):
            perf = pd.concat([perf, pd.DataFrame(missing)], ignore_index=True)
            storage.save_df("performance", perf)
            st.rerun()

    edited = st.data_editor(perf, num_rows="dynamic", hide_index=True, width="stretch")
    if st.button("Save performance data", type="primary"):
        st.success("Performance data saved.") if storage.save_df("performance", edited) else st.error("Save failed.")

    numeric_cols = ["impressions", "reach", "engagements", "clicks", "shares", "saves", "comments", "video_views", "member_reposts", "website_sessions"]
    p = edited.copy()
    for col in numeric_cols:
        if col in p:
            p[col] = pd.to_numeric(p[col], errors="coerce")
    observed = p[p["impressions"].notna()] if "impressions" in p else pd.DataFrame()
    st.subheader("What is working?")
    if len(observed) < 5:
        st.info(f"Insufficient data for reliable pattern analysis. {len(observed)} execution(s) currently have impression data; aim for at least 5 before reading directional signals.")
    else:
        observed = observed.copy()
        observed["engagement_rate"] = observed["engagements"].fillna(0) / observed["impressions"].replace(0, float("nan"))
        pillar_perf = observed.groupby("pillar", dropna=False).agg(posts=("item_id", "count"), median_engagement_rate=("engagement_rate", "median"), total_clicks=("clicks", "sum")).reset_index()
        st.caption("Early signal — median engagement rate and clicks by pillar")
        st.dataframe(pillar_perf, hide_index=True, width="stretch")
        st.caption("Interpret carefully: performance can reflect audience size, paid support, timing, and platform differences as well as content quality.")


# ================= SETTINGS =================
elif PAGE == "Settings":
    st.header("Settings")
    st.caption("Keep the strategic controls simple. These settings shape recommendations without changing any factual content.")
    s = json.loads(json.dumps(SETTINGS))
    c1, c2 = st.columns(2)
    s["posts_per_week"] = c1.number_input("Posts / content ideas per week", min_value=1, max_value=3, value=int(s.get("posts_per_week", 3)))
    s["recency_days"] = c2.number_input("Repetition warning window (days)", min_value=7, max_value=90, value=int(s.get("recency_days", 21)))
    s["active_platforms"] = st.multiselect("Active platforms", brand.CHANNELS, default=s.get("active_platforms", ["Instagram", "LinkedIn", "Facebook"]))
    s["default_owner"] = st.text_input("Default content owner", s.get("default_owner", ""))
    s["primary_website_url"] = st.text_input("Primary website URL", s.get("primary_website_url", ""))
    u1, u2, u3 = st.columns(3)
    s["plan_finder_url"] = u1.text_input("Plan-finder URL", s.get("plan_finder_url", ""))
    s["report_url"] = u2.text_input("Report URL", s.get("report_url", ""))
    s["employer_url"] = u3.text_input("Employer / 529-at-work URL", s.get("employer_url", ""))
    s["utm_campaign"] = st.text_input("Default UTM campaign", s.get("utm_campaign", "529_network_content"))
    st.caption("These URLs turn the call to action in generated copy into a real, UTM-tagged link. Leave blank to keep the call to action as plain text.")
    st.subheader("Monthly pillar targets")
    targets = {}
    cols = st.columns(len(brand.PILLARS))
    for col, pillar in zip(cols, brand.PILLARS):
        targets[pillar] = col.number_input(pillar.replace(". ", ".\n"), min_value=0, max_value=100, value=int(s.get("pillar_targets", {}).get(pillar, brand.PILLARS[pillar])), key=f"target_{pillar}")
    s["pillar_targets"] = targets
    total = sum(targets.values())
    if total != 100:
        st.warning(f"Pillar targets currently total {total}%. Recommendations work best when they total 100%.")
    if st.button("Save settings", type="primary"):
        st.success("Settings saved.") if storage.save_settings(s) else st.error("Save failed.")

    st.subheader("Backup and restore")
    st.caption("On local storage, data resets when the server reboots. Download a backup before closing, and restore it after a reboot or when moving between local and Google Sheets.")
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        st.download_button("Download full backup (.zip)", storage.export_all_bytes(),
                           f"content_hub_backup_{dt.date.today().isoformat()}.zip", "application/zip")
    with bcol2:
        up = st.file_uploader("Restore from backup (.zip)", type=["zip"], key="restore_zip")
        if up and st.button("Restore now", type="secondary"):
            restored = storage.import_all_bytes(up.getvalue())
            if restored:
                st.success("Restored: " + ", ".join(restored))
                st.cache_data.clear()
            else:
                st.error("Nothing restored. Check the backup file.")

    with st.expander("Data / deployment note"):
        st.write("Local files make the prototype easy to run, but Streamlit Community Cloud local storage is ephemeral. Configure the existing Google Sheets backend for durable shared team use. The app does not require paid infrastructure to run locally.")
