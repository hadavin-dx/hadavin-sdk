# CONFLICTS (tree-COMBINE, baseline = tree-EV, committed locally in the copy as 9f5dc1f)

Order actually applied: F1, F3, F1b, F2, F2b, F6. (The brief said F1, F1b, F3. F1b does NOT apply before F3: it extends
src/lead_desk/regfile.py, which F3 creates. After F3 it applies with `git apply` and no conflict.)

Clean: F1 on baseline; F3 on F1; F1b on F1+F3. F2b marker applies with `git apply -p1`.

## 1. scripts/feed.py  (F1 + F1b vs F2)  -- hand merged
F1 split main() into run() + one error-to-refusal main(), with argparse.ArgumentParser; F2 swapped argparse for
RefusingParser and removed `import argparse`. Resolution: F1's structure kept, `ap = RefusingParser(...)` (F2), F2's
sys.path line for tools/ kept, `import argparse` dropped (no other use), `import http.client` kept (F1).
Result is still one parse path: a bad command line ends in RefusingParser.error (exit 2, fixed line), the rest in F1's main().

## 2. scripts/refusals.py (F1) vs tools/refusing_args.py (F2)  -- one source of truth
Both defined `refusal()` and EXIT_REFUSED. Resolution: tools/refusing_args.py is the single definition and gained
EXIT_UNREACHABLE = 3; scripts/refusals.py is now only a re-export (with the repo folder put on sys.path) so F1's
import name `from refusals import ...` and its test keep working. No duplicate text left.

## 3. src/lead_desk/live_claude.py  (F3/F1b regfile reader vs F2 size limit vs F6 output opener)
- _read_key: F3 uses open_regular(); F2 added a bounded read (SECRET_FILE_MAX_BYTES + 1, "too large" refusal).
  Resolution: both: `with open_regular(...) as f: raw = f.read(SECRET_FILE_MAX_BYTES + 1)`, then the F2 size check, then decode.
- Imports: `from lead_desk.regfile import open_output, open_regular` (F6 added open_output, F3 open_regular).
- F6's open_output for the ledger and its lock applied cleanly.

## 4. src/lead_desk/regfile.py  (F1b reader functions vs F6 open_output)
Both extended the F3 module at the same place. Resolution: keep both. Imports `errno` (F6) and `json` (F1b); F1b's
FileRefused / read_regular_* / load_json_file block, then F6's _OUTPUT_MODES / open_output. No function duplicated.

## 5. demo_only/fake_model_server.py  (F2 vs F6)
F2: RefusingParser import. F6: removed argparse, imports open_output/open_regular. Resolution: both imports, sorted
(ruff isort clean).

## 6. Clean 3-way merges in files several patches touch
scripts/run_real_check.py (F1b, F2), scripts/n8n_api.py (F1b, F2), scripts/run_live_check.py (F2, F2b),
src/lead_desk/smtp_provider.py (F1, F2, F3), src/lead_desk/crm_hubspot.py (F2, F3), src/lead_desk/constants.py,
tools/scrub_n8n_export.py (F1, F1b), src/lead_desk/trace.py (F3, F6): no textual conflict.

## 7. F2b marker line too long
The F2b comment makes scripts/run_live_check.py:192 140 characters (ruff E501, limit 120; and ruff format would
re-wrap it). Resolution: comment shortened to `# wall-clock: a calendar day; one day of slack` (still starts with the
`# wall-clock:` marker the guard in tests/test_clock_steps.py looks for).

## 8. Hygiene fix (asked for in the brief) -- tests only
tests/test_special_files_and_plain_text.py (F3): literal web addresses now built from HTTP = "http" + "://" and
HTTPS = "https" + "://". Also found: tests/test_file_reader_refusals.py (F1b) line 136, where "try:\n" and
"except OSError:\n" inside a string matched the Windows-path pattern `y:\n` / `r:\n`; the string is now built from
parts ("try:" + ... ). Meaning of both tests unchanged.

## Not a conflict but to watch
F2's note says tests/test_n8n_api_url.py:651 needs "RecursionError"; F1b changed that expectation to "FileRefused".
The combined test result below shows which one holds.

## 9. Test-expectation conflict found by running (F1b vs F2)
tests/test_cli_refusals.py:327 (F2) pinned `cannot read a workflow from the FILE given (JSONDecodeError)`; with F1b's
shared reader the same input now ends `(FileRefused)` (F1b made the same change to tests/test_n8n_api_url.py:651).
Expectation changed to FileRefused; behaviour (one clean line, no typed name, no traceback) is the same. Not weakened.
