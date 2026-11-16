<!-- full hand-back report of sub-agent a9588739, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

# Naive-reader review: pull request 89, head b95b0ca7 (mutation runner texts)

**Verdict:** a careful reader can use the tool, but cannot re-copy it safely from these texts alone. There are 9 Major and 9 Minor findings. The worst are: the three texts disagree on which files to copy, on what `first_lines` holds, and on whether child text is shown.

Files read (all under `/home/user/build/snap/p89-b95b0ca/`):
- `CHANGELOG.md`: the 28 added "Unreleased" bullets (lines 9-36) and the hash list (lines 414-422)
- `tools/mutation_runner.py`: module docstring (lines 1-136) and `run_mutants` signature and docstring (lines 1107-1134)
- `src/hadavin_sdk/testing/mutation.py`: module docstring (lines 1-21)
- `DIFF-vs-main.patch`: the CHANGELOG hunk only
- House rule: `/home/user/hadavin-sdk/.claude/rules/wording-clear-for-everyone.md`

## (1) My three sentences, and where I guessed

**What this proposes.** The tool makes many copies of a package, puts one deliberate bug in each copy, runs chosen tests on each, and reports whether a test failed for the stated reason. `pass_env` hands one allowlisted environment variable (a test database address) to the tests and replaces their output with a short fixed-shape text; `throwaway_hosts` is the exact list of host names that address may use; `forbid_skips` turns any run with a skipped test into a "proves nothing" row. To re-copy, I copy `tools/mutation_runner.py` and `src/hadavin_sdk/testing/mutation.py` (perhaps four files), update my sha256 pins, and expect some former kills to become error rows.

**How the existing system works, per these texts.** The runner takes one snapshot of the source tree, runs the tests once on the unchanged copy, then once per mutant, each in a subprocess with a small fixed environment. A function called `judge` turns exit code, failing test id and first error line into a verdict. Other repositories keep byte copies of the files and pin their hashes.

**Places where I had to guess:**
1. How many files to copy: two, "both", or four (finding M1).
2. Where a copy of `src/hadavin_sdk/testing/mutation.py` goes in a repository that installs the SDK as a dependency rather than copying it.
3. What "set" means: the name listed in `pass_env`, the variable present in the environment, or the value non-empty (finding M4).
4. Whether `forbid_skips` existed before; "The default is now" suggests yes, "three opt-in keywords" suggests new.
5. Whether `throwaway_hosts` is opt-in; the headline separates it from the "opt-in" three and no text says why.
6. Whether host and port are required in the URL form, or only the login is optional.
7. Whether the "FULL unmutated test list" of the canary run is my `tests` argument or the whole suite.
8. Whether the test in `Mutant.pinned` is compared with the raw test id or the shown one (`[parameters hidden]`).
9. Whether "console output is discarded" means it never reaches my terminal or CI log (finding M5).
10. Whether the lock exists at all on Windows; the glossary defines the lock as `flock`, which is POSIX.
11. Whether the "about 16 mutants survive on Windows" are the SDK's own mutants or mine.
12. What triggers "more than 300 texts to hide" and what I do then.
13. What `crash_type`, `allow_crash`, `CHILD_ENV`, "reaped" and "judged row" mean.
14. Whether the per-mutant temp folders (which hold the raw JUnit file) can stay on disk with the secret after a SIGKILL.

## (2) Hidden, shown, not protected: is it in one place without contradiction?

No. It is in three places: the docstring table, the CHANGELOG bullets "what is shown" and "cost and what is not covered", and the `run_mutants` docstring. They disagree.

**Contradiction A (what `first_lines` holds, and what `crash_type` reads):**
- `run_mutants` docstring: "filled with the first ``E`` line of each judged row that has one, masked (... what ``crash_type`` is checked against)"
- Module docstring: "The raw line stays inside the runner: ``judge`` and the ``crash_type`` check read it."

The first says the caller gets the real line with the secret masked, and that `crash_type` reads that text. The second says the caller gets no line at all, and that `crash_type` reads the raw one.

**Contradiction B (is child text shown?):**
- Both files: "The child's text is not shown at all while a passed value is set"
- Docstring table, "shown" row: "the leading exception class name ... the file path and function name of a test id"

The class name and the test id come from the child. The row heading "shown, fixed or from the caller" is also wrong for them.

**Contradiction C (always-on changes):**
- CHANGELOG headline: "three results change for every caller"
- Docstring: "two changes of result and one new label"

The CHANGELOG then lists more: the `EXIT CODE <n>` label and `first_lines` entries that are no longer empty.

**Contradiction D (when the lock refuses):**
- CHANGELOG: "Steps, in order; each is an error, never a run" (the lock is step 5)
- Docstring: "BEFORE any test runs, except step 5"

Not stated in any of the three places:
- which process output is discarded and where it goes;
- whether the whole address or only the password is "the secret";
- the fate of the raw JUnit files in the temp folders;
- that the tests themselves and every process they start hold the full address.

## Findings, most serious first

### Major

**M1. Which files to re-copy: three different answers.**
- `tools/mutation_runner.py` docstring: "copies ``tools/__init__.py`` and ``tools/mutation_runner.py`` byte for byte"
- CHANGELOG re-copy bullet: "A repository that keeps a copy re-copies both files" (the runner and `mutation.py`)
- CHANGELOG line 417: "re-copies the four of them in one commit"

A reader who follows the docstring copies the runner only and gets an import failure. The CHANGELOG mentions that failure only in passing.

Replacement, in both files: "Copy these four files, byte for byte, in one commit: `tools/__init__.py`, `tools/mutation_runner.py`, `src/hadavin_sdk/testing/__init__.py`, `src/hadavin_sdk/testing/mutation.py`. Then set your four sha256 pins to the values listed at the end of this section. The new runner does not start with the old `mutation.py`." Also say what a repository does when it installs the SDK instead of copying `mutation.py`.

**M2. `first_lines` and `crash_type` (Contradiction A).** A caller who writes checks against `first_lines` text will see them break when a database address is passed, or will believe the real line is still shown.

Replacement in the `run_mutants` docstring: "`first_lines` receives, per mutant name, the first error line. While a passed variable is set it receives only the short replacement text described in the module docstring, not the line. The runner checks `crash_type` against the real line, which it never returns."

**M3. "so a token never reaches the child" (CHANGELOG, `pass_env` bullet).** The runner checks the variable's name, not what the value holds. A database address normally contains a password, and it does reach the child. A reader concludes that no credential can reach the tests.

Replacement: "The runner refuses any variable name that is not on the list. It does not check what the value contains. The tests, and every process they start, receive the full address, password included."

**M4. "set" has three meanings.**
- "Setting a passed name also switches on ``forbid_skips``"
- "a name that is not set is simply not passed"
- "runs whenever a passed name is set, also when its value is empty text"
- "while a passed value is set"

I cannot tell whether listing the name in `pass_env` on a machine without the variable switches on the skip check, the canary run and the hiding. That decides whether my run goes red or silently proves nothing.

Replacement: one small table with three rows (name listed but variable absent; variable present but empty; variable present with a value) and three columns (skip check on? canary run? output replaced?).

**M5. "discarded" is listed under "not covered".** Both files: "the child's own console output is discarded and never read". Under "not covered" a reader takes this as a hole (the secret can appear on my console). If it is thrown away, it is a protection.

Replacement, moved to the "hidden" row: "The runner throws away everything the tests print to the screen. It does not reach your terminal or your CI log." Use that only if it is true; I did not read the code.

**M6. The safety paragraph reads as if the runner checks that the database is disposable.** Docstring: "SAFETY: the address must point at a THROWAWAY database ... The runner checks in code: after EVERY mutant run". "Checks in code" directly after the requirement reads as a check of the requirement.

The keyword name `throwaway_hosts` adds to this, and the `run_mutants` docstring never mentions that keyword. The text "lists that exact name" invites adding any host with no warning at that spot.

Replacement: "`throwaway_hosts`: the host names the runner accepts in the address. The runner cannot check that a database is disposable. You must make sure of it. If you add a host name here, you remove the only host check. What the runner does check: after every mutant it runs the unchanged tests again and stops if they fail."

**M7. The lock is over-stated.**
- CHANGELOG title: "the lock that keeps two runners apart"
- Step 5: "A second runner on the same address is refused"
- "the canary run still catches a collision afterwards"

The third quote contradicts "The canary proves only that the full unmutated tests pass, not that the database is clean". The lock misses a second spelling, a second user, a second temp folder and a second machine. The CHANGELOG leaves out the last two; only the docstring has "A runner with another temp folder or on another machine is not seen". A reader shares one database between two CI jobs.

Replacement title: "A lock that stops a second runner of the same user, on the same machine, with the same spelling of the address". Then: "It does not stop any other second runner. The repeat run notices a collision only when the collision makes the unchanged tests fail. Give every run its own database."

**M8. The red-list changes are scattered, and no action is given.**
- The warning sits at the end of a bullet of about 200 words: "Existing mutants whose kill came from a fixture assertion turn into error rows".
- It does not say what to do. Suggested: move the assertion into the test body, or accept the row as "proves nothing".
- It does not say that a mutant with `allow_crash` whose crash came from a fixture also turns red.
- `forbid_skips` also counts "(or an expected failure)" as a skip.
- `first_lines` now has no entry for some rows, so `first_lines[name]` can raise `KeyError`.
- `CanaryFailed` now stops the whole run, and a run with `pass_env` takes about twice as long.

Replacement: one bullet "What can turn a passing mutant list red after the re-copy", with one line per change and the action for each. Split it into "for every caller" and "only when you pass `pass_env`".

**M9. Windows: no instruction, and one over-claim.**
- "About 16 mutants survive on Windows because their killers skip there": I cannot tell whether these are the SDK's mutants or mine, or what to do.
- "On Windows the temp folder is private to the account" is stated as fact. A machine can point its temp folder at a shared one.
- Whether a lock exists on Windows is not said.

Replacement: "On Windows we have not run this. The 16 are mutants of the SDK's own list (`tests/mutation_runner_mutants.py`); your own list is not affected. On Windows the runner does not check who owns the lock file. If your temp folder is shared, another account can block a run." Add one sentence on whether two runners are kept apart on Windows.

### Minor

**m1. Words with two or more meanings.**
- "address": the whole value of the variable (password included); the `hostaddr` part ("host address"); and the four parts the lock compares ("same address").
- "secret" / "value" / "address" / "hidden text" / "texts to hide": five words for one thing. "Value" also means a `key=value` word and a sha256 hash ("the new values replace the old ones").
- "hidden": the glossary's "hidden text" is the secret forms; the table's "hidden (never shown)" is the child's text.
- "name": variable name, host name, mutant name, lock file name ("gets two names"), a hard-link count ("one name"), and a verb ("naming the mutant").
- "baseline": the first unmutated run (CHANGELOG), and "a reviewed baseline" in `mutation.py` (a stored list of pinned tests).
- "pin": the test tied to a mutant (`Mutant.pinned`, "pinned killer"), and the sha256 values ("updates its pins").
- "snapshot": the copied file tree, and the environment read once.
- "kill" and "tree": a mutant killed versus "tree kill" of processes; file tree versus process tree.
- "copy": the temp copy per mutant, the byte copy in another repository, and "a base64 or hex copy".
- "canary": "canary run", "the canary message", "a failed canary", and "the canary decision" (never explained).
- "row": "ERROR row", "error row" and "the row" in mixed spelling. An "ERROR row that has no verdict from the judge" still carries the verdict ERROR.
- "projection": defined in the CHANGELOG glossary, but the definition says "instead of the child's text" while it includes the child's class name. The docstring uses it with only the table as its definition.

**m2. Terms used before or without explanation.**
- "guard" (first line of both docstrings: "revert one guard at a time")
- "DSN" (docstring line 3; the CHANGELOG says "database address")
- "the pytest child" / "the child"
- "the older masker" (used inside the glossary before it is described)
- `crash_type`, `allow_crash`, `expect` (explained only in `mutation.py`), `CHILD_ENV`
- "reaped", "judged row", "selected test", "E line" (the glossary says "first error line")
- "fail closed", "loopback name", "unix socket folder", "the wheel", "demos"
- The glossary defines `TMPDIR`, "hard link" and "hidden text", but the text after it does not use them. It says "temp folder" and "one name".

**m3. Internal codes in user-facing text.**
- "ladder (CODE-LAST rung table)", "Rung 1", "Rung 3" (CHANGELOG and docstring). The house rule names "rung 3" as a term not to use. No rung 2 is given.
- "Over-breadth note"
- "Evidence for item (3) above"
- The constant names `CLASS_HIDDEN`, `ID_HIDDEN`, `PARAMETERS_HIDDEN` and `PROJECTION_MIN` in the docstring table, where the CHANGELOG gives the shown texts (`[class not shown]`).

Replacement for the ladder: "Why we wrote code: ready-made mutation tools cannot say why a mutant died."

**m4. Three bullets under "Upgrade steps" are not upgrade steps.** They are "tests of the hiding and the address check", "Evidence for item (3)" and "ladder", plus the "Choice made:" design note in the lock bullet. They bury the steps. Move them to a "Background" entry.

**m5. Sentences over about 40 words** (approximate counts).
- Docstring lines 3-6, about 90 words. Its subject gets lost: "the pytest child sees only ... , replaces every occurrence" reads as if the child replaces the text.
- Docstring lines 16-21, about 170 words in one sentence.
- `run_mutants` docstring, "Raises ``RuntimeError`` when: ...", about 130 words.
- Docstring lock sentence "It lives in a folder of the user (POSIX: ...", about 75.
- Docstring always-on item (3), about 60.
- CHANGELOG glossary, the `first_lines` sentence, about 70.
- CHANGELOG step 3, "The address CI passes, ...", about 55.
- CHANGELOG "what is shown", "In every place where child text becomes output ...", about 60 before the list.
- CHANGELOG tests bullet: "A seeded fuzz test ..." about 50; "Runs of a real pytest ..." about 70.
- CHANGELOG shared database: "All mutants and the baseline share it, so after EVERY ...", about 75.
- CHANGELOG lock: "On POSIX the file is in a folder ...", about 75; "Choice made: ...", about 50.
- CHANGELOG always-on item (2), about 45.
- The glossary itself is one paragraph of about 450 words. Make it a list.

**m6. Headline.** "three opt-in keywords (`conftest`, `pass_env`, `forbid_skips`) and one new keyword (`throwaway_hosts`)" reads as if the three are not new and the fourth is not optional. The docstring says "all off by default", while `forbid_skips` defaults to "on when a `pass_env` name is set". "its text is not shown" is ambiguous between the address's text and the tests' text.

Replacement: "Four new optional keywords. `forbid_skips` switches itself on when you use `pass_env`."

**m7. "shares no piece of 4 characters with a secret".** This reads as a guarantee. The evidence is a seeded random test; pieces of 3 characters and passwords under 4 characters are outside it.

Replacement: "We test with random values that no run of 4 or more characters of the address appears. Shorter pieces are not checked."

**m8. Address rules without the action.**
- A password with a quote mark, a backslash or a non-ASCII character is refused. Say "change the test database password".
- "(optional login, host, port, ONE database name ...)" does not say which parts are required.
- "A value that gives more than 300 texts to hide is refused" gives the reader no way to predict or fix it.

**m9. Table duplicates.** "mutant names" and "the caller's own ``expect`` text" appear in both the "shown" row and the "not covered" row. The row "refused (before any run)" is not about hiding. Keep each item in one row.

## What I did not read

- Any code body in `tools/mutation_runner.py` or `mutation.py`, or any helper docstring. I therefore could not confirm which side of any contradiction is true, nor whether console output is really discarded.
- The tests, `tests/fixtures/mutation_manifest.json`, `ci.yml`, and all patch hunks other than the CHANGELOG one. I did not check the hashes against the files.
- CHANGELOG entries not added by this pull request, except lines 405-422 around the hash list. I did not review the older entries there.
- The pull request description and any README.
- The bundled standards of the plugin, beyond the persona file. No other standard was supplied.
