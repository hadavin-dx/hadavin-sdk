# Resolve log: CORE-PR-HANDOFF.md to CORE-PR-HANDOFF-v2.md (2026-11-16, builder)

Status of each review finding. "Fixed" means the text in v2 answers it; nothing was run (see v2 section 0).

## READY (review-handoff-readiness.md)
| # | Sev | Resolution | Where in v2 |
|---|---|---|---|
| 1 | Blocker RD-1.1 | Fixed: signature, map source, bytes/str, `redact_text` for replayed assistant text, fail-closed DeadLetter, tests, recordings | 5.1 |
| 2 | Blocker SG-B2 | Fixed: reserve policy (shared worst_case, input estimate + max_tokens x price), first-call-over-cap rule, expected call count 1 on a named route | 5.4 |
| 3 | Major SG-B3/SV-G | Fixed: `book_cost`, `reserve_spend`, `settle_spend` names, signatures, refusal codes, release rules, two-thread test on both stores via the shared contract test | 5.3, 5.4 |
| 4 | Major G4-B1/D2 | Fixed: B1a wording PR first (G1), B1b shapes later, separating rule for `rm x` vs `rm the file` | 4 (PR-G1, G4), D2 |
| 5 | Major G4-B2/M5/M10 | Partly: continuation join before tokenising specified (PR-G2); inversion false-positive budget defined (section 6). Lists `_NAMES` and `_ENGLISH` are not re-specified because I did not open `gate.py` beyond the header (UNVERIFIED) | 6 |
| 6 | Major M6/M7/M8/M4 | Fixed with defaults: D13 retry policy, D12 timezone default UTC, D10 no new alert kind (F5 verified none exists), D11 zero-price flag and fixtures (F6: none affected) | 3 |
| 7 | Major SA-3.1/3.2 | Fixed: field names, wording, exit codes unchanged, the `:520` test named (F12) | 5.5 |
| 8 | Major SA-3.3/3.5/3.4/3.6 | Partly: PR assignment, S3 probe absence verified (F13), policy text outline 5.6. `anchors.collect` exact signature left to the builder (listing in, `dict[int, tuple[str, str]]` out, error on name mismatch or duplicate): stated in PR-D2 by reference only. Postgres negative tests UNVERIFIED | 4, 5.6 |
| 9 | Major SA-1.2 | Fixed: neutral shared reader `fileguard.py`, symlink and mode checks every stage, test-key mode handled | 5.7 |
| 10 | Major D6 | Fixed: real size verified (F11): 2 src lines and 3 test sites; READY's 26 hits were dataset split names | F11, PR-0 |
| 11 | Minor SG-M5 | Fixed: NaN settled by running a Decimal field; cross-field check goes in `registry.Budget` validator | F10, PR-M1 |
| 12 | Minor SG-B1/D1 | Fixed: field name, place (global `Config`), no clock test | 5.2 |
| 13 | Minor PR split | Fixed: seam first, RD-1.1 second, slow marker is `perf` (F7), D7 removed | 4 |
| 14 | Minor not-checked lists | Fixed: callers of charge/blocked/add_spend (F9), retry.py (F8), alert kind (F5); channel.py read for wording | 1 |

## ZOOM (review-handoff-zoomout.md)
| # | Sev | Resolution |
|---|---|---|
| 1 | Blocker D1 | Fixed: default Blocker, PR-M1, required for non-fake llm |
| 2 | Blocker PR-B split | Fixed: M1 validation, M2 ledger, M3 reserve, M4 timezone, M5 calls cap; SV-D in M2; test rewrites need D9 |
| 3 | Major alert | Fixed: log + audit + card now, kind later (D10) |
| 4 | Major zero price | Fixed: D11 flag, self-hosted only |
| 5 | Major PR-A bundle | Fixed: PR-1 seam, PR-2 masking, PR-3 errors |
| 6 | Major RD-1.1 premise | Fixed: F1, F2 verified; producers.py row reworded in PR-2 |
| 7 | Major PR-F grab-bag | Fixed: R1 to R4 by pattern family, runtime-path JSON pair first (R2) |
| 8 | Major G4 scope | Fixed: G1 to G5 with item lists and a false-positive budget |
| 9 | Major round cap | Fixed: per-PR status, PR-D* uncapped |
| 10 | Major D2 lines | Fixed: gate.py:4, 366-377, channel.py:20-21; grep of docs and README found nothing else |
| 11 | Major dropped items | Fixed: section 8 table; test 8 and 9 assigned; demos pipeline assigned but not opened |
| 12 | Major PR-D size | Fixed: D1 wording, D2 names, D3 re-anchor, D4 config floor, D5 outbox, D6 identity |
| 13 | Major stage policy | Fixed: D6 decided once, PR-0 first |
| Decisions | D1-D8 | Rewritten, D7 and D8 removed as not decisions, added D9 to D14 |
| Missing step | evidence batch | Section 7 (E0) |

## Not fixed, with reason
- G4 behaviour claims and regex claims: cannot run here (missing `markdown_it`); handled by E0.
- D5 integer money and D4 refuse-`none`: owner-only (exception 2b), dated 2026-11-16.
- Process-crash-between-reserve-and-settle over-count: no safe sweep rule without per-call ids; stated in 5.4 as a design choice for the lead.
- Per-attempt retry billing needs adapter bodies not read; the PR-M2 builder must read them.
