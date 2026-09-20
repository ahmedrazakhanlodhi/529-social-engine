# Test report

## Passed

- Python syntax compilation (`py_compile`) for all application modules.
- Fact-bank load: 19 controlled Compendium content records.
- Workflow-status load: 19 imported controlled records marked Approved.
- Calendar migration/schema: 6 channel executions correctly resolve to 3 unique content ideas.
- Campaign initialization: first item is correctly `Week 1`.
- Smart Planner: returns three distinct recommendations and avoids the repeatedly scheduled `$275M` item within the configured 21-day recency window.
- Repetition detector: flags the existing repeated `$275M` scheduling pattern.
- Content mix vs. channel mix: 3 unique content ideas vs. 6 executions in the bundled sample calendar.
- Atomization: approved factual core remains verbatim in LinkedIn, Instagram, and Facebook outputs.
- Renderer: all 19 bundled content items rendered successfully across all 5 supported sizes = **95 render combinations**.
- Dedicated People & Partnerships template path renders successfully.
- Quality checks flag missing sources and missing CTA/alt-text/photo-rights conditions.

## Environment limitation

A live Streamlit browser session was not run in the build container because Streamlit is not installed in that environment and outbound package installation is blocked. The application is syntax-valid and the non-UI logic/rendering tests above passed. `requirements.txt` remains configured for normal deployment with Streamlit.
