# PR89 round 15, reviewer design (egm-design), head 13b7124
Coverage: runner 1-1223 of 1223. Read-only, nothing run (regexes traced by hand).
Result: no Blocker/Major in slice. No input found that puts a password byte in the hashed lock text, a log line, a result row or an exception message (many URL and key=value hostile shapes walked; all end "unparsed" or a name without password). Docstring vs code matches for refusal, bounds, fragment rule, lock file open flags, Windows paragraph. r14 lock-name, 12/45, Windows items judged fixed in the code.
Minor:
- s1-01 runner 56-66 vs 504-507: doc says every hidden text is decoded and re-encoded; only password texts are. Fix wording (no leak).
- s1-02 runner 91, 519, 528-541: "costs at most a scan of len(secret)" false; head/tail loops slice per candidate, O(len^2) per hit (secret "a"*1999+"b", line ("a"*1998+"c"+"...")*1000, ~4e9 char ops, not measured). Use startswith or reword.
- s1-03 runner 721 vs 1075: environment read twice; a value changed mid-run by caller code is never refused or masked. Read once, pass dict to _pytest, state in docstring.
Nit: s1-04 runner 320 dead `\t`; s1-05 runner 97/660/455 "no password text is read" should say never captured or hashed.
