# fix-xread: changes from reviews/crossread-branches-r1.md (2026-11-16)
Reviewer words were unverified; I checked each against our files first. Static, nothing ran. Backups: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-xread/ (FINDINGS.md, FIX-PLAN.md, DECISION-one-store.md).

Checked and confirmed in our files: DECISION-one-store.md line 7 (film-v5 and real-v5), 14 (one Postgres instance, `app` schema), 23 and 27 ("deleted at clean-up") are stale against decisions 1, 10 and Q19-1/Q21 (FIX-PLAN.md:20 says no deletion promise).

(a) inputs/DECISION-one-store.md: NOT edited (inputs/ is lead-owned). Added FINDINGS.md:60 (new NOT COVERED item 30) marking lines 7, 14, 23, 27 SUPERSEDED. LIST FOR THE LEAD: correct those four lines; the other session's owner sheets also promise deletion.
(b) FINDINGS.md:34 item 5. Before: "The lane3 raw files (HB171 ... F-c) are not in the repository. The numbers ... are relayed, raw files not seen;" After: named files not in this checkout and not found by name on the other branches; raw kill-series files DO exist on cloud/system-map (handover/demo3/kill/RESULTS.md, data/results.jsonl; copy on core-hardening c6-skip-audit/raw-lane3/); we have NOT read them, numbers stay UNVERIFIED by us.
(c) FIX-PLAN.md:8 item 3(b). Appended: loopback re-smoke fills the film-v5 stand-in flows and does not prove real-v5's HubSpot node, mail credential or DESK_URL.
(d) FIX-PLAN.md:8 item 3(b) (same line, item 3). Appended: "processed once" is proved only for a second send; a crash between mail send and the finished mark is not tested. (I used the words of the limit, not the exact quote you gave; meaning is the same.)
(e) FINDINGS.md:61 (item 31): their step-0 probe (create then try delete) vs our item-20 id probe: unknown if same step. FINDINGS.md:62 (item 32): their planted canary in the n8n SQLite WAL (RESULTS.md:40-48); B-136 must not be read as general; no Postgres-backed test. CLAIMS-TABLE.md not touched (other agent owns it).

Not done: rows 2, 3, 6, 10, 14 of the cross-read need lead rulings; the cross-read's rows on CLAIMS-TABLE/RUNSHEET are for their owners.
Outputs: count_findings.py FINDINGS.md: rows 45 unique 45; Blocker 5/7 Major... table: all 13 BEFORE, 32 AFTER, 45 total (Blocker 5, Major 7, Nit 33). check_patches.sh: PASS 4 patches.
