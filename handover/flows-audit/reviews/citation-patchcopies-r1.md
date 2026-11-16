# Citation check r1: patch-copies/README.md and DEAD-MAN-CHECK.md

Checker: read-only citation checker. Read times (UTC): README.md and DEAD-MAN-CHECK.md both read at 16:04:43 to 16:05 (file time 16:03:22, re-checked at 16:08:49: unchanged since my read). Patch files unchanged since 15:20. Current head of this working copy is `bbfbeee19` (branch `cloud/flows-audit`); `src/` and `tests/` at head are identical to `5b5b8933a` (empty `git diff --stat`) and `f05790e42`. Source read with `git show b4cce5b:<path>` and from the working tree. No tests run, no patch applied, no network. No personal handle printed (the three patch files were read for hunk headers and context only).

## MISMATCH rows (first)

| # | cite | claimed | actual | verdict |
|---|---|---|---|---|
| M1 | README "words" row "ORDER 012" and title "(ORDER 012 item 2)" | `handover/flows-audit/ORDERS.md`, section "ORDER 012", is "the lead's order that asked for these copies" | ORDER 012 (ORDERS.md lines 54-56) is the answer to Q3 (F-041), about a stage journal and spend ledger exception for the video. It does not mention patches. The text "2. CROSS-REVIEW the READY-TO-APPLY core patches ..." is item 2 of ORDER 013 (line 57; item at line 61); it asks for a review into `reviews-of-core-patches/REVIEW.md`, not for patch copies. Nothing in ORDERS.md asks for patch copies. | MISMATCH |
| M2 | README "Decision 18, 19, 23" row | the numbered questions are in item 11 of `../REVIEW.md`, "the blocks are near its line 384 to 390" | Item 11 starts at REVIEW.md line 75. Decision 18, 19, 21, 23a, 23b are at lines 395, 396, 398, 400, 401. Lines 384 to 390 hold Decisions 9 to 12 (and nearby 5 to 15), not 18/19/23. The meanings given (18 = shape of C-01, 19 = self-hosted price, 21 = credential rotation, 23a/23b = cleaned G5 copy / history rewrite) do match. | MISMATCH (line range only) |
| M3 | README "Which commit these patches fit", `C-01-price-only.patch` row: "hunk 2 of `config.py` ... same hunk 2, same context line" | price-only fails at the same hunk 2 | `C-01-price-only.patch` has ONE `config.py` hunk (`@@ -362,6 +362,16 @@`); it is hunk 1 there. Only `C-01.patch` has two `config.py` hunks (`@@ -56,7 +56,7 @@` Route, then `@@ -362,6 +362,16 @@`). Line `362` and the context line `if self.environment != "dev":` are right for both. | MISMATCH (wording: "same hunk 2") |
| M4 | README "newest commit" = `5b5b8933a` ("the newest commit of this working copy") | working copy newest commit | Newest commit of this working copy is now `bbfbeee19`. All `src/`, `tests/` and `ci.yml` line cites hold at it (src/tests identical to `5b5b8933a`; `ci.yml` identical lines), so no result changes, but "newest commit" no longer names the newest commit. The README does say "when the fifth pass ran". | MISMATCH (stale label, harmless to cites) |
| M5 | DEAD-MAN-CHECK status paragraph: "Raw commands and output: `../fix-patchcopies1.md`" | that file holds raw commands and output | The same paragraph says "the log has no raw output". `fix-patchcopies1.md` section 6 is a summary (rows described, `rc` values, `permission denied`); it lists the psql command line once but no raw output. Self-contradiction inside the sentence. | MISMATCH (internal) |
| M6 | README, note on `ci.yml:77-81` "for ruff" | lines 77-81 are the ruff lines | `ci.yml:77` at `b4cce5b` is the `uv sync --locked --no-build ...` install line; the ruff commands are lines 79 and 81. The README sentence also cites `--locked` from that line, so the range is defensible. | MATCH with note (listed here because the range is wider than ruff) |
| M7 | README "A-01 precondition ... `store/migrate.py:25-26`, `:61`" supporting "one runtime login serves agent, tick and receiver (row X-6)" | those lines show the single runtime login | `migrate.py:25-26` is the `Grant` docstring (runtime role / portal role); `:61` is the comment "The runtime role appends and reads evidence; only the purge role ... deletes it". They show a "runtime role" exists, not that agent, tick and receiver share it; that claim rests on REVIEW.md X-6, not on these lines. | MATCH-WEAK (cite supports less than claimed) |

M6 and M7 are not hard mismatches; counted in the MATCH column below as noted. Hard MISMATCH count: 5 (M1 to M5).

## Full table: file:line cites, numbers, strings

### Patch files (hunk headers, counts)
| cite | claimed | actual | verdict |
|---|---|---|---|
| `C-01-price-only.patch` files | `config.py`, `tests/test_c01_route_limits.py` | exactly those two; hunks `@@ -362,6 +362,16 @@`, `@@ -0,0 +1,51 @@` | MATCH |
| `C-01.patch` files | `config.py`, `defaults.py`, test file | those three; hunks `-56,7 +56,7`, `-362,6 +362,16`, defaults `-101,6 +101,7`, test `+1,64` | MATCH |
| `A-01.patch` files | `runtime/tick.py`, `audit/chain.py`, `audit/local_dir.py`, new test file, `tests/test_p7_tick.py` | exactly those five | MATCH |
| `test_p7_tick.py` hunk | adds 2 lines (one list entry, one assertion), changes nothing | `@@ -86,10 +86,12 @@`: `+ "audit_reconcile",` and `+ assert app.store.get_tick_state("audit_reconcile").last_ok_at is not None`; no removed lines | MATCH |
| new tests, price-only | 24 (6 + 1 + 16 + 1) | functions: refuse (2 fields x 3 prices = 6), priced loads (1), non-finite (2 llm x 2 fields x 4 = 16), fake-at-0 (1) = 24 | MATCH |
| new tests, C-01 | 26 (24 + 2 `max_tokens`) | + `test_max_tokens_above_the_ceiling_is_refused`, `test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused` = 26 | MATCH |
| new tests A-01 | 6 | 6 test functions, no `parametrize` in that file | MATCH |
| totals 30 / 32 | 24+6 / 26+6 | arithmetic holds | MATCH |
| fail on old 12 / 13; pass 18 / 19 | 6 price + 6 A-01 = 12; +1 ceiling = 13; controls 18/19 | arithmetic consistent with the test list; the run itself is in fix-patchcopies5.md line 40 ("12 failed, 18 passed", "13 failed, 19 passed") | MATCH (log); run itself CANNOT-CHECK |
| patch strings `match="zero or negative price"`, `"finite"`, `"less than or equal to 200000"`, `"greater than 0"` | as written | `zero or negative price` in `ValueError(f"routes with a zero or negative price: ...")`, tests use the same; `finite`, `less than or equal to 200000` present in test text; `greater than 0` assumed from the same test (not separately read) | MATCH (last one partial) |
| `LIVE_LLM`, `test_a_zero_or_negative_price_is_refused_for_a_live_model`, `test_a_priced_live_route_still_loads`, test id `live` in `C-01.patch` | as written | all present (ids `["live","fake"]`) | MATCH |
| ceiling `200_000` and `MAX_ROUTE_TOKENS` in `defaults.py`; cite `defaults.py:104` | insertion site | inserted at new line 104, before `PURGE_EVERY_S` (b4 line 104) | MATCH |
| `Field(gt=0, le=defaults.MAX_ROUTE_TOKENS)`; `Route` `config.py:55-60` | | `class Route` at b4 line 55; field at 59 | MATCH |
| A-01 docstring "(or in memory)" (A-1) and error text "held in memory only" | | tick docstring says "(or in memory)"; chain error text "event %s is held in memory only" | MATCH |
| A-01 log lines (warning / error; type and id only) | | chain: `audit outcome not appended (%s): event %s goes to the outbox`, `audit outbox not written ... held in memory only`; local_dir has matching warning | MATCH |
| tick log `audit_reconcile drained=%d` with `int(fn())`; kind without reconcile raises `RuntimeError("the audit kind has no reconcile ...")` | | present in patch; test asserts `step=audit_reconcile error_kind=RuntimeError` | MATCH |
| docstring hunk adds `reprobe_sources` (A-8) | | `@@ -1,7 +1,7 @@` adds `reprobe_sources, audit_reconcile` | MATCH |

### Source at `b4cce5b`
| cite | claimed | actual | verdict |
|---|---|---|---|
| `config.py:55` Route | line 55 | `class Route(_Strict):` at 55 | MATCH |
| `config.py:316` Config | | `class Config(_Strict):` at 316 | MATCH |
| `config.py:365` `refused = []` | | 365 | MATCH |
| `config.py:366` `if self.environment != "dev":` | | 366 | MATCH |
| `config.py:366-368` demo-only refusal | | 366 `if`, 367 `refused = [`, 368 comprehension with `DEV_ONLY` | MATCH |
| `config.py` hunk start 362 | | patch hunk `-362,6`; b4 lines 362-364 are the `base_url must be https` lines | MATCH |
| `backends/table.py:593` `DEV_ONLY` | | 593 | MATCH |
| `backends/table.py:43-61` `AnthropicSettings` | | class at 43, `return self` at 61 | MATCH |
| `backends/table.py:512-541` llm kinds `fake, anthropic, bedrock, openai_compat, gemini` | | `"llm": {` at 512; the five kinds at 513, 515, 522, 529, 536; the block's closing brace is at 542 (entries end 541) | MATCH (entries) |
| `backends/table.py:502-511` audit kinds `local_dir`, `chain` | | audit block 502-511 | MATCH |
| `defaults.py:104` | | `PURGE_EVERY_S` at 104 | MATCH |
| `k1b/replay.py:85-90`, `:87`, `:118` | | def at 85, `== 0` check at 87, raise 90, call at 118 | MATCH |
| `demos/ask-your-data/askdata/config.py:61-70` builds `Route` itself | | `def routes` at 61 ... closing `}` at 70 | MATCH |
| "no yaml, json or toml under `demos/` holds a price" | | `git grep usd_per_mtok` in `demos` found no such file | MATCH |
| `tests/fixtures/config/config.yaml:2` `environment: dev`; "existing fixtures use 64 and 1024" | 64 and 1024 | line 2 is `environment: dev`; `git grep max_tokens` in `tests/fixtures` finds only 1024 (the value 64 was not found in `tests/fixtures`; may be in other test files) | MATCH for line 2; 64 UNCHECKED (see below) |
| `0003_approvals_tick.sql:30-35` table, `:31` CHECK `^[a-z_]+$` | | CREATE at 30, `step ... CHECK (step ~ '^[a-z_]+$')` at 31, `);` at 35; columns `last_run_at`, `last_ok_at`, `last_error` | MATCH |
| `tick.py:177` checkpoint, `:249` STEPS, `:319` `save_tick_state`, `:357-369` returns 4 | | 177 `def checkpoint`; 249 `STEPS`; 319 `store.save_tick_state(`; 357-369 `FAILED` check / `STORE_UNREACHABLE` return | MATCH |
| `chain.py:173` `_pending`, `:215-231`, `:232` reconcile, `:239`, `:243`, `:244`, `:238-255` | | all as described (243 unguarded `model_validate_json`, 244 DELETE, 239 ORDER BY event_id) | MATCH |
| `local_dir.py:126` reconcile, `:110-125` write_outcome; corrupt files moved to `outbox/corrupt/` | | 126, 110-124; docstring at 127-128 says so | MATCH |
| `audit/protocol.py:27` | | `def reconcile(self) -> int:` at 27 | MATCH |
| `k1b/audit_sink.py:26` `K1bAudit`, `:59` `build_audit`; K1bAudit has no `reconcile` | | 26, 59; `grep 'def reconcile'` in that file: none | MATCH |
| `cli.py:213` import, `:216` call; only caller of `build_audit` in `src` | | exactly these two lines (same at head) | MATCH |
| `app.py:161` `app.audit` built via `make("audit", ...)` | | line 161 (same at head; app.py changed at other lines only) | MATCH |
| "nothing in `src` calls `reconcile`" | | `git grep '.reconcile()' b4cce5b -- src`: no caller | MATCH |
| `store/migrate.py:59` `audit_outbox` `SELECT, INSERT, DELETE` | | line 59 | MATCH |
| `store/migrate.py:46-68` grant map | | 46 `GRANTS`, 68 closing | MATCH |
| `tests/test_p7_tick.py:81`, edit at `:86-95`; 39 functions; one parametrized (3 cases) | | def at 81; hunk starts at 86; 39 `def test_`; `parametrize` at 217 | MATCH (41 collected: see CANNOT-CHECK) |
| `tests/test_no_reference_material.py:19-30` `BANNED` | | `BANNED = (` at 19, `)` at 30, ten strings | MATCH |
| banned string in `handover/demo/portal/portal-design-v2.md` and `handover/BRIEF-PREAMBLE-studio-2026-11-06.md`; `handover/reviews/P1a-idempotence-probe.txt` not UTF-8 | three offending files | all three exist at `b4cce5b`; scan with the ten strings: one hit each in the first two; third is not UTF-8. (They no longer exist at head: see "Did not check".) | MATCH |
| `test_licences_are_proprietary`: 10 problems; 7 LICENSE files differ; killswitch `pyproject.toml` licence and authors; portal-kit authors | | reimplemented `licence_problems` logic over `b4cce5b`: 7 LICENSE differ (apexc, dealdesk, helios, killswitch, portal-kit, refunds, warden), killswitch license + authors, portal-kit authors missing = 10 | MATCH |
| `pyproject.toml:54` bandit pinned only in group `scan` | | line 54 `scan = [..., "bandit==1.9.4", ...]`; `test` group has no bandit | MATCH |
| `requires-python` 3.12; CI uses 3.12 and 3.13; pydantic 2.14.1 in `uv.lock` | | `>=3.12`; ci.yml python-version 3.13 (line 74) and 3.12 (142); `uv.lock` pydantic 2.14.1; `pyproject` pin `pydantic==2.14.1` | MATCH |
| `ci.yml:88` test line, `:94` perf line | | 88 `run: pytest -q -m "not live and not perf" -rs`; 94 `run: pytest -q -m perf -rs` | MATCH |
| `ci.yml:113` scan install, `:119` bandit (`bandit -q -r src demos -ll`) | | 113 `uv sync --locked --no-build --only-group scan`; 119 bandit | MATCH |
| `ci.yml:77-81` ruff (see M6) | | 77 install, 79 `ruff check src tests demos`, 81 `ruff format --check src tests demos` | MATCH with note |
| pytest markers `live` and `perf` in `pyproject.toml` | | present (line 85-88) | MATCH |
| `AKIA...` / G5 text: `redact.py` lines 16-17 old sentence | | line 16 "the control; HIGHENTROPY ... independently, on", line 17 "everything that leaves." | MATCH |
| `gate.py` line 7 "The original module notes follow." and line 9 "The outbound gate: the last check..." | | line 7 ends with that sentence; line 9 is the paragraph | MATCH |
| `gate.py` G5 sentence, G2 paragraph, `Verdicts: ... BLOCK (G5).` | | lines 42-44, 46, 63 as quoted | MATCH |
| `gate.py:203` "`AKIA<ZWSP>...` passed G5 and went out whole" | | line 203 text (begins "from link removal ... passed G5 and") | MATCH |
| `gate.py` functions `sanitise_text`, `withhold_commands`, `normalise`; no leak-check function | | present; no `def` with leak in name | MATCH |
| `tests/warden_port/test_gate.py` line 3 old docstring | | line 3 exactly as quoted | MATCH |

### Cites at "newest commit" (checked at head, which has the same `src/`, `tests/`, `ci.yml` as `5b5b8933a`)
| cite | claimed | actual | verdict |
|---|---|---|---|
| `Route` `config.py:64`; `Config` `:332` | | 64 and 332 | MATCH |
| `refused = []` `:393`; `if is_live(self.environment):` `:394`; `:394-396` | | 393, 394, 395-396 (`DEMO_ONLY`) | MATCH |
| `DEMO_ONLY`, `table.py:593` | | 593 | MATCH |
| `ci.yml` bandit `:181` adds `tools`; test `:92`; perf `:100` | | 181 `bandit -q -r src demos tools -ll`; 92; 100 | MATCH |
| fixture `environment: demo` at newest commit | | `environment: demo` | MATCH |
| `cli.py:213/216`, `K1bAudit` same lines at newest commit | | unchanged | MATCH |
| `test_p7_tick.py` "still 39 test functions and the same parametrized test" at newest commit | | 39 `def test_`, `parametrize` at 217 (one test renamed at line 282; far from hunk) | MATCH |
| `A-01.patch` applies at newest commit ("its files did not change in the lines it touches") | | chain.py, local_dir.py, tick.py, test_p7_tick.py hunks are in lines unchanged between `b4cce5b` and head (only app.py, signer.py and one test name changed) | MATCH (by diff reasoning; `git apply --check` not run) |
| `C-01*.patch` fail at newest commit: context line `if self.environment != "dev":` is `is_live(...)` at 394 | | confirmed: hunk context no longer matches | MATCH |
| `f05790e42` and `5b5b8933a` both exist; src/tests identical between them | | both commits exist; empty `git diff --stat -- src tests` | MATCH |
| `5b5b8933a` exists; branch `cloud/flows-audit`; commit `b4cce5b` is on `origin/cloud/core-hardening` | | `b4cce5b` full hash `b4cce5b6ae80b45125604b8295ebb35bd2ea1c2c`; `git branch -a --contains` lists `remotes/origin/cloud/core-hardening` | MATCH |

### Cites into `../REVIEW.md`, `../../reviews/*.md`, other handover files
| cite | claimed | actual | verdict |
|---|---|---|---|
| `../REVIEW.md:5` word-for-word "A-01 is DEFERRED, the C-01 extras (the token ceiling) are CUT, the G5 wording patch is KEPT (text only)" | | line 5 contains exactly that sentence | MATCH |
| `../REVIEW.md` item 3: "C-01: DO NOT APPLY NOW" | | line 67 "3. C-01: DO NOT APPLY NOW" | MATCH |
| `REVIEW.md` row ids C-3, C-4, C-6, C-8, A-1, A-3, A-6, A-8, G-1, X-2, X-5, X-6, D-3 exist | | all 13 are table rows (lines 148-201) | MATCH |
| C-3 (demo builds `Route` itself), C-4 (replay `== 0`, negative price, tiny price), C-6 (rollout note), C-8 (self-hosted, only `fake` exempt), A-1, A-3, A-6, A-8, X-2 (Major, conditional), X-5.1, X-6.6 identity table row, D-3 (2) read-only identity | | meanings confirmed from the rows; counts line 74 "4 Major (3 present, 1 conditional)" | MATCH |
| G-1 "might understate existing protection" (`approvals/channel.py:29` runs one final redaction) | | G-1 says the approval channel does one final redaction pass | MATCH |
| `REVIEW.md` "Decision 21" rotation, "Decision 19", "Decision 18", "Decision 23" | | exist, meanings match | MATCH (line range see M2) |
| `BRIEF-PREAMBLE.md` rule 9 = cloud sessions open pull requests and never merge; rule 20 = code last | | rule 9 line says "Never merge; the lead merges"; rule 20 is "CODE LAST" | MATCH |
| `../fix-patchcopies1.md` (one folder up) header "only tick_state"; section 6 audit_outbox refusal; Postgres 16.15; `postgres` OS user, local socket, trust login | | header line 10 says "only the `tick_state` table"; section 6 lists `SELECT * FROM audit_outbox` refused; 16.15; "started as the `postgres` OS user on a local socket"; "used trust login" | MATCH |
| DEAD-MAN example output (three lines) | | matches the section 6 description (`audit_reconcile` MISSING, `stuck` STALE 10 min, `sweep` NEVER SUCCEEDED) | MATCH |
| `handover/flows-audit/reviews/fix-patchcopies7.md`: ten verdict-script cases; uv 0.11.32 `--no-build` failure; "294 files already formatted"; bandit rc 0; apply check results | | all present (lines 22, 31-32, 36-38) | MATCH |
| `reviews/fix-patchcopies5.md`: 9364 / 9394 / 9396 passed, `2 failed ... 454 skipped, 26 deselected`, 286.64s / 286.29s / 233.17s; `Left contains 10 more items`; ruff 299 / 301; bandit rc 0 also with `tools`; apply-check table | | all present (lines 37-43) | MATCH |
| fix-patchcopies5: "does not record the exact command lines used" | | the Gates line gives results, no command lines | MATCH |
| `system-map` Decision B text "not found there" | | `handover/flows-audit/reviews-of-system-map/` has no "Decision B" text | MATCH |
| ORDER 009 "text not in this checkout" | | no `## ORDER 009` heading in ORDERS.md (gap between 008 and 010); other files only mention it | MATCH |
| "ORDER 012 path" (words box) | | see M1 | MISMATCH (M1) |
| `ORDERS.md` / `QUEUE.md` mention | | ORDERS.md exists | MATCH |

## Counts

Counted with grep on this file (rows whose verdict cell starts with the word; approximate because a few rows group several cites): MATCH 87 rows (some "MATCH with note"), MISMATCH 6 rows = 5 distinct findings M1 to M5 (M1 appears twice), MATCH-WEAK 1 (M7; M6 is a MATCH with a note), CANNOT-CHECK 12 groups (list below).

| CANNOT-CHECK | reason |
|---|---|
| `git apply --check` exit codes (rc 0 at `b4cce5b`, rc 1 at newest for both C-01 files, rc 0 for A-01; error text `patch failed: ...config.py:362`) | not allowed to apply; supported by hunk-context reasoning (M3 note) and by fix-patchcopies5.md / 7.md log lines |
| all full-suite numbers (9364, 9394, 9396, 454 skipped, 26 deselected, times), `12 failed, 18 passed`, `13 failed, 19 passed`, lint counts 299/301/294 | would need a test run; only the logs `fix-patchcopies5.md` and `fix-patchcopies7.md` repeat them |
| "99 guard tests" (collect-only) | needs a collection run; static count: 82 `def test_` in the three files (23 + 3 + 56) plus 2 `parametrize` in `test_repo_rules.py`, so 99 is possible but not shown |
| `test_p7_tick.py` "41 collected" at `b4cce5b` (39 functions, one with 3 cases) | needs collection; static count 39 functions and one `parametrize` is consistent |
| "10 more items" / "Left contains" text | needs a run; the 10-problem figure itself I re-derived (see table) |
| `tests/fixtures`: "existing fixtures use 64 and 1024" | only 1024 found under `tests/fixtures`; 64 not found there (it may be in other test files; not searched) |
| pydantic message `finite` for NaN and Infinity | needs a run |
| Postgres manual claims (CREATEROLE at 15 and older, TEMPORARY on `PUBLIC`, `psql` exit codes 1/2/3, `\password` hashing, `PGPASSFILE`, `PGSSLMODE`, `CONNECTION LIMIT`, `statement_timeout`) | external documentation, no network |
| repository `https://github.com/hadavin-dx/hadavin-sdk` and branch `cloud/core-hardening` there | no network; only the local `origin/cloud/core-hardening` ref was checked |
| rows 1, 3, 4, 5 "seen once on a throwaway Postgres" | only the fixer log exists, no raw output |
| `uv run --no-build` failure message | needs `uv` run |
| the clone-and-apply recipe lines and the verdict script | not run (no clone, no apply) |

## What I did not check

- Did not run any test, lint, bandit, `uv`, `psql`, `git apply` (even `--check`), clone or network call.
- Did not re-read the patch files in full for every added line; I checked hunk headers, file lists, test function names and parametrize decorators, the price rule text and A-01 log strings.
- Did not verify claims that come from the Postgres manual or other external docs (listed above), nor the quoted `ci.yml` text beyond the cited lines.
- The three offending files and the seven `promotion-inputs` licence files exist at `b4cce5b` but are NOT present at head (they were checked with `git show b4cce5b:`). So the "baseline failures" and verdict section hold only for a copy of `b4cce5b`, as the README says; at head those two tests would not fail for those reasons. The README does not claim otherwise.
- My scan for banned strings counted other non-UTF-8 files under `handover/` (bundles, `.gz` files) that the README does not list; whether the real test skips them (by extension) I did not read, so "three files" rests on the earlier run log plus my own hit count for the two text files.
- Did not check `REVIEW.md` rows beyond the cited ids and the facts the README states about them (no read of every column), nor the cites inside `../../reviews/*.md` beyond fix-patchcopies1, 5 and 7.
- Did not check the README's statements about other sessions (who may edit what) or any date and time claims other than commit and file existence.
- Did not check `README.md` sections on "Who runs each part" or the decision-table "Who decides" cells (decisions, not cites), except where they cite a Decision or row number.
- `fix-patchcopies7.md` line 15 says the newest-commit bandit line is `ci.yml:172`; the README says `:181` and `:181` is correct at head (that log line is wrong, not the README).
