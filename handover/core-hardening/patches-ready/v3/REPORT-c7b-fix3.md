# C7b fix pass 3 report (evidence builder; not a review). 2026-11-16, UTC. Raw files: `v3/raw-c7b-fix3/`. Patch under test: `v6-extra/FIX-id-vs-command-withheld.patch` (sha256 `12e4be6f...`, unchanged, matches its `.sha256` file).

## Failed, not checked, or not closed (read first)
1. **The pass 2 claim "env -i uv run worked with no network" is withdrawn.** Network was NOT absent. Inside the same `env -i PATH HOME` environment, `curl https://pypi.org/simple/pytest/` returned http 200 (`network-facts.log`, section B). So the earlier run did not prove a no-network run, and my pass 2 sentence had no log behind it. What the logs do show is below (M-A2).
2. **Pass 1's "env -i uv run cannot build a venv" is partly reproduced.** On a tree with no `.venv`, `env -i PATH HOME uv run ...` exited rc 1 with `invalid peer certificate: UnknownIssuer` while fetching `https://pypi.org/simple/uv-build/` (`uv-run-env-i-tree-without-venv.log`). The log shows the certificate error and the hint `--system-certs`. My explanation, that `env -i` drops the session's certificate settings (`UV_NATIVE_TLS`, `SSL_CERT_FILE`) so uv could not trust the server, is an inference: I did not run a test that changes only those settings. I did not try other certificate settings; the hint in the log says `--system-certs`. So the full-suite command only works after a prior `uv sync` with the session settings. That is how the base run and these runs were done. No change to any result below.
3. Not run, same as pass 2: the 455 Postgres tests (skipped, no Postgres here); (a mutation run of the lookahead was done afterwards, see the last section); the fix on the real head `de6b574` (everything is on base `b4cce5b`); the v5 tree. I ran no ruff or bandit again (nothing in `src/` changed by me). The patched gate.py hash in this pass's trees is `0dbf8c4a...`; I did not save pass 2's gate.py hash, so I cannot say it equals pass 2's file.
4. The first `uv sync -v` here (`uvsync-p-verbose.log`) also used the session settings (proxy variable present). It shows installs from the uv cache; it does not prove the network was unused (see M-A2).
5. The scratch trees' fresh `.venv` was built by this pass, so the package versions came from uv's cache of earlier passes; the versions are in `uvsync-p-verbose.log` (`+ name==version` lines).

## M-A1 closed: the 9514 run is tied to the shipped gate.py (`full-run.log`, `final-gate-hashes.txt`, `tree-manifest.log`)
- Two trees were built the same way (`tree-manifest.log`): `git archive b4cce5b`, `handover/` removed, `git init` and one commit, patches C-01, A-01, G5 (all rc 0), then the fix (rc 0, gate.py hunk offset 5). No `.orig` or `.rej`. 14 modified, 4 new files in each. Tree P is the one that was run; tree Q is the clean reference that was never run or edited. Both are the result of the fix3 script applying the patches (the tie is "patch applied by the fix3 script", not a hash of an independently built file). Fresh-tree check of the three v3 patches, the git archive tree id and the forward and reverse apply: `raw-c7b-fix3/fresh-tree-hashes.log` (`sha256sum -c` OK for C-01, A-01, G5-wording and the fix; tree id `00c5cffd...` for `b4cce5b`; gate.py after v3 patches `8baee570...`, after the fix `0dbf8c4a...`).
- gate.py sha256 right after the build, P and Q: both `0dbf8c4ad9862355c99e37b62f44b64840bad638e87436f63d945617b4a8641a`.
- Full run on P (10:50:03Z to 10:54:06Z): gate.py hash BEFORE and AFTER both `0dbf8c4a...`; test file `test_g4_ids_not_withheld.py` hash BEFORE and AFTER both `a27dc6e60b4387308c888b458779fbc258a0f9af2fe73c96fb6271475114ccf7`. Command, exactly: `env -i PATH=$PATH HOME=$HOME uv run --all-extras --group test pytest -q -p no:cacheprovider`. Result: **9514 passed, 455 skipped, 0 failed, PYTEST_RC=0, 240.35 s.** Env dump holds PATH and HOME only (`full-run-envdump.txt`, written by a separate `env -i` call, not by the pytest process itself). Same-hash P and Q (`final-gate-hashes.txt`) show repeatability of the patch application, not correctness of the patch; correctness is what the 23 tests and the old-code run show.
- The old-code and restore steps ran AFTER the full run (below), so the full run could not be affected by them. After everything, P and Q gate.py hashes are still equal (`final-gate-hashes.txt`).
- Import path check: `uv run python -c "import ...gate"` prints `.../f3/p/src/hadavin_sdk/approvals/gate.py`, so the tests read the tree's `src/` copy, not an installed copy (`network-facts-uv.log`, section 1).

## g4 file alone, -v (`g4-v-new-code.log`)
`env -i PATH HOME uv run --all-extras --group test pytest -v -p no:cacheprovider tests/test_g4_ids_not_withheld.py`, 10:54:13Z: **23 PASSED lines** (grep count 23), 0 FAILED or ERROR, `23 passed in 1.21s`, rc 0; gate.py hash before and after the run is `0dbf8c4a...`.

## Old code, revert and restore with hashes (`old-code-run.log`)
Old gate.py was made on a copy OUTSIDE tree P: the shipped fix reverse-applied (`patch -R`, rc 0) to a copy of Q's gate.py: sha256 `8baee5702e06d3d482c08cc9e77df171979510c9fb7d09c4d5f9aec6edb88b0a`. Applying the fix forward again to that copy gives `0dbf8c4a...` (so the reversal is exact for gate.py). The raw output of `patch -R` and the forward re-apply, with the gate.py hashes, was missing in the first version of this report (the folders were deleted); it is now in `raw-c7b-fix3/fresh-tree-hashes.log`, from a fresh tree, both rc 0, hashes `8baee570...` after `-R` and `0dbf8c4a...` after the forward re-apply.
| step | time (UTC) | gate.py sha256 in P |
|---|---|---|
| T1 before revert | 10:54:29 | `0dbf8c4a...` (equals Q) |
| T2 old code copied in | 10:54:29 | `8baee570...` |
| old-code g4 run (-v) | | **11 failed, 12 passed**, rc 1 |
| T3 after that run | 10:54:30 | `8baee570...` |
| T4 restored from a backup copy | 10:54:30 | `0dbf8c4a...`, `cmp` with Q: identical |
| restored-code g4 run (-v) | | **23 passed**, rc 0 |
| T5 final | 10:54:32 | `0dbf8c4a...` |
The test file is the shipped one throughout. The 11 failures and 12 passes match pass 2's numbers.

## M-A2 closed as a statement of facts, not as a no-network claim (`network-facts.log`, `network-facts-uv.log`, `net-env-before.txt`, `uvsync-p-verbose.log`, `uv-run-env-i-offline.log`)
What WAS shown:
- Network facts: the session has an outbound proxy variable; `env -i` removes it (0 proxy variables inside `env -i`); a direct curl to pypi.org inside `env -i` still returned http 200. So network was reachable during the earlier runs.
- `env -i ... uv run --offline -v ... python -c ...` on P: rc 0, and no request line other than cache hits in its log (`uv-run-env-i-offline.log`). This shows that on a tree that has a synced `.venv`, `env -i uv run` works when uv is forbidden to use the network.
- `uv sync -v` on P (session settings): log shows "Found fresh response" cache hits and installs from the uv cache.
What was NOT shown: that the pass 2 full run (or this pass's full run) was done with the network cut; neither run was. The full run used the plain command, with network reachable, no uv log of it was kept beyond pytest's output, so I cannot say whether uv sent any request during that run. The claim in M-A that matters is only: the patched tree runs with the same command as the base after a prior sync. That is what is shown.

## Added after review round 4 (2026-11-16, UTC)
- Mutation check of the lookahead (`raw-c7b-fix3/mutation-lookahead.log`, scratch copy only, patch bytes untouched): unmutated 23 passed; `{32,}` changed to `{33,}`: **10 failed, 13 passed**; changed to `{31,}`: **1 failed, 22 passed** (only the 31-hex boundary case, as it should). The restored gate.py hash is `0dbf8c4a...` again. The `sed` also changed the same text inside the patch's own comment line (grep count 2); that does not change behaviour. Run with the repo's existing Python and `PYTHONPATH` pointing at the scratch `src/` (import path printed in the log), not with `uv run`.
- Nit, described only (patch not changed, sha256 `12e4be6f...` stays): the test at patch lines 124-126 (`"Remove-ec2" + "0"*32 + "-suffix"`, kept) also passes on the old code, and its comment "same" misleads: it pins nothing the fix changed. Suggested change for a later pass: delete that case or rewrite the comment.
- Describe-only, from the codebase review: the rule released is "32 or more hex digits ending at a non-word character (for example a hyphen)", not strictly "an id". A module word followed by a digit or underscore (`Remove-EC2_x`, `Remove-S32`) is never withheld by this rule; not caused by this patch.
- Fresh-tree hashes, raw patch -R and forward re-apply output: `raw-c7b-fix3/fresh-tree-hashes.log`.

## Housekeeping
Nothing in `src/` or `tests/` of the real repository was edited; nothing committed or pushed (only files under `handover/core-hardening/patches-ready/v3/` were added). Processes: the full run and my wait helper finished; none left running. Disk free was above 5 GB throughout (8.7 GB at start). Scratch folder `f3` (trees P, Q, rev, fwd, logs; deleted after this report). Banned-term scan: see the last line of `raw-c7b-fix3/banned-scan.txt`. R-numbers: only through the preamble (no bible lookup; narrow evidence task). Token use: not measured by me.
