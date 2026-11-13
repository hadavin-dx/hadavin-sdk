# out-ver3 (read-only verifier; EGM skipped: read-only verification; no bible R-numbers needed, no model/spend used)
| row | verified how | verdict |
|---|---|---|
| limits.md:91 Known gaps deleted | grep "Known gaps"/"indications for the machine" over tree: no hit; limits.md:85 says "No result of this test is stored here, and no figure ... for any computer"; line 62 also says no run result stored | TRUE |
| README.md:117 | read line; grep "Windows computer" over tree: no hit; link target docs/limits.md:85 says same | TRUE |
| n8n-recipe.md:18 community licence | read lines 18-19; line 76 says NOT checked: "running the workflows WITHOUT a free registered n8n community licence"; new sentence says "also run WITH ... licence is not checked" = inverted meaning, and contradicts line 10 (licence is an item used) | FALSE. Replace with: "Whether the workflows here also run without n8n's free community licence is not checked" |
| n8n-recipe.md:24 port 5679 | scripts/n8n_api.py:3 and :89 default 5679; n8n/proof.json:149 url 127.0.0.1:5679 | TRUE |
| semgrep.in:3 "with this command" | read; lock .txt starts at the first package (no header); command line 4 is literal | TRUE |
| semgrep.in:5 "a fixed date" | line 4 command holds literal 2026-11-12; comment repeats it | TRUE |
| semgrep.in:10 who bumps | LICENSE line 1 names the author; README:14,174 call that person "the author"; quarter clause gone | TRUE |
| .coderabbit.yaml:3 | README:174 "Outside contributions (pull requests) are not accepted" supports "only the author pushes" | TRUE |
| test_gitleaks_exceptions.py:7-8 | variants() lines 56-62; ONLY_LITERAL_SCAN (108) holds "other project, letters only"; "letters and digits" is in neither set so both scans assert it; no "repeated character" text left | TRUE |
| sonar.yml:4 | line 4 is 89 chars, next line 112 (awk length); YAML equals main (below). Side note: the notes claim "also fixes the 120-char rule", but 13 lines are over 120 both in main and now (e.g. the new line 164 is 162 chars); no test or ruff rule covers yml (pyproject line-length 120 is Python only). Not a row text, so no verdict change | TRUE (comment text); the "120-char" claim UNPROVEN: delete it from the notes |
| settings.md:72 | read: sentence is about a real mail relay or tunnel on 127.0.0.1 that the desk cannot see; src/lead_desk/config.py:64-78 is_loopback_host accepts only loopback IPs; new wording matches | TRUE |

Special checks
* requirements-semgrep.in: the diff command printed only the +++/--- lines: non-comment lines identical to f3c39cf8.
* YAML: safe_load of main vs file: .github/workflows/sonar.yml True, .coderabbit.yaml True.
* Also seen (not in the notes, other builder's edits): sonar.yml diff has extra comment changes (timeout, pip, two-job split); comments only, YAML still equal.
Not checked: full suite not run (not allowed); no file was written in the tree.
