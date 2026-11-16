# FINDINGS r30 reader B: F-037, F-008, F-011, F-018, F-029, F-041 (rows 280-285). Non-security; condensed; unverified; static. UTC/IST pairs correct. 0 Blockers, 9 Majors.
1 F-011 PASS LINE (a) names "GUARD OK" line that cannot print; evidence is the three F041 checker lines.
2 F-011 variables ($KEEP,$REPO,need_set) used before set; PASS LINE has no VARIABLES FIRST.
3 F-011 BLOCKED UNTIL (2) "no input except $OWNER_SHEET" contradicts Q31 items 10(b),10(c),18, second reader, review date.
4 F-037 rating kind: SUMMARY "Blocker by rubric" vs RATING BASIS "nearer Major".
5 F-041 "passes when read list empty or lists only read files" vs checker (PASS only exactly 4 lines; else NOT A PASS BY COMMAND; today R2-tables.md listed).
6 F-041 $R7OUT can be lost between calls; add to VARIABLES FIRST.
7 F-037/F-029/F-008 export command and grep runner have no named supplier or Q31 item with due time.
8 F-018 Wednesday half no machine PASS/FAIL (mail count LEAD FILLS, HubSpot reader NOT NAMED); Tuesday cannot pass; split row.
9 F-011/F-041 "four roles" ambiguous (three flow roles plus n8n's own).
Minor: F-008 prose says ls lists files but block uses no ls; F-037 quotes F-029 text no longer present.
