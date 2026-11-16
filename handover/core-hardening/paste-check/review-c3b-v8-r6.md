# C3b v8 round 6 short re-check (egm-implementation-readiness), condensed copy, 2026-11-16
Read only, nothing run. R5-M1 CLOSED (A9 flip block line 62 only flips marker 9 when counts are 1 and 2, idempotent, C7 second count can reach 0; unset PF STOP text misleading but fails safe). R5-M2 closed in substance. 0 blockers.
Major (fixed by lead in-place): line 86 closing fence and prose on one line, "``` Flip the markers of questions 1 and 1b..." -> not a valid CommonMark close; fixed: fence on own line, sentence in own paragraph.
Minor (fixed by adding a sentence to A8 refusal): C2b can create evidence-2/PROGRESS.md before the runner; A8 says stop if PROGRESS.md has lines of a run; the single NOTE line is expected. OPEN: not checked whether plan run.sh/P-1/P-2 tolerate an already existing PROGRESS.md (C9 line 110 assumes they do): lead to confirm against the plan.
Nit (fixed): D2 step 3 said "command below", read command 2b is above. Nit open: C2b block run twice gives two NOTE lines; D2 reads tail -n 1 so the last wins.
Untested: Git Bash, WSL /proc, cygpath -w, real CRLF PROGRESS.md; hand-back counts (27 blocks, 17 markers, section 14) not re-checked.
