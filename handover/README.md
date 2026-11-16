# handover/ (temporary folder; deleted before the final merge)

This folder exists only on branch `core/cloud-handover`. It gives the cloud Claude session everything the laptop session knows. Nothing here is reviewed code for the core; the code under `promotion-inputs/` is copied verbatim from the demos, Jagrat and Warden and must be rewritten and tested before it enters `src/`.

| Path | What it is |
|---|---|
| `CLOUD-PROMPT.md` | the prompt to paste into the cloud session |
| `STUDIO-RULES.md` | the rules the cloud session must follow |
| `TICKET-TEMPLATE.md` | one ticket per package |
| `MANIFEST.csv`, `MANIFEST-SUMMARY.md` | every copied file: source, commit, sha256, proposed target |
| `promotion-inputs/<source>/...` | verbatim copies (source files, their tests, pin files, licences) |
| `studio-notes/` | the plan, inventories, review reports, frozen redesign, course work packages |
| `STATUS.md`, `ledger.md`, `cloud-register.md`, `questions-for-lead.md`, `evidence/` | written by the cloud session |

Rules for this folder: not part of the Python package; not imported by any test; the repo tests that scan the whole tree (`test_no_reference_material`) must stay green, so no banned vendor-inspired strings in any file here.
