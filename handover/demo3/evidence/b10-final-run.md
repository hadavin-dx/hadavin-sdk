# b10 final run (EVIDENCE RUNNER, no judgement)
Tree /home/user/work/ev-b10, patch lane3-fix-8-r2 (sha256 0c976b13...). Start 04:09:5xZ, end Sat Nov 14 04:25:55 UTC 2026. gitleaks: /home/user/work/priv/gitleaks-bin/x/gitleaks (existed).
Pre-run: git status 8 entries (7 M, 1 A), ls data: No such file.
Log: raw/b10-full-final.log
```
5.74s call     tests/test_http.py::test_second_desk_refuses_to_start
3783 passed, 169 skipped in 924.24s (0:15:24)
rc=0
```
rc=0; pytest wall 924.24s (0:15:24); FAILED/ERROR lines: none
Post-run git status --porcelain --ignored (no pycache):
```
M  contract.md
M  docs/limits.md
M  docs/tests.md
M  src/lead_desk/config.py
M  src/lead_desk/identity.py
M  src/lead_desk/smtp_outbox.py
M  src/lead_desk/smtp_provider.py
A  tests/test_domain_labels.py
```
ls data after run: an EMPTY data/ directory exists (created 04:22Z, during the run; absent before; git does not list empty dirs, so status shows nothing for it). ls -la data: total 8, no entries.
