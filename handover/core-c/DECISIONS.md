# DECISIONS of core-c (newest on top; the lead writes the verdict column)

| time UTC / IST | question | options | CHOSEN and why | gives up | reversible | lead verdict |
|---|---|---|---|---|---|---|
| 05:20 / IST +5:30 | Board every minute: cron was denied twice | (a) retry more, (b) background shell loop, (c) board at end of every tool batch | (c): it is the fallback written in ORDER 003 item 1 and does not go around the denial | boards can be older than 1 minute while only agents run | yes | |
| 05:20 / IST +5:30 | Who runs Q1 capability probe | agent, or the session itself | session itself in one shell call: 12 commands, no reading needed, cheaper than an agent | nothing | yes | |
| 05:20 / IST +5:30 | Board renderer | write the board by hand each minute, or a script outside the repo that fills header numbers from real commands | script in the session scratch folder (not in the repo); table rows come from a state file the session edits | rows can be one tool batch old | yes | |
| 05:20 / IST +5:30 | Commit trailer | preamble rule 9 says Sonnet 5.5 co-author line; the session harness supplies a Fable 5.2 line | harness line on the ORDER 001 commit; board commits carry only "board <time>" as ORDER 002 A.1 words it | differs from preamble rule 9 | yes | |
| 05:20 / IST +5:30 | Q3 to Q9 baselines | run them, or skip | skip: the GO message item 4 says the lead runs them on the laptop | tickets cannot cite inherited failures until the lead puts results in inputs/ | yes | |
