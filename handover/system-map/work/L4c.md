Older notes: work/L4c-history.md and work/L4c-history-2.md (ignore). Cite finding ids, not line numbers.
Key (added 16 Nov): finding id prefixes S-, X-, J-, K-, D-, T-, F- label the kind of row and FD- is a finding; the meaning of each letter is NOT RECORDED, so read an id as a name only. The findings are in the table further down this file (search the heading Findings). The one-store decision copies are handover/system-map/DECISION-one-store.md (20 lines) and handover/system-map/inputs/DECISION-one-store.md (28 lines). Mode A and the Stores section: meaning NOT RECORDED. Questions in this file go to the lead session, which passes studio questions to the studio lead.

## Status 16 Nov 2026 (the only status block)
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
- Counts: 26 findings (L4c-FD-001 to FD-026). Blocker outside the quarantine: FD-002 only. FD-001 and FD-003 are also security Blockers but are QUARANTINED (see below), so nothing is done with them.
- Quarantined rows (do not act on them; these rows touch the earlier real-run folder, which this lane must not reopen): S-003 to S-006, X-001 to X-003, J-003, J-004, J-008, K-001 to K-004, D-002, T-001, T-004, F-001, FD-001, FD-003, FD-007, FD-008, FD-019, FD-020, FD-022 to FD-024. The list came from a reader and is UNVERIFIED.
- Who rules: only the studio head (the human who runs the studio) rules on the real-run quarantine; no date is set. Until then FD-001 and FD-003 have owner studio head and next step "rule on real-run".
- The claim "none describes the take stores" sits in the Stores section and cites FD-013 (not FD-014).
- Coverage: 38 of 137 files READ; 99 NOT-READ (list in Checkpoint).

## Terms
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
take = the filmed run of the lead-intake demo on made-up data. desk = the earlier lead-handling demo product; "retired from the take" = the studio lead's decision that its store is not used in the take, resting on lines 7 and 15 of DECISION-one-store.md (root copy 20 lines or inputs/ copy 28 lines; source unknown), which this lane never opened: UNVERIFIED, so rows FD-013 and FD-014 carry "premise unverified". lane = one read-only audit slice. job key = a label for what a store or job is for: LOG, RETRY, COUNTER, STORE, NOTICE, FILTER, OTHER. studio lead = the Claude session doing the technical steps. PLAN table = the severity table of PLAN-002.md. Mode A = NOT RECORDED.

# Lane L4c

<!-- LANE-KEY -->
> KEY (inline, added 16 Nov 2026, so this page can be read alone)
> - take = the one recorded run of the lead-intake demo (made-up data, run through n8n), planned for 23 Nov 2026.
> - lane = one read-only audit pass over a set of files by one agent. L1c, L3c, L4c, L5ac are continuation lanes that read what the first lane left. Findings are cited by id (for example L1c-FD-003 = finding 3 of lane L1c), not by line number; the merged list is merged-findings.md.
> - Size columns are bytes unless the header says otherwise.
> - Status words: READ = opened fully, apart from any cut named in the row. READ-TRUNCATED = opened fully but long lines were cut at the length named in the row. SKIMMED = only headers, search hits or a first and last slice read. LISTED-ONLY = name and size seen, contents not opened. NOT-READ = not opened (older rows also use it for "only the top read": treat those as LISTED-ONLY). OWNER-ONLY = never opened. Draw no conclusion from the absence of findings in a file that is not READ.
> - UNVERIFIED = no source file states it and nobody checked. NOT FOUND = searched, none found. N/A = does not apply (the reason follows).
> - Job keys (what a component does): COUNTER counts events; FILTER refuses input; RETRY repeats a failed step; LOG records output; STORE holds data; NOTICE alerts a person; OTHER none of these.
> - DECISION line N = line N of DECISION-one-store.md (decision 10 of inputs/DECISIONS-2026-11-16.md names that file and its line 14; two copies exist and which one is meant is not recorded). The sentence on line N is NOT RECORDED here, so every finding citing one is UNVERIFIED.
> - The lead / lead session = the Claude session giving orders. Studio lead = the Claude session doing the technical steps. Other terms: GLOSSARY.md.

> PURPOSE: this page records which files the lane opened, how far it read each, and which findings it raised, so the lead can decide what to fix. It states no result about the system itself beyond the findings cited by id.

<!-- TABLE-KEY -->
> TABLE KEY (added 16 Nov 2026). Coverage tables on this page have the columns: path | size in bytes | status | note. If a row says SKIMMED but its note says "not opened", read it as LISTED-ONLY (name, size, and where the note says so a checksum; contents not read). If a note says only a grep or a count line was taken, the file's contents were not read and no claim on this page rests on them. A size of 0 means the file is empty. A note repeated on many rows describes the method for the whole group; it is not a per-file result. Where a note names a search (grep) without its pattern or its hits, the pattern and the hits are NOT RECORDED.

NOTE 16 Nov 2026 (system-map session): this lane marked seven files under handover/demo/real-run/ as READ before decision 5 (the lead reads only masked take outputs, never owner-only or real-run folders) was applied. Whether these files are masked builder notes or owner-only is NOT known: the studio lead must say. Until then the continuation lane must not open real-run, and nothing in this file may be used for the take. Line 146 'none describes the take stores' holds only for the 38 files read, not for all 137.

## Coverage
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
Lane is PARTIAL. READ 38, SKIMMED 0, NOT-READ 99 (of 137). Honest reason: the 137 reports hold about 1.4 MB of text; my context budget ran out after 38 full reads, so the other 99 were not opened (not even grepped as "nothing found"). They are NOT-READ and a second continuation lane is needed for them. Nothing in this file says "nothing found" about a NOT-READ file. A grep for postgres, mf_leads, stage.journal, sqlite and journal over the folder list was run only to find where to read first; it is not a read.
| path | bytes | status | note |
|---|---|---|---|
| handover/demo/coverage/REVIEW-1.md | 11761 | READ | full |
| handover/demo/coverage/REVIEW-2.md | 10480 | READ | full |
| handover/demo/coverage/REVIEW-3.md | 11357 | READ | full |
| handover/demo/fixes/PLAN-v2-pillow-draft.md | 5566 | NOT-READ | not opened (budget); name says draft of the own-Pillow plan, likely superseded, UNVERIFIED |
| handover/demo/fixes/REVIEW-1.md | 8967 | READ | full |
| handover/demo/fixes/REVIEW-2.md | 14100 | NOT-READ | not opened (budget) |
| handover/demo/fixes/REVIEW-3.md | 8326 | READ | full |
| handover/demo/gitleaks/REVIEW-1.md | 9543 | READ | full |
| handover/demo/gitleaks/REVIEW-2.md | 10133 | READ | full |
| handover/demo/hang/REVIEW-1.md | 4862 | READ | full |
| handover/demo/hang/REVIEW-2.md | 4953 | READ | full |
| handover/demo/layout/REVIEW-1.md | 12731 | NOT-READ | not opened (budget) |
| handover/demo/layout/REVIEW-2.md | 4235 | READ | full |
| handover/demo/layout/REVIEW-3.md | 4788 | READ | full |
| handover/demo/real-run/NOTES-desk-address-required.md | 7660 | READ | full |
| handover/demo/real-run/NOTES-start-prompt.md | 9676 | READ | full |
| handover/demo/real-run/REVIEW-core-hunks-v6-fresh.md | 15022 | NOT-READ | not opened (budget) |
| handover/demo/real-run/REVIEW-real-run-v6-fresh.md | 16342 | READ | full |
| handover/demo/real-run/REVIEW-start-prompt-fresh.md | 19359 | NOT-READ | not opened (budget) |
| handover/demo/real-run/REVIEW-v2-fresh.md | 7144 | READ | full |
| handover/demo/real-run/REVIEW-v3-fresh.md | 9964 | READ | full |
| handover/demo/real-run/REVIEW-v4-fresh-copy.md | 10885 | NOT-READ | same byte size as REVIEW-v4-fresh.md; L4-FD-008 says byte-identical (md5); I did not compare, so not counted as read |
| handover/demo/real-run/REVIEW-v4-fresh.md | 10885 | READ | full |
| handover/demo/real-run/REVIEW-v5-fresh.md | 18354 | READ | full |
| handover/demo/semgrep/NOTES-semgrep-v5.md | 7064 | NOT-READ | not opened (budget) |
| handover/demo/semgrep/REVIEW-1.md | 18832 | NOT-READ | not opened (budget) |
| handover/demo/semgrep/REVIEW-2.md | 4518 | READ | full |
| handover/demo/semgrep/REVIEW-3.md | 4077 | READ | full |
| handover/demo/semgrep/REVIEW-4.md | 4316 | READ | full |
| handover/demo/semgrep/REVIEW-5-delta.md | 3131 | READ | full |
| handover/demo/semgrep/REVIEW-6-v5-fresh.md | 9531 | NOT-READ | not opened (budget) |
| handover/demo/semgrep/SUMMARY-14b.md | 3327 | READ | full |
| handover/demo/semgrep/SUMMARY-14c.md | 2501 | READ | full |
| handover/demo/semgrep/main-61ded9e-v8/REVIEW-semgrep-v8-fresh.md | 12029 | NOT-READ | not opened (budget) |
| handover/demo/semgrep/main-61ded9e-v8/semgrep-pr-body-v8.md | 27169 | NOT-READ | not opened (budget) |
| handover/demo/semgrep/main-61ded9e-v8/semgrep-pr-claims-v8.md | 22689 | NOT-READ | not opened (budget) |
| handover/demo/semgrep/main-61ded9e-v9/semgrep-pr-body-v9.md | 28260 | NOT-READ | not opened (budget) |
| handover/demo/semgrep/main-61ded9e/REVIEW-semgrep-v7-fresh.md | 9564 | NOT-READ | not opened (budget) |
| handover/demo/semgrep/main-61ded9e/semgrep-pr-body-v7.md | 22066 | NOT-READ | not opened (budget) |
| handover/demo/semgrep/main-61ded9e/semgrep-pr-claims-v7.md | 19116 | NOT-READ | not opened (budget) |
| handover/demo/skips/CRLF-EMULATION.md | 4276 | NOT-READ | not opened (budget) |
| handover/demo/skips/CRLF-GUARD-NOTES.md | 2290 | NOT-READ | not opened (budget) |
| handover/demo/skips/CRLF-GUARD-V3-NOTES.md | 965 | READ | full |
| handover/demo/skips/CRLF-GUARD-V4-NOTES.md | 1464 | READ | full |
| handover/demo/skips/CRLF-GUARD-V5-NOTES.md | 3823 | NOT-READ | not opened (budget) |
| handover/demo/skips/CRLF-GUARD-V6-NOTES.md | 13154 | NOT-READ | not opened (budget) |
| handover/demo/skips/REVIEW-crlf-sonaryaml-v3-fresh.md | 9245 | NOT-READ | not opened (budget) |
| handover/demo/skips/REVIEW-crlf-v4-yaml-delta-fresh.md | 11756 | NOT-READ | not opened (budget) |
| handover/demo/skips/REVIEW-crlf-v5-yaml-trimmed-fresh.md | 11405 | NOT-READ | not opened (budget) |
| handover/demo/skips/REVIEW-crlf-v6-fresh.md | 15051 | NOT-READ | not opened (budget) |
| handover/demo/skips/REVIEW-crlf-v7-fresh.md | 13890 | NOT-READ | not opened (budget) |
| handover/demo/skips/evidence-b10-8-mutant-table.md | 5075 | NOT-READ | not opened (budget) |
| handover/demo/skips/evidence-b13-4-mutant-table.md | 7974 | NOT-READ | not opened (budget) |
| handover/demo/skips/evidence-b15-4-mutant-table.md | 10829 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-nodemo-ci-v4.md | 13013 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-nodemo-v2.md | 6891 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-nodemo-v3.md | 12176 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-nodemo-v4.md | 6490 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-nodemo.md | 5280 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p1-quickwins-v2.md | 7828 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p1-quickwins-v3.md | 9616 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p1-quickwins-v31.md | 10017 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p1-quickwins-v32.md | 10951 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p1-quickwins-v321.md | 9192 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p1-quickwins.md | 5310 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p2-feed-constants.md | 2110 | READ | full |
| handover/demo/sonar/NOTES-p2-optional-gaps.md | 5751 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p2-v2.md | 11525 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p2-v21.md | 6023 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p2-v22.md | 3488 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p2-v23.md | 4017 | READ | full |
| handover/demo/sonar/NOTES-p2.md | 7961 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p3-final-v2.md | 8245 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p3-final.md | 13136 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p3-path-helper-v2.md | 10668 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p3-path-helper-v3.md | 8694 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p3-path-helper.md | 6644 | NOT-READ | not opened (budget) |
| handover/demo/sonar/NOTES-p3-probes.md | 3218 | NOT-READ | not opened (budget) |
| handover/demo/sonar/PROBE-AB-NOTE.md | 5955 | NOT-READ | not opened (budget) |
| handover/demo/sonar/PROBE-AB-V2-NOTE.md | 13864 | NOT-READ | not opened (budget) |
| handover/demo/sonar/PROBE-AB-V3-NOTE.md | 22433 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-flaky413-fresh.md | 6596 | NOT-READ | not opened (budget); review of the unmerged flaky-413 fix named in REVIEW-p2v23-fresh.md:8 |
| handover/demo/sonar/REVIEW-nodemo-ci-v4-fresh4.md | 17636 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-nodemo-fresh.md | 9285 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-nodemo-optional-v4-partial.md | 5340 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-nodemo2-fresh.md | 10890 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-nodemo3-fresh.md | 11925 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p1-fresh.md | 9397 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p1v2-fresh.md | 9564 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p1v3-fresh.md | 11838 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p1v31-fresh.md | 9025 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p1v32-fresh.md | 7317 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p1v321-fresh.md | 7239 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p2-fresh.md | 18947 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p2-optional-gaps-fresh.md | 8676 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p2-optional-pair-fresh.md | 7420 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p2v2-fresh.md | 10698 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p2v21-fresh.md | 9820 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p2v22-fresh.md | 6471 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p2v23-fresh.md | 8667 | READ | full |
| handover/demo/sonar/REVIEW-p3-fresh.md | 16445 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p3-minors-risky-fresh.md | 17487 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p3-v21-fresh.md | 13158 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p3final-fresh.md | 10620 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-p3v3-fresh.md | 14956 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-probe-p3v2-fresh.md | 16924 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-probe2-fresh.md | 13836 | NOT-READ | not opened (budget) |
| handover/demo/sonar/REVIEW-probe3-fresh.md | 8596 | NOT-READ | not opened (budget) |
| handover/demo/triage/CODEANT-COVERAGE.r2.md | 40551 | NOT-READ | not opened (budget); superseded copy of CODEANT-COVERAGE.md per SUMMARY-codeant3-rt.md:10 (old copy r2) |
| handover/demo/triage/PATCH-NOTES.md | 6843 | READ | full |
| handover/demo/triage/RESOLVE-js.md | 7747 | READ | full |
| handover/demo/triage/REVIEW-codeant-A.md | 14587 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant-B.md | 11803 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant-C.md | 14048 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant2-rt-A.md | 4240 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant2-rt-B.md | 4644 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant2-sec.md | 20555 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant3-rt-A.md | 5877 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant3-rt-B.md | 5001 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant3-sec.md | 3699 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant4-rt.md | 4143 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant4-sec.md | 4951 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant5-rt-delta.md | 3349 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant5-sec.md | 5739 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-codeant6-sec-nits.md | 3840 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-extra.md | 7899 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-js-2.md | 6559 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-js.md | 5181 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-py-2.md | 7063 | NOT-READ | not opened (budget) |
| handover/demo/triage/REVIEW-py.md | 6436 | NOT-READ | not opened (budget) |
| handover/demo/triage/SUMMARY-codeant2-runtime.md | 4071 | READ | full |
| handover/demo/triage/SUMMARY-codeant2-sec.md | 8449 | READ | full |
| handover/demo/triage/SUMMARY-codeant3-rt.md | 9083 | READ | full |
| handover/demo/triage/SUMMARY-codeant3-sec.md | 3341 | READ | full |
| handover/demo/triage/SUMMARY-codeant4-sec.md | 3644 | READ | full |
| handover/demo/triage/SUMMARY-codeant5-sec.md | 3530 | READ | full |
| handover/demo/triage/SUMMARY-codeant6-sec-nits.md | 4169 | READ | full |

## Components
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
General finding for the 38 files read: they are builder notes and fresh-reviewer reports about patches to the desk (the Mode A product), its CI checks and its scripts. None describes the take's own stores (Postgres `mf_leads`, `stage.journal`, n8n data); see L4c-FD-014 and L4-FD-001.
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L4c-C-001 | desk HTTP server (src/lead_desk/server.py) | receives leads and steps; core code touched by a pending patch (drain of the request body on 413 and 501) | `handover/demo/triage/SUMMARY-codeant2-runtime.md:4 "answered without draining the body"` | OTHER |
| L4c-C-002 | desk mirror worker (CRM copy) | copies leads to the CRM stand-in with a per-lead busy wait; has its own retry counter | `handover/demo/triage/SUMMARY-codeant2-runtime.md:10 "never reaches MIRROR_MAX_TRIES by itself if the hang lasts"` | RETRY |
| L4c-C-003 | fake HubSpot server and fake model server (demo_only) | stand-ins used by tests and dry runs; guarded by one lock | `handover/demo/triage/SUMMARY-codeant2-runtime.md:14 "one locked public view"` | OTHER |
| L4c-C-004 | desk portal pages (CSS and JS) | the portal screens that the take retires | `handover/demo/layout/REVIEW-3.md:7 "CORE vs DEMO (lead must approve core CSS in the PR text)"` | STORE |
| L4c-C-005 | sonar.yml workflow (GitHub Actions) | runs tests with coverage then the Sonar scan; the only place SONAR_TOKEN is used | `handover/demo/coverage/REVIEW-3.md:19 "SHA pins char by char"` | OTHER |
| L4c-C-006 | semgrep.yml workflow (GitHub Actions) | runs the Semgrep scan on pull requests and main | `handover/demo/semgrep/REVIEW-5-delta.md:3 "has only pull_request to main and push to main"` | OTHER |
| L4c-C-007 | secret-scan config (.gitleaks.toml, exceptions.txt, tools/hygiene.py) | decides which text counts as a leak; allowlists for lock-file hashes and the public Sonar project key | `handover/demo/gitleaks/REVIEW-2.md:12 "pipeline compiles every exception with Python"` | FILTER |

## Stores
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
All stores below belong to the desk or to review tooling. None is a store of the take per DECISION-one-store.md.
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4c-S-001 | desk lead book (SQLite file, DESK_DB_PATH) | lead rows, send state, stage, wait | desk (retired from the take: DECISION line 15) | leads from server and mirror | rows read by portal and checks | busy database is swallowed and logged; row stays and shows as stalled | up to 3 tries on a plain busy error, 1 try when the write gate ran out | write deadline from WRITE_DEADLINE_SECONDS (value NOT FOUND in files read) | stage rank guard: same rank does not move | desk log (plain text) | desk process (identity detail UNVERIFIED) | tests/test_sonar_p2_gaps.py (18 tests) | desk, portal, check_invariants | `handover/demo/sonar/NOTES-p2-v23.md:10 "other busy errors are tried LOCK_RETRIES (3) times"` | STORE |
| L4c-S-002 | desk lock file next to the book | one desk per book | desk | start of desk | lock file | refused for a memory book, but the lock file appears before the refusal in old code | N/A: file lock | UNVERIFIED | N/A: lock | none | desk process | tests/test_codeant_desk.py (name from SUMMARY, file not read) | desk start | `handover/demo/triage/SUMMARY-codeant2-runtime.md:9 "file appears before the"` | STORE |
| L4c-S-003 | live-model spend ledger file | running total of spend for the live check | run_live_check.py and run_real_check.py --live-model | model calls | cap decision | garbage, folder or 9 MB file is refused with a fixed line before the question | N/A: one try | a FIFO path can block 12 s (measured) | reserve then settle is NOT read in these files; UNVERIFIED | none | script user | tests/test_take_script_refusals.py | live check scripts | `handover/demo/real-run/REVIEW-v3-fresh.md:14 "the spend ledger could not be read or written"` | STORE |
| L4c-S-004 | real-run result file (REAL_RESULT_FILE) | final counts of a real check | run_real_check.py | end of run | JSON file | write failure gives one fixed line, exit 3, clean-up still runs | N/A: one write | N/A: no timeout | overwrite; may equal another file the config names | none | script user | tests/test_take_script_refusals.py | owner or lead reading counts | `handover/demo/real-run/REVIEW-v5-fresh.md:21 "NIT 5: REAL_RESULT_FILE may name an existing file that matters"` | STORE |
| L4c-S-005 | fake HubSpot call record (desk-1.hubspot.json) | counts calls and creates made to the CRM stand-in | desk dry-run harness | CRM calls | calls and created counters | N/A: output file | N/A: none | N/A: none | N/A: counter file | file itself | harness | harness checks | reviewers | `handover/demo/real-run/REVIEW-v4-fresh.md:5 "calls 52, created 0"` | COUNTER |
| L4c-S-006 | desk log (desk-1.log in the run folder) | desk text log for a run | desk | desk events | text lines | tracebacks end up here when a setting is refused after the question | N/A: log | N/A: none | N/A: append | file | desk process | read by reviewers | reviewers | `handover/demo/real-run/REVIEW-v3-fresh.md:10 "the desk ended while starting"` | LOG |

## Workflows
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4c-W-001 | n8n proof recipe (proof.json result rule) | independent check of one run: exactly one new, nine duplicate, one email, one CRM row | n8n Code node plus the desk (take owner NOT decided here) | replies from the desk and fakes | MATCH or MISMATCH text | false MISMATCH under a 503 busy answer (start again) | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | rule tested in node with stand-in values only (10 reply sets) | owner step recipe | `handover/demo/triage/SUMMARY-codeant2-sec.md:26 "the rule was checked in node only"` | COUNTER |

## Workflow walk
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
| id | flow | node | type | trigger or branch | error path | retry or timeout | on kill or restart | on duplicate | on out-of-order | on empty or huge input | writes where | person sees | identity | evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4c-WK-001 | n8n proof recipe | the Code node that waits for the desk to finish and builds the result | Code | after the desk answers | false MISMATCH under 503 per recipe | UNVERIFIED | UNVERIFIED | counts nine duplicate as expected | UNVERIFIED | UNVERIFIED | N/A: returns a value | MATCH or MISMATCH text in n8n | UNVERIFIED | `handover/demo/triage/SUMMARY-codeant2-sec.md:6 "A real n8n was not run"` |

## Scripts
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4c-X-001 | scripts/run_real_check.py | real-service check of the desk with a start question | script itself | config file, key files, answer at a terminal | counts, result file | refuses with one fixed line and exit 2 before the question; exit 3 on failure | N/A: no retry | UNVERIFIED | N/A: one run | stdout, result file | script user | tests/test_take_script_refusals.py, test_real_check_dry.py | lead, reviewers | `handover/demo/real-run/NOTES-start-prompt.md:18 "NEW module constant NO_TERMINAL_TEXT"` | FILTER |
| L4c-X-002 | scripts/run_live_check.py | live model check with spend ledger | script itself | key file, ledger, caps | cost banner, counts | refusal lines; no vendor default base URL after patch | N/A: no retry | UNVERIFIED | N/A: one run | stdout | script user | tests/test_live_claude.py | lead | `handover/demo/real-run/REVIEW-v5-fresh.md:18 "refusals do not follow the"` | COUNTER |
| L4c-X-003 | scripts/hubspot_probe.py | real HubSpot probe, spend consent by a numeric flag | script itself | flag --yes-spend-calls 7, token from an environment variable | CRM calls | UNVERIFIED | N/A: none | UNVERIFIED | N/A: probe | stdout | token holder | tests/test_hubspot_probe.py | lead | `handover/demo/real-run/NOTES-start-prompt.md:32 "its explicit numeric flag is the deliberate consent"` | OTHER |
| L4c-X-004 | scripts/n8n_api.py | calls the n8n API to import and activate workflows | script itself | key file, URL | workflow changes | clean SystemExit lines after patch, tracebacks before | N/A: none | UNVERIFIED | N/A: UNVERIFIED | stdout | key file holder | tests/test_n8n_api_url.py | owner steps | `handover/demo/triage/SUMMARY-codeant2-sec.md:24 "A5 n8n_api.py: reuses"` | OTHER |
| L4c-X-005 | tools/scrub_n8n_export.py | cleans an n8n export so no address, e-mail or active link remains | script itself | n8n export JSON | cleaned JSON | stated limits, not fixed | N/A: none | 2 s linearity limit in tests | N/A: pure function | none | none | tests/test_scrub_n8n_export.py | export step | `handover/demo/triage/SUMMARY-codeant5-sec.md:6 "tab/CR/LF right after a localhost host replaces the address"` | FILTER |
| L4c-X-006 | tools/hygiene.py | git grep scan minus exceptions.txt | script itself | patterns.txt, exceptions.txt | list of hits | any hit fails test_hygiene | N/A: none | N/A: none | N/A: pure | none | none | tests/test_hygiene.py | CI | `handover/demo/gitleaks/REVIEW-2.md:12 "pipeline compiles every exception with Python"` | FILTER |

## Jobs
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4c-J-001 | desk locked-database retry (_locked_retry) | tries a busy write again | desk (conflicts with DECISION line 7: the take retries through the n8n recovery flow) | busy database error | success or swallow with log | swallowed and logged, row shows stalled | 3 tries; 1 try for a spent write gate | write deadline | UNVERIFIED | desk log | desk process | tests/test_sonar_p2_gaps.py | desk | `handover/demo/sonar/NOTES-p2-v23.md:10 "sqlite3.OperationalError with the text"` | RETRY |
| L4c-J-002 | desk mirror busy wait (10, 60, 180, 420 s) | waits longer after repeated refusals of the same lead | desk (retired from the take: DECISION line 15) | refused mirror call | wait then try | never reaches MIRROR_MAX_TRIES if the hang lasts | escalating wait | the wait values | count keyed by stage rank and count | desk log | desk process | focused tests in the patch set | desk | `handover/demo/triage/SUMMARY-codeant3-rt.md:11 "Mirror busy wait escalates on repeated refusals"` | RETRY |
| L4c-J-003 | start-question terminal guard | refuses to start a real run unless stdin is a terminal and the destination host is typed | terminal_guard.ask_to_start | stdin, typed host | start or refusal | a pty-driven program can still type the host | N/A: none | N/A: none | N/A: one answer | stdout | person at a terminal | tests/test_real_run_v6.py (named in the review) | run_real_check.py, run_live_check.py | `handover/demo/real-run/REVIEW-real-run-v6-fresh.md:21 "terminal_guard.ask_to_start"` | FILTER |
| L4c-J-004 | spend and call counters in dry and live checks | cap on live spend, counts of CRM calls | scripts plus SpendLedger | model calls | totals | refusal at the cap | N/A: none | N/A: none | UNVERIFIED | ledger file | script user | tests/test_ledger_amounts.py | scripts | `handover/demo/real-run/REVIEW-v4-fresh.md:7 "adds no caller in the desk, takes no lock"` | COUNTER |
| L4c-J-005 | independent count rule in n8n (proof.json) | one new and nine duplicate, one email, one CRM row | n8n Code node | desk replies | MATCH or MISMATCH | false MISMATCH on 503 | start again | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | node stand-in only | owner step | `handover/demo/triage/SUMMARY-codeant2-sec.md:26 "(any order), 1 email and 1 CRM row"` | COUNTER |
| L4c-J-006 | secret-scan allowlists | decides what text is allowed to look like a key | .gitleaks.toml and exceptions.txt | file text | pass or leak | hidden finding if too wide | N/A: none | N/A: none | N/A: pure | none | CI | tests/test_hygiene.py, test_exceptions_narrow | CI | `handover/demo/gitleaks/REVIEW-2.md:13 "REAL HOLE worth telling the owner"` | FILTER |
| L4c-J-007 | nosemgrep form guard | refuses any inline suppression that is not of the form nosemgrep colon rule id | tests/test_nosemgrep_form.py | repo files | pass or fail | bare nosem hides everything (found in round 2) | N/A: none | N/A: none | N/A: pure | none | CI | tests/test_nosemgrep_form.py (54 to 63 cases) | CI | `handover/demo/semgrep/SUMMARY-14b.md:6 "old test missed 23 of the 24 new shapes"` | FILTER |
| L4c-J-008 | refusal messages (fixed one-line texts) | tells the person why a start was refused | scripts | bad setting | one line `refused: NAME: text` | mixed formats remain | N/A: none | N/A: none | N/A: pure | stdout | script user | tests/test_take_script_refusals.py | person at terminal | `handover/demo/real-run/REVIEW-v4-fresh.md:14 "three refusal formats are mixed in the same script"` | NOTICE |

## Credentials
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
Names only, no values were seen.
| id | name | purpose | job owner | inputs | outputs | failure path | retry | timeout | idempotency | logs to | identity | tested where | used by | evidence | job keys |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L4c-K-001 | DESK_HUBSPOT_KEY_FILE | HubSpot key file path | desk | N/A: credential | N/A: credential | refused before the question if unreadable or not one line | N/A: credential | N/A: credential | N/A: credential | none | desk | test_take_script_refusals.py | desk, scripts | `handover/demo/real-run/REVIEW-v4-fresh.md:33 "DESK_SMTPP_PASSWORD_FILE"` | OTHER |
| L4c-K-002 | DESK_SMTPP_PASSWORD_FILE | SMTP password file path | desk | N/A: credential | N/A: credential | same refusal | N/A: credential | N/A: credential | N/A: credential | none | desk | test_take_script_refusals.py | desk mail sender | `handover/demo/real-run/REVIEW-v3-fresh.md:26 "refused: DESK_SMTPP_PASSWORD_FILE"` | NOTICE |
| L4c-K-003 | REAL_IMAP_n_PASSWORD_FILE (n = 1 and 2) | mailbox password files for the independent mail count | scripts | N/A: credential | N/A: credential | same refusal | N/A: credential | N/A: credential | N/A: credential | none | scripts | test_take_script_refusals.py | run_real_check.py | `handover/demo/real-run/REVIEW-v3-fresh.md:29 "REAL_IMAP_2_PASSWORD_FILE"` | NOTICE |
| L4c-K-004 | DESK_LIVE_KEY_FILE | live model key file | scripts | N/A: credential | N/A: credential | refused if two lines or too short | N/A: credential | N/A: credential | N/A: credential | none | scripts | test_core_key_readers (named in v6 review) | run_live_check.py | `handover/demo/real-run/REVIEW-v5-fresh.md:9 "the FIXES.md v5 claim"` | OTHER |
| L4c-K-005 | SONAR_TOKEN | Sonar scan token (GitHub secret) | sonar.yml scan step | N/A: credential | N/A: credential | test code and scan share one runner | N/A: credential | N/A: credential | N/A: credential | none | GitHub Actions | N/A: not testable offline | sonar.yml | `handover/demo/coverage/REVIEW-1.md:6 "the secret-holding scan step"` | OTHER |
| L4c-K-006 | n8n API key file (setting name NOT FOUND in the files read) | key for scripts/n8n_api.py | scripts | N/A: credential | N/A: credential | key could be sent to a second server on redirect in old code | N/A: credential | N/A: credential | N/A: credential | none | scripts | tests/test_n8n_api_url.py | n8n_api.py | `handover/demo/triage/SUMMARY-codeant2-sec.md:24 "on the old code the second server receives the key"` | OTHER |

## Docs and tests and folders
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
| id | name | purpose | evidence | job keys |
|---|---|---|---|---|
| L4c-D-001 | triage/SUMMARY-codeant*-sec and -rt files | builder hand-backs for CodeAnt fix rounds 2 to 6; unreviewed when written | `handover/demo/triage/SUMMARY-codeant5-sec.md:1 "previous versions kept as codeant3-*-r4.patch"` | OTHER |
| L4c-D-002 | real-run/REVIEW-v2..v5 and v6 | fresh reviewer reports of the real-run patch chain | `handover/demo/real-run/REVIEW-v5-fresh.md:9 "the FIXES.md v5 claim"` | OTHER |
| L4c-T-001 | tests/test_take_script_refusals.py | refusals before the start question (118 tests in v5) | `handover/demo/real-run/REVIEW-v5-fresh.md:67 "test_take_script_refusals(118)"` | FILTER |
| L4c-T-002 | tests/test_server_stop_guard.py | diagnostic guard that a stop must return within a bound | `handover/demo/hang/REVIEW-2.md:3 "test_server_stop_guard.py module docstring"` | RETRY |
| L4c-T-003 | tests/test_nosemgrep_form.py | guard on inline suppressions | `handover/demo/semgrep/REVIEW-5-delta.md:7 "tests/test_nosemgrep_form.py 63 passed"` | FILTER |
| L4c-T-004 | tests/keep_scan.py | tripwire for tests that leave temp folders | `handover/demo/real-run/REVIEW-real-run-v6-fresh.md:44 "a tripwire only"` | FILTER |
| L4c-F-001 | handover/demo/triage, sonar, semgrep, skips, real-run, layout, coverage, fixes, gitleaks, hang | patch builder notes, reviews and evidence about the desk and its CI | `handover/demo/triage/PATCH-NOTES.md:11 "do NOT convert now"` | OTHER |

## Findings
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
Severity by the PLAN table. Several Blockers are fixed only in pending patches (not merged): that is stated, not deferred.
| id | claim type | severity | evidence | conflicts with | job key |
|---|---|---|---|---|---|
| L4c-FD-001 | security | Blocker | A default address that is the vendor's own sent the key to the vendor when the setting was omitted (a reviewer's valid test config made 52 attempts with a made-up key); fixed only in the pending desk-address-required patch, which touches core src and needs the lead's approval: `handover/demo/real-run/REVIEW-v4-fresh.md:5 "towards the vendor's default address with a made-up key"`; `handover/demo/real-run/NOTES-desk-address-required.md:8 "a default address that is the vendor's own"` | none | OTHER |
| L4c-FD-002 | security | Blocker | n8n API key: old code sent the key to a second server after a redirect and printed a key in a traceback for a two-line key file; fixed only in pending codeant patches (apply order matters): `handover/demo/triage/SUMMARY-codeant2-sec.md:24 "on the old code the second server receives the key"`; `handover/demo/triage/SUMMARY-codeant5-sec.md:4 "r4 code printed a traceback ending"` | none | OTHER |
| L4c-FD-003 | security | Blocker | scripts/hubspot_probe.py confirms a real spend by a numeric flag with no terminal test; the builder left it unchanged and called it a decision for the lead; the v6 reviewer lists it as open: `handover/demo/real-run/NOTES-start-prompt.md:32 "its explicit numeric flag is the deliberate consent"`; `handover/demo/real-run/REVIEW-real-run-v6-fresh.md:75 "confirms a real spend by a flag"` | none | OTHER |
| L4c-FD-004 | security | Major | The gitleaks exception for the public Sonar project key was wider than the toml allowlist and hid any lowercase made-up key after the prefix; gitleaks itself does not flag a lowercase high-entropy value after such a key, so one layer only guards it; keys under 40 characters are caught by neither layer. Extends L4-FD-013: `handover/demo/gitleaks/REVIEW-2.md:13 "REAL HOLE worth telling the owner"` | `handover/demo/gitleaks/SUMMARY.md:8 "sonar-project.properties line 4"` | FILTER |
| L4c-FD-005 | security | Major | Lock-file hash allowlists are unanchored in several patches (interim): a nested copy of a lock file passes gitleaks until the anchored line lands; the tightening is only in a note and depends on codeant3-gitleaks changing the scan to run from the repo root: `handover/demo/triage/SUMMARY-codeant4-sec.md:13 "unanchored reports no nested copy (hole)"`; `handover/demo/fixes/REVIEW-3.md:15 "Interim state acceptable"` | none | FILTER |
| L4c-FD-006 | security | Major | The scrub tool leaves two address shapes uncleaned and the builder pinned them as tests instead of fixing them; the studio rule is fix, not document: `handover/demo/triage/SUMMARY-codeant2-sec.md:11 "Two scrub limits are stated and pinned as tests rather than fixed"` | none | FILTER |
| L4c-FD-007 | inconsistent | Major | The v5 write-up claimed one core file was touched; the reviewer measured three: `handover/demo/real-run/REVIEW-v5-fresh.md:9 "the FIXES.md v5 claim"` | none | OTHER |
| L4c-FD-008 | inconsistent | Major | Real-run patch chain conflicts: start-prompt-hardening and v5 do not apply on each other and disagree on the no-terminal exit code (1 versus 2); older v4-after-p3 does not apply on p3 v2 or v3: `handover/demo/real-run/REVIEW-v5-fresh.md:77 "does not apply on v5"` | none | OTHER |
| L4c-FD-009 | duplicate | Major | Superseded patch versions are kept next to the live ones (codeant, codeant2, codeant3 with -r3 -r4 copies; old codeant-* obsolete) so a reader cannot tell which is current: `handover/demo/triage/SUMMARY-codeant3-rt.md:1 "the old codeant-* are obsolete"`; `handover/demo/triage/SUMMARY-codeant5-sec.md:1 "previous versions kept as codeant3-*-r4.patch"` | none | OTHER |
| L4c-FD-010 | inconsistent | Major | Contradicting claims about whether a patch applies: builder 10c-2 says docs-and-deps does not apply on 0841f36, lane 8 evidence says it does; the coverage evidence described a patch version that is no longer the file on disk: `handover/demo/triage/SUMMARY-codeant2-runtime.md:7 "CONTRADICTS lane 8 evidence-d6"`; `handover/demo/gitleaks/REVIEW-2.md:5 "evidence out of date"` | none | OTHER |
| L4c-FD-011 | inconsistent | Major | Extends L4-FD-003: more unreconciled test totals (2349 passed plus 116 skipped; 2462 and 3; 2513 and 3; 2579 passed and 2 failed in one serial run); a stated Node explanation contradicts the raw log: `handover/demo/fixes/REVIEW-1.md:7 "the 2349/116 run HAD Node"`; `handover/demo/fixes/REVIEW-3.md:18 "2513 vs 2462 differs by 51"`; `handover/demo/triage/SUMMARY-codeant2-runtime.md:6 "2 failed, 2579 passed, 2 skipped, 1070 s"` | `handover/demo/skips/SKIP-TABLE.md:9 "cannot be reconciled to a test list"` | COUNTER |
| L4c-FD-012 | inconsistent | Major | Extends L4-FD-005: one builder places the 38 percent full-suite hang in the head (a portal restart test) while the hang reviewer says the cause stays unproven and the fix is only a diagnostic guard: `handover/demo/triage/SUMMARY-codeant3-rt.md:29 "the 38% hang was in the head"` | `handover/demo/hang/REVIEW-2.md:3 "cause UNPROVEN"` | RETRY |
| L4c-FD-013 | duplicate | Major | The desk owns three retry mechanisms (locked-database retry, mirror busy wait with 10 60 180 420 s, reaper stop guard); DECISION gives the take one recovery path through n8n and `mf_leads`: `handover/demo/sonar/NOTES-p2-v23.md:10 "other busy errors are tried LOCK_RETRIES (3) times"`; `handover/demo/triage/SUMMARY-codeant3-rt.md:11 "Mirror busy wait escalates on repeated refusals"` | DECISION line 15 | RETRY |
| L4c-FD-014 | idle | Major | CONFLICT WITH DECISION line 15: portal CSS and JS rounds (drawer, phone layout, 504 var statements) are reviewed and patched for a portal the take retires; one of them is explicitly parked for the laptop: `handover/demo/layout/REVIEW-3.md:7 "CORE vs DEMO (lead must approve core CSS in the PR text)"`; `handover/demo/triage/PATCH-NOTES.md:11 "do NOT convert now"` | DECISION line 15 | STORE |
| L4c-FD-015 | unverified | Major | Extends L4-FD-010: the independent count rule for n8n (one new, nine duplicate, one email, one CRM row) was only checked in node with stand-in values; no real n8n run: `handover/demo/triage/SUMMARY-codeant2-sec.md:6 "A real n8n was not run"`; `handover/demo/triage/SUMMARY-codeant2-sec.md:26 "the rule was checked in node only"` | none | COUNTER |
| L4c-FD-016 | unverified | Major | Never run in the real system: Sonar scanner acceptance of coverage.xml, any GitHub run of the Semgrep workflow, the docker form of the lock command, Windows: `handover/demo/coverage/REVIEW-1.md:2 "Real sonar-scanner acceptance of coverage.xml is UNVERIFIED"`; `handover/demo/semgrep/SUMMARY-14c.md:2 "NOT run: docker lock command, any GitHub run, the full suite"` | none | OTHER |
| L4c-FD-017 | inconsistent | Major | Corrects L4-FD-016: the lead did run the Semgrep registry scan (ERROR-level clean at 0841f36, image 1.185.0, without --strict); L4-FD-016 quotes the older summary line that says the registry is blocked: `handover/demo/semgrep/SUMMARY-14b.md:10 "ERROR-level clean on the stack head at 0841f36 as of the lead's run"`; `handover/demo/semgrep/REVIEW-3.md:8 "the lead's run (lead-registry-run.txt:3) omitted"` | `handover/demo/semgrep/SUMMARY.md:3 "The Semgrep registry is blocked"` | FILTER |
| L4c-FD-018 | inconsistent | Major | Corrects L4-FD-002: the final docs-and-deps route drops the need for Pillow (decode in the browser, hashed browser lock with zero Pillow); the own-decoder and Pillow drafts are superseded; the missing-module line still prints in a run log while tests passed: `handover/demo/triage/SUMMARY-codeant2-runtime.md:6 "lane 8 replaced Pillow by in-browser decode"`; `handover/demo/fixes/REVIEW-3.md:12 "0 Pillow"` | `handover/demo/fixes/PLAN.md:2 "Patch: docs-and-deps.patch"` | OTHER |
| L4c-FD-019 | ops | Major | Reviewer and builder hygiene slips against the studio rules: a pkill of a process not known to be the reviewer's own, a folder left outside the work area, real outbound attempts with a made-up key, and 986 temp folders from earlier dry runs: `handover/demo/real-run/REVIEW-v2-fresh.md:65 "without being sure the process was mine"`; `handover/demo/real-run/REVIEW-v3-fresh.md:20 "Please remove by hand"`; `handover/demo/real-run/REVIEW-v5-fresh.md:69 "folders on this machine are from earlier runs of other agents"` | none | OTHER |
| L4c-FD-020 | unverified | Major | After the P3 change no test runs a config-driven real run past the start question; only the dry-fakes self-test does, and it ignores the config: `handover/demo/real-run/REVIEW-real-run-v6-fresh.md:47 "NO test runs a config-driven run past the question"` | none | OTHER |
| L4c-FD-021 | ops | Major | A pre-existing flaky test (413 body drain, fails 3 of 15 idle runs) has an unmerged fix patch and falsely killed mutants during a review: `handover/demo/sonar/REVIEW-p2v23-fresh.md:8 "fails 3 of 15 runs on an idle machine"` | none | OTHER |
| L4c-FD-022 | inconsistent | Nit | Refusal text forms are mixed (new form, old form, argparse form that echoes the typed value): `handover/demo/real-run/REVIEW-v4-fresh.md:14 "three refusal formats are mixed in the same script"`; `handover/demo/real-run/REVIEW-real-run-v6-fresh.md:67 "still uses plain argparse"` | none | NOTICE |
| L4c-FD-023 | unverified | Nit | The temp-folder tripwire (keep_scan) is admitted to be a tripwire only, with known wrong accepts and rejects: `handover/demo/real-run/REVIEW-real-run-v6-fresh.md:44 "a tripwire only"` | none | FILTER |
| L4c-FD-024 | ops | Nit | Builders and reviewers state they never saw the studio bible and skipped EGM (rule 1 and rule 13 of the brief): `handover/demo/real-run/NOTES-start-prompt.md:2 "R-numbers not grepped, not cited"`; `handover/demo/real-run/NOTES-start-prompt.md:3 "EGM skipped: I cannot invoke"` | none | OTHER |
| L4c-FD-025 | idle | Nit | A contingent Sonar patch is parked unpushed until a Sonar analysis finishes: `handover/demo/sonar/NOTES-p2-feed-constants.md:3 "has not been analysed yet"` | none | OTHER |
| L4c-FD-026 | inconsistent | Nit | Extends L4-FD-011: yet another base head (3598120) in the sonar series: `handover/demo/sonar/NOTES-p2-feed-constants.md:2 "base pr-3-tests 3598120"` | `handover/demo/scans/SCAN-TABLE.md:14 "2db392650e8b"` | OTHER |

## Checkpoint
> REMINDER (full KEY at page top): job keys COUNTER counts, FILTER refuses, RETRY repeats, LOG records, STORE holds, NOTICE alerts, OTHER none; UNVERIFIED = nobody checked; NOT VISIBLE = file not in this checkout; NOT FOUND = searched, absent; take = demo run planned 23 Nov 2026; DECISION line N = line N of DECISION-one-store.md (text not recorded).
Done: 38 of 137 files READ (coverage 3, fixes 2, gitleaks 2, hang 2, layout 2, real-run 7, semgrep 6, skips 2, sonar 3, triage 9). Rows: 7 components, 6 stores, 1 workflow, 1 walk row, 6 scripts, 8 jobs, 6 credentials, 7 doc/test/folder rows,  26 findings (3 labelled Blocker: FD-001, FD-002, FD-003; FD-001 and FD-003 quarantined; 18 Major, 5 Nit).
Next (for a further continuation lane): 99 NOT-READ files, in this order: real-run REVIEW-core-hunks-v6-fresh, REVIEW-start-prompt-fresh (and a md5 check of REVIEW-v4-fresh-copy); semgrep REVIEW-1, REVIEW-6, v7 to v9 pr-body and claims files (look for numbers in claims); skips CRLF notes and reviews; fixes REVIEW-2; layout REVIEW-1; triage REVIEW-codeant-A..C and codeant2-sec; sonar NOTES and REVIEW series (p1, p2, p3, nodemo, probe).
Blockers: none beyond the Status block. No file was changed except this one. No secret, key, token or personal e-mail value was copied; credentials are listed by name.
