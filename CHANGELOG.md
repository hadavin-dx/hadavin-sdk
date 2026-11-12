# Changelog

## Unreleased

### Upgrade steps
- **Mutation runner: what to do when you take this version.** The mutation runner (`tools/mutation_runner.py`) is the developer tool that puts one deliberate bug at a time (a *mutant*: one text of one source file replaced by another) into a copy of the code and checks that a test fails for the stated reason (the mutant is then *killed*). A *mutant list* is the list of such bugs a repository runs. The *judge* is the function `judge_report` that decides from pytest's result file whether a test failed for the stated reason. A result row is `(name, verdict, test id, good)`. Its `verdict` is one of `KILLED`, `WRONG_REASON`, `CRASH`, `ERROR` and so on; `FIXTURE ERROR`, `SKIPPED TESTS` and similar words are texts in the test-id column of a row whose verdict is `ERROR`. The function `run_mutants` gains five keywords: `conftest`, `pass_env`, `forbid_skips`, `throwaway_hosts` and `shown_classes`. A call that gives none of them takes the same arguments as before. For every caller, two results change, one row gets a new label and `first_lines` no longer holds empty entries (step 3). The keywords, the address checks, the lock and the hiding of text described below are all new in this version.
  1. **Which files to re-copy.** A repository that keeps its own copy re-copies FOUR files in one commit: `tools/__init__.py`, `tools/mutation_runner.py`, `src/hadavin_sdk/testing/__init__.py` and `src/hadavin_sdk/testing/mutation.py`. It then updates its sha256 pins (the stored fingerprints of the copied files) to the values in the list at the end of the section "Added (P1m, test tooling: the mutation runner and judge)" below. The same values are in `tests/fixtures/mutation_manifest.json`. A repository that installs the SDK as a package already has the two `testing` files. It re-copies the two `tools` files, sets the SDK version it installs to the commit it copied them from, and keeps two sha256 pins, for the two `tools` files. The new runner does not start with an older `mutation.py`: it needs the new function `judge_report`.
  2. **Run your mutant list once.** Expect about twice the run time when you use `pass_env` with a database address that is present (one extra test run per mutant).
  3. **What can turn a passing mutant list red after the re-copy, and what to do.**
     - Every caller:
       - A mutant that was "killed" by an assertion inside a fixture (setup or teardown) is now a row with the test-id text `FIXTURE ERROR` and the verdict `ERROR`. It is not a kill, because the test never ran as written. Do: move the assertion into the test body, or name a test that fails in its body.
       - A mutant with `allow_crash=True` (the caller says that a crash is the intended reaction) whose crash came from a fixture is now `FIXTURE ERROR` too. Do: the same.
       - A run that failed (exit code 1) while the result file named no failing test now has the verdict `ERROR`. Before it was `CRASH` or `KILLED`. Do: find out why the result file is empty (a crash of pytest itself is the usual cause).
       - `first_lines` (the dictionary a caller may pass to get the first failure line per mutant) has an entry only for a row that has such a line. Before, some rows got an empty entry. Do: read it with `first_lines.get(name, "")`.
       - New label only: a test file that cannot be imported is the row `COLLECTION ERROR`. It was an `ERROR` row before, with the module name in the test-id column. Do: nothing, unless your script matches on that column.
     - Only with `pass_env`:
       - A test that is skipped, or marked as an expected failure, is the row `SKIPPED TESTS`, and a first run that skips stops the call. This is on as soon as a name is listed in `pass_env`. Do: make the tests run (start the database), or pass `forbid_skips=False` when the skip is intended. With it off, a mutant can count as killed because the tests could not run.
       - A mutant run that leaves no result file, or an empty one, is the row `JUNIT MISSING` (verdict `ERROR`). Do: find out why pytest wrote no result file.
       - The first run on the unmutated code (all the tests of your `tests` argument) is repeated after every mutant on the same database (the canary run). When it no longer passes, the call stops with `CanaryFailed`, and the rows so far are in its `rows`. Do: make the tests clean up after themselves, or give the mutant list a fresh database.
       - An address the runner cannot check is refused before any test runs (next entry). Do: write the address in one of the two accepted shapes and list its host.
       - A second run on the same database address in the same lock folder is refused with a `RuntimeError`. Do: wait for the other run, or give each run a database of its own.
       - The first failure line and the test id are replaced by short fixed texts while the address is present (entry "what is shown"). Do: if a script reads `first_lines`, test for the fixed words `[expect found]`. Your own `expect` text (the fragment of the failure message that the mutant must produce) is printed after both `[expect found]` and `[expect not found]`, so its presence proves nothing. Example entries: `AssertionError [expect found] go must give its flag back` (the failure had the text) and `KeyError [expect not found] go must give its flag back` (it did not).
  4. **Windows and macOS.** Only Linux is run in CI. We have not run the runner on Windows or macOS, with or without `pass_env`, and we have not run the mutant list of this tool (`tests/mutation_runner_mutants.py`, 329 mutants of the runner and its judge; these are the SDK's own mutants, not yours) there. By reading the skip markers, some of those mutants would not be killed on Windows, because the tests that kill them need POSIX signals, file owners, file modes or links. Their names are in the header of that file, in three lists. Two are derived by a test and compared both ways: the killers that skip through a mark (`posix_only` or a `skipif` on the system name) and the killers that call `pytest.skip` in their body. The third is kept by hand and checked by a test against the killers that read `os.name` or `sys.platform` in their body: two killers drop the case that tests a POSIX-only guard where the system is Windows, so their mutants survive there. The header prose says why each skipping killer skips. Nothing of it is counted by a run on Windows. The type checker `mypy --platform win32 tools/mutation_runner.py` reports 14 errors at this version (measured in round 27 by running the repo test with mypy 2.4.1 added for that run only, on Python 3.12 and 3.13; the repo test that runs mypy is skipped where mypy is not installed, which is the case in CI): 13 are POSIX-only functions and constants (`getuid`, `O_DIRECTORY`, `O_NOFOLLOW`, `waitid` constants, `killpg`, `SIGKILL`), and 1 is the missing type information of `hadavin_sdk.testing.mutation` (the same single error appears on Linux). On Windows the runner takes a lock file in the temp folder and checks nothing about that folder or file there, so we do not know that it keeps two runners apart. Give each run a database of its own, and treat a green mutant list on Windows or macOS as unproven.
- **Mutation runner, keyword `pass_env`: what it does and what it does NOT do.** `pass_env=("HADAVIN_TEST_PG_DSN",)` gives the test process the listed environment variable, which holds the address of a test database. Words used below: the *passed variable* is that variable; its *address* is the whole value of the variable (a login and a password in it included); a *replacement text* is a fixed text in square brackets that the runner shows in place of other text. The runner checks the variable's name only (one name is allowed today). The tests, and every process they start, receive the full address, a password in it included. So pass only the address of a test database, never a token or a key.

  What a listed name switches on depends on the variable. "Skip check" is `forbid_skips` (below). "Canary run" is the first run repeated after each mutant, together with the lock (below). "Output replaced" is the allowlist of shown text (below).

  | the variable | skip check (`forbid_skips`) | canary run and lock | output replaced |
  |---|---|---|---|
  | listed, variable absent | on (off with `forbid_skips=False`) | no | no |
  | listed, variable present but empty | the call is refused before any run | | |
  | listed, variable present with a value | on (off with `forbid_skips=False`) | yes | yes |

- **Mutation runner, keyword `pass_env`: what is refused before any test runs, in this order.** Refusals 1 to 12 are a `ValueError` (a bare string in place of a list is a `TypeError`) and are raised before any folder is made; refusal 13 is a `RuntimeError`. A refusal of an address names the variable and the reason, never the address.
  1. A path in `tests` or `extra_dirs` that is not a plain relative path. Do: write the path relative to the root of your tree.
  2. A name in `pass_env` that is not allowed. Do: pass only `HADAVIN_TEST_PG_DSN`.
  3. An entry of `throwaway_hosts` that is not exact (a pattern such as `*`, brackets, white space, an empty text). This is checked for every call, also when no variable is passed. Do: write each host in full.
  4. An entry of `shown_classes` that is not an exception class name. Do: write the bare class name (`PostgresError`).
  5. A `conftest` that is not a plugin file of the tree. Do: see the entry on `conftest` below.
  6. An address longer than 2,000 characters. Do: use a shorter address.
  7. A character that a print would change (a quote mark, a backslash, a control character, a non-ASCII character) in the address, or in its password after percent-decoding. Do: change the password of the test database to plain ASCII letters and digits.
  8. An address that gives more than 300 texts to search for (a password written in many percent-encoded layers). Do: do not percent-encode the password more than once.
  9. An address outside the two accepted shapes, both in lower case. Shape one is a `postgresql://` (or `postgres://`) URL with an optional login, a host, an optional port and ONE database name, and nothing after it. Shape two is `key=value` words separated by one space, with these keys only, each at most once: `host`, `hostaddr`, `port`, `dbname`, `user`, `sslmode`, `connect_timeout`. `sslmode` takes `disable`, `allow`, `prefer`, `require`, `verify-ca` or `verify-full`; `connect_timeout` takes digits. An IPv6 host is written `[::1]` in a URL and `host=::1` in words. An empty text is refused too. Any other key is refused, a password key included, because it can change where the connection goes or name a file. Do: write the address in one of the two shapes.

     A password goes in the login part of the URL. Example: `postgresql://app:p%40ss@localhost:5432/testdb` is the address for the login `app` with the password `p@ss`. In a password, write `@` as `%40`, `/` as `%2F`, `?` as `%3F`, `#` as `%23`, a space as `%20` and `%` as `%25`. A colon may stand as it is. The runner searches for the password as written and as decoded.

     Not possible today: a password together with `sslmode` or `connect_timeout`. The URL shape takes nothing after the database name, and the words shape takes no password key. Do: use a test database whose login needs no password, or one that needs no option.
  10. An address with no `host` and no `hostaddr`. It would use the default local socket of the machine, which the runner cannot check. Do: write the host.
  11. A host that is not listed. `host` and `hostaddr`, each when written, must be a member of `throwaway_hosts`. A host name is compared whole, without regard to upper and lower case; a unix socket folder (`host=/var/run/postgresql`) is compared exactly as written. The default list is `localhost`, `127.0.0.1` and `::1` and holds no socket folder. There is no pattern and no override. The address CI uses, `postgresql://postgres@localhost:5432/postgres`, passes. Do: FIRST make sure that the database on that host is disposable and that its login can touch nothing else. The runner cannot check this. Only then pass `throwaway_hosts=("the-exact-name",)`. The list you pass REPLACES the default list, so also write `localhost` in it when you still need it.
     The same step also refuses a password that is the same, in any letter case, as the name of an exception class that the runner may show (a name of Python itself, a `crash_type` of a mutant of the call, an entry of `shown_classes`). Hiding such a name would tell the reader that the password equals it. Do: choose another password.
  12. A mutant whose `test_file` is not one of `tests`. Do: add the file to `tests`.
  13. A second runner on the same address in the same lock folder (entry "the lock"). Do: wait for the other run, or give this run a database of its own.

- **Mutation runner, round 27: what the reviewers of round 26 found.** No Blocker. The mutant list has 329 mutants (2 added, 2 re-pointed because the text they search for moved).
  - The killer of the mutant "the folders between are made without the private helper" is killed for its stated reason also by a user who is not root. Before, the folder made with mode 0500 under the mask 0277 made a later step fail with `PermissionError` for such a user, so the failing line did not hold the expected fragment and the list ended red for anyone but root (round 26 had been run as root only). The helper spy now runs first under the normal mask, an `OSError` under the mask is turned into a failure that names the guard, and the comment says 0500. The mutant list was run once as a non-root user and once as root (the evidence file of the package says how).
  - The CHANGELOG and the header say the same thing about the lists: two derived lists, compared both ways, and one hand-kept list of two killers (below); the prose gives the reason for every killer that skips, "a link out of the tree is accepted" included.
  - The reader of the skip marks reads every decorator and every part of `pytestmark`, also after one that is already true, and raises on one it cannot read. Before, it stopped at the first true mark.
  - A file that a runner makes is put back to mode 0600 only when it is a regular file of this user with one name (`_narrowable`); a refused file with a second name keeps its mode (before, its shared inode was narrowed first). The open uses `O_NONBLOCK`: a named pipe under the name of a result file or settings file fails at once (no reader) or is refused as not a regular file (a reader), where the open for writing used to wait for a reader for ever. A test runs the real function on a named pipe with a time limit. The text says that the refusal for a file of another user is reached only by root or for a file this user may write.
  - The pin of the places that create folders and files is now (spelling, function, number of calls). The text says "the listed spellings" and names the spellings it does not find (a name assigned first, `getattr`, `map` or `partial`, `os.fdopen`, `io.open`, `codecs.open`, other `Path` methods, `shutil.copyfileobj`). The parents of the target of an `extra_dirs` copy are made by `copytree` and `makedirs` and keep the caller's modes.
  - A test that always runs says that "CI does not run the mypy count" is true: the CI workflow does not name mypy and the lock file has no package of that name. The mypy figure is now 14 errors (13 places of POSIX-only names and the one import error): the new function `_narrowable` calls `os.getuid` once more, which is a fifth place of that name, so the round 26 figure of 13 is out of date. It was measured by running the repo test with mypy 2.4.1 added for that run only (not added to the lock), on Python 3.12 and 3.13. The text says how it was measured and a sentence about who would do the work is replaced by "a separate decision of the owner".
  - Wording only: a hidden class name of the caller shows one bit (the name equals the password or holds a piece of it); a reader cannot read the password from an equal name. Not changed in behaviour, as decided. Folder checks: the temp folder and the snapshot folder are checked again after every rebuild, the others once when made.
- **Mutation runner, round 26: what the reviewers of round 25 found.** Round 25 had no Blocker; this round fixes the Major and the Nits that were accepted.
  - One rule for every shown class name. A name that is equal to a secret in any letter case is `[class not shown]` whether it is a name of Python, a `crash_type` or a `shown_classes` entry (round 24 did it for the names of Python only: `shown_classes=("PostgresError",)` with the password `postgreserror` showed the name). The address check now also refuses such a password before any run (fixed sentence, naming the variable and never the password), so the hiding is the second layer and a reader can no longer infer from a hidden name that the password equals it.
  - A password that is only a piece of a name of Python does not hide it, but a piece of a name the caller owns does (the caller's names go through the second layer like every caller text). This difference is on purpose and is now stated in the module docstring.
  - The folders between the temp folder and a copied test file are made by the same helper as every other folder (mode 0700 whatever the umask, checked), so the text "every folder the runner makes" is true; a part that was already there is left as it is.
  - A made file is checked on the open file BEFORE it is emptied: a file with a second name keeps its content when it is refused (round 24 emptied it first).
  - The pin test of the creation sites reads the whole module (module-level code too), reads aliased imports, and lists more spellings (`shutil.copytree`, `copy`, `copy2`, `copyfile`, `move`, `os.rename`, `replace`, `symlink`, `link`, `mkfifo`, `tempfile.TemporaryDirectory`, `TemporaryFile`, `SpooledTemporaryFile`). The module docstring now says "the listed spellings" and names the sites that are not helpers on purpose: the copies of the caller's tree keep the caller's modes, and the mutant is written into the copy of one existing file.
  - The test that derives the Windows skips from the skip marks raises on a `skipif` condition it cannot read (it used to read such a condition as "no skip"), reads the module-level `pytestmark`, and the header of the mutant list has a second list of the killers that call `pytest.skip` in their body, compared with the killers in both directions (13 killers). Every killer that skips is named in the prose of the header with the reason it skips (round 27 added the one that round 26 had left out, "a link out of the tree is accepted": it links a folder, a junction on Windows).
  - mypy: CI does not run the `mypy --platform win32` count, because mypy is not in the locked test environment and adding it is not a plain addition (a `uv lock` with the tool chain of this machine also rewrites the format revision and the platform markers of `uv.lock`); that is a separate decision of the owner and is stated in the module docstring. What CI runs is the table test that counts the places of the POSIX-only names. The test that runs mypy now uses fixed flags (no summary line, no colour, no settings file) and every line that says `: error:` must be one the pattern reads.
  - The mutant list had 327 mutants at the end of round 26: 320 plus 7 new. The 7 new: a built-in class name hidden for a password that is a piece of it; a name the caller owns equal to a secret in another letter case; the address check for a password equal to a class name (three mutants: refusal off, case-sensitive, caller names not given); the folders between made without the helper; a file emptied before the check. The re-pointed ones are listed in the header of the mutant file.
- **Mutation runner, round 24: what the reviewers of round 23 found.**
  - The count of `mypy --platform win32` errors was a hand count. It is now measured (mypy 2.4.1, Python 3.12 and 3.13: 13 errors, the command and output are in the evidence folder of the package) and a test runs mypy itself where mypy is installed. The measuring showed that `os.fchmod` is unknown to mypy on Windows before Python 3.13 (the count would have been 14 on 3.12), so the runner calls `os.chmod` on the open file instead.
  - The header of the mutant list no longer says that every other killer runs on both systems. The names of the mutants whose killer is skipped on Windows are listed in the header and derived by a test from the skip marks of the killers (52 mutants, not the 21 that round 23 counted). Killers that skip inside their body were still named by hand in round 24 (round 26 made that list derived too).
  - The two order mutants that round 23 declined (the secret-count step against the address step, the junction checks against the first temp folder) exist now: a mutant may replace several lines. The wrong reason in the header is removed.
  - The settings file and the result file are checked on the open file like the lock file (one check, `_file_problem`). The temp folder, the folder of the settings file and the `tests` folder of the copy are made by helpers, and a test pins that every creation site of the runner is a helper.
  - A password that is equal to the name of a Python exception class (in any letter case) is no longer shown as the class of a failing line (the probe of 498 cases shows 0 of 498). A password that is only a piece of such a name still does not hide the class: the name tells nothing about the password, and hiding every name that holds a short password would blank all of them.
  - A bare string for `crash_markers` of a `Mutant` is a `TypeError`. `connect_timeout` takes one to five digits (the texts said "digits"). The text about the order of the bare-string checks is exact now: three come before the path check, three after it.
- **Mutation runner, round 23: private folders and files, and the limits that were missing.**
  - Every folder and file the runner makes (the temp folder, the snapshot, the folder of the pytest settings file, the settings file, the result file, the lock folder and file) is made with mode 0700 or 0600 whatever the umask of the caller, and is CHECKED when it is made, the temp folder also after every rebuild of the copy. A folder is checked with `lstat` (a real folder, not a link, owned by the user, no group or other bits); a file is checked on the open file (a regular file, owned by the user, mode 0600 or narrower, one name only: round 24 added this check for the settings file and the result file, which round 23 only made with mode 0600). The temp folder is emptied and kept, never removed and made again with the default mode.
  - A bare string for `tests`, `extra_dirs` or `only` is a `TypeError` (it used to be read letter by letter); for `throwaway_hosts` and `shown_classes` it already was (round 22).
  - A port of an address must be 1 to 65535, in the URL and the key=value form. A lock folder inside the tree under test is refused (give the run a temp folder outside the tree with `TMPDIR`). Two runs that differ only in the login are treated as one database for the lock; a run with the variable absent takes no lock.
  - A result file that a mutated test forges is the caller's problem inside its own temp folder; the runner reads the result only through the judge. The mutant list had 299 mutants at round 23 and has 320 at round 24.
- **Mutation runner, keyword `pass_env`: what the runner cannot check.** It cannot check that the database is disposable. It cannot see what the login may do. The host list is the only check, and it checks only the host written in the address; the tests are code and can connect elsewhere. A local name does not prove a local database, because a tunnel or a proxy can point it at a shared one. Adding a host to `throwaway_hosts` removes that one check for that host. Every mutant run writes to the database, and a mutant can make the tests drop or fill tables. So you must know that the database is disposable and that its login can touch only that database.
- **Mutation runner, keyword `pass_env`: what protects the address, and what is shown.**
  - The console output of the tests (stdout and stderr) goes to the null device. The runner never reads or prints it.
  - The tests get a fixed short list of environment variables plus the passed variable. No variable of the database library (`PGHOST`, `PGSERVICE`, `PGPASSFILE` and the like) is on it; a test checks that. The runner limits environment variables only; it does not fence off files or the network. `HOME` IS inherited, so the tests can read any file of the user who runs them: a `~/.pgpass` file (which the tests' database library then uses), cloud credential files, SSH keys. Run the mutant list under an account that holds no real credentials.
  - The passed variables are read once, at the start of the call; a change of them during the run changes nothing. Two lookups are made later and are not covered by that sentence: `XDG_RUNTIME_DIR` (where the lock folder lies) and the temp folder lookup (`TMPDIR` and the like, read each time a temp folder is made).
  - With no passed variable nothing is replaced and nothing is claimed: a failing line of a test is shown as it is. Do not pass this runner a test suite that must not see its own secrets without passing them. (Decision D-023: a limit stated here, no change of behaviour.)
  - While the passed variable has a value, text from the tests is shown only when it is on an allowlist of text that the caller or Python owns. A list of the forms a secret can take (a slice, a reversed copy, base64, hex) can never be complete, so the allowlist does not depend on such a list.

    | the place | what is shown |
    |---|---|
    | the exception class name | shown when it is a built-in Python exception name or pytest's `Failed`, a `crash_type` of a mutant of this call (the exception class that mutant says its crash must have), or a name in the keyword `shown_classes`; for a line that starts with a bare `assert` the fixed word `assert`; else `[class not shown]`. A shown name that is equal to a secret in any letter case is `[class not shown]` too (one rule for every one of these names; such a password is refused before any run, see refusal 11) |
    | the rest of the failing line | never shown; instead `[expect found]` or `[expect not found]`, then the caller's own `expect` text |
    | a test id | the file part is shown when it equals one of the caller's `tests` entries (the caller's text is printed, without `.py` and without a leading `./`); a class name or function name is shown when `def name` or `class name` stands in the snapshot of that file, or the caller named it on the mutant (`only_test` names the killer test; `pinned` names the test id the kill must come from); when any part is not allowed, the WHOLE id is `[test id not shown]` |
    | the `[...]` part of a test id | always `[parameters hidden]` |
    | how a run ended | fixed words: the exit code, "timed out", or "reaped" (another part of the program collected the exit status of the test process first, so it is lost) |

    This holds for every text the runner returns or puts in the message of an error it raises: `first_lines`, the test id of a row, the messages of the `COLLECTION ERROR`, `FIXTURE ERROR` and `SKIPPED TESTS` rows, and the messages about a failed or skipped first run and about a failed or skipped canary run.

    Examples, from a real run with an address present (the row, then its `first_lines` entry):

    ```
    ('go gives the opposite', KILLED, 'tests/test_core::test_a', True)
        AssertionError [expect found] go must give its flag back
    ('go raises', WRONG_REASON, 'tests/test_core::test_a', False)
        KeyError [expect not found] go must give its flag back
    ('pick gives 2', KILLED, 'tests/test_core::test_b[parameters hidden]', True)
        AssertionError [expect found] pick must give 1
    ```

    A test id with a part that is not allowed is shown whole as `[test id not shown]`.
  - Second layer, for the caller's own text only. Four slots hold text the caller wrote: a test id, an exception class name from `crash_type` or `shown_classes`, the `expect` text, and a mutant name inside a message. Each slot is searched for the address, its password and the percent-encoded forms of the password. A slot that holds one of them is replaced WHOLE by its replacement text: `[test id not shown]`, `[class not shown]`, `[expect text not shown]` or `[mutant name not shown]`. Nothing is ever cut out of the middle of a text. Python's own exception names and the runner's fixed words are never searched and never changed. `[expect found]` and `[expect not found]` are shown also when the `expect` text itself is replaced. With a weak password this hides much: with the password `test` every test id that holds the letters `test` is `[test id not shown]`, and a password of one or two characters hides nearly every id. Use a random password of 12 or more characters, or a login that needs none.
  - `first_lines` and `crash_type`, stated once: the judge and the `crash_type` check read the real line of the tests inside the runner. `first_lines` gets what the table shows. With no passed variable that has a value, nothing is replaced.
  - Not covered:
    - The name column of a row and the keys of `first_lines` are the caller's mutant names, given back unchanged. A piece of a password written in `expect` or in a mutant name is shown (only the whole password is found). So never put a secret in `expect` or in a mutant name.
    - A test that itself writes the address to a file or to the network is out of reach of this tool. A test can also write the result file of its own run, so a hostile test can forge its own verdict row.
    - A test can choose which allowed name it shows (one of about 70 exception class names of Python, one of the caller's function names), so a hostile test could pass a few bits per row that way. The counts and the exit code are numbers the test chooses, too.
    - The result files of the test runs hold the tests' real text. They lie in a temp folder of the run that Python makes for the current user only (mode 0700 on POSIX; the runner does not check that mode itself). The runner removes the folder at the end. After a kill that cannot be caught (SIGKILL) it stays on disk (`mutants_*` and `mutant_ini_*` in the temp folder): delete it by hand.
    - A traceback of an error that the runner raises holds the address in its local variables. A tool that prints local variables (pytest `--showlocals`, an error tracker) prints the address with its password. The messages of the errors never hold it.
  - `pinned` is compared with the real test id inside the runner, parameters included. Only the shown id has `[parameters hidden]`.
- **Mutation runner, the lock: one runner per address in one lock folder.** Its reach is small. It stops a second runner only when that runner uses the same lock folder and the same spelling of host, `hostaddr`, port and database name. The lock file is named by the first 16 hex digits of a sha256 of those four parts; the password is never read for it and the file name holds no part of the address. The lock does NOT see a runner of another user, or a runner with another temp folder or on another machine. It does NOT see the same database written another way (`localhost` and `127.0.0.1`, a port written or left out). It does NOT see a run with `XDG_RUNTIME_DIR` set (a login shell) next to a run without it (cron, `su`, a CI step): they use two lock folders. The canary run does not replace the lock: it proves only that the unmutated tests still pass. So give each run a database of its own. The lock only catches the plain mistake of starting twice.
  - Where: on Linux and macOS the lock folder is `hadavin_mutation_locks_<user id>`. It lies in `XDG_RUNTIME_DIR` when that names a folder of this user that is closed to others, else in the temp folder that Python picks (`tempfile.gettempdir()`, which is not `TMPDIR` when `TMPDIR` cannot be written). The runner makes it with mode 0700, opens it without following a link, checks what it opened, and creates the lock file under the opened folder (mode 0600, never deleted).
  - A folder under that name that belongs to someone else, is a link, or is open to group or others is REFUSED: the run stops with a `RuntimeError`. The runner cannot prevent another user of a shared temp folder from putting such a folder there first. Do: give the run a temp folder of its own with `TMPDIR`. The runner does not look at the PARENT folder: in a shared temp folder without the sticky bit another user can move the lock folder away, the next runner then makes a new one, and the two runs do not see each other.
  - Two databases behind one unix socket folder get two lock names.
  - Windows: the lock file lies directly in the temp folder. The runner checks nothing about that folder or file there, and we have not run it there.
- **Mutation runner, keywords `conftest`, `forbid_skips` and `shown_classes`.**
  - `conftest="tests/conftest.py"`: one file of the tree that every test run loads as a pytest plugin. The path must be plain ASCII names ending in `.py`, no part may be a Python keyword, and the file must be called `conftest.py` or lie in a folder called `tests`. No other `conftest.py` is read.
  - `forbid_skips=True`: a run where any selected test is skipped (or is an expected failure) is the row `SKIPPED TESTS`, never a kill. A first run that skips stops the call. A run with no result file is the row `JUNIT MISSING`. Default: on when a name is LISTED in `pass_env`, whether or not the variable is present; off otherwise. `forbid_skips=False` turns it off.
  - `shown_classes=("PostgresError",)`: exception class names of your own libraries that may be shown while the passed variable has a value. Plain identifiers only; test class names are not allowed by it.
- **Mutation runner: background (not needed for the upgrade).**
  - Why we wrote code: ready-made mutation tools cannot say why a mutant died. `pytest` runs the tests, and whole-file mutation tools neither judge the reason nor name the killer test. No no-code tool fits a developer check. The product's redaction function was read and not reused: it finds secret-shaped text by pattern, not one given value, and it would tie a tool that other repositories copy byte for byte to the product module.
  - The changed results in detail. (1) A run whose FIRST failing test case failed in a fixture is `FIXTURE ERROR`; a test body that failed and whose teardown failed afterwards is still judged by the body's failure (confirmed by a real run). (2) `judge()` returns `ERROR` when the run failed with exit code 1 and no failing test id is known. The row then says `NO FAILING TEST NAMED`; for any other exit code with no failing test it says `EXIT CODE <n>`. (3) `COLLECTION ERROR` is a new label only: pytest exits 2 for it and `judge()` already returned `ERROR`.
  - Evidence for change (3). The unchanged runner of `main` (commit 2a8c2aa, `tools/mutation_runner.py` sha256 `489517fb224f0598e14244ded1b37fe2a68be69e2396e56e450be0d8b1c0a1a7`) was run on a tree whose test file starts with `assert go(True) is True, 'at import'`. It gave the row `('flip', ERROR, '::tests.test_core', False)` with the first line `E   AssertionError: at import`. pytest exited 0 for the first run and 2 for the mutant run.
  - Judge helpers. `src/hadavin_sdk/testing/mutation.py` gains `skipped_tests(xml_text)`, `fixture_errors(xml_text)`, `read_junit(xml_text)` (one parse of the result file) and `judge_report(rc, report, ...)`. `judge_report` is the one call that judges a run correctly. `judge()` alone cannot know about a fixture error, so a harness that feeds it `first_failure_junit(xml)` only can still count one as a kill.
  - The result file is read only when it is a regular file, and its size is checked first. A file that is refused, truncated or cannot be read is that mutant's row `JUNIT REFUSED`, and the run goes on.
  - Lock folder, the choice made: a private folder, not a keyed hash (a key would need its own protected file) and not a lock inside the database (the runner uses the standard library only and has no database driver).
  - Tests (`tests/test_mutation_runner_keywords.py`). A seeded test makes 60 random passwords and 8 forms of each as text from the tests (plain, slice, reversed, base64, hex, rot13, upper case, percent-encoded): 480 runs. In each it takes 13 outputs from the real code paths (nine kinds of result row, the message of a failed first run, of a skipped first run and the two canary messages) plus the `first_lines` entry of every row that has one. It checks that each output is one of the texts that can be built from the caller's side alone. A control switches the allowlist off and the same check must fail. A second seeded test uses 150 weak passwords that are pieces of the caller's own text (a word of a test id, of a class name, of the `expect` text, of a mutant name), with 3 texts from the tests each, and checks that every slot of caller text is whole or its fixed text, never cut, and that each fixed text is reached. One real run raises exceptions whose class NAME is the password reversed and in five more forms. Further tests cover every refusal of an address and a refused neighbour for every allowed key. One test tries hosts that are almost a listed one: a trailing dot, the decimal, hex and short forms of `127.0.0.1`, an IPv4 address inside an IPv6 one, and 300 seeded random draws of hosts. Others pin the order of all 13 refusals and the three cases of the table above. One run goes through the real address check, the real lock folder and the allowlist together. Tests that need a made-up address name the made-up host `db.invalid` in `throwaway_hosts`, as a caller would.
  - The mutant list of the runner itself has 327 mutants, run with `uv run python tests/mutation_runner_mutants.py`. It covers the allowlist, the second layer, the address check and its call, the key rules, the socket rule and the lock folder checks. Equivalent mutants (a replacement that changes no behaviour) are not listed; the header of that file says which and why.
- **Breaking: the first stage is now called `demo`; `environment: dev` is refused.** The stages are exactly `demo`, `pilot` and `prod`. A config that says `environment: dev` stops at start with "environment: dev was renamed to demo; write environment: demo (allowed values: demo, pilot, prod)" (shown beside any other problem found in the same file, and also for `Dev`, `DEV` and spellings with spaces, which are refused all the same); any other value (`Demo`, `staging`, `uat`, an empty value) is refused too, and values are never tidied or guessed. To upgrade: (1) change `environment:` in your config to `demo`; (2) if your code imports `backends.table.DEV_ONLY`, import `DEMO_ONLY` instead (same six kind pairs, no old name kept); (3) a project label such as `uat` is not a stage: map it to one stage in your own config. Also: the pilot and prod checks (`deferred.py`, `registry.py`, `app.py`) now ask one function, `hadavin_sdk.stages.is_live(environment)`, which treats anything that is not exactly `demo` as live; the prod-only rules (no local key file, a retention-agreed anchor) ask `hadavin_sdk.stages.is_prod(environment)`, which is true for `prod` and for any value that is not a stage. `STAGES`, `is_live` and `is_prod` live in the new leaf module `hadavin_sdk/stages.py`, not in `config.py`; the list `deferred.LIVE` is removed. The redactor no longer sweeps the words `demo` and `pilot` as a name (it already skipped `prod`), but a secret that reads `demo` is still swept. No stage is stored today; the first change that stores one must map an old `dev` value to `demo` on read, for display only and never for a guard decision, and add a test through that real read site.
- **Code-quality scanner fixes (SonarCloud, an automated code-quality scanner); one public name removed.** `guard.runmap.PARTIAL_ESCAPE` is gone. If your code imports it, call `guard.runmap.partial_escape_start(text, pos)` instead; it returns the start position as a number (or None), not a match object, so replace a `.search(...)` call and its `.start()` with it. The old pattern looked for a cut-off percent code such as `%C3` at the end of a text and slowed down sharply on a long run of them (about 65 s for 40,000 codes in a row, measured 2026-11-06); the new function takes milliseconds. `guard/http.py` now holds the cloud-metadata addresses that no tool may reach as one documented table `METADATA_ENDPOINTS` (the same six addresses as before; the other refused ranges are unchanged).
- **K5-core, redaction behaviour you may notice.** The producers of text that reaches a model, a vendor screen, a card or a log line (listed in `guard/producers.py`, each tested by `tests/test_k5_round9.py` with a percent-, entity- and assignment-encoded secret) go through one function, `guard.runmap.redact_text`, which also undoes percent, HTML-entity, backslash-u, `\u{41}`, `%u0041`, backslash-x, backslash-U (eight digits) and three-digit octal escapes (not one- and two-digit octal or named escapes: `\1` and Windows paths would decode wrongly) and NFKC to a fixed point before it redacts: a secret written as `%41KIA...`, `&#65;KIA...` or `password%3Dx` is masked in those places, not only in tool results. Not on that list: the text of the ask-your-data demo's own ledger and command line (see its README). A text nested deeper than `defaults.SCRUB_MAX_LAYERS` (8) layers is not shown. A tool result is redacted whole up to 262,144 characters before it is cut; when it IS cut (at that cap, or again after a short handed-out secret was replaced by the longer marker), the last 8,192 characters of the result are dropped so a token that straddles the cut leaves no fragment (`defaults.CUT_MARGIN`; a PEM key is about 1.7 KB for RSA-2048, 3.2 KB for RSA-4096 and 6.4 KB for RSA-8192). Cost: redacting a hostile text at the cap takes one to four seconds on a laptop (one pass per distinct view); a call that has spent `defaults.REDACT_BUDGET_S` (6 s) before a further view is refused (`InputTooLarge`, nothing shown), and the perf step bounds it. A card text is sanitised and has commands withheld first and is redacted once, last (and once more with tags deleted, real placeholders and line breaks kept, when markup split a key from its value; that view is used only when it finds a secret value the text pass did not). A card summary is shown whole or replaced by a short note (never cut); a summary whose inputs are too large to redact says so. In a case bundle, camelCase credential keys (`clientSecret`, `dbPassword`), numbers and nested values under a credential key are masked too. The Kubernetes source defaults (`K8S_*`) stay in `defaults.py`, under their own header, with every other default.
- **K5-core, stated limits of redaction.** A secret value that itself contains a plain space, `;`, `,` or `&` (for example `password="my secret phrase"`) is masked only up to that character, by the redactor's own definition of a value; and a form-encoded `;` or `&` inside a value (`password%3Dab%3Bzq9`) is ambiguous between one secret and a key and value followed by more text (see SECURITY.md). A masked value nested deeper than the layer cap, or more than 256 values that need pairing across decoded views, refuses the text (`InputTooLarge` or `TooDeep`) instead of showing it.
- **K5-core, upgrade steps for an existing database.**
  - **API changes (breaking for custom code; pre-1.0, so the minor version moves).** The `Store` protocol gains six methods (`add_tool_call`, `list_tool_calls`, `purge_tool_calls`, `put_redaction_map`, `get_redaction_map`, `purge_redaction_maps`): a custom store without them is refused at start with their names (`ConfigError`). `Executor.execute` takes an optional `inputs_view`. Source kinds register through `sources.kinds.register`, which refuses overlapping operation prefixes. `make`, `hosts` and `Deps` now live in `hadavin_sdk.backends.factory`; there is no re-export from `hadavin_sdk.backends` on purpose (a repo rule keeps that package file free of imports so importing the config never loads a secret provider), so the old import fails with an ImportError: change it to `from hadavin_sdk.backends.factory import make`.
  - **Ledger test:** a database whose ledger holds `0005_evidence` and whose files are renamed is REFUSED by `migrate` with a message naming the row (`tests/test_k5_fixes2.py`); it never applies anything silently.
  - **Repair every dev and demo database before the first run of the merged code** (a demo database is taken from the merge commit, not from a branch). If the tables already exist: change the `version` of the `0005_evidence` row in `schema_migrations` to `0006_evidence` by hand. If not (or if an early `0005_evidence` lacks `tool_calls.error`): drop `tool_calls`, `redaction_maps` and that ledger row, then run `hadavin-sdk migrate --runtime-role R --purge-role P` again.
- **K5-core, redaction input cap.** `redact_text` refuses text over 262,144 characters AND any view of it the second pass would scan over that size (`InputTooLarge`, before the work; 87,000 U+FDFA used to take 24 s and now 0.03 s). A document refused that way ends `NEEDS_PERSON document_too_large`. `evidence.max_document_bytes` may not exceed 262144. An action input schema with an `identifier` flag below the top level is refused at load. A tool's `generated_suffix` may hold at most two variable-length repeats (`{lo,hi}`). `evals.gate` raises a `ConfigError` naming the golden case whose input cannot be redacted. Name lookups: at most 8 may be stuck process-wide (shared by tools, LLM clients and the executor), and the permit is returned if the lookup thread cannot start. NAT64 (`64:ff9b::/96`, `64:ff9b:1::/48`) is refused by our own rule on every Python version.
- **K5-core, tool-result size and decode.** A tool result is now REFUSED (`InputTooLarge`, the run abstains `redaction_error`) when a secret was handed out to the tool and the decoded view of the result (JSON `\u` escapes, percent-encoding, HTML entities, then NFKC) would pass 262,144 characters; the decode is computed once per result. A tool result that was cut keeps its `[truncated]` marker inside the same cap (the window is 262,132 characters), so a large legitimate output is no longer refused because of the marker. Action contracts with an `identifier` flag below the top level are refused for every action, used or not. Card text over the redactor's cap is refused, and tick, log and validation-error lines are redacted first and then cut to their length.
- **K5-core, the scrub of a tool result.** The limits below are pinned by tests in `tests/test_k5_fixes5.py` to `test_k5_fixes9.py` and `tests/test_k5_layers.py`; the two figures on the end of a cut text (the proportion that loses a group) are estimates from a run, not pinned.
  - **Size.** Scrubbing grows a short secret (6 characters become the 17-character `<SECRET_REDACTED>`), so a result far below the 262,144-character cap could pass it and was refused (`InputTooLarge`; 15,421 copies of a 6-character secret was the smallest case). The grown text is now cut back to the cap with the `[truncated]` marker. `max_bytes` of a tool and `legacy_max_output_bytes` may be at most 262,144. Two refusals remain, both `InputTooLarge` and a `redaction_error` abstention: a decoded view of the result that would pass the cap, and a text that the escaping of result markers and placeholder look-alikes (the neutralise step of `redact_untrusted`) grows past the cap (it needs look-alike characters within a few times of the cap).
  - **Cuts.** A cut can split a handed-out secret (the raw-size cut, the window cut, the cut after a replace inside the scrub), and then no whole spelling is left to mask. After EVERY such cut, and before any swap of the text for its decoded view, the scrub removes: a half-written escape at the end (`\u005`, `&#9`, `%C3`, half of a surrogate pair); the longest stretch before the marker that reads (layers and NFKC undone) as the start of a spelling of any handed-out secret (a compatibility-character spelling can need more than one character to read as a start) (hex in any case); and the front of a base64 token that wraps a secret (standard or URL-safe alphabet, token of 8 characters or more, cut back to the 4-character group that holds the first byte). A reply loses the last few characters to this; ordinary text at the very end can lose a trailing `&T`, a `%C3%A9`, or (about 3 in 100, when the tail looks like base64) its last group. The look-back is at most `evidence.scrub.fragment_scan` (4,096) start positions with one decode each.
  - **Exception messages.** The message of a tool's exception is scrubbed in full BEFORE it is cut to 160 characters (200 for a refusal), so the cut cannot leave the front of a secret.
  - **What the scrub undoes.** A handed-out secret (6 characters or more) is found as it is, URL-quoted, hex (any case), base64 and base32 (base64 also two or three times), and behind JSON string escapes (`\uXXXX` with surrogate pairs joined, `\/`, `\"`, `\\`, `\n`, `\t`; PHP writes every slash as `\/`), percent-encoding (twice), HTML entities, NFKC compatibility characters (full-width, mathematical, circled, superscript) and invisible characters. The layers are undone to a fixed point, at most 8 rounds (`defaults.SCRUB_MAX_LAYERS`; deeper is cut or replaced, see the next entry), so they may nest either way (`&#37;41`, a double-escaped entity). The redactor's second pass (`guard/runmap.py`) joins surrogate pairs and reads `\/` too.
  - **What it does not undo.** Hex of a percent-encoded value, ROT13 or any substitution cipher, reversed text, a character separator (`V-h-5`), one- and two-digit octal escapes, named escapes, a base32 token that wraps a secret, a base64 token shorter than 8 characters (`tools.B64_MIN_TOKEN`, the one bound), and any layer not listed: the text stays as it came and a cut inside such a spelling leaves its first characters next to the marker. This is a limit, not a guarantee: the control is that a tool is not handed a secret it does not need (least privilege). `tests/test_k5_fixes7.py` pins the unhandled layers so a change is seen.
  - **Settings.** The thresholds are validated configuration under `evidence.scrub` (`tail_window` 256, `min_redaction_window` 4096, `min_secret` 6, `fragment_scan` 4096, `fragment_min` 1, `partial_end` 10; ranges in `config.ScrubSettings`), one set of defaults in `hadavin_sdk/defaults.py`.
- **K5-core, layered encodings.** Every tool result, whether or not a secret was handed out, also gets a decode-to-fixed-point view (percent, entity, backslash escapes, NFKC) that is redacted too, so a pattern-shaped secret (`%41KIA...`, `password%3Dx`) is found; a text nested deeper than the cap is not shown. The scrub undoes any ordered stack of percent, HTML entity (decimal and hex), backslash-u, backslash-slash and NFKC full-width layers, and a base64 token front, to a fixed point: each round applies NFKC, JSON escapes, percent-decoding and entity-decoding ONE AT A TIME (a combined step turned the half entity `&#10`, which percent-decoding had just exposed, into a newline, so `percent(entity(secret))` cut inside the token left its front: 7 of 451 cut points). A half-written escape at the end is dropped before every decoder. The depth is capped at `defaults.SCRUB_MAX_LAYERS` (8); a text that still changes after the cap is not shown (the tail is cut back to its start; a whole result becomes `<SECRET_REDACTED>` + `[truncated]`): fail closed. Our own design (not a quoted standard): CWE-174 (double decoding) warns that decoding twice lets values past a check and says to reject non-conforming input; OWASP Input Validation Cheat Sheet says to decode before checking and to cap parser nesting depth (both pages fetched 2026-11-03); neither describes decoding to a fixed point, which is what finding a secret in any spelling needs. `error_reason` and every tool result go through the same `_scrub`. Pinned by `tests/test_k5_layers.py` (seeded fuzz of 20,000 orderings and depths at the default and a small window, the recorded failing cut points, a sensitivity control, a perf-marked 100 KB timing test).
- **K5-core, purge role, store settings and tool gating.**
  - **Required now in pilot and prod on Postgres: `backends.store.purge_dsn_secret_name`** (the process refuses to start without it, so the purge cannot silently fail and keep plaintext originals for ever), and `evidence.restored_hash_key_secret_name` must hold at least 16 bytes. Re-run `hadavin-sdk migrate --runtime-role R --purge-role P`: the purge role now has column-level SELECT only (`runs`: run_id, state, updated_at; `redaction_maps`: run_id, updated_at; `tool_calls`: call_id, run_id, created_at) plus DELETE on the two evidence tables, and `migrate` asserts both roles' EFFECTIVE privileges (membership, PUBLIC, default privileges, relations outside the map, ownership, CREATE, superuser) and rolls back on any excess.
  - New settings, both under `evidence`: `max_map_entries` defaults to 2000 (a run whose text plants more distinct values ends `NEEDS_PERSON document_too_complex`), `post_read_operations` defaults to empty (a tool operation bound to POST must be listed). The redactor's built state is kept per run, so cost no longer multiplies strings by map size.
  - A tool whose source was switched off by a failed re-probe is refused in `ToolBox.invoke` (by `options.source` or by host), not only the app's own source objects. A non-string value for an identifier input is ungrounded. Every redaction bound now has a masking fallback. Source reads count toward the request cap. More metadata addresses are refused and a name lookup has a 5 s timeout. The restored-hash comparison is constant-time.
  - The import-pin text is corrected everywhere: the pin proves the reviewed text of one file is what runs; the loader-name refusal is a best-effort tripwire; a tool body is trusted code. Perf tests moved to a `perf` marker in their own CI step (blocking: the check is a ratio, so a noisy runner moves both runs alike); the `check` job's timeout is 30 minutes.
- **K5-core, restored-input hash key, document size and concurrency slots.**
  - **New required key in pilot and prod: `evidence.restored_hash_key_secret_name`** (a secret in your secrets kind). The gate's audit event now carries an HMAC of the restored inputs under that key, not a plain hash of real identifiers; an execution whose plan has no recorded hash is refused (`restored_unbound`), not skipped.
  - `evidence.max_document_bytes` now defaults to 262144 (was 1 MiB). The command-line credential patterns (curl, mysql, redis-cli, sqlcmd, ldap, htpasswd, docker/mongo/az login) were quadratic on repeated words and are bounded to 1024 characters of gap; a long-token sweep masks any run of 129 or more base64-ish characters; the URL-password bound is 1024. EMAIL masks local parts up to 254 characters. A test generates its inputs from every pattern's own keywords and fails on super-linear time.
  - No regular expression is built from a client value any more (`evidence.contains` uses plain scans; the sweep finders are compiled without entering `re`'s cache). The pinned-module import check refuses these loader names as a best-effort tripwire, not a boundary (`import_module`, `__import__`, `importlib`, `runpy`, `exec`, `eval`, `compile()`, `builtins`, `spec_from_file_location`); it stays best effort, a meta-path finder restricted to the pin is the sound fix.
  - The concurrency slot is held until the tool's thread ENDS (a timed-out body keeps its slot), and every request a tool makes counts toward `max_tool_calls_per_minute`. Tools never use an environment proxy; the LLM clients and the executor still may. More addresses are refused (metadata addresses, 6to4, Teredo, NAT64, 198.18.0.0/15). `generated_suffix` is a tiny grammar (literals and bounded character classes). Any credential-bearing header is refused over plain http. The scrub also sees double percent-encoding, base32 and triple base64. A failed re-probe switches the source OFF (reads refused) until a probe passes; a malformed RBAC rule proves nothing.
- **K5-core, migration roles and store settings.**
  - **Run `hadavin-sdk migrate` again with `--runtime-role R --purge-role P` (two different roles) and set `backends.store.purge_dsn_secret_name`.** The runtime role no longer holds DELETE on `tool_calls` or UPDATE/DELETE beyond what it needs: only the purge role deletes evidence (it holds column-level SELECT plus DELETE on the two evidence tables only). Without a purge DSN the purge step runs under the runtime identity, is refused by the database and FAILS loudly (evidence is kept, never silently deleted).
  - New `evidence` keys: `max_document_bytes` 1048576 (a larger document ends `NEEDS_PERSON document_too_large`), `case_insensitive_targets` [] (grounding is exact in case unless the contract's `target_system` is listed), `source_reprobe_s` 3600 (a new tick step `reprobe_sources` probes every source's scope again and fails loudly if RBAC widened), `max_concurrent_tool_calls` 4 and `max_tool_calls_per_minute` 120 (per process: the agent cannot raise the load on a client system). New manifest key `generated_suffix` (a regex; the only way a proposal may name the front of a longer name, such as a pod's hash suffix).
  - Behaviour: grounding is a whole-token match and exact in case (`payments` is not found in `payments-canary`, `admin` not in `Admin`); a validator crash or an evidence-store outage is `evidence_unavailable` with no `caught_by` (it was `invalid_proposal`/`guard`); redaction patterns are bounded (bounded polynomial time, see README) and tool results are cut to twice their cap before redaction; hosts are resolved once, refused if they resolve to loopback, link-local, unspecified, multicast or reserved addresses, and the connection goes to the checked address (DNS rebinding, in process; K7 stays the backstop and is a hard prerequisite before any pilot); the Kubernetes probe accepts `create` only on the three self-review resources and treats an empty or status-less answer as not proven; a bearer token never travels over plain http; a tool secret under 6 characters is refused; the gate's decide event carries `restored_hash` and every tool event carries `output_hash` and `rows`; `forbidden_host` normalises trailing dots, case and non-ASCII and knows more metadata names.
- **K5-core, placeholder look-alikes and decoded views.** `redact_untrusted` escapes markers and placeholder look-alikes in every decoded view; redacted text is cleaned of lone surrogates last and a document that cannot encode is an abstention; tooled agents need `additionalProperties: false` contracts and an undeclared input is `invalid_proposal`; the pin refuses relative imports and parent `__init__.py` with code, and a cached module must carry the same digest; `caught_by=guard` now also covers `uncited` and `invalid_proposal` (not `guard_unavailable`); a failed step is due again at the next tick; a source endpoint obeys the manifest host rules; fetch resolves a hostname once and connects to the checked address; K7 network policy is still required).
- **K5-core, evidence migration, retention keys and tool pins.**
  - The evidence migration is `0006_evidence.sql` (the number follows the reservations migration that ships before it); it was never released under another name, so no database needs renaming except a development one (see the upgrade steps).
  - New key `retention.held_tool_calls_max_days` (400): held runs' tool calls now have their own ceiling, and the two 400-day ceilings run before the hold hook, so a failing hook cannot stop them.
  - `tool_module_hashes` are checked BEFORE any tool module is imported (a mismatch or a missing pin in pilot and prod raises `ConfigError` with nothing imported); the pins are part of the agent's config hash.
  - Every non-boolean action input must say `identifier: false` (or `true` on a string); `evidence.cluster_suffixes` must end in a private label; a Kubernetes `api_url` is scheme and host only; `sources=` objects are refused in pilot and prod.
  - A run parked in NEEDS_PERSON no longer keeps its redaction map past the ordinary retention (it cannot move again).
  - `caught_by` is now set only when a control stopped a proposal (`ungrounded`, `run_budget`, `injection_suspected`, `uncited`, `invalid_proposal`); a tool, redaction or evidence failure sets none.
- **K5-core, config and wiring.**
  - **Run `hadavin-sdk migrate` with the runtime role granted** (`--runtime-role`) **before** starting the new image: the evidence migration (`0006_evidence.sql`) adds `tool_calls` (with an `error` column) and `redaction_maps`; without the grants the runtime cannot write them.
  - New `config.yaml` keys (defaults in `hadavin_sdk/defaults.py`; units as named): `tool_modules`, `tool_timeout_s` (seconds, 10; one deadline for a whole tool call), `tool_module_hashes` (SHA-256 of each tool module's source file; required in pilot and prod), `executor_timeout_s` (seconds, 10; demo executor), `scope_inventory` (`"<page>#<anchor> sha256:<64 hex>"`, format-checked only), `sources` (`kind`, `settings`, `token_secret_name`, `ca_file`; built and probed at start-up), `retention.tool_calls_days` 30, `retention.redaction_maps_days` 30, `retention.hold_labelled` true, `retention.held_maps_max_days` 400 (at most 400 and at least `redaction_maps_days`), `retention.purge_every_s` 86400, and an `evidence` block: `max_tool_errors` 3, `legacy_max_output_bytes` 20000, `fetch_ceiling_bytes` 2097152, `https_ports` [443], `cluster_ports` [80, 8080, 9090, 9093, 3100], `cluster_suffixes` ['.svc.cluster.local', '.svc'], `stored_kinds` (may narrow the default, never widen it; UUID is not stored), `max_tool_calls_per_run` 40, `max_tool_bytes_per_run` 262144, `max_abandoned_tool_threads` 8.
  - Tool manifests (`tools/<agent>.yaml`) gain `ports`, `options`, `ca_file`, `ca_secret_name`; an agent with a manifest must mark every string input of its actions `identifier: true` or `identifier: false`; hosts may not be IP literals, loopback or metadata names; `cluster_http` needs every host in-cluster. A tool with a credential, or one that reads a configured kind of source, needs a `scope_inventory` entry `tool:<name>` or an explicit mapping (`options.source`) to a probed source whose token secret is the tool's only secret and whose host is one of the tool's `hosts`.
  - `app.build(..., hold_run_ids=)` wires the held-run hook (a retention-hold feature supplies it); a hook that raises stops that tick's purge, loudly. A hold is not retroactive. `tools=` (plain callables) is refused in pilot and prod.
  - `evals.gate` now matches by subset (expected inputs must match, extra optional inputs are allowed) and offers a tooled agent's actions with the required `evidence` field, as the runtime does.
  - Behaviour changes to know: a redaction fault is an abstention (no `caught_by`), a store fault while keeping evidence is `evidence_unavailable`; the model now sees its own tool-call arguments in later steps; text sent to the model is no longer rewritten except for placeholder-shaped literals and result markers.
- **K5-core: read-only evidence, redaction before the model, tool wiring.** Needs `hadavin-sdk migrate` (new
  the evidence migration (`0006_evidence.sql`): tables `tool_calls` and `redaction_maps`; the runtime role gets SELECT, INSERT on
  `tool_calls` and SELECT, INSERT, UPDATE on `redaction_maps`; only the purge role deletes them (rounds 8 and 10); the portal role reads neither). Run it
  before starting the new image; a custom `Store` must implement the six new methods.
  - **The document and every tool result are now redacted with the run's one map before the injection check and
    before the model** (`guard/runmap.py`). Placeholders (`<EMAIL_1>`) appear in plans; real values are restored
    only for tool arguments, for the gate's schema check (`authorize(..., inputs_view=)`, new denial
    `input.unresolved`) and for the demo executor (`Executor.execute(..., inputs_view=)`). Only identifier kinds are
    stored; secret and regulated kinds are never stored or restored.
  - **Recorded model answers (`FakeLLM`) and `evals.gate` are keyed by the redacted document.** Re-record any
    fixture whose document holds an email, a phone number or another redactable value (the two repo fixtures were
    re-recorded: `pii.txt`, `injected.txt`). `config_hash` is unchanged for agents without a tool manifest.
  - New `tools/<agent>.yaml` manifests (read tools only; `side_effect: none`), `Config` keys `tool_modules`,
    `tool_timeout_s`, `retention` (`tool_calls_days` 30, `redaction_maps_days` 30, `hold_labelled` true,
    `held_maps_max_days` 400, at most 400) and `scope_inventory`. A manifest is part of `config_hash` (a changed tool
    needs a new gate run); a tooled agent with a manifest must not share a tool secret with a backend or an
    executor.
  - A tooled agent's action tools now require an `evidence` list of call ids (`call_id = "<run_id>:<n>"`); an
    empty or foreign list ends the run `NEEDS_PERSON uncited`, and an input the contract flags `identifier: true`
    (new schema keyword, string properties only) that is not found in the cited results or the incident ends it
    `ungrounded`. `evals.gate` ignores `evidence`. A tool's exception is now a result (`ERROR: ...`) and the third
    one in a run ends it `tool_error`; a run whose cost reaches `max_run_usd` ends `run_budget`.
  - New tick step `purge_evidence` (daily). New `hadavin_sdk.sources` (four read-source interfaces, the neutral
    `KubernetesSource`, the start-up scope probe) and `app.build(sources=)`: a source that fails its probe, or
    cannot be probed and has no `scope_inventory` reference, stops the process starting.
  - The no-redirect HTTP opener moved to `guard/http.py`. **`make`, `hosts` and `Deps` now live in
    `hadavin_sdk.backends.factory`** (`hadavin_sdk.backends` itself imports nothing): change
    `from hadavin_sdk.backends import make` to `from hadavin_sdk.backends.factory import make`.
  - Review round: a tool module's `READ_OPERATIONS` is now a mapping operation id -> `(METHOD, path regex)`, and
    `ToolContext.fetch` refuses a call that fits neither; the manifest gains `ports` (default 443, in-cluster
    set for plain http), `cluster_http` needs every host in-cluster, and a tool with `secret_names` needs a
    `scope_inventory` entry `tool:<name>`. `tool_timeout_s` is one deadline for the whole tool call. Tool results
    that failed are stored with `error = true` (in the evidence migration) and cannot be cited. Literal
    placeholder-shaped text in a document or tool result is escaped (`‹IPV4_2›`) before redaction. The ARN pattern
    stops at `?`, `&` and `#`; the stored map drops any original that holds secret-shaped text. Redaction maps of
    runs that have not ended are kept until the 400-day ceiling (`purge_redaction_maps(..., keep_open=)`).
- **K3 pilot build path (levels, shadow cut-off, fail-closed loading).** Action contracts change shape:
  `executor.system` moves to a contract field `target_system`, and `executor` is now a tagged union
  (`kind: none | manual | http`). Edit every contract: move `system:` out of `executor:` to `target_system:` beside
  it. `chain_id` and `verify_check` may be omitted for `none`.
  - **`config_hash` changes once** (the contract dump changed): every agent needs ONE new gate run
    (`hadavin-sdk gate <agent>`). A level flip (`levels`) never changes the hash.
  - **A tooled agent (`tools_allowed` not empty) now needs a gate run with `--k 3` that passed pass^3**; a k = 1
    green record no longer qualifies it. Non-tooled agents are unchanged.
  - New optional agent fields `levels` (per action: `shadow` or `suggest`; `act` is refused until Phase 4) and
    `max_run_usd`. In `pilot` and `prod` both are required and `levels` must list every `scope_allowed` action;
    `suggest` is refused there until K6 and K8, an `http` contract and a `read_only` contract are refused, and so are
    `confidential` and `restricted` agents. See `deferred.py` for every refusal and the phase it arrives in.
  - In `pilot` and `prod`, `build` makes no `Executor` and reads no client-system secret. `build` takes a new
    `llm=` override.
  - Shadow and abstain cards are posted through the new `Channel.post_card` (and `Channel.max_card_chars`); a
    custom channel kind must implement both. `AuditEvent` gains `caught_by`.
  - New file `replay-records.jsonl` (reader only for now; the writer arrives with K1b-full). A tooled agent at
    `suggest` is refused at load without a green record in it for the current config hash, model and prompt.
    **Shadow qualification through the gate is a start-up gate, not accuracy evidence.**
- **K1b-lite replay check (report only).** New commands `hadavin-sdk replay AGENT --bundles D --cause-list D
  --max-usd X --out OUT [--k K]` and `hadavin-sdk score --outputs OUT --answers F --cause-list D --bundles D`.
  Neither gives a met / not met verdict; a replay pass is not evidence of live accuracy.
  - New optional `k1b:` section in `config.yaml` (`max_steps` 12, `max_tool_calls` 20, `case_timeout_s` 300).
    It does not change `config_hash`, so no agent needs a new gate run.
  - `replay` and `score` write `k1b` audit events (`replay_run`, `hard_check_a`, `hard_check_b`, `score_run`) to the
    configured `local_dir` or `chain` audit. A `chain` over the memory store warns that events are lost at exit.
  - `replay` refuses a non-empty `OUT`, a route with a zero price (unless the llm kind is `fake`) and a bundle with
    any timestamp after the alert time. A run that dies half-way leaves `FAILED.txt`; delete the folder to re-run.
  - **Exit codes of every command changed for crashes.** `main` now returns 2 for a `ConfigError` (message on
    stderr) and 3 for any other uncaught error, instead of a Python traceback with exit 1. Exit 1 keeps its meaning
    (gate red, audit not intact, replay aborted or cost cap reached).
- **K1b-lite masks client data before the model.** Until now `replay` ran only the injection screen: the alert,
  every tool result and the runbooks went to the model raw. Every text value of a case bundle is now masked with
  the studio redactor (`guard.redact.redact_many`, one placeholder namespace per case, so one value is one
  placeholder everywhere) before the model or the injection screen sees it. The placeholder map lives in memory
  only: it is never written to the outputs or the audit sink, and never logged. Evidence IDs, file names, the
  the values of the `service`, `kind` and `fault_type` keys (the Cause List vocabulary), exact timestamps and numbers
  are left alone; dict keys are masked too. Names, queries and labels are masked in the snapshot and in what the model
  sees alike, so citations and queries still resolve. New `k1b.redact` (default `true`); `false` is refused unless `replay` gets
  `--i-know-data-is-already-masked`, and the run records `redaction.mode: off_acknowledged`. `run.json` records the
  scheme and the number of distinct values masked per class (no values); both reports print them. **What the
  redactor does NOT catch:** names in free text, customer or project names, ticket numbers, unusual formats,
  most company or cloud host names (it masks `.local`-style hosts, not `api.client-bank.com` or `*.rds.amazonaws.com`),
  and the values of the `service`, `kind` and `fault_type` keys. It is a strong first filter, not proof that no client data leaves; the
  reports say so under "What the numbers cannot say". Re-run `replay` for earlier runs: they sent data unmasked.
- **K1b-lite: a `not_sure` answer may omit `causes`.** A real Sonnet 5.5 smoke run abstained correctly on a
  no_evidence incident with `{"not_sure": true, "reason": "..."}` and the strict parser called it unreadable (a Miss).
  `causes` may now be omitted (or empty) only when `not_sure` is true; every other strictness is unchanged (both
  forms, no form, wrong types, extra keys, fenced or surrounded text, duplicate keys, NaN). The `submit_diagnosis`
  schema no longer lists `causes` as required and its description, and the system prompt, say so. Case files now
  record `answered_via` (`tool` or `text`), and `run.json`, `replay-report.md` and `score-report.md` list the case
  ids that were unreadable, errored, timed out, capped or converted for uncited evidence (ids only, never answers).
  Re-run `replay` for runs made before this change: their saved unreadable answers are not re-parsed.
- **`tick` now matches the v5 contract.** Exit code **4** (was 3) when the store is unreachable, for both
  `run_tick` and the CLI; 3 stays the wrapper code for any other uncaught error. The heartbeat summary line is no
  longer a step: it is logged after the steps, writes no `tick_state` row and cannot change the exit code (K7 sends
  the external heartbeat is PENDING K7: nothing sends it today). **A scheduler that treated exit 3 as "store down" must now watch 4.** `tick` also returns 4 when the store stops answering during the steps (it re-probes after a step failed); 1 stays for a failed step with a reachable store. Exit 4 is only for connection failures: a store that answers with a missing table or grant exits 2 ("run migrate, check grants") for `tick`, `limits stop` and `limits reset`. `limits stop` and `limits reset` with the store unreachable now exit 4 (was 2) and print "kill switch NOT set" or "NOT reset" with "Nothing was changed".
- **K1b-lite gap fixes.**
  - SDK version is now `0.1.0` (`pyproject.toml` and `hadavin_sdk.__version__`, pyproject and `__init__` kept equal by a test). Replay and
    score reports print it; `0.0.0` still prints "unreleased build".
  - `replay`: every provider call has a wall-clock bound (the time left in `k1b.case_timeout_s`, at least 1 s),
    for every llm kind: the call runs in a worker thread and, on expiry, the case ends as `timeout` with stop
    reason `call_timeout`, the worst-case cost of that call is charged to `--max-usd`, and the whole run stops
    as `aborted` (exit 1), so at most one abandoned call exists per invocation. The abandoned call is not killed;
    it can outlive the run (a slow trickle defeats a socket timeout). Next step, only if a client run ever shows a hung call: run each case in a child process that can be killed. The per-socket timeout is already
    `call_timeout_s` on each llm kind's settings (`backends.llm`). Ctrl-C during a replay now also leaves `FAILED.txt`.
  - `score` audit order changed: `score_report` `started` (intent, before anything is written), the report file,
    then `score_report` `written` and one `score_run` per run (these append like any K1b event: a failed append exits 3 with the report on disk). A report that cannot be written
    leaves `started` then `failed` (with the error class) and no `score_run`; the command exits 3.
- **Audit and lock-in guard gaps.**
  - Anchors and checkpoint rows carry a non-secret `key_label` (new optional `key_label` setting on every
    signer kind; default `pk:` plus a fingerprint of the public key), never the configured `key_id`. An alias and
    an ARN of one key give one label and no account id reaches the anchor bucket. **Anchor bodies written by
    the previous build hold `key_id`; the offline verifier accepts them but never compares or prints it (it can be an ARN).** A custom anchor kind must
    now accept `alg` and `key_label` keywords (one taking `alg`/`key_id` is treated as a legacy 3-argument anchor
    and warns).
  - `verify_anchor_bodies(bodies, public_key, names=None, assume_alg=None)`: `names` binds each object name to
    the seq inside it; `assume_alg` verifies pre-`alg` anchors by signature (a wrong guess fails every
    signature). The immutable objects are not rewritten.
  - **Upgrade step: run `hadavin-sdk migrate`** (0004 adds `alg` and `key_label` to `audit_checkpoints`; old rows
    are NULL, meaning "not recorded": verify then uses the configured signer's scheme). A runtime started before migrating refuses with the "run migrate" hint.
  - Lock-in guard: the literal scan now also covers bytes constants, constant `+` joins and f-strings (it found
    `".meta" + ".json"` written to dodge it; that suffix is now a plain literal and the model-id pattern
    matches `meta.llama` only); every `neutral` kind must show no vendor SDK import (S3 anchor excepted, with
    `endpoint_url`) and a `Neutral protocol:` line in its module docstring.
  - Vault licence check, live 2026-11-01: HashiCorp Vault 1.15 and later is BSL 1.1 (change date four years after
    each release, then MPL-2.0); OpenBao is MPL-2.0 under the Linux Foundation and states API compatibility with
    Vault 1.14 (Transit has extras of its own). The `vault` and `vault_transit` kinds stay `neutral` because they
    speak the Vault-compatible HTTP API that OpenBao also serves, but neither has been run against OpenBao by us
    (they stay `unverified`); the docstrings say so.
- **Lock-in guard.** `tests/test_lockin_guard.py` fails CI when a vendor SDK is imported outside its kind
  module, a capability lacks a neutral prod kind (`Entry.neutral`) and two prod kinds without a dated
  exception, or core logic names a vendor.
  - Anchor objects now carry `alg` and `key_id`, so `chain.verify_anchor_bodies(bodies, public_key)` checks
    them with nothing else. A custom anchor kind's `put` must accept `alg` and `key_id` keywords. Anchors
    written before this change have no body fields and verify only through `verify()`.
- **P5/P6 follow-ups.**
  - **Re-gate every agent once.** `golden_sha256` now covers the input documents the golden cases point at,
    so a changed document un-qualifies.
  - `config_hash` now also holds `eval_threshold` (when not 1.0), `max_completion_tokens` and the Foundry
    `resource`.
  - `eval_threshold: 0` is refused.
  - A `bedrock_guardrail` must name a published `guardrail_version` (digits; `DRAFT` can change).
  - A detector `threshold: 0` is refused (it flagged every clean text).
  - A `bedrock_guardrail` needs `bedrock:GetGuardrail`. Start-up refuses a guardrail with no PROMPT_ATTACK
    input filter switched on.
  - Moving model aliases are refused per kind:
    - OpenAI names with no dated snapshot (`gpt-4o`, `o3`);
    - untagged names on a local OpenAI-compatible server (Ollama: `llama3` means `:latest`);
    - Gemini names with no version (`gemini-pro`);
    - Bedrock names without a provider prefix.
- **Rewrite config.yaml to config v2** (slice 2 P1b). `environment: dev|pilot|prod` is required. Each backend
  is `backends.<capability>: {kind: <name>, ...settings}`. The old top-level keys are refused with a message
  naming the new place: `audit_dir` -> `backends.audit.dir`, `recorded_dir` -> `backends.llm.recorded_dir`,
  `detector_threshold` -> `backends.detector: [{kind: regex, threshold}]`, `region` -> each AWS kind's
  `region`, `slack` -> `backends.channel`. Start-up now refuses dev-only kinds outside `dev`, a secret name used
  by both a backend and an action, and any secret that cannot be read.
- `app.build(config_dir, agents, *, secrets=None, ...)`: `secrets` is now a keyword; `make_llm`,
  `make_detector` and `make_channel` are gone (backends are built from the table in `hadavin_sdk.backends`).
- **Re-gate every agent once** (slice 2 P1a). `config_hash` now hashes with `exclude_defaults` and includes the
  llm backend kind, so every stored green gate run stops matching. Run `hadavin-sdk gate <agent>` for each agent
  before starting the runtime; until then start-up raises `Unqualified`. After this one re-gate, adding an optional
  field with a default no longer un-qualifies agents, and swapping the llm backend does.

### Added
- **G4 command withholding** (P5/P6 follow-ups). `channel.clean` now withholds every command a person could
  paste to change a system: `[command withheld (G4)]` stands in its place.
  - It covers AWS, gcloud/gsutil/bq, az, azcopy and PowerShell Az, kubectl/oc, helm, terraform/tofu/pulumi,
    ansible, systemctl, docker/podman, git, gh/glab, psql/mysql/mongosh/redis-cli, SQL write statements,
    `rm -rf` and `curl | sh`.
  - It fails closed: a CLI command passes only when it is positively read-only. The WARDEN port was dead code
    and AWS/K8s-only.
- `backends.hosts(entries)`: the hosts the configured kinds connect to, as a suggested egress list.
  The Postgres store is not in the list: its address sits inside the secret DSN, so add the database host by hand.
- **No single-dependency detector.** `llm_judge` runs on any llm kind, a local open-weights model on
  `openai_compat` included, so the cloud-neutral production detectors are `regex` + `llm_judge`.
  `bedrock_guardrail` is AWS-only. The approval-summary screen runs without the judge: no agent can be
  charged there, and the judge already screens the document and tool output.
- `hadavin-sdk tick` (slice 2 P7, v5 contract): one pass of isolated steps (`sweep`, `reconcile`, `stuck`,
  `checkpoint`; the summary line is logged after them and is not a step); a failing step is logged and recorded in `tick_state` and the others
  still run. Exit 0 ok, 1 a step failed, 2 config error, 4 store unreachable. Later steps are appended to
  `runtime.tick.STEPS`.
- `slack` approval channel (`backends.channel: {kind: slack, channel_id, signing_secret_name,
  bot_token_secret_name}`) and `approvals/receiver.py`: verified clicks are recorded only; `tick` runs the plan.
- Migration `0003_approvals_tick.sql`: `approval_requests.sent_at` and `channel_ref` (a failed send is resent
  by `tick`), one decision per approval step, an exact month spend counter, the kill switch row (a missing row
  reads as ON), `tick_state`.

- `postgres` store (`pip install hadavin-sdk[pg]`, slice 2 P2): `backends.store: {kind: postgres,
  dsn_secret_name, iam_auth, region}`; compare-and-set in SQL; RDS IAM login with `iam_auth: true`.
- `hadavin-sdk migrate [--runtime-role R]`: forward-only schema (`store/migrations/0001_core.sql`) applied under
  an advisory lock with the migration role's DSN from `HADAVIN_MIGRATE_DSN`. Rollback = restore the snapshot
  taken before migrating.
- `hadavin-sdk limits stop|reset` now works on a shared (postgres) store.
- llm kinds (slice 2 P5, all `slice2-unverified` until the P9 live run): `anthropic` with `platform: api |
  vertex | foundry` (extra `anthropic`), `bedrock` through Converse (extra `aws`), `openai_compat` (OpenAI,
  Groq, OpenRouter, a local Ollama) and `gemini` over stdlib HTTP. Each has `call_timeout_s` (60) and
  `max_attempts` (3): transient failures retry with exponential backoff and jitter, then `ProviderExhausted`.
  `output_schema` is a forced tool call. Model ids that are moving aliases (`sonnet`, `*-latest`) are refused.
  The llm `platform` and `base_url` are part of `config_hash`.

- Detector lists (slice 2 P6): `backends.detector` takes one or more entries (an `llm_judge` never alone); every
  entry runs and any flag flags the run (max score, the flagging names joined by `+`, the first flag's reason).
  New kinds, both `slice2-unverified`: `llm_judge` (`route`, `threshold` 0.7; a fixed prompt hashed into
  `config_hash`, its cost charged to the agent, qualified at its own rate by a non-empty `golden_dir/judge.jsonl`
  in the evals gate; that file is part of `golden_sha256`) and `bedrock_guardrail`
  (`guardrail_id`, `guardrail_version`, `region`; the PROMPT_ATTACK filter, extra `aws`).

### Changed
- P5/P6 follow-ups:
  - limits are checked again before a tool output is screened, so a reply that spent the budget never pays
    for a judge call;
  - redaction masks GCP `projects/<id>/...` paths and Azure `/subscriptions/<uuid>/...` ids, and ARNs with no
    account (`arn:aws:s3:::bucket`) or in the `aws-cn` and `aws-us-gov`
    partitions;
  - `llm/retry.py` names no vendor: each llm kind says which of its SDK's errors are retryable.
- Postgres TLS (slice 2 P7): `verify-full` by default for any non-local host, with the server's CA bundle
  from `sslrootcert` (a file) or `sslrootcert_secret_name` (a PEM in any secrets backend); an explicit weaker
  `sslmode` is a dev opt-down. With `iam_auth` only `verify-full`/`verify-ca`, and a runtime DSN with a
  password is refused.
- The runtime role gets SELECT, INSERT only on `approval_decisions`, `dead_letters`, `gate_decisions`.
- Gate decisions are written once per run; a run stuck in `RECEIVED` or `PLAN_READY` can go to `NEEDS_PERSON`.
- Approver ids carry the channel kind's name (`slack:<id>`, `fake:<id>`); request signing is the shared
  `approvals/hmac_v0.py`, not borrowed from Slack.
- `ProviderExhausted` from the model ends the run in `NEEDS_PERSON provider_exhausted` instead of escaping.
- A provider that refuses the request (`ProviderError`, e.g. a bad key) ends the run in
  `NEEDS_PERSON provider_error`; `ProviderExhausted` is now a `ProviderError`.
- `Reply.stop_reason` is one of `end_turn`, `tool_use`, `max_tokens`, `refusal` for the network kinds. A reply
  cut off at the output cap or declined ends the run in `NEEDS_PERSON llm_max_tokens` / `llm_refusal` instead
  of `NO_ACTION`; a cut-off reply's tool calls are dropped (their input may be incomplete).
- Store: `get_approval_decision`, `list_approvals`, `list_runs`, `touch`, `spend_totals`; `add_cost` raises
  `NotFound`; `Limits.blocked` no longer writes a zero-spend row.
- The executor calls a heartbeat before every HTTP attempt, so long retries do not look stuck.
- `Verdict.score` is bounded to 0..1; a detector failure is logged with its cause (still fails closed).

### Added (slice 2 P3, every kind `slice2-unverified` until the P9 live run)
- `backends.audit: {kind: chain}`: WARDEN's hash-chained, append-only audit in the store's database, signed
  checkpoints every `checkpoint_every` rows, and an optional `anchor: {kind: s3_object_lock, bucket, region}`
  (GOVERNANCE, 1 day by default). `hadavin-sdk audit verify` exits 0 intact, 1 not intact,
  2 refused (a memory store lives in one process), 3 unreadable.
- `backends.signer`: `none` (default), `ed25519_local`, `aws_kms`. Start-up signs a probe message.
- Environment table: prod refuses `ed25519_local` and a chain without an anchor that has `retention_ack: true`;
  COMPLIANCE mode only in prod with `retention_ack`.
- `store/migrations/0002_audit_chain.sql` (applied by `hadavin-sdk migrate` with the postgres store).

### Added (slice 2 P4, `slice2-unverified` until the P9 live run)
- `backends.secrets: {kind: aws_secrets_manager, region, ttl_s: 300}`: values cached for `ttl_s` (0 = no
  cache), a missing secret is a `ConfigError` at the start-up probe, values are never logged.
- `backends.secrets: {kind: env, prefix: HADAVIN_SECRET_}` (dev only): `fixture-token` reads
  `HADAVIN_SECRET_FIXTURE_TOKEN`.

### Added (slice 2 P4b, `slice2-unverified` until a live run): cloud-neutral secret stores
- `backends.secrets: {kind: vault, address, auth: token|approle|kubernetes, mount, path_prefix, field,
  namespace, ca_cert}`: HashiCorp Vault or OpenBao KV v2 over the standard library (no extra); TLS always
  verified, plain http only to this machine; a 403 signs in again once (approle, kubernetes).
- `backends.secrets: {kind: azure_key_vault, vault_url}` (`pip install hadavin-sdk[azure]`):
  `DefaultAzureCredential` (managed or workload identity).
- `backends.secrets: {kind: gcp_secret_manager, project_id}` (`pip install hadavin-sdk[gcp]`): Application
  Default Credentials (attached service account or workload identity), version `latest`.
- `backends.secrets: {kind: mounted_file, dir}`: one file per secret (Kubernetes Secret, CSI driver, External
  Secrets); paths stay inside the folder; on POSIX a world-readable file is refused (mount 0400/0440).
- Every remote kind shares one TTL cache with one refresh at a time; an empty value is refused at start-up.
  A missing `aws`/`azure`/`gcp` extra now always names the `pip install`.

### Upgrade steps (slice 2 P3b)
- **The anchor moved out of the audit entry.** `backends.audit: {kind: chain, anchor: {...}}` becomes
  `backends.audit: {kind: chain}` plus `backends.anchor: {kind: s3_object_lock, ...}` (default `none`).
- **Prod now refuses `signer: none` and `anchor: none`**, and `ed25519_local` with a key file (set
  `private_key_secret_name` instead). Config errors list every refusal at once.
- `migrate(dsn, password=...)` replaces `iam_auth=`/`region=`; build the helper with
  `hadavin_sdk.store.postgres.password_source(iam_auth, region)` (the CLI does).

### Added (slice 2 P3b, `slice2-unverified` until a live run): cloud-neutral audit
- `backends.anchor`: `s3_object_lock` (AWS S3, or MinIO / Ceph RGW through `endpoint_url`),
  `azure_immutable_blob` (version-level WORM; container checked at start-up), `gcs_retention_lock` (bucket
  retention policy checked; COMPLIANCE needs it locked). A put that finds the same bytes counts as anchored;
  different bytes are never overwritten.
- Signers: `vault_transit` (Vault / OpenBao Transit, ed25519, one pinned key version), `azure_key_vault_key`
  (ECDSA P-256 / ES256: Key Vault has no Ed25519), `gcp_kms` (EC_SIGN_ED25519). `ed25519_local` can read its
  key from any secrets kind (`private_key_secret_name`).
- `audit verify` also checks that each row's event id column matches its body.
- Cloud SDKs only in their kind modules: `audit/signer_aws.py`, `store/auth_aws.py` (RDS IAM).
- `mounted_file` also refuses group- or other-writable files and checks the opened file (no stat-then-read
  gap, `O_NOFOLLOW`); a Kubernetes JWT read error in `vault` is a `ConfigError`; the GCP secret fetch is bounded
  (5 s, no retry).

### Added (P1m, test tooling: the mutation runner and judge)
- `tools/mutation_runner.py` (a developer tool, not in the wheel) runs one mutant at a time on a temp copy of a package and
  judges the kill by its reason with `hadavin_sdk.testing.mutation` (in the wheel). They come with
  their tests (`tests/test_mutation_runner.py`, one test per guard) and their mutants
  (`tests/mutation_runner_mutants.py`, run with `uv run python tests/mutation_runner_mutants.py`). Changes after review: the tests work on Windows as well (`_pid_alive` asks the system library on Windows; a symlink is skipped only
  on Windows without the privilege, and a junction is used for the folder case); a mutant now names a distinctive fragment of the
  failing assertion message (not the killer's name) and the test it pins; the runner kills the run's whole process group on an
  interrupt (Ctrl-C) and after a normal exit, hands pytest an empty ini file and the copy as rootdir (a planted `pytest.ini` is
  never read), compares the exception class a crash row declares by its parsed leading name (not a substring), treats a baseline
  timeout of 0 as a timeout, and refuses a path with a `:`; the `mutation.py` comment no longer holds process words. Three
  `nosec` comments the scanner does not need are deleted.
  A SIGTERM or SIGHUP sent to the runner now ends it like Ctrl-C (the pytest tree is killed, the temp folders are removed; POSIX);
  after a normal exit the tree is killed on POSIX only (on Windows the pid may be reused); the temp folders are cleaned up when a
  path is refused; the mutants script exits 2 when its filter selects no mutant; `tools` is now also checked by bandit and
  Semgrep in CI.
  Review round 3 (P1m): the judge looks for `expect` in the first error line only (a fragment found only in the test id no longer
  counts; `pinned` ties a kill to its test). The runner waits for the pytest child without reaping it (`os.waitid` with `WNOWAIT`,
  POSIX; macOS has no `waitid` and keeps the old order) and kills the process group before the reap, so the group id cannot belong to
  another process. A SIGTERM or SIGHUP that arrives while the child is being started, while the tree is killed or while the temp
  folders are removed is held until that step is done (then raised), and once a signal has ended the run a second one cannot cut the
  cleanup short; the narrow window of a few instructions between a signal handler and the first line of the cleanup stays (stated in
  the module docstring), and SIGKILL still cannot be caught. A signal that was ignored on entry (SIGHUP under `nohup`, SIGTERM from
  a parent that ignores it) stays ignored. The ini file of a pytest run now lives in its own temp folder, no longer in the working
  folder. `FIRST_LINES` (a module global, not safe for two runs at once) is gone: pass `first_lines={}` to `run_mutants` and read
  it after the call. Tests: the helper tests no longer run a real `os.kill` or `os.symlink` under a faked platform (they failed on
  Windows); the rule "a test that fakes the platform fakes every OS call of that branch" is stated in the helpers docstring; the
  interrupt test kills its leftover process only after its assertions; the signal test starts the runner in its own session, kills
  the leftover pytest group, and resets SIGTERM and SIGHUP to the default first. Eight new mutants (49 in all).
  Review round 4 (P1m): a test path, fixture folder or mutant file that starts with `-` or `@` is refused (`ValueError`; write `./name`)
  where the paths are first checked and again where the pytest command line is built; the `--` marker is no longer relied on (on
  Python 3.12.3 `pytest -- -x` still takes `-x` as an option, and pytest reads `@name` as an argument file also after `--`). A relative
  symlink of the snapshot that points outside the tree is refused. `run_mutants` states that it is not re-entrant and raises
  `RuntimeError` on a nested call in the same thread (POSIX main thread). A leader that someone else already reaped is now known to
  its `Popen` object, so the group of a reaped pid is not signalled. The docstring lists all the module constants. CI runs the tests
  on Python 3.12 and 3.13. Tests: the liveness check of the background-process test polls against a deadline and names the state of
  a process that survives; the signal test ends a runner that never started its child with SIGTERM before it kills the leftovers; the
  refused-run test checks the shared folder after the first refusal. Five new mutants and one replaced (54 in all).
  Fix 1 (P1m, three review-4 Minors): (a) a Windows junction under `src` or a fixture folder is refused (`ValueError`) before the
  snapshot copy, because `shutil.copytree` follows a junction and copies its target as a real folder (`os.path.isjunction`, Python 3.12
  and later; where it is missing nothing is refused). (b) The refusal of a path with `:` now says "a path may not contain ':'" and the
  module docstring states the limit. (c) A pytest child that someone else reaped first (SIGCHLD ignored) used to come back as exit code 0,
  which the judge reads as a pass; it is now `REAPED_ELSEWHERE`: an ERROR row (`REAPED ELSEWHERE`) for a mutant, a `RuntimeError` for the
  baseline. Six new tests, eight new mutants (62 in all). Review 5 (order 40) added: a junction is also refused when it is the `src` or fixture folder itself or a part of the fixture path (`tests` in `tests/fixtures`); a reaped baseline is named as reaped; the Limits docstring now says that without `os.waitid` (macOS) a child reaped by someone else can still read as exit code 0, and that on the reaped-leader path descendants are not killed.
  A real Windows junction was probed by hand by the lead (not by this test, which patches `os.path.isjunction`; record: `handover/reviews/P1m-fix1-junction-probe.txt`). Run by the lead on Windows, Python 3.13.3, `mklink /J`:
  ```
  3.13.3 mklink rc 0
  islink False isjunction True
  is_dir True
  ```
  Also: `tests-py312` is named in the `ci.yml` header comment (no job or check name changed).
  The byte-copy hash of `tools/mutation_runner.py` changes (new value below): a repository that keeps a copy re-copies all four files listed at the end of this section, not this one alone.
- Note on the name: `tools/` is a top-level Python package called `tools`, a generic name. A repository that copies it and already
  has its own `tools` package or folder must merge or rename deliberately; the mutants script puts the repository root on
  `sys.path` so that `tools.mutation_runner` imports, and another `tools` earlier on the path would shadow it.
- Every repository that keeps a byte copy of these files re-copies the four of them in one commit and updates its pins to the
  sha256 values below (also pinned in `tests/fixtures/mutation_manifest.json`):
  - `src/hadavin_sdk/testing/__init__.py`: `3c77d034fe2a1ee70adea0d0bd259a20edda397d8ebd55a0e40b63e5c21c9e1c`
  - `src/hadavin_sdk/testing/mutation.py`: `3489a198d41db0306826cffcb1813a40ecc7e985c6a7da4885ba656bf351d3c4`
  - `tools/__init__.py`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
  - `tools/mutation_runner.py`: `d9543b75fca9c185698f015a2b1e8402207d52014a650a235a050107663028e7`
