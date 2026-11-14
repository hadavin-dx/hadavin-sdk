# WINDOWS-RUN-1: run the two PowerShell scripts on the lead's Windows laptop

Written 2026-11-14 04:36Z (10:06 IST) by lane3. READ THIS FIRST: nothing below has ever been run on Windows. This
Linux container has no PowerShell, so `scripts/reset.ps1` and `scripts/start_all.ps1` have only been READ and checked by
text tests. The "expected" lines come from reading the code of patch `lane3-fix-5-r6.patch` (sha256 starts `0117c654`),
not from a run. If a real line differs, that difference is the finding: copy the output, do not "fix" it on the spot.

Data: made-up only. Network: loopback only (127.0.0.1, ports 8765 and 8766). Nothing real is touched. No secrets.

## 0. What you need
* Windows 11, Windows PowerShell 5.1 (the blue one: `powershell.exe`), Python 3.13 (`py -3`), git.
* Do not use an administrator window. Use a scratch folder, for example `C:\Temp\lane3-win`.
* Nothing else may listen on ports 8765 and 8766 (check below).

## 1. Get a clean checkout and apply the patches (in this order, stop at the first error)
The patch files are in the repository `hadavin-dx/hadavin-sdk`, branch `demo/lane3`, folder `handover/demo3/evidence/`.
Fetch that branch in a SEPARATE folder, then copy the patch files out.

    mkdir C:\Temp\lane3-win ; cd C:\Temp\lane3-win
    git clone https://github.com/hadavin-dx/hadavin-sdk.git sdk
    git -C sdk checkout demo/lane3
    git clone https://github.com/hadavin-dx/duplicate-proof-lead-desk-n8n.git desk
    cd desk
    git checkout f3c39cf89ec989f032ea48a23cfd824b88da9c68
    git apply --check ..\sdk\handover\demo3\evidence\claims-stack-on-f3c39cf8.patch ; $LASTEXITCODE     # expect 0
    git apply ..\sdk\handover\demo3\evidence\claims-stack-on-f3c39cf8.patch ; $LASTEXITCODE            # expect 0
    git apply --check ..\sdk\handover\demo3\evidence\lane3-fix-5-r6.patch ; $LASTEXITCODE              # expect 0
    git apply ..\sdk\handover\demo3\evidence\lane3-fix-5-r6.patch ; $LASTEXITCODE                      # expect 0

(`git apply` leaves the changes unstaged and makes no commit. If the stack run later produces one combined patch, lane3
will replace step 1 with that file; use the newest `WINDOWS-RUN-*.md`.)
If `git apply` prints a line-ending warning, that is expected on Windows; any "error:" line is a finding.

## 2. Environment (same terminal for everything below, working directory `C:\Temp\lane3-win\desk`)

    py -3 -m venv .venv
    Set-ExecutionPolicy -Scope Process RemoteSigned
    .venv\Scripts\Activate.ps1
    $env:PYTHONPATH = "src"
    python --version                       # expect Python 3.13.x
    Get-NetTCPConnection -LocalPort 8765,8766 -ErrorAction SilentlyContinue    # expect: no output

## 3. Happy path (README "Windows PowerShell" block)

    .\scripts\start_all.ps1 keyed          # expect: "started: demo servers (keyed outbox) pid N, desk pid M", then a "ports: ..." line and a "logs: ..." line; $LASTEXITCODE not meaningful here
    Start-Sleep 3
    Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/counts | Select-Object -ExpandProperty Content   # numbers, all 0
    python scripts\feed.py --source form --index 1       # 201 ... "verdict": "new"
    python scripts\feed.py --source form --index 1       # 201 ... "replayed": true
    python scripts\feed.py --source webhook --index 1    # 201 ... "verdict": "duplicate"
    Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/counts | Select-Object -ExpandProperty Content   # received 2, new 1, duplicate 1
    Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8766/fake/outbox | Select-Object -ExpandProperty Content   # "count": 1
    Get-ChildItem data                                   # desk.pid, fakes.pid, logs, the database files
    .\scripts\reset.ps1 ; $LASTEXITCODE                  # expect last line "reset done", then 0
    Get-ChildItem data                                   # expect: empty or no pid files, no database, no logs
    Get-NetTCPConnection -LocalPort 8765,8766 -ErrorAction SilentlyContinue    # expect: no output (the port may stay in "TimeWait" for about two minutes: that is the operating system; say so if you see it)

## 4. Refusal cases (each: run, copy the one line, write the exit code). Start from an empty `data` folder after each.
Each refusal prints ONE line and deletes nothing (except case D, which deletes the stale file on purpose).

| Case | Setup | Command | Expected last line | Expected `$LASTEXITCODE` |
|---|---|---|---|---|
| A bad wait value | `$env:RESET_STOP_WAIT_SECONDS = "abc"` | `.\scripts\reset.ps1` | `refused: RESET_STOP_WAIT_SECONDS must be a whole number of seconds from 0 to 999 with no leading zero; nothing was stopped or deleted` | 2 |
| A2 leading zero | `$env:RESET_STOP_WAIT_SECONDS = "007"` | same | same line | 2 |
| B pid file is a folder (the exit-7 fix) | `Remove-Item Env:RESET_STOP_WAIT_SECONDS ; New-Item -ItemType Directory -Force data\desk.pid` | `.\scripts\reset.ps1` | `refused: ...data\desk.pid cannot be removed (is it a folder?); nothing else was deleted` | **7** (and `data\desk.pid` still exists) |
| B2 same, folder not empty | `New-Item -ItemType File data\desk.pid\x` | same | same line | 7 |
| C pid file names another program | `$PID \| Set-Content data\desk.pid` (your own PowerShell window) | same | `refused: pid N in ...desk.pid is not the desk or the demo server; nothing was stopped or deleted (delete the pid file yourself if it is stale)` | 6 (your window must NOT be stopped) |
| D stale pid file | `"abc" \| Set-Content data\desk.pid` | same | `reset done` | 0 (the file is gone) |
| D2 stale, 64+ characters | `("1" * 70) \| Set-Content data\desk.pid` | same | `reset done` | 0 |
| E leading zero pid | `"007" \| Set-Content data\desk.pid` | same | `reset done` | 0 |
| F port still answered (needs a started desk) | `.\scripts\start_all.ps1 keyed`, then delete only the pid files: `Remove-Item data\*.pid` | `.\scripts\reset.ps1` | a `refused:` line from `scripts\reset_check.py` about the port or the database | 3 or 4 (note which) |

For F, stop the servers afterwards by hand: `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'lead_desk.server|demo_only.fakes_server' } | ForEach-Object { Stop-Process -Id $_.ProcessId }`
(first LOOK at what that lists; it must show only the desk and the demo server), then `.\scripts\reset.ps1` again, expect `reset done`.

## 5. start_all.ps1 checks
* `.\scripts\start_all.ps1 blind` after a reset: prints `started: demo servers (blind outbox) ...`.
* Run `.\scripts\start_all.ps1 keyed` a second time WITHOUT reset: expect an error that contains `pid files exist: run scripts\reset.ps1 first`.
* `.\scripts\start_all.ps1 wrongmode`: PowerShell's own refusal of the value (ValidateSet); nothing starts.
* `$env:DESK_LEADFLOW_FILE = "off"` then start: starts without the reminder address.
* Finish with `.\scripts\reset.ps1` (expect `reset done`) and `Remove-Item Env:DESK_LEADFLOW_FILE`.

## 6. Optional: the test suite on Windows (about 20 minutes; only if you have time)
    pip install --require-hashes -r requirements-dev-win.txt
    python -m pytest -q -p no:cacheprovider
Expected: no failures; skips are the Linux-only ones. Note the final line.

## 7. What to look at and send back
Per step: the exact output line and the exit code. Anything that differs from "expect", any red text, any process that
stays alive after `reset done` (`Get-Process python`), and whether `data\` is empty afterwards. A difference is a real
finding for fix-5: send it as text, lane3 will build a fix and a test that fails on the old code.

## 8. Clean up

    deactivate
    cd C:\Temp ; Remove-Item -Recurse -Force C:\Temp\lane3-win
    # if python processes of the demo are still running (check first): Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'lead_desk.server|demo_only.fakes_server' }

## 9. Not covered by this run
* PowerShell 7 (`pwsh`) and Windows 10: not asked.
* `scripts/reset.sh` on macOS bash 3.2: not run anywhere (its refusal is exit 2 by reading, and a text test).
* n8n workflows are not part of this run.

## 10. Extra lines collected from the builders' notes (13:00Z on 2026-11-14, by lane3)
READ THIS FIRST: nothing in this section has run on Windows either. The three fix lanes are PAUSED (fix-5 at round 11, fix-2 at round 13, fix-10 at round 7), so the patch series is not final: step 1 above will be replaced by one final stack patch, and these lines must be run on THAT tree. Each line names the note it came from; the "expect" text is the builder's reading of the code, not a run.

### 10a. reset.ps1 pid-file and exit-code cases (source: evidence/lane3-fix-5-r9-notes.md and lane3-fix-5-r10-notes.md)
1. Port still answered (check refuses): run once with `2>&1` joined and once plain. Expect exit 4, the ONE refusal line, and no red NativeCommandError block (Windows PowerShell 5.1 turns a program's stderr into one under `$ErrorActionPreference='Stop'`).
2. desk.pid holding the live desk's number saved as UTF-16 (with and without a byte-order mark) and, separately, the number plus one U+3000 (wide space): expect the file called stale, the desk still running, the file deleted.
3. desk.pid "123" plus a line end: still read as the number. "12" newline "34": stale.
4. desk.pid with 64 bytes and with 63 bytes after a UTF-8 mark: 64 is stale; 63 (plus digits) reads as before.
5. `$env:PATH` without python, then `powershell -File scripts/reset.ps1`: expect the line "refused: a desk setting was refused (or python was not found) ..." and exit 8.
6. A stand-in `python.cmd` that exits 1 for scripts\reset_check.py: expect "refused: the check program failed (exit 1) ..." and exit 5, pid files kept.
7. In the same session first run `cmd /c exit 9`, then the reset with a check stand-in that prints nothing and ends with no exit code: expect exit 5 (the stale 9 must not be reused).
8. `$env:DESK_PORT='abc'`, then the reset: exit 8. `$env:RESET_STOP_WAIT_SECONDS='08'`, or a value with a trailing line end: exit 8.
9. Plain run with a running desk: exit 0.

### 10b. process lookup (source: evidence/lane3-fix-5-r8-notes.md, "WINDOWS-RUN-1 lines for the lead")
1. `Get-CimInstance Win32_Process` for the desk's pid: `$p.CommandLine` printed with brackets around it must read from its FIRST character (no leading space or quote), so the anchored match holds. Same for the demo server: it must read `python -m demo_only.fakes_server` from its first character (also fix-5 round 7, "launcher / Start-Process quoting").
2. A process that has ended gives `$null` with no error (the pid file is then stale: exit 0 in pass 1; in pass 2 the program is skipped as "gone"); a lookup that throws gives exit 6 "could not be looked up".
3. What `Get-Item -LiteralPath -Force` does with a dangling symbolic link (reset.ps1, row 18): unverified; run it and copy the line.

### 10c. start_all.ps1 (source: evidence/lane3-fix-10-r2-notes.md, r4, r5 notes)
1. bad `DESK_PORT` for reset.ps1 AND start_all.ps1: expect exit 8 and one line. A bad `DESK_NUDGE_TO` (set `DESK_LEADFLOW_FILE` first): the same. start_all.ps1 with a taken port: expect exit 5 and no "started" line.
2. (5b) make the desk log end with a non-ASCII line, run start_all.ps1 against a failing desk: the failure line shows it as readable text, the script ends with the exit code of the table, not a red error block, and the console code page (`[Console]::OutputEncoding`) is the same after the run as before.
3. The demo server counts as up only when `fakes.log` holds "fakes server ... on port N". Include the case where something else already holds the port (two binds to the same port at once).

### 10d. Not covered, still
PowerShell 7, Windows 10, and the full test suite on Windows (section 6) are as before. The Linux side of every line above is covered by tests; the Windows side is not.
