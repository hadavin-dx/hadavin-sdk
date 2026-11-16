# Lead re-pin checklist (guide version 5, script version 5): the items the lead said it verifies itself

Written Mon 16 Nov 2026 (times in UTC; IST = UTC + 5:30 hours, so 14:00 UTC is 19:30 IST; run `date -u` to see the UTC time now) by a builder. Read this first: **nothing in this file or in the script was verified against the real test program.** The test program is not in this checkout. I wrote the commands against the file names the inputs quote and tested the script only on a made-up folder. Every "expected shape" below says what a reader should look for; it is not a result.

Versions used in this file: this guide v5, the script v5 (`lead-repin-verify.sh`), the release note v8 (`../steps-edits/LEAD-RELEASE-NOTE-v8.md`) and the owner sheet v24-A (`../steps-edits/OWNER-SHEET-v24-A.md`). A newer release note (v9) and owner sheet (v25-A) exist in `../steps-edits/`; I did not re-check the numbers below against them (see "What I did not check").

## Quick start (3 steps)
1. **Open a terminal in the test program's folder** (the text window where you type commands), then type: `sh /path/to/lead-repin-verify.sh --self-test`. Wait for the last line. It must read `SELF-TEST: passed=1022 failed=0`. Any other last line: **stop**, nothing below is safe to run, tell the lead.
2. **Run the checklist and keep the output in a file:** `sh /path/to/lead-repin-verify.sh > /tmp/lead-repin-out.txt; echo "exit code: $?"`. The script reads files and prints; it deletes nothing of yours and starts no program of the test. Look at the exit code (the table below says what each number means). At the end of the file read the `RUN-CHECK` lines: any `STOP-SIGNAL` line means "fix, or ask the lead".
3. **Read every block yourself.** The script judges nothing. Then send the answers to the lead only (not to a chat, not into a pull request), and read the masked output once before you share it (see "Masking is a safety net").

## What the output means: continue or stop
| What you see | Meaning | Continue or stop | Who decides | Next action |
|---|---|---|---|---|
| Exit code `0` and `RUN-CHECK: no stop signal` | The run reached its end. It does **not** mean the answers are good. | Continue | You read; the lead decides each answer | Read every block, fill the answers |
| Exit code `0` and one or more `STOP-SIGNAL` lines | The run itself could not look at something (missing file, unreadable file, zero files searched, missing lines, hidden search word) | Stop for the named search | You, then the lead | Fix the path or permission and run again, or tell the lead; do not use the zero counts named |
| Exit code `2` | Setup problem: no work folder could be made, or the test program folder was not found | Stop | You | Check the folder path and that `TMPDIR` (or `/tmp`) is writable; run again |
| Exit code `3` | The masking filter is unusable or failed its own canary test; **no file of the test program was opened** | Stop | The lead | Run `--self-test`, send its output to the lead. Common cause: a sed that is not GNU sed (check with `sed --version`) |
| Exit code `4` | The output pipeline failed (for example the reader closed with `| head`); partial output kept in the work folder | Stop | You | Run again without `| head`; then delete the work folder (see below) |
| Exit code `129`, `130`, `131`, `141`, `143` | The run was ended by hang-up (129), Ctrl-C (130), quit (131), closed pipe (141) or kill (143) | Stop | You | Run again. The script removed its work folder itself |
| `--self-test` exit code `0` | Every check passed | Continue | You | Go to step 2 |
| `--self-test` exit code `1`, or any line starting `FAIL` | At least one check failed | Stop | The lead | Send the output to the lead |
| Line `STOP:` printed by the script | The script refused to print | Stop | The lead | Send the line to the lead |
| `ZERO HITS` on one search | Either not there or the search words are wrong | Continue, but not proof | The lead | Read the left-out counts; try the hand command |
| `ZERO FILES SEARCHED` | The search looked at nothing | Stop for that search | You | Fix the folder path; a `0 matching lines` there means nothing |
| `UNREADABLE (not searched, NOT zero matches)` | A file could not be opened | Stop for that file | You | Fix the permission or tell the lead |
| `PRINT MISMATCH` | Fewer lines printed than grep counted | Stop for that search | You | Open the file at the line numbers yourself |
| `MATCH WORD HIDDEN` | The filter hid the searched word itself on a line | Continue after you open the file lines printed | You | Open those lines in the file yourself |
| A secret-looking value on the screen (not `<masked>`) | The filter missed it | Stop; do not share the output | The lead | Tell the lead the file and line (not the value); delete the output file |

**When a real run prints something the made-up folder never did** (a new kind of line, a different file layout): do not guess. Keep the output file, tell the lead the line number and what looks different, and wait.

**Delete the work folder when you finish.** A normal run keeps one folder named `lead-repin.XXXXXX` under `$TMPDIR` (or `/tmp`) with the masked output copy and the three rule files. The script prints its exact path on the first lines. Delete it with `rm -rf <that exact path>` after you copied what you need. Never type `rm -rf` with a pattern.

## Plain words first (read this if you have never seen the project)
Every label below is used later in this file. One word keeps one meaning.
- **script**: the file `lead-repin-verify.sh`. It only reads and prints; it judges nothing.
- **test program** (also called the **take** in older notes; the release note v8 says "test program"): the program `run_real_check_n8n.py` that drives the real test run with the paid model and the customer list (CRM). It makes made-up sales leads, sends them through n8n (the workflow tool) into HubSpot (the CRM) and a mailbox, and prints a result. The script's setting `TAKE_DIR` is the folder of this program. **model program**: the separate program that makes the paid model calls and holds the model key. **Its folder is not in this checkout.**
- **masking filter** (also **filter**): the part of the script that looks at every line before it is printed and replaces a value that looks like a password, key, token or e-mail address with `<masked>` (or `<email-masked>`). Two other replacement words exist: `<masked-blob>` for a long string of letters and digits that no name explains, and `<masked-token>` for a mixed-letter word of 12 or more characters.
- **stage**: one step of the filter. Stage 1 uses rules about names and shapes (a `sed` program); stage 2 (an `awk` program) hides long opaque strings and whole lists and cuts long lines.
- **canary test** (also **self-test**): before the script opens any file of the test program, it feeds the filter a list of made-up secrets and a list of harmless lines. If one made-up secret still shows, or a harmless line is hidden, the script stops with exit code 3 and has opened no file. Each made-up line is checked through up to four views of the filter (the whole filter, the final pass, stage 1 alone, stage 2 alone), so a damaged rule cannot hide behind the other stage. The name comes from the bird taken into a mine to warn of bad air.
- **work folder**: the private folder the script makes for itself with `mktemp`. Only its owner can open it.
- **exit code**: the number a program leaves when it ends. 0 means it ran to its end; any other number is a specific kind of stop.
- **sed, awk, grep, find**: ordinary text tools on Linux. **GNU sed** is the usual Linux version; macOS and busybox ship a different one, which the canary test then rejects. Check yours with `sed --version`: the first line must say `GNU sed`.
- **WSL**: Windows Subsystem for Linux, a Linux terminal inside Windows.
- **sha256**: a 64-character fingerprint of a file; any change to the file gives a different one.
- **head**: the newest saved version (commit) of a folder in git. **final head**: the version the real test will run from; every answer must say which one it is about (block R00 prints it).
- **second reader**: a second person or agent who reads the same code on their own and also answers (release note v8, gate G1).
- **Release note v8**: `../steps-edits/LEAD-RELEASE-NOTE-v8.md`. **G1 to G38**: its numbered gates (rows the lead must answer, for example G1 line 22, G16 line 61, G26 line 63, G27 line 69, G34 line 48). **Q23, Q27**: numbered questions answered in `../ORDERS.md` (the answers are on lines 185 to 194). **Owner sheet v24-A**: `../steps-edits/OWNER-SHEET-v24-A.md`; its rules are **R1 and R4 to R10** (R2 and R3 are not used): R4 is money (the most the owner can lose), R5 is "compare every number in the notice with the numbers message", R6 is "the owner types `y`, the challenge line and `end` by hand", R10 is the FREEZE rule.
- **Numbers message**: the lead's message to the owner with the final figures (release note v8 section 3). **Ban list**: the sentences nobody may say unless shown (release note v8 line 122); its item 10 forbids saying the test program deletes or does not delete contacts unless G1 and the printed result both show it.
- **the typed word `end`**: after the test program has made its sends, the owner types `end` by hand to tell it to finish. Whether it can still call the model afterwards is question Q27 a.
- **stage 2 words**: see **stage** above. **BL-wp6-G1**: a row in the studio's own list of open problems; this file only quotes it.
- **lease**: the time n8n keeps a lead claimed while it works on it. The release note (G12, line 33) says only that a gap longer than the lease is not claimed. I found no more exact definition.
- **FREEZE**: the owner sheet's word (R10) for the state after a surprise: the owner types and closes nothing more, reports in words and waits for the lead's written word.
- **need_seconds**: a number inside the test program: how many seconds it needs to finish. The last allowed start is the deadline minus that number. The lead reads the real value at the final head (G10).
- **files_read**: in the output, how many files a search really opened. A search that opened 0 files looked at nothing.
- **qs_37**: the name of the test that shows a refusal after the window end (Q27 b). **window**: the allowed time span for paid calls.
- **marker**: a small file whose existence says "the owner has accepted"; the model program must see it before its first paid call (Q27 c). **decision 2**: the studio decision that the test program never deletes contacts (ORDERS Q23).
- **UNVERIFIED**: written from a source, not seen working. **masked**: a value replaced by `<masked>`.
- **porcelain**: the machine-readable output form of `git status`.

## Two earlier reviews disagree about a delete path (read this before Q23)
- `../AGENT-SCOPE-DO-AND-DONT.md` line 20 (it cites finding F-01 of `review-codebase-1.md`, marked CODE-CHANGE-NEEDED, not fixed) says the test program ends by archiving its own made-up HubSpot contacts, and that the code does this as a **DELETE call** at `run_real_check_n8n.py:1051` and `crm_hubspot.py:504-509`. It adds that the owner's HubSpot key is read-only, so the archive would fail only after the sends.
- The lead's answer to Q23 (`../ORDERS.md` lines 185 to 194) says the r17 review (11:00Z) found **no delete or archive path**, only a read called `rows_with_prefix`, and calls the line 1051 reading UNVERIFIED stale text.
- I cannot tell which is right. The script decides neither: block Q23-2 prints what stands today at those line numbers, and block Q23-1 searches every file for delete words. The lead reads both at the final head.
- **What counts as a delete path** (my criterion, for the lead to correct): a place in the code that **calls** something which deletes, archives, purges or removes a contact (a call line, not a comment, not printed text, not a test, not a variable name such as `deleted_at`). A match that is only a comment, a printed sentence or a test is not a delete path.

## Rules that bind this file (ORDERS.md lines 185 to 194, lead answers of 12:50Z)
- **Q23:** decision 2 stays: the test program never deletes. The line 1051 reading is UNVERIFIED stale text. The lead shows the final-head search at re-pin. The HubSpot key is not widened.
- **Q25:** cancel-by 18:19 UTC (23:49 IST). Target test is Wed 18 Nov, "so no take on 23 Nov unless Q27 is shown at the final head".
- **Q27:** (a), (b) and (c) are UNVERIFIED; the lead reads `run_real_check_n8n.py` at the final head and answers with line numbers at re-pin; until then write "lead verifies at re-pin".
- **Builder's reading, not an order:** "Q27 is shown" means **all three** of (a), (b) and (c). The lead can correct this; if it reads "any" or "two", the sentence in this file changes. Where this file says what an outcome means, the meanings are the builder's reading. ORDERS gives no default for "Q23 not shown"; the lead decides.

## What the script does to the machine (exact)
`sh lead-repin-verify.sh [TAKE_DIR]` (TAKE_DIR defaults to the current folder). It needs GNU sed (or a sed that knows the `s///I` flag), grep, awk, tr and find. All text tools run with `LC_ALL=C` (byte-wise matching) and `grep -a` (a file with a byte that is not valid text is still searched). The script sets its own `PATH` without the current folder, and turns the shell trace off (`set +x`) so that `sh -x` does not print a value.
- It reads files (grep, sed, awk, tr, wc, find, sha256sum), reads git (`rev-parse`, `log`, `status`) and reads the list of listening ports. A file the person running it cannot read is counted as UNREADABLE, including in block R00 (checksums).
- **Git switches.** All git calls use `--no-optional-locks` and `-c core.fsmonitor=false`. Checked on a made-up git folder (`evidence-repin4/09-git-index.txt`): the index file had the same sha256 and modification time before and after a normal run. These switches do **not** stop every program the folder's own git settings can name (`git status` may run a filter program). If you do not trust the folder, run with `LEAD_REPIN_NO_STATUS=1`: the script then does not run `git status`. With a git older than 2.36 the script does not run `git status` either, and says so. The script prints the top folder of the git work tree, because a test folder inside a bigger repository would print that repository's commit id.
- It writes **only** into one private work folder made by `mktemp` (folder mode 700, files mode 600). **On a Windows-mounted drive under WSL those modes may not be enforced**; set `TMPDIR` to a Linux folder. **No unmasked line of a searched file is written to disk**: every search sends grep's output straight into the filter. The only file with made-up secrets is the canary input; it is deleted at once and on every exit path.
- **When the run ends normally, the script deletes every file in the work folder except the masked output copy and the three rule files.** The file-name lists are deleted because a file name can itself hold private text.
- It deletes only inside the work folder it made (the path must have the form `.../lead-repin.XXXXXX`, checked before `rm -rf`). It removes the whole work folder in `--self-test` and `--mask`, when the canary test fails, and when the run is stopped by INT, TERM, HUP, PIPE or QUIT. A normal run keeps the work folder with the masked output copy; delete it yourself. When the run is stopped, the script also stops the programs it started (sed, awk, grep).
- It makes no network call and no model call, starts no program of the test and never the model program. It judges nothing.
- **Exit codes:** see the table above.
- **Masking is a safety net, not a guarantee.**
  - One filter is used on every search result, and a second pass over the whole output runs at the end (the script prints how many extra values it hid). The canary test runs first.
  - A value is hidden when its **name** looks secret. The name rule is general: any identifier that holds, as a word or inside a word, secret, password (passwd, pwd), passphrase, credential, token or apikey (secretValue, tokenString, passwordHash, authTokenValue), or the whole word key, pass, pat, auth, bearer, private, cookie, session, signature, hmac, dsn, webhook, salt, otp, cert (also with value, string, data, text, hash, bytes, material after it). It also hides: values in URLs with `user:password@`, `curl -u`, header values (Bearer, Basic, Authorization), JWT-shaped values, well-known key shapes (`sk-`, `ghp_`, `AKIA...` and others), JSON and YAML values (including all block forms `|`, `>`, with indent or chomp marks, and their continuation lines), PEM private-key blocks, triple-quoted text, command flags (`--password`, `-p` after `mysql`, `mysqldump`, `mysqladmin`, `mariadb`, `mongodump`, `mongorestore`, `sshpass` or `redis-cli`), XML attribute pairs, netrc lines, and e-mail addresses. Token counters (`max_tokens`, `prompt_tokens`) are kept.
  - A value with no secret name that is 24 or more letters and digits (with at least one letter and one digit) is hidden as `<masked-blob>`; mixed-letter words of 12 or more characters as `<masked-token>`.
  - **What it can still show:** a short secret (under 24 characters) with an unknown name and no known shape; and a bare line such as `passwd NAME` or `-p VALUE` with no command in front (my probe set of 49 new lines left exactly these two showing; ``evidence-repin5/02-probe-49-lines.txt``). The filter errs on the side of hiding: `key_file`, `monkey`, `session` and `cert` words hide their value, a folder name with a 36-character id prints as `<masked-blob>`, and a container (a JSON or YAML block) longer than the line limit is hidden whole rather than printed.
  - **Before you share the output**, read it once on screen for anything that still looks like a secret. Give it to the lead only; never paste it into a chat or a pull request.
- At the end of the output the script prints how many lines had a value hidden, how many searches printed fewer lines than grep counted (`PRINT MISMATCH`), and on how many matching lines the searched word itself was hidden (`MATCH WORD HIDDEN`).

**Other modes.** `sh lead-repin-verify.sh --self-test` runs the canary test and prints PASS or FAIL per case (case names only, never a made-up secret); it then runs the machinery checks (the stop after a damaged filter, signals in the main phase and in `--mask`, file names with sed characters, the judging of a forged result, the count of left-out files). `<command> | sh lead-repin-verify.sh --mask` runs the canary test, then masks any text. **Test aids, never for real use:** `SELFTEST_FILTER="sh other.sh --mask"` (with `--self-test` only) runs the cases against another filter; `LEAD_REPIN_TEST_BREAK_FILTER=weak|empty` damages the filter on purpose; `LEAD_REPIN_TEST_LATE_FAIL=1` makes the self-test fail only at its return value, to show that the exit code follows the tally; `LEAD_REPIN_NO_META=1` skips the machinery checks that start the script again.

**Test counts** (from `evidence-repin5/03-selftest-dash.txt` and `03-selftest-bash.txt`): `--self-test` passed=1022 failed=0 under dash and under bash. The 49-line independent probe: `evidence-repin5/02-probe-49-lines.txt`. Timing: passing text through `--mask` takes about 1.3 seconds for the start-up canary test alone, and a 1 MB single line took about 10.7 seconds in total (three runs: 10.66, 10.77, 10.75 seconds; `evidence-repin5/07-timing-1mb.txt`). The v4 guide said 0.57 to 0.70 seconds for the 1 MB line; I could not reproduce that with v5, which has more rules and a bigger canary test, so use the v5 figure.

**Mutation check:** I damaged the script copy one place at a time and ran the self-test: all 14 damages under both shells (28 runs) were caught; the survivors found on the way (the line-start YAML rule, the quoted-string YAML rule, the two result judges, the left-out-files count) each got a new case (`evidence-repin5/04-mutants.txt`). The old v4 check ran 7 damages under 2 shells (14 runs); the independent run found 3 of those to be missed or mis-read. One of my earlier readings was wrong: I had called mutant m3 (the self-test return value forced to success) harmless; the independent run showed the v4 tests did catch it. Plain statement: **my earlier "equivalent mutant" reading of m3 was wrong; it is caught.** A variant with no check for `FAIL` lines plus a forged tally still exited 1 with passed=6 in the independent run; the reason is that a third, independent signal (the return code of `self_test`) fails it. In v5 each judge of the result (`st_verdict` and `st_recount`) is also tried alone on forged results.

Settings (environment variables, all optional): `TAKE_PY CRM_PY DRIVE_PY N8N_PY` (when not set, the script finds each file by name among files with at most 3 sub-folders below TAKE_DIR, prefers one in a `scripts/` folder, prints which file it used and any other with the same name), `FLOWS_DIR`, `MODEL_DIR`, `MODEL_SETTINGS`, `ONE_STORE`, `LEAD_REPIN_NO_STATUS`, `END_RE`, `MODEL_RE`, `DELETE_RE`.

**Setting MODEL_DIR.** The model program folder is not in this checkout. If you have it: `MODEL_DIR=/path/to/model-program-folder sh lead-repin-verify.sh > /tmp/lead-repin-out.txt`. Without it, the model side of Q27 a, b and c cannot be answered (the script says so).

**How deep the search goes.** Files whose path has at most 4 parts below the folder are searched: `a/b/c/file` (3 sub-folders) yes; `a/b/c/d/file` no. The script counts the left-out files by reason and prints the numbers.

**Tested only here:** GNU sed 4.9, mawk 1.3.4, dash and bash on Linux. Not tested on busybox, macOS, WSL or Windows, and not against the real test program.

## Failures first (what this checklist cannot do)
1. A search finds text; it does not prove behaviour. "No delete call found" needs a second reader (G1). "Refusal exists" needs the refusal SHOWN (a test run or the startup refusal), not only a grep hit.
2. Q27 a is about run order. A grep prints line numbers; read the code around them. A call already sent before `end`, and an n8n retry or lease that fires a call after `end`, cannot be shown by reading: they need a run or a test shown at the final head.
3. The default search words are my guesses. Zero hits can mean "not there" or "wrong words". A block total line is a sum of several searches; read the per-search lines.
4. **By default the model program is NOT searched** (MODEL_DIR is empty). Then Q27 a model side, Q27 b model side, `qs_37` on the model side and Q27 c half B cannot be answered, so **Q27 c cannot be answered at all** without MODEL_DIR.
5. Block Q23-1 searches the four named files first, then every other python and shell file, then every flow json, and **prints how many files each list left out and why**: a path of 5 or more parts, symbolic links, folders find could not open, names with a line break, files inside `node_modules`, `_local`, `secrets`, `.venv`, `venv`, `__pycache__`, `tests`, `test`, and every file of another type. A "0 matching lines" means "none in the files that were looked at". Flow files under `_local` are searched only for the delete words and printed as `file:line:word`, never the line.
6. An unreadable file is printed as `UNREADABLE (not searched, NOT zero matches)`. In v2 I saw that branch work as an ordinary user. For v5: I ran v5 as the user `nobody` on a made-up folder with one unreadable file: exit code 0, no `Permission denied` text, block R00 prints `UNREADABLE (checksum not made, NOT zero)` and counts it, and the run check prints `STOP-SIGNAL` lines (`evidence-repin5/06-nonroot.txt`). Still not seen on a real test folder.
7. Not covered by a read-only command, so not in the script: G2, G3, G5, G8, G9, G11 to G15 (except what the table names), G19, G21 permission names, G22 to G25, G27 to G32.
8. The hand-typed commands below are not the script: they have no line cutting and fewer search words. They go through `--mask` (same filter), but run the script when you can.
9. Windows listeners are not seen from WSL (the script says so when it detects WSL; check `netstat -ano` on Windows for 5678 and 5679).
10. Not tested: a run inside a real git work tree of the test program; WSL; macOS; Windows; busybox; any sed that is not GNU sed 4.9; any awk other than mawk 1.3.4.
11. The delete words are the pieces `delet`, `archiv`, `purg`, `remov`, `trash`, `gdpr`, `clean`, `unlink`, `rmtree` and `method = delete or patch`; they also match harmless words such as `deleted_at`, so more lines print.
12. The `-p` flag rule works only after a fixed list of commands. A secret on a line with a name the rules do not know, shorter than 24 characters, can show (see "Masking is a safety net").
13. **A mask is not a replacement for reading.** If the real output holds a value that looks like a secret and is not masked, stop and tell the lead.

## How to type a hand command safely
The hand commands in the items below all follow this pattern. Set the folder once: `T=/path/to/test-program-folder` (keep the quotes if the path has spaces), then `LC_ALL=C; export LC_ALL`. **Check the path first:** `[ -f "$T/scripts/run_real_check_n8n.py" ] && echo path-ok || echo WRONG-PATH` (a wrong path gives an empty search that looks like "nothing found"). Then one file per command, so one wrong name cannot hide the others:

`{ grep -a -n -i -E 'WORDS' "$T/scripts/FILE.py"; echo "grep-exit-code=$?" >&2; } | sh lead-repin-verify.sh --mask`

The line `grep-exit-code=0` means grep found lines, `1` means found none, `2` means grep could not read the file (a wrong path or permission), which is **not** "none". Git commands: `git --no-optional-locks -c core.fsmonitor=false -C "$T" rev-parse HEAD`.

## Items

### Q23: does the test program have any delete or archive path to the CRM (G1; also G21 and G17)
- **Question:** does any python or shell file of the test program (not tests), the CRM module or any flow json **call** something that deletes, archives, purges, removes or cleans up a contact? (See the disagreement above.)
- **Answer needed (ORDERS Q23):** the lead shows the final-head search: yes or no, plus the line number of every hit, plus a named second reader (G1).
- **Blocks:** Q23-1 (search; counts of everything left out), Q23-2 (what stands at `run_real_check_n8n.py` lines 1045 to 1056 and `crm_hubspot.py` lines 500 to 512, printed with line numbers; says when the file is shorter), Q23-3 (HTTP methods in the CRM module), Q23-4 (delete wording the owner would read; G17), R00 (commit id and checksums; G26 asks for the checksum again just before the run).
- **Paste by hand** (after the path check above; one file per command):
  - `git --no-optional-locks -c core.fsmonitor=false -C "$T" rev-parse HEAD`
  - `{ grep -a -n -i -E 'DELETE|\.delete\(|archive|purge|remove|trash|gdpr|cleanup|unlink|rmtree' "$T/scripts/run_real_check_n8n.py"; echo "grep-exit-code=$?" >&2; } | sh lead-repin-verify.sh --mask` (repeat for `crm_hubspot.py`, `n8n_drive.py`, `n8n.py`)
  - `{ grep -a -r -n -i -E 'DELETE|archive|purge|remove|trash' --include='*.json' --exclude-dir=node_modules --exclude-dir=_local --exclude-dir=secrets "<flows folder>"; echo "grep-exit-code=$?" >&2; } | sh lead-repin-verify.sh --mask`
  - `{ sed -n '1045,1056p' "$T/scripts/run_real_check_n8n.py"; echo "sed-exit-code=$?" >&2; } | sh lead-repin-verify.sh --mask`
  - `{ grep -a -n -E '(^|[^A-Za-z_])(GET|POST|PUT|PATCH|DELETE)([^A-Za-z_]|$)|rows_with_prefix' "$T/scripts/crm_hubspot.py"; echo "grep-exit-code=$?" >&2; } | sh lead-repin-verify.sh --mask`
  - `sha256sum "$T/scripts/run_real_check_n8n.py" "$T/scripts/crm_hubspot.py" "$T/scripts/n8n_drive.py" "$T/scripts/n8n.py"` (a file you cannot read is named in an error line: that file is **not** checked)
- **Expected shape:** Q23-1 prints either only comment, test or wording lines, or a real call line. Q23-2: "file is shorter than line N" means the old number is stale. Q23-3: GET and POST names, and `rows_with_prefix` as a GET.
- **What each outcome means (builder's reading; ORDERS Q23 governs):**
  - No call anywhere and a second reader agrees: G1 can be YES; decision 2 stands; the clean-up message may say "the test program made no delete call" (G27); AGENT-SCOPE line 20 stays marked stale.
  - A delete or archive call exists: decision 2 is false at this head. The lead (or the owner) decides what follows. The sentence "the test program made no delete call" is not sent (ban-list item 10), and G21 (which permissions each HubSpot key has) reopens. The key is still not widened without the owner (ORDERS Q23).
  - Delete wording still printed (Q23-4): G17 fails; owner-sheet R5 then sends `n`; the wording in the numbers message must change.
  - Not shown: ORDERS gives no default; the lead decides.

### Q27 a: the test program never calls the model after the word `end` (G34). UNVERIFIED until the lead shows it.
- **Answer needed:** yes or no with line numbers. If a call can still follow, also what is printed and which exit code is left when the owner cancels the key right after `end`.
- **Block:** Q27a: part 1 lines handling `end` (case-sensitive, a quoted word or a constant; with 20 lines after each); part 2 every model-call line in the test program, `n8n_drive.py`, `n8n.py` and (if MODEL_DIR is set) the model program.
- **Paste by hand:** `{ grep -a -n -E "[\"']end[\"']" "$T/scripts/run_real_check_n8n.py"; echo "grep-exit-code=$?" >&2; } | sh lead-repin-verify.sh --mask`, then the same with your model-call words, then `sed -n 'A,Bp'` around the `end` branch to the end of `main`, each through `--mask`.
- **Expected shape:** the `end` line number and the model-call line numbers. "Never" holds only if no model-call line can run after the `end` branch AND a run or test at the final head shows no n8n retry or lease fires one.
- **Outcome (release note v8 G34, line 48):** shown "never": the numbers message says so with file, line and the test. Not shown: the numbers message says "exit code accepted then: none" (any other exit code is a FREEZE) and the owner sheet's cancel sentence stays. Fill G18's early-cancel line (line 38) from the same read.

### Q27 b: an end-date refusal exists and is SHOWN at the final head (G16, G10). UNVERIFIED until the lead shows it.
- **Spend warning:** to see the refusal, **run only the named `qs_37` test, against the fake (recorded) model.** Do not start the real model program, or a real stage with a real key, to "see" a refusal: the model program holds the real model key and a start could make a paid call. (A fake model only; no paid call without the owner's yes and numbers.) The hand command for the test, with the fake model, is the lead's to give: I did not see how the test is started, so I give no command for it.
- **Answer needed:** yes or no with file and line, and the refusal SHOWN (the `qs_37` test, or the startup refusal read from a safe run, at the final head). Also `need_seconds`.
- **Block:** Q27b: window-end words in the test program and (if MODEL_DIR is set) the model program; the test name `qs_37` in every python file including tests; lines of MODEL_SETTINGS whose name has the whole word end, window, deadline, until or not_after: **a value is shown only if it looks like a date or a number**; anything else is replaced by a note.
- **Paste by hand:** `{ grep -a -n -i -E 'window|end_date|not_after|deadline|need_seconds|2026-11-2|refus' "$T/scripts/run_real_check_n8n.py"; echo "grep-exit-code=$?" >&2; } | sh lead-repin-verify.sh --mask`; `{ grep -a -r -n qs_37 --include='*.py' "$T"; echo "grep-exit-code=$?" >&2; } | sh lead-repin-verify.sh --mask`.
- **Expected shape:** a setting name and a comparison line; a test name. A grep hit alone is "exists", not "shown".
- **Outcome:** shown: the numbers message line reads "End-date refusal: shown". Not shown (default): "End-date refusal: NOT SHOWN" and the test stays on Wed 18 Nov (owner sheet v24-A line 62 already carries "NOT SHOWN"). On my reading of Q25, showing (b) alone does not make Mon 23 Nov possible.

### Q27 c: the go marker before any model call (G33, line 47). UNVERIFIED until the lead shows it.
- **Answer needed:** yes or no with file and line in BOTH programs, plus a test at the final head.
- **Block:** Q27c: half A (marker words in the test program) and half B (marker words in the model program folder; needs MODEL_DIR). A zero in either half means NOT SHOWN by that search.
- **Paste by hand:** `{ grep -a -n -i -E 'marker|\.used|go_file|accepted|challenge' "$T/scripts/run_real_check_n8n.py"; echo "grep-exit-code=$?" >&2; } | sh lead-repin-verify.sh --mask`; the same for the model program files.
- **Expected shape:** the test program writes a marker after the accepted challenge; the model program tests for it before the first paid call. `~/.hadavin-take-tags/<id>.used` (AGENT-SCOPE) is the single-use tag marker made before the first post; it is not shown to be the same as the go marker.
- **Outcome:** shown: "Go marker: shown". Not shown (default): "Go marker: NOT SHOWN", the owner sheet's fallback wording applies and the owner's yes names it; no marker line at all means no run.

### Other gates the sheet leaves open, where a read can help
| Id | Question | Block | Answer needed | If not shown (default) |
|---|---|---|---|---|
| G35 (line 49) | Does the test program ask the owner to type anything besides `y`, the challenge line and `end`? | G35 | file and line of every prompt; "asks you to type a figure: no" | unknown: no run until the sheet is changed |
| G6 (line 27) | Exit codes, and the one for person C "unknown" | G06 | codes with file and line | default `none`: only 0 accepted |
| G4, G14 (lines 25, 35) | Call ceiling, retries, ledger (running total of calls), limit | G04 | file and line | the run total is not called a limit |
| G18 (line 38) | Wrong line after `end`, Ctrl-C, a pause that ends without `end`, which lock file is left | G18 | file and line | unknown; the sheet treats both as called-off runs |
| G36 (line 50) | The printed line that starts the film pause; silence and give-up minutes | G36 | copied line or offsets from the rehearsal | no cue named: no run |
| G37, G38 (lines 51, 52) | The per-run key file refuses an existing file; the start of the mail subjects; the prep contact not matching the film search | G37-38 | statement, copied subject start | statement missing: no run |
| G7 (line 28) | Ports 5678, 5679 (the owner's own), 5690 to 5693 (rehearsal), the test program's port | G07 | listing showing the ports free | a collision: change the port |
| G20 (line 40) | DECISION-one-store line 14 still says ONE database | G20 | the edited line | still ONE: edit it |

## What I did not check
The real test program, flows and model program (none present); real output of any block; whether the default search words match the real names; the owner-sheet sentences beyond the lines quoted from the release note; whether release note **v9** and owner sheet **v25-A** (newer files in `../steps-edits/`) still match every G and R number used above (I re-read only the rows I quote, in v8 and v24-A, on 16 Nov); that every ORDERS line number is still current; macOS and Windows shells (only dash and bash on Linux, GNU sed 4.9, mawk); WSL; a run inside a real git work tree of the test program; whether this script prints something a real test program would reveal that the made-up tree does not. **Sources I could not open:** the real test program, the model program, the flows, `review-codebase-1.md` (quoted only through AGENT-SCOPE line 20).
