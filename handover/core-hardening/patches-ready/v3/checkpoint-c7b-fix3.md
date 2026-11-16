# C7b fix pass 3 checkpoint (2026-11-16, UTC)
- Done: full suite on the patched tree 9514 passed, 455 skipped, 0 failed (rc 0); g4 file 23 passed; old code (gate.py `8baee570...`) 11 failed, 12 passed; restored gate.py `0dbf8c4a...`; patch sha256 `12e4be6f...` unchanged.
- Hashes: v3 patches `sha256sum -c` OK; git archive tree id of `b4cce5b` `00c5cffd...`; patch -R and forward re-apply logged in `v3/raw-c7b-fix3/fresh-tree-hashes.log`.
- Withdrawn: "env -i uv run worked with no network" (network was reachable); "venv from nothing untested" now reproduced as rc 1 (certificate error). Banner added to `REPORT-c7b-fix2.md`.
- Mutation check of the lookahead: `{33,}` 10 failed, `{31,}` 1 failed (`raw-c7b-fix3/mutation-lookahead.log`).
- Not done: Postgres tests, fix on the real head `de6b574`, full suite on v5.
- Next: lead's independent result review. Report: `v3/REPORT-c7b-fix3.md`.
