# ON-PATH LIST: the take's imported files and which hardening changes touch them

Updated 2026-11-14 12:50 UTC (18:20 IST) for r7q and r7r (new section 'r7q and r7r' below); first written about 11:00 UTC (16:30 IST) by the core lead, from the lead's list `handover/core/TAKE-USED-FILES.md` (take head 27a1ed8) and my own trees. Supersedes my provisional version.

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

## r7q and r7r: what changed on the path (added 12:50 UTC / 18:20 IST; builder, evidence and lead evidence in handover/core/fix/)
Release chain now: ... r7p (test-only) -> r7q (on-path source and tests; EV7P found two failing tests) -> **r7r (two test files only; source and scripts byte-equal to r7q; this is the tree that goes to the take)**. Evidence on r7r: EV7R, full run in a staged git copy, 6021 passed, 7 skipped, 0 failed (runner's number). Independent egm review of r7q/r7r: started by the laptop lead 12:41Z, result not in yet.

| file changed in r7q | what changed | runs under Design A (my reading, still unverified, not traced) |
|---|---|---|
| scripts/run_real_check.py | banner worst-case model cost now the largest request over every person and the twin (`longest_request_bytes`, `new_tag` once per run); `MODEL_CALLS_PER_LEAD` taken from `MODEL_CALLS_PER_LEAD_MAX` | YES (entry point; the banner is what the person reads before the Start answer) |
| src/lead_desk/scrub.py | `MemoryError` passes through `secret_boundary` with its error chain scrubbed; docstring says what is not followed | YES (imported by imap_count, live_claude, regfile, crm_hubspot, smtp_provider) |
| demo_only/bad_request.py | new `QuietServer` (silences only closed-connection errors) | only when adapters=demo or `--dry-fakes` self-test; no effect on the real take |
| demo_only/fake_hubspot.py, fake_model_server.py | use `QuietServer` | `--dry-fakes` self-test only |
| demo_only/fakes_server.py | uses `QuietServer` | NO for the run itself (started by scripts/start_all.*) |
| tests/test_r7n_findings.py, tests/test_r7q_findings.py (new), tests/test_file_call_guard.py (r7r) | tests and the guard allow-list | not run in the take; they guard the files above |

Consequences for the minimal subset: scripts/run_real_check.py and src/lead_desk/scrub.py are now the r7r versions (not the r7n/r7o ones listed above). The demo_only files are optional for the take (self-test only). Not new needs: no new source file after r7o.

## Still open on the path (not fixed, stated plainly)
- M9-74 (exit 0 with contacts left): a desk-created contact missing from the HubSpot list, for a lead not yet marked CRM-done, is not archived and does not fail the exit. Not probed; argued from source only; reachability unknown. Under Design A (n8n writes the CRM) the desk's own CRM path does not run, so it may be off-path: not confirmed.
- M9-79 (live worst case with crash restart): reachable maximum read, not measured.
- QuietServer would also hide a handler bug that surfaces as BrokenPipe (demo fakes only).
- The independent reviewer's findings: not in yet.

## Next step that would confirm this list
A runner that executes `run_real_check.py --dry-fakes` and a real-mode refusal run under `unshare -n` with `python -X importtime` or `sys.modules` dumped to a file, then diffs the module list against the table. Not started.
