# Recommendations (core lane, running list)
Status values: adopted / rejected / owner-needed. Newest at the bottom.

| # | date | what | why | evidence | status |
|---|---|---|---|---|---|
| 1 | 2026-11-12 | Add a repo guard test that every hook command in .claude/settings.json names an existing script via $CLAUDE_PROJECT_DIR | a relative hook path blocked every prompt for hours (fixed by ecb1e242) | git log of .claude/settings.json; the error text "cannot open .claude/hooks/egm-gate.sh" | owner-needed (touches .claude settings, which I do not edit) |
| 2 | 2026-11-12 | Run the 12 Vault engine tests (tests/test_policy_engine.py) in CI on the final Q8c-1 head and read the -rs line (12 passed, 0 skipped) before the Q8c-1 merge | no vault or bao binary exists in this session; the tests were never run | evidence Q8c-1 be531371 (13 skips) | owner-needed |
| 3 | 2026-11-12 | Merge order Q8b before PR77, or rebase PR77 on Q8b | Q8b edits redact.py though its ticket said not to; PR77 edits the same file | Q8b r2 evidence | owner-needed |
