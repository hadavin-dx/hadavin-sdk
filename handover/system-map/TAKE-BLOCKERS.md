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
| 1 | The `$env` values are not filled in (BL-wp6-G1). EXTEND the existing throwaway `fill_flows.py` (plan-wp6-resmoke-v5.md:223, :249-250, :298; flowset/REPORT.md:37), used so far for film-v5 only, to real-v5: input folder; read DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO (no MF_* names needed); refuse and name a missing value; made-up values only in rehearsal. Inputs: flows-audit head 848fa093, demo/handover head 5928fb1e (patch dry-runs in work/evidence-patches-2.md). The block on `$env` reads stays on. `$vars` is UNVERIFIED. Also unchecked: credential ids in the flow files are placeholders; the lead's `n8n_api.py` import must not import flows that still hold `$env.` | a builder named by the studio lead, with a date | the filled copy has 0 leftover `$env.` and an n8n import exits 0 |
| 2 | The flows changed by the five proposed patches have never run in n8n (the patches are proposals, not applied to the files n8n imports; only patches touching real-v5 matter). First laptop rehearsal: the studio lead runs it (decision 12) right after the loopback re-smoke passes, target tonight or tomorrow morning IST. Nobody touches Docker Desktop settings. Plan line 489 says the lead starts Docker Desktop (QUESTIONS item 3 asks to confirm) | studio lead | a rehearsal result file, then the "rehearsal passed" rule below |
| 3 | Security edits as TEXT (decision 5): S9-5, S9-12, S9-3, S9-2 (the owner compares the settings-file figures; v5 says the program does not print them). DEFERRED, describe-only: S9-1, S9-4. The fallback "the lead activates flows after the owner's typed y" is NOT accepted. v5 must not say nothing can spend before the typed answers. Runs in parallel with rows 1 and 2 | core-hardening edits; studio lead confirms | v5 and the scope sheet carry the four edits, tests pass, no page claims a closed gate |
| 4 | Take date and start time, chosen after rows 1 and 2; state how many reruns fit before the latest start | studio lead, written to the owner in UTC and IST | the owner has a written date |
| 5 | PENDING QUESTIONS item 1 (does `end` delete?). HubSpot account-check text and the login-key choice (OWNER-VIEW row 7). The HubSpot delete-rights check (R8-5) is MOOT: the take identity is read-only (decision 2); leftover contacts are listed by lead key and contact id (decision 2's words) and the owner deletes them by hand | studio lead writes the lines or removes the row | the owner has exact lines, or the row is gone |

DECIDED, nothing to do: scope is real-v5 only (decision 1); film-v5 mail-credential risk and the flow-set switch are gone; roles proposal parked (decision 3). START WITH ROW 1. This is the only to-do list; QUESTIONS.md holds the decisions.

**Before the post, not the take (the studio lead confirms the split; QUESTIONS.md item 2):** drift D-04 and D-05 (post wording), the exact post words, a named person who checks the post. D-01 to D-03 and D-10 are about v3, which is archived. **Not a take blocker:** the licence guard test failing on core-hardening is a branch artefact (decision 11); archive lists (after the take).

## Single points to accept
The owner alone types `y` (state a backup window). One n8n on one laptop with no fallback if Docker fails on the day.

## What "rehearsal passed" must mean (a draft; the studio lead chooses at each [choose] BEFORE saying it to the owner)
No document defines it: v5 line 74 only requires "rehearsal passed, with its result file"; plan section 7 has a 20-row PASS/FAIL table (STOP, GO, REC) but no overall rule.
1. What runs: the loopback re-smoke, plus one import of the filled real-v5 flow set, plus take prep (decision 8; replaces the real-account smoke). Open: take prep uses a paid model call only inside the owner's written yes, or a fake model; it also leaves one contact and one mail that must be on the leftover list and cleaned before run-day step 1.
2. Result file: `evidence-2/INDEX.md` of that plan, plus a summary of at most 10 plain lines for the owner.
3. Pass: every STOP row PASS; every GO finding "accepted" or "fixed"; REC rows recorded. One STOP row failing = rehearsal failed.
4. Crash test (row DM): [choose] required / not required. If not PASS, the post must not say "crash-safe" (v5 line 170).
5. Who judges: an independent `egm:*` result review and the resolve step (plan line 505); only then the studio lead writes "rehearsal passed" and names the file.
6. Time: the review round must end by [date]; reruns that fit before the latest start: [number] (a rehearsal takes 3.5 to 4.5 hours, plan line 445).
