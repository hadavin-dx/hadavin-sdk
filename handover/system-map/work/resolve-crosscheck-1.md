> READ FIRST (added 16 Nov 2026 by system-map, because cold readers could not follow this note). This is a working note, not a finished page. Words: "take" = the one filmed run of the lead-intake demo (made-up data, run through n8n); "lead session" = the Claude session that gives orders; "studio lead" = the Claude session that does the technical steps; "owner" = the human; "studio head" = a role name in older notes, meaning unknown (UNVERIFIED). Short prefixes in older notes (my reading, UNVERIFIED): PL = inputs/plan-wp6-resmoke-v5.md, OS = inputs/OWNER-STEPS-realrun-v3.md, SC = inputs/AGENT-SCOPE-DO-AND-DONT.md, DE = DECISION-one-store.md. Ids like D-01 are drift rows in drift/REPORT.md; ids like L6-J-005 are rows in work/L6.md; M1, B1, Z-1 are finding numbers inside the note that uses them. One-line meanings of other terms: work/GLOSSARY.md. Nothing in this note was run or verified.

Status: resolved (headless, auto accept; fixes applied by the author, not by this skill)

# Goldfish Annotated Review Report, ORDER 014 round 1

**Target:** `handover/system-map/FINAL-CROSSCHECK.md` (full file). Findings: work/review-crosscheck-design-r1.md (egm-design) and work/review-crosscheck-codebase-r1.md (egm-codebase-details). Both are condensed copies of the inline reports. No finding is a Blocker.

## Majors
### 1. [codebase M1] Sources misattributed in section 1 and section 4 row 1. PROPOSE FIX (applied)
Section 1 now names the two review files as written by the flows-audit and core-hardening lanes, drops "could not open", and gives the 154/85/1/68 citation counts with their source.
### 2. [codebase M2] "F-010 = F-030" is not a duplicate. PROPOSE FIX (applied)
Section 3 now says the two overlap only on the shared mail login.
### 3. [design M1] No one-minute summary at the top. PROPOSE FIX (applied)
Summary block and id key inserted under the Words line.
### 4. [design M2] Wording and id key. PROPOSE FIX (applied)
Id key added; labels explained once.
### 5. [design M3] No per-row source column; no statement on coverage of FA CUT-LIST.md. PROPOSE FIX (coverage statement applied; column NOT yet)
Still to do: add a "source" column to the section 2 table and a source cell per section 4 row (the file and line already named inside the cells moves to the column). Reason it matters: a reader can then see which audit each rating came from without reading the cell text.
### 6. [design M4] "did not re-judge severity", loose wording. PROPOSE FIX (applied)
Reworded in section 1.
### 7. [design M5] "Safe now" must be conditional. PROPOSE FIX (applied)
Rows 20-21 and the summary say: only after an archive place outside the repository is named.

## Nits
PROPOSE FIX (applied): L6-FD-001/002 mapping; "overlapping hunks" wording; n8n-flows/v1-superseded added to rows 1-11; duplicate row number 16 fixed (15, 17 and 16); RUN-ON-LAPTOP.md:51; trigger_ref wording; A-02 "converged" wording; rows 20-21 "no live caller".
PROPOSE FIX (NOT yet applied): UTC and IST times for Wed 18 Nov in sections 6 and 8 (write "Wed 18 Nov 2026, morning; exact hour is the laptop lead's, not stated in the files I read"); "who moves files" in section 6 (the laptop lead moves, the studio head says yes first); row numbering line "2 + 28 + 9 = 39" (already in the summary); section 7 note (add that the cut list rests on audits' citations for rows 1-19 and 33-39).

## Counts: accepted 7 Majors + all Nits; contested 0; escalated 0; declined 0.
Still open after this round: design M3 column, three Nits above. Round 2 only for Blockers and Majors: design M3 is the only Major left; apply it and have one reviewer re-read sections 2 and 4.
