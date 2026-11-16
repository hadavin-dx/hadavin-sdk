# v7 changes: where each v6 finding went (2026-11-16 UTC / IST)

Nothing was run except file reads, one import-graph program and one banned-word count (hand-off section 0). Every "fixed" below means "the design text now says it"; nothing is verified until the E0 items run. Section numbers are those of `CORE-PR-HANDOFF-v7.md`.

## Security review of v6 (5 majors, 7 nits)
| Id | Finding in one line | Where fixed in v7 | Note |
|---|---|---|---|
| S-M1 | One reservation settled for two answered attempts (OpenAI-compatible two loops), numbering unspecified | 4.1 "What a reservation covers", 4.2 `CallBook` and `_retry` closure | each answered attempt settles from its own answer; one counter per `CallBook`; two-request test and attempt census in 4.2 |
| S-M2 | Kept reservations can never be corrected | 4.1 `spend_adjust` table, trigger, adjust role; 4.3 `limits correct`; 6 (M2a) | relief before M2a, not a floor estimate (reason in 4.1) |
| S-M3 | Gate from another meter accepted; `MeteredLLM` reserves 0 in live; non-network object with inner retries | 4.2 live-stage rules (`llm.gate is limits.meter.gate`, `MeteredLLM` refused in live, covers one attempt); section 5 negative test 13 | |
| S-M4 | Under-reported cost: input-only floor, trust in usage | 4.1 "Unknown usage, the floor, and the output bound"; `Reply.usage_estimated` | floor guards against zero or missing usage only; stated |
| S-M5 | Over-claims about a compromised runtime and "no client can skip it" | section 0 items 2(g), 5, 8; section 5 reworded paragraph | provider-side limit and invoice comparison are required controls with owner and date |
| S-N1 | D5 default contradicts "money is integers"; owner-must-answer vs default-ships | D5 (section 3), 4.1 money unit | nano-dollar `BIGINT` default; one exact question; "lead decision" |
| S-N2 | `hashtextextended` is internal | 4.1 serialising reservers (blake2b key in Python) | |
| S-N3 | Autocommit and READ COMMITTED | 4.1 (cites `store/postgres.py:146`), E0-3 `SHOW transaction_isolation` | |
| S-N4 | `finish_spend` order, update `runs` only if applied, late log | 4.1 `finish_spend` steps 1 to 4 | |
| S-N5 | `max_call_usd` global | D19, 4.5 | per agent, `daily / 4`, zero reserve never refused |
| S-N6 | Two UTC date helpers | 4.2 table (`models.utc_day`), 4.5 | |
| S-N7 | Nested scopes; run cap inflates K6 "caught" | 4.2 nested-scope refusal; 4.4 new code `run_budget_reserve` in `POLICY_STOP_REASONS` | |

## Implementation-readiness review of v6 (2 blockers, 11 majors, nits)
| Id | Finding | Where fixed | Note |
|---|---|---|---|
| R-B1 | Pure types had no home; import cycle gate and common | 4.2 module-home table; 6 (new PR M2-0); E0-12 | program output quoted; runner repeats it |
| R-B2 | Double booking in the two-loop kind; attempt numbering | 4.1, 4.2 (same fix as S-M1) | |
| R-M1 | Trigger body missing | 4.1 SQL text and decision table | specified, unverified; Postgres not run |
| R-M2 | `MeteredLLM` breaks `rt.llm.calls` | 4.2 (`self.llm` raw, `_chat_llm`, `__getattr__`) | |
| R-M3 | Judge's llm unwrapped; detectors need `gate=` | 4.2 (`app.build` wraps once, census of `make("detector"`) | |
| R-M4 | Floor not computable by `MeteredLLM`; `test_k5_run_budget_stops_run` | 4.1 and 4.2 (floor and keep-on-unknown for network kinds only) | |
| R-M5 | No `ts` argument | 4.1 store methods all take `ts` | |
| R-M6 | `SpendRefused` handling at k1b, extract, guardrail | 4.2 site-by-site table | |
| R-M7 | App and CLI edits unassigned; interim state | 4.2 edit table, interim paragraph; 6 | M2b, M2c, M3 merged as one train |
| R-M8 | Wrong test list, dict config, others | 4.2 test list, 4.5 | k1b replay test removed from the list |
| R-M9 | E0 items not runnable | section 7 | command, output, pass rule, or "builder writes it in PR X" |
| R-M10 | `Config.spend` cannot import `Budget` | 4.3 field table | |
| R-M11 | `run_id` NULL in `finish_spend` | 4.1 step 4 | |
| R-nits | `SpendMeter` signature; hook naming; `UnknownReservation` home; `correct` needs exactly one selector; `max_call_usd` checked once; UTC helper; `checkpoint_every` class; keyword-only `gate=` | 4.1, 4.2, 4.3, 4.6 | `ChainSettings` is `backends/table.py:192-193` |
| R-0006 | Migration plumbing | 4.1 grants paragraph | adjust role added |

## Citation check of v6 (4 wrong, 6 partly right)
| Row | Fixed to | Where |
|---|---|---|
| 1 | `except ProviderError` is inside the tuple at `agent_loop.py:432-434` | cited in 4.4 and facts |
| 2 | `extract.py:58` | 4.7 |
| 3 | `_FILE` is `migrate.py:71` | F21 |
| 4 | `FakeLLM.calls`; `everything_sent()` belongs to `ScriptLLM` (`k5_support.py:124`, `:156`) | F10, 4.7 |
| 5 | recording key only when documents exist | F10, 4.7 |
| 6 | corrected file and line list | 4.2 test list, 4.5 |
| 7 | `verify_rows` `chain.py:363-383` | F11 |
| 8 | `detail()` `:93-101`, `retryable()` `:104-110` | F6 |
| 9 | `build_runtime` `:160-211` | F8, 4.2 |
| 10 | `anchor_s3.py:1-12` states one constraint at `:5-7`, no actions | D18, 4.11 |
| 11 | D5 versus Q28: intentional disagreement, stated | section 0 intro, D5 |
Also fixed: `load_config` wrapper `config.py:451-454` (F14, 4.5, 4.11); `k1b/replay.py:85-91` (D11).

## Not fixed in v7 (need the lead, the owner or a third party)
- The two controls of section 0 item 5 (person's name by 2026-11-18, limit figure, hard stop or alert only): owner.
- D5: default applied; the lead's exact question is in section 3.
- Inputs the repository lacks (E0-5 recorded replies with real usage, E0-6 200 sentences, E0-9 golden set): named in section 7 with who supplies each.
