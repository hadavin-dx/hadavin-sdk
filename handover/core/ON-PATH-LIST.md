# ON-PATH LIST: the take's imported files and which hardening changes touch them

Written 2026-11-14 about 11:00 UTC (16:30 IST) by the core lead, from the lead's list `handover/core/TAKE-USED-FILES.md` (take head 27a1ed8) and my own trees. Supersedes my provisional version.

## What is NOT checked (first)
- **I cannot see the take head or run the take.** The per-file answer "RUNS under Design A" is my reading of `scripts/run_real_check.py` on my tree-R7O, assuming Design A = n8n sends the mail and writes the CRM, the desk does the spend cap, the model call and the independent mail count. It is not traced and not confirmed on the take's own files. The take's `run_real_check.py` is an older file than mine (my patch changes it by +234/-69 against the frozen tree).
- **The minimal patch subset is a computed list of files, NOT a patch that applies on 27a1ed8.** I did not try to apply it there (the lead said not to). The 88 patch files with no counterpart in the take (see the lead's list) include 12 non-test files; the take's old copies of every touched file must be replaced by my version, since my hunks are written against the frozen tree, not the take.
- Line counts are `diff` of tree against tree ignoring CR; "same" means no change between those two releases.

## Which release changed what (only src, scripts, tools, load_tools, demo_only files)
Release chain: frozen 49d3c85 -> r7m (all earlier hardening) -> r7n (leak fix, scrub choke point, banner fixes) -> r7o (regfile reads a leading BOM; tests) -> r7p (TEST-ONLY, no source change) -> r7q (in progress, see below). Columns: lines added/removed.

| file | frozen to r7m | r7m to r7n | r7n to r7o | new files it needs | runs under Design A (my reading, unverified) |
|---|---|---|---|---|---|
| scripts/run_real_check.py | +211/-60 | +23/-9 | same | jsonread, regfile, scrub, tls_trust, pathconfine, refusing_args | YES (entry point) |
| scripts/crash_desk.py | +16/-3 | same | same | (none) | YES (child process the run starts) |
| scripts/http_guard.py | +191/-11 | same | same | jsonread | YES |
| load_tools/check_invariants.py | +218/-59 | same | same | jsonread, regfile, pathconfine, refusing_args | YES (the final table) |
| load_tools/load_driver.py | +322/-48 | same | same | jsonread, netconnect, regfile, pathconfine, refusing_args | YES (`send_with_retries` is imported by the run) |
| src/lead_desk/config.py | +22/-8 | same | same | jsonread, regfile | YES (desk and run settings) |
| src/lead_desk/constants.py | +123/-1 | same | same | (none) | YES |
| src/lead_desk/envnum.py | +51/-4 | same | same | (none) | YES (every numeric setting) |
| src/lead_desk/db.py | +1/-1 | same | same | (none) | YES (desk) |
| src/lead_desk/desk.py | +80/-8 | same | same | errcode, jsonread, regfile | YES (desk: cap, model call) |
| src/lead_desk/server.py | +45/-9 | same | same | jsonread | YES (desk process) |
| src/lead_desk/hooks.py | +4/-3 | same | same | regfile | YES (crash flags) |
| src/lead_desk/lockfile.py | +7/-3 | same | same | regfile | YES (desk process) |
| src/lead_desk/portal_api.py | +8/-3 | same | same | jsonread, regfile | YES (desk process imports it) |
| src/lead_desk/adapters.py | +2/-1 | same | same | jsonread | YES (loaded by the desk) |
| src/lead_desk/run_stats.py | +5/-1 | same | same | regfile | YES (imported by smtp_provider and crm_hubspot; writes only when they send) |
| src/lead_desk/live_claude.py | +20/-16 | +25/-14 | same | jsonread, regfile, scrub | YES when the live model is on (`--live-model`); its request/cost functions are used by the banner either way |
| src/lead_desk/imap_count.py | +197/-9 | +3/-0 | same | netconnect, scrub, tls_trust | YES (the independent mail count: Design A keeps it) |
| src/lead_desk/smtp_outbox.py | +7/-2 | same | same | (none) | IMPORTED and partly used: imap_count reads its `_HOST_NAME`; the sending class runs only if the desk is set to send mail itself |
| src/lead_desk/smtp_provider.py | +74/-31 | +4/-0 | same | netconnect, regfile, scrub, tls_trust | PART: settings (`ProviderSettings.from_env`, `max_sends`, recipients), `read_secret_file` (used by imap_count) and the banner run in the script itself; the SEND path runs only if the desk sends the mail (under Design A n8n sends, so not) |
| src/lead_desk/crm_hubspot.py | +17/-24 | +5/-3 | same | jsonread, regfile, scrub | PART: `HubspotSettings.from_env`, `max_calls`, the secret-file check and the banner run in the script; the CRM calls run only if the desk writes the CRM (under Design A n8n does, so not) |
| src/lead_desk/trace.py | +6/-5 | same | same | regfile | UNVERIFIED: no import of it found in the run chain on tree-R7O (my own search) |
| demo_only/fakes.py | +2/-2 | same | same | regfile | YES when adapters=demo: run_real_check.py sets DESK_ADAPTERS=demo for the desk it starts (loader imports it) |
| demo_only/portal_demo.py | +39/-21 | same | same | jsonread, regfile | YES when adapters=demo (same reason) |
| demo_only/fake_hubspot.py, fake_imap.py, fake_smtp_tls.py | +23/-21; +27/-4; +16/-2 | same | same | bad_request (hubspot) | ONLY in the `--dry-fakes` self-test (run_real_check.py lines 160-260): not in the real take |
| demo_only/fake_model_server.py | +71/-14 | same | same | bad_request, jsonread, regfile, pathconfine, refusing_args | dry-fakes / self-test; not in a real take (unverified) |
| demo_only/fakes_server.py | +61/-19 | same | same | bad_request, refusing_args | NO for the run itself: started by scripts/start_all.* (a separate script) |

Only `src/lead_desk/regfile.py` changed from r7n to r7o in source (it is a new file, so it is "new" for the take). r7p changes no source file.

## New files the take does NOT have, which on-path files need (dependency closure, from the imports of tree-R7O)
These must come with any on-path file, or the on-path files fail to import:
`src/lead_desk/scrub.py` (no new imports), `src/lead_desk/jsonread.py` (none), `src/lead_desk/errcode.py` (none), `src/lead_desk/netconnect.py` (none), `src/lead_desk/regfile.py` (needs jsonread, scrub), `src/lead_desk/tls_trust.py` (needs regfile), `tools/pathconfine.py` (none), `tools/refusing_args.py` (none), `demo_only/bad_request.py` (none; needed by demo_only fakes in self-test only).
Not needed by the take's run: `scripts/desk_setting.py`, `scripts/refusals.py`, `scripts/reset_check.py` (nothing on the path imports them in my tree).

## Minimal patch subset (files), in two tiers
1. **Must-have (the run itself):** the 9 new files above (except bad_request), plus the changed versions of: run_real_check.py, crash_desk.py, http_guard.py, check_invariants.py, load_driver.py, config.py, constants.py, envnum.py, db.py, desk.py, server.py, hooks.py, lockfile.py, portal_api.py, adapters.py, run_stats.py, live_claude.py, imap_count.py, smtp_outbox.py, smtp_provider.py, crm_hubspot.py, demo_only/fakes.py, demo_only/portal_demo.py, plus the tests that guard them. Replacing only SOME of these will not work: they import each other and the new files (for example imap_count needs netconnect, scrub, tls_trust, and reads smtp_provider.read_secret_file).
2. **Self-test only:** demo_only/fake_hubspot.py, fake_imap.py, fake_smtp_tls.py, fake_model_server.py, bad_request.py.
3. **Not on the path (pause):** demo_only/fakes_server.py, demo_only/burst.py, load_tools/catcher.py, scripts/start_all.*, reset.*, feed.py, n8n_api.py, hubspot_probe.py, check_schema.py, run_live_check.py, tools/scrub_n8n_export.py, trace.py (unverified), docs, README, CHANGELOG.

## What the take's tree must be (ORDER C-CORRECT)
The r7p tree plus the r7q on-path fixes, never r7n alone. Open findings that touch ON-PATH files: money Major (banner worst-case model cost, run_real_check.py about line 1054), M9-74 and M9-79 checks, the echo-server test (done in r7p, unverified), hygiene literal (done in r7p, hygiene NOT run), MemoryError in secret_boundary (scrub.py), R08/K01 test gaps, the guard, the demo_only fakes' stray log line. r7q is being built now (builder aab1bf4c); then EV7P with the hygiene scan, then a fresh uncapped reviewer. Status of every step is in REPORT.md.

## Next step that would confirm this list
A runner that executes `run_real_check.py --dry-fakes` and a real-mode refusal run under `unshare -n` with `python -X importtime` or `sys.modules` dumped to a file, then diffs the module list against the table. Not started.
