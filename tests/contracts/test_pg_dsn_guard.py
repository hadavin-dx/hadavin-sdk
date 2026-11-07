"""Order 111 item 1 (class fix): a test that needs the database must skip (or fail under the fail rule) when
`HADAVIN_TEST_PG_DSN` is missing, never die with a KeyError. The one place that reads the variable by key is
`pg_test_dsn()` in `tests/contracts/kinds/__init__.py`, which calls `require_backend` first.

Three layers: an AST guard over the whole tests tree (no other raw `environ["HADAVIN_TEST_PG_DSN"]`), a check that
the guard itself sees the planted forms it must see, and a real nested run of the file that had the bug with the
variable unset."""

import ast

import pytest

from tests.contracts.test_store_registry import ROOT, _nested

TESTS = ROOT / "tests"
HELPER = TESTS / "contracts" / "kinds" / "__init__.py"
NAME = "HADAVIN_TEST_PG_DSN"


def raw_reads(source: str) -> list[int]:
    """Line numbers of every `<anything>.environ[<the DSN name>]` or `environ[<the DSN name>]` in `source`."""
    lines = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Subscript):
            continue
        base = node.value
        is_environ = (isinstance(base, ast.Attribute) and base.attr == "environ") or (
            isinstance(base, ast.Name) and base.id == "environ"
        )
        key = node.slice
        if is_environ and isinstance(key, ast.Constant) and key.value == NAME:
            lines.append(node.lineno)
    return lines


def scan(tests_dir, helper, root):
    """`path:line` of every raw read under `tests_dir`, the one `helper` file excepted."""
    found = []
    for path in sorted(tests_dir.rglob("*.py")):
        if path == helper:
            continue
        found += [
            f"{path.relative_to(root).as_posix()}:{n}" for n in raw_reads(path.read_text("utf-8"))
        ]
    return found


def test_no_test_file_reads_the_database_variable_by_key_except_the_helper():
    found = scan(TESTS, HELPER, ROOT)
    assert not found, (
        f"a raw environ[{NAME!r}] read dies with a KeyError where the test should skip; "
        f"call pg_test_dsn() from tests.contracts.kinds instead: {found}"
    )


def test_the_scan_reports_a_raw_read_in_any_file_but_the_helper(tmp_path):
    """The scan itself: a planted read is found in every other file and only the helper is exempt."""
    raw = f'import os\nx = os.environ["{NAME}"]\n'
    (tmp_path / "sub").mkdir()
    helper = tmp_path / "sub" / "helper.py"
    other = tmp_path / "sub" / "other.py"
    helper.write_text(raw, "utf-8")
    other.write_text(raw, "utf-8")
    (tmp_path / "top.py").write_text(raw, "utf-8")
    assert scan(tmp_path, helper, tmp_path) == ["sub/other.py:2", "top.py:2"]
    assert scan(tmp_path, tmp_path / "nowhere.py", tmp_path) == [
        "sub/helper.py:2",
        "sub/other.py:2",
        "top.py:2",
    ]


@pytest.mark.parametrize(
    "source",
    [
        f'import os\nx = os.environ["{NAME}"]\n',
        f"import os\nx = os.environ['{NAME}']\n",
        f'from os import environ\nx = environ["{NAME}"]\n',
        f'import os\nf(os.environ["{NAME}"])\n',
        f'import os\ndef g():\n    with h(os.environ["{NAME}"]) as c:\n        pass\n',
    ],
)
def test_the_guard_sees_every_form_of_the_raw_read(source):
    assert raw_reads(source), source


@pytest.mark.parametrize(
    "source",
    [
        f'import os\nx = os.environ.get("{NAME}")\n',
        f'import os\nx = os.getenv("{NAME}")\n',
        'import os\nx = os.environ["OTHER"]\n',
        'import os\nx = {"a": 1}["a"]\n',
        f'import os\nx = "os.environ[\\"{NAME}\\"]"\n',
    ],
)
def test_the_guard_does_not_flag_a_read_that_cannot_raise_a_key_error(source):
    assert raw_reads(source) == [], source


def _run_pg_driver_tests(extra_env):
    args = ["tests/contracts/test_pg_driver.py", "-q", "-p", "no:cacheprovider", "-rs"]
    return _nested(ROOT, extra_env, args)


def test_the_pg_driver_tests_skip_without_the_database_variable():
    """The case the order named: plain `pytest` with the variable unset gave 3 failures (KeyError) here."""
    done = _run_pg_driver_tests({})
    out = done.stdout
    assert done.returncode == 0, out[-1500:]
    assert " failed" not in out and "KeyError" not in out, out[-1500:]
    assert "skipped" in out and f"{NAME} not set" in out, out[-1500:]


def test_the_pg_driver_tests_fail_with_the_backend_message_under_the_fail_rule():
    """Under the fail rule a missing database is a failure that says so, not a KeyError."""
    done = _run_pg_driver_tests({"HADAVIN_REQUIRE_PG": "1"})
    out = done.stdout
    assert done.returncode != 0, out[-1500:]
    assert "KeyError" not in out, out[-1500:]
    assert f"require_backend: postgres: {NAME} not set" in out, out[-1500:]
