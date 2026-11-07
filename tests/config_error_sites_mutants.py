"""The mutants of the ConfigError site table generator (``tools/gen_config_error_sites.py``).

Each mutant is a copy of the generator with one edit (a few have two edits that belong together; the row says so). The runner builds a
temporary tree, runs the whole file ``tests/test_config_error_sites.py`` once per mutant in a fresh interpreter, and reads the verdict from
the exit code and the junit file only:

* KILLED  exit code 1 and at least one failed test (a ``<failure>`` element: a failed assert, ``DID NOT RAISE`` and any exception
          raised in a test body all count);
* CRASH   exit code 2, 3, 4 or 5; exit code 1 with only ``<error>`` elements (setup, teardown or collection); or a failed pre-check
          (the mutated file does not parse or does not import);
* SURVIVED  exit code 0;
* SKIPPED   any ``<skipped>`` element.

The baseline (the unmutated tree) must run with 0 failures, 0 errors and 0 skips, or the runner exits 2. Exit 0 only when every row is
KILLED. For every mutant the runner lists the failed test ids and flags a row whose expected killer is not among them (the row is still
KILLED). The runner uses ``multiprocessing`` with the ``spawn`` start method and no ``subprocess``. Not collected by pytest. Run from the
repository root:

    uv run --all-extras --group test python tests/config_error_sites_mutants.py            # all mutants
    uv run --all-extras --group test python tests/config_error_sites_mutants.py M9 M12     # only the named ids

Not covered by a mutant (covered by the named test instead): a missing CSV is not "no rows"; ``--csv`` must end in ``.csv``; a relative
``--csv`` resolves against ``--root``; the CLI exit codes; no ``*.py`` file; no ``ConfigError`` class; invalid UTF-8; a factory called
through a factory; the taint sources of BN-7; the reason check (it lives in the test file, which this runner does not mutate).
M8c switches off all its forms in one edit; it proves only that the group has teeth.
"""

from __future__ import annotations

import multiprocessing
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = "tools/gen_config_error_sites.py"
TEST_FILE = "tests/test_config_error_sites.py"
T = TEST_FILE + "::"


@dataclass(frozen=True)
class Mutant:
    ident: str
    what: str
    edits: tuple[tuple[str, str], ...]
    killer: str  # the expected killer: a test id (or the start of one) inside the test file


def m(ident: str, what: str, killer: str, *edits: tuple[str, str]) -> Mutant:
    return Mutant(ident, what, tuple(edits), T + killer)


MUTANTS: tuple[Mutant, ...] = (
    m(
        "M1",
        "subclass closure runs once, not to a fixed point",
        "test_unit4_subclass_closure_across_modules_and_file_order",
        (
            "                    classes.add(node.name)\n                    changed = True\n",
            "                    classes.add(node.name)\n",
        ),
    ),
    m(
        "M2",
        "a base written errors.ConfigError is ignored",
        "test_unit4_base_written_as_attribute",
        (
            "    if isinstance(expr, ast.Attribute):\n        return expr.attr\n    return None\n",
            "    return None\n",
        ),
    ),
    m(
        "M3",
        "an import alias is ignored",
        "test_unit4_alias_import_and_attribute_call_are_recorded_canonically",
        ("        return aliases.get(expr.id, expr.id)\n", "        return expr.id\n"),
    ),
    m(
        "M4",
        "a bare raise of the class is ignored",
        "test_unit4_bare_raise_of_the_class_is_a_literal_site",
        (
            "                name = _canon_name(exc, mod.aliases)\n                if name in self.classes:\n",
            "                name = _canon_name(exc, mod.aliases)\n                if False and name in self.classes:\n",
        ),
    ),
    m(
        "M5",
        "the walk also writes position fields",
        "test_unit5_a_moved_function_and_an_indent_keep_the_row",
        (
            '        out.append("(" + type(node).__name__)\n',
            '        out.append("(" + type(node).__name__ + str(getattr(node, "lineno", "")))\n',
        ),
    ),
    m(
        "M6",
        "the hash covers the node type only, not the tree",
        "test_unit5_changed_word_gives_a_new_key",
        (
            '    return hashlib.sha256("".join(out).encode("utf-8")).hexdigest()[:HASH_LEN]\n',
            '    return hashlib.sha256(type(node).__name__.encode("utf-8")).hexdigest()[:HASH_LEN]\n',
        ),
    ),
    m(
        "M7",
        "k is dropped (identical sites collapse)",
        "test_unit6_identical_sites_in_one_function_get_k1_and_k2",
        (
            "                sites.append(Site(f, sym, kind, h, k, ac, ar, line, hints))\n",
            "                sites.append(Site(f, sym, kind, h, 1, ac, ar, line, hints))\n",
        ),
    ),
    m(
        "M8a",
        "type(e).__name__ is not seen as a use of the exception",
        "test_unit3_taint_forms_are_exception_variable[type-name]",
        (
            "def _mentions(expr: ast.AST, names: frozenset[str] | set[str]) -> bool:\n",
            (
                "def _mentions(expr: ast.AST, names: frozenset[str] | set[str]) -> bool:\n"
                '    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "type" for n in ast.walk(expr)):\n'
                "        return False\n"
            ),
        ),
    ),
    m(
        "M8b",
        "assignment does not carry taint",
        "test_unit3_taint_forms_are_exception_variable[assign]",
        (
            "            if isinstance(node, ast.Assign):\n",
            "            if isinstance(node, ast.Assign) and False:\n",
        ),
    ),
    m(
        "M8c",
        "the wider forms are not followed (for, comprehension, walrus, with, subscript or attribute target, mutating calls); two edits",
        "test_unit3_taint_forms_are_exception_variable[for]",
        (
            (
                "            elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):\n"
                "                pairs.append((node.iter, [node.target]))\n"
                "            elif isinstance(node, ast.NamedExpr):\n"
                "                pairs.append((node.value, [node.target]))\n"
                "            elif isinstance(node, (ast.With, ast.AsyncWith)):\n"
                "                for item in node.items:\n"
                "                    if item.optional_vars is not None:\n"
                "                        pairs.append((item.context_expr, [item.optional_vars]))\n"
                "            elif (\n"
                "                isinstance(node, ast.Call)\n"
                "                and isinstance(node.func, ast.Attribute)\n"
                "                and node.func.attr in MUTATORS\n"
                "            ):\n"
                "                values = [*node.args, *(kw.value for kw in node.keywords)]\n"
                "                if any(_mentions(v, tainted) for v in values):\n"
                "                    tainted.update(_target_names(node.func.value))\n"
            ),
            "",
        ),
        (
            "    if isinstance(target, (ast.Subscript, ast.Attribute)):\n        return _target_names(target.value)\n",
            "",
        ),
    ),
    m(
        "M9",
        "OPERATOR is allowed on an exception-variable row",
        "test_unit9_locked_downgrade_operator_and_literal",
        (
            '        elif site.auto_reason == EXC_VAR and row.klass != "FOREIGN":\n',
            '        elif site.auto_reason == EXC_VAR and row.klass not in ("FOREIGN", "OPERATOR"):\n',
        ),
    ),
    m(
        "M10",
        "a blank class is accepted",
        "test_unit9_blank_class",
        (
            '        if row.klass == "":\n            blank.append(key)\n',
            "        if False:\n            blank.append(key)\n",
        ),
    ),
    m(
        "M11",
        "a reason is not required for OPERATOR",
        "test_unit9_missing_reason_for_operator_and_foreign_unproven",
        (
            '            row.klass == "OPERATOR" or (row.klass == "FOREIGN" and site.auto_reason == UNPROVEN)\n',
            '            (row.klass == "FOREIGN" and site.auto_reason == UNPROVEN)\n',
        ),
    ),
    m(
        "M12",
        "compare does not report unclassified sites",
        "test_planted_unclassified_site_is_refused",
        (
            "    unclassified = sorted(k for k in by_site if k not in by_row)\n",
            "    unclassified = []\n",
        ),
    ),
    m(
        "M13",
        "stale rows are not reported",
        "test_unit9_stale",
        ("    stale = sorted(k for k in by_row if k not in by_site)\n", "    stale = []\n"),
    ),
    m(
        "M14a",
        "the scan reads *.pyc and other file types; two edits",
        "test_hostile_pycache_and_other_file_types_are_not_read",
        (
            '            elif entry.suffix == ".py":\n',
            '            elif entry.suffix in (".py", ".pyc", ".txt", ".json"):\n',
        ),
        ('                if entry.name != "__pycache__":\n', "                if True:\n"),
    ),
    m(
        "M14b",
        "the scan skips subfolders",
        "test_unit4_nested_package",
        (
            '                if entry.name != "__pycache__":\n                    pending.append(entry)\n',
            "                pass\n",
        ),
    ),
    m(
        "M15",
        "a file that cannot be parsed is skipped, not raised",
        "test_hostile_syntax_error",
        (
            '            raise SitesError(f"cannot parse {rel}: {type(exc).__name__}") from exc\n',
            "            continue\n",
        ),
    ),
    m(
        "M16",
        "write() fills the class of a new unproven row",
        "test_unit7_write_fills_blank_for_unproven_literal_and_foreign_for_locked",
        (
            '            rows.append(Row(site.key, "", ""))\n',
            '            rows.append(Row(site.key, "OPERATOR", "auto"))\n',
        ),
    ),
    m(
        "M17",
        "the generator imports a module that is not in the allowlist",
        "test_generator_imports_standard_library_only",
        ("import hashlib\nimport sys\n", "import hashlib\nimport importlib\nimport sys\n"),
    ),
    m(
        "M18",
        "ConfigError.from_cause(...) is counted as a site",
        "test_unit11_from_cause_is_not_a_site",
        (
            "            name = _canon_name(node.func, mod.aliases)\n            if name in self.classes:\n                return name\n",
            (
                "            name = _canon_name(node.func, mod.aliases)\n"
                "            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):\n"
                "                name = node.func.value.id\n"
                "            if name in self.classes:\n                return name\n"
            ),
        ),
    ),
    m(
        "M19",
        "class LITERAL is accepted on a row that is not automatically LITERAL (direction 1)",
        "test_unit9_wrong_literal_direction_one",
        (
            '        elif (row.klass == "LITERAL") != (site.auto_class == "LITERAL"):\n',
            '        elif row.klass != "LITERAL" and site.auto_class == "LITERAL":\n',
        ),
    ),
    m(
        "M19b",
        "a class other than LITERAL is accepted on a LITERAL row (direction 2)",
        "test_unit9_wrong_literal_direction_two",
        (
            '        elif (row.klass == "LITERAL") != (site.auto_class == "LITERAL"):\n',
            '        elif row.klass == "LITERAL" and site.auto_class != "LITERAL":\n',
        ),
    ),
    m(
        "M21",
        "factories are ignored (calls of a returning helper are not sites)",
        "test_unit12_a_returning_function_gives_one_row_per_call",
        (
            "        helper = self.resolve(node, mod, self.factories)\n        if helper is not None:\n",
            "        helper = None\n        if helper is not None:\n",
        ),
    ),
    m(
        "M23",
        "write() drops the human fields of unchanged rows",
        "test_unit7_write_is_idempotent_keeps_human_fields_and_with_blank_rows_present",
        (
            "            rows.append(old[site.key])\n",
            '            rows.append(Row(site.key, "", ""))\n',
        ),
    ),
    m(
        "M24a",
        "load_csv accepts a wrong header",
        "test_hostile_csv_is_refused[ten-columns]",
        ("    if not records or tuple(records[0]) != COLUMNS:\n", "    if not records:\n"),
    ),
    m(
        "M24b",
        "load_csv accepts a duplicate site",
        "test_hostile_csv_is_refused[duplicate]",
        ("        if site in seen:\n", "        if False and site in seen:\n"),
    ),
    m(
        "M24c",
        "load_csv accepts a non-ASCII byte",
        "test_hostile_csv_is_refused[non-ascii]",
        (
            '    if not raw.isascii():\n        raise SitesError("the table holds a non-ASCII byte")\n    text = raw.decode("ascii")\n',
            '    text = raw.decode("utf-8")\n',
        ),
    ),
    m(
        "M24d",
        "load_csv accepts a reason over REASON_MAX or with a line break; two edits",
        "test_hostile_csv_is_refused[long]",
        ("        if len(reason) > REASON_MAX:\n", "        if False:\n"),
        ("        if any(ord(c) < 32 or ord(c) == 127 for c in reason):\n", "        if False:\n"),
    ),
    m(
        "M24e",
        "load_csv refuses an empty class",
        "test_unit7_write_is_idempotent_keeps_human_fields_and_with_blank_rows_present",
        (
            '        if klass != "" and klass not in CLASSES:\n',
            "        if klass not in CLASSES:\n",
        ),
    ),
    m(
        "M26",
        "the body rule for a site class is removed; two edits",
        "test_hostile_site_class_bodies_are_refused[dunder-assign]",
        (
            '            raise SitesError(f"site class {cls.name} assigns a dunder or complex name")\n',
            "            continue\n",
        ),
        (
            '        raise SitesError(f"site class {cls.name} holds more than a docstring and plain fields")\n',
            "        continue\n",
        ),
    ),
    m(
        "M27",
        "the hash depends on the source columns (stand-in for a hash of tokens)",
        "test_unit5_hash_survives_formatting",
        (
            '        out.append("(" + type(node).__name__)\n',
            '        out.append("(" + type(node).__name__ + str(getattr(node, "end_col_offset", "")))\n',
        ),
    ),
    m(
        "M28",
        "raising functions are counted as factories",
        "test_unit12_a_raising_function_gives_no_call_site_rows",
        (
            "        helper = self.resolve(node, mod, self.factories)\n",
            "        helper = self.resolve(node, mod, self.factories) or self.resolve(node, mod, self.raisers)\n",
        ),
    ),
    m(
        "M29",
        "auto_class reads only the first argument",
        "test_unit1b_extra_argument_shapes_are_foreign",
        (
            "    if call.keywords or any(isinstance(a, ast.Starred) for a in call.args):\n        return False\n    if len(call.args) > 1:\n        return False\n",
            "",
        ),
    ),
    m(
        "M30",
        "rule C5 (a raiser called with a tainted value) is ignored",
        "test_unit12_c5_a_raiser_called_with_str_exc_in_a_handler_gives_one_locked_row",
        (
            "        if raiser is not None and any(",
            "        if False and raiser is not None and any(",
        ),
    ),
    m(
        "M31",
        "the super().__init__ call of a site class is not a row",
        "test_hostile_a_class_shaped_like_the_migration_number_error_gives_a_row_for_super",
        (
            '        if _is_super_init(node) and isinstance(scope, ast.FunctionDef) and scope.name == "__init__":\n',
            '        if False and _is_super_init(node) and isinstance(scope, ast.FunctionDef) and scope.name == "__init__":\n',
        ),
    ),
)

TREE_FILES = (
    "pyproject.toml",
    "tools/__init__.py",
    "tests/__init__.py",
    TEST_FILE,
    "tests/test_no_hardcoded_values.py",
    "tests/data/config_error_sites.csv",
)


def build_tree(tmp: Path, text: str) -> None:
    for rel in TREE_FILES:
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dest)
    (tmp / GENERATOR).write_text(text, encoding="utf-8")
    shutil.copytree(
        ROOT / "src" / "hadavin_sdk",
        tmp / "src" / "hadavin_sdk",
        ignore=shutil.ignore_patterns("__pycache__"),
    )


def _precheck_child(path: str) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("gen_under_test", path)
    if spec is None or spec.loader is None:
        sys.exit(3)
    module = importlib.util.module_from_spec(spec)
    sys.modules["gen_under_test"] = module
    spec.loader.exec_module(module)


def _pytest_child(tmp: str) -> None:
    import pytest

    os.chdir(tmp)
    sys.path.insert(0, tmp)
    code = pytest.main(
        [
            "-p",
            "no:cacheprovider",
            "--rootdir",
            tmp,
            "-q",
            "--junitxml",
            str(Path(tmp) / "result.xml"),
            TEST_FILE,
        ]
    )
    sys.exit(int(code))


def run_child(target: Callable[[str], None], arg: str) -> int:
    ctx = multiprocessing.get_context("spawn")
    proc = ctx.Process(target=target, args=(arg,))
    proc.start()
    proc.join()
    return proc.exitcode if proc.exitcode is not None else -1


CASE = re.compile(r"<testcase\b([^>]*?)(/>|>(.*?)</testcase>)", re.DOTALL)
ATTR = re.compile(r'(\w+)="([^"]*)"')


def read_result(path: Path) -> dict[str, list[str]]:
    """Failed, errored and skipped test ids from the junit file (read as text; no XML parser)."""
    out: dict[str, list[str]] = {"failed": [], "error": [], "skipped": [], "cases": []}
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    for match in CASE.finditer(text):
        attrs = {k: unescape(v) for k, v in ATTR.findall(match.group(1))}
        ident = attrs.get("classname", "").replace(".", "/") + "::" + attrs.get("name", "")
        out["cases"].append(ident)
        body = match.group(3) or ""
        if "<failure" in body:
            out["failed"].append(ident)
        if "<error" in body:
            out["error"].append(ident)
        if "<skipped" in body:
            out["skipped"].append(ident)
    return out


def verdict(code: int, res: dict[str, list[str]]) -> str:
    if res["skipped"]:
        return "SKIPPED"
    if code == 0:
        return "SURVIVED"
    if code == 1 and res["failed"]:
        return "KILLED"
    return "CRASH"


def short(ident: str) -> str:
    return ident.split("::", 1)[1] if "::" in ident else ident


def run_one(original: str, mutant: Mutant | None) -> tuple[str, int, dict[str, list[str]], str]:
    text = original
    if mutant is not None:
        for old, new in mutant.edits:
            if text.count(old) != 1:
                return (
                    "CRASH",
                    -1,
                    {"failed": [], "error": [], "skipped": [], "cases": []},
                    f"edit text occurs {text.count(old)} times",
                )
            text = text.replace(old, new)
    with tempfile.TemporaryDirectory(prefix="ces_mut_") as raw:
        tmp = Path(raw)
        build_tree(tmp, text)
        if mutant is not None:
            try:
                compile(text, GENERATOR, "exec")
            except SyntaxError as exc:
                return (
                    "CRASH",
                    -1,
                    {"failed": [], "error": [], "skipped": [], "cases": []},
                    f"does not parse: {exc.msg}",
                )
            if run_child(_precheck_child, str(tmp / GENERATOR)) != 0:
                return (
                    "CRASH",
                    -1,
                    {"failed": [], "error": [], "skipped": [], "cases": []},
                    "does not import",
                )
        code = run_child(_pytest_child, str(tmp))
        res = read_result(tmp / "result.xml")
    return verdict(code, res), code, res, ""


def main(argv: list[str]) -> int:
    original = (ROOT / GENERATOR).read_text(encoding="utf-8")
    chosen = [mu for mu in MUTANTS if not argv or mu.ident in argv]
    ids = [mu.ident for mu in MUTANTS]
    if len(set(ids)) != len(ids):
        print("duplicate mutant id")
        return 2
    base, code, res, note = run_one(original, None)
    print(
        f"baseline: exit {code}, {len(res['cases'])} cases, failed {len(res['failed'])}, errors {len(res['error'])}, skipped {len(res['skipped'])}"
    )
    if code != 0 or res["failed"] or res["error"] or res["skipped"]:
        print(f"baseline red ({base} {note})")
        return 2
    worst = 0
    counts: dict[str, int] = {}
    for mu in chosen:
        result, code, res, note = run_one(original, mu)
        counts[result] = counts.get(result, 0) + 1
        failed = [short(x) for x in res["failed"]]
        expected = short(mu.killer)
        flag = (
            ""
            if any(f == expected for f in failed)
            else "  EXPECTED KILLER NOT AMONG THE FAILED TESTS"
        )
        print(f"{mu.ident:5} {result:8} exit={code} failed={len(failed)} {note}{flag}")
        print(f"      {mu.what}")
        print(f"      expected killer: {expected}")
        for name in failed[:6]:
            print(f"        failed: {name}")
        if len(failed) > 6:
            print(f"        ... and {len(failed) - 6} more")
        if result != "KILLED":
            worst = 1
    print(
        "summary: " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())) + f" of {len(chosen)}"
    )
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
