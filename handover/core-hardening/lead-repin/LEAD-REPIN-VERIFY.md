# Lead re-pin checklist (guide version 6, script version 6)

Written Mon 16 Nov 2026 by a builder. Times are in UTC; IST (India time) is UTC plus 5 hours 30 minutes, so 14:00 UTC is 19:30 IST. Type `date -u` to see the UTC time now.

**Read this first.** Nothing in this file or in the script was checked against the real test program. The test program is not in this checkout. The commands use the file names the inputs quote, and the script was tried only on made-up folders. "Expected shape" below says what to look for; it is not a result.

## Version warning (the numbers in this file can be out of date)
This file quotes `../steps-edits/LEAD-RELEASE-NOTE-v8.md` and `../steps-edits/OWNER-SHEET-v24-A.md`. Newer files now exist in `../steps-edits/`: release notes v9, v10 and v11, and owner sheets up to v27-A. **I did not re-read any G number, R number or line number against those newer files.** Before you give an answer that names a gate (G) or a rule (R), open the newest release note and owner sheet and check that the number still means what this file says. Where they differ, the newer file wins and this file is wrong at that place.

## Who is who (every "you" in this file is the first one)
- **You, the reader:** the person who types the commands in this file on a computer that holds the test program's folder.
- **The lead:** the studio's lead (a person or the lead agent) who decides each answer and answers the owner. Where this file says "tell the lead", send it to the lead only: not to a chat, not into a pull request. **If you are the lead,** read "tell the lead" as "write it in your own notes and decide it".
- **The owner:** the person who pays for the test run and types `y`, the challenge line and `end` by hand.
- **The builder:** the person or agent who wrote this file and the script. The builder decides nothing. Where this file says "builder's reading", the lead may replace it.

## Stop now if (check this before anything else)
- You cannot type commands in a terminal (a text window where you type commands): stop; ask the lead for a person who can.
- `sed --version` does not print `GNU sed` on its first line: stop; the script's own test will refuse to run on another sed.
- You are about to type anything that contains a real password or key into a chat: stop; this file never asks for that.
- The self-test (Quick start step 2) does not end with the exact last line shown: stop; do not run step 3.

## Glossary (read once; every label below keeps one meaning)
- **script:** the file `lead-repin-verify.sh`. It reads files and prints; it judges nothing.
- **test program:** the program `run_real_check_n8n.py` that drives the real test run with the paid model and the customer list (CRM). It makes made-up sales leads, sends them through n8n (a workflow tool) into HubSpot (the CRM) and a mailbox, and prints a result. The script setting `TAKE_DIR` is the test program's folder (the name `TAKE_DIR` is old; it means "test-program folder"). The release note calls this the "take". **model program:** the separate program that makes the paid model calls and holds the model key. Its folder is not in this checkout.
- **commit:** one saved version of a folder in git. **final commit:** the commit the real test will run from; every answer must say which commit it is about (block R00 prints it). (Older notes call this "head".)
- **terminal:** the text window where you type commands. **command:** one line you type and then press Enter.
- **exit code:** the number a program leaves when it ends. 0 means it reached its end; any other number is a stop of a named kind (table below).
- **self-test:** the script's own check of its masking filter on made-up secrets (`--self-test`). The same short check also runs automatically at the start of every run and is then called the **start check**. Both are the same list of cases.
- **masking filter (filter):** the part of the script that looks at every line before it is printed and replaces a value that looks like a password, key, token or e-mail address with `<masked>` (or `<email-masked>`). Two other replacement words: `<masked-blob>` for a long string of letters and digits that no name explains, and `<masked-token>` for a mixed-letter word of 12 or more characters.
- **filter step:** the filter has steps that run one after another: step 0 (an awk program) cuts very long lines and finds values that continue over several lines; step 1 (a `sed` program) uses rules about names and shapes; step 2 (an `awk` program) hides long opaque strings and whole lists and cuts long lines. (Older notes call step 1 "stage 1" and step 2 "stage 2".)
- **work folder:** the private folder the script makes for itself with `mktemp` (mode 700: only its owner can open it). **masked copy:** the file `lead-repin-verify-out.txt` inside the work folder: the same text the script printed, already masked, written with mode 600 (only its owner can read it).
- **block:** one numbered part of the output, headed `===== BLOCK <id>: <title> =====` (for example R00, Q23-1, Q27a). **search:** one grep inside a block. **run check:** the last lines of the output, headed `RUN-CHECK`; **STOP-SIGNAL** is a line there that says "the run itself could not look at something".
- **stop for that search:** do not use that search's result (its zero or its count means nothing), write "not done" for the item that search feeds, and **carry on with the other searches and items**.
- **hand command:** a command you type yourself (items below) instead of running the whole script.
- **TMPDIR:** the setting that names the folder where `mktemp` makes the work folder (default `/tmp`).
- **sed, awk, grep, find, tr:** ordinary text tools on Linux. **GNU sed** is the usual Linux version; macOS and busybox ship a different one, which the self-test then rejects.
- **WSL:** Windows Subsystem for Linux, a Linux terminal inside Windows. **sha256:** a 64-character fingerprint of a file; any change to the file gives a different one.
- **second reader:** a second person or agent who reads the same code on their own and also answers (release note v8, gate G1).
- **Release note v8** (`../steps-edits/LEAD-RELEASE-NOTE-v8.md`): its numbered gates are **G1 to G42** (rows the lead must answer). **Q23, Q25, Q27:** numbered questions answered in `../ORDERS.md` (lines 185 to 194). **Owner sheet v24-A** (`../steps-edits/OWNER-SHEET-v24-A.md`): its rules are R1 and R4 to R10 (R2 and R3 are not used): R4 is money (the most the owner can lose), R5 is "compare every number in the notice with the numbers message", R6 is "the owner types `y`, the challenge line and `end` by hand", R10 is the FREEZE rule.
- **Numbers message:** the lead's message to the owner with the final figures (release note v8 section 3). **Ban list:** the sentences nobody may say unless shown (release note v8 line 122); its item 10 forbids saying the test program deletes or does not delete contacts unless G1 and the printed result both show it.
- **the typed word `end`:** after the test program has made its sends, the owner types `end` by hand to tell it to finish. Whether it can still call the model afterwards is question Q27 a.
- **lease:** the time n8n keeps a lead claimed while it works on it. Release note v8 line 123 says only "A gap longer than the lease is not claimed" (G12, line 33, says the lease sentence must be decided). I found no more exact definition.
- **FREEZE:** the owner sheet's word (R10) for the state after a surprise: the owner types and closes nothing more, reports in words and waits for the lead's written word.
- **need_seconds:** a number inside the test program: how many seconds it needs to finish. The last allowed start is the deadline minus that number. **files_read:** how many files a search really opened (0 means it looked at nothing). **qs_37:** the name of the test that shows a refusal after the window end (Q27 b). **window:** the allowed time span for paid calls.
- **marker:** a small file whose existence says "the owner has accepted"; the model program must see it before its first paid call (Q27 c). **decision 2:** the studio decision that the test program never deletes contacts (ORDERS Q23).
- **challenge line, person C, prep contact, film search, film pause:** words of the owner sheet; this file uses them only where it quotes the sheet, and explains none of them. If one of them blocks you, ask the lead.
- **UNVERIFIED:** written from a source, not seen working.

## Quick start (3 steps)
**Set these two names once per terminal** (replace the two paths; keep the quotes):
```
S="/full/path/to/lead-repin-verify.sh"
T="/full/path/to/the/test-program-folder"
```
Check both: `[ -f "$S" ] && echo script-ok || echo WRONG-SCRIPT-PATH` and `[ -f "$T/scripts/run_real_check_n8n.py" ] && echo path-ok || echo WRONG-TEST-FOLDER-PATH`. A wrong path gives an empty search that looks like "nothing found".

1. **Self-test** (works from any folder): `sh "$S" --self-test`. It takes about 2 minutes. The **last line** must read exactly `SELF-TEST: passed=1191 failed=0 (the made-up input and output files were deleted)`. Any other last line, or any line that starts with `FAIL`: **stop**, do not run step 2, send the whole output to the lead. (If you run it with `LEAD_REPIN_NO_META=1` the number is 1167: that is the shorter start check, not the self-test.)
2. **Run the checklist:** `sh "$S" "$T"`. It prints to the screen and, at the same time, writes the same masked text to the masked copy. The first two lines it prints say `WORK-FOLDER: <path>` and `COPY-OF-OUTPUT (masked): <path>`: both go to the screen's error channel, so they show on the screen even if you redirect the output. **Write down that path** (call it `$OUT` below: `OUT="<the COPY-OF-OUTPUT path>"`). Do not redirect the output to a file of your own: the masked copy already exists, in the private work folder. Then type `echo "exit code: $?"` right away.
3. **Read, then hand in** (next section). The script judges nothing; the lead decides each answer.

If a run was ended and you lost the path, find the folders: `ls -d "${TMPDIR:-/tmp}"/lead-repin.??????`.

## What you hand in
Hand in **one text answer sheet** to the lead, and keep the masked copy on the computer until the lead says you may delete it. For each item below write one line in this form (copy and fill; "not done" is a valid answer):
`ITEM | answer: yes / no / not shown / not done | file and line numbers | which commit (from block R00)`
Items: **Q23**, **Q27 a**, **Q27 b**, **Q27 c**, and each row of the table "Other gates" below.
- **List the blocks:** `grep -n '^===== BLOCK' "$OUT"`.
- **Show one block** (replace Q23-1 by an id from the list): `awk -v b="Q23-1:" '/^===== BLOCK /{p=($3==b)} p' "$OUT"`.
- **Never paste a secret-looking value.** Give the file and line number only.
- The lead gets the answer sheet and, if asked, the masked copy. Nobody else gets either.

## What the output means: continue or stop
| What you see | What it means | Do | Who decides | Next |
|---|---|---|---|---|
| Exit code `0` and `RUN-CHECK: no stop signal` | The run reached its end. It does **not** mean the answers are good. | Continue | The lead decides each answer | Read every block, fill the answer sheet |
| Exit code `0` and one or more `STOP-SIGNAL` lines | The run itself could not look at something (missing file, unreadable file, zero files searched, missing lines, a hidden search word) | **Stop for the named search** (defined above) and continue with the others | You, then the lead | Fix the path or permission and run again, or tell the lead |
| Exit code `2` | Setup problem: no work folder could be made, or the test-program folder was not found | Stop | You | Check `$T` and that `TMPDIR` (or `/tmp`) can be written; run again |
| Exit code `3` | The masking filter is unusable or failed its own start check; **no file of the test program was opened** | Stop | The lead | Run step 1 and send its output to the lead. Common cause: a sed that is not GNU sed |
| Exit code `4` | The output pipe failed (for example the reader closed with `| head`); partial output is in the masked copy | Stop | You | Run again without `| head`; then delete the work folder |
| Exit code `129`, `130`, `131`, `141`, `143` | The run was ended by hang-up (129), Ctrl-C (130), quit (131), closed pipe (141) or kill (143), or by the time limit (143, see below) | Stop | You | Run again. The script removed its work folder itself |
| Self-test exit code `0` and the exact last line | Every check passed | Continue | You | Go to step 2 |
| Self-test exit code `1`, or any line starting `FAIL` | At least one check failed | Stop | The lead | Send the output to the lead |
| A line starting `STOP:` | The script refused to print | Stop | The lead | Send the line to the lead |
| `ZERO HITS` on one search | The words are not there, or the search words are wrong | Continue; it is not proof | The lead | Read the left-out counts; try the hand command |
| `ZERO FILES SEARCHED` | The search looked at nothing | Stop for that search | You | Fix the folder path |
| `UNREADABLE (not searched, NOT zero matches)` | A file could not be opened | Stop for that search | You | Fix the permission or tell the lead |
| `PRINT MISMATCH` | Fewer lines printed than grep counted | Stop for that search | You | Open the file at the line numbers yourself |
| `MATCH WORD HIDDEN` (also a STOP-SIGNAL line) | The filter hid the searched word itself on a line | Stop for that search | You | Open those file lines yourself and read them; then continue with the others |
| A secret-looking value on the screen (not `<masked>`) | The filter missed it | Stop; do not share the output | The lead | Tell the lead the file and line number (not the value); delete the work folder |

**One rule for `MATCH WORD HIDDEN`:** it is always "stop for that search" (the table row and the script's RUN-CHECK say the same).

**When a real run prints something the made-up folder never did** (a new kind of line, a different file layout): do not guess. Keep the masked copy, tell the lead the line number and what looks different, and wait.

**Time limit.** A run that takes longer than 1200 seconds (20 minutes) is ended by the script itself: it prints a `STOP:` line saying so and exits with 143. Change the limit with `LEAD_REPIN_MAX_SECONDS=<seconds>`.

**Delete the work folder when you finish** (after the lead has what is needed): `rm -rf "<the exact WORK-FOLDER path>"`. Never type `rm -rf` with a pattern.

## Two earlier reviews disagree about a delete path (read this before Q23)
- `../AGENT-SCOPE-DO-AND-DONT.md` line 20 (it cites finding F-01 of `review-codebase-1.md`, marked CODE-CHANGE-NEEDED, not fixed) says the test program ends by archiving its own made-up HubSpot contacts, and that the code does this as a **DELETE call** at `run_real_check_n8n.py:1051` and `crm_hubspot.py:504-509`. It adds that the owner's HubSpot key is read-only, so the archive would fail only after the sends.
- The lead's answer to Q23 (`../ORDERS.md` lines 185 to 194) says the r17 review (11:00Z, an earlier review of the code) found **no delete or archive path**, only a read called `rows_with_prefix`, and calls the line 1051 reading UNVERIFIED stale text.
- I cannot tell which is right. The script decides neither: block Q23-2 prints what stands today at those line numbers, and block Q23-1 searches every file for delete words. The lead reads both at the final commit.
- **What counts as a delete path** (the builder's criterion; the lead may replace it): a place in the code that **calls** something which deletes, archives, purges or removes a contact (a call line, not a comment, not printed text, not a test, not a variable name such as `deleted_at`). Lead's decision on this criterion: ____________ (blank: the lead fills it in).

## Rules that bind this file (ORDERS.md lines 185 to 194, lead answers of 12:50Z)
- **Q23:** decision 2 stays: the test program never deletes. The line 1051 reading is UNVERIFIED stale text. The lead shows the final-commit search at re-pin. The HubSpot key is not widened.
- **Q25:** cancel-by 18:19 UTC (23:49 IST). Target test is Wed 18 Nov, "so no take on 23 Nov unless Q27 is shown at the final head" (ORDERS wording; "take" there means a real test run).
- **Q27:** (a), (b) and (c) are UNVERIFIED; the lead reads `run_real_check_n8n.py` at the final commit and answers with line numbers at re-pin; until then write "lead verifies at re-pin".
- **Open decisions (the lead fills these in; the builder gives no order):**
  - "Q27 is shown" means: all three of (a), (b), (c) / any / two: ____________
  - What happens when Q23 is "not shown": ____________
  - Whether showing Q27 b alone makes Mon 23 Nov possible: ____________ (the builder's guess is no; it is a guess).

## What the script does to the machine (exact)
`sh "$S" [TEST_PROGRAM_FOLDER]` (the folder defaults to the current folder). It needs GNU sed (or a sed that knows the `s///I` flag), grep, awk, tr and find. All text tools run with `LC_ALL=C` (byte-wise matching) and `grep -a` (a file with a byte that is not valid text is still searched). The script sets its own `PATH` without the current folder, and turns the shell trace off so that `sh -x` does not print a value.
- It reads files (grep, sed, awk, tr, wc, find, sha256sum), reads git (`rev-parse`, `log`, `status`) and reads the list of listening ports. A file the person running it cannot read is counted as UNREADABLE, also in block R00 (checksums).
- **Git switches.** All git calls use `--no-optional-locks` and `-c core.fsmonitor=false`. Checked on a made-up git folder (`evidence-repin4/09-git-index.txt`): the index file had the same sha256 and modification time before and after a normal run. These switches do **not** stop every program the folder's own git settings can name (`git status` may run a filter program). If you do not trust the folder, run with `LEAD_REPIN_NO_STATUS=1`: the script then does not run `git status`. With a git older than 2.36 it does not run `git status` either, and says so. The script prints the top folder of the git work tree, because a test folder inside a bigger repository would print that repository's commit id.
- **Where it writes.** The script writes **only inside its private work folder** (one folder made by `mktemp`, mode 700, files mode 600). That folder holds the masked copy and the three filter rule files; the script's own temporary lists are deleted when it ends. **It never needs, and this file never tells you to use, a file name of your own under `/tmp`.** If you want the output in a file, read the masked copy in the work folder; if you must save text elsewhere, first type `umask 077` and make a private folder (`mkdir -m 700 <folder>`) and use that folder. **On a Windows-mounted drive under WSL the modes may not be enforced**; set `TMPDIR` to a Linux folder. **No unmasked line of a searched file is written to disk**: every search sends grep's output straight into the filter. The only file with made-up secrets is the self-test input; it is deleted at once and on every exit path.
- **When the run ends normally, the script deletes every file in the work folder except the masked copy and the three rule files.** The file-name lists are deleted because a file name can itself hold private text.
- It deletes only inside the work folder it made (the path must have the form `.../lead-repin.XXXXXX`, checked before `rm -rf`). It removes the whole work folder in `--self-test` and `--mask`, when the start check fails, and when the run is stopped by INT, TERM, HUP, PIPE or QUIT. A normal run keeps the work folder with the masked copy; delete it yourself. When the run is stopped, the script also stops every program it started (sed, awk, grep, find, git), at once, even while one of them is busy (v6; the v5 run left such a program running in one case).
- It makes no network call and no model call, starts no program of the test and never the model program. It judges nothing.

### Masking is a safety net, not a guarantee
- **How it works.** One filter is used on every search result, and a second pass over the whole output runs at the end. The self-test runs first.
- **What it hides** (a value is hidden when its **name** looks secret): any name that holds, as a word or inside a word, secret, password (passwd, pwd), passphrase, credential, token or apikey, or the whole word key, pass, pat, auth, bearer, private, cookie, session, signature, hmac, dsn, webhook, salt, otp, cert (also with value, string, data, text, hash, bytes, material after it). It also hides: passwords in web addresses of every form (`user:password@host`, `:password@host` with an empty user, `//password@host`, and a password after `@` or `:` in a longer address), `curl -u`, header values (Bearer, Basic, Authorization), JWT-shaped values, well-known key shapes (`sk-`, `ghp_`, `AKIA...` and others), JSON and YAML values (all block forms and their continuation lines), PEM private-key blocks, triple-quoted text, command flags (see the list below), XML attribute pairs, netrc lines, and e-mail addresses. Token counters (`max_tokens`, `prompt_tokens`) are kept.
- **Values over several lines (new in v6).** After a line that gives a secret-named variable a value and opens a bracket it does not close (`NAME = (`, `[`, `{`, `$(`), or ends with a backslash, every following line is hidden until the brackets close, a line containing only `--` appears, or the input ends. It never prints the rest raw, however many lines it takes.
- **Names with a character outside plain English letters (new in v6).** A name that holds a hidden zero-width character or any byte outside plain ASCII (`pass<zero-width space>word = ...`) is treated as a secret name: its value is hidden.
- **Very long lines (new in v6).** A line longer than 20000 characters is cut before the filter looks at it (this keeps the run time bounded), and the printed line is cut again at about 240 characters with a note `[CUT: this line has N characters; the rest is not shown]`.
- **Password flags: this is a LIST, not a rule that covers everything.** The value after `-p`, `-P`, `-a`, `-w`, `-k`, `-pVALUE` is hidden when the line starts with one of these commands: docker, podman, nerdctl, skopeo, buildah, helm, redis-cli, ldapsearch and the other ldap tools, zip, zipcloak, unzip, 7z, 7za, 7zr, rar, unrar, arj, htpasswd, smbclient, smbget, rpcclient, mount, psql, pg_dump, pg_restore, mongo and the other mongo tools, sqlcmd, bcp, ftp, lftp, ncftp, rclone, openconnect, openssl, ccrypt, gpg, mysql, mysqldump, mysqladmin, mariadb, sshpass, cqlsh, beeline, impala-shell, influx, svn, hg, az, cryptsetup, ansible, vncpasswd, xfreerdp, rdesktop, remmina (the list is in the script as `PWCMDS`). For a command **not** on the list, a second rule hides the value when the line looks like a command (it starts with a word, has `-p`, `-P` or `-w`, and the value is not a plain number). A password given in another way, to a command that is neither on the list nor shaped like that, can show.
- **Long values with no secret name.** A value of 24 or more letters and digits (at least one letter and one digit) is hidden as `<masked-blob>`; mixed-letter words of 12 or more characters as `<masked-token>`.
- **What it can still show (I tested these and they show):**
  - a short secret (under 24 characters) with an unknown name and no known shape;
  - a bare line such as `passwd NAME` or `-p VALUE` with no command in front;
  - a password made only of digits, after a command that is not on the list;
  - a secret that starts with `/`, `.` or `~` and is cut by slashes into pieces of under 24 characters each (the filter judges such text piece by piece; the v5 run showed this gap and v6 narrowed it: a mixed-case piece of 24 or more characters is now hidden, shorter pieces are not);
  - a sentence where the name is written with a look-alike letter from another alphabet (for example `the pa<Cyrillic s>sword is hunter99`): not recognised, so the value shows (tested). In an assignment (`name = value` or `name: value`) the same look-alike name is caught by the non-ASCII rule: the value is hidden and the name is printed as `NONASCII_NAME_SECRET` (tested).
- The filter errs on the side of hiding: `key_file`, `monkey`, `session` and `cert` words hide their value, a folder name with a 36-character id prints as `<masked-blob>`, and a container (a JSON or YAML block) longer than the line limit is hidden whole.
- **Before you share the output**, read it once on screen for anything that still looks like a secret. Give it to the lead only.
- **What the script prints about its own hiding** (exact wording; the counts are printed by the script, not claimed here): `Hidden by the masking filter in search results: N line(s) had a value hidden, M of them were hidden whole`; and `Final pass over the whole output above: N additional value(s) hidden (0 means the search-time filter had already hidden everything the belt knows)`; also `PRINT MISMATCH` and `MATCH WORD HIDDEN` counts.

### Other modes
- `sh "$S" --self-test` runs the self-test and prints PASS or FAIL per case (case names only, never a made-up secret), then the machinery checks (the stop after a damaged filter; signals TERM and HUP in the main phase and while the file lists are made; the time limit; signals in `--mask`; file names with sed characters; the judging of a forged result and of a wrong case count; the count of left-out files).
- `<command> | sh "$S" --mask` runs the start check, then masks any text.
- **Test aids, never for real use:** `SELFTEST_FILTER="sh other.sh --mask"` (with `--self-test` only) runs the cases against another filter; `LEAD_REPIN_TEST_BREAK_FILTER=weak|empty` damages the filter on purpose; `LEAD_REPIN_TEST_LATE_FAIL=1` makes the self-test fail only at its return value; `LEAD_REPIN_NO_META=1` skips the machinery checks that start the script again.
- **Settings (environment variables, all optional):** `TAKE_PY CRM_PY DRIVE_PY N8N_PY` (when not set, the script finds each file by name among files with at most 3 sub-folders below the test-program folder, prefers one in a `scripts/` folder, prints which file it used and any other with the same name), `FLOWS_DIR`, `MODEL_DIR`, `MODEL_SETTINGS`, `ONE_STORE`, `LEAD_REPIN_NO_STATUS`, `LEAD_REPIN_MAX_SECONDS`, `END_RE`, `MODEL_RE`, `DELETE_RE`.
- **MODEL_DIR.** The model program folder is not in this checkout. If you have it: `MODEL_DIR="/path/to/model-program-folder" sh "$S" "$T"`. Without it, the model side of Q27 a, b and c cannot be answered (the script says so).
- **How deep the search goes.** Files whose path has at most 4 parts below the folder are searched: `a/b/c/file` yes; `a/b/c/d/file` no. The script counts the left-out files by reason and prints the numbers.
- **Tested only here:** GNU sed 4.9, mawk 1.3.4, dash and bash on Linux. Not tested on busybox, macOS, WSL or Windows, and not against the real test program.

## Failures first (what this checklist cannot do)
1. A search finds text; it does not prove behaviour. "No delete call found" needs a second reader (G1). "Refusal exists" needs the refusal SHOWN (a test run or the startup refusal), not only a grep hit.
2. Q27 a is about run order. A grep prints line numbers; read the code around them. A call already sent before `end`, and an n8n retry or lease that fires a call after `end`, cannot be shown by reading: they need a run or a test shown at the final commit.
3. The default search words are the builder's guesses. Zero hits can mean "not there" or "wrong words". A block total line is a sum of several searches; read the per-search lines.
4. **By default the model program is NOT searched** (MODEL_DIR is empty). Then the model side of Q27 a and b, `qs_37` on the model side and Q27 c half B cannot be answered, so **Q27 c cannot be answered at all** without MODEL_DIR.
5. Block Q23-1 searches the four named files first, then every other python and shell file, then every flow json, and prints how many files each list left out and why: a path of 5 or more parts, symbolic links, folders find could not open, names with a line break, files inside `node_modules`, `_local`, `secrets`, `.venv`, `venv`, `__pycache__`, `tests`, `test`, and every file of another type. "0 matching lines" means "none in the files that were looked at". Flow files under `_local` are searched only for the delete words and printed as `file:line:word`, never the line.
6. An unreadable file is printed as `UNREADABLE (not searched, NOT zero matches)`. I ran v5 as the user `nobody` on a made-up folder with one unreadable file (`evidence-repin5/06-nonroot.txt`): exit code 0, no `Permission denied` text, block R00 counts it, and the run check prints `STOP-SIGNAL` lines. The v6 non-root run is in `evidence-repin6/`. Not seen on a real test folder.
7. Not covered by a read-only command, so not in the script: G2, G3, G5, G8, G9, G11 to G15 (except what the table names), G19, G21 permission names, G22 to G25, G27 to G32.
8. The hand commands below are not the script: they have no line cutting and fewer search words. They go through `--mask` (the same filter), but run the script when you can.
9. Windows listeners are not seen from WSL (the script says so when it detects WSL; check `netstat -ano` on Windows for 5678 and 5679).
10. Not tested: a run inside a real git work tree of the test program; WSL; macOS; Windows; busybox; any sed that is not GNU sed 4.9; any awk other than mawk 1.3.4.
11. The delete words are the pieces `delet`, `archiv`, `purg`, `remov`, `trash`, `gdpr`, `clean.?up`, `unlink`, `rmtree` and `method = delete or patch`; they also match harmless words such as `deleted_at`, so more lines print.
12. The masking lists in "Masking is a safety net" are lists: a case not named there can show. **A mask is not a replacement for reading.** If the real output holds a value that looks like a secret and is not masked, stop and tell the lead.

## How to type a hand command safely
Every hand command below uses `$S` and `$T` from the Quick start (set them in the same terminal), after `LC_ALL=C; export LC_ALL`. One file per command, so one wrong name cannot hide the others. The pattern is:

`{ grep -a -n -i -E 'WORDS' "$T/scripts/FILE.py"; echo "grep-exit-code=$?" >&2; } | sh "$S" --mask`

The line `grep-exit-code=0` means grep found lines, `1` found none, `2` means grep could not read the file (a wrong path or permission), which is **not** "none". That line goes to the error channel, so on the screen it can appear between masked lines. Git commands: `git --no-optional-locks -c core.fsmonitor=false -C "$T" rev-parse HEAD`.

## Items

### Q23: does the test program have any delete or archive path to the CRM (G1; also G21 and G17)
- **Question:** does any python or shell file of the test program (not tests), the CRM module or any flow json **call** something that deletes, archives, purges, removes or cleans up a contact? (See the disagreement above.)
- **Answer needed (ORDERS Q23):** the lead shows the final-commit search: yes or no, plus the line number of every hit, plus a named second reader (G1).
- **Blocks:** Q23-1 (search; counts of everything left out), Q23-2 (what stands at `run_real_check_n8n.py` lines 1045 to 1056 and `crm_hubspot.py` lines 500 to 512, printed with line numbers; says when the file is shorter), Q23-3 (HTTP methods in the CRM module), Q23-4 (delete wording the owner would read; G17), R00 (commit id and checksums; G26 asks for the checksum again just before the run).
- **Hand commands** (set `$S` and `$T` first; the flows folder is `$FLOWS`, set it with `FLOWS="/path/to/flows"`; if you do not know the flows folder, the last-but-two line **cannot be done with this guide: it needs the flows folder path from the lead; write "not done"**):
  - `git --no-optional-locks -c core.fsmonitor=false -C "$T" rev-parse HEAD`
  - `for f in run_real_check_n8n.py crm_hubspot.py n8n_drive.py n8n.py; do echo "== $f"; { grep -a -n -i -E 'DELETE|\.delete\(|archive|purge|remove|trash|gdpr|clean.?up|unlink|rmtree' "$T/scripts/$f"; echo "grep-exit-code=$?" >&2; } | sh "$S" --mask; done`
  - `{ grep -a -r -n -i -E 'DELETE|archive|purge|remove|trash' --include='*.json' --exclude-dir=node_modules --exclude-dir=_local --exclude-dir=secrets "$FLOWS"; echo "grep-exit-code=$?" >&2; } | sh "$S" --mask`
  - `{ sed -n '1045,1056p' "$T/scripts/run_real_check_n8n.py"; echo "sed-exit-code=$?" >&2; } | sh "$S" --mask`
  - `{ sed -n '500,512p' "$T/scripts/crm_hubspot.py"; echo "sed-exit-code=$?" >&2; } | sh "$S" --mask`
  - `{ grep -a -n -E '(^|[^A-Za-z_])(GET|POST|PUT|PATCH|DELETE)([^A-Za-z_]|$)|rows_with_prefix' "$T/scripts/crm_hubspot.py"; echo "grep-exit-code=$?" >&2; } | sh "$S" --mask`
  - `sha256sum "$T/scripts/run_real_check_n8n.py" "$T/scripts/crm_hubspot.py" "$T/scripts/n8n_drive.py" "$T/scripts/n8n.py"` (a file you cannot read is named in an error line: that file is **not** checked)
- **Expected shape:** Q23-1 prints either only comment, test or wording lines, or a real call line. Q23-2: "file is shorter than line N" means the old number is stale. Q23-3: GET and POST names, and `rows_with_prefix` as a GET.
- **What each outcome means (builder's reading; ORDERS Q23 governs; the lead replaces it where it differs):**
  - No call anywhere and a second reader agrees: G1 can be YES; decision 2 stands; the clean-up message may say "the test program made no delete call" (G27); AGENT-SCOPE line 20 stays marked stale.
  - A delete or archive call exists: decision 2 is false at this commit. The lead (or the owner) decides what follows. The sentence "the test program made no delete call" is not sent (ban-list item 10), and G21 (which permissions each HubSpot key has) reopens. The key is still not widened without the owner (ORDERS Q23).
  - Delete wording still printed (Q23-4): G17 fails; owner-sheet R5 then sends `n`; the wording in the numbers message must change.
  - Not shown: ORDERS gives no default; the lead decides (blank above).

### Q27 a: the test program never calls the model after the word `end` (G34). UNVERIFIED until the lead shows it.
- **Answer needed:** yes or no with line numbers. If a call can still follow, also what is printed and which exit code is left when the owner cancels the key right after `end`.
- **Block:** Q27a: part 1 lines handling `end` (case-sensitive, a quoted word or a constant; with 20 lines after each); part 2 every model-call line in the test program, `n8n_drive.py`, `n8n.py` and (if MODEL_DIR is set) the model program.
- **Hand commands:**
  - `{ grep -a -n -E "[\"']end[\"']" "$T/scripts/run_real_check_n8n.py"; echo "grep-exit-code=$?" >&2; } | sh "$S" --mask`
  - `{ grep -a -n -i -E 'anthropic|messages\.create|/v1/messages|model_program|call_model|post_model|post_lead|llm|complete\(|burst|/qualify|/control|urlopen|requests\.(get|post)|httpx|subprocess|Popen' "$T/scripts/run_real_check_n8n.py"; echo "grep-exit-code=$?" >&2; } | sh "$S" --mask`
  - Reading the code around the `end` branch: take the line number N of the `end` branch from the first command, then type (replace N with that number): `{ sed -n "$((N)),$((N+40))p" "$T/scripts/run_real_check_n8n.py"; echo "sed-exit-code=$?" >&2; } | sh "$S" --mask` (set `N=<number>` first).
  - The same two grep commands for the model program: **cannot be done with this guide: it needs the model program folder from the lead (it is not in this checkout); write "not done".**
- **Expected shape:** the `end` line number and the model-call line numbers. "Never" holds only if no model-call line can run after the `end` branch AND a run or test at the final commit shows no n8n retry or lease fires one.
- **Outcome (release note v8 G34, line 48):** shown "never": the numbers message says so with file, line and the test. Not shown: the numbers message says "exit code accepted then: none" (any other exit code is a FREEZE) and the owner sheet's cancel sentence stays. Fill G18's early-cancel line (line 38) from the same read.

### Q27 b: an end-date refusal exists and is SHOWN at the final commit (G16, G10). UNVERIFIED until the lead shows it.
- **Spend warning:** to see the refusal, **run only the named `qs_37` test, against the fake (recorded) model.** Do not start the real model program, or a real step with a real key, to "see" a refusal: the model program holds the real model key and a start could make a paid call. No paid call without the owner's yes and numbers.
- **The command that starts the `qs_37` test: cannot be done with this guide. It needs the exact test command from the lead (I did not see how the test is started). Write "not done" until the lead gives it.**
- **Answer needed:** yes or no with file and line, and the refusal SHOWN (the `qs_37` test, or the startup refusal read from a safe run, at the final commit). Also `need_seconds`.
- **Block:** Q27b: window-end words in the test program and (if MODEL_DIR is set) the model program; the test name `qs_37` in every python file including tests; lines of MODEL_SETTINGS whose name has the whole word end, window, deadline, until or not_after: **a value is shown only if it looks like a date or a number**; anything else is replaced by a note.
- **Hand commands:**
  - `{ grep -a -n -i -E 'window|end_date|not_after|deadline|need_seconds|2026-11-2|refus' "$T/scripts/run_real_check_n8n.py"; echo "grep-exit-code=$?" >&2; } | sh "$S" --mask`
  - `{ grep -a -r -n qs_37 --include='*.py' "$T"; echo "grep-exit-code=$?" >&2; } | sh "$S" --mask`
- **Expected shape:** a setting name and a comparison line; a test name. A grep hit alone is "exists", not "shown".
- **Outcome:** shown: the numbers message line reads "End-date refusal: shown" (I could not find this exact wording in release note v8; line 61 names the gate; the lead checks the wording). Not shown (default): "End-date refusal: NOT SHOWN" and the test stays on Wed 18 Nov (owner sheet v24-A line 62 already carries "NOT SHOWN"). Whether showing (b) alone makes Mon 23 Nov possible: the lead decides (blank above).

### Q27 c: the go marker before any model call (G33, line 47). UNVERIFIED until the lead shows it.
- **Answer needed:** yes or no with file and line in BOTH programs, plus a test at the final commit.
- **Block:** Q27c: half A (marker words in the test program) and half B (marker words in the model program folder; needs MODEL_DIR). A zero in either half means NOT SHOWN by that search.
- **Hand commands:**
  - Half A: `{ grep -a -n -i -E 'marker|\.used|go_file|accepted|challenge' "$T/scripts/run_real_check_n8n.py"; echo "grep-exit-code=$?" >&2; } | sh "$S" --mask`
  - Half B (the model program): **cannot be done with this guide: it needs the model program folder from the lead; write "not done".**
- **Expected shape:** the test program writes a marker after the accepted challenge; the model program tests for it before the first paid call. `~/.hadavin-take-tags/<id>.used` (AGENT-SCOPE) is the single-use tag marker made before the first post; it is not shown to be the same as the go marker.
- **Outcome:** shown: "Go marker: shown". Not shown (default): "Go marker: NOT SHOWN", the owner sheet's fallback wording applies and the owner's yes names it; no marker line at all means no run.

### Other gates the sheet leaves open, where a read can help
For each row, read the named block and write one answer-sheet line. "Default" is what the sheet says if nothing is shown.
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

## Appendix: test and evidence record (does not drive any decision)
- **v6 self-test:** `--self-test` passed=1191 failed=0 under dash and under bash; the short start check has 1167 cases. A run that passes a different number of cases is refused by two separate judges (new in v6).
- **The v6 cases run against the v5 filter:** 136 of 1164 cases fail (`evidence-repin6/selftest-v6-cases-against-v5.txt`): the new tests do fail on the old code.
- **The three forms the security review named (M1 to M3):** 13 of 13 made-up values showed in v5 (`evidence-repin6/baseline-v5-result.txt`); the v6 results are in `evidence-repin6/` (files named in `../v6-CHANGES.md`).
- **Timing (v6, measured):** the start check alone takes about 1.5 seconds. A single line of 1,000,000 characters printed through `--mask` took about 1.5 to 1.7 seconds in three runs (`evidence-repin6/timing-1mb.txt`), because a line is cut to 20000 characters before the filter reads it. The v5 figure was about 7 to 11 seconds; the independent v5 run measured 6.8 to 7.3 seconds.
- **Mutation check:** damaging the script one place at a time and running the self-test; the counts and the survivors, if any, are in `evidence-repin6/mutants-dash.txt` and `evidence-repin6/mutants-bash.txt` and are summarised in `../v6-CHANGES.md`. (v5: 14 damages under two shells, all caught; one earlier reading of mine, that damage m3 was harmless, was wrong.)
- **Not run:** busybox, macOS, WSL, Windows; the real test program.

## What I did not check
The real test program, flows and model program (none present); real output of any block; whether the default search words match the real names; the owner-sheet sentences beyond the lines quoted from the release note; whether release notes v9 to v11 and owner sheets v25-A to v27-A (newer files in `../steps-edits/`) still match every G and R number used above (I re-read only the rows I quote, in v8 and v24-A, on 16 Nov, and the G count and the lease line for this version); that every ORDERS line number is still current; macOS and Windows shells (only dash and bash on Linux, GNU sed 4.9, mawk); WSL; a run inside a real git work tree of the test program; whether this script prints something a real test program would reveal that the made-up tree does not. **Sources I could not open:** the real test program, the model program, the flows, `review-codebase-1.md` (quoted only through AGENT-SCOPE line 20), and the row BL-wp6-G1 of the studio's own list of open problems (not found in `core-hardening`).
