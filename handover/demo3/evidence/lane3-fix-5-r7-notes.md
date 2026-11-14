# lane3-fix-5 round 7 notes (builder B16), 2026-11-14

## Failures and open items first
- reset.ps1 was NOT run (no PowerShell here). Its checks are text pins plus Windows-only tests that are skipped on this machine (8 skipped in the reset/port files). Row 2b stays with the lead (WINDOWS-RUN-1 on the final stack tree). The pwsh attempt: `apt-get update`, then `apt-cache policy powershell` and `apt-cache search` found no package in the configured Ubuntu 24.04 repositories; no download from the web (lead order 2); stopped there.
- NOT done by me: the "launcher / Start-Process quoting" step for WINDOWS-RUN-1 (row 10). That file is in the studio folder, outside my outputs; the lead must add one line: "start_all.ps1 started the desk and the demo server; in Task Manager or Get-CimInstance the command line must read `python -m lead_desk.server` (and `... demo_only.fakes_server`) from its first character".
- Row 23 (duplicate book fixture, tests/conftest.py 166-176) left to the stack step, as ordered.
- The mutation run was made on the head before two wording edits (messages "pid N in" -> "process N named in", README exit-3 sentence). After them I re-ran the three reset test files (120 passed, 8 skipped) but not the mutants again.
- A pid file that is a locked file (not a folder) is only detected in pass 3 on Linux/Windows: the message then says the lead book and logs were not deleted and the programs may be stopped. That is the true statement; "nothing was stopped" is claimed only in pass 1.

## Counts
- Old code (r6 scripts and port helpers) with the new tests: raw/b16-fails-before.log: 114 failed, 93 passed, 8 skipped.
- xdist: raw/b16-xdist.log: pytest-xdist 3.8.0 installed with `pip --target` in the scratch folder (not a repo dependency), `-n 4` on the port and reset tests: 204 passed, 8 skipped; plus a probe on 4 real workers: gw0..gw3 got the blocks 20000-21595, 21596-23191, 23192-24787, 24788-26383 (PYTEST_XDIST_WORKER_COUNT=4 is set by xdist).
- Mutation: raw/b16-mutation.log, 36 mutants, first run 35 killed, 1 survived (support width 5000 -> 6000); a new test killed it (rerun of that mutant only). The 3 survivors of the r6 first run, by name: "ps1 [Pp]ython -> python (interp 1)", "ps1 Remove-Item catch dropped", "support worker regex too loose" (all three are mutants again in this log and are killed). The mutant "every worker gets range 0" (row 18) is in the log and killed.
- Full run: see raw/b16-full-final.log (tail in the hand-back).

## Row by row
1 two passes in both scripts (markers # PASS 1/2/3). Pass 1 judges both pid files and has no stop/wait/delete; pass 2 stops (desk first) and exit 5 names what was stopped, deletes nothing; pass 3 deletes pid files. Tested on Linux with real stand-in processes: second pid file another program -> exit 6, desk still running; second pid file a folder -> exit 7, desk running; stubborn demo server -> exit 5 naming the desk. ps1: text pins (pass 1 holds no Stop/Wait/Remove, aliases too).
2a README says plainly that reset.ps1 was not run on Windows (2026-11-14). 2b see above.
3 -LiteralPath on every Test-Path and Remove-Item in reset.ps1 (pin over all uses); Windows-only runtime test with "[" in a folder NOT written (not possible to run; the pin is the check). 
4 Get-CimInstance in try/catch -ErrorAction Stop, failure exits 6 "could not be looked up" in pass 1 (pin + mutants).
5 / 6 worker_port_range rewritten (tests/port_blocks.py): block width depends only on the count; workers 0..count-1 use the first half, restarted workers (count, count+1, ...) the second half, slot (n-count) mod count; start 20000, end 32767 (below Linux's own range from 32768 and Windows/macOS 49152). Property test for count 1..64 and numbers 0..2*count-1. Stated limit: two restarted workers share a block only if one outlives `count` later restarts; a missing count is treated as 256 workers. All 11 direct bind-to-port-0 sites in tests routed through bound_socket(); a guard test finds any new one. Guarantee is only "held versus free numbers of the helpers" (a program under test that binds by itself is not covered). The port code sits in tests/port_blocks.py, not support.py, so test_http_guard.py does not need the removable demo folder.
7 done (see counts).
8 multi-line pins and one mutant per pin; Windows-only runtime tests written (folder -> 7, long file -> stale, second pid file other program -> 6 with desk alive), skipped here.
9 held_port imported under its own name; reset_ports() in support.py gives two held ports.
10 start_all pin docstring reworded (text pin only). Quoting step: see open items.
11 README and comments say 64 bytes; reset.sh reads in the C locale so it is true. (Digits are ASCII, so the count never changes a decision.)
12 vocabulary: "process number / pid file / lead book" in the README and messages ("process N named in ..."); exit-3 clause split in the README.
13 reset.ps1 refusals go to standard error ([Console]::Error.WriteLine; pin: every exit 2-7 has one directly before it).
14 ps1 pattern anchored with "^" (no \s*), parity test row added; a pid file that is a link to a folder -> exit 7 in reset.sh (test with a real symlink); message "(a folder, or a file that is locked)" in both.
15 bash minimum raised (lead approved). The number is written once, in the README; the script says "mapfile -d" is missing and points to the README; the test reads the minimum from the README. Not run on a real old bash (no old bash here): the guard line is run alone with made-up version numbers.
16 _GIVEN_FREE cleared in release_held_ports (finally). 17 thread table per instance. 18 test renamed; mutant in log.
19 read loop to 64 bytes or end of file (pin; a regular file never returns less before its end, so the loop is only pinned, mutant "reads nothing" killed).
20 UTF-8 byte order mark skipped in both scripts (sh tested for real; ps1 pin); UTF-16 stays stale (sh tested for real).
21 CONTEST kept: the text is Trim()med before the match.
22 pid path made absolute with Convert-Path -LiteralPath before the .NET open (pin).
23 stack step. 24 survivors named above.

## Not checked
reset.ps1 execution; a real old bash; Windows ephemeral behaviour of the new port blocks; the stack's other tests beyond the full run; B14/B15 interplay.

## Files
Patch: lane3-fix-5-r7.patch (delta on claims series + r6; applies on a fresh tree and gives the same tree id as my tree). Tree /home/user/work/b16-tree (staged, not committed).
