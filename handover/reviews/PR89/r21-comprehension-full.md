<!-- full hand-back report of sub-agent a3cdc11d, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

# Naive-reader review: pull request 89, head 7a2eb4cc (round 21, mutation runner texts)

**Verdict:** the texts are much better than in round 19, and the re-copy steps can now be followed. I still found 4 Major and 16 Minor points. Two of the Majors are sentences that tell the reader to do the wrong thing: one "Do" line and one "What to do" line.

Nothing here was checked against code. Every statement is about what the texts say.

Files read, all under `/home/user/build/snap/p89-7a2eb4c/`:
- `CHANGELOG.md`: the added "Unreleased" bullets (patch lines 9-82) and the hash list (file lines 463-468)
- `tools/mutation_runner.py`: module docstring (lines 1-202) and `run_mutants` docstring (lines 1322-1346)
- `src/hadavin_sdk/testing/mutation.py`: module docstring (lines 1-21)
- `REVIEWS-r19/r19-comprehension-full.md`
- `/home/user/hadavin-sdk/.claude/rules/wording-clear-for-everyone.md`

## Paraphrase

**What this proposes.** `run_mutants` gets five new optional keywords. With `pass_env` the tests receive the address of a test database. While that address is present, the runner replaces text from the tests with fixed words and allowlisted names, repeats the unmutated tests after every mutant, and takes a lock. Two results change for every caller (fixture failures and "exit 1 with no failing test" become errors) and one row gets a new label.

**How the existing system works, per these texts.** The runner takes one snapshot of the source tree and runs the tests on the unmutated copy. It then makes one temp copy per mutant with one text replaced, runs pytest in a subprocess with a short fixed environment, and reads pytest's result file. `judge_report` turns that into a verdict, and each mutant becomes a row `(name, verdict, test id, good)`. Other repositories keep byte copies of four files and pin their sha256 values.

## (1) My three sentences, and where I guessed

1. The tool puts one deliberate bug at a time into a temp copy of a package, runs chosen tests, and counts the bug as caught only when a test body fails for the stated reason.
2. The four keywords:
   - `pass_env` hands the tests one allowed environment variable holding a test database address, which switches on the skip check, the repeat run and the output replacement.
   - `throwaway_hosts` is the exact list of host names or socket folders that address may name.
   - `forbid_skips` turns a run with a skipped or expected-failure test into an error row.
   - `shown_classes` lists my own exception class names that may still be shown.
3. To re-copy, I copy four files in one commit, set four sha256 pins, read `first_lines` with `.get`, and move fixture assertions into test bodies.

Places where I had to guess:
1. What a failing row and its `first_lines` entry look like with an address: order, separators, quoting. There is no example.
2. Whether one part of a test id that is not allowed replaces the whole id with `[test id not shown]` or only that part.
3. How a URL with a password is written. The only example URL has none; I assume `user:password@host`.
4. Whether `throwaway_hosts=(...)` replaces the three defaults or adds to them.
5. What makes an entry of `throwaway_hosts` "not exact", and whether `Localhost` matches `localhost`.
6. Which commit "moves its SDK pin to the same commit" means, and whether a package-installing repository keeps two hash pins or four.
7. Whether `pass_env` and the lock existed in a released version. The texts say "gains five keywords", but also "Not usable any more", "an older copy of this tool" and "the earlier rule ... is gone".
8. Whether a lock works on Windows at all.
9. Whether the runner prints anything, or only returns rows. The texts use "shown", "prints" and "returns or raises" for the same thing.
10. Who can read the temp folders that hold the real result files during the run.
11. What counts as one of the "300 texts", so I cannot predict that refusal.
12. Which characters besides `@ / ? #` must be percent-encoded in a password (`%`, `:`, space).
13. What a user does who needs both a password and `sslmode`. The URL shape allows "nothing after" the database name, and the word shape allows no password.
14. Whether `FIXTURE ERROR` is a verdict or a text in the test-id column, when reading the CHANGELOG alone.
15. What "guard", "demos", "reviewed baseline" and "the no-hardcoding rule" mean.

## (2) What is shown, what is not protected, one place, contradictions

**What is shown.** Both texts carry the same five-row table, and they agree on it: allowlisted exception class or `[class not shown]`; `[expect found]` or `[expect not found]` plus my `expect` text; allowlisted parts of a test id or `[test id not shown]`; `[parameters hidden]`; fixed words for how a run ended. Then a second pass replaces the address and password forms with `[REDACTED]`.

**Can a reader predict a failing row?** No. The table gives the pieces, not the assembled line. There is no example in either file. See Major 1 and Minor 1.

**What is not protected.** Stated in both: my own `expect` text and mutant names; a test that writes the address elsewhere; result files in temp folders after SIGKILL; `~/.pgpass` through `HOME`. Not stated anywhere:
- that every other file under `HOME` is also within reach of the tests;
- the access mode of the temp folders during the run;
- that `[expect found]` tells the caller whether a chosen text is in the hidden line.

**One place?** Two near-identical places (CHANGELOG bullet "what protects the address, and what is shown" and the docstring block under `pass_env`). They agree on the table. Contradicting pairs:

- A, inside the docstring (Major 2):
  - "no other database address, token or secret of the caller"
  - "``HOME`` IS inherited, so a ``~/.pgpass`` file of the caller is used"
- B, inside the docstring:
  - "can never be complete, so no such list is used"
  - "searched for the address, its password and the percent-encoded forms of the password"
- C, inside the CHANGELOG:
  - "Two of its results change and one row gets a new label"
  - "Before, some rows got an empty entry." (a third change for every caller)
- D, inside the CHANGELOG (Windows):
  - "The lock and the checks of the lock folder described below are not checked there"
  - "Windows: the lock file lies directly in the temp folder."
- E, docstring against CHANGELOG, small:
  - "the canary message" against "the two canary messages"
  - "texts to hide" against "texts to search for"
  - "the snapshot of that file" against "the caller's copy of that file"
  - refusals numbered 1-13 against 1-7

## Findings, most serious first

### Major

**Major 1. The "Do" for scripts makes a wrong-reason line look like a match.**
- File: `CHANGELOG.md`, step 3, last line under "Only with `pass_env`".
- Quote: "match on the caller's own `expect` text, which is kept"
- Why a reader goes wrong: the table says the `expect` text is printed after `[expect found]` and after `[expect not found]`. A script that looks for the `expect` text finds it in both cases, so it reads a mutant that died for the wrong reason as correct.
- Replacement: "Do: if a script reads `first_lines`, test for the fixed words `[expect found]`. Your `expect` text is printed in both cases, so its presence proves nothing. Example entry: `<paste one real entry here>`."

**Major 2. The opening paragraph says the tests see no other secret of the caller.**
- File: `tools/mutation_runner.py`, lines 6-7.
- Quote: "no other database address, token or secret of the caller"
- Why a reader goes wrong: the limit is on environment variables only. Line 119 says `HOME` is inherited and `~/.pgpass` is used. With `HOME`, the tests can read every file of the user (`~/.aws`, `~/.netrc`, SSH keys). A reader runs mutants on a laptop believing the tests are fenced off.
- Replacement: "The tests get a fixed short list of environment variables plus the passed variable. The runner does not fence off files. `HOME` is inherited, so the tests can read any file of the user, `~/.pgpass` and cloud credential files included. Run it under an account that holds no real credentials."
- Use the same sentence in the CHANGELOG bullet "what protects the address", which names only `~/.pgpass`.

**Major 3. The line a refused developer reads tells them to list the host, without the condition.**
- Files: `CHANGELOG.md` refusal 6; `tools/mutation_runner.py` refusal 11.
- Quote: "Do: pass `throwaway_hosts=("the-exact-name",)`."
- Why a reader goes wrong: a developer with a "host not listed" error reads this item and no further. The warning is one bullet (CHANGELOG) or one paragraph (docstring) later. The keyword name also suggests the runner knows the host is throwaway.
- Replacement: "Do: first make sure the database on that host is disposable and that its login can touch nothing else. The runner cannot check this. Only then pass `throwaway_hosts=("the-exact-name",)`. This list replaces the default list, so also write `localhost` if you still need it." (Confirm the last sentence; I guessed it.)
- Related over-read: "The host list is the only check of where the tests write". The list checks which host the address names, not where the tests connect. Replacement: "The host list is the only check, and it checks only the host written in the address. The tests are code and can connect elsewhere."

**Major 4. Windows: advice without evidence, and the lock sentence can be read two ways.** Borderline Major.
- File: `CHANGELOG.md`, step 4.
- Quotes: "What to do on Windows: use the runner as it is." and "are not checked there"
- Why a reader goes wrong:
  - "Not run" is said plainly for the SDK's own mutant list only ("Nobody has run the mutant list of this tool ... on Windows"). It is not said for the runner, the hiding or the lock.
  - "Use the runner as it is" then reads as approval.
  - "The lock ... are not checked" can mean "we did not test it" or "there is no lock". The lock bullet says a lock file exists there.
  - The module docstring has no Windows statement at all, and describes Windows behaviour as fact.
- Replacement: "Windows: we have not run the runner with `pass_env` on Windows, and CI runs Linux only. We have not run its own 248 mutants there either; from the skip markers, 26 would not be killed. On Windows the runner takes a lock file in the temp folder but checks nothing about that folder or file. We do not know that it keeps two runners apart. Give each run its own database, and treat a green list on Windows as unproven." Add one such sentence to the module docstring.

### Minor

**Minor 1. No example of the output.** Both files. Add, under the table, one real example each of: a killed row with its `first_lines` entry, a wrong-reason entry, an id with hidden parameters, and a fully hidden id. Say whether one disallowed part hides the whole id.

**Minor 2. No password URL example, and the encoding rule is incomplete.**
- Quote (CHANGELOG): "write the password in the login part of the URL".
- Add: "Example: `postgresql://app:p%40ss@localhost:5432/testdb`."
- Say whether `%`, `:` and a space must be encoded.
- Say what to do when both a password and `sslmode` are needed.

**Minor 3. Refusals without a next step.**
- CHANGELOG refusal 2 (quote mark, backslash, non-ASCII): add "Do: change the test database password to plain ASCII letters and digits."
- CHANGELOG refusal 5 (no host): add "Do: write the host." The docstring has it.
- Refusal 3: "use a plainer password" is vague. Say "do not percent-encode the password more than once".
- Docstring refusal 3: "an entry of `throwaway_hosts` that is not exact" is undefined. Say what is refused (a pattern, a wildcard, upper case, a trailing dot).

**Minor 4. Label and verdict are mixed in the CHANGELOG.**
- Quotes: "is now the row `FIXTURE ERROR`" and "is now `ERROR`. Before it was `CRASH` or `KILLED`."
- The first is a text in the test-id column of an `ERROR` row; the second is a verdict. The CHANGELOG never gives the row shape.
- Add once: "A row is `(name, verdict, test id, good)`. `FIXTURE ERROR`, `SKIPPED TESTS` and the like are texts in the test-id column of a row whose verdict is `ERROR`."
- The docstring still says "an ERROR row with no verdict from the judge", though the row's verdict is ERROR. Replacement: "an ERROR row that the runner made without asking the judge".

**Minor 5. Review history left in user-facing text.** A reader of a release cannot tell what was ever released.
- "Changed in this round"
- "28 added and 4 removed in this round"
- "Not usable any more, by decision"
- "the earlier rule ... is gone"
- "No test switches the address check off any more"
- "It does NOT see an older copy of this tool"
- "(before, every socket address shared one name)"
- "three older gaps"

Replacement: say in the headline which parts of `pass_env` and the lock existed in the last released copy. Delete the rest, or move it to the pull request description.

**Minor 6. Internal codes and names.**
- "P1m": the reader is sent to the section "Added (P1m, test tooling ...)".
- "Evidence for (3)": "(3)" is also "step 3" of the same entry.
- "The no-hardcoding rule" and `defaults.py`, in the docstring's last paragraph.
- "demos" ("a tool that demos copy byte for byte").
- Private helper names `_locate`, `_inside`, `_plain_operand` in prose.
- `denied:internal_error`, "an executor's", in `mutation.py`.

**Minor 7. Terms used before or without explanation.**
- "guard": first line of both docstrings ("revert one guard"). The CHANGELOG's "one deliberate bug" is the plain form; use it.
- "mutant" and "mutant list": the CHANGELOG never ties them to "deliberate bug".
- "judge": CHANGELOG step 4, before the background bullet.
- `expect`, `crash_type`, `allow_crash`, `only_test`: used in the CHANGELOG with no explanation. `pinned` is explained only after its first use in the table.
- "canary run": docstring line 63, explained at line 71.
- "``E `` line", "``-rf`` text", "reviewed baseline", `crash_markers`: in `mutation.py`.
- "another waiter": in the docstring. The CHANGELOG explains it well.

**Minor 8. Words with two meanings.**
- "address":
  - defined as the whole value of the variable;
  - but "one runner per address" means only host, `hostaddr`, port and database name;
  - also `hostaddr`.
- "value":
  - the variable's value: "A value longer than 2,000 characters" (should be "an address");
  - a `key=value` word;
  - "sha256 values";
  - "the two plain values" (`mutation.py`).
- "row": see Minor 4. Also "nine kinds of result row".
- "canary": "canary run", "the canary message", "the two canary messages".
- "baseline":
  - the first unmutated run (docstring; the CHANGELOG says "first run");
  - "a reviewed baseline" in `mutation.py`.
- "listed":
  - a name listed in `pass_env`;
  - a host listed in `throwaway_hosts`;
  - "found by LISTING the tree";
  - "the listed test files".
- "class":
  - exception class;
  - a test class inside a test id;
  - "<error class>".

  A reader may think `shown_classes` also allows test class names. Say "exception class" every time.
- "pin":
  - sha256 pins;
  - "SDK pin" (a dependency version);
  - `pinned` (the killer test).
- "checked": the runner checks, against "not checked there" (we did not test).
- "snapshot": the file tree, and "that one snapshot" of the environment.
- "kill": a mutant kill, a "tree kill", and "a kill that cannot be caught".
- "replacement text": defined, but then `[expect found]` is called "fixed words".
- "set": "unless set to off" in the table that was built to remove "set".

**Minor 9. Sentences over about 40 words** (approximate counts).
- Docstring lines 20-26: "the tool imports only ... whole process tree of the run", about 190. Flagged in round 19, unchanged. Make it a list of five refusals.
- Docstring lines 37-39, about 70. Lines 39-42, about 65. Lines 42-44, about 50.
- Docstring `conftest` bullet, about 75.
- Docstring table cell "a test id", about 60.
- Docstring lines 190-194, "For an ERROR row ...", about 75.
- `run_mutants` docstring, "``RuntimeError``: the unmutated copy fails ...", about 85. Flagged in round 19, unchanged.
- `mutation.py`: "Verdicts: ..." about 110; "Harness contract ..." about 50; "Only an AssertionError ..." about 45.
- CHANGELOG table cell "a test id", about 60.
- CHANGELOG tests bullet: "In each it takes 13 outputs ...", about 50.
- CHANGELOG mutant-list bullet, about 60.
- CHANGELOG "(1) A run whose FIRST failing test case ...", about 45.

**Minor 10. "Three opt-in keywords ... (all off by default)"** (docstring line 56), against "Default: on when a name is LISTED in `pass_env`". Flagged in round 19. Replacement: "Five optional keywords. `forbid_skips` switches itself on when you list a name in `pass_env`."

**Minor 11. Contradiction B.** Replacement for the docstring: "so the allowlist does not depend on such a list. A second pass still searches for the known forms of the address."

**Minor 12. Contradiction C.** Replacement for the headline: "For every caller, two results change, one row gets a new label, and `first_lines` no longer holds empty entries (step 3)."

**Minor 13. The red list misses two cases.**
- Under `forbid_skips`, a run with no result file is now `JUNIT MISSING`.
- A second job on the same address in the same lock folder is refused.

Add both to step 3 with a "Do". At "pass `forbid_skips=False` when the skip is intended", add: "With it off, a mutant can count as killed because the tests could not run."

**Minor 14. "moves its SDK pin to the same commit".** Replacement: "and sets the SDK version it installs to the commit it copied the two `tools` files from. It keeps two sha256 pins, for the two `tools` files."

**Minor 15. "never put a secret in `expect`".** The reason is given ("a piece of a password written there is shown"). The temp-folder point lacks one: say who can read the temp folders while the run lasts, or say "we do not set or check their access mode". Also say that the lock file name holds no password; the docstring says it, the CHANGELOG does not.

**Minor 16. An older bullet above the hash list.** CHANGELOG line 459, not added by this pull request, says "re-copy it in every repository" for one file. A reader sent to that section by step 1 sees it right above "re-copies the four of them".

## (4) Safety statements a careless reader over-reads

- `throwaway_hosts` as proof of a disposable database: the texts now deny this plainly in three places. The remaining hole is the "Do" line (Major 3).
- "never shown" as "cannot leak": mostly bounded by "Not covered". Remaining: Major 2 (files under `HOME`) and Minor 15 (temp folders).
- "never put a secret in `expect`": the reason is given.
- "The host list is the only check of where the tests write": over-read, see Major 3.

## (5) Refused addresses

| Refusal | Reason given | Next step given |
|---|---|---|
| Password key in `key=value` form | yes, docstring only ("can change where the connection goes or name a file") | yes, both files |
| URL password with plain `@ / ? #` | no; only "by decision (when in doubt the runner refuses)" | yes, but no example (Minor 2) |
| No host | yes | docstring only |
| Unlisted host or socket folder | yes | yes, without the condition (Major 3) |
| Odd characters | docstring only ("a character that a print would change") | no |
| More than 300 texts | partly | vague |

## (6) Upgrade path

- Files: complete and consistent. Four files in the docstring, in step 1 and in the hash list. The package-install case is covered.
- Hashes: four values listed, also said to be in `tests/fixtures/mutation_manifest.json`. I did not check them against the files.
- Red list: good, with a "Do" per item. Gaps in Minor 13; one wrong "Do" in Major 1.
- Windows: Major 4.

## (7) Round-19 Majors

| Round-19 Major | Status | Quote from this round |
|---|---|---|
| M1 files to copy | fixed | "re-copies FOUR files in one commit" |
| M2 `first_lines` and `crash_type` | fixed | "the entry is NOT the child's line" |
| M3 "a token never reaches the child" | fixed in that bullet; a related claim remains (Major 2) | "receive the full address, a password in it included" |
| M4 "set" | fixed | "listed, variable present but empty: the call is refused before any run" |
| M5 "discarded" | fixed | "goes to the null device. The runner never reads or prints it." |
| M6 safety paragraph | partly (Major 3) | "It cannot check that the database is disposable." |
| M7 lock over-stated | fixed | "Its reach is small." |
| M8 red list | fixed, small gaps | "What can turn a passing mutant list red after the re-copy, and what to do." |
| M9 Windows | partly (Major 4) | "these are the SDK's own mutants, not yours" |

Round-19 Minors not fixed: "guard"; "demos"; the 190-word docstring sentence; the `RuntimeError` sentence; "all off by default"; "ERROR row with no verdict from the judge"; two meanings of "baseline", "pin", "snapshot" and "kill". The "ladder" and "rung" codes are gone.

## What I did not read

- Any code body, test, `tests/fixtures/mutation_manifest.json`, `ci.yml`, or any patch hunk other than the CHANGELOG one. I cannot say which side of any contradiction is true.
- CHANGELOG entries not added by this pull request, except lines 452-468 around the hash list.
- The pull request description and any README.
- Read in passing and not reviewed: lines 204-320 of `tools/mutation_runner.py` (imports, the `Mutant` dataclass with its field comments, three small helpers, constants) and the first lines of the `mutation.py` hunk in the patch. My read ranges covered them. I did not use them as evidence.
- No standard other than the persona file and the house rule was supplied.
