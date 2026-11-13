"""The ONE helper the tests use to start a program (git, node, chown, chmod, this interpreter) is
`run_fixed` of
`tools/fixed_run.py`: a fixed list of arguments, never a shell string, the program looked up on the
PATH and run by its full path.
There is one place in the project that starts a program, so the project's subprocess rule is never waived."""

from __future__ import annotations

from tools.fixed_run import run_fixed as run

__all__ = ["run"]
