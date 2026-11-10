# Parallel plan, round 1, implementation-readiness review (egm:egm-implementation-readiness, sonnet; agent ab6b98e1f67bbe453; saved by the cloud session)
Reviewer did not open branches/PRs. Status: NOT READY. 0 Blocker, 9 Major, 7 Nit. Startable with only pointer-level decisions open: A2, A3, A5 (evidence), A9, A19, A22, A24. Not startable: A1, A4, A20, and any fix/resolve step.

MAJOR
M1 (A1, line 24) `noqa: S603` open decision, no default. CLAUDE.md forbids suppressions and order 193 needs a DEFAULT. State: refuse the suppression, fix the code; say what the builder does while waiting.
M2 (A2, line 25) always-on FIXTURE ERROR decision is owner-only, no default; A2 has no builder, so unclear whether reviewed as-is or blocking.
M3 (A4, line 27, P1d-a build, UNCAPPED) not startable and breaks EGM order: no branch name, no base SHA (A7 still reviewing P1b at 0d843b4), no file list/test list/fail-before spec; CLOUD-RESUME says the P1d tickets are "drafted, unreviewed" and need egm design+readiness plan review first (no cap) but the plan has no plan-review row and marks the build READY-NOW; reports/P1d-a-builder-report.md exists (fresh build or continuation?); "text views of P1a/P1b" is unexplained jargon.
M4 (A23, lines 46, 62) ledger file ambiguous: plan says lead writes egm/BLOCKER-LEDGER.md; CLAUDE.md says handover/ledger.md while handover exists; A4 needs row BL-hadavin-sdk-cilint-001. Name one file, one owner, one rule.
M5 "lands" undefined (lines 10, 33-36, 39-41, 44, 52): merges are lead-only. Critical path (about 8 h clock) only works if "lands" = "review clean", not "merged". Define per row; A10 and A11 carry two statuses, order asks one status per row; split.
M6 Order 232 compliance: MODEL column missing per row (merged into "agent kind / MODEL"); many rows have no model (A11-A14, A16-A19, A24, A8, A9); reviewer types mostly unnamed; most rows have no resolve step (egm-resolve via Skill, Opus) and no fix-builder model after review; PROOF table not mentioned/located (cloud-register.md MODEL column).
M7 UNCAPPED marks incomplete, no classification rule: A21 (T1 own-meter, money evidence), A18 (PR86 stacked on money PR78, llm kind), A24 (scan guard), A14 (profile gate, least privilege), A15-A17 (redaction exposure unknown), A5 (migrations), A1 (already at round-5 findings vs the 2-round cap). Add a Class column with a one-line reason per row.
M8 Heavy-run machinery unspecified and Postgres plan contradicts the dblink failure: qrun/qsubmit/pgstart are gone (CLOUD-RESUME lists heavy.sh and pgstart.sh to recreate; plan does not say who). Per-builder port range 55400+10n vs dblink needing -k /var/run/postgresql -p 5432 (one cluster at a time). State the rule: serialised single-cluster slot, or accept dblink as documented env noise with a base comparison; port formula has no number for rows without heavy runs.
M9 Queue order (lines 55-56) contradicts "UNCAPPED first": A9 (critical path head, UNCAPPED), A4, A11 sit after non-UNCAPPED A5, A14, A1, A2, A20. Critical-path 14 h does not match row hours (A9+A3+A10+A12+A18 = 12).

NIT
N1 Completeness vs order 230: all listed items covered. Missing from other sources: PR71 (151d3e1), AK-G2 (CLOUD-RESUME item 8), STANDING-ORDERS 6f hourly handoff cross-check; PR91 not in order 230 (why included?); PR70 head e3f946f unchanged.
N2 Moved heads not only PR73/72/63: PR75 (f8b9056 -> a8abba0), PR76 (e323ac7 -> 7f32349), PR84 (8a677ad -> 69b69c6); old evidence void for those too.
N3 60-minute time box vs 2-5 h rows: say "stop, commit, a fresh agent resumes from the checkpoint note" and where the note goes.
N4 "17 builders" wrong: only A1, A4, A20, A21 are builders; state the real agent count for the RAM mitigation.
N5 A6 duplicates A12 ("PR78 builder pass"); P4a has reviews through round 11 plus build-start review, plan says "rev 7": reconcile which revision is current.
N6 Missing scripts (P3a-2 66 mutants, P6a-1 62 hand mutants, gen_evidence): default is NOT RUN; say reviewers must not treat NOT RUN as pass.
N7 No per-row exit criterion (clean fresh pass for UNCAPPED, 2 rounds others, drift report); egm-drift-report never mentioned in section 3.
