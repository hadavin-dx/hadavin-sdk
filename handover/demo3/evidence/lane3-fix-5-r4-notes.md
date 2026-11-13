# lane3-fix-5 round 4 notes (builder B5d)

Patch: lane3-fix-5-r4.patch (full diff from f3c39cf8), sha256 97a01910c3a79ab13aa858f79e2f89433aa06891b3a274d45d108423e7a9f4e2

## Rung table
| Component | Rung | Why lower rungs were rejected |
|---|---|---|
| Which process reset.sh may stop | 7, one small shell fix at the choke point (the `case` in scripts/reset.sh) plus tests | Rungs 1-6 (reuse, client tool, no-code, MCP, RAG, model features) cannot decide which process id to kill; no existing core module does this. |
| Test ports | 1, reuse: extends tests/support.py (free_port stays; held_port added) | free_port closes its socket at once, which is the race. |

## Items
| # | Finding | What changed | Evidence |
|---|---|---|---|
| 1 | MAJOR ruff I001 | In tests/test_reset_scripts.py and tests/test_reset_ps_width.py every `X as Y` is its own `from support import X as Y` line; plain names in one statement. Order follows ruff's rule by reading (not run: ruff is CI-only). | uncertain: not run |
| 2 | glob matched marker anywhere | reset.sh now needs `python` earlier in the line and the marker as its own word: ` -m lead_desk.server` or ` -m demo_only.fakes_server`, at the end or followed by a space (/proc lines end with a space, ps lines do not). start_all.sh runs `python -m lead_desk.server` and `python -m demo_only.fakes_server --outbox ...`; a test pins both lines. Tests: 8 real-process cases (`vim lead_desk.server.py`, `-m lead_desk.server.py`, `.serverx`, `xlead_desk.server`, `--x=lead_desk.server`, old bare word) must survive and give exit 6; real shapes (desk, demo server) still stopped; 13 stand-in-`tr` lines test both forms (with and without trailing space, a path with a space, `vim -m lead_desk.server` with no python). | old script: all 8 fail |
| 3 | multi-token pid file | Decision: a pid file that is not one plain number (no leading zero, not 0) is stale: nothing is looked up or stopped, the file is deleted, the reset goes on (reset_check still refuses if the desk still holds the lock or port). Comment in reset.sh. Tests: "123 456", "123\n456\n", "self", "../1", "0", "007", and a REAL running desk named in a two-number file (5 shapes) is not stopped. | old script: 007 and 3 of 5 two-number cases fail |
| 4 | fails-before of integration tests | Ran the final tests against the ORIGINAL scripts/reset.sh from f3c39cf8: 19 failed (list in raw/lane3-fix-5-r4-fails-before-list.txt, plus the 8 marker cases above, run separately without COLUMNS: 8 failed). The 3 COLUMNS=80 integration tests fail on the original (confirmed by running, not by reading). | raw files |
| 5 | skipif and fragile assert | Redundant skipif removed. The `"pytest" in out` assertion now compares with the real /proc/self/cmdline (NULs as spaces) plus newline. | pass |
| E7-1 | tests/support.py comment contained "our" (wording test) | Reworded the noqa comment; tests/test_portal_wording_and_masking.py run: passed. | pass |
| E7-2 | flake: port 43217 answered under -n 2 | Root cause: free_port() binds port 0 and closes at once, so the operating system can hand the number to a parallel test that then listens on it. Fix: held_port() keeps the socket bound (not listening, so nothing answers) until an autouse fixture releases it; both reset test files use it. Unit test of held_port added. | 10 runs each under -n 2 and -n 4, all pass (raw/lane3-fix-5-r4-xdist-proof.txt) |
| E7-3 | fails-before per changed behaviour | see items 2 and 3 | |
| hygiene | a test line used an absolute /opt path, caught by test_hygiene | changed to a relative one | test_hygiene passes |

## Not done or uncertain
- xdist proof is 10 runs per mode, not 20 (the 14:35Z stop). The old failure itself was not reproduced here (it is rare); the cause is by reading plus the unit test.
- ruff / format / mypy / bandit not run (CI only); import order and line wrapping follow ruff by reading.
- macOS/BSD ps, busybox, hidepid /proc, Windows reset.ps1 (its own `-match 'lead_desk\.server|...'` substring is unchanged and has the same wide-match weakness; not in this patch).
- A venv path with the word "python" only in a directory is accepted as interpreter (the rule is "python appears earlier in the line"); `python -mlead_desk.server` (no space) is not recognised.

## Final run on the final head
Full suite, `q1-xdist-venv ... pytest tests -q -n 4` (NOT the serial run: serial needs 21 min, hard stop was 14:35Z): 3734 passed, 200 skipped, rc=0, 14:34Z. Log: raw/lane3-fix-5-r4-full-suite-n4.log. Earlier head runs had 1 failure (hygiene, fixed above). git apply --check of r4 after claims-stack-on-f3c39cf8, lane3-fix-3-r5, lane3-fix-1-r4 (applied in that order): rc=0.
