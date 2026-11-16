# fill_flows (item F3)

Tool-ladder line: rung 7 (our own small code); no n8n node writes a filled copy of flow files.
Python standard library only. Nothing here talks to a network or to n8n.

## What it does
Takes a local COPY of the flow JSON files (film-v5 or real-v5) and a values file, and writes a
filled copy in which every `$env.DESK_*` / `$env.MF_*` token inside a node is replaced by the
literal value. The take then imports the filled copy, so n8n no longer needs to read
environment variables inside nodes (finding F-037).

## Commands
    python3 -I fill_flows.py fill   --in DIR --values FILE --out NEWDIR
    python3 -I fill_flows.py check  DIR [--tokens-only]
    python3 -I fill_flows.py delete --out NEWDIR [--force-hash]

Values file: one `KEY=VALUE` per line; blank lines and lines starting with `#` are skipped; no
quotes are stripped; keys are A-Z, 0-9, `_`; a key twice is refused. Use Unix line ends.

## Rules (each one is tested)
- Which tokens: `$env.NAME`, `$env['NAME']`, `$env["NAME"]` (spaces allowed), also inside
  longer expressions. Only names `DESK_*` and `MF_*` are filled. Any other `$env` use (another
  name, or a dynamic form such as `$env[x]`) is a leftover and is refused.
- How a value sits in the text: parsed JSON is walked, never string-hacked, so quotes and
  backslashes cannot break the file.
  - Plain field (text not starting with `=`): the raw value.
  - Expression (text starting with `=`): inside a `{{ ... }}` part the value becomes a JS
    double-quoted string literal (`"..."`, non-ASCII as `\uXXXX`, `{` and `}` as `{` and
    `}`, so a value holding `}}` cannot end the expression early). Outside `{{ }}`: raw
    text. So `Number($env.DESK_TIMEOUT_MS || 10000)` becomes `Number("2500" || 10000)`; a number
    in the values file is therefore a string at run time, and the existing `Number(...)` makes
    it a number. If a new node uses a value as a bare number, wrap it in `Number(...)` too.
- Refuses (exit 1, the message names the KEY, file or line number, never a value): a needed key
  missing or empty; a value with a control, line-break or format character (CRLF files count)
  or containing `$env`; a token left over; input not valid JSON; a symlink in the input.
- Unused keys in the values file: warning with the key name only, exit stays 0.
- Output: must not exist, must not sit inside a git repository (a parent folder with `.git`,
  checked on the real path), parent folder must exist. Folder 0700, files 0600, created with
  O_EXCL and no symlink following. All output is built in memory first; on a write failure the
  partly written output is removed. Output is JSON re-printed with 2-space indent (the format
  of the input files is not kept byte for byte; node count and connections are checked equal).
- Manifest: `NEWDIR.manifest.json` beside the output (not inside it): file names and sha256 of
  the OUTPUT files only. Never values.
- Idempotent: same input and same values give byte-identical files and manifest. Running
  `fill` on an already filled copy finds no token and exits 4 ("nothing to fill"), writes
  nothing. Running into an existing output refuses (exit 1).
- `check`: read-only; lists leftover tokens and the placeholders `PLACEHOLDER`,
  `SUB_WORKFLOW_ID`, `PG_CREDENTIAL_ID`, `SMTP_CREDENTIAL_ID` by file and count (F-029 wants 0
  after import). Exit 1 if any are found, 0 if clean. `--tokens-only` ignores placeholders.
  `fill` does NOT fill placeholders (they are filled by the later import/credential step); it
  prints how many remain.
- `delete`: reads the manifest; refuses (nothing removed) if the manifest is missing or
  malformed, names anything but a plain file name, the folder or a file is a symlink, the
  folder holds a file not in the manifest, or a file's hash changed (unless `--force-hash`;
  that skips only the hash check, never the symlink or not-in-manifest checks). Then removes
  the files, the folder and the manifest.

## Exit codes
0 done / clean; 1 refused or problems found; 2 command-line mistake; 4 nothing to fill.

## Tests
`python3 -m unittest -v` in this folder (copies the real flows into `/tmp/ff13`, override with
`FF_TEST_BASE`; `FF_DEMO_DIR` overrides the flows location). Values are made up and built from
parts. A canary value is checked never to appear in stdout, stderr or the manifest.
