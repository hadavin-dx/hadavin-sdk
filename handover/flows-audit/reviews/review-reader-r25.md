# REVIEW.md round 25 fresh reader (agent af02fb4), uncapped. Reviewer words unverified. Saved by flows-audit, condensed.
0 Blockers, 9 Majors. Checked by reader: 28 rows, 4 Major/13 Minor/11 Nit by grep; 25+9b+23b+5-K+Q1=29; alt-count arithmetic; 18+7=25; code pointers config.py:394, app.py:62, tick.py:85, chain.py:232, local_dir.py:126, protocol.py:27 correct. Not read: lines 191-289 in full, History 469-615.
M1 Q1 branches contradict lead default and other lines (L361 "does not drop the patch" vs L456; L64 unconditional vs L127/L145 conditional on Route config; Decision 18 same whatever Q1 says; "it" in Decision 18 / A-6 unclear: A-6 belongs to A-01).
M2 Decision 2(a) ordered before X-2 it depends on (L364 vs L359/L194/L330/L332); drain-in-tick (L421) vs separate program (criterion 6, L413); "drain" two meanings.
M3 Start-up check lets a note stand for criteria notes cannot close ((1),(6),(9): L31, L404, L415 vs L407); coverage differs ((1)-(9) vs (1)-(7),(9)).
M4 Decisions missing from the 29: who names notes folder (L417,L447); binding method (signed commit vs CODEOWNERS + repo-setting yes, L415); whether start-up refusal wanted (L448); "does not sign" setting (L367) sized only inside option (i).
M5 L72 says table gives who/when/size for each of 29; table (L328-356) has 27 rows; Q1 and 5-K no row; Q1 "asked first but does not gate" odd.
M6 "step" second meaning after L19 (L31, L339, L372, L427, approvals steps).
M7 Decision 19 answer format unusable (L383): whole number vs decimal examples (C-8 0.05, L150 0.000001); "two bad results" undefined.
M8 Timing/doer: Decision 2 trigger "before proposal sent" (L330,L364) vs "before first pilot" (L420); L326 "nothing built" vs L446 fallback "not deferred", fallback is new write path needing X-2.
M9 Pointers: L64/L127 cite patch-copies/README.md line 154 (text at 168); L64 "line 8 says 24 tests instead of 26" (line 8 says 26 new; 32 with A-01; 24 cases at 189); header L3 says last edit fix-review16, L321/L427 credit fix-review17; bare log names resolve only in flows-audit/reviews; /tmp cites may be cleared.
Notes: units "three/nine serious/11 Major"; "owner" git sense in L31/L415.
