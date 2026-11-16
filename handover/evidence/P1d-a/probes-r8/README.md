# Probe P10 (plan pass 7, rev 9 -> rev 10)
Trees: orig = `/tmp/p7/orig` (base `2742c1bf`), P9 = `/tmp/p9`, P10 = P9 plus `p10_apply.py` (steps 1-7; step 7 `_drop_targets` by `p10_apply7.py`).
Apply command: `rm -rf /tmp/p10 && cp -r /tmp/p9 /tmp/p10 && python p10_apply.py /tmp/p10/src/hadavin_sdk` (prints ok..ok6, then ok7).
Tree stamp (`sh stamp.sh /tmp/p10`, first 12 hex of sha256 over src/**/*.py): see `stamp-p10.txt`.
Run: `PYTHONPATH=<tree>/src <repo>/.venv/bin/python <script>`.
| script | output |
|---|---|
| p10_rows.py | rows-p10.out |
| p10_lk.py | lk-p10.out, lk-orig.out |
| p10_links3.py | links3.out (0 failures on 2,000 texts) |
| p10_rt.py | rt10.out (fixed-point failures 0; b != a 1, more masking only) |
| p10_fixpt.py | fixpt.out (0) |
| p10_time.py, p10_t1.py, runtime.sh | time-p10.out, mutants-timing.out |
| p10_dest.py | p10-dest.out (300,000 strings, 0 different) |
| p10_s8d.py, p10_s8d18.py | s8d*.out |
| p10_n8.py, p10_n9.py, p10_diag.py | n8.out, n9.out, diag.out |
