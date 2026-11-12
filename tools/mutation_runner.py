"""A small mutation runner: put one deliberate bug at a time into a temp copy of a package and judge the kill by its reason.

Words used in this text. A *mutant* is one deliberate bug: one text of one source file replaced by another. A mutant is *killed* when a test
fails because of it. The *child* is the pytest process the runner starts. The *first run* is the run of the tests on the copy without any bug.

``run_mutants(root, mutants, ...)`` takes ONE snapshot of ``root/src`` (and the listed test files and fixtures) when it starts. An edit of
``root`` during the run never leaks into a later mutant. For EACH mutant it copies the snapshot to a temp folder and replaces every occurrence
of ``old`` by ``new`` in one file. It then runs pytest on the targeted tests with a JUnit file (the result file pytest writes) and judges the
failing test with ``testing.mutation.judge_report``. A mutant counts as GOOD only if the verdict is KILLED, or CRASH when the mutant sets
``allow_crash`` (a crash with the exception class named in ``crash_type`` is the intended reaction). The first run must pass (otherwise every
kill is meaningless). Stdlib only; runs pytest through ``sys.executable``.

What the tests can reach. The runner limits the child's ENVIRONMENT VARIABLES only: the child gets a fixed short list of variables plus the
names given in ``pass_env``. The runner does not fence off files or the network. ``HOME`` is inherited, so the tests can read any file of the
user who runs them: database password files and client certificates (``~/.pgpass``, ``~/.postgresql/``), cloud credential files, SSH keys.
Run it under an account that holds no real credentials.

Why we wrote code: ready-made mutation tools cannot say why a mutant died. ``pytest`` itself runs the tests, and tools such as ``mutmut`` change
whole files without a judged reason and without a named killer test. No no-code tool fits a developer check. So this is thin code around
``pytest`` and the judge. The product's redaction (``guard.runmap.redact_text``) was read and not reused for hiding the address: it finds
secret-shaped text by pattern, not one given value, and it would tie this tool to the product module (other repositories copy the tool byte for byte).

This is a developer tool, not a runtime module: it lives in ``tools/`` (NOT in the installed package, not under ``src``). A repository that keeps
its own copy copies FOUR files byte for byte, in one commit: ``tools/__init__.py``, ``tools/mutation_runner.py``,
``src/hadavin_sdk/testing/__init__.py`` and ``src/hadavin_sdk/testing/mutation.py``. Their sha256 values are in
``tests/fixtures/mutation_manifest.json`` and in the CHANGELOG. A repository that installs the SDK as a package already has the two ``testing``
files. It copies the two ``tools`` files and sets the SDK version it installs to the commit it copied them from; it keeps two sha256 values, for
the two ``tools`` files. The runner does not start with an older ``mutation.py`` (it imports ``judge_report`` from it). The tool imports only
``hadavin_sdk.testing.mutation``.

The runner starts a subprocess on trees the caller chooses, so it refuses these before anything runs:

- A mutant file that is not in the tree. The file is found by LISTING the tree: the caller's text is compared with the listed names and never
  joined to a path.
- Any other path that leaves its tree: a ``..`` part or an absolute path is a ``ValueError``.
- A path that starts with ``-`` or ``@``. pytest would read it as an option or as a file of arguments, also after ``--``. Write ``./name``.
- A relative symbolic link of the snapshot that points outside the tree.
- A Windows junction (a folder link that the copy would follow and copy as a real folder) in ``src`` or in a fixture folder, as one of those
  folders, or as a part of its path. This check needs Python 3.12 or later and finds nothing off Windows.

Every pytest run has a timeout, and a timeout stops the whole process tree of the run.

The limit on names: a path may not contain ':' (a Windows drive or an NTFS stream name), so a file or folder whose name holds a colon cannot be named to this tool at all, on any system.

Windows and macOS. The runner has not been run on Windows or macOS at this version; CI runs Linux only. What this text says about Windows
and macOS is written from reading the code, not from a run. ``mypy --platform win32 tools/mutation_runner.py`` reports 14 errors at this version (measured in round 27 by running the repo test with mypy 2.4.1 added for that run only, on Python 3.12 and 3.13; the repo test is skipped where mypy is not installed): 13 are POSIX-only functions and constants (``getuid``, ``O_DIRECTORY``, ``O_NOFOLLOW``, the ``waitid`` constants, ``killpg``,
``SIGKILL``) and 1 is the missing type information of ``hadavin_sdk.testing.mutation`` (the one error that Linux shows too; where the package
is not installed it reads "cannot find"). The file does not call ``os.fchmod``: mypy does not know it on Windows before Python 3.13, so the
count would be 15 on 3.12. CI does not run the mypy count: mypy is not in the locked test environment (adding it to the lock file is a separate decision of the owner: a
plain ``uv lock`` of this tool chain also rewrites the format revision and the platform markers of ``uv.lock``, so it is not a plain addition). What CI does run is the table test of the keyword
test file, which counts the places of the POSIX-only names in this file (13 places, plus the one import error). A test of the same file runs mypy itself and compares
(it is skipped, with its reason, where mypy is not installed; on a developer machine, install mypy 2.4.1 and run it).

Limits, stated plainly. Stopping the process tree reaches the processes that stay in the run's process group (POSIX) or the parent chain
(Windows ``taskkill /T``). A test or mutant that starts a process in a NEW session (``setsid``, ``start_new_session=True``) or, on
Windows, a process whose parent has already ended, escapes it. The mutant runner does not use a Windows Job Object (one would
reach those processes). After a normal exit the group is stopped once more, so a leftover background process of a finished run
does not outlive it (POSIX only; on Windows nothing is stopped after a normal exit: the parent is gone, ``taskkill /T`` cannot
find the children, and its pid may already belong to an unrelated process).

A SIGTERM or SIGHUP sent to the process that runs ``run_mutants`` is turned into ``SystemExit(128 + signal number)`` for the length of the
call (POSIX, main thread). So the same cleanup as for Ctrl-C runs: the pytest tree is stopped and the temp folders are removed. A signal that
was ignored on entry stays ignored (SIGHUP under ``nohup``, or a SIGTERM that the parent set to ignore). The old handlers are restored
afterwards. While the cleanup runs and while the child is being started, a termination signal is remembered and raised when that step is
done. Once one signal has ended the run, a further one is remembered and dropped, so a second signal cannot cut the cleanup short. What stays
open: a signal in the few bytecodes between the handler and the cleanup's first line is held only by the "one signal already ended the run"
rule. SIGKILL cannot be caught, and then the temp folders (``mutants_*`` and ``mutant_ini_*`` in the temp directory) stay.

On POSIX the run's process group is stopped while its leader has ended but is NOT yet reaped (``os.waitid`` with ``WNOWAIT``), so the
group id cannot belong to an unrelated process by then. Where ``os.waitid`` does not exist (macOS) the leader is reaped by ``wait``
first and stopping the group after a normal exit has the old, tiny pid-reuse risk.

Two more limits of the "reaped by someone else" case (SIGCHLD ignored, or a stray ``wait``). (a) Where ``os.waitid`` does not exist
(macOS) the run is waited for with ``proc.wait``, which cannot tell a reaped child from one that exited with status 0, so such a child
can still read as exit code 0 there: the ``REAPED_ELSEWHERE`` result exists on platforms with ``os.waitid`` only. (b) On the reaped-leader
path the group is NOT stopped (its leader's pid may belong to another process by now), so descendants the child left behind keep running.

pytest runs with ``--noconftest`` and with an empty ini file on purpose (a planted file in a parent folder is never read), so a
``pyproject.toml`` / ``pytest.ini`` is never read and, by default, no ``conftest.py`` is loaded. Five optional keywords of ``run_mutants``
cover tests that need more. ``forbid_skips`` switches itself on when you list a name in ``pass_env``; ``throwaway_hosts`` and
``shown_classes`` only matter with ``pass_env``:

- ``conftest="tests/conftest.py"``: a file of the tree (copied like a test file) that every pytest run loads as a plugin (``-p``). Its path is
  made of plain ASCII identifier parts and ends in ``.py``. No part may be a Python keyword, so ``class/conftest.py`` is refused. The file is
  called ``conftest.py`` or lies in a folder called ``tests``; any other tree file, such as ``src/pk/core.py``, is refused. It replaces
  ``--noconftest`` for that one file only; no other conftest is read.
- ``pass_env=("HADAVIN_TEST_PG_DSN",)``: names of environment variables of the caller that the child also gets. It gets them in the first run,
  in every mutant run and in every canary run (the first run repeated after a mutant, see below). Words used below: a *passed variable* is a
  variable whose name is listed here; its *address* is the whole text of that variable (the database address, a login and a password in it
  included); a *replacement text* is a fixed text in square brackets that the runner shows in place of other text.

  Only one name is accepted today (the address of the test database); any other name is a ``ValueError`` before anything runs. The tests, and
  every process they start, receive the full address, a password in it included. So pass only the address of a test database, never a token
  or a key. To allow one more name, add it to the list of allowed names in this file, re-copy the file and update its sha256 value. A second
  name does not work by that alone: every passed variable goes through the PostgreSQL address rules below, so a variable of another kind
  needs its own address rules and its own host check, written and reviewed with it.

  What a listed name switches on depends on the variable. "Skip check" is ``forbid_skips`` (below). "Canary run" is the first run repeated
  after each mutant, with the lock (below). "Output replaced" is the allowlist of shown text (below).

  ======================================  ====================================  ==========  ===============
  the variable                            skip check                            canary run  output replaced
  ======================================  ====================================  ==========  ===============
  listed, variable absent                 on (off with ``forbid_skips=False``)  no          no
  listed, variable present but empty      the call is refused before any run (an empty text is no address)
  listed, variable present with a value   on (off with ``forbid_skips=False``)  yes         yes
  ======================================  ====================================  ==========  ===============

  What is refused, in this order, before any test runs. Refusals 1 to 12 are a ``ValueError`` before any folder is made (a bare string in
  place of a list is a ``TypeError`` for ``tests``, ``extra_dirs``, ``only``, ``pass_env``, ``throwaway_hosts`` and ``shown_classes``: the first
  three are checked before the path check of refusal 1, so a bad path next to one of them still gives the ``TypeError``; the other three are
  checked in their own refusals, 2 to 4, so a bad path in ``tests`` comes first when the call has both; a bare string for ``crash_markers`` of a
  ``Mutant`` is a ``TypeError`` when the ``Mutant`` is made). The one exception to "before any folder is made" is a symbolic link: the junction checks come before any folder is made, but the check
  of relative links out of the tree comes after the snapshot is copied (it needs the copy), and the folders are removed again. Refusal 13 is a
  ``RuntimeError``. A refusal of an address names the variable and the reason, never the address.

  1. A path in ``tests`` or ``extra_dirs`` that is not a plain relative path. What to do: write the path relative to ``root``.
  2. Not allowed: a name in ``pass_env`` that is not allowed. What to do: pass only the name above.
  3. Not exact: an entry of ``throwaway_hosts`` that is not exact. An entry is one host name, one IP address or one absolute unix socket
     folder. A pattern (``*``), brackets, white space and an empty text are refused. This is checked for every call, also when no variable is
     passed. What to do: write each host in full.
  4. Not a name: an entry of ``shown_classes`` that is no exception class name. What to do: write the bare class name (``PostgresError``).
  5. A ``conftest`` that is not a plugin file of the tree. What to do: see ``conftest`` above.
  6. Too long: an address longer than 2,000 characters. What to do: use a shorter address.
  7. Odd characters: a character that a print would change (a quote mark, a backslash, a control character, a non-ASCII character), in the
     address or in its password after percent-decoding. What to do: change the password of the test database to plain ASCII letters and digits.
  8. An address that gives more than 300 texts to search for. What to do: do not percent-encode the password more than once.
  9. Wrong shape: an address outside the grammar. The grammar has two shapes, both in lower case. Shape one is a ``postgresql://`` (or
     ``postgres://``) URL with an optional login, a host, an optional port (1 to 65535) and ONE database name, and nothing after it. Shape two is words
     ``key=value`` separated by one space, with these keys only, each at most once: ``host``, ``hostaddr``, ``port``, ``dbname``, ``user``,
     ``sslmode``, ``connect_timeout``. ``sslmode`` takes ``disable``, ``allow``, ``prefer``, ``require``, ``verify-ca`` or ``verify-full``;
     ``connect_timeout`` takes one to five digits; ``port`` takes one to five digits that are a port number (1 to 65535, so ``0000080`` and ``99999999999`` are refused). An IPv6 host is written ``[::1]`` in a URL and ``host=::1`` in words. Any other key is refused, a
     password key included, because it can change where the connection goes or name a file. A URL with a driver name in its scheme
     (``postgresql+driver://``) is refused too. What to do: write the address in one of the two shapes.

     A password goes in the login part of the URL: ``postgresql://app:p%40ss@localhost:5432/testdb`` is the address for the login ``app``
     with the password ``p@ss``. In a password, write ``@`` as ``%40``, ``/`` as ``%2F``, ``?`` as ``%3F``, ``#`` as ``%23``, a space as
     ``%20`` and ``%`` as ``%25``. A colon may stand as it is. The runner searches for the password as written and as decoded.

     Not possible today: a password together with ``sslmode`` or ``connect_timeout``. The URL shape takes nothing after the database name,
     and the words shape takes no password key. What to do: use a test database whose login needs no password, or one that needs no option.
  10. No host: an address with no host and no ``hostaddr``. It would use the default local socket of the machine. What to do: write the host.
  11. Host not listed: a host that is not listed. ``host`` and ``hostaddr``, each when written, must be a member of ``throwaway_hosts``. A host
      name is compared whole, without regard to upper and lower case; a unix socket folder (``host=/var/run/postgresql``) is compared exactly
      as written. The default list is ``localhost``, ``127.0.0.1`` and ``::1`` and holds no socket folder. There is no pattern and no
      override. The address CI uses, ``postgresql://postgres@localhost:5432/postgres``, passes.
      What to do: FIRST make sure that the database on that host is disposable and that its login can touch nothing else. The runner cannot
      check this. Only then pass ``throwaway_hosts=("the-exact-name",)``. The list you pass REPLACES the default list, so also write
      ``localhost`` in it when you still need it.
      Also refused at this step, after the host check: a password that is the same, in any letter case, as the name of an exception class that
      the runner may show (a name of Python itself, a ``crash_type`` of a mutant of the call, an entry of ``shown_classes``). Hiding such a name
      would tell the reader that the password equals it. What to do: choose another password.
  12. A mutant whose ``test_file`` is not one of ``tests``. What to do: add the file to ``tests``.
  13. Lock held: a second runner on the same database address in the same lock folder (the lock, below). What to do: wait for the other
      run, or give this run a database of its own. The lock folder is refused when it lies inside the tree under test (the temp folder that
      Python picks is the working folder when no temp folder can be written, and ``TMPDIR`` may point into the tree). What to do: give the run a
      temp folder outside the tree with ``TMPDIR``.

  SAFETY: what the runner CANNOT check. It cannot check that the database is disposable. It cannot see what the login may do. The host list
  checks only the host written in the address. The tests are code and can connect elsewhere. A local name does not prove a local database: a
  tunnel or a proxy can point it at a shared one. Adding a host to ``throwaway_hosts`` removes that one check for that host. Every mutant run
  writes to the database, and a mutant can make the tests drop or fill tables. So the caller must know that the database is disposable and
  that its login can touch only that database.

  What protects the address (it may hold a password):

  - The child's console output (stdout and stderr) goes to the null device. The runner never reads or prints it.
  - The environment is read once, at the start of the call, except ``XDG_RUNTIME_DIR`` and the temp folder lookup of the lock folder, which are
    read when the lock is taken. Every child run, the lock name and the texts to search for come from that one reading.
  - The child gets a fixed short list of variables (``PATH``, the temp folder, ``HOME`` and a few more) plus the passed variable. No variable
    of the database library (``PGHOST``, ``PGSERVICE``, ``PGPASSFILE``, ...) is on that list. ``HOME`` IS inherited: see "What the tests can
    reach" at the top.
  - While a passed variable has a value, text from the child is shown only when it is on an ALLOWLIST of text that the caller or Python owns.
    A list of the forms a secret can take (a slice, a reversed copy, base64, hex) can never be complete, so the allowlist does not depend on
    such a list.

    ==================================  ====================================================================================================
    the place                           what is shown
    ==================================  ====================================================================================================
    the exception class name            Shown when it is a built-in Python exception name or pytest's ``Failed``. Also shown when it is a
                                        ``crash_type`` of a mutant of this call or a name in the caller's ``shown_classes``. For a line that
                                        starts with a bare ``assert`` the fixed word ``assert`` is shown. Else: ``[class not shown]``. A shown name that is EQUAL to a
                                        secret value in any letter case (one rule for every name: a built-in one, a ``crash_type``, a
                                        ``shown_classes`` entry; a password that is ``TimeoutError`` or ``timeouterror``) is ``[class not shown]`` too.
                                        A password that is only a PIECE of a name of Python does not hide it; a piece of a name of the caller
                                        hides it (the caller's names are caller text, see the second layer below): this difference is on purpose. What a reader can learn from it: a
                                        name equal to the password is hidden, so the password cannot be read from the name; a hidden name of the caller
                                        may also be one that only HOLDS a piece of the password, and the hiding itself shows that (one bit per row,
                                        the same channel as a test id or an ``expect`` slot).
    the rest of the failing line        Never shown. In its place: the fixed words ``[expect found]`` or ``[expect not found]``, then the
                                        caller's ``expect`` text.
    a test id                           The file part is shown when it equals one of the caller's ``tests`` entries. The caller's text is
                                        printed, without ``.py`` and without a leading ``./``. A test class name or function name is shown
                                        when ``def name`` or ``class name`` stands in the snapshot of that file, or when the caller named it
                                        on the mutant (``only_test``, ``pinned``). When any part is not allowed, the WHOLE id is
                                        ``[test id not shown]``. A test file in a folder whose name holds a dot is never matched.
    the ``[...]`` part of a test id     always the replacement text ``[parameters hidden]``
    how a run ended                     fixed words: the exit code, "timed out", or "reaped" (another part of the program collected the exit
                                        status of the child first, so it is lost)
    ==================================  ====================================================================================================

    This holds for every text the runner returns or puts in the message of an error it raises: ``first_lines``, the test id of a row, the
    messages of the ``COLLECTION ERROR``, ``FIXTURE ERROR`` and ``SKIPPED TESTS`` rows, the message of a failed first run, the message of a
    first run that skipped a test, and the two canary messages (a canary run that failed, a canary run that skipped a test).
  - Second layer, for the caller's own text only. Four slots hold text the caller wrote: a test id, an exception class name from
    ``crash_type`` or ``shown_classes``, the ``expect`` text, and a mutant name inside a message. Each slot is searched for the address, its
    password and the percent-encoded forms of the password. A slot that holds one of them is replaced WHOLE by its replacement text:
    ``[test id not shown]``, ``[class not shown]``, ``[expect text not shown]`` or ``[mutant name not shown]``. Nothing is ever cut out of
    the middle of a text. Python's own exception names and the runner's fixed words are never searched and never changed. The fixed words
    ``[expect found]`` or ``[expect not found]`` are shown also when the ``expect`` text itself is replaced.
    With a weak password this hides much: with the password ``test`` every test id that holds the letters ``test`` is
    ``[test id not shown]``, and a password of one or two characters hides nearly every id. A slot that is hidden this way tells a reader
    that its text holds the password. Use a random password of 12 or more characters, or a login that needs none.

  Examples, from a real run with an address present (the row, then its ``first_lines`` entry)::

      ('go gives the opposite', KILLED, 'tests/test_core::test_a', True)
          AssertionError [expect found] go must give its flag back
      ('go raises', WRONG_REASON, 'tests/test_core::test_a', False)
          KeyError [expect not found] go must give its flag back
      ('pick gives 2', KILLED, 'tests/test_core::test_b[parameters hidden]', True)
          AssertionError [expect found] pick must give 1
      a test id with a part that is not allowed:  [test id not shown]

  A script that reads ``first_lines`` must test for the fixed words ``[expect found]``. The ``expect`` text is printed in both cases, so its
  presence proves nothing. To see the real failing line of a ``WRONG_REASON`` row, run that one test by hand against the test database.

  Not covered:

  - The name column of a row and the keys of ``first_lines`` are the caller's mutant names, given back unchanged. A piece of a password
    written in ``expect`` or in a mutant name is shown (only the whole password is found). So never put a secret in ``expect`` or in a mutant name.
  - A test that itself writes the address to a file or to the network is out of reach of this tool.
  - A test that runs as the same user can alter everything the runner reads back: the result file of its own run (so it can forge its own
    verdict row, its test id, its first failing line and the list of skipped tests; the allowlist bounds what is then shown, never whether it is
    true), and the snapshot folder and ``base.xml`` of the run. The folders and files of the run are private to the user, not to the tests.
  - A test can choose which allowed name it shows (one of about 70 exception class names of Python, one of the caller's function names).
    A hostile test could pass a few bits per row that way. The counts and the exit code are numbers the child chooses, too.
  - The JUnit files hold the child's real text. Every folder the runner makes by the helper, the folders between the temp folder and a copied test file included
    (a part that was already there is left as it is), is created with mode 0700 whatever the umask and is checked (a real
    folder of this user with no access for group or others, ``lstat``) when it is made. The temp folder and the snapshot folder are checked again after every rebuild of the temp copy; the
    others once, when made (the parent is re-checked and gates the way in). The folders are: the temp folder of the run, its ``tests`` folder, its snapshot folder (next to it in the temp folder), the folder of the pytest settings file and the lock folder.
    The temp folder is emptied and kept, never removed and made again with the default mode. The settings file and every result file are made by
    the runner with mode 0600 before the child gets their path, and checked on the open descriptor (a regular file of this user with one name and no access for
    group or others, ``_file_problem``), and an old file is emptied only after that check (a file with a second name keeps its content when it is
    refused). The folders below these (the copies of ``src`` and of the tests) keep the modes of the
    caller's tree and can be reached only through the private folder. On purpose these copy sites are NOT helpers: ``shutil.copytree`` and ``shutil.copy``
    of the snapshot and of every rebuild copy the caller's tree and keep its modes, and ``write_text`` replaces the text of one file of the copy with the mutant. A test pins
    every creation site of the listed spellings (``tempfile.mkdtemp``, ``mkstemp``, ``NamedTemporaryFile``, ``TemporaryFile``, ``SpooledTemporaryFile``, ``TemporaryDirectory``,
    ``os.mkdir``, ``makedirs``, ``open``, ``rename``, ``replace``, ``symlink``, ``link``, ``mkfifo``, ``shutil.copytree``, ``copy``, ``copy2``, ``copyfile``, ``move``, ``open``, and the methods
    ``mkdir``, ``touch``, ``write_text``, ``write_bytes``, ``open``), also under an alias and in module-level code. The test pins each (spelling, owner function, count) in this file; a spelling that
    is not listed is NOT found: a name assigned to a variable first, ``getattr``, ``map`` or ``functools.partial`` of a creating function, ``os.fdopen``, ``io.open``, ``codecs.open``, other ``Path`` methods
    and ``shutil.copyfileobj``. The intermediate parents of the destination of an ``extra_dirs`` copy are made by ``copytree`` and ``makedirs`` and keep the caller's modes. On Windows nothing is checked: mode bits mean nothing there. The runner removes the folders at the end. After SIGKILL, which cannot be
    caught, they stay on disk (``mutants_*`` in the temp folder): delete it by hand.
  - A traceback of an error the runner raises holds the address in its local variables. A tool that prints local variables (pytest
    ``--showlocals``, an error tracker) prints the address with its password. The messages of the errors never hold it.

  ``pinned`` is compared with the child's real test id inside the runner, parameters included. The judge and the ``crash_type`` check read the
  child's real line inside the runner; ``first_lines`` gets what the table above shows. With no passed variable that has a value, nothing is
  replaced: the line and the test id are shown as the child wrote them.

  With no passed variable nothing is replaced and nothing is claimed. The allowlist protects the value of a passed variable and has nothing to
  protect then, and the runner cannot know what else a test suite must not show. Hiding the failure text of every child for every caller was
  considered and not done: it would take away the failing line from every caller who has nothing to protect. The child can read the files of the
  caller's home folder (see "What the tests can reach"), so do not pass this runner a test suite that must not see them.

  ``shown_classes=("PostgresError",)``: exception class names of the caller's libraries that may be shown (plain identifiers only). It
  allows exception class names only, not the names of test classes.

  The canary run. All runs share the one database. So after EVERY mutant run the runner copies the tree again and runs all the tests of the
  ``tests`` argument, without any bug, on that database. When they no longer pass, the run stops with ``CanaryFailed`` (a ``RuntimeError``;
  its ``rows`` hold the rows so far) and names the mutant: what the mutant left behind would make later verdicts false. Under ``forbid_skips``
  a canary run that skips a test stops the run too. Cost: one more pytest run and one more copy of the tree per mutant. The canary run proves
  only that the tests still pass. It does not prove that the database is clean, and it does not notice a second runner whose leftovers do not
  break the tests.

  The lock: one runner per database address in one lock folder. Its reach is small. It stops a second runner only when that runner uses
  the SAME lock folder and the SAME spelling of host, ``hostaddr``, port and database name. The lock is a file named by the first 16 hex digits
  of a SHA-256 of those four parts. A password is never read for it, and the file name holds no part of the address. The second runner gets a
  ``RuntimeError`` before any test runs.
  It does NOT see a runner of another user, or a runner with another temp folder or on another machine. It does NOT see the same database
  written another way (``localhost`` and ``127.0.0.1``, a port written or left out). It does NOT see a runner that keeps its lock folder
  elsewhere: a run WITH ``XDG_RUNTIME_DIR`` (a login shell) and a run WITHOUT it (cron, ``su``, a CI step) use two lock folders and do not
  see each other. Give each run a database of its own. The lock only catches the plain mistake of starting twice.
  The login is not part of the lock name: two runs that differ only in the login are treated as one database, and the second is refused. A run with
  the variable absent takes no lock at all (no address, no shared database).
  The lock folder (POSIX) is ``hadavin_mutation_locks_<uid>``. It lies in ``XDG_RUNTIME_DIR`` when that is a folder of this user closed to
  others, else in the temp folder that Python picks (``tempfile.gettempdir()``, which is not ``TMPDIR`` when ``TMPDIR`` cannot be written). ``XDG_RUNTIME_DIR`` is read from the environment when the lock is taken. The folder is made with mode 0700
  and opened without following a link; the lock file is created under the opened folder.
  A folder under that name that belongs to someone else, is a link, or is open to group or others is REFUSED: the run stops with a
  ``RuntimeError``. The tool cannot prevent another user of a shared temp folder from putting such a folder there first. The way out is a temp
  folder of your own (``TMPDIR``). The runner does not look at the PARENT folder: in a shared temp folder without the sticky bit another user
  can move the lock folder away, the next runner then makes a new one, and the two runs do not see each other. The lock file is opened without
  following a link, mode 0600, and the runner then looks at what it opened (it must be a regular file of this user with one name). The file
  is never deleted.
  On Windows the runner takes a lock file in the temp folder and checks nothing about that folder.
- ``forbid_skips=True``: a run in which any selected test is skipped (or is an expected failure) proves nothing. A mutant run with a skip is
  the ERROR row ``SKIPPED TESTS``, never a kill. A first run with a skip raises ``RuntimeError``. A mutant run with no JUnit file,
  or an empty one, is the ERROR row ``JUNIT MISSING``. This closes the false kill where a mutant "dies" because the tests could not run (no
  database was reachable, say). Default: on when a name is LISTED in ``pass_env`` (whether or not the variable is present), off otherwise.
  ``forbid_skips=False`` turns it off; a mutant can then count as killed because the tests could not run.

For every caller, with or without a keyword: two results change against the earlier version of this tool and one row gets a new label.

1. A changed result. A run whose FIRST failing test case failed in a fixture, at setup or at teardown, is the ERROR row ``FIXTURE ERROR`` and
   never a kill. Before, it was a kill when the fixture failed with an ``AssertionError`` and a crash otherwise. A test whose body failed and
   whose teardown failed afterwards is judged by the body's failure (the test ran as written).
2. A changed result. ``testing.mutation.judge`` returns ``ERROR`` when the run failed (exit 1) and no failing test id is known (an empty or
   unreadable JUnit file). Before, it returned ``CRASH`` or ``KILLED``.
3. A new label only. A run whose FIRST failing case is a test file that could not be imported or collected is the ERROR row
   ``COLLECTION ERROR``. An ``assert`` at import time is included. pytest exits 2 for it and the judge already returned ``ERROR`` for every exit
   code other than 1, so the old row was an ERROR row too (with the module name as its test id), never a kill.

A mutant counts as killed only when a test ran as written and failed.

Result rows. A row is ``(name, verdict, test id, good)``. The test id column holds the failing test id. For an ERROR row that the runner
made without asking the judge, the test id column holds one of these labels instead:

- ``SETUP FAILED: <exception class>``, ``SNIPPET NOT FOUND``, ``TIMEOUT``, ``REAPED ELSEWHERE``;
- ``JUNIT REFUSED`` (refused or unreadable), ``JUNIT MISSING`` (``forbid_skips``);
- ``COLLECTION ERROR``, ``FIXTURE ERROR``, ``SKIPPED TESTS`` (``forbid_skips``);
- ``NO FAILING TEST NAMED`` (exit code 1, the JUnit file names no failing test);
- ``EXIT CODE <n>`` (any other exit code with no failing test named: a usage error, an internal error, a process stopped by the system).

``first_lines`` (a dictionary the caller may pass) gets one entry per judged row that has a first failure line, a kill or not. For a
``COLLECTION ERROR``, ``FIXTURE ERROR`` or ``SKIPPED TESTS`` row it gets the message that says why. While a passed variable has a value each
entry is what the table under ``pass_env`` shows, not the child's line.

The numbers and names this tool fixes are constants at the top of this file and NOT in the product's file of defaults. They are the timeouts,
the bounds of the search for known texts, the child's variable list, the allowed keys and hosts, and the row labels. The rule that such
values live in one config file is about product behaviour (names, regions, prices, thresholds a deployment tunes). This is a developer tool
that is not part of the installed package, has no config surface and is copied byte for byte into other repositories. A caller changes the
timeouts and the host list by argument.
"""

from __future__ import annotations

import builtins
import contextlib
import errno
import hashlib
import itertools
import keyword
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import FrameType
from urllib.parse import quote, quote_plus, unquote, unquote_plus, urlsplit

from hadavin_sdk.testing.mutation import (
    MAX_JUNIT_CHARS,
    JunitReport,
    Verdict,
    judge_report,
    read_junit,
    skipped_tests,
)


@dataclass(frozen=True)
class Mutant:
    name: str
    file: str  # relative to the copied root
    old: str
    new: str
    expect: str  # >= 4 characters: a distinctive fragment of the INTENDED failing assertion line (its message), never of the killer's name
    allow_crash: bool = (
        False  # the intended reaction is a crash (an exception other than an assertion)
    )
    crash_type: str = ""  # REQUIRED with allow_crash: the exception CLASS NAME that must LEAD the first ``E`` line (parsed, not a substring match), or the mutant is not good
    crash_markers: tuple[
        str, ...
    ] = ()  # passed to ``judge``: a first line holding one of these is a CRASH even if it is an assertion
    test_file: str = ""  # one of the `tests` files: run ONLY this file for the mutant (its killer is not in the first file)
    pinned: str = ""  # the test id (as ``first_failure_junit`` writes it, ``tests/test_x::test_y``) that must be the one failing; another failing test is OTHER_TEST
    only_test: str = ""  # a test function name: run ONLY that test (of the first test file, or of `test_file`), so the killer never depends on test order or a fuzz seed

    def __post_init__(self) -> None:
        _relative(self.file)
        if len(self.expect) < 4:
            raise ValueError("expect must be at least 4 characters")
        if self.allow_crash and not self.crash_type.isidentifier():
            raise ValueError(
                "allow_crash needs crash_type: the exception class name the kill must show"
            )
        if self.crash_type and not self.allow_crash:
            raise ValueError("crash_type without allow_crash")
        if isinstance(self.crash_markers, str):
            raise TypeError("crash_markers is a sequence of texts, not one string")
        if self.only_test and not self.only_test.isidentifier():
            raise ValueError("only_test must be a test function name")
        if self.test_file:
            _relative(self.test_file)


def _plain_operand(arg: str) -> str:
    """``arg`` may reach the pytest command line as an operand: it must not start with ``-`` (pytest reads it as an option; the ``--``
    marker is not a safe fence, on some Python 3.12 builds argparse still takes the next word after it as an option) or with ``@``
    (pytest reads ``@name`` as a file of further arguments, also after ``--``). A caller who means such a file name writes ``./name``."""
    if arg.startswith(("-", "@")):
        raise ValueError(f"a path may not start with '-' or '@' (write ./name): {arg!r}")
    return arg


def _relative(rel: str) -> str:
    """``rel`` must be a relative path with no ``..`` part (checked as a POSIX and as a Windows path) and must not start with ``-`` or ``@``."""
    if not isinstance(rel, str) or not rel:
        raise ValueError("a path is a non-empty string")
    _plain_operand(rel)
    # a Windows drive, or an NTFS alternate data stream name (``file.py:stream``): neither is a plain relative path
    if ":" in rel:
        raise ValueError(f"a path may not contain ':': {rel!r}")
    for pure in (PurePosixPath(rel), PureWindowsPath(rel)):
        if pure.is_absolute() or pure.anchor or ".." in pure.parts:
            raise ValueError(f"path escapes its tree: {rel!r}")
    return rel


def _inside(base: Path, rel: str) -> Path:
    """``base / rel``, resolved, and proven to lie inside ``base`` (symlinks included)."""
    root = base.resolve()
    path = (root / _relative(rel)).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"path escapes its tree: {rel!r}")
    return path


_IS_WINDOWS = (
    os.name == "nt"
)  # one place to ask (tests set it to check the Windows branch of the tree kill on any system)
DEFAULT_TIMEOUT = 900.0  # seconds one pytest run may take (a 15-minute ceiling for the slowest killer); override by argument
REAPED_ELSEWHERE = -1001  # returned instead of an exit code when someone else reaped the child first (SIGCHLD ignored, a stray ``wait``): its exit status is lost and ``Popen`` would report 0, which the judge must never read as a pass or a fail
TIMED_OUT = -1000  # returned instead of an exit code when the run exceeded its timeout; no process exit status is this low (POSIX -9 is a SIGKILL, for example the OOM killer, and is judged as an error)
CHILD_ENV = (
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE",
    "LANG", "LC_ALL", "PYTHONHASHSEED", "PYTHONUTF8", "PYTHONIOENCODING",
)  # fmt: skip  # the only variables a mutant run inherits
# the ONLY names ``pass_env`` may add to the child's environment: the address of a throwaway test resource, never a token or a key.
# To widen it: add the name here, re-copy this file and update its pin (CHANGELOG list and tests/fixtures/mutation_manifest.json); the
# trigger is a demo's tests needing the address of another throwaway test resource, and each name gets the same review.
PASS_ENV_ALLOWED = ("HADAVIN_TEST_PG_DSN",)
MASK = "[REDACTED]"
NO_TEST_NAMED = "NO FAILING TEST NAMED"  # the id column of an ERROR row for a failed run whose JUnit file names no failing test
EDGE_MIN = 2  # a head or tail piece of a secret next to ``...`` is masked from this many characters on (one character cannot be told from ordinary text)
PASSWORD_PIECE_MIN = 3  # a piece of an unquoted password that holds a quote mark, ``;`` or ``&`` is a secret of its own from this many characters on
MAX_FRAGMENT_HITS = 1_000  # more ``...`` than this in one text is no honest line (pytest writes a few): the whole text is replaced, never scanned (see ``_masked``)
PORT_MIN = 1  # a port of an address is from here to ``PORT_MAX`` (TCP port numbers); outside it the address is outside the grammar
PORT_MAX = 65_535
MAX_SECRETS = 300  # more secret texts than this (a value, its password and their decoded and encoded forms) are refused: no honest address has that many
MAX_FRAGMENT_WORK = 50_000  # (``...`` in a line) x (secrets): more than this replaces the whole line, so one line costs a bounded number of scans
MAX_VALUE_CHARS = 2_000  # a passed value longer than this is refused: no address is that long, and the scan and the memory of the secrets grow with its length
CHILD_FIXED_ENV = {
    "PYTHONNOUSERSITE": "1"
}  # set, not inherited: the child never imports from the caller's user site-packages
SETUP_TRIES = 5  # attempts to clear and rebuild the temp copy (a Windows file lock may hold a file for a moment)
SETUP_WAIT = 0.5  # seconds between those attempts
# a refused JUnit file (DOCTYPE, ENTITY, too large) or a truncated one (ET.ParseError is a SyntaxError) is THIS mutant's ERROR, not the end of the run
JUNIT_REFUSED = (ValueError, SyntaxError)
_UNUSABLE_JUNIT = (
    OSError,
    *JUNIT_REFUSED,
)  # a JUnit file that is refused, truncated or cannot be read: that mutant's ERROR row


def _taskkill() -> str:
    """taskkill.exe by its full path under %SystemRoot%\\System32, not by a PATH search (a planted taskkill in a work folder is not run)."""
    root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT") or r"C:\Windows"
    return str(Path(root) / "System32" / "taskkill.exe")


# the Windows flag that gives the child a process group of its own (Python defines the name on Windows only; 0, "no flag", elsewhere,
# where the flag is never used for a real run)
if sys.platform == "win32":
    _NEW_PROCESS_GROUP = subprocess.CREATE_NEW_PROCESS_GROUP
else:
    _NEW_PROCESS_GROUP = 0
WAIT_POLL = (
    0.05  # seconds between two looks at a running child (POSIX ``os.waitid`` has no timeout)
)
TREE_KILL_TIMEOUT = 60.0  # seconds ``taskkill`` may take before the child itself is killed anyway


def _leading_class(first: str) -> str:
    """The exception class name that starts a pytest ``E`` line (``E   demo.fakes.AuditWriteError: text`` gives ``AuditWriteError``;
    a name that only CONTAINS the declared one, or that appears later in the text, does not match it). The ``E`` marker is a letter
    followed by spaces: a class such as ``EOFError`` keeps its first letter, and a line with no marker (a message fallback) is read as is."""
    head = re.sub(r"^E\s+", "", first.strip()).split(":", 1)[0].strip()
    return head.rsplit(".", 1)[-1]


def _locate(base: Path, rel: str) -> Path:
    """The file ``rel`` names inside ``base``, found by listing the tree (``os.walk``; a match is accepted only if its real path stays inside the tree): the caller's string is only
    COMPARED as data with the listed relative names and is never joined to a path, so it cannot steer a read or a write out of the tree."""
    want = _relative(rel).replace("\\", "/")
    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            full = os.path.join(dirpath, name)
            if os.path.relpath(full, base).replace(os.sep, "/") != want:
                continue
            real_base, real_full = os.path.realpath(base), os.path.realpath(full)
            # a link (or junction) out of the tree does not count
            if os.path.commonpath([real_base, real_full]) == real_base:
                return Path(full)
    raise ValueError(f"no such file inside the tree: {rel!r}")


class _ReapedElsewhere(Exception):
    """The child ended but another waiter reaped it, so its exit status is unknown (``Popen`` itself would call it 0)."""


def _plugin_module(conftest: str) -> str:
    """The module name pytest loads (``-p``) for the tree file ``conftest``: ``tests/conftest.py`` gives ``tests.conftest``. Every part must be a
    plain ASCII identifier that is not a Python keyword (``class.py`` and a non-ASCII look-alike are refused) and the file must end in ``.py``, so the name can carry no option, no ``no:`` prefix and no path trick."""
    _relative(conftest)
    parts = conftest.replace("\\", "/").split("/")
    names = (*parts[:-1], parts[-1][:-3])
    if not parts[-1].endswith(".py") or not all(
        p.isascii() and p.isidentifier() and not keyword.iskeyword(p) for p in names
    ):
        raise ValueError(
            f"conftest must be a .py file whose path parts are plain ASCII names that are not Python keywords: {conftest!r}"
        )
    if parts[-1] != "conftest.py" and "tests" not in parts[:-1]:
        raise ValueError(
            f"conftest must be called conftest.py or lie in a folder called tests: {conftest!r}"
        )
    return ".".join([*parts[:-1], parts[-1][:-3]])


def _refuse_bare_string(value: object, name: str) -> None:
    """``TypeError`` when ``value`` is one string where a sequence of texts is meant: it would be read letter by letter (``only="flip"`` would
    select every mutant whose name holds an ``f``, an ``l``, an ``i`` or a ``p``; ``extra_dirs="fixtures"`` would copy nothing)."""
    if isinstance(value, str):
        raise TypeError(f"{name} is a sequence of texts, not one string")


def _checked_env_names(names: Iterable[str]) -> tuple[str, ...]:
    """``names`` if every one is in ``PASS_ENV_ALLOWED``, else ``ValueError`` (a bare string is a ``TypeError``, not read letter by letter)."""
    if isinstance(names, str):
        raise TypeError("pass_env is a sequence of names, not one string")
    chosen = tuple(names)
    for name in chosen:
        if name not in PASS_ENV_ALLOWED:
            raise ValueError(f"pass_env may name only {PASS_ENV_ALLOWED}: {name!r} is refused")
    return chosen


_PASSWORD_WORD = re.compile(
    r"(?is)(?:password|passwd|pwd) *=( *)([^\s&;]+)"
)  # ``password=...`` of a key=value DSN or a URL query, up to the next white space, ``&`` or ``;`` (no quote mark, backslash or control character such as a tab can be in the value: see ``_refuse_odd``, which runs first, so only the space is spelled out). No lookbehind: ``sslpassword=`` and ``PGPASSWORD=`` are read too
_NOT_WHITE = re.compile(r"\S*")  # the rest of a word, up to the next white space
# every ``...`` (or the one character U+2026 that a newer pytest could print), also those that share a dot (a secret may end in a dot): one match at the start of each
_DOTS = re.compile(r"(?=\.\.\.|\u2026)")


def _odd_character(text: str) -> str | None:
    """The kind of the first character of ``text`` that a print of the text could change, or ``None``: a quote mark or a backslash (a print adds
    them), a control character or a non-ASCII character (a print writes them as an escape such as ``\\xe9``). Space and the other printable ASCII
    characters are printed as they are."""
    for char in text:
        if char in "'\"":
            return "a quote mark"
        if char == "\\":
            return "a backslash"
        if ord(char) < 32 or ord(char) == 127:
            return "a control character"
        if ord(char) > 127:
            return "a non-ASCII character"
    return None


def _refuse_odd(name: str, what: str, text: str) -> None:
    """``ValueError`` when ``text`` (``what`` of the variable ``name``) holds a character ``_odd_character`` names. The message names the variable and
    the kind of character, never the text."""
    kind = _odd_character(text)
    if kind is not None:
        raise ValueError(
            f"{name} is refused: {what} holds {kind}. The runner hides a secret by looking for its plain text, and a print of a text with such a"
            " character no longer shows the plain text, so it could not be hidden. The rule covers the whole address, also its host, database"
            " name and options. Use a throwaway database whose address and password hold only plain printable ASCII letters, digits and"
            " punctuation without quote marks and backslashes (a percent-encoded password is read decoded)."
        )


def _url_passwords(value: str) -> tuple[list[str], list[str]]:
    """The password of a URL as ``urlsplit`` reads it, and every text between the first ``:`` after ``://`` and an ``@`` after it: a password that
    holds an unencoded ``/``, ``?``, ``#`` or ``@`` is not read right by ``urlsplit`` (it takes the first of them as the end of the address), so
    every ``@`` is tried as the end of the login (more than needed is masked, never less). With no ``@`` after the first colon (``host:5432/db``) there is
    no password and no candidate; with one, everything between them is a candidate, also ``12/45`` in ``svc:12/45@h/db``."""
    found: list[str] = []  # every text between the first colon and an @
    proper = ""
    with contextlib.suppress(ValueError):  # not URL-shaped: only the key=value scan applies
        proper = urlsplit(value).password or ""
    if "://" in value:
        rest = value.split("://", 1)[1]
        colon = rest.find(":")
        at = rest.find("@", colon + 1) if colon != -1 else -1
        while at != -1:
            found.append(rest[colon + 1 : at])
            at = rest.find("@", at + 1)
    # a candidate with ``?`` or ``#`` in it may reach into the options after the address: hidden as written only; the others are read as passwords
    return [proper, *(c for c in found if not re.search(r"[?#]", c))], [
        c for c in found if re.search(r"[?#]", c)
    ]


def _password_texts(value: str) -> tuple[list[str], list[str]]:
    """``(decoded, plain)``: the texts of ``value`` that are, or may be, a password. ``decoded`` are those that are read as a password and so also
    checked and percent-decoded: the one right after ``password=`` (up to the next ``&``, ``;`` or white space) and the passwords of a URL.
    ``plain`` are those that are only hidden as written: the rest of the word after a password word (up to the next white space), its pieces split
    at ``;`` and ``&`` of ``PASSWORD_PIECE_MIN`` characters or more (an unquoted password may hold them), and the text after ``password=`` and a
    space (it may be the next option, not a password). Other options in the same value are not decoded, so a non-ASCII option does not refuse a run.
    From ``run_mutants`` an address with a password key, or with ``@``, ``/``, ``?`` or ``#`` in a URL password, is refused by the address check before
    any run. This wider reading is kept so that the search for known texts never depends on that check."""
    matches = list(_PASSWORD_WORD.finditer(value))
    decoded = [m.group(2) for m in matches if not m.group(1)]
    plain = [m.group(2) for m in matches if m.group(1)]
    words: list[str] = []
    reached = 0  # a password word inside the word of an earlier one adds nothing: its text is a piece of that word and of its pieces
    for m in matches:
        if m.start(2) >= reached:
            word = _NOT_WHITE.match(
                value, m.start(2)
            )  # ``\S*`` always matches; the fallback only keeps the type honest
            reached = word.end() if word else m.end(2)
            words.append(value[m.start(2) : reached])
    plain += words
    plain += [
        piece
        for word in words
        for piece in re.split(r"[;&]", word)
        if len(piece) >= PASSWORD_PIECE_MIN
    ]  # the pieces of an unquoted password that holds ``;`` or ``&``: each may stand alone in a message
    url_decoded, url_plain = _url_passwords(value)
    decoded += url_decoded
    plain += url_plain
    return [p for p in dict.fromkeys(decoded) if p], [p for p in dict.fromkeys(plain) if p]


def _decoded_forms(name: str, password: str) -> set[str]:
    """``password`` as written, percent-decoded once with and without ``+`` read as a space, and decoded again until nothing changes (a password that
    was encoded twice, ``a%2540b``, shows as ``a@b`` after two decodes). Every step is checked by ``_refuse_odd``."""
    forms = {password}
    for what, decode in (
        ("the password in it, percent-decoded", unquote),
        ("the password in it, percent-decoded with + read as a space", unquote_plus),
    ):
        text = password
        for _ in range(
            len(password) + 1
        ):  # each change makes the text shorter or swaps ``+`` for a space, so this ends
            decoded = decode(text)
            _refuse_odd(name, what, decoded)
            # this chain ends when a step changes nothing; the other chain starts again from the password (``a%2Bb`` is ``a+b`` after ``unquote`` and ``a b`` after ``unquote_plus``)
            if decoded == text:
                break
            forms.add(decoded)
            text = decoded
    return forms


def _encoded_forms(text: str) -> set[str]:
    """``text`` as a URL or a form writes it: every character but letters, digits and ``_.-~`` as a percent code (``quote(safe="")``), the same with
    ``/`` kept (``quote``), and with a space as ``+`` (``quote_plus``); each in upper and in lower case hex."""
    forms = set()
    for form in (quote(text, safe=""), quote(text), quote_plus(text)):
        forms.add(form)
        forms.add(re.sub(r"%[0-9A-F]{2}", lambda m: m.group().lower(), form))
    return forms


_NAME_HOST = r"[A-Za-z0-9.-]+"  # a host name or an IPv4 address
_IP6_HOST = (
    r"[0-9A-Fa-f:.]*:[0-9A-Fa-f:.]*"  # an IPv6 address: hex digits, dots and at least one colon
)
_URL_ADDRESS = re.compile(
    rf"postgres(?:ql)?://(?:[^@/?#\s]*@)?({_NAME_HOST}|\[{_IP6_HOST}\])(?::([0-9]{{1,5}}))?/([A-Za-z0-9_.-]+)"
)  # the WHOLE value: a scheme, a login with no ``@``, ``/``, ``?`` or ``#`` in it, a host (IPv6 in brackets), a port, ONE database name, nothing after
_PAIR = re.compile(
    r"([a-z_]+)=([A-Za-z0-9_.:/@+%,~-]+)"
)  # one ``key=token`` of a key=value address; a key is written in lower case (the database library reads keys with exact letter case)
_SOCKET_DIR = re.compile(
    r"/[A-Za-z0-9_./-]*"
)  # a unix socket folder: an absolute path of plain characters
_ADDRESS_VALUE = {
    # IPv6 WITHOUT brackets in key=value form (``host=::1``), as the database library reads it
    "host": re.compile(rf"{_NAME_HOST}|{_IP6_HOST}"),
    "hostaddr": re.compile(r"[0-9A-Fa-f.:]+"),
    "port": re.compile(r"[0-9]{1,5}"),
    "dbname": re.compile(r"[A-Za-z0-9_.-]+"),
}
# the two option keys take listed values only (the lock name is not made from them)
_OPTION_VALUE = {
    "sslmode": re.compile(r"disable|allow|prefer|require|verify-ca|verify-full"),
    "connect_timeout": re.compile(r"[0-9]{1,5}"),
}
# the ONLY keys a key=value address may hold, each with the reason it is needed. Every other key is refused: it can change where the connection goes
# (``service``, ``options``, ``passfile``, ``target_session_attrs``), names a file to read (``sslrootcert``, ``sslcert``, ``sslkey``) or is not needed
# to reach a test database (``application_name``).
ADDRESS_KEYS_ALLOWED = {
    "host": "where the database listens: checked against throwaway_hosts",
    "hostaddr": "the numeric form of the host: checked against throwaway_hosts",
    "port": "several local test databases differ only by their port",
    "dbname": "which database of the server the tests may write to",
    "user": "the login of the test database (trust or peer sign-in needs no password)",
    "sslmode": "a local test server without TLS needs sslmode=disable",
    "connect_timeout": "a database that is down must fail fast, not hang every mutant run",
}
THROWAWAY_HOSTS = (
    "localhost",
    "127.0.0.1",
    "::1",
)  # the default of ``throwaway_hosts``: this machine by name and number; NO unix socket folder (a caller names one on purpose)


def _is_socket_dir(token: str) -> bool:
    """True when ``token`` is written like a unix socket folder: an absolute path of plain characters with no ``..`` part."""
    return bool(_SOCKET_DIR.fullmatch(token)) and ".." not in token.split("/")


def _port_in_range(port: str) -> bool:
    """True when ``port`` (one to five digits, as the grammar read it) is a TCP port number: 1 to 65535."""
    return PORT_MIN <= int(port) <= PORT_MAX


def _address_fields(value: str) -> dict[str, str] | None:
    """The parts (``host``, ``hostaddr``, ``port``, ``dbname``) of ``value``, or ``None`` when the value is outside the ONE strict grammar that the
    address check and the lock name share. (a) A URL ``postgres://`` or ``postgresql://`` with an optional login, a host (a name, an IPv4 address or
    an IPv6 address in brackets), an optional ``:digits`` port and exactly one ``/name``, with nothing after it. (b) Words ``key=token`` separated by
    one space, every key in ``ADDRESS_KEYS_ALLOWED`` (so no password key, whatever its spelling), NO key twice; ``host`` is a name, an IPv4 address, an IPv6 address
    without brackets or a unix socket folder (``_is_socket_dir``). A host name is given in lower case, a bracketed IPv6 host without its brackets, a
    socket folder as written (a path keeps its letter case). An empty value is outside the grammar."""
    found: dict[str, str] = {}
    url = _URL_ADDRESS.fullmatch(value)
    if url:
        if url.group(2) and not _port_in_range(url.group(2)):
            return None
        return {
            "host": url.group(1).strip("[]").lower(),
            "port": url.group(2) or "",
            "dbname": url.group(3),
        }
    seen: set[str] = set()
    for word in value.split(" "):
        pair = _PAIR.fullmatch(word)
        if not pair:
            return None
        key, token = pair.group(1), pair.group(2)
        if key not in ADDRESS_KEYS_ALLOWED:
            return None
        if key in seen:
            return None
        seen.add(key)
        if key in _OPTION_VALUE and not _OPTION_VALUE[key].fullmatch(token):
            return None
        if key not in _ADDRESS_VALUE:
            continue
        socket = key == "host" and _is_socket_dir(token)
        if not socket and not _ADDRESS_VALUE[key].fullmatch(token):
            return None
        if key == "port" and not _port_in_range(token):
            return None
        found[key] = token.lower() if key in ("host", "hostaddr") and not socket else token
    return found


def _address_parts(value: str) -> str:
    """The text the lock name is hashed from: host, host address, port and database name of ``value`` as ``_address_fields`` reads them (the same
    reading as the address check, so two databases behind one unix socket folder give two texts), or ``"unparsed"`` for a value outside the
    grammar. The login and every other word are never used. THIS IS A MATCH ON SPELLING, NOT ON THE DATABASE: ``localhost`` and ``127.0.0.1``, a
    port written or left out, and ``host=`` and ``hostaddr=`` give different texts for one database."""
    fields = _address_fields(value)
    if fields is None:
        return "unparsed"
    return "\n".join(fields.get(key, "") for key in _ADDRESS_VALUE)


def _checked_throwaway_hosts(hosts: Iterable[str]) -> tuple[str, ...]:
    """``hosts`` as a tuple of exact members, else ``ValueError`` (a bare string is a ``TypeError``). A member is a host name or address (letters,
    digits, ``.``, ``:``, ``-``; kept in lower case, because host names ignore letter case) or a unix socket folder (an absolute path, kept as
    written). No pattern: ``*``, brackets and white space are refused."""
    if isinstance(hosts, str):
        raise TypeError("throwaway_hosts is a sequence of host names, not one string")
    chosen: list[str] = []
    for host in hosts:
        if isinstance(host, str) and _is_socket_dir(host):
            chosen.append(host)
        elif isinstance(host, str) and re.fullmatch(r"[A-Za-z0-9.:-]+", host):
            chosen.append(host.lower())
        else:
            raise ValueError(
                "throwaway_hosts holds exact host names, addresses or absolute unix socket folders only (letters, digits, '.', ':', '-', and '/' and"
                " '_' in a folder): no pattern, no brackets"
            )
    return tuple(chosen)


def _refuse_unsafe_address(
    env_name: str,
    value: str,
    throwaway_hosts: Sequence[str],
    class_names: Iterable[str] = (),
) -> None:
    """``ValueError`` (before anything runs; the message names the variable and the reason, never the value) unless ``value`` is inside the strict
    grammar (``_address_fields``), names a ``host`` or a ``hostaddr``, and EACH of the two that is written is an exact member of ``throwaway_hosts``.
    A unix socket folder is a host like any other: it must be listed. Least privilege: the tests of every mutant write to this database. What this
    does NOT prove: that the database is disposable (a tunnel or a proxy can point a local name at a shared database), or what its login may do.
    Also refused: a password that is equal, in any letter case, to the name of an exception class that the runner may show (every name of
    Python itself and ``Failed``, and the ``class_names`` the caller gives: the ``crash_type`` of its mutants and its ``shown_classes``). Hiding such
    a name would tell the reader that the password equals it (the hiding of ``_shown_class`` is the second layer for the same case)."""
    allowed = _checked_throwaway_hosts(
        throwaway_hosts
    )  # first: a host list that is not exact is refused whatever the address is
    fields = _address_fields(value)
    if fields is None:
        raise ValueError(
            f"{env_name} is refused: its address is not in a shape the runner can check. Write a postgresql:// URL in lower case with an optional"
            " login, a host, an optional port (1 to 65535) and ONE database name and nothing after it, or key=value words separated by one space, with the keys"
            f" {', '.join(ADDRESS_KEYS_ALLOWED)} in lower case, each key once. The key=value shape takes no password key: a password goes in the"
            " login part of the URL (postgresql://user:password@host:port/database), with @ / ? # in it written as %40 %2F %3F %23. Also"
            " refused: a service file, an option after the database name, sslmode other than disable, allow, prefer, require, verify-ca or"
            " verify-full, connect_timeout other than one to five digits, an empty text"
        )
    if not fields.get("host") and not fields.get("hostaddr"):
        raise ValueError(
            f"{env_name} is refused: its address names no host and no hostaddr, so it would use the default local socket of this machine, which the"
            " runner cannot check. Write the host (or the socket folder) and list it in throwaway_hosts"
        )
    for part in ("host", "hostaddr"):
        host = fields.get(part, "")
        if host and host not in allowed:
            raise ValueError(
                f"{env_name} is refused: its {part} is not one of throwaway_hosts {allowed}. The tests of every mutant write to that database. Add"
                " the exact host (or socket folder) with throwaway_hosts=(...) only when you know the database is disposable: the runner cannot check it"
            )
    names = {n.casefold() for n in (*_BUILT_IN_CLASSES, *class_names)}
    if any(text.casefold() in names for text in _password_forms(env_name, value)):
        raise ValueError(CLASS_NAME_REFUSAL.format(env_name=env_name))


CLASS_NAME_REFUSAL = (
    "{env_name} is refused: its password is the same, in any letter case, as the name of an exception class that the runner may show (a name of"
    " Python itself, a crash_type of a mutant or an entry of shown_classes). Choose another password."
)


def _password_forms(env_name: str, value: str) -> list[str]:
    """Every text of ``value`` that is, or may be, a password, as ``_secret_values`` reads it (as written and percent-decoded), for the check of
    ``_refuse_unsafe_address``. The value is already inside the strict grammar when this is called, so ``_refuse_odd`` cannot refuse here."""
    decoded, plain = _password_texts(value)
    forms = set(plain)
    for password in decoded:
        forms |= _decoded_forms(env_name, password)
    return sorted(forms)


def _env_snapshot(names: Iterable[str]) -> dict[str, str]:
    """ONE read of the caller's environment for a whole call: the variables a child gets (``CHILD_ENV``) and the passed ``names`` that are set (a
    name set to an empty text is kept, and the address check then refuses it). The secrets to hide, the canary test, the lock name and every child's environment come from this dict and
    never again from ``os.environ``, so a variable the caller changes while the run is going changes nothing."""
    return {k: os.environ[k] for k in (*CHILD_ENV, *names) if k in os.environ}


def _secret_values(
    names: Iterable[str], environ: Mapping[str, str] | None = None
) -> tuple[str, ...]:
    """The values of the passed environment variables (read from ``environ``, the snapshot of the call; ``os.environ`` when none is given), and the password inside them (see ``_password_texts``; each as written, percent-decoded
    until nothing changes, with ``+`` read as a space, and percent-encoded again as ``_encoded_forms`` writes it), longest first. Text that may show
    them is run through ``_masked``. ``ValueError`` (before anything runs) when a value is longer than ``MAX_VALUE_CHARS``, or when any of these
    texts but the encoded ones holds a quote mark, a backslash, a control character or a non-ASCII character (``_refuse_odd``): every text left is
    plain printable ASCII, so a print of it at any depth still holds it as written."""
    bases: set[str] = set()
    for name in names:
        value = (os.environ if environ is None else environ).get(name, "")
        if not value:
            continue
        if len(value) > MAX_VALUE_CHARS:
            raise ValueError(
                f"{name} is refused: its address is longer than {MAX_VALUE_CHARS} characters (no address is, and the runner would search every"
                " shown text for every form of it). Use a shorter address."
            )
        _refuse_odd(name, "its value", value)
        bases.add(value)
        decoded, plain = _password_texts(value)
        bases.update(plain)
        for password in decoded:
            for form in _decoded_forms(name, password):
                bases.add(form)
                bases |= _encoded_forms(form)
        if len(bases) > MAX_SECRETS:
            raise ValueError(
                f"{name} is refused: it gives more than {MAX_SECRETS} texts to search for (a password percent-encoded in many layers). Do not"
                " percent-encode the password more than once."
            )
    return tuple(sorted(bases, key=len, reverse=True))


def _prefix_table(pattern: str) -> list[int]:
    """The KMP failure table of ``pattern`` (entry ``i``: the length of the longest proper prefix of ``pattern[:i + 1]`` that is also its suffix)."""
    table = [0] * len(pattern)
    k = 0
    for i in range(1, len(pattern)):
        while k and pattern[i] != pattern[k]:
            k = table[k - 1]
        if pattern[i] == pattern[k]:
            k += 1
        table[i] = k
    return table


def _longest_overlap(pattern: str, table: Sequence[int], window: str) -> int:
    """The length of the longest prefix of ``pattern`` that is a suffix of ``window`` (``table`` is ``_prefix_table(pattern)``). One pass over ``window``
    (the cost is linear in ``len(window)``; the table work is amortised), no slice and no repeated compare. ``window`` must be shorter than ``pattern``."""
    k = 0
    for ch in window:
        while k and ch != pattern[k]:
            k = table[k - 1]
        if ch == pattern[k]:
            k += 1
    return k


def _fragment_spans(text: str, secret: str, hits: list[re.Match[str]]) -> list[tuple[int, int]]:
    """Spans of ``text`` that show a shortened ``secret``: pytest cuts a long text in an assertion line to ``head...tail`` (about 12 characters
    at the start and 13 at the end, checked with a real run), so the longest start of the secret that ends right before a ``...`` and the longest end of it that
    starts right after one are returned (each ``EDGE_MIN`` characters or longer, and shorter than the secret). ``hits`` are the ``...`` of the line,
    found once by ``_masked`` (not more than ``MAX_FRAGMENT_HITS``). Cost: the prefix tables of the secret and of its reverse are built once, O(len(secret)); each ``...`` then costs one pass
    over at most ``len(secret) - 1`` characters before it and one over as many after it (``_longest_overlap``), O(len(secret)) per ``...``, never a compare per candidate start."""
    spans: list[tuple[int, int]] = []
    top = len(secret) - 1
    if top < EDGE_MIN:  # a piece must be shorter than the secret and EDGE_MIN long
        return spans
    backwards = secret[::-1]
    head_table, tail_table = _prefix_table(secret), _prefix_table(backwards)
    for hit in hits:
        start = hit.start()
        end = start + (
            1 if text[start] == "\u2026" else 3
        )  # the width of the ellipsis that this hit is
        # the longest start of the secret that ends right before the ellipsis: the longest prefix of the secret that is a suffix of the text before it
        size = _longest_overlap(secret, head_table, text[max(0, start - top) : start])
        if size >= EDGE_MIN:
            spans.append((start - size, start))
        # the longest end of the secret that starts right after it: the same on the reversed secret and the reversed text after it
        size = _longest_overlap(backwards, tail_table, text[end : end + top][::-1])
        if size >= EDGE_MIN:
            spans.append((end, end + size))
    return spans


def _masked(text: str, secrets: Sequence[str]) -> str:
    """``text`` with every secret value replaced by a marker (pass_env values must never reach ``first_lines``, a result row or an error message).
    ``secrets`` are plain printable ASCII (``_secret_values`` refuses anything else), so each is found as it stands. A secret that pytest shortened
    to ``head...tail`` is masked by its pieces beside ``...`` too (see ``_fragment_spans``). Every span is found in the ORIGINAL text and then
    all are cut out at once, so a short secret that sits inside a longer one cannot break the match of the longer one. More than
    ``MAX_FRAGMENT_HITS`` ``...`` replace the whole text (no honest line has that many; hiding only the first ``MAX_FRAGMENT_HITS`` would leave a
    piece beside a later ``...`` readable). Cost: a line is scanned for each secret once, and each ``...`` costs one pass per secret over at most twice the length of that secret (``_fragment_spans``); (``...`` x secrets) above ``MAX_FRAGMENT_WORK`` (a count of pairs, not of characters; worst case about 2 x 10^8 character steps) replaces the whole line. A secret of one or two characters hides every such text in the line (garbling is the price of never leaving a short secret readable)."""
    chosen = tuple(v for v in secrets if v)
    if not chosen:
        return text
    dots = list(
        itertools.islice(_DOTS.finditer(text), MAX_FRAGMENT_HITS + 1)
    )  # found once for the whole line
    if len(dots) > MAX_FRAGMENT_HITS:
        return f"{MASK} (line with more than {MAX_FRAGMENT_HITS} '...' replaced: it cannot be checked for pieces of a value)"
    if len(dots) * len(chosen) > MAX_FRAGMENT_WORK:
        return f"{MASK} (line with too many '...' for the number of values replaced: it cannot be checked for pieces of a value)"
    hit = bytearray(len(text))
    for value in chosen:
        marked = 0  # the text before this index is already marked for this value: each character is marked once
        at = text.find(value)
        while at != -1:
            lo = max(at, marked)
            hit[lo : at + len(value)] = b"\x01" * (at + len(value) - lo)
            marked = at + len(value)
            at = text.find(value, at + 1)
    if dots:
        for value in chosen:
            for lo, hi in _fragment_spans(text, value, dots):
                hit[lo:hi] = b"\x01" * (hi - lo)
    out: list[str] = []
    for ch, bad in zip(text, hit, strict=True):
        if not bad:
            out.append(ch)
        elif not out or out[-1] != MASK:
            out.append(MASK)
    return "".join(out)


def _holds_secret(text: str, secrets: Sequence[str]) -> bool:
    """True when ``text`` holds one of ``secrets`` (the address, its password or a form of the password that ``_secret_values`` gives), or a
    shortened piece of one beside ``...``: exactly the texts in which ``_masked`` would put a marker."""
    return _masked(text, secrets) != text


def _own_text(text: str, fixed: str, secrets: Sequence[str]) -> str:
    """THE SECOND LAYER, in one place. ``text`` is one whole slot of caller-owned text (a test id, an exception class name the caller listed,
    the caller's ``expect``, a mutant name inside a message). It is given back unchanged, or, when it holds a secret, the fixed text ``fixed``
    is given back in its place. Nothing is ever cut out of the middle: a marker inside a text the reader knows (a file name of the repository)
    would show by its position what was removed. Python's own exception names and the runner's fixed words never go through here
    (a name of Python equal to a secret is handled by ``_shown_class``)."""
    return fixed if _holds_secret(text, secrets) else text


CLASS_HIDDEN = "[class not shown]"  # the replacement text for a class name that is not on the allowlist of this call
ID_HIDDEN = "[test id not shown]"  # the replacement text for a test id that is not made of the caller's own text
PARAMETERS_HIDDEN = (
    "[parameters hidden]"  # replaces the ``[...]`` part of a parametrized test id, always
)
EXPECT_HIDDEN = "[expect text not shown]"  # the replacement text for the caller's ``expect`` text when it holds a secret
MUTANT_HIDDEN = "[mutant name not shown]"  # the replacement text for a mutant name inside a message when it holds a secret
ASSERT_SHOWN = "assert"  # the fixed word shown for a failing line that starts with a bare ``assert`` (pytest writes no class name for it)
_BARE_ASSERT = re.compile(r"(?:E\s+)?assert(?:\s|$)")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# every exception class of Python itself (``AssertionError``, ``KeyError``, ...) and the one class pytest raises for ``pytest.fail`` and "DID NOT RAISE"
_BUILT_IN_CLASSES = frozenset(
    name
    for name, thing in vars(builtins).items()
    if isinstance(thing, type) and issubclass(thing, BaseException)
) | {"Failed"}
_DEFINED = re.compile(r"\b(?:def|class) ([A-Za-z_][A-Za-z0-9_]*)")


@dataclass(frozen=True)
class _Shown:
    """What one call of ``run_mutants`` may show of a child's text while a passed variable has a value: an ALLOWLIST of text that the caller
    or Python owns. ``classes``: built-in exception names, pytest's ``Failed``, the ``crash_type`` of this call's mutants and the caller's
    ``shown_classes``. ``files``: the file part of a test id as the JUnit file writes it, mapped to the caller's own ``tests`` entry in that form.
    ``names``: per such file, every name that follows ``def`` or ``class`` in the snapshot copy of that file. ``secrets`` empty means that no
    passed variable has a value: nothing is replaced."""

    secrets: tuple[str, ...] = ()
    classes: frozenset[str] = _BUILT_IN_CLASSES
    files: Mapping[str, str] = field(default_factory=dict)
    names: Mapping[str, frozenset[str]] = field(default_factory=dict)


def _checked_shown_classes(names: Iterable[str]) -> tuple[str, ...]:
    """``names`` (the caller's ``shown_classes``) if every one is a plain ASCII identifier, else ``ValueError`` (a bare string is a ``TypeError``)."""
    if isinstance(names, str):
        raise TypeError("shown_classes is a sequence of class names, not one string")
    chosen = tuple(names)
    for name in chosen:
        if not isinstance(name, str) or not _IDENTIFIER.fullmatch(name):
            raise ValueError("shown_classes holds exception class names only (plain identifiers)")
    return chosen


def _id_form(test_path: str) -> str:
    """A ``tests`` entry in the form a test id uses for its file part: ``/`` between the parts, no ``.`` part and no ``.py`` (``tests/test_x.py``
    and ``./tests/test_x.py`` both give ``tests/test_x``, which is what pytest writes for either spelling)."""
    return PurePosixPath(test_path.replace("\\", "/")).as_posix().removesuffix(".py")


def _shown_for(
    secrets: Sequence[str],
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    shown_classes: Sequence[str],
    snapshot: Path,
) -> _Shown:
    """The allowlist of one call (see ``_Shown``), built once from the caller's arguments and the snapshot of the caller's test files."""
    names: dict[str, frozenset[str]] = {}
    for test in tests:
        try:
            text = _inside(snapshot, test).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = (
                ""  # a file that cannot be read gives no name: its test ids show the file part only
            )
        names[_id_form(test)] = frozenset(_DEFINED.findall(text))
    return _Shown(
        tuple(secrets),
        _BUILT_IN_CLASSES | {m.crash_type for m in mutants if m.crash_type} | set(shown_classes),
        {_id_form(test): _id_form(test) for test in tests},
        names,
    )


def _shown_class(raw: str, shown: _Shown) -> str:
    """What stands for the exception class of the ``E`` line ``raw``. A line that starts with a bare ``assert`` gives the fixed word
    ``ASSERT_SHOWN``. Otherwise the leading exception class name is given when it is on the allowlist of this call (``shown.classes``), else
    ``CLASS_HIDDEN``. ONE equality rule for every name of ``shown.classes`` (a name of Python, a ``crash_type``, an entry of ``shown_classes``): a name
    that is equal to a secret value in any letter case (``casefold``) is ``CLASS_HIDDEN``: a password that is ``TimeoutError`` or ``timeouterror``
    must not come back as the class of a failing line. (``_refuse_unsafe_address`` refuses such a password before any run, so this rule is the
    second layer.) A password that is only a PIECE of a name of Python (``Err``) does not hide it: the name is public text that tells nothing of
    the password, and hiding every name that holds a short password would blank all of them. A name the caller owns also goes through the
    second layer (``_own_text``): when it HOLDS a secret (a piece of the name does too), ``CLASS_HIDDEN`` is given, never a part of the name. So
    a piece of a name hides a caller's name and does not hide a name of Python: that difference is on purpose (the caller's names are the caller's
    own text, which the second layer treats like every other caller text). One bit is left on purpose: a hidden name of the caller shows that
    the name equals the password or holds a piece of it (the same channel as a test id or an ``expect`` slot); a reader cannot read the password
    from an equal name, and the hiding of a name that holds only a piece tells that the piece is in that name."""
    if _BARE_ASSERT.match(raw.strip()):
        return ASSERT_SHOWN
    head = _leading_class(raw) if raw else ""
    if head not in shown.classes:
        return CLASS_HIDDEN
    folded = head.casefold()  # ONE rule for every name of ``shown.classes``: equal to a secret up to letter case hides the name
    if any(secret.casefold() == folded for secret in shown.secrets):
        return CLASS_HIDDEN
    if head in _BUILT_IN_CLASSES:
        return head
    return _own_text(head, CLASS_HIDDEN, shown.secrets)


def _shown_line(raw: str, shown: _Shown, expect: str = "") -> str:
    """What the caller gets to see of the first ``E`` line of a child run. With no passed value: the line as it is. With one, the child's text is
    replaced by (a) what ``_shown_class`` gives, (b) the fixed words that say whether the caller's ``expect`` text was in the line, and (c) the
    caller's own ``expect`` text, whole, or ``EXPECT_HIDDEN`` when that text holds a secret (``_own_text``). The fixed words of (b) are given in
    both cases: they say whether the caller's text was in the child's line, which the caller's own judge verdict says too. An empty line stays empty."""
    if not any(shown.secrets):
        return raw
    if not raw:
        return ""
    word = ""
    if expect:
        found = " [expect found] " if expect in raw else " [expect not found] "
        word = found + _own_text(expect, EXPECT_HIDDEN, shown.secrets)
    return f"{_shown_class(raw, shown)}{word}"


def _shown_id(test_id: str, shown: _Shown, own_names: Iterable[str] = ()) -> str:
    """The test id of a row as the caller sees it. With no passed value: as it is. With one: ``ID_HIDDEN`` unless the id is made of the caller's own
    text. The file part must equal one of the caller's ``tests`` entries (the caller's text is printed, never the child's). Every name after it (a
    test class, then the test function) must follow ``def`` or ``class`` in the snapshot copy of that file, or be one of ``own_names`` (the
    mutant's ``only_test`` and the function of its ``pinned`` id). The ``[...]`` part of a parametrized test is always replaced by
    ``PARAMETERS_HIDDEN``. The caller's text then goes through the second layer (``_own_text``): an id that holds a secret is ``ID_HIDDEN`` as a
    whole, never an id with a piece cut out."""
    if not any(shown.secrets):
        return test_id
    base, bracket, _rest = test_id.partition("[")
    path, sep, function = base.partition("::")
    for file_part, text in shown.files.items():
        if path == file_part:
            classes: list[str] = []
        elif path.startswith(file_part + "/"):
            classes = path[len(file_part) + 1 :].split(
                "/"
            )  # the test classes between the file and the function
        else:
            continue
        allowed = shown.names.get(file_part, frozenset()) | set(own_names)
        if sep and function and all(name in allowed for name in (*classes, function)):
            tail = "".join(f"/{name}" for name in classes)
            end = PARAMETERS_HIDDEN if bracket else ""
            own = _own_text(f"{text}{tail}::{function}", ID_HIDDEN, shown.secrets)
            return own if own == ID_HIDDEN else own + end
    return ID_HIDDEN


class CanaryFailed(RuntimeError):
    """The unmutated copy no longer passes after a mutant run (shared database). ``rows`` holds the rows of the mutants judged so far."""

    rows: tuple[tuple[str, Verdict, str, bool], ...] = ()


_LOCK_HELD = (
    errno.EAGAIN,
    errno.EACCES,
    errno.EDEADLK,
)  # what a non-blocking lock reports when another holder has it (EWOULDBLOCK equals EAGAIN)


_RUN_END_IN_WORDS = {
    TIMED_OUT: "the run timed out",
    REAPED_ELSEWHERE: "the run was reaped by another waiter, its exit status is lost",
}


def _run_end(rc: int) -> str:
    """How a failed canary run ended, in words: the two internal codes (``TIMED_OUT``, ``REAPED_ELSEWHERE``) are not exit codes."""
    return _RUN_END_IN_WORDS.get(rc, f"exit code {rc}")


_LOCK_DIR_WAY_OUT = "remove it as its owner, or give the run a temp folder of its own with TMPDIR"


def _own_private_dir(path: str) -> bool:
    """True when ``path`` is a real folder (not a link) of this user with no access for group or others."""
    try:
        info = os.lstat(path)
    except OSError:
        return False
    return (
        stat.S_ISDIR(info.st_mode)
        and info.st_uid == os.getuid()
        and not stat.S_IMODE(info.st_mode) & 0o077
    )


def _dir_problem(info: os.stat_result) -> str:
    """Why a folder that was looked at (``lstat`` or ``fstat``) is not a private folder of this user, or ``""`` when it is: it is not a real folder
    (a link is not followed), it belongs to another user, or it is open to group or others (it must have mode 0700). POSIX only. THE ONE
    CHECK for every folder this runner makes: the lock folder, the temp folder of a run, its snapshot folder and the folder of the pytest settings file."""
    if not stat.S_ISDIR(info.st_mode):
        return "is not a folder"
    if info.st_uid != os.getuid():
        return "belongs to another user"
    if stat.S_IMODE(info.st_mode) & 0o077:
        return "is open to group or others (it must have mode 0700)"
    return ""


def _refuse_unless_private(path: Path, what: str) -> None:
    """``RuntimeError`` unless ``path`` (``what`` of this run) is a real folder of this user with mode 0700 (``lstat``: a link is not followed;
    ``_dir_problem``). Called when a folder is made and after every rebuild of the temp copy. Not on Windows, whose mode bits mean nothing."""
    if _IS_WINDOWS:
        return
    problem = ""
    try:
        problem = _dir_problem(os.lstat(path))
    except OSError as exc:
        problem = f"could not be looked at ({type(exc).__name__})"
    # raised outside the ``except`` block: the error keeps no other exception in its chain
    if problem:
        raise RuntimeError(f"the {what} of this run {problem}")


def _make_private_dir(path: Path, what: str) -> None:
    """Make the folder ``path`` (it must not exist, ``FileExistsError`` otherwise, also for a link) with mode 0700 whatever the umask, then
    check it (``_refuse_unless_private``). ``os.mkdir`` takes the mode and the umask can only take bits away; ``chmod`` then puts them back."""
    os.mkdir(path, 0o700)
    if not _IS_WINDOWS:
        os.chmod(path, 0o700)
    _refuse_unless_private(path, what)


def _make_private_temp_dir(prefix: str, what: str) -> Path:
    """A new folder in the temp folder (``tempfile.mkdtemp``: mode 0700 minus what the umask takes away), checked (``_refuse_unless_private``) like
    every other folder of the run. A umask that takes OWNER bits away (0277, say) would give a folder this user cannot use: those bits are put
    back to 0700 first (the mode is never widened for group or others). A folder that fails the check is removed again before the error is raised."""
    path = Path(tempfile.mkdtemp(prefix=prefix))
    checked = False
    try:
        if not _IS_WINDOWS and stat.S_IMODE(os.lstat(path).st_mode) & 0o700 != 0o700:
            os.chmod(path, 0o700)
        _refuse_unless_private(path, what)
        checked = True
    finally:
        if not checked:
            shutil.rmtree(path, ignore_errors=True)
    return path


def _make_dirs(top: Path, path: Path) -> None:
    """Make ``path`` (inside ``top``) and every missing folder between them, each by ``_make_private_dir``: mode 0700 whatever the umask, and checked
    (``mkdir(parents=True)`` would make the ones in between with the default mode). A part that exists already is left as it is, not checked
    (it was made by this runner earlier in the same call, or it is a folder of the caller's own tree that a test path runs through); a part
    that exists and is not a folder is ``FileExistsError``."""
    here = top.resolve()
    for part in path.relative_to(here).parts:
        here = here / part
        try:
            _make_private_dir(here, "folder of the copy")
        except FileExistsError:
            if not here.is_dir():
                raise


def _empty_dir(folder: Path) -> None:
    """Remove everything INSIDE ``folder`` and keep ``folder`` itself: it was made private once and a new folder under the same name would have the
    default mode. Errors are ignored (a Windows file lock may hold a file for a moment): what is left makes the rebuild fail and be retried."""
    try:
        children = list(os.scandir(folder))
    except OSError:
        return
    for child in children:
        if child.is_dir(follow_symlinks=False):
            shutil.rmtree(child.path, ignore_errors=True)
        else:
            with contextlib.suppress(OSError):
                os.unlink(child.path)


def _file_problem(info: os.stat_result) -> str:
    """Why a file that was looked at (``fstat``) is not a private file of this user, or ``""`` when it is: it is not a regular file, it belongs to
    another user, it is open to group or others or runs (it must have mode 0600 or narrower), or it has another name (a hard link). POSIX only.
    THE ONE CHECK for every file this runner makes: the lock file, the pytest settings file and the result file of a run."""
    if not stat.S_ISREG(info.st_mode):
        return "is not a regular file"
    if info.st_uid != os.getuid():
        return "belongs to another user"
    if stat.S_IMODE(info.st_mode) & 0o177:
        return "is open to group or others (it must have mode 0600 or narrower)"
    if info.st_nlink > 1:
        return "has more than one name"
    return ""


def _narrowable(info: os.stat_result) -> bool:
    """Whether a file that was opened (``fstat``) may be put back to mode 0600: it is a regular file, it is ours and it has no second name. A file
    that fails one of these three is only refused (``_file_problem``): a mode change on it would reach a file that is not ours alone (a hard link
    shares its inode with the other name). POSIX only."""
    return stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and info.st_nlink == 1


def _make_private_file(path: Path, what: str = "private file") -> None:
    """Make (or empty) the file ``path`` (``what`` of this run) with mode 0600 whatever the umask, without following a link, then check it
    (``_file_problem``, on the open descriptor, so the file that was checked is the file that was made), and only THEN empty it (``ftruncate``): a
    file that fails the check (a second name, another owner) keeps its content and its mode (the mode is changed only on a regular file of this
    user with one name, ``_narrowable``). The open does not wait for a reader (``O_NONBLOCK``): a named pipe under the name fails at once (no
    reader) or is refused as not a regular file (a reader), where a plain open for writing would block for ever. The refusal for a file of another
    user is reached only by root or when that file is writable by this user: any other caller already fails at the open with ``PermissionError``.
    A result file or a settings file that the runner names is made here before the child gets its path."""
    problem = ""
    flags = os.O_WRONLY | os.O_CREAT
    # a link under the name is refused (``ELOOP``), not followed
    flags |= getattr(os, "O_NOFOLLOW", 0)
    # a named pipe under the name must not block the open (POSIX only: Windows has no such flag and no named pipes here)
    flags |= getattr(os, "O_NONBLOCK", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if not _IS_WINDOWS:
            # ``chmod`` on the descriptor: ``os.fchmod`` is unknown to mypy on Windows before Python 3.13
            if _narrowable(os.fstat(fd)):
                os.chmod(fd, 0o600)
            problem = _file_problem(os.fstat(fd))
        if not problem:
            os.ftruncate(fd, 0)
    finally:
        os.close(fd)
    # raised outside the ``try``: the error keeps no other exception in its chain
    if problem:
        raise RuntimeError(f"the {what} of this run {problem}")


def _lock_dir() -> Path:
    """Where the folder of the lock files lies. POSIX: ``hadavin_mutation_locks_<uid>`` inside ``XDG_RUNTIME_DIR`` when that variable names a real
    folder of this user that is closed to group and others (no other user can then put a folder under the name first), else inside the temp
    folder. Windows: the temp folder itself; this tool checks nothing about that folder there."""
    base = Path(tempfile.gettempdir())
    if _IS_WINDOWS:
        return base
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    if runtime and os.path.isabs(runtime) and _own_private_dir(runtime):
        base = Path(runtime)
    return base / f"hadavin_mutation_locks_{os.getuid()}"


def _refuse_lock_folder_in_tree(root: Path) -> None:
    """``RuntimeError`` when the lock folder lies inside ``root``, the tree under test. That happens when the temp folder that Python picks is
    the working folder (``tempfile.gettempdir()`` falls back to it when no temp folder can be written), or ``TMPDIR`` points into the tree. Lock
    files would then be left in the caller's own tree."""
    lock = _lock_dir().resolve()
    base = Path(root).resolve()
    if lock.is_relative_to(base):  # also true when the two are the same folder
        raise RuntimeError(
            "the lock folder of this run lies inside the tree under test: give the run a temp folder outside the tree with TMPDIR"
        )


def _open_lock_dir() -> int | None:
    """The lock folder, made if it is missing (mode 0700) and opened: a descriptor that the lock file is then created under (``dir_fd``), so the
    folder that was checked is the folder that is used. ``RuntimeError`` when the folder cannot be made or opened, or when what was opened is not a
    real folder (a symbolic link is not followed) of this user with no access for group or others. So a folder that someone else put under the name
    is REFUSED, it is not prevented: the run stops and the message names the way out. Windows: ``None`` (the lock file is opened by its path)."""
    path = _lock_dir()
    if _IS_WINDOWS:
        return None
    fd = -1
    problem = ""
    try:
        with contextlib.suppress(FileExistsError):  # an existing folder is checked below
            os.mkdir(path, 0o700)
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        info = os.fstat(fd)
    except OSError as exc:
        problem = f"could not be made or opened ({type(exc).__name__})"
    else:
        problem = _dir_problem(info)
    if (
        problem
    ):  # raised outside the ``except`` block: the error keeps no other exception in its chain
        if fd != -1:
            os.close(fd)
        raise RuntimeError(f"the lock folder of this run {problem}: {_LOCK_DIR_WAY_OUT}")
    return fd


if sys.platform == "win32":
    import msvcrt

    def _lock_or_raise(fd: int) -> None:
        """Lock the first byte of the open lock file without waiting (``OSError`` when another run holds it)."""
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
else:
    import fcntl

    def _lock_or_raise(fd: int) -> None:
        """Lock the open lock file without waiting (``OSError`` when another run holds it)."""
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


_NO_ACCESS = "this user may not open it (it belongs to another user, the temp folder is closed to this user, or the temp folder is read-only; give the run a temp folder of its own with TMPDIR)"
_NOT_OPENED_BECAUSE = {
    errno.ELOOP: "it is a symbolic link",
    errno.EACCES: _NO_ACCESS,
    errno.EPERM: _NO_ACCESS,
    errno.EISDIR: "it is a folder",
    errno.ENOTDIR: "a part of its path is not a folder",
}


def _why_not_opened(code: int | None) -> str:
    if code is None:
        return f"errno {code}"
    return _NOT_OPENED_BECAUSE.get(code, f"errno {code}")


def _check_lock_file(fd: int) -> None:
    """Refuse (``RuntimeError``) a lock file that is not a regular file of the current user with a mode no wider than 0600 (not on Windows, whose
    mode bits mean nothing): a file left by an older version or made by hand with wider rights could be written by another user of the temp folder."""
    if _IS_WINDOWS:
        return
    if _file_problem(os.fstat(fd)):
        raise RuntimeError(
            "the lock file of this run is not a regular file of this user with one name, mode 0600 or narrower (remove it as its owner, or give the run a temp folder of its own with TMPDIR), so the run cannot be proven alone on its database"
        )


@contextlib.contextmanager
def _one_run_per_database(values: Sequence[str]) -> Iterator[None]:
    """Hold an exclusive lock for the whole run. The lock file lies in the lock folder (``_open_lock_dir``) and is named by the first 16 hex
    digits of a SHA-256 of host, host address, port and database name of the addresses (``_address_parts``; a password is never read for it).

    A second runner with the same lock folder and the same spelling of those four parts gets a ``RuntimeError``. THIS IS A MATCH ON SPELLING, not
    on the database: ``localhost`` and ``127.0.0.1``, or a port written or left out, give two names, and that second runner is NOT refused.
    A runner of another user, with another temp folder or on another machine is not seen either. Values outside the grammar share one name.

    The file is created under the opened folder (``dir_fd``), without following a symbolic link, without blocking (a FIFO under the name is
    refused instead of hanging the run) and with mode 0600. It is checked after opening (a regular file of this user, one name, mode 0600 or
    narrower) and never deleted: one empty file per distinct name stays. A file that cannot be opened or locked for another reason than "held
    by another run" is a ``RuntimeError`` with its own message; a folder on a network file system whose ``flock`` fails is one such case."""
    digest = hashlib.sha256(
        "\0".join(sorted(_address_parts(v) for v in values)).encode()
    ).hexdigest()[:16]
    name = f"hadavin_mutation_{digest}.lock"
    # O_NONBLOCK: a FIFO planted under the name would block an open for reading for ever (it is then refused by the fstat check)
    # read-only on POSIX (``flock`` needs no write access, so a file narrowed to 0400 still works); Windows locks a byte, which needs write access
    flags = (
        (os.O_RDWR if _IS_WINDOWS else os.O_RDONLY)
        | os.O_CREAT
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0)
    )
    problem = ""  # every refusal below is raised outside its ``except`` block: the error keeps no other exception in its chain
    with _signals_held():  # a termination signal waits until the folder descriptor is closed again
        folder = _open_lock_dir()
        try:
            try:
                if folder is None:
                    fd = os.open(_lock_dir() / name, flags, 0o600)
                else:
                    fd = os.open(name, flags, 0o600, dir_fd=folder)
                try:
                    handle = os.fdopen(fd, "r+b" if _IS_WINDOWS else "rb")
                except OSError:
                    os.close(fd)  # no file object took the descriptor over
                    raise
            except OSError as exc:
                problem = (
                    f"could not be opened ({type(exc).__name__}): {_why_not_opened(exc.errno)}"
                )
        finally:
            if folder is not None:
                os.close(folder)
    if problem:
        raise RuntimeError(
            f"the lock file of this run {problem}, so the run cannot be proven alone on its database"
        )
    with handle:
        _check_lock_file(handle.fileno())
        try:
            _lock_or_raise(handle.fileno())
        except OSError as exc:
            problem = (
                "another mutation run that uses the same lock folder has the same passed database address: give each run a database of its own"
                if exc.errno in _LOCK_HELD
                else f"the lock file of this run could not be locked ({type(exc).__name__}, errno {exc.errno}), so the run cannot be proven alone on its database"
            )
        if problem:
            raise RuntimeError(problem)
        yield  # the lock goes with the closed file


def _pytest(
    cwd: Path,
    tests: Sequence[str],
    junit: Path,
    timeout: float,
    *,
    plugin: str = "",
    env_names: Sequence[str] = (),
    environ: Mapping[str, str] | None = None,
    hosts: Sequence[str] = THROWAWAY_HOSTS,
) -> int:
    # an ALLOWLIST, not os.environ: a mutant run must not see a database DSN, a token or any other secret of the caller; PYTHONPATH also holds the tree root (tests may import tools.*)
    for operand in tests:  # the one place the caller's strings reach the argv: refuse here too, not only where the paths are first checked
        _plain_operand(operand)
    # ``environ`` is the snapshot that ``run_mutants`` took once at its start (see ``_env_snapshot``); a direct call without one reads ``os.environ`` now
    source = os.environ if environ is None else environ
    env = {k: source[k] for k in CHILD_ENV if k in source}
    for name in _checked_env_names(env_names):
        if name in source:
            # the one place a passed variable reaches a child: the address is checked HERE too, so no caller of this function can hand
            # an unchecked address to a child (``hosts`` is the caller's ``throwaway_hosts``)
            _refuse_unsafe_address(name, source[name], hosts)
            env[name] = source[name]
    env.update(CHILD_FIXED_ENV)
    load = ["-p", _plugin_module(plugin)] if plugin else []
    env["PYTHONPATH"] = os.pathsep.join([str(cwd / "src"), str(cwd)])
    # an EMPTY ini file inside the copy is the config file and the copy is the rootdir: a planted pytest.ini, tox.ini, setup.cfg or
    # pyproject.toml in a parent folder (the shared temp folder, for one) is never picked up
    # the ini file lives in a private temp folder of its own, never in the caller's working folder
    ini_dir: Path | None = None
    proc: subprocess.Popen[bytes] | None = None
    try:
        with _signals_held():
            ini_dir = _make_private_temp_dir("mutant_ini_", "folder of the pytest settings file")
        ini = ini_dir / "mutant_run.ini"
        # an empty settings file, mode 0600
        _make_private_file(ini, "pytest settings file")
        # the result file pytest fills: made by the runner (mode 0600), not by the umask of the caller
        _make_private_file(junit, "result file")
        cmd = [
            sys.executable,
            *("-m", "pytest", "-q", "-p", "no:cacheprovider", "--noconftest", *load),
            *("-x", "-c", str(ini), f"--rootdir={cwd}", f"--junitxml={junit}", *tests),
        ]
        # own process group (POSIX session / Windows group): on a timeout the whole tree dies, not only pytest (a test may have started psql or a server)
        # the child's own console output (stdout and stderr) goes to the null device: the runner never reads or prints it
        # a termination signal during the start is held until ``proc`` is known, then raised inside this ``try``: the child is killed
        with _signals_held():
            # S603 stays a listed exception: the argument list holds the caller's test paths and the junit path, so ruff cannot see it as a literal. Fixed argv (our own interpreter), no shell, caller strings only as pytest operands that ``_plain_operand`` has checked
            # both keywords are always given and chosen by platform: a new process group on Windows, a new session elsewhere
            proc = subprocess.Popen(  # noqa: S603
                cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=_NEW_PROCESS_GROUP if _IS_WINDOWS else 0, start_new_session=not _IS_WINDOWS,
            )  # fmt: skip
        try:
            _wait_unreaped(proc, timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            # a mutant that loops forever is reported, never allowed to hang the run
            return TIMED_OUT
        except _ReapedElsewhere:
            return REAPED_ELSEWHERE  # ``proc`` knows it has ended (poll), so there is no group to signal and nothing to kill
        # a normal exit can leave a background process of the run behind: on POSIX it is killed too. Not on Windows: the parent is
        # gone, taskkill /T finds no children, and the pid may already belong to an unrelated process
        if not _IS_WINDOWS:
            _kill_tree(proc)
        return proc.wait()
    except BaseException:  # Ctrl-C (KeyboardInterrupt) or any other exit while waiting: never leave a spinning mutant behind
        if proc is not None and proc.returncode is None:
            _kill_tree(proc)
        raise
    finally:
        with _signals_held():
            if ini_dir is not None:
                shutil.rmtree(ini_dir, ignore_errors=True)


def _wait_unreaped(proc: subprocess.Popen[bytes], timeout: float) -> None:
    """Return when ``proc`` has ended; raise ``subprocess.TimeoutExpired`` after ``timeout`` seconds. On POSIX the ended leader is NOT
    reaped (``os.waitid`` with ``WNOWAIT``, polled), so the later group kill cannot hit a reused pid; ``_kill_tree`` reaps it. If someone
    else reaped it first (SIGCHLD ignored) its exit status is gone: ``proc`` is told it has ended, and ``_ReapedElsewhere`` is raised.
    Windows,
    and a POSIX without ``os.waitid`` (macOS): ``proc.wait``, which reaps. Tests patch this function to steer the wait."""
    if _IS_WINDOWS or not hasattr(os, "waitid"):
        proc.wait(timeout=timeout)
        return
    deadline = time.monotonic() + timeout
    while True:
        try:
            if os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                return
        except ChildProcessError:  # someone else reaped it already (SIGCHLD ignored): let ``proc`` learn it, or ``_kill_tree`` would signal a reaped group
            proc.poll()  # sets returncode (0, a guess) so ``_kill_tree`` will not signal a reaped group
            raise _ReapedElsewhere from None
        left = deadline - time.monotonic()
        if left <= 0:
            raise subprocess.TimeoutExpired(proc.args, timeout)
        time.sleep(min(WAIT_POLL, left))


def _kill_tree(proc: subprocess.Popen[bytes]) -> None:
    """Kill ``proc`` and everything it started (POSIX: its process group; Windows: ``taskkill /T``). A failing tree kill (no ``taskkill``
    on the PATH, its own timeout, ``PermissionError`` from ``killpg``) never skips the kill of the child itself. The group is not
    killed when the leader was already reaped (its pid may be someone else's by now), except where ``os.waitid`` is missing. A
    termination signal during the kill is held until it is done."""
    with _signals_held():
        try:
            if _IS_WINDOWS:
                # S603 stays a listed exception: the pid is our own child's, but the list is not a literal to ruff. No shell; the program path is built from SystemRoot (``_taskkill``), which is the caller's environment, as trusted as PATH
                subprocess.run(  # noqa: S603
                    [_taskkill(), "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=TREE_KILL_TIMEOUT,
                )  # fmt: skip
            elif proc.returncode is None or not hasattr(os, "waitid"):
                os.killpg(proc.pid, signal.SIGKILL)
        # ProcessLookupError and PermissionError are OSErrors
        except (OSError, subprocess.TimeoutExpired):
            pass
        finally:
            proc.kill()  # the child itself, always
            proc.wait()


# the signals that end a run like Ctrl-C does (POSIX; SIGHUP does not exist on Windows)
_TERMINATING = ("SIGTERM", "SIGHUP")
# State of the termination handling. Only the main thread changes it (the handlers run there, and ``_signals_held`` does nothing in
# another thread): ``depth`` counts the steps that must not be cut short, ``pending`` is the first signal that arrived during one,
# ``ended`` says that a signal has already ended the run (every later one is remembered and dropped: the cleanup is under way),
# ``active`` says that a ``run_mutants`` call of this thread is under way (one at a time: the counters are shared, see ``run_mutants``).
_SIGNALS = {"depth": 0, "pending": 0, "ended": 0, "active": 0}


def _signals_active() -> bool:
    return not _IS_WINDOWS and threading.current_thread() is threading.main_thread()


@contextlib.contextmanager
def _signals_held() -> Iterator[None]:
    """POSIX main thread: a termination signal that arrives inside the block does not raise there; the first one is raised as
    ``SystemExit`` when the outermost block ends (unless a signal has already ended the run). Used around the start of the child, the
    tree kill and the removal of temp folders. Elsewhere it changes nothing."""
    if not _signals_active():
        yield
        return
    _SIGNALS["depth"] += 1
    try:
        yield
    finally:
        _SIGNALS["depth"] -= 1
        if _SIGNALS["depth"] == 0 and _SIGNALS["pending"]:
            number, _SIGNALS["pending"] = _SIGNALS["pending"], 0
            if not _SIGNALS["ended"]:
                _SIGNALS["ended"] = 1
                raise SystemExit(128 + number)


@contextlib.contextmanager
def _terminations_raise() -> Iterator[None]:
    """POSIX main thread: SIGTERM and SIGHUP raise ``SystemExit(128 + signal number)`` inside the block, so the cleanup in ``finally`` and in
    ``_pytest`` runs (a stopped runner would otherwise leave the pytest tree and the temp folders behind). The old handlers are restored;
    a signal that was ignored on entry (``nohup``) stays ignored. Elsewhere (Windows, another thread) it changes nothing."""
    if not _signals_active():
        yield
        return
    # refused BEFORE anything is changed: the counters of the outer call stay as they are
    if _SIGNALS["active"]:
        raise RuntimeError(
            "run_mutants is not re-entrant: a second call inside a running one is refused"
        )

    def stop(signum: int, _frame: FrameType | None) -> None:
        if _SIGNALS["depth"] or _SIGNALS["ended"]:
            _SIGNALS["pending"] = _SIGNALS["pending"] or signum
            return
        _SIGNALS["ended"] = 1
        raise SystemExit(128 + signum)

    previous: dict[int, Callable[[int, FrameType | None], object] | int | None] = {}
    _SIGNALS.update(depth=0, pending=0, ended=0, active=1)
    try:
        for name in _TERMINATING:
            sig = getattr(signal, name, None)
            if sig is None or signal.getsignal(sig) is signal.SIG_IGN:
                continue
            previous[sig] = signal.signal(sig, stop)
        yield
    finally:
        for sig, old in previous.items():
            signal.signal(sig, signal.SIG_DFL if old is None else old)
        _SIGNALS.update(depth=0, pending=0, ended=0, active=0)


def run_mutants(
    root: Path,
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    *,
    extra_dirs: Sequence[str] = ("tests/fixtures",),
    only: Sequence[str] = (),
    timeout: float = DEFAULT_TIMEOUT,
    baseline_timeout: float | None = None,
    on_result: Callable[[tuple[str, Verdict, str, bool]], None] | None = None,
    first_lines: dict[str, str] | None = None,
    conftest: str = "",
    pass_env: Sequence[str] = (),
    forbid_skips: bool | None = None,
    throwaway_hosts: Sequence[str] = THROWAWAY_HOSTS,
    shown_classes: Sequence[str] = (),
) -> list[tuple[str, Verdict, str, bool]]:
    """Run every mutant and return one row per mutant: ``(name, verdict, failing test id, good)``. The module docstring explains each keyword.

    Refused before any folder is made: a bad path, keyword or address is a ``ValueError`` (a bare string in place of a list is a ``TypeError`` for
    ``tests``, ``extra_dirs``, ``only``, ``pass_env``, ``throwaway_hosts`` and ``shown_classes``).
    The module docstring lists these refusals in the order of the code.

    A ``RuntimeError`` is raised when:

    - the unmutated copy fails, times out, or its exit status was collected by another part of the program;
    - under ``forbid_skips``, the unmutated copy skips a test or leaves no readable result file;
    - another runner holds the lock for the same address;
    - the lock folder or the lock file is not this user's own private one, or cannot be opened or locked;
    - the copy cannot be rebuilt for a canary run;
    - a canary run fails (the subclass ``CanaryFailed``, whose ``rows`` hold the rows so far);
    - the call is made while another call is running in the same thread.

    Rows that are errors, not exceptions: a mutant whose temp copy cannot be built is ``(name, ERROR, "SETUP FAILED: <error class>", False)``.
    A mutant run longer than ``timeout`` seconds is ``(name, ERROR, "TIMEOUT", False)``. The baseline run gets ``baseline_timeout`` (default:
    ``timeout``; 0 is a real, immediate timeout). ``on_result`` is called with each row as soon as that mutant finishes.

    ``first_lines``, if given, is emptied at the start and belongs to this call. It then gets, per mutant name, the first failure line of each
    judged row that has one. While a passed variable has a value the entry is NOT the line of the tests: it is the exception class name when it
    is on the allowlist, then the fixed words ``[expect found]`` or ``[expect not found]``, then the caller's ``expect`` text. ``crash_type`` is always checked against the child's real line, inside the runner.

    ``conftest``, ``pass_env`` and ``forbid_skips`` are opt-in. ``throwaway_hosts`` is the exact list of hosts (or unix socket folders) the
    address of a passed variable may name; the runner cannot check that a database is disposable, so add a host only when you know it is.
    ``shown_classes`` names exception classes that may be shown while a passed variable has a value. A SIGTERM or SIGHUP during the call
    ends it like Ctrl-C.

    NOT re-entrant: on POSIX in the main thread a ``run_mutants`` call made while another is running in the same thread (from ``on_result``,
    say) raises ``RuntimeError`` and leaves the outer call untouched. Calls in other threads do not share that state; the signal handling is
    then off."""
    with _terminations_raise():
        return _run_mutants(
            root, mutants, tests, extra_dirs, only, timeout, baseline_timeout, on_result,
            {} if first_lines is None else first_lines, conftest, pass_env, forbid_skips, throwaway_hosts, shown_classes,
        )  # fmt: skip


def _refuse_links_out(base: Path) -> None:
    """Refuse a RELATIVE symlink of the snapshot whose target lies outside ``base`` (``ValueError``). The snapshot and every copy of it sit
    side by side in the shared temp folder, so such a link (``../../x`` out of ``src``) would resolve to a neighbour in that folder, not to
    what it meant in the caller's tree. An absolute link keeps its meaning in a copy and stays a link (it is the caller's explicit choice)."""
    real_base = os.path.realpath(base)
    for dirpath, dirs, files in os.walk(base):  # os.walk does not enter a linked folder
        for name in (*dirs, *files):
            link = os.path.join(dirpath, name)
            if not os.path.islink(link):
                continue
            target = os.readlink(link)
            if os.path.isabs(target):
                continue
            hop = os.path.normpath(os.path.join(os.path.realpath(dirpath), target))
            if os.path.commonpath([real_base, hop]) != real_base:
                raise ValueError(
                    f"a relative link points outside the tree: {os.path.relpath(link, base)!r}"
                )


def _refuse_junctions(root: Path, rel: str) -> None:
    """Refuse a Windows junction at ``root / rel`` (``ValueError``): the folder itself, any part of the path ``rel`` (``tests`` in
    ``tests/fixtures``) and anything below it. ``shutil.copytree(symlinks=True)`` does not see a junction as a link (Python
    3.12 ``islink`` is False for it), follows it and copies the target as a real folder, so the snapshot would hold files from outside the
    tree. Looked at in the CALLER's tree before the copy: afterwards nothing tells the copy from a real folder. ``os.path.isjunction`` exists
    from Python 3.12 (always False off Windows); where it is missing there is nothing to ask."""
    isjunction = getattr(os.path, "isjunction", None)
    if isjunction is None:
        return
    here = root
    for part in re.split(r"[\\/]", rel):
        here = here / part
        if isjunction(here):
            raise ValueError(f"a junction is not followed: {rel!r} (at {part!r})")
    for dirpath, dirs, _files in os.walk(here):
        for name in dirs:
            if isjunction(os.path.join(dirpath, name)):
                raise ValueError(
                    f"a junction is not followed: {os.path.relpath(os.path.join(dirpath, name), root)!r}"
                )


def _junit_text(junit: Path) -> str:
    """The text of a JUnit file, or ``""`` when there is none. Only a regular file is read (``lstat``, so a symbolic link is not followed; a FIFO
    would block the read for ever): anything else, or a file of more than ``MAX_JUNIT_CHARS`` bytes (``st_size`` counts bytes; testing.mutation counts characters, and a file has at least as many bytes as characters, so this ceiling is the stricter), is a ``ValueError``."""
    try:
        info = junit.lstat()
    except FileNotFoundError:
        return ""
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("junit path is not a regular file")
    if info.st_size > MAX_JUNIT_CHARS:  # looked at BEFORE the file is read
        raise ValueError("junit file over the ceiling")
    return junit.read_text(encoding="utf-8")


def _refuse_skips_in_baseline(junit: Path, shown: _Shown) -> None:
    """``RuntimeError`` when the passing unmutated run skipped a test, or left no readable JUnit file to prove it did not (``forbid_skips``).
    ``shown`` is required: the ids in the message are always given as ``_shown_id`` gives them."""
    skipped: list[str] = []
    unusable = ""
    try:
        skipped = skipped_tests(_junit_text(junit))
    except _UNUSABLE_JUNIT as exc:
        # only the class name is kept, and the error is raised after this block: the caught error (its text can hold bytes of the
        # child's file) is in no ``__context__`` or ``__cause__`` of what the caller gets
        unusable = type(exc).__name__
    if unusable:
        raise RuntimeError(
            f"the unmutated copy left no usable JUnit file to check for skips: {unusable}"
        )
    if skipped:
        raise RuntimeError(
            f"the unmutated copy skipped {len(skipped)} selected test(s): {[_shown_id(t, shown) for t in skipped[:3]]}"
        )


def _baseline_failure(rc: int, junit: Path, shown: _Shown) -> str:
    """The message of a failed unmutated run: how it ended (exit code, timeout) and the first ``E`` line of its JUnit file when there is one, as
    ``_shown_line`` gives it (with a passed value: what stands for the exception class only). ``shown`` is required."""
    message = f"the unmutated copy does not pass its tests ({_run_end(rc)})"
    try:
        first = read_junit(_junit_text(junit)).first_line if junit.exists() else ""
    except _UNUSABLE_JUNIT:
        first = ""
    return f"{message}: {_shown_line(first, shown)}" if first else message


def _canary_refusal(m: Mutant, rc: int, junit: Path, forbid_skips: bool, shown: _Shown) -> str:
    """Why the canary run after the mutant ``m`` (the unmutated copy, run again on the shared database) stops the whole run, or ``""`` when it
    passed. It stops the run when it did not pass (``rc``), and under ``forbid_skips`` also when it skipped a test (a database that is gone makes
    tests skip, not fail). The message holds the mutant's name, the run end in words and, for a skip, test ids as ``_shown_id`` gives them."""
    name = _own_text(m.name, MUTANT_HIDDEN, shown.secrets)
    if rc != 0:
        return (
            f"the unmutated copy no longer passes its tests after mutant {name!r} ({_run_end(rc)}): the shared test database holds what the"
            " mutant left behind, so the verdicts of the later mutants would not be reliable"
        )
    if forbid_skips:
        try:
            _refuse_skips_in_baseline(junit, shown)
        except RuntimeError as exc:
            return f"after mutant {name!r}: {exc}"
    return ""


def _own_names(m: Mutant) -> tuple[str, ...]:
    """The test function names the caller wrote on the mutant ``m``: its ``only_test`` and the function of its ``pinned`` id (without parameters)."""
    pinned = m.pinned.partition("[")[0].rpartition("::")[2]
    return tuple(name for name in (m.only_test, pinned) if name)


def _row(
    m: Mutant,
    rc: int,
    junit: Path,
    forbid_skips: bool,
    shown: _Shown,
    first_lines: dict[str, str],
) -> tuple[str, Verdict, str, bool]:
    """The result row of one mutant run: its exit code ``rc`` and its JUnit file, judged once (one parse of the file)."""
    if rc == TIMED_OUT:
        return (m.name, Verdict.ERROR, "TIMEOUT", False)
    # the exit status is lost: an error row, never a pass or a kill
    if rc == REAPED_ELSEWHERE:
        return (m.name, Verdict.ERROR, "REAPED ELSEWHERE", False)
    try:
        xml_text = _junit_text(junit)
        report = read_junit(xml_text) if xml_text else JunitReport("", "", [], [], False, False)
    except _UNUSABLE_JUNIT:  # refused or unreadable (a permission error, say): this mutant's ERROR, not the end of the run
        return (m.name, Verdict.ERROR, "JUNIT REFUSED", False)
    if (
        forbid_skips and not xml_text
    ):  # no record of what ran cannot prove nothing was skipped: never judged
        return (m.name, Verdict.ERROR, "JUNIT MISSING", False)
    if report.collection_failed:  # a test file that could not be imported or collected: no test ran, an assert at import time is no kill
        first_lines[m.name] = _shown_line(report.first_line, shown)
        return (m.name, Verdict.ERROR, "COLLECTION ERROR", False)
    if report.fixture_failed:  # a fixture that failed in setup or teardown means the test never ran as written: never a kill
        first_lines[m.name] = _shown_line(report.first_line, shown)
        return (m.name, Verdict.ERROR, "FIXTURE ERROR", False)
    if (
        forbid_skips and report.skipped
    ):  # a skipped test proves nothing: never a kill, whatever else failed in the same run
        why = (
            _shown_line(report.first_line, shown)
            or f"skipped: {', '.join(_shown_id(t, shown, _own_names(m)) for t in report.skipped[:3])}"
        )
        first_lines[m.name] = why
        return (m.name, Verdict.ERROR, "SKIPPED TESTS", False)
    v = judge_report(
        rc, report, expect=m.expect, pinned=m.pinned or None, crash_markers=m.crash_markers
    )
    if (
        report.first_line
    ):  # an entry only for a row that has a first ``E`` line (a kill or not), as the docstring says
        first_lines[m.name] = _shown_line(report.first_line, shown, m.expect)
    declared = _leading_class(report.first_line) == m.crash_type
    crash_ok = v is Verdict.CRASH and m.allow_crash and declared
    # an ERROR row with no failing test id says why: exit 1 with no test named, or another exit code (usage error, internal error, a kill by the system)
    no_id = (NO_TEST_NAMED if rc == 1 else f"EXIT CODE {rc}") if v is Verdict.ERROR else ""
    shown_id = _shown_id(report.test_id, shown, _own_names(m)) if report.test_id else ""
    return (
        m.name,
        v,
        shown_id or no_id,
        v is Verdict.KILLED or crash_ok,
    )


def _run_mutants(
    root: Path,
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    extra_dirs: Sequence[str],
    only: Sequence[str],
    timeout: float,
    baseline_timeout: float | None,
    on_result: Callable[[tuple[str, Verdict, str, bool]], None] | None,
    first_lines: dict[str, str],
    conftest: str = "",
    pass_env: Sequence[str] = (),
    forbid_skips: bool | None = None,
    throwaway_hosts: Sequence[str] = THROWAWAY_HOSTS,
    shown_classes: Sequence[str] = (),
) -> list[tuple[str, Verdict, str, bool]]:
    first_lines.clear()  # the diagnostics of an earlier run must not answer for this one
    root = Path(root)
    mutants = list(mutants)
    # a bare string is a ``TypeError`` for every keyword that takes a sequence of texts (the three below, and ``pass_env``,
    # ``throwaway_hosts`` and ``shown_classes`` in their own checks): it would be read letter by letter
    _refuse_bare_string(tests, "tests")
    _refuse_bare_string(extra_dirs, "extra_dirs")
    _refuse_bare_string(only, "only")
    for t in (*tests, *extra_dirs):
        _relative(t)
    # the refusals below come in the order the module docstring gives them; each is raised before any folder is made or any test runs
    env_names = _checked_env_names(pass_env)  # an unlisted name is refused, never passed
    # checked for every call, also when no variable is passed
    hosts = _checked_throwaway_hosts(throwaway_hosts)
    classes = _checked_shown_classes(shown_classes)
    if conftest:
        _plugin_module(conftest)
        if (
            not _inside(root, conftest).is_file()
        ):  # before any temp folder: a missing plugin file is a refusal, not a late copy error
            raise ValueError(f"conftest is not a file of the tree: {conftest!r}")
    environ = _env_snapshot(env_names)  # the ONE read of the environment of this call
    secrets = _secret_values(env_names, environ)
    for env_name in env_names:  # a variable that is present, also with an empty text, must hold an address the check accepts
        if env_name in environ:
            _refuse_unsafe_address(
                env_name,
                environ[env_name],
                hosts,
                (*classes, *(m.crash_type for m in mutants if m.crash_type)),
            )
    if (
        forbid_skips is None
    ):  # on when a name is LISTED in pass_env, whether or not the variable is present
        forbid_skips = bool(env_names)
    # a listed variable that is present (it then holds a checked address) means a shared database: the lock and the canary run
    canary = any(name in environ for name in env_names)
    copied = (*tests, conftest) if conftest and conftest not in tests else tuple(tests)
    for m in mutants:  # before anything runs: a bad `test_file` must not surface after earlier mutants were already run
        if m.test_file and m.test_file not in tests:
            raise ValueError(
                f"mutant {m.name!r}: test_file {m.test_file!r} is not one of the copied tests"
            )
    # both folders are named from ONE mkdtemp, made inside the try below (held against a signal), so no signal can leave ``tmp`` alone behind
    made: list[Path] = []
    tmp: Path
    snap: Path

    def build() -> None:
        # the top folder is KEPT and emptied, never removed and made again (a new folder would have the default mode, not 0700); it is
        # checked before anything is removed in it and again after every rebuild
        _refuse_unless_private(tmp, "temp folder")
        _empty_dir(tmp)
        # not ``_make_dirs``: a ``tests`` folder that is still there (a failed removal) must fail this attempt
        _make_private_dir(tmp / "tests", "tests folder")
        shutil.copytree(snap / "src", tmp / "src", symlinks=True)
        for t in copied:
            dst = _inside(tmp, t)
            _make_dirs(tmp, dst.parent)
            shutil.copy(_inside(snap, t), dst)
        for d in extra_dirs:
            if _inside(snap, d).exists():
                shutil.copytree(
                    _inside(snap, d), _inside(tmp, d), symlinks=True, dirs_exist_ok=True
                )
        _refuse_unless_private(tmp, "temp folder")

    def fresh() -> None:
        """Rebuild the temp copy: retried ``SETUP_TRIES`` times, then the last ``OSError`` is raised (never swallowed)."""
        for attempt in range(SETUP_TRIES):
            try:
                return build()
            except OSError:
                if attempt == SETUP_TRIES - 1:
                    raise
                time.sleep(SETUP_WAIT)

    out: list[tuple[str, Verdict, str, bool]] = []

    def emit(row: tuple[str, Verdict, str, bool]) -> None:
        out.append(row)
        if on_result is not None:
            on_result(row)

    held = contextlib.ExitStack()
    # the try starts before the lock is entered: a ``SystemExit`` right after the lock is taken (a signal, a caller) still reaches
    # ``held.close()`` in the ``finally``, so the lock is never left held until the garbage collector runs. A refusal (a path through
    # a link out of the tree, a missing ``src``) or a signal at any later point leaves no temp folder behind either
    try:
        if canary:  # before any temp folder: a second runner on the same database is refused
            _refuse_lock_folder_in_tree(root)
            held.enter_context(
                _one_run_per_database([environ[n] for n in env_names if n in environ])
            )
        # the junction checks look at the CALLER's tree, so they come before any folder is made; the check of relative links out of the tree
        # (``_refuse_links_out``) needs the copy and comes after it (the folders are removed again)
        _refuse_junctions(root, "src")
        for d in extra_dirs:
            if _inside(root, d).exists():
                _refuse_junctions(root, d)
        with _signals_held():
            made.append(_make_private_temp_dir("mutants_", "temp folder"))
        tmp = made[0]
        snap = tmp.with_name(tmp.name + "_snap")
        _make_private_dir(snap, "snapshot folder")
        # ONE snapshot of the tree at the start: every mutant copy is made from it, so an edit of ``root`` while the run is going (a
        # developer saving a file, a second tool) can never leak into a later mutant
        shutil.copytree(
            root / "src", snap / "src", symlinks=True, ignore=shutil.ignore_patterns("__pycache__")
        )  # links stay links (never followed out of the tree)
        for t in copied:
            dst = _inside(snap, t)
            _make_dirs(snap, dst.parent)
            shutil.copy(_inside(root, t), dst)
        for d in extra_dirs:
            if _inside(root, d).exists():
                shutil.copytree(
                    _inside(root, d), _inside(snap, d), symlinks=True, dirs_exist_ok=True
                )
        _refuse_unless_private(snap, "snapshot folder")
        _refuse_links_out(snap)
        shown = _shown_for(secrets, mutants, tests, classes, snap)
        fresh()
        base_timeout = timeout if baseline_timeout is None else baseline_timeout
        base_rc = _pytest(
            tmp,
            tests,
            tmp / "base.xml",
            base_timeout,
            plugin=conftest,
            env_names=env_names,
            environ=environ,
            hosts=hosts,
        )
        if base_rc == REAPED_ELSEWHERE:
            raise RuntimeError(
                "the baseline run was reaped by someone else: its exit status is unknown"
            )
        if base_rc != 0:
            raise RuntimeError(_baseline_failure(base_rc, tmp / "base.xml", shown))
        if forbid_skips:
            _refuse_skips_in_baseline(tmp / "base.xml", shown)
        for m in mutants:
            if only and not any(o in m.name for o in only):
                continue
            try:
                fresh()
            except OSError as exc:  # a setup failure is a RESULT ROW for this mutant, never a crash of the run and never silent
                emit((m.name, Verdict.ERROR, f"SETUP FAILED: {type(exc).__name__}", False))
                continue
            p = _locate(tmp, m.file)
            text = p.read_text(encoding="utf-8")
            if m.old not in text:
                emit((m.name, Verdict.ERROR, "SNIPPET NOT FOUND", False))
                continue
            p.write_text(text.replace(m.old, m.new), encoding="utf-8", newline="\n")
            junit = tmp / "r.xml"
            if m.test_file:
                operands = [f"{m.test_file}::{m.only_test}" if m.only_test else m.test_file]
            else:
                operands = (
                    [f"{tests[0]}::{m.only_test}", *tests[1:]] if m.only_test else list(tests)
                )
            rc = _pytest(
                tmp,
                operands,
                junit,
                timeout,
                plugin=conftest,
                env_names=env_names,
                environ=environ,
                hosts=hosts,
            )
            emit(_row(m, rc, junit, forbid_skips, shown, first_lines))
            if canary:  # the passed database is shared by the baseline and every mutant run: prove the unmutated copy still passes on what this one left
                rebuild_failed = ""
                try:
                    fresh()
                except OSError as exc:
                    rebuild_failed = type(exc).__name__
                if rebuild_failed:  # raised outside the ``except`` block: the error keeps no other exception in its chain
                    raise RuntimeError(
                        "the unmutated copy could not be rebuilt for the canary run after mutant"
                        f" {_own_text(m.name, MUTANT_HIDDEN, shown.secrets)!r}: {rebuild_failed}"
                    )
                again = _pytest(
                    tmp,
                    tests,
                    tmp / "again.xml",
                    base_timeout,
                    plugin=conftest,
                    env_names=env_names,
                    environ=environ,
                    hosts=hosts,
                )
                reason = _canary_refusal(m, again, tmp / "again.xml", forbid_skips, shown)
                if reason:
                    failure = CanaryFailed(reason)
                    failure.rows = tuple(out)
                    raise failure
    finally:
        held.close()
        with _signals_held():  # a signal is raised after the removal
            for folder in made:
                shutil.rmtree(folder, ignore_errors=True)
                shutil.rmtree(folder.with_name(folder.name + "_snap"), ignore_errors=True)
    return out
