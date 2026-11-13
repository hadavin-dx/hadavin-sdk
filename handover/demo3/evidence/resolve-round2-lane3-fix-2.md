# egm-resolve round 2 for lane3-fix-2-r2.patch (saved by lane 3 lead from the resolve answer; Opus 5.5)
Inputs: review-lane3-fix-2-r2-design.md (REV-2c), review-lane3-fix-2-r2-codedetails.md (REV-2d). Product-code path, no round cap.
Counts: accepted 11, contested 1, escalated 0, declined 2.

Verified by reading (nothing edited, no desk started):
- python 3.12.3 Path.is_dir ignores only errno 2, 20, 9, 40; EACCES re-raised. Unguarded probes: desk.py:329,332,334 (book_problem, runs at server.py:1146 BEFORE the mkdir try/except at 1149-1153), config.py:253, crm_hubspot.py:196, smtp_provider.py:135.
- Added lines over 120 (diff, not file): config.py:74,79,84; tests/test_env_numbers.py:359; tests/test_live_claude.py:255; tests/test_settings_lane3.py:165,233,323,518 (518 missed by REV-2d). Others in the whole-file scan are base lines.
- contract.md:133-143 start-up order stale (no unopenable lock file, no check_secret_files/exit 4, only :memory: for db_path, no mkdir step). Real order in server.main: settings+public bind, book_problem, mkdir, lock, adapters+check_secret_files, Desk, bind.
- _is_bind_name only called from Config.__post_init__ (config.py:555); unpaired "[::1" / "::1]" pass on purpose (tests/test_bind_refusals PUBLIC).
- lockfile.py has no unlink: flock dropped at process exit; leftover .lock is normal after any exit -> REV-2d #5 CONTESTED.
- tests/test_path_confinement.py ~573-600 writes real key files and answers "n"; tests/test_real_check_dry.py:462 uses a missing key path but ends EXIT_STOPPED before a desk is built. By reading only; E5 full suite is the proof.
- limits.md:117 exit-code bullet is rewritten by both fix-1-r2 and fix-2-r2; fix-1 test requires the phrase "cannot reach the demo servers" in it. fix-1-r4.patch now exists.

Resolution table (item | decision | change):
1 PermissionError on is_dir/exists (REV-2c#1, REV-2d#2, major) | FIX | one helper path_kind(path)->folder|file|absent|unreadable (stat; ENOENT/ENOTDIR/ELOOP = absent; other OSError = unreadable), used at all 4 sites; fail closed with a fixed text naming the setting, no path, exit 4; tests monkeypatch Path.stat so they run as root; keep chmod test.
2 9 added lines over 120 (REV-2d#1, major) | FIX | wrap/shorten exactly those 9, no noqa; awk on diff-added lines and whole new test file.
3 contract.md start-up order stale (REV-2d#3) | FIX | rewrite steps 2-4, add mkdir step, exit 2/1/4 per the real order; fix limits.md:58, README ~90, docs/tests.md; add doc test pinning the step order.
4 bind brackets/punctuation (REV-2c#2, REV-2d#4) | FIX | strict check on from_env path only (one pair of brackets around the whole name; every label has a letter or digit); Config(bind="[::1") stays public; document non-ASCII refusal.
5 .lock left after key-file refusal (REV-2d#5) | CONTEST | lockfile.py has no unlink; same after clean stop.
6 in-process main() tests leak lock handle (REV-2c#3, REV-2d#6) | FIX | close the handle (shared fixture); label regression-guard tests.
7 live key reader lenient (REV-2d#7) | FIX | LiveQualifier._load_key reuses read_secret_file one-line/size rule; check tests/test_live_claude for multi-line reliance; update settings.md.
8 DESK_LIVE_ALLOW_ANY_BASE_URL true/1 now refused (REV-2c#4) | FIX (verify) | grep scripts/n8n/docs for true/1; record hits.
9 key check only after servers reachable (REV-2c#5) | DECLINE | documented trade-off.
10 existing tests under the new start check | FIX (evidence) | E5 full suite.
11 unrelated doc hunks unverified (REV-2c#7) | FIX | quote the code line for each (outbox reminders, "Hide names" label, n8n scrub line count, portal # route, fakes_server comment); remove what cannot be proven; keep hunks separate.
12 conflict with fix-1 at limits.md:117 | FIX | one merged exit-code bullet containing fix-1's phrase and fix-2's text; variants: (a) on f3c39cf8, (b) after lane3-fix-1-r4.patch, (c) for the claims stack; git apply --check each.
13 root skips the real-permission test | FIX | covered by item 1; state it unverified as root.
14 verified-good notes | DECLINE.

Work order B2c: worktrees (r2 + r4) -> item 1 + tests (fails-before list) -> items 4, 7, 6, 8 -> items 3 and 11 -> item 2 last (awk) -> item 12 variants (apply --check) -> hygiene, affected family, one full suite -> notes with fails-before list, rung table, sha256, commands + exit codes. No ruff/mypy/bandit.
Fresh final review checks: helper used at every site (search for bare .is_dir/.exists on setting paths); fixed texts, no path leak; strict bracket check only on from_env; contract order matches server.main line by line; live key rules; merged bullet keeps the fix-1 phrase; variants apply; item 5 justified; no new noqa, no added line over 120.
