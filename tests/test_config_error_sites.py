"""The table of every place where the SDK builds a ``ConfigError`` (P5b2): the CI check and the tests of its generator.

The generator is ``tools/gen_config_error_sites.py``. Every test reaches it through ``need(name)``, which fails with an
assertion (not an import error) when the generator or a name is missing, so the whole file fails on a tree without it.
Synthetic source folders are written into ``tmp_path``; no repository code is imported or run.
"""

from __future__ import annotations

import ast
import csv
import importlib
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.test_no_hardcoded_values import PATTERNS

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "hadavin_sdk"
TABLE = ROOT / "tests" / "data" / "config_error_sites.csv"
GENERATOR = ROOT / "tools" / "gen_config_error_sites.py"
HOLD = '"""x."""'
ERRORS = f"class ConfigError(ValueError):\n    {HOLD}\n"
HEAD = "from pkg.errors import ConfigError\n"
STDLIB_ALLOWED = {
    "__future__",
    "argparse",
    "ast",
    "csv",
    "dataclasses",
    "hashlib",
    "pathlib",
    "re",
    "sys",
    "typing",
}

try:
    GEN: Any = importlib.import_module("tools.gen_config_error_sites")
except ImportError:
    GEN = None


def need(name: str) -> Any:
    obj = getattr(GEN, name, None)
    assert obj is not None, f"tools.gen_config_error_sites.{name} is missing"
    return obj


def make(tmp: Path, files: dict[str, str], *, errors: bool = True) -> Path:
    pkg = tmp / "pkg"
    pkg.mkdir(exist_ok=True)
    allfiles = {"errors.py": ERRORS, **files} if errors else dict(files)
    for name, text in allfiles.items():
        path = pkg / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding="utf-8")
    return pkg


def sites_of(tmp: Path, body: str, **more: str) -> list[Any]:
    return need("scan")(make(tmp, {"m.py": HEAD + body, **more}))


def only(tmp: Path, body: str, **more: str) -> Any:
    found = sites_of(tmp, body, **more)
    assert len(found) == 1, [s.key for s in found]
    return found[0]


def sites_keys(tmp: Path, body: str) -> list[str]:
    return [s.key for s in sites_of(tmp, body)]


def call_node(text: str) -> ast.AST:
    node = ast.parse(text).body[0]
    assert isinstance(node, ast.Expr)
    return node.value


def refuses(tmp: Path, files: dict[str, str], **kw: Any) -> None:
    with pytest.raises(need("SitesError")):
        need("scan")(make(tmp, files, **kw))


# --------------------------------------------------------------------------------------------------------------------
# the CI check on the real source


def real_scan() -> list[Any]:
    return need("scan")(SRC)


def test_committed_table_matches_source() -> None:
    real_sites = real_scan()
    report = need("compare")(real_sites, need("load_csv")(TABLE))
    assert report.ok, (
        report.render() + "\nrun python -m tools.gen_config_error_sites --review and decide"
    )


def test_committed_table_is_in_canonical_form() -> None:
    rows = need("load_csv")(TABLE)
    assert TABLE.read_bytes() == need("render_csv")(rows).encode("ascii")
    assert b"\r" not in TABLE.read_bytes()


# The FOREIGN count is a stop sign, not a target: 21 before order 132, then +4 migrate.py rows that interpolate names read back
# from the database, +2 store/postgres.py tls_mode rows (sslmode can come from the DSN) and +1 k1b/bundle.py row (a folder name
# echoed before it is validated). A new FOREIGN row must be reviewed by a person who raises this number on purpose.
FOREIGN_LIMIT = 28


def test_the_table_has_no_blank_class_and_a_bounded_foreign_count() -> None:
    rows = need("load_csv")(TABLE)
    assert rows
    assert all(r.klass in need("CLASSES") for r in rows)
    assert sum(r.klass == "FOREIGN" for r in rows) <= FOREIGN_LIMIT


def test_reasons_name_symbols_not_line_numbers() -> None:
    """A line number in a reason goes stale on the next edit above it (order 132, R-2)."""
    line_ref = re.compile(r"\.py:\d|\(:\d|\bline \d")
    assert [r.site for r in need("load_csv")(TABLE) if line_ref.search(r.reason)] == []


def reason_problems(rows: list[Any], patterns: dict[str, re.Pattern[str]]) -> list[str]:
    return [
        f"{r.site}: {name}" for r in rows for name, pat in patterns.items() if pat.search(r.reason)
    ]


def test_reasons_hold_no_key_url_or_account_id() -> None:
    assert reason_problems(need("load_csv")(TABLE), PATTERNS) == []


def test_reason_check_has_teeth() -> None:
    row_cls = need("Row")
    fake_key = "AKIA" + "ABCDEFGHIJKLMNOP"
    host = "api." + "example" + ".com"
    flagged = reason_problems([row_cls("a::b::c::1", "OPERATOR", f"uses {fake_key}")], PATTERNS)
    assert flagged
    assert reason_problems([row_cls("a::b::c::1", "OPERATOR", f"calls {host}")], PATTERNS)
    assert (
        reason_problems(
            [row_cls("a::b::c::1", "OPERATOR", "a secret name from settings")], PATTERNS
        )
        == []
    )


def test_generator_imports_standard_library_only() -> None:
    assert GENERATOR.is_file(), "tools/gen_config_error_sites.py is missing"
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported.add((node.module or "").split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"__import__", "exec", "eval", "compile"}, node.func.id
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            assert not (node.value.id == "sys" and node.attr == "path"), (
                "the generator touches sys.path"
            )
    assert imported <= STDLIB_ALLOWED, sorted(imported - STDLIB_ALLOWED)
    assert imported <= set(sys.stdlib_module_names)
    assert imported


def test_planted_unclassified_site_is_refused(tmp_path: Path) -> None:
    scan, compare, load_csv = need("scan"), need("compare"), need("load_csv")
    copy = tmp_path / "hadavin_sdk"
    shutil.copytree(SRC, copy, ignore=shutil.ignore_patterns("__pycache__"))
    before = {s.key for s in scan(copy)}
    plant = (
        "\n\ndef plant():\n    try:\n        pass\n    except Exception as exc:\n"
        '        raise ConfigError(f"plant {exc}")\n'
    )
    with (copy / "audit" / "signer.py").open("a", encoding="utf-8") as handle:
        handle.write(plant)
    after = scan(copy)
    new = [s for s in after if s.key not in before]
    assert len(new) == 1
    assert (new[0].symbol, new[0].auto_reason) == ("plant", "exception-variable")
    report = compare(after, load_csv(TABLE))
    assert report.unclassified == [new[0].key]
    assert report.ok is False


def test_ledger_row_005_a_planted_validation_error_text_is_reported(tmp_path: Path) -> None:
    """Ledger BL-core-c18a-005: ``ConfigError(str(<validation error>))`` must be reported by the table check."""
    body = (
        "def check(model):\n    try:\n        model.validate()\n    except ValueError as err:\n"
        "        raise ConfigError(str(err)) from err\n"
    )
    site = only(tmp_path, body)
    assert (site.auto_class, site.auto_reason) == ("FOREIGN", "exception-variable")
    report = need("compare")([site], [])
    assert report.unclassified == [site.key]
    assert not report.ok


def test_the_real_source_has_the_known_locked_sites() -> None:
    real_sites = real_scan()
    locked = {(s.file, s.symbol) for s in real_sites if s.auto_reason == "exception-variable"}
    assert ("tools.py", "parse_manifest") in locked  # a derived value of the pydantic error
    assert ("tools.py", "load_tool_module") in locked
    assert ("evals.py", "gate") in locked
    assert sum(s.auto_reason == "exception-variable" for s in real_sites) >= 18


# --------------------------------------------------------------------------------------------------------------------
# unit 1 and 2: the automatic class


@pytest.mark.parametrize(
    "arg",
    ['"a"', '"a" "b"', 'f"abc"', ""],
    ids=["string", "implicit-concat", "fstring-no-part", "no-argument"],
)
def test_unit1_literal_shapes(tmp_path: Path, arg: str) -> None:
    site = only(tmp_path, f"def f():\n    raise ConfigError({arg})\n")
    assert (site.auto_class, site.auto_reason) == ("LITERAL", "constant")
    assert site.kind == "ConfigError"


@pytest.mark.parametrize(
    "call",
    [
        'ConfigError("x", exc)',
        'ConfigError("x", detail=v)',
        "ConfigError(*parts)",
        "ConfigError(**kw)",
        'ConfigError("a", "b")',
    ],
)
def test_unit1b_extra_argument_shapes_are_foreign(tmp_path: Path, call: str) -> None:
    site = only(tmp_path, f"def f(exc=None, v=1, parts=(), kw=None):\n    raise {call}\n")
    assert site.auto_class == "FOREIGN"


def test_unit1b_extra_argument_in_a_handler_is_exception_variable(tmp_path: Path) -> None:
    body = 'def f():\n    try:\n        pass\n    except Exception as exc:\n        raise ConfigError("x", exc)\n'
    site = only(tmp_path, body)
    assert (site.auto_class, site.auto_reason) == ("FOREIGN", "exception-variable")


@pytest.mark.parametrize(
    "arg",
    ['f"{x}"', "str(x)", '", ".join(x)', '"%s" % x', '"a" + x', "x"],
    ids=["fstring", "call", "join", "percent", "plus", "name"],
)
def test_unit2_other_shapes_are_unproven(tmp_path: Path, arg: str) -> None:
    site = only(tmp_path, f"def f(x):\n    raise ConfigError({arg})\n")
    assert (site.auto_class, site.auto_reason) == ("FOREIGN", "unproven-origin")


# --------------------------------------------------------------------------------------------------------------------
# unit 3: taint

HANDLER = "def f(x=None, d=None):\n    try:\n        pass\n    except Exception as e:\n"
TAINT_BODIES = {
    "fstring": '        raise ConfigError(f"{e}")\n',
    "str": "        raise ConfigError(str(e))\n",
    "repr": "        raise ConfigError(repr(e))\n",
    "args0": "        raise ConfigError(e.args[0])\n",
    "type-name": "        raise ConfigError(type(e).__name__)\n",
    "class-name": "        raise ConfigError(e.__class__.__name__)\n",
    "percent": '        raise ConfigError("%s" % e)\n',
    "format": '        raise ConfigError("{}".format(e))\n',
    "assign": "        msg = str(e)\n        raise ConfigError(msg)\n",
    "join": '        fields = ", ".join(y for y in e.errors())\n        raise ConfigError(f"({fields})")\n',
    "augassign": '        m = ""\n        m += str(e)\n        raise ConfigError(m)\n',
    "annassign": "        m: str = str(e)\n        raise ConfigError(m)\n",
    "tuple": "        a, b = 1, str(e)\n        raise ConfigError(b)\n",
    "for": "        for y in e.errors():\n            pass\n        raise ConfigError(y)\n",
    "comprehension": "        items = [y for y in e.errors()]\n        raise ConfigError(items)\n",
    "walrus": "        if (w := str(e)):\n            raise ConfigError(w)\n",
    "with": "        with e as h:\n            raise ConfigError(h)\n",
    "subscript": '        d["k"] = e\n        raise ConfigError(d)\n',
    "attribute": "        d.a = e\n        raise ConfigError(d)\n",
    "append": "        parts = []\n        parts.append(e)\n        raise ConfigError(parts)\n",
    "extend": "        parts = []\n        parts.extend([e])\n        raise ConfigError(parts)\n",
    "insert": "        parts = []\n        parts.insert(0, e)\n        raise ConfigError(parts)\n",
    "add": "        parts = set()\n        parts.add(e)\n        raise ConfigError(parts)\n",
    "update": "        parts = set()\n        parts.update([e])\n        raise ConfigError(parts)\n",
    "appendleft": "        parts = []\n        parts.appendleft(e)\n        raise ConfigError(parts)\n",
}


@pytest.mark.parametrize("name", sorted(TAINT_BODIES))
def test_unit3_taint_forms_are_exception_variable(tmp_path: Path, name: str) -> None:
    site = only(tmp_path, HANDLER + TAINT_BODIES[name])
    assert (site.auto_class, site.auto_reason) == ("FOREIGN", "exception-variable"), name


@pytest.mark.parametrize(
    "call",
    [
        "sys.exc_info()",
        "sys.exception()",
        "traceback.format_exc()",
        "traceback.format_exception(e)",
        "traceback.format_exception_only(e)",
    ],
)
def test_unit3_taint_sources_are_tainted_wherever_they_appear(tmp_path: Path, call: str) -> None:
    body = f"import sys\nimport traceback\n\n\ndef f(e=None):\n    raise ConfigError(str({call}))\n"
    site = only(tmp_path, body)
    assert site.auto_reason == "exception-variable"


def test_unit3_raise_from_without_interpolation_stays_literal(tmp_path: Path) -> None:
    body = 'def f():\n    try:\n        pass\n    except Exception as e:\n        raise ConfigError("x") from e\n'
    assert only(tmp_path, body).auto_class == "LITERAL"


def test_unit3_taint_does_not_cross_functions_and_the_hint_names_the_callee(tmp_path: Path) -> None:
    body = (
        "def g(holder):\n    raise ConfigError(str(holder[0]))\n\n\n"
        "def f(fetch):\n    msg = fetch()\n    raise ConfigError(msg)\n"
    )
    found = {s.symbol: s for s in sites_of(tmp_path, body)}
    assert found["g"].auto_reason == "unproven-origin"
    assert found["f"].auto_reason == "unproven-origin"
    assert any("fetch" in hint for hint in found["f"].origin_hints)


def test_unit3_an_inner_function_is_its_own_scope(tmp_path: Path) -> None:
    body = (
        "def f():\n    try:\n        pass\n    except Exception as e:\n        def inner():\n"
        "            raise ConfigError(str(e))\n        inner()\n"
        "        g = lambda: ConfigError(str(e))\n"
    )
    assert {s.auto_reason for s in sites_of(tmp_path, body)} == {"unproven-origin"}


def test_tainted_names_is_public_and_follows_forms() -> None:
    tainted = need("tainted_names")
    func = ast.parse(
        "def f():\n    try:\n        pass\n    except E as e:\n        m = str(e)\n        n = 1\n"
    ).body[0]
    assert tainted(func) == frozenset({"e", "m"})


# --------------------------------------------------------------------------------------------------------------------
# unit 4: classes, aliases, nesting


def test_unit4_subclass_closure_across_modules_and_file_order(tmp_path: Path) -> None:
    files = {
        "z_base.py": f"{HEAD}\n\nclass A(ConfigError):\n    {HOLD}\n",
        "a_sub.py": f"from pkg.z_base import A\n\n\nclass B(A):\n    {HOLD}\n",
        "m.py": 'from pkg.a_sub import B\n\n\ndef f():\n    raise B("x")\n',
    }
    found = need("scan")(make(tmp_path, files))
    assert [(s.file, s.kind) for s in found] == [("m.py", "B")]


def test_unit4_base_written_as_attribute(tmp_path: Path) -> None:
    files = {
        "a.py": f"import pkg.errors as errors\n\n\nclass A(errors.ConfigError):\n    {HOLD}\n\n\ndef f():\n    raise A('x')\n",
    }
    assert [(s.kind) for s in need("scan")(make(tmp_path, files))] == ["A"]


def test_unit4_alias_import_and_attribute_call_are_recorded_canonically(tmp_path: Path) -> None:
    files = {
        "m.py": (
            "from pkg.errors import ConfigError as CE\nimport pkg.errors as errors\n\n\n"
            "def f():\n    raise CE('a')\n\n\ndef g():\n    raise errors.ConfigError('b')\n"
        ),
    }
    found = need("scan")(make(tmp_path, files))
    assert [s.kind for s in found] == ["ConfigError", "ConfigError"]


def test_unit4_call_as_module_attribute_of_a_subclass(tmp_path: Path) -> None:
    files = {
        "base.py": f"{HEAD}\n\nclass A(ConfigError):\n    {HOLD}\n",
        "m.py": "import pkg.base as base\n\n\ndef f():\n    raise base.A('x')\n",
    }
    assert [s.kind for s in need("scan")(make(tmp_path, files))] == ["A"]


def test_unit4_bare_raise_of_the_class_is_a_literal_site(tmp_path: Path) -> None:
    site = only(tmp_path, "def f():\n    raise ConfigError\n")
    assert (site.auto_class, site.auto_reason) == ("LITERAL", "constant")


def test_unit4_nested_package(tmp_path: Path) -> None:
    files = {"sub/deep/x.py": HEAD + "\n\ndef f():\n    raise ConfigError('x')\n"}
    found = need("scan")(make(tmp_path, files))
    assert [s.file for s in found] == ["sub/deep/x.py"]


def test_symbol_chain_uses_defs_and_classes_only(tmp_path: Path) -> None:
    body = (
        "class K:\n    def meth(self, d=ConfigError('dflt')):\n        h = lambda: ConfigError('lam')\n"
        "        return [ConfigError('comp') for _ in range(2)]\n\n\n"
        "async def top():\n    raise ConfigError('async')\n\n\nX = ConfigError('mod')\n"
    )
    symbols = sorted(s.symbol for s in sites_of(tmp_path, body))
    assert symbols == ["<module>", "K", "K.meth", "K.meth", "top"]


# --------------------------------------------------------------------------------------------------------------------
# unit 5 and 6: the hash and the key


@pytest.mark.parametrize(
    "variant",
    [
        'ConfigError(f"a {x}")',
        'ConfigError(f"a {x}",)',
        "ConfigError(f'a {x}')",
        'ConfigError((f"a {x}"))',
        'ConfigError(\n    f"a {x}"\n)',
        'ConfigError(f"a { x }")',
        'ConfigError(f"a {x}")  # a comment',
        '\n\nConfigError(f"a {x}")',
    ],
)
def test_unit5_hash_survives_formatting(variant: str) -> None:
    node_hash = need("node_hash")
    assert node_hash(call_node(variant)) == node_hash(call_node('ConfigError(f"a {x}")'))


@pytest.mark.parametrize(
    "variant",
    [
        'ConfigError(f"b {x}")',
        'ConfigError(f"a {y}")',
        'ConfigError(f"a {x}", 1)',
        'Other(f"a {x}")',
    ],
)
def test_unit5_hash_changes_with_words_and_names(variant: str) -> None:
    node_hash = need("node_hash")
    assert node_hash(call_node(variant)) != node_hash(call_node('ConfigError(f"a {x}")'))


def test_unit5_hash_has_the_stated_length_and_ignores_positions() -> None:
    node_hash = need("node_hash")
    one = node_hash(call_node('ConfigError("x")'))
    two = node_hash(ast.parse("\n\n\n    \nConfigError('x')").body[0].value)
    assert one == two
    assert re.fullmatch(r"[0-9a-f]{16}", one)


def test_unit5_a_moved_function_and_an_indent_keep_the_row(tmp_path: Path) -> None:
    plain = "def f(x):\n    raise ConfigError(f'a {x}')\n"
    moved = (
        "\n\n# comment\nX = 1\n\n\ndef f(x):\n    raise ConfigError(\n        f'a {x}',\n    )\n"
    )
    a = sites_keys(tmp_path / "a", plain) if (tmp_path / "a").mkdir() is None else []
    b = sites_keys(tmp_path / "b", moved) if (tmp_path / "b").mkdir() is None else []
    assert a == b
    assert len(a) == 1


def test_unit5_changed_word_gives_a_new_key(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    a = sites_keys(tmp_path / "a", "def f(x):\n    raise ConfigError(f'a {x}')\n")
    b = sites_keys(tmp_path / "b", "def f(x):\n    raise ConfigError(f'b {x}')\n")
    assert a != b


def test_unit5_a_bare_raise_and_a_return_hash_their_own_node(tmp_path: Path) -> None:
    node_hash = need("node_hash")
    bare = only(tmp_path, "def f():\n    raise ConfigError\n")
    assert bare.snippet_hash == node_hash(call_node("ConfigError"))
    (tmp_path / "r").mkdir()
    ret = only(tmp_path / "r", "def f(x):\n    return ConfigError(f'a {x}')\n")
    assert ret.snippet_hash == node_hash(call_node("ConfigError(f'a {x}')"))


def test_unit6_identical_sites_in_one_function_get_k1_and_k2(tmp_path: Path) -> None:
    # same text AND same guard: nothing but the source order tells them apart, so k numbers them
    body = "def f(a):\n    if a:\n        raise ConfigError('x')\n    if a:\n        raise ConfigError('x')\n"
    found = sites_of(tmp_path, body)
    assert [s.k for s in found] == [1, 2]
    assert found[0].key.endswith("::1") and found[1].key.endswith("::2")
    assert len({s.key for s in found}) == 2


SWAP_A = "def f(x, y, m):\n    if x:\n        raise ConfigError(m)\n    if y:\n        raise ConfigError(m)\n"
SWAP_B = "def f(x, y, m):\n    if y:\n        raise ConfigError(m)\n    if x:\n        raise ConfigError(m)\n"


def test_f1_swapping_two_same_text_blocks_keeps_each_key_with_its_guard(tmp_path: Path) -> None:
    """Design F1: identical constructions were keyed by source order only, so swapping the blocks moved the labels unseen.
    Killing mutant: M32 (the hash is not seeded with the guard)."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    before = sorted(sites_of(tmp_path / "a", SWAP_A), key=lambda s: s.lineno)
    after = sorted(sites_of(tmp_path / "b", SWAP_B), key=lambda s: s.lineno)
    assert [s.lineno for s in before] == [4, 6] and [s.lineno for s in after] == [4, 6]
    assert len({s.key for s in before}) == 2
    # the block guarded by x is first before the swap and second after it; its key must not change
    assert before[0].key == after[1].key
    assert before[1].key == after[0].key
    assert before[0].key.endswith("::1") and before[1].key.endswith("::1")


def test_f1_the_labels_follow_the_guard_when_the_blocks_are_swapped(tmp_path: Path) -> None:
    """The row of the block guarded by ``x`` is still found for that block; with order keys the two classes would trade places."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    before = sorted(sites_of(tmp_path / "a", SWAP_A), key=lambda s: s.lineno)
    after = sorted(sites_of(tmp_path / "b", SWAP_B), key=lambda s: s.lineno)
    row = need("Row")
    table = [
        row(before[0].key, "OPERATOR", "the x block"),
        row(before[1].key, "FOREIGN", "the y block"),
    ]
    report = need("compare")(after, table)
    assert report.ok
    by_key = {r.site: r.klass for r in table}
    assert by_key[after[1].key] == "OPERATOR"  # the x block is second now and keeps its class


def test_f1_a_new_same_text_site_changes_the_key_of_the_old_one_so_the_table_must_be_reviewed(
    tmp_path: Path,
) -> None:
    (tmp_path / "a").mkdir()
    alone = only(tmp_path / "a", "def f(x, m):\n    if x:\n        raise ConfigError(m)\n")
    pair = sites_of(tmp_path, SWAP_A)
    assert alone.key not in {s.key for s in pair}


def test_f1_a_site_without_a_twin_keeps_the_plain_node_hash(tmp_path: Path) -> None:
    site = only(tmp_path, "def f(x, m):\n    if x:\n        raise ConfigError(m)\n")
    assert site.snippet_hash == need("node_hash")(call_node("ConfigError(m)"))


def test_f1_guards_tell_apart_branches_loops_handlers_and_withs(tmp_path: Path) -> None:
    body = (
        "def f(x, y):\n    if x:\n        raise ConfigError('s')\n    else:\n        raise ConfigError('s')\n"
        "    for i in x:\n        raise ConfigError('s')\n    for i in y:\n        raise ConfigError('s')\n"
        "    try:\n        pass\n    except KeyError:\n        raise ConfigError('s')\n"
        "    except IndexError:\n        raise ConfigError('s')\n"
        "    with x:\n        raise ConfigError('s')\n    with y:\n        raise ConfigError('s')\n"
    )
    found = sites_of(tmp_path, body)
    assert len(found) == 8
    assert len({s.key for s in found}) == 8
    assert all(s.key.endswith("::1") for s in found)


# --------------------------------------------------------------------------------------------------------------------
# unit 7 to 9: write, round trip and compare


def synthetic(tmp: Path) -> Path:
    body = (
        "def a():\n    raise ConfigError('lit')\n\n\ndef b(x):\n    raise ConfigError(f'v {x}')\n"
    )
    body += "def c():\n    try:\n        pass\n    except Exception as e:\n        raise ConfigError(str(e))\n"
    return make(tmp, {"m.py": HEAD + body})


def test_unit7_write_fills_blank_for_unproven_literal_and_foreign_for_locked(
    tmp_path: Path,
) -> None:
    pkg = synthetic(tmp_path)
    table = tmp_path / "t.csv"
    need("write")(pkg, table)
    rows = {r.site.split("::")[1]: r for r in need("load_csv")(table)}
    assert rows["a"].klass == "LITERAL"
    assert rows["b"].klass == ""
    assert rows["c"].klass == "FOREIGN"


def test_unit7_write_is_idempotent_keeps_human_fields_and_with_blank_rows_present(
    tmp_path: Path,
) -> None:
    pkg = synthetic(tmp_path)
    table = tmp_path / "t.csv"
    write, load_csv, row_cls = need("write"), need("load_csv"), need("Row")
    write(pkg, table)
    first = table.read_bytes()
    write(pkg, table)  # blank rows present: no SitesError, same bytes
    assert table.read_bytes() == first
    rows = load_csv(table)
    rows = [row_cls(r.site, "OPERATOR", "my reason") if "::b::" in r.site else r for r in rows]
    table.write_bytes(need("render_csv")(rows).encode("ascii"))
    write(pkg, table)
    kept = {r.site.split("::")[1]: r for r in load_csv(table)}
    assert (kept["b"].klass, kept["b"].reason) == ("OPERATOR", "my reason")


def test_unit7_write_drops_stale_rows_and_blanks_new_ones(tmp_path: Path) -> None:
    pkg = synthetic(tmp_path)
    table = tmp_path / "t.csv"
    write, load_csv = need("write"), need("load_csv")
    write(pkg, table)
    (pkg / "m.py").write_text(
        HEAD + "def b(x):\n    raise ConfigError(f'w {x}')\n", encoding="utf-8"
    )
    write(pkg, table)
    rows = load_csv(table)
    assert [r.site.split("::")[1] for r in rows] == ["b"]
    assert rows[0].klass == ""


def test_unit7_output_form_is_lf_ascii_sorted(tmp_path: Path) -> None:
    pkg = synthetic(tmp_path)
    table = tmp_path / "t.csv"
    need("write")(pkg, table)
    raw = table.read_bytes()
    assert raw.isascii() and b"\r" not in raw
    sites = [r.site for r in need("load_csv")(table)]
    assert sites == sorted(sites)
    assert raw.splitlines()[0] == b"site,class,reason"


def test_unit7_a_missing_csv_counts_as_empty_only_in_write(tmp_path: Path) -> None:
    pkg = synthetic(tmp_path)
    table = tmp_path / "none.csv"
    with pytest.raises(need("SitesError")):
        need("load_csv")(table)
    need("write")(pkg, table)
    assert table.exists()


def test_unit7_a_broken_csv_raises_and_stays_unchanged(tmp_path: Path) -> None:
    pkg = synthetic(tmp_path)
    table = tmp_path / "t.csv"
    table.write_bytes(b"wrong,header\n")
    with pytest.raises(need("SitesError")):
        need("write")(pkg, table)
    assert table.read_bytes() == b"wrong,header\n"


def test_unit7_write_refuses_a_path_not_ending_in_csv(tmp_path: Path) -> None:
    with pytest.raises(need("SitesError")):
        need("write")(synthetic(tmp_path), tmp_path / "t.txt")
    assert not (tmp_path / "t.txt").exists()


def test_unit8_csv_round_trip_with_comma_and_quote(tmp_path: Path) -> None:
    row_cls = need("Row")
    rows = [row_cls("a::b::c::1", "OPERATOR", 'has a comma, and a "quote"')]
    table = tmp_path / "t.csv"
    table.write_bytes(need("render_csv")(rows).encode("ascii"))
    assert need("load_csv")(table) == rows


def site_of(auto_class: str, auto_reason: str, name: str = "s") -> Any:
    return need("Site")("f.py", name, "ConfigError", "0" * 16, 1, auto_class, auto_reason, 1)


def test_unit9_clean_case_is_ok() -> None:
    site_cls, row_cls = need("Site"), need("Row")
    sites = [
        site_of("LITERAL", "constant", "a"),
        site_of("FOREIGN", "unproven-origin", "b"),
        site_of("FOREIGN", "exception-variable", "c"),
    ]
    rows = [
        row_cls(sites[0].key, "LITERAL", ""),
        row_cls(sites[1].key, "OPERATOR", "why"),
        row_cls(sites[2].key, "FOREIGN", ""),
    ]
    report = need("compare")(sites, rows)
    assert report.ok is True
    assert site_cls is not None


LISTS = (
    "unclassified",
    "stale",
    "blank_class",
    "locked_downgrade",
    "wrong_literal",
    "missing_reason",
)


def only_list(report: Any, name: str) -> None:
    assert report.ok is False
    for other in LISTS:
        assert bool(getattr(report, other)) == (other == name), (other, report.render())


def test_unit9_unclassified() -> None:
    site = site_of("LITERAL", "constant")
    only_list(need("compare")([site], []), "unclassified")


def test_unit9_stale() -> None:
    row_cls = need("Row")
    only_list(need("compare")([], [row_cls("gone::x::y::1", "LITERAL", "")]), "stale")


def test_unit9_blank_class() -> None:
    site = site_of("FOREIGN", "unproven-origin")
    only_list(need("compare")([site], [need("Row")(site.key, "", "")]), "blank_class")


def test_unit9_locked_downgrade_operator_and_literal() -> None:
    site = site_of("FOREIGN", "exception-variable")
    for klass in ("OPERATOR", "LITERAL"):
        only_list(
            need("compare")([site], [need("Row")(site.key, klass, "why")]), "locked_downgrade"
        )


def test_unit9_wrong_literal_direction_one() -> None:
    site = site_of("FOREIGN", "unproven-origin")
    only_list(need("compare")([site], [need("Row")(site.key, "LITERAL", "")]), "wrong_literal")


def test_unit9_wrong_literal_direction_two() -> None:
    site = site_of("LITERAL", "constant")
    for klass in ("OPERATOR", "FOREIGN"):
        only_list(need("compare")([site], [need("Row")(site.key, klass, "why")]), "wrong_literal")


def test_unit9_missing_reason_for_operator_and_foreign_unproven() -> None:
    for auto, klass in (("unproven-origin", "OPERATOR"), ("unproven-origin", "FOREIGN")):
        site = site_of("FOREIGN", auto)
        only_list(need("compare")([site], [need("Row")(site.key, klass, "  ")]), "missing_reason")


def test_unit9_a_locked_foreign_row_needs_no_reason() -> None:
    site = site_of("FOREIGN", "exception-variable")
    assert need("compare")([site], [need("Row")(site.key, "FOREIGN", "")]).ok is True


def test_unit9_overlaps_land_in_one_list() -> None:
    row_cls = need("Row")
    lit = site_of("LITERAL", "constant")
    only_list(need("compare")([lit], [row_cls(lit.key, "", "")]), "blank_class")
    locked = site_of("FOREIGN", "exception-variable")
    only_list(need("compare")([locked], [row_cls(locked.key, "LITERAL", "")]), "locked_downgrade")


def test_unit9_the_judgement_reads_only_the_scan() -> None:
    """A table can store nothing but site, class and reason, so a lock cannot be edited away."""
    assert tuple(need("COLUMNS")) == ("site", "class", "reason")
    assert {f for f in need("Row").__dataclass_fields__} == {"site", "klass", "reason"}


def test_report_render_prints_lists_and_the_count_line() -> None:
    site = site_of("FOREIGN", "exception-variable")
    report = need("compare")([site], [need("Row")(site.key, "OPERATOR", "x")])
    text = report.render()
    assert "locked_downgrade" in text and site.key in text
    assert text.splitlines()[-1] == "rows=1 LITERAL=0 OPERATOR=1 FOREIGN=0 blank=0 locked=1"


# --------------------------------------------------------------------------------------------------------------------
# unit 10: the command line


def project(tmp: Path, body: str = "def f():\n    raise ConfigError('x')\n") -> Path:
    pkg = tmp / "src" / "hadavin_sdk"
    pkg.parent.mkdir(parents=True)
    pkg.mkdir()
    (pkg / "errors.py").write_text(ERRORS, encoding="utf-8")
    (pkg / "m.py").write_text(
        "from hadavin_sdk.errors import ConfigError\n" + body, encoding="utf-8"
    )
    return tmp


def test_unit10_cli_check_exit_codes_and_relative_csv(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main = need("main")
    root = project(tmp_path)
    assert main(["--write", "--root", str(root), "--csv", "t.csv"]) == 0
    assert (root / "t.csv").exists()  # a relative --csv resolves against --root
    assert main(["--check", "--root", str(root), "--csv", "t.csv"]) == 0
    (root / "src" / "hadavin_sdk" / "m.py").write_text(
        "from hadavin_sdk.errors import ConfigError\ndef f(x):\n    raise ConfigError(f'{x}')\n",
        encoding="utf-8",
    )
    capsys.readouterr()
    assert main(["--root", str(root), "--csv", "t.csv"]) == 1
    out = capsys.readouterr().out
    assert "unclassified" in out and "stale" in out
    (root / "src" / "hadavin_sdk" / "m.py").write_text("def broken(:\n", encoding="utf-8")
    assert main(["--check", "--root", str(root), "--csv", "t.csv"]) == 2


def test_unit10_cli_review_lists_blank_and_operator_rows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main = need("main")
    root = project(tmp_path, "def f(x):\n    raise ConfigError(f'v {x}')\n")
    assert main(["--write", "--root", str(root), "--csv", "t.csv"]) == 0
    capsys.readouterr()
    assert main(["--review", "--root", str(root), "--csv", "t.csv"]) == 0
    out = capsys.readouterr().out
    assert "param x of f" in out and "unproven-origin" in out


def test_unit10_cli_refuses_a_csv_not_ending_in_csv(tmp_path: Path) -> None:
    root = project(tmp_path)
    assert need("main")(["--write", "--root", str(root), "--csv", "t.txt"]) == 2
    assert not (root / "t.txt").exists()


def test_unit10_cli_missing_csv_is_an_error_not_no_rows(tmp_path: Path) -> None:
    root = project(tmp_path)
    assert need("main")(["--check", "--root", str(root), "--csv", "none.csv"]) == 2


# --------------------------------------------------------------------------------------------------------------------
# unit 11: from_cause


def test_unit11_from_cause_is_not_a_site(tmp_path: Path) -> None:
    body = "def f(d):\n    raise ConfigError.from_cause(d)\n"
    assert sites_of(tmp_path, body) == []


# --------------------------------------------------------------------------------------------------------------------
# unit 12: factories and raiser helpers

FACTORY = "def _fail(case, msg):\n    return ConfigError(f'bundle {case}: {msg}')\n"
RAISER = "def _bad(where, k):\n    raise ConfigError(f'{where}: {k}')\n"


def test_unit12_a_returning_function_gives_one_row_per_call(tmp_path: Path) -> None:
    body = (
        FACTORY + "\n\ndef a(c):\n    raise _fail(c, 'x')\n\n\ndef b(c):\n    raise _fail(c, 'y')\n"
    )
    found = sites_of(tmp_path, body)
    assert sorted(s.symbol for s in found) == ["_fail", "a", "b"]
    calls = [s for s in found if s.symbol != "_fail"]
    assert all(s.auto_class == "FOREIGN" and s.auto_reason == "unproven-origin" for s in calls)


def test_unit12_a_call_with_only_plain_strings_is_literal(tmp_path: Path) -> None:
    found = sites_of(tmp_path, FACTORY + "\n\ndef a():\n    raise _fail('c', 'm')\n")
    assert {s.symbol: s.auto_class for s in found}["a"] == "LITERAL"


def test_unit12_a_raising_function_gives_no_call_site_rows(tmp_path: Path) -> None:
    body = RAISER + "\n\ndef a(w):\n    _bad(w, 1)\n"
    assert [s.symbol for s in sites_of(tmp_path, body)] == ["_bad"]


def test_unit12_a_factory_call_in_a_handler_is_exception_variable(tmp_path: Path) -> None:
    body = (
        "def _fail2(case, msg):\n    return ConfigError(f'{case}: {msg}')\n\n\n"
        "def caller(c):\n    try:\n        pass\n    except Exception as exc:\n        raise _fail2(c, f'{exc}')\n"
    )
    found = {s.symbol: s for s in sites_of(tmp_path, body)}
    assert found["caller"].auto_reason == "exception-variable"
    assert found["caller"].kind == "ConfigError"


def test_unit12_a_factory_called_through_another_factory_is_refused(tmp_path: Path) -> None:
    body = FACTORY + "\n\ndef outer(c):\n    return _fail(c, 'x')\n"
    refuses(tmp_path, {"m.py": HEAD + body})


def test_unit12_assigning_a_construction_then_returning_the_name_is_refused(tmp_path: Path) -> None:
    body = "def f(x):\n    err = ConfigError(f'{x}')\n    return err\n"
    refuses(tmp_path, {"m.py": HEAD + body})


def test_unit12_a_function_that_returns_and_raises_is_a_factory_and_its_raises_stay_rows(
    tmp_path: Path,
) -> None:
    body = "def f(x):\n    if x:\n        raise ConfigError(f'r {x}')\n    return ConfigError(f'm {x}')\n\n\ndef g(y):\n    raise f(y)\n"
    found = sites_of(tmp_path, body)
    assert sorted(s.symbol for s in found) == ["f", "f", "g"]


def test_unit12_resolved_forms_and_the_same_name_elsewhere(tmp_path: Path) -> None:
    files = {
        "fac.py": HEAD + "\n" + FACTORY,
        "plain.py": HEAD + "\n" + FACTORY + "\n\ndef use():\n    raise _fail('c', 'x')\n",
        "frm.py": "from pkg.fac import _fail\n\n\ndef use():\n    raise _fail('c', 'x')\n",
        "als.py": "from pkg.fac import _fail as F\n\n\ndef use():\n    raise F('c', 'x')\n",
        "att.py": "import pkg.fac as fac\n\n\ndef use():\n    raise fac.F2('c', 'x')\n\n\ndef use2():\n    raise fac._fail('c', 'x')\n",
        "other.py": "def _fail(a, b):\n    return (a, b)\n\n\ndef use():\n    raise _fail('c', 'x')\n",
        "meth.py": "def use(self, obj):\n    raise self._fail('c', 'x')\n    raise obj._fail('c', 'y')\n",
    }
    found = need("scan")(make(tmp_path, files))
    by_file = {}
    for s in found:
        by_file.setdefault(s.file, []).append(s.symbol)
    assert by_file["plain.py"] == ["_fail", "use"]
    assert by_file["frm.py"] == ["use"]
    assert by_file["als.py"] == ["use"]
    assert by_file["att.py"] == ["use2"]
    assert "other.py" not in by_file
    assert "meth.py" not in by_file


def test_unit12_c5_an_untainted_raiser_call_gives_no_row(tmp_path: Path) -> None:
    body = RAISER + "\n\ndef a(w):\n    _bad(w, 1)\n"
    assert len(sites_of(tmp_path, body)) == 1


def test_unit12_c5_a_raiser_called_with_str_exc_in_a_handler_gives_one_locked_row(
    tmp_path: Path,
) -> None:
    body = (
        RAISER
        + "\n\ndef a(w):\n    try:\n        pass\n    except Exception as exc:\n        _bad(w, str(exc))\n"
    )
    found = {s.symbol: s for s in sites_of(tmp_path, body)}
    assert found["a"].auto_reason == "exception-variable"
    assert found["a"].auto_class == "FOREIGN"


def test_unit12_c5_review_hints_list_resolvable_callers(tmp_path: Path) -> None:
    body = RAISER + "\n\ndef a(w):\n    _bad(w, 1)\n"
    own = next(s for s in sites_of(tmp_path, body) if s.symbol == "_bad")
    assert any("caller" in h and "in a" in h for h in own.origin_hints)


@pytest.mark.xfail(
    strict=True, reason="a raiser called with document text (not an exception) is not detected"
)
def test_raiser_called_with_document_text_is_not_detected(tmp_path: Path) -> None:
    body = RAISER + "\n\ndef a(w, document_text):\n    _bad(w, document_text)\n"
    assert len(sites_of(tmp_path, body)) == 2


# --------------------------------------------------------------------------------------------------------------------
# unit 13


def test_unit13_reason_problems_flags_a_key_shaped_string_and_passes_a_plain_reason() -> None:
    row_cls = need("Row")
    shaped = "sk-" + "a1B2c3D4e5F6g7H8i9J0k1L2"
    assert reason_problems([row_cls("s", "OPERATOR", shaped)], PATTERNS)
    assert reason_problems([row_cls("s", "OPERATOR", "secret name from settings")], PATTERNS) == []


# --------------------------------------------------------------------------------------------------------------------
# hostile inputs


def test_hostile_syntax_error(tmp_path: Path) -> None:
    refuses(tmp_path, {"bad.py": "def broken(:\n"})


def test_hostile_invalid_utf8(tmp_path: Path) -> None:
    refuses(tmp_path, {"bad.py": b"x = '\xff\xfe'\n"})  # type: ignore[dict-item]


def test_hostile_null_byte(tmp_path: Path) -> None:
    refuses(tmp_path, {"bad.py": "x = 1\x00\n"})


def test_hostile_no_python_files(tmp_path: Path) -> None:
    refuses(tmp_path, {"readme.txt": "ConfigError('x')"}, errors=False)


def test_hostile_missing_package_folder(tmp_path: Path) -> None:
    with pytest.raises(need("SitesError")):
        need("scan")(tmp_path / "nowhere")


def test_hostile_no_config_error_class(tmp_path: Path) -> None:
    refuses(tmp_path, {"m.py": "def f():\n    raise ValueError('x')\n"}, errors=False)


def test_hostile_pycache_and_other_file_types_are_not_read(tmp_path: Path) -> None:
    files: dict[str, Any] = {
        "m.py": HEAD + "def f():\n    raise ConfigError('x')\n",
        "__pycache__/m.cpython-313.pyc": b"raise ConfigError('stale')\nConfigError(",
        "notes.txt": "raise ConfigError('in text')\n",
        "data.json": '{"x": "raise ConfigError(1)"}',
    }
    found = need("scan")(make(tmp_path, files))
    assert [s.file for s in found] == ["m.py"]


def test_hostile_pycache_with_a_python_file_is_skipped(tmp_path: Path) -> None:
    files = {
        "m.py": HEAD + "def f():\n    raise ConfigError('x')\n",
        "__pycache__/leftover.py": "raise ConfigError('y')\n",
    }
    assert [s.file for s in need("scan")(make(tmp_path, files))] == ["m.py"]


def test_hostile_symlinked_file_and_folder_are_refused(tmp_path: Path) -> None:
    pkg = make(tmp_path, {"m.py": HEAD + "def f():\n    raise ConfigError('x')\n"})
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "o.py").write_text("raise ConfigError('o')\n", encoding="utf-8")
    (pkg / "link.py").symlink_to(outside / "o.py")
    with pytest.raises(need("SitesError")):
        need("scan")(pkg)
    (pkg / "link.py").unlink()
    (pkg / "dirlink").symlink_to(outside, target_is_directory=True)
    with pytest.raises(need("SitesError")):
        need("scan")(pkg)


@pytest.mark.parametrize(
    "cls_body",
    [
        "    def __str__(self):\n        return 'x'\n",
        "    def __repr__(self):\n        return 'x'\n",
        "    def __format__(self, spec):\n        return 'x'\n",
        "    def __new__(cls, *a):\n        return super().__new__(cls)\n",
        "    __str__ = helper\n",
        "    def other(self):\n        return 1\n",
    ],
    ids=["str", "repr", "format", "new", "dunder-assign", "other-def"],
)
def test_hostile_site_class_bodies_are_refused(tmp_path: Path, cls_body: str) -> None:
    text = f"{HEAD}\n\ndef helper(self):\n    return 'x'\n\n\nclass A(ConfigError):\n{cls_body}"
    refuses(tmp_path, {"a.py": text})


@pytest.mark.parametrize(
    "header",
    [
        "@decorator\nclass A(ConfigError):\n    pass\n",
        "class A(ConfigError, Mixin):\n    pass\n",
        "class A(ConfigError, metaclass=Meta):\n    pass\n",
        "class A(ValueError):\n    pass\n\n\nclass B(A, ConfigError):\n    pass\n",
    ],
    ids=["decorator", "two-bases", "keyword", "mixed"],
)
def test_hostile_site_class_headers_are_refused(tmp_path: Path, header: str) -> None:
    refuses(tmp_path, {"a.py": f"{HEAD}\n\nMixin = object\nMeta = type\n\n\n{header}"})


def test_hostile_config_error_itself_must_have_exactly_value_error(tmp_path: Path) -> None:
    refuses(
        tmp_path,
        {"errors.py": f"class ConfigError(ValueError, KeyError):\n    {HOLD}\n"},
        errors=False,
    )


def test_hostile_a_second_base_initialiser_call_is_refused(tmp_path: Path) -> None:
    text = (
        f"{HEAD}\n\nclass A(ConfigError):\n    def __init__(self, p):\n        super().__init__('a')\n"
        "        super().__init__('b')\n"
    )
    refuses(tmp_path, {"a.py": text})


def test_hostile_init_assigning_args_or_missing_super_is_refused(tmp_path: Path) -> None:
    refuses(
        tmp_path,
        {
            "a.py": f"{HEAD}\n\nclass A(ConfigError):\n    def __init__(self, p):\n        super().__init__('a')\n        self.args = (p,)\n"
        },
    )
    (tmp_path / "x").mkdir()
    refuses(
        tmp_path / "x",
        {
            "a.py": f"{HEAD}\n\nclass A(ConfigError):\n    def __init__(self, p):\n        self.p = p\n"
        },
    )


MIG_ERR = (
    f"{HEAD}\n\ndef msg(problems):\n    return 'inconsistent: ' + '; '.join(problems)\n\n\n"
    f"class MigErr(ConfigError):\n    {HOLD}\n\n    def __init__(self, problems):\n"
    "        self.problems = tuple(problems)\n        super().__init__(msg(self.problems))\n\n"
    "    def __reduce__(self):\n        return (type(self), (self.problems,))\n\n\n"
    "def check(p):\n    raise MigErr(p)\n"
)


def test_hostile_a_class_shaped_like_the_migration_number_error_gives_a_row_for_super(
    tmp_path: Path,
) -> None:
    found = need("scan")(make(tmp_path, {"a.py": MIG_ERR}))
    assert sorted(s.symbol for s in found) == ["MigErr.__init__", "check"]
    init = next(s for s in found if s.symbol == "MigErr.__init__")
    assert (init.auto_class, init.auto_reason, init.kind) == (
        "FOREIGN",
        "unproven-origin",
        "MigErr",
    )


def test_the_real_migration_number_error_keeps_the_original_bn8_shape() -> None:
    """Order 130: no local, no ``if``, no helper inside ``__init__``; one attribute, one ``super().__init__`` call."""
    tree = ast.parse((SRC / "store" / "migration_numbers.py").read_text(encoding="utf-8"))
    cls = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "MigrationNumberError"
    )
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    kinds = [type(st).__name__ for st in init.body]
    assert kinds == ["AnnAssign", "Expr"], kinds
    assert [n.name for n in cls.body if isinstance(n, ast.FunctionDef)] == [
        "__init__",
        "__reduce__",
    ]


INIT_BODIES = {
    "local": "        shown = list(p)\n        super().__init__('x' + ';'.join(shown))\n",
    "if": "        if p:\n            self.p = p\n        super().__init__('x')\n",
    "for": "        for q in p:\n            self.p = q\n        super().__init__('x')\n",
    "args": "        super().__init__('x')\n        self.args = (p,)\n",
    "setattr": "        super().__init__('x')\n        setattr(self, 'args', (p,))\n",
    "object-setattr": "        super().__init__('x')\n        object.__setattr__(self, 'args', (p,))\n",
    "dict": "        super().__init__('x')\n        self.__dict__['args'] = (p,)\n",
    "vars": "        super().__init__('x')\n        vars(self)['args'] = (p,)\n",
    "add-note": "        super().__init__('x')\n        self.add_note(p)\n",
    "args-read": "        super().__init__('x')\n        self.p = self.args\n",
    "alias": "        me = self\n        super().__init__('x')\n        me.args = (p,)\n",
    "unpack": "        super().__init__('x')\n        self.a, self.b = p, p\n",
    "subscript": "        super().__init__('x')\n        self.p['k'] = p\n",
    "setattr-in-assign": "        self.p = setattr(self, 'args', (p,))\n        super().__init__('x')\n",
    "dict-in-assign": "        self.p = self.__dict__.update(args=(p,))\n        super().__init__('x')\n",
    "add-note-in-assign": "        self.p = self.add_note(p)\n        super().__init__('x')\n",
    "vars-in-super": "        super().__init__('x', vars(self).update(args=(p,)))\n",
    "args-in-super": "        super().__init__(*self.args)\n",
    "object-in-assign": "        self.p = object.__setattr__(self, 'args', (p,))\n        super().__init__('x')\n",
    "call-statement": "        super().__init__('x')\n        print(p)\n",
    "with": "        with p:\n            super().__init__('x')\n",
    "try": "        try:\n            super().__init__('x')\n        except KeyError:\n            self.p = p\n",
}


@pytest.mark.parametrize("body", list(INIT_BODIES.values()), ids=list(INIT_BODIES))
def test_hostile_init_bodies_beyond_attributes_and_super_are_refused(
    tmp_path: Path, body: str
) -> None:
    text = f"{HEAD}\n\nclass A(ConfigError):\n    def __init__(self, p):\n{body}"
    refuses(tmp_path, {"a.py": text})


def test_a_docstring_and_annotated_attribute_in_init_are_accepted(tmp_path: Path) -> None:
    text = (
        f"{HEAD}\n\nclass A(ConfigError):\n    def __init__(self, p):\n        'doc'\n"
        "        self.p: tuple = tuple(p)\n        self.q = self.p\n        super().__init__('x')\n"
    )
    assert [s.symbol for s in need("scan")(make(tmp_path, {"a.py": text}))] == ["A.__init__"]


RED = "    def __reduce__(self):\n"
REDUCES = {
    "reduce-ex": "    def __reduce_ex__(self, protocol):\n        return (type(self), (self.problems,))\n",
    "getstate": "    def __getstate__(self):\n        return {}\n",
    "setstate": "    def __setstate__(self, state):\n        self.args = state\n",
    "other-class": RED + "        return (Other, (self.problems,))\n",
    "three-tuple": RED + "        return (type(self), (self.problems,), {'a': 1})\n",
    "helper": RED + "        return rebuild(self)\n",
    "different-helper": RED + "        return (type(self), (rebuild(self.problems),))\n",
    "attr-of-attr": RED + "        return (type(self), (self.problems.x,))\n",
    "str-self": RED + "        return (type(self), (str(self),))\n",
    "empty-args": RED + "        return (type(self), ())\n",
    "extra-statement": RED
    + "        self.problems = ()\n        return (type(self), (self.problems,))\n",
    "dunder-attr": RED + "        return (type(self), (self.__dict__,))\n",
    "decorated": "    @property\n" + RED + "        return (type(self), (self.problems,))\n",
    "extra-arg": "    def __reduce__(self, x=1):\n        return (type(self), (self.problems,))\n",
    "async": "    async def __reduce__(self):\n        return (type(self), (self.problems,))\n",
    "assigned": "    __reduce__ = helper\n",
}


@pytest.mark.parametrize("body", list(REDUCES.values()), ids=list(REDUCES))
def test_hostile_pickle_helpers_other_than_the_one_exact_reduce_are_refused(
    tmp_path: Path, body: str
) -> None:
    text = (
        f"{HEAD}\n\nOther = type\n\n\ndef helper(self):\n    return 1\n\n\ndef rebuild(x):\n    return x\n\n\n"
        f"class A(ConfigError):\n    def __init__(self, problems):\n        self.problems = problems\n"
        f"        super().__init__('x')\n\n{body}"
    )
    refuses(tmp_path, {"a.py": text})


def test_the_one_exact_reduce_is_accepted_with_a_docstring_and_two_attributes(
    tmp_path: Path,
) -> None:
    text = (
        f"{HEAD}\n\nclass A(ConfigError):\n    def __init__(self, a, b):\n        self.a = a\n        self.b = b\n"
        "        super().__init__('x')\n\n    def __reduce__(self):\n        'rebuild'\n"
        "        return (type(self), (self.a, self.b))\n"
    )
    assert [s.symbol for s in need("scan")(make(tmp_path, {"a.py": text}))] == ["A.__init__"]


def test_two_reduce_methods_are_refused(tmp_path: Path) -> None:
    one = "    def __reduce__(self):\n        return (type(self), (self.problems,))\n"
    text = (
        f"{HEAD}\n\nclass A(ConfigError):\n    def __init__(self, problems):\n        self.problems = problems\n"
        f"        super().__init__('x')\n\n{one}\n{one}"
    )
    refuses(tmp_path, {"a.py": text})


def test_hostile_non_ascii_symbol_is_refused(tmp_path: Path) -> None:
    body = "def caf\u00e9():\n    raise ConfigError('x')\n"
    refuses(tmp_path, {"m.py": HEAD + body})


def test_hostile_non_ascii_file_name_is_refused(tmp_path: Path) -> None:
    refuses(tmp_path, {"caf\u00e9.py": HEAD + "def f():\n    raise ConfigError('x')\n"})


# the table file


def write_table(tmp: Path, text: str | bytes) -> Path:
    path = tmp / "t.csv"
    path.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
    return path


GOOD = "site,class,reason\n"


@pytest.mark.parametrize(
    "text",
    [
        "site,class\na::b::c::1,LITERAL\n",
        "site,class,code,reason\na::b::c::1,LITERAL,,\n",
        "site,class,reason,kind,auto_class,auto_reason,code,line,a,b\n",
        "",
        GOOD + "a::b::c::1,LITERAL,\na::b::c::1,LITERAL,\n",
        GOOD + "a::b::c::1,literal,\n",
        GOOD + "a::b::c::1,SAFE,\n",
        GOOD + "a::b::c::1, LITERAL,\n",
        GOOD + "a::b::c::1,LITERAL,x\u00e9\n",
        GOOD + "a::b::c::1,OPERATOR," + "r" * 201 + "\n",
        GOOD + 'a::b::c::1,OPERATOR,"two\nlines"\n',
        GOOD + "a::b::c::1,OPERATOR\n",
        GOOD + "\n",
    ],
    ids=[
        "short-header",
        "old-header",
        "ten-columns",
        "empty",
        "duplicate",
        "lower",
        "safe",
        "space",
        "non-ascii",
        "long",
        "newline",
        "short-row",
        "blank-line",
    ],
)
def test_hostile_csv_is_refused(tmp_path: Path, text: str) -> None:
    with pytest.raises(need("SitesError")):
        need("load_csv")(write_table(tmp_path, text))


def test_hostile_csv_reason_of_exactly_the_limit_loads(tmp_path: Path) -> None:
    rows = need("load_csv")(write_table(tmp_path, GOOD + "a::b::c::1,OPERATOR," + "r" * 200 + "\n"))
    assert len(rows[0].reason) == 200


def test_hostile_csv_blank_class_loads(tmp_path: Path) -> None:
    rows = need("load_csv")(write_table(tmp_path, GOOD + "a::b::c::1,,\n"))
    assert rows[0].klass == ""
    site = need("Site")("a", "b", "ConfigError", "c", 1, "FOREIGN", "unproven-origin", 1)
    assert site.key == "a::b::c::1"
    only_list(need("compare")([site], rows), "blank_class")


def test_hostile_csv_with_crlf_line_endings_is_accepted(tmp_path: Path) -> None:
    rows = need("load_csv")(write_table(tmp_path, "site,class,reason\r\na::b::c::1,LITERAL,\r\n"))
    assert [r.klass for r in rows] == ["LITERAL"]


def test_csv_module_is_used_with_the_stated_columns() -> None:
    assert csv.excel is not None
    assert tuple(need("COLUMNS")) == ("site", "class", "reason")
    assert need("REASON_MAX") == 200
    assert need("HASH_LEN") == 16
    assert tuple(need("CLASSES")) == ("LITERAL", "OPERATOR", "FOREIGN")


# --------------------------------------------------------------------------------------------------------------------
# design F3: a site class used as a value


VALUE_USES = {
    "variable": "kind = ConfigError\n\n\ndef f():\n    raise kind('x')\n",
    "argument": "def raise_as(cls, text):\n    raise cls(text)\n\n\ndef f():\n    raise_as(ConfigError, 'x')\n",
    "tuple": "def f():\n    return (type(None), ConfigError)\n",
    "list": "ERRORS = [ConfigError]\n",
    "dict": "ERRORS = {'a': ConfigError}\n",
    "partial": "import functools\n\nmake = functools.partial(ConfigError, 'x')\n",
    "return": "def f():\n    return ConfigError\n",
    "attribute": "import pkg.errors as errors\n\n\ndef f():\n    return errors.ConfigError\n",
    "dunder-call": "def f():\n    raise ConfigError.__call__('x')\n",
    "new": "def f():\n    raise ConfigError.__new__(ConfigError, 'x')\n",
    "lambda": "make = lambda: ConfigError\n",
    "comprehension": "def f(xs):\n    return [ConfigError for _ in xs]\n",
    "default": "def f(cls=ConfigError):\n    raise cls('x')\n",
    "type-call": "def f():\n    raise type(ConfigError)('x')\n",
    "subclass-by-name": "def f(e):\n    return e.__class__ is ConfigError\n",
}


@pytest.mark.parametrize("body", list(VALUE_USES.values()), ids=list(VALUE_USES))
def test_f3_a_site_class_used_as_a_value_is_refused(tmp_path: Path, body: str) -> None:
    """Design F3. Killing mutant: M33 (the value check is removed)."""
    refuses(tmp_path, {"m.py": HEAD + body})


def test_f3_a_subclass_and_an_alias_used_as_a_value_are_refused(tmp_path: Path) -> None:
    sub = "class Sub(ConfigError):\n    pass\n\n\nkind = Sub\n"
    refuses(tmp_path, {"m.py": HEAD + sub})
    (tmp_path / "x").mkdir()
    alias = "from pkg.errors import ConfigError as CE\n\nkind = CE\n"
    refuses(tmp_path / "x", {"m.py": alias})


ALLOWED_USES = {
    "call": "def f():\n    raise ConfigError('x')\n",
    "bare-raise": "def f():\n    raise ConfigError\n",
    "except": "def f():\n    try:\n        pass\n    except ConfigError:\n        pass\n",
    "except-tuple": "def f():\n    try:\n        pass\n    except (KeyError, ConfigError):\n        pass\n",
    "except-as": "def f():\n    try:\n        pass\n    except ConfigError as exc:\n        raise exc\n",
    "isinstance": "def f(e):\n    return isinstance(e, ConfigError)\n",
    "isinstance-tuple": "def f(e):\n    return isinstance(e, (KeyError, ConfigError))\n",
    "isinstance-union": "def f(e):\n    return isinstance(e, KeyError | ConfigError)\n",
    "issubclass": "def f(c):\n    return issubclass(c, ConfigError)\n",
    "base": "class Sub(ConfigError):\n    pass\n",
    "annotation": "def f(e: ConfigError) -> ConfigError:\n    return e\n",
    "annotation-generic": "ERRORS: list[ConfigError] = []\n",
    "class-name": "NAME = ConfigError.__name__\n",
    "classmethod": "def f():\n    return ConfigError.from_cause\n",
    "attribute-call": "import pkg.errors as errors\n\n\ndef f():\n    raise errors.ConfigError('x')\n",
}


@pytest.mark.parametrize("body", list(ALLOWED_USES.values()), ids=list(ALLOWED_USES))
def test_f3_the_allowed_uses_of_a_site_class_still_scan(tmp_path: Path, body: str) -> None:
    need("scan")(make(tmp_path, {"m.py": HEAD + body}))
