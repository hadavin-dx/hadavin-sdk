| id | source | mutant | v4 result (before) | v5 with gitleaks | v5 without gitleaks |
|---|---|---|---|---|---|
| N1 | builders | hint loses git checkout cure | KILLED | KILLED | KILLED |
| N2 | builders | .ps1 no longer exempt | KILLED | KILLED | KILLED |
| N3 | builders | .txt also exempt | KILLED | KILLED | KILLED |
| N4 | builders | LF_ONLY_FILES cut to sonar only | KILLED | KILLED | KILLED |
| N5 | builders | _crlf_note always empty | KILLED | KILLED | KILLED |
| N6 | builders | ./ prefix kept | KILLED | KILLED | KILLED |
| N7 | builders | bad JSON raises | KILLED | KILLED | KILLED |
| N8 | builders | file list dropped from message | KILLED | KILLED | KILLED |
| N9 | builders | message drops 'values are redacted' | KILLED | KILLED | KILLED |
| N10 | builders | scan-file filter off | KILLED | KILLED | KILLED |
| N11 | builders | safety assert removed | KILLED | KILLED | KILLED |
| N12 | builders | missing file not skipped | KILLED | KILLED | KILLED |
| N13 | builders | .ps1 case sensitive | KILLED | KILLED | KILLED |
| N14 | builders | guard message drops the cure | KILLED | KILLED | KILLED |
| N15 | builders | python cure loses the lone-CR replace | KILLED | KILLED | KILLED |
| N15b | builders | python cure CRLF replace broken | KILLED | KILLED | KILLED |
| N15c | builders | v3 sed cure instead of python cure | SKIP | n/a: v3 sed text no longer exists | n/a: v3 sed text no longer exists |
| N16 | builders | every file reported | KILLED | KILLED | KILLED |
| N17 | builders | scan --exit-code 1 -> 0 | KILLED | KILLED | KILLED |
| N18 | builders | scan without report format | KILLED | KILLED | KILLED |
| N19 | builders | ls-files from wrong path | KILLED | KILLED | KILLED |
| M1 | builders | CR check always false | KILLED | KILLED | KILLED |
| M3 | builders | note never appended | KILLED | KILLED | KILLED |
| M3b | builders | scan bypasses the message function | KILLED | KILLED | KILLED |
| M5 | builders | guard test body emptied | KILLED | KILLED | KILLED |
| M6 | builders | cure 1 replaced by --renormalize | KILLED | KILLED | KILLED |
| M8 | builders | _flagged_files always [] | KILLED | KILLED | KILLED |
| M9 | builders | only CRLF counts, lone CR ignored | KILLED | KILLED | KILLED |
| C1 | reviewer | cure order swapped (CR first then CRLF) | KILLED | KILLED | KILLED |
| C2 | reviewer | hint says python3 (Windows has no python3) | KILLED | KILLED | KILLED |
| C3 | reviewer | backslash->slash normalisation dropped (Windows report paths) | SURVIVED | KILLED | KILLED |
| C4 | reviewer | flagged files not de-duplicated | SURVIVED | KILLED | KILLED |
| C5 | reviewer | rows without File kept as empty name | SURVIVED | KILLED | KILLED |
| C6 | reviewer | --ignore-gitleaks-allow dropped from shared args | SURVIVED | KILLED | KILLED |
| C7 | reviewer | --redact dropped from shared args | SURVIVED | KILLED | KILLED |
| C8 | reviewer | scan cwd dropped | KILLED | KILLED | KILLED |
| C9 | reviewer | guard message lists only first bad file | SURVIVED | KILLED | KILLED |
| C10 | reviewer | note lists only first bad file | SURVIVED | KILLED | KILLED |
| C11 | reviewer | hint adds a third (bad) backtick cure | KILLED | KILLED | KILLED |
| C12 | reviewer | hint drops 'throws away your edits' warning | SURVIVED | KILLED | KILLED |
| C13 | reviewer | hint drops the 'needs Python' note | SURVIVED | KILLED | KILLED |
| C14 | reviewer | hint drops the python3-on-macOS note | SURVIVED | KILLED | KILLED |
| C15 | reviewer | guard scans index blobs not work copy (reads git show) | KILLED | KILLED | KILLED |
| C16 | reviewer | guard skips lone CR at file end | SURVIVED | KILLED | KILLED |
| C17 | reviewer | guard skips directory-nested via fnmatch->basename only? exact-match list | KILLED | KILLED | KILLED |
| C18 | reviewer | guard uses git ls-files -o only (untracked) | KILLED | KILLED | KILLED |
| C19 | reviewer | pyproject marker not registered | SURVIVED | KILLED | KILLED |
| C20 | reviewer | .editorconfig says ps1 lf | SURVIVED | KILLED | KILLED |
| C21 | reviewer | .editorconfig [*] says crlf | SURVIVED | KILLED | KILLED |
| C22 | reviewer | gitleaks test: crlf copy gets LF (always clean)  | KILLED | KILLED | SURVIVED |
| C23 | reviewer | report written inside scanned tree (target) instead of outside | SURVIVED | SURVIVED | SURVIVED |
| C24 | reviewer | real-scan: failure assert dropped in test_hygiene_scan_public | SURVIVED | SURVIVED | SURVIVED |
| C25 | reviewer | _scan_failure_message drops sub name | SURVIVED | KILLED | KILLED |
| C26 | reviewer | CRLF_BY_DESIGN adds .bat | KILLED | KILLED | KILLED |
| D1 | this builder | hint loses the 'py -3' Windows note | n/a (new) | KILLED | KILLED |
| D2 | this builder | hint loses 'replace <file> with the path' | n/a (new) | KILLED | KILLED |
| D3 | this builder | hint says 'Windows line endings' only for text (the binary wording dropped) | n/a (new) | KILLED | KILLED |
| D4 | this builder | .gitattributes dropped from the planted tree (the autocrlf bug) | n/a (new) | SURVIVED here; KILLED with autocrlf=true | SURVIVED; KILLED with autocrlf=true |
