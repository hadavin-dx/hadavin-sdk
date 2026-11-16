# v5-CHANGES: finding id | fixed where in CORE-PR-HANDOFF-v5.md | or why not

Nothing was run (design only). "Fixed" means the design now specifies it; it is verified only when the E0 evidence batch and the lead's EGM review exist. Section numbers are v5's.

## Security review of v4 (`review-handoff-v4-security.md`)
| Id | Fixed where | Note |
|---|---|---|
| B-1 NaN, infinity, negative amounts | 4.1 validation at `reserve_spend`, `finish_spend`, `add_spend`; `Money`, `Budget`, `Reply.cost_usd` types | E0-3, E0-7 fuzz |
| B-2 settle, release, keep not idempotent | 4.1 `spend_op` table, one `:final` key per reservation | replaces v4 "no store change" |
| B-3 window end tied to the stage rename | D1, 4.2, 4.5: rule spells no stage name | H-0 independent |
| B-4 extract sent unmasked documents | 4.7 masking before any call, strict UTF-8, `redact_untrusted` | PR-2 first |
| B-5 `Valid.mapping` could leak originals | 4.7 `storable` only, repr off, explicit `restore_kinds` | canary test on repr, asdict, JSON |
| M-1 refused reservation visible, crash gap | 4.1 single-transaction rollback; orphan view; `max_call_usd` (D19) | |
| M-2 wall card dedupe marked before delivery | 4.4 mark only after delivery (D13) | |
| M-3 eval spend memory store resets cap | 4.3 memory store refused for live eval | |
| M-4 release on every `ProviderError` | 4.1 outcome table, `ProviderRefused` | |
| M-5 runtime could lower totals | 4.1 refund bounded by own reservation, once; `Limits.correct` audited | grants do not enforce it: stated |
| M-6 key-file permissions | 4.8 | Windows rule stated |
| M-7 extract restore recipe | 4.7 BaseModel, `restore_value` types, kinds explicit | |
| M-8 PDF, image, bad encoding | 4.7, D22 | |
| M-9 masking may damage fields | 4.7, E0-10 | unmeasured until E0-10 |
| M-10 `tamper_evident` overclaim | 4.6 named bounded claims, ceiling constant | |
| N-1, N-2 nits | 4.7 (placeholder collisions via shared mapping), 4.4 wording | |

## Readiness review of v4 (`review-handoff-v4-readiness.md`)
| Id | Fixed where |
|---|---|
| R-M1 billed bad-body 200 released | 4.1 outcome table (keep) |
| R-M2 reserve ignores tools, schema, margin | 4.1 `worst_case_usd`, D20 |
| R-M3 CLI gate and eval ledger | 4.3 |
| R-M4 wall card, crash gap | 4.4, 4.1 |
| R-M5 judge swallows `SpendRefused` | 4.2 re-raise in `injection_check`, test through `qualify` |
| R-M6 extract contract | 4.7 |
| R-M7 G3 marker ambiguity | 4.9 compiled markers and scratch table |
| R-D1 placement and sequencing | D1, 4.2 census, section 6 (11 gating PRs, M2 split into a/b/c, G-W before G) |
| R-n* nits (docstring cites, `retain_days`, wording, gaps list) | sections 0, 1, 4.11, 9; v4's "the existing 7" corrected |

## Citation check (`citation-check-handoff-v4.md`)
| Id | Fixed where |
|---|---|
| X1 S3 docstring has no identity rights | D18 correction, 4.11 H-1 |
| X2-X9 wrong line cites | section 1 and designs re-cited; all 144 `file:line` cites re-opened for range, key ones for content (one tool-picked `tools.py` match was my checker's mistake; the cite is `src/hadavin_sdk/tools.py:361`, correct) |
| note retain_days default 1, 7 is a new floor | 4.11 H-1 |
| note CREDPAIR new label | 4.10 |

## Window-end audit and review
| Finding | Fixed where |
|---|---|
| Check in `NetworkLLM._retry` per attempt | 4.2 |
| `cli.py:150`, `:221-222`, direct `Runtime` bypass | 4.2 `build_llm`, gate on the kind, `Runtime` wraps |
| `app.py:90-98` accepts `llm=` live | 4.2 third refusal |
| No clock reaches `Limits` | 4.5 clock argument |
| `bedrock_guardrail.py:101`, `pipeline.py:155` | 4.2 census table |
| Stage field is dev/pilot/prod | D1, D6, F14 |
| `Limits.blocked` KeyError on made-up ids | 4.3, F5 |
| Day boundary | D1 (UTC date, last day allowed), D12 |

## Evidence (`evidence-handoff-v4.md`)
| Item | Fixed where |
|---|---|
| `git rebase -i HEAD~3` already withheld | 4.9, row G5b dropped |
| `KUBECTL.EXE delete ns prod` defanged by `channel.clean` | D21, 4.9 |
| G4 is a display filter only | F1, 4.9 |
| Other definite claims confirmed | kept (G2a, G2b, G3, G4a, G5a) |

## Coordinator messages
| Item | Fixed where |
|---|---|
| Q28: defaults ship; D5 OWNER-OPEN non-blocking; not on demo critical path | top of v5, D5, section 3 |
| Complete D1-D18 table, blocking vs non-blocking | section 3 (D1-D22 plus FA, RC) |

## Open, not fixed (and why)
| Item | Class |
|---|---|
| Provider billing a failed attempt | 2c third party; monthly invoice comparison, owner names the person by 2026-11-18 |
| D5 Decimal vs integers | 2b owner |
| D4, D18, D6 alias | 2b owner |
| Everything "unverified" | needs E0 run after build; no tests were run |
| Model-reply cache absence, Postgres behaviour, G5b other words, fence handling | not checked (section 0 item 3, section 9) |
