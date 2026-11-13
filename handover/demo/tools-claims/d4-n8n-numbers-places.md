# d4: n8n comparison numbers in README.md and docs

Studio folder note: the studio folder does not exist in this container, so no R-numbers were looked up or cited.
Tree edited: /tmp/d4-work (README.md and docs/*.md only; no tests, no lint, no network).

## Important finding
The repository holds NO source file for any n8n comparison result. The n8n-only variants (a to d, a variant "e" with a second CRM row), their ten-at-once counts, replays and kill runs are not in this tree: versions.md, contract.md, README.md and docs/*.md contain no variant "e" and no "second CRM row" text, and n8n/ holds only three workflow files (desk-form.json, desk-webhook.json, proof.json), which are workflows, not results. The only n8n numbers in the text are those of the desk-behind-n8n run of 2026-11-09 (docs/n8n-recipe.md).

## Table (Task 1)
| file:line | numbers | source file in repo | own run label (quote) | says runs can differ (before my edit) |
|---|---|---|---|---|
| docs/n8n-recipe.md:34 | replay of same id recognised ("replayed": true) | NONE | yes: "from the author's own run; no log is shipped" | no |
| docs/n8n-recipe.md:46 | reply body passed through, status 200 | NONE | yes: "from the author's own run; no log is shipped" | no |
| docs/n8n-recipe.md:52 | same lead: 200, verdict duplicate; second reply replayed | NONE | partly: intro line 4 says "run ... on 2026-11-09, on one computer" | no |
| docs/n8n-recipe.md:54 | retry 3 tries, 1 s apart; success on 2nd try after about 1 s; failure within about 2 s; rejected call counted 3 times; one lead, one CRM row, one e-mail | NONE (n8n/desk-form.json holds only the retry setting) | partly: line 4 "run against the desk on 2026-11-09" | no |
| docs/n8n-recipe.md:68 | n8n success mark shown for a duplicate caller answered with an error | NONE | yes: "from the author's own run; no log is shipped" | no |
| docs/n8n-recipe.md:70 | ten at once: 1 new, 9 duplicates, 1 CRM row, 1 e-mail; all ten stored in the same second; first import and clean re-import, 2026-11-09 | NONE (n8n/proof.json is the workflow; demo_only/burst.py, tests/test_http.py::test_ten_parallel run the desk-only burst, not n8n) | yes: "Checked (from the author's own run; no log is shipped)" | no |
| docs/n8n-recipe.md:74 | findings header for lines 76-82 | NONE | yes: "all from the author's own run on 2026-11-09; no log is shipped" | no |
| docs/n8n-recipe.md:76-78 | 200 for desk 201/202; refusal 400/413 shown as 500, counted 3 times; restart: 2nd try ok after about 1 s, down a few seconds fails within about 2 s | NONE | yes (via line 74 header) | no |
| docs/n8n-recipe.md:79 | ten at once: 1 email, 1 CRM row, all ten stored within the same second, two runs | NONE | yes: "in the runs made (first import, and again after a clean re-import)" (own-run label comes from line 74) | no |
| docs/limits.md:70 | real kill while a load ran, every follow-up ended sent; number of runs not recorded | NONE (load_tools/ holds the load driver and checks, not the result; the text says script and logs are not shipped) | yes: "from the author's own run" | no (says number of runs not recorded) |
| docs/limits.md:93-96 | burst: 150 connections all answered, from about 300 some refused (desk-only, not n8n) | NONE | yes: "tried once by the author, logs not shipped" | YES: "the counts varied from run to run" |
| docs/tests.md:124, docs/limits.md:92 | ten requests, one new, nine duplicates, one email (desk-only burst, reproducible) | tests/test_http.py::test_ten_parallel (a test, not an n8n result) | n/a (test) | n/a |
| README.md:126, docs/why-this-code.md:13, docs/limits.md:17 and :73 | no numbers: say n8n-only patterns were "tried once", logs not shipped, no result stated | NONE | yes: "tried once, by the author" | no (they state no numbers, so nothing to hedge) |
| docs/n8n-recipe.md:56-63 | patterns (a) to (d) described, no results | NONE | "no result about them is claimed here" | not needed |
| versions.md, contract.md | no n8n comparison numbers (contract.md:238 only documents the burst script) | n/a | n/a | n/a |

Numbers whose source file is NONE (no result in the repository backs them): the replay result (n8n-recipe.md:34, :52); the 200 status finding (:46, :76); the 3-tries timings of about 1 s and about 2 s and the 3-fold counting (:54, :77, :78); the n8n success mark for a duplicate (:68); ten at once = 1 new, 9 duplicates, 1 CRM row, 1 e-mail, stored within the same second (:70, :79); the real-kill result "every follow-up ended sent" (limits.md:70); the 150 and 300 connection burst figures (limits.md:93). No number for a variant "e" or a second CRM row exists anywhere in the tree, so there was nothing to hedge there and nothing was invented.

## Edits applied (Task 2), old part -> new part
All in /tmp/d4-work; original numbers untouched; prose only. The edits were made with /tmp/work/d/d4_edit.py.

1. docs/n8n-recipe.md (intro, line 6)
   old: "the names below were not compared with the screen."
   new: "the names below were not compared with the screen. All counts and timings quoted in this page come from the author's own published run; runs can differ, the counts moved a little between runs, and an independent rerun by another person differed slightly from the published run (the numbers of that rerun are not in this repository)."
2. docs/n8n-recipe.md (section 3, line 70)
   old: "(on the first import and again after a clean re-import, 2026-11-09)."
   new: same text followed by " These are the numbers of the author's published run only: another run can give other counts, and an independent rerun differed slightly (its numbers are not in this repository), so read them as one run, not as a fixed result."
3. docs/n8n-recipe.md (section 4 header, line 74)
   old: "(all from the author's own run on 2026-11-09; no log is shipped):"
   new: "(all from the author's own run on 2026-11-09; no log is shipped; counts and timings can differ from run to run, and an independent rerun differed slightly):"
4. docs/n8n-recipe.md (section 4, ten-at-once bullet, line 79)
   old: "... not milliseconds). These runs used"
   new: "... not milliseconds). These are the published run's numbers; runs can differ. These runs used"
5. docs/n8n-recipe.md (item 7 of the checklist, line 54)
   old: "so the 3-fold counting is an effect of this setting."
   new: same text followed by " The timings and counts in this item are from the author's own run and can differ between runs."
6. docs/limits.md (line 70, kill run)
   old: "The author reports that every follow-up ended `sent`,"
   new: "The author reports that in that run every follow-up ended `sent` (what such a kill run shows can differ from run to run, and no repeat of it is shipped),"

Not edited, on purpose: README.md:126, docs/why-this-code.md:13, docs/limits.md:17 and :73 (no numbers, already say "tried once, logs not shipped, no result stated"); docs/limits.md:93 (already says counts varied from run to run); tests.md P5 (a reproducible test, not the n8n comparison).

## Checks done
Only a text scan of my added lines: no URLs or host names, no run of 40 or more unbroken characters, no backslash quotes, no new backticks, no table rows touched (git diff shows 2 files, 6 lines changed). I did not run lint, tests or the repository scan (not allowed). The words "an independent rerun differed slightly" come from your brief; the rerun's numbers are not in the repository and were not guessed.
Not checked: the lead's note (not in the tree); whether the Windows line-endings of the files were preserved (the script wrote with newline untouched, a git diff shows only the 6 intended lines).
