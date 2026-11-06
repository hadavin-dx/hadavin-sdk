"""The migration rule, as pure functions (no database library): file-name numbers, late files, the written recipe for
a late file, the ledger-without-file message, and the one-pass SQL lexer with the refusal list.

`store/migrate.py` calls these before it connects. Nothing here opens a connection; the only file access is
`list_migration_files`, `check_migration_numbers` (directory listings) and `read_files` (one read per file).

Why a lexer of our own: a file that creates a table without the exact grants, or that ends the one migration
transaction, or that changes the role or a setting, must be refused. The text rules below are a tripwire against
accidents and a help to the reviewer of a migration; the guard that cannot be blinded by spelling is the read-back in
`migrate()` after each file (a later change). The lexer follows the PostgreSQL scanner rules that matter for where a
string, comment or body starts and ends, with `standard_conforming_strings = on`.
"""

from __future__ import annotations

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
# The one place this command is written (the message, the module docstring of `migrate` and the CHANGELOG use it).
RECIPE_COMMAND = "psql -X -v ON_ERROR_STOP=1 -f recipe.sql"
# The one generated psql command: with it a run WITHOUT -X still stops at the first error even when a person's startup
# file says `\set ON_ERROR_STOP off`.
RECIPE_FIRST_LINE = "\\set ON_ERROR_STOP on"
# The advisory-lock key of every migrate run, `migrate._LOCK` (a later change makes that name point here).
MIGRATE_LOCK = int.from_bytes(b"hadvnmig", "big") >> 1
# Runbook case (e) (rename recipe for databases built from a branch) is written (ticket Open point 12, recommended yes).
RUNBOOK_E = True
MIGRATIONS = Path(__file__).parent / "migrations"

# The recipe's ledger line (text for a person to run, never executed here). Filled with `replace` after the stem passed
# STEM, so no quote can occur; not an f-string, which the SQL-injection scanner would flag.
_LEDGER_INSERT = "INSERT INTO schema_migrations (version) VALUES ('{stem}');"
_WS = " \t\n\r\f\v"  # statement-start whitespace: the server's set plus vertical tab (the safe direction)
_ALLOWED_CONTROL = "\t\n\r\f"


class MigrationNumberError(ConfigError):
    """The migration files or the ledger are inconsistent. `problems` holds all of them; the message shows at most
    `MAX_PROBLEMS_SHOWN` and a count of the rest."""

    def __init__(self, problems: Sequence[str]):
        self.problems: tuple[str, ...] = tuple(problems)
        shown = list(self.problems[:MAX_PROBLEMS_SHOWN])
        if len(self.problems) > MAX_PROBLEMS_SHOWN:
            shown.append(f"and {len(self.problems) - MAX_PROBLEMS_SHOWN} more")
        super().__init__("migrations are inconsistent: " + "; ".join(shown))


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
    the scan and the run is not run in its new form. An unreadable file raises the original error."""
    return {p: p.read_text(encoding="utf-8") for p in files}


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
    if any(ch not in _ALLOWED_CONTROL and unicodedata.category(ch) == "Cc" for ch in text):
        return "the text holds a control character (an escape code could hide what is copied)"
    if "\\" in text:
        return "psql would read part of it as a command (a backslash)"
    cleaned, problem = statement_text(text)
    if problem:
        return f"the text cannot be read: {problem}"
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
        f"SELECT pg_advisory_xact_lock({lock});",
    ]
    for stem, text in entries:
        lines.append(text)
        cleaned, _ = statement_text(text)
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
    head = (
        f"{names} is numbered at or below the applied '{_esc(highest)}' and must not run in the normal way. "
        "Do not rename it. A database administrator applies it by hand, as the migration role, while no "
        "migrate runs. "
    )
    try:
        recipe = hand_recipe([(p.name[:-4], texts[p]) for p in late], schema)
    except ValueError as e:
        return [
            head
            + f"No recipe is printed: {e}. A person must write the steps by hand, with a reviewer. "
            "Runbook: CHANGELOG.md, case (a)."
        ]
    return [
        head
        + "Save the lines between the two RECIPE lines below to a file, for example recipe.sql, and run exactly: "
        f"{RECIPE_COMMAND} with your own connection settings (-X keeps psql from reading your own startup file, "
        "which could switch off the stop at the first error) (a PGSERVICE entry or the usual PG environment "
        "variables; this message never prints a connection string). Do not type the lines into psql one by one. "
        "If psql prints an error it stops and keeps nothing. Before you start, review each file against every "
        "later applied migration. Afterwards run migrate again with the usual role options (that re-applies the "
        "grants). Write the date, the files and your name in the change log. Runbook: CHANGELOG.md, case (a).\n"
        + recipe
    ]


def _names(names: Sequence[str]) -> str:
    return ", ".join(_esc(n) for n in names)


# --- a ledger name that has no file ------------------------------------------------------------------------------------


def gone_message(applied: Collection[str], files: Sequence[Path]) -> str:
    """ "" when every applied name has a file. Otherwise a prefix line (kept word for word: existing tests match it)
    and ONE line per case present; each orphan gets exactly one case, decided by NAME (1 rename, 2 newer, 3 a person
    must look). The rename line does not print the file's stem."""
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
    orphan_texts = [o[5:] for o in orphans if STEM.fullmatch(o)]
    cases: dict[int, list[str]] = {1: [], 2: [], 3: []}
    for o in orphans:
        if STEM.fullmatch(o):
            same = after.get(o[5:], [])
            if len(same) == 1 and same[0] not in applied and orphan_texts.count(o[5:]) == 1:
                cases[1].append(o)
                continue
            if int(o[:4]) > highest:
                cases[2].append(o)
                continue
        cases[3].append(o)
    e = " and (e)" if RUNBOOK_E else ""

    lines = [f"applied migrations have no file in this release: {_names(orphans)}."]
    if cases[1]:
        lines.append(
            f"{_names(cases[1])}: the folder has a file with the same name after the number, so the file was probably "
            "renamed. If it is the same migration and its tables already exist, a database administrator changes "
            "the version of each of these ledger rows by hand to the stem of that file, under the migration lock "
            "(runbook case (b))."
        )
    if cases[2]:
        lines.append(
            f"{_names(cases[2])}: this database is newer than this release. Do not rename, drop or edit the ledger. Run "
            "the release that has these files. If the code was not reverted, and the row was renamed or the "
            f"database was built from a branch, see runbook case (b){e}."
        )
    if cases[3]:
        lines.append(
            f"{_names(cases[3])}: no file in this release has this name, and the number is not above the highest file "
            "number, so this is neither a newer database nor a plain rename. A person must look: do not rename "
            f"or drop by guess (runbook case (c){e})."
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
    return 1 + head.count("\n") + head.count("\r") - head.count("\r\n")


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


def statement_text(text: str, keep_quoted: bool = False) -> tuple[str, str]:
    """ONE left-to-right pass: comments become one space and every quoted part is emptied (`''`, `""`, `$$`), plus a
    problem string (`""` when fine). With `keep_quoted=True` quoted parts are kept as written and only comments are
    replaced; the problem string is the same in both views.

    Handled in the same pass so that no rule runs before another: `--` to the next LF or CR; nested block comments;
    `'...'` with `''`; `E'...'` where a backslash escapes the next character (an `E` not preceded by an identifier
    character) and a second literal that continues it after a newline is refused (the server keeps E mode there);
    `"..."` with `""`; `$tag$...$tag$` (tag: ASCII letter, underscore or any non-ASCII character, then those or
    digits; compared with case; only when the `$` is not preceded by an identifier character); `$1` is left alone and
    any other `$` is refused. Precondition: `standard_conforming_strings = on`."""
    out: list[str] = []
    problem = ""
    n = len(text)
    i = 0

    def fail(kind: str, at: int) -> None:
        nonlocal problem
        if not problem:
            problem = f"{kind} at line {_line_of(text, at)}"

    while i < n:
        m = _SPECIAL.search(text, i)
        if m is None:
            out.append(text[i:])
            break
        j = m.start()
        if j > i:
            out.append(text[i:j])
        c = text[j]
        prev = text[j - 1] if j > 0 else ""
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
            e_mode = prev in "Ee" and prev != "" and not (j >= 2 and _ident_char(text[j - 2]))
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
            if prev and _ident_char(prev):
                out.append("$")
                i = j + 1
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
            end = text.find(tag, k + 1)
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
    rf"(do|execute|alter{_W}role|alter{_W}user|alter{_W}database|drop{_W}owned|reassign{_W}owned)\b",
    re.IGNORECASE,
)


def refused_statements(text: str) -> list[str]:
    """Reasons a file must be refused, from `statement_text` (the emptied view) and the list: a lexer problem;
    transaction control; every `SET` and `RESET` except `SET LOCAL lock_timeout` and `SET LOCAL statement_timeout`;
    `DO`, `EXECUTE`, `ALTER ROLE|USER|DATABASE`, `DROP OWNED`, `REASSIGN OWNED`. A rule matches at the START of a
    statement (the cleaned text split at `;`, leading whitespace removed). A tripwire against accidents, not a
    sandbox: the read-back after each file is the guard."""
    cleaned, problem = statement_text(text)
    reasons = [problem] if problem else []
    for stmt in cleaned.split(";"):
        s = stmt.lstrip(_WS)
        if not s:
            continue
        if m := _TRANSACTION.match(s):
            word = " ".join(m.group(1).upper().split())
            reasons.append(
                f"{word}: transaction control is not allowed (the run is one transaction)"
            )
        elif m := _SET.match(s):
            if not _SET_ALLOWED.match(s):
                reasons.append(
                    f"{m.group(1).upper()}: a session or role setting may not be changed by a migration"
                )
        elif m := _BLIND.match(s):
            word = " ".join(m.group(1).upper().split())
            reasons.append(f"{word}: the guard cannot read what this statement does or changes")
    return reasons
