# Lane 3 fix 4, round 3 (B4c): email capitals rule, documents + pinning test (no product code changed)
Base f3c39cf89ec989f032ea48a23cfd824b88da9c68; started from lane3-fix-4-r2.patch (improved, not restarted). Worktrees: /home/user/work/b4c-base (plain, `git add -A`, nothing committed), /home/user/work/b4c-stack (stack variant). Python 3.12.3 (final-venv). Made-up data only.

## Failed first / not checked (read this first)
* The first version of my /counts check (B8) was a muddled expression; I rewrote it before any run: `_desk_run` now returns `new` from /counts and the tests assert it (2 for the three pairs, 1 for the control).
* Added lines over 120 characters: 0 in the test file. 7 added lines over 120 in README.md, contract.md, docs/limits.md, docs/tests.md; these files already hold long single-line paragraphs (the existing lines are longer), so the lines were not split. Not a rule I could find for Markdown; not checked against CI.
* NOT checked: the fix-4 / fix-8 apply order in both directions: there is no lane3-fix-8 patch in evidence/ yet. My text does not mention `loc@.dom` or `loc@a..b` (grep of the patch: 0 hits). gitleaks (program absent: 4 hygiene skips). ruff, mypy, bandit (CI only by brief).
* NOT done (not mine): the `# noqa: S603` comment at tests/support.py:112 (lead note E6) belongs to fix-5/Target A.
* The documents still say nothing about Windows or other Python versions: all behaviour is Python 3.12.3 here.

## Items
| Item | Fixed how | Verified how |
|---|---|---|
| B1 anchors | Each place has an anchor that holds on exactly one line: README definition "means the same email address", README Not claimed "the same address in capitals", limits "Email addresses written in capitals", contract "not `casefold()`". `_line` fails unless exactly one line matches (also 0). Old hole (line 28 loses all letters while line 106 keeps them) now fails. | raw/b4c-mutation-summary.txt: for each of the 4 places, removing ſ from the anchored line (1 failed) and removing the phrase "different lead" (1 failed); the same README anchor on two lines fails (1 failed). Each failure names the right test (raw/b4c-readme_def-letter.log etc.). |
| B2 two emails | Path taken: bounded poll (10 s) until the number of follow-ups in state `sent` is reached, then count `rig.outbox.count`. In-process desk did send within the time, so the documents keep "two follow-up emails (in this demo, two entries in the stand-in mail system)". Tests assert outbox 2 (three pairs) and 1 (control). | raw/b4c-pass-patched.log (25 passed). Not measured: how long the sends take (the whole file ran in 2.4 s). |
| B3 remedy | README :28 and limits: switch off "Hide names and email addresses" in the portal, look in the Leads list for two entries that are the same address written two ways, `straße@…` and `STRASSE@…`, `ıstanbul@…` and `ISTANBUL@…`, `ſam@…` and `SAM@…`; "The desk does not merge them." | Text only; the switch name is the one in README :108. |
| B4 | "not for some rare letters. Three examples, each of these pairs is a different lead"; further examples µ ŉ ǰ named in README and limits ("Some other rare letters"). | test_other_rare_letters (µ ŉ ǰ split). |
| B5 | "a Greek final sigma ς followed by a full stop and another letter, such as οδος.x@example.com and ΟΔΟΣ.X@example.com". | test_other_rare_letters uses exactly that pair. |
| B6 | New test `test_limits_sentences_are_there` pins the other-forms sentence (xn--, brackets, 64, 254) and the Kelvin/U+0130 sentence (U+212A, U+0130, refused, review list), each by its own unique anchor. | Mutation: xn-- changed (1 failed); U+0130 changed (1 failed). |
| B7 jargon | casefold: "A stricter way of ignoring capitals (Python's `casefold()`) would join the ß and ſ pairs but not the ı pair; the desk does not use it." Kelvin/U+0130: "refused and put on the review list" in README/limits. contract.md keeps its existing technical wording (verdict `review`). | Text only. |
| B8 | /counts `new` asserted. | Tests pass; casefold copy fails the two-lead tests. |
| B9 | "trimmed of blank characters (spaces, tabs and other white space)". | Text only (strip() behaviour from the review). |

## Evidence (raw in evidence/raw/, all exit codes inside the logs)
* New file on BASE documents (f3c39cf plus only the test file): 7 failed, 18 passed [exit 1] (b4c-base-docs.log): the four places, the two new limits anchors, docs/tests.md row.
* `normalise_email` changed to casefold in a copy: 10 failed, 15 passed [exit 1] (b4c-casefold.log).
* 8 per-place mutations + 2 anchor mutations + duplicate anchor: each 1 failed [exit 1] (b4c-mutation-summary.txt).
* Patched tree: 25 passed [exit 0] (b4c-pass-patched.log).
* Hygiene + new file + test_portal_wording_and_masking: 66 passed, 7 skipped [exit 0] (b4c-hygiene.log).
* Comment checks: 0 added `noqa`, 0 `type: ignore`.
* `git apply --check` (plain on base, for-stack on the stack tree): both rc 0 (b4c-apply-check.txt).
