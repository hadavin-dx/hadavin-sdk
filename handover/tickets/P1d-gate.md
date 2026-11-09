# Package ticket P1d-gate: the client profile (pilot or prod) can start although the redaction fixes P1d, P1d-learn, P2d-2, P1d-b and P1d-c have not landed, or with a key-length floor that skips 9-character secrets. DRAFT revision 2 (plan review round 9 not yet run)

**Status (2026-11-09 UTC; IST = UTC+5:30):** text only, no code. Split from P1d by lead ORDER 177 (q386: "marker gate and canaries = small P1d-gate"; keep 4 markers; ONE start-up canary per distinct failure class, with a class-to-canary table the reviewer checks). Contents moved from P1d rev 7 precondition 5, round-7 resolve G10, mutants M22, M28, M31. Rev 2 applies `handover/reviews/P1d/round8-resolve.md` (merge order, the canary table, test facts). Code facts R were read on `core/cloud-handover` (`6d8699a`, `app.py:186-200`; `e03f847`, `app.py:83-98`); everything about P1d's and P1d-learn's names is their ticket text (P1d rev 9, P1d-learn rev 2), UNVERIFIED until they are built. Marker: CODE-LAST v1. Under 250 lines.

## The problem in plain words
Several separate packages close redaction holes (P1d, P1d-learn, P2d-2, P1d-b, P1d-c). Until all of them have landed, no real client data may go through the software (ORDER 165 M6, 167, 168, 173). Today nothing stops someone from starting the software for a client with one of them missing. This package makes the start refuse, with a message that names what is missing, and runs four tiny self-tests at start ("canaries") that prove the most important checks really work in the build that is starting.

## Words used (defined once)
- **Client profile** = a configuration whose stage is `pilot` or `prod` (`deferred.LIVE`; R449 stage names; `Config.environment` still spells the demo stage `dev` until the rename PR of ORDER 178 q389 (1), which is not this package's). **Demo stage** starts without any of this.
- **Marker** = a module-level boolean in `guard/runmap.py`, set to `True` by the package it names when that package merges. A marker proves a package is PRESENT, not that it works.
- **Canary** = one redaction run at start on a made-up split key built from parts, whose expected result is fixed. A canary proves a check WORKS in this build. Markers and canaries are both required; neither is derived from the other (round-7 G10).
- **Floor** = `evidence.redaction.min_key_chars` (P1d setting): known values shorter than it are not checked.

## Design
In `app.build`, after `load_config` and `runmap.apply_settings`, when `cfg.environment in deferred.LIVE`, in this order (each refusal is a `ConfigError`, which `app.build` already raises for refusals, R):
1. **Markers:** refuse with `ConfigError("redaction packages not applied: <missing names, comma separated>")` unless `getattr(runmap, name, False) is True` for every name in `REQUIRED_MARKERS = ("P1D_APPLIED", "P1DL_APPLIED", "P2D2_APPLIED", "P1DB_APPLIED", "P1DC_APPLIED")` (a tuple in `app.py`, one place).
2. **Floor:** refuse `min_key_chars > 8` with `ConfigError("redaction floor above 8 is refused in the client profile")`.
3. **Canaries:** `app._startup_canaries() -> None`, a pure function (no store, no channel, no network, no model call), called inside `if live:` directly after the existing pilot/prod refusals (`app.py:84-98`) and the two checks above, before the store and the channel are built. Each canary failure is `ConfigError("start-up canary failed: <canary id>")`; never any text. A canary's own withhold is logged at INFO (`source="canary"`, P1d `_withhold`), so the operator's WARNING lines stay a signal (round-8 N8).

**Class-to-canary table** (one canary per distinct failure class; a class is a way the redaction can be broken in a running build while the marker is still true):
| canary id | failure class it catches | input (built from parts) | pass condition | why not merged with another |
|---|---|---|---|---|
| C-KNOWN | the residue rule for KNOWN values does not withhold (P1d `_finish`, views, finder, default-mode wiring, `apply_settings` values) | a fresh `RunMap`; call 1 `"password=" + SV` through `runmap.redact_text(..., source="canary")`; call 2 `SV_A + "**" + SV_B` (P1d literals, built from parts) | call 2: `runmap.is_withheld(result)` | the only canary on the known-value rule and on the default (withhold) mode; round-8 M5: no other canary fails when `_finish` is broken |
| C-CARD | the card path does not raise (raise-mode wiring of `clean`; `LookalikeCopy` swallowed) | P1d's `KVS` through `channel.clean(..., source="canary")` | raises `runmap.LookalikeCopy` | a different entry and mode; P1d mutants M19, M40 break only this |
| C-LEARN | the learning pass of the redactor's patterns is off although `P1DL_APPLIED` is true | `"key " + "AKIA**" + "IOSFODNN7EXAMPLE" + "** here"` through `redact_text` with a fresh `RunMap` | `is_withheld(result)` | the only canary on `find_matches` over the learning views |
| C-AWS | the AWS-style rule is off although `P1DL_APPLIED` is true | `("AKIA" + "IOSFODN2" + "7EXAMPLE").lower()` through `redact_text` with a fresh `RunMap` | `is_withheld(result)` | the pattern pass cannot learn a lower-case key; only this canary fails when `_learn_aws` is not called |
**Dropped (each would catch a class already caught, or cannot run safely):** the rev-7 `request_approval` canary (it is a closure inside `app.build`, `app.py:194`, and would write to the real store if it failed; the no-save route is pinned by P1d's `test_withheld_summary_saves_no_request` and mutants M21, M39); a P1d-a canary (P1d-a has no setting or switch that a running build can turn off; `P1D_APPLIED` implies P1d-a, because P1d is built on it); P2d-2, P1d-b and P1d-c canaries (their tickets add one each if they have a runtime switch; this table is extended there, one row per new class).
**Cost:** five redaction runs of under 100 characters at start (BS-4 of P1d measures `redact_text`; expected well under 1 s).

## RUNG TABLE (scale of 2026-11-06)
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| marker and floor check | the client profile refuses without the packages | 2 (`app.build` `ConfigError` refusals) | R `app.py` | five names, one comparison | exact (presence only) | KEEP-CODE, about 15 lines |
| canaries | the checks work in the starting build | 2 (`redact_text`, `clean`) | P1d rev 9, P1d-learn rev 2 | four fixed inputs | exact for the four classes | KEEP-CODE, about 20 lines |
Rung 1 and 3 closed: a start-up refusal of our own process has no external tool. **80 percent (R448):** no higher rung meets either need (a refusal of our own start and a check of our own redactor); rung 2 is the existing `ConfigError` refusal path. Cost (estimate): 2 agent-hours.

## Goals and Non-Goals
**Goals.** (G1) The client profile does not start unless all five markers are true. (G2) It does not start with a floor above 8. (G3) It does not start if any canary fails. (G4) The demo stage is unchanged.
**Non-Goals.** (N1) Proving that P2d-2, P1d-b or P1d-c work (their own tickets and canaries). (N2) The `dev` to `demo` rename. (N3) Any change at run time after start.

## Tests (`tests/test_p1d_gate.py`, all driven through `app.build` with the pilot config of `tests/test_k3_pilot_env.py::pilot_cfg(tmp_path)`; an autouse fixture restores `runmap._SETTINGS` and every marker after each test)
- `test_client_profile_refuses_without_marker`, once per marker (markers not on the branch are injected with `monkeypatch.setattr(runmap, name, True, raising=False)`); the message names exactly the missing ones. fb.
- `test_foreign_markers_false_on_this_branch`: `P2D2_APPLIED`, `P1DB_APPLIED`, `P1DC_APPLIED` are absent or `False` in a fresh import. pb (true on the base too).
- `test_client_profile_refuses_floor_above_8` (9 refused, 8 starts). fb.
- `test_client_profile_refuses_when_canary_leaks`, once per canary id, with the check it targets patched off: C-KNOWN `runmap._finish` returns `shown` unchanged; C-CARD `channel.clean` returns its input; C-LEARN `runmap.redact.find_matches` returns `[]` inside `_learn_unknown`; C-AWS `runmap._learn_aws` returns `[]`; the message names the id and holds no part of the key. fb.
- `test_client_profile_starts_with_all_markers` (pb: the base has no gate, so it starts); `test_demo_stage_starts_without_markers` (pb); `test_canaries_touch_no_store_or_channel` (spies: zero calls; fb, new surface); `test_canary_withhold_logged_at_info` (fb).
- Fail-before: every test marked fb above fails on the base (no refusal exists), with prefix `NEW_SURFACE:` for names absent on the base; the pb tests pass there.

## Mutation plan (`tests/p1d_gate_mutants.py`; numbers kept from P1d rev 7; all required)
| mutant | planted change | killer |
|---|---|---|
| M22 | marker refusal removed | `test_client_profile_refuses_without_marker` |
| M28 | `_startup_canaries` not called | `test_client_profile_refuses_when_canary_leaks` |
| M31 | floor check removed | `test_client_profile_refuses_floor_above_8` |
| M47 | one name dropped from `REQUIRED_MARKERS` | the per-marker test for that name |
| M48 | floor compared with `>=` | the "8 starts" case |
| M49 | canaries run after the store is built | `test_canaries_touch_no_store_or_channel` |

## Template fields
- **Package id and name:** P1d-gate (DEFAULT PENDING LEAD 4), "client-profile start gate for the redaction packages". Branch `core/P1d-gate`. **Path class:** security; result rounds uncapped.
- **Depends on:** P1d and P1d-learn merged (`LookalikeCopy`, `is_withheld`, `apply_settings`, `source=`, `_learn_unknown`, `_learn_aws`). **Order: P1d-a, P1d, P1d-learn, P1d-gate** (round-8 M5: on a branch without P1d-learn, C-LEARN and C-AWS cannot run; NEEDS LEAD confirm, it changes DEFAULT 4). Until P2d-2, P1d-b and P1d-c merge, the client profile refuses to start, which is the intended state.
- **Files:** change `src/hadavin_sdk/app.py` (`REQUIRED_MARKERS`, the three checks, `_startup_canaries`), `CHANGELOG.md`; create `tests/test_p1d_gate.py`, `tests/p1d_gate_mutants.py`.
- **Interface:** `app.REQUIRED_MARKERS: tuple[str, ...]`; private `app._startup_canaries() -> None`.
- **Security and least-privilege notes:** no identity, right or secret; canary inputs are built from parts; refusal messages carry names and ids only.
- **Rollback:** tag `pre-P1d-gate`; removing the gate re-opens the client profile, so a rollback needs the lead's yes.
- **Reviewers:** fresh `egm-design` + `egm-codebase-details`; the reviewer checks the class-to-canary table (ORDER 177).
- **Done =** a fresh round finds no blocker or major; all gates green (as P1d-a); the lead merges.

## Evidence commands
As P1d-a's list (copied from `ci.yml`), with `tests/p1d_gate_mutants.py`; raw output to `handover/evidence/P1d-gate/evidence-<n>.md`.

## Owner-facing wording
CHANGELOG: "The software no longer starts for a client (pilot or production stage) until all five redaction fixes have landed, and it checks at start, on four made-up texts, that the hiding of split keys really works. The demo stage is unchanged."

## DEFAULT PENDING LEAD
(4) the name, the fifth marker `P1DL_APPLIED` (kept), and the order P1d-a, P1d, P1d-learn, P1d-gate (changed in rev 2).

## Revision log
Rev 1 (2026-11-09): split from P1d rev 7 (precondition 5, M22, M28, M31; ORDER 177); round-7 G10 applied (canaries mandatory, one per class, `request_approval` canary dropped, pure helper before store and channel, `test_foreign_markers_false_on_this_branch`); C-LEARN added for the fifth marker; M47-M49 added.
**Rev 2 (2026-11-09):** `round8-resolve.md` applied: order P1d-learn before P1d-gate (M5); C-MODEL replaced by C-KNOWN (known-value residue, two calls) and C-CARD on `KVS` (P1d has no learning since ORDER 180 (2)); C-LEARN split into C-LEARN (pattern pass) and C-AWS (AWS rule); patch targets named; canary placement after `app.py:84-98`; test config named; fail-before classes corrected (N-9); canary withholds at INFO (N8); 80-percent line (N7).
