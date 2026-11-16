# Independent check of CORE-PR-HANDOFF-v10.md and -other-tracks.md (EVIDENCE RUNNER, no judging)
Date 2026-11-16 (UTC). Read-only on src/tests/inputs. Did not read evidence-handoff-v10/ output. Scripts and raw output are in this folder.

## Failures and mismatches first
| # | Claim (where) | Checked value | Match |
|---|---|---|---|
| 1 | E0-S1-1 row, v10 line 294: gate4.sh runs "the exact commands of ci.yml" | gate4.sh uses `ruff check` and `ruff format --check` with no paths, plain `pytest` (no `-m "not live and not perf"`), and `bandit -q -r src demos -ll`. ci.yml uses `ruff check src tests demos`, `ruff format --check src tests demos`, `pytest -q -m "not live and not perf" -rs`. So the commands differ, and gate4 would also run `live` and `perf` tests | NO |
| 2 | 8.1 under counting B, text says llm.spend and llm.callgate join the existing llm cycle "through the package, not through any new edge" | B run+type today: group of 9 (config, deferred, guard.judge, llm, llm.common, llm.fake, llm.retry, registry, replay_records). With the planned table: group of 16, which also pulls in guard, guard.http, guard.injection, guard.runmap and tools. The single planned edge `guard.injection -> llm.protocol` (run) is enough to merge the guard group (3) into it (raw-merge-probe.txt) | NO (text understates) |
| 3 | 8.1 text vs its own parents raw file (raw-import-graph-v10-parents.txt) | My B result above differs from the text's description of the group. Not re-derived from the author's file because I did not read it | see 2 |
| 4 | v10 line 17: `llm/retry.py` 20-110 read | retry.py has 108 lines | NO |
| 5 | v10 lines 188-189 cites to guard/injection.py 239-250, 421, 318-322 | my resolver attached bare `:N` continuations to injection.py (101 lines). Manual check: they point at redact.py and the lines are right there | resolver artefact, doc OK |
| 6 | other-tracks line 129: tests/warden_port/test_redaction.py:513 | file has 456 lines; other-tracks line 128 context is also a continuation misattribution. Manual check done, see note | doc OK after manual check (low confidence, recheck) |
| 7 | `app.py:160` | the statement is at line 161 | NO (off by one) |
| 8 | F16: assign sites of `.detector =` / `.llm =` after build | a fifth site exists at tests/test_p6_detectors.py:186 | NO (omitted) |
| 9 | `_limits_stop` call sites | also called at runtime/agent_loop.py:460 | NO (omitted) |
| 10 | "seven PRs" (v10 line 346; other-tracks line 3) | the PR table in v7 lists 12 rows; 7 without spend content are rows 8-12 plus... the ids total 9 in the list I counted | NO / unclear |

## Matches
| Claim group | Checked value | Match |
|---|---|---|
| File:line citations | 327 extracted, 322 in range, 5 out of range (rows 4-6 above, resolver artefacts included) | yes except above |
| Fact claims F1-F16, O-2, O-4.6 to O-4.11, O-6, O-7 (claims_check.py) | 240 checked, 232 pass; the 8 flagged (S5.9a, S6b, O26, O52, O53, O54, O55, O82) are my own regex or range slips; for O26, O52-O55 and O82 I read the lines by hand and the doc is right. S6b: my range 1-5 exceeds the 4-line file, not a doc cite | yes |
| Python fence at v10 line 133 (`_retry`) | compiles (module level) | yes |
| Bash fences | none found | n/a |
| Counting A, run only | 0 cycles today and with planned edges | yes |
| Counting A, run+type | 3 groups (4, 3, 3), unchanged by planned edges; the 4-group is config, deferred, registry, replay_records | yes |
| Counting B, run only | 4 groups of sizes 3, 3, 2, 2, unchanged by planned edges | yes |
| Number of modules | 102 | n/a |

## Not checked
- Live tests, mutation runs and the CI suite were not run (nothing paid, read only).
- The migration guard on the 0006 SQL (not written yet in the tree).
- `bedrock_guardrail` full-Config sites, only sampled.
- The author's raw files, by instruction.
- Row 10 count of PR ids needs a second look by a person.
- Whether the design is right (not my job).
