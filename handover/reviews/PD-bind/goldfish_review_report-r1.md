Status: resolved

# Goldfish Annotated Review Report: PD part 2 (public-bind refusal), round 1

**Target:** `/home/user/build/snap/pdbind-e75f9f25/DIFF.patch` (full), head e75f9f25, merge-base 2a8c2aac. Mode-safety/security path (no round cap; one confirming round after the fix batch must find nothing real).
**Reviews read in full:** `handover/reviews/PD-bind/pdbind-e75f9f25-design-r1.md` (1 Blocker, 2 Major, 4 Minor, 2 Nit) and `pdbind-e75f9f25-codebase-r1.md` (0 Blocker, 3 Major, 5 Minor, 3 Nit). Evidence: `handover/evidence/PD-bind/e75f9f25/RESULTS.md` (37/37 stage mutants, 18/18 bind mutants, lint clean, one own-Postgres failure then clean rerun).
**Mode:** automated, recommended option for every item.

## What is true first
- The two reviewers agree on the one root defect: the refusal only runs when a caller passes `config=` to `serve` (src approvals/receiver.py:42-56). Every existing call shape `serve(approvals, host="0.0.0.0")` is unchecked, and a test pins that fail-open behaviour. This is a class defect (enforcement is per call site and opt-in), not one bad line.
- Lead decision needed before merge: making `config` required changes the public signature of `approvals.receiver.serve`. I recommend it (below) but the signature break is **LEAD DECIDES BEFORE MERGE** (it is the same question as the lead's open item on `serve(config=None)`).
- My own check of the checkout I hold (core/cloud-handover, near main, NOT the part 2 branch): the only server socket in `src`, `demos` and `tools` is `ThreadingHTTPServer` in `approvals/receiver.py:65`, and nothing in `src` calls `serve(`. That is evidence for the builder to confirm on the branch; the reviewers saw only the 14 changed files.

## Group 1: enforcement is opt-in and per call site (class)
Standard violated: deny by default (least privilege rule); fix at the choke point.

### [Issue 1] [`design F1` + `codebase M1`] - Severity: Blocker
*   **Scope:** approvals/receiver.py:42-56; tests/test_bindguard.py:824 (`test_the_receiver_without_a_config_is_unchanged`); CHANGELOG headline
*   **Description:** refusal runs only if `config` is passed; default is fail-open; the CHANGELOG headline reads as unconditional.
*   ***AI Suggestion:*** PROPOSE FIX (signature break: LEAD DECIDES BEFORE MERGE)
*   ***Justification:*** valid and confirmed by the code text both reviewers quote. A guard that is off by default protects nobody; "one choke point" is the whole claim of this part.
*   ***FIX BRIEF:***
    1. Add `listen(config, host, port, handler)` in `bindguard.py` (neutral stdlib, no new dependency). It is the ONLY place in the package that creates a server socket: it calls `require_safe_bind(config, host)` first, then builds the `ThreadingHTTPServer`.
    2. `approvals/receiver.py::serve(approvals, *, config, host="127.0.0.1", port=8080, allow_public_bind_reason=None)`: `config` required, keyword-only, no default; `serve` calls `listen`. Delete the `if config is not None` branch.
    3. Replace `test_the_receiver_without_a_config_is_unchanged` with: calling `serve` without `config` raises `TypeError`; calling with a real-service config and `host="0.0.0.0"` raises the refusal before any socket exists (assert by patching `ThreadingHTTPServer.__init__` to fail the test if called).
    4. New scan test `test_only_listen_creates_a_server_socket`: parse every `.py` under `src`, `demos`, `tools` (whole tree, not only changed files; no file exempted by name) and fail on any `ThreadingHTTPServer`, `HTTPServer`, `socketserver.*Server`, `asyncio.start_server`, `uvicorn.run` or `.bind(` call outside `bindguard.listen`. Seed one bad fixture in the test and assert the scan flags it.
    5. Mutant (add to tests/bind_mutants.py): `serve` skips `require_safe_bind` when `host` is a str (killed by item 3); mutant: `listen` builds the server before the check (killed by the patched-init test).
    6. Fail-before: stub-run on the OLD `serve` (shim module as in Issue 9) showing `serve(approvals, host="0.0.0.0")` returns a bound public server.
    7. Builder greps the FULL tree on the branch and lists in the notes every server that binds and every `serve(` caller (my check of the near-main checkout found one binder and no callers in `src`; confirm).
    8. CHANGELOG: first sentence states the call now needs `config=` and what a caller changes (one upgrade step); remove the old headline wording that implied the old call was checked.

### [Issue 2] [`design F2`] - Severity: Major
*   **Scope:** bindguard.py:244-247; receiver.py:55
*   **Description:** no explicit allow path, so the only way to bind publicly (for example a container behind a proxy) is to drop the guard.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid. A visible, named, logged exception is safer than a silent bypass and matches "refuse unless explicitly allowed".
*   ***FIX BRIEF:*** keyword-only `allow_public_bind_reason: str | None = None` on `listen` and `serve`. A non-empty reason (after strip, max 200 characters, printable) lets a public bind through; it is written to the log and to the audit trail through the existing audit kind if one is reachable from `listen` without a new dependency, otherwise logged at WARNING with the reason (state which in the notes). The refusal text names this parameter. Tests: refused without it, accepted with it, empty/whitespace/NUL/overlong reason refused, reason appears in the log record; mutant: the reason is ignored; mutant: an empty reason is accepted. The refusal text still never prints the raw bind string unbounded (Issue 11).

### [Issue 3] [`design F3`] - Severity: Major
*   **Scope:** receiver.py:42-56
*   **Description:** `config` is not tied to the `approvals` object that holds the real channel and store.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid. Builder must first read how `Approvals` is built; I did not (the reviewers read only the receiver).
*   ***FIX BRIEF:*** if `Approvals` already keeps the `Config` (or the backends) that built it, `serve` reads the service list from `approvals` and the separate `config` parameter is removed (supersedes the signature in Issue 1: pass only `approvals`). If it does not, add the minimal link: `Approvals` stores the `Config` it was built from and `serve` asserts `approvals.config is config`, refusing otherwise. Test: stand-in config plus real approvals is refused. Mutant: the link check is removed. Builder states in the notes which branch of this item applied.

## Group 2: incomplete input to the decision (class)

### [Issue 4] [`codebase M2`] - Severity: Major
*   **Scope:** bindguard.py:203-227; config.py:325-332 (`check_modules`, `tool_modules`, `egress_hosts`)
*   **Description:** `real_services` counts backends, systems and sources only; custom code that runs in the process and live egress hosts are not read; docstring "one place decides it" too strong.
*   ***AI Suggestion:*** PROPOSE FIX (partly)
*   ***Justification:*** valid for `tool_modules` and `check_modules` (custom code can open any connection, so a non-empty list is not "everything is a stand-in"). `egress_hosts` is an allow-list of hosts a call may reach, not a service; a non-loopback entry still means the process is configured to reach the outside, so it also counts, conservatively. Fail closed.
*   ***FIX BRIEF:*** `real_services` also reports `tool_modules` (name `tools:<module>`), `check_modules`, and each non-loopback `egress_hosts` entry (use `netguard.is_loopback_host`). Tests: each of the three alone makes a public bind refused with that name in the message; an all-stand-in config with all three empty still passes; hostile: an entry with a NUL or a trailing dot. Mutants: each of the three reads removed. Docstring says exactly what is counted and what is not (anything outside `Config`). If a rule elsewhere makes these fields demo-only, the builder cites it; otherwise the three counts stay.

### [Issue 5] [`design F6`] - Severity: Minor
*   **Scope:** table.py:153-161 (`IN_PROCESS`: secrets/mounted_file, signer/ed25519_local, detector/llm_judge, plus two more)
*   **Description:** no recorded reason why these five kinds do not count as real; a signing key in a process that listens could be driven to sign.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***FIX BRIEF:*** one comment per kind (one line each: what it holds, why a bind does not widen it). Test `test_no_listener_route_reaches_the_signer`: enumerate the route paths the receiver `Handler` serves (today only `POST /slack/actions`) and assert the set equals a pinned list, so adding a route is a visible test change. For `detector/llm_judge`, test that a config using it without an `llm` entry is refused at config load or counted real (builder reads the cross-reference; if neither holds, count it real).

## Group 3: proof gaps (class)

### [Issue 6] [`codebase M3` + `design F7`] - Severity: Major
*   **Scope:** CHANGELOG "answers are unchanged"; tests/test_loopback_sites.py; RESULTS items 5a, 5b
*   **Description:** the unchanged-behaviour claim and the receiver behaviour were never run against old code (new tests fail only at import).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***FIX BRIEF:*** evidence runner (separate agent, records only) runs `tests/test_loopback_sites.py` on the merge-base `src` with a shim `netguard` module that exposes the OLD five rules, and runs a stub script showing old `serve(approvals, host="0.0.0.0")` accepts a public bind. Raw output saved; counts written into RESULTS and the run ledger. Wording in CHANGELOG limited to what that run shows.

### [Issue 7] [`design F5` + `codebase m1`] - Severity: Minor
*   **Scope:** tests/test_bindguard.py:811-822; bindguard.py:71 (refusal text advises `::1`)
*   **Description:** AF_INET server cannot bind `::1`; the test swallows the error and passes without testing anything.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***FIX BRIEF:*** in `listen`, set `address_family` from the parsed IP (AF_INET6 for an IPv6 literal) so `::1` really works; the test then asserts a successful start on `::1` and is skipped only when the machine has no IPv6 (explicit `skipif`, not `except OSError`). If the builder chooses instead to drop `::1`, the advice text, the test and the CHANGELOG all change together. Mutant: address family hard-coded to AF_INET.

### [Issue 8] [`codebase m4`] - Severity: Minor
*   **Scope:** tests/test_bindguard.py:837-853
*   **Description:** duplicate-list scan matches only Set/Tuple/List/Call with `localhost` plus a loopback IP; exempts all of `tools.py` by name; misses dict, regex, `startswith("127.")`, concatenation.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***FIX BRIEF:*** widen to any string constant `127.0.0.1`, `::1`, `localhost` or the prefix `127.` outside `netguard.py` and a pinned allow-list of (file, line-text) pairs, each with a reason; remove the whole-file exemption of `tools.py`; seeded bad fixtures for each shape listed; `store/postgres._is_local` and `tools.py` hits are listed with a reason or routed through `netguard` (builder decides per site; the CHANGELOG says left alone on purpose, keep that only if the allow-list reason is written).

### [Issue 9] [`codebase m5` + `design mutant gaps`] - Severity: Minor
*   **Scope:** tests/bind_mutants.py; tests/test_bindguard.py:697-708, :726
*   **Description:** no mutants for the bracket-imbalance clause (netguard.py:373), the `isprintable` fallback, the unreadable-input refusal branch, the default `host`; every-kind test near tautological; `hosts is None` assertion weak; systems/sources tested only with `model_construct`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***FIX BRIEF:*** add the four mutants (each with a killing test); replace the every-kind check with an exact pinned table of 31 kinds to class; drop the `hosts is None` assertion; add tests that build systems and sources through real validated config loading (not `model_construct`) and show they count as real. Run the full `tests/bind_mutants.py` once at the final head.

## Group 4: name resolution at bind and Python-version dependence (class)

### [Issue 10] [`design F4` + `codebase m2`] - Severity: Minor
*   **Scope:** netguard.py:27-62 and :366; receiver.py:80
*   **Description:** the check accepts `localhost` by name but the OS resolves it at bind time (hosts file, nsswitch), so the guarantee "never looks a name up" holds for the check only.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***FIX BRIEF:*** in `listen`, map the accepted name `localhost` (any case) to the literal `127.0.0.1` BEFORE creating the socket, so the socket never resolves a name; refuse any other non-literal host for a bind. After bind, assert `server.server_address[0]` is a loopback literal when no allow reason was given, else close the socket and raise. Docstring says the check never resolves and the bind never resolves. Tests: `localhost` binds `127.0.0.1` (patch `socket.getaddrinfo` to fail the test if called); a non-literal name is refused. Mutant: the mapping is removed.

### [Issue 11] [`codebase n1`, `design Nit`] - Severity: Nit
*   **Scope:** netguard.py:55, test expectations for `0177.0.0.1` and `127.000.000.001`
*   **Description:** leading-zero rejection in `ipaddress` depends on the patch release (3.9.5 and later); only 3.13 was run; docstring says "every Python version".
*   ***AI Suggestion:*** PROPOSE FIX (worth it, small)
*   ***FIX BRIEF:*** reject any dotted-quad with a leading-zero octet explicitly in `netguard` before calling `ipaddress` (so the answer does not depend on the interpreter); keep the test cases; read the supported-Python range from `pyproject.toml` and state it in the docstring. Python 3.12 is not available here (IMPOSSIBLE-NOW, stated); CI covers it.

## Group 5: wording and docs (class)

### [Issue 12] [`codebase m3`] - Severity: Minor
*   **Description:** three loopback meanings (`is_loopback_host` wide, `is_loopback_literal` exact, `guard/http.py:162` normalised exact); title "one shared check" generous; `bindguard` uses two of them.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***FIX BRIEF:*** netguard module docstring and CHANGELOG say plainly: one list (`LOOPBACK_LITERALS`) and two named questions (is this exact text a loopback spelling; is this bind host loopback), and that `guard/http.py` uses the list through `normalise_host`. Rename in prose only; no code rename. A short table in the docstring: question, function, who asks it.

### [Issue 13] [`codebase n2` + `n3`] - Severity: Nit
*   **Description:** `shown` (bindguard.py:236) not length-capped; CHANGELOG entry is one long paragraph under "Upgrade steps" with no real upgrade action.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***FIX BRIEF:*** cap the shown bind text at 80 characters with an ellipsis and a test with a 10,000-character host; CHANGELOG: split into a short "Changed" bullet list; "Upgrade steps" holds only the `config=` change from Issue 1.

### [Issue 14] [`design Nit`] - Severity: Nit
*   **Description:** `real_services` computed before the bind is inspected.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:* harmless (design reviewer's own words); computing after a loopback bind would change behaviour only by hiding the service list in the log, which we want. Recorded, no change.

## Handoff
- Accepted fixes (PROPOSE FIX): 13 findings (Issues 1-13; Issue 4 partly; Issue 1 flagged LEAD DECIDES BEFORE MERGE for the signature break). Issues 6 and 9 include evidence work by a separate runner.
- Contested: 0. Escalated: 0 (the signature break is a lead decision, stated above, not a contest). Declined: 1 (Issue 14, nit).
- Unaddressed: none; nothing from the two reports is left out. Not checked by anyone: the other listeners outside the 14 files (builder greps the full tree), `llm/common.py` alias, CI Python matrix.
- Ledger: PDBIND-r1-1..5 appended (class groups), status OPEN until the confirming round.
- Stop rule: mode-safety path, uncapped; after the fix batch push, independent evidence, then ONE fresh pair of reviewers; stop when they find 0 Blocker and 0 Major. Round exists because round 1 found a real class defect (not because a gate failed to run).
