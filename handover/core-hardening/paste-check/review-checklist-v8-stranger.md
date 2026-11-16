# LEAD-CHECKLIST-v5 (v8) + LEAD-FILL-list-v5: stranger read (egm-comprehension), condensed copy, 2026-11-16
Read only; the reader did not read the plan, the patches or acc5.sh. Nothing run.
## Blockers
1. Where `pastes\` lives is never stated (CL 79, 88; FL 49): lead cannot save, hash or test P-4b.sh / P-4b.control.txt.
2. EV (evidence folder) is "a guess" with no confirm step (CL 83, 112, 120, 125; FL 16): wrong EV means the C9 LEAD-GO lands where the runner never reads; runner waits forever silently. Add a check that runner lines appear after C3.
## Majors
3. Per-window variables: re-running A1 in a new window makes a new unpatched copy so A6 fails; list omits PIN, EV, WT, SF, SP. Empty PIN makes `show "$PIN:scripts/n8n_kill.py"` read the index copy silently (CL 79 wrongly says it errors).
4. A8 collision message: backticks inside double quotes run as a command (CL 52); A8 uses EV/PROGRESS before C2b defines EV.
5. STOPs with no next action: CL 14 checksum mismatch; CL 19-31 dry-run rc non-zero; CL 45 after A6 STOP; CL 94 FILE-MISSING; CL 103 C6 STOP; CL 124 kill exit=3; FL 7 P-3b STOP; FL 48 "tell me" = who.
6. Roles undefined (owner, builder, channel); FL 17 vs CL 1 on who is at the laptop.
7. C1/C4/C5/C6 hardcode guesses (user name path, eec6ba4, nlite-fix3, W3) not marked EDIT POINT; branch=HEAD not covered by Q7.
8. C2 placeholder count: "three" vs 24 strings; 40-char vs 7-char order contradicts C4; no list command; no replace command; no source of truth for "final head of round 5".
9. C4 output: "count of 0" but prints line numbers; empty last field vs 0 ambiguous; "edit the plan" and MISMATCH no action; REC and "the tar" undefined.
10. C2b: criteria for n8n-shaped/unreadable have no pointer; no command for control file, CR check, word scan; "Positive-control instructions" paragraph not named; ONE note line vs FL 49(7); stand-in (sleeps 600 s) end of life: no check it is gone before C9, D2(3) wording; re-run changes pid vs "ONE"; WSL user not stated.
11. C3 brief: no template; nothing says stop after P-3a and wait for LEAD-GO; BRIEF-PREAMBLE rule not mentioned; race while lead edits PF; PROGRESS.md-exists only asserted in A8.
12. C6: ACCEPT gives no rule for reading + lines; exit 3, R2 unexplained.
13. D1/D2: register row and n8n.pid location; WSL shell prerequisites; no rm command for fresh start.
14. B1: no sed for B1; LEAD-FILL 1 would match 1b; no one-liner for accepted defaults.
## Order / A9 flip
A9 flip tests only that PF agrees with itself: running it on the guessed path closes marker 9 on a guess; CL 59 says (2),(3) not used yet flip requires both = 2. Stand-in must be dead before C9. EV typed four times (once WSL form).
## Nits
Version naming v5/v8/v6; A1 `<path>` unmarked; A2 checksum by eye; A7 no expected count; unexplained labels (WORDS, UNVERIFIED 14/15, 0.1, S13, HEAD_PIN); FL 17 lists a,c,d no b; `less` quit; sed -i vs editor stale overwrite, no CRLF recheck; C6 out.txt cwd; C10 comparison base; dead refs evidence-c7g.md / section 13.
