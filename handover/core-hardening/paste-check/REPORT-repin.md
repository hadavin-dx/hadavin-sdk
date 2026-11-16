# C3b re-pin patch report (2026-11-16)
## Failures and unchecked items (first)
- NOT DONE: the exit 3 pre-run check command. Nothing in the plan or the scripts' text shows how to list unreadable n8n-shaped processes. The existing scans (`grep -lsF ... /proc/*/environ`, plan 13.1, 13.5, `ours`) use `-s`, which silently skips processes whose environ cannot be read, so they cannot find them. Written as step P-4b (patched plan line 242): "the lead supplies the command", status UNVERIFIED. The lead must supply it.
- NOT CHECKED: I did not read `n8n_kill.py` or `n8n_start.sh` (outside my allowed files). The exit 3 rule rests on the lead's text only. `gone()` already failed on any non-zero exit; the new line only gives exit 3 its own message and wording.
- NOT RUN: PowerShell (no pwsh), so the P-2 first-line edit is read only. No shell span contains a placeholder, so no dummy-hex substitution was needed.
- UNCONFIRMED: worktree name. Plan line 3 names `nlite-fix5` as the round-5 worktree; I used it in header, code row and P-2 `$WT` as plain text (not a placeholder). The lead confirms it.
- Lead facts vs plan: the task gave no facts beyond its text; where the plan differs it is noted above. Plan item 11 (line 561 patched, 559 original) already mentioned exit 3 only as "not read"; replaced, not duplicated.
## What the patch does (plan line numbers after plan-v5-fixes.patch; original numbers in brackets where they differ)
1. Header line 2 and RE-PIN line 3: placeholders `<FINAL-SHA-7>`, `<FINAL-SHA-FULL>`, `<FINAL-BRANCH>`; r3/r4 kept as history; line 3 now says exit 3 is GONE-FAIL (the old text "check exit 3 cannot be returned" contradicted the new rule). Line 76 (UNVERIFIED 1) said "provisional eec6ba4": reworded, no placeholder.
2. Section 2 code row, line 120: placeholders.
3. P-2 first line, 235 [234]: the four values (`$WT` = nlite-fix5).
4. Section 11 part A (515-537 [513-]): new last-but-one column "final head": S1-S8 and K1-K4 say "to be re-read by the lead at the final head"; D1-D6, H1-H2 say "not re-read here". Intro sentence (513) now says all of S1-S8 and K1-K4 move (it said only S4-S8, K3, K4). Separator row widened.
5. `gone()` 150-153 [150-152]: new line `if [ $e -eq 3 ] ... GONE-FAIL ... return 1; fi` before the generic test.
6. New P-4b before P-5 (242); order line updated.
7. Item 11 rewritten (561 [559]).
## Evidence
`evidence-c3d.md`: both patches dry-run rc=0 in order, real apply rc=0, result identical to the build tree, placeholders only at lines 2, 120, 235, 515; `bash -n` and `dash -n` on `gone()` rc=0.
Placeholders are only for the lead to fill (R5 verbatim code does not apply to them).
Files: plan-v5-repin.patch, evidence-c3d.md, REPORT-repin.md. No sub-agents, no commits.
