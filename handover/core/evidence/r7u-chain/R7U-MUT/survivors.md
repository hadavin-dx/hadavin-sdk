### X01 at scripts/run_real_check.py:997
expected catcher: test_r7u_a a2 / b7 (smtp file with bad value)
OLD:
```
            if not all(type(v) is int and v >= 0 for v in values.values()):
```
NEW:
```
            if suffix == ".hubspot.json" and not all(type(v) is int and v >= 0 for v in values.values()):
```
wide: ['X01', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['................']", 'restored=True']

### X05 at scripts/run_real_check.py:1389
expected catcher: test_r7u_a a1c open term
OLD:
```
            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),
            len(lead_ids),
        )
    result["checks"].append
```
NEW:
```
            hub_stats.get("create_open", 0) * 2 + hub_stats.get("create_unknown", 0),
            len(lead_ids),
        )
    result["checks"].append
```
wide: ['X05', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['.................']", 'restored=True']

### X10 at scripts/run_real_check.py:671
expected catcher: test_r7t/r7s exit_code_of or a2 real run
OLD:
```
return 0 if ok and written and not left and not unseen and counter_known else EXIT_FAILED
```
NEW:
```
return 0 if ok and written and not left and not unseen else EXIT_FAILED
```
wide: ['X10', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['.................']", 'restored=True']

### X11 at scripts/run_real_check.py:1369
expected catcher: test_r7u_b b7 stale dict
OLD:
```
    smtp_stats = smtp_read.totals if smtp_known else {}
```
NEW:
```
    smtp_stats = smtp_read.totals if smtp_known else dict(hub_stats)
```
wide: ['X11', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['.................']", 'restored=True']

### X12 at scripts/run_real_check.py:1363
expected catcher: test_r7u_b b7 hub read used for mail
OLD:
```
    smtp_known = smtp_counter_is_known(smtp_read)
```
NEW:
```
    smtp_known = smtp_counter_is_known(hub_read)
```
wide: ['X12', 'KILLED', '37s', "['FAILED tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end - Assertio...']", "['1 failed, 1 passed in 36.69s']", 'restored=True']

### X14 at scripts/run_real_check.py:1382
expected catcher: test_r7u_a a3 / b5
OLD:
```
    counter_known = counter_is_known(hub_read)
    # the clean-up
```
NEW:
```
    counter_known = counter_is_known(smtp_read)
    # the clean-up
```
wide: ['X14', 'KILLED', '36s', "['FAILED tests/test_real_check_dry.py::test_dry_fakes_run_end_to_end - Assertio...']", "['1 failed, 1 passed in 36.32s']", 'restored=True']

### X19 at scripts/run_real_check.py:611
expected catcher: test_r7u_a a4 / r7s readback result file
OLD:
```
{"ok": False, "note": note, "leads_in_book": leads, "hubspot_calls_by_the_desk": hub_stats},
```
NEW:
```
{"ok": False, "note": note, "leads_in_book": leads, "hubspot_calls_by_the_desk": {}},
```
wide: ['X19', 'SURVIVED-UNTIL-TIMEOUT', '120s', '[]', "['................']", 'restored=True']

### Y09 at scripts/run_real_check.py:1000
expected catcher: test_r7u_a/b OSError (folder instead of file)
OLD:
```
        except (OSError, ValueError, AttributeError, TypeError, ArithmeticError):
```
NEW:
```
        except (ValueError, AttributeError, TypeError, ArithmeticError):
```
wide: None

### Y10 at scripts/run_real_check.py:1000
expected catcher: test_r7u_a a2 TypeError
OLD:
```
        except (OSError, ValueError, AttributeError, TypeError, ArithmeticError):
```
NEW:
```
        except (OSError, ValueError, AttributeError, ArithmeticError):
```
wide: None

### Y13 at scripts/run_real_check.py:1387
expected catcher: (equivalent probe: default 0 behind counter_known)
OLD:
```
            hub_stats.get("created"),
            len(crm_pairs),
            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),
            len(lead_ids),
        )
    result["checks"].append
```
NEW:
```
            hub_stats.get("created", 0),
            len(crm_pairs),
            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),
            len(lead_ids),
        )
    result["checks"].append
```
wide: ['Y13', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['.................']", 'restored=True']

### Y15 at scripts/run_real_check.py:1466
expected catcher: test_r7u_a a3 real run (list lag) exit
OLD:
```
return exit_code_of(result["ok"], written, left, unseen, counter_known)
```
NEW:
```
return exit_code_of(result["ok"], written, left, 0, counter_known)
```
wide: ['Y15', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y16 at scripts/run_real_check.py:1466
expected catcher: test_r7u_a a2/a3 real run exit
OLD:
```
return exit_code_of(result["ok"], written, left, unseen, counter_known)
```
NEW:
```
return exit_code_of(result["ok"], written, left, unseen, True)
```
wide: ['Y16', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y17 at scripts/run_real_check.py:1450
expected catcher: test_r7u_a a3 (words printed)
OLD:
```
    if not counter_known:
        print(
            "the desk's HubSpot counter cannot
```
NEW:
```
    if counter_known:
        print(
            "the desk's HubSpot counter cannot
```
wide: ['Y17', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y18 at scripts/run_real_check.py:1456
expected catcher: test_r7u_a a3 unseen message printed
OLD:
```
    if (
        unseen
    ):
```
NEW:
```
    if (
        False
    ):
```
wide: ['Y18', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y19 at scripts/run_real_check.py:1461
expected catcher: test_r7u_a a1c main-level message
OLD:
```
            f"{hub_stats.get('create_open', 0) + hub_stats.get('create_unknown', 0)} create requests with no known "
```
NEW:
```
            f"{hub_stats.get('create_open', 0)} create requests with no known "
```
wide: ['Y19', 'SURVIVED-UNTIL-TIMEOUT', '100s', '[]', "['................']", 'restored=True']

### Y25 at scripts/run_real_check.py:606
expected catcher: test_r7u_a a4 not-known note
OLD:
```
        note += "; an unknown number of contacts may still be in HubSpot, "
```
NEW:
```
        note += "; up to 0 contacts may still be in HubSpot, "
```
wide: None

### Y28 at scripts/run_real_check.py:662
expected catcher: test_r7u_a a3 counter_check shape
OLD:
```
        "offender_count": 0,
        "offenders": [],
        "values"
```
NEW:
```
        "offender_count": unseen,
        "offenders": [],
        "values"
```
wide: None

### Z01 at src/lead_desk/loopback.py:27
expected catcher: test_r7u_c / r7t loopback spellings
OLD:
```
    bare = name[1:-1] if name.startswith("[") and name.endswith("]") else name
```
NEW:
```
    bare = name[1:-1] if name.startswith("[") or name.endswith("]") else name
```
wide: ['Z01', 'SURVIVED-UNTIL-TIMEOUT', '300s', '[]', "['........................................................................ [ 23%]\\n........................................................................ [ 46%]\\n..............']", 'restored=True']

### Z02 at src/lead_desk/loopback.py:27
expected catcher: test_r7u_c / r7t
OLD:
```
    bare = name[1:-1] if name.startswith("[") and name.endswith("]") else name
```
NEW:
```
    bare = name[1:-1] if name.endswith("]") else name
```
wide: None

### Z03 at src/lead_desk/loopback.py:28
expected catcher: test_r7u_c half bracket
OLD:
```
    if "[" in bare or "]" in bare or "%" in bare:
```
NEW:
```
    if "[" in bare or "%" in bare:
```
wide: None

### Z04 at src/lead_desk/loopback.py:28
expected catcher: test_r7u_c half bracket
OLD:
```
    if "[" in bare or "]" in bare or "%" in bare:
```
NEW:
```
    if "]" in bare or "%" in bare:
```
wide: None

### Z08 at src/lead_desk/loopback.py:46
expected catcher: test_r7u_c returns the host unchanged
OLD:
```
    return host
```
NEW:
```
    return host.strip()
```
wide: None

### Z10 at demo_only/fake_imap.py:16
expected catcher: test_r7u_c light-import
OLD:
```
from lead_desk.loopback import require_loopback_host

```
NEW:
```
from demo_only.fake_smtp_tls import require_loopback_host as _r
require_loopback_host = _r

```
wide: None

### Z11 at demo_only/fakes_server.py:247
expected catcher: test_r7u_b b8 / c refusal in fakes_server
OLD:
```
    where = require_loopback_host(Config().fakes_host if host is None else host)
```
NEW:
```
    where = Config().fakes_host if host is None else host
```
wide: None

### Z12 at demo_only/fake_model_server.py:275
expected catcher: test_r7u_c / r7t fake model refuses
OLD:
```
    require_loopback_host(host)  # a stand-in
```
NEW:
```
    pass  # a stand-in
```
wide: None

### Z15 at tools/refusing_args.py:190
expected catcher: test_r7u_c text / r7t refusing_args
OLD:
```
        raise ArgumentTypeError(LOOPBACK_HOST_TEXT) from None
```
NEW:
```
        raise ArgumentTypeError("x") from None
```
wide: None

### Z16 at src/lead_desk/smtp_outbox.py:87
expected catcher: smtp_outbox loopback
OLD:
```
        if not is_loopback_host(self.host):
```
NEW:
```
        if is_loopback_host(self.host):
```
wide: None

