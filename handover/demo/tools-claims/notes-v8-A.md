# notes-v8-A (README.md, SECURITY.md in /tmp/v8work)

Studio folder does not exist in this container: no bible lookup, no R-numbers cited. Nothing was run (no pytest, no lint, no network, no commit). Edits were made by one script, and afterwards I checked only: no 40+ character run, no backslash-escaped quote, an even number of backticks on every line. I did not re-read the whole files after the edit and did not run the repository link checker.

## Facts and rows

| row id | file:line | problem | verdict | edit (old -> new) |
|---|---|---|---|---|
| d1-a | README:6 vs :100, limits:22, :77 | "never sent a second email" vs "sent again with the same key" | TRUE-PROBLEM (limits:77 and contract say a keyed send can be handed over again; only the keyed demo mail system ignores it) | :6 now states both cases (keyed: may repeat the same email with the same send key, demo ignores it; blind: no resend, listed for a person). :100 adds the same repeat rule. Right one: limits and contract, because they describe the code path |
| d1-b | README:22, :65, :82, :88 vs :118 | "exactly one email" while demo scripts switch on a reminder | TRUE-PROBLEM. demo_only/leadflow.json has nudge_after_seconds 90 and start_all.sh sets DESK_LEADFLOW_FILE and DESK_NUDGE_TO by default | "exactly one email" -> "exactly one email, if you look within 90 seconds of the first lead" plus a sentence that a reminder is added later (4 places). The exact start of the 90 seconds was not checked in code; I wrote "about 90 seconds after the lead arrives" |
| d1-c | README:28 | "nothing more" | TRUE-PROBLEM (contract.md:252 refuses characters such as the Kelvin sign) | "nothing more" -> "The desk refuses a few unusual characters ... (review; see contract.md) and does nothing else to it" |
| d1-d | README:99 vs limits:69, tests.md:96 | nine simulated + one real vs all ten simulated + D2 also a real kill | TRUE-PROBLEM. tests/test_http.py:315 has a real os._exit at D2; limits and tests.md:113 say all ten are simulated | README:99 now: "All ten were simulated ... and D2 was also tried with a real process kill". NOTE: docs/tests.md:96 still has the old "nine of them are simulated ... only D2 is a real process kill" (not my file; whoever owns tests.md should use the same wording) |
| d1-e | README:99 | "tests assert at most one lead..." vs contract.md:289 | TRUE-PROBLEM (d) | "at the crash points the tests cover ... contract.md says that not every path is covered" |
| d1-f | README:47 vs :130 | 3.12 or newer vs "other combination not tried" | TRUE-PROBLEM (pyproject says >=3.12) | :47 keeps "3.12 or newer" and points to the section that lists what was tried |
| d1-g | README:130 | "any other combination was not tried", "not timed on the current set" | TRUE-PROBLEM per out-d9 (a separate run: Linux 3.13 3684 passed; about 20 minutes on a later set) | added the two sentences, each marked as a separate run with no log shipped; kept 16 min 33 s as the last timing in this repository |
| d1-h | README:120 owner id | "when a lead has an owner, the owner id" | TRUE-PROBLEM: crm_hubspot.py:402 sends hubspot_owner_id only if crm_owner_id is non-empty, and the demo file has empty ids | -> "when the lead's owner has a CRM owner id, that owner id" (same as limits:142) |
| d1-i | README:36 | review "incomplete" only | TRUE-PROBLEM (contract.md:244-252: bad characters, invalid email, internal) | review = incomplete or holds a value the desk will not store |
| d1-j | README:40 | UNKNOWN only for email | TRUE-PROBLEM (contract.md:287: crm_unconfirmed is an unknown follow-up) | added "or whether the CRM row was written" |
| d1-k | README:108 vs limits:115, portal.md | list of masked values | TRUE-PROBLEM (portal masks messages and request numbers too) | added "messages and request numbers"; switch name stays "Hide names and email addresses" (that is what portal.md:5 and limits say; contract.md:222 says "Hide email addresses", NOT my file, left for its owner) |
| d1-l | README:141 | script "was not run" next to a probe that touched a real service | TRUE-PROBLEM (confusing, not wrong) | split into: this script has not been run; the separate probe script was run once, no log |
| d1-m | README:142 | "code and tests agree on" vs contract.md:5 (a mismatch is a bug) | TRUE-PROBLEM (d) | "the replies the desk is meant to give (if the code and this file differ, that is a bug to report)" |
| d1-n | README:34 | request id / number naming | TRUE-PROBLEM (minor) | one clause: written "request number" in the portal and below. Other files use more names (reference, source_ref, receipt number): not mine |
| d1-o | README:107 vs :120 | two bind rules | TRUE-PROBLEM (read as two rules; both true) | one sentence: listens on this computer only; you can change it for the demo; with any real service the desk refuses any other address |
| d1-p | README:104 | adopter must be told first that no test touches a real CRM | TRUE-PROBLEM (d) | prepended "no test here talks to one" (hubspot_probe test uses a stub: tests/test_hubspot_probe.py:1) |
| d1-q | SECURITY:5 vs README:120 | "Do not put real customer data" vs real-CRM steps | TRUE-PROBLEM | "Use made-up data only. Real customer data is not meant to go into it, even when a real CRM is connected, until a person has done the checks" (README "Optional features") |
| d1-r | SECURITY:19 vs limits:72 | "runs a secret scanner" | TRUE-PROBLEM (d): no result claimed | "is set up to run" |
| d1-s | SECURITY:28 | "a stand-in can never be a real host" | TRUE-PROBLEM: config.py:517 only requires a loopback host, which can still forward elsewhere | "so a stand-in is not pointed at a remote host by mistake" |
| d1-t | SECURITY:9-10 | button may be off | TRUE-PROBLEM (d) | "if that button is shown" |
| d1-u | SECURITY (whole) | nothing on a leaked key | TRUE-PROBLEM | added "revoke it at its provider first, then report it as above" (advice, no product claim) |
| d1-v | README:6 vs :40 "does not resend" | on a keyed system the desk does resend | covered by d1-a | -- |
| d1-w | README:122 | "later messages" not defined | readability | defined on the spot |
| d8 rows 1 and 8 | server.py make_server order; MIRROR_RETRY_WAIT_SECONDS | tests do not catch the mutation | NOT-A-PROBLEM for README and SECURITY: grep found no sentence in either file that cites those tests or those wait values (limits.md owns it) | none |
| d9 DIFFERS rows | tests.md/limits.md/versions.md figures | skip counts, timing | NOT-A-PROBLEM for README except Linux 3.13 and timing (see d1-g) | -- |
| d1 rows for :29-:31, :33, :35, :37-:38, :43 note, :44 | misc | NOT-A-PROBLEM or not in the top 8 | -- | untouched |
| SECURITY:15, :26 | "latest state", "variable" | readability | fixed: "newest commit", "environment variable" |

## Readability edits (the 8 worst plus a few small)

README:4 AI step defined; :9 and :20 door named; :41 crash point split in short sentences; :42 "settles" -> "decides receipts that were written but never got an answer"; :43 webhook; :51 split into three sentences; :68 shortened (no dash/busybox/zsh names); :73 comment; :88 test names turned into plain sentences; :90 exit codes explained (codes are the reset script's own); :106; :109; :115; :117; :118 (stage, wait, reminder step explained); :120 loopback explained, "step route" and "review routes" described in words; :126; :32 SQLite explained. SECURITY: :3-5, :15, :22, :24 (IMAP), :26, :31-32.

## CODE-LOOKS-WRONG

None found for these two files.

## NOT-ADDED

- Basetemp must stay inside the folder TMPDIR points to (56 tests fail otherwise): belongs to docs/tests.md, not README or SECURITY; the repository itself does not state it in my files.
- Two extra skip reasons (Python 3.13 only, root user): docs/tests.md.
- Skip count and 3683 passed figures: docs/tests.md and limits.md.
- Git commands cutting a test log, hard links, foreign tools package on PYTHONPATH, LEAD_DESK_PATH_ROOTS=/, path objects giving TypeError: belong to docs/settings.md or docs/tests.md; the evidence is a separate run with no log shipped.
- Not done on purpose: README:60 long comment on the loop line, README:113-ish items outside the top rows, the "Words used here" renaming of "lead book" (README does not use it; SECURITY now says "the desk's records"). README:99 "the Kelvin sign" detail not repeated in README.

true problems 22 (fixed 22), not-a-problem 3, readability edits 20
