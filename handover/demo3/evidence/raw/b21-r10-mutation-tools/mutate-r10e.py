import subprocess, sys, pathlib, shutil, difflib
SRC = pathlib.Path("/home/user/work/b21-tree"); part = sys.argv[1]; which = int(sys.argv[2]); n = int(sys.argv[3])
RAW = pathlib.Path("/home/user/hadavin-sdk/handover/demo3/evidence/raw")
OUT = RAW / f"b21-r10-mutants-re3{part}.log"; DIFFS = RAW / f"b21-r10-mutant-diffs-re3{part}.txt"
TMP = pathlib.Path(f"/home/user/work/b21-logs/mut/tmp10-{part}"); TMP.mkdir(exist_ok=True)
WORK = TMP / "tree"
if WORK.exists(): shutil.rmtree(WORK)
shutil.copytree(SRC, WORK, ignore=shutil.ignore_patterns(".git", "data", "__pycache__"))
PY = "/home/user/work/py313-venv/bin/python"
FILES = ["tests/test_reset_order_and_words.py", "tests/test_reset_scripts.py", "tests/test_reset_ps1_pid_rules.py", "tests/test_reset_ps1_links.py", "tests/test_reset_ps_width.py", "tests/test_port_helpers.py", "tests/test_http_guard.py"]
SH, PS, PB, RD = "scripts/reset.sh", "scripts/reset.ps1", "tests/port_blocks.py", "README.md"
M = [
 # -- the 36 earlier mutants, re-pointed at the r8 text
 ("sh pass 1 also stops (kill added in pass 1)", SH, 'number[$name]="$pid"', 'number[$name]="$pid"; kill "$pid" 2>/dev/null || true'),
 ("sh exit 5 message forgets what was stopped", SH, 'stopped="$stopped, $name (process $pid)"', 'stopped=""'),
 ("sh byte order mark not skipped", SH, "pid=\"${pid#$'\\xef\\xbb\\xbf'}\"", ":"),
 ("sh folder check dropped", SH, '[[ -d "$pidfile" ]]', '[[ -d "$pidfile.none" ]]'),
 ("sh read loop reads nothing", SH, "tries < 67 &&", "tries < 0 &&"),
 ("sh read not in C locale", SH, "local LC_ALL=C chunk", "local chunk"),
 ("sh version guard minor < 4 -> < 3", SH, "bash_minimum=(4 4)", "bash_minimum=(4 3)"),
 ("sh pid files not deleted (pass 3)", SH, 'if ! rm -f -- "$pidfile" 2>/dev/null; then', 'if ! true; then'),
 ("sh ours judged stale", SH, "kind[$name]=ours", "kind[$name]=stale"),
 ("ps1 final delete without -LiteralPath", PS, "Remove-Item -LiteralPath $f -Force -ErrorAction Stop", "Remove-Item $f -Force -ErrorAction Stop"),
 ("ps1 final Test-Path without -LiteralPath", PS, "if (Test-Path -LiteralPath $f)", "if (Test-Path $f)"),
 ("ps1 process lookup errors silenced", PS, "-Filter \"ProcessId = $procId\" -ErrorAction Stop\n            } catch {", "-Filter \"ProcessId = $procId\" -ErrorAction SilentlyContinue\n            } catch {"),
 ("ps1 lookup failure no exit 6", PS, "could not be looked up; nothing was stopped or deleted\")\n                exit 6", "could not be looked up; nothing was stopped or deleted\")"),
 ("ps1 Convert-Path dropped", PS, "$full = Convert-Path -LiteralPath $pidFile", "$full = $pidFile"),
 ("ps1 byte order mark byte changed", PS, "$buffer[0] -eq 0xEF", "$buffer[0] -eq 0xEE"),
 ("ps1 folder exit 7 -> 1", PS, "yourself)\")\n            exit 7", "yourself)\")\n            exit 1"),
 ("ps1 refusal back to Write-Host", PS, "[Console]::Error.WriteLine(\"refused: process $procId did not stop", "Write-Host (\"refused: process $procId did not stop"),
 ("ps1 pattern not anchored (\\s* back)", PS, "$ours = '^' + $interpreter", "$ours = '^\\s*' + $interpreter"),
 ("ps1 Stop-Process in pass 1", PS, "$plan += [pscustomobject]@{ Name = $name; PidFile = $pidFile; ProcId = $procId; Ours = $true }", "$plan += [pscustomobject]@{ Name = $name; PidFile = $pidFile; ProcId = $procId; Ours = $true }; Stop-Process -Id $procId"),
 ("ps1 Remove-Item catch drops exit 7", PS, "have been stopped)\")\n        exit 7", "have been stopped)\")"),
 ("ps1 [Pp]ython -> python (interp 1)", PS, "'(\"([^\"]*[\\\\/])?[Pp]ython", "'(\"([^\"]*[\\\\/])?python"),
 ("ps1 exit 5 forgets already stopped", PS, "$note = if ($stopped) { \" (already stopped: $stopped)\" } else { '' }", "$note = ''"),
 ("ps1 cap -ge 64 -> -gt 64", PS, "($count - $from) -ge 64", "($count - $from) -gt 64"),
 ("support width 5000 -> 6000", PB, "_RANGE_WIDTH = 5000", "_RANGE_WIDTH = 6000"),
 ("support width ignores count", PB, "width = min(_RANGE_WIDTH, _HALF // total)", "width = min(_RANGE_WIDTH, _HALF // 4)"),
 ("support restart uses first half", PB, "first = _RANGE_START + _HALF + ((number - total) % total) * width", "first = _RANGE_START + (number % total) * width"),
 ("support restart no modulo", PB, "((number - total) % total)", "(number - total)"),
 ("support worker regex too loose", PB, 're.fullmatch(r"gw(\\d+)"', 're.match(r"gw(\\d+)"'),
 ("support every worker gets range 0", PB, "first = _RANGE_START + number * width", "first = _RANGE_START"),
 ("support range start back to 40000", PB, "_RANGE_START = 20000", "_RANGE_START = 40000"),
 ("support last = first+width", PB, "return first, first + width - 1", "return first, first + width"),
 ("support given-free not cleared", "tests/support.py", "_GIVEN_FREE.clear()", "pass"),
 ("support serial uses range always", PB, "if block is None:", "if False:"),
 ("support missing count not max", PB, "else _MAX_WORKERS", "else number + 1"),
 ("tests: a direct bind to port 0 added", "tests/test_http_guard.py", "with bound_socket() as s:", "with __import__('socket').socket() as s:\n        s.bind((\"127.0.0.1\", 0))\n    with bound_socket() as s:"),
 # -- new for round 8
 ("sh pass-2 recheck dropped", SH, 'if ! is_ours "$pid" "$(proc_args "$pid" || true)"; then', 'if false; then'),
 ("sh recheck exit 6 -> 1", SH, "and nothing was deleted${stopped:+ (already stopped: $stopped)}\" >&2\n      exit 6", "and nothing was deleted${stopped:+ (already stopped: $stopped)}\" >&2\n      exit 1"),
 ("sh reset_check dropped", SH, "python scripts/reset_check.py || exit $?", "true"),
 ("sh reset_check failure ignored", SH, "python scripts/reset_check.py || exit $?", "python scripts/reset_check.py || true"),
 ("sh dangling link not seen", SH, '[[ -e "$pidfile" || -L "$pidfile" ]]', '[[ -e "$pidfile" ]]'),
 ("sh 64 -> 65 after the mark", SH, "if (( ${#pid} >= 64 )); then pid=\"\"; fi", "if (( ${#pid} >= 65 )); then pid=\"\"; fi"),
 ("sh read 64 instead of 67", SH, "-N $((67 - ${#pid}))", "-N $((64 - ${#pid}))"),
 ("sh removal sentence changed", SH, "the desk's records and the logs were not deleted", "the logs were not deleted"),
 ("sh folder message changed", SH, "is a folder, not a pid file, so it cannot be removed; nothing was stopped or deleted", "cannot be removed; nothing was stopped or deleted"),
 ("sh old-bash message names a version again", SH, "this bash (${BASH_VERSION}) is too old for this script", "this bash (${BASH_VERSION}) is old"),
 ("check prints to stdout", "scripts/reset_check.py", 'print(f"refused: {reason}; {KEPT}", file=sys.stderr)', 'print(f"refused: {reason}; {KEPT}")'),
 ("check forgets pid files", "scripts/reset_check.py", "nothing was deleted, not even the pid files", "nothing was deleted"),
 ("ps1 recheck dropped", PS, "-not ($again.CommandLine -cmatch $ours)", "$false"),
 ("ps1 recheck exit 6 -> 1", PS, "it was not stopped, and nothing was deleted$note\")\n        exit 6", "it was not stopped, and nothing was deleted$note\")\n        exit 1"),
 ("ps1 Get-Item back to Test-Path", PS, "$found = Get-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue", "$found = if (Test-Path -LiteralPath $pidFile) { Get-Item -LiteralPath $pidFile } else { $null }"),
 ("ps1 buffer 67 -> 64", PS, "New-Object byte[] 67", "New-Object byte[] 64"),
 ("ps1 count not after the mark", PS, "if (($count - $from) -ge 64)", "if ($count -ge 64)"),
 ("ps1 reset_check dropped", PS, "python scripts/reset_check.py\n", "\n"),
 ("ps1 command line trimmed", PS, "$proc.CommandLine -cmatch $ours", "$proc.CommandLine.Trim() -cmatch $ours"),
 ("ps1 removal sentence changed", PS, "the desk's records and the logs were not deleted", "the logs were not deleted"),
 ("ports: session part ignored", PB, "for window in (session_window(block, os.getpid()), block):", "for window in (block,):"),
 ("ports: session part index 0", PB, "index = pid % parts", "index = 0"),
 ("ports: one part only", PB, "_SLICES = 16", "_SLICES = 1"),
 ("ports: part leaves the block", PB, "low = first + index * size", "low = first + index * size + 7"),
 ("tests: HOST defined twice", "tests/support.py", "from port_blocks import _ATTEMPTS, HOST,", "HOST = '127.0.0.1'\nfrom port_blocks import _ATTEMPTS,"),
 ("tests: a direct server bind added", "tests/test_http_guard.py", "with bound_socket() as s:", "__import__('http.server').server.ThreadingHTTPServer((\"127.0.0.1\", 0), None).server_close()\n    with bound_socket() as s:"),
]
R9 = [
 ("r9 M1 length rule outside C locale", SH, '(( ${#pid} >= 64 )) || [[ "$pid" == *[![:print:][:space:]]* ]]', '[[ "$pid" == *[![:print:][:space:]]* ]]'),
 ("r9 M4 NUL size check off", SH, '[[ ! "$size" =~ ^[0-9]+$ ]] || (( ${#pid} != (size < 67 ? size : 67) ))', 'false'),
 ("r9 M5 length rule only", SH, '(( ${#pid} >= 64 )) || [[ "$pid" == *[![:print:][:space:]]* ]]', '(( ${#pid} >= 64 ))'),
 ("r9 M6 read not in C locale", SH, 'local LC_ALL=C chunk="" tries size', 'local chunk="" tries size'),
 ("r9 M7 pass 2 no second look (elif alive -> else)", SH, '    elif alive "$pid"; then', '    else'),
 ("r9 M8 alive: not-permitted counts as gone", SH, '    [[ "$err" == *"not permitted"* ]] || return 1', '    return 1'),
 ("r9 M10 length 64 -> 65", SH, '(( ${#pid} >= 64 ))', '(( ${#pid} >= 65 ))'),
 ("r9 P1 ps1 anchor \\z -> $", PS, "\\A[1-9][0-9]*\\z", "^[1-9][0-9]*$"),
 ("r9 P3 ps1 bad-byte rule only >126", PS, "if ($b -gt 126 -or ($b -lt 32 -and ($b -lt 9 -or $b -gt 13))) { $bad = $true }", "if ($b -gt 126) { $bad = $true }"),
 ("r9 P4 ps1 read loop offset dropped", PS, "$got = $stream.Read($buffer, $count, 67 - $count)", "$got = $stream.Read($buffer, 0, 67)"),
]
R10 = [
 ("r10 ps1 stale LASTEXITCODE not cleared", PS, "$LASTEXITCODE = $null # a stale value from an earlier program must not pass for this call's answer\n", ""),
 ("r10 ps1 null exit code not refused", PS, "$null -eq $checkExit -or $checkExit -notin 0, 3, 4", "$checkExit -notin 0, 3, 4"),
 ("r10 ps1 any other code not refused (raw code passed on)", PS, "$checkExit -notin 0, 3, 4", "$false"),
 ("r10 ps1 crash mapped to the raw code, not 5", PS, "not even the pid files$already\")\n    exit 5", "not even the pid files$already\")\n    exit $checkExit"),
 ("r10 ps1 Continue not restored (P5 kind)", PS, "$ErrorActionPreference = $previousPreference\n", ""),
 ("r10 ps1 Continue dropped (P2 kind)", PS, "$ErrorActionPreference = 'Continue'\n", ""),
 ("r10 ps1 refused setting exit 8 -> 2 (stop wait)", PS, "nothing was stopped or deleted')\n        exit 8", "nothing was stopped or deleted')\n        exit 2"),
 ("r10 ps1 refused setting exit 8 -> 2 (data folder)", PS, "data folder, so nothing was stopped or deleted\")\n    exit 8", "data folder, so nothing was stopped or deleted\")\n    exit 2"),
 ("r10 ps1 config refusal exit 8 -> 1", PS, "was not found), so the database path could not be read; nothing was stopped or deleted\")\n    exit 8", "was not found), so the database path could not be read; nothing was stopped or deleted\")\n    exit 1"),
 ("r10 sh guard without BASH_VERSINFO", SH, "[[ a == a && -n ${BASH_VERSINFO+x} ]]", "[[ a == a ]]"),
 ("r10 start_all guard without BASH_VERSINFO", "scripts/start_all.sh", "[[ a == a && -n ${BASH_VERSINFO+x} ]]", "[[ a == a ]]"),
 ("r10 sh python-missing wording removed", SH, '  127) echo "refused: python was not found', '  1270) echo "refused: python was not found'),
 ("r10 sh exit 5 for crash -> raw code", SH, 'nothing was deleted, not even the pid files${stopped:+ (already stopped: $stopped)}" >&2; exit 5 ;;\nesac', 'nothing was deleted, not even the pid files${stopped:+ (already stopped: $stopped)}" >&2; exit "$check_exit" ;;\nesac'),
 ("r10 sh stop-wait refusal exit 8 -> 2", SH, "no leading zero; nothing was stopped or deleted\" >&2; exit 8 ;;", "no leading zero; nothing was stopped or deleted\" >&2; exit 2 ;;"),
 ("r10 sh data-folder refusal exit 8 -> 2", SH, "nothing was stopped or deleted\" >&2\n  exit 8", "nothing was stopped or deleted\" >&2\n  exit 2"),
 ("r10 sh config refusal back to a traceback (no refusal)", SH, "2>/dev/null)\" || { echo \"refused: a desk setting was refused", "2>/dev/null)\" || { true; echo \"refused: a desk setting was refused"),
 ("r10 sh config refusal exit 8 -> 1", SH, "to see which setting)\" >&2; exit 8; }", "to see which setting)\" >&2; exit 1; }"),
 ("r10 README exit 5 back to one meaning", RD, "or the check program failed (", "or the program failed ("),
 ("r10 README exit 8 line loses run_real_check", RD, "`start_all` and `run_real_check` give", "`start_all` give"),
 ("r10 sh header loses exit 5 meaning", SH, "OR the check program failed with some other exit code", "OR something else with some other exit code"),
]
R11 = [
 ("r10b README exit 5 loses the crash meaning", RD, "or the check program crashed (it gave", "or the program ended (it gave"),
 ("r10b README exit 8 loses the same-meaning clause", RD, "(same meaning as `start_all` and `run_real_check`)", "(a bad setting)"),
 ("r10b sh header loses the crash meaning", SH, "or the check program crashed (nothing was deleted", "or something (nothing was deleted"),
 ("r10b sh header loses the exit 8 same-meaning clause", SH, "(same meaning as start_all and run_real_check:", "(a bad setting:"),
 ("r10b ps1 header loses the crash meaning", PS, "or the check program crashed (nothing was deleted", "or something (nothing was deleted"),
 ("r10b ps1 header loses the exit 8 same-meaning clause", PS, "(same meaning as start_all and run_real_check:", "(a bad setting:"),
]
M = R11
M = [m for i, m in enumerate(M) if i % n == which]
out = open(OUT, "w"); dif = open(DIFFS, "w")
out.write("# round 10: name | KILLED/SURVIVED/NOT APPLIED | pytest last line | killing tests (first FAILED line (-x))\n")
for name, f, old_, new_ in M:
    p = WORK / f; orig = p.read_text(encoding="utf-8")
    pairs = old_ if isinstance(old_, list) else [(old_, new_)]
    if any(o not in orig for o, _ in pairs):
        out.write(f"{name} | NOT APPLIED (text not found)\n"); out.flush(); continue
    mut = orig
    for o, nw in pairs: mut = mut.replace(o, nw, 1)
    dif.write(f"##### {name} ({f})\n" + "".join(difflib.unified_diff(orig.splitlines(True), mut.splitlines(True), "good", "mutant", n=0)) + "\n"); dif.flush()
    p.write_text(mut, encoding="utf-8", newline="")
    try:
        r = subprocess.run([PY, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "-rf", "--basetemp", str(TMP/"mbt"), *FILES], cwd=WORK, capture_output=True, text=True, timeout=900, env={**__import__("os").environ, "LC_ALL": "C.UTF-8"})
        lines = r.stdout.strip().splitlines() or ["?"]
        failed = [l.split(" - ")[0].replace("FAILED ", "") for l in lines if l.startswith("FAILED")]
        out.write(f"{name} | {'KILLED' if r.returncode else 'SURVIVED'} | {lines[-1]} | {'; '.join(failed[:8])}\n")
    except subprocess.TimeoutExpired:
        out.write(f"{name} | KILLED (timeout) |\n")
    finally:
        p.write_text(orig, encoding="utf-8", newline="")
    out.flush()
out.close(); dif.close()
