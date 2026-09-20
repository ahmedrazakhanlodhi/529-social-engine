# Migration notes

The original app used calendar columns such as `fact_id`, `approval_lane`, and `status=Planned`. The upgraded app uses `content_id`, a content-level `item_id`, explicit workflow states, campaign/owner metadata, and separate content-status records.

`storage.py` can still read the original calendar/campaign shape and migrates it in memory. The bundled data files have already been migrated.

The 19 original Compendium facts remain in `fact_bank.json`; they were not rewritten. Workflow status is stored separately in `data/content_status.csv` (or the Google Sheet), preserving source content independently from operational metadata.
