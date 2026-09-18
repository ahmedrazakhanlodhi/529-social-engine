"""The 529 Network Social Engine.
Plan the week, pull an approved fact, atomize it into eight formats, render
on-brand graphics for Instagram, Facebook and LinkedIn, and track the campaign.
Built on the 2026 National 529 Survey and the Social Media Revamp Strategy."""

import io, json, datetime as dt
from pathlib import Path
import pandas as pd
import streamlit as st

import brand, render, atomize, storage

ROOT = Path(__file__).parent
st.set_page_config(page_title="529 Network Social Engine", page_icon="\U0001F393", layout="wide")

# ---------- data ----------
@st.cache_data
def load_facts():
    d = json.load(open(ROOT / "fact_bank.json"))
    campaign = d["campaign_findings"]
    spots = d.get("state_spotlights", [])
    cred = d.get("credibility_facts", [])
    for f in campaign: f["_group"] = "Campaign finding"
    for f in spots: f["_group"] = "State spotlight"
    for f in cred: f["_group"] = "Credibility"
    allf = campaign + spots + cred
    return d, allf, {f["id"]: f for f in allf}

DATA, FACTS, FACT_BY_ID = load_facts()

def label(f):
    return f"{f['headline']}  \u2014  {f.get('id')}"

def norm(f):
    """uniform keys used by render/atomize"""
    return {
        "id": f.get("id"), "template_type": f.get("template_type", "BIG NUMBER"),
        "headline": f.get("headline", ""), "approved_statement": f.get("approved_statement", ""),
        "statement": f.get("approved_statement", ""), "source": f.get("source", ""),
        "primary_cta": f.get("primary_cta", ""), "cta": f.get("primary_cta", ""),
        "qualifier": f.get("qualifier", ""), "primary_audience": f.get("primary_audience", ""),
        "pillar": f.get("pillar", ""), "state": f.get("state", ""), "program": f.get("program", ""),
    }

# ---------- auth ----------
def _has_secret(key):
    try:
        return key in st.secrets
    except Exception:
        return False

def gate():
    if not _has_secret("app_password"):
        st.sidebar.info("Open access. Set app_password in secrets to lock this to you and Catherine.")
        return True
    if st.session_state.get("_auth"):
        return True
    st.title("The 529 Network Social Engine")
    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == st.secrets["app_password"]:
            st.session_state["_auth"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not gate():
    st.stop()

# ---------- sidebar ----------
st.sidebar.image(brand.LOGOS["529_color"], width="stretch")
page = st.sidebar.radio("Go to", ["This Week", "Fact Bank", "Atomize", "Design Studio", "Calendar", "Campaign"])
st.sidebar.caption(f"Storage: {storage.backend_name()}")
if st.session_state.get("_storage_error"):
    st.sidebar.warning("Storage note: " + st.session_state["_storage_error"])

def next_weekday(base, weekday):
    days = (weekday - base.weekday()) % 7
    return base + dt.timedelta(days=days)

# ================= THIS WEEK =================
if page == "This Week":
    st.header("This Week")
    st.caption("Pick three anchor stories on the Monday / Wednesday / Friday cadence. One post, one audience, one action.")
    today = dt.date.today()
    slots = [("Monday", "2. Proof in Numbers", 0), ("Wednesday", "1. 529 Made Simple", 2),
             ("Friday", "3. Across the States", 4)]
    picks = []
    cols = st.columns(3)
    for (day, pillar_hint, wd), col in zip(slots, cols):
        with col:
            st.subheader(day)
            st.caption(pillar_hint)
            fid = st.selectbox(f"{day} anchor", [f["id"] for f in FACTS],
                               format_func=lambda x: label(FACT_BY_ID[x]), key=f"tw_{day}")
            f = FACT_BY_ID[fid]
            st.write(f["approved_statement"])
            st.caption(f"Pillar: {f.get('pillar','')}  |  Audience: {f.get('primary_audience','')}")
            lane = brand.default_lane(f.get("template_type",""), f.get("pillar",""))
            st.caption(f"Suggested approval lane: {lane}")
            chans = st.multiselect(f"{day} channels", ["Instagram", "Facebook", "LinkedIn"],
                                   default=["Instagram", "LinkedIn"], key=f"ch_{day}")
            picks.append((next_weekday(today, wd), f, chans, lane))

    if st.button("Add this week to the calendar", type="primary"):
        cal = storage.load_df("calendar")
        rows = []
        for date, f, chans, lane in picks:
            for ch in chans:
                rows.append({"date": str(date), "channel": ch, "pillar": f.get("pillar",""),
                             "audience": f.get("primary_audience",""), "fact_id": f["id"],
                             "headline": f["headline"], "template_type": f.get("template_type",""),
                             "approval_lane": lane, "status": "Planned", "notes": ""})
        cal = pd.concat([cal, pd.DataFrame(rows)], ignore_index=True)
        if storage.save_df("calendar", cal):
            st.success(f"Added {len(rows)} posts to the calendar.")

    st.divider()
    st.subheader("Feed balance this month")
    cal = storage.load_df("calendar")
    if not cal.empty:
        cal["date"] = pd.to_datetime(cal["date"], errors="coerce")
        m = cal[cal["date"].dt.strftime("%Y-%m") == today.strftime("%Y-%m")]
        if not m.empty:
            dist = (m["pillar"].value_counts(normalize=True) * 100).round().to_dict()
            for pillar, target in brand.PILLARS.items():
                got = int(dist.get(pillar, 0))
                st.write(f"{pillar} \u2014 target {target}%, planned {got}%")
                st.progress(min(got, 100) / 100)
        else:
            st.info("No posts planned this month yet.")
    else:
        st.info("Calendar is empty. Add this week above.")

# ================= FACT BANK =================
elif page == "Fact Bank":
    st.header("Fact Bank")
    st.caption("One approved wording and one source per statistic. National findings are separate from state-specific rules.")
    for note in DATA["meta"].get("known_discrepancies", []):
        st.warning(note)
    c1, c2 = st.columns([2, 1])
    q = c1.text_input("Search")
    groups = ["All"] + sorted({f["_group"] for f in FACTS})
    g = c2.selectbox("Group", groups)
    for f in FACTS:
        if g != "All" and f["_group"] != g:
            continue
        blob = " ".join(str(v) for v in f.values()).lower()
        if q and q.lower() not in blob:
            continue
        with st.expander(f"{f['headline']}  \u2014  {f.get('pillar', f['_group'])}"):
            st.write(f["approved_statement"])
            st.caption(f"Source: {f.get('source','')}")
            st.caption(f"Template: {f.get('template_type','')}  |  Audience: {f.get('primary_audience','')}  |  CTA: {f.get('primary_cta','')}")
            if f.get("qualifier"): st.caption(f"Qualifier: {f['qualifier']}")
    st.download_button("Download fact_bank.json", json.dumps(DATA, indent=2),
                       "fact_bank.json", "application/json")

# ================= ATOMIZE =================
elif page == "Atomize":
    st.header("Atomize")
    st.caption("One approved fact, eight outputs. Edit before use.")
    fid = st.selectbox("Fact", [f["id"] for f in FACTS], format_func=lambda x: label(FACT_BY_ID[x]))
    f = norm(FACT_BY_ID[fid])
    outputs = atomize.all_formats(f)
    edited = {}
    tabs = st.tabs(list(outputs.keys()))
    for tab, (name, text) in zip(tabs, outputs.items()):
        with tab:
            edited[name] = st.text_area(name, text, height=220, key=f"atom_{name}")
    bundle = f"# Atomized content: {f['headline']}\nSource: {f['source']}\n\n" + \
             "\n\n".join(f"## {n}\n{t}" for n, t in edited.items())
    st.download_button("Download all as Markdown", bundle, f"atomized_{fid}.md", "text/markdown")

# ================= DESIGN STUDIO =================
elif page == "Design Studio":
    st.header("Design Studio")
    st.caption("On-brand graphics for Instagram, Facebook and LinkedIn. Rendered with the bundled brand fonts and logos.")
    fid = st.selectbox("Start from a fact", [f["id"] for f in FACTS], format_func=lambda x: label(FACT_BY_ID[x]))
    base = FACT_BY_ID[fid]
    families = ["BIG NUMBER", "MYTH / FACT", "STATE SPOTLIGHT", "ACCESS", "PARTNERSHIPS"]
    default_family = base.get("template_type", "BIG NUMBER").upper()
    default_family = default_family if default_family in families else "BIG NUMBER"

    c1, c2, c3 = st.columns(3)
    family = c1.selectbox("Template", families, index=families.index(default_family))
    theme = c2.selectbox("Theme", ["green", "light"])
    size_name = c3.selectbox("Size", list(brand.SIZES.keys()))

    st.subheader("Content")
    headline = st.text_input("Headline / big number", base.get("headline", ""))
    statement = st.text_area("Statement", base.get("approved_statement", ""), height=90)
    source = st.text_input("Source", base.get("source", ""))
    cta = st.text_input("Call to action", base.get("primary_cta", ""))
    qualifier = st.text_input("Qualifier", base.get("qualifier", ""))

    spec = {"template_type": family, "headline": headline, "statement": statement,
            "source": source, "cta": cta, "qualifier": qualifier, "theme": theme}

    if family == "MYTH / FACT":
        spec["myth_text"] = st.text_input("Myth text", "\u201cI need a lot of money to start.\u201d")
    if family in ("STATE SPOTLIGHT", "PARTNERSHIPS"):
        spec["state"] = st.text_input("State / band", base.get("state", "STATE SPOTLIGHT"))
        spec["program"] = st.text_input("Program", base.get("program", ""))
        up = st.file_uploader("Optional photo (rights must be clear)", type=["png", "jpg", "jpeg"])
        if up:
            from PIL import Image
            spec["photo"] = Image.open(up)
    if family == "ACCESS":
        st.caption("Three stats")
        nums = (base.get("headline", "").replace(" ", "").split("/") + ["", "", ""])[:3]
        labels_default = ["states report targeted rural outreach", "accept ITINs as account-owner ID", "provide plan info in Spanish"]
        stats = []
        for i in range(3):
            a, b = st.columns([1, 3])
            n = a.text_input(f"Number {i+1}", nums[i] if i < len(nums) else "", key=f"acc_n{i}")
            l = b.text_input(f"Label {i+1}", labels_default[i] if i < len(labels_default) else "", key=f"acc_l{i}")
            if n:
                stats.append({"num": n, "label": l})
        spec["stats"] = stats

    if st.button("Render", type="primary"):
        core = {"Instagram portrait (1080x1350)", "Instagram / Facebook square (1080x1080)", "LinkedIn (1200x627)"}
        chosen = st.session_state.get("export_all") and core or {size_name}
        for sn in ([size_name] if not st.session_state.get("export_all") else sorted(core)):
            spec["size"] = brand.SIZES[sn]
            img = render.render(dict(spec))
            buf = io.BytesIO(); img.save(buf, "PNG")
            st.image(img, caption=sn, width="stretch")
            st.download_button(f"Download PNG ({sn})", buf.getvalue(),
                               f"{fid}_{sn.split('(')[0].strip().replace(' ','_')}.png", "image/png",
                               key=f"dl_{sn}")
    st.checkbox("On next render, export IG portrait + square + LinkedIn at once", key="export_all")

# ================= CALENDAR =================
elif page == "Calendar":
    st.header("Calendar")
    st.caption("The living editorial calendar. Green / Amber / Red approval lanes. Edits save to the shared store.")
    with st.expander("Approval lanes"):
        for k, v in brand.LANES.items():
            st.write(f"**{k}** \u2014 {v}")
    cal = storage.load_df("calendar")
    edited = st.data_editor(cal, num_rows="dynamic", width="stretch",
        column_config={
            "approval_lane": st.column_config.SelectboxColumn(options=list(brand.LANES.keys())),
            "status": st.column_config.SelectboxColumn(options=["Planned", "Drafting", "In review", "Approved", "Scheduled", "Published"]),
            "channel": st.column_config.SelectboxColumn(options=["Instagram", "Facebook", "LinkedIn", "Other"]),
        })
    if st.button("Save calendar", type="primary"):
        st.success("Saved.") if storage.save_df("calendar", edited) else st.error("Save failed. See sidebar note.")

# ================= CAMPAIGN =================
elif page == "Campaign":
    st.header('Campaign: "A National Effort, State by State"')
    st.caption("The 12 findings, tracked over the 10 to 12 week franchise.")
    camp = storage.load_df("campaign")
    if camp.empty:
        rows = []
        for i, f in enumerate(DATA["campaign_findings"], 1):
            rows.append({"order": i, "fact_id": f["id"], "headline": f["headline"],
                         "approved_statement": f["approved_statement"], "status": "Not started",
                         "target_week": f"Week {min((i+1)//1, 12)}"})
        camp = pd.DataFrame(rows)
        storage.save_df("campaign", camp)
    done = (camp["status"] == "Published").sum() if "status" in camp else 0
    st.progress(done / max(len(camp), 1), text=f"{done} of {len(camp)} findings published")
    edited = st.data_editor(camp, num_rows="dynamic", width="stretch",
        column_config={"status": st.column_config.SelectboxColumn(
            options=["Not started", "Drafted", "Scheduled", "Published"])})
    if st.button("Save campaign", type="primary"):
        st.success("Saved.") if storage.save_df("campaign", edited) else st.error("Save failed.")
