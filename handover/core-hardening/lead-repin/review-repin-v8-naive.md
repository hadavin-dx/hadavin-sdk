# Re-pin v8 naive-reader review (egm-comprehension, condensed copy of the inline report), 2026-11-16T18:37:29Z
Target LEAD-REPIN-VERIFY.v8.md (guide) and v8-CHANGES.md; ran nothing; no review-repin-v7-*.md exists in lead-repin/ so nothing compared. Verdict: a studio lead cannot follow the Quick start without asking someone. 2 blockers, 11 majors, minors.
## Failures first
- B1 (lines 24, 61, 255) self-test count wrong: guide says passed=1567 (1372 with LEAD_REPIN_NO_META=1); script plans 1635 and 1601; a correct run prints 1635 and the stop rule then tells every first-time reader to stop.
- B2 (lines 5, 28, 56) script name contradicts itself: Quick start example uses lead-repin-verify.sh, which does not exist until the lead does the cp; line 5 says the .v8.sh file; glossary says .sh.
- M3 (lines 61-62) step 2 loses the exit code: typing OUT=... resets 0; put the echo on the same line as the run.
- M4 NOT TESTED (HUP with nohup) appears in a normal self-test but is explained 25 lines later; "if the lead agrees" has no how.
- M5 run time stated two ways (2 and 3 minutes). M6 checksum step unexplained, no stop rule. M7 line 133 says LEAD_REPIN_NO_STATUS; v8 has git status off unless LEAD_REPIN_GIT_STATUS=1; "git older than 2.36" not found in the script. M8 appendix test counts (24+16) differ from v8-CHANGES (24+17); the 31-plant gap not stated. M9 exit-code table: exit 4 delete advice not safe until line 102; on other exits the folder is already removed (not said). M10 11:00Z and 12:50Z UTC only, Z undefined. M11 words with two meanings (take, head, test, window, stop, step, block, gate, G/R numbers, lease, challenge line...). M12 T folder: how to find it unsaid; scripts/ check stricter than the script (3 levels). M13 four steps cannot be done by the reader (flows folder, model program twice, qs_37 command); missing from the line-7 list.
- Minors: first two printed lines claim unchecked; pattern ls vs rm -rf; STOP rows say "you decide" and "send to the lead"; first unexplained terms (CRM, n8n, HubSpot); G/R/line numbers may be out of date; blank fields not said to be optional.
## Works
Shows/hides section is thorough and honest; never paste a secret-looking value is clear; action table gives who decides; exit codes agree with the script apart from the above; UTC/IST pairs and weekdays correct.
## Not checked
Real test program, flows, model program; block content on real files; WSL, macOS, busybox; the 31 plants not rerun; newer release notes and ORDERS numbers.
