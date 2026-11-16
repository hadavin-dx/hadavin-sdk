# Evidence v30, independent runner (raw results; the runner does not judge)
Run 2026-11-16 about 17:22 to 17:50 UTC. No commit, no push, no spend. Own scripts: indep30.py, hostile30.py (both use `python3 -B -I`, take the folder as an argument). Raw outputs: out-*.txt in this folder.

## Failures and deviations first
1. **MISSED mutation H06**: a lead page (LEAD-RELEASE-NOTE-v14 source) with the added words `the lead sends the owner the words "cancel the older key now"` is NOT caught by check-v30.py (rc 0, no FAIL line). The only check on this wording is C188, which looks for the exact text `waits for your message "cancel the older key`; the same idea in other words passes. H13 (exact C188 text) is caught. See out-hostile30.txt.
2. **MISSED mutation H09**: changing one of five `[LEAD FILLS at re-pin: ...]` placeholders in the sheet source to `[LEAD FILLS: ...]` is not caught (other copies of the right spelling remain, so presence checks pass). Presence is what the brief asks; a single wrong copy is not detected.
3. **MISSED mutation H15**: fact `ls_t` changed to a wrong time; not caught because `{{ls_t}}` is used in no source (dead fact), so the mutation changes no page. Not a checker gap by itself; listed because it counts as missed in the table.
4. **Pair 18:00 UTC = 23:30 IST is absent from every v30 page** (owner pages A and B, card, appendix, film page, both lead pages). The other three pairs (18:29=23:59, 18:19=23:49, 18:04=23:34) are right. 18:29=23:59 is in the owner pages (x5 per sheet, 4 of them in the appendix); 18:19=23:49 and 18:04=23:34 are in the lead pages only (x3 and x5), not in any owner page. The `18:00 = 23:30` in the brief matches no v30 text (v30 uses 18:04 for the 23 Nov latest start).
5. My own secret scan reports 2 email-shaped hits (OWNER-APPENDIX-v30-A.md line 71, -B.md line 69): the masked example text `de…1@gmail.com` (a made-up masked address shown as an example). No full address, no key-shaped string (anthropic shape built from parts: 0 hits; AWS shape: 0 other than the allowed example; github, slack, JWT, private key, bearer, long token shapes: 0).
6. Not mine: `git status` shows `evidence-r15-runner/mutate.py` and `mutate-run.txt` modified, and the git log shows automatic "wip" commits at 17:23-17:24 UTC that already contain my evidence folder. I did not touch evidence-r15-runner. Some other process is committing in this tree. My script outputs may therefore appear in those commits.
7. My first run of indep30.py had 6 FAIL lines that were my own mistakes (looked for 18:19/18:04/18:00 in owner pages only; flagged the explanatory `[OWNER FILLS ...]` text as an odd spelling). I fixed the script; both versions of the logic are described here, only the final output is saved.

## Results
| # | Step | Result | Raw file |
|---|---|---|---|
| 1a | `build-v30.py` | rc 0; 9 files built; hashes of all v30 pages, both lead pages and the three scripts identical before and after (build changed nothing) | out-build-v30.txt, hashes-before.txt, hashes-after-build.txt |
| 1b | `check-v30.py` | rc 0, "0 failure(s)" | out-check-v30.txt |
| 2a | `mut30.py` | rc 0; 209 plants: 208 caught by the meant check, missed 0, anchor-not-found 0; 1 negative control printed MISSED as it must | out-mut30.txt |
| 2b | `v30-fail-proof.py` | rc 0; Part 7 has 23 checks (C185 to C209), all 23 fail on built v29, none fail on built v30 | out-fail-proof.txt |
| 3a | word counts (words as split on spaces) | sheet A 6285, sheet B 6097, card A 1777, card B 1711, appendix A 3950, appendix B 3881, film page 442; lead note v14 12837, open list 7527. Sheet A+appendix+film 10677; B 10420 | out-indep30.txt (I01) |
| 3b | UTC/IST pairs | every pair in all 9 pages checked with +5:30 (calculation in script): 0 wrong, 0 missing partner. Required pairs: see deviation 4 | I02 |
| 3c | weekdays | every "Weekday D Mon [2026]" mention checked: 0 wrong. Mon 16 / Wed 18 / Mon 23 / Wed 25 Nov 2026 present in both sheets' owner pages and correct | I03 |
| 3d | placeholders | both `[OWNER FILLS: ...]` (x4 per sheet) and `[LEAD FILLS at re-pin: ...]` (x5 per sheet) present in owner pages A and B; also in lead note (x4, x5) and open list (x1, x1) | I04 |
| 3e | "cancel the older key" in lead pages | 3 mentions, all descriptive (the owner cancels), none in lead-message wording by my heuristic; plus variants "cancels/cancelling/Cancelling the older key". My heuristic is crude; a person should read the 3 lines printed in I05 | I05 |
| 3f | appendix pointers | appendix parts 1 to 10 present in A and B, none empty; all 10 distinct pointers resolve in A (36 mentions) and B (34 mentions); 0 unresolved | I06 |
| 3g | rebuild into temp, compare | rebuild rc 0; all 9 built files byte-equal to disk (sha256 prefixes in file) | I07 |
| 3h | secret scan | see deviation 5; all other patterns 0 hits | I08 |
| 3i | banned-string scan | 10 entries read from the test file at run time; hits 0 over 9 built pages and 11 other v30 files (counts only, strings never printed) | I09 |
| 4 | 15 hostile mutations on a temp copy | caught 12, missed 3 (H06, H09, H15), anchor-missing 0 | out-hostile30.txt |

Hostile mutations (id: what, result, codes): H01 deadline +10 min in facts: caught C03,C79. H02 placeholder misspelled: caught C108. H03 wrong weekday: caught C04. H04 built sheet pointer to appendix 11: caught C01,C19,C201. H05 key-shaped text built from parts: caught C55. H06 see deviation 1: MISSED. H07 wrong IST on deadline in built appendix: caught C01,C04. H08 wrong IST for 18:04 in lead note: caught C04. H09 see deviation 2: MISSED. H10 banned string: caught C06. H11 built card B cut by 15 lines: caught (22 codes incl. C01). H12 post-by pair wrong: caught C03,C04,C19,C73. H13 old exact wording in lead note: caught C188. H14 sheet date Mon 17 Nov: caught C04. H15 see deviation 3: MISSED.

Not checked: that the sheet content is understandable or correct for a real person; the claims of the sheets about the model company's pages (marked UNVERIFIED in the sheets); any text outside the 9 pages and the listed scripts; the live CI gates (ruff, pytest, bandit) of the repo.
Agents/shells started by me: 1 background shell (mut30.py run), finished (rc 0). None left.
