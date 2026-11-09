# Package ticket P1d-gate: the client profile (pilot or prod) can start although the redaction fixes P1d, P1d-learn, P2d-2, P1d-b and P1d-c have not landed, or with a key-length floor that skips 9-character secrets. DRAFT revision 1 (plan review round 1 not yet run)

**Status (2026-11-09 UTC; IST = UTC+5:30):** text only, no code. Split from P1d by lead ORDER 177 (q386: "marker gate and canaries = small P1d-gate"; keep 4 markers; ONE start-up canary per distinct failure class, with a class-to-canary table the reviewer checks). Contents moved from P1d rev 7 precondition 5, round-7 resolve G10, mutants M22, M28, M31. The fifth marker `P1DL_APPLIED` is DEFAULT PENDING LEAD (4). Code facts R were read on `core/cloud-handover` `6d8699a` (`app.py:186-200`); everything about P1d's names is P1d rev 8 text, UNVERIFIED until P1d is built. Marker: CODE-LAST v1. Under 250 lines.

## The problem in plain words
Several separate packages close redaction holes (P1d, P1d-learn, P2d-2, P1d-b, P1d-c). Until all of them have landed, no real client data may go through the software (ORDER 165 M6, 167, 168, 173). Today nothing stops someone from starting the software for a client with one of them missing. This package makes the start refuse, with a message that names what is missing, and runs two or three tiny self-tests at start ("canaries") that prove the most important checks really work in the build that is starting.

## Words used (defined once)
- **Client profile** = a configuration whose stage is `pilot` or `prod` (`deferred.LIVE`; R449 stage names; `Config.environment` still spells the demo stage `dev` until the rename PR of ORDER 178 q389 (1), which is not this package's). **Demo stage** starts without any of this.
- **Marker** = a module-level boolean in `guard/runmap.py`, set to `True` by the package it names when that package merges. A marker proves a package is PRESENT, not that it works.
- **Canary** = one redaction run at start on a made-up split key built from parts, whose expected result is fixed. A canary proves a check WORKS in this build. Markers and canaries are both required; neither is derived from the other (round-7 G10).
- **Floor** = `evidence.redaction.min_key_chars` (P1d setting): known values shorter than it are not checked.

## Design
In `app.build`, after `load_config` and `runmap.apply_settings`, when `cfg.environment in deferred.LIVE`, in this order (each refusal is a `ConfigError`, which `app.build` already raises for refusals, R):
1. **Markers:** refuse with `ConfigError("redaction packages not applied: <missing names, comma separated>")` unless `getattr(runmap, name, False) is True` for every name in `REQUIRED_MARKERS = ("P1D_APPLIED", "P1DL_APPLIED", "P2D2_APPLIED", "P1DB_APPLIED", "P1DC_APPLIED")` (a tuple in `app.py`, one place).
2. **Floor:** refuse `min_key_chars > 8` with `ConfigError("redaction floor above 8 is refused in the client profile")`.
3. **Canaries:** `app._startup_canaries() -> None`, a pure function (no store, no channel, no network, no model call), run before the store and the channel are built. Each canary failure is `ConfigError("start-up canary failed: <canary id>")`; never any text.

**Class-to-canary table** (one canary per distinct failure class; a class is a way the redaction can be broken in a running build while the marker is still true):
| canary id | failure class it catches | input (built from parts) | pass condition | why not merged with another |
|---|---|---|---|---|
| C-MODEL | the model path does not withhold a split known or learned key (P1d views, learning on patterns, default mode wiring, `apply_settings` values) | `"key " + "AKIA**" + "IOSFODNN7EXAMPLE" + "** here"` through `runmap.redact_text(..., source="canary")` with a fresh `RunMap` | `runmap.is_withheld(result)` | the only canary on the default (withhold) mode |
| C-CARD | the card path does not raise (raise-mode wiring of `clean`; `LookalikeCopy` swallowed) | the same text through `channel.clean(..., source="canary")` | raises `runmap.LookalikeCopy` | a different entry and a different mode; C-MODEL passing does not prove `clean` raises (M19, M40 of P1d break only this) |
| C-LEARN | the AWS-style rule is not active although its marker is true | `"AKIA" + "IOSFODN2" + "7EXAMPLE"` in lower case through `redact_text` | `is_withheld(result)` | C-MODEL's key is learned by the plain pattern on a view, not by this rule; only this canary fails when the rule is off |
**Dropped (each would catch a class already caught, or cannot run safely):** the rev-7 `request_approval` canary (it is a closure inside `app.build`, `app.py:194`, and would write to the real store if it failed; the no-save route is pinned by P1d's `test_withheld_summary_saves_no_request` and mutants M21, M39); a P1d-a canary (P1d-a has no setting or switch that a running build can turn off; `P1D_APPLIED` implies P1d-a, because P1d is built on it); P2d-2, P1d-b and P1d-c canaries (their tickets add one each if they have a runtime switch; this table is extended there, one row per new class).
**Cost:** three redaction runs of under 100 characters at start (BS-4 of P1d measures `redact_text`; expected well under 1 s).

## RUNG TABLE (scale of 2026-11-06)
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| marker and floor check | the client profile refuses without the packages | 2 (`app.build` `ConfigError` refusals) | R `app.py` | five names, one comparison | exact (presence only) | KEEP-CODE, about 15 lines |
| canaries | the checks work in the starting build | 2 (`redact_text`, `clean`) | P1d rev 8 | three fixed inputs | exact for the three classes | KEEP-CODE, about 15 lines |
Rung 1 and 3 closed: a start-up refusal of our own process has no external tool. Cost (estimate): 2 agent-hours, one plan round.

## Goals and Non-Goals
**Goals.** (G1) The client profile does not start unless all five markers are true. (G2) It does not start with a floor above 8. (G3) It does not start if any canary fails. (G4) The demo stage is unchanged.
**Non-Goals.** (N1) Proving that P2d-2, P1d-b or P1d-c work (their own tickets and canaries). (N2) The `dev` to `demo` rename. (N3) Any change at run time after start.

## Tests (`tests/test_p1d_gate.py`, all driven through `app.build` with a test config; an autouse fixture restores `runmap._SETTINGS` and every marker after each test)
- `test_client_profile_refuses_without_marker`, once per marker (markers not on the branch are injected with `monkeypatch.setattr(runmap, name, True, raising=False)`); the message names exactly the missing ones.
- `test_foreign_markers_false_on_this_branch`: `P2D2_APPLIED`, `P1DB_APPLIED`, `P1DC_APPLIED` (and `P1DL_APPLIED` before P1d-learn merges) are absent or `False` in a fresh import.
- `test_client_profile_refuses_floor_above_8` (9 refused, 8 starts).
- `test_client_profile_refuses_when_canary_leaks`, once per canary id: the check it targets is monkeypatched off (C-MODEL: `redact_text` returns its input; C-CARD: `clean` returns its input; C-LEARN: the rule returns nothing); the message names the id and holds no part of the key.
- `test_client_profile_starts_with_all_markers`; `test_demo_stage_starts_without_markers`; `test_canaries_touch_no_store_or_channel` (spies: zero calls).
- Fail-before: every test above except the demo-stage test fails on the base (no refusal exists), with prefix `NEW_SURFACE:` for names absent on the base.

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
- **Package id and name:** P1d-gate (DEFAULT PENDING LEAD 4), "client-profile start gate for the redaction packages". Branch `core/P1d-gate`. **Path class:** security; **extended review (no round cap): yes** for results; one plan round (DEFAULT PENDING LEAD 2).
- **Depends on:** P1d rev 8 merged (`LookalikeCopy`, `is_withheld`, `apply_settings`, `source=`). Order: P1d-a, P1d, P1d-gate, P1d-learn (DEFAULT 4). Until P1d-learn and the other three merge, the client profile refuses to start, which is the intended state.
- **Files:** change `src/hadavin_sdk/app.py` (`REQUIRED_MARKERS`, the three checks, `_startup_canaries`), `CHANGELOG.md`; create `tests/test_p1d_gate.py`, `tests/p1d_gate_mutants.py`.
- **Interface:** `app.REQUIRED_MARKERS: tuple[str, ...]`; private `app._startup_canaries() -> None`.
- **Security and least-privilege notes:** no identity, right or secret; canary inputs are built from parts; refusal messages carry names and ids only.
- **Rollback:** tag `pre-P1d-gate`; removing the gate re-opens the client profile, so a rollback needs the lead's yes.
- **Reviewers:** fresh `egm-design` + `egm-codebase-details`; the reviewer checks the class-to-canary table (ORDER 177).
- **Done =** a fresh round finds no blocker or major; all gates green (as P1d-a); the lead merges.

## Evidence commands
As P1d-a's list (copied from `ci.yml`), with `tests/p1d_gate_mutants.py`; raw output to `handover/evidence/P1d-gate/evidence-<n>.md`.

## Owner-facing wording
CHANGELOG: "The software no longer starts for a client (pilot or production stage) until all five redaction fixes have landed, and it checks at start, on three made-up keys, that the hiding of split keys really works. The demo stage is unchanged."

## DEFAULT PENDING LEAD
(2) one plan round; (4) the name, the fifth marker `P1DL_APPLIED`, the order.

## Revision log
Rev 1 (2026-11-09): split from P1d rev 7 (precondition 5, M22, M28, M31; ORDER 177); round-7 G10 applied (canaries mandatory, one per class, `request_approval` canary dropped, pure helper before store and channel, `test_foreign_markers_false_on_this_branch`); C-LEARN added for the fifth marker; M47-M49 added.
