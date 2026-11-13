# lane3-fix-1 round 4 (builder B1d): notes
Written 2026-11-13 (UTC and IST: see the checkpoint file raw/progress-B1d.txt). Worktree /home/user/work/b1d-base = public main f3c39cf8 + lane3-fix-1-r3.patch + round-4 changes, files staged (`git add -A`), nothing committed anywhere. Patch: evidence/lane3-fix-1-r4.patch (diff from f3c39cf8, so it REPLACES r3, it does not stack on it). sha256 df2515f356cdbb87157a55fc907878aa0d8988b15533256448e6a57658956f29. Prose and tests only; product code untouched.

## Gaps first (not tried / not verified)
* n8n is not installed here. Nothing in Steps 1 to 6 of docs/n8n-recipe.md was run by me except the Linux key-file lines (printf, chmod) and the script's own reading of such a file. The text says "not tried here" for every other step.
* Windows: no Windows computer. Every PowerShell line (`$env:...`, `Set-Content -NoNewline -Encoding ascii`, `Get-NetTCPConnection`) is marked "not tried". A key file with a byte-order mark IS refused by the script (I ran it: message "the n8n API key file must hold one word of printable ASCII ..."); that a Windows editor adds one was not tried.
* Docker: the new Docker paragraph is a statement about the default Docker network (container 127.0.0.1 is the container; a desk bound to 127.0.0.1 is not reachable from it). I did not run Docker; the text says "Not tried here".
* The reviewers' open points I could not close: "the 100-send figure" (now re-run, see below, but only on this Linux container; the older measurement's logs are not shipped); minor tech 8 ("four tests start a real desk, the slowest part") needs no change: the new test file ran in about 3.4 seconds.
* The ONE run of the 12 test files (the 11 files that mention the three documents, plus tests/test_hygiene.py, which is among the 12 listed by `grep -lE "limits\.md|n8n-recipe|README\.md" tests/*.py`): see "Proof runs".
* Not run by design: ruff, mypy, bandit, gitleaks (CI only; so the 4 gitleaks-dependent hygiene tests skip), and the full 21-minute suite (the evidence runner does that).

## Facts I verified myself before writing them (command or file)
| claim | how verified |
|---|---|
| A repeat is not stored again: the upsert updates the first row (attempts + 1) | desk.py lines 1361-1364 read; real desk: SQLite file after (form, f-1) twice and (webhook, w-1): rows `[(1, 2), (3, 1)]` (test asserts it) |
| SQLite AUTOINCREMENT uses up number 2 during the conflicting insert; the webhook lead gets 3 | plain sqlite3 experiment: rows `(1,'f','1',2)` and `(3,'w','1',1)`, sqlite_sequence 3; and the real-desk test: other-door `receipt_id` 3 |
| The repeat's reply shows the first receipt number (1) | test: `again[1]["receipt_id"] == first[1]["receipt_id"] == 1` on a real child desk |
| `received` = number of stored receipts | desk.py `_COUNTS_SQL` `(SELECT count(*) FROM receipts)`; real desk: received 2, new 1, duplicate 1 |
| 202 is a `review` verdict and cannot occur in the burst | desk.py 1286-1294 (else branch: `review`); burst.py `build_body` puts an email into every body; burst counts 200/201/202 as success |
| RETRIES counts 503 busy answers or refused connections a send met, the last answer too, not repeats | burst.py `post_with_retries` (`on_retryable` is called "for every 503 or refused answer, the last too") and `fire` (`stats["busy503"]`, `stats["refused"]`) |
| Burst n=100: `201=1 200=99`, same prefix again `201=1 200=99`, other prefix `200=100`, new 1, outbox count 1 | run on a real desk with the demo stand-in servers on private ports 32211/32212: raw/b1d-burst-100.txt (STATUS lines, `received 100 new 1 duplicate 99` after run 1; `received 200 new 1 duplicate 199` at the end; RETRIES 0/0 each time; RESULT sent=100 expected=100) |
| 5679 comes from scripts/n8n_api.py, 8765/8766 from docs/settings.md | scripts/n8n_api.py line 89 `N8N_URL`, default `http://127.0.0.1:5679`; settings.md table (`DESK_PORT` 8765) |
| proof.json needs the desk-form workflow on | n8n/proof.json line 149: `http://127.0.0.1:5679/webhook/desk-form` |
| The Reaper starts before the desk listens (so "it can take a second" was unfounded) | server.py: `desk.start_background()` line 1195 before `server.serve_forever()` line 1208 (the test compares the positions) |
| A bad `DESK_*` value gives exit code 4, not a traceback | limits.md text for code 4 (the desk refuses a setting); the reviewer checked it as correct; I did not try every setting |
| curl on a closed port: prints `curl: (7) Failed to connect ...`, exit 7 | ran `curl -i --max-time 3 http://127.0.0.1:1/counts`: exit 7, message `curl: (7) Failed to connect to 127.0.0.1 port 1 after 0 ms: Couldn't connect to server` |
| Key file: `printf '%s\n'` file is read by the script; no-newline file too; BOM file refused | ran scripts/n8n_api.py `_read_key` on three files: `'abc123KEYtext'`, `'abc123'`, and for the BOM file the refusal message, exit 1 |
| `docs.n8n.io` is allowed by the hygiene list | exceptions.txt line 6 (`docs\.n8n\.io`); hygiene test run after `git add -A` |

## Table: item | fixed how | verified how
Comprehension review (r3):
| item | fixed how | verified how |
|---|---|---|
| MAJOR 1 n8n has no start step | Step 1 of the recipe: install as the n8n documentation says (link https://docs.n8n.io/), own terminal window, set `N8N_PORT=5679` BEFORE starting (Linux `export`, PowerShell `$env:`), start as documented, leave open, second window for the rest, check http://127.0.0.1:5679 answers; no invented start command; "Not tried here" | test_the_recipe_import_steps_match_the_script (step 1 regexes, port-then-start order); the port default read from scripts/n8n_api.py |
| MAJOR 2 owner account came after the API key | the owner account text moved into Step 1, before Step 2 (API key) | same test: index of "owner account" < index of "create an API key" |
| MAJOR 3 "step 0" vs "## 0." | steps are "Step 1" to "Step 6"; the section is "## Before you start" (no number); the steps say "First read Before you start" | same test: numbers 1 to 6, `## Before you start` present, `## 0.` and `step 0` absent |
| MAJOR 4 receipt wording (README) | rewritten with only true words (see the facts table): repeat not stored again, reply shows receipt 1, database used up 2, webhook lead 3, skipped number is not a lost request, received = stored receipts. Applies to both blocks (Windows line says "same reason") | test_the_receipt_explanation_is_true_and_the_word_is_defined; test_the_second_feed_and_the_receipt_number_match_the_real_desk (real desk, rows `[(1, 2), (3, 1)]`) |
| MAJOR 5 burst step 1 "counts check (not the feed lines)" | names the lines: wait until http://127.0.0.1:8765/counts answers 200 (README Linux wait-loop line starting `for i in 1 2 3`; Windows line starting `Start-Sleep 3; Invoke-WebRequest`); do not run the `scripts/feed.py` lines; PYTHONPATH: step 1 terminal has `src`, step 2's one line sets `src:.` for that command only, PowerShell `$env:` stays for the window | test_the_burst_steps_explain_each_term_and_both_systems |
| MINOR 1 port-check paragraph | README "You need ..." is a sentence plus four bullets (Linux command; what 000 means; 404 and the remedy placed after "step 2 below"; Windows not tried) | test_readme_port_check_explains_000_and_404 (bullet count, facts) |
| MINOR 2 words with two meanings | README word list: Request id = `source_ref` inside; Receipt = one row, the reply carries its number as `receipt_id`; Repeat (`"replayed": true`) = same request id AND same door; duplicate = same email in another request; "request number" now appears once (the portal's name); `received` counts stored receipts (rows) | test_the_words_repeat_duplicate_and_request_id_keep_one_meaning; premises: schema.sql `UNIQUE (source, source_ref)` and `source_ref` |
| MINOR 3 "202" undefined | limits.md step 3: 202 = `review` verdict, does not occur because every send has an email | test (regex) + premises: burst.py counts 202 as success and puts an email into each body; desk.py else branch is `review` |
| MINOR 4 different split | limits.md: a different split means something is wrong or the desk was not fresh, start again at step 1 | burst-steps test |
| MINOR 5 every n8n step run or not tried | each of Steps 1 to 6 says "not tried here", "ran this once" or "run once" | test loops over the six steps |
| MINOR 6 key file commands | Step 3: Linux `printf '%s\n' ... > "$HOME/n8n-key.txt"`, `chmod 600`; PowerShell `Set-Content -NoNewline -Encoding ascii` (not tried); BOM refusal stated (run); `.txt.txt` slip stated as not tried | import-steps test; ran the script's key reading on three files |
| MINOR 7 licence key vs API key | Step 1: n8n licence key = code for a paid plan, do not enter one; the API key is Step 2 | import-steps test |
| MINOR 8 fresh desk after the burst test | recipe: "after that demo or after the burst test the form call answers `duplicate`" | test_the_recipe_says_to_reset_...: also premise that the burst email equals the form example email (lower case) |
| MINOR 9 "see step 3" | the N8N_URL pointer now says Step 4 (the step where the variable is set) | read in the text only (no test pins the words 'Step 4') |
| MINOR 10 Reaper word-list entry | exists (README word list line "**Reaper**"); now pinned | fresh-desk test |
| MINOR 11 curl -sf silent | Linux comment: if after 10 seconds there is no 200 line (curl prints `curl: (7)` or nothing), read `data/desk.log` | fresh-desk test; I ran curl on a closed port (above) |
Technical review (r3):
| item | fixed how | verified how |
|---|---|---|
| 1 "It can take a second" | removed; the sentence is now: if it says `false` and still does after 10 seconds, read `data/desk.log` | premise in the fresh-desk test (server.py order) |
| 2 exit-code 1 bullet | a traceback is a program fault, or someone edited a fixed value in `src/lead_desk/constants.py`; never caused by a `DESK_*` setting because a bad `DESK_*` value gives exit code 4 | test_exit_code_1_uses_the_words_the_desk_prints (real desk run, exit 1) |
| 3 Docker bullet | "On the default Docker network" 127.0.0.1 in the container is the container; a desk bound to 127.0.0.1 cannot be reached from a container even with edited files; `DESK_ALLOWED_HOSTS` changes neither the files nor the listening address; "Not tried here" | test_the_recipe_tells_one_true_story_about_docker; premise: `bind: str = "127.0.0.1"` in config.py |
| 4 5679 source | "8765 and 8766 are the defaults of docs/settings.md; 5679 is the default of scripts/n8n_api.py (setting N8N_URL), not of n8n" | ports test + premise test reading the script |
| 5 proof.json needs desk-form on | clause added | ports test; premise: proof.json holds /webhook/desk-form |
| 6 RETRIES | wording replaced (see above) | burst-steps test; burst.py read |
| 7 100-send figure | re-run on a real desk here (table above); text now says "run on a Linux computer with 100 sends, most recently on 2026-11-13; logs not shipped" | raw/b1d-burst-100.txt |
| 8 four tests start a real desk | no change needed (file runs in about 3.4 s) | pytest duration |
| 9 fragile guard | `"not 0" not in linux` replaced by `\bnot 0\b` regex | fresh-desk test |

## Proof runs
* What failed first: the ONE run of the 12 files (`pytest <12 files> -p no:cacheprovider`, TMPDIR and --basetemp outside every git folder, after `git add -A`) ended `1 failed, 796 passed, 33 skipped in 303.78s`, exit 1 (raw/b1d-12-files-run.log). The failure was `tests/test_hygiene.py::test_hygiene_scan_public` and it was my own slip: my new test file held four literals the repository scan reads as a web address or a Windows drive path (regular expressions with escaped dots, and `src:\.`). Fixed by building those patterns from `HOST`, `re.escape` and split strings.
* After the fix I re-ran only the two files that read the test file: `tests/test_docs_claims_lane3.py` and `tests/test_hygiene.py`: `35 passed, 4 skipped`, exit 0 (raw/b1d-docs-claims-and-hygiene-rerun.log). The 4 skips are the hygiene tests that need the gitleaks program (not installed). The other 10 files were NOT re-run after that fix (their inputs, the three documents, did not change after the 12-file run; only the test file did).
* New test file alone on the patched tree: 15 passed (it also ran inside the 12-file run: that run's only failure was the hygiene test above).
* Proof that the changed tests fail on the r3 documents: the final test file copied onto a tree of f3c39cf8 + lane3-fix-1-r3.patch: `10 failed, 5 passed`, exit 1 (raw/b1d-new-tests-on-r3-tree.log). The 10 failing tests: exit-code 1 text, fresh-desk counts text, receipt explanation, words repeat/duplicate/request id, burst steps, ports, Docker, reset sentence, import steps, README port check. The 5 passing ones are premise tests and the real-desk receipt test (those check the code and the desk, whose behaviour did not change).
* Line length: `awk 'length>120'` over tests/test_docs_claims_lane3.py: 0 lines. The three documents are prose with long lines by the repository's own style; the 120-limit applies to the test file as asked.
* Burst n=100 on a real desk: raw/b1d-burst-100.txt (checked by me, above).
* `git apply --check lane3-fix-1-r4.patch`: clean (exit 0) on a fresh f3c39cf8; clean after claims-stack-on-f3c39cf8.patch; clean after claims-stack + lane3-fix-3-r4.patch + lane3-fix-5.patch. The patch is the full diff from f3c39cf8 (it replaces r3).
* Processes: my desk (pid 24820) and demo stand-in (pid 24689) were stopped; my two pytest runs ended; nothing of mine is left running. I did not touch other builders' processes.
* Not done: no sub-agent, no commit, no push, no change in /home/user/hadavin-sdk except files under handover/demo3/evidence/.


## Rung table (no product code)
| group | rung | why |
|---|---|---|
| README, limits.md, n8n-recipe.md wording | 1 (existing documents, improved) | wording only; n8n steps describe rung 3 (no-code tool), not run |
| tests/test_docs_claims_lane3.py | 7 (our own checking code) | pins facts read from code and a real child desk |
