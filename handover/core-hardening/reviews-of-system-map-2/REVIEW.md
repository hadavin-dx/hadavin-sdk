# Review of the corrected system-map outputs (ORDER 012 item 1, round 1)

## Verdict: PARTLY CORRECTED, NOT CLEAN
Most of the lead's corrections are really made. Two of the studio-head decisions cannot be decided as written (A: dollar cap, B: second alert channel). One claim is stated as fact without evidence (shared Postgres superuser). Most take-side evidence could not be opened by anyone in this review, so it is UNVERIFIED. 0 Blockers, 6 Majors (after merging the two reviewers), about 14 Nits.

## Failures first
1. **Decision A (dollar cap) is not decidable.** Limit blank; option 2 has finding ids where its cost should be; the arithmetic contradicts the proof (1 new lead, 9 duplicates, one paid call per new key); the "x 3" is unsupported; hard stop at provider UNVERIFIED with no fallback; not tied to L7-FD-005 (open webhook). Design D-1, Codebase C-3.
2. **Decision B (second alert channel) contradicts itself.** The table recommends option 2, the prose option 3 plus heartbeat; the heartbeat names no channel (same SMTP credential would repeat the shared-fate flaw), misses a slow mail server, may share the machine; the watcher is still called a laptop-lead question in three places. D-2, C-2.
3. **"Shared Postgres superuser" has no evidence** (a credential name and an OS user id are cited). C-1.
4. **The proof count's independence is not checked before the video.** D-4.
5. **L2-FD-018 stays a Blocker though its values are made-up**; "repo is public" and gitleaks coverage unconfirmed. D-3, C-9.
6. **Evidence gap.** The citation runner found 154 cites in ONE-PLACE-TABLE, DECISION-one-store and SWEEP lines 367-455: 85 point at files that exist in neither tree, 1 is out of range (`ci.yml:228`, file length 144), 68 resolved (67 in range). The 85 are the take-side files (handover/demo, demo3, tools). I did not open any of them either, so rows resting on them are UNVERIFIED, not wrong. Nobody here checked line-by-line whether the 67 in-range cites SAY what the rows claim: the codebase reviewer did that for the src and demo cites it could open (all correct).

## What was corrected for real (checked by the reviewers)
Counter owner (J-034 and six gated rows); false archive gate (grep finds 0 of the old text; wording only); rows 15-17; L6-FD-026 text; re-rates L1c-FD-001, L1c-FD-021, L6-FD-004 (Major), L6-FD-003 kept Blocker with reason, L7-FD-005 raised to Blocker; counts 322 raw / 315 deduplicated (recounted: 322 rows, 18+218+86); honest scope line; owner-name fix step; LOG audit label; key rotation order; L7-FD-001..007 added.

## Options real and costed?
Options are real in A, B, C, D, E. Costs are the weak part (mostly "free tier UNVERIFIED", "about one agent-day (estimate)", or blank). A and B each add a vendor or channel with no replacement trigger (single-dependency item). No over-sizing found.

## What this review did NOT check
Take-side files; provider limits and prices; whether the repo is public; SWEEP lines 38-366 except cited rows; MASTER-MAP and lane files. Both reviewers were fresh egm agents (egm-design, egm-codebase-details) reading the outputs, not the author; the evidence runner never judged. Round 1 of max 2; the fixes are for the system-map session or a laptop reader, so no second review round was run here (no round 2 needed unless they ask).

Files: review-design.md, review-codebase.md, evidence-cites.tsv, CORRECTIONS.md, result-resolve-1.md, LEDGER-ROWS.md.
