# Changelog — Content Hub upgrade

## Product / UX
- Renamed the internal concept from **529 Social Engine** to **The 529 Network Content Hub**.
- Reorganized navigation around staff workflow: Home, Plan, Content Library, Create, Calendar, Approvals, Member Toolkits, Performance, Settings.
- Simplified visual styling and reduced dashboard/card clutter.

## Planning
- Replaced passive three-fact selection with a deterministic **Smart Weekly Planner**.
- Recommendations consider pillar target gap, recent use, audience coverage, format variety, campaign relevance, sourcing, and approval status.
- Added plain-English “why this was recommended” explanations.
- Added repetition warnings.
- Corrected strategic balance to count unique content ideas, not every channel execution.

## Content governance
- Added workflow states: Draft, Fact checked, Communications review, Approved, Scheduled, Published, Archived, Retired.
- Added reviewer/approver metadata and dates.
- Bundled fact-bank wording remains controlled; new library items start Draft.
- Added deterministic source/qualifier/CTA/content-length checks.

## Creation / graphics
- Expanded atomization to channel-specific LinkedIn, Instagram, Facebook, short-form, carousel, video, web/newsletter, email, member toolkit, and alt text outputs.
- Added publication-ready ZIP export containing copy, source-control note, and three core graphics.
- Added a dedicated **PEOPLE & PARTNERSHIPS** rendering path rather than fallback behavior.
- Added mobile-density, missing-source, CTA, alt-text, and photo-rights warnings.

## Member amplification
- Added a dedicated Member Toolkits page.
- Packages include national copy, localizable placeholders, source note, alt text, UTM template, posting window, and core graphics.
- State-specific placeholders remain intentionally blank unless verified.

## Campaigns / calendar
- Generalized campaign storage schema.
- Fixed campaign initialization so the first Compendium item is **Week 1**, not Week 2.
- Added `item_id` so one story distributed to several platforms remains one strategic content idea.
- Migrated the bundled sample calendar to the new schema.

## Performance
- Added a performance tracker for impressions, reach, engagements, clicks, shares, saves, comments, video views, member reposts, and website sessions.
- Added cautious early-signal analysis with an “insufficient data” threshold.

## Storage / engineering
- Centralized data schemas in `storage.py`.
- Added backward-compatible migration for the original calendar/campaign files.
- Added configurable settings persistence.
- Added modules for planning, quality control, and content operations.

## Post-review hardening (verified running)

- Ran the app end to end (all nine pages boot, 95/95 renders, write paths exercised); the prior build could not run Streamlit in its environment.
- Storage: audit log is now append-only, so a concurrent save no longer clobbers audit history. Added a "last saved" stamp in the sidebar.
- Added full Backup and restore in Settings: one-click ZIP of every table plus settings and the fact bank, and restore from that ZIP. Mitigates ephemeral local storage until Google Sheets is configured.
- Settings now hold plan-finder, report, and employer URLs. Generated copy turns the call to action into a real UTM-tagged link when a URL exists, and stays plain text (no dead placeholder) when it does not.
- Renderer: content is vertically balanced instead of top-heavy, and every data card carries a small bottom source line for provenance.
- Home surfaces the source-control decisions from the fact bank (for example the $439M topline).
