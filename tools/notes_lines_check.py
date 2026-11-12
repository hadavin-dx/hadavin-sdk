"""List the tests that are new or changed against a base commit and check that a builder's notes hold a row for each.

    python tools/notes_lines_check.py <base-commit> <notes.md> <test file> [<test file> ...]
    python tools/notes_lines_check.py --auto <base-commit>

What it reads. In each test file it reads every top-level `test_*` function (plain or `async`) and every `test_*`
method of a top-level class whose name starts with `Test` (named `Class::test_x`). A test is "new or changed" when
it is missing from the base commit's copy of the file, or when its own syntax tree differs, or when the syntax tree
of anything it uses from the same file differs: a module-level function, class, constant or fixture it names, and
(transitively) what those name. A helper, a fixture or a constant that changed therefore lists every test that
uses it. Names that come from another file are not followed (a change there is not seen).

What the notes must hold. A table row (a line that starts with `|`) whose FIRST cell is the test file (its name, or
the end of its path) and whose SECOND cell names the test id in backticks (`test_x`, or `Class::test_x`); the id is
read from that cell only, so a name mentioned in another cell or another row counts for nothing, and the same name
in two files needs a row for each file. The LAST cell is the reason; it must pass `reason_problem`: at least
`MIN_WORDS` words, not a placeholder, and naming one of `REASON_MARKERS` (a killing mutant, a failing run on the
old code, a plant, or the control reason). A test that existed in the base and is gone now is a problem too.

What it does NOT show. It does not show that a test was not weakened: it lists the changed tests and checks that a
reason was written; whether the reason is true is for the reviewer reading the diff. Only functions and methods are
compared (not a test written another way), and only the files it is given.

Exit codes: 0 when every listed test has its row; 1 with one plain line per problem; 1 when the base commit does not
resolve (a mistyped base would make every test look new); 2 for a wrong command line. `--auto <base>` takes the
changed files from `git diff --name-only <base> HEAD`: the test files `tests/**/test_*.py` and the notes files
`handover/evidence/**/NOTES.md` among them; with no test file in the change there is nothing to check (and it says
so); with a changed test and no notes file in the change, every changed test is a problem (no row). In CI the base
is the head the pull request had before the push (the base of the pull request when it is new), so each push that
changes a test carries its notes. It runs `git` only, with a fixed argument list and no shell, and reads files; it never writes."""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

MIN_WORDS = 4  # words of the reason cell
PLACEHOLDERS = frozenset(
    {"ok", "todo", "tbd", "x", "n/a", "na", "same", "none", "-", "...", "later"}
)
REASON_MARKERS = (
    "killing mutant",
    "fails on",
    "fail-before",
    "fails before",
    "plant",
    "control",
    "passes on",
)
_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _tests(tree: ast.Module) -> dict[str, ast.AST]:
    """key -> node: `name` for a top-level test function (plain or async), `Class::name` for a method of a
    top-level `Test*` class."""
    out: dict[str, ast.AST] = {}
    for n in tree.body:
        if isinstance(n, _FUNCS) and n.name.startswith("test_"):
            out[n.name] = n
        elif isinstance(n, ast.ClassDef) and n.name.startswith("Test"):
            for m in n.body:
                if isinstance(m, _FUNCS) and m.name.startswith("test_"):
                    out[f"{n.name}::{m.name}"] = m
    return out


def _module(tree: ast.Module) -> tuple[dict[str, str], dict[str, ast.AST]]:
    """(name -> the dump of every module-level function, class or assignment that binds it, joined when bound
    twice; name -> the function or class node, for following what it uses)."""
    dumps: dict[str, str] = {}
    nodes: dict[str, ast.AST] = {}
    for n in tree.body:
        if isinstance(n, (*_FUNCS, ast.ClassDef)):
            names = [n.name]
            nodes[n.name] = n
        elif isinstance(n, ast.Assign):
            names = [t.id for t in n.targets if isinstance(t, ast.Name)]
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            names = [n.target.id]
        else:
            continue
        for name in names:
            dumps[name] = dumps.get(name, "") + ast.dump(n)
    return dumps, nodes


def _used(node: ast.AST) -> set[str]:
    """The names a function uses: every name it reads and every parameter (a fixture is a parameter)."""
    used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
    if isinstance(node, _FUNCS):
        args = node.args
        used |= {a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
    return used


def tests_of(source: str) -> dict[str, str]:
    """key -> a signature of the test: the dump of the test itself and of everything of the same file it uses, to
    any depth (a changed helper, fixture or constant changes the signature of each test that uses it)."""
    tree = ast.parse(source)
    dumps, nodes = _module(tree)
    out: dict[str, str] = {}
    for key, node in _tests(tree).items():
        seen: set[str] = set()
        todo = [u for u in _used(node) if u in dumps]
        while todo:
            name = todo.pop()
            if name in seen:
                continue
            seen.add(name)
            if name in nodes:
                todo += [u for u in _used(nodes[name]) if u in dumps and u not in seen]
        seen.discard(key.split("::")[-1])
        out[key] = ast.dump(node) + "".join(f"|{name}={dumps[name]}" for name in sorted(seen))
    return out


def changed_tests(old: str, new: str) -> tuple[list[str], list[str]]:
    """(new or changed test keys, keys that existed before and are gone), each sorted."""
    before, after = (tests_of(old) if old else {}), tests_of(new)
    changed = sorted(n for n, d in after.items() if before.get(n) != d)
    gone = sorted(set(before) - set(after))
    return changed, gone


def reason_problem(reason: str) -> str:
    """'' when the reason cell is a real reason, else why not."""
    if reason.strip(" .").lower() in PLACEHOLDERS or len(reason.split()) < MIN_WORDS:
        return f"the reason `{reason}` is a placeholder or has fewer than {MIN_WORDS} words"
    lowered = reason.lower()
    if not any(m in lowered for m in REASON_MARKERS):
        return (
            f"the reason `{reason[:60]}` names no killing mutant, failing run on the old code, "
            "plant or control reason"
        )
    return ""


def lines_of(notes: str) -> dict[tuple[str, str], str]:
    """(file cell, test id) -> the reason cell (the last cell), for every table row with at least three cells whose
    first cell names a file (`*.py`) and whose second cell names test ids in backticks. Only those two cells are
    read for the key."""
    out: dict[tuple[str, str], str] = {}
    for line in notes.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        file_cell = cells[0].strip("`").strip()
        if not file_cell.endswith(".py"):
            continue
        for name in re.findall(r"`((?:\w+::)?test_\w+)`", cells[1]):
            out[(file_cell, name)] = cells[-1]
    return out


def _file_matches(file_cell: str, rel: str) -> bool:
    return rel == file_cell or rel.endswith("/" + file_cell)


def problems(changed: list[str], gone: list[str], notes: str, label: str) -> list[str]:
    """One line per problem for the file `label`: a changed test with no row (file and id from the first two
    cells) or with a bad reason, and a test that is gone."""
    rows = {
        name: reason
        for (file_cell, name), reason in lines_of(notes).items()
        if _file_matches(file_cell, label)
    }
    out = []
    for n in changed:
        if n not in rows:
            out.append(
                f"{label}: the test {n} is new or changed and has no row of its own in the notes"
            )
            continue
        why = reason_problem(rows[n])
        if why:
            out.append(f"{label}: the test {n} has a row but {why}")
    out += [
        f"{label}: the test {n} existed in the base commit and is gone (never delete a test)"
        for n in gone
    ]
    return out


def _git(*args: str) -> subprocess.CompletedProcess:
    git = shutil.which("git")
    if git is None:
        raise SystemExit("git was not found")
    return subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git, *args], capture_output=True, text=True, check=False
    )


def base_resolves(base: str) -> bool:
    """True when `base` names a commit (a mistyped base would make every test look new)."""
    return _git("rev-parse", "--verify", "--quiet", f"{base}^{{commit}}").returncode == 0


def _base_source(base: str, rel: str) -> str:
    proc = _git("show", f"{base}:{rel}")
    return proc.stdout if proc.returncode == 0 else ""  # a file new since the base has no old text


def check(base: str, notes: str, files: list[str]) -> list[str]:
    """Every problem line for the test files `files` against `base`; a file missing now counts as empty (its tests
    are gone)."""
    if not base_resolves(base):
        return [f"the base commit {base!r} does not resolve: every test would look new"]
    bad: list[str] = []
    for rel in files:
        path = Path(rel)
        now = path.read_text(encoding="utf-8") if path.is_file() else ""
        changed, gone = changed_tests(_base_source(base, rel), now)
        bad += problems(changed, gone, notes, rel)
    return bad


_TEST_FILE = re.compile(r"tests/(?:.+/)?test_[^/]*\.py")
_NOTES_FILE = re.compile(r"handover/evidence/.+/NOTES\.md")


def auto_files(base: str) -> tuple[list[str], list[str]] | None:
    """(test files, notes files) of the change `base`..HEAD, or None when the base does not resolve."""
    if not base_resolves(base):
        return None
    names = [n for n in _git("diff", "--name-only", base, "HEAD").stdout.splitlines() if n]
    return (
        [n for n in names if _TEST_FILE.fullmatch(n)],
        [n for n in names if _NOTES_FILE.fullmatch(n) and Path(n).is_file()],
    )


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "--auto":
        found = auto_files(argv[1])
        if found is None:
            print(f"the base commit {argv[1]!r} does not resolve: every test would look new")
            return 1
        files, notes_files = found
        if not files:
            print("no test file changed in this change: nothing to check")
            return 0
        notes = "\n".join(Path(n).read_text(encoding="utf-8") for n in notes_files)
        bad = check(argv[1], notes, files)
        if bad and not notes_files:
            bad.insert(0, "the change has no builder notes file (handover/evidence/**/NOTES.md)")
    elif len(argv) >= 3 and not argv[0].startswith("-"):
        notes = Path(argv[1]).read_text(encoding="utf-8")
        bad = check(argv[0], notes, argv[2:])
    else:
        print(
            "usage: notes_lines_check.py <base-commit> <notes.md> <test file> [...]\n"
            "       notes_lines_check.py --auto <base-commit>",
            file=sys.stderr,
        )
        return 2
    for line in bad:
        print(line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
