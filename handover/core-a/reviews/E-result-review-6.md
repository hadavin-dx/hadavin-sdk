# E result review, round 6

| id | decision | action |
|---|---|---|
| MAJOR (Windows directory flag, PermissionError) | accepted | `_look`: PermissionError branch sets unreadable only if the flag is not a directory; test `test_a_directory_flag_read_failing_with_permission_error_is_not_armed` |
| NIT 1 (left kept after a vanished flag) | accepted | `__exit__`: `left` kept only if `_disarm()` returned True; test with unlink raising FileNotFoundError |
| NIT 2 (exists swallows PermissionError on Linux) | accepted, documented | one sentence in the `_still_there` docstring |
| NIT 3 (missing tests) | accepted | stuck delete on unreadable flag; KeyError in flight not replaced |
| NIT 4 (revert check) | accepted | docstring of the nth-count test says it pins `hit` and passes on revert |
| NIT 5 (global time.sleep patch) | accepted | `stub_unlink` patches `_UNLINK_PAUSE_S` to 0 and the module's own `time` name |
| NIT 6 (endpoint_mutants.py hash) | not edited | crash.py sha256 changed; another agent re-runs the mutants |
