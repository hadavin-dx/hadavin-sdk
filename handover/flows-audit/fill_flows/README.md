# fill_flows (item F3)

## What it is
A small helper program. The n8n flow files in the demo folders contain short markers such as
`$env.DESK_URL` (a web address) that n8n cannot read when it runs a flow. This program makes a
COPY of the flow files in which each marker is replaced by the real value you give it. You then
import the copy into n8n. Your original files are never changed.

It also fills six "placeholder" names (`PG_CREDENTIAL_ID`, `SMTP_CREDENTIAL_ID`,
`SUB_WORKFLOW_ID`, `HS_CRED_PLACEHOLDER`, `FROM_ADDRESS_PLACEHOLDER`,
`INTAKE_ADDRESS_PLACEHOLDER`) once you know their values.

It uses only Python's standard library, talks to no network, and never prints a value.
(Ladder line: our own small code; no ready-made n8n step writes a filled copy of flow files.)

## Where it runs
Linux, macOS, or WSL (Windows Subsystem for Linux) using the Linux home folder (for example
`/home/you/keep`), NOT `/mnt/c/...` (a Windows drive, where file permissions do not protect
anything). Native Windows is not supported: the program checks this when it starts and refuses
with a plain message if the system cannot open files without following symlinks.
Python 3.11 or newer: the program refuses to start on an older Python. The tests were run on
3.11, 3.12 and 3.13 (all three, last run recorded in `fix-f3-r8.md`); no older version and no
Mac was ever run. Always use full paths (below); a relative `--in` path depends on the folder
you are standing in.

## The values file
A plain text file with one `KEY=VALUE` per line. Use only the keys of the flow set you are filling
(other keys only give a "not used" warning):

| Flow folder | Keys it reads |
|---|---|
| `n8n-flows-real-v5` | `DESK_URL`, `DESK_TIMEOUT_MS`, `DESK_ALERT_TO` |
| `n8n-flows-film-v5` | `MF_STAGE_URL`, `MF_STAGE_TIMEOUT_MS`, `MF_CRM_URL` |

and, for either set, the six placeholder names once you know them (see the walk-through).
Example (all made up):

    # flow-values.env
    DESK_URL=http://127.0.0.1:9000
    DESK_TIMEOUT_MS=2500
    DESK_ALERT_TO=desk@example.invalid
    PG_CREDENTIAL_ID=made-up-credential-1

Rules: no quotes around a value (quotes are not removed, so they are refused); no space at the
start or end of a value; a value must not start with `=` (n8n would read the field as an
expression); keys ending `_MS` take digits only (milliseconds); a ` #` inside a value is kept as
part of the value (it is not a comment; you get a warning); a trailing `/` on a `*_URL` value gets
a warning (the flows add their own `/path`); a value must not contain `{{` or `}}`; keys use
A-Z, 0-9 and `_`; a key may appear only once; save as plain UTF-8 with Unix line ends (no BOM).

Keep it OUTSIDE any git folder, NOT under `/mnt`, and make it readable by you only
(`chmod 600`). The program refuses a values file that breaks any of these.

## Copy-paste setup (change the first line only)

    REPO=/full/path/to/hadavin-sdk
    TOOL="$REPO/handover/flows-audit/fill_flows/fill_flows.py"
    mkdir -p -m 700 "$HOME/keep"
    (umask 077; : > "$HOME/keep/flow-values.env")
    # now open "$HOME/keep/flow-values.env" in an editor and type the KEY=VALUE lines

## The commands
1. Fill (the output folder must not exist yet; it must be outside git, not under /mnt, and not
   inside the input folder):

       python3 -I "$TOOL" fill --in "$REPO/handover/demo/n8n-flows-real-v5" \
         --values "$HOME/keep/flow-values.env" --out "$HOME/keep/filled"

   Always join the next step to this one with `&&` (for example `fill ... && import ...`), never
   with `;`. If the values file has no value for a placeholder name, `fill` refuses by default
   (exit 1, nothing written). Add `--allow-placeholders` only for the credential walk-through
   below: it then writes a copy and ends with code 3, so the `&&` still stops and nothing is
   imported. That copy is also marked: the folder then holds a file
   `NOT-READY-DO-NOT-IMPORT.txt`, and `check` reports it as a problem. (Limit: a program that
   imports every file of a folder without being asked by a `&&` still sees the flow files; the
   note file and the exit code are the guards, not the file format.)

2. Check (read-only; run it on the filled folder). It must say `0 problem(s)` before you import.
   `--tokens-only` does not list placeholder names (it prints "placeholders: not checked"), but a
   copy that is marked NOT READY is still refused. A folder with no `.json` file is an error (if
   the not-ready note is there, the message names it). `check` always prints one line saying
   whether the comparison with the fingerprint file (`NAME.manifest.json`) ran. When that file
   sits next to the folder, a missing file, an extra file (any kind: also `.DS_Store`) or a
   changed file is a problem. A folder that carries this program's marker file
   (`.fill_flows-output`) but has NO fingerprint file next to it (a copied or moved folder) is a
   problem too, as is a marker that names another folder, and a folder or file that is no longer
   private (mode 0700 for the folder, 0600 for the files, yours): `cp -r` can loosen them.
   A folder with NO marker file and NO fingerprint file next to it is a problem as well: it is
   not shown to be a copy that `fill` made. This is what a copy made with `cp -r filled/*`, a zip
   or an rsync that skips hidden files looks like (the marker file starts with a dot), and also
   what an input folder looks like. `check` also reports as a problem: a folder that sits inside
   a git repository, inside a cloud-synced or backed-up folder, or on `/mnt` (the same places
   `fill` refuses); a file that has a second name (a hard link: the other name would not be
   removed by `delete`); and a fingerprint file that says the copy was written with placeholders
   left (`fill` writes a `ready` flag into it), even when the note file was deleted afterwards or
   `--tokens-only` is used. Do not copy a filled folder to import it: import from the folder
   `fill` made.

       python3 -I "$TOOL" check "$HOME/keep/filled"

3. Delete when the take is over (running it a second time, or on a name with nothing there, is
   not an error: it says "nothing to delete" and ends with 0):

       python3 -I "$TOOL" delete --out "$HOME/keep/filled"

   A stray file that the fingerprint file does not list (macOS `.DS_Store`, an editor's `.swp`
   file) stops the delete and is named. Add `--remove-others` to remove stray plain files that
   are yours; a folder, a link or a file of another user still stops it. If the folder cannot be
   removed at the end (a file appeared while it ran), the message says `folder left behind`,
   names what is in it, and the fingerprint file stays (when there is one): run delete again.

Do not move or rename the output folder: its list of file fingerprints (`filled.manifest.json`)
sits next to it, and `delete` finds it by that name.

## Walk-through: credentials and the sub-flow (first time only)
The six placeholder names stand for ids that exist only inside your n8n. Which flow file is which:
`mf-sub-crm-mail.json` is the sub-flow (n8n name "Lead desk main frame: CRM + mail
(sub-workflow)"); the other three files (`mf-form.json`, `mf-hook.json`, `mf-recovery.json`) call
it by id (placeholder `SUB_WORKFLOW_ID`). Do the steps in this order:

1. In n8n, create the credentials by these names (the flow files use the names): `n8n-publish-pg`
   (Postgres), `mf-mail-smtp` (SMTP mail) and, for `n8n-flows-real-v5` only, `hubspot-app-token`
   (HubSpot). The flows' own notes name the credentials but do not say where n8n shows their ids:
   check on your n8n (usually the id is in the address bar when you open the credential).
   ORDER 037 (lead, 2026-11-16): there is ONE filled flow set, and `hubspot-app-token` holds the real
   trial-account credential in every phase. There is no stand-in HubSpot credential and no refill
   with a real one later (any older text saying so is superseded by ORDER 037). The partial
   fill in steps 3 to 6 is only about the sub-flow id (`SUB_WORKFLOW_ID`), not about a credential.
   Whether the take repo's runbook already matches this at its final head is UNVERIFIED.
2. Put the three credential ids in the values file as `PG_CREDENTIAL_ID`, `SMTP_CREDENTIAL_ID`
   and (real only) `HS_CRED_PLACEHOLDER`, and the two mail addresses as `FROM_ADDRESS_PLACEHOLDER`
   and `INTAKE_ADDRESS_PLACEHOLDER` (real set; the film flows do not carry them). Leave
   `SUB_WORKFLOW_ID` out for now.
3. Fill into `"$HOME/keep/filled-1"` with `--allow-placeholders`. It ends with exit code 3 and
   `NOT READY TO IMPORT: ... placeholders left` on the error screen. That is expected here (only
   `SUB_WORKFLOW_ID` is left; the folder holds the `NOT-READY-DO-NOT-IMPORT.txt` note, and you
   import only the one file named in step 4).
4. In n8n, import ONLY `filled-1/mf-sub-crm-mail.json`. Open the imported workflow and read its id
   (check on your n8n: usually the address bar of the open workflow ends in the id).
5. Add `SUB_WORKFLOW_ID=<that id>` to the values file. Run `delete --out "$HOME/keep/filled-1"`.
6. Fill again into `"$HOME/keep/filled"`. This time it must end with exit code 0 and
   `no placeholders left`. Run `check` on it: `0 problem(s)`.
7. Import `mf-form.json`, `mf-hook.json` and `mf-recovery.json` from `filled`. If you also
   imported `mf-sub-crm-mail.json` from `filled`, n8n now holds a second copy of the sub-flow:
   delete the copy whose id is NOT the one you typed as `SUB_WORKFLOW_ID` (the other flows call
   that id; deleting it would break them). Never keep two copies.

## Exit codes (what the number means)
| Code | Meaning |
|---|---|
| 0 | Done: for `fill`, the copy is written and no placeholder is left; for `check`, nothing wrong; for `delete`, deleted or nothing was there. |
| 1 | Refused, or `check` found problems (for example a placeholder is still there: `check` ends with 1 until every one is filled) (or the folder holds no `.json`). The message names the key, file or line, never a value. |
| 2 | The command was typed wrongly (missing option). |
| 130 | Stopped with Ctrl-C. The clean-up of a fill ran first; one plain line says so. |
| 3 | `fill --allow-placeholders` wrote the copy, but placeholders are left (without the flag `fill` refuses with 1). `NOT READY TO IMPORT: N placeholders left` is printed on the error screen and the folder holds `NOT-READY-DO-NOT-IMPORT.txt`. Do not import this copy. |
| 4 | Nothing to fill: the input has no marker and no placeholder you gave a value for (probably already filled, or the wrong folder). Nothing is written. |

## What a refusal means and what to do
- "token sits outside a clean {{ }}", "inside a quoted JS string", "in a jsCode/functionCode/
  pythonCode field", "with a '/' outside a string", "holds a // or /* comment": a marker is in a
  place where a plain replacement could change the meaning or break the code. Edit that flow so
  the marker stands alone inside `{{ ... }}`, then fill again.
- "a backtick or '${' (a template string)": a marker sits in an expression that holds a template
  string (text between backticks); a plain replacement could end up inside it. Edit the flow.
- "a plain text ... plain fields are filled only in: url, toEmail, ...": a marker sits in a text
  that does not start with `=` and is not one of the listed address fields (n8n does not read such
  a text as an expression, so the marker would stay literal text). The real v5 flows have no
  such marker (the test `test_real_flows_hold_no_plain_token` counts them); every marker there is
  inside an `={{ }}` expression.
- "the name holds a path or control character": an input file name (or the output folder name)
  has a backslash, a control character or another look-alike character; rename it.
- "cannot fill these names": a key is missing or empty in the values file, or the name is not
  `DESK_*` / `MF_*`. Add it, or fix the flow. (An empty value for one of the six placeholder
  names is treated as no value: the name stays and the copy is NOT READY.)
- "a $env token follows a name character or a dot": the marker is glued to another name (such as
  `a$env.X` or `x.$env.X`), so it is not the n8n `$env`; it is not filled. Edit the flow.
- "inside a cloud-synced or backed-up folder": the values file or the output sits under a folder
  named like Dropbox, OneDrive, iCloud Drive, Google Drive and similar; those programs copy it
  elsewhere. Use a plain folder such as `$HOME/keep`.
- "larger than N bytes": a flow file or fingerprint file over 32 MB, or a values file over 1 MB,
  is refused instead of read into memory.
- "values file ...": follow the message (chmod, move out of git or /mnt, remove quotes, etc.).
- "output ... already exists": delete the old output first (see above).
- "output folder is the input folder or inside it": choose another `--out`.

## If the run was killed or the fingerprint file is lost
- If a fill stopped half way (power cut, disk full), run `delete --out DIR` for that folder. A fill
  that fails by itself removes what it made (including a file cut in the middle). A Ctrl-C during
  a fill is held back while a file or the folder is being made and noted, so it leaves nothing
  behind either; so are the signals terminate (SIGTERM) and hang-up (SIGHUP): the fill cleans up
  and ends with code 1 (the clean-up itself is shielded from a second signal). These three
  signals (SIGINT, SIGTERM, SIGHUP) are the ones handled. A stop by any other signal (SIGKILL,
  SIGQUIT, SIGUSR1, SIGALRM, SIGXCPU and so on) or a power cut can leave a partial copy; the note
  `NOT-READY-DO-NOT-IMPORT.txt` is written first and removed last, so such a copy is still
  marked and `check` refuses it. It can also leave the manifest cut
  short with no folder: the next `fill` then says the manifest exists; run
  `delete --out DIR --force-hash` (it removes a cut or empty manifest when no folder exists; it
  still refuses a link, and a manifest that is not yours).
- `delete` refuses a file whose content changed since it was written (you edited it, or a kill left
  it cut short). If you are sure, add `--force-hash`.
- If the fingerprint file is lost: `delete --out DIR --no-manifest`. It does not touch a
  fingerprint file that sits next to the folder unless that file is a valid manifest (then it is
  removed with the folder); an invalid one makes it refuse, nothing deleted, and with
  `--force-hash` it is removed too. When a valid manifest exists, the folder must hold nothing
  beyond what it lists (otherwise nothing is deleted). It removes only the marker, the
  not-ready note and `.json` files that look like this program's output, and takes the note and
  the marker last, so a delete cut short leaves a folder that is still marked. It deletes only a folder that
  looks exactly like this program's output: the folder holds the small marker file
  `.fill_flows-output` (and, when placeholders were left, the note `NOT-READY-DO-NOT-IMPORT.txt`
  with its exact text) that `fill` writes first (right format and this folder's name), the folder
  is mode 0700 and the files are mode 0600, all owned by you; every file is a plain `.json` file that reads as JSON and holds no `$env`
  text. Anything else is refused and nothing is deleted. A file cut short by a kill is not valid
  JSON: add `--force-hash` to skip the JSON and `$env` reading (the mode, owner and name
  checks stay).

## How a value is placed
The JSON is read and rewritten as JSON, never edited as raw text, so quotes and backslashes
cannot break a file. In a plain field the raw value is used. Inside `{{ ... }}` of an expression
(text starting with `=`) the value becomes a quoted string: `Number($env.DESK_TIMEOUT_MS || 10000)`
becomes `Number("2500" || 10000)`. A new node that needs a bare number must wrap it in
`Number(...)`. Placeholder names are replaced only when the whole text equals the name.
The output files are re-printed with 2-space indent (layout may differ from the input; node
count and connections are checked equal). Same input and same values give identical files.
Files are mode 0600 and the folder 0700. The program opens the output folder once and creates,
reads and deletes everything through that open folder, so swapping the folder name for a link
while it runs changes nothing. It also reads the mode back from each new file and folder and
refuses (removing what it made) if the disk did not keep it private, instead of guessing from
the path. The first folder in the output path is looked up by name once; a link there is accepted
only when you or root made it. The git and `/mnt` checks are made on the typed path first and
then again on the place the OPEN folder (and the open values file) really is in, asked of the
open handle (Linux: `/proc/self/fd`; macOS: `F_GETPATH`), so a link swapped in between the check
and the open is caught. On another system the second check falls back to the typed path and the program prints one
warning line saying so. `delete` makes the same place check but only warns (it still removes the
copy: leaving it would be worse), and it warns about a file with a second name. Option names
must be typed in full (`--force-hash`, not `--force`): an abbreviation is refused with code 2.
`delete` also refuses an `--out` whose last part is empty or is not a plain file name (for
example `/`).
A plain text is filled only in the address fields `url`, `toEmail`, `fromEmail`, `ccEmail` and
`bccEmail` (the list `PLAIN_KEYS` in the program); a number that is too large for JSON (such as
`1e999`) is refused instead of being written as `Infinity`; the output files are flushed to disk.

## Clean-up checklist (after the take)
1. `delete --out DIR` (removes the filled files, the folder and the fingerprint file).
2. Remove the values file.
3. In n8n: remove the imported workflows and the saved executions (executions can hold the values).
4. Remember: deleting a file is not a secure wipe; the bytes may stay on the disk. Treat any value
   that mattered as exposed and replace it (use made-up or throwaway values for demos).

## Folders that are links (symlinks) in the output path
- The output folder itself and the fingerprint file must not be links (refused).
- A link in the folders above it is accepted when you or root made it (for example `/tmp` on a
  Mac). The real place it leads to is still checked for `/mnt` and for git. A link made by another
  user is refused for `fill` and `delete`, because it could send your files somewhere you did not
  choose.

## Limits to know
- A `$env` name written with a JavaScript escape (for example `\u0024env`) is refused, but how
  n8n itself reads such an escape was not tested; refusing is the safe side. A name built at run
  time (for example `this["$"+"env"]`) cannot be found by reading the text at all (that is
  impossible in general); it is not filled, so it simply stays and n8n handles it when the flow
  runs. The flows are your own; do not fill flows from a source you do not trust.
- The cloud-sync check goes by folder names. It cannot see a backup program (Time Machine, a
  disk image tool) that copies a normal folder: keep the output folder out of every backup and
  delete it after the take; after a backup ran, treat the values as exposed.
- A key of a JSON object that equals one of the six placeholder names is replaced like a text
  that equals it (the flows have none; two keys that become one are refused).
- The fingerprint file sits next to the folder and holds SHA-256 fingerprints of the whole filled
  files. A short, guessable value could be tested offline against them. The statement "no extra
  exposure" is true only while the manifest and the folder stay together; do not send the
  manifest alone anywhere.
- The values file must be owned by you (and mode 0600).
- Stop signals (Ctrl-C, terminate, hang-up) are held back for the few lines that create the
  folder and for the whole removal in `delete` (a few small files). A signal that comes in then
  is acted on right after; if the removal had already finished, `delete` says so and ends with 0.

## What `delete --no-manifest` cannot tell
It has no fingerprint to compare with. If someone who already controls your account edits a
file of this program's output so that it is still valid JSON without `$env`, still mode 0600 and
yours, the folder is still deleted. This is accepted: that someone could delete the folder
anyway, and the command only removes files of this program's own kind inside a 0700 folder that
you named. Use the normal `delete` (with the fingerprint file) when you have it.

## Other facts
- A placeholder name inside a longer text (for example `x PG_CREDENTIAL_ID y`) is counted as
  "left" but cannot be filled (only a text that equals the name is replaced), so `fill` ends with
  exit code 3 until the flow is edited. A placeholder name alone in a program-code field is refused.
- The fingerprint file holds a SHA-256 of each filled file. Someone who can read it can read the
  filled files too (same owner, same mode 0600), so it adds no new exposure; but do not copy it
  anywhere the filled files must not go.

## Known limits
- The "inside a git folder" check looks for a `.git` entry in the folder or a parent. A bare
  repository (a git store with no `.git` entry) is not recognised; do not put the values file or
  the output in one.

## Tests
`python3 -I -m unittest` in this folder (the tests start child programs through `asyncio`'s
process calls, with fixed argument lists and made-up files only). They copy the real flows into a fresh temporary folder
(`FF_TEST_BASE` chooses where; `FF_DEMO_DIR` points at the flows). Values are made up and built
from parts. Every run of the program in the tests goes through one helper that fails the test if
any made-up value written by the tests appears in the screen output, also in its escaped forms
(JSON, Python literal); every test that writes a values file by hand does it through `write_raw`,
which adds the value to that list. One test needs `node` (a JavaScript engine) and is skipped when
it is not installed.
