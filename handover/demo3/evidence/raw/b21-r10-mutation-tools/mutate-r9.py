import subprocess, sys, pathlib, shutil, os
SRC = pathlib.Path("/home/user/work/b21-tree"); part = sys.argv[1]; OUT = pathlib.Path(f"/home/user/work/b21-logs/mut/out9-{part}.log")
TMP = pathlib.Path(f"/home/user/work/b21-logs/mut/tmp9-{part}"); TMP.mkdir(exist_ok=True)
WORK = TMP / "tree"
if WORK.exists(): shutil.rmtree(WORK)
shutil.copytree(SRC, WORK, ignore=shutil.ignore_patterns(".git", "data", "__pycache__"))
PY = "/home/user/work/py313-venv/bin/python"
FILES = ["tests/test_reset_pid_file_reading.py", "tests/test_reset_order_and_words.py", "tests/test_reset_scripts.py", "tests/test_reset_ps1_pid_rules.py", "tests/test_reset_ps1_links.py", "tests/test_reset_ps_width.py", "tests/test_port_helpers.py"]
SH, PS, PB = "scripts/reset.sh", "scripts/reset.ps1", "tests/port_blocks.py"
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
 ("sh pass-2 recheck dropped", SH, 'if is_ours "$pid" "$(proc_args "$pid" || true)"; then', 'if true; then'),
 ("sh recheck exit 6 -> 1", SH, "and nothing was deleted${stopped:+ (already stopped: $stopped)}\" >&2\n      exit 6", "and nothing was deleted${stopped:+ (already stopped: $stopped)}\" >&2\n      exit 1"),
 ("sh recheck refuses an ended process", SH, 'elif alive "$pid"; then', 'else'),
 ("sh alive: EPERM read as stopped", SH, 'kill -0 "$1" 2>/dev/null || ps -p "$1" >/dev/null 2>&1 || return 1', 'kill -0 "$1" 2>/dev/null || return 1'),
 ("sh >= 64 check dropped", SH, "if (( ${#pid} >= 64 )) || [[", "if [["),
 ("sh non-ASCII check dropped", SH, ' || [[ "$pid" == *[![:print:][:space:]]* ]]', ''),
 ("sh NUL size check dropped", SH, ' || (( ${#pid} != (size < 67 ? size : 67) ))', ''),
 ("sh trim dropped", SH, 'pid="${pid#"${pid%%[![:space:]]*}"}"; pid="${pid%"${pid##*[![:space:]]}"}"\n}', ':\n}'),
 ("sh guard without BASH_VERSINFO", SH, "[[ a == a && -n ${BASH_VERSINFO+x} ]]", "[[ a == a ]]"),
 ("sh start_all guard without BASH_VERSINFO", "scripts/start_all.sh", "[[ a == a && -n ${BASH_VERSINFO+x} ]]", "[[ a == a ]]"),
 ("sh check crash exit 5 -> 1", SH, "exit 5 ;; esac", "exit 1 ;; esac"),
 ("sh check crash ignored", SH, "python scripts/reset_check.py || check_exit=$?", "python scripts/reset_check.py || true"),
 ("sh check dropped", SH, "python scripts/reset_check.py || check_exit=$?", "true"),
 ("sh check exit 3/4 changed", SH, "3|4) exit \"$check_exit\" ;;", "3|4) exit 1 ;;"),
 ("ps1 read loop dropped", PS, "while ($count -lt 67)", "while ($false)"),
 ("ps1 plain-text rule dropped", PS, "-or -not $plain)", "-or $false)"),
 ("ps1 number test back to ^$", PS, "'\\A[1-9][0-9]*\\z'", "'^[1-9][0-9]*$'"),
 ("ps1 preference stays Stop for the check", PS, "$ErrorActionPreference = 'Continue'", "$ErrorActionPreference = 'Stop'"),
 ("ps1 check crash exit 5 -> 1", PS, "not even the pid files\")\n    exit 5", "not even the pid files\")\n    exit 1"),
 ("ps1 plain rule upper bound 126 -> 255", PS, "$one -gt 126", "$one -gt 255"),
 
 
 ("sh dangling link not seen", SH, '[[ -e "$pidfile" || -L "$pidfile" ]]', '[[ -e "$pidfile" ]]'),
 ("sh 64 -> 65 after the mark", SH, "if (( ${#pid} >= 64 )) ||", "if (( ${#pid} >= 65 )) ||"),
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
 ("ps1 count not after the mark", PS, "(($count - $from) -ge 64) -or", "($count -ge 64) -or"),
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
which = int(sys.argv[2]); n = int(sys.argv[3])
M = [m for i, m in enumerate(M) if i % n == which]
out = open(OUT, "w")
for name, f, old, new in M:
    p = WORK / f; orig = p.read_text()
    if old not in orig:
        out.write(f"{name} | NOT APPLIED (text not found)\n"); out.flush(); continue
    p.write_text(orig.replace(old, new, 1))
    try:
        r = subprocess.run([PY, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "--basetemp", str(TMP/"mbt"), *FILES], cwd=WORK, capture_output=True, text=True, timeout=420)
        last = (r.stdout.strip().splitlines() or ["?"])[-1]
        out.write(f"{name} | {'KILLED' if r.returncode else 'SURVIVED'} | {last}\n")
    except subprocess.TimeoutExpired:
        out.write(f"{name} | KILLED (timeout) |\n")
    finally:
        p.write_text(orig)
    out.flush()
out.close()
