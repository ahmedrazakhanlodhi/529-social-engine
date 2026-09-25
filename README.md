# The 529 Network Content Hub

A lightweight internal content-operations system for The 529 Network. It turns the approved 2026 National 529 Survey fact bank into a repeatable workflow for planning, source control, approvals, channel adaptation, graphics, member amplification, and performance learning.

## What changed from the original Social Engine

The product is now organized around staff workflows rather than individual tools:

- **Home** — what is scheduled, what needs review, repetition warnings, campaign progress, and the recommended next action.
- **Plan** — deterministic weekly recommendations based on pillar balance, audience coverage, recent use, and approval status.
- **Content Library** — controlled Compendium facts plus new evergreen/timely content that can be added as Draft.
- **Create** — one approved item becomes channel copy plus branded graphics and a downloadable publication-ready ZIP.
- **Calendar** — content ideas are separated from channel executions using a shared `item_id`.
- **Approvals** — Draft → Fact checked → Communications review → Approved → Scheduled → Published.
- **Member Toolkits** — national copy, localizable placeholders, source notes, alt text, UTM template, and graphics.
- **Performance** — manual/CSV-friendly post-publication metrics and cautious early-signal analysis.
- **Settings** — cadence, recency window, active channels, owner, and pillar targets.

The app intentionally does **not** directly publish to social platforms. It focuses on everything before the publish button.

## Safety / source-control design

Bundled Compendium facts are imported as controlled approved copy. The deterministic atomizer preserves the factual statement verbatim and only adds creative framing around it. New content begins as Draft and is excluded from Smart Planner recommendations until approved.

The known `$439M` / `$413M` tax-savings discrepancy remains visible in the Content Library. The approved social wording is not silently reconciled or rewritten.

The **Fact Bank** now also carries national **Modern Record** trend facts (assets and accounts, 2001 to Q2 2026) drawn from the 529assets dataset, and **Design Studio / Create** can render an on-brand **TREND** area chart for them. National aggregates only, attributed to The 529 Network.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Password protection

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set:

```toml
app_password = "YOUR_PASSWORD"
```

If no password is configured, the app runs open for local/demo use.

## Persistence

Two backends are supported:

1. **Google Sheets** — durable shared storage when `gcp_service_account` and `sheet_id` are provided in Streamlit secrets.
2. **Local files** — zero-setup prototype storage under `data/`.

Local disk on Streamlit Community Cloud is ephemeral, so Google Sheets (or another durable backend later) should be used for actual shared team use.

## Google Sheets setup

Use the existing secrets pattern in `.streamlit/secrets.toml.example`. The app creates/uses worksheets named:

- `calendar`
- `campaign`
- `content_status`
- `custom_content`
- `performance`
- `settings`

## Content model

The bundled `fact_bank.json` remains the controlled Compendium source. Additional items are stored in `custom_content.csv` / the corresponding Google Sheet. Workflow metadata is stored separately, which means content governance does not require modifying the fact bank itself.

## Graphic templates

Supported families:

- BIG NUMBER
- MYTH / FACT
- STATE SPOTLIGHT
- ACCESS
- PEOPLE & PARTNERSHIPS
- EVENT / TIMELY
- SIMPLE EXPLAINER

Graphics are rendered in five sizes defined in `brand.py`. The app warns when text is too dense for mobile use. The distributable does not bundle font files; it uses common system fonts with a safe Pillow fallback.

## Testing performed in this build

The code was syntax-checked with `py_compile`. The renderer was exercised against all 19 bundled content items across all 5 supported image sizes (95 render combinations). Planner logic was tested against the existing calendar, including de-duplication and recency scoring. Storage schemas, campaign Week 1 initialization, fact-bank loading, content-status loading, and atomized factual-core preservation were also checked.

A live Streamlit browser session could not be executed in the build environment because Streamlit is not installed there and outbound package installation is disabled. The `requirements.txt` remains configured for a normal Streamlit deployment.
