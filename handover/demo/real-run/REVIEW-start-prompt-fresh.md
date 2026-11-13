# rv20: independent review of start-prompt-hardening.patch (NOTES-start-prompt.md, evidence-q4f-*)

Reviewer: fresh, adversarial, shell. Base db54e13 (patch applies alone with `git apply --check`; also applies on 2db3926 per the builder, not re-run by me).
Studio bible is not on this machine, so no R-numbers were grepped or cited (preamble rule 1: stated). EGM: I am the independent reviewer step; I did not run egm:* skills. Token use: not measured.
Scratch: /tmp/work/rv20-main (clones repo, apx = v4+patch merge, apy = old code, mut = mutants, cfg_* = made-up configs, blk = socket harness).

## Safety record (what I did and did not do)
- NEVER answered y/yes. Non-terminal forms were driven with `n`, `yes n |` (an endless stream of n), EOF, /dev/null, closed stdin; the pty driver (pty_n.py) answers only `n`. I did NOT run `yes |`: the hard rule forbids it, and it takes the same code path as `yes n |` (the refusal looks only at isatty, before any read). An `input()` stub (RV_NOINPUT=1) that logs and exits was installed in every non-pty run, so even a bug could never have read a y.
- Network: ALL runs inside `unshare -rn` (worked: root-mapped user namespace; loopback brought up with an ioctl script because `ip` is not installed; external connect gave ENETUNREACH, DNS failed). On top of that a `sitecustomize.py` in the clone root raised on any non-loopback connect/getaddrinfo and logged every attempt (RV_LOG). Limit: the desk child process gets a whitelisted environment (no RV_LOG), so its attempts are not logged, only blocked by the namespace.
- Settings used: every config URL loopback (`http://127.0.0.1:9`, `localhost`), made-up key files (`made-up-key-NNNN`). The deliberately non-loopback values (vendor default by omission, evil lookalikes) were only ever run under unshare -n + the blocking harness, and only for the direct-desk test did the code try to reach a vendor name (blocked, logged).
- Processes I started (fakes server, desk) were killed by PID. Other processes visible in `ps` belong to other agents; untouched.

## VERDICT (honest)
The patch closes the incident as it happened (run_real_check.py / run_live_check.py: pipe plus an address omitted from the config) and I could not defeat that with the inputs listed in the brief. It does NOT close the incident class for ALL entry points of the desk that can send to the vendor: the desk itself still defaults to the vendor with no refusal and no question (Major 1, measured). It also does not merge with real-run-fixes-v4 by the builder's "mechanical" recipe (Major 2, measured: 49 of 66 tests of v4's new file fail after the union merge).

## FAILURES FIRST

### Major 1: the desk itself still sends to the vendor by omission (class not closed)
Measured under unshare -n + blocking harness, made-up key file, no DESK_HUBSPOT_BASE_URL anywhere:
```
DESK_CRM=hubspot DESK_HUBSPOT_KEY_FILE=<made-up> DESK_HUBSPOT_MAX_CALLS=5 python -m lead_desk.server   (+ demo fakes for mail)
POST one canned lead (scripts/feed.py)  ->  201
desk log: "follow-up steps 1-2 failed after the claim: CrmError" (x3)
connect log: getaddrinfo 'api.hubapi.com' BLOCK  (x3)       <- it tried to send to the vendor; no prompt, no refusal
```
Same with `DESK_QUALIFIER=live_claude` + DESK_LIVE_* (fake model/prices/caps) and no DESK_LIVE_BASE_URL: `getaddrinfo 'api.anthropic.com' BLOCK`, desk log `LiveTransport`.
Reason: src/lead_desk/crm_hubspot.py (HubspotSettings.base_url default = HUBSPOT_BASE_URL; from_env only sets it `if "DESK_HUBSPOT_BASE_URL" in env`) and config.py LiveSettings/_live_from_env have the same vendor default. Entry points that reach this: `python -m lead_desk.server`, scripts/crash_desk.py, scripts/start_all.sh/.ps1 (they start the server with whatever DESK_* the shell holds). There is no `take` script in the repo (grep): "take" = the two check scripts, which ARE covered. The NOTES say the desk default is "unchanged on purpose"; that is a decision, not a closure.
Why it matters: an agent or person who runs the desk with a valid private config that omits the address repeats the incident with zero prompts (the child of run_real_check is protected only because the script now refuses first).
Fix at the choke point (rule 7): make `HubspotSettings.from_env` and `_live_from_env` refuse when the address name is absent or blank ("DESK_HUBSPOT_BASE_URL is required: name the address, the vendor's own or a loopback address"), keep the constant only as documentation/example value; same for IMAP host in imap_settings (the script already does). Then unnamed_remote_default in the script becomes redundant (keep as a pre-banner message). Needs the demo/test fixtures to name the address (small).

### Major 2: the proposed mechanical merge with real-run-fixes-v4 is wrong for the tests (and has one semantic conflict)
I applied v4 on db54e13, committed it, then `git apply --3way` the patch: conflicts in docs/settings.md, run_live_check.py (3 hunks), run_real_check.py (4 hunks), tests/test_live_claude.py. I resolved them exactly as the builder says (keep both blocks, `_run` order: --assume-yes refusal, v4's --keep refusal, then the terminal check; question block from the patch with EXIT_STOPPED; import line merged; docs: v4 text plus the patch's four edits). Result: ruff check, ruff format --check, mypy linux and win32 clean. Code resolution is therefore right. Tests:
- tests/test_start_prompt_hardening.py + test_real_check_dry + test_live_claude + test_ledger_amounts + test_clock_steps: 280 passed, 1 failed (`test_a_terminal_reaches_the_question_and_n_stops`: v4 now refuses the filler key file the patch's `_config` writes, `refused: DESK_HUBSPOT_KEY_FILE`).
- v4's new file tests/test_take_script_refusals.py: 49 failed, 17 passed. Cause: the no-terminal refusal now comes first, so every v4 test that calls `rrc.main(["--config", ...])` or the live script by subprocess gets exit 2 with the no-terminal text instead of the refusal it asserts (e.g. `assert 2 == 3` for failed calls, `assert (2 == 1)`, `rrc.EXIT_BOOK_REFUSED == 4` got 2). The live subprocess tests also lack `--base-url`/`--assume-yes`.
- Semantic conflict: v4 documents and tests "no terminal = stopped, exit 1" (docs line and `test_live_check_without_a_terminal_stops_with_one_line_not_a_traceback`); the patch says "no terminal = refused, exit 2". Pick one (I recommend exit 2: it is a refusal before anything starts) and change the v4 docs text and test.
Needed resolution beyond the builder's: add the terminal stand-in (autouse fixture of test_real_check_dry) to test_take_script_refusals.py, pass `--base-url <loopback fake>` and `--assume-yes` in its live subprocess tests, fix the key content in the patch's `_config`, settle the exit code. Not testable by me: real-run-fixes-v5 (does not exist), v4-after-sonar-p3 (needs sonar P3 first).

### Minor 3: the AST guard is weaker than advertised
`test_every_script_that_asks_a_question_checks_for_a_terminal_first` (`_reads_a_person`). Measured on 17 snippets: DETECTED only `input()` and `sys.stdin.readline()`. MISSED: `getpass.getpass()` (a code bug: the `getpass` attribute test sits inside the `stdin` test), `from getpass import getpass as g`, `builtins.input`, `ask = input`, `from sys import stdin; stdin.readline()`, `sys.stdin.buffer.read()`, `for l in sys.stdin`, `open(0)`, `open('/dev/stdin')`, `os.read(0, n)`, `fileinput.input()`, `sys.__stdin__.read()`, `click.confirm`, `msvcrt.getch`, `select` on stdin, and a shell `read -p` inside subprocess. Scope: walks scripts/ load_tools/ tools/ src/ demo_only/ only (not tests/, n8n/, root .py, *.sh/*.ps1; I grepped the .sh/.ps1: no read/Read-Host today). The order check is a textual `index()` comparison. It is a tripwire for a new `input(` only; behaviour tests (below) carry the real guarantee.

### Minor 4: hubspot_probe.py consent
Adequate as a deliberate act, not as protection against an unattended caller: no question, no terminal check; `--yes-spend-calls 7` (must equal the plan) plus a token in an env var is all it needs, and the address is the built-in vendor constant (that is its whole purpose; there is no config to omit from, so the incident's cause cannot occur). Anything that can set the env var and pass the flag makes 7 real calls. I would accept it, and recommend (cheap) refusing a non-terminal stdin there too, or leaving it as is with the decision recorded. Parser differential found in its `--dry-run` check (loopback test uses `urlsplit().hostname`): `--dry-run 'http://evil.test\@127.0.0.1:9'` is ACCEPTED (hostname = 127.0.0.1) while urllib asks the resolver for the literal `evil.test\@127.0.0.1` (measured: getaddrinfo 'evil.test\\@127.0.0.1', blocked). That string is not a valid host name, so I do not claim an exploit; I did not test a resolver that answers it. The user must also type the flag, so risk is low. Same differential exists in run_live_check `_loopback_url` but LiveSettings then refuses it (measured), so no effect there.

### Minor 5: not measured
Windows: `sys.stdin.isatty()` for `< NUL` and a closed handle on a Windows console was not run (only mypy win32). I recall that the NUL device has historically been reported as a tty on Windows by some Python versions; UNVERIFIED. Please run `python scripts\run_live_check.py ... < NUL` on the owner's Windows Python 3.13 and confirm exit 2.

### Nits (docs/wording, measured by reading)
1. scripts/real-run.env.example line 53 still lists `REAL_IMAP_n_HOST` under "Optional:" while line 42 says REQUIRED. Contradiction.
2. Same file line 22 "Optional (only with --live-model): the DESK_LIVE_* names": does not say DESK_LIVE_BASE_URL is now required with --live-model (run_real_check docstring and settings.md do).
3. docs/settings.md exit-codes bullet is jumbled: after "1 stopped..." it says "2 includes standard input is not a terminal ..." then continues with the traceback clause and a second "2 refused at the start". Reorder (rule 14).
4. docs/settings.md run_live_check flag list (end of the n8n_api bullet) does not list `--assume-yes`.
5. The banner printed before `Start? [y/N]` shows counts but NOT where the keys go (measured in the pty run). Recommend one line per destination (CRM host, each mailbox host, SMTP host, model host) so a person sees "api.hubapi.com" before typing y.
6. The IMAP host value is not validated at all (any text counts as "named"; an unreplaced `<IMAP_HOST>` is accepted and just fails at DNS). Harmless; a one-line shape check would catch typos before the question.
7. Pre-existing, out of patch scope: HubspotSettings checks the vendor suffix on `urlsplit().hostname` without percent-decoding: `https://evil.test%2f.hubapi.com` is ACCEPTED without ALLOW_ANY (measured), while urllib's Request.host is `evil.test/.hubapi.com` (not a valid host name; I did not run the connect). Worth fixing at the same choke point as Major 1 (refuse `%` in the host).

## (a) Every start/confirm prompt refuses a non-interactive stdin: PASS (patch scope)
Run under unshare -n + harness; each: exit code, "Start?" never printed, `input` stub never reached, connect log 0 lines.
| script | stdin | result |
|---|---|---|
| run_real_check --config valid | `echo n \|` | exit 2, refused text |
| | file with n | exit 2 |
| | /dev/null | exit 2 |
| | here-string n | exit 2 |
| | closed (`<&-`) | exit 2 |
| | `yes n \|` | exit 2 |
| | pty, n only | question reached (valid config), `n`, exit 1 "stopped, nothing was called" |
| run_live_check loopback url | pipe n / vendor url + /dev/null / closed | exit 2 each, 0 connect |
| | pty n | question, exit 1 |
| both | `--assume-yes` | real: only with --dry-fakes; live: only with loopback --base-url (see c) |
Builder's tests also pipe `y\n`/`yes\n` with `input` raising (29 tests pass). I confirmed fails-before: new file on db54e13 = 26 failed, 3 passed (the 3 passing are the unchanged `--assume-yes` rules and the pty-question case, expected).
What remains possible: anything that gives the script a pseudo-terminal and types y: `expect`, `script`, a python `pty` driver (mine, with n), a CI pseudo-tty, `ssh -tt`. No isatty-based measure can tell it from a person. Stricter measures, weakest to strongest: (1) print the destinations in the banner and require the person to TYPE the CRM host name (or the call cap) instead of y: defeats a blind `yes |`, a pty script can still parse the banner; (2) a changing word/number shown in the banner and echoed back, same limit; (3) a time bound adds little against a script; (4) real protection is out of band: a hand-made approval file (config hash + plan numbers + expiry minutes) created by the owner outside the session, which the script checks before it starts. I recommend (1) now plus (4) for anything that reaches a real account.

## (b) Omitted address refused BEFORE anything starts, nothing connects: PASS for the two scripts
pty runs (so the stdin guard does not hide the result), under the harness, 0 connect lines each:
- DESK_HUBSPOT_BASE_URL dropped: `refused: DESK_HUBSPOT_BASE_URL: not named in the settings; ...` exit 2
- REAL_IMAP_1_HOST dropped / REAL_IMAP_2_HOST dropped: refused with that name, exit 2
- `--live-model` with DESK_LIVE_BASE_URL absent: refused, exit 2
- value blank, `""`, `''`, whitespace only: refused (4 of 4)
- run_live_check without --base-url: refused (exit 2) in both pipe and pty runs
- config parsing path: `load_env`, REQUIRED check, unnamed check run before any settings object; 0 connects on every refusal path above. Loopback config + `--dry-fakes --assume-yes`: exit 0 under unshare -n, harness log 130 loopback entries (parent process only), 0 BLOCK.

## (c) Bypass hunting (table run through run_live_check._loopback_url, HubspotSettings, LiveSettings, urllib Request.host)
- Looks loopback but is not: `127.0.0.1.evil.test`, `localhost.evil.test`, `http://127.0.0.1@evil.test`, `[::1]@evil`, `0.0.0.0`, `127.1`, `2130706433`, `0x7f.0.0.1`, `017700000001`, trailing dots (`localhost.`, `127.0.0.1.`), `127.0.0.1%2eevil.test`, `127.0.0.1:9@evil.test`, `[::1%25eth0]`: refused by `_loopback_url` and by every settings class. Uppercase `LOCALHOST`/`LocalHost:9` accepted as loopback (correct, hostname is lower-cased).
- `_loopback_url` alone says True for `127.0.0.2`, `[::ffff:127.0.0.1]`, `http://127.0.0.1#@evil.test`, `http://evil.test\@127.0.0.1`; the settings classes then refuse all of them, so the second layer holds (measured end to end with `--assume-yes --base-url 'http://evil.test\@127.0.0.1:9'`: refused by LiveSettings, 0 connects). DNS names that resolve to loopback (e.g. localtest.me style) are refused by name (only `localhost` and IP literals pass); I did not resolve any real DNS name.
- DESK_HUBSPOT_ALLOW_ANY_BASE_URL=yes: lifts the vendor-suffix rule: any https host, and it is REQUIRED even for `http://127.0.0.1` (measured: refused without it). It is not in scripts/real-run.env.example; run_real_check does `setdefault("no")`, so only a line in the config file turns it on (the builder's make_synthetic_config adds it for loopback). With ALLOW_ANY=yes the key goes to whatever is NAMED: that is the intended meaning, and the patch only guarantees "named", not "right".
- Names outside the config file: the parent shell's DESK_HUBSPOT_BASE_URL/REAL_IMAP_n_HOST do NOT satisfy the check (measured, refused) and child_environment passes only DESK_*/REAL_* from the config plus PATH/HOME/TEMP-style system names (code read; the child never sees src defaults overridden by the shell).
- Desk started by other paths with the vendor default: see Major 1 (server, crash_desk, start_all, DESK_QUALIFIER=live_claude).

## (d) Sibling sweep
Grep of input(/getpass/stdin: the builder's AST walk covers src, scripts, load_tools, tools, demo_only; I additionally grepped the .sh/.ps1 scripts for read prompts (none). Only the two scripts ask. hubspot_probe: see Minor 4. n8n_api.py: refuses non-loopback http (not re-tested). No other script prompts. Vendor-reaching code paths found by grep: crm_hubspot (desk), live_claude (desk), imap_count (only via run_real_check), smtp_provider (host required). AST guard: Minor 3.

## (e) Behaviour change and docs
Existing private configs are refused until they add DESK_HUBSPOT_BASE_URL and REAL_IMAP_n_HOST (and DESK_LIVE_BASE_URL with --live-model): documented in docs/settings.md (required list, new bullet, mailbox bullet), example file and the refusal text itself (names the setting and the fix). Truthful except the nits above. make_synthetic_config-q4f.py maps the two new placeholders to loopback (`http://127.0.0.1:9`, `localhost`) and adds ALLOW_ANY=yes; I used it unchanged for cfg_ok. real-services.md not updated (it points to the example and settings.md; acceptable).

## (f) Conflicts: see Major 2.

## (g) Mutants of my own: 16 against tests/test_start_prompt_hardening.py (14 killed, 2 survived)
M1 isatty except-branch returns True: killed. M2 `and`->`or` in the real-check guard: killed. M3 isatty replaced by `not closed`: killed. M4 blank counts as named: killed. M5 skip mailbox 1: killed. M6 only the first mailbox checked: killed. M7 every default treated as loopback: killed. M8 EOF at the question counted as y (real check): SURVIVED the new file, KILLED by existing test_real_check_dry::test_no_terminal_to_answer_on_is_a_stop_not_a_traceback. M9 live --assume-yes with any URL: killed. M10 live `_loopback_url` replaced by a substring test (`"127." in url or "localhost" in url`): SURVIVED (no test feeds lookalike URLs to `_loopback_url`; LiveSettings backstop refuses them, measured). M11 live terminal check dropped: killed. M12 live no-base-url refusal dropped: killed. M13 real terminal check removed: killed. M14 live EOF counted as y: killed. M15 live-model address check skipped: killed. M16 unnamed check disabled: killed.
Recommended extra test: lookalike table (127.0.0.1.evil.test, localhost.evil.test, userinfo forms, 127.1, 0.0.0.0, mapped, trailing dot) against `_loopback_url` and `unnamed_remote_default`.

## Checks run (raw)
- ruff check . : All checks passed. ruff format --check . : 147 files already formatted. mypy --platform linux and win32: Success, 26 source files each (venv /tmp/work/fresh-venv5, Python 3.12, ruff 0.17.4, mypy 2.4.1; the repo has no uv `test` group).
- `git add -A`, DPLD_REQUIRE_SCAN=1 with gitleaks 8.30.1 on PATH: tests/test_hygiene.py + tests/test_gitleaks_exceptions.py: 59 passed.
- test_real_check_dry, test_ledger_amounts, test_live_claude, test_clock_steps, test_env_numbers, test_portal_wording_and_masking, test_start_prompt_hardening: 652 passed in 327 s (builder said 663 passed + 3 skipped including hygiene; consistent). Not the whole suite.
- bandit not re-run (builder reports clean). Not run: Windows runtime, v5, 2db3926 apply, any real service.

## Does the patch close the incident class for ALL entry points that can send to the vendor?
No. Closed: the two check scripts (non-terminal stdin, omitted CRM/IMAP/model address), measured. Open: the desk process itself (server, crash_desk, start_all) for DESK_CRM=hubspot and DESK_QUALIFIER=live_claude, hubspot_probe (flag-only consent, by design), pty-driving automation (cannot be excluded by isatty), and any address that is named wrongly or with ALLOW_ANY=yes on purpose. Blocker/Major/Nit count: Blocker 0, Major 2, Minor 3, Nit 7 (Major 1 would be a Blocker if the claim is "all entry points").
