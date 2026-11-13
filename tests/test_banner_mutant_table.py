"""The table of banner and guard mutants (`tests/banner_mutants.py`) is checked here. The runner replaces EVERY occurrence
of a row's search text, so a row whose text occurs twice changes two places at once and can be killed for a reason that is
not its own; a text that is not found is an error at run time. `non_unique_rows` finds both, and a planted duplicate proves
that it does."""

from __future__ import annotations

import re
from pathlib import Path

from tests import banner_mutants as bm


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: assert [('B25 a sour... times'), ...] == [] (new rows whose search text is not in the old files)
def test_every_row_of_the_table_has_its_own_label_and_a_search_text_found_exactly_once() -> None:
    assert bm.non_unique_rows() == []


def test_the_table_has_no_loose_expectation_left() -> None:
    loose = [m.name for m in bm.M if m.expect in ("assert", "ZZZZ") or len(m.expect) < 4]
    assert loose == []


def test_a_planted_duplicate_or_missing_search_text_or_repeated_label_is_reported(
    tmp_path: Path,
) -> None:
    (tmp_path / "x.py").write_text("a = 1\nb = 1\nc = 2\n", encoding="utf-8")
    rows = [
        bm.mutant("Z1 once", "x.py", "c = 2", "c = 3", "t.py", "test_k", "wrong value"),
        bm.mutant("Z2 twice", "x.py", "= 1", "= 5", "t.py", "test_k", "wrong value"),
        bm.mutant("Z3 never", "x.py", "d = 9", "d = 8", "t.py", "test_k", "wrong value"),
        bm.mutant("Z1 again", "x.py", "c = 2", "c = 4", "t.py", "test_k", "wrong value"),
    ]
    assert bm.non_unique_rows(root=tmp_path, rows=rows) == [
        ("Z2 twice", "search text found 2 times"),
        ("Z3 never", "search text found 0 times"),
        ("Z1", "label used twice"),
    ]


GENERIC_EXPECTATIONS = ("AssertionError", "did not match", "boom", "assert", "Exception", "Error")


def weak_expectations(rows=None) -> list[tuple[str, str]]:
    """Rows whose `expect` would also fit an unrelated failure: a bare exception word, pytest's own "did not match"
    line, a bare tuple repr, or a short bare comparison of two values. Every row names a fragment of its own message
    instead (the message of the assert, or the name of the rule it expects)."""
    weak: list[tuple[str, str]] = []
    for m in bm.M if rows is None else rows:
        e = m.expect.strip()
        generic = (
            e in GENERIC_EXPECTATIONS
            or "did not match" in e
            or (e.startswith("AssertionError: ") and len(e) < 24)
            or e.startswith(
                ("AssertionError: (", "assert")
            )  # a printed tuple or comparison, not a message
            or "] ==" in e
            or "== [" in e
            or "..." in e  # pytest shortened the line: what hides behind the dots is not checked
        )
        if generic:
            weak.append((m.name, e))
    return weak


def test_no_row_has_a_generic_or_shortened_expectation() -> None:
    assert weak_expectations() == []


def test_no_row_changes_nothing() -> None:
    assert [m.name for m in bm.M if m.old == m.new] == []


def test_a_planted_generic_expectation_or_a_row_that_changes_nothing_is_reported() -> None:
    good = bm.mutant("Z1 ok", "x.py", "a", "b", "t.py", "test_k", "wrong value written")
    rows = [
        good,
        bm.mutant("Z2 bare", "x.py", "a", "b", "t.py", "test_k", "AssertionError"),
        bm.mutant("Z3 nomatch", "x.py", "a", "b", "t.py", "test_k", "Regex pattern did not match"),
        bm.mutant("Z4 boom", "x.py", "a", "b", "t.py", "test_k", "boom"),
        bm.mutant("Z5 cut", "x.py", "a", "b", "t.py", "test_k", "assert 0 == 2"),
        bm.mutant("Z6 tuple", "x.py", "a", "b", "t.py", "test_k", "AssertionError: ('x',)"),
        bm.mutant(
            "Z8 dots",
            "x.py",
            "a",
            "b",
            "t.py",
            "test_k",
            "wrong value in ['src/pkg/a.p...-only-folder']",
        ),
    ]
    assert [name for name, _ in weak_expectations(rows)] == [
        "Z2 bare",
        "Z3 nomatch",
        "Z4 boom",
        "Z5 cut",
        "Z6 tuple",
        "Z8 dots",
    ]
    same = bm.mutant("Z7 same", "x.py", "a", "a", "t.py", "test_k", "wrong value written")
    assert [m.name for m in [good, same] if m.old == m.new] == ["Z7 same"]


EXCEPTION_ONLY = re.compile(r"[A-Za-z_.]*(Error|Exception|Exit|Warning)")


def shape_problems(rows=None, same=None) -> list[tuple[str, str]]:
    """Rows whose `expect` is a shape that cannot tell its own killer assert from another failure: a bare exception type,
    pytest's own `DID NOT RAISE` line (it names no input), a fragment that starts with a quote or an operator (it is the
    middle of a comparison, so it also fits any other line holding that value), and two rows that share one killer and one
    expectation unless `same` (label group -> reason) lists the group with a reason."""
    same = bm.SAME_ASSERT if same is None else same
    rows = bm.M if rows is None else rows
    problems: list[tuple[str, str]] = []
    groups: dict[tuple[str, str], list[str]] = {}
    for m in rows:
        label = m.name.split(" ", 1)[0]
        e = m.expect.strip()
        if EXCEPTION_ONLY.fullmatch(e):
            problems.append((label, "expect is a bare exception type"))
        elif e.startswith("DID NOT RAISE"):
            problems.append((label, "expect is pytest's DID NOT RAISE line"))
        elif e[:1] in "'\"" or e.startswith(("==", "!=", "<", ">", "]", ")", "}")):
            problems.append((label, "expect starts mid-comparison"))
        groups.setdefault((m.only_test, m.expect), []).append(label)
    listed = {tuple(k.split()) for k, reason in same.items() if reason.strip()}
    for labels in groups.values():
        if len(labels) > 1 and tuple(labels) not in listed:
            problems.append(
                (
                    " ".join(labels),
                    "rows share one killer and one expect without a same-assert reason",
                )
            )
    return problems


def test_no_row_has_a_bare_type_a_did_not_raise_a_mid_comparison_fragment_or_an_unexplained_shared_assert() -> (
    None
):
    assert shape_problems() == []


def test_every_same_assert_entry_names_a_group_that_exists_and_has_a_reason() -> None:
    labels = {m.name.split(" ", 1)[0] for m in bm.M}
    for group, reason in bm.SAME_ASSERT.items():
        assert reason.strip(), f"the same-assert group {group!r} has no reason"
        missing = [x for x in group.split() if x not in labels]
        assert not missing, (
            f"the same-assert group {group!r} names rows that do not exist: {missing}"
        )


def test_planted_shapes_are_each_reported() -> None:
    def row(label: str, killer: str, expect: str):
        return bm.mutant(f"{label} planted", "x.py", "a", "b", "t.py", killer, expect)

    rows = [
        row("Z1", "t1", "TypeError"),
        row("Z2", "t2", "DID NOT RAISE"),
        row("Z3", "t3", "DID NOT RAISE <class 'ValueError'>"),
        row("Z4", "t4", "'internal-host' not in"),
        row("Z5", "t5", "== [1, 2]"),
        row("Z6", "t6", "own message of the killer"),
        row("Z7", "t7", "shared message"),
        row("Z8", "t7", "shared message"),
        row("Z9", "t9", "shared again"),
        row("Z10", "t9", "shared again"),
    ]
    got = shape_problems(rows=rows, same={"Z9 Z10": "both break the single assert of t9"})
    assert got == [
        ("Z1", "expect is a bare exception type"),
        ("Z2", "expect is pytest's DID NOT RAISE line"),
        ("Z3", "expect is pytest's DID NOT RAISE line"),
        ("Z4", "expect starts mid-comparison"),
        ("Z5", "expect starts mid-comparison"),
        ("Z7 Z8", "rows share one killer and one expect without a same-assert reason"),
    ]
    assert shape_problems(rows=rows[8:], same={"Z9 Z10": " "}) == [
        ("Z9 Z10", "rows share one killer and one expect without a same-assert reason")
    ], "a same-assert entry with a blank reason was accepted"


INTERPRETER_TEXT = re.compile(
    r"(AttributeError|TypeError|KeyError|NameError|IndexError)\b|has no attribute|object of type|is not subscriptable|"
    r"unexpected keyword|validation errors? for|object is not"
)


def interpreter_text_problems(rows=None, pinned=None) -> list[tuple[str, str]]:
    """Rows whose `expect` is the interpreter's or a library's own error text, unless the row is on the pinned crash list:
    only a row that crashes on purpose may be expected to show that text; any other row must show a message of its test."""
    pinned = bm.CRASH_ROWS if pinned is None else pinned
    problems = []
    for m in bm.M if rows is None else rows:
        label = m.name.split(" ", 1)[0]
        if INTERPRETER_TEXT.search(m.expect) and label not in pinned:
            problems.append(
                (label, "expect is an interpreter message and the row is not a pinned crash row")
            )
    return problems


def test_pin_the_crash_rows_are_exactly_the_pinned_set_and_only_they_expect_an_interpreter_message() -> (
    None
):
    declared = {m.name.split(" ", 1)[0] for m in bm.M if m.allow_crash}
    assert declared == set(bm.CRASH_ROWS), (
        f"crash rows not pinned: {sorted(declared - set(bm.CRASH_ROWS))}; pinned but not crash rows: "
        f"{sorted(set(bm.CRASH_ROWS) - declared)}"
    )
    assert interpreter_text_problems() == []


def test_pin_a_planted_interpreter_message_outside_the_pinned_set_is_reported() -> None:
    rows = [
        bm.mutant(
            "Z1 on",
            "x.py",
            "a",
            "b",
            "t.py",
            "k",
            "AttributeError: 'list' has no x",
            crash="AttributeError",
        ),
        bm.mutant("Z2 off", "x.py", "a", "b", "t.py", "k", "'list' object has no attribute 'get'"),
        bm.mutant("Z3 fine", "x.py", "a", "b", "t.py", "k", "the names were not shown once"),
    ]
    assert interpreter_text_problems(rows=rows, pinned={"Z1"}) == [
        ("Z2", "expect is an interpreter message and the row is not a pinned crash row")
    ]


# PIN: this test also passes on dd827d79 (the fail-before run of batch 10 shows it); it keeps a behaviour from breaking and is not proof of a fix


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_rows_killed_by_the_same_first_failing_line_of_one_killer_are_reported() -> None:
    from collections import Counter

    kill = Counter(m.only_test for m in bm.M).most_common(1)[0][0]
    names = [m.name for m in bm.M if m.only_test == kill][:2]
    assert len(names) == 2
    same = {names[0]: "assert 1 == 2", names[1]: "assert 1 == 2"}
    assert bm.shared_first_lines(same) == [[n.split(" ", 1)[0] for n in names]]
    assert bm.shared_first_lines({names[0]: "assert 1 == 2", names[1]: "assert 3 == 4"}) == []
    assert bm.shared_first_lines({}) == []


# PIN: this test also passes on dd827d79 (the fail-before run of batch 10 shows it); it keeps a behaviour from breaking and is not proof of a fix


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_every_killer_named_in_the_table_is_a_test_that_exists_in_its_file() -> None:
    """A renamed or removed killer left its row naming a test that is not there (R9A4 did, found by running it); the run
    then reports an error for the row only when someone runs that row. Checked here for every row, with no run."""
    root = Path(bm.ROOT)
    missing = []
    for m in bm.M:
        text = (root / m.test_file).read_text(encoding="utf-8")
        if f"def {m.only_test}(" not in text:
            missing.append((m.name.split(" ", 1)[0], m.only_test))
    assert missing == []


def _rows_in_the_text_of_the_table() -> list[str]:
    """The row calls of the list `M`, read from the SOURCE TEXT of the table (not from the objects it builds): every call of
    one of the row helpers at the top level of the list. A row that is built any other way would not be counted, and the
    count then differs from `len(M)`: the next test compares the two."""
    import ast

    tree = ast.parse(Path(bm.__file__).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "M" for t in node.targets):
            assert isinstance(node.value, ast.List)
            return [
                c.args[0].value
                for c in node.value.elts
                if isinstance(c, ast.Call) and isinstance(c.args[0], ast.Constant)
            ]
    raise AssertionError("the list M was not found in the table file")


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_row_count_constant_is_the_number_of_rows_in_the_text_of_the_table() -> None:
    labels = [name.split(" ", 1)[0] for name in _rows_in_the_text_of_the_table()]
    assert len(labels) == len(set(labels)), "a label is used twice"
    assert bm.ROW_COUNT == len(labels) == len(bm.M), (
        f"ROW_COUNT is {bm.ROW_COUNT}, the text of the table holds {len(labels)} rows, M holds {len(bm.M)}"
    )


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: the CHANGELOG does not say that the table has 332 rows
def test_the_changelog_states_the_row_count_of_the_table() -> None:
    text = (Path(bm.ROOT) / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"the table has {bm.ROW_COUNT} rows" in text, (
        f"the CHANGELOG does not say that the table has {bm.ROW_COUNT} rows"
    )


def _module_functions(tree) -> dict:
    """The functions of the module level of a parsed test file, by name (a killer and its helpers are found only here)."""
    import ast

    return {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}


def _shadowed_names(tree, names) -> list[str]:
    """Of `names`, those that are defined more than once at the module level, or again as a nested function anywhere in
    the file: the name then does not say which function runs, and the check would read the wrong one."""
    import ast

    top = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    nested = [
        sub.name
        for outer in ast.walk(tree)
        if isinstance(outer, (ast.FunctionDef, ast.ClassDef))
        for sub in ast.iter_child_nodes(outer)
        if isinstance(sub, ast.FunctionDef)
    ]
    return sorted(
        name for name in set(names) if top.count(name) > 1 or name in set(nested) - set(top[:0])
    )


def _text_pieces(tree, name: str) -> list[tuple[str, object]]:
    """The strings a killer can print: ("plain", text) for a string constant and ("fstring", parts) for an f-string, where
    `parts` lists its literal texts and None for each formatted value. They are read from the function `name` of a parsed
    test file and from the module-level functions of that file it calls by name DIRECTLY (its helpers; the helpers of the
    helpers are not read) and from the module-level tables those read by name. Nothing else counts: not the rest of the file."""
    import ast

    funcs = _module_functions(tree)
    node = funcs.get(name)
    if node is None:
        return []
    scopes = [node]
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in funcs:
            scopes.append(funcs[sub.func.id])
    # module-level data the scopes read by name (a table of cases the killer loops over)
    tables = {
        t.id: stmt
        for stmt in tree.body
        if isinstance(stmt, ast.Assign)
        for t in stmt.targets
        if isinstance(t, ast.Name)
    }
    read = {
        sub.id
        for scope in scopes
        for sub in ast.walk(scope)
        if isinstance(sub, ast.Name) and sub.id in tables
    }
    scopes += [tables[name] for name in sorted(read)]
    pieces: list[tuple[str, object]] = []
    for scope in scopes:
        in_fstring = {
            id(part)
            for sub in ast.walk(scope)
            if isinstance(sub, ast.JoinedStr)
            for part in sub.values
            if isinstance(part, ast.Constant)
        }
        for sub in ast.walk(scope):
            if isinstance(sub, ast.JoinedStr):
                pieces.append(
                    (
                        "fstring",
                        [
                            part.value if isinstance(part, ast.Constant) else None
                            for part in sub.values
                        ],
                    )
                )
            elif (
                isinstance(sub, ast.Constant)
                and isinstance(sub.value, str)
                and id(sub) not in in_fstring
            ):
                pieces.append(("plain", sub.value))
    return pieces


MIN_FRAGMENT = 8  # the least text of the killer's own that an expectation must hold


def _is_part_of_fstring_output(parts: list, fragment: str) -> bool:
    """True when `fragment` can be a stretch of the text that the f-string prints: the literal parts it covers are matched
    exactly and in order, a formatted value may print anything, and the literal text matched is at least MIN_FRAGMENT
    characters. A literal that merely occurs inside the fragment, with other text around it, does not count."""
    from functools import cache

    @cache
    def rest(i: int, pos: int, matched: int) -> bool:
        # parts[i:] must continue the fragment from `pos`; the fragment may end inside the part
        if pos >= len(fragment):
            return matched >= MIN_FRAGMENT
        if i >= len(parts):
            return False
        part = parts[i]
        if part is None:  # a value: it prints anything, including nothing
            return any(rest(i + 1, k, matched) for k in range(pos, len(fragment) + 1))
        tail = fragment[pos:]
        if tail.startswith(part):
            return rest(i + 1, pos + len(part), matched + len(part))
        if part.startswith(tail):  # the fragment ends inside this literal
            return matched + len(tail) >= MIN_FRAGMENT
        return False

    for i, part in enumerate(parts):
        if part is None:  # the fragment starts inside a value
            if any(rest(i + 1, k, 0) for k in range(len(fragment) + 1)):
                return True
        else:  # it starts inside a literal: a tail of the literal is the start of the fragment
            for off in range(len(part)):
                piece = part[off:]
                if fragment.startswith(piece):
                    if rest(i + 1, len(piece), len(piece)):
                        return True
                elif piece.startswith(fragment) and len(fragment) >= MIN_FRAGMENT:
                    return True
    return False


# Rows whose `expect` holds text that is made at run time and is in no string of the killer or of its direct helpers: a value
# of a loop or of a data table built by a helper of a helper, the text of the page script's probe, or the text of the checked
# code itself. The static check cannot see these; the mutation run can (the expectation must appear in the first failing line
# of the killer, or the row is not good). Each entry says where its text comes from; `test_every_computed_expectation_has_
# a_reason_and_is_not_seen_by_the_static_check` keeps the list honest (a row that the static check accepts must leave it).
COMPUTED_EXPECT = {
    "B1": "the case is the loop variable `mode` of the killer (f'stage {mode!r}' printed by the shared refused helper)",
    "B39": "the odd url is a value of the killer's own data list, printed in the failure",
    "B40": "the odd url is a value of the killer's own data list, printed in the failure",
    "B41": "the odd url is a value of the killer's own data list, printed in the failure",
    "G56": "the encoding name is the loop variable of the killer (f'binary {encoding}')",
    "G57": "the encoding name is the loop variable of the killer (f'binary {encoding}')",
    "G81": "the file ending is the loop variable of the killer (f'named {ending}')",
    "G82": "the file ending is the loop variable of the killer (f'named {ending}')",
    "B2": "the killer loops over inputs and the message holds the repr of one input (str 'crm')",
    "B2b": "the killer loops over inputs and the message holds the repr of one input (set {'crm'})",
    "J3": "the word is from the page script's own probe output (the write that was made), not from the killer",
    "B21": "the message holds the repr of the config under test, made by the checked code",
    "B22": "the message holds the repr of the config under test, made by the checked code",
    "B24": "the message holds the repr of the settings under test, made by the checked code",
    "B38": "an odd url from a data list in a helper of a helper (a back slash written with escapes)",
    "B59": "an odd url from a data list in a helper of a helper",
    "B60": "the refusal text of the checked code, which the message repeats",
    "G30": "a full-width spelling made by a helper of a helper from a code point table",
    "G38": "a path of the made-up repository the killer builds, printed in the failure",
    "G51": "the archive ending is the loop variable of the killer",
    "G52": "the archive ending is the loop variable of the killer",
    "G53": "the archive ending is the loop variable of the killer",
    "G54": "the archive ending is the loop variable of the killer",
    "G55": "the archive ending is the loop variable of the killer",
}


def _printable(pieces: list, fragment: str) -> bool:
    """Whether the killer can print `fragment`: inside one plain string (at least MIN_FRAGMENT characters) or as a stretch
    of what one of its f-strings prints."""
    for kind, payload in pieces:
        if kind == "plain":
            if len(fragment) >= MIN_FRAGMENT and fragment in payload.strip():
                return True
        elif _is_part_of_fstring_output(payload, fragment):
            return True
    return False


def expectation_nowhere_in_killer(rows=None, root=None, strict=False) -> list[tuple[str, str]]:
    """Rows whose `expect` cannot come from the killer's own assertion message. `expect` is a fragment of that message AS
    PRINTED. It is accepted when it lies inside one string of the killer or of its direct helpers (at least MIN_FRAGMENT
    characters), or, where the message formats a value (an f-string), when it is a stretch of what that f-string prints (its
    literal parts exact and in order, any value in between, at least MIN_FRAGMENT characters of the killer's own text). Not
    accepted: a fragment found only elsewhere in the test file, an f-string of another function, a literal that only occurs
    somewhere inside the fragment, a start-of-text match of a few characters, or a killer whose name is defined twice (the
    check would not know which one runs). Crash rows (the pinned set) expect the text of the interpreter or of the changed
    code and are left out."""
    import ast

    base = Path(bm.ROOT if root is None else root)
    trees: dict[str, object] = {}
    nowhere = []
    for m in bm.M if rows is None else rows:
        label = m.name.split(" ", 1)[0]
        if label in bm.CRASH_ROWS or (label in COMPUTED_EXPECT and not strict):
            continue
        if m.test_file not in trees:
            trees[m.test_file] = ast.parse((base / m.test_file).read_text(encoding="utf-8"))
        tree = trees[m.test_file]
        helpers = {
            sub.func.id
            for fn in [_module_functions(tree).get(m.only_test)]
            if fn is not None
            for sub in ast.walk(fn)
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
        }
        if shadowed := _shadowed_names(
            tree, {m.only_test} | (helpers & set(_module_functions(tree)))
        ):
            nowhere.append((label, f"the function name {shadowed[0]} is defined more than once"))
            continue
        pieces = _text_pieces(tree, m.only_test)
        if _printable(pieces, m.expect):
            continue
        # the shared `refused` helper (tests/refusal.py) prints "<what> was not refused" or "<what>: refused, but with
        # another text": `what` is the killer's own text (a string, or the start of an f-string with a value after it)
        what = re.split(r" was not refused|: refused, but with another text", m.expect)[0]
        if what != m.expect and _printable(pieces, what):
            continue
        nowhere.append((label, m.expect))
    return nowhere


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_every_expectation_of_a_row_is_made_of_text_its_killer_can_print() -> None:
    assert expectation_nowhere_in_killer() == []


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_planted_expectation_that_no_string_of_the_killer_can_print_is_reported(
    tmp_path: Path,
) -> None:
    (tmp_path / "t.py").write_text(
        "def test_k():\n    assert False, f'value {1} was not refused'\n"
        "def test_plain():\n    assert False, 'the plain message of the killer'\n",
        encoding="utf-8",
    )
    good = bm.mutant("Z1 a", "x.py", "a", "b", "t.py", "test_k", "was not refused")
    plain_good = bm.mutant("Z2 b", "x.py", "a", "b", "t.py", "test_plain", "plain message of the")
    bad = bm.mutant("Z3 c", "x.py", "a", "b", "t.py", "test_plain", "a message nobody wrote")
    assert expectation_nowhere_in_killer(rows=[good, plain_good, bad], root=tmp_path) == [
        ("Z3", "a message nobody wrote")
    ]


# fail-before (real run on dd827d79 and on 06ed4b4c, batch 12): it PASSES on both, because the code it checks is the checker in this same new test file. A pin, not proof of a fix.
def test_pin_every_computed_expectation_has_a_reason_and_is_not_seen_by_the_static_check() -> None:
    labels = {m.name.split(" ", 1)[0] for m in bm.M}
    assert set(COMPUTED_EXPECT) <= labels, sorted(set(COMPUTED_EXPECT) - labels)
    assert all(len(why.split()) >= 5 for why in COMPUTED_EXPECT.values()), (
        "an entry without a reason"
    )
    seen_statically = {
        m.name.split(" ", 1)[0]
        for m in bm.M
        if m.name.split(" ", 1)[0] in COMPUTED_EXPECT
        and not expectation_nowhere_in_killer(rows=[m], strict=True)
    }
    assert not seen_statically, f"these rows no longer need an entry: {sorted(seen_statically)}"


# fail-before (batch 13): cannot fail on old code. It reads `bm.EQUIVALENT`, a table that exists only in this new file, so a pin (same new file).
def test_pin_every_equivalent_mutation_has_a_reason_and_its_line_is_still_in_the_file() -> None:
    assert bm.EQUIVALENT, "the list of equivalent mutations is empty"
    for (path, text), why in bm.EQUIVALENT.items():
        source = (Path(bm.ROOT) / path).read_text(encoding="utf-8")
        assert source.count(text) == 1, (
            f"{path}: the line of an equivalent mutation is not there once: {text!r}"
        )
        assert len(why.split()) >= 10, f"{path}: {text!r} has no reason"


# fail-before (real run on dd827d79 and on 06ed4b4c, batch 12): it PASSES on both, because the code it checks is the checker in this same new test file. A pin, not proof of a fix.
def test_pin_a_planted_expectation_found_only_elsewhere_in_the_test_file_is_reported(
    tmp_path: Path,
) -> None:
    (tmp_path / "t.py").write_text(
        "def test_k():\n    assert False, 'the message of the killer'\n"
        "def test_other():\n    assert False, 'a sentence of another test'\n",
        encoding="utf-8",
    )
    elsewhere = bm.mutant("Z4 d", "x.py", "a", "b", "t.py", "test_k", "a sentence of another test")
    assert expectation_nowhere_in_killer(rows=[elsewhere], root=tmp_path) == [
        ("Z4", "a sentence of another test")
    ]


# fail-before (batch 13): cannot fail on old code, because the checker it tests is in this same new file. A pin.
def test_pin_three_loose_expectations_and_a_short_one_are_each_reported(tmp_path: Path) -> None:
    (tmp_path / "t.py").write_text(
        "def test_k():\n    assert False, 'the message of the killer'\n", encoding="utf-8"
    )
    (tmp_path / "twin.py").write_text(
        "def test_dup():\n    assert False, 'first body of the twin'\n"
        "def test_dup():\n    assert False, 'second body of the twin'\n",
        encoding="utf-8",
    )
    (tmp_path / "nest.py").write_text(
        "def helper():\n    def test_n():\n        pass\n"
        "def test_n():\n    assert False, 'message of nest'\n",
        encoding="utf-8",
    )

    def row(label: str, file: str, killer: str, expect: str):
        return bm.mutant(f"{label} planted", "x.py", "a", "b", file, killer, expect)

    rows = [
        # an invented sentence that only holds a 5 character literal of the killer ("the m")
        row("Z5", "t.py", "test_k", "the m is an invented sentence"),
        # an invented sentence that starts like the killer text for 4 characters ("the ")
        row("Z6", "t.py", "test_k", "the minister wrote this"),
        # a message of 5 characters, shorter than the 8 character minimum
        row("Z7", "t.py", "test_k", "the m"),
        row("Z8", "twin.py", "test_dup", "first body of the twin"),
        row("Z9", "nest.py", "test_n", "message of nest"),
        row("Z10", "t.py", "test_k", "message of the killer"),  # a real stretch: not reported
    ]
    reported = {label for label, _ in expectation_nowhere_in_killer(rows=rows, root=tmp_path)}
    assert reported == {"Z5", "Z6", "Z7", "Z8", "Z9"}, reported


def test_a_focused_run_names_a_word_that_matches_nothing_and_a_row_outside_the_list() -> None:
    names = ["R1A one", "R2B two"]
    assert bm.focus_problems(["R1A"], ["R1A one"], names) == []
    assert bm.focus_problems(["R9Z"], [], names) == ["focus word matches no row: R9Z"], (
        "a typo ran nothing quietly"
    )
    assert bm.focus_problems(["R1A"], ["R1A one", "R2B two"], names) == [
        "row run but not in the focus list: R2B two"
    ], "a row outside the focus list was run"
    assert bm.focus_problems([], ["R2B two"], names) == [], "a full run has no focus list"
