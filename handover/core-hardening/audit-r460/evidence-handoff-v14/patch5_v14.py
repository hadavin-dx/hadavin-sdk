from patch_lib import Doc
d = Doc("CORE-PR-HANDOFF-v14.md")
d.rep("finds 14 lines in 6 files", "finds 14 lines in 5 files")
d.after_line("| 8 | a failed attempt that was not billed costs nothing", "| 9 | the injection screen on approval summaries runs | the agent's `-unattributed` counter is not used up | once it is used up, the screen on that agent's approval summaries is disabled (5.11 item 10) | a summary is shown with no injection screen | the status line says so; a person reads the card |")
d.rep("a second `migrate()` applies nothing | `E0-DB-2.txt`", "a second `migrate()` applies nothing; **the temporary-table attack: the runtime role creates and grants on a temporary table of the log's name, lowers a total, and the real log gets the row (it must fail on the v13 function); `TEMP` is revoked from PUBLIC and the runtime role is then refused; the portal role reads the log and cannot delete from it** | `E0-DB-2.txt`")
d.rep("| `E0-S1-1 |", "| `E0-S1-1 |") if False else None
d.save()
