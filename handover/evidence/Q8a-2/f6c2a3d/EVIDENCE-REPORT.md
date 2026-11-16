<!-- full hand-back report of sub-agent ab1486e8, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

EVIDENCE RUNNER report, Q8a-2 head f6c2a3d9198defbee2d01ee4979a5d6e75607c8a (fix batch 2). Raw numbers only, no verdict. RESULTS.md has the full table with file names.

**Files:** /home/user/hadavin-sdk/handover/evidence/Q8a-2/f6c2a3d/ (RESULTS.md, the raw logs, junit XML and scripts/). The same raw files are also in /home/user/build/evidence-raw/Q8a2-f6c2a3d/. The checkpoint note is /home/user/build/checkpoints/EV-Q8a2-f6c2a3d.md. Nothing was pushed. I stopped my PostgreSQL on port 56277, and no processes of mine are left running. The worktrees /home/user/build/EV-Q8a2-f6c2a3d and /home/user/build/EV-Q8a2f-main are still on disk.

**What failed or went wrong (read first)**
1. **Full suite, exit 1:** `1 failed, 10766 passed, 1 skipped, 28 deselected` (junit tests=10768, 398 s).
   - The failure is `tests/demo_askdata/test_validate_harm.py::...[dblink-connect]`, a `SqlclientUnableToEstablishSqlconnection` on the default socket /var/run/postgresql.
   - It comes from my set-up: I started my PostgreSQL without PGHOST and PGPORT in the server's own environment, and that test connects from inside the server.
   - The file is not in the branch diff.
   - After restarting PostgreSQL with PGHOST and PGPORT set, that file alone gave exit 0, `253 passed`. I did not run a second full suite.
2. **Fail-before on origin/main 2a8c2aac:** `tests/test_p7_tick.py` does not import on main (`cannot import name 'handle_action'`, exit 2, 0 tests ran). With the other three head test files over main's `src`:
   - Exit 1, 94 failed, 246 passed.
   - Per file: callback 63 failed / 9 passed, lockin guard 29 / 196, capabilities 2 / 41.
   - No collection error. The worktree was restored.
3. **Server stderr during the hostile inputs:** 6 lines in total, none of them a traceback.
   - Each handler failure gives one line `a request ended with an error: AttributeError`.
   - A client reset right after a correctly signed click gives one line `... ConnectionResetError while handling AttributeError`, logged at ERROR level.
4. **Guard plants:** 4 plants gave an empty result from every scan: `# slack`, a docstring naming Slack, and the SQL comments `-- slack` and `/* slack */`. The other 36 Python plants, the 2 GCS table plants and 4 of the 6 SQL plants were each reported by at least one scan. Aliased, relative and `async def` plants were all reported.
5. **Step 8, variant A (serial opening of the 50 connections):** opening them took 7.2 s (200 took 30.7 s). Early connections were already closed by the 10 s bound before the last ones were open. Variant B (parallel opening) is the cleaner run; both are kept.
6. Machine load average was 3.9 to 5.9 on 4 cores during all runs, so timings are not quiet-machine numbers.

**Table summary**

| # | command | exit | result |
|---|---|---|---|
| 1 | head sha check | 0 | f6c2a3d9, worktree clean |
| 2 | full pytest `-m "not live and not perf"` | 1 | 1 failed (item 1), 10766 passed |
| 3a | ruff check | 0 | All checks passed |
| 3b | ruff format --check | 0 | 323 files already formatted |
| 3c | bandit -ll -r src tools | 0 | No issues identified |
| 3d | tools/scan_repo.py | 0 | no output |
| 3e | suppression grep on the diff (noqa/nosec/type: ignore) | 1 (no match) | 0 hits |
| 3f | gitleaks on origin/main..HEAD | 0 | no leaks found |
| 4 | stage_mutants.py | 0 | `37 of 37 good; problems: []` |
| 5 | fail-before over clean origin/main | 1 | 94 failed, 246 passed (item 2) |
| 6 | hostile inputs, fake and Slack kinds | 0 | see below |
| 7 | guard plants (44 in all, including SQL) | 0 | 4 all-empty (item 4) |
| 8 | 50 held slow connections | 0 | see below |

**Step 6 (hostile inputs).** Both channel kinds gave the same status for every case.
- Content-Length at the right path:
  - 400: empty, header twice, `-5`, `+5`, `+9`, Arabic-Indic and fullwidth digits, `0x10`, `1_0`, `9.0`, `1e1`, `9 ` (trailing space).
  - 413: 12, 13, 4000, 4301 and 10000 digits, and 65537.
  - 401: ` 9` (leading space), `0`, `0009`, and no header.
  - No answer, connection closed after 2.0 s: 65536 with only 9 bytes sent.
- Content-Length at a wrong path: 404 for every form tried.
- Slow first line, slow headers, slow body, short body, and connect-and-send-nothing: no status, the server closed the connection at the bound.
- Resets: no stderr output, except the one case in item 3.
- Header floods: 99 to 5000 extra headers and a 70000-byte header value gave 431, and a 70000-byte request line gave 414.
- Request line: tab, vertical tab, 0x1C, two spaces and the no-break space all gave 401 (they reach the signature check). Doubled and tripled slash, percent-encoded path, query, trailing slash and absolute form all gave 404.
- Handler failure with store None: 500 twice, one stderr line each, no traceback.
- A str-subclass `callback_path` (including one whose `__eq__` is always True): `serve()` raised `ConfigError`.
- Non-loopback connections attempted: 0.

**Step 8 (variant B, default 10 s bound).**
- With 50 held connections, fast requests were all answered with the expected status (200 or 401). Medians were 1.5 to 3.4 ms signed and 0.5 to 0.8 ms wrong-signature.
- The largest single value was 1017.7 ms, one signed request while the 50 connections were still being opened.
- With 200 silent connections held, the signed median was 2.0 ms.
- After the bound, 50 of 50 held connections in each of the three patterns (silent, short body, partial first line) were closed by the server, and threads returned to baseline.

**NOT RUN**
- A real-store signed approval over the socket for the Slack kind. The real-store fixture builds the fake kind only, so the Slack kind was probed with store None.
- A second full-suite run (not asked for).
- The merge-tree and guard run against the Q8a-1 branch (not in this brief's list).
- CI, CodeQL, SonarCloud and CodeRabbit.
- I did not review the diff and fixed nothing.
