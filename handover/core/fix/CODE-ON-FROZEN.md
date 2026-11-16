# CODE-ON-FROZEN (report only, nothing resolved)

Command: `git apply --check /home/user/build/rr6/out/COMBINE/core-fix-v1.patch` on a fresh copy of the frozen tree (tree a019c448...): **exit 1, it does NOT apply**. 33 error lines; git refuses the whole patch (all or nothing).
Probe (a second scratch copy, thrown away): `git apply --reject` to count hunks: the patch has 120 hunks in 48 files; 30 hunks are rejected in 15 files; 3 files named by the patch do not exist in the frozen tree.

## Files the patch edits that the frozen tree does not have
- `scripts/precheck.py`, `tests/test_core_key_readers.py`, `tests/test_survivor_r20_config_read.py` (probably from the real-run patches that are not in demo main f3c39cf8 + 18 commits; I did not check where they come from)

## Rejected hunks (file: hunk headers of the .rej files; the context lines no longer match the frozen wording; I did not judge each one)

- `README.md`: 1 hunk(s): @@ -87,7 +87,7 @@ If PowerShell refuses to run the scripts at all (a policy set by your organisati
- `demo_only/fake_model_server.py`: 2 hunk(s): @@ -19,15 +19,18 @@ and counts in `auth_failures`; the key itself is never stored or printed."""; @@ -239,14 +242,24 @@ def make_model_server(
- `src/lead_desk/constants.py`: 1 hunk(s): @@ -170,6 +170,9 @@ MAIL_SPAM_FOLDER: Final = "[Gmail]/Spam"  # the provider's English spam folder n
- `src/lead_desk/crm_hubspot.py`: 1 hunk(s): @@ -93,7 +95,6 @@ BACKOFF_FIRST_SECONDS: Final = 0.5  # used when a 429 names no Retry-After
- `src/lead_desk/desk.py`: 1 hunk(s): @@ -315,10 +320,16 @@ def book_problem(db_path: Path | str) -> str | None:
- `src/lead_desk/live_claude.py`: 1 hunk(s): @@ -421,7 +423,11 @@ class LiveQualifier:
- `load_tools/catcher.py`: 1 hunk(s): @@ -39,6 +39,8 @@ except ModuleNotFoundError:
- `load_tools/check_invariants.py`: 1 hunk(s): @@ -23,6 +23,8 @@ except ModuleNotFoundError:
- `load_tools/load_driver.py`: 1 hunk(s): @@ -31,6 +30,8 @@ except ModuleNotFoundError:
- `scripts/n8n_api.py`: 2 hunk(s): @@ -46,6 +46,7 @@ from http_guard import open_http  # noqa: E402; @@ -191,12 +192,12 @@ def main(a: list[str]) -> int:
- `scripts/reset_check.py`: 1 hunk(s): @@ -1,6 +1,7 @@
- `scripts/run_live_check.py`: 7 hunk(s): @@ -30,9 +30,9 @@ import statistics; @@ -40,14 +40,17 @@ from terminal_guard import NoTerminal, ask_to_start, stdin_is_terminal; @@ -62,6 +65,8 @@ NO_TERMINAL_TEXT = (; @@ -105,13 +110,6 @@ PHRASE_OF = {; @@ -131,33 +129,6 @@ def setting_refusal(text: str) -> str:; @@ -208,6 +179,47 @@ def _loopback_url(url: str) -> bool:; @@ -226,24 +238,8 @@ def main(argv: list[str] | None = None) -> int:
- `scripts/run_real_check.py`: 7 hunk(s): @@ -71,7 +71,7 @@ for _p in (str(REPO / "src"), str(REPO)):; @@ -103,6 +103,7 @@ from lead_desk.imap_count import (  # noqa: E402; @@ -111,8 +112,10 @@ from lead_desk.smtp_provider import (  # noqa: E402; @@ -745,9 +748,9 @@ def load_env(path: Path) -> dict[str, str]:; @@ -1098,7 +1101,32 @@ def main(argv: list[str] | None = None) -> int:; @@ -1122,7 +1150,7 @@ def _run(a: argparse.Namespace, stack: contextlib.ExitStack) -> int:; @@ -1164,6 +1192,10 @@ def _run(a: argparse.Namespace, stack: contextlib.ExitStack) -> int:
- `scripts/start_all.ps1`: 1 hunk(s): @@ -7,8 +7,14 @@ $ErrorActionPreference = 'Stop'
- `tools/scrub_n8n_export.py`: 2 hunk(s): @@ -49,11 +49,13 @@ import sys; @@ -193,8 +195,27 @@ def main(argv: list[str]) -> int:

## Why (a reading, not a proof)
The frozen series (18 commits) edited comments, docstrings and messages in the same files (git diff --stat f3c39cf..HEAD lists 23 code files: constants.py, crm_hubspot.py, desk.py, live_claude.py, gate.py, loader.py, trace.py, db.py, run_stats.py, imap_count.py, load_tools/*, scripts/*). Hunks of ours that sit next to those lines lose their context. Whether a rejected hunk is still needed (the bug may be fixed, or the line gone) is for the lead to decide; not resolved here as ordered.
Hunks that applied cleanly are not listed; I did not run any test on a partly applied tree.
