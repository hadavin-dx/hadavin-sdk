# L2 (a)+(b) report: SmtpOutbox and SMTP catcher

Built in /tmp/dpld-l2, staged only (not committed). Diff: /home/user/build/L2a.diff (4 files, 770 lines added).
Files: src/lead_desk/smtp_outbox.py, live_l2/catcher.py, live_l2/README-L2.md, tests/test_smtp_outbox.py.

## Not done or not checked (first)
- Loader NOT changed. `DESK_OUTBOX=smtp` / `DESK_ADAPTERS=smtp` would touch config.py, constants.py (ADAPTER_CHOICES, pinned by
  validation), loader.py and server.py: not a small change. Instead: `make_smtp_outbox(env)` and `load_smtp_adapters(config, env)`
  (demo CRM + Qualifier through loader.py, SMTP outbox swapped in). The launcher injects it before the server starts:
  `lead_desk.server.load_demo_adapters = lambda cfg: load_smtp_adapters(cfg, os.environ); server.main(hooks)`.
  DESK_ADAPTERS stays "demo", so the demo portal still loads. Only `test_loader_swaps_in_smtp_outbox` checks the swap
  (type and capability); no full desk run through SMTP was done.
- Connect-phase TIMEOUT (unroutable address) not tested: needs a non-loopback address, which hygiene forbids. The code path is
  the same `except (OSError, TimeoutError)` as a refused connect.
- Full test suite not run (as ordered). Windows not tested. TLS / AUTH not implemented (loopback catcher only).
- Settings live in smtp_outbox.py (`SmtpSettings`), not in config.py/constants.py, to touch no existing file. Env names are in
  the module docstring.
- Catcher `body_sha256` is over the decoded text with LF line ends minus ONE trailing line break. A body that itself ends in a
  line break was not checked against this rule (the L2-b checker should hash bodies without a trailing newline, or I should be told).
- Decision for the lead to confirm: a final-reply 4xx/5xx (after the text) maps to SendAmbiguous, not SendRefused (conservative,
  matches the order text "any error after the body started"). Failure before the text (silent server, hang-up, timeout in the
  greeting/EHLO/MAIL/RCPT/DATA steps) maps to SendUnreachable (nothing of the message left); 4xx/5xx there, greeting and EHLO
  included, maps to SendRefused.

## Mapping
| Situation | Exception |
|---|---|
| connect refused, no such host, connect timeout, any connect OSError | SendUnreachable |
| greeting / EHLO / MAIL / RCPT / DATA reply 4xx or 5xx | SendRefused |
| silence, hang-up or timeout before the text is offered | SendUnreachable |
| CR, LF or NUL in to / subject / send_key; recipient not a plain ASCII address; empty key | SendRefused, before any network use |
| timeout, hang-up, unreadable reply after the text started; any non-2xx final reply | SendAmbiguous |
| 2xx final reply | "SENT" (blind: never "ALREADY_SENT") |
Total deadline: one `_Budget`; every recv/send gets only the time left (own small SMTP client over socket, because smtplib
cannot give a total bound; stdlib only, no new dependency). `timeout <= 0` means DESK_SMTP_TIMEOUT_SECONDS.
Headers: X-Send-Key = send key; Message-ID = `<sha256(send_key)[:32]@DESK_SMTP_MESSAGE_ID_DOMAIN>` (same key, same id: a repeat is
visibly a repeat). UTF-8 goes out as quoted-printable/base64 (cte 7bit), so no 8BITMIME needed. Dot-stuffing done.
Exception texts carry codes and class names only, no addresses.

## Catcher (live_l2/catcher.py)
stdlib asyncio, backlog 1024, prints `LISTENING host port`. JSONL fields: ts, send_key, message_id, to, subject, body_sha256, mode.
Control: a text file (`--control`, default `<out>.mode`), read on every command: `ok`, `slow N`, `drop-after-data` (recorded, then
closed without final reply, record mode = drop-after-data), `reject` (550 at RCPT, nothing recorded), `down` (close at once;
a closed port = stop the process). Documented in live_l2/README-L2.md.
aiosmtpd: usable here (pip download worked through the proxy); version 1.4.6, Apache-2.0, uploaded 2024-05-18, source
pypi.org JSON, checked 2026-11-09. Not used (no new dependency; needs record-then-drop, delay and file-switched modes).

## Test results
`python -m pytest tests/test_smtp_outbox.py -q -p no:cacheprovider` -> `30 passed in 3.75s` (final run).
Covers: capability blind; headers + UTF-8 + dot-leading line round trip (hash match); two sends = two records; closed port;
RCPT 550; MAIL 450; greeting 554; drop-after-data (record exists, Ambiguous); slow final reply with 0.6 s budget (stops < 1.6 s);
final 550 and garbage; silent before text; dribbled greeting and dribbled final reply (1 byte / 0.2 s, stops within budget+0.6 s);
CR/LF/NUL in to/subject/key (12 cases) refused even with a closed port (proves "before network"); odd recipients; 50 concurrent
sends all land (50 distinct keys); catcher holds 200 connections; settings validation; loader swap.

## Fail-before (mutants, file restored each time, `git diff` of smtp_outbox.py clean afterwards)
- M1 post-DATA failure as SendRefused: 4 failed (drop_after_data, slow_final_reply, final_550_and_garbage, deadline_dribbled_final_reply).
- M2 drop the CR/LF/NUL check only: first run 27 tests all passed (the standard library's header check refused CR/LF anyway:
  an equivalent mutant for CR/LF). Added NUL cases; rerun: 2 failed (NUL in subject and key). So the early check is real for NUL.
- M2b drop the check AND the library-error catch: 8 failed (all CR/LF/NUL subject and key cases).
- M3 per-read timeout (5 s) instead of remaining budget: 4 failed (slow_final_reply, silent_before_text, deadline_dribbled_greeting,
  deadline_dribbled_final_reply; run took 20 s).
- M4 pre-text failure as Ambiguous: 2 failed (silent_before_text, deadline_dribbled_greeting).

## Lint, types, hygiene
- `ruff check` and `ruff format --check` on my 3 code files: All checks passed / already formatted.
- `mypy --platform linux` (repo config, src+tools): Success, no issues in 18 files. `bandit -ll -r src`: 0 findings. (live_l2/ is outside the mypy/bandit scope.)
- tests/test_hygiene.py: with my files: 2 failed, 7 passed: test_hygiene_scan_public (2 hits in tests/test_portal_log.py, not my files)
  and test_hygiene_wordlist (needs HYGIENE_WORDLIST): the two known-red on the clean base. My first version also failed
  test_no_demo_only_outside_loader (docstring named the demo folder); fixed, now green.
- Processes: every catcher subprocess is terminated by the fixture; no leftover (`pgrep -f catcher.py` empty).
