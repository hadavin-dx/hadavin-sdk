# notes-r1fix7 (builder, tree /tmp/final-series, nothing committed; EGM skipped: wording edits to docs/comments, lead runs EGM)
| sentence | file:line | old | new | proof |
|---|---|---|---|---|
| Known gaps bullet | docs/limits.md:91 | "Known gaps in these figures ... indications for the machine they ran on" | deleted | limits.md:85-86 says no result/figure is stored; no figure remains to qualify |
| Windows-computer figures | README.md:117 | "The measured figures ... one Windows computer, were tried by the author ... raw logs are not shipped ..." | "No measured load figure is stored in this repository (see `docs/limits.md`)." | same limits.md lines; grep "Windows computer" finds nothing else |
| community licence | docs/n8n-recipe.md:18 | "The runs used its free community licence; whether the workflows here also run without it is not checked" | "Whether the workflows here also run with n8n's free community licence is not checked" | no run log in tree (grep "community" only here) |
| port 5679 | docs/n8n-recipe.md:24 | "The demo ran n8n on port 5679" | "The shipped files expect n8n on port 5679" | scripts/n8n_api.py:3,89 and n8n/proof.json:149 hold 5679 |
| lock command | requirements-semgrep.in:3 | "with the command that made it" | "with this command" | lock file has no header; nothing proves which command made it |
| exclude-newer date | requirements-semgrep.in:5 | "is the day of the first lock run" | "is a fixed date" | same; the date is a literal in the command |
| who bumps | requirements-semgrep.in:10 | "the repository owner ... or about once a quarter" | "the author ..." (quarter clause and hedge "about" removed) | author = person in LICENSE line 1; quarter cadence has no source |
| maintainer | .coderabbit.yaml:3 | "the repository maintainer" | "the author" | same meaning (only the author pushes) |
| gitleaks variants | tests/test_gitleaks_exceptions.py:7-8 | "asserted for gitleaks only if it holds a digit and is not one repeated character; ..." | "a second project key made of letters and digits is asserted for both scans; one made of letters only ... literal scan alone (ONLY_LITERAL_SCAN)" | variants() lines 56-60 and ONLY_LITERAL_SCAN set; no repeated-character case exists |
| secret origin | .github/workflows/sonar.yml:4 | "(created by the author; this file only passes it ...)" (185 chars) | "(set in GitHub, not in this repository)." + second comment line with the rest (90 and 113 chars) | nothing in tree shows who created it; clause deleted; also fixes the 120-char rule |
| owner's responsibility | docs/settings.md:72 | "is the owner's responsibility" | "is the responsibility of whoever runs that relay or tunnel" | sentence is about a relay/tunnel on the loopback address that the desk cannot see |

Non-comment lines of requirements-semgrep.in: byte-identical (git diff, non-# lines: none changed).
Not done: the verifier's optional README "Words used here" entry for "the author" (not in the brief).
Not checked: the full suite (not allowed). Test results: see the reply.
