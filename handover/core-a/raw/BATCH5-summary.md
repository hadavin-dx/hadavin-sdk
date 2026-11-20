# BATCH5 summary (item 2, whole suite in checkout)

Last line: `2 skipped, 1 error in 2.56s` (run stopped at collection, 2.56s, nothing else ran)

## FAILED ids
none listed; 1 collection ERROR: tests/triggers/test_t5_main_start.py (ImportError from require_core_b: HADAVIN_REQUIRE_PG=1: core-b trigger config (TriggerSettings, Config.triggers) not on this tree)

## Skip reasons
| reason | count |
|---|---|
| core-b trigger config not on this branch yet | 1 |
| the model gate (step F) is not on this branch yet: hadavin_sdk.guard.model_gate is missing | 1 |

xfail count: 0
