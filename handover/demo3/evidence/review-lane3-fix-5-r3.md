# REV-5c: fresh egm-codebase-details review of lane3-fix-5-r3.patch (read-only, nothing executed by the reviewer)
Saved by lane 3 lead from the reviewer's inline report (13:5xZ).

0 blocker, 1 major (probable CI failure, 85 percent sure by reading), 4 minor, 1 nit.
Not checked by the reviewer: no test, ruff, mypy, bandit or shellcheck run; whether procps ps cuts at COLUMNS into a pipe (fails-before of the 3 integration tests is by reading); macOS/BSD/busybox ps, hidepid /proc, Windows.

1. MAJOR ruff I001: tests/test_reset_scripts.py:15-23 and tests/test_reset_ps_width.py:13-21 mix `X as Y` members and plain names in one `from support import (...)`; ruff default combine-as-imports=false wants each `as` import on its own line (repo style: tests/test_codeant_fakes.py:18-19). Fix: plain names in one statement, each `as` name its own `from support import X as Y`, or un-alias.
2. MINOR scripts/reset.sh:48,51: the glob `*lead_desk.server*|*demo_only.fakes_server*` matches the marker anywhere in the command line; a reused pid of an unrelated program with that text in an argument is killed. Patch widens exposure slightly (full line now always read). Fix: match the marker as its own word (e.g. `* -m lead_desk.server*`).
3. MINOR reset.sh:30-41,48-49: `proc_line` global (harmless); multi-pid pid file ("123 456", two lines) reaches ps -p, kill gets one invalid argument, `|| true` hides it, pid file removed, desk not stopped (reset_check.py port/lock is the only guard). No wrong-process kill. Optional test "123 456". "self" and "../1" blocked by the ^[0-9]+$ guard but not tested.
4. MINOR tests/test_reset_ps_width.py:314-327: 6 of 7 pid-file values also pass on the OLD script (regression guards); the 5 proc_args unit tests fail on old only because the function does not exist; real fail-on-old evidence = the 3 integration tests (lines 182, 207, 229), which rely on ps honouring COLUMNS; confirm with a run on the old script.
5. MINOR test_reset_ps_width.py:315 skipif(WINDOWS) duplicates module pytestmark line 166.
6. NIT lines 291, 298, 306: assert "pytest" in out or "python" in out; fragile for unusual launchers.
CI-class by reading: no line over 120 in changed hunks; no unused imports; no new noqa (1 S603 moved); test_shell_single_bracket passes for the new [[ ]] lines; ToolMissing(SkipTest) reports as skip.
