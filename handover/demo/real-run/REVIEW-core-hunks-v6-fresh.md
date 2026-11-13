# Fresh review: core hunks of v6 (A core-touches-3, B desk-address-required-v6)

Reviewer: fresh, read-only (made-up data, no network, no live model, no mail, no push, no y/yes typed, no prompt reached).
Preamble rules used: 5, 6, 7, 11, 12, 13(e), 19. Studio bible not on this machine: no R-numbers cited.
Work tree: /tmp/work/rvq-24678 (clone of own clone, main 61ded9e). Every pytest ran under `unshare -n` + lo up (/tmp/work/run-un.sh). My own scripts only called pure settings/reader code; the one dial probe stubbed `socket.getaddrinfo`.

## Verdict: CLEAN for A and for the B core hunks as written; two non-blocking items for the lead (Major-if-you-want-strict: hubspot_probe default host; Minor: control characters in a URL value)

No Blocker. No Major in A or in the B hunks. One "by omission" path remains outside the desk (see 3.1), recorded by the builder as by design.

## 0. Apply checks
* sha256 verified: core-touches-3 c61791a6..., desk-address-required-v6 66679357..., real-run-fixes-v6-after-sonar-p3-final 9fc11e9a... (all match).
* A alone on 61ded9e: `git apply --check` OK, applied.
* B: main 61ded9e ALREADY contains sonar-p3-final (tools/pathconfine.py exists), so `sonar-p3-final.patch` itself does not apply on it (expected). `real-run-fixes-v6-after-sonar-p3-final.patch` then `desk-address-required-v6.patch` both apply with `git apply --check` and `git apply`. `desk-address-required-v6` on the plain base fails (docs/settings.md), as the notes say.

## 1. The three key readers, old vs new (condition b, c, d; question 1 and 2)
Re-ran `core-differential-q4h.py` (old = base src + the A test file; new = A): identical to the builder's numbers.
hubspot 366 both / 1146 refused both (text changed 848) / only-old 0 / only-new 0; smtp 448 / 1064 (766) / 0 / 0; live 582 / 833 (677) / only-old 97 (multi-line) / only-new 0. RESULT: no difference outside the allowed ones.

My own 47 key-file shapes x 3 readers (x/mydiff.py, old src vs new src, accepted VALUE also compared): CRLF, CR, trailing and leading newline, two trailing newlines, BOM (alone, with key, with trailing newline), NUL (end, middle), trailing/leading spaces, tab (end, middle), 4096/4097/100000 bytes, NBSP/ZWSP/U+2028/U+0085/VT/FF/FS inside and at the end, only newline, only CRLF, empty, only spaces, UTF-16, invalid UTF-8, 7 and 8 characters with and without newline, a 7-char first line plus a second line, DEL, control char in the middle.
* Accept/refuse and accepted value identical for hubspot and smtp on all 47.
* Live: the only differences are the 4 multi-line shapes (LF in the middle, CRLF in the middle, a lone CR in the middle which Python's text mode turns into LF, 7 chars + newline + 1 char). Everything else identical.
* A key file ending in a newline (LF, CRLF, CR, two newlines) is STILL ACCEPTED by all three readers, and so are BOM+newline and trailing blanks (the check runs after `strip()`). The multi-line refusal does not break the normal form.
* Messages: every refusal text over the 141 readings is one of a closed set of fixed strings (hubspot 7, live 4, smtp 7); none contains the key (canary "ZQ7"), a path or a temp folder; `__cause__` is None and `__context__` suppressed in all of them (`from None`). Condition (c) holds.
* Observation (pre-existing, unchanged by A, NOT a regression): the live reader has no size cap (accepted a 100000-byte file), no printable/space rule (accepts NUL, DEL, tab, NBSP, spaces in the middle of the key), and its "one line" rule is only `\n` / `\r`, so a key with an inner VT, FF, FS, U+0085 or U+2028 is accepted. This does not allow header injection (http.client refuses only CR/LF, which are refused; a non-Latin-1 char raises a ValueError that the transport turns into a fixed text). FIXES/NOTES already say the live key does not get the HubSpot rules. Not for this gate; worth a later one-line rule.
* Condition (a): FIXES.md v6 section lists all three with file, function, exact change, why (lines 67-70). Minor: the older v3 line 29 of FIXES.md still says "no logic change" for the live reader; the v6 correction bullet supersedes it but the stale sentence is not struck out.
* Condition (b): `tests/test_core_key_readers.py` (12 tests) on the base source: 7 failed, 5 passed (reproduced). Failing ones cover each reader's text (hubspot, smtp, live params), the live multi-line test, the "three texts" test and the closed-set test; the 5 passing are the "unchanged" pins (hubspot and smtp oracle comparisons of 1512 files, live oracle expects old rule minus multi-line, no-echo test). Hubspot and smtp therefore have both a fails-before text test and an accept/refuse pin; live has the single intended behaviour change pinned.
* Condition (d) (fresh read of just the three hunks): the hunks are as described. Hubspot: three `if`s in the same order and with the same conditions as the one old `or` (empty is a subset of `len < 8`; empty refused first, then short, then space/unprintable): accept set identical. SMTP the same. Live: `strip()` first, then `\n`/`\r` (the only new refusal), then empty, then short. Safe.

## 2. B (core hunks of desk-address-required-v6) (question 3)
Read: `HubspotSettings.from_env` (absent or blank after strip -> SettingRefused naming the setting, no value echoed), `base_url` field has no default (HUBSPOT_BASE_URL import removed), `__post_init__` `%` in netloc refused; `_live_from_env` same, `LiveSettings.base_url` no default, `%` refused; constants.py comments only; docs.
* One choke point: `make_crm` (the loader's entry) calls `HubspotSettings.from_env(os.environ)`; `Config.from_env` calls `_live_from_env`; run_real_check, crash_desk, start_all, feed, reset all go through `Config.from_env`; run_live_check builds `LiveSettings(base_url=a.base_url)` after its own "not given" refusal. `Config(crm="hubspot")` built in Python still reaches `from_env(os.environ)` at load time, so no omission there either.
* Sweep of every kind (grep of src/, scripts/, tools/, load_tools/, docs, demo_only, n8n, workflows for vendor hostnames and default-URL constants): 
  | kind | host source | verdict |
  |---|---|---|
  | crm hubspot (`DESK_HUBSPOT_BASE_URL`) | required, no default (B) | OK |
  | model (`DESK_LIVE_BASE_URL`) | required, no default (B); run_live_check `--base-url` required | OK |
  | mail send `smtp_provider` (`DESK_SMTPP_HOST`) | required list in `from_env`, field has no default | OK |
  | mail read `ImapSettings.host` / `REAL_IMAP_n_HOST` | dataclass field without default; script refuses unnamed | OK |
  | `smtp` outbox (`DESK_SMTP_HOST`) | default is the desk's own loopback bind; must be loopback | OK |
  | fakes, n8n, load driver | loopback | OK |
  | `scripts/hubspot_probe.py` | `HUBSPOT_BASE_URL` built from parts, used whenever `--dry-run` is not given | SEE 3.1 |
  The vendor constants in constants.py are only referenced by `config.py` (provider host check) and the run script's `unnamed_remote_default` (now a second, redundant guard) and tests; the tripwire test in B enforces this for src/.
* Hostile values (x/hostile.py, both HubSpot `from_env` and `Config.from_env`, 77 values, each with and without the ALLOW_ANY flag where relevant): absent, "", " ", tab, LF, CRLF, NBSP, U+2003, "  \n " -> all refused with the "required" text (strip is Unicode-aware); ZWSP, BOM, NUL -> refused as not an address; vendor URL typed explicitly -> accepted (intended; case, `:443`, trailing `/`, leading space accepted by the old check as well); trailing dot, `.evil.test` suffix, `evilhubapi.com`, userinfo (also `\@`, `#@`, `?@`), `%2f`, `%61`, `%00`, `%25` zone, IDN / fullwidth dot / ideographic full stop, `http://` to a non-loopback name, `127.1`, `0x7f.1`, decimal IP, IPv4-mapped IPv6, long-form `::1`, `localhost.evil.test`, `127.0.0.1@evil` -> all refused. `[::1]` / `localhost` / `127.0.0.1` over http accepted by the live reader (loopback), and for HubSpot only with the ALLOW_ANY flag (as before). With `DESK_*_ALLOW_ANY_BASE_URL=yes` a blank value is still refused and a `%` host is still refused.
* Fuzz: 400000 random strings from 35 URL-significant tokens; 3709 accepted by the two settings classes; for the accepted ones I compared the host urlsplit sees with the host urllib's Request will dial. Differences exist only when the value holds a tab, CR, LF or an empty userinfo (`https://@host`), because urlsplit deletes those characters and urllib keeps them. Probe with the real opener (no proxy) and a stubbed resolver: tab/CR/LF values fail closed with `InvalidURL: URL can't contain control characters` before any name lookup; `https://@evil.hubapi.com` reaches the resolver as `@evil.hubapi.com` and fails there; a leading space is dialled as the vendor host. No key can reach a host outside the allowed suffix by this route on this Python (3.12). Minor hardening, not caused by B: refuse any whitespace/control character in the value (a 2-line check beside the new `%` check) so the check does not rely on http.client's check.
* Demo/loopback profiles still start: no demo script or profile sets DESK_CRM / DESK_QUALIFIER / DESK_HUBSPOT_* / DESK_LIVE_* (grep); default demo desk startup tests on the B tree: tests/test_http.py + test_server_main_reaper.py + test_portal_api.py: 191 passed. The desk has no "profile says real" switch other than `Config.real_services` (banner, loopback-only bind); a vendor URL typed explicitly with `DESK_CRM=hubspot` is accepted on purpose, and it requires the key file and call cap too.
* Fail-before: B tests on the code without the B src hunks (reverse-applied src part only, docs kept): 12 failed, 4 passed (the 4 are the explicit-address controls and the docs test; the builder's 13/3 also reverts the docs). Reproduced in substance.

## 3. Findings
3.1 (Major only if the lead reads the breach class strictly; the builder recorded it as by design) `scripts/hubspot_probe.py`: when `--dry-run` is not given, `base = HUBSPOT_BASE_URL` (vendor address built from parts) and the probe sends the token to the vendor. Confirmation is `--yes-spend-calls 7` and a token in the environment variable named by `--token-env`, not a typed or named address. It is a vendor-address default reached by omission, outside the desk. I did not run it (it would call the vendor). Fix suggestion, 4 lines: require a `--base-url` (or `--vendor-host`) with the same http/https and suffix check as HubspotSettings, no default; add a test that omission refuses before the token is read.
3.2 (Minor) Control characters and spaces inside the base URL value are not refused by the settings classes (they rely on http.client). See fuzz above; fails closed on Python 3.12.
3.3 (Minor) Live key reader accepts the shapes listed under "Observation" (pre-existing).
3.4 (Minor, record) FIXES.md stale "no logic change" line 29 for the live reader (v6 corrects it in a later bullet).
3.5 (Note) B's core hunks depend on v6 (apply after it); the lead's "B applies after the after-sonar-p3-final copy" is correct only because 61ded9e already contains sonar-p3-final.

## 4. Mutants of my own (13 distinct, plus 1 duplicate; x/mut.py; each run: test_core_key_readers.py + test_desk_address_required.py)
| # | mutation | result |
|---|---|---|
| M1 | live: multi-line check removed | killed (4 failed) |
| M2 / M14 | live: no `strip()` so a trailing newline would be refused | killed (3 failed) |
| M3 | hubspot: short rule `<` -> `<=` | killed (2 failed) |
| M4 | smtp: ASCII rule dropped | killed (3 failed) |
| M5 | smtp: "too short" message echoes 2 characters of the secret | killed (3 failed) |
| M6 | hubspot: unprintable rule dropped (isspace only) | killed (2 failed) |
| M7 | hubspot `from_env`: required check disabled | killed (3 failed) |
| M8 | live `_live_from_env`: blank no longer refused (only absence) | killed (1 failed) |
| M9 | hubspot `%` check removed | killed (4 failed) |
| M10 | live `%` check removed | killed (4 failed) |
| M11 | hubspot required check without `.strip()` | killed (1 failed) |
| M12 | hubspot `base_url` default restored in the dataclass | killed (1 failed) |
| M13 | live `base_url` default restored in the dataclass | killed (1 failed) |
All killed; none survived.

## 5. Breach row BL-duplicate-proof-lead-desk-breach-reviewer-y: move to FIXED-VERIFIED?
NO, not yet. Supported by this artifact: the omission half (an unnamed vendor address reaching the vendor by default) is closed at the choke point for hubspot and the live model, with fails-before (12-13 failed), 13 mutants killed, hostile values refused, demo still starts. Missing: (1) a decision and fix or recorded acceptance for `hubspot_probe.py` (3.1); (2) the whole suite and CI on the combined tree were not run by anyone (the builder ran 15 files; I ran 12 files plus 191 server tests): the lead's full run; (3) the row's own subject, a reviewer answering y at a start prompt, belongs to the start-prompt hardening hunks of v6 (scripts/terminal_guard, precheck), which I did NOT re-review here beyond reading NOTES; it needs its own verification (REVIEW-v5-fresh and a fresh pass on the v6 scripts) before the row moves; (4) Windows run not done by the builder or me (mypy win32 clean only).

## 6. Gates (all clean)
* A tree: ruff check + format --check clean; mypy linux and win32 "no issues in 28 source files"; bandit -ll 9 low / 0 medium / 0 high (same 9 as base); tests/test_core_key_readers.py 12 passed; tests/test_hygiene.py 24 passed with DPLD_REQUIRE_SCAN=1 after `git add -A` and commit (gpgsign off via GIT_CONFIG_COUNT env); `gitleaks dir` no leaks (gitleaks 8.30.1) after removing __pycache__ (the .pyc files from my test runs produce 19 false hits; they are gitignored).
* B tree (base + v6-after-p3-final + desk-address-required-v6, `git add -A`, committed): ruff, format (164 files), mypy linux and win32 (30 files), bandit 9 low / 0 / 0, check_schema ALL PASS, git diff --check clean; tests: test_desk_address_required 16 passed, test_core_key_readers 12 passed, test_crm_hubspot + test_env_numbers + test_live_claude + test_ledger_amounts 562 passed, test_http + test_server_main_reaper + test_portal_api 191 passed, test_hygiene 24 passed (DPLD_REQUIRE_SCAN=1); `gitleaks git` no leaks; `gitleaks dir` no leaks.
* Not run: the whole suite; Windows; run-dry-checks.sh; any real service; a Python older than 3.12 (the fail-closed behaviour on control characters is measured on 3.12 only).
* A first hygiene run failed only because commit signing was on in the test's temporary repo (`test_term_scan_finds_a_planted_term`); with the GIT_CONFIG_COUNT override it passes. Not a code issue.

## 7. Safety record
No y/yes or host typed anywhere; no script with a start prompt was run; no pkill -f; one mutant runner of mine (PID 24557) was stopped by PID after it stalled and re-run in the foreground; no files at absolute system paths (all under /tmp/work/rvq-24678 and this report); no push; no suppression comments added.

Files: /tmp/work/rvq-24678/x/{mydiff,hostile,fuzz,dial,mut,mut2}.py (my scripts), /tmp/work/rvq-24678/{old,new}.json.
