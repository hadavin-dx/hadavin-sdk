# TAKE-BLOCKERS: the one to-do list for the studio lead (round 3, 16 Nov 2026, after the lead's decisions in inputs/DECISIONS-2026-11-16.md)
Made-up data only: the demo uses invented people and a test mailbox. The owner reads OWNER-VIEW.md and the two cards (OWNER-RUN-DAY-CARD.md, OWNER-CLEANUP-CARD.md), not this page. Everything else in this folder is a record.

## Words, one per line, in the order they first appear
- Take = the one filmed run of the lead-intake demo (a video, not a social post).
- Post = the owner publishing that video on social media.
- Owner = the human who types the steps and posts. Older pages say "studio head". Same person.
- Studio lead = the Claude session that does the technical steps. Older pages say "lead".
- core-hardening = another Claude session, on its own branch. It writes v5 and, per the lead's orders, the text-only security edits (S9-5, S9-12, S9-3, S9-2).
- v5 = the owner steps file inputs/OWNER-STEPS-realrun-v5-core-hardening.md. It replaces the older v3, which is archived, never deleted.
- Scope sheet = the file describing the model program (the `stage` that answers `/qualify`). Exact file name: not found by this session (UNVERIFIED).
- n8n = the workflow tool the take runs through. A flow = one n8n workflow. A flow set = the flows imported together.
- real-v5 = the flow set that talks to the real test accounts (HubSpot contacts, a real mailbox). It is the ONLY flow set in this video (scenes 1 to 4).
- film-v5 = a second flow set that talks to stand-in programs. OUT of this video (decision 1). Scenes 5 to 11 are cut.
- `$env` values = settings the flows read at run time (real-v5: DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO).
- BL-wp6-G1 = ledger row: the step that fills those settings into a local copy of the flows is not built.
- Spend gate = a lock that would refuse paid calls until both typed answers are given. v5 has NO closed gate (S9-1 is deferred). No page may say nothing can spend before the typed answers.
- S9-n, R8-5, D-n, L-01 = row ids in drift/REPORT.md (S9-12 is in drift/APPLIED-S9.md).
- STOP / GO / REC = the plan's three classes of check: STOP = halt, GO = may go on, REC = recorded only.
- Row DM = the plan's crash-test row. Crash-safe = no double send after a power cut. (Not the same as "DM" used elsewhere for a delivery message: that old use is dropped.)
- Rehearsal = a test run with stand-in programs and no real account. Loopback re-smoke = the rehearsal in inputs/plan-wp6-resmoke-v5.md; by its section 9 it does not prove real-v5 at run time.
- Take prep = ONE made-up lead sent through real-v5 just before the take (decision 8).
- "The plan" = inputs/plan-wp6-resmoke-v5.md; every "plan line" below cites that file.
- Decisions of 16 Nov = inputs/DECISIONS-2026-11-16.md, numbered 1 to 12; they are in force.

## Dates
The take must happen by Mon 23 Nov 18:29 UTC / 23:59 IST; latest start before 18:14:40 UTC (v5 says "about 18:15 UTC / 23:45 IST"); the studio lead's notice ("take starts at ...") must come at least 3 hours before the start, so on the last day before about 15:14 UTC / 20:44 IST. The post is Wed 25 Nov 15:00 UTC / 20:30 IST. Target take Wed 18 Nov is NOT confirmed.

## Work order (row number = order of work; row ids are new)
| # | what | by whom | done when |
|---|---|---|---|
| 1 | GOAL: a local filled copy of the PATCHED real-v5 flows (lead's answer 16 Nov 10:20Z: patches F-002 and F-008 applied first, then the fill) in which DESK_URL, DESK_TIMEOUT_MS and DESK_ALERT_TO are literal values; n8n imports it. Closes BL-wp6-G1. INPUTS: (1) the tool to extend is `fill_flows.py`: two copies exist (the plan's throwaway, plan-wp6-resmoke-v5.md:223, :249-250, :298, film-v5 only; and `handover/flows-audit/fill_flows/fill_flows.py` on branch cloud/flows-audit, MASTER-MAP L8-X-005, which already handles `$env.DESK_*`); the builder compares them, extends one, writes the choice and reason in the ledger; it never edits the input folder. (2) the four real-v5 files mf-form, mf-hook, mf-recovery, mf-sub-crm-mail from `flowcheck/in/real-v5/` (flows-audit final head d1097db3, not 848fa093; the builder confirms folder and head with the studio lead) plus patch dry-runs in work/evidence-patches-2.md; the sha of the patched copy is named once. (3) values from environment variables of the same names; rehearsal uses loopback and `@example.test` made-up values only; the studio lead gives take values at take prep. (4) the studio lead's `n8n_api.py` (path from the lead; not in this checkout). RULES: a missing or empty value exits non-zero and names the variable, never the value; output goes to a new folder outside any git repo; do not use `$vars` (UNVERIFIED); never import a flow still holding `$env.`; credential ids stay placeholders until the lead maps them. | a builder named by the studio lead, with a finish date in UTC and IST that leaves room for rows 2 and 4 | (1) `grep -rc '\$env\.'` on the output folder is 0 for every file; (2) a run with one value removed exits non-zero and names it; (3) `n8n_api.py` imports all four files and exits 0; (4) raw output saved in evidence-2/; (5) the studio lead writes "row 1 done" with commit and file names |
| 2 | The take imports the PATCHED real-v5 copy (F-002 and F-008 applied, then the fill values; lead's decision 10:20Z). It has never run in n8n. TWO RUNS, each with its own result file: (a) the loopback re-smoke on stand-ins (the plan), (b) the first laptop rehearsal of the filled patched copy; [choose] the "rehearsal passed" rule applies to (a), (b) or both. Row 2 needs row 1 done first. First laptop rehearsal: the studio lead runs it (decision 12) right after the loopback re-smoke passes, target tonight or tomorrow morning IST. Nobody touches Docker Desktop settings. The lead starts Docker Desktop (decided, lead 10:13Z item 3; plan line 489) | studio lead | a rehearsal result file that also shows test T19 (one lead posted twice gives one mail and one CRM write) and whether any lead key, e-mail or name stays in n8n's run list or the Postgres tables (F-008 turns saving on); then the "rehearsal passed" rule below |
| 3 | Security edits as TEXT (decision 5): S9-5, S9-12, S9-3, S9-2 (the owner compares the settings-file figures; v5 says the program does not print them). DEFERRED, describe-only: S9-1, S9-4. The fallback "the lead activates flows after the owner's typed y" is NOT accepted. v5 must not say nothing can spend before the typed answers. Runs in parallel with rows 1 and 2 | core-hardening edits; studio lead confirms | v5 and the scope sheet carry the four edits, tests pass, no page claims a closed gate |
| 4 | Take date and start time, chosen after rows 1 and 2; state how many reruns fit before the latest start | studio lead, written to the owner in UTC and IST | the owner has a written date |
| 5 | PENDING QUESTIONS item 1 (does `end` delete?). HubSpot account-check text and the login-key choice (OWNER-VIEW row 7). The HubSpot delete-rights check (R8-5) is MOOT: the take identity is read-only (decision 2); leftover contacts are listed by lead key and contact id (decision 2's words) and the owner deletes them by hand | studio lead writes the lines or removes the row | the owner has exact lines, or the row is gone |

DECIDED, nothing to do: scope is real-v5 only (decision 1); film-v5 mail-credential risk and the flow-set switch are gone; roles proposal parked (decision 3). START WITH ROW 1. This is the only to-do list; QUESTIONS.md holds the decisions.

**Before the post, not the take (the studio lead confirms the split; QUESTIONS.md item 2):** drift D-04 and D-05 (post wording), the exact post words, a named person who checks the post. D-01 to D-03 and D-10 are about v3, which is archived. **Not a take blocker:** the licence guard test failing on core-hardening is a branch artefact (decision 11); archive lists (after the take).

## Single points to accept
The owner alone types `y` (state a backup window). One n8n on one laptop with no fallback if Docker fails on the day.

## What "rehearsal passed" must mean (a draft from an independent read; the studio lead chooses at each [choose] BEFORE saying it to the owner)
No document defines it: v5 line 74 only requires "rehearsal passed, with its result file"; plan section 7 (lines 464 to 486) has a 20-row PASS/FAIL table (STOP, GO, REC) but no overall rule. Nine rows are mixed (T1, B1, C3, X1, E1, E3, E5, L4, C1) and the letter "D" in row C1 is not defined.
1. PASS means all of the following hold. A mixed row is judged on its STOP part. Row NC is copied into the result file as it is.
2. Every STOP part is PASS. A row not run counts as FAIL. One STOP failure is FAIL; the studio lead fixes it and reruns only the failed sections plus row Z1.
3. Every GO finding is "fixed" (a rerun shows it) or "accepted": the owner's one-line written yes in the result file, with date, before the take starts. An EGRESS-FAIL stays FAIL until option (a), (b) or (d) of plan line 506 is chosen in writing.
4. Crash test (row DM): [choose] required / not required. If required, DM PASS means mails == 1. If mails >= 2, or E and E2 both MISSED, the rehearsal passes only if the owner accepts the limit in writing; the take and post then must not say "crash-safe" (v5 line 170).
5. Take prep (decision 8) uses [choose] a fake model / a paid call inside the owner's written yes with numbers. Its leftover contact and mail are listed and cleaned, and row Z1 confirms it.
6. The evidence runner fills the raw-result column only. The independent `egm:*` reviewer reads the raw results, not the runner's verdict. The studio lead fills the verdict column; a reviewer blocker overrides the lead. Only then the studio lead writes "rehearsal passed" and names the file.
7. Time box: one run at most 5 hours, at most 2 review rounds, fixes batched. A rerun is allowed only if it can end 4 hours before the latest take start (18:14:40 UTC / 23:44:40 IST; v5's 18:15 / 23:45 is rounded). Otherwise the studio lead tells the owner, in UTC and IST, which limit the take carries. Result file: `evidence-2/INDEX.md` of that plan plus at most 10 plain lines for the owner.
Gaps this draft still leaves: the plan has no row for the flow import or for take prep; the imported copy must be the patched real-v5 copy, sha named once (scope mismatch); the studio lead must add rows or accept that they are judged outside the table.
