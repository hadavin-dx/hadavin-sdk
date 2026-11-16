Status: resolved

# Goldfish Annotated Review Report (round 2)

**Target:** `/home/user/build/snap/pdbind-6e6ae211/DIFF.patch` (full file), part 2 (network bind guard), head 6e6ae211. Security / mode-safety path.
Reviews: `pdbind-6e6ae211-design-r2.md` (0 Blocker, 1 Major, 3 Minor, 2 Nit) and `pdbind-6e6ae211-codebase-r2.md` (0 Blocker, 0 Major, 6 Minor, 6 Nit). Independent evidence: `handover/evidence/PD-bind/6e6ae211/RESULTS.md` (landed; full pytest has no single green run: 1 failure `dblink-connect`, an environment slip, the file alone 253 passed; stage mutants 37 of 37; bind mutants 39 of 39).
Decisions: no ESCALATE items. A second fresh round is REQUIRED after the fix batch (security path, 1 Major).

## Class (a): every route by which a real service can reach the approvals must be counted — Major, NEEDS CONFIRMING ROUND

### [Issue 1] [`design`] - Severity: Major (M1)
*   **Affected Scope:** receiver.py:106-111, requests.py:73-74, app.py:62-75 and 170-181
*   **Discrepancy:** `approvals.config is config` proves the same Config object, not the services the approvals hold. `build()` overrides (`channel=`, `llm=`, `detector=`, `tools=`, `sources=`) are public API; a stand-in config plus an injected real service gives `real_services` empty and a public bind with no reason. `Approvals(real_channel, ..., config=stand_in)` is accepted; `Approvals.config` is a mutable attribute.
*   ***AI Suggestion:*** PROPOSE FIX (confirming round required)
*   ***Justification:*** Valid and the one soft spot of the least-privilege story. The class is "a service that reaches the approvals by a route other than the config". The fix goes at the one choke point (the two places that make an `Approvals`: `build()` and the constructor), not at `serve`.
*   ***FIX BRIEF:***
    *   File: `src/hadavin_sdk/app.py` (`build`), `src/hadavin_sdk/approvals/requests.py` (`Approvals`), `src/hadavin_sdk/bindguard.py` (`real_services`), `src/hadavin_sdk/approvals/receiver.py` (`serve`).
    *   Change: (1) `build()` records every injected override as a named entry (`overrides: tuple[str, ...]`) on `Approvals`; (2) `real_services` counts each override whose object is not a known stand-in class (stand-in test by an explicit allowlist of the core's own fake classes, never by name text) and counts any override of `tools` or `sources` as real unless empty; (3) `Approvals` gets `config` and `overrides` as set-once, read-only (frozen dataclass field or property without setter); a hand-built `Approvals` has `config=None` and is refused by `serve` (already true) with the refusal text naming that; (4) `serve` additionally refuses when `approvals.overrides` contain a real service and no reason is given, and says which override.
    *   Tests (`tests/test_bindguard.py`): a stand-in config with an injected real-class channel, a real source, a `tools` dict, a real llm each bind `0.0.0.0` without a reason: refused; with a valid reason: bound to 127.0.0.1 in the test; assigning `approvals.config = other` raises; `Approvals(real, ..., config=stand_in)` built by hand is refused by `serve`.
    *   Mutants (`tests/bind_mutants.py`): one per rule: drop the override recording; treat all overrides as stand-in; make `config` writable again; skip the override check in `serve`.
    *   Fail-before: run the new tests on head 6e6ae211 src: all must fail (the injected-service bind succeeds there).
    *   Alternative if the fix proves too wide: narrow docstring and CHANGELOG ("injected overrides are not seen") and pin the limit; NOT recommended (the lead's rule is fail-closed).

## Class (b): reason check and the IN_PROCESS claim — Minor, batch only

### [Issue 2] [`design`] - Severity: Minor (m3)
*   **Scope:** bindguard.py:349-360. A one-character reason passes and goes to the log only.
*   ***AI Suggestion:*** PROPOSE FIX (batch only)
*   ***FIX BRIEF:*** Require at least 10 printable characters (keep 200 maximum); say in docstring and CHANGELOG that the reason is logged at WARNING and is not an audit record. Tests: 9 characters refused, 10 accepted; B-mutant on the minimum. Fail-before: the 9-character test fails on the head.

### [Issue 3] [`design`] - Severity: Minor (m4)
*   **Scope:** table.py:216-236 (IN_PROCESS reasons).
*   ***AI Suggestion:*** PROPOSE FIX (batch only)
*   ***FIX BRIEF:*** Add a test that the receiver module has exactly one route and that the handler reaches the signer only through the signature check (AST read of `receiver.py`: the only call path from the handler body to `on_decided`/`receive` passes `verify`); if that is too brittle, state in the reason text that the claim depends on config being the whole truth and rely on Issue 1. Mutant: add a second route.

## Class (c): CHANGELOG and wording — batch only

### [Issue 4] [`codebase`] - Severity: Minor (m1) and Nits n1, n2, n4
*   **Scope:** CHANGELOG (upgrade step, "Changed" entry), receiver.py:103, netguard docstring, `guard/http.py`/`llm/common.py` wording.
*   ***AI Suggestion:*** PROPOSE FIX (batch only)
*   ***FIX BRIEF:*** Label the signature change `Breaking:`; state that old positional `serve(approvals, host, port)` raises TypeError, that a hand-built `Approvals` must now carry `config=` (or is refused), and the read-only attribute from Issue 1; restore the `ThreadingHTTPServer` return annotation (or give the reason); reword "asked by guard/http.py" to "shares the one list"; split the long entry. Test: a CHANGELOG-claims test already exists in the repo for similar rows: add the Breaking row to it if the pattern fits.

### [Issue 5] [`codebase`] - Severity: Minor (m2)
*   **Scope:** CHANGELOG "The 66 behaviour checks give the same answers on the old code".
*   ***AI Suggestion:*** PROPOSE FIX (batch only)
*   ***FIX BRIEF:*** Have the next evidence runner reproduce the shim run (merge-base `src` plus a stand-in `netguard`, the 66 checks) and save its raw output; until then label the claim "builder-run, not independently reproduced". No code change.

### [Issue 6] [`codebase`] - Severity: Minor (m4) and Nit n3
*   **Scope:** test_bindguard.py:1740-1778 (`server_sockets` scan); bindguard.py:321-329 (http-loopback rule re-derived).
*   ***AI Suggestion:*** PROPOSE FIX (batch only)
*   ***FIX BRIEF:*** Widen the scan list with `multiprocessing.connection.Listener`, `http.server.test`, `create_datagram_endpoint`, `aiohttp` `run_app`/`TCPSite`, `hypercorn`, `waitress`, `.run(` with `host=`; soften "fails on any other" to "fails on the forms in the list"; one seeded fixture per new form. Nit n3: call `config.url_allowed`'s http-loopback half instead of re-deriving, only if the change is a one-line reuse (reuse rule); otherwise add a test that both agree on a table of hosts.

## Class (d): tests and evidence

### [Issue 7] [`design` m2, `codebase` m6] - Severity: Minor
*   **Scope:** IPv6 on a real socket (test_bindguard.py:438 skipped; Errno 97 here).
*   ***AI Suggestion:*** PROPOSE FIX for the wording, impossible-now for the run
*   ***Justification:*** IMPOSSIBLE-NOW on this machine (no IPv6 loopback). Next step: the lead runs `pytest tests/test_bindguard.py -k ipv6` on the laptop or CI (GitHub runners have IPv6 loopback); record the result in `READY-TO-MERGE.md`. Reword the CHANGELOG "`::1` really works" to "tested through the constructor arguments; real-socket run on CI".

### [Issue 8] [`codebase`] - Severity: Minor (m3)
*   **Scope:** Python 3.12 (mapped-address string form, `is_loopback` change in 3.13, seeded fuzz).
*   ***AI Suggestion:*** PROPOSE FIX for wording; run is IMPOSSIBLE-NOW (3.12 not installed here, ORDER rules)
*   ***FIX BRIEF:*** State the interpreter version in RESULTS.md for each run; add a lenient `ip_address` shim test like B37 for the mapped-form string on both spellings so the check is version independent; the real 3.12 run belongs to the CI job.

### [Issue 9] [`codebase`] - Severity: Minor (m5)
*   **Scope:** `listen` has no hook for backlog or timeout.
*   ***AI Suggestion:*** DECLINE for this PR (note for the Q8a-2 merge)
*   ***Justification:*** Not a defect today; the Q8a-2 receiver will extend `listen` (add keyword options validated inside `listen`, never its own server). Written into the PR body.

### [Issue 10] [`codebase`] - Severity: Nits n5, n6; [`design`] Nits n5, n6
*   **Scope:** loose mutant `expect` fragments (B20 "assert", B8/B9/B28 "== ()", B31 "evil"); post-bind check only reachable by monkeypatch and not run when a reason is given.
*   ***AI Suggestion:*** PROPOSE FIX for the fragments (tighten to the full failure text); DECLINE for the post-bind check (defence in depth, documented).
*   ***FIX BRIEF:*** Pin each fragment to the exact assertion text of the named test; qualify the CHANGELOG line "After binding, the address the socket got is checked" with "when no reason is given and a real service is present".

## Settled (not to be re-opened)
Post-bind check unreachable except by monkeypatch (n5/n6): accepted as defence in depth. `listen` server options (m5): noted for the Q8a-2 merge.

## Handoff
- PROPOSE FIX: 12 items (Issues 1-8 and the fragments in 10); 1 of them needs a confirming round (Issue 1, class (a)); the others are batch only.
- CONTEST: 0. ESCALATE: 0. DECLINE: 2 (Issue 9, post-bind check in Issue 10).
- IMPOSSIBLE-NOW: real IPv6 socket run, Python 3.12 run (next step: CI or laptop, lead).
- Open after this report: all items OPEN in the ledger (PDBIND-r2-1..8). Evidence for the fix batch: one full pytest, stage mutants, bind mutants (full), fail-before on the 6e6ae211 src.
- Second fresh round (design + codebase, security path) REQUIRED after the fix batch; round cap does not apply.
