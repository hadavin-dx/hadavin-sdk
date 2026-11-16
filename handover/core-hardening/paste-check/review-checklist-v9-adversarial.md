# Checklist revision 9: implementation-readiness / adversarial review (egm-implementation-readiness), condensed copy, 2026-11-16
Read only. Nothing run (no Git Bash, WSL, dash, patch). sha256 values and plan line numbers not recomputed; plan and edit script not read.
Blockers: none. 7 Majors (fix before the lead starts), 9 Nits.
1. LEAD-FILL-list-v5.md:9 (Q2): "the lead (and the owner if the process is his)" widens the owner past decision 7. Fix: "the lead", point to open ruling L1.
2. CL:170 (C9) release line does not call pinok, does not check C6 ACCEPT, C2c "P-4b files ok", stand-in gone (C8b is prose), and accepts any non-NOTE runner line, not "P-3a done". Fix: add them.
3. CL:20 `accept` flips any marker unchecked: accept 9 bypasses PF_CONFIRMED/drive letter/counts; accept 6, 1 1b, 5 7 bypass C4, C2b, C2c, C2. Markers 1, 1b, 6, 9 have no indirect protection.
4. CL:101 (C2): PIN need only be an ancestor of the branch; a stale pin passes and C4 prints only MISMATCH and continues. Fix: PIN equals branch tip, or MISMATCH = STOP.
5. CL:16: CHAIN=3 shipped as default on an open ruling (L2). Fix: leave empty (A6 then STOPs safely).
6. CL:3, 5, 226: claims revision-9 helpers (hbok, evok, pinok, c7check, accept, CHAIN branches, A5b4, C2c) were tested in evidence-c7g.md sections 11-14 and "the scratch run named in the changelog"; changelog names none; no evidence file covers them. Fix: run and record, or say "not tested".
7. CL:129 (C2c) `dash -n` probably missing in Git Bash, so "P-4b files ok" never prints. Fix: run in WSL or make optional with a visible message.
Nits: stand-in gone check tests one typed pid (scan /proc instead); D1 does not enforce "no R2 after kill exit=3"; "runner will find the checksum differs" (plan=) unverified, say procedural; silent no-op if section 1 block not run (add else echo); A1-A5b4 have no hbok; patch may prompt "Assume -R?" (use -N/--batch); HBW assumes drive-letter form of HB; file names still say v5; CL:3 verbatim claim now honest.
Prior findings: v8 stranger blockers 1-2 and majors 3-14 closed (marker flips remain unguarded, Major 3; A9 PF_CONFIRMED is self-assertion); adversarial v8 items 1,2,4,5,8,9,10 closed, 3,6,7,11,12 partly; contradiction v8: only LF:9 still open (rest in patches-ready/README.md); citation v8: all fixed except new "tested" claim (Major 6).
Held up by reading: v10 script hidden failure (reads failing [] and sha), A3/A4/A5b chain dry-run && apply && sha, C9 refuses second LEAD-GO and wrong 40-hex, C2/C4 fills safe, C3 runner-may-not-write-LEAD-GO text present, limits declared (procedural gates).
