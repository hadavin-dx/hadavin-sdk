# notes-v8-B (group B: docs/limits.md, contract.md)

Studio folder (bible, handoff, memory) does not exist in this container: no R-numbers cited. Tree edited: /tmp/v8work. No test, no linter, no network, no commit. Edit script (scratch): /tmp/claude-0/-home-user/b34836a1-affe-5ae5-ba66-3c71b6499c1e/scratchpad/edit_b.py. out-d7.md is missing (not needed for these two files).
Line numbers are those of the file before my edits.

## 1. Facts first (types c and d, out-d9, out-d8)

| row id | file:line | problem | verdict | edit (old -> new) |
|---|---|---|---|---|
| d1 limits:5 | limits.md:5 | "Known gaps" pointed to a bullet that covers only the burst figures | TRUE-PROBLEM | "Known gaps are in the last bullet" -> "Gaps in the load figures are in the last bullet ...; other gaps are listed in What is not claimed (in full)" |
| d1 limits:17 | limits.md:17 | "Everything below was measured once": most of the page is rules read from code | TRUE-PROBLEM | -> "The load figures below were measured once ...; the rules below them are read from the code and checked by the named tests" |
| d1 limits:22 vs README:6, :100, limits:77 | limits.md:22 | fragment; "never sent twice" vs "sent again with the same key" | TRUE-PROBLEM | fragment -> full sentences: not claimed that no lead is lost, no email sent twice, exactly-once; adds that after an unclear result the same email can be sent again with the same send key (the lead's id, checked: contract.md send_key=lead_id), a keyed stand-in ignores it, a real one may not. README:6 and :100 are in group A's file: they must say the same (not edited here) |
| d1 README:99 vs limits:69 | limits.md:69 | "nine simulated + one real" (README) vs "ten simulated + a real kill at D2" (limits) | NOT-A-PROBLEM for limits.md; limits.md:69 and contract.md:98-99 agree with each other (real kill only at D2). README:99 needs the limits wording (group A) |
| d1 limits:115 vs contract:222 | contract.md:222 | switch named "Hide email addresses"; the portal label in leads.js is "Hide names and email addresses" (src/lead_desk/portal/pages/leads.js) | TRUE-PROBLEM (contract only) | "Hide email addresses" -> "Hide names and email addresses" |
| d1 limits:121 vs contract:131 | contract.md:131 | exit code 2 lists differ; exit 1 "sender" ambiguous | TRUE-PROBLEM | checked server.py main: code 2 is given for LockHeldError and for any other OSError of the lock; code 1 is EXIT_ADAPTERS_UNREACHABLE (demo servers unreachable). contract and limits now both say: 1 the demo servers cannot be reached at start-up, or a Python traceback; 2 another desk holds the lock file, or the lock file cannot be taken for another reason |
| d1 contract:128 | contract.md:128 | "A held lead-book lock raises OSError" | TRUE-PROBLEM (imprecise) | checked lockfile.py: held lock raises LockHeldError (subclass of BlockingIOError, so an OSError); other failures LockUnavailableError (OSError). Rewritten with both names and exit code 2 |
| d1 limits:138 vs :47-49 | limits.md:47, :138 | two wait schedules with the same numbers, not told apart | TRUE-PROBLEM | each now says which situation it is (refusal because an old call runs: kept in memory; failed copy: tries kept in the database, checked: lead_state.crm_tries in desk.py) |
| d1 limits:138 + d8 row 8 | limits.md:138 | said the waits 10, 60, 180, 420 are tested in test_mirror_gate; d8: changing 420 to 400 still passes (test follows the constant) | TRUE-PROBLEM | -> "The five tries and the giving up are tested ... That test checks that the tries follow the constant MIRROR_RETRY_WAIT_SECONDS; no test pins the literal values ... (a mutation check reported by a separate run changed 420 to 400 and the test still passed)". The code constant is (10, 60, 180, 420) in constants.py:159, so the numbers stand |
| d1 limits:138 | limits.md:138 | "after a restart the next try happens immediately" stated, then "not tested" | TRUE-PROBLEM (d) | -> "is expected to happen at once (not tested)" |
| d1 contract:5 vs :241 | contract.md:5, :241 | one says the code is the bug, the other that the table row is wrong | TRUE-PROBLEM | both now say: a bug in one of the two, tell the author. Which side is right is decided case by case (the contract has no rule for it); I did not invent one |
| d1 contract:7, :17 | contract.md:7, :17 | "table below" / "503 above" point to the wrong place | TRUE-PROBLEM | -> "HTTP table further down" and "in the next row" |
| d1 contract:9-22 | contract.md:17, :19 | receipt_id said "the receipt id, or null" for 503 and 500 on every route | TRUE-PROBLEM | checked contract.md:154 (no receipt_id outside POST /leads): cells now say "on POST /leads ... not present on other routes" |
| d1 contract:20 | contract.md:20 | "Any 409 ... hint" while some 409 carry none | TRUE-PROBLEM | added "(no hint for in_progress, unknown_needs_person, not_retryable and already_decided)" (contract.md:64, :203) |
| d1 contract:26 | contract.md:26 | lone-surrogate sentence unreadable | readability, same meaning | split into short sentences |
| d1 contract:28 | contract.md:28 | "see the CRM row above" does not exist; "claim" undefined | TRUE-PROBLEM | claim defined in one sentence; pointer now names the section "Ownership of a follow-up and the CRM mark" |
| d1 contract:36, :41 | contract.md:36, :41 | "review desk", "honest wall-clock bound" | TRUE-PROBLEM (wording) | "stalled items of the review list (GET /review)"; "a true limit on total time only if the adapter itself stops at that time" |
| d1 contract:59 | contract.md:59 | parenthetical unclear | TRUE-PROBLEM | now says step 1 is checked in the server before any lookup, step 4 inside the desk after the item was found |
| d1 contract:65 vs :209 vs :261 | contract.md:261 | no `expected`: is `ok` null or computed? | TRUE-PROBLEM | checked desk.py counts(): ok is None when expected is None. :65 and :209 were right; :261 now says "With expected given, ok is true only when ...; with no expected, ok is null" |
| d1 contract:115 | contract.md:115 | "only unless by_email=0" garbled | TRUE-PROBLEM | checked portal_api.py SQL: company and lead id always; name, email, first request number only with by_email=1 (default). Rewritten that way |
| d1 contract:119 | contract.md:119 | "nothing was sent" only for three reasons, then a fourth (crash_while_sending with ambiguous_prior 0) also says not sent | TRUE-PROBLEM | added the fourth case to the first list ("see below") |
| d1 contract:220 | contract.md:220 | "no personal data" while the log shows lead name and free-text request number | TRUE-PROBLEM (d) | test sentence now says it plants email, phone, company and message and finds none; name and request number are shown on purpose; "keeps back" -> "does not show ... but request_id and lead_name are shown as typed and can hold anything" |
| d1 contract:231 | contract.md:231 | "meant to be harmless" for a real CRM | TRUE-PROBLEM (d) | -> "expected to change nothing on the fake ...; it was not checked against a real CRM" |
| d1 contract:252 | contract.md:252 | reversed reasoning "should not merge two" | TRUE-PROBLEM | -> "so it cannot merge them". The "every other exclusion stands" vs README "nothing more" is README's (group A) |
| d1 contract:300 | contract.md:300 | hint quoted with "..." | TRUE-PROBLEM | full text copied from desk.py HINT_EMAIL_UNKNOWN |
| d1 contract:314, :317 | contract.md:314, :317 | heading suggests the full list; "the other lead" unclear | TRUE-PROBLEM | heading "Three more known limits ... (the longer list is in docs/limits.md)". Checked desk.py ~1235: a duplicate's lead_id is the existing lead with that email key (the first). Sentence now says so and "This is intended" (what the author wrote: "kept as it is") |
| d1 contract:138 | contract.md:138 | same phrase twice | TRUE-PROBLEM | removed the repeat |
| d1 contract:178 | contract.md:178 | "add the replay row" | NOT-A-PROBLEM | the paragraph states replayed true and payload_matches; table shows the first-answer rows. Not edited |
| d1 contract:190 | contract.md:190 | attempts above 5 next to "5 tries" | TRUE-PROBLEM (unclear) | added "so it can be above 5 while the cap of 5 automatic tries still holds" |
| d8 row 1 (1a not caught, 1b caught) | contract.md:118 | said "loaded before bound, so a broken extension leaves nothing listening" with the test as proof; the test passes with the two lines swapped unless the socket is kept alive | TRUE-PROBLEM (d) | now "should leave nothing listening"; the test shows no socket is left after the failure, not the order; a swapped-order mutation still passed unless the bound socket was kept alive (separate run) |
| d9 limits:72 and "Linux 3.13 passed" | limits.md:72 | test figures; the evidence has Linux Python 3.13 3684 passed, 0 failed, 199 skipped (commit f3c39cf8) | TRUE-PROBLEM (incomplete) | bullet split into sub-bullets, numbers unchanged; added one sentence with the 3.13 result marked "reported by a separate run of the desk's tests; no log is shipped" |
| d9 limits:11, :45 | limits.md | MATCH, nothing to fix | NOT-A-PROBLEM | none |
| d1 limits:53-54 | limits.md:53 | hung_workers has four counters | TRUE-PROBLEM (unclear) | "the send and crm counts in hung_workers are back to 0" (the blocked call is a send or CRM call) |
| d1 limits:142 vs README:120 | limits.md:142 | owner id wording differs from README | NOT-A-PROBLEM in limits.md (it says the owner id is written when the owner has a CRM owner id, which is what the test checks); README is group A's |
| d1 limits:154 | limits.md:154 | "our own portal" ambiguous | TRUE-PROBLEM | HubSpot calls an account a portal. Rewritten: the probe script (not the desk's own adapter) did the one write; the adapter was not run against any real HubSpot account (limits.md:15 already says so) |

## 2. Readability edits (same meaning, no new fact)
1 limits:31-39 split into a short list (AI step, keyed, blind).
2 limits:47-52 wait list split.
3 limits:72 test-run bullet split into sub-bullets.
4 limits:77 clock-step bullet split.
5 limits:154 closing paragraph split into three.
6 limits:73, :75-76, :68 fragments turned into full sentences.
7 contract:113 (330 words, five levels of brackets) split into five bullets.
8 contract:40 split into two bullets; contract:154 order fixed; contract:55-56 "3a." empty line merged; contract:26, :28 shortened and claim defined.
Small word fixes: limits:3, :9, :11, :13/:14 (keyed/blind defined in item 4, put-back said in plain words), :28-30 (label hot/warm/cold; caps are in US dollars, from settings.md DESK_LIVE_CAP_RUN_USD), :60, :63, :67 (dangling "1.9 seconds" sentence removed: it referred to a figure never given), :92, :103, :115, :118, :121, :122, :128, contract:121, :127, :222, :230 left.

## 3. CODE-LOOKS-WRONG
None found. One doubt, not edited: contract.md:316 says start-up "counts a try for a row whose backoff has not passed", while contract.md:307 says that with start_background() called first, start-up does not drive pending follow-ups (the reaper does). I did not trace which wins; the sentence is unchanged. Needs a check by whoever owns desk.py startup().

## 4. NOT-ADDED (out-d9 "findings no doc mentions")
- basetemp / TMPDIR (finding 1): belongs to docs/tests.md, not my files.
- Linux Python 3.13 (finding 2): ADDED to limits.md:72 with the "separate run" wording. README.md:130 and docs/tests.md need the same (other groups).
- Two extra skip reasons (3), skip count 200 (4), 20-minute run time (5), git commands cutting logs (6), no flake data (11): belong to docs/tests.md and README, not my files.
- Findings 7-10 (TypeError path, hard links, foreign tools package, LEAD_DESK_PATH_ROOTS set to /): belong to docs/settings.md; the repository holds the fact only in the sibling evidence, so the "separate run" wording would be needed there.
- Finding 12 (wall time spread): open question, no doc effect.
- README:99, :6, :100, :28, :120, :142 contradictions with my files: group A must align with limits.md wording above.

## Not checked
Rendering of the Markdown (nested bullets inside list items); no link check run; contract.md rows 214-222 (cells of 300-500 words) not split (not in the 8 worst I took); limits.md:55-59 and :86-88 (SQL words) not rewritten.
