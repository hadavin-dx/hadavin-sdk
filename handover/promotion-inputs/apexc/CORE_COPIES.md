# Temporary copies of core modules (one source of truth is the core)

Rule: generic controls are written ONCE, in the core (`hadavin-dx/hadavin-sdk`), and consumed from there. Until the core pull request
below is merged and this demo's pin moves, the demo keeps a byte-identical COPY so it can run offline. `core_copies.json` pins the sha256
of each core file, the open core pull request (`core_pr`: 50, on every row) and the full 40-character core commit it was taken from
(`pr_snapshot`: `153d2178b81c7f623a2e029930001da2e079df97`, branch `core/promote-apexc-review8`);
`tests/test_v9.py::test_the_core_copies_match_the_pinned_core_files` fails if a copy drifts (the only allowed difference is the one import
named in the pin).

Risk, stated plainly: that commit is on an UNMERGED core branch. If the core branch is rebased or force-pushed, the commit can vanish from
the core while the pin test still passes (it compares the copies to the pins, not to the live core). The CI `check` job therefore runs
`python tools/check_core_copies.py` against the pinned commit fetched from the public core repository (last step), so a vanished commit
fails the run. By hand: `python tools/check_core_copies.py <path to a core checkout>`.

## Two pins, one table (format as in the dealdesk demo)

`pyproject.toml` and `uv.lock` pin `hadavin-sdk` at `6608146` (a merged commit that has the core class table the tests read and none of the
modules below). `core_copies.json` now carries the SAME commit as its `core_commit` (the demo's own pin, so the sync tool's pin check agrees),
and each copied file names its own `pr_snapshot`: the unmerged core pull request commit its bytes came from (`153d2178b81c7f623a2e029930001da2e079df97`).
`tools/check_core_copies.py` and the CI step fetch each `pr_snapshot` and compare the files at it. Before this change the table's `core_commit`
was the PR commit, the sync tool reported `pin_table_disagrees` as an error, and the doc called that expected; it is fixed, not waived.
**Do not merge this demo before core pull request #50 is merged.**

## Behind the PR head

The copies equal core pull request #50 at `153d217` (round 5). The PR head has since moved to `f886a29` (round 6); the only copied file that
differs between the two is `egress_text.py` (45 changed lines). Re-sync steps when the demo needs round 6: copy that file, re-hash it in
`core_copies.json`, run `pytest`, `python mutation_check.py --record`, review the `mutant_kills.json` diff, update `acceptance.md` counts.
It is moot if #50 merges first (steps 1 to 4 of the procedure below replace the copies by the import).

## Merge procedure (in this order)

1. Merge core pull request #50 and note the merge commit (not the branch commit).
2. Set the `hadavin-sdk` `rev` in `pyproject.toml` and `uv.lock` and `core_commit` in `core_copies.json` to that one commit (and drop every `pr_snapshot`). Re-verify every
   "verified against hadavin-sdk 6608146" statement (`acceptance.md`, `gate_rules.md`, `spec_stage2.md`, `src/apexc/tools.py`,
   `tests/test_core_class.py`) and re-run the core class tests.
3. Move `hadavin-sdk` from the test group to `dependencies` in `pyproject.toml` (its comment says it is test-only today).
4. Re-run `tools/check_core_copies.py` against the merge commit, then delete the seven copies in the table below and import `hadavin_sdk`
   instead, in this order: textnorm, egress_text, config_view and stop_gate, rowstore, mutation judge.
5. Delete `core_copies.json`, `tools/check_core_copies.py`, the copy test in `tests/test_v9.py`, the CI core-copies step, the ruff exclude for
   the copies and this file.
6. Retarget or drop every mutant aimed at a deleted copy file in `mutation_check.py` and `mutant_kills.json`; the mutant count and the
   mutant-list hash change, so update `acceptance.md` and `README.md`.
7. Move tests of core-owned behaviour to the core (pull request #50 carries its own).
8. Run the sync check with the strict pin option (expect exit 0), wait for CI green on the pull request, then merge.

| Copy in this demo | Core module | Core change | Switch-over step |
|---|---|---|---|
| `src/apexc/_confusables.py` | `hadavin_sdk/guard/_confusables.py` | PR #50 | delete the copy (generated UTS #39 table; `textnorm.py` imports it) |
| `src/apexc/textnorm.py` | `hadavin_sdk/guard/textnorm.py` | PR #50 | delete the copy; `from hadavin_sdk.guard.textnorm import fold, squeeze` in `normalise.py` |
| `src/apexc/egress_text.py` | `hadavin_sdk/guard/egress_text.py` | PR #50 | delete the copy; import from `hadavin_sdk.guard.egress_text` in `tools.py` |
| `src/apexc/config_view.py` | `hadavin_sdk/runtime/config_view.py` | PR #50 | delete the copy; `config.py` imports `ConfigView`, `ConfigHolder` from the core |
| `src/apexc/stop_gate.py` | `hadavin_sdk/runtime/stop_gate.py` | PR #50 | delete the copy; `executor.py` and `config.py` import `StopGate`, `EffectBlocked` from the core |
| `src/apexc/rowstore.py` | `hadavin_sdk/runtime/rowstore.py` | PR #50 | delete the copy; `fakes.py` imports `copy_row`, `json_keys_ok` from the core |
| `mutation_judge.py` | `hadavin_sdk/testing/mutation.py` | PR #50 | delete the copy; `mutation_check.py` imports `hadavin_sdk.testing.mutation` |

Not copies, and what happens to them:

| Demo code | Status | Decision |
|---|---|---|
| `src/apexc/executor.py` | demo logic, not a copy | the core has `actions/executor.py`, a different thing (the governed-action executor); the name match is a coincidence. At the pin move decide whether the core executor can host the release logic; until then this file is the demo's own |
| `Audit.append_capped`, `deny_audit` (`fakes.py`) | demo-local | the core has `audit/capped.py` (PR #50, needs the core `AuditEvent`); switch to it at the pin move |
| `Audit` (per-tenant hash chain, `fakes.py`) | demo-local | the core has `audit/chain.py` (signed chain with sinks); at the pin move compare formats and use the core chain |
| `ControlState`, `guarded`, `ReleaseStore` (`rules.py`), `Intake` (`intake.py`), the audit chain | demo-local, named follow-up | generic patterns (kill switch plus caps state, the per-call error choke point, one release row per key, a durable inbound ledger, a per-tenant chain); candidates for a core promotion with their own design review, not decided here |
| `config.py` (`ConfigHolder` watch/effect wiring, the digest, the last-known-good policy) | demo wiring over the core holder | replaced by the core `StopGate` at the switch-over |
| `src/apexc/intake.py` | demo-local inbound ledger (`allowed_local`) | message-id reuse ends `rejected:<reason>` here, `rejected` in dealdesk, `dead_lettered` in intake; folded into one rule when the core gets an inbox kind (`runtime/inbox.py`) |
| `src/apexc/fakes.py`, `src/apexc/normalise.py` | demo-local fakes and domain text/money rules (`allowed_local`) | the in-memory chain becomes a core `MemoryChain` kind if one is promoted; the look-alike table in `normalise.py` is replaced by the copied fold at the pin move |
| `src/apexc/audit_event.py` | `hadavin_sdk.models.AuditEvent` (one name) | stand-in (`allowed_local`) | the copied `stop_gate.py` imports `AuditEvent` for an audit row the gate writes only when it is given a `Limits` object (this demo gives none); delete the stand-in and the import rewrite when the copy is replaced by the core import |
