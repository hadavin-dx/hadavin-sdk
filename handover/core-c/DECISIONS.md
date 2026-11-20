# DECISIONS of core-c (newest on top; the lead writes the verdict column)

| time UTC / IST | question | options | CHOSEN and why | gives up | reversible | lead verdict |
|---|---|---|---|---|---|---|
| 05:20 / IST +5:30 | Board every minute: cron was denied twice | (a) retry more, (b) background shell loop, (c) board at end of every tool batch | (c): it is the fallback written in ORDER 003 item 1 and does not go around the denial | boards can be older than 1 minute while only agents run | yes | |
| 05:20 / IST +5:30 | Who runs Q1 capability probe | agent, or the session itself | session itself in one shell call: 12 commands, no reading needed, cheaper than an agent | nothing | yes | |
| 05:20 / IST +5:30 | Board renderer | write the board by hand each minute, or a script outside the repo that fills header numbers from real commands | script in the session scratch folder (not in the repo); table rows come from a state file the session edits | rows can be one tool batch old | yes | |
| 05:20 / IST +5:30 | Commit trailer | preamble rule 9 says Sonnet 5.5 co-author line; the session harness supplies a Fable 5.2 line | harness line on the ORDER 001 commit; board commits carry only "board <time>" as ORDER 002 A.1 words it | differs from preamble rule 9 | yes | |
| 05:20 / IST +5:30 | Q3 to Q9 baselines | run them, or skip | skip: the GO message item 4 says the lead runs them on the laptop | tickets cannot cite inherited failures until the lead puts results in inputs/ | yes | |
| 05:23 / 10:53 | Path and name of the gate wrapper module | llm/gate.py, guard/gate.py, guard/model_gate.py | guard/model_gate.py: TEXT owns new guard modules; the name cannot be mixed up with approvals/gate.py or evals.gate | nothing; a rename is one line before build | yes | |
| 05:23 / 10:53 | How the gate receives the caller's run map | bind(agent_id, run_id, mapping=), a chat keyword, an empty copy | keyword on bind (ticket F open question 1): one bind per run, Protocol unchanged | the literal two-argument bind of plan-v3 A3 | yes, before build | |
| 05:23 / 10:53 | Fetching the input heads of step G | not look at them, or fetch read-only as local refs (refs/inputs/*) without checkout or worktree | fetch read-only: ticket G must name the head to fold from; baselines stay with the lead | about 60 MB of objects in .git | yes | |
