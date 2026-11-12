"""The migration rule, as pure functions (no database library): file-name numbers, late files, the written recipe for
a late file, the ledger-without-file message, the one-pass SQL lexer with the refusal list, and the check that a released
file never changes.

`store/migrate.py` calls these before it connects (a later change, P3a-2: until it merges, NOTHING calls them and none of
the rules here is in force). Nothing here opens a connection; the only file access is `list_migration_files`,
`check_migration_numbers`, `released_problems` (directory listings and one read per released file) and `read_files`.

Why a lexer of our own (R448 rung decision, 2026-11-06). The text rules do exactly two jobs the database cannot do for us:
(a) hand `migrate._scan` a view of the file without comments, so it can refuse a `CREATE TABLE` that has no exact grants;
(b) refuse transaction control (`COMMIT`, `END`, `ROLLBACK`, `SAVEPOINT` ...) before the run, because a hidden `COMMIT`
ends the one migration transaction. The other refusals (`SET`, `RESET`, `ALTER ROLE`, `DO`, `EXECUTE` ...) are a tripwire
against accidents and a help to the reviewer: the guard that cannot be blinded by spelling is the read-back in `migrate()`
after each file (a later change), which compares the role, `search_path`, `standard_conforming_strings`,
`backslash_quote`, `client_encoding` and the trigger state. A higher rung was looked at: the SQL tokenizer of sqlglot
(MIT, already pinned in the `askdata` extra). It was NOT adopted, for design reasons, not for a measured score: in the one check made (2026-11-06,
not kept here) it did not refuse a psql meta-command (`SELECT 1 \\g` comes out as tokens), and it is a dependency
upgrade on a safety path whose behaviour could change without a test here failing. No number about sqlglot is claimed in this file,
because the comparison that was run is not kept in this repository. pglast (the server's own scanner, GPL-3.0) is
test-only: `tests/test_migration_numbers_guards.py` compares it with this lexer (skipped when pglast is absent). If the
lexer reads a file LONGER than the server does, a `COMMIT` can hide inside a string (the dangerous direction); if it ends
a string EARLIER, the file is refused although it is fine (the safe direction).

Which function to call. `statement_text(text, keep_quoted=False)` returns the pair `(text, problem)` (the ticket's
signature); `problem` is "" when the file was read to its end, and when it is not the returned text stops at the problem
and must not be used. A caller that wants no pair and no half text uses `checked_statement_text`, which returns the text
alone or raises `SqlReadError`. `lex` is the same as `statement_text`.

The lexer follows the PostgreSQL scanner rules that matter for where a string, comment or body starts and ends, with
`standard_conforming_strings = on`. Preconditions: the migration role is NOT a superuser (statements such as
`CREATE EXTENSION`, `COPY ... PROGRAM` and `LOAD` are refused here as a tripwire, not as the guard), the server is
PostgreSQL 15 or later, and the files are UTF-8 text without hidden characters. The scanner rules were compared with
pglast 8.7 (the PostgreSQL 17 scanner) and probed on 16.15 (ticket P3a); that PostgreSQL 15 scans the same way is an
ASSUMPTION nobody has tested here. `refused_statements` refuses `CREATE EXTENSION` outright: no extension is allowed
today, because no planned migration creates one (grep of the tickets, in the pull request text). If one is wanted, add
its name to a named allow-list constant here and test it; never a bypass.
"""

from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path

from hadavin_sdk.errors import ConfigError

# --- constants ---------------------------------------------------------------------------------------------------------

# Four ASCII digits (never `\d`: it matches Arabic-Indic and full-width digits), at most 9999 migrations.
NAME = re.compile(r"[0-9]{4}_[a-z0-9_]+\.sql")
STEM = re.compile(r"[0-9]{4}_[a-z0-9_]+")
# The schema names that a printed recipe may carry: no double quote can occur, so the quoted name is the plain name.
PLAIN_SCHEMA = re.compile(r"[a-z_][a-z0-9_]{0,62}")
# One hostile name once produced thousands of problem lines: 21 problems show 20 plus "and 1 more".
MAX_PROBLEMS_SHOWN = 20
# The one place this command is written (the late-file message uses it; `migrate` and the CHANGELOG runbook will, in P3a-2).
RECIPE_COMMAND = "psql -X -v ON_ERROR_STOP=1 -f recipe.sql"
# The one generated psql command: with it a run WITHOUT -X still stops at the first error even when a person's startup
# file says `\set ON_ERROR_STOP off`.
RECIPE_FIRST_LINE = "\\set ON_ERROR_STOP on"
# The advisory-lock key of every migrate run, `migrate._LOCK` (a later change makes that name point here).
MIGRATE_LOCK = int.from_bytes(b"hadvnmig", "big") >> 1
MIGRATIONS = Path(__file__).parent / "migrations"

# The recipe's ledger line (text for a person to run, never executed here). Filled with `replace` after the stem passed
# STEM, so no quote can occur; not an f-string, which the SQL-injection scanner would flag.
_LEDGER_INSERT = "INSERT INTO schema_migrations (version) VALUES ('{stem}');"
_WS = " \t\n\r\f\v"  # statement-start whitespace: the server's set plus vertical tab (the safe direction)
_ALLOWED_CONTROL = "\t\n\r\f"
# Characters a person cannot see in a review but that change what the file is: controls (Cc), format characters such as
# the right-to-left override, the isolates, zero-width space and the byte order mark (Cf), line and paragraph separators.
_HIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp"})
_ASCII_CONTROL = re.compile(r"[\x00-\x08\x0b\x0e-\x1f\x7f]")


class MigrationNumberError(ConfigError):
    """The migration files or the ledger are inconsistent. `problems` holds all of them; the message shows at most
    `MAX_PROBLEMS_SHOWN` and a count of the rest."""

    def __init__(self, problems: Sequence[str]):
        self.problems: tuple[str, ...] = tuple(problems)
        shown = list(self.problems[:MAX_PROBLEMS_SHOWN])
        if len(self.problems) > MAX_PROBLEMS_SHOWN:
            shown.append(f"and {len(self.problems) - MAX_PROBLEMS_SHOWN} more")
        super().__init__("migrations are inconsistent: " + "; ".join(shown))

    def __reduce__(self):
        # `copy` and `pickle` rebuild an exception as `cls(*self.args)`; `args` holds the message, which would become
        # one "problem" per character. Rebuild from the problems instead.
        return (type(self), (self.problems,))


def _esc(name: str) -> str:
    """A name for a message: control characters, ANSI escapes and lone surrogates are written as escapes. The slice
    removes the outer quotes that `ascii()` adds, so the old messages keep their exact text."""
    return ascii(name)[1:-1]


# --- file names and the ledger -----------------------------------------------------------------------------------------


def list_migration_files(folder: Path) -> list[Path]:
    """Entries whose name ends in `.sql` in any letter case, sorted. Other entries are ignored at run time."""
    with os.scandir(folder) as it:
        return sorted(folder / e.name for e in it if e.name.lower().endswith(".sql"))


def check_ledger(paths: Sequence[Path]) -> list[str]:
    """Problems with the file names: each is `NNNN_<name>.sql`, a regular file (or a link to one), numbers start at
    0001 and run 1, 2, 3 ... with no repeat or gap. Opens no file; never raises for a bad name."""
    problems: list[str] = []
    numbers: list[int] = []
    for p in paths:
        name = _esc(p.name)
        if not NAME.fullmatch(p.name):
            problems.append(f"{name}: not named NNNN_<name>.sql")
        elif int(p.name[:4]) == 0:
            problems.append(f"{name}: number 0000 is not allowed, numbers start at 0001")
        else:
            numbers.append(int(p.name[:4]))
        if not p.is_file():
            problems.append(
                f"{name}: not a regular file (a directory, or a link that points nowhere)"
            )
    problems += [
        f"two migrations are numbered {n:04d}"
        for n, count in sorted(Counter(numbers).items())
        if count > 1
    ]
    have = set(numbers)
    problems += [
        f"migration {n:04d} is missing"
        for n in range(1, max(numbers, default=0) + 1)
        if n not in have
    ]
    return problems


def folder_problems(folder: Path) -> list[str]:
    return check_ledger(list_migration_files(folder))


def check_migration_numbers(folder: Path = MIGRATIONS) -> None:
    """The CI and test check. Also refuses what the run time tolerates: a symbolic link and a stray entry that does
    not end in `.sql` (`__pycache__`, `.bak`). Raises `MigrationNumberError`."""
    problems = folder_problems(folder)
    with os.scandir(folder) as it:
        for e in sorted(it, key=lambda e: e.name):
            if e.is_symlink():
                problems.append(f"{_esc(e.name)}: is a symbolic link; CI wants the file itself")
            elif not e.name.lower().endswith(".sql"):
                problems.append(f"{_esc(e.name)}: not a migration file (stray entry in the folder)")
    if problems:
        raise MigrationNumberError(problems)


def read_files(files: Sequence[Path]) -> dict[Path, str]:
    """Each file ONCE, as UTF-8 text. The same text is scanned and later executed, so a file changed on disk between
    the scan and the run is not run in its new form. An unreadable file raises the original error. `read_text` in text
    mode translates CRLF and a lone CR to LF, so the text the lexer sees (and the server later gets) has only LF; the
    hash in `released_problems` reads bytes and does the same translation for CRLF by hand. A byte order mark is NOT
    removed here: `hidden_character` names it and the file is refused."""
    return {p: p.read_text(encoding="utf-8") for p in files}


def hidden_character(text: str) -> str:
    """ "" when the text has no hidden character, otherwise a plain-words reason naming the first one and its line. Tab,
    line feed, carriage return and form feed are allowed. A byte order mark at the very start is named as such."""
    if text.startswith("\ufeff"):
        return "the file starts with a byte order mark (U+FEFF); save it as UTF-8 without it"
    if text.isascii():
        m = _ASCII_CONTROL.search(text)
        pos = m.start() if m else -1
    else:
        pos = next(
            (
                i
                for i, ch in enumerate(text)
                if ch not in _ALLOWED_CONTROL and unicodedata.category(ch) in _HIDDEN_CATEGORIES
            ),
            -1,
        )
    if pos < 0:
        return ""
    kind = "control character" if unicodedata.category(text[pos]) == "Cc" else "hidden character"
    return (
        f"a {kind} U+{ord(text[pos]):04X} at line {_line_of(text, pos)} "
        "(it is not shown to a reviewer and could change what runs)"
    )


def _number(stem: str) -> int | None:
    return int(stem[:4]) if STEM.fullmatch(stem) else None


def late_files(applied: Collection[str], files: Sequence[Path]) -> list[Path]:
    """Files not applied whose number is at or below the HIGHEST applied number, sorted by number. `applied` holds
    stems; an applied name that is not a stem is ignored here (`gone_message` reports it)."""
    highest = max((n for s in applied if (n := _number(s)) is not None), default=None)
    if highest is None:
        return []
    late = [
        p
        for p in files
        if NAME.fullmatch(p.name) and p.name[:-4] not in applied and int(p.name[:4]) <= highest
    ]
    return sorted(late, key=lambda p: (int(p.name[:4]), p.name))


# --- the recipe for a late file ----------------------------------------------------------------------------------------

_PSQL_VARIABLE = re.compile(r"(?<!:):(?!:)(?=[A-Za-z_'\"{]|[^\x00-\x7f])")
_RECIPE_MARKER = re.compile(r"recipe\s+(?:begins|ends)", re.IGNORECASE)


def _refuse_entry(stem: str, text: str) -> str | None:
    """Why `psql -f` must not be given this entry, or None."""
    if not STEM.fullmatch(stem):
        return "the name does not match NNNN_<name> and is printed inside quotes"
    if _RECIPE_MARKER.search(text):
        return "the text holds the words RECIPE begins or RECIPE ends, which could shorten what is copied"
    if hidden := hidden_character(text):
        return f"the text holds {hidden}"
    if "\\" in text:
        return "psql would read part of it as a command (a backslash)"
    cleaned, problem = lex(text)
    if problem:
        return f"the text cannot be read: {problem}"
    if reasons := refused_statements(text):
        return reasons[0]
    if _PSQL_VARIABLE.search(cleaned):
        return "psql would read part of it as a variable (a colon name)"
    return None


def hand_recipe(entries: Sequence[tuple[str, str]], schema: str, lock: int = MIGRATE_LOCK) -> str:
    """The SQL a database administrator runs by hand for late files: `entries` are `(stem, sql_text)` in number
    order. Raises `ValueError` (naming the stem) for a schema or an entry that `psql -f` could misread."""
    if not PLAIN_SCHEMA.fullmatch(schema):
        raise ValueError("the schema name has unusual characters")
    for stem, text in entries:
        if (why := _refuse_entry(stem, text)) is not None:
            raise ValueError(f"{_esc(stem)}: {why}")
    lines = [
        "-- RECIPE begins",
        RECIPE_FIRST_LINE,
        f'SET search_path TO "{schema}";',
        "BEGIN;",
        f"SELECT pg_advisory_xact_lock({lock:d});",
    ]
    for stem, text in entries:
        lines.append(text)
        cleaned = checked_statement_text(text)  # cannot raise: _refuse_entry read this text above
        if cleaned.rsplit(";", 1)[-1].strip(_WS):
            lines.append(";")  # an unterminated last statement would swallow the INSERT
        # printed text for a person, never executed here; the stem matched STEM above, so no quote can occur
        lines.append(_LEDGER_INSERT.replace("{stem}", stem))
        lines.append("")
    lines += ["COMMIT;", "-- RECIPE ends"]
    return "\n".join(lines)


def order_problems(
    applied: Collection[str], files: Sequence[Path], texts: Mapping[Path, str], schema: str
) -> list[str]:
    """ONE problem for all late files (one recipe, one transaction, one lock). `schema` is `current_schema()` read in
    the transaction. A refused schema or file gives a message with no recipe, never an exception."""
    late = late_files(applied, files)
    if not late:
        return []
    highest = max((s for s in applied if _number(s) is not None), key=lambda s: (int(s[:4]), s))
    names = _names([p.name for p in late])
    verb = "would be" if len(late) == 1 else "would all be"
    head = (
        f"{names} {verb} applied out of order: the number is at or below '{_esc(highest)}', which this database "
        "has already applied. Do not rename the file. What to do: a database administrator applies it by hand, as "
        "the database user that runs migrations, while no migrate command is running. "
    )
    try:
        if missing := [p.name for p in late if p not in texts]:
            raise ValueError(f"the text of {_names(missing)} was not read")
        recipe = hand_recipe([(p.name[:-4], texts[p]) for p in late], schema)
    except ValueError as e:
        return [
            head
            + f"No recipe is printed: {e}. A person must write the steps by hand, with a reviewer."
        ]
    return [
        head + "Steps:\n"
        "1. Save the lines between the two RECIPE lines below to a file, for example recipe.sql.\n"
        f"2. Run exactly: {RECIPE_COMMAND} and add your own connection settings (a PGSERVICE entry or the usual "
        "PG environment variables; this message never prints a connection string). The -X option keeps psql from "
        "reading your own startup file, which could switch off the stop at the first error.\n"
        "3. Do not type the lines into psql one by one. If psql prints an error it stops and keeps nothing.\n"
        "4. Before you start, review each file against every migration applied after it.\n"
        "5. Afterwards run migrate again with the usual role options (that applies the grants again).\n"
        "6. Write the date, the files and your name in the change log.\n" + recipe
    ]


def _names(names: Sequence[str]) -> str:
    """At most `MAX_PROBLEMS_SHOWN` names, then "and N more": one hostile ledger once meant thousands of names."""
    shown = [_esc(n) for n in names[:MAX_PROBLEMS_SHOWN]]
    if len(names) > MAX_PROBLEMS_SHOWN:
        shown.append(f"and {len(names) - MAX_PROBLEMS_SHOWN} more")
    return ", ".join(shown)


# --- a released file never changes -------------------------------------------------------------------------------------


def released_problems(folder: Path, manifest: Mapping[str, str]) -> list[str]:
    """Forward-only: `manifest` maps the stem of every RELEASED file to the SHA-256 of its bytes (Windows line endings
    read as Unix ones). A released file that is missing or changed is a problem, and so is a file that is not in the
    manifest but is numbered at or below the highest released one. Add a row to the manifest when a release is cut."""
    files = {p.name[:-4]: p for p in list_migration_files(folder) if NAME.fullmatch(p.name)}
    problems: list[str] = []
    for stem in sorted(manifest):
        p = files.get(stem)
        if p is None or not p.is_file():
            problems.append(f"{_esc(stem)}: a released file is missing")
        elif hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() != manifest[stem]:
            problems.append(f"{_esc(stem)}: a released file was changed")
    released = [s for s in manifest if STEM.fullmatch(s)]
    if released:
        top = max(released, key=lambda s: (int(s[:4]), s))
        problems += [
            f"{_esc(stem)}: a new migration is numbered at or below the highest released one ({_esc(top)})"
            for stem in sorted(files)
            if stem not in manifest and int(stem[:4]) <= int(top[:4])
        ]
    return problems


# --- a ledger name that has no file ------------------------------------------------------------------------------------


def gone_message(applied: Collection[str], files: Sequence[Path]) -> str:
    """ "" when every applied name has a file. Otherwise a prefix line (kept word for word: existing tests match it)
    and ONE line per case present; each orphan gets exactly one case, decided by NAME (1 rename, 2 newer, 3 a person
    must look). The rename line does not print the file's name. At most `MAX_PROBLEMS_SHOWN` names per line."""
    stems = {p.name[:-4] for p in files if p.name.lower().endswith(".sql")}
    orphans = sorted(a for a in applied if a not in stems)
    if not orphans:
        return ""
    folder_numbers = [int(p.name[:4]) for p in files if NAME.fullmatch(p.name)]
    highest = max(folder_numbers, default=0)
    after = {}  # text after "NNNN_" -> file stems of the folder that have it
    for s in stems:
        if STEM.fullmatch(s):
            after.setdefault(s[5:], []).append(s)
    orphan_texts = Counter(o[5:] for o in orphans if STEM.fullmatch(o))
    cases: dict[int, list[str]] = {1: [], 2: [], 3: []}
    for o in orphans:
        if STEM.fullmatch(o):
            same = after.get(o[5:], [])
            if len(same) == 1 and same[0] not in applied and orphan_texts[o[5:]] == 1:
                cases[1].append(o)
                continue
            if int(o[:4]) > highest:
                cases[2].append(o)
                continue
        cases[3].append(o)
    lines = [f"applied migrations have no file in this release: {_names(orphans)}."]
    if cases[1]:
        lines.append(
            f"{_names(cases[1])}: the folder has a file with the same name after the number, so the file was probably "
            "renamed. If it is the same migration and its tables already exist, a database administrator changes "
            "the version of each of these records (table schema_migrations) by hand to the name of that file "
            "(without .sql), while no migrate command is running."
        )
    if cases[2]:
        lines.append(
            f"{_names(cases[2])}: this database is newer than this release. Do not rename, drop or edit the records "
            "(table schema_migrations). Run the release that has these files. If the code was not reverted, and "
            "the record was renamed or the database was built from a branch, a database administrator must look "
            "at the records before anyone changes them."
        )
    if cases[3]:
        lines.append(
            f"{_names(cases[3])}: no file in this release has this name, and the number is not above the highest file "
            "number, so this is neither a newer database nor a plain rename. A person must look: do not rename "
            "or drop by guess."
        )
    return "\n".join(lines)


# --- the lexer ---------------------------------------------------------------------------------------------------------


def _ident_char(ch: str) -> bool:
    return ch.isascii() and (ch.isalnum() or ch in "_$") or not ch.isascii()


def _ident_start(ch: str) -> bool:
    return ch.isascii() and (ch.isalpha() or ch == "_") or not ch.isascii()


def _line_of(text: str, pos: int) -> int:
    """1-based line of `pos`: a line ends at LF, CR or CRLF, counted once."""
    head = text[:pos]
    return 1 + len(re.findall(r"\r\n|\r|\n", head))


_SPECIAL = re.compile(r"[-/'\"$]")
_PLAIN_STR_END = re.compile(r"'")
_E_STR_STEP = re.compile(r"[\\']")
_DQ_END = re.compile(r'"')


def _skip_blank(text: str, i: int) -> int:
    """Skip whitespace and comments from `i`; stops at anything else, and at an unclosed comment (the main pass
    reports that one)."""
    n = len(text)
    while i < n:
        c = text[i]
        if c in _WS:
            i += 1
        elif text.startswith("--", i):
            j = i + 2
            while j < n and text[j] not in "\n\r":
                j += 1
            i = j
        elif text.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if text.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif text.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            if depth:
                return i
            i = j
        else:
            break
    return i


class SqlReadError(ValueError):
    """`checked_statement_text` could not read the file to its end (an unclosed quote, comment or `$` body, an unrecognised
    `$`). The message names the problem and its line."""


def checked_statement_text(text: str, keep_quoted: bool = False) -> str:
    """The text `lex` returns, or `SqlReadError`: a caller that wants the view of the file gets a complete view or no
    view at all, never a text that stops at the first problem (fail closed). It returns a `str`, not a pair; the
    ticket's name `statement_text` returns the pair."""
    cleaned, problem = lex(text, keep_quoted)
    if problem:
        raise SqlReadError(problem)
    return cleaned


def statement_text(text: str, keep_quoted: bool = False) -> tuple[str, str]:
    """The ticket's function: `(text, problem)`, see `lex`. Write `cleaned, problem = statement_text(...)`. It never
    raises and never returns a bare `str`, so `statement_text(...)[0]` is the whole text and not its first character."""
    return lex(text, keep_quoted)


def lex(text: str, keep_quoted: bool = False) -> tuple[str, str]:
    """ONE left-to-right pass: comments become one space and every quoted part is emptied (`''`, `""`, `$$`), plus a
    problem string (`""` when fine; when it is not empty the returned text STOPS at the problem and must not be used as
    a view of the file). With `keep_quoted=True` quoted parts are kept as written and only comments are
    replaced; the problem string is the same in both views.

    Handled in the same pass so that no rule runs before another: `--` to the next LF or CR; nested block comments;
    `'...'` with `''`; `E'...'` where a backslash escapes the next character (an `E` not preceded by an identifier
    character) and a second literal that continues it after a newline is refused (the server keeps E mode there);
    `"..."` with `""`; `$tag$...$tag$` (tag: ASCII letter, underscore or any non-ASCII character, then those or
    digits; compared with case; the `$` is part of a NAME, not a tag, only when the run of name characters before it
    starts with a letter, underscore or non-ASCII character: after a number or after a closing `$` it opens a tag, as
    the server scans it); `$1` is left alone and any other `$` is refused. Precondition: `standard_conforming_strings = on`."""
    out: list[str] = []
    problem = ""
    n = len(text)
    i = 0

    def fail(kind: str, at: int) -> None:
        nonlocal problem
        if not problem:
            problem = f"{kind} at line {_line_of(text, at)}"

    carried = -1  # start of the name that ends exactly at `i` when the last action was a `$` inside a name, else -1

    while i < n:
        m = _SPECIAL.search(text, i)
        if m is None:
            out.append(text[i:])
            break
        j = m.start()
        if j > i:
            out.append(text[i:j])
        c = text[j]
        # start of the run of name characters that ends at j (j itself when there is none); it cannot reach below
        # `i` except through a name that the last action carried over, so the scan is linear over the whole text
        run = j
        while run > i and _ident_char(text[run - 1]):
            run -= 1
        if run == i and carried >= 0:
            run = carried
        carried = -1
        if c == "-":
            if text.startswith("--", j):
                k = j + 2
                while k < n and text[k] not in "\n\r":
                    k += 1
                out.append(" ")
                i = k
            else:
                out.append("-")
                i = j + 1
        elif c == "/":
            if text.startswith("/*", j):
                depth, k = 1, j + 2
                while k < n and depth:
                    if text.startswith("/*", k):
                        depth, k = depth + 1, k + 2
                    elif text.startswith("*/", k):
                        depth, k = depth - 1, k + 2
                    else:
                        k += 1
                if depth:
                    fail("comment not closed", j)
                    break
                out.append(" ")
                i = k
            else:
                out.append("/")
                i = j + 1
        elif c == "'":
            e_mode = j - run == 1 and text[run] in "Ee"
            k = j + 1
            closed = False
            while True:
                s = (_E_STR_STEP if e_mode else _PLAIN_STR_END).search(text, k)
                if s is None:
                    break
                if text[s.start()] == "\\":
                    k = s.start() + 2
                    continue
                if text.startswith("''", s.start()):
                    k = s.start() + 2
                    continue
                k = s.start() + 1
                closed = True
                break
            if not closed:
                fail("string not closed", j)
                out.append("'")
                break
            out.append(text[j:k] if keep_quoted else "''")
            i = k
            if e_mode:
                nxt = _skip_blank(text, i)
                if nxt < n and text[nxt] == "'":
                    fail("E'' string continued", nxt)
        elif c == '"':
            k = j + 1
            closed = False
            while True:
                s = _DQ_END.search(text, k)
                if s is None:
                    break
                if text.startswith('""', s.start()):
                    k = s.start() + 2
                    continue
                k = s.start() + 1
                closed = True
                break
            if not closed:
                fail("quoted identifier not closed", j)
                out.append('"')
                break
            out.append(text[j:k] if keep_quoted else '""')
            i = k
        else:  # "$"
            if run < j and _ident_start(text[run]):  # part of a name such as a$b$
                out.append("$")
                i = j + 1
                carried = run
                continue
            k = j + 1
            if k < n and text[k].isascii() and text[k].isdigit():
                out.append("$")  # a parameter such as $1: left alone
                i = j + 1
                continue
            if k < n and _ident_start(text[k]):
                k += 1
                while k < n and _ident_char(text[k]) and text[k] != "$":
                    k += 1
                if not (k < n and text[k] == "$"):
                    fail("unrecognised $", j)
                    break
            elif not (k < n and text[k] == "$"):
                fail("unrecognised $", j)
                break
            tag = text[j : k + 1]
            end: int = text.find(tag, k + 1)
            if end == -1:
                fail("dollar body not closed", j)
                out.append(tag if keep_quoted else "$$")
                break
            out.append(text[j : end + len(tag)] if keep_quoted else "$$")
            i = end + len(tag)
    return "".join(out), problem


# --- the refusal list --------------------------------------------------------------------------------------------------

_W = f"[{_WS}]+"
_TRANSACTION = re.compile(
    rf"(commit|end|begin|abort|rollback|savepoint|release|start{_W}transaction|prepare{_W}transaction)\b",
    re.IGNORECASE,
)
_SET_ALLOWED = re.compile(rf"set{_W}local{_W}(?:lock_timeout|statement_timeout)\b", re.IGNORECASE)
_SET = re.compile(r"(set|reset)\b", re.IGNORECASE)
_BLIND = re.compile(
    rf"(do|execute|load|discard|alter{_W}role|alter{_W}user|alter{_W}group|alter{_W}system|alter{_W}database"
    rf"|create{_W}role|create{_W}user|create{_W}group|create{_W}extension|drop{_W}owned|reassign{_W}owned)\b",
    re.IGNORECASE,
)
# `COPY ... PROGRAM` runs a shell command; `GRANT r TO s` and `REVOKE r FROM s` (no ON) change role membership.
_COPY_PROGRAM = re.compile(r"copy\b.*?\bprogram\b", re.IGNORECASE | re.DOTALL)
_ROLE_MEMBERSHIP = re.compile(r"(grant|revoke)\b(?!.*?\bon\b)", re.IGNORECASE | re.DOTALL)


def refused_statements(text: str) -> list[str]:
    """Reasons a file must be refused, from `lex` (the emptied view) and the list: a lexer problem;
    transaction control; every `SET` and `RESET` except `SET LOCAL lock_timeout` and `SET LOCAL statement_timeout`;
    `DO`, `EXECUTE`, `LOAD`, `DISCARD`, `COPY ... PROGRAM`, `ALTER ROLE|USER|GROUP|SYSTEM|DATABASE`,
    `CREATE ROLE|USER|GROUP|EXTENSION`, `GRANT` and `REVOKE` without `ON` (role membership), `DROP OWNED`,
    `REASSIGN OWNED`; hidden characters (`hidden_character`) come first. A rule matches at the START of a
    statement (the cleaned text split at `;`, leading whitespace removed). A tripwire against accidents, not a
    sandbox: the read-back after each file is the guard."""
    cleaned, problem = lex(text)
    reasons = [hidden] if (hidden := hidden_character(text)) else []
    if problem:
        reasons.append(problem)
    for stmt in cleaned.split(";"):
        s = stmt.lstrip(_WS)
        if not s:
            continue
        if m := _TRANSACTION.match(s):
            word = " ".join(m.group(1).upper().split())
            hint = (
                "; inside a function body write $$ ... $$ instead of BEGIN ATOMIC ... END"
                if word in ("BEGIN", "END")
                else ""
            )
            reasons.append(
                f"{word}: transaction control is not allowed (the run is one transaction){hint}"
            )
        elif m := _SET.match(s):
            if not _SET_ALLOWED.match(s):
                reasons.append(
                    f"{m.group(1).upper()}: a session or role setting may not be changed by a migration"
                )
        elif m := _BLIND.match(s):
            word = " ".join(m.group(1).upper().split())
            reasons.append(f"{word}: the guard cannot read what this statement does or changes")
        elif _COPY_PROGRAM.match(s):
            reasons.append(
                "COPY ... PROGRAM: the guard cannot read what this statement does or changes"
            )
        elif m := _ROLE_MEMBERSHIP.match(s):
            reasons.append(
                f"{m.group(1).upper()} without ON: the guard cannot read what this statement does or changes"
            )
    return reasons
