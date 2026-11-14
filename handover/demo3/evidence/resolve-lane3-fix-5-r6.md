# egm-resolve (Opus, Skill egm:egm-resolve, non-interactive) for fix-5 r6, saved by lane3 2026-11-14 ~05:07Z
Inputs: review-lane3-fix-5-r6-design.md (0/2/5/5) + review-lane3-fix-5-r6-codedetails.md (0/1/5/5). Tree rv-fix5r6. Read-only; nothing run.
COUNTS: 24 rows: 21 PROPOSE FIX, 1 CONTEST (row 21), 2 ESCALATE (row 2b Windows run = impossible-now 2(c); row 23 duplicate book fixture = stack step, lead decision A1), 0 DECLINE. Row 15 raises bash minimum to 4.4 (behaviour change, lead may veto).
CHECKS (read): D-M1 TRUE (sequential loop: desk stopped + pid file removed at reset.sh:84-87,103 / reset.ps1:65-68,76 before fakes looked at; refusals 5/6/7 say "nothing was stopped or deleted"). reset.ps1:86-87 Test-Path/Remove-Item without -LiteralPath TRUE. reset.ps1:60 SilentlyContinue TRUE. Port overlap TRUE by arithmetic (8 workers: gw7 62344-65535; restarted gw8 total 9 width 2837 -> 62696-65532). conftest.py:167-176 duplicate book TRUE. `which pwsh powershell` empty; xdist not in py313-venv (not a repo dependency). `$` before newline: not applicable (text is .Trim()med at reset.ps1:55); .NET working-directory part TRUE.
TABLE (# item | sev | decision | change):
1 D-M1/C-m-3 non-atomic refusal | Major | FIX | two passes in sh and ps1: pass 1 classifies both pid files (absent/stale/ours/refuse6/refuse7), no side effects; pass 2 stops, waits, deletes. Exit 5 message names what was already stopped. "nothing was stopped" only on pass-1 refusals. README 90/92. Tests: desk.pid=real stub desk + fakes.pid=other program -> 6, stub alive, desk.pid kept; fakes.pid folder -> 7; stubborn process -> exit 5 names stopped. ps1 text pins + Windows-only runtime tests.
2a D-M2/C-M-1 README states Windows as fact | Major | FIX | one README sentence "checked by reading and text tests only; not run on Windows in this build (2026-11-14); run WINDOWS-RUN-1"; split README:115 (measured vs not); notes "Open: A-M2" -> dated owner step; keep pins incl. start_all.ps1 -m and module words.
2b run of ps1 for real | Major residue | ESCALATE 2(c) impossible-now | lead's Windows run of WINDOWS-RUN-1 on final stack tree. Builder: one 10-min attempt to get pwsh; if it works run Parser::ParseFile on both scripts and record; else record refusal.
3 -LiteralPath reset.ps1:86-87 | Minor | FIX | Test-Path/Remove-Item -LiteralPath -Force -ErrorAction Stop; multi-line pin; Windows-only test with "[" in folder.
4 WMI failure | Minor | FIX | Get-CimInstance -ErrorAction Stop in try/catch; failure -> "process N could not be looked up; nothing was stopped or deleted" exit 6 (pass 1); README exit-6 text.
5 port block overlap on restart | Minor | FIX | worker_port_range: total = count if count else number+1; slot = number % total. Tests: 8 workers gw7 vs gw8; property count 1..64, number 0..2*count.
6 blocks overlap OS ephemeral; direct-bind sites | Minor | FIX | _RANGE_START 20000; route direct bind((HOST,0)) sites through helper; guard test finds remaining ones; notes: guarantee = held-vs-free only.
7 no real xdist run | Minor | FIX | scratch venv with pytest-xdist, -n 4 on port + reset tests, raw/b16-xdist.log; if install fails, state error.
8 pin blind spots | Minor | FIX | multi-line regex pins (-not, $raw = $null, -LiteralPath, two-pass order, exit 6 on lookup failure); one mutant per pin; Windows-only runtime tests (folder->7, long file->stale, python -M->6).
9 helper aliasing | Minor | FIX | import held_port under own name; two-distinct-ports helper into support.py.
10 start_all pin docstring | Minor | FIX | reword (module names and bare python only); launcher/Start-Process quoting step on WINDOWS-RUN-1.
11 "64 characters" | Nit | FIX | "64 bytes" (README:93, test name, sh comment; LC_ALL=C read or say difference).
12 vocabulary | Nit | FIX | process number / pid file / lead book; split exit-3 clause.
13 Write-Host vs stderr | Nit | FIX | ps1 refusals to stderr.
14 parity | Nit | FIX | ps1 ^ without \s*; pid link to folder -> exit 7 in both; message "(a folder, or a file that is locked)".
15 bash 4.1-4.3 no mapfile -d | Nit | FIX | minimum 4.4 in script, README:47, guard test.
16 _GIVEN_FREE not cleared | Nit | FIX | clear in finally.
17 worker_of_thread dict | Nit | FIX | per-test local.
18 "at once" test name; "range 0" mutant missing from log | Nit | FIX | rename; record mutant.
19 Read may return <64 before EOF | Nit | FIX | read loop to EOF up to 64.
20 BOM/UTF-16 pid file | Nit | FIX | strip UTF-8 BOM; UTF-16 stays stale (reset_check refuses 3/4 if desk alive); README sentence; pin.
21 `$` before final newline | Nit | CONTEST | $text is .Trim()med at reset.ps1:55 before the match; $ours ends (\s|$).
22 .NET working directory | Nit | FIX | absolute pid path via Convert-Path/GetFullPath(Join-Path (Get-Location).Path ...).
23 duplicate book fixture | Minor | ESCALATE to stack step (A1) | stack builder deletes conftest.py:166-176, checks fix-9 fixture yields same desk.sqlite3/desk.log "keep me".
24 19-mutant first-run survivors (3) | Minor | FIX | notes list survivors by name; new mutants for rows 1,3,4,5,8,20 in raw/b16-mutation.log with survivors before fix-up.
WORK ORDER (B16, fix-5 r7): start from lane3-fix-5-r6.patch on claims-series tree (f3c39cf8); failing tests first (rows 1,3,4,5,8,9,20,22) and save the old-code failures; implement rows 1,14 in both scripts, then 3,4,19,20,22; rows 5,6,9,16,17; docs rows 2a,10-13,15; row 2b attempt; row 7 xdist run; row 24 mutation; ONE full run on the final head (3.13, DPLD_REQUIRE_SCAN=1, gitleaks, no data/, clone WITHOUT origin/n8n-evidence-rerun), raw log saved; no ruff/mypy/bandit; cut lane3-fix-5-r7.patch + notes; git add -A, no commit.
FINAL REVIEW MUST CHECK: no side effect before pass 1 ends and every "nothing was stopped" true on all paths in both scripts; sh/ps1 same exit code and wording per README row; port blocks disjoint for live and restarted workers 1-64, new range start, no direct bind left; each new test fails on r6 (saved output) and no blind single-line pin; README says Windows never run; book duplicate left to the stack; bash 4.4 consistent; full-run log from clone without n8n ref and no data/.
