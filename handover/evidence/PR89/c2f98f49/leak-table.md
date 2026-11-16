# Leak probes: password form x output channel

Cases run: 498 (13 made-up passwords x up to 44 child behaviours). Each cell: cases where the form was found / cases where that channel held any text. SHOWN means found at least once.

| form of the password | rows | on_result rows | first_lines | exception.str | exception.repr | exception.args | exception.rows | exception.notes | traceback text | parent stdout | parent stderr | left file names | left file contents |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| plain | NOT SHOWN (0/394) | NOT SHOWN (0/433) | SHOWN (2/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| reversed | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| upper | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| lower | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| percent_all | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| percent_quote | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| percent_quote_lower | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| base64 | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| hex | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| zero_width | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |
| two_lines | NOT SHOWN (0/394) | NOT SHOWN (0/433) | NOT SHOWN (0/433) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/104) | NOT SHOWN (0/39) | channel empty in every case | NOT SHOWN (0/104) | channel empty in every case | channel empty in every case | NOT SHOWN (0/498) | NOT SHOWN (0/498) |

Channel names: `rows` = the returned list; `on_result rows` = rows handed to the caller's callback; `first_lines` = the caller's dictionary; `exception.*` = the raised error (text, repr, args, the `rows` of a canary failure, notes); a chained cause or context would appear as `exception.cause.*` / `exception.context.*` (no such channel held text in any case: listed above only if present); `traceback text` = `traceback.format_exception` of the raised error in the calling process; `parent stdout/stderr` = everything the calling process printed; `left file names/contents` = every file and folder left in the private temp folder of the call (lock folder included).

## Per made-up password (label, length) x child behaviour: forms found anywhere

| password label | length | cases | cases with any form found | child behaviours where the raw JUnit copy did not hold the forms (console-only behaviours) |
|---|---|---|---|---|
| L3 | 3 | 39 | 0 | warning, stdio |
| L4 | 4 | 39 | 0 | warning, stdio |
| L8 | 8 | 39 | 0 | warning, stdio |
| L24 | 24 | 39 | 0 | warning, stdio |
| AT | 8 | 36 | 0 | warning, stdio |
| SPACE | 8 | 36 | 0 | warning, stdio |
| DIGITS | 8 | 36 | 0 | warning, stdio |
| BUILTIN_CLASS | 12 | 39 | 2 | warning, stdio |
| LIB_CLASS | 16 | 39 | 0 | warning, stdio |
| LIB_CLASS_SHOWN | 16 | 39 | 0 | warning, stdio |
| FUNC_NAME | 14 | 39 | 0 | warning, stdio |
| EXPECT_WORD | 4 | 39 | 0 |  |
| PATH_PART | 10 | 39 | 0 |  |

## Child behaviours (one run_mutants call each: baseline, one mutant, one canary run)

| behaviour | calls | how the calls ended (count) | pytest runs per call |
|---|---|---|---|
| assert_msg | 13 | {'returned rows': 13} | [3] |
| assert_first | 13 | {'returned rows': 13} | [3] |
| exc_msg | 13 | {'returned rows': 13} | [3] |
| exc_chained | 13 | {'returned rows': 13} | [3] |
| exc_class_dynamic | 13 | {'returned rows': 13} | [3] |
| exc_class_dynamic_plain | 13 | {'returned rows': 13} | [3] |
| exc_class_literal | 10 | {'returned rows': 10} | [3] |
| param_id | 13 | {'returned rows': 13} | [3] |
| param_id_plain | 13 | {'returned rows': 13} | [3] |
| fixture_missing | 13 | {'returned rows': 13} | [3] |
| fixture_raises | 13 | {'returned rows': 13} | [3] |
| fixture_teardown | 13 | {'returned rows': 13} | [3] |
| skip_reason | 13 | {'returned rows': 13} | [3] |
| skip_param | 13 | {'returned rows': 13} | [3] |
| skip_module | 13 | {'returned rows': 13} | [3] |
| xfail_reason | 13 | {'returned rows': 13} | [3] |
| collect_error | 13 | {'returned rows': 13} | [3] |
| collect_error_class | 13 | {'returned rows': 13} | [3] |
| collect_assert | 13 | {'returned rows': 13} | [3] |
| warning | 13 | {'returned rows': 13} | [3] |
| stdio | 13 | {'returned rows': 13} | [3] |
| func_dynamic | 13 | {'returned rows': 13} | [3] |
| class_dynamic | 13 | {'returned rows': 13} | [3] |
| func_literal | 10 | {'returned rows': 10} | [3] |
| class_literal | 10 | {'returned rows': 10} | [3] |
| forged_message | 13 | {'returned rows': 13} | [3] |
| forged_type | 13 | {'returned rows': 13} | [3] |
| forged_classname | 13 | {'returned rows': 13} | [3] |
| forged_name | 13 | {'returned rows': 13} | [3] |
| forged_sysout | 13 | {'returned rows': 13} | [3] |
| forged_body | 13 | {'returned rows': 13} | [3] |
| baseline_fail | 13 | {'RuntimeError': 13} | [1] |
| baseline_fail_class | 13 | {'RuntimeError': 13} | [1] |
| baseline_skip | 13 | {'RuntimeError': 13} | [1] |
| baseline_collect | 13 | {'RuntimeError': 13} | [1] |
| baseline_func_dynamic_skip | 13 | {'RuntimeError': 13} | [1] |
| canary_fail | 13 | {'CanaryFailed': 13} | [3] |
| canary_skip | 13 | {'CanaryFailed': 13} | [3] |
| canary_func_dynamic_skip | 13 | {'CanaryFailed': 13} | [3] |

Both halves of a password (8 characters or longer) present somewhere in one channel, not adjacent: BUILTIN_CLASS--exc_class_dynamic_plain (first_lines), BUILTIN_CLASS--exc_class_literal (first_lines)
