# Lead re-pin checklist (version 2): the items the lead said it verifies itself

Written Mon 16 Nov 2026 (UTC; IST = UTC + 5:30) by a builder. Read this first: **nothing in this file was verified against the real take program.** The take program is not in this checkout. I wrote the commands against the file names the inputs quote. I never saw real output. Every "expected shape" below says what a reader should look for; it is not a result.

Rules that bind this file (ORDERS.md, lead answers of 12:50Z):
- **Q23:** decision 2 stays: the take never deletes. The r17 review found no delete or archive path in `run_real_check_n8n.py` (only a `rows_with_prefix` GET). The line 1051 reading is UNVERIFIED stale text. The lead shows the final-head grep at re-pin. The HubSpot key is not widened.
- **Q25 and Q27:** the target take is Wed 18 Nov. **There is no take on Mon 23 Nov unless Q27 a, b and c are ALL shown at the final head.** Showing two of the three is not enough. Q27 a, b and c stay **UNVERIFIED** until the lead shows them; until then the text says "lead verifies at re-pin" and the defaults below apply.

## Words used in this file
- **take** and **take program**: the real run with the paid model and the CRM, and the program `run_real_check_n8n.py` that drives it. **model program**: the program that makes the paid model calls (its folder is not in this checkout).
- **head**: the newest saved version (commit) of a folder in git. **final head**: the version the real take will run from; every answer here must say which one it is about (block R00 prints it).
- **second reader**: a second person or agent who reads the same code on their own and also answers; G1 asks for one so one reader's line numbers are not trusted alone.
- **G1 to G38**: numbered checks in `steps-edits/LEAD-RELEASE-NOTE-v4.md` (the release note). **Q23, Q27**: numbered questions in QUESTIONS.md. **R3 to R10**: numbered rules on the owner sheet (`steps-edits/OWNER-SHEET-v20.md`). **ban-list item 10**: item 10 of the release note's list of sentences that must not be sent unless shown.
- **the sheet**: the owner sheet. **numbers message**: the lead's message to the owner with the final figures (release note section 3).
- **FREEZE**: as the owner-sheet reviews use it, the state where the owner stops and waits for the lead. I did not find the full definition in the files I read; the lead confirms the meaning.
- **need_seconds**: a number named in G10 (how many seconds a step needs before the window end); I did not see its definition in the files I read.
- **files_read** in the script output: how many files that search really opened. A search that opened 0 files looked at nothing.
- **UNVERIFIED**: written from a source, not seen working. **masked**: a value replaced by `<masked>` because its name looked like a key, token, secret or password.

## What the script does to the machine (exact)
`sh lead-repin-verify.sh [TAKE_DIR]` (TAKE_DIR defaults to the current folder).
- It reads files (grep, sed, awk, wc, find, sha256sum), reads git (`rev-parse`, `log`, `status`, all run with `--no-optional-locks` and the file-system monitor switched off, so git does not rewrite its index; I checked the `.git` folder before and after one run: identical names, times, sizes and index checksum), and reads the list of listening ports.
- It writes **only** into one private work folder made by `mktemp` (folder mode 700, files mode 600). The folder holds a copy of the output (`lead-repin-verify-out.txt`) and small helper files. Its path is printed at the top and bottom of the output. The script deletes nothing, not even that folder; you may delete it yourself.
- It makes no network call and no model call, and starts no program of the take.
- It judges nothing.
- **Masking is a safety net, not a guarantee.** The lead reads the output before sharing it with anyone.

Other modes: `sh lead-repin-verify.sh --self-test` tests the masking with made-up secrets built from parts and prints PASS or FAIL for each. `<command> | sh lead-repin-verify.sh --mask` passes any text through the same masking.

Settings (environment variables, all optional): `TAKE_PY CRM_PY DRIVE_PY N8N_PY` (when not set, the script finds each file by name up to 4 folders below TAKE_DIR, prefers a `scripts/` folder, and prints which file it used and any other file with the same name), `FLOWS_DIR`, `MODEL_DIR`, `MODEL_SETTINGS`, `ONE_STORE`, and the search words `END_RE`, `MODEL_RE`, `DELETE_RE`. Folders left out on purpose: `.git node_modules _local secrets .venv venv __pycache__ tests test`, and files `test_*`, `*_test.py`, `conftest.py`; this applies only below TAKE_DIR, so a take folder inside a parent called `test_runs` is still searched. The script prints how many files each list holds and says `0 FILES SEARCHED` loudly when a list is empty.

## Failures first (what this checklist cannot do)
1. A search finds text; it does not prove behaviour. "No delete call found" needs a second reader (G1). "Refusal exists" needs the refusal SHOWN (a test run or the startup refusal), not only a grep hit.
2. Q27 a is about run order. A grep prints line numbers; read the code around them. Line order is not always run order. A call already sent before `end`, and an n8n retry or lease that fires a call after `end`, cannot be shown by reading the program: they need a run or a test shown at the final head.
3. The default search words are my guesses. Zero hits can mean "not there" or "wrong words". Every search prints its own line `matching lines / files_read / missing / unreadable`, and `ZERO HITS`, `ZERO FILES SEARCHED` or `UNREADABLE` when it applies. The block total line is a sum of several searches; read the per-search lines, not the total.
4. An unreadable file is printed as `UNREADABLE (not searched, NOT zero matches)`. I saw that branch work only as an ordinary user (uid 65534); as root every file is readable.
5. Not covered by a read-only command, so not in the script: G2 (flow checksum after import), G3 (what n8n holds), G5, G8, G9, G11 to G15, G19, G21 permission names, G22 to G25, G27 to G32. They stay in the release note unchanged.
6. The hand-typed commands in the table below are not the script: they have no line cutting and fewer search words. They are piped through `--mask` so a secret cannot print, but run the script when you can.
7. Windows listeners are not seen from WSL (the script says so when it detects WSL; check `netstat -ano` on Windows for 5678 and 5679).

## Items

### Q23: does the take program have any delete or archive path to the CRM (G1, G21, G17)
- **Question:** does any python or shell file of the take (not tests), the CRM module or any flow json contain a delete, archive, purge, remove, trash or cleanup call to the CRM? The old reading (AGENT-SCOPE line 20) said yes at `run_real_check_n8n.py:1051` and `crm_hubspot.py:504-509`; the lead calls that UNVERIFIED stale text; the r17 review found only a `rows_with_prefix` GET.
- **Answer needed:** yes or no, plus the line number of every hit, plus a named second reader (G1).
- **Blocks:** Q23-1 (census), Q23-2 (what stands at the old line numbers), Q23-3 (HTTP methods in the CRM module, case-sensitive), Q23-4 (delete wording the owner would read), R00 (commit id and checksums).
- **Paste by hand (adjust paths; keep the quotes, paths may hold spaces):**
  - `git --no-optional-locks rev-parse HEAD; git --no-optional-locks status --porcelain | wc -l`
  - `grep -n -i -E 'DELETE|\.delete\(|archive|purge|remove|trash|gdpr|cleanup|unlink|rmtree' "scripts/run_real_check_n8n.py" "scripts/crm_hubspot.py" "scripts/n8n_drive.py" "scripts/n8n.py" | sh lead-repin-verify.sh --mask`
  - `grep -rn -i -E 'DELETE|archive|purge|remove|trash' --include='*.json' --exclude-dir=node_modules --exclude-dir=_local --exclude-dir=secrets "<flows folder>" | sh lead-repin-verify.sh --mask`
  - `sed -n '1045,1056p' "scripts/run_real_check_n8n.py" | sh lead-repin-verify.sh --mask`
  - `grep -n -E '(^|[^A-Za-z_])(GET|POST|PUT|PATCH|DELETE)([^A-Za-z_]|$)|rows_with_prefix' "scripts/crm_hubspot.py"`
  - `sha256sum "scripts/run_real_check_n8n.py" "scripts/crm_hubspot.py" "scripts/n8n_drive.py" "scripts/n8n.py"`
- **Expected shape:** Q23-1 prints either only comment, test or wording lines, or a real call line. Q23-2: "file is shorter than line N" means the old number is stale. Q23-3: GET and POST names, and `rows_with_prefix` as a GET.
- **What each outcome means (ORDERS Q23 governs):**
  - No call anywhere and a second reader agrees: G1 can be YES; decision 2 stands; the clean-up message may say "the take program made no delete call" (release note G27); AGENT-SCOPE line 20 stays marked stale.
  - A delete or archive call exists: decision 2 is false at this head. The lead (or the owner) decides what follows; I do not. The sentence "the take program made no delete call" is not sent, ban-list item 10 applies, and the HubSpot key question G21 reopens. The key is still not widened without the owner.
  - Delete wording still printed (Q23-4): G17 fails; the sheet's R5 sends `n`; the notice wording in the numbers message must change.
  - Default if not shown: G1 stays NO and no run (v20-OPEN item 1); the HubSpot key is not widened.

### Q27 a: the take program never calls the model after the word `end` (G34). UNVERIFIED until the lead shows it.
- **Answer needed:** yes or no with line numbers. If a call can still follow, also what is printed and which exit code is left when the owner cancels the key right after `end`.
- **Block:** Q27a: part 1 lines handling `end` (case-sensitive, quoted word or a constant; with 20 lines after each); part 2 every model-call line, in the take program, `n8n_drive.py`, `n8n.py` and (if MODEL_DIR is set) the model program. The default model words include the real call route (`post_lead`, `burst`, `/qualify`, `/control`, `n8n_drive`, loopback calls), but they are still guesses.
- **Paste by hand:** `grep -n -E "[\"']end[\"']" "scripts/run_real_check_n8n.py"`, then `grep -n -E '<your model-call words>' ...`, then `sed -n 'A,Bp'` around the `end` branch to the end of `main`; pipe each through `sh lead-repin-verify.sh --mask`.
- **Expected shape:** the `end` line number and the model-call line numbers. "Never" holds only if no model-call line can run after the `end` branch AND a run or test at the final head shows no n8n retry or lease fires one.
- **Outcome:** shown "never": the numbers message says so with file, line and the test; the sheet's 7.7 error sentence may then be reviewed. Not shown: the default stays: the numbers message says "exit code accepted then: none" (any other code is a FREEZE) and the 7.7 sentence stays. Fill G18's early-cancel line from the same read.

### Q27 b: an end-date refusal exists and is SHOWN at the final head (G16, G10). UNVERIFIED until the lead shows it.
- **Answer needed:** yes or no with file and line, and the refusal SHOWN (the `qs_37` test, or the startup refusal, run at the final head). Also `need_seconds` (G10) from the take program.
- **Block:** Q27b: window-end words in the take program and (if MODEL_DIR is set) the model program; `qs_37` under TAKE_DIR and MODEL_DIR (if MODEL_DIR is not set the script says the model side was NOT SEARCHED; that is not "absent"); names of window-like settings, values never printed.
- **Paste by hand:** `grep -n -i -E 'window|end_date|not_after|deadline|need_seconds|2026-11-2|refus' "scripts/run_real_check_n8n.py"`; `grep -rn qs_37 --include='*.py' .`; then run the named test or start the model program with a past window end and copy the printed refusal (through `--mask`).
- **Expected shape:** a setting name and a comparison line; a test name. A grep hit alone is "exists", not "shown".
- **Outcome:** shown: the numbers message line reads "End-date refusal: shown". Not shown (the default): "End-date refusal: NOT SHOWN" and the take stays on Wed 18 Nov (sheet line 44 already carries "NOT SHOWN"). Showing (b) alone never makes Mon 23 Nov possible: Q27 a, b and c must all be shown at the final head.

### Q27 c: the go marker before any model call (G33). UNVERIFIED until the lead shows it.
- **Answer needed:** yes or no with file and line in BOTH programs, plus a test at the final head.
- **Block:** Q27c: half A (marker words in the take program) and half B (marker words in the model program folder). The block prints both hit counts on one line; a zero in either half means NOT SHOWN by that search.
- **Paste by hand:** `grep -n -i -E 'marker|\.used|go_file|accepted|challenge' "scripts/run_real_check_n8n.py"`; `grep -n -i -E 'marker|exists\(|isfile' <model program files>`.
- **Expected shape:** the take program writes a marker after the accepted challenge; the model program tests for it before the first paid call. `~/.hadavin-take-tags/<id>.used` (AGENT-SCOPE) is the single-use tag marker made before the first post; it is not shown to be the same as the go marker.
- **Outcome:** shown: "Go marker: shown". Not shown (the default): "Go marker: NOT SHOWN", the sheet's fallback wording (R4 and 8.1) applies and the yes names it; no marker line at all means no run.

### Other gates the sheet leaves open, where a read can help
| Id | Question | Block | Answer needed | If not shown (default) |
|---|---|---|---|---|
| G35 | Does the take program ask the owner to type anything besides `y`, the challenge line and `end` (AGENT-SCOPE line 22 mentions a typed worst-case figure)? | G35 | file and line of every prompt; "Take program asks you to type a figure: no" | unknown: no run until the sheet is changed |
| G6 | Exit codes, and the one for person C "unknown" | G06 | codes with file and line | default `none`: only 0 accepted |
| G4, G14 | Call ceiling, retries, ledger, program limit | G04 | file and line; "informational only" if not measured | the run total is not called a limit |
| G18 | Wrong line after `end`, Ctrl-C, pause ending without `end`, lock file | G18 | file and line | unknown; the sheet treats both as called-off runs |
| G36 | Line that starts the film pause; minimum think time; silence and give-up minutes | G36 | copied line or offsets from the rehearsal | no cue named: no run |
| G37, G38 | Per-run key file refuses an existing file; start of the take mail subjects; prep contact not matching the film search | G37-38 | statement, copied subject start | statement missing: no run |
| G7 | Ports 5678, 5679 (owner's), 5690 to 5693 (rehearsal), take port (proposal 5701, 5702) | G07 | listing showing the take's ports free | a collision: change the port |
| G20 | DECISION-one-store line 14 still says ONE database | G20 | the edited line | still ONE: edit it |

## What I did not check
The real take program, flows and model program (none present); real output of any block; whether the default search words match the real names; the owner-sheet sentences beyond the lines quoted from the release note (sheet section numbers are as the release note gives them); the Q20.4 and Q21.4 items (exit code and retake count are in the G6 block only); macOS and Windows shells (only dash and bash on Linux); WSL (the detection line is untested); the definitions marked above as not found.
