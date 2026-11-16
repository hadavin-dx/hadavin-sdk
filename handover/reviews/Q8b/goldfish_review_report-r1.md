Status: resolved (no person available; recommended option taken for every item)

# Goldfish Annotated Review Report

**Target:** branch head be53718c (one commit on origin/main 2a8c2aac), `src/hadavin_sdk/k1b/redaction.py`, the `clean()` path, `requests.py`, `CHANGELOG.md`, tests (full files). Redaction path: security, no round cap; no readable-secret finding is declined.
**Inputs:** `result-r1-design-full.md` (0 Blocker, 2 Major, 6 minor, 3 nit), `result-r1-codebase-full.md` (0 Blocker, 2 Major, 12 minor), evidence `evidence/Q8b/be53718/RESULTS.md`, `08-hostile.txt`, `08b-hostile-on-main.txt`, `08c-probe-email-glued-key.txt`.
Evidence facts (as recorded by the runner, not re-run by me): full suite 10670 passed after a Postgres setup fix; mutants 26/26, stage 37/37; fail-before 112 failed on main source; the perf step failure is the known flaky timing test, fixed on `core/fix-timing-harness-flake`, not a Q8b defect. Postgres 17 not run. The evidence runner's property generator glues text without separators, so some of its readable cases are unrealistic; the glued e-mail finding itself reproduces in the 08c probe.

Counts: PROPOSE FIX 12 (items 1-9, 11-13 below, grouped), ESCALATE 1 (item 10, safe default taken), CONTEST 0, DECLINE 0.

## Findings

### 1 [Blocker for the fix batch; design M1 + evidence E1] REGRESSION: an e-mail or host glued to a credential key leaves the value readable
* Evidence: `08c-probe-email-glued-key.txt`: `bob.smith@example.com` + `password=<made-up-value>` glued gives `<EMAIL_1>=<made-up-value>` on head; main gave `...[.]compassword=<SECRET_1>`. `token=` the same; a zero-width separator the same; a space, newline, comma or semicolon masks correctly. Property run: 87 vs 38 readable-in-assignment texts of 3000; the reviewer notes not every one of the 49 extra cases was checked as this single cause.
* Cause (design review): the e-mail/host pattern now runs before the key word is read and swallows the key.
* Decision: the reviewers suggested only stating it as a limit and an xfail pointing at PR77. That is deferral of a regression versus main on a redaction path, so it is not accepted. ***PROPOSE FIX***: fix it in the code. Preferred fix at the choke point: run the key/value rule so the key word is read before (or independent of) the e-mail/host pattern, or run the redactor on both the bracketed and the unbracketed text and keep the more-masked result; the builder picks the smaller one after reading `guard/redact.py` and `clean()`, and proves it with the glued-key probes (password, token, zero-width, host-glued), a property test (every assignment value with a made-up secret is masked for every separator including none), and a mutant. If the fix needs a file the ticket calls PR77's, the builder widens scope by the smallest change, records it in the ticket errata, and lists the likely conflict for PR77's restart. Fail-before on be53718c required.

### 2 [codebase Major F1] `_named` misses an entry that has both `name` and `key`
* Checked in the review: `redaction.py:276-282` takes the first of `name`/`key`; `{"name":"db","key":"password","value":"<secret>"}` is not treated as named, the value shows.
* ***PROPOSE FIX***: collect every name-like key (any case) and every `value` spelling; named when ANY name-like value is sensitive. One N1 row, a property test over key orders, a mutant.

### 3 [codebase Major F2] `LIMITS` (redaction.py:44) contradicts the code
* ***PROPOSE FIX***: add the exceptions the code makes (a text that is exactly a UTC time; setting-key values; bool and None) to the LIMITS sentence and the CHANGELOG, in plain words; one test that reads LIMITS and checks each named exception against `_walk` behaviour.

### 4 [E2] Card path half-masks a value with spaces
* Evidence: `password=correct horse battery staple` gives `password=<SECRET_1> horse battery staple` in `clean` and the Slack block (same on main); the walk path masks it fully. Also `password:` and `password%3D...%20...`.
* ***PROPOSE FIX***: mask the whole value for an unquoted multi-word assignment value on the card path (to end of line or the next key), as the walk path does; tests for the three spellings; mutant. Same class as item 1 (key/value rule), fix both in one pass.

### 5 [E3] Other readable copies
* `kind: secret` lower case not masked; a Secret whose `data` is not a map/list/valid base64 leaves a log copy readable; `<IPV4_1>@channel` in a closed code fence keeps `@channel`; appendix row M5 leaves `orders-api timeout` readable.
* ***PROPOSE FIX*** each: case-fold the `kind`; mask the log copy when the Secret is masked for any data shape; handle the fence case or state it with the reason (the builder notes say a fence body is unchanged: decide with a test); M5 row re-checked after the fix and either masked or the appendix and CHANGELOG state what stays readable. One test and mutant per item.

### 6 [codebase F3] Case folding: ſ, İ, ı keys fail open versus main
* ***PROPOSE FIX***: NFKC then casefold before splitting; add ſ, İ, ı to T1; property test over main's `re.IGNORECASE` behaviour.

### 7 [codebase F4] `GLUED_ENDINGS` drifted from the redactor's key list (`guard/redact.py:599-606`)
* ***PROPOSE FIX***: add `accountkey`, `keydata`, `certdata`, `certificatedata`; a drift test that feeds every alternative of the redactor's key list through `sensitive`.

### 8 [codebase F5, m1] The 256-entry cap is bypassable and misdescribed
* ***PROPOSE FIX***: `known_secret = i < MAX_REGISTERED_ENTRIES and isinstance(vx, str)` including nested dict/list levels (cap on the total across nesting); test with a list inside `data`; correct the comment and the CHANGELOG sentence.

### 9 [design/codebase minors, E4] Remaining minors and wording
* Over-masking list incomplete (`tokens_per_second`, `tokens_remaining`, `reasoning_tokens`, `cache_tokens`, plus PWD, OLDPWD, auth_method, session_duration): ***PROPOSE FIX***: name the full cost list in the CHANGELOG and docstring and fix the clearest false positives (token-count keys) with tests.
* The rest of the codebase minors (m2-m12) and design minors/nits: ***PROPOSE FIX***, the fix builder reads them in the two review files, fixes each with a test or wording change, and lists each in its report (none is declined on this path).

### 10 [design Major M2] The approver cannot read the target on the card
* `requests.py:41` puts `plan.target.system` through `clean`; a host name target becomes `<HOSTNAME_1>`.
* ***ESCALATE***: this is an owner decision (what the approver may see). Safe default taken (masking stays, the privacy-safe choice): the target is masked and the card shows a label; the builder adds the label route (an integrator-chosen display name per target) and states the trade-off in plain words in the CHANGELOG. If the owner prefers exempting `target.system`/`agent_id`/`action_id` from identifier masking while still masking `Inputs`, it is a small later change; question entered in `handover/questions-for-lead.md`.

### 11 [E4 perf] Perf-step failure
* ***PROPOSE FIX*** (record only): the evidence note states the failure is the known flaky timing test; the branch does not touch it; no change here.

### 12 [evidence process] Full-suite attempts 1 and 2 died silently at 10% and 14%
* ***PROPOSE FIX***: the fix batch's final full run is done through `heavy.sh` with the log kept; if it dies again, report the cause instead of re-running blindly (cause unknown so far; no OOM evidence found).

### 13 [ledger] Rows
* ***PROPOSE FIX***: add rows to the ledger (done by the lead this turn).

## Handoff
Accepted fixes 12 (items 1-9, 11-13). Contested 0. Escalated 1 (item 10; default taken). Declined 0. Unaddressed 0.
Next: one fix builder for the whole list (redaction path, uncapped), then delta evidence (hostile property run with a real separator set, fail-before, mutants) and a fresh round 2 on the new head; drift report before READY.
