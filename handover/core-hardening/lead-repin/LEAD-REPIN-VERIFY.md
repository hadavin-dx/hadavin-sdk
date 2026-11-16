# Lead re-pin checklist: the items the lead said it verifies itself

Written Mon 16 Nov 2026 (UTC; IST = UTC + 5:30) by a builder. Read this first: **nothing in this file was verified.** The take program is not in this checkout. I wrote commands against the file names the inputs quote, and every path is "adjust if different". I never saw the real output, so every "expected shape" below is a description of what a reader should look for, not a result. The script `lead-repin-verify.sh` was run once, only against a made-up folder (`raw-dummy-run.txt`), to show it prints blocks.

Sources read: ORDERS.md ("ANSWER (lead, 12:50Z): Q22 to Q31", ORDER 039), QUESTIONS.md Q23 and Q27, steps-edits/LEAD-RELEASE-NOTE-v4.md (gates G1 to G38), steps-edits/v20-OPEN-FOR-LEAD.md, inputs/AGENT-SCOPE-DO-AND-DONT.md, inputs/DECISIONS-2026-11-16.md. Words: "take program" = `run_real_check_n8n.py` and the files it uses; "model program" = the program that makes the paid model calls; "the sheet" = steps-edits/OWNER-SHEET-v20.md; "numbers message" = the lead's message to the owner (Release note section 3).

## How to use
In the take repo, at the final head: `sh lead-repin-verify.sh /path/to/take/repo` (optional environment: `MODEL_DIR`, `MODEL_SETTINGS`, `TAKE_PY`, `CRM_PY`, `FLOWS_DIR`, `END_RE`, `MODEL_RE`, `DELETE_RE`). It only reads, prints one block per item and ends with a one-line count. It copies its output to `/tmp/lead-repin-verify-out.txt` (override with `LEAD_REPIN_OUT`). It judges nothing: a block with zero hits can mean "not there" or "my search word was wrong", so look at `FILES_READ` and `FILES_MISSING` first, then adjust the word variables and re-run. Setting values whose name contains key, token, secret or password are masked in the output. The commands equivalent to each block are in the table so you can paste them one by one.

## Failures first (what this checklist cannot do)
1. A search finds text, it does not prove behaviour. "No delete call found" needs the second reader (G1). "Refusal exists" needs the refusal SHOWN (a test run or startup output), not only a grep hit.
2. Q27 (a) is about run order. A grep shows line numbers only; read the code around them. Line order is not always execution order.
3. The default search words (`call_model`, `anthropic`, `marker` and so on) are my guesses, not the real names. If a block shows zero hits, change the word first.
4. `ss` was not available in the builder's shell, so the ports block was not exercised (it printed the "ss not found" line). Check it on the laptop.
5. Not coverable by a read-only command, so not in the script: G2 (flow checksum after import), G3 (what n8n holds), G5, G8, G9, G11 to G15, G19, G21 permission names (read them in the HubSpot page), G22 to G25, G27 to G32. They are in the release note unchanged.

## Items

### Q23: does the take program have any delete or archive path to the CRM (G1, G21, G17)
- **Question:** does any python file of the take program, the CRM module or any flow node send a delete or archive call to the CRM? The old reading (AGENT-SCOPE line 20) says yes at `run_real_check_n8n.py:1051` and `crm_hubspot.py:504-509`; the r17 review found only a `rows_with_prefix` GET.
- **Answer needed:** yes / no, plus the line numbers of every hit, plus a second reader named (G1).
- **Blocks:** Q23-1 (delete/archive census over the take's python files and flow json), Q23-2 (what stands at the old line numbers today), Q23-3 (HTTP methods in the CRM module), Q23-4 (delete wording the owner would read), R00 (commit id and checksums).
- **Paste by hand (adjust paths):**
  - `git rev-parse HEAD; git status --porcelain | wc -l`
  - `grep -n -i -E 'DELETE|\.delete\(|archive|requests\.delete' run_real_check_n8n.py crm_hubspot.py n8n_drive.py n8n.py`
  - `grep -rn -i -E 'DELETE|archive' --include='*.json' <flows folder>`
  - `sed -n '1045,1056p' run_real_check_n8n.py; sed -n '500,512p' crm_hubspot.py`
  - `grep -n -E 'GET|POST|PUT|PATCH|DELETE|rows_with_prefix' crm_hubspot.py`
  - `grep -n -i -E 'delete|archiv' run_real_check_n8n.py`
  - `sha256sum run_real_check_n8n.py crm_hubspot.py n8n_drive.py n8n.py`
- **Expected shape:** Q23-1 either prints only comment, test or word-in-text lines, or prints a real call line. Q23-2: "file is shorter than line N" means the old number is stale; code there means read it. Q23-3: a list of GET and POST names, and `rows_with_prefix` as a GET.
- **What each outcome means:**
  - No call anywhere, second reader agrees: G1 can be YES; the clean-up message may carry "the take program made no delete call" (sheet line about the clean-up message, R7; Release note G27); AGENT-SCOPE line 20 stays marked stale text.
  - A delete or archive call exists: decision 2 is false at this head. Then (owner or lead decides, not me): the sentence "the take program made no delete call" is removed, the Release note ban-list item 10 applies, the HubSpot key question G21 reopens (AGENT-SCOPE F-01: a read-only key fails at the archive after the sends), and the sheet's R7 owner deletes stay but the "never deletes" claim is not posted.
  - Delete wording still printed (Q23-4): G17 fails; the sheet's R5 sends `n`, and the notice wording copied into the numbers message must change.
  - Default if not shown: G1 stays NO, no run (v20-OPEN item 1); HubSpot key not widened.

### Q27 (a): the take program never calls the model after the word `end` (G34)
- **Answer needed:** yes / no with line numbers; if "can still call", what it prints and which exit code it leaves when the owner cancels the key right after `end`.
- **Block:** Q27a (lines handling `end` with 20 lines after, then every model-call line).
- **Paste by hand:** `grep -n -E "[\"']end[\"']" run_real_check_n8n.py` then `grep -n -E '<your model-call names>' run_real_check_n8n.py`; then `sed -n 'A,Bp'` around the `end` branch to the end of `main`.
- **Expected shape:** the `end` line number, and model-call line numbers; yes holds only if no model-call line can run after the `end` branch.
- **Outcome:** shown "never": the numbers message says so with file and line plus a test; the sheet's 7.7 error sentence may then be reviewed. Not shown: default unchanged, the numbers message says "exit code accepted then: none" (any other code is a FREEZE) and the 7.7 sentence stays. Also fill G18's early-cancel line from the same read.

### Q27 (b): an end-date refusal exists and is shown at the final head (G16, G10)
- **Answer needed:** yes / no with file and line; and the refusal SHOWN (test `qs_37` or the startup refusal run at the final head). Also `need_seconds` (G10) from the take program.
- **Block:** Q27b (window-end words in the take program and model program, `qs_37` search, names of window-like settings, values hidden).
- **Paste by hand:** `grep -n -i -E 'window|end_date|not_after|deadline|need_seconds|2026-11-2|refus' run_real_check_n8n.py <model program files>`; `grep -rn qs_37 --include='*.py' .`; then run the named test or start the model program with a past window end and copy the printed refusal.
- **Expected shape:** a setting name and a comparison line; a test name. A grep hit alone is "exists", not "shown".
- **Outcome:** shown: numbers message line "End-date refusal: shown"; a run on Mon 23 Nov becomes possible (G10, Q25). Not shown: line "End-date refusal: NOT SHOWN", **no run on Mon 23 Nov**, target Wed 18 Nov stays (sheet line 44 already carries "NOT SHOWN"). Default: "NOT SHOWN".

### Q27 (c): the go marker before any model call (G33)
- **Answer needed:** yes / no with file and line in both programs, plus a test at the final head.
- **Block:** Q27c (marker words in the take program, then the model program).
- **Paste by hand:** `grep -n -i -E 'marker|\.used|go_file|accepted|challenge' run_real_check_n8n.py`; `grep -n -i -E 'marker|exists\(|isfile' <model program files>`.
- **Expected shape:** the take program writes a marker after the accepted challenge; the model program tests for it before the first paid call. Both halves are needed. Note `~/.hadavin-take-tags/<id>.used` in AGENT-SCOPE is the single-use tag marker made before the first post; it is not shown to be the same as the go marker, so do not treat it as one without reading the model program.
- **Outcome:** shown: numbers message "Go marker: shown". Not shown: "Go marker: NOT SHOWN", the sheet's fallback wording (R4 and 8.1) applies and the yes names it; no line at all means no run. Default: NOT SHOWN.

### Other gates the sheet leaves open and a read can help with
| Id | Question | Block | Answer needed | If not shown (default) |
|---|---|---|---|---|
| G35 | Does the take program ask the owner to type anything besides `y`, the challenge line and `end` (AGENT-SCOPE line 22 mentions a typed worst-case figure)? | G35 | file and line of every prompt; line "Take program asks you to type a figure: no" | unknown: no run until the sheet is changed |
| G6 | Exit codes, and the one for person C "unknown" | G06 | codes with file and line | default `none`: only 0 accepted |
| G4, G14 | Call ceiling, retries, ledger, program limit | G04 | file and line; "informational only" if not measured | the run total is not called a limit |
| G18 | Wrong line after `end`, Ctrl-C, pause ending without `end`, lock file | G18 | file and line | unknown; the sheet treats both as called-off runs |
| G36 | Line that starts the film pause; minimum think time; silence and give-up minutes | G36 | copied line or offsets from the rehearsal | no cue named: no run |
| G37, G38 | Per-run key file refuses an existing file; subject start of the take mails; prep contact not matching the film search | G37-38 | statement, copied subject start | statement missing: no run |
| G7 | Ports 5678, 5679 (owner's), 5690 to 5693 (rehearsal), take port (proposal 5701, 5702) | G07 | `ss` output showing the take's ports free | a collision: change port |
| G20 | DECISION-one-store line 14 still says ONE database | G20 | the edited line | still ONE: edit it |

## What I did not check
The real take program, flows and model program (none present); real output of any block; whether the default search words match the real names; the `ss` branch; the owner sheet sentences beyond the lines quoted from the release note and the sheet lines found by grep (sheet section numbers are as the release note gives them); the Q20.4 and Q21.4 items (exit code and retake count are in the G6 block only).
