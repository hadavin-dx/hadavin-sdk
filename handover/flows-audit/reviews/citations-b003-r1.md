# Citation check of RW and CT, B-003a-d rows and pair sync (egm-codebase-details, agent a72843e5b5d439bd0, round 1)
Saved by flows-audit, condensed. Reviewer words are unverified until checked. Read-only, no edits. 5 failures, no Blockers (listed as Majors).
1. Major: B-003c (RW:302) and B-219 (RW:359) both replace the sentence at ONS:131 with different strings; whichever applies first removes the other's old text. Fix: one row owns ONS:131.
2. Major: B-101 (RW:330, CT:622) old quote stops at ")" but RUN-ON-LAPTOP.md:56 continues ", or done without exactly 1 CRM row and 1 mail." After replacement the line says the same thing twice. Old quote must run to sentence end. mf.py:83 supports the new string.
3. Major: B-010 CT note (CT:515) still says "three different made-up addresses"; RW string says "different". PLAN:37 is a table row, old text "CRM write / one contact per lead" is not word for word.
4. Major: B-003b/c/d replacement contains internal id "A-016f"; public post text and owner question must not. ONS:135 quote marks plus multi-sentence string read badly.
5. Major: B-045 replaces only the first sentence of PLAN:79; the next sentence (10 concurrent posts: 1 fresh, 9 cached, 0 unknown) contradicts it.
Passes: B-003a-d old quotes found at PLAN:9, :57, ONS:131, :135; PLAN:184 correctly has no row; 30 of 57 "this string wins" pairs identical; Q28 caption row matches ORDERS lines 144, 166.
Not checked: other 27 "this string wins" rows; R:33/R:41 cites; V5-README:17; behaviour of take scripts.
