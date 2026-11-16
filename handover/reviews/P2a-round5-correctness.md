# P2a round 5, correctness (egm:egm-codebase-details), head 60fedf6. Condensed. Verdict: 0 BLOCKER, 7 MAJOR, 14 MINOR/NIT. Reviewer ran nothing; PR #50 content not on disk (UNVERIFIED).
| id | sev | problem | fix |
|---|---|---|---|
| R5-C1 | MAJOR | "S3 shows 1000 stops then reset with original token succeeds": S3 shows only version stays 1; the reset is S8. | Cite S3+S8 or add reset to S3. |
| R5-C2 | MAJOR | "direct SQL reset writes no audit row (S10)": evidence model has no audit tables. | Reword; UNVERIFIED until migration run. |
| R5-C3 | MAJOR | "(verified)" on PR50 gate fail-closed and row-store claims; only core half verified (postgres.py:444-451). | Mark PR50 half UNVERIFIED; P0e confirms. |
| R5-C4 | MAJOR | Sibling-ticket line cites wrong/incomplete (P4d 12,31,114,214; P4c 55,57,65,125,134,138,216-220; P4b2 173,184; P4b1 21,57; P4a 59); P4d is rev 6. | Replace list. |
| R5-C5 | MAJOR | P3a rev 6 (P3a.md:76) makes P2a-1 the first ACCEPTED_CHANGES consumer; P2a never adds the entry. | Add entry (kill_switch trigger, column, grants; reason; named test) to Files and Done. |
| R5-C6 | MAJOR | `limits.label_key_secret` has no wiring: core precedent `*_secret_name` (config.py:241, app.py:84-89,120,203,390, cli.py:186); no live-env requirement. | Specify name, resolver, startup and overlap checks, CLI path. |
| R5-C7 | MAJOR | Lock timeout -> P4d `StoreBusy` is not a connectivity error; cli.py:366-380 prints wrong advice and exit 2 on the stop path. | Exit code/message for StoreBusy on stop and reset; test and mutant. |
| R5-C8..C21 | MINOR/NIT | OFF->OFF, OFF-state dry run, upsert refusal, NOINHERIT group login untested (mark UNVERIFIED or add S-tests); S6/S20 id collision; evidence model `by` not null vs real nullable; `ResetRefused` maps any 42501 (infra fault reported as refusal); `ts` and REVOKE no S-output; tick-step probe on the runtime handle waits behind in-process lock (P4d.md:29); stale cites (test_repo_rules.py:305, P4d.md:80, P3a rev 6, apexc sha 153d217 vs 3d78bc7); audit `events()` exists for "N earlier stops"; ledger-seed.md:133 corroborates 262. | Per report. |
Stop rule: not met (needs two clean rounds at final commit).
