# Text for handover/core/ON-PATH-LIST.md: section "r7s and r7t" plus corrections (written 2026-11-14, not applied)

Written by the DOC builder from handover files only (R7S-RESULTS.md, R7T-RESULTS.md, snapshot-r7s and snapshot-r7t deltas and MANIFEST, TAKE-USED-FILES-r7t.md, the lead's saved reviews of r7s and r7t, REPORT.md). Nothing was run. The file ON-PATH-LIST.md was NOT edited.

## Part 0: what this text does NOT check (read first)
- I ran no test, no import and no tree. Every "what changed" sentence comes from the delta diffs (`delta-r7r-to-r7s.diff`, `delta-r7s-to-r7t.diff`) and from the builders' result files; the builders' numbers are theirs, not confirmed by an independent run (the evidence run on r7t, EV7T, had not reported when I wrote this).
- "Loaded by the take" below means: the file is in the 42-file closure in `snapshot-r7t/TAKE-USED-FILES-r7t.md`, which was computed by reading imports (python `ast`), not by running anything. That list says a file is IMPORTED. It does NOT say that its code RUNS under Design A (n8n sends mail and writes the CRM; the desk does the spend cap, the model call and the independent mail count). Where this section says what runs, it is my reading of the changed lines and is marked UNVERIFIED unless the closure list settles it.
- The take tree is not on this machine. Whether the take has the names r7s and r7t add is checked only by `test_take_imports.py` on the laptop (not run).
- The lead's fresh review of r7t says NOT PASS (one Major, see the open list). So r7t is not the tree that goes to the take. r7u is being built to fix it.

## Part 1: the new section (paste under the r7q/r7r section)

## r7s and r7t: what changed on the path (added 2026-11-14, from the delta diffs; times in UTC)
Release chain now: ... r7p (test-only) -> r7q -> r7r (two test files only) -> **r7s** (13:12 UTC / 18:42 IST; 15 files) -> **r7t** (15:36 UTC / 21:06 IST; 12 files; core commit 8fb631c0) -> r7u (in progress, see the last table). The tree that goes to the take is the first release that passes a fresh review; neither r7s nor r7t has done so (r7s: 0 Blocker, 1 Major; r7t: 0 Blocker, 1 Major, 8 Minor, 5 Nit).

How to read the last column: "in the take list" means the closure list says the take imports the file. "UNVERIFIED" means the list does not say whether its code runs under Design A.

### r7s (delta r7r to r7s, 15 files; only 2 are source or script files, 13 are tests)
| file | what changed (one plain sentence) | in the take list / runs under Design A |
|---|---|---|
| demo_only/bad_request.py | `QuietServer` (the quiet web server the fake services use) now refuses a listening address that is not this computer, before any socket exists (+14/-1). | In the take list (imported by fake_smtp_tls.py and fake_hubspot.py). Imported: certain. Executed only when a fake is started: UNVERIFIED. |
| scripts/run_real_check.py | The desk counter files are now named with the run tag so an older run's files are not read; a new rule counts contacts the desk made that the HubSpot list did not show; a new function `exit_code_of` ends the run as failed when such a contact may be left (+38/-10). | YES: entry point (in the take list). The counter rule only has something to count if the desk writes the CRM itself: UNVERIFIED under Design A (see caution C1). |
| tests/support.py | New helper that fails (instead of skipping) a test that needs `openssl` when the environment flag `DPLD_REQUIRE_SCAN` is set (+14/-1). | Not in the take list (tests are not imported by the run). |
| tests/test_ca_file_reads.py, test_r7_mail_context.py, test_r7c_mail6_killers.py, test_r7c_mail_killers.py, test_r7f_findings.py, test_r7m_new.py, test_r7n_findings.py, test_smtp_provider.py | Eight existing test files call the new helper instead of a plain skip (1 to 5 lines each). | Not in the take list. |
| tests/test_file_call_guard.py | The guard that lists which files may open a server now knows the new `QuietServer` refusal and lists three fakes that use it (+14/-1). | Not in the take list. |
| tests/test_real_check_dry.py | The one call that built a desk now passes the run tag (+2/-1). | Not in the take list. |
| tests/test_r7q_findings.py | The test that checks an error hides its cause now also checks the cause link itself (+30/-11). | Not in the take list. |
| tests/test_r7s_findings.py (new) | New tests for the loopback refusal, the contact count rule, the exit code table and the openssl helper (+307). | Not in the take list. |

### r7t (delta r7s to r7t, 12 files; 7 are source or script files, 5 are tests)
| file | what changed (one plain sentence) | in the take list / runs under Design A |
|---|---|---|
| src/lead_desk/crm_hubspot.py | Fixes a real race: a counter showing "1 contact created" could be missing one when the desk was stopped between HubSpot's answer and the count; the desk now records "a create is open" before it sends the request, and the outcome ("created", "conflict", "unknown") in one write, and does not send the create at all if the counter file cannot be written (+74/-9). | In the take list (imported by run_real_check.py). The CRM calls run only if the desk writes the CRM: under Design A n8n does, so this path likely does not run: UNVERIFIED. |
| src/lead_desk/run_stats.py | New `write_stats_strict` (writes a temp file, then replaces the counter file whole, and raises if it fails); the old `write_stats` calls it and still ignores failures (+11/-5). | In the take list (imported by smtp_provider.py and crm_hubspot.py). Runs when the desk sends mail or writes the CRM itself: UNVERIFIED under Design A. |
| scripts/run_real_check.py | The contact rule now adds open and unknown creates, capped at the number of leads in the book; the desk counter must be known or the run ends as failed (new `CounterUnreadable`, `counter_is_known`, `read_counter_files_checked`); `Desk` needs a run tag (+97/-23). | YES: entry point. See caution C1 before relying on it under Design A. |
| demo_only/bad_request.py | New function `require_loopback_host`, the one place that refuses a non-local listening address; `QuietServer` calls it (+11/-2). | In the take list. Imported: certain; executed only when a fake starts: UNVERIFIED. |
| demo_only/fake_imap.py | The fake mail reader refuses a non-local host before it opens any file or socket (+2/-0). It now imports bad_request.py (new import chain, see minor m6 in the review). | In the take list (imported by run_real_check.py). Executed only in the self-test (`--dry-fakes`): my reading, UNVERIFIED. |
| demo_only/fake_smtp_tls.py | The fake mail sender does the same refusal (+3/-0), and also imports bad_request.py. | In the take list (imported by run_real_check.py). Same as above. |
| demo_only/fake_model_server.py | Uses the shared refusal instead of its own copy (+3/-6). | NOT in the take list (resolved by TAKE-USED-FILES-r7t.md; the earlier "yes" was wrong). Not loaded by the take. |
| demo_only/fakes_server.py | Uses the shared refusal; an empty host is now refused instead of meaning "the default" (+5/-6). | NOT in the take list. Not loaded by the take. |
| tests/test_r7t_findings.py (new) | 138 new test cases (+1057); the builder reports 78 fail on r7s and 60 are pins that pass on both. | Not in the take list. |
| tests/test_r7s_findings.py | Two tests changed: a missing counter is no longer read as "nothing missing" (it now raises); the exit-code table gets a "counter known" column (+13/-9). | Not in the take list. |
| tests/test_real_check_dry.py, tests/test_r7c_one_json_loader.py | One line each: the desk is built with a run tag (+1/-1 each). | Not in the take list. |

### Cautions for the take (not confirmed)
- **C1 (UNVERIFIED, worth checking first):** in the r7t `scripts/run_real_check.py`, `counter_is_known` is true only if at least one file `desk-<tag>-*.hubspot.json` exists and holds a `created` number (lines 931 to 936, 1377). If, under Design A, the desk never calls the CRM, I found no evidence that such a file is written. Then the run would print "the desk's HubSpot counter cannot be trusted" and end as failed on every run. r7s returned 0 for an unknown counter (it failed open, which is the bug r7t fixed), so this would be a new behaviour of r7t. I read the code lines only; I did not run it. A `--dry-fakes` run under Design A settings would settle it.
- **C2:** the header of `TAKE-USED-FILES-r7t.md` still says the columns compare "the r7r file" with r7n and r7p. The title says r7t. The text under the table looks like it was copied from the r7r version: read the "CHANGED" marks as "differs from r7n / r7p in the r7t tree" only after the builder confirms.
- **C3:** the names the take must have, new since r7n: `demo_only.bad_request.QuietServer`, `demo_only.bad_request.require_loopback_host`, `lead_desk.run_stats.write_stats_strict`. No new source FILE after r7o (still regfile.py as the last new one); r7t adds names, not files. Checked only by the list; the take tree itself is not seen.
- **C4:** the lists of "files to replace in the take" in the old text (lines 51 to 53) now also need `src/lead_desk/crm_hubspot.py` and `src/lead_desk/run_stats.py` at their r7t versions, `scripts/run_real_check.py` at r7t, and the four loaded demo_only files listed above.

### Still open on the path after r7t (not fixed in r7t; the first two are fixed in r7u if the builders succeed)
- **Major M1 of the r7t review (money, uncapped):** the contact count rule caps the possible contacts at the number of leads, so a duplicate or out-of-book contact hidden by list lag (N leads, N+1 created, N listed) gives 0 and the run could end 0 with a contact left; r7s gave 1 in that case. Suggested fix in the review: cap only the open part. Test missing: `f(N+1, N, 0, N) == 1`.
- Minors m1 to m8 and nits n1 to n5 of the r7t review, among them: a counter value such as `1e999`, `-1`, `0.9`, `true` or `"5"` is not refused (m2); the saved result file says "ALL CHECKS HOLD" even when the counter is unreadable (m3); the mail counter `sent` has the same write-after-reply gap as the CRM counter had (m7); a mail sent but not yet visible in the mailbox and not counted stays invisible to both counters (needs the mail server: a third-party limit, stated by the builder).
- M9-74 and M9-79 from the older list: no new information in r7s or r7t. I did not re-check them.
- Evidence on r7s: the lead's review names the staged full run EV7S at 6072 passed. Evidence on r7t: the builder's guard run is 1526 passed, 1 skipped (a Python 3.13 feature); the independent full run EV7T has not reported.

### r7u (in progress; placeholder rows, from REPORT.md; nothing here is a result)
| builder | planned work (builder's own words) | state |
|---|---|---|
| A | cap fix for the contact count (M1) and minors m1 to m4 in scripts/run_real_check.py | in progress; box ends about 17:05 UTC (22:35 IST) |
| B | the mail counter read through the checked reader (m7), m8 (loopback wording), m5 | in progress; same box |
| C | a light loopback module `src/lead_desk/loopback.py` so the fakes stop importing the heavy chain (m6), docstrings (n1, n2), more tests | in progress; same box |
| merge, guard run, packaging, mutant run, independent evidence, fresh review | after the three builders; lead's plan says about 17:35 UTC for the packaged tree | not started |
Files for r7u are TO BE FILLED when the r7u delta exists. Do not paste file rows for r7u before then.

## Part 2: corrections to the older text (line numbers of the file as it stands, 79 lines)

| line | now wrong because | replace with |
|---|---|---|
| 3 | says "Updated ... for r7q and r7r (new section 'r7q and r7r' below)". | "Updated 2026-11-14 <time> UTC for r7q, r7r, r7s and r7t (sections 'r7q and r7r' and 'r7s and r7t' below); first written about 11:00 UTC ..." (keep the rest). |
| 11 | release chain stops at r7q "in progress", and names the frozen head as `49d3c85`. `49d3c85938fe...` is the hash of the TREE of the frozen commit, not a commit. Checked: `git -C /home/user/build/rr6/demo-frozen/repo2 log -1 --format=%H` printed `58aa4031e911e682ec5702e0641d11cbaf927817`; `git rev-parse 'HEAD^{tree}'` printed `49d3c85938fe5323a3378a49195d3b8da434b3ca`. | "Release chain: frozen (commit 58aa4031e911e682ec5702e0641d11cbaf927817; 49d3c85 is only the hash of its file tree) -> r7m (all earlier hardening) -> r7n (leak fix, scrub choke point, banner fixes) -> r7o (regfile reads a leading BOM; tests) -> r7p (TEST-ONLY) -> r7q (on-path source and tests) -> r7r (two test files) -> r7s -> r7t (see the r7s and r7t section) -> r7u (in progress). Columns: lines added/removed." |
| 36 | `trace.py` is "UNVERIFIED: no import found". Settled by the closure list. | "NO: not in the take's closure (TAKE-USED-FILES-r7t.md: no file of the closure imports it; the only `trace` import is the standard module `traceback` in scrub.py)." |
| 39 | says the demo_only fakes (hubspot, imap, smtp) run ONLY in the `--dry-fakes` self-test, "not in the real take". `run_real_check.py` imports all three at module level, so the take must HAVE them (and bad_request.py); they only EXECUTE in the self-test (my reading). | "IMPORTED by run_real_check.py, so the take needs these files (TAKE-USED-FILES-r7t.md); their code runs only in the `--dry-fakes` self-test (my reading, unverified)." |
| 40 | `fake_model_server.py` "dry-fakes / self-test; ... (unverified)". Settled: NOT in the closure. | "NO: not in the take's closure (the closure list). A live run uses the real model host." |
| 41 | `fakes_server.py` is "NO for the run itself: started by scripts/start_all.*". Still true; add that it is confirmed. | append "(confirmed: imported by no file of the closure)". |
| 43 | "r7p changes no source file." True. Needs a sequel. | append "r7q to r7t change these source files: scrub.py, run_real_check.py, bad_request.py, fake_hubspot.py, fake_imap.py, fake_smtp_tls.py, fake_model_server.py, fakes_server.py, crm_hubspot.py, run_stats.py. No new source FILE after regfile.py." (fake_hubspot.py is changed in r7q per the old r7q table, line 66.) |
| 47 | says `demo_only/bad_request.py` is "needed by demo_only fakes in self-test only". It is in the closure. | "`demo_only/bad_request.py` (none; imported by fake_hubspot.py, fake_smtp_tls.py and fake_imap.py, so the take needs it to import them)." |
| 52 | tier 2 "Self-test only" lists fake_hubspot.py, fake_imap.py, fake_smtp_tls.py, fake_model_server.py, bad_request.py as optional. | "2. Imported but used only by the self-test: fake_hubspot.py, fake_imap.py, fake_smtp_tls.py, bad_request.py (the take needs these files to start). Not needed: fake_model_server.py." |
| 53 | "trace.py (unverified)" under 'Not on the path'; and `burst.py` is listed as not on the path. | remove "(unverified)"; remove `demo_only/burst.py` from the list: it IS in the closure (imported by portal_demo.py). |
| 56 | "r7q is being built now (builder aab1bf4c); then EV7P ..." is long past. | "The take's tree must be the first release that passes a fresh uncapped review. r7r, r7s and r7t have not (see the r7s and r7t section). Status of every step is in REPORT.md." |
| 59 | "(r7r) ... **this is the tree that goes to the take**" and "result not in yet" are wrong now. | "... r7r (two test files only; source and scripts byte-equal to r7q). It is NOT the tree that goes to the take: r7s and r7t followed, and r7u is in progress. Evidence on r7r: EV7R, 6021 passed, 7 skipped, 0 failed (runner's number). The independent egm review of r7q/r7r is saved as review-r7r-lead-saved.md." (I did not read that review file; check that line before pasting.) |
| 70 | "The demo_only files are optional for the take (self-test only)." Wrong for fake_hubspot, fake_imap, fake_smtp_tls, bad_request (imported). | "The demo_only files bad_request.py, fake_hubspot.py, fake_imap.py and fake_smtp_tls.py are needed in the take so that run_real_check.py can import; fake_model_server.py and fakes_server.py are not." |
| 73 | M9-74 "Not confirmed" is now partly overtaken by r7s and r7t, which changed the rule for contacts left. | append "r7s and r7t changed this rule (see the r7s and r7t section); the case is not re-probed." |
| 76 | "The independent reviewer's findings: not in yet." | "The lead's reviews: r7q/r7r in review-r7r-lead-saved.md, r7s in review-r7s-lead-saved.md (0 Blocker, 1 Major), r7t in review-r7t-lead-saved.md (NOT PASS: 0 Blocker, 1 Major, 8 Minor, 5 Nit)." |
| 78 to 79 | "Not started." | keep the sentence; this runner is also what would settle caution C1. Status unknown to me; check REPORT.md. |

## Part 3: sources and sizes (for the person checking this text)
- Delta line counts (+added/-removed) were counted by me from the two `delta-*.diff` files with a small script over the `+`/`-` lines of each file; they match the sizes printed in the diff headers' hunks, but I did not compare them with `git diff --stat`.
- Release times come from the file dates in the diff headers (last changed file of each release), not from a release log.
- r7s Major (counter off when missing) is fixed in r7t by the "known" check; the r7t review confirmed spec points (2) to (5) and (6) met, and (1) met for the exit code but not the saved result.
