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

## The values file
A plain text file with one `KEY=VALUE` per line. Example (all made up):

    # flow-values.env
    DESK_URL=http://127.0.0.1:9000
    DESK_TIMEOUT_MS=2500
    DESK_ALERT_TO=desk@example.invalid
    PG_CREDENTIAL_ID=made-up-credential-1

Rules: no quotes around a value (quotes are not removed, so they are refused); no space at the
start or end of a value; a ` #` inside a value is kept as part of the value (it is not a
comment; you get a warning); a value must not contain `{{` or `}}`; keys use A-Z, 0-9 and `_`;
a key may appear only once; save as plain UTF-8 with Unix line ends (no BOM).

Keep it OUTSIDE any git folder, NOT under `/mnt` (a Windows drive, where file permissions do
not protect it), and make it readable by you only: `chmod 600 flow-values.env`. The program
refuses a values file that breaks any of these.

## The three commands, in order
1. Fill (the output folder must not exist yet; it must also be outside git and not under /mnt):

       python3 -I fill_flows.py fill --in n8n-flows-real-v5 --values ~/keep/flow-values.env --out ~/keep/filled

   While placeholders remain, the last line says `NOT READY TO IMPORT: N placeholders left`.
   Create the credentials in n8n, import the sub-flow, put those ids in the values file, and run
   fill again into a NEW output folder (delete the old one first).
2. Check (read-only; run it on the filled folder):

       python3 -I fill_flows.py check ~/keep/filled

   It must say `0 problem(s)` before you import. `--tokens-only` ignores placeholders.
3. Delete when the take is over:

       python3 -I fill_flows.py delete --out ~/keep/filled

Do not move or rename the output folder: its list of file fingerprints (`filled.manifest.json`)
sits next to it, and `delete` finds it by that name.

## Exit codes (what the number means)
- 0: done, or the check found nothing wrong.
- 1: refused, or the check found problems. The message names the key, file or line, never a value.
- 2: the command was typed wrongly (missing option).
- 4: nothing to fill: the input has no marker and no placeholder you gave a value for (it is
  probably already filled, or the wrong folder). Nothing is written.

## What a refusal means and what to do
- "token sits outside a clean {{ }}", "inside a quoted JS string", "in a jsCode/functionCode/
  pythonCode field": a marker is in a place where a plain replacement would change the meaning
  or break the code. Edit that flow so the marker stands alone inside `{{ ... }}`, then fill again.
- "cannot fill these names": a key is missing or empty in the values file, or the name is not
  `DESK_*` / `MF_*`. Add it, or fix the flow.
- "values file ...": follow the message (chmod, move out of git or /mnt, remove quotes, etc.).
- "output ... already exists": delete the old output first (see below).
- If a fill stopped half way (power cut, disk full), run `delete` for that folder. If the
  fingerprint file is lost, `delete --out DIR --no-manifest` removes the folder, but only when
  it holds nothing except plain `.json` files.

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

## Known limit (not fixed, by design)
Someone who can already write inside the parent folder while this runs could swap a path between
a check and its use. The folder is 0700 and the tool is meant for your own laptop; keep the
parent folder private.

## Tests
`python3 -I -m unittest` in this folder. They copy the real flows into a fresh temporary folder
(`FF_TEST_BASE` chooses where; `FF_DEMO_DIR` points at the flows). Values are made up and built
from parts; every test checks that no value reaches the screen output.
