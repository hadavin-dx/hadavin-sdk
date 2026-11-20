"""Exit codes of the mutant script: a failing run never exits 0, and a mutant whose killer file is not in TESTS is named.

``tests/mutation_exit.py`` holds the helpers; they are driven here in a subprocess with a fake mutant list. The real
mutant list is only imported (never run): every killer file it names must be in its TESTS.
"""

import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

from tests import endpoint_mutants as em
from tests.mutation_exit import check_test_files

ROOT = Path(__file__).resolve().parents[1]


def drive(body: str):
    code = (
        "import sys\nfrom tests.mutation_exit import check_test_files, exit_guard\n"
        + textwrap.dedent(body)
    )
    return subprocess.run(  # noqa: S603  # our own interpreter and a text of this file, no shell
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        cwd=ROOT,
    )


def test_every_mutant_killer_file_is_in_tests():
    assert check_test_files(em.M, em.TESTS) == []
    for m in em.M:
        assert not m.test_file or m.test_file in em.TESTS, (m.name, m.test_file)
        assert not m.test_file or (ROOT / m.test_file).is_file(), (m.name, m.test_file)
    assert {em.T13, em.T14} <= set(em.TESTS)


def test_the_check_names_the_mutant_and_the_file():
    fake = [
        SimpleNamespace(name="GX fake", test_file="tests/x.py"),
        SimpleNamespace(name="GY", test_file=""),
    ]
    (msg,) = check_test_files(fake, ["tests/other.py"])
    assert "GX fake" in msg and "tests/x.py" in msg and "missing from TESTS" in msg


def test_a_missing_killer_file_exits_2_with_a_clean_message():
    done = drive(
        """
        from types import SimpleNamespace
        def main():
            bad = check_test_files([SimpleNamespace(name="GX fake", test_file="tests/x.py")], ["tests/other.py"])
            if bad:
                print("\\n".join(bad), file=sys.stderr)
                sys.exit(2)
        sys.exit(exit_guard(main))
        """
    )
    assert done.returncode == 2, (done.returncode, done.stderr[-300:])
    assert "GX fake" in done.stderr and "tests/x.py" in done.stderr
    assert "Traceback" not in done.stderr


def test_an_uncaught_exception_is_a_nonzero_exit_with_the_traceback():
    done = drive(
        """
        def main():
            raise RuntimeError("the unmutated copy does not pass its tests")
        sys.exit(exit_guard(main))
        """
    )
    assert done.returncode == 1, (done.returncode, done.stderr[-300:])
    assert "RuntimeError" in done.stderr and "does not pass its tests" in done.stderr


def test_a_value_error_of_the_validation_is_a_nonzero_exit():
    done = drive(
        """
        def main():
            raise ValueError("mutant 'G34': test_file 'x' is not one of the copied tests")
        sys.exit(exit_guard(main))
        """
    )
    assert done.returncode == 1 and "ValueError" in done.stderr


def test_a_normal_end_and_an_explicit_exit_keep_their_codes():
    assert drive("sys.exit(exit_guard(lambda: None))").returncode == 0
    assert drive("sys.exit(exit_guard(lambda: sys.exit(3)))").returncode == 3


def test_a_stale_anchor_exits_2_and_names_the_mutant():
    done = drive(
        """
        from types import SimpleNamespace
        from tests import endpoint_mutants as em
        def main():
            fake = SimpleNamespace(name="GZ gone", file="src/hadavin_sdk/triggers/server.py", old="no such text \\x00")
            problems = em.check_anchors([fake])
            if problems:
                print("\\n".join(problems), file=sys.stderr)
                sys.exit(2)
        sys.exit(exit_guard(main))
        """
    )
    assert done.returncode == 2, (done.returncode, done.stderr[-300:])
    assert "GZ gone" in done.stderr and "occurs 0 times" in done.stderr
    assert "Traceback" not in done.stderr


def test_a_failing_unmutated_baseline_exits_1_naming_the_cause():
    done = drive(
        """
        def baseline():
            raise RuntimeError("the unmutated copy does not pass its tests")
        def main():
            baseline()
            print("mutants ran")
        sys.exit(exit_guard(main))
        """
    )
    assert done.returncode == 1, (done.returncode, done.stderr[-300:])
    assert "does not pass its tests" in done.stderr and "mutants ran" not in done.stdout


def test_a_runner_exception_in_a_later_step_is_exit_1_after_earlier_output():
    done = drive(
        """
        def main():
            print("first mutant done", flush=True)
            {}["missing"]
        sys.exit(exit_guard(main))
        """
    )
    assert done.returncode == 1 and "first mutant done" in done.stdout
    assert "KeyError" in done.stderr
