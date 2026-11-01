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

## Limits and trust (K5 read tools)

- A tool module is code in the SDK process. `tool_module_hashes` pins its source (checked before import); review it like the release. The box defends against a misbehaving model, not a hostile tool author.
- `scope_inventory` entries are operator attestations: format-checked and logged, not verified against the page.
- Redaction is pattern-based: it finds the kinds it knows (addresses, ARNs, keys, tokens) in the original, canonical (NFKC, invisible characters removed) and JSON-unescaped forms of a string. A secret in a shape it does not know passes; the per-kind allowlist grammars keep unknown shapes out of the stored map.
- `caught_by` counts only controls that stopped a proposal; failures are not catches.
- A hold on a run is not retroactive, and no hold outlives 400 days.
- Kubernetes is the only built read-source kind; a second one is an SDK edit (trigger K5-ITO).

## Licence

Proprietary. Copyright (c) 2026 Hadavin. All rights reserved. See [LICENSE](LICENSE). Viewing this repository
does not grant any licence to use it.

## Security

See [SECURITY.md](SECURITY.md).
