"""The CHANGELOG names tests, files and numbers; a name that no longer exists or a number that is no longer true is a claim
nobody can check. Round 16: names are found with `ast` (an exact `def name(`, not a text search), tests are searched in every
folder under `tests/`, any repository path may be named, and the counts of the batch 16 entry are computed here."""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
sys.path.insert(0, str(ROOT / "tests"))


def _defined_test_names() -> set[str]:
    names: set[str] = set()
    for path in (ROOT / "tests").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                names.add(node.name)
    return names


def test_every_test_name_in_the_changelog_is_defined_in_tests():
    defined = _defined_test_names()
    named = set(re.findall(r"`(test_[A-Za-z0-9_]+)`", TEXT))
    assert named, "the CHANGELOG names no test: the scan is empty"
    missing = sorted(n for n in named if n not in defined)
    assert missing == [], f"the CHANGELOG names tests that do not exist: {missing}"


def test_every_repository_path_in_the_changelog_exists():
    paths = set(
        re.findall(
            r"`((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:py|md|yaml|yml|sql|toml|txt|json|sh))`",
            TEXT,
        )
    )
    # a path under the package is written without the `src/hadavin_sdk/` prefix in prose, and a few are examples
    # (a file the reader makes); only paths that start at a folder of this repository are checked
    # `handover/` is the studio's notes folder: it is on its own branch, not in the code branches, so its paths are not checked here
    roots = {p.name for p in ROOT.iterdir() if p.is_dir()} - {"handover"}
    own = sorted(p for p in paths if p.split("/")[0] in roots)
    assert own, "the CHANGELOG names no repository path: the scan is empty"
    missing = [p for p in own if not (ROOT / p).exists()]
    assert missing == [], f"the CHANGELOG names files that do not exist: {missing}"


def _handler_lines(source: str) -> list[tuple[str, int]]:
    """(enclosing function, line) of every `except` handler that carries `noqa: BLE001` on its header (found with `ast`, so a
    handler written over several lines is one, and a comment or a string that holds the words is none)."""
    tree = ast.parse(source)
    lines = source.splitlines()
    parent = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ExceptHandler):
            # the header runs from the `except` line up to the line before the first statement of the body; a one-line handler
            # (`except X: pass  # noqa: BLE001`) has its body on the `except` line itself, so that line is the header
            header = "\n".join(lines[n.lineno - 1 : max(n.body[0].lineno - 1, n.lineno)])
            if "noqa: BLE001" in header:
                f = n
                while f in parent and not isinstance(f, ast.FunctionDef | ast.AsyncFunctionDef):
                    f = parent[f]
                out.append((getattr(f, "name", "<module>"), n.lineno))
    return out


def _handler_sites() -> dict[tuple[str, str], int]:
    sites: dict[tuple[str, str], int] = {}
    base = ROOT / "src" / "hadavin_sdk"
    for path in sorted(base.rglob("*.py")):
        for fn, _ in _handler_lines(path.read_text(encoding="utf-8")):
            key = (path.relative_to(base).as_posix(), fn)
            sites[key] = sites.get(key, 0) + 1
    return sites


def _mutant_count() -> int:
    """The mutants by the tree of `tests/stage_mutants.py` (the elements of the list `M`), and no name twice."""
    import stage_mutants

    tree = ast.parse((ROOT / "tests" / "stage_mutants.py").read_text(encoding="utf-8"))
    listed = next(
        n.value
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "M" for t in n.targets)
        and isinstance(n.value, ast.List)
    )
    names = [m.name for m in stage_mutants.M]
    assert len(set(names)) == len(names), "a mutant name is used twice"
    assert len(listed.elts) == len(names), (
        "M holds elements that the tree does not show as written rows"
    )
    return len(listed.elts)


def _computed_counts() -> dict[str, int]:
    import _guard_allowances as allowances
    import test_guard_reasons as reasons
    import test_stage_names as names

    own = len(allowances.NEW_ALLOWED) + len(allowances.SCOPED_ALLOWED)
    return {
        "REASONS": len(allowances.REASONS),
        "CHECKED": len(allowances.REASONS) - len(reasons.UNCHECKED),
        "OWN": own,
        "ALL": own + len(names.GUARD_ALLOWED),
        "MUTANTS": _mutant_count(),
        "HANDLERS": sum(_handler_sites().values()),
    }


_COUNTS = re.compile(
    r"\*\*Counts at this head[^*]*\*\*\s*(\d+) reasons, (\d+) of them checked by code; the allowance table has (\d+) rows of "
    r"its own plus the older ones \((\d+) rows in all\); (\d+) mutants in `tests/stage_mutants.py`; (\d+) handlers marked"
)


def _claimed_counts(text: str) -> dict[str, int]:
    assert text.count("Counts at this head") == 1, (
        "the CHANGELOG has more than one sentence of counts at this head"
    )
    claim = _COUNTS.search(text)
    assert claim, "the CHANGELOG has no sentence of counts in the written form"
    keys = ("REASONS", "CHECKED", "OWN", "ALL", "MUTANTS", "HANDLERS")
    return dict(zip(keys, map(int, claim.groups()), strict=True))


def test_the_counts_at_this_head_are_the_counts_of_this_head():
    got = _computed_counts()
    said = _claimed_counts(TEXT)
    assert said == got, f"the CHANGELOG counts {said} are not the counts of this head {got}"


def test_a_wrong_sentence_of_counts_is_found():
    got = _computed_counts()
    wrong = TEXT.replace(f"{got['MUTANTS']} mutants in", f"{got['MUTANTS'] + 1} mutants in", 1)
    assert wrong != TEXT, "the sentence has no mutant count to change"
    assert _claimed_counts(wrong) != got, (
        "a wrong count in the sentence is not found by the claims test"
    )


def test_the_numbers_of_older_entries_are_labelled_with_their_batch():
    """A total (rows of the allowance table, reasons checked, mutants, handlers) in an entry other than the newest is history:
    `at batch N` stands within 300 characters before the number, so it cannot be read as the count of this head."""
    newest = TEXT.index("Q8a-1 batch 19, what changes for you")
    older = TEXT[:newest]
    stale = []
    totals = r"\b(?:\d+ rows (?:in all|of its own|\(each)|\d+ of (?:the )?\d+ reasons|\d+ mutants in|\d+ `except` handlers marked)"
    for m in re.finditer(totals, older):
        near = older[max(0, m.start() - 300) : m.end() + 150].lower()
        if "at batch" not in near and "counts at batch" not in near:
            stale.append(older[max(0, m.start() - 40) : m.end() + 20])
    assert stale == [], f"totals of older entries with no batch label: {stale}"


def test_the_handler_list_of_the_changelog_is_the_handlers_of_the_code():
    """The CHANGELOG lists every `noqa: BLE001` handler as `file` `function` xN; the list is the handlers that `ast` finds."""
    listed: dict[tuple[str, str], int] = {}
    for f, fn, n in re.findall(r"`([A-Za-z0-9_/]+\.py)` `([A-Za-z0-9_<>]+)` x(\d+)", TEXT):
        listed[(f, fn)] = listed.get((f, fn), 0) + int(n)
    assert listed == _handler_sites(), (
        "the handler list of the CHANGELOG differs from the handlers of src: "
        f"missing {sorted(set(_handler_sites()) - set(listed))}, extra {sorted(set(listed) - set(_handler_sites()))}"
    )


# The `noqa: BLE001` handlers whose body uses the caught error for more than its class name (batch 19, found with `ast`). The
# CHANGELOG says what each one does with it; a handler added later that uses its error is a new row here, with a reason.
_USES_THE_ERROR = {
    ("audit/chain.py", "build"): "asks is_connectivity_error, then says the class name only",
    ("cli.py", "main"): "class name; HADAVIN_DEBUG=1 adds the frames (_print_frames), never a text",
    (
        "cli.py",
        "kill_switch",
    ): "passes it to _kill_switch_store_down: a fixed sentence and the class name",
    ("guard/http.py", "lookup"): "kept in a dict for the caller thread (HANDOFF)",
    ("k1b/loop.py", "work"): "kept in a dict for the caller thread (HANDOFF)",
    ("runtime/agent_loop.py", "_run_tool"): "error_reason(exc): the open owner question",
    ("sources/kubernetes.py", "_call"): "keeps only too_large of it",
    ("tools.py", "work"): "kept in a dict for the caller thread (HANDOFF)",
    ("tools.py", "invoke"): "error_reason(exc, ...): the open owner question",
}


def _handlers_that_use_the_error() -> dict[tuple[str, str], int]:
    found: dict[tuple[str, str], int] = {}
    base = ROOT / "src" / "hadavin_sdk"
    for path in sorted(base.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        lines = source.splitlines()
        parent = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
        for h in ast.walk(tree):
            if not (isinstance(h, ast.ExceptHandler) and h.name):
                continue
            header = "\n".join(lines[h.lineno - 1 : max(h.body[0].lineno - 1, h.lineno)])
            if "noqa: BLE001" not in header:
                continue
            body = ast.Module(body=h.body, type_ignores=[])
            owner = {c: n for n in ast.walk(body) for c in ast.iter_child_nodes(n)}
            for n in ast.walk(body):
                if not (isinstance(n, ast.Name) and n.id == h.name and isinstance(n.ctx, ast.Load)):
                    continue
                p = owner.get(n)
                only_class = (
                    isinstance(p, ast.Call)
                    and isinstance(p.func, ast.Name)
                    and p.func.id == "type"
                    and isinstance(owner.get(p), ast.Attribute)
                    and owner[p].attr == "__name__"
                ) or (
                    isinstance(p, ast.Attribute)
                    and p.attr == "__class__"
                    and isinstance(owner.get(p), ast.Attribute)
                    and owner[p].attr == "__name__"
                )
                if not only_class:
                    f = h
                    while f in parent and not isinstance(f, ast.FunctionDef | ast.AsyncFunctionDef):
                        f = parent[f]
                    key = (path.relative_to(base).as_posix(), getattr(f, "name", "<module>"))
                    found[key] = found.get(key, 0) + 1
                    break
    return found


def test_the_handlers_that_use_their_error_are_the_pinned_ones():
    """Batch 17 said two handlers show error text and the others print none; the claim needs the list of handlers that touch
    the error at all, found by code. A new one fails here until it is listed with what it does."""
    assert set(_handlers_that_use_the_error()) == set(_USES_THE_ERROR), (
        f"new: {sorted(set(_handlers_that_use_the_error()) - set(_USES_THE_ERROR))}, "
        f"gone: {sorted(set(_USES_THE_ERROR) - set(_handlers_that_use_the_error()))}"
    )
