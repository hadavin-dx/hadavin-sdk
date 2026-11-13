# Mutation check: tests/test_input_edge_cases.py::test_deeply_nested_json_is_bad_envelope (scratch copy of the frozen tree, Python 3.12.3)
Guards: src/lead_desk/server.py line 971 (envelope) and line 913 (resolve): `except (ValueError, RecursionError)` around json.loads.
| guard removed | result |
|---|---|
| none | pass (1 passed) |
| server.py:971 | pass |
| server.py:913 | pass |
| both | pass |
| restored | pass (diff vs original identical) |
Cause (checked directly): json.loads of 5000 nested brackets (the test's depth) does not raise RecursionError on 3.12.3; 10000, 20000 and 32000 do; the body cap is 65536 bytes, so a depth near 30000 fits. The test passes through the envelope-shape and decision checks, never reaching the guards.
Not done: the test was not changed or rerun at depth 30000; the set_step guard (line 938) was not mutated; other Python versions not tried.
