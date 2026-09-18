# The 529 Network Social Engine

Operational tool for running the Social Media Revamp Strategy. It holds the
strategy's rules and the approved Compendium fact bank, and turns one finding
into planned posts, eight text formats, and on-brand graphics for Instagram,
Facebook and LinkedIn.

## What it does
- **This Week** — pick three anchor stories on the Mon / Wed / Fri cadence, assign
  channels, and see the monthly feed balance against the five-pillar targets.
- **Fact Bank** — the approved wording and source for every statistic. One number,
  one wording, one source. Search and download.
- **Atomize** — one fact into eight outputs (IG carousel, Reel script, LinkedIn,
  Facebook, blog stub, member toolkit, email, alt text) using HOOK -> VALUE ->
  PROOF -> NEXT STEP. Editable, then download as Markdown.
- **Design Studio** — render BIG NUMBER, MYTH / FACT, STATE SPOTLIGHT, ACCESS and
  PARTNERSHIPS cards at IG (1080x1350, 1080x1080), Facebook and LinkedIn (1200x627)
  sizes. Bundled brand fonts and logos. Download PNG.
- **Calendar** — the living editorial calendar with Green / Amber / Red approval
  lanes. Saves to the shared store.
- **Campaign** — the 12-finding "A National Effort, State by State" tracker.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Deploy on Streamlit Community Cloud
1. Push this folder to a GitHub repo (your `ahmedrazakhanlodhi` account).
2. On share.streamlit.io, create an app pointing at `app.py`.
3. Open **Settings -> Secrets** and paste from `.streamlit/secrets.toml.example`:
   - `app_password` to lock it to you and Catherine.
   - `sheet_id` + `[gcp_service_account]` to switch storage from local CSV to a
     shared Google Sheet. Share the Sheet with the service account `client_email`
     first. The app creates `calendar` and `campaign` worksheets on first save.

## Notes
- No browser or system binaries are used for rendering, so no Playwright install
  step. This avoids the Community Cloud install hangs seen with Chromium.
- The gold accent (`COLORS["gold"]` in `brand.py`) is the one unconfirmed brand
  value. Change it in one place.
- The fact bank is `fact_bank.json`. Editing wording is a one-field change and the
  whole app reads from it.
