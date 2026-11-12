# pdbind-6e6ae211-design-r2: part 2 (bind guard), head 6e6ae211, round 2, persona design

Source: hand-back of the design reviewer (agent a20724e0702656cb7), saved by the lead (condensed). SECURITY / mode-safety path. Static read of DIFF.patch lines 1-1078, test_bindguard.py in full, RESULTS.md; no code run. 0 Blocker, 1 Major (M1), Minor m2-m4, Nits n5-n6. Snapshot /home/user/build/snap/pdbind-6e6ae211. Verdict: r1 F1-F6 closed in code and tests; loopback-only rule holds against every host spelling tried (0.0.0.0, ::, empty, 127.1, decimal, hex, octal-looking, zone id, brackets, mapped, trailing dot or space).

## Major
- **M1** receiver.py:106-111, requests.py:73-74, app.py:62-75 and 170-181: the identity check (`approvals.config is config`) proves the same Config object, not the services the approvals really hold. `build()` overrides (`channel=`, `llm=`, `detector=`, `tools=`, `sources=`) are public API; a config saying fake plus an injected real channel or source gives `real_services` empty and a public bind with no reason. `Approvals(real_channel, ..., config=stand_in_config)` is accepted too (config is a mutable attribute). Docstring and comment "reads the services these approvals really hold" overstate. Fix: record the overrides on App or Approvals and count any non-stand-in override as real (or refuse serve when overrides were passed), with test and mutant; else narrow docstring and CHANGELOG and pin the limit.

## Minor
- m2 IPv6 never run on a real socket (test_bindguard.py:438 skipped, family test monkeypatches the constructor). Confirm CI has IPv6 loopback or record the gap.
- m3 bindguard.py:349-360: a reason of one character passes, goes to the log only; set a minimum (about 10 characters) and do not call it a record.
- m4 table.py:216-236 IN_PROCESS reasons rest on the claim that the only route is POST /slack/actions; the route test pins text only, not what receive or on_decided can reach.

## Nits
n5 post-bind address check fires only by monkeypatch; n6 a reason set on a loopback bind logs nothing (fine).

## Not checked
DIFF lines 1079-2283, mutation runner body, other Approvals constructor calls in demos or tools, docs showing the old serve form, Python 3.12 vs 3.13, Windows or macOS, Slack signature verification, store/postgres._is_local, PR body.
