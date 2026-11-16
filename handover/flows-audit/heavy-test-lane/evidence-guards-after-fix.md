## Guards after fix
$ uv run --all-extras --group test pytest -q -p no:cacheprovider -k "test_no_vendor_brand_string_is_tracked or test_licences_are_proprietary" (AWS_* unset)
rc=0
$ git status --short | head
?? handover/flows-audit/flow-check/selftest-output/cycle_only@film-mf-form.json.out
?? handover/flows-audit/flow-check/selftest-output/cycle_only@real-mf-form.json.out
?? handover/flows-audit/flow-check/selftest-output/cycle_only@real-mf-hook.json.out
?? handover/flows-audit/flow-check/selftest-output/cycle_only@real-mf-recovery.json.out
?? handover/flows-audit/flow-check/selftest-output/cycle_only@real-mf-sub-crm-mail.json.out
?? handover/flows-audit/flow-check/selftest-output/dangling@film-mf-form.json.out
?? handover/flows-audit/flow-check/selftest-output/dangling@real-mf-form.json.out
?? handover/flows-audit/flow-check/selftest-output/dangling@real-mf-hook.json.out
?? handover/flows-audit/flow-check/selftest-output/dangling@real-mf-recovery.json.out
?? handover/flows-audit/flow-check/selftest-output/dangling@real-mf-sub-crm-mail.json.out
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Using CPython 3.13.18 interpreter at: /usr/local/bin/python3
Creating virtual environment at: .venv
   Building hadavin-sdk @ file:///home/user/hadavin-sdk
      Built hadavin-sdk @ file:///home/user/hadavin-sdk
Installed 76 packages in 95ms
..                                                                       [100%]
2 passed, 10551 deselected in 8.54s
```
