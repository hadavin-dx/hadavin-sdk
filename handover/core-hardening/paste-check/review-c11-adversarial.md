# Rev 11 adversarial review (egm hostile reader, read-only, condensed copy), 2026-11-16
Result: 0 Blockers, 2 Majors (checklist text). M1-M9 of review-c10-adversarial closed in text (M2 and M6 with caveats).
## Failures
- F1 MAJOR: D1 (LEAD-CHECKLIST-v5.md ~285, 289) greps 'GONE-FAIL|kill exit=3', so any normal GONE-FAIL blocks the plan's R2 clean-up kill (plan 13.1: on GONE-FAIL use R2). Fails closed but leaves n8n alive. Fix: match only exit 3 (`kill exit=3([^0-9]|$)`); fix line 289 and table row D1 to say "after exit 3" (as LEAD-FILL row 4).
- F2 MAJOR: C4 fill block (~243-249) trusts rows.rc/rows.txt not tied to current PIN or strings.txt; stale rows from another pin can be written with the current PIN in proof-6.txt. Also strings.txt column 3 never compared to the plan table. Fix: check rows.txt line 1 is `head=$PIN ...` (or rows writes PIN into rows.rc); grep -F each column-3 string in the PF table row.
## Minor
Hand-typed P-4b-HIT control file still passes (disclosed attestation); D1 register grep -w matches any number token; C9 "P-3a done" not bound to session; c7check 7-char count weak; WSL-4 line 225 redirection order; line 136 says STOP gives mv but gives aside; rows returns 0 when git grep errors.
## Not checked
No sha256 computed; patched plans, three patches in full, apply-v10-after-chain.py, edit lists not read; nothing run in Git Bash/WSL/patch; plan P-3b/P-4b text not read.
