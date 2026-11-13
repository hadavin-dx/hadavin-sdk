# rv30: independent review of sonar-p2-regex-http-bug-v2.2-delta.patch (test-only, tests/test_sonar_p2_gaps.py, 12 tests, 143 lines)
Fresh clone at db54e13, scratch /tmp/work/rv30-main (base/, stack/ = P1 v3.2 + P2 v2.1 + P3 v3 + delta, p2only/ = P2 v2.1 + delta). No pushes, no writes to the network, made-up data. Preamble rules used: 5, 6, 7, 8, 12, 19, 20. Not run: full suite, Sonar, Windows, Python 3.12 (3.13 used), EGM.

## Verdict: P2 v2.2 CLEAN (no Blocker, no Major; 3 Nits)

## Failures first
None in the delta. Notes that are not defects:
- Brief named `_StageMove`: no such name exists in src or tests at any patch level (grep). The refactor is _finish_update / _finish_update_moved / _finish_with / _locked_retry / _record_send_result only; I mutated those and the callers.
- unshare -rn proves less than it sounds: bind() on 127.0.0.1 still works in a fresh netns, so I proved "no socket" differently (below).
- One of my own runs left a mutant in stack/ (my timeout killed the runner mid-mutant, before its restore). Found and restored from p2only/ (cmp identical for desk, server, identity, urls, config) before any final measurement.

## Apply
Delta applies on db54e13 + P2 v2.1 and in all six orders of P1 v3.2 / P2 v2.1 / P3 v3 with the delta last (`git apply --check` + apply: ok=1 x6). The delta also applies on bare db54e13 (new file only) but its tests then fail by design (needs v2.1 desk.py).

## Determinism
- 12 passed on the real code (stack and p2only), 0.3 to 3 s.
- 30 runs of the file idle: 0 failures. 30 runs with 6 busy-loop hogs on 4 cores: 0 failures. DESK_BIND=127.0.0.2 in the environment: 12 passed.
- No sleep, no real wait: time comes from FakeClock/rig.clock; no thread or socket in the file (grep).
- No-socket proof for the `desk listening on` test: autouse fixture making socket.socket.__init__, create_connection and getaddrinfo raise (plugin /tmp/work/rv30-main/m/nosock.py): 12 passed. Also 12 passed under `unshare -rn`. The test uses a stub with serve_forever raising KeyboardInterrupt; make_server and load_demo_adapters are monkeypatched, signal.signal patched (monkeypatch restores).

## Mutants (runner /tmp/work/rv30-main/m/mut30.py; kill set = only the new file; results /tmp/work/rv30-main/m/rvM.txt, rvO.txt, rvO2.txt)
The seven rv22 mutants, recreated verbatim from /tmp/work/rv22-main/mut.py: M01 KILLED (6 failing tests), M04 KILLED (3), M06 KILLED (2), M08 KILLED (2), M09 KILLED (1), M10 KILLED (1), M26 KILLED (1). All seven die, as claimed.

Own 26 mutants (O01-O26) of the guarantee-class path. Killed by the new file alone (15): O01 (moved = rows>0), O07 (unknown also moves stage), O08 (token dropped from UPDATE), O09 (warn only when changed>1), O10 (wait never freed), O11 (wait always freed), O16 (nudge record drops attempts), O18 (record_nudge_result not through _finish_update), O20 (_finish_with returns None), O22 (rc==1 guard dropped), O23 (count taken from the flag), O26 (_locked_retry returns None on the last busy error), plus M-class equivalents.
Survived the new file, killed by the existing repo tests (8 files, or 32 files for the starred ones): O02 (locked => moved True), O04 (retry off by one), O05 (_GateBusy retried), O17 (give_back_nudge not via _finish_update), O19 (busy re-raised instead of swallowed), O24, O25 (mirror callers not via _finish_update), O13* (sent_at set for every state), O15* (ambiguous flag dropped).
Survived both the new file and 32 repo test files (7 gaps are in lines NOT changed by P2 except O21/O03): 
- O03 the "database stayed locked" log line removed (its text is only asserted absent in the new test): Nit.
- O06 `_locked_retry` without the call-deadline check: base behaviour, untested anywhere: Nit.
- O12 `_mark_contacted` `step_rank < ?` -> `<=`: base behaviour; the new test only exercises step_rank=99 (already further), not an equal rank: Nit.
- O14 last_error kept on a `sent` result: base behaviour: Nit.
- O21 only a non-_GateBusy busy error is swallowed (a _GateBusy escapes _finish_with): this is the one in the P2 refactor; rv22 differential flows (GateBusy case) showed identical behaviour to base, but no committed test pins it. Nit.
Equivalent (not counted): outcome and outcome[1] vs outcome is not None and outcome[1].
Verdict on tests: each test really tests what its name says (confirmed by which tests fail under which mutant above).

## S5332 / hygiene
- The only http literal: line 143 `"desk listening on http://127.0.0.1:4321"`. Re-verified from public source (raw.githubusercontent.com SonarSource/sonar-python ClearTextProtocolsCheck.java, master): (1) the STRING_ELEMENT consumer is skipped when `ctx.isLikelyTestFile()` (tests/ + test_ prefix); (2) `unsafeProtocol` uses `literalValue.startsWith(protocol)`, and this literal starts with "desk listening on", so it cannot match at all; (3) separately, sonar-analyzer-commons CleartextProtocolFilter.java (master, commons/.../appsec/) exempts localhost and 127.0.0.0/8 (lines 73-80). Three independent reasons; the repo already has 75 `http://127.0.0.1` uses in tests. Not reachable by the gate. Note: sonar.test.inclusions=tests/** also makes it a test file for Sonar.
- No secret-like literals; gitleaks 8.30.1 `git --staged` after `git add -A` (31 files): no leaks; `gitleaks dir` on the file: no leaks. DPLD_REQUIRE_SCAN=1: test_hygiene + test_codeant_hygiene + test_sonar_p2_choke_points + test_sonar_p2_gaps: 52 passed, 0 skipped.
- ruff check . clean, ruff format --check . (154 files) clean on the whole stack. mypy N/A (tests excluded by repo config; `# type: ignore[arg-type]` comments are present in the file, they are not suppression of Sonar findings but of mypy; ruff does not flag them).

## Nits
1. The seven mutants listed above (O03, O06, O12, O14, O21) are untested lines; only O21 is in the refactor and is base-equivalent per the rv22 differential. Optional extra test: a _GateBusy raised inside the attempt makes _record_send_result return without raising.
2. Test d hardcodes 127.0.0.1 while the stub address uses HOST (Config().bind); a changed default bind would break it for the wrong reason. It passed with DESK_BIND=127.0.0.2, so the env is not read; harmless.
3. test_d sets DESK_PORT=0 but the stub reports 4321; the asserted line comes from the stub, which is the point, but the env var is dead weight.

P2 v2.2 CLEAN
Files: /tmp/work/rv30-report.md. Head: db54e13 + P1 v3.2 + P2 v2.1 + P3 v3 + delta (local only). Tokens: not measured.
