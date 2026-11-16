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
Always use full paths (below); a relative `--in` path depends on the folder you are standing in.

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
    install -m 600 /dev/null "$HOME/keep/flow-values.env"
    # now open "$HOME/keep/flow-values.env" in an editor and type the KEY=VALUE lines

## The commands
1. Fill (the output folder must not exist yet; it must be outside git, not under /mnt, and not
   inside the input folder):

       python3 -I "$TOOL" fill --in "$REPO/handover/demo/n8n-flows-real-v5" \
         --values "$HOME/keep/flow-values.env" --out "$HOME/keep/filled"

2. Check (read-only; run it on the filled folder). It must say `0 problem(s)` before you import.
   `--tokens-only` ignores placeholders. A folder with no `.json` file is an error.

       python3 -I "$TOOL" check "$HOME/keep/filled"

3. Delete when the take is over:

       python3 -I "$TOOL" delete --out "$HOME/keep/filled"

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
2. Put the three credential ids in the values file as `PG_CREDENTIAL_ID`, `SMTP_CREDENTIAL_ID`
   and (real only) `HS_CRED_PLACEHOLDER`, and the two mail addresses as `FROM_ADDRESS_PLACEHOLDER`
   and `INTAKE_ADDRESS_PLACEHOLDER` (real set; the film flows do not carry them). Leave
   `SUB_WORKFLOW_ID` out for now.
3. Fill into `"$HOME/keep/filled-1"`. It ends with exit code 3 and
   `NOT READY TO IMPORT: ... placeholders left` on the error screen. That is expected here (only
   `SUB_WORKFLOW_ID` is left).
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
| 0 | Done: for `fill`, the copy is written and no placeholder is left; for `check`, nothing wrong. |
| 1 | Refused, or `check` found problems (for example a placeholder is still there: `check` ends with 1 until every one is filled) (or the folder holds no `.json`). The message names the key, file or line, never a value. |
| 2 | The command was typed wrongly (missing option). |
| 3 | `fill` wrote the copy, but placeholders are left. `NOT READY TO IMPORT: N placeholders left` is printed on the error screen. Do not import this copy. |
| 4 | Nothing to fill: the input has no marker and no placeholder you gave a value for (probably already filled, or the wrong folder). Nothing is written. |

## What a refusal means and what to do
- "token sits outside a clean {{ }}", "inside a quoted JS string", "in a jsCode/functionCode/
  pythonCode field", "with a '/' outside a string", "holds a // or /* comment": a marker is in a
  place where a plain replacement could change the meaning or break the code. Edit that flow so
  the marker stands alone inside `{{ ... }}`, then fill again.
- "cannot fill these names": a key is missing or empty in the values file, or the name is not
  `DESK_*` / `MF_*`. Add it, or fix the flow.
- "values file ...": follow the message (chmod, move out of git or /mnt, remove quotes, etc.).
- "output ... already exists": delete the old output first (see above).
- "output folder is the input folder or inside it": choose another `--out`.

## If the run was killed or the fingerprint file is lost
- If a fill stopped half way (power cut, disk full), run `delete --out DIR` for that folder. A fill
  that fails by itself removes what it made (including a file cut in the middle).
- `delete` refuses a file whose content changed since it was written (you edited it, or a kill left
  it cut short). If you are sure, add `--force-hash`.
- If the fingerprint file is lost: `delete --out DIR --no-manifest`. It deletes only a folder that
  looks exactly like this program's output: the folder is mode 0700 and the files are mode 0600,
  all owned by you; every file is a plain `.json` file that reads as JSON and holds no `$env`
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
Files are mode 0600 and the folder 0700, created without following symlinks.

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

## What `delete --no-manifest` cannot tell
It has no fingerprint to compare with. If someone who already controls your account edits a
file of this program's output so that it is still valid JSON without `$env`, still mode 0600 and
yours, the folder is still deleted. This is accepted: that someone could delete the folder
anyway, and the command only removes files of this program's own kind inside a 0700 folder that
you named. Use the normal `delete` (with the fingerprint file) when you have it.

## Known limits (not fixed, by design)
- Someone who can already write inside the parent folder while this runs could swap a path between
  a check and its use. The folder is 0700 and the tool is meant for your own laptop; keep the
  parent folder private.
- The "inside a git folder" check looks for a `.git` entry in the folder or a parent. A bare
  repository (a git store with no `.git` entry) is not recognised; do not put the values file or
  the output in one.

## Tests
`python3 -I -m unittest` in this folder. They copy the real flows into a fresh temporary folder
(`FF_TEST_BASE` chooses where; `FF_DEMO_DIR` points at the flows). Values are made up and built
from parts. Every run of the program in the tests goes through one helper that fails the test if
any made-up value written by the tests appears in the screen output; the few tests that write a
values file by hand add their value to that list.
