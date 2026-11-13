# Lane 3 fix 4, round 2 (B4b): email capitals rule, documents + pinning test (no product code changed)
Base: public demo repo main f3c39cf89ec989f032ea48a23cfd824b88da9c68. Python 3.12.3 (final-venv), PYTHONPATH=src. Made-up data (example.com).
Plan followed: resolve-round1-lane3-fix-4.md, items 1-16, 18, 20 done; 17 declined; 19 not mine (see "Not done").

## Failures and gaps first
* My own slip, fixed: first draft of the control test expected HTTP 201 for a duplicate; the desk answers 200. Caught by the first run, fixed.
* My own slip, fixed: the first draft of limits.md claimed "95 other rare letters"; that count was not pinned by a test and depends on the Unicode version. Replaced by "Many other rare letters (for example µ ŉ ǰ and a Greek ς before a full stop)", each pinned by `test_other_rare_letters`. The Kelvin sign / U+0130 claim is pinned by `test_refused_letters`.
* The first draft used `ada@bücher.example.com`; the hygiene test flagged it (domain scan matches after the non-ASCII letter). Changed to `ada@xü.example.com` and its punycode `xn--x-eha.example.com`; hygiene passes.
* The full suite was started once, then I stopped it (my own process) after about 3 minutes because I changed the docs and test file (items above); the one full run reported below is on the final tree.
* Hygiene scans: 4 tests SKIPPED (the gitleaks program is not installed here; same skips as the base). Not checked: gitleaks on the new text.
* Not run (CI-only by brief): ruff, mypy, bandit. Line length checked by my own script, counting characters: 0 lines over 120 in the test file.
* The scratch tree for the stack check (/home/user/work/priv/b4b-tmp/stack-only) is a throwaway `git init` with one local commit to give `git apply --check` a clean base; it is not a project repository and nothing was pushed.

## What changed (documents)
1. README, definition of Same lead: plain words, three address pairs with a gloss for each letter (`ß` German sharp s, capital SS; `ı` Turkish dotless i, capital I; `ſ` old long s, "like an f without the crossbar"), first-capital and mixed-case also split (`Istanbul@`, `StraSSe@`), two leads and two follow-up emails (in this demo two entries in the stand-in mail system), rare, `casefold()` would join ß and ſ but NOT ı, remedy only "check the Leads list for entries that differ only in capitals". No ß->ss remedy.
2. README, Not claimed: reads as "Not claimed either: that the same address in capitals is always the same lead ...", lists ß ı ſ and "some other rare letters".
3. README duplicate line (:97): "(same lead, see **Same lead**)".
4. docs/limits.md: new bullet (ordinary letters checked a-z é ü ö ç; the three pairs; first capital and mixed case; Kelvin sign and U+0130 refused not split; remedy; test file) and a second bullet with the short true list: non-ASCII domain vs punycode stay different, a comment in brackets, a domain in square brackets, no 64-character limit before the @ (only 254 for the whole address).
5. contract.md "- Email:" bullet: `lower()` not `casefold()`, ß ı ſ in capitals give a different lead, two follow-ups, first capital/mixed case, other rare letters, pointers.
6. docs/tests.md: sentence naming `tests/test_email_case_rule.py` with ß ı ſ.
Wording: "email address" used throughout; no upper-case domain literal in the test (`"example.com".upper()` built at run time).

## The test file: tests/test_email_case_rule.py (24 tests)
Header says exactly what happens on a code change (key tests fail; whoever makes them pass updates README, docs/limits.md, contract.md, docs/tests.md; the document test fails if a place loses the three letters or the phrase "different lead"). Messages on every assert. One constant `SPLIT_PAIRS` used by all parametrizations (no long lines).
* `test_split_pairs_differ` (3), `test_first_capital_splits` (2), `test_safe_letters_one_key` (5: é ü ö ç and ADA with a capital domain built at run time), `test_casefold_claim`, `test_other_forms_stay_apart` (IDN vs punycode, comment, bracket domain, 65 characters before the @ accepted, 254 whole accepted, 255 refused), `test_other_rare_letters`, `test_refused_letters`.
* Real desk: `test_desk_two_leads_two_mails` (3 pairs: ß ı ſ; two `new` answers, `rig.leads() == 2`, `SELECT count(*) FROM followups` == 2; the old `/counts == 200` check is only used to read a valid answer, not as the proof) and `test_desk_plain_capitals_one_lead` (control: new then duplicate, 1 lead, 1 follow-up).
* Document test derives the facts from `normalise_email` (the letters among ß ı ſ that split) and checks four places (README definition, README Not claimed bullet, docs/limits.md, contract.md): each names every such letter and matches the regular expression `different\s+lead`; `test_tests_page_lists_it` checks docs/tests.md.
* Test names pass exceptions.txt (words of at most 12 characters).

## Proof (raw logs in raw/)
Commands: `cd <tree>; TMPDIR=/home/user/work/priv/b4b-tmp PYTHONPATH=src /home/user/work/final-venv/bin/python -m pytest tests/test_email_case_rule.py -p no:cacheprovider --basetemp <under TMPDIR> -q`.
See the final report and the section "Results" below (filled after the last runs).
