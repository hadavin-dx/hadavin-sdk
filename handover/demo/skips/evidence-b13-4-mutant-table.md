| v6 mutant | source | mutant | result with v6 (autocrlf false and true) |
|---|---|---|---|
| F1 | reviewer-F | hint loses git cure | KILLED |
| F2 | reviewer-F | python cure deletes lone CR | KILLED |
| F3 | reviewer-F | python cure deletes CRLF | KILLED |
| F4 | reviewer-F | git cure without -- | KILLED |
| F5 | reviewer-F | LF_ONLY_FILES drops exceptions.txt | KILLED |
| F6 | reviewer-F | only CRLF counts | KILLED |
| F7 | reviewer-F | lone CR at EOF ignored | KILLED |
| F8 | reviewer-F | safety assert removed | KILLED |
| F9 | reviewer-F | safety assert weakened | KILLED |
| F10 | reviewer-F | filter by .txt suffix | KILLED |
| F11 | reviewer-F | message lists first bad file only | KILLED |
| F12 | reviewer-F | guard body emptied | KILLED |
| F13 | reviewer-F | planted tree without .gitattributes | KILLED only with autocrlf=true |
| F14 | reviewer-F | gitleaks test: crlf copy gets LF | KILLED |
| F15 | reviewer-F | gitleaks test: no --config | SURVIVED |
| F16 | reviewer-F | gitleaks test: cwd dropped | KILLED |
| F17 | reviewer-F | hint drops py -3 | KILLED |
| F18 | reviewer-F | hint drops needs Python | KILLED |
| F19 | reviewer-F | hint drops python3 macOS note | KILLED |
| F20 | reviewer-F | hint drops throws away warning | KILLED |
| F21 | reviewer-F | hint drops replace <file> note | KILLED |
| F22 | reviewer-F | hint drops a text file | KILLED |
| F23 | reviewer-F | hint adds third backtick cure | KILLED |
| F24 | reviewer-F | ls-files -o added | SURVIVED |
| F25 | reviewer-F | guard_message leaks REPO patch (v5 form) | KILLED |
| F26 | reviewer-F | lone-cr param removed | SURVIVED |
| F27 | reviewer-F | cure test compares to nothing (tautology) | SURVIVED |
| F28 | reviewer-F | hint cure order: CR first | KILLED |
| F29 | reviewer-F | hint python3 for python (Windows has none) | KILLED |
| F30 | reviewer-F | _planted_tree: index not LF (setup) | SURVIVED |
| G1 | E6 | guard matches the base name only (a nested file of the same name is flagged) | KILLED |
| G2 | E16 | hint drops 'or a lone CR' | KILLED |
| G3 | E15/N16 | bad files joined with a space | KILLED |
| G4 | E13 | premise test accepts any exit code but 1 as clean (the min patch's form) | KILLED |
| G5 | E13 | premise test: gitleaks gets a bad option (exits 126) | KILLED |
| G6 | E13 | premise test: --exit-code 0 (never fails) | KILLED |
| G7 | N19 | ls-files taken from the real repo, not the tree under test | KILLED |
| G8 | C15 | guard reads the index blob, not the work copy | KILLED |
| G9 | M6 | cure 1 replaced by git add --renormalize | KILLED |
| G10 | N8 | message without the file names | KILLED |
| G11 | N15 | python cure without the lone-CR replace | KILLED |
| G12 | E26 | planted tree: only the odd file written | SURVIVED |
| G13 | own | LF_ONLY_FILES also lists .gitleaks.toml (wider than measured) | SURVIVED |
| G14 | own | cure test runs only the first cure | SURVIVED |
| G15 | own | cure test: the file is not compared (cure may leave a CR-free but wrong file) | SURVIVED |
| G16 | own | cure test: guard recheck dropped (only the bytes compared) | SURVIVED |
| G17 | own | empty-list message loses the word empty | KILLED |
| G18 | own | python cure: replaces CR with nothing then LF text kept (drops all CR bytes, joins lone-CR lines) | KILLED |
| G19 | own | HINT_PHRASES check removed from the guard test | SURVIVED |
| G20 | own | premise test: .gitleaks.toml not copied (gitleaks falls back to defaults) | KILLED |
| G21 | own | REPO patch leaks (v5 form) AND the lone-CR cure deletes the CR | KILLED |
| G22 | E13 | crash test: the fake crash (exit 2) on the clean copy becomes exit 0 | KILLED |
| G23 | C18 | guard reads untracked files only (ls-files -o) | KILLED |

## Builders' 58-row table (evidence-b10-8-mutant-table.md) mapped onto v6

| id | mapped to | v6 result |
|---|---|---|
| N1 | F1 | KILLED |
| N2 | n/a: no .ps1 exemption in v6 (list is 2 exact names) | n/a: no .ps1 exemption in v6 (list is 2 exact names) |
| N3 | F10 | KILLED |
| N4 | F5 | KILLED |
| N5 | n/a: no _crlf_note in v6 | n/a: no _crlf_note in v6 |
| N6 | n/a: no report rows read in v6 | n/a: no report rows read in v6 |
| N7 | n/a: no report JSON read in v6 | n/a: no report JSON read in v6 |
| N8 | G10 | KILLED |
| N9 | n/a: scan failure message not touched in v6 | n/a: scan failure message not touched in v6 |
| N10 | F10 | KILLED |
| N11 | F8 | KILLED |
| N12 | n/a: v6 reads the file; a tracked file deleted from the work tree is a FileNotFoundError (loud) | n/a: v6 reads the file; a tracked file deleted from the work tree is a FileNotFoundError (loud) |
| N13 | n/a: no .ps1 exemption | n/a: no .ps1 exemption |
| N14 | F1 | KILLED |
| N15 | G11 | KILLED |
| N15b | F3 | KILLED |
| N15c | n/a: obsolete (v3 sed text) | n/a: obsolete (v3 sed text) |
| N16 | F11 | KILLED |
| N17 | n/a: scan args not touched in v6 | n/a: scan args not touched in v6 |
| N18 | n/a: scan args not touched in v6 | n/a: scan args not touched in v6 |
| N19 | G7 | KILLED |
| M1 | F12 | KILLED |
| M3 | n/a: no note in v6 | n/a: no note in v6 |
| M3b | n/a: no scan wrapper in v6 | n/a: no scan wrapper in v6 |
| M5 | F12 | KILLED |
| M6 | G9 | KILLED |
| M8 | n/a: no _flagged_files in v6 | n/a: no _flagged_files in v6 |
| M9 | F6 | KILLED |
| C1 | F28 | KILLED |
| C2 | F29 | KILLED |
| C3 | n/a: no report paths in v6 | n/a: no report paths in v6 |
| C4 | n/a: no report rows | n/a: no report rows |
| C5 | n/a: no report rows | n/a: no report rows |
| C6 | n/a: scan args not touched | n/a: scan args not touched |
| C7 | n/a: scan args not touched | n/a: scan args not touched |
| C8 | n/a: scan cwd not touched | n/a: scan cwd not touched |
| C9 | F11 | KILLED |
| C10 | n/a: no note | n/a: no note |
| C11 | F23 | KILLED |
| C12 | F20 | KILLED |
| C13 | F18 | KILLED |
| C14 | F19 | KILLED |
| C15 | G8 | KILLED |
| C16 | F7 | KILLED |
| C17 | G1 | KILLED |
| C18 | G23 | KILLED |
| C19 | n/a: no pyproject marker in v6 | n/a: no pyproject marker in v6 |
| C20 | n/a: no .editorconfig in v6 | n/a: no .editorconfig in v6 |
| C21 | n/a: no .editorconfig in v6 | n/a: no .editorconfig in v6 |
| C22 | F14 | KILLED |
| C23 | n/a: report path code not touched | n/a: report path code not touched |
| C24 | n/a: test_hygiene_scan_public not touched | n/a: test_hygiene_scan_public not touched |
| C25 | n/a: no _scan_failure_message | n/a: no _scan_failure_message |
| C26 | n/a: no CRLF_BY_DESIGN list | n/a: no CRLF_BY_DESIGN list |
| D1 | F17 | KILLED |
| D2 | F21 | KILLED |
| D3 | F22 | KILLED |
| D4 | F13 | KILLED only with autocrlf=true |

## Reviewer's 26 E-mutants (rv25 mutc.py) mapped onto v6

| id | mapped to | v6 result |
|---|---|---|
| E1 | n/a: no CRLF_BY_DESIGN | n/a: no CRLF_BY_DESIGN |
| E2 | n/a: .gitleaks.toml not in the list (G13 widens it) | n/a: .gitleaks.toml not in the list (G13 widens it) |
| E3 | F5 | KILLED |
| E4 | n/a: patterns.txt not in the list | n/a: patterns.txt not in the list |
| E5 | n/a: requirements-*.txt not in the list | n/a: requirements-*.txt not in the list |
| E6 | G1 | KILLED |
| E7 | F2 | KILLED |
| E8 | F4 | KILLED |
| E9 | n/a: no is_file() call in v6 | n/a: no is_file() call in v6 |
| E10 | F9 | KILLED |
| E11 | n/a: no _flagged_files | n/a: no _flagged_files |
| E12 | n/a: no _gitleaks_common | n/a: no _gitleaks_common |
| E13 | G4 + G22 (+ fake gitleaks programs, evidence-b13-2) | KILLED |
| E14 | n/a: no _gitleaks_scan | n/a: no _gitleaks_scan |
| E15 | G3 | KILLED |
| E16 | G2 | KILLED |
| E17 | F30 | SURVIVED |
| E18 | F24 | SURVIVED |
| E19 | n/a: no .editorconfig | n/a: no .editorconfig |
| E20 | n/a: no .editorconfig | n/a: no .editorconfig |
| E21 | n/a: no .editorconfig | n/a: no .editorconfig |
| E22 | n/a: no pyproject marker | n/a: no pyproject marker |
| E23 | n/a: no pyproject marker | n/a: no pyproject marker |
| E24 | n/a: no marker | n/a: no marker |
| E25 | n/a: .gitattributes not touched by v6 | n/a: .gitattributes not touched by v6 |
| E26 | G12 | SURVIVED |
