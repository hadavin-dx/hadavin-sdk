# Citation check r9: patch-copies/README.md and patch-copies/DEAD-MAN-CHECK.md

Checker: static only. Commands used: grep, sed, wc, ls, `git show`, `git cat-file`, `git diff --stat`, `git archive` (extracts in the scratchpad), `git apply --check`, and `git apply` on scratch copies only to count test functions. No test, lint, bandit or database was run.
Sources: `b4cce5b` exists locally (`git cat-file -t` = commit) and was extracted with `git archive b4cce5b`; `bbfbeee19` (the README's "newest commit") also exists and was extracted. The branch head now is `36fd181c6` (later than `bbfbeee19`); `git diff --stat bbfbeee19 HEAD -- . ':!handover'` is empty, so the README's "later commits change only handover/" holds. `b4cce5b` is NOT an ancestor of `bbfbeee19` (it lives on `origin/cloud/core-hardening`); the README does not claim otherwise.
Files checked: `../REVIEW.md` is the live file (it has changed since the README was written: it was edited at 16:18, README at 16:14).

## MISMATCHES (5)
| # | cite | claim | what the file says |
|---|---|---|---|
| M1 | README:37 (words box "Decision 18, 19, 23") | `../REVIEW.md` Decision blocks "at its lines 395 to 401: Decision 18 at 395, 19 at 396, 21 at 398, 23a at 400, 23b at 401" | In the current `../REVIEW.md`: Decision 16 at 395, 17 at 396, **18 at 397, 19 at 398, 21 at 400, 23a at 402, 23b at 403** (22 at 401). Every one of the five numbers is off by 2. (Item 11 at line 75, line 5 and line 67 are correct.) |
| M2 | README:84 (line-number list) | `ci.yml` ruff lines `:79` and `:81` are "same at the newest commit unless marked" | At `bbfbeee19` the ruff lines are `:80` and `:82` (`ruff check src tests demos tools`, `ruff format --check src tests demos tools`). At `b4cce5b` they are `:79` and `:81` (correct there). |
| M3 | README:89 and :116 | "CI uses 3.12 and 3.13" (in a text that says the lines follow the CI file at `b4cce5b`) | At `b4cce5b` `ci.yml` has `python-version: "3.13"` at lines 73 and 109 and no 3.12 job. The 3.12 job (`tests-py312`) exists only at `bbfbeee19` (`ci.yml:3`, `:102-103`). |
| M4 | README:201 | the CI file "also runs" the Python 3.12 job, `tools/scan_repo.py` and the stage mutants (given as a statement about the CI file the recipe is built on, `b4cce5b`) | At `b4cce5b` there is no 3.12 job, no `tools/` folder and no `stage_mutants.py` step; `tools/scan_repo.py` (`ci.yml:84`) and `tests/stage_mutants.py` (`:94`) exist only at `bbfbeee19`. True for the newest commit, false for `b4cce5b`; the sentence names no commit. |
| M5 | README:38 (three numbering schemes) | "row 7 of the table = Decision 23a" | Table row 7 is "G5 wording: approve the new sentences". Decision 23a in `../REVIEW.md:402` asks "may a cleaned copy [of the G5 patch] be kept in the repository?". They are different questions; the REVIEW.md list has no decision about approving the wording. (Rows 2 = Decision 18 and 4 = Decision 19 are right.) |
| Note (not a mismatch) | DEAD-MAN-CHECK.md:49 | "the migration creates it [`tick_state`] in the schema that is current when it runs (`store/migrate.py:172-173`, `current_schema()`)" | Lines 172-173 are `schema = db.execute("SELECT current_schema()")...` and `GRANT USAGE ON SCHEMA {} TO {}`: they show `current_schema()` used for the grant, not the creation of `tick_state`. The creation claim is a reasonable inference (the SQL in `0003_approvals_tick.sql:30` is unqualified) but is not what the cited lines show. Weak; listed for completeness (counted as "OK, inferential" in the table, not as a mismatch). |

(M1 to M5 are the mismatches; the last row is only a weak-cite note, counted as OK.)

## Table (cite | claim | what the file says | verdict)
### README.md
| cite | claim | what the file says | verdict |
|---|---|---|---|
| README:6-7 -> `../REVIEW.md:5` | quote "A-01 is DEFERRED, the C-01 extras (the token ceiling) are CUT, the G5 wording patch is KEPT (text only)" | line 5 contains exactly that sentence | OK |
| README:7 -> `../REVIEW.md:67` | item 3 says "C-01: DO NOT APPLY NOW" | line 67: "3. C-01: DO NOT APPLY NOW." | OK |
| README:7 | these are the lead's default of 2026-11-16, not the studio head | REVIEW.md:5 "WHO DECIDED ... the lead ... NOT the studio head in person" | OK |
| README:10 | `C-01-price-only.patch`: 24 new tests; plus 6 of A-01 = 30 | after `git apply` on scratch: `test_c01_route_limits.py` 6 price (2x3 params) + 1 + 16 (2x2x4) + 1 = 24; A-01 file 6 test functions | OK (counted statically from def/parametrize) |
| README:11 | `C-01.patch`: 26 new tests; 32 with A-01 | 24 + 2 `max_tokens` test functions = 26; +6 = 32 | OK |
| README:16 | first fix report is `reviews-of-core-patches/fix-patchcopies1.md`; later ones `reviews/fix-patchcopies<N>.md` | `fix-patchcopies1.md` is in `reviews-of-core-patches/`; `reviews/` holds fix-patchcopies4,5,6,7,9 | OK |
| README:16 | ten cases in seventh pass; clause (e) in ninth | `reviews/fix-patchcopies7.md:31` "10 cases"; fix-patchcopies9 present | OK |
| README:16, 245 | first-pass database "almost certainly a superuser", trust login | `fix-patchcopies1.md:43` "trust login on a local socket", started as the `postgres` OS user (:37) | OK |
| README:31 | `b4cce5b` = `b4cce5b6ae80b45125604b8295ebb35bd2ea1c2c` | `git rev-parse b4cce5b` = that sha | OK |
| README:31 | newest commit `bbfbeee19`, branch `cloud/flows-audit`; earlier `5b5b8933a` and `f05790e42`; `src/ tests/ .github/` identical in all three | all three commits exist; `git diff --stat bbfbeee19 5b5b8933a -- src tests .github` and `... f05790e42 ...` are empty; branch is `cloud/flows-audit` | OK |
| README:31 | later commits of the branch change only `handover/` | `git diff --stat bbfbeee19 HEAD -- . ':!handover'` empty | OK |
| README:37 | item 11 starts at REVIEW.md line 75 | line 75 starts "11. The studio head gives 33 answers" | OK |
| README:37 | Decision blocks lines 395-401 (18@395, 19@396, 21@398, 23a@400, 23b@401) | see M1 | MISMATCH |
| README:37 | 18 = where price check lives; 19 = stand-in price of a self-hosted model; 23 = two G5 questions (23a cleaned copy, 23b rewrite history) | REVIEW.md:397 (shape of patch C-01), :398 (price of a self-hosted model), :402, :403 match in substance | OK |
| README:38 | row 2 = Decision 18, row 4 = Decision 19, row 7 = Decision 23a, Decision 21 = rotation | rows 2 and 4 right; 21 = "credential lifetime and rotation" (:400) right; row 7 see M5 | MISMATCH (row 7 only) |
| README:38 | D5 appears only in DEAD-MAN-CHECK.md | README mentions D5 only inside this words row | OK |
| README:40 | ORDER 013 in `ORDERS.md`, item 2 at line 61, orders a cross-review into `reviews-of-core-patches/REVIEW.md`, no patch copies asked | ORDERS.md:57 "## ORDER 013", :61 "2. CROSS-REVIEW the READY-TO-APPLY core patches ... Output handover/flows-audit/reviews-of-core-patches/REVIEW.md." | OK |
| README:40 | ORDER 012 answers another question, never mentions patches | ORDERS.md:54-56 "ORDER 012 ... ANSWER to Q3 (F-041)", 0 matches for "patch" | OK |
| README:40 | ORDER 009 text is not in `handover/` | no heading `ORDER 009` anywhere under `handover/` (12 files mention it, none define it) | OK |
| README:41 | system-map Decision B text not found in `reviews-of-system-map/` | `grep "Decision B"` there: no hit | OK |
| README:42 | BRIEF-PREAMBLE rule 9 = PRs, never merge; rule 20 = code last | `handover/BRIEF-PREAMBLE.md:11` "9. PRS: ... Never merge; the lead merges."; :22 "20. CODE LAST" | OK |
| README:45 | `dev` at `b4cce5b`, `demo` at newest; stage names demo/pilot/prod after `b4cce5b` | b4 `config.py:317` `Literal["dev","pilot","prod"]`; nw `:333` `Literal["demo","pilot","prod"]` | OK |
| README:44 | `LIVE_LLM`, test names `test_a_zero_or_negative_price_is_refused_for_a_live_model`, `test_a_priced_live_route_still_loads`, id `live` in `C-01.patch` | all present in C-01.patch (`LIVE_LLM` :59, ids=["live","fake"] :87) | OK |
| README:63 | `CLAUDE.md`: cloud sessions never merge | CLAUDE.md "Cloud sessions open pull requests; they never merge" | OK |
| README:75-81 | `git apply --check`: C-01 rc 0 at b4 / rc 1 at newest (`config.py:362`); price-only rc 0 / rc 1; A-01 rc 0 / rc 0 | my run: b4 0,0,0; nw C-01 rc 1, price-only rc 1 (both `error: patch failed: src/hadavin_sdk/config.py:362`), A-01 rc 0 | OK |
| README:78 | context line `if self.environment != "dev":` at `config.py:366` (b4); `if is_live(self.environment):` at `:394` (nw) | b4 `config.py:366` and nw `:394` exactly | OK |
| README:79 | price-only has one `config.py` hunk, same start line 362 | `C-01-price-only.patch:5` `@@ -362,6 +362,16 @@`; C-01.patch has hunks `@@ -56,7` (Route) and `@@ -362,6` | OK |
| README:83 | `Route` `config.py:55` (nw `:64`); `Config` `:316` (nw `:332`); `refused = []` `:365` (nw `:393`) | b4 55/316/365; nw 64/332/393 | OK |
| README:83-84 | allowed-in-demo table `DEV_ONLY` at `table.py:593` (nw `DEMO_ONLY`, `:593`) | b4 `table.py:593` `DEV_ONLY`; nw `:593` `DEMO_ONLY` | OK |
| README:84 | `ci.yml` bandit `:119` (nw `:181`, adds `tools`); test `:88` (nw `:92`); perf `:94` (nw `:100`) | b4 119/88/94; nw 181 (`bandit ... src demos tools`)/92/100 | OK |
| README:84 | ruff `:79` and `:81` same at newest commit | see M2 | MISMATCH |
| README:85-86 | fixture `tests/fixtures/config/config.yaml:2` `environment: dev` (b4) / `demo` (nw) | line 2 of both | OK |
| README:89 | `requires-python` 3.12 or newer | `pyproject.toml:6` `>=3.12` | OK |
| README:89 | "CI uses 3.12 and 3.13" | see M3 | MISMATCH |
| README:90 | repo `https://github.com/hadavin-dx/hadavin-sdk`; commit on branch `cloud/core-hardening` | `git remote -v` shows that URL; `b4cce5b` is contained in `origin/cloud/core-hardening` | OK (URL reachability CANNOT-CHECK, no network test) |
| README:92 | `tests/test_repo_rules.py`, `tracked_files` | file exists; the `tracked_files` helper name not grepped | CANNOT-CHECK (`tracked_files` name) |
| README:116 | `ci.yml:77` install, `:79`,`:81` ruff, `:113` and `:119` bandit; CI pins uv 0.13.6; CI passes `--no-build`; `--locked` | b4: :77 `uv sync --locked --no-build --all-extras --group test`; :79, :81; :113 `uv sync --locked --no-build --only-group scan`; :119 bandit; uv version "0.13.6" (:71, :107) | OK |
| README:116 | bandit pinned only in group `scan`, `pyproject.toml:54` | :54 `scan = ["pip-audit==2.10.1", "bandit==1.9.4", ...]`; `test` group has no bandit | OK |
| README:116 | `tools` folder does not exist at `b4cce5b`; CI at newest adds `tools` | `ls b4/tools` no such dir; nw ruff/bandit lines add `tools` | OK |
| README:116 | uv 0.11.32 in the seventh pass; `--no-build` error text | `reviews/fix-patchcopies7.md:22` "uv 0.11.32", the quoted error | OK |
| README:140 | markers `live` and `perf` in `pyproject.toml` | `pyproject.toml:87-89` | OK |
| README:140 | CI main run `ci.yml:88` (nw `:92`), perf `:94` (nw `:100`) | as above | OK |
| README:151 | clauses (a)-(d) tested on 10 made-up log sets (seventh pass) | fix-patchcopies7.md:31 | OK |
| README:192 | patched copy changes exactly 7 files (8 with C-01) | `git apply` of price-only + A-01 touches config.py, 2 new tests, tick.py, chain.py, local_dir.py, test_p7_tick.py = 7; C-01 adds defaults.py = 8 | OK |
| README:194 | 99 guard tests in the three files (counted sixth pass) | `fix-patchcopies6.md:24` states 99 collected; the three files exist; I did not run `--collect-only` | CANNOT-CHECK (run), source note OK |
| README:194, 203-208 | two red tests: `test_no_vendor_brand_string_is_tracked`, `test_licences_are_proprietary` | not run; names appear in fix5 logs | CANNOT-CHECK (run) |
| README:193 | `Left contains 10 more items` at `b4cce5b`; 3 offending files | `fix-patchcopies5.md:14,42` "Left contains 10 more", "three paths" | OK (as quoted from the log; not re-run) |
| README:204 | `BANNED` list at `tests/test_no_reference_material.py:19-30` | b4 lines 19 (`BANNED = (`) to 30 (`)`), ten strings | OK |
| README:204-205 | the 3 files `handover/demo/portal/portal-design-v2.md`, `handover/BRIEF-PREAMBLE-studio-2026-11-06.md` hold a banned name; `handover/reviews/P1a-idempotence-probe.txt` not UTF-8 | all three exist at b4; each of the first two has 1 banned-string hit; `file` says the third is "ISO-8859 text" | OK |
| README:206-208 | licence problems: LICENSE of apexc, dealdesk, helios, killswitch, portal-kit, refunds, warden; pyproject of killswitch (licence and authors) and portal-kit (authors); 10 problems | b4 `handover/promotion-inputs/` has exactly those 7 LICENSE files and the 2 pyproject files; 7 + 2 + 1 = 10 | OK |
| README:210, 58 | at newest commit those files are not under `handover/` | none of the 3 files nor `promotion-inputs` exist at `bbfbeee19` (`git cat-file -e` fails) | OK |
| README:219, 242 | 12 failed 18 passed (price-only), 13 failed 19 passed; baseline 9364 passed, 454 skipped, 26 deselected 286.64s; 9394 / 286.29s; 9396 / 233.17s | `fix-patchcopies5.md:37-40` give exactly these | OK (as recorded; not re-run) |
| README:242 | "shared a 4-core machine" | no source found in fix-patchcopies5 or others | CANNOT-CHECK |
| README:245 | `ruff format --check` 299 unpatched / 301 patched; 294 with the folders named; ruff check and bandit rc 0 | fix5:43 (299/301), fix7:38 (294); runs not repeated | OK (as recorded) |
| README:223-228 | test table: 24/26, 6, 30/32; 12/13 fail, 18/19 pass; "1 case holding two assertions" | static count 24/26/6 matches; the `max_tokens_at_the_ceiling` test has two asserts (C-01.patch:110-111); failure counts not run | OK (counts), CANNOT-CHECK (fail on old code) |
| README:228 | `tests/test_p7_tick.py` 41 collected, 39 test functions, one with 3 parametrized cases; same 39 and same test at newest; hunk adds 2 lines | `grep` 39 `def test_` in both b4 and nw; one `parametrize` (:217) with 3 cases (RECEIVED, EXECUTING, VERIFYING) = 41; patch hunk adds one list entry and one assert; fix7:20 quotes `41 tests collected` | OK |
| README:231-235 | each old-code failure message (`DID NOT RAISE ConfigError`, `assert 0 == 1`, etc.) | needs a run | CANNOT-CHECK |
| README:236-237 | pydantic 2.14.1 in `uv.lock`; message contains "finite" | `uv.lock:1651-1652` pydantic 2.14.1; `reviews-of-core-patches/evidence-pydantic-nan.md:51-53` "Input should be a finite number" (an earlier evidence file; the README itself says "UNVERIFIED in the ninth pass", which is fair) | OK |
| README:253-257 | "What each patch is" file lists | patch diff headers: price-only config.py + test; C-01 + defaults.py; A-01 tick.py, chain.py, local_dir.py, 2 tests | OK |
| README:255 | `audit/protocol.py:27` has `reconcile` | `def reconcile(self) -> int:` at :27 | OK |
| README:260-262 | `Money` rejects floats only; `k1b/replay.py:85-90`, `:118`; `:87` tests `== 0` | `config.py:40-47` `_money` rejects float; replay.py 85-90 `_refuse_zero_price`, :118 call, :87 `== 0` | OK |
| README:263-264 | `config.py:366-368` refuses `DEV_ONLY` kinds in real-use stages (nw `:394-396`) | b4 :366-368 and nw :394-396 | OK |
| README:270 | `demos/ask-your-data/askdata/config.py:61-70` builds a `Route`; `fixtures.py:24-26` Route of 2 and 10; `tests/demo_askdata/test_audit.py:30` | all three confirmed (prices "2" and "10") | OK |
| README:270 | no yaml/json/toml under `demos/` holds a price | grep for `usd_per_mtok` in those types under `demos/`: none (only `list_price`/`unit_price` dataset columns in a json) | OK |
| README:279 | `Field(gt=0, le=defaults.MAX_ROUTE_TOKENS)`, ceiling `200_000`; "Existing fixtures use 64 and 1024" | C-01.patch:10, :39 confirm; fixtures: 1024 seen (fixtures.py:25, test_audit.py:30); value 64 not searched | OK (patch), CANNOT-CHECK (the "64") |
| README:281 | `AnthropicSettings`, `table.py:43-61`, config `{kind: anthropic, platform: api, api_key_secret_name}` | table.py:43-61 matches; LIVE_LLM in patch matches | OK |
| README:283 | llm kinds at `table.py:512-541`: fake, anthropic, bedrock, openai_compat, gemini | exactly those five | OK |
| README:284 | only config in the tree naming an llm kind is `tests/fixtures/config/config.yaml` (kind fake) | that file has `llm: {kind: fake, ...}`; a grep for `llm:` in yaml/yml/json returned only that file | OK |
| README:287 | cites `config.py:55-60`, `:316`, `:365`, `defaults.py:104` | 55-60 Route; 316 Config; 365 `refused = []`; patch hunk `@@ -101,6 +101,7 @@` adds the new line at 104 | OK |
| README:291 | `0003_approvals_tick.sql:31` CHECK `^[a-z_]+$` | line 31 `step TEXT PRIMARY KEY CHECK (step ~ '^[a-z_]+$')` | OK |
| README:293-294 | tick exit code; `tick.py:357-369` returns 4 when store unreachable | :357-369; `STORE_UNREACHABLE = 4` at :267 | OK |
| README:294-296 | both audit kinds have `reconcile` (`local_dir.py:126`, `chain.py:232`); table `table.py:502-511` | confirmed | OK |
| README:295-296 | `K1bAudit` (`audit_sink.py:26`) has none; `build_audit` `:59`; only caller `cli.py:216`, import `:213`; `app.py:161`; same lines at newest | `audit_sink.py:26,59`; no `def reconcile` in the file; `cli.py:213,216` and `app.py:161` identical in b4 and nw; `grep build_audit src` shows only cli.py | OK |
| README:299-302 | `chain.py:243` unguarded `model_validate_json`, `DELETE` at `:244`, ordered by `event_id` `:239`; `chain.py:238-255` swallows errors | exactly as quoted | OK |
| README:303 | `migrate.py:25-26` and `:61` mention a runtime role; `audit_outbox` grant `SELECT, INSERT, DELETE` at `:59` | :25-26 docstring "runtime role", :61 comment, :59 `Grant("table", "SELECT, INSERT, DELETE")` | OK |
| README:306 | `_pending` at `chain.py:173`; docstring says "or in memory"; error text "held in memory only" | chain.py:173; A-01.patch:98 "(or in memory)", :26/:73 "held in memory only" | OK |
| README:313 | step logs `int(fn())`; ERROR line `step=audit_reconcile error_kind=RuntimeError` asserted | A-01.patch:105, :207 | OK |
| README:317-318 | cites `tick.py:177` (checkpoint), `:249` (STEPS), `chain.py:215-231`, `:232`, `local_dir.py:110-125`, `protocol.py:27`, `test_p7_tick.py:81` (edit `:86-95`) | all line numbers confirmed; patch hunk `@@ -86,10` | OK |
| README:324-326 | `redact.py` lines 16-17 old sentence quoted | lines 16-17 (b4) read exactly as quoted | OK |
| README:327-332 | `gate.py`: "The original module notes follow." line 7, outbound-gate paragraph line 9; G5 and G2 sentences; "Verdicts: PASS ... BLOCK (G5)." | lines 7, 9; G5 sentence at :42-44 quoted exactly; G2 paragraph :46; Verdicts :63 | OK |
| README:333 | `tests/warden_port/test_gate.py` line 3 old text | line 3 exact | OK |
| README:335 | `gate.py:203` "`AKIA<ZWSP>...` passed G5" | line 203 | OK |
| README:323 | gate.py functions `sanitise_text`, `withhold_commands`, `normalise`; no leak-check function | `grep '^def '`: these plus helpers only | OK |
| README:341-343 | "Not checked" list and `../REVIEW.md` may quote "13 new tests fail on old code" | not verified line by line; statements are negative/hedged | CANNOT-CHECK |

### DEAD-MAN-CHECK.md
| cite | claim | what the file says | verdict |
|---|---|---|---|
| DM:3-4 | `../REVIEW.md:5` and `:67` quotes | confirmed (see README rows) | OK |
| DM:9-10 | `runtime/tick.py:319` `store.save_tick_state`; migration `0003_approvals_tick.sql:30-35` | :319 `store.save_tick_state(`; :30-35 `CREATE TABLE tick_state (...)` | OK |
| DM:13-16 | first pass: Postgres 16.15, `postgres` OS user, local socket, no password; `../fix-patchcopies1.md` section 6; header says only `tick_state`; section 6 lists `audit_outbox` refusal | fix-patchcopies1.md:10 "16.15 with only the `tick_state` table", :36-43 section 6 (socket, trust login, `SELECT * FROM audit_outbox` permission denied) | OK |
| DM:37-38 | `STEPS` at `tick.py:249`; steps `sweep`, `reconcile`, `stuck`, `checkpoint` | :249; entries at :250-253 | OK |
| DM:42-43 | `purge_evidence`, `reprobe_sources` have their own interval | `tick.py:254-260` (`interval=`) | OK |
| DM:48 | tick runs every 30 to 60 seconds | `tick.py:1` "run every 30-60 s", :38 | OK |
| DM:49 | `store/migrate.py:172-173`, `current_schema()` | lines 172-173 show `current_schema()` used for a GRANT, not the table creation; inference only | OK (inferential) |
| DM:72-79 | `psql` exit codes 1/2/3; flags | from the psql manual, not a file in the repo | CANNOT-CHECK |
| DM:80 | no `alert` kind in `src` at `b4cce5b` | `backends/table.py` kinds: secrets, signer, anchor, store, audit, llm, detector, channel; no `alert` | OK |
| DM:83-89 | unhealthy example (audit_reconcile MISSING, stuck STALE, sweep NEVER SUCCEEDED), seen with five-name form | `fix-patchcopies1.md:39` "3 lines (audit_reconcile|||MISSING..., stuck|...|STALE..., sweep||...|NEVER SUCCEEDED), rc 0"; the timestamps are not in the log | OK (shape), CANNOT-CHECK (timestamps) |
| DM:139-141 | refused statements and `REVOKE` then exit 3 `permission denied` | fix1:42 lists those refusals and rc 3 | OK |
| DM:144 | grant map `store/migrate.py:46-68` | `GRANTS` dict at :46-68 | OK |
| DM:91, 154 | `REVIEW.md` D-3 (2); identity table row `dead-man reader` under X-6.6; X-6 says one runtime login | REVIEW.md:179 (D-3 (2) read-only identity), :243 `dead-man reader` row under "### X-6.6 login table" (:232), :201 X-6 row | OK |
| DM:137 | `REVIEW.md` Decision 21 = rotation | :400 "Decision 21 (credential lifetime and rotation)" | OK |
| DM:162-168 | `chain.py:244` DELETE unguarded; `k1b/audit_sink.py:59`; `cli.py:216`, import `:213`; `app.py:161` | confirmed | OK |
| DM:23-31 | decision rows D1-D6, T1-T3 consistent with README rows 1, 8 and "rows 5 and 6" | README table rows 1, 5, 6, 8 match | OK |
| DM:20-31, 24-28 | defaults 180 s and 90 s | proposals, no cite | OK (no file claim) |

## Counts
- Cites/claims checked in the table: 109 rows (README 93, DEAD-MAN-CHECK.md 16). Several rows group many cites; the individual line numbers inside them were each compared with the file.
- OK: 96. MISMATCH: 5 rows (M1, M2, M3, M4, M5; M1 contains five wrong numbers, M3/M4 are "true only at the newest commit"). CANNOT-CHECK: 9 (test-run results and failure messages, 99 collected, 4-core machine, "64" in fixtures, GitHub reachability, `tracked_files` name, psql exit codes, timestamps, "Not checked" negatives).
- Not run, so every "seen in the fifth/seventh pass" figure is only compared with what the fix reports say, not reproduced.

## Raw evidence (last lines)
```
git apply --check at b4cce5b: C-01.patch rc=0; C-01-price-only.patch rc=0; A-01.patch rc=0
git apply --check at bbfbeee19: C-01.patch rc=1 (error: patch failed: src/hadavin_sdk/config.py:362); C-01-price-only.patch rc=1 (same); A-01.patch rc=0
config.py (nw): 64:class Route  332:class Config  393:refused = []  394:if is_live(self.environment):
REVIEW.md: 395 Decision 16 | 396 Decision 17 | 397 Decision 18 | 398 Decision 19 | 400 Decision 21 | 402 Decision 23a | 403 Decision 23b
ci.yml (nw): 80 ruff check ... tools | 82 ruff format --check ... tools ; (b4): 79 and 81 ; python-version "3.13" only at b4 (lines 73, 109)
```
