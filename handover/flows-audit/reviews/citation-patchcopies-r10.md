# Citation check r10: patch-copies README.md and DEAD-MAN-CHECK.md

Checker only; no repository file changed except this report. Targets: `handover/flows-audit/reviews-of-core-patches/patch-copies/README.md` (352 lines) and `DEAD-MAN-CHECK.md` (208 lines). Made-up data, no network, no secret or handle copied.
Method: `git archive b4cce5b` extracted into new empty folders under the scratchpad (`x-b4`, `x-b4-ac`, `x-b4-ac2`; the newest commit `80e9b09a7` into `x-new`); a line reader script kept in a different folder, run with `python3 -I`; for the runs, local clones at `b4cce5b` (cloned from the local checkout, no network), `uv --offline`, `env -i`.

## 1. Result in short
MISMATCH (4): see section 2. Everything else that could be resolved is MATCH. CANNOT-CHECK list: section 4.

## 2. MISMATCHES
| # | Where | Target says | Actual |
|---|---|---|---|
| 1 | DEAD-MAN-CHECK.md line 49 | `CREATE TABLE tick_state` is at `store/migrations/0003_approvals_tick.sql:29` | `:30` (`:29` is the comment line above it). The same file's line 10 says `:30-35`, which is right |
| 2 | DEAD-MAN-CHECK.md line 153 | `effective_problems` is at `store/migrate.py:192` | `:193` (`:192` is a blank line; `def effective_problems` at `:193`) |
| 3 | README.md line 138 ("bandit prints one `nosec` warning") and line 254 ("one nosec warning line") | one warning | exit code 0, but 9 warning lines: 2 identical `nosec encountered (B608)` lines for `demos/ask-your-data/db/lumen.py:723`, 2 identical `nosec encountered (B102)` lines for `src/hadavin_sdk/tools.py:389`, 5 `Test in comment: <word> is not a test name or id, ignoring` lines (same output on unpatched and patched) |
| 4 | README.md line 16 ("Date of this text: ... ninth fixer pass") | ninth pass | the same file says in lines 117, 156, 227 that lines were "written in the tenth pass", and `reviews/fix-patchcopies10.md` exists ("tenth fixer pass ... for patch-copies README.md and DEAD-MAN-CHECK.md"). Internal inconsistency in the pass number |

Notes (not mismatches): (a) README line 31 names `bbfbeee19` as the newest commit; the branch tip is now `80e9b09a7`. `git diff --stat` of `src tests .github` between `bbfbeee19`, `5b5b8933a`, `f05790e42` and `80e9b09a7` is empty, so every result holds for all four. (b) README lines 6-7 quote `../REVIEW.md:5` with a line break after "(the token ceiling)"; in the file the words are on one line (line 5), same words.

## 3. Per-cite results (MATCH unless stated)
### 3.1 Commands run, with exit codes (fresh `git archive b4cce5b`, not a git repository)
```
check C-01 rc=0 / check C-01-price-only rc=0 / check A-01 rc=0
apply C-01-price-only rc=0; git apply --check A-01 after it rc=0; apply A-01 rc=0
apply C-01 rc=0;            git apply --check A-01 after it rc=0; apply A-01 rc=0
at the newest commit (80e9b09a7 extract):
  error: patch failed: src/hadavin_sdk/config.py:362 / error: src/hadavin_sdk/config.py: patch does not apply
  NEW check C-01 rc=1 ; NEW check C-01-price-only rc=1 ; NEW check A-01 rc=0
sha256:
 64fdf315221fb9d653fe8defc844aa438c39c56bc32c5a86c70d8aab67892095  A-01.patch
 e7ff677e70d0c1fd61e9c4e2f1024c58fd35b83bc715abd3d0449202038dae01  C-01-price-only.patch
 ca4982ebb9daef2d5c96e1538d2cdde5291d2d9a948c70553b5661a0a17fded0  C-01.patch
git apply --numstat:  C-01: config.py 11/1, defaults.py 1/0, tests/test_c01_route_limits.py 64/0 (3 files)
                      C-01-price-only: config.py 10/0, tests/test_c01_route_limits.py 51/0 (2 files)
                      A-01: chain.py 13/2, local_dir.py 15/2, tick.py 13/1, tests/test_a01_audit_reconcile.py 123/0, tests/test_p7_tick.py 2/0 (5 files)
                      union with C-01-price-only = 7 files, with C-01 = 8 files
```
Patch line counts (`wc -l`): A-01 264, C-01-price-only 78, C-01 112.
README cites resolved: `git apply --check` b4 rc 0 for all three (MATCH); newest rc 1/1/0 and the error text `config.py:362` (MATCH); file counts 7 and 8 (MATCH); hunk of price-only starts at 362 and the second hunk of C-01 starts at 362 (MATCH); C-01 hunk 1 is in `Route` (`@@ -56,7`) (MATCH). The sha256 values are not quoted in the targets.

### 3.2 Test counts (MATCH)
- `pytest --collect-only` on the patched extract (price-only + A-01): `71 tests collected` = 24 + 6 + 41 (`tests/test_p7_tick.py` 41, MATCH; 39 `def test` plus one parametrize of 3 cases; at the newest commit 39 `def test` and 1 parametrize, MATCH).
- By reading the file: C-01 file has 6 (2 fields x 3 prices) + 1 + 16 (2 llm x 2 fields x 4 values) + 1 + 2 = 26; price-only 24; A-01 file 6. Totals 30 / 32 (MATCH).
- Run: patched clone (price-only + A-01), the two new files: `30 passed in 0.56s`, exit 0. Patched clone (C-01 + A-01): `32 passed in 0.63s`, exit 0.
- Proof on unpatched clone with the two files copied in and `git add -A`: price-only set `exit=1`, `12 failed, 18 passed in 6.25s` (MATCH); C-01 set `exit=1`, `13 failed, 19 passed in 0.55s` (MATCH). Failure texts: 6 x `Failed: DID NOT RAISE ConfigError` (MATCH); `assert 'audit_reconcile' in [...]` (MATCH); `assert 'audit_reconcile drained=1' in '... tick ok=True failed=-'` (MATCH); `assert 0 == 1` (MATCH); the 3 log tests fail with the captured log text `''` (MATCH). The 16 NaN/Infinity cases pass on old code and `match="finite"` holds with pydantic 2.14.1 (`uv.lock` line 1652 `version = "2.14.1"`; MATCH, UNVERIFIED part of line 245 is now verified: the cases passed).
- `git ls-files tests` in the patched clone lists both new test files (MATCH); `git diff HEAD --name-only` there = 7 files (chain.py, local_dir.py, config.py, tick.py, the two new tests, test_p7_tick.py) (MATCH, clause (e)); the unpatched clone has none.
- Guard tests: `99 tests collected` for `test_repo_rules.py`, `test_no_reference_material.py`, `test_lockin_guard.py` (MATCH).

### 3.3 Full runs (recipe lines, clones at `b4cce5b`, `uv --offline`, `env -i`, `-m "not live and not perf" -rfE`)
```
baseline: 2 failed, 9364 passed, 454 skipped, 26 deselected in 253.60s (0:04:13)   rc 1
patched : 2 failed, 9394 passed, 454 skipped, 26 deselected in 237.98s (0:03:57)   rc 1
FAILED tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked   (both)
FAILED tests/test_repo_rules.py::test_licences_are_proprietary                        (both)
"Left contains 10 more items" in both logs; offender list: 3 files, identical in both:
  handover/BRIEF-PREAMBLE-studio-2026-11-06.md, handover/demo/portal/portal-design-v2.md, handover/reviews/P1a-idempotence-probe.txt
diff of the FAILED/ERROR lines: empty
```
MATCH: 9364, 9394 (= 9364 + 30), 454 skipped, 26 deselected, 2 failed, rc 1, "10 more items", three offending files, the two failing test names. 9396 (C-01 + A-01 full run) was NOT re-run here (only its two new test files, 32 passed): CANNOT-CHECK as a full-run number, see section 4. Times 286.64s / 286.29s / 233.17s are the fifth pass's own; this run took 253.60s / 237.98s (times are not claims of the target; not compared).
Gates on the same clones (recipe lines): `ruff check src tests demos` rc 0 `All checks passed!` both; `ruff format --check src tests demos` rc 0, `294 files already formatted` unpatched (MATCH line 254) and `296` patched (line 254 gives 299/301 for the no-folder form; not run in that form here: CANNOT-CHECK); `bandit -q -r src demos -ll` from group `scan` rc 0 both (but see mismatch 3). Patched run in this check was price-only + A-01 only; `C-01.patch` ruff/bandit not run (the target says the same).
Handover files: the three offending files and the nine `handover/promotion-inputs/` files (7 `LICENSE`: apexc, dealdesk, helios, killswitch, portal-kit, refunds, warden; 2 `pyproject.toml`: killswitch, portal-kit) exist at `b4cce5b` (`git cat-file -e`) and are absent from the newest commit's folder (MATCH line 216, 58). `BANNED` list is at `tests/test_no_reference_material.py:19-30` (MATCH).

### 3.4 File and line cites at `b4cce5b` (unless marked newest)
MATCH: `config.py:55-60` Route (newest `:64`); `:316` Config (newest `:332`); `:365` `refused = []` (newest `:393`); `:366` `if self.environment != "dev":` (newest `:394` `if is_live(self.environment):`); `:366-368` and newest `:394-396`; `backends/table.py:593` `DEV_ONLY` (newest `DEMO_ONLY`, `:593`); `defaults.py:104` (the inserted line of C-01); `tests/fixtures/config/config.yaml:2` `environment: dev` (newest `demo`); `pyproject.toml:54` group `scan` holds bandit (group `test` at `:52` does not), `requires-python = ">=3.12"` at `:6`; `ci.yml:73` and `:109` Python 3.13; `:77` install (newest `:78`); `:79` and `:81` ruff (newest `:80`, `:82`, both with `tools`); `:88` pytest (newest `:92`); `:94` perf (newest `:100`); `:113` scan install; `:117` pip-audit; `:119` bandit (newest `:181`, with `tools`); `:123` Semgrep; `:126` gitleaks; `:138` Trivy; newest only: `:105` `tests-py312`, `:84` `tools/scan_repo.py`, `:94` `tests/stage_mutants.py` (both files absent at `b4cce5b`); CI `uv` version `0.13.6` (`:71` at b4); local `uv` 0.11.32.
`k1b/replay.py:85-90`, `:87` (`== 0`), `:118`; `demos/ask-your-data/askdata/config.py:61-70`; `demos/.../fixtures.py:24-26`; `tests/demo_askdata/test_audit.py:30`; no yaml/yml/toml file under `demos/` and the one json file has no model price; `backends/table.py:43-61`, `:502-511` (audit kinds `local_dir`, `chain`), `:512-541` (llm kinds fake, anthropic, bedrock, openai_compat, gemini, in that order); `store/migrate.py:25-26`, `:46-68`, `:59` (`audit_outbox` SELECT, INSERT, DELETE), `:61`, `:172-173`; `0003_approvals_tick.sql:31` (CHECK `^[a-z_]+$`), `:30-35` (table); `runtime/tick.py:177`, `:249`, `:319`, `:357-369` (returns `STORE_UNREACHABLE`, which is `= 4` at `:267`); `audit/chain.py:173`, `:215-231`, `:232`, `:238-255`, `:239`, `:243`, `:244`; `audit/local_dir.py:110-125`, `:126`, `outbox/corrupt/` move at `:145-146`; `audit/protocol.py:27`; `k1b/audit_sink.py:26`, `:59`; `cli.py:213`, `:216` (same at newest); `app.py:161`; `tests/test_p7_tick.py:81`, `:86-95`; `K1bAudit` has no `reconcile` method (only a docstring word at `:38`); `build_audit` has one caller in `src` (`cli.py:216`); nothing in `src` calls `.reconcile()`; no `alert` kind in the backends table; the one yaml with `llm:` is the fixture (kind fake); `max_tokens` fixtures 64 and 1024.
Quoted strings: `redact.py` lines 16-17 (old sentence, MATCH across the two lines); `gate.py` line 7 "The original module notes follow.", line 9 "The outbound gate: the last check ...", line 42 G5 sentence, line 46 G2 paragraph, line 63 "Verdicts: PASS ...", line 203 `AKIA<ZWSP>...` text; `tests/warden_port/test_gate.py` line 3 (exact); gate functions `sanitise_text`, `withhold_commands`, `normalise` exist and no leak-check function. The A-01 patch text holds the quoted log lines (`audit_reconcile drained=%d`, "the audit kind has no reconcile", "held in memory only", "goes to the outbox"), `int(fn())`, `reprobe_sources` in the docstring hunk, and the two-line `test_p7_tick.py` hunk (list entry plus assertion). `C-01.patch` has `MAX_ROUTE_TOKENS = 200_000`.
Other references: `../REVIEW.md:5` (words present), `../REVIEW.md:67` ("3. C-01: DO NOT APPLY NOW"), item 11 at line 75, Decision 18/19/21/23a/23b blocks present (lines 397-403), all 13 row ids (C-3, C-4, C-6, C-8, A-1, A-3, A-6, A-8, G-1, X-2, X-5, X-6, D-3) present as table rows; `ORDERS.md` line 61 is ORDER 013 item 2; ORDER 012 (lines 54-56) has no word "patch"; "ORDER 009" is mentioned in other files but no heading defines it (grep over `handover/`); `system-map` folder has no "Decision B"; `BRIEF-PREAMBLE.md` rule 9 ("Never merge; the lead merges.") and rule 20 (CODE LAST); the fix reports `reviews/fix-patchcopies{4,5,6,7,9,10}.md` and `reviews-of-core-patches/fix-patchcopies1.md` exist; `.claude/rules/verify-tests-and-evals.md` exists; the fifth-pass numbers 9364/9394/9396/454/26 and 299/301 files are in `fix-patchcopies5.md` (lines 37-39, 43); `fix-patchcopies1.md` section 6 matches DEAD-MAN lines 13-16 (Postgres 16.15, `postgres` OS user on a local socket, trust login, three example rows, `audit_outbox` refusal listed, rc 3 after revoke). The repository address `https://github.com/hadavin-dx/hadavin-sdk` equals `origin`; commit `b4cce5b6ae80b45125604b8295ebb35bd2ea1c2c` resolves from `b4cce5b`, is contained only in `origin/cloud/core-hardening`, and is not an ancestor of the current branch (`cloud/flows-audit`), as the README implies. `bbfbeee19`, `5b5b8933a`, `f05790e42` resolve and are ancestors of the current tip.
DEAD-MAN query: the four-name form with `:limit_s` replaced by `180` parses with `pglast` (`1 statement parsed OK`); static only, no database.

## 4. CANNOT-CHECK
- The 9396 full run (`C-01.patch` + `A-01.patch`) and its 233.17s time: not re-run (only the two new test files with that patch, 32 passed).
- `ruff format --check` with no folder named (`299`/`301 files`): not run in that form; with the folders named it gives 294 / 296.
- Anything needing a real database or the Postgres manual: the whole DEAD-MAN-CHECK permission table (rows 1-8), `psql` exit codes 1/2/3, `CREATEROLE` behaviour at Postgres 15 versus 16, `\password` hashing, `pg_hba_file_rules`, the catalog queries a-f, the example output timestamps (`2026-11-16 14:28:52+00` lines: `fix-patchcopies1.md` records the three rows only with `...` for the times), "superuser almost certainly" (no database was started here).
- The claim that `tests/test_p7_tick.py` has 41 collected tests at the newest commit: not collected there (39 `def test` + 1 parametrize counted with grep, 41 derived; same as the target says).
- `ci.yml` `uv` pin and the Python-3.12 job content beyond the line cites; GitHub-only checks (CodeQL, SonarCloud, CodeRabbit).
- ORDER 009 text and system-map "Decision B" text: absent from the checkout (target says so too).
- The verdict script itself (README lines 158-192) was not executed on these logs by this check; only its inputs (counts, failed lines, offender lists, `rc` values) were computed by hand and agree with its clauses (a), (b), (c), (d1), (d2), (e).

## 5. Cleanup
Background runs finished (`pgrep` shows none of mine). Scratch folders remain under `/tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad` (`x-b4`, `x-b4-ac`, `x-b4-ac2`, `x-new`, `runs/`, logs `runs/base.log`, `runs/patched.log`, `proof.log`, `proof2.log`, `pat1.log`, `pat2.log`, `guardcollect.log`, `collect1.log`). No repository file was changed.
