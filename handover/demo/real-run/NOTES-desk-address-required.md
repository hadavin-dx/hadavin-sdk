# NOTES: desk-address-required.patch (OPTIONAL, THIS TOUCHES CORE src: the lead's approval is needed before it goes in)
Preamble rules used: 5, 6, 7, 11, 12, 13. Studio bible not on this machine (no R-numbers). EGM skipped (cannot invoke egm:* here; the lead runs it). Evidence: evidence-q4g-p2-*.txt.
Variants: `desk-address-required.patch` (against db54e13 or 2db3926, standalone: includes its own small edits of tests/test_real_check_dry.py) and
`desk-address-required-after-v2.patch` (the same minus the test_real_check_dry.py hunks, for use AFTER start-prompt-hardening-v2.patch, which already makes those edits; the two overlap there and cannot both be applied).
Order if all are taken: v4, start-prompt-hardening-v2-on-top-of-v4.patch, desk-address-required-after-v2.patch applied with `git apply --3way` (plain apply fails on docs/settings.md context only; 3way is clean, measured).

## The class and the fix
Class: a default address that is the vendor's own. It passed the "vendor's own domain" check, so omitting the setting sent the key to the vendor with no refusal and no question
(reviewer's measurement: server + DESK_CRM=hubspot + key file + call cap, no DESK_HUBSPOT_BASE_URL -> 201 and a try on the vendor host; same for DESK_QUALIFIER=live_claude and the model host).
Fix at the shared choke point (the settings classes, so every caller is covered: server, crash_desk.py, start_all.sh/.ps1, scripts, tests):
- `HubspotSettings.from_env` and `_live_from_env` REFUSE an absent or blank address (SettingRefused naming the setting; the desk prints "the desk refuses a setting: ..." and exits 4, no traceback).
- `HubspotSettings.base_url` and `LiveSettings.base_url` lose their default (required dataclass fields), so Python code cannot omit it either. (Separable: if you want the smaller touch, drop these two field hunks; then only the env readers refuse.)
- Reviewer's nit 7: a `%` in the host of either address is refused (urllib and urlsplit read `https://evil.test%2f.hubapi.com` differently; the vendor-suffix check accepted it).
Exactly which core lines change (git diff -U0 of src/):
- src/lead_desk/config.py: line 127 `base_url: str = LIVE_DEFAULT_BASE_URL` -> `base_url: str`; +2 lines in `LiveSettings.__post_init__` (percent check, after the "no path" check); in `_live_from_env` (line ~203) the `if "DESK_LIVE_BASE_URL" in e:` block becomes a required check (+5 lines) and `kw = {"base_url": e["DESK_LIVE_BASE_URL"]}`.
- src/lead_desk/crm_hubspot.py: import of HUBSPOT_BASE_URL removed (line 79); line 146 `base_url: str = HUBSPOT_BASE_URL` -> `base_url: str`; +2 lines percent check in `__post_init__`; `from_env` docstring and the same required check (+5 lines).
- src/lead_desk/constants.py: three comments only (HUBSPOT_BASE_URL, MAIL_IMAP_DEFAULT_HOST, LIVE_DEFAULT_BASE_URL say "no default"). The constants keep their values (still used as the vendor's own address: the live host check, tests, examples). Their names still say DEFAULT; a rename is churn I did not do.
- docs/settings.md (2 places), contract.md (2 places): the address is required.

## Behaviour change for existing private configs
- A desk started with DESK_CRM=hubspot and no DESK_HUBSPOT_BASE_URL now stops at start, exit 4: "DESK_HUBSPOT_BASE_URL is required for the hubspot CRM ...". Fix: add `DESK_HUBSPOT_BASE_URL=<the vendor's own address, see HUBSPOT_BASE_URL in constants.py>`. Same for DESK_QUALIFIER=live_claude and DESK_LIVE_BASE_URL.
- The vendor's own address named on purpose still works unchanged; a loopback address still works (HubSpot: with DESK_HUBSPOT_ALLOW_ANY_BASE_URL=yes as before; live model: plain http to loopback needs no opt-out as before).
- A shell that holds DESK_CRM=hubspot or DESK_QUALIFIER=live_claude while running scripts/start_all.sh|.ps1 or scripts/crash_desk.py (they start the server with the shell's DESK_* names) now stops at the server's start instead of sending by omission. The scripts themselves needed no edit (none sets those names; grep).
- Callers that relied on the default and were edited (all tests; no src, script, demo_only or doc caller relied on it): tests/test_crm_hubspot.py (4 sites), test_env_numbers.py (HUBSPOT and LIVE dicts), test_live_claude.py (3 dicts, the env test), test_ledger_amounts.py (2 env dicts), test_real_check_dry.py (standalone variant only: config names the address). demo_only: no caller (grep). run_real_check.py: DryFakes already names DESK_HUBSPOT_BASE_URL; `--live-model` already needs the address via start-prompt-hardening-v2.

## Sibling sweep: every other vendor default address in src, scripts, demo_only, tools, load_tools
| where | default | verdict |
|---|---|---|
| HubspotSettings.base_url | vendor | FIXED here |
| LiveSettings.base_url | provider | FIXED here |
| scripts/run_real_check.py imap_settings REAL_IMAP_n_HOST | MAIL_IMAP_DEFAULT_HOST | FIXED in start-prompt-hardening-v2 (host required, shape checked) |
| scripts/run_live_check.py --base-url | provider | FIXED in v1/v2 (no default) |
| DESK_SMTPP_HOST (smtp_provider), ImapSettings.host | none: required | nothing to do |
| DESK_SMTP_* (smtp_outbox) | not a vendor address (host setting; local default) | unchanged, not a vendor default |
| scripts/hubspot_probe.py HUBSPOT_BASE_URL | vendor, by design (its whole purpose, consent by --yes-spend-calls 7) | unchanged, recorded |
| scripts/n8n_api.py N8N_URL, Config.fakes_host/bind, feed.py, load_driver | loopback | not a vendor address |
A tripwire test walks src/ and fails if any of the three vendor constants is used anywhere but the live host check in config.py (also catches an import).

## What was run (all under unshare -rn + blocker; blocker log empty)
- evidence-q4g-p2-fail-before.txt: the new test file on db54e13 src: 13 failed, 3 passed. Honest note: the desk-process tests fail on old code because the old desk accepted the settings (exit 1 "cannot reach the demo servers" instead of 4); the child never reached the vendor name in that test because the default outbox fails first. The vendor attempt itself is the reviewer's measurement, not repeated here.
- evidence-q4g-p2-mutants.txt: 12 mutants, 9 killed, 3 survived: P2 and P4 (the fallback `or VENDOR` added while the required check is still there) and P10 (a `pass` before the raise) are equivalent mutants (the unchanged check still raises first); the same fallbacks with the required check also removed (P2b, P4b) are killed. Percent checks, dataclass defaults, blank handling and the tripwire import are killed.
- Tests: standalone patch tree: 807 passed + the 20 failures it first had in test_real_check_dry / test_live_claude fixed and those two files re-run (119 passed); files: desk_address_required, crm_hubspot, env_numbers, live_claude, ledger_amounts, mode_safety, bind_refusals, codeant_hygiene, load_tools, ledger_and_bind_retry, real_check_dry. v2 + after-v2 combined on db54e13: evidence-q4g-p2-tests-combined-v2-p2.txt, 985 passed (adds start_prompt, clock_steps). On 2db3926: 603 passed (evidence-q4g-on-2db3926.txt). v4 + v2-on-v4 + after-v2: 621 passed (evidence-q4g-v4-v2-p2-tests.txt). Not the whole suite.
- Gates: evidence-q4g-p2-lint-mypy-bandit.txt (ruff, format, mypy linux + win32, bandit -ll clean). evidence-q4g-p2-hygiene-gitleaks.txt holds a FIRST FAILED run (one env-style line in a test tripped the hygiene scan, `NAME=CONSTANT`) followed by the pass after the fix (59 passed, gitleaks 8.30.1, DPLD_REQUIRE_SCAN=1).
- Apply matrix: evidence-q4g-apply-matrix-p2.txt and -final.txt (db54e13 and 2db3926 alone; after v2; on v4 plain apply fails only in docs/settings.md, 3way clean).
Not run: Windows, the whole suite, any real service.
