# Independent citation check of hand-off v12 (EVIDENCE RUNNER output: facts only, no verdict)

Tree: live `/home/user/hadavin-sdk`, branch `cloud/core-hardening`, HEAD `2cda4bba0`. Documents: `CORE-PR-HANDOFF-v12.md` (443 lines) and `CORE-PR-HANDOFF-v12-other-tracks.md` (205 lines). Nothing was run except my own read-only Python programs (own code, `python -I`) and one `bash -n`. No pytest, no repo code, no network, no spend. Files in this folder: `cites-table.tsv` (2,833 rows), `r2_cites.py`, `r2_finalize.py`, `r2_graph.py`, `raw-graph-live.txt`, `raw-gate4.txt`.

## What did not hold, and what I did not check (first)

1. **LINE-OFF: 0. MISSING among real code cites (class A): 0.** This is AFTER my hand review. My first program flagged 39 class-A cites (21 LINE-OFF, 18 MISSING) because its "anchor word" heuristic picks the wrong word (a class name for a line inside it, a symbol the design only proposes, a bold word). I opened the cited lines of all 39 (`cites-table.tsv` column `first_pass_status`, note "heuristic flag") and each holds what the claim names. The heuristic's verdict is therefore not independent for those 38; my reading is.
2. **Weak coverage (be sure to read this).** Of the 389 class-A rows, only 86 were checked by an anchor word inside the cited range (72 exact, 14 from the wider sentence). 264 are `range-only`: the file exists and the line range lies inside it, nothing more. I skimmed the first line of every one of the 264 against the claim sentence (no mismatch seen), but that is a human skim, not a program check.
3. **13 evidence names in section 8 of the main document and 1 in other-tracks are absent from `evidence-handoff-v12/`** (the document says "Evidence saved this pass"): `raw-greps-v12.txt` (also cited at line 102), `import_graph_v12.py`, `raw-import-graph-v12.txt`, `raw-import-graph-v12-parents.txt`, `cite_check_v12.py`, `snippet_check_v12.py`, `banned_count_v12.py`, `cycles_v12_from_independent.py`, `merge_probe_v12.py`, `raw-merge-probe-v12.txt`, `raw-cite-check-v12*.txt` (glob; no file), and in other-tracks line 205 `raw-cite-check-v12-other.txt`. The folder holds the `_v11` copies (`import_graph_v11.py`, `cite_check_v11.py`, `snippet_check_v11.py`, `banned_count_v11.py`, `cycles_v11_from_independent.py`, `merge_probe_v11.py`) and `raw-banned-v12.txt`, `raw-cites-v12.txt`, `raw-counts-v12.txt`, `raw-cycles-v12-independent-script.txt`, `raw-fences-v12.txt`, `raw-gate4-*.txt`, `raw-snippets-v12.txt`. Either the files were not saved or were not renamed; the document may have been written before the folder was finished (git log says "wip").
4. **Present tense for something that does not exist:** main doc E0-S2-4 says "Bedrock: `status_of` reads that key, `llm/bedrock.py:108`". `status_of` is not in the tree; the key `ResponseMetadata.HTTPStatusCode` is read at `llm/bedrock.py:108` by `retryable()`. The cite is right, the symbol is a proposed hook.
5. **Count not reproduced:** "which of the 38 test hits pass a `NetworkLLM` into `app.build`" (main doc section 10). My own grep of `build(` lines with `llm` in `tests/` gives 18 to 19; the method of the 38 is not stated. AMBIGUOUS, not wrong.
6. **Not checked:** the planned cycle group of 10 modules and the "11 / 10 by parent package, planned the same" (they need the planned-edge table merged into a graph; I only recomputed today's graph). Every Postgres, vendor and CI-run claim (nothing can be checked offline). Whether the 340 proposed symbol names are all really "new in this design" (I did not read each sentence; they are simply absent from the tree). The `ci.yml` run steps beyond the lines cited. Content of the `v12-CHANGES.md` file.

## Counts by status (`cites-table.tsv`)

| Class | MATCH | LINE-OFF | MISSING | AMBIGUOUS | Total |
|---|---|---|---|---|---|
| A: real code cites (path:N, path:N-M, `path` N-M in prose, `path` line N) | 388 | 0 | 0 | 1 | 389 |
| B: prose words in backticks (symbols, files, folders, commands) | 878 | 0 | 503 | 1,063 | 2,444 |
| All | 1,266 | 0 | 503 | 1,064 | 2,833 |

Class A detail: 354 `path:N` rows, 34 prose-range rows, 1 bare `:N` that is not a continuation. That one is the document's own format example (`path:1, :2` at main line 5), not a cite: AMBIGUOUS. So the claim "every `:N` has its path or follows a cite of the same file" holds on this tree. How verified: 232 + 32 range-only, 72 anchor exact, 14 anchor wide-sentence, 38 hand-opened.

Class B MISSING (503), by what I can tell:
- 67 planned-new files and folders (modules, tests, `E0-*.txt` outputs, `.github/CODEOWNERS`, `migrations_held/`); the design says they do not exist yet.
- 14 evidence names the document says are saved but are not in the folder (item 3 above; 13 main + 1 other-tracks).
- 421 symbols absent from `src`, `tests`, `demos`, `.github` (349 whole absent, 72 where only part of a dotted or call form is absent). These are almost all names the spend design proposes (`SpendRefused`, `CallGate`, `booked_usd`, `scope_missing`, `ProcessCap`, ...). Present-tense exceptions I read: `status_of` (item 4). Other names that read as existing but are not in the tree: `restore_kinds`, `hash_chain_ok`, `anchored_checkpoints`, `anchor_supplied`, `signing_key_location`, `masking_damage` (these look like other-tracks proposals; I did not confirm each sentence).
- 1 `CallGate.admit/settle/keep` (a slash list, not a symbol) and 1 `audit/signer.build_local` (a module.function written with a slash; `build_local` exists at `audit/signer.py:96`).
- Class B AMBIGUOUS 1,063: 1,046 are not code (words, values, commands, ids such as `E0-S1-4`, config values) and 17 are bare file names that match several files (for example `gate4.sh` has copies in three evidence folders).

## Prose-word backticks vs real code cites (counted separately)

Real code cites: 389 rows. Prose backtick spans (all other backticks): 2,444 rows; of these 878 resolve to a file, folder or symbol that exists.

## Counts checked against the live tree

| Claim | Found | Status |
|---|---|---|
| 5 `.chat(` call sites in `src/` (F8) | `extract.py:47`, `evals.py:73`, `guard/judge.py:72`, `runtime/agent_loop.py:425`, `k1b/loop.py:94` (one more hit is a docstring in `guard/producers.py:5`) | MATCH |
| `Limits(` at 7 test sites (F16) | `test_k5_round5.py:241`, `k5_support.py:206`, `test_k5_postgres.py:58`, `test_k5_tools.py:1133` and `:1269`, `test_k3_pilot.py:104`, `test_s5_runtime.py:28` | MATCH |
| 5 test sites assign `.detector =` / `.llm =` after build | `test_p5p6_followups.py:101`, `test_p6_detectors.py:186,264,364`, `test_k5_tools.py:608` | MATCH |
| "About 26 test classes define `chat`" | 26 classes in 14 files (by `ast`) | MATCH |
| Migrations `0001` to `0005` exist, no `0006` | `store/migrations/` holds exactly 0001 to 0005 | MATCH |
| 13 PR ids = 4 spend + 9 other-tracks; 13 rows in the merge table | 13 rows (S-1, S-2a, S-2b, DB-1, PR-2, R, K1, A1, G-W, G, H-0, H-1, H-2) | MATCH |
| "six builder sessions (2 + 2 + 1 + 1)" | sums to 6 | MATCH |
| v11 re-check "78 cites flagged" and "62 ambiguous" | `evidence-handoff-v11-independent/raw-cites-summary.txt`: ANCHOR-MISS 2+22+10+44 = 78; AMBIGUOUS 2+5+1+10+2+42 = 62 | MATCH |
| Cycle group around `llm`: 9 modules today (config, deferred, guard.judge, llm, llm.common, llm.fake, llm.retry, registry, replay_records), counting B with type-only imports | my own `r2_graph.py` gives the same 9 modules (`raw-graph-live.txt`) | MATCH |
| Under A with type-only imports: config, deferred, registry, replay_records (4) | same 4 | MATCH |
| Without type-only imports no `llm` group under A or B | none (A: 0 groups without function imports, 1 with: the approvals trio; B: guard, store, audit, approvals) | MATCH |
| By parent package: 11 with function-level imports, 10 without | not recomputed (different grouping) | not checked |
| Planned group of 10 (adds `llm.callgate`) | not recomputed | not checked |
| `ORDERS.md` line 217 is the Q34 answer | `handover/core-hardening/ORDERS.md:216` heading, `:217` text (migration 0006, "keep the default") | MATCH |
| Q33/Q34 say "seven PRs" | line 217 says "all 7" | MATCH |
| ci.yml cites: 77 install, 79 ruff check, 81 format, 83 `psql --version`, 86-87 and 93 env lines, 88 pytest, 94 perf, 119 bandit, 40 `postgres:17.10` | all as stated (read with `sed`) | MATCH |
| pyproject groups | `dev` (pytest, ruff), `test` (moto, pglast), `scan` (pip-audit, bandit, zizmor); `default-groups = ["dev"]` | MATCH |

## gate4.sh against ci.yml (not run)

`bash -n evidence-handoff-v12/gate4.sh`: rc=0 (`raw-gate4.txt`). Its five commands:

| gate4.sh | ci.yml | Same arguments? |
|---|---|---|
| `ruff check src tests demos` | line 79 | yes |
| `ruff format --check src tests demos` | line 81 | yes |
| `pytest -q -m "not live and not perf" -rs` | line 88 | yes |
| `pytest -q -m perf -rs` | line 94 | yes |
| `bandit -q -r src demos -ll` | line 119 | yes |

Differences, all stated in the script's own header and all true: it runs through `uv run --all-extras --group test` (bandit through `--group scan`); it sets neither `HADAVIN_TEST_PG_DSN` nor `HADAVIN_TEST_VAULT_ADDR` (ci.yml 86-87, 93), so database and vault tests skip; it omits `uv sync --locked` (77) and `psql --version` (83) and the security job's pip-audit, Semgrep, zizmor, gitleaks. `ruff` and `pytest` come from the `dev` group, which uv installs by default (`default-groups`), so `--group test` adds to it: I read this from `pyproject.toml`, I did not run it. Root path: the script goes four folders up from `evidence-handoff-v12/` (audit-r460, core-hardening, handover, root) which is correct for its location.

## Method

`r2_cites.py` reads both documents line by line, extracts cites by regex (`path:N`, `path:N-M`, `, :N` continuations, `` `path` N-M `` prose ranges, `path line(s) N`), resolves the path by the document's own rule (folder name under `src/hadavin_sdk`, a bare name only if unique under `src/hadavin_sdk`), checks the range lies inside the file, then looks for the nearest backtick symbols inside the range (MATCH), elsewhere in the file (LINE-OFF with the line), or nowhere (MISSING). `r2_finalize.py` applies my hand verdicts and classifies class B. Method adapted from `evidence-handoff-v11-independent/ind_cites.py` (read only; no code reused). No banned vendor strings were written or scanned.
