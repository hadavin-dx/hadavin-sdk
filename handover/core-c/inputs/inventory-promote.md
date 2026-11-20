# Promotion inventory (read-only Fable Explore agent, 2026-11-20; condensed by the lead)
Full row table (about 85 rows, read depth R/O marks) is only in the agent hand-back of lead session 2026-11-20; this file keeps the decisions. Roots: LD = `_local\scratch\wt\dpld-demo-final` (HEAD d3eff65), JG = `projects\jagrat`, AYD = `projects\hadavin-sdk\demos\ask-your-data`, SDK = hadavin-sdk origin/main 51c9fc4fb. ATLAS-CHECKED: `research\tool-atlas\README.md`, `n8n.md`, `crm\README-crm.md`, `crm\hubspot.md`, 2026-11-20 (16 other CRM cards not opened). Every claim on an outline-only row beyond its docstring is UNVERIFIED (builders re-read before coding).

## Ten best promotions, in order (all guarantee-class or reusable; neither n8n/Make nor a CRM provides them)
1. Spend reserve/settle ledger: merge `LD live_claude.SpendLedger` and `AYD askdata\meter.py` into one core piece beside `limits.py` (core charges after the call today; no pre-call reserve).
2. Effect-once flow: `LD desk.py` (`_claim`, `_take_token`, `_crm_step`, `_send_claimed`, `_record_send_result`, `_requeue_sending`) plus the `receipts` table of `schema.sql` (UNIQUE source+ref, immutable payload, write-once verdict). Check against `actions/executor.py` first (the blind-target / `unknown` branch looks new, UNVERIFIED).
3. Bounded call with worker caps: `LD desk.py:_bounded` / `_Call`; removes three hand copies.
4. Single-instance file lock: `LD lockfile.py` as is; make `live_claude._FileLock` and `askdata\meter.py` use it.
5. Write-failure taxonomy and effect ports: `LD adapters.py:_failure/_exchange` and the keyed/blind capability and error family from `contract.py`.
6. Untrusted-text quarantine plus quoted-span citation check: `JG quarantine.py`, the `facts.py` kernel, `grounding.citation_problems` (completes `runtime/evidence.py`).
7. Crash-point test harness into `hadavin_sdk.testing`: `LD hooks.py`, `trace.CrashWindows`, `tests\crash_launcher.py`.
8. Local server safety kernel: Host/Origin/Sec-Fetch-Site gate, deadline/slot/descriptor code, read-only snapshot helpers from `LD server.py` and `portal_api.py`.
9. Text safety: `AYD safe_text.clean` as is; `LD identity.py` character checks.
10. Time-window gate and post-action checks: `JG freeze.py` + `expected.py` as one window model, `symptom.judge`, `landed.since_fix`.
Next in line: FairGate/FairSemaphore (only with an SQLite store kind), read-only Postgres source (`AYD pgsource.py`), eval freeze/seal (`AYD evalset.py`), `JG tests\conftest.py` socket guard, `JG tests\test_import_closure.py`, multi-root path confinement (`JG paths.py` into `config.confined`), `JG handback.py` (check the K6 plan first), `JG catalog` live-value bounds, `hedge` (the SDK header says it was deliberately not ported: ask first).

## Duplicates to remove (hand-copied code, the clearest signal)
Three file locks, two spend ledgers, three path-confinement helpers, two no-redirect openers outside the SDK one, three secret-file readers (SDK `secrets_file.py` exists). CUT in the demo: `run_stats.py`, `safe_path.py`, `scripts\http_guard.py`, `read_approvers` (SDK principals), `live_claude.LiveQualifier` (SDK llm clients).

## Not core (stays in the project or in the tool)
Portal lists, charts, owner rota, pipeline steps, reminders and email dedupe are CRM features; sending mail and the webhook door are n8n features; HubSpot keyed put is vendor code (the atlas says test the native upsert first); Jagrat verifier, models, playbook, platforms, knowledge are use-case code (the owner rule bans those words from core). Portal UI shell (`portal.js`, tokens, `list.js`): half is a generic safe UI kernel; compare first with `egm\portal-kit` and `archive\projects-old-2026-11-14\hadavin-portal-kit` (NOT read). Caveat: `projects\jagrat\pyproject.toml` points to `vendor/portal-kit`, which does not exist in the tree.

## Not read (UNVERIFIED)
Most of `tests\` in LD (about 100 files), `portal\pages\*`, `demo_only\*`, `n8n\*.json`, docs, JG `data\*`, AYD `db\*`, SDK test files and most module bodies, `egm\portal-kit\*`, `make.md`, `n8n-coverage.md`, 16 CRM cards. JG held modules (bounds, history, chain, tools, links, cards, report, sim_db, cli) are not in the tree.

## Paths that look like personal or real data (paths only, not opened)
`projects\jagrat\tools\allowed_identities.txt` (names and emails), LD `scripts\real-run.env.example`, LD `demo_only\*.json` (`approvers_n8n.json`, `leadflow_n8n.json` may hold real names, written from a live n8n team table), LD `tests\portal_fixtures\*.json`, `projects\hadavin-sdk\snap855.tar`, `projects\hadavin-sdk\.claude\`, LD `.codeant\*.json`; about 60 `*.whl` files in the LD worktree root. No key, token or password value was seen.
