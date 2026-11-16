# PR H ticket rev 2: raw outputs of the ticket author's runs (2026-11-11, about 16:20 to 17:00 UTC / 21:50 to 22:30 IST)

These are the TICKET AUTHOR's own runs against a clean main worktree (2a8c2aac) and a throwaway prototype of the design.
They are NOT independent evidence: the prototype is the author's code. Made-up data only; secrets in the scripts are built from parts.
Environment for every run: `cd /home/user/build/prh-author/main && env -i PATH=/usr/bin:/bin HOME=/root /home/user/build/prh-author/venv/bin/python <script> [mode]`.
Modes: `main` (no patch), `proto` (rev-1 design as monkeypatches, `scripts/prh_proto.py`), `protofix` (+ case-790 fix, `scripts/fix790.py`), `protofixes` (+ every rev-2 change, `scripts/fixes.py`).
Pytest runs: `env -i ... PYTHONPATH=<errata dir> python -m pytest -q -p no:cacheprovider -p <plug_*> -m "not live and not perf" <files>`.

| File | What | Command |
|---|---|---|
| c790.out | case 790 reproduced under `proto`; main does not leak | `scripts/c790.py` |
| c790d.out | the cause: earlier-mask spellings applied in list order | `scripts/c790d.py` |
| fuzz-plug_proto.log / fuzz-plug_proto_fix.log / fuzz-plug_main_fix.log | `tests/test_k5_round12_fuzz.py` under proto (1 failed), proto + fix (5 passed), main + fix (5 passed) | pytest with `-p plug_proto`, `plug_proto_fix`, `plug_main_fix` |
| target-files.txt | the 43 test files that import the redaction modules | grep, see ticket 8.3 |
| targeted-proto-fix.log | the 43 files under proto + case-790 fix | `-p plug_proto_fix` |
| targeted-proto-fixes-run1.log | first run under every rev-2 change: 3 failures (author's prototype slip, ticket 8.3) | `-p plug_proto_fixes` |
| targeted-proto-fixes-rerun3.log | the two failing files + the round-12 fuzz file after the correction | `-p plug_proto_fixes` |
| targeted-proto-fixes-run2.log | the 43 files after the first correction (before the in-round created-shape rule) | `-p plug_proto_fixes` |
| targeted-proto-fixes.log | the 43 files under the FINAL rev-2 prototype | `-p plug_proto_fixes` |
| repro-main.out / repro-proto.out / repro-protofix.out / repro-protofixes.out | design-review inputs M1 to M6, `_first_decoded`, the OSC/U+009C row | `scripts/repro.py <mode>` |
| check-protofixes.out | the leak rows L1-L12, G1-G3 and forgery rows of ticket section 2 under every rev-2 change | `scripts/check2.py` |
| f1b-error-reason.out | the real output of F1b on `error_reason` (the check script flags it only because that path's map is internal) | `scripts/f1b.py` |
| cost-main.out / cost-protofixes.out (final prototype; the first rev-2 run's file was overwritten, its two F1e lines are quoted in ticket W2) | forgery on callers without the escaping step; rough cost at the cap, 1 run per row, machine shared with other agents | `scripts/cost2.py <mode>` |
| di-312-313.out | Default_Ignorable: formula vs perl table on Python 3.12.3 and 3.13.18; perl version; hash of the range file | `scripts/di312.py` |
| default_ignorable_perl5382_unicode1500.txt | the range file the builder copies into tests/fixtures/ (SHA-256 in di-312-313.out) | perl one-liner of ticket W6, converted to ranges |

Scripts are in `scripts/` (copies of `/home/user/build/prh-author/errata/`); `c790b.py` printed to the terminal only (its reduced-input finding is repeated in `c790d.out`).
