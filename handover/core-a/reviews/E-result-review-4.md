Status: extra pass granted by the lead (E5 = yes); resolved; stop at this round (no round 5). Fresh reviewer egm-codebase-details, sonnet, read-only. Result: no Blocker, no Major, 7 Nits.
| id | finding | category | action |
|---|---|---|---|
| E4-1 | crash.py ~142/282 (Python 3.12 on Windows): Path.exists after a refused unlink can raise PermissionError into the code under test | PROPOSE FIX | helper around os.path.exists in try/except OSError (treat as still there) + test |
| E4-2 | a read error counts as 'not armed' and nth does not advance | PROPOSE FIX (docs) | one sentence in the docstring |
| E4-3 | misspelled point passes vacuously in exit mode | PROPOSE FIX (docs) | docstring line: an exit-mode test must assert marker and exit code |
| E4-4 | test_worker.py:499 importorskip hides a broken helper | PROPOSE FIX | plain import |
| E4-5 | test name promises three facts, checks substrings | PROPOSE FIX | rename |
| E4-6 | constant-pinning tests | DECLINE | harmless |
| E4-7 | 'flag taken' test simulates the race | PROPOSE FIX | say 'simulated' in the name |
Fixes after batch6 finishes (crash.py is part of its hashed tree): small builder, then ruff + test_testing_crash.py + test_worker once.
