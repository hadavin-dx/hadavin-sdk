# NOTES: start-prompt-hardening-v2.patch (replaces start-prompt-hardening.patch) and desk-address-required.patch
Preamble rules used: 5, 6, 7, 11, 12, 13, 19, 20. The studio bible is not on this machine: R-numbers not grepped, not cited.
EGM skipped: I cannot invoke the egm:* skills here; the lead runs the independent review of this result. Evidence: evidence-q4g-*.txt.
Hard rules kept: I never typed y or yes, never typed the destination host at a real question, no push, no network write, made-up data only.
Every script and every pytest run went through `unshare -rn` (loopback brought up by an ioctl script, `ip` is missing) with a
sitecustomize that blocks and logs any non-loopback connect or name lookup. The clone of the public repo was the only network read.
The desk-process test also installs the same blocker inside its child. Block lines logged in all runs: 0.

## FAILURES AND LIMITS FIRST
1. Windows is NOT run. Nothing here ran on Windows. mypy --platform win32 passes (it type-checks the ctypes call). The GetConsoleMode call
   itself (`terminal_guard._windows_console_input`) was never executed; only the logic around it is tested, with a stand-in.
   Known: Microsoft documents GetConsoleMode as succeeding only on a console handle (fails on NUL, pipes, files); libuv and Rust `IsTerminal` use it.
   Unknown: what `sys.stdin.isatty()` returns for `< NUL` on the owner's Python 3.13 (the C runtime's isatty has historically said True
   for any character device, NUL is one). Decision: on Windows isatty() alone is never trusted; the handle must also pass GetConsoleMode, so the
   unknown does not matter. Cost: a Git Bash (mintty) window, whose stdin is a pipe, is refused too (fail closed). Please still run once
   `python scripts\run_live_check.py ... --base-url <loopback> < NUL` on the owner's Windows: expected exit 2, "needs a person at a terminal".
2. A program that drives a pseudo-terminal and reads the banner can still type the host. No terminal test can tell it from a person. My own
   harness drives a pty and types only `n`. For a real account the protection is still an approval file made by the owner outside the session (reviewer's option 4); not built.
3. The no-terminal check sits FIRST in `_run` (before any config read), as in v1: under a pipe the script refuses before it shows any
   config refusal. Consequence for tooling (list below). An alternative (check just before the banner, after the config refusals) would leave v4's 49
   config-refusal tests and run-dry-checks.sh untouched, but `--dry-fakes` would start its local fakes before refusing and the
   "nothing was started" guarantee gets weaker. I kept the stronger guarantee; the lead may choose.
4. Not run: the whole suite (lead runs it), real services, v5 (does not exist), v4-after-sonar-p3 (needs sonar P3).
5. hubspot_probe.py: unchanged (decision recorded, reviewer's Minor 4). It has no question; the consent is `--yes-spend-calls 7` + a token in the environment; the vendor address is its whole purpose.
   Making it refuse a non-terminal stdin is one line with `stdin_is_terminal()`; I did not do it because the flag is the deliberate act and its tests pipe nothing; say if you want it.
6. The nits I did not do: none open from the review (nit 7, the `%` in the host, is in desk-address-required.patch because it is core code).

## What v2 changes (against db54e13; v1 is NOT applied first, v2 contains it)
Files: scripts/terminal_guard.py (NEW), scripts/run_real_check.py, scripts/run_live_check.py, scripts/real-run.env.example, docs/settings.md, pyproject.toml (one word: the new file joins mypy `files`),
tests/conftest.py (fixture `a_terminal`), tests/test_start_prompt_hardening.py (rewritten, 129 tests), test_real_check_dry.py, test_ledger_amounts.py, test_live_claude.py (small).
`start-prompt-hardening-v1-to-v2.diff` is the change from v1 to v2 for review (not meant to be applied).
- Shared module `scripts/terminal_guard.py`: `stdin_is_terminal()` (isatty AND, on Windows, a real console; fails closed on any error), `ask_to_start(word, prompt)`
  (refuses without reading when stdin is not a terminal; True only if the person typed `word`; `y`, `yes`, `n`, empty are refused as the word itself).
  The two scripts keep v1's early refusal (exit 2, before anything starts) AND the question itself refuses again (defence in depth, tested).
- Minor 3 (AST guard): rewritten. Detects: `input`/`raw_input`/`breakpoint` as a bare name (calls, aliases `ask = input`, `partial(input)`), `builtins.input`, `from builtins import input`,
  `getpass` (import, from-import, alias), `fileinput`, `readline`, `cmd`, `code`, `pdb`, click, typer, prompt_toolkit, questionary, inquirer, pexpect, rich.prompt, `sys.stdin`/`sys.__stdin__` (any use except `.isatty`, also `from sys import stdin`,
  `import sys as s`, `.buffer.read`, `for l in sys.stdin`), `open(0)`, `io.open(0)`, `os.read/fdopen/dup(0)`, paths /dev/stdin /dev/tty CON CONIN$, `msvcrt.getch*`/`kbhit`, `getattr(x,"input")`, `__import__`/`import_module`/`eval`/`exec` (not checkable; only src/lead_desk/loader.py, fixed module names, is allowed),
  and a `read -x` inside a Python string. 34 snippets that must be found and 10 that must not (no wolf cries), all tested. Scope widened from 5 folders to every .py outside tests/ (root files, n8n, anything).
  Only scripts/terminal_guard.py may read a person; the callers must call `stdin_is_terminal` before `ask_to_start` (checked by line number in the AST, not by text `index()`), and `ask_to_start` checks before its own `input`.
  Shell scan: every .sh .ps1 .bat .cmd in the repo (`read`, `select`, /dev/tty, Read-Host, [Console]::ReadLine, $Host.UI.Prompt*, Get-Credential, pause, set /p); 14 positive and 4 negative snippets; today's shell scripts have none.
  Stated limits of the guard: a descriptor held in a variable (`os.read(fd, n)` with fd = 0 elsewhere), a name built at run time, and a `read` inside quotes in a shell file (`bash -c 'read x'`). It is a tripwire; the behaviour tests carry the guarantee.
- Minor 5 (Windows): see Failures 1. Tested with a stand-in probe (NUL-like stream whose isatty is True but console test False), a failing probe (OSError/ValueError/AttributeError), real /dev/null, a file, a pipe (False) and a real pty (True, skipped where `pty` is missing).
- Typed confirmation (reviewer's measure 1): IMPLEMENTED, it stayed small (about 25 lines in the scripts + the module) and `--dry-fakes`/`--assume-yes` keep their meaning (`--assume-yes` still skips the question, only with `--dry-fakes` / a loopback --base-url).
  The banner now prints one line per destination before the question: HubSpot key host, mail sending host, each mailbox host, model host (or "none (recorded replies)"); the live check prints "the key goes to: <host>".
  The question: `To start, type the HubSpot host (<host>) and press Enter; anything else stops:` (live check: the provider's host). `y`, `yes`, an empty line, a wrong or lookalike host all stop (exit 1). A blind `yes |` is refused before it by the terminal check; a pty script is not stopped (limit 2).
  This changes the UX: nobody types `y` any more. Docs updated.
- Nits: env.example (IMAP host no longer under Optional; DESK_LIVE_BASE_URL required with --live-model), settings.md exit-code bullet reordered, `--assume-yes` and `--base-url (required)` in the run_live_check flag list.
  Also: the mailbox host shape is checked (letters, digits, dots, hyphens; `<IMAP_HOST>` or a typo is refused before the question), and `imap_settings` no longer falls back to MAIL_IMAP_DEFAULT_HOST at all (host required), so the check script's last vendor default is gone.
  Reviewer's M10 survivor (substring loopback test) is now killed by a 9-lookalike table.

## Exit code decision: 2 for "standard input is not a terminal" (and for the model/no --base-url refusals). 1 stays for "you answered no / typed something else / the terminal closed under the question".
Reason: it is a refusal before anything starts, the same class as every other start refusal (exit 2); v4 documented 1.
What in v4 (and v5, and the studio) must change to match (all measured in the merged tree, see conflicts):
 - v4 docs/settings.md exit-code bullet (1 "...or there was no terminal to answer on") and run_live_check.py docstring "Exit codes ... 1 ... or there was no terminal": reworded in start-prompt-hardening-v2-on-top-of-v4.patch.
 - v4 tests/test_take_script_refusals.py::test_live_check_without_a_terminal_stops_with_one_line_not_a_traceback: asserted `returncode == 1` and "no terminal"; now `== 2` and "needs a person at a terminal" (with `assume_yes=False`).
 - run-dry-checks.sh (studio harness, outside the repo): `rrc-valid-eof` and `rrc-dry-fakes-no-assume` expect exit 1 'there is no terminal' with null stdin: now exit 2 'needs a person at a terminal'. And EVERY case that runs the real check with null stdin and expects a config refusal text
   (rrc-noargs, rrc-cfg-*, rrc-assume-*, ...) now gets the no-terminal refusal first (Failures 3): run them through a pty driver (see pty_ans-q4g.py in this folder, which answers only n or an empty line; lo_up-q4g.py and sitecustomize-q4g.py are the loopback-only namespace helper and the connect blocker) or with `--dry-fakes --assume-yes`. DRY-RUN-CHECKS.md D4 and the `rlc-eof-prompt` row need the same rewording. docs/real-services.md has no exit-code text (checked).
 - An EOF at the question on a real terminal (terminal closed) is still exit 1 (v4 test `test_no_terminal_to_answer_on_is_a_stop_not_a_traceback` unchanged).

## Conflicts with real-run-fixes-v4.patch (measured: v4 applied on db54e13, then `git apply --3way` v2)
Applies cleanly alone on db54e13 and on 2db3926 (evidence-q4g-apply-matrix-final.txt). On top of v4 it conflicts in: docs/settings.md, scripts/run_live_check.py (3 hunks), scripts/run_real_check.py (4 hunks: import line, exit constants, helper functions, the first refusals in `_run`), tests/conftest.py (both add a fixture), tests/test_live_claude.py (1 hunk).
I resolved them and ship the result as `start-prompt-hardening-v2-on-top-of-v4.patch` (apply it AFTER v4, instead of v2). Resolution: keep both blocks; in `_run` the order is: --assume-yes refusal, v4's --keep refusal, then the terminal check; import line `Config, LiveSettings, is_loopback_host, read_leadflow`;
settings.md: v4 text plus v2's edits; the live-runner test that failed all calls keeps v4's `returncode == 3`.
v4's tests/test_take_script_refusals.py: with the naive merge 49 of 66 failed (the reviewer's number, reproduced exactly). The exact fix (in the "-on-top-of-v4" patch, 66 of 66 pass):
 1. add to that file an autouse fixture `_a_person_at_a_terminal(a_terminal)` (the conftest fixture);
 2. `_live(...)`: add `--assume-yes` to the child command (a child has no terminal; `--base-url http://127.0.0.1:1` was already there) with a parameter `assume_yes=True`; the no-terminal test passes `assume_yes=False`;
 3. `_live_lines()`: add `"DESK_LIVE_BASE_URL": "http://127.0.0.1:1"`;
 4. never pipe `y`: `_live(.., "y\n")` became `_live(.., "")`; the one test that answered `n` to the child (`test_a_new_live_ledger_is_fine...`) now calls `run_live_check.main` in-process with the terminal stand-in and `input` mocked to `n`;
 5. the prompt text assertions: `asked == ["Start? [y/N] "]` -> startswith "To start, type the HubSpot host ("; every `"Start?" not in out` -> `"To start" not in out` (the old ones would be vacuously true).
 Also the one-line fix in v4's tests that the reviewer found: the key content of the patch's `_config` (done: my `_config` now writes a real one-line made-up key file for every *_KEY_FILE / *_PASSWORD_FILE).
Merged-tree evidence: evidence-q4g-merged-with-v4-tests.txt (447 passed: take refusals, start-prompt, real_check_dry, live_claude, ledger_amounts, clock_steps). Not run on the merged tree: the other test files.
For v5: rebase `start-prompt-hardening-v2-on-top-of-v4.patch` the same way; the hunks to watch are the first lines of `_run` and the question block in both scripts.
real-run-fixes-v4-after-sonar-p3.patch: not testable (needs sonar P3); expect the same files to conflict.

## Rung table (CODE-LAST) 
| component | need | rung tried | verdict |
|---|---|---|---|
| terminal test | stop a piped y | stdlib `isatty` (rung 1) | KEEP: isatty + Windows console test (GetConsoleMode is the stdlib-adjacent standard, ctypes) |
| typed host | stop a blind `yes \|` | none free (no library asks "type the host") | KEEP-CODE, 25 lines, a safety guarantee |
| AST guard | catch a new prompt | none free | KEEP as a tripwire in tests only |

## What was run (raw output in the evidence files)
- evidence-q4g-fail-before-v2.txt: the new test file against db54e13 scripts (plus the new module and fixture, otherwise it cannot even import): 52 failed, 77 passed (the 77 are guard-unit tests and rules that did not change).
- evidence-q4g-mutants-v2.txt: 23 mutants, 23 killed (terminal test always true / isatty only / probe ignored / probe fails open, ask takes y, ask reads a non-terminal, either early check removed, either start accepts any answer, early refusal exit 1, banner lines missing, mailbox shape unchecked, imap default restored, unnamed check off, loopback by substring, live no-base-url refusal off, three guard mutants, repo walk skipping scripts).
- evidence-q4g-tests-affected.txt: 752 passed (test_real_check_dry, ledger_amounts, live_claude, clock_steps, env_numbers, portal_wording_and_masking, start_prompt_hardening) under unshare -rn. NOT the whole suite.
- evidence-q4g-lint-mypy-bandit.txt: ruff check, format, mypy linux and win32 (27 files), bandit -ll: no issues. Venv /tmp/work/fresh-venv5 (Python 3.12, ruff 0.17.4, mypy 2.4.1; no uv `test` group in the repo).
- evidence-q4g-hygiene-gitleaks.txt: `git add -A`, gitleaks 8.30.1, DPLD_REQUIRE_SCAN=1: 59 passed (run outside unshare: git commits inside the hygiene test do not work in a user namespace; they open no network connection).
- evidence-q4g-harness.txt: the real scripts, under unshare -rn + blocker, synthetic loopback config: piped / /dev/null / closed stdin -> exit 2; pty with `n` and with an empty line -> banner with destinations, exit 1; live check piped -> 2, without --base-url -> 2, pty `n` -> 1; unnamed HubSpot address -> 2; placeholder mailbox host -> 2. Blocker log: 0 lines, 0 BLOCK.
- evidence-q4g-on-2db3926.txt: v2 + desk-address-required-after-v2 on 2db3926: 603 passed (start-prompt, address-required, crm_hubspot, env_numbers, live_claude).
Token use: not measured.
