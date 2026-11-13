# F7 rerun on d5b4451 (stale head; PR head is now edadd00)
Scripts unchanged: scratch/hostile_unc2.py and scratch/hostile_unc.py, run `python3.12 -I <script> /home/user/work/final`, both exit code 0. Raw: raw/hostile-f7-hostile_unc2-final.log, raw/hostile-f7-hostile_unc-final.log. Old = hostile.md and raw/hostile-unc*-pr12b.log on 8d65577. All with path_module=ntpath, on Linux (text level only, no Windows).
Refusal text (all PathRefused): `book path: a Windows device or network path (\\server\share, \\?\C:\) cannot be opened read-only by SQLite`

| input (repr) | old result on 8d65577 | new result on d5b4451 |
|---|---|---|
| `'\\??\\UNC\\host\\share\\x'` (NT object path) | NOT refused: `file:///tmp/%5C%3F%3F%5CUNC%5Chost%5Cshare%5Cx?mode=ro` | refused: PathRefused, text above |
| `''` | `file:///tmp?mode=ro` | refused: PathRefused `book path: the path is empty` |
| `'\x00'` | `file:///tmp/%00?mode=ro` (hostile.md) | refused: PathRefused `book path: contains a control character` |
| `'a\x00b'` | not listed in hostile.md | refused: PathRefused `book path: contains a control character` |
| `'\\\\?\\unc\\host\\share\\x'`, `'//?/UNC/host/share/x'`, `'//./C:/x'`, `'\\\\host/share/x'`, `'/\\/host/x'`, `'//'`, `'\\\\'`, `'\\\\?\\\\UNC\\host\\share'` | refused | refused (same text) |
| all 17 rows of the hostile_unc table with ntpath (`\\host\share\x.db`, `//host/share/x.db`, `\\?\UNC\...`, `\/host/...`, `/\host\...`, `\\?\C:\`, `\\.\C:\`, `\\localhost\...`, `//localhost/c$/x.db`, `\\host`, `\\host\share`, `\\?\UNC\`, `///host/share/x.db`, `\\\host\share`) | refused | refused (same text) |
| `'C:\\x.db'`, `'/tmp/ok.db'`, `'rel.db'` | not refused, `file:///tmp/...` | not refused; `C%3A%5Cx.db`, `/tmp/ok.db` unchanged |

Differences that are only the run folder: relative inputs resolve against the current folder (old /tmp, new /home/user/hadavin-sdk/handover/demo3), so `C:\x.db` gives `file:///home/user/hadavin-sdk/handover/demo3/C%3A%5Cx.db?mode=ro`. posixpath rows and confine* rows are unchanged from the old log apart from that. `read_book` rows: `\\?\UNC\host\share\x.db` now `InputError ... no such file` (old log: same per hostile.md row 51 column).
Not run: Windows itself.
