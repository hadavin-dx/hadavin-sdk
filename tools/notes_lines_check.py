"""List the tests (and the files that make tests pass or fail) that are new or changed against a base commit and check
that a builder's notes hold a row for each.

    python tools/notes_lines_check.py <base-commit> <notes.md> <file> [<file> ...]
    python tools/notes_lines_check.py --auto <base-commit> [--head <commit>]

What it reads. In each test file it reads every top-level `test_*` function (plain or `async`) and every `test_*`
method of a top-level class whose name starts with `Test` (named `Class::test_x`). A test is "new or changed" when
it is missing from the base commit's copy of the file, or when its own syntax tree differs, or when the syntax tree
of anything it uses differs, to any depth: a module-level function, class, constant, import or `+=` it names, a
fixture it names as a parameter, every fixture of the same file marked `autouse=True` (it applies to every test of
the file, named or not), and what a name imported from another test module is (`from tests.x import name`,
`from tests import x` then `x.name`, `import tests.x as x`, or a relative form, also inside a function). A helper, a
fixture or a constant that changed therefore lists every test that uses it.

Four kinds of file are in scope, because a change to any of them can make a test pass or fail without touching a
test function. `tests/test_*.py`: the tests, as above. `tests/policy_mutants.py` and `tests/stage_mutants.py`: each
`mutant(...)` (or `Mutant(...)`) call whose first argument is a text is one unit named by that text; a mutant that is
new or altered needs a row, a mutant that is gone is a problem, and so is a count that fell. `conftest.py`: each
top-level function or class is one unit. `tests/fixtures/policy_sources_*.txt`: the whole file is one unit named by
its file name.

What the notes must hold. A table row (a line that starts with `|`) whose FIRST cell is the file (its name, or the
end of its path, ending `.py` or `.txt`) and whose SECOND cell names the unit in backticks (`test_x`,
`Class::test_x`, a function of a conftest, a file name; for a mutant the full text of its name, in backticks or, when
the name holds a backtick itself, written in the cell); the id is read from that cell only, so a name mentioned in
another cell or another row counts for nothing, and the same name in two files needs a row for each file. The LAST
cell is the reason; it must pass `reason_problem`: at least `MIN_WORDS` words, not a placeholder, one of
`REASON_MARKERS` as a whole word or phrase (a killing mutant, a failing run on the old code, a plant, or the
control reason), and after the marker an identifier (a backticked text, a file name, a mutant code such as B11,
a test name or a commit id) that a reader can look up. A unit that existed in the base and is gone now is a
problem too.

What it does NOT show. It does not show that a test was not weakened: it lists the changed units and checks that a
reason with something to look up was written; whether the reason is true is for the reviewer reading the diff. It
reads only the syntax of Python files: a test written another way (generated, or collected by a plugin), a name
bound inside an `if`, `try` or `for` at the top of a module, a change in `src/` or `tools/` that a test uses (those
have their own mutants), and a change to a file outside the four kinds above are not seen. A text a function reads
from a file at run time is seen only through the fixture file kind. A row is checked for form, never for truth.

Exit codes: 0 when every listed unit has its row; 1 with one plain line per problem; 1 when the base commit does not
resolve (a mistyped base would make every test look new); 1 when git cannot give the change (a failed `merge-base`
or `diff`: never read as "nothing changed"); 2 for a wrong command line. `--auto <base>` is for a pull request: it
reads the change as `git diff --no-renames <merge-base of base and head> <head>` and every file's text as the blob of
that head (`git show <head>:path`), never the working tree, so the answer is the same whatever is checked out, and
each run covers the whole pull request, not the last push. `--head` defaults to HEAD. With no file of the four kinds
in the change there is nothing to check (and it says so); with a changed unit and no notes file in the change,
every changed unit is a problem (no row). It runs `git` only, with a fixed argument list and no shell, and reads
files; it never writes."""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

MIN_WORDS = 4  # words of the reason cell
PLACEHOLDERS = frozenset(
    {"ok", "todo", "tbd", "x", "n/a", "na", "same", "none", "-", "...", "later"}
)
# Whole words or phrases (a word boundary on both sides: "plant" is not found in "implant", "control" is not found in
# "controller"). "passes on" is not a reason: that a test passes on the old code is a fact to explain, not an
# explanation.
REASON_MARKERS = (
    "killing mutant",
    "fails on",
    "fail-before",
    "fails before",
    "plant",
    "control",
)
_MARKER = re.compile(
    r"\b(?:killing mutants?|fails? on|fail-before|fails? before|plants?|controls?)\b", re.IGNORECASE
)
# Something a reader can look up after the marker: a backticked text, a file name, a mutant code (B11, P09b), a test
# name, or a commit id of 7 to 40 hex digits (with at least one digit, so a word like "defaced" is not one).
_IDENTIFIER = re.compile(
    r"`[^`]+`"
    r"|[\w./-]+\.(?:txt|log|md|json|py)\b"
    r"|\b[A-Z]{1,3}\d+[a-z]?\b"
    r"|\btest_\w+"
    r"|\b(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b"
)
_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)
_MUTANT_CALLS = ("mutant", "Mutant")

Loader = Callable[
    [str], str
]  # path of a file -> its text in the state being read ("" when it is not there)


# ----------------------------------------------------------------------------------------------- reading a module


def _bound(alias: ast.alias) -> str:
    return alias.asname or alias.name.split(".")[0]


def _is_autouse(fn: ast.AST) -> bool:
    """True for a function decorated `@pytest.fixture(..., autouse=True, ...)` (or `@fixture(...)`)."""
    for d in getattr(fn, "decorator_list", []):
        if isinstance(d, ast.Call):
            callee = d.func.attr if isinstance(d.func, ast.Attribute) else getattr(d.func, "id", "")
            if callee == "fixture" and any(
                k.arg == "autouse" and isinstance(k.value, ast.Constant) and k.value.value is True
                for k in d.keywords
            ):
                return True
    return False


def _stem(rel: str, level: int, module: str | None) -> str | None:
    """The path stem of the module an import names, or None when it is not under `tests`. `from tests.x import a`
    names tests/x; `from . import x` or `from .x import a` in tests/y.py names tests/x."""
    parts = module.split(".") if module else []
    if level:
        here = rel.split("/")[:-1]
        parts = [*(here[: len(here) - (level - 1)] if level > 1 else here), *parts]
    return "/".join(parts) if parts and parts[0] == "tests" else None


def _imports(tree: ast.AST, rel: str) -> dict[str, tuple[str, str | None]]:
    """local name -> (path stem of a module under `tests`, the name taken from it or None for the module itself),
    for every import of the file that reaches such a module (module level or inside a function)."""
    out: dict[str, tuple[str, str | None]] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            stem = _stem(rel, n.level, n.module)
            if stem is not None:
                out.update({a.asname or a.name: (stem, a.name) for a in n.names})
        elif isinstance(n, ast.Import):
            for a in n.names:
                stem = _stem(rel, 0, a.name)
                if stem is not None:
                    out[a.asname or a.name.split(".")[0]] = (stem, None)
    return out


class _Module:
    """One parsed Python file: the dump of every module-level binding, the nodes of its functions and classes, the
    imports of the whole file (also inside a function) and its autouse fixtures."""

    def __init__(self, rel: str, source: str) -> None:
        self.rel = rel
        self.tree = ast.parse(source)
        self.dumps: dict[str, str] = {}
        self.nodes: dict[str, ast.AST] = {}
        for n in self.tree.body:
            if isinstance(n, (*_FUNCS, ast.ClassDef)):
                names = [n.name]
                self.nodes[n.name] = n
            elif isinstance(n, ast.Assign):
                names = [t.id for t in n.targets if isinstance(t, ast.Name)]
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and isinstance(n.target, ast.Name):
                names = [
                    n.target.id
                ]  # `X += ...` changes what X is, so it is joined to the dump of X
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                names = [_bound(a) for a in n.names]
            else:
                continue
            for name in names:
                self.dumps[name] = self.dumps.get(name, "") + ast.dump(n)
        self.imports = _imports(self.tree, rel)
        self.autouse = [n.name for n in self.tree.body if isinstance(n, _FUNCS) and _is_autouse(n)]


def _used(node: ast.AST) -> set[str]:
    """The names a function uses: every name it reads, `mod.attr` for an attribute of a plain name (a module's
    member), and every parameter (a fixture is a parameter)."""
    used: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            used.add(n.id)
        elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
            used.add(f"{n.value.id}.{n.attr}")
    if isinstance(node, _FUNCS):
        args = node.args
        used |= {a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
    return used


class _Signatures:
    """The signature of a unit: its own dump plus the dump of everything it uses, to any depth, across the files
    under `tests` that it imports from (each file is parsed once)."""

    def __init__(self, loader: Loader | None) -> None:
        self.loader = loader
        self.modules: dict[str, _Module | None] = {}

    def module(self, rel: str, source: str | None = None) -> _Module | None:
        if rel not in self.modules:
            text = source if source is not None else (self.loader(rel) if self.loader else "")
            try:
                self.modules[rel] = _Module(rel, text) if text else None
            except SyntaxError:
                self.modules[rel] = None
        return self.modules[rel]

    def _file_of(self, stem: str) -> str | None:
        return next((c for c in (f"{stem}.py", f"{stem}/__init__.py") if self.module(c)), None)

    def _imported(
        self, table: dict[str, tuple[str, str | None]], head: str, attr: str
    ) -> tuple[_Module | None, str]:
        """(the module and member that the import `head` (+ `.attr`) of the table stands for, the member name)."""
        stem, taken = table[head]
        if taken is None:  # `import tests.x as head`: head.attr is a member of tests/x.py
            return self.module(self._file_of(stem) or ""), attr
        file = self._file_of(stem)
        inner = self.module(file) if file else None
        if (
            inner is not None and taken in inner.dumps
        ):  # `from tests.x import taken`: a member of tests/x.py
            return inner, taken
        sub = self._file_of(
            f"{stem}/{taken}"
        )  # `from tests import taken`: taken is the module tests/taken.py
        return self.module(sub) if sub else None, attr

    def closure(self, mod: _Module, node: ast.AST, own: str) -> str:
        """The signature text of `node`, a unit of `mod` named `own`."""
        parts: list[str] = []
        seen: set[tuple[str, str]] = {(mod.rel, own)}
        todo: list[tuple[_Module, str]] = [(mod, u) for u in sorted(_used(node))]
        todo += [(mod, a) for a in mod.autouse]
        while todo:
            m, name = todo.pop()
            if (m.rel, name) in seen:
                continue
            seen.add((m.rel, name))
            head, _, attr = name.partition(".")
            if name in m.dumps:
                parts.append(f"|{m.rel}:{name}={m.dumps[name]}")
                if name in m.nodes:
                    todo += [(m, u) for u in sorted(_used(m.nodes[name]))]
            table = (
                m.imports
            )  # (every import of the file, also one inside a function: see `_imports`)
            if head not in table:
                continue
            target, member = self._imported(table, head, attr)
            if target is None:
                continue
            if member and member in target.dumps:
                todo.append((target, member))
            elif (
                not member
            ):  # the module itself is used as a value: its whole text is the dependency
                parts.append(f"|module {target.rel}={ast.dump(target.tree)}")
        return ast.dump(node) + "".join(sorted(parts))


def _units_of_tests(mod: _Module) -> dict[str, ast.AST]:
    """key -> node: `name` for a top-level test function (plain or async), `Class::name` for a method of a
    top-level `Test*` class."""
    out: dict[str, ast.AST] = {}
    for n in mod.tree.body:
        if isinstance(n, _FUNCS) and n.name.startswith("test_"):
            out[n.name] = n
        elif isinstance(n, ast.ClassDef) and n.name.startswith("Test"):
            for m in n.body:
                if isinstance(m, _FUNCS) and m.name.startswith("test_"):
                    out[f"{n.name}::{m.name}"] = m
    return out


def _units_of_functions(mod: _Module) -> dict[str, ast.AST]:
    """key -> node for every top-level function or class (a conftest)."""
    return {n.name: n for n in mod.tree.body if isinstance(n, (*_FUNCS, ast.ClassDef))}


def _mutant_units(mod: _Module) -> dict[str, str]:
    """name -> dump, for every `mutant(...)` or `Mutant(...)` call with a text as first argument, in the whole file
    (the dumps of the same name are joined). The dump of the builder function `mutant` is part of every one: a change
    of the builder changes what every mutant is."""
    builder = "".join(
        ast.dump(n) for n in mod.tree.body if isinstance(n, _FUNCS) and n.name in _MUTANT_CALLS
    )
    out: dict[str, str] = {}
    for n in ast.walk(mod.tree):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id in _MUTANT_CALLS
            and n.args
            and isinstance(n.args[0], ast.Constant)
            and isinstance(n.args[0].value, str)
        ):
            out[n.args[0].value] = out.get(n.args[0].value, "") + ast.dump(n)
    return {k: v + "|" + builder for k, v in out.items()}


_TEST_FILE = re.compile(r"tests/(?:.+/)?test_[^/]*\.py")
_MUTANT_FILE = re.compile(r"tests/(?:policy_mutants|stage_mutants)\.py")
_CONFTEST = re.compile(r"tests/(?:.+/)?conftest\.py")
_FIXTURE_FILE = re.compile(r"tests/fixtures/policy_sources_[^/]*\.txt")
_NOTES_FILE = re.compile(r"handover/evidence/.+/NOTES\.md")


def kind_of(rel: str) -> str | None:
    """'test', 'mutants', 'conftest', 'fixture' or None (a file outside the four kinds)."""
    if _TEST_FILE.fullmatch(rel):
        return "test"
    if _MUTANT_FILE.fullmatch(rel):
        return "mutants"
    if _CONFTEST.fullmatch(rel):
        return "conftest"
    if _FIXTURE_FILE.fullmatch(rel):
        return "fixture"
    return None


def units_of(rel: str, source: str, loader: Loader | None = None) -> dict[str, str]:
    """key -> a signature, for the file `rel` with text `source`; `loader` gives the text of another file in the
    same state (to follow imports). An empty source has no units, and nor has a file that does not parse (a
    broken file is caught by the test run)."""
    if not source:
        return {}
    kind = kind_of(rel) or "test"
    if kind == "fixture":
        return {Path(rel).name: source}
    sigs = _Signatures(loader)
    mod = sigs.module(rel, source)
    if mod is None:
        return {}
    if kind == "mutants":
        return _mutant_units(mod)
    nodes = _units_of_tests(mod) if kind == "test" else _units_of_functions(mod)
    return {key: sigs.closure(mod, node, key.split("::")[-1]) for key, node in nodes.items()}


def tests_of(
    source: str, rel: str = "tests/test_x.py", loader: Loader | None = None
) -> dict[str, str]:
    """key -> a signature of the test: the dump of the test itself and of everything it uses (see the module
    docstring), to any depth."""
    return units_of(rel, source, loader)


def changed_tests(
    old: str,
    new: str,
    rel: str = "tests/test_x.py",
    old_loader: Loader | None = None,
    new_loader: Loader | None = None,
) -> tuple[list[str], list[str]]:
    """(new or changed unit keys, keys that existed before and are gone), each sorted."""
    before = units_of(rel, old, old_loader)
    after = units_of(rel, new, new_loader)
    changed = sorted(n for n, d in after.items() if before.get(n) != d)
    gone = sorted(set(before) - set(after))
    return changed, gone


# ----------------------------------------------------------------------------------------------- the notes


def reason_problem(reason: str) -> str:
    """'' when the reason cell is a real reason, else why not."""
    if reason.strip(" .").lower() in PLACEHOLDERS or len(reason.split()) < MIN_WORDS:
        return f"the reason `{reason}` is a placeholder or has fewer than {MIN_WORDS} words"
    found = _MARKER.search(reason)
    if found is None:
        return (
            f"the reason `{reason[:60]}` names no killing mutant, failing run on the old code, "
            "plant or control reason (as whole words)"
        )
    if not _IDENTIFIER.search(reason[found.end() :]):
        return (
            f"the reason `{reason[:60]}` gives nothing to look up after `{found.group(0)}` (a mutant code or "
            "name, a test name, a log file name or a commit id)"
        )
    return ""


def lines_of(notes: str) -> dict[tuple[str, str], tuple[str, str]]:
    """(file cell, unit id) -> (the reason cell (the last cell), the second cell), for every table row with at least
    three cells whose first cell names a file (`*.py` or `*.txt`) and whose second cell holds ids in backticks. Only
    those two cells are read for the key."""
    out: dict[tuple[str, str], tuple[str, str]] = {}
    for line in notes.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        file_cell = cells[0].strip("`").strip()
        if not file_cell.endswith((".py", ".txt")):
            continue
        for name in re.findall(r"`([^`]+)`", cells[1]):
            out[(file_cell, name)] = (cells[-1], cells[1])
        # the whole cell is a key too: the names of two mutants that hold the same backticked word each keep their
        # own row (the backticked word alone would be one key and the second row would replace the first)
        out[(file_cell, cells[1])] = (cells[-1], cells[1])
    return out


def _file_matches(file_cell: str, rel: str) -> bool:
    return rel == file_cell or rel.endswith("/" + file_cell)


def problems(
    changed: list[str],
    gone: list[str],
    notes: str,
    label: str,
    counts: tuple[int, int] | None = None,
) -> list[str]:
    """One line per problem for the file `label`: a changed unit with no row (file and id from the first two
    cells) or with a bad reason, and a unit that is gone. `counts` (units before, units now) is given for a file of
    mutants: a count that fell is a problem of its own."""
    rows = {
        name: (reason, cell)
        for (file_cell, name), (reason, cell) in lines_of(notes).items()
        if _file_matches(file_cell, label)
    }
    word = "mutant" if kind_of(label) == "mutants" else "test"
    out = []
    for n in changed:
        found = rows.get(n)
        if (
            found is None and word == "mutant"
        ):  # a name with a backtick in it cannot be written in backticks
            found = next(((r, c) for r, c in rows.values() if n in c), None)
        if found is None:
            out.append(
                f"{label}: the {word} {n} is new or changed and has no row of its own in the notes"
            )
            continue
        why = reason_problem(found[0])
        if why:
            out.append(f"{label}: the {word} {n} has a row but {why}")
    out += [
        f"{label}: the {word} {n} existed in the base commit and is gone (never delete a {word})"
        for n in gone
    ]
    if counts is not None and counts[1] < counts[0]:
        out.append(f"{label}: the mutant count fell from {counts[0]} to {counts[1]}")
    return out


# ----------------------------------------------------------------------------------------------- git


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


def _show(rev: str, rel: str) -> str:
    proc = _git("show", f"{rev}:{rel}")
    return proc.stdout if proc.returncode == 0 else ""  # a file new since the base has no old text


def check(base: str, notes: str, files: list[str], head: str | None = None) -> list[str]:
    """Every problem line for the files `files` against `base`; a file missing now counts as empty (its units
    are gone). With `head` the new text of every file (and of the test modules it imports) is the blob of that
    commit (`git show head:path`), else the file on disk."""
    if not base_resolves(base):
        return [f"the base commit {base!r} does not resolve: every test would look new"]
    if head is not None and not base_resolves(head):
        return [f"the head commit {head!r} does not resolve"]

    def old_load(rel: str) -> str:
        return _show(base, rel)

    def new_load(rel: str) -> str:
        if head is not None:
            return _show(head, rel)
        path = Path(rel)
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    bad: list[str] = []
    for rel in files:
        old, now = old_load(rel), new_load(rel)
        changed, gone = changed_tests(old, now, rel, old_load, new_load)
        counts = None
        if kind_of(rel) == "mutants":
            counts = (len(units_of(rel, old, old_load)), len(units_of(rel, now, new_load)))
        bad += problems(changed, gone, notes, rel, counts)
    return bad


def auto_files(base: str, head: str = "HEAD") -> tuple[str, str, list[str], list[str]] | str:
    """(merge-base, head commit, files in scope, notes files present at head) of the change, or ONE problem line
    when git cannot give it (the base or head does not resolve, there is no common ancestor, or `diff` fails: a
    failure is never read as "nothing changed"). The change is `git diff --no-renames merge-base head`."""
    if not base_resolves(base):
        return f"the base commit {base!r} does not resolve: every test would look new"
    if not base_resolves(head):
        return f"the head commit {head!r} does not resolve"
    sha = _git("rev-parse", head)
    merged = _git("merge-base", base, head)
    if sha.returncode != 0 or merged.returncode != 0 or not merged.stdout.strip():
        return (
            f"git found no common ancestor of {base!r} and {head!r} (a shallow checkout: fetch the full "
            "history, `fetch-depth: 0`)"
        )
    mb, head_sha = merged.stdout.strip(), sha.stdout.strip()
    diff = _git("diff", "--name-only", "--no-renames", "-z", mb, head_sha)
    if diff.returncode != 0:
        return (
            f"`git diff {mb[:12]} {head_sha[:12]}` failed (exit {diff.returncode}): "
            f"{diff.stderr.strip()[:200]}"
        )
    names = [n for n in diff.stdout.split("\0") if n]
    return (
        mb,
        head_sha,
        [n for n in names if kind_of(n)],
        sorted(n for n in names if _NOTES_FILE.fullmatch(n) and _show(head_sha, n)),
    )


def main(argv: list[str]) -> int:
    if argv[:1] == ["--auto"] and len(argv) in (2, 4) and (len(argv) == 2 or argv[2] == "--head"):
        found = auto_files(argv[1], argv[3] if len(argv) == 4 else "HEAD")
        if isinstance(found, str):
            print(found)
            return 1
        mb, head_sha, files, notes_files = found
        if not files:
            print("no test file changed in this change: nothing to check")
            return 0
        notes = "\n".join(_show(head_sha, n) for n in notes_files)
        bad = check(mb, notes, files, head_sha)
        if bad and not notes_files:
            bad.insert(0, "the change has no builder notes file (handover/evidence/**/NOTES.md)")
    elif len(argv) >= 3 and not argv[0].startswith("-"):
        notes = Path(argv[1]).read_text(encoding="utf-8")
        bad = check(argv[0], notes, argv[2:])
    else:
        print(
            "usage: notes_lines_check.py <base-commit> <notes.md> <file> [...]\n"
            "       notes_lines_check.py --auto <base-commit> [--head <commit>]",
            file=sys.stderr,
        )
        return 2
    for line in bad:
        print(line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
