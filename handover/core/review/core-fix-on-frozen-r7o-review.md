# Review of the delta r7n -> r7o (BOM decision plus 14 pins). EGM goldfish, codebase-details, fallback mode

Verdict: **NOT CLEAN**. 1 Blocker-level gate failure counted as Major, 2 minor real gaps, 3 nits. Counts: B 0 / M 1 / m 2 / n 3.
The BOM decision itself is sound: keep utf-8-sig (see 1). The 14 pins are real. What fails is the repository hygiene gate and two unpinned siblings.

## What I did NOT run or conclude (first)
- No full suite. Narrow set = tests/test_r7o_findings.py (18 tests, about 40-110 s). Survivors were re-run on a wider set (7 files, 304 tests; the REAL_DRAIN_SECONDS mutants on 451 tests: r7o + test_real_check_dry + test_env_numbers). Old files were NOT added to every pass 12 mutant; all 8 pass-12 style mutants were killed already on the narrow set, so a wider set could only add kills.
- gitleaks is not installed: 3 hygiene tests SKIPPED (the literal-pattern scan ran, the history scan did not).
- mypy not run. Bandit ran on regfile.py only (the changed source), not on the test file.
- I did not read the r7n reviewer's file or EV7N evidence (not asked). I read R7O-RESULTS.md only after forming my own view.
- Own slip: while lane B was mutating tree-REV7O-m2 I ran one probe (p12.py) that imported from it; it only read the file, and the mutated copy is irrelevant to that probe's printed result (the printed result was from tree-R7O). All three of my trees are byte-identical to the originals at the end (`diff -rq` clean). I also made a third copy (tree-REV7O-m2) for a second mutant lane; two test processes at most were running from me.
- Clock: `date -u` in the sandbox moved only about 27 minutes over the whole run (10:06 to 10:33), the checkpoint lines are in out/REV7O/checkpoint.md.

## Recipe and trees
tree-REV7O (r7o bytes), tree-REV7O-base (r7n bytes + the new test file copied in, for the fail-before run), tree-REV7O-m2 (copy of r7o, second mutant lane), scratch out/REV7O. Delta unpacked sha256 = b606cab5...59bfb (matches). The delta touches exactly: src/lead_desk/regfile.py (one line: decode("utf-8") -> decode("utf-8-sig") plus docstring) and the new test file. `diff -rq` of r7n vs r7o confirms nothing else differs in source.

## Findings

### M1 (Major, CI gate): hygiene scan FAILS on r7o
- tests/test_r7o_findings.py:218 and :219: the literal `@api.hubapi.com"` (two of the three base addresses in `test_a_login_part_in_the_hubspot_base_address_is_refused`). Repo rule: vendor-style literals are built from parts; the repo test lists them.
- Probe: staged git copy of r7o (git init, git add -A, no commit), `tests/test_hygiene.py`: **1 failed, 20 passed, 3 skipped** (test_hygiene_scan_public: "hardcoded literals found: tests/test_r7o_findings.py:218:api.hubapi.com\" and :219"). Same test on a staged copy of r7n: **20 passed, 4 skipped**. So r7o breaks a gate r7n passes. Raw: out/REV7O/hygiene.log, hygiene-r7n.log.
- Builder said "ruff, no new suppression, bandit not run"; hygiene was not mentioned.
- Fix: build the host from parts, for example `"https://" + "someuser" + "@" + "api." + "hubapi" + ".com"`, the way the other tests do (the old tests never write the whole name). Killing test is the hygiene test itself; re-run it on a staged copy after the fix.

### m1 (minor, real gap, sibling of the pinned J02): `from None` in read_regular_text is unpinned
- src/lead_desk/regfile.py:161 `raise FileRefused("the file is not UTF-8 text") from None`.
- Mutant B15: drop `from None`. KILLED by none: narrow set 18 passed, wider set (7 files) 304 passed, 1 skipped.
- Probe (scratch copy out/REV7O/sc, file `password=hunter2-\xff-rest`): original traceback 380 chars with no codec text; mutant traceback 1048 chars naming "codec" and "position" (the chained UnicodeDecodeError, whose `.object` also holds the whole file bytes). The comment in run_real_check.load_env says "a byte value and its place in the file are never named": the choke point is where that must hold, not only in the one caller that re-raises.
- Killing test in words: write `b"\xff"`, call read_regular_text and load_json_file, catch FileRefused: `__suppress_context__ is True`, `__cause__ is None`, and "codec" and "position" not in `"".join(traceback.format_exception(e))`. Same class as J02, fix by the same test shape.

### m2 (minor, real gap): the password-only login form is unpinned
- src/lead_desk/crm_hubspot.py:164. The three o5 forms all carry a user name, so `parts.username` alone refuses them. Mutant B12 (drop `or parts.password`): narrow 18 passed, wider 304 passed, 1 skipped, SURVIVED.
- Probe: `urlsplit("https://:pw@api.hubapi.com")` gives username `''` (false) and password `'pw'`; r7o refuses it only because of the password term (both `https://:pw@host` and `http://:pw@127.0.0.1:9` print "refused").
- Killing test in words: the two password-only addresses (built from parts, see M1) raise SettingRefused matching "no query, fragment or login".

### Nits
- n1: test file lines 147, 153, 160 hold a raw invisible U+FEFF character inside a string. An editor that drops it turns line 153 into `== "{}"`. Write `"﻿"`.
- n2: R7O-RESULTS.md says "No new suppression". The new file has 8 `# noqa: E402` (the same pattern exists 3 times in test_real_check_dry.py) and one `# type: ignore[misc]` (line 96; mypy runs only on src and tools, so it does nothing). The repo rule says no suppressions; the E402 pattern is the existing house style, the `type: ignore` can simply go.
- n3: REAL_DRAIN_SECONDS boundaries stay unpinned (see item 4). Not part of r7o's job, listed for the ledger.

## Item 1: the BOM decision (utf-8-sig kept; recommend accepting; no Major)
Who reads through `read_regular_text` (grep of src, scripts, tools, load_tools, demo_only): the crash flag readers (trace.py:131, hooks.py:41), the settings file (run_real_check.load_env), the SMTP catcher control file (load_tools/catcher.py:69), the fake model server control file (demo_only/fake_model_server.py:109), the /proc readers and load-driver kernel file, and `load_json_file` (n8n script, workflow scrubber, feed, invariant checker, result totals). No allow-list, no secret, no permission file.
- Secret and password files do not use it: `read_secret_line` already decodes utf-8-sig on r7n. Probe on r7n and r7o, identical: plain, one BOM -> same key; two BOMs, a BOM in the middle, a BOM at the end -> refused ("holds no key"). So the BOM was never part of a secret, and r7o changes nothing there.
- Flag files: r7n = a BOM'd flag silently never fires (no crash); r7o = fires, same as without the BOM. A second BOM keeps the flag unread (tested). It is a test crash hook (the launcher gives the path); turning "ignored" into "honoured as written" is not a fail-open of a security decision.
- Config file: r7n = refused ("config line 1 is not NAME=VALUE", loud but misleading); r7o = loaded. Name checks still run on the stripped text; a double mark is still refused.
- Catcher control file (probe, both trees): r7n `BOM+"down"` gave `("ok", 0.0)` (the fault was silently NOT injected, a test would pass for the wrong reason); r7o gives `("down", 0.0)`; `BOM+BOM+"down"` stays `("ok", 0.0)`; `BOM+"slow 2"` gives `("slow", 2.0)`. This is the old silent default, not a refusal; accepting is the safer reading for a fault tool.
- JSON: r7n refused a BOM'd file; r7o loads it; a mark inside a string or in the middle is data or invalid JSON (tested).
- Recommendation: **accept (utf-8-sig)**. Reasons: the key reader, the CA reader and the invariant checker (line 1 only) already accept one mark; refusing would only change four readers of eight from "silently ignored" to "refused" and break Windows-saved files; there is no reader where the mark made a token fail closed that now matches an allow. Residual note (not a finding): `iter_regular_lines` (load files, /proc) still decodes plain utf-8 and keeps the mark; a BOM'd first line there fails JSON loudly, so it is fail-closed.
- Docstring claim "as the key and password reader and the invariant checker already do": true (regfile.py:93, check_invariants.py:210, tls_trust.py:41).

## Item 2: the 14 PINs, mutants (pass 12 text, run on tree-REV7O, restored by byte compare after each: `restored=True` every time)
On r7n (tree-REV7O-base + new file): 4 failed (the four BOM tests: json/text reader, only-one-mark, flag readers, config) and 14 passed (raw r7o-on-r7n.log). On r7o: 18 passed (r7o-on-r7o.log). Each pin passes on r7n because the source line the pass 12 survivor altered is the same on r7n and r7o.

| pass 12 mutant | planted as | result on narrow set (r7o file) |
|---|---|---|
| M9-79 drop `* 2` of the live cost line | run_real_check.py:1055 | KILLED, 3 failed (the three persons values) |
| M9-74 exit 0 with contacts left | `and not left` removed | KILLED, 1 failed (left-contact test) |
| M10-J13 decode errors="replace" | regfile.py read_regular_text | KILLED, 4 failed |
| M10-J09 plain utf-8 (BOM kept) | regfile.py | KILLED, 4 failed |
| M9-56 `parts.username` removed | crm_hubspot.py:164 | KILLED, 2 failed (the third form needs the password term: see m2) |
| M10-J02 `from None` removed in jsonread | jsonread.py:24 | KILLED, 1 failed |
| M9-82 `< MIN-1` (4 accepted) | run_real_check.py:1030 | KILLED, 1 failed: test_the_minimum_readback_cap_is_accepted_and_one_below_is_refused |
| M9-82b `<= MIN` (5 refused) | same | KILLED, 4 failed |
Each test pins the survivor line itself, not only the builder's O-mutants; the survivor text of pass 12 matches the pinned property for M9-79, M9-74, J13, J09, M9-56 (partly: m2), J02, M9-82. The sibling of J02 in regfile is the gap m1.

## Item 3: "source already right on r7n"
Verified on tree-REV7O-base with my own probes (probe3.py, probe3b.py): `{"a":"x\xffy"}` refused by both readers ("the file is not UTF-8 text"); `http://u@127.0.0.1:9` and `https://u@api.hubapi.com` refused; `JsonTooDeep.__suppress_context__` True and no RecursionError text; banner figure for persons 8 and 12 scales as (persons+3)*2 (0.0450 and 0.0614, ratio matches 22 to 30 within the 4-place rounding), and the exact-figure test passes on r7n; minimum read-back 5 accepted (stops at the question, exit 6), 4 refused (exit 2, "must be at least 5"). The exit code with a failing archive (EXIT_FAILED, "LEFT") is covered by the o2 test passing on r7n. Claim confirmed for items 1, 2, 3, 5, 6, 7.

## Item 4: M9-82 wording and REAL_DRAIN_SECONDS
The pinned boundary (read-back minimum 5, 4 refused) is the right one, and the old test (test_a_bad_readback_cap...[4]) already pinned 4 refused; the pass 12 "kill by REAL_DRAIN_SECONDS test" was only the first failing test under `-x`. But REAL_DRAIN_SECONDS has boundaries that the 0 test does not cover (wider set 451 tests):
- D1 `high=REAL_SECONDS_MAX` -> `*10`: SURVIVED (an upper bound of one day is not pinned for either time setting).
- D3 call-site default 150.0 -> 151.0: SURVIVED (the test at test_real_check_dry.py:865 calls `positive_seconds` directly, not the call site in main).
- D2 `value > 0` -> `value > 1`: KILLED. D4 (default taken from another setting): KILLED.
Real but low: a time wait, no money. Killing tests in words: REAL_DRAIN_SECONDS=86400 accepted and 86400.5 refused; with the setting absent the banner or the child gets 150.

## Item 5: hygiene
Ruff 0.17.1 on a copy: check "All checks passed!", format --check "227 files already formatted". bandit -ll regfile.py: no issues. Hygiene scan: FAILS (M1). No IP-like or secret literals found by the scan other than the two vendor-host lines; keys in the tests are made up and short.

## Item 6: my own 15 mutants (narrow set unless noted)
KILLED (12): B1 errors="ignore" (4 failed), B2 latin-1 (8), B3 except clause swapped (4), B4 message text changed (4), B5 lstrip of every mark (2), B6 every U+FEFF removed (2), B7 trace.py strip removed (1), B8 hooks.py strip removed (1), B9 `not left` replaced by `len(left) < 2` (1), B10 persons+2 (3), B11 calls-per-lead dropped (3), B14 MIN_READBACK_CALLS 6 (4), and B13 (`except (RecursionError, ValueError)` in jsonread) survived the narrow set but was KILLED on the wider set (3 failed, test_n8n_api_url among them), so not counted as a gap.
SURVIVED even on the wider set (2): B12 (password term, m2) and B15 (`from None`, m1). 12 killed narrow + 1 killed wide = 13 of 15; the 2 survivors are findings m1 and m2.

## State left behind
Nothing applied, committed or pushed. No runner left (ps checked). tree-REV7O, tree-REV7O-m2 byte-identical to tree-R7O; tree-REV7O-base = r7n bytes plus the copied test file. Scratch and raw logs: /home/user/build/rr6/out/REV7O (results-A/B/Bw/D.tsv, mut-*.log, hygiene*.log, probes).
