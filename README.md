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

- A tool module is code in the SDK process. `tool_module_hashes` pins its source and its parent packages' `__init__.py` (checked before import, and the hashed bytes are what runs). A pinned module may not use relative imports and its parent `__init__.py` may not hold code; both are refused. NOT covered by the pin: absolute imports of other project modules, data files and the standard library. A module already loaded under other bytes is refused (restart the process after changing a pinned module). The import check refuses by name anything that can load code from elsewhere; it is best effort, not a sandbox (a meta-path finder restricted to the pin would be the sound fix). Review a tool module like the release. The box defends against a misbehaving model, not a hostile tool author.
- `scope_inventory` entries are operator attestations: format-checked and logged, not verified against the page.
- Redaction is pattern-based: it finds the kinds it knows (addresses, ARNs, keys, tokens) in the original, canonical (NFKC, invisible characters removed) and JSON-unescaped forms of a string. A secret in a shape it does not know passes; the per-kind allowlist grammars keep unknown shapes out of the stored map. It does not decode base64 or URL-encoded client PII, does not join a secret split across two results, and does not strip combining marks. Result markers and placeholder look-alikes are escaped in every decoded view, so a returned text is never a decoded view that was not escaped.
- `caught_by=guard` is set when a guard stopped a concrete proposal (ungrounded, uncited, invalid_proposal, run_budget, injection_suspected); failures (tool, redaction, evidence, a guard outage, the provider) are not catches.
- The fetch layer resolves a host once, refuses loopback, link-local (the cloud metadata address), unspecified, multicast and reserved answers, and connects to the checked address, so a DNS answer that changes between the check and the connect cannot reach the socket. Private ranges are allowed (in-cluster services live there). K7's network policy stays the backstop and is a hard prerequisite before any pilot.
- Grounding is a whole-token match, exact in case. A proposal may name the front of a longer name only where the tool's manifest declares a `generated_suffix`; case is folded only for a `target_system` listed in `evidence.case_insensitive_targets`.
- Load on a client system: at most `max_concurrent_tool_calls` reads at once and `max_tool_calls_per_minute` per minute per process, plus the per-run caps; every read is an audit event (principal, tool, `inputs_hash`, `output_hash`, `rows`) and a `tool_calls` row a client can review. Nothing of one client is kept in a process-global cache.
- Tools never go through an environment proxy (it would resolve the target itself, skipping the address check); the LLM clients and the executor may. A source whose scope probe fails on the tick is switched off until a probe passes again.
- Redaction work is bounded: patterns are linear or bounded, the document is capped (`evidence.max_document_bytes`, 256 KiB) and tool results are cut before redaction. A command-line credential flag more than 1024 characters after its command word on one line relies on the key=value and long-token patterns.
- Evidence is deleted only by the purge role (`migrate --purge-role`, `backends.store.purge_dsn_secret_name`); the runtime role cannot.
- A tooled agent's action contracts must set `additionalProperties: false`; an undeclared input is refused as `invalid_proposal`.
- The purge step is due 60 s early by design (`max(every - 60, every // 2)`, `TICK_SLACK_S`) so a tick every 30-60 s does not stretch the cadence; a failed purge is retried at the next tick.
- A hold on a run is not retroactive, and no hold outlives 400 days.
- Kubernetes is the only built read-source kind; a second one is an SDK edit (trigger K5-ITO).

## Licence

Proprietary. Copyright (c) 2026 Hadavin. All rights reserved. See [LICENSE](LICENSE). Viewing this repository
does not grant any licence to use it.

## Security

See [SECURITY.md](SECURITY.md).
