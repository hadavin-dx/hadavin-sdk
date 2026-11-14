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
