# v7 mutant table (builder b15). Source: F = reviewer-F 30 and G = builder 23 (the v6 table, evidence-b13-4); rv33 = the 49 of the reviewer's A/B mutants that apply (A14 was invalid in his run, B16/B17 run by hand below); C = 15 new v7 mutants + C0 baseline.
Harness: h/mut15.py (copy of the final patched tests/test_hygiene.py, one text replacement, tests selected `-k "secret_scan_files or names_every_bad or every_cure or reports_a_carriage or crashes"`, `-x`, run under GIT_CONFIG_GLOBAL core.autocrlf=false AND true, gitleaks 8.30.1, DPLD_REQUIRE_SCAN=1). KILLED = a test failed under both settings.

| id | set | mutant | result | note |
|---|---|---|---|---|
| F1 | F | hint loses git cure | KILLED |  |
| F2 | F | python cure deletes lone CR | KILLED |  |
| F3 | F | python cure deletes CRLF | KILLED |  |
| F4 | F | git cure without -- | KILLED |  |
| F5 | F | LF_ONLY_FILES drops exceptions.txt | KILLED |  |
| F6 | F | only CRLF counts | KILLED |  |
| F7 | F | lone CR at EOF ignored | KILLED |  |
| F8 | F | safety assert removed | KILLED |  |
| F9 | F | safety assert weakened | KILLED |  |
| F10 | F | filter by .txt suffix | KILLED |  |
| F11 | F | message lists first bad file only | KILLED |  |
| F12 | F | guard body emptied | KILLED |  |
| F13 | F | planted tree without .gitattributes | KILLED only autocrlf=true | dies only with autocrlf=true (as v6 notes say) |
| F14 | F | gitleaks test: crlf copy gets LF | KILLED |  |
| F15 | F | gitleaks test: no --config | SURVIVED | equivalent: gitleaks finds ./.gitleaks.toml in the cwd |
| F16 | F | gitleaks test: cwd dropped | KILLED |  |
| F17 | F | hint drops py -3 | KILLED |  |
| F18 | F | hint drops needs Python | KILLED |  |
| F19 | F | hint drops python3 macOS note | KILLED |  |
| F20 | F | hint drops throws away warning | KILLED |  |
| F21 | F | hint drops replace <file> note | KILLED |  |
| F22 | F | hint drops a text file | KILLED |  |
| F23 | F | hint adds third backtick cure | KILLED |  |
| F24 | F | ls-files -o added | SURVIVED | equivalent for tracked files |
| F25 | F | guard_message leaks REPO patch (v5 form) | KILLED |  |
| F26 | F | lone-cr param removed | SURVIVED | deletion of a test parameter, not a code mutant |
| F27 | F | cure test compares to nothing (tautology) | SURVIVED | deletion of a test assertion, not a code mutant |
| F28 | F | hint cure order: CR first | KILLED |  |
| F29 | F | hint python3 for python (Windows has none) | KILLED |  |
| F30 | F | _planted_tree: index not LF (setup) | SURVIVED | setup variant, equivalent |
| G1 | G | guard matches the base name only (a nested file of the same name is flagged) | KILLED |  |
| G2 | G | hint drops 'or a lone CR' | KILLED |  |
| G3 | G | bad files joined with a space | KILLED |  |
| G4 | G | premise test accepts any exit code but 1 as clean (the min patch's form) | KILLED |  |
| G5 | G | premise test: gitleaks gets a bad option (exits 126) | KILLED |  |
| G6 | G | premise test: --exit-code 0 (never fails) | KILLED |  |
| G7 | G | ls-files taken from the real repo, not the tree under test | KILLED |  |
| G8 | G | guard reads the index blob, not the work copy | KILLED |  |
| G9 | G | cure 1 replaced by git add --renormalize | KILLED |  |
| G10 | G | message without the file names | KILLED |  |
| G11 | G | python cure without the lone-CR replace | KILLED |  |
| G12 | G | planted tree: only the odd file written | KILLED |  |
| G13 | G | LF_ONLY_FILES also lists .gitleaks.toml (wider than measured) | SURVIVED | wider list than measured; unpinned (not a measured claim) |
| G14 | G | cure test runs only the first cure | SURVIVED | deletion of test lines (the 2 cures are also pinned by the cure-list assertion) |
| G15 | G | cure test: the file is not compared (cure may leave a CR-free but wrong file) | SURVIVED | deletion of a test assertion |
| G16 | G | cure test: guard recheck dropped (only the bytes compared) | SURVIVED | deletion of a test assertion |
| G17 | G | empty-list message loses the word empty | KILLED |  |
| G18 | G | python cure: replaces CR with nothing then LF text kept (drops all CR bytes, joins lone-CR lines) | KILLED |  |
| G19 | G | HINT_PHRASES check removed from the guard test | SURVIVED | deletion of a test assertion (the pin itself is what kills C1-C3, C7, C8) |
| G20 | G | premise test: .gitleaks.toml not copied (gitleaks falls back to defaults) | KILLED |  |
| G22 | G | crash test: the fake crash (exit 2) on the clean copy becomes exit 0 | KILLED |  |
| G23 | G | guard reads untracked files only (ls-files -o) | KILLED |  |
| G21 | G | REPO patch leaks (v5 form) AND the lone-CR cure deletes the CR | KILLED |  |
| A1 | rv33 | cure appends a newline | KILLED |  |
| A2 | rv33 | cure strips the final newline | KILLED |  |
| A3 | rv33 | cure turns a lone CR into a space | KILLED |  |
| A4 | rv33 | cure doubles newlines | KILLED |  |
| A5 | rv33 | cure: read_text/write_text (right on Linux) | SURVIVED | read_text/write_text is right on Linux; differs only on Windows (cannot be told apart here) |
| A6 | rv33 | cure 1: git checkout -- . (wider) | KILLED |  |
| A7 | rv33 | cure 1: git restore | KILLED |  |
| A8 | rv33 | cure 1: git checkout HEAD -- file | KILLED |  |
| A9 | rv33 | scan reads only the first line | KILLED |  |
| A10 | rv33 | scan reads only first 100 bytes | KILLED |  |
| A11 | rv33 | scan: only a CR at the very end | KILLED |  |
| A12 | rv33 | guard checks tests/ not repo | KILLED |  |
| A13 | rv33 | message prints the list repr | KILLED |  |
| A15 | rv33 | cure tests run cures in REPO not the tree | KILLED |  |
| A16 | rv33 | cure test: bytes compared to itself | SURVIVED | weakened assertion of the test itself |
| A17 | rv33 | planted .gitattributes is -text | SURVIVED | `-text` attribute: equivalent here |
| A18 | rv33 | planted .gitattributes is the stricter '* text eol=lf' | SURVIVED | the stricter `* text eol=lf` line: equivalent for these tests |
| A19 | rv33 | weak plant: CR only appended at EOF | KILLED |  |
| A21 | rv33 | premise accepts any non-zero as found | KILLED |  |
| A22 | rv33 | premise: exit 2 counts as found, exit 1 as clean | KILLED |  |
| A23 | rv33 | premise: one dir for both copies | KILLED |  |
| A24 | rv33 | crash test: fake not installed | KILLED |  |
| A25 | rv33 | crash test fake returns 1 on the other copy | KILLED |  |
| A26 | rv33 | crash test expects looser text | SURVIVED | weakened assertion of the test itself |
| A27 | rv33 | LF_ONLY adds patterns.txt | SURVIVED | wider list than measured, same class as G13 |
| A28 | rv33 | LF_ONLY order swapped (equivalent) | SURVIVED | order only: equivalent |
| A29 | rv33 | ls-files uses -z | KILLED |  |
| A30 | rv33 | empty-list assert weakened | KILLED |  |
| A31 | rv33 | HINT_PHRASES any() | SURVIVED | weakened assertion of the test itself |
| A32 | rv33 | cures regex: only >=1 cure | SURVIVED | weakened assertion of the test itself |
| A34 | rv33 | cure 2 missing space before <file> | KILLED |  |
| A35 | rv33 | cure 2 reads sys.argv[2] | KILLED |  |
| A36 | rv33 | nested sub file never added (untracked) | SURVIVED | only matters together with G1 (which is killed) |
| A37 | rv33 | guard test: pytest.raises accepts any exception | SURVIVED | weakened assertion of the test itself |
| B1 | rv33 | cure deletes lone CRs | KILLED |  |
| B2 | rv33 | cure joins lines | KILLED |  |
| B3 | rv33 | cure deletes all CR bytes only | KILLED |  |
| B4 | rv33 | cure writes empty file | KILLED |  |
| B5 | rv33 | cure CRLF only | KILLED |  |
| B6 | rv33 | cure 1 is a no-op (git status) | KILLED |  |
| B7 | rv33 | guard assert emptied | KILLED |  |
| B8 | rv33 | guard: empty list returned | KILLED |  |
| B9 | rv33 | scan ignores CRs followed by LF | KILLED |  |
| B10 | rv33 | scan flags a file name suffix | KILLED |  |
| B11 | rv33 | planted tree always staged | KILLED |  |
| B12 | rv33 | guard_message first line only | SURVIVED | the message is one line: equivalent |
| B13 | rv33 | cure order check reversed-reversed (equivalent) | SURVIVED | identity: equivalent |
| B14 | rv33 | premise: tree not planted with CRLF | KILLED |  |
| B15 | rv33 | premise: gitleaks run on the real repo | KILLED |  |
| C0 | v7 | UNMUTATED baseline (must be SURVIVED) | SURVIVED | unmutated baseline: SURVIVED is the correct result |
| C1 | v7 | hint reverts to the v6 claim: cure 1 on every system | KILLED |  |
| C2 | v7 | hint says cure 1 also works after git add (keeps the restriction sentence) | KILLED |  |
| C3 | v7 | hint drops 'run it again afterwards' | KILLED |  |
| C4 | v7 | hint adds a third cure: rm then checkout | KILLED |  |
| C5 | v7 | staged plant is not staged (git add skipped) | KILLED |  |
| C6 | v7 | staged case no longer expects cure 1 to fail (test weakened) | KILLED |  |
| C7 | v7 | hint drops 'Cure 2 works in every state' | KILLED |  |
| C8 | v7 | hint drops 'only if you have not run git add' (keeps 'does nothing') | KILLED |  |
| C9 | v7 | _run: check defaults to False | KILLED |  |
| C10 | v7 | bad-file test: mid-file shape removed | KILLED |  |
| C11 | v7 | premise test: crlf-copy crash case dropped (test weakened) | SURVIVED | deletion of a test parameter (the code mutants A21/A22/G22 that it serves are killed) |
| C12 | v7 | cure test: staged case dropped (test weakened) | SURVIVED | deletion of a test parameter (the code mutants C1, C2, C5, B11 that it serves are killed) |
| C13 | v7 | plant check before the cure dropped | SURVIVED | deletion of a sanity assertion; a plant without CR would still fail the staged case |
| C14 | v7 | hint offers git restore as cure 1 (works unstaged only) | KILLED |  |
| C15 | v7 | planted .gitattributes only '*.txt' line | KILLED only autocrlf=true | dies only with autocrlf=true: the real sonar-project.properties is covered by `* text=auto` alone |

Totals: 118 rows = 117 mutants + 1 unmutated baseline. KILLED 89, killed only with autocrlf=true 2, SURVIVED 27 (incl. the baseline, which must survive; the other 26 are judged in the note column: none is a mutant of the cure text, the hint, the scan, the file list or the exit codes).

Reviewer rv33 mutants that were SURVIVORS on v6 and are now KILLED: A9 (first line only), A10 (first 100 bytes), A11 (only a CR at the very end), A21 (premise accepts any non-zero), A22 (premise: exit 2 counts as found). B11 (git add after the plant, which died on v6 for another reason) still dies.
By hand, no gitleaks program on PATH (GITLEAKS_BIN unset), DPLD_REQUIRE_SCAN=1, tests `-k "gitleaks_reports or crashes"`: unmutated: 1 failed (the premise test names the variable), 2 passed; with DPLD_REQUIRE_SCAN unset: 2 passed 1 skipped. B16 (skip instead of fail under REQUIRE) and B17 (skip ignores REQUIRE) turn the failed into 1 skipped: the behaviour differs from the unmutated test, but no test of the suite pins it (as in v6; the reviewer ran these by hand too).
