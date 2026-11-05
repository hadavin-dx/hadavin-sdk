# Agent and shell supervision (hard rule)

Unmanaged wait-loops and unwatched agents burned compute and tokens. The root cause was not the number of agents but that nobody tracked or checked them.

1. Supervision is the rule; the count of agents is secondary. Keep a live register (one row per agent, shell, detached job and container: id, purpose, started, expected end, last checked, state, next action). Write the row BEFORE starting it. Check each item at its expected end (bounded read of its output or the agent list); if it shows no progress, find out why, then message, restart or stop it. When an agent reports, read the report, close the row and stop its helper shells in the same turn. Sweep the register at the end of every work block and before saying done.
2. Quality and speed come first; spend what the plan needs. Waste = idle or unwatched agents and loops, duplicate work, re-reading what is known, agents with no purpose or output. Every agent has a written purpose and expected output.
3. Never start an unbounded `until`/`while`/`sleep` loop; use background execution with a notification or a bounded poll with a timeout.
4. Before saying done or stopping, list agents and shells, stop every one you started, and report the counts. Never kill a process you did not start.
