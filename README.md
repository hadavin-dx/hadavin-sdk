# hadavin-sdk

Shared building blocks for Hadavin's fixed-price AI builds, and the demo builds that use them.

| Folder | What it holds |
|---|---|
| `src/hadavin_sdk/` | The reusable core: one interface per capability, with backends chosen per client in config |
| `demos/` | Demo builds on the core (invoice & PO automation, document Q&A) |
| `tests/` | Tests for the core and the repository rules |

Rules:
- The core never imports anything from `demos/` (a test enforces it), so a client delivery can take the core alone.
- Demo data is synthetic only. No client data, secrets, account ids or personal details are ever committed.

## K1b-lite: replay check (report only)

`hadavin-sdk replay AGENT --bundles D --cause-list D --max-usd X --out OUT [--k K]` runs a client's recorded
incidents through an agent; `hadavin-sdk score --outputs OUT --answers F --cause-list D --bundles D` counts the
results into `OUT/score/score-report.md`. Neither gives a verdict, and a replay pass is not evidence of live accuracy.
`replay` refuses a non-empty `OUT`. If a replay dies half-way it leaves `FAILED.txt` in `OUT`: delete the folder to
re-run. `score` refuses an `OUT` holding `FAILED.txt`, and a non-empty `OUT/score/`. A `score_run` audit event does not prove a report file exists (events are written first).

## Licence

Proprietary. Copyright (c) 2026 Hadavin. All rights reserved. See [LICENSE](LICENSE). Viewing this repository
does not grant any licence to use it.

## Security

See [SECURITY.md](SECURITY.md).
