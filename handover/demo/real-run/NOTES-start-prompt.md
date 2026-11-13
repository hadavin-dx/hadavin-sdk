# NOTES: start-prompt hardening (patch: start-prompt-hardening.patch, bases db54e13 and 2db3926)
Preamble rules used: 5, 6, 7, 11, 12, 13, 19, 20 (the studio bible is not on this machine: R-numbers not grepped, not cited).
EGM skipped: I cannot invoke the egm:* reviewer agents from here; the lead runs the EGM review of this result. Evidence files: evidence-q4f-*.txt.

## What I found FIRST (reading code and the reviewer's evidence, before any change)
1. Did the start path refuse a non-interactive stdin? NO. scripts/run_real_check.py (line ~911 on db54e13) only did `input("Start? [y/N] ")` and caught EOFError. A pipe that holds `y` is read as a yes, exactly as the reviewer's report says. There was no isatty / stdin check anywhere (grep of scripts/, load_tools/, tools/, src/, demo_only/ for isatty, sys.stdin, input( , getpass: only the two input() calls below).
2. How did the reviewer get around it? He did not get around anything: nothing was there. He piped `y` into a VALID synthetic config. There is an `--assume-yes` flag, but it is already safe (refused unless `--dry-fakes`), and he did not use it.
3. Did anything refuse a non-loopback base URL? Only partly, and the gap is the one that bit:
   - HubSpot: HubspotSettings refuses a base URL that is not https at the vendor's own domains (or plain http to loopback) unless ALLOW_ANY=yes. But the DEFAULT is the vendor's own address (HUBSPOT_BASE_URL = https://api.hubapi.com), which passes that check. So a config that does not mention DESK_HUBSPOT_BASE_URL sends the key to the vendor by omission. That is why the valid synthetic config made 52 create attempts.
   - Mail reading (IMAP): REAL_IMAP_n_HOST defaulted to MAIL_IMAP_DEFAULT_HOST (the provider's public host) in imap_settings(); nothing refused a config that omitted it. (It was never reached in the incident because nothing got far enough; it is the same hole.)
   - SMTP: DESK_SMTPP_HOST is in REQUIRED, so it is always named. No change needed (a named host is the settings explicitly naming it).
   - Live model: DESK_LIVE_BASE_URL defaults to LIVE_DEFAULT_BASE_URL; LiveSettings refuses any other non-vendor host, but the vendor default is accepted when omitted. run_live_check.py had `--base-url` default = that vendor address.
   - run_live_check.py: `input()` with no EOF handling (traceback on a closed stdin) and the piped existing tests (tests/test_live_claude.py) answered `y` through a pipe on purpose.
4. Honest limit: I did not re-run the incident. The hard rule forbids answering y; all my evidence is code reading plus tests in which `input`, the desk, the fakes, `run_model` and every socket connect raise if reached.

## What the patch does (function-level, kept small for the rebase over real-run-fixes-v5)
scripts/run_real_check.py
 - NEW module constant NO_TERMINAL_TEXT (after the EXIT_ line), NEW functions stdin_is_terminal() and unnamed_remote_default(env, live_model) (just before imap_settings()).
 - _run(): two inserted blocks. (a) right after the existing `--assume-yes without --dry-fakes` refusal: `if not (a.assume_yes and a.dry_fakes) and not stdin_is_terminal(): print(NO_TERMINAL_TEXT); return EXIT_REFUSED` (exit 2, before DryFakes, config reading or any start). (b) right after the `missing` (required names) refusal: `unnamed = unnamed_remote_default(...)`: refuses with `refused: <NAME>: not named in the settings; ...` exit 2.
 - Imports: urlsplit; is_loopback_host; HUBSPOT_BASE_URL, LIVE_DEFAULT_BASE_URL. Docstring of the module: required names and the terminal rule. The existing EOFError handler at the question stays as a backstop (terminal closes under the question: exit 1).
 - The documented scripted flag already existed and is safe: `--assume-yes` only with `--dry-fakes` (local fakes). Unchanged.
scripts/run_live_check.py
 - NEW NO_TERMINAL_TEXT, stdin_is_terminal(), _loopback_url(); main(): `--base-url` default None (no vendor default); NEW flag `--assume-yes` (only with a loopback --base-url); three refusals after the leads/runs check (no --base-url, --assume-yes with a non-loopback, stdin not a terminal); the question is wrapped (EOFError = stop, exit 1, no traceback). Removed import LIVE_DEFAULT_BASE_URL.
scripts/real-run.env.example, docs/settings.md: DESK_HUBSPOT_BASE_URL and REAL_IMAP_n_HOST are now required and documented (placeholders <HUBSPOT_ADDRESS> and <IMAP_HOST>), terminal rule, exit-code text.
tests: NEW tests/test_start_prompt_hardening.py (29 tests). Edited existing tests only where the new rule applies: tests/test_real_check_dry.py (autouse fixture that stands in for a terminal; _config_file names the three addresses; live config names DESK_LIVE_BASE_URL), tests/test_ledger_amounts.py (2 places: --assume-yes with loopback / a terminal stand-in), tests/test_live_claude.py (the `y` through a pipe became `--assume-yes` against the loopback fake; the `n` through a pipe became "a pipe is refused").

## Sibling sweep (every y/N, "type yes", input(), getpass, stdin read)
| script | behaviour | action |
|---|---|---|
| scripts/run_real_check.py | `Start? [y/N]` | fixed (above) |
| scripts/run_live_check.py | `Start? [y/N]`, paid model | fixed (above) |
| scripts/hubspot_probe.py | no question; needs `--yes-spend-calls 7` (must equal the plan) and a token from an env var; always the vendor address unless `--dry-run` names a loopback stub | NOT changed: its explicit numeric flag is the deliberate consent, the vendor is its whole purpose, it never prompts. Stated, a decision for the lead (could also require a terminal). |
| scripts/n8n_api.py, reset.*, start_all.*, feed.py, crash_desk.py, check_schema.py | no prompt | none needed (n8n_api already refuses non-loopback http) |
| load_tools/, tools/, src/ | no input()/stdin | none |
| demo_only/ | no input()/stdin | none (noted only) |
A test (test_every_script_that_asks_a_question_checks_for_a_terminal_first) walks scripts/, load_tools/, tools/, src/, demo_only/ with ast and fails if a new input()/getpass/stdin read appears outside these two files or before the terminal check.

## Evidence
- evidence-q4f-fail-before.txt / -reasons.txt: new test file on db54e13 scripts: 26 failed, 3 passed. The behavioural failures are `Reached` (old code reached the question / desk / fakes on a non-terminal stdin and an unnamed address). Some failures are AttributeError for the new function names (those prove only that the functions are new).
- evidence-q4f-mutants.txt: 17 mutants, 17 killed (terminal check removed / fail-open / always true, both scripts; unnamed-address check off, per setting HubSpot / IMAP / live; blank counted as named; loopback accepted for unreadable URL; EOF handler off).
- evidence-q4f-tests-after.txt: 663 passed 3 skipped, 1 failed (hygiene found two URL literals in my new test: fixed, rerun in evidence-q4f-hygiene-gitleaks.txt: 117 passed, with gitleaks 8.30.1 and DPLD_REQUIRE_SCAN=1). Files run: test_ledger_amounts, test_live_claude, test_clock_steps, test_env_numbers, test_portal_wording_and_masking, test_hygiene, test_gitleaks_exceptions, test_start_prompt_hardening, test_real_check_dry. NOT the whole suite.
- evidence-q4f-lint-mypy-bandit.txt: ruff check, format, mypy linux and win32 clean, bandit -ll no issues, gitleaks dir and git no leaks. (`gitleaks dir .` inside my clone reports 81 matches: those are inside my local .venv; the staged-tree export is clean.)
- evidence-q4f-harness.txt: real script and live script with a made-up synthetic loopback config (settings used: DESK_HUBSPOT_BASE_URL=http://127.0.0.1:9 + ALLOW_ANY=yes, DESK_SMTPP_HOST=localhost, REAL_IMAP_n_HOST=localhost): piped stdin exit 2 with the fixed message; pseudo-terminal: question reached, only `n` sent, exit 1; unnamed HubSpot / IMAP host refused exit 2. I never sent y.
- evidence-q4f-apply-matrix.txt. make_synthetic_config-q4f.py: the harness config maker with the two new placeholders mapped to loopback.

## Apply matrix and conflicts
 - applies alone (git apply --check) on db54e13 and on 2db3926.
 - with real-run-fixes-v4.patch (either order) it CONFLICTS in: scripts/run_real_check.py (docstring top + _run: the same lines v4 touches), scripts/run_live_check.py (docstring and main), docs/settings.md, tests/test_live_claude.py, tests/test_real_check_dry.py. Resolution is mechanical: keep both blocks; the two _run insertions go (a) after the --assume-yes refusal, (b) after the `missing` refusal, before v4's desk_setting_problem call, and v4's new refusals use the same `refused: <NAME>: text` form. real-run-fixes-v4-after-sonar-p3.patch itself applies only after the sonar P3 patch (it fails alone on db54e13 and 2db3926 at run_real_check.py:87), so I could not test it directly; it will conflict in the same files.
 - Not tested: rebase over real-run-fixes-v5 (not yet written).

## Not done / uncertain
 - A tty of a kind where isatty() is true but nobody is there (e.g. `script`, `expect`, a CI pseudo-terminal) cannot be told from a person: the guard stops pipes, files, /dev/null and schedulers, not a program that drives a pseudo-terminal (my own harness does exactly that, with n). Nothing short of a fixed human check could; say if you want an extra typed confirmation of the vendor address.
 - Windows: only mypy --platform win32; sys.stdin.isatty() on a Windows console not run.
 - The desk's own default of DESK_HUBSPOT_BASE_URL / DESK_LIVE_BASE_URL is unchanged for the desk itself (it is the product's documented default); only the check scripts demand it be named.
 - I expect real-run.env.example users to need the two new lines; existing private config files will be refused until they add DESK_HUBSPOT_BASE_URL and REAL_IMAP_n_HOST (intended).
