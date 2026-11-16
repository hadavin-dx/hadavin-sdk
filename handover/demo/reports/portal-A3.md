# Portal A3: request log and data map endpoints (read-only)

Agent A3, order 210, started 15:34Z, finished about 15:50Z (about 16 minutes of the 60-minute box). Tree: /tmp/dpld-portal (baseline bfb28cf plus A2 edits). Nothing committed, pushed or copied.

## What failed or differs from the brief (read first)

1. **Door words differ from the brief.** The brief shape says `door: web_form|email_message`. The desk stores `form|webhook` (schema CHECK), `/api/ui/summary` and `/api/ui/leads` already return those, and design v2 line 156 maps them to the labels "Web form" and "Email message" in the page. I return the stored words `form|webhook` so the three endpoints agree and the page keeps one label map. Fixtures use `form|webhook`. If the lead wants the page words in the JSON, it is a one-line map in `_log_row`; I did not guess.
2. **8 tests fail in the full run, none caused by A3.** Full run (detached, `/tmp/dpld-out/portal-A9-full.txt`): `8 failed, 510 passed, 1 skipped in 286.45s`. Six of them (`test_failed_retry`, `test_retry_twice_concurrent`, `test_f14_lock_file_unopenable`, `test_demo_adapters`, `test_mutant_no_claim`, `test_reply_write_fails_after_commit_followup_still_runs`) fail the same way on a clean export of baseline bfb28cf (6 failed, 23 passed, 1 skipped) and on the A2 base. I did not find their cause (the log shows `follow-up failed: TypeError` at desk.py line 1021 in one); it looks like this machine, not the code, but that is unproven. They need the lead or a separate fixer. The other two are `test_hygiene_scan_public` (no gitleaks program installed here; the literal-address part of that scan passes) and `test_hygiene_wordlist` (needs the private word list, local only).
3. **Run-order note.** `/tmp/dpld-out/portal-A8-full.txt` never got a summary line: it stopped at 15:14Z with failures shown and no pytest process was alive at 15:42Z (likely cut at the 30-minute background limit). I did not wait forever; I started my one full run at 15:42Z after checking no pytest process was running. Tell me if that broke your rule; the run finished in under 5 minutes alone.
4. Not checked: a live browser view (there is no page yet), the mutation script `scripts/mutation_check.py` (not run), CodeQL, SonarCloud, CodeRabbit, `mypy --platform win32`, load beyond the existing 9,000-receipt big-book test.

## What was built

* `GET /api/ui/log?limit=&before=` in `src/lead_desk/portal_api.py` (`_log`, `_log_row`, `_cursor`). One read transaction (5 statements incl. BEGIN and COMMIT: snapshot start, page, total). Newest first, keyset on `(received_at, receipt_id)`; page read with `limit+1` rows to know whether `next` exists. `limit` 1..200 (default 100), constants `LOG_LIMIT_DEFAULT` and `LOG_LIMIT_MAX` in `constants.py`. Bad or repeated `limit` or `before`, unknown parameter, negative, 19+ digits, non-ASCII digits, spaces, 3-part cursor: 400 `bad_query` with the field name via the existing helpers. Output keys exactly: `request_id, received_at, door, result, lead_id, lead_name, followup_state`. Never email, phone, company, message.
* Outcome mapping: `new`, `duplicate`, `review` map to themselves; outcome NULL maps to `open`. Anything else (the table's own CHECK refuses it, so this is a guard behind the guard) is shown as `review`; an unknown follow-up state or door as `unknown`; the stored text never leaves (unit test `test_log_unmapped_values_do_not_leak`).
* `GET /api/ui/data-map` (`_data_map`, `ai_inputs`, `DataMapRefused`). No database read, no parameters. `receives` = parameter names of `contract.Qualifier.qualify` at call time (self skipped), checked against `AI_INPUT_FIELDS` in constants. The loaded qualifier's own `qualify` must take exactly the same names. Unknown name, `*args` or `**kwargs`, or a mismatch: `DataMapRefused`, which the server answers as 500 `{"error":"internal"}` (no guess). `never_receives` = `LEAD_CONTENT_FIELDS` (`lead_id, name, email, phone, company, message`) minus the fields the received names carry (`email_key` carries `email`): gives `name, phone, company, message`. A test ties both lists to the real `leads` table columns, so a new column must be classified or the test fails.
* `mode`: from the loaded qualifier's class attribute `mode`. I added `mode = "recorded"` to `RecordedQualifier` in `demo_only/fakes.py` (not a lead-owned core file; desk.py and loader.py untouched by A3). Default when the attribute is missing or not in `QUALIFIER_MODES`: `live`, because "recorded" (no live AI called) is a reassuring claim and must be declared by the class, never assumed. The word "recorded" lives only in constants.py and the demo file because the product-file word check bans it in portal_api.py.
* `access`: `bind` from `desk.config.bind`. Config has no host/origin switch (the gate is always on), so `host_check`, `origin_check`, `portal_read_only` are fixed `true` and `login`, `encryption_at_rest`, `masking` fixed `false`, per spec. A test checks the three `true` flags against behaviour (bad Host gives 403, bad Origin gives 403, a write on the portal connection fails).
* `stored`: 11 entries, all `where: "lead book"`, including `request_payload` (the whole request is stored in the receipts table, so the page must say so).
* `contract.md`: paragraph and table rows for both endpoints in plain words, with the note "request record, not a full audit log". No "secure", "encrypted" or "compliant" wording. Docstring endpoint list in portal_api.py updated. server.py has no endpoint allowlist (generic `/api/ui/*` route), so no change there.

## Tests (new file tests/test_portal_log.py: 44 tests; plus one line in the big-book test)

Paging across ties (seed has many equal `received_at`), page sizes 1, 2, 3, 7, 19, 20, 21 all equal the one-page list; empty book; 24 bad-query cases; no-personal-data canary (email, phone, company, message of a first request and of a repeat with different details, plus an incomplete request); one-transaction spy; snapshot test (a receipt committed after the page was read is not in `total`; the next reply sees it); no write; 404 and 405 and Host/Origin 403; data-map equals fixture; signature mutant; variable arguments; loaded-step mismatch; mode default; bind from config; column lists complete; data-map opens no database. Added `("log", "/api/ui/log?limit=200", 5)` to the statement budget in `test_big_book_is_fast_and_cheap` (9,000 receipts; passes). `_review` untouched, budget 6 unchanged.

Result: `44 passed in 22.46s` (new file); ruff check and ruff format --check clean on src, tests, demo_only, tools; mypy `--platform linux` clean; `bandit -ll -q -r src` printed nothing.

## Mutant evidence (details in /tmp/dpld-out/portal-A3-evidence.md)

Real source mutants in a copy (/tmp/dpld-mut, import path checked), not in the tree:
* M1 contract.py `qualify` gains a parameter `name`: 8 tests fail (`DataMapRefused`), including fixture equality and the signature test. So a source-level mutant CAN be shown.
* M2 keyset `<` changed to `<=`: `test_log_paging_with_ties` fails.
* M3 log SQL returns the lead's email as `lead_name`: `test_log_shape_and_results` and `test_log_shows_no_personal_data` fail.
* M4 `email_key` mapped to the wrong field: fixture equality fails.
Unmutated copy: 44 passed. Limit: I did not run the repo's own mutation script, and I did not mutate the `outcome` map.

## Hygiene

One line of my test was flagged by the hard-coded-literal scan (a cursor written as three numbers joined by colons looked like an address); fixed by building it from parts, no exception file change. The bind value `127.0.0.1` in `data-map.json` is already covered by an existing exact exception in `exceptions.txt`, so none was added. Test names are under 40 characters.

## Honest limits

* The log sorts all receipts for each page (no index on `received_at` except a partial one). Fine at 9,000 receipts in the big-book test; a very large book would want an index plus a schema step, which I did not add.
* The log is the request record: latest follow-up state only, not every step. Said in contract.md and must be said on the page.
* `host_check` and `origin_check` are statements about the always-on gate, not read from a setting.

## Files changed (tree /tmp/dpld-portal, on top of A2)

src/lead_desk/portal_api.py, src/lead_desk/constants.py, demo_only/fakes.py, contract.md, tests/test_portal_api.py (one line), tests/test_portal_log.py (new), tests/portal_fixtures/log.json, log-empty.json, data-map.json (new, byte-identical copies in handover/demo/portal/portal-fixtures/).

## Patches

* Full diff vs bfb28cf: /tmp/dpld-out/patch-new-A3.diff (5,625 lines). `git apply --check` and apply on a clean `git archive bfb28cf` reproduces the tree exactly (`diff -r` empty).
* Increment over A2: /home/user/hadavin-sdk/handover/demo/portal/patch-portal-A3.diff (9 files, 770 lines, a/ b/ prefixes). `git apply --check` and apply on a fresh copy of the A2 base (/tmp/dpld-a2-base) reproduces the result exactly.
* Intent-to-add entries were reset, so the tree's index is as I found it (new files untracked).

## R-numbers

The bible folder is not on this machine, so I cite only the numbers named in the repository rules text: R368 (every request has an outcome: the log shows one line per receipt, `open` included), R372 (purpose limitation: no personal fields beyond the display name), R330 and the honest-claims rule (flags stated only as far as code and tests show), R448 CODE-LAST (standard-library `inspect`, existing helpers reused), R449 (stage names untouched). Least privilege: both endpoints only read; no new identity, credential or role. Agents spawned: none. Processes started and stopped: one detached pytest run (finished), mutant runs in /tmp/dpld-mut (finished).

## Open items for the lead

1. Decide the door words (`form|webhook` as built, or page words).
2. The 6 failures that exist on the clean baseline here need an owner (cause unknown).
3. Install gitleaks or run CI to get a true hygiene result.
4. Checkpoint note /home/user/build/A3-checkpoint.md was overwritten with the final state.

## Fix pass 1 after review round 1 (main session, 2026-11-09 ~16:00Z / 21:30 IST)
Reviews: portal-A3-review-1-security.md (0 Blocker, 2 Major, 5 Nit) and portal-A3-review-1-correctness.md (0 Blocker, 3 Major, 5 Nit); resolution table at the end of the correctness file.
Fixed: (1) log query read and sorted the whole book per page: new index `receipts_time_ix` on (received_at DESC, receipt_id DESC) in schema.sql and in `db._VIEW_AND_INDEXES` (an older book gets it at the next start through the existing repair path); plan before: `SCAN r` + `USE TEMP B-TREE FOR ORDER BY`, after: `SCAN r USING INDEX receipts_time_ix`, no temp sort (first page and after-cursor page). Test test_log_query_uses_the_time_index fails when the index line is removed (shown). NOTE: schema.sql and db.py are lead-owned; this is an additive index, user_version unchanged. (2) `_digits` let 5000 zeros reach int() (500): now `len(raw) > MAX_DIGITS`; two new cases fail on the old check (2 failed, 24 passed shown). Also fixes /leads limit/offset. (3) test_log_values_match_the_book (door, received_at, follow-up state per row; door mutant fails it) and test_stored_list_names_every_field. (4) contract.md: null wording, 18-digit rule, request_id/lead_name are caller text.
Evidence: full run /tmp/dpld-out/portal-A10-full.txt: 8 failed, 515 passed, 1 skipped (the same 8 as the clean baseline: 6 known-red plus the two hygiene tests that need gitleaks and the private word list). ruff check and format clean.
Not re-reviewed: a second review round was not run (fixes are test additions, one additive index and a one-line check); lead may ask for it. NEEDS LEAD: door words (`form|webhook` kept) and the index addition. Patch: handover/demo/portal/patch-portal-A3.diff (11 files, 854 lines, a/ b/ prefixes, `git apply --check` on a clean A2 base and identical result verified); fixtures byte-identical.

## Fix pass 2 (security review round 2, M1)
- M1 fixed: `_LOG_ROWS` now uses `(r.received_at, r.receipt_id) < (:at, :id)`; the first page passes a value above every real cursor, so there is no `:first` term. Plan before: `SCAN r USING COVERING INDEX receipts_time_ix`; the new test requires `SEARCH r USING INDEX receipts_time_ix` (fails on the old query).
- Run: `pytest tests/test_portal_log.py tests/test_portal_api.py` = 218 passed (129.6 s). Patch re-made (11 files, 853 lines), `git apply --check` on the clean A2 base OK.
- Not changed, for the lead (q-entry): M2 (`portal_read_only` wording/rename), M3 (`never_receives` caveat). `count(*)` per page is still O(n); total kept exact.
