# Ticket G4 v2: P1c redactor gaps (base64 view, whole host names, bare numbers written down)

Version 2, written by the core-c drafter (opus tier), 2026-11-20. It replaces tickets/G4-P1c-redactor-gaps.md (v1) and resolves
plan review round 1 (tickets/G4-review-1.md). A builder with no other context builds from this file alone.
Why this file is over 250 lines: the review asked for zero-decision decode rules, exact regex pieces, per-row expected
results for 186 probe rows and a mutant list. Each of those is a table here. Nothing is built before plan review round 2 is clean.

## 0. Package line
- Package: G4 (plan item P1c, ORDER 006 item 1). Path class: redaction. Extended review: yes (no round cap).
- Lead rule (unchanged): build only a gap that a failing input proves. A gap with no failing input is cut.
- Depends on, merged first, in this order (decision D1, section 2): G0 (`runmap.enforce_map`; `is_masked` is deleted by
  lead order m7), the integration of P1d-a + P2d-1 fold scan + G7 (cloud/core-c merge d95a727), then G7 fix round 2
  (ORDER 020 MJ-B: the capped fixed-point loop `_Redactor.settle` with `_SETTLE_ROUNDS` = 4 and `RedactionError("NotSettled")`;
  it is being built in the working tree now). G4 starts from the first commit that holds MJ-B. Record its sha in the evidence.
- Source of the code: our own (rung 5), with Python stdlib `base64` as the decoder. Nothing is copied from another repository.
- Target: `src/hadavin_sdk/guard/runmap.py` (base64 step), `src/hadavin_sdk/guard/redact.py` (kind ENCODED, host-name
  patterns, docstring), `src/hadavin_sdk/defaults.py` (6 constants, SPINE's file, its own commit).

## 1. Problem in plain words
A secret that is only written in base64 reaches the model today: the redactor has no decoded view. Short base64 blobs
(under 40 characters) pass unchanged, alone, in a sentence, in JSON, after `data=`. Wrapped base64 passes when the lines
are short, or leaves its last line readable. Long unbroken blobs are already masked whole by HIGHENTROPY.
A private host name is masked only up to its private suffix: `db01.corp.example` becomes `<HOSTNAME_1>.example`.
A bare host label after `host`, an underscore label, a non-ASCII label and `[.]` dots are not masked at all.
Bare numbers without a label are not masked. That is an accepted decision (order 64 item 4); it is written down and pinned.

### What the probe proved (evidence/P1c-probe.md, script evidence/p1c_probe.py, clean export of main 51c9fc4, seed 20261120)
| gap | rows | leaked today | v2 result (prototype, section 9) |
|---|---|---|---|
| 1 base64 (1b 128 + 1c 14) | 142 | 52 | 52 closed; 85 unchanged; 5 change kind HIGHENTROPY to ENCODED (no leak before or after) |
| 2 host names | 44 | 28 | 21 closed; 3 stay (stated limits: rows 10, 15, 16); 4 kept on purpose (rows 6, 8, 9, 42); 16 already masked stay |
| 3 bare numbers | 43 | 24 not masked, 2 in part | not a gap: written down and pinned by class |
| 4 hostile corpus | - | - | CUT: the old 30-row corpus is not in this repository |

Drafter's prototype (not committed, scratch only): the rules of sections 3 to 6 were coded against a clean export of main
51c9fc4 (in-process, nothing in the repository changed) and run over the 229 probe rows built by the probe's own builders.
Results are quoted where used and marked "prototype". The builder re-measures everything on the G4 base commit.

## 2. Decision D1: order of work and where the base64 step plugs in
Order: G0, then the integration with G7, then MJ-B, then G4. Reason: G4 edits `redact_text` in runmap.py and the label
registry and the pattern table in redact.py; MJ-B edits `_Redactor.settle` in the same file. Building G4 first would put
two open builders on one function family.

Where: inside `runmap.redact_text`, which holds the scan inline on cloud/core-c (the `_scan` helper of G0 was folded back
when `is_masked` was deleted). If the base commit has a helper `_scan` again, the same change goes into that helper.
The two calls `redact(text, ...)` (the input) and `redact(view, ...)` (each view) are each replaced by one call of a new
private helper `_redact_encoded(text, mapping, cache, deadline, neutralise, depth, budget)`. Everything else in
`redact_text` (caps, `_clean`, `neutralise`, `_views`, `_decoded_masks`, `_keep_earlier_masks`, the view rule
`again.mapping != current or _held(again.text) > _held(out)`, the final `_clean`, the `mapping.update`) stays as it is.

`_redact_encoded` does, in this order (the "base64 step"):
1. `first = redact(text, mapping=mapping, _cache=cache, _deadline=deadline)`: pass 1 exactly as today (with G7/MJ-B settle).
2. Gate (separate from the `scan` flag): if `_B64_RUN.search(text)` is None, return `first`. Nothing else runs.
3. Find the units of `text` (section 3.1). Drop every unit that is HELD by `first` (section 3.3). Drop every unit
   that does not decode to text (section 3.2). If none is left, return `first` (byte-identical to today).
4. Decide the hits with ONE decoded view: the decoded texts are joined into one text and scanned once, recursively,
   with `depth + 1` (section 3.4).
5. No hit: return `first`. The decoded scan's map is thrown away.
6. Hits: take the decoded scan's map (the incoming `mapping` plus what the decoded texts held), call
   `redact.place_encoded(that_map, [unit text as written, ...])`, write each placeholder over its unit IN `text`
   (the cleaned and neutralised input, or the neutralised view), giving `text2`.
7. `return redact(text2, mapping=that_map, _cache=cache, _deadline=deadline)`: pass 1 runs again on `text2`.
   This is how the replacement reaches `out`: `out` is pass 1 of a text in which the blob already is a placeholder.
   Nothing is mapped back by position. Pass 1 leaves a placeholder alone, so the result holds `<ENCODED_n>` where the
   blob stood. The first pass's map additions are not kept (they would hold junk such as one HIGHENTROPY entry per
   wrapped line of a blob that is now one ENCODED).

`redact_text` then computes the views from the text pass 1 finally saw (`text2`, or `text` when nothing was replaced)
and runs the view loop with `_redact_encoded` in place of `redact`. A blob that is readable only in a view (JSON `\/`
slashes, `%3D` padding) is decoded there (prototype: both closed). In a view, a unit already masked at the text level
is swept by pass 1 (ENCODED is a secret kind of 4 or more characters, swept in every copy), so it is HELD and not decoded again.

Option not taken (the reviewers' first proposal): decode on the input BEFORE pass 1 and replace every unit that decodes
to something. Simpler (one pass 1), but every blob HIGHENTROPY, BASIC or JWT holds whole today would change kind, and a
JWT whose payload holds an e-mail address would be cut into ENCODED segments with its signature left to HIGHENTROPY. It
gives up the "nothing changes for what pass 1 already holds" invariant (I3) and changes existing JWT, BASIC and
HIGHENTROPY tests. The chosen design pays one extra pass 1 only on a text that has a hit.

## 3. G4a: the base64 rules (zero decision)
### 3.1 Units
Alphabet `_B64_CHARS = "A-Za-z0-9+/_\-"`. One `=`, two `=` or none may end a run.
1. RUN: `_B64_RUN = re.compile(r"(?<![A-Za-z0-9+/_\-])[A-Za-z0-9+/_\-]{12,}={0,2}(?![A-Za-z0-9+/_\-=])")`, with the
   minimum taken from `defaults.B64_MIN_CHARS` (12, padding not counted). A `=` BEFORE a run is allowed (`data=<b64>`,
   `key=<b64>`): the look-behind excludes the alphabet only. (Prototype: excluding `=` too left all 7 `data=` rows open.)
2. WRAPPED BLOCK: two or more consecutive lines (split on `\n`; a trailing `\r` and spaces or tabs at both ends of a line
   are ignored) where each line is exactly one run of the alphabet, the first line is at least 16 characters long and
   its length is a multiple of 4, every line but the last has the first line's length and no `=`, and the last line is
   no longer than the first (it may end in `=` or `==`). Lines are scanned once, top to bottom; each line belongs to at
   most one block (the block is maximal: it ends at the first line that breaks a rule, that line included if it is a
   valid shorter last line). Linear in the text: the builder must not test every window of lines, nor scan the list of
   blocks once per run (prototype: a per-run scan of the block list made a 262,000-character text 35 percent slower; an
   index set of taken lines fixed it).
3. A unit is a block, or a RUN that does not start inside a block. The unit's text AS WRITTEN is the stretch of `text`
   from its first to its last character (for a block: its lines and the line breaks between them).
4. Offset 0 only. A run glued to other alphabet characters (`/v1/blob/<b64>`, `keyx<b64>`) is one longer run that does not
   decode to text: it stays as today. Stated limit L-B1, pinned by a strict expected failure (prototype: both leak).

### 3.2 Decode (`runmap._b64_text(joined: str) -> str | None`; `joined` = the unit's lines joined with nothing between them)
1. Strip the trailing `=`. Call the rest the body.
2. Alphabet: a body with `+` or `/` AND `-` or `_` is mixed: not decodable (None). A body with `-` or `_` is URL-safe:
   map `-` to `+` and `_` to `/`. Otherwise standard.
3. Length: `len(body) % 4 == 1` is not decodable. Otherwise pad with `=` to a multiple of 4 (the written padding is
   ignored, so padded, unpadded and wrongly padded runs decode the same). `base64.b64decode(padded, validate=True)`.
   Non-canonical trailing bits are accepted (the decoder reads them as a reader would). Any `binascii.Error` /
   `ValueError`: None.
4. Bytes to text, first rule that applies, each decode strict (`errors="strict"`):
   a. starts with `FF FE`: UTF-16-LE of the rest; `FE FF`: UTF-16-BE of the rest; `EF BB BF`: UTF-8 of the rest;
   b. otherwise UTF-8; if that fails, or its printable share (rule 5) is under the threshold, then
   c. if the length is even and at least 4: at least 90 percent of the odd-index bytes are 0: UTF-16-LE; else at least
      90 percent of the even-index bytes are 0: UTF-16-BE.
5. Printable share, measured on the decoded `str`, before `_clean`: the share of characters `c` with
   `c.isprintable() or c in "\t\n\r"`. Text if the share is at least `defaults.B64_PRINTABLE_SHARE` (0.90) and the
   string is not empty. NUL is not printable, so NUL-interleaved UTF-16 read as UTF-8 fails rule 5 and is tried as UTF-16
   (the review's M4 point: `_clean` would remove the NULs and make it look readable; the test runs before `_clean`).
6. Returns the text, or None. Hex, base32, base85, gzip and quoted-printable are not decoded (stated limit L-B2).

### 3.3 HELD (what pass 1 already masks is left as pass 1 wrote it)
A line of a unit is HELD when pass 1 (`first.mapping`) holds it exactly as the original of any placeholder, or the line is
a substring of the original of a JWT or PRIVKEY placeholder. A unit is HELD when every one of its lines is HELD.
Effect: the 80 HIGHENTROPY rows of 1b, the 3 `data:` rows and the 2 BASIC rows of 1c, JWTs and PEM blocks are not
decoded and do not change. A wrapped block whose full lines are HIGHENTROPY and whose last line is readable is NOT
held: it is decoded whole and becomes one ENCODED (1c rows 2, 3, 6, 7, 10, 11).
Why exact originals and not "the run is still readable in `first.text`": a run that pass 1 masks only in part is not
held. Found by the prototype: base64 of `pwd=...` often contains `PWd...=`, which a SECRET key=value pattern takes as key
`PWd...` with value `=`, so the run's head stays readable but the run itself no longer appears whole. With the exact
original rule that run is not held, is decoded, and is masked as ENCODED.

### 3.4 The decoded view and the hit rule
1. Budget (one object per `redact_text` call, shared by the text, every view and every depth): before each unit is
   decoded, `time.thread_time() > deadline` raises `InputTooLarge` (the clock check per candidate; `deadline` is the one
   `redact_text` already passes to `redact`). Decodable units that are not held count against `defaults.B64_MAX_UNITS`
   (4,096); one more raises `InputTooLarge`. Decoded characters count against `defaults.B64_MAX_DECODED_CHARS` (262,144);
   past it, `InputTooLarge`.
2. A block longer than `defaults.B64_MAX_BLOCK_CHARS` (65,536) is not decoded: if it is not held it is a hit unread
   (masked whole). Fail closed; it keeps one huge attachment from using the whole decoded-character budget.
3. Depth: the input and its views are depth 0. At depth `defaults.B64_MAX_DEPTH` (3), a decodable unit that is not held
   is a hit unread (masked as ENCODED without decoding). So three levels of base64 are decoded and read; a fourth level
   is masked unread. This is fail closed for the unit and keeps the rest of the text (decision L4).
4. Each decoded text `d` becomes a piece: `_clean(d)` with every `\x1e` replaced by a space. The pieces are joined with
   `_B64_SEP = "\n\x1e\n"` (no piece can hold `\x1e`; NFKC, `undo`, `json_unescape` and `_clean` leave it alone).
5. The joined text is scanned by the SAME function as the input, recursively, with `depth + 1`, the same `neutralise`, the
   same deadline and budget, a COPY of the incoming map, and `_cache=None`: `fits_after_nfkc(_clean(...))`, `neutralise`,
   `_redact_encoded` (so base64 inside decoded text is decoded again: the nesting rule), `_views` (so `undo`, the
   canonical and composed views and the JSON view run on decoded text too: base64 of `password%3Dx` or of a full-width
   secret is found), `_decoded_masks`, the view rule, `_clean`. TooDeep from `undo` propagates: the call is refused.
6. Hit rule per piece: split the scan's output on `_B64_SEP`. A unit is a hit when its output piece holds more genuine
   placeholders (`runmap.PLACEHOLDER`) than the same piece after `_clean` and `neutralise` (the spelling the scan saw).
   This counts a new value AND a value the map already held (base64 of a known password gets the known placeholder:
   prototype, "value known to the map, seen encoded", masked). It is the view rule of `redact_text` applied per piece.
7. If the output does not split back into exactly as many pieces (a pattern such as PRIVKEY's "to the end of the text"
   ate a separator), every unit of that decoded view is a hit. Fail closed.
8. The decoded scan's new map entries are KEPT when at least one unit is a hit (decision L8): its pass 1 on `text2` then
   also sweeps a plain copy of the decoded secret elsewhere in the text. They are thrown away when no unit is a hit.

### 3.5 What stays out of G4a
`redact_many` and `redact()` called directly (k1b `redact_bundle`, the case-bundle path) get no base64 step (stated
limit L-B3). `tools._b64_holds` / `tools._derived` (SPINE's file: the scrub of handed-out secrets, known values only,
base32 too) and `k1b.redaction._pair` (decodes a Kubernetes Secret value under a credential key) are not changed and not
merged: different jobs, noted in the rung table. No offsets other than 0, no base32, no hex.

## 4. G4b: the new kind ENCODED (guard/redact.py)
Exact changes:
1. Label registry: `_LABELS = tuple(dict.fromkeys([*(label for label, _ in PATTERNS), "ENCODED"]))`. ENCODED is NOT put in
   `PATTERNS` (it needs decoding and recursion, it is not a regex). Everything built from `_LABELS` follows: the
   counters, `_KIND` and `_OPENINGS` of the own-output rule (`‹ENCODED_1›` is then an escaped look-alike of a real label,
   exactly like `‹SECRET_1›`), the enforce growth-factor test (ENCODED, 7 letters, is shorter than AZURERESOURCE).
2. `SECRET_KINDS` gains "ENCODED". Effect: the sweep rule "every copy, anywhere, from 4 characters"; `_rules_conflict` in
   runmap's snapshot puts it first; `held_value_left` checks it. `_SECRET_PATTERNS` in runmap is built from PATTERNS, so
   it does not change.
3. Counter restoration needs no new code: `_Redactor.__init__` sets `counters = dict.fromkeys(_LABELS, 0)` and restores
   every kind in `counters` from the map's highest number (`_countable`). With ENCODED in `_LABELS`, a map holding
   `<ENCODED_5>` hands out `<ENCODED_6>` next (v1's KeyError and re-issue are gone).
4. One public function, the only way ENCODED is written:
   `def place_encoded(mapping: dict[str, str], runs: list[str]) -> list[str]`: for each run in order, the placeholder
   it gets, added to `mapping` IN PLACE. A run that already is the original of a placeholder of a SECRET kind gets that
   placeholder (same blob, same placeholder, across calls). A run that is the original of an identifier-kind placeholder
   only gets a NEW ENCODED entry (never a restorable placeholder for a blob that decodes to a secret). New numbers follow
   the `_Redactor` counter rule (after the highest `<ENCODED_n>` in `mapping`). Exactly one entry per new run: no
   `_PIECE` splitting, no `_secret_shaped` pieces, no `_spelled` entry, no journal. The original is the unit's text as
   written in the cleaned and neutralised input (or view), line breaks included, NEVER the decoded text. O(map + runs).
5. `defaults.STORED_KINDS` does NOT change, and `runmap._GRAMMAR` gets no ENCODED entry: `storable` needs the kind in the
   allowlist AND a grammar, so an ENCODED entry is never stored and never restored, even with `kinds={"ENCODED"}`.
6. `RedactionResult.actions` does not count ENCODED replacements (no reader in src; stated).
Fallback if the lead declines the name (L1): `place_encoded` issues `<SECRET_n>` placeholders (SECRET is in `_LABELS`
and `SECRET_KINDS` already), steps 1 and 2 are dropped, the tests assert SECRET. It gives up telling an operator that a
mask hides a decoded blob, not a typed value.

## 5. G4c: whole host names (guard/redact.py, the HOSTNAME entries of PATTERNS)
### 5.1 One place for the suffix list
The redactor's private suffixes live in the HOSTNAME pattern pieces in redact.py and nowhere else:
`_HOST_BARE = "internal|local"` (a host only when nothing follows) and `_HOST_TAIL = "corp|lan|intranet|intra|localdomain|home<DOT>arpa"`
(a host whatever follows). `defaults.PRIVATE_SUFFIX_LABELS` is a different job (config.py checks which in-cluster suffixes
may be called over plain http) and is NOT used: it also lists `test`, `invalid`, `svc`, `cluster`, `home`, which would
mask every `.test` fixture name and every word `home` after a dot. A comment beside each list names the other.

### 5.2 The main pattern (replaces the HOSTNAME regex; same place in PATTERNS: after EMAIL, URLCRED, IPV4; no capture group)
```
_HOST_LABEL = r"[\w-]+"                 # Unicode letters and digits, underscore, hyphen; no length bound (see below)
_HOST_DOT = r"(?:\.|\[\.\])"            # a dot, or a defanged [.]
HOSTNAME = r"(?i)(?<![\w.\-\]])(?:" + _HOST_LABEL + _HOST_DOT + r")+(?:"
           r"(?:internal|local)(?![\w-])(?!" + _HOST_DOT + r"\w|\()"            # bare suffix: nothing may follow
           r"|(?:corp|lan|intranet|intra|localdomain|home" + _HOST_DOT + r"arpa)(?![\w-])"
           r"(?:" + _HOST_DOT + _HOST_LABEL + r")*)"                              # tail: the rest of the dotted name
```
1. Start: not after a word character, `.`, `-` or `]`, so a match starts at the first label of the dotted name and the
   name is masked whole. Underscore is a label character (`db_01`, `_ldap._tcp.corp`), so the old `\b` boundary problem
   with `_` is gone. `\w` is Unicode, so `bücher.internal` matches.
2. Tail: after a `_HOST_TAIL` suffix the rest of the dotted name goes into the match (`db01.corp.example`,
   `billing-db.prod.corp.example`, `xn--bcher-kva.corp.example`). A trailing dot is not a label: `db01.corp.example.`
   gives `<HOSTNAME_1>.`. A port, a path and `@` end the name.
3. Bare suffix `.internal` / `.local`: kept from today. Never a tail; a following label (`.x`, `[.]x`) or `(` means code
   (`jdk.internal.reflect`, `threading.local()`), not a host: no match.
4. Labels are unbounded and the label count is unbounded on purpose. With the start rule there is one start per dotted
   token, so the greedy `+` backtracks at most once per label: linear. A bound would be fail-open here (a name with a
   64-character label, or 9 labels before `corp`, would not match at all). Measured on main (prototype, CPU s): `a.` x
   130,000: old 0.154, new 0.025; `ab-cd.` x 40,000: old 0.152, new 0.012; 262,000 characters of `abc.def.ghi`: old
   0.023, new 0.011; `a.corp.` x 50,000: one match, the whole token.
5. `_KEPT_HOST` is unchanged and still applied to the whole match in `_decide`: `x.svc.cluster.local` and
   `eu-west-1.compute.internal` / `ec2.internal` stay. A defanged `x[.]svc[.]cluster[.]local` is masked (accepted).
6. Java-package over-masking: `com.acme.corp.billing.Service` was `<HOSTNAME_1>.billing.Service` and becomes
   `<HOSTNAME_1>` (pinned as a stated limit L-H1; a package with a `corp`/`lan`/`intranet` label is rare).

### 5.3 The host-key rule (a second HOSTNAME entry, right after the main one; group 1 is the value)
```
HOSTKEY = r"(?i)(?<![\w-])(?:(?:--)?host(?:name)?(?:[\"']?[ \t]*[:=][ \t]*[\"']?|[ \t]+)|server[\"']?[ \t]*[:=][ \t]*[\"']?)"
          r"(?=[A-Za-z0-9_-]{0,62}[0-9-])(?=[A-Za-z0-9_-]{0,62}[A-Za-z])"
          r"([A-Za-z0-9][A-Za-z0-9_-]{1,61}[A-Za-z0-9])(?![\w\-/@])(?!\.\w)"
```
Value grammar: ONE label, 3 to 63 characters, at least one letter AND at least one digit or hyphen, not followed by a
word character, `-`, `/`, `@` or a dot and a word character. Keys: `host`, `hostname`, `--host`, `--hostname` with `=`,
`:` or spaces; `server` only with `=` or `:`. A dotted value is never taken by this rule: a private one is the main
pattern's, a public one (`Host: api.github.com`) stays. `_KEPT_HOST` applies (a single label never matches it). The value
is not in `_COMMON` by construction (it has a digit or a hyphen).
Must-keep (prototype, all unchanged): `host is down`, `server timed out`, `Server: nginx`, `Server: nginx/1.18.0`,
`ghost town db01`, `ghost=ab12`, `Host: api.github.com`, `host: localhost`, `--host 0.0.0.0` (IPV4 masks the address as
today), `host 1 of 3 failed`, `server 500 error`, `the hostname is unknown`.
Closed: rows 33 `host db01 is down`, 34 `host: db01`, 35 `hostname=db01`, 36 `psql --host db01`.

### 5.4 Restorable grammar
`runmap._GRAMMAR["HOSTNAME"]` (`[A-Za-z0-9.\-]{3,253}`) is NOT changed. A HOSTNAME original with `_`, a non-ASCII letter
or `[.]` is masked for the model and never stored or restored (fail safe: a tool call with that placeholder gets the
placeholder). Fallback (L5): add `_` to the grammar so underscore names restore.

## 6. G4d: bare numbers (written down, pinned)
One paragraph added to the module docstring of guard/redact.py, after the "What this is not" paragraph:
"A bare number with no label or context (for example `ref 55556666 paid`) is not masked, by decision (order 64 item 4).
Masked by shape: 10 to 16 contiguous digits (PHONE; exactly 12 as ACCOUNTID) and 16 digits in four groups of four joined
by spaces or hyphens (CREDITCARD). Other groupings are masked in part or not at all: 16 digits joined by dots lose their
first 12 to MAC and keep the last group; 15 digits in 4-6-5 groups lose the first 10 to PHONE and keep the last 5."
Pin (class level, no output strings): tests/test_p1c_gaps.py classifies the 43 gap-3 rows with the probe's own rule
(whole / part / NOT masked) and asserts the class per row: 24 NOT masked (rows 1-7, 9-12, 14-20, 30, 35, 38-40, 43),
2 part (29, 32), 17 whole (8, 13, 21-28, 31, 33, 34, 36, 37, 41, 42). A row that differs at build time: report, change
no pattern.

## 7. Constants (defaults.py, one SPINE commit holding only these six lines and their comments)
| constant | value | what it bounds |
|---|---|---|
| `B64_MIN_CHARS` | 12 | shortest run tried, padding not counted (closes row 83, 15 characters; v1's 16 left it open) |
| `B64_PRINTABLE_SHARE` | 0.90 | printable share of the decoded text (section 3.2 rule 5) |
| `B64_MAX_UNITS` | 4096 | decodable, not-held units per `redact_text` call (all views, all depths); past it `InputTooLarge` |
| `B64_MAX_DECODED_CHARS` | 262144 (= `MAX_REDACT_CHARS`) | decoded characters per call; past it `InputTooLarge` |
| `B64_MAX_BLOCK_CHARS` | 65536 | longest wrapped block that is decoded; a longer unheld block is masked unread |
| `B64_MAX_DEPTH` | 3 | levels decoded; a unit found at level 3 is masked unread |
Also update the stale comment above `REDACT_BUDGET_S` (G7 result review cb-M2): one call now runs pass 1, up to
`_SETTLE_ROUNDS` settle rounds, the views, and on a hit one decoded scan and one more pass 1; the budget is checked
inside the fold scan, between settle rounds (MJ-B), between views and before each decoded unit.
Fallback (L7): the six constants as module constants in runmap.py beside `MAX_DECODED_MASKS`, if SPINE declines.

## 8. Cost
Measured by the drafter, prototype on main 51c9fc4 (Python 3.13.18, this container, CPU seconds, best of 3 or 7):
| text | `redact_text` today | base64 step alone or with step |
|---|---|---|
| 100,000 chars of snake_case, paths and prose lines | 0.140 | step alone 0.0071 (5.1 percent) |
| 262,000 chars of the same | 0.357 | step alone 0.0195 (5.5 percent) |
| 100,000 chars of prose | 0.143 | step alone 0.0011 (0.7 percent) |
| the 100,000-char mix plus one planted `password=` | 0.138 | with step 0.154 (noise level on this shared machine) |
| 4,000 benign base64 runs, padded to 262,000 chars | 0.35-0.44 | 0.47-0.56 |
| 2,000 double-base64 secrets (70,000 chars) | 0.08-0.12 | 0.59-0.74 |
| 4,096 base64 secrets (110,591 chars), the unit cap | 0.18 | 0.72-0.82 (mostly `_build` over a map of 8,192 entries) |
| 4,097 base64 secrets | 0.18 | `InputTooLarge` after 0.20 |
Baseline after G7: not measurable by the drafter (only main may be run). G7's own numbers: 100,000 characters with
matches 0.206 s before, 0.484 s after; a text with no match 1.0x. MJ-B adds rounds only when a round grows the map.
Worst case: a text at the unit cap runs pass 1 twice, one decoded scan of at most 262,144 characters and the views;
each `redact()` may cost up to about 2.4x on the post-MJ-B tree, so the estimate is about 2 s without views on this
machine, under `REDACT_BUDGET_S` (6.0). With `\`, `%` or `&` in the text each of up to 6 views runs pass 1 again
(held units are swept, not decoded). Past the deadline: `InputTooLarge` (fail closed, nothing shown), never a skipped
step. `MAX_MAP_ENTRIES` (2,000) is not enforced anywhere today; G4 adds at most `B64_MAX_UNITS` ENCODED entries per call.

## 9. Expected results per probe row
### 9.1 Base64, 142 rows (probe numbering; "unchanged" = output and map byte-identical to the base commit)
| rows | value | expected |
|---|---|---|
| 1b 1-5, 7, 8 | kv secret short | one `<ENCODED_n>` where the blob stood; map also SECRET |
| 1b 6, 9-16 | kv secret | unchanged (HIGHENTROPY holds it) |
| 1b 17-32 | bearer token | unchanged (HIGHENTROPY) |
| 1b 33-37, 39, 40 | AWS key id short | ENCODED; map also APIKEY |
| 1b 38, 41-48 | AWS key id | unchanged |
| 1b 49-53, 56 | e-mail short | ENCODED; map also EMAIL |
| 1b 54, 55, 57-64 | e-mail | unchanged |
| 1b 65-72 | host name short (70 = UTF-16-LE, 71 = double) | ENCODED; map also HOSTNAME |
| 1b 73-80 | host name long | unchanged |
| 1b 81-88 | private IPv4 short (83 = 15 chars, closes with `B64_MIN_CHARS` 12; 86 = UTF-16-LE) | ENCODED; map also IPV4 |
| 1b 89-96 | private IPv4 long | unchanged |
| 1b 97-101, 104 | connection string short | ENCODED; map also URLCRED |
| 1b 102, 103, 105-112 | connection string | unchanged |
| 1b 113-117, 120 | JSON with password short (113-117: 38 + `==`) | ENCODED; map also SECRET |
| 1b 118, 119, 121-128 | JSON with password | unchanged |
| 1c 1, 5, 9 | wrapped at 32 (whole blob readable today) | the whole block is one `<ENCODED_1>` |
| 1c 2 | wrapped at 64, last line held 11 of 14 password chars | one `<ENCODED_1>` (kind change from HIGHENTROPY lines) |
| 1c 3, 6, 7, 10, 11 | wrapped at 64 / 76, no leak today | one `<ENCODED_1>`: KIND CHANGES from `<HIGHENTROPY_1>` lines plus a readable last line; still no leak |
| 1c 4, 8, 12 | `data:` URL | unchanged (HIGHENTROPY) |
| 1c 13, 14 | `Basic <b64>` | unchanged (BASIC) |
Totals: 52 closed (48 in 1b, 4 in 1c), 85 unchanged, 5 change kind. Prototype: 0 leaks by the probe's `leak_of` for
`redact_text` and for `redact_untrusted`; the 85 unchanged rows byte-identical.
Unprobed shapes (prototype on main, constructed here; the builder adds them to the G4 tests):
| shape | result | status |
|---|---|---|
| JSON with `\/`-escaped slashes | closed through the JSON view | expected pass |
| `%3D` padding | closed through the `undo` view | expected pass |
| value already in the run map, seen in base64 | known placeholder counted: ENCODED | expected pass |
| UTF-16-BE without BOM, UTF-16-LE with BOM (long samples) | held by HIGHENTROPY; a short BE sample is not built yet | builder builds a short one |
| triple base64 (short, under 40 chars at level 3) | decoded at depth 3 | builder builds it |
| fourth level | masked unread (depth rule) | builder builds it |
| glued to a prefix (`/v1/blob/<b64>`, `keyx<b64>`) | leaks (offset 0 only) | limit L-B1, strict xfail |
| a blob split across two JSON fields | the second half stays readable | limit L-B4, strict xfail |
| wrapped lines with a log prefix per line | readable | limit L-B5, strict xfail |
| base32, hex | not decoded | limit L-B2, strict xfail |
| row 83 with `B64_MIN_CHARS` 16 (fallback L6) | stays a leak | limit only if L6 is declined |

### 9.2 Host names, 44 rows
| row | input shape | expected after G4 | class |
|---|---|---|---|
| 1, 2, 17, 19, 24, 26, 29, 37, 38, 44 | `...corp.example` with port, URL, upper case, trailing dot, punycode, `host=`, JSON, two names | whole name one placeholder (`dial <HOSTNAME_1> now`, `:5432`, `/v1`, `.` kept outside) | closed (part before) |
| 21 | URL with credentials | `postgres://app:<URLCRED_1>@<HOSTNAME_1>:5432/orders` | closed |
| 39, 40, 41 | `.`, `%2E`, full-width dots | whole name, through the views | closed |
| 31 | `bücher.internal` | `<HOSTNAME_1>` | closed (whole before) |
| 32 | `db_01.corp.example` | `<HOSTNAME_1>` | closed |
| 43 | `db01[.]corp[.]example` | `<HOSTNAME_1>` | closed |
| 33, 34, 35, 36 | `host db01`, `host: db01`, `hostname=db01`, `--host db01` | `<HOSTNAME_1>` in place of `db01` | closed (host-key rule) |
| 3, 4, 5, 7, 11, 12, 13, 14, 18, 20, 22, 23, 25, 27, 28, 30 | already masked whole | unchanged | already masked |
| 6, 8 | `.internal` / `.local` then more labels | unchanged (code-name guard) | kept on purpose |
| 9 | `.svc.cluster.local` | unchanged (`_KEPT_HOST`) | kept on purpose |
| 42 | `ip-<IPV4_1>.eu-west-1.compute.internal` | unchanged (`_KEPT_HOST`; IPV4 masks the address) | kept on purpose |
| 10 | `billing.payments.svc` | unchanged | stated limit L-H2 (in-cluster short form, same reason as `.cluster.local`) |
| 15, 16 | `db01.acme.example`, `db01.acme.test` | unchanged | stated limit L-H3 (no private suffix: looks like a public site) |
Totals: 21 closed (14 part rows and 7 whole rows: 31, 32, 33, 34, 35, 36, 43), 3 limits, 4 kept, 16 unchanged.
Prototype: exactly these 21 change, the other 23 rows are unchanged. Two warden_port MASKED rows change and stay green
(their test asserts the kind only): `db at billing-db.prod.corp.example:5432` and `smb://files.lan.example/share`
become `<HOSTNAME_1>:5432` and `smb://<HOSTNAME_1>/share`. Rows 31 and 41 are non-ASCII: on the integrated tree the fold
scan runs first; their expected class is the same, the exact output is checked at step 0 (section 12).

## 10. Invariants (each is one test or one parametrised test)
- I1. Each of the 52 leaked base64 rows: `leak_of(protected, out)` is "no" and `<ENCODED_` is in `out`, through
  `redact_text` and through `redact_untrusted`.
- I2. The 85 unchanged base64 rows: output and map equal the base commit's (recorded as a fixture at step 0).
- I3. The 5 kind-change rows (1c 3, 6, 7, 10, 11): output is exactly `<ENCODED_1>`; no part readable.
- I4. Must-keep base64 (output and map equal the base commit's): base64 of benign text (`this is just a status message`,
  `ok status 200`), binary bytes, a Kubernetes `data:` value of plain config text, a JWT with a benign payload, a JWT
  whose payload holds an e-mail address (stays `<JWT_1>`), UUID with and without dashes, SHA-256, SHA-1, a short git sha,
  long words, snake_case, kebab-case, a path, camelCase, and every row of `tests/warden_port/privacy_corpus.py`
  MASKED and KEPT (prototype: 79 of 79 equal).
- I5. A text with no run of `B64_MIN_CHARS` makes exactly as many `redact()` calls as before and returns the same text.
- I6. ENCODED is never restored: `restore_text(out, m)` and `restore_text(out, m, kinds=frozenset({"ENCODED"}))` leave
  `<ENCODED_n>` as it is; `storable(m)` holds no ENCODED key.
- I7. Numbering: a map holding only `<ENCODED_5>` gets `<ENCODED_6>`; two different blobs get 1 and 2; the same blob in
  two calls with one map gets the same placeholder; a blob equal to a TENANT original gets a new ENCODED, not the TENANT one.
- I8. One entry per unit: the ENCODED original equals the unit as written (line breaks included), never the decoded text.
  A nested blob also adds one entry per inner unit, whose original is that inner run as decoded one level up (prototype:
  four levels of base64 of `status ok` give `x <ENCODED_4>`, three inner entries); output numbers can therefore skip.
- I9. Idempotent: `redact_text(redact_text(t, m), m)` changes neither text nor map, for all 229 probe rows (prototype: 229 of 229).
- I10. Parity: `redact_untrusted` and `redact_text` give the same leak verdict on all 142 base64 rows and the same
  output on the 44 host and 43 number rows.
- I11. Host must-keep rows of section 5.3 and the KEPT corpus are unchanged; `x.svc.cluster.local`,
  `x.svc.cluster.local.foo`, `eu-west-1.compute.internal`, `jdk.internal.reflect...`, `threading.local()` unchanged.
- I12. Host: the 21 closed rows have no label of the name readable outside a placeholder (the probe's own label test);
  the 3 limits, the 4 kept rows and the 16 already masked rows are unchanged; both e-mail rows stay one EMAIL.
- I13. Caps fail closed: one unit over `B64_MAX_UNITS`, decoded characters over `B64_MAX_DECODED_CHARS`, or a spent
  deadline raises `InputTooLarge`; nothing is returned. (Tests patch the constants to small values.)
- I14. Depth: a unit still decodable at depth `B64_MAX_DEPTH` is masked as ENCODED even when it holds only benign text.
- I15. Separator fallback: a unit test of the hit decision, given decoded pieces whose scan output holds fewer
  separators than pieces (as a decoded `-----BEGIN PRIVATE KEY-----` without END would cause; through the whole text such a
  blob is usually long enough for HIGHENTROPY to hold it), marks every unit of that view a hit.
- I16. Cost (perf mark, fixed ceilings against the base commit on the same machine, best of 5 CPU seconds): 100,000
  characters of snake_case and paths at most 1.10x; 100,000 characters of prose at most 1.05x; the same with one planted
  `password=` at most 1.10x; 4,096 base64 secrets under `REDACT_BUDGET_S`.
- I17. The G7 property test (tests/test_redact_idempotent_property.py) stays green with 1,835 inputs and its counts, now
  fed by tests/p1c_cases.py.
- I18. Bare numbers: the 43 gap-3 rows keep their class (24 / 2 / 17).

## 11. Files
Create:
- `tests/p1c_cases.py`: a copy of the probe's builders (`rand`, `gap1_values`, `ENCODINGS`, `b64`, `wrap`, `no_digit_line`,
  the 1c case list, `gap2_cases`, `luhn_number`, `gap3_cases`, `leak_of` with `lcs`, `_decodings`, `readable`), one
  module-level `random.Random(20261120)` consumed in the probe's call order (gap1 1b, 1c including both `no_digit_line`
  searches, gap2, gap3). Not imported from handover/: tests must not read the evidence folder.
- `tests/test_p1c_gaps.py`: the per-row expectations of section 9 and the gap-3 class pin. Uses only public names
  (`redact_text`, `redact_untrusted`, `restore_text`, `storable`), so it can run unchanged on the base commit (FAIL-BEFORE).
- `tests/test_b64_scan.py`: unit tests of `_b64_text`, the unit finder, the held rule, `place_encoded`, the caps, the depth
  rule, the separator fallback, the host-key value grammar, the must-keep rows, the constructed shapes and the strict
  xfails L-B1, L-B2, L-B4, L-B5, L-H1.
Modify:
- `src/hadavin_sdk/guard/runmap.py`: `_B64_RUN`, `_B64_SEP`, `_b64_text`, the unit finder, `_redact_encoded`, the budget,
  the two call sites in `redact_text`; the `redact_text` docstring gains one paragraph on the base64 step.
- `src/hadavin_sdk/guard/redact.py`: `_LABELS`, `SECRET_KINDS`, `place_encoded`, the HOSTNAME regex and comment, the
  HOSTKEY entry, the module docstring (section 6 and one sentence: "A value only written in base64 is found by the
  decoded view of `runmap.redact_text` and masked whole as ENCODED; `redact()` itself does not decode").
- `src/hadavin_sdk/defaults.py` (SPINE's file, its own commit): section 7.
- `tests/test_redact_idempotent_property.py`: `_p1c_module()` loads tests/p1c_cases.py instead of the evidence file;
  counts unchanged.
Must stay green UNCHANGED (run, do not edit): tests/warden_port/test_redaction.py (OWN_SHAPES JWT and BASIC rows,
`test_a_high_entropy_value_after_any_key_is_masked`), tests/warden_port/test_redaction_classes.py, test_redaction_bank.py,
test_redaction_review*.py, tests/test_redact_context_after_sweep.py (E5 BASIC row), tests/test_redact_own_output.py,
tests/test_redact_own_output_hardening.py, tests/test_k5_round8.py (`_jwt` straddling test), tests/test_k5_classes.py
(stored-kind grammar per kind; unknown kind never stored), tests/test_runmap_enforce_map.py (the growth factor from
`_LABELS`), tests/test_k1b_redaction.py (`db01.corp.local`), tests/test_text_parts_together.py (`db-7.corp.internal`),
tests/fixtures/p1d_cases.py users (test_p1d_a_paths.py and the defang suites: `[.]` text after a placeholder).
If one of them fails, it is a finding: report it, do not edit it in this step. Delete: nothing. Migration: none (maps are
per run and in memory; ENCODED is never stored).

## 12. Tests and evidence
Step 0 (before any code): on the base commit, run the probe from a clean export of that commit and record its tables;
any row whose verdict differs from main 51c9fc4 is reported, and its expectation in section 9 is re-derived by the
lead's rule before building. Record the base outputs of the 85 + 23 + 43 unchanged rows as the I2 / I12 fixture.
FAIL-BEFORE: copy tests/p1c_cases.py and tests/test_p1c_gaps.py into a worktree of the base commit:
`git -C /home/user/hadavin-sdk worktree add /tmp/g4-base <base-sha> && cp tests/p1c_cases.py tests/test_p1c_gaps.py /tmp/g4-base/tests/ && cd /tmp/g4-base && uv run --all-extras --group test pytest tests/test_p1c_gaps.py -q -p no:randomly`
Expected: exactly 78 failures (57 base64: 52 leaks + 5 kind changes; 21 host rows), every other row passes. The failing
ids go into the evidence verbatim. Remove the worktree afterwards (`git worktree remove /tmp/g4-base`).
Parity: tests/test_p1c_gaps.py asserts the sha256 of the joined inputs of tests/p1c_cases.py (all 229 rows, in order,
`"\x00".join`) equals the value recorded in evidence/G4-1.md, which the builder computes once by running
evidence/p1c_probe.py's builders in a clean export. The probe and the copy then provably build the same inputs.
Mutants (each must be killed; tools/mutants or a hand diff, raw result in the evidence):
| mutant | killed by |
|---|---|
| skip the printable rule (any bytes count as text) | test_b64_scan: `_b64_text` of base64 of `bytes(range(256))` is None; I4 binary row |
| accept a mixed alphabet run | `_b64_text` of a run with `+` and `_` is None; I4 path rows |
| drop the `len % 4 == 1` rule | `_b64_text` of a 13-character body is None |
| drop the UTF-16 rules | 1b rows 70, 86 (I1) |
| drop the depth limit | I14 (benign text four levels deep must be ENCODED) |
| drop the unit cap | I13 with `B64_MAX_UNITS` patched to 3 and 4 units |
| drop the decoded-character cap | I13 with the cap patched to 10 |
| drop the clock check per unit | I13 with a deadline already spent at the step |
| ENCODED outside `SECRET_KINDS` | `_sweep("<ENCODED_1>", run) is _EVERY_COPY`; a glued copy of the run elsewhere is masked |
| ENCODED in `STORED_KINDS` or given a grammar | I6 |
| counter not restored for ENCODED | I7 (`<ENCODED_5>` then 6) |
| `place_encoded` splits pieces | I8 (exactly one new entry) |
| original = decoded text | I8 |
| skip neutralise on the decoded text | `redact_untrusted` of base64 of `password=<FOO_1>` is ENCODED (as `redact_untrusted("password=<FOO_1>")` masks), `redact_text` parity row |
| skip `_views` on the decoded text | base64 of `password%3Dx...` is ENCODED |
| decode units pass 1 already holds (no held rule) | I2 (80 HIGHENTROPY rows), I4 JWT rows |
| held = "run still readable" instead of exact originals | the `PWd...=` row (base64 of `pwd=` whose run pass 1 cuts) |
| mask only the found span inside the decoded text, not the blob | I1 |
| drop the wrapped-line join | 1c rows 1, 2, 5, 9 |
| join any window of lines (no width rule) | test_b64_scan: two unrelated short lines are not one unit |
| no separator fallback | I15 |
| first pass's map kept instead of the decoded scan's | I3 (no HIGHENTROPY entries in the map) |
| host: drop the tail | rows 1, 2, 17 ... |
| host: `_` not a label character | row 32 |
| host: drop `[.]` | row 43 |
| host: drop the `.internal`/`.local` guard | KEPT `jdk.internal.reflect`, `threading.local()` |
| host: unkeep `.cluster.local` | row 9, KEPT `orders.shop.svc.cluster.local:8080` |
| host-key without value grammar | `host is down`, `server timed out`, `Server: nginx` |
| host-key `server` with a space form | `server 500 error`, `server timed out` |
| host-key takes dotted values | `Host: api.github.com` |
Evidence commands (raw output to evidence/G4-1.md):
- `uv run --all-extras --group test ruff check src/hadavin_sdk/guard/runmap.py src/hadavin_sdk/guard/redact.py src/hadavin_sdk/defaults.py tests/p1c_cases.py tests/test_p1c_gaps.py tests/test_b64_scan.py`
- `uv run --all-extras --group test pytest tests/test_p1c_gaps.py tests/test_b64_scan.py -q`
- `uv run --all-extras --group test pytest tests/test_redact_idempotent_property.py tests/test_redact_context_after_sweep.py tests/test_redact_own_output.py tests/test_redact_own_output_hardening.py tests/warden_port -q -n 2`
- the files that import redact or runmap once (`grep -rlE "guard\.(redact|runmap)|from hadavin_sdk.guard import" tests`), `-n 2`
- the perf-marked redactor tests serially (`-m perf -p no:xdist`), and I16
- `uv run --group scan bandit -q -r src/hadavin_sdk/guard -ll`
- the probe re-run on the G4 head (clean export) with its totals.

## 13. Lead decisions (build default first, fallback if declined)
| id | question | build default | fallback |
|---|---|---|---|
| L1 | new kind name | ENCODED | SECRET (section 4 last paragraph) |
| L2 | host keys | `host`, `hostname`, `--host`, `--hostname` with `=`, `:` or space; `server` with `=` or `:` only; one label with a letter and a digit or hyphen | `=` and `:` only: rows 33 and 36 become limits (19 closed) |
| L3 | dotted names with no private suffix (rows 15, 16) and the `.svc` short form (row 10) | stay unmasked, stated limits | add `svc` to `_HOST_BARE` (row 10 closes; every in-cluster short name is masked) |
| L4 | a fourth base64 level | the unit is masked unread | `TooDeep` refuses the whole text (repository convention of `undo`) |
| L5 | restore of underscore host names | grammar unchanged: not restorable | add `_` to `_GRAMMAR["HOSTNAME"]` |
| L6 | shortest run | 12 characters (row 83 closes) | 16 (row 83 a stated limit) |
| L7 | where the constants live | defaults.py, a SPINE commit of six lines | module constants in runmap.py |
| L8 | decoded finds | kept in the run map when a unit is a hit (plain copies elsewhere are swept; a HOSTNAME found only in base64 can then be stored) | only the ENCODED entries are kept |

## 14. Security notes, what stays out, rollback, reviewers, done
- No secret value is logged or put in an exception; `InputTooLarge` / `RedactionError` carry only their type name.
- The decoded text never leaves the redactor: only `<ENCODED_n>` is written; its original (the encoded run) lives in the
  run map in memory, is never stored (I6) and is swept in every copy.
- Stays out: `redact_many`; offsets other than 0; base32, hex, gzip; blobs glued to a prefix or split across fields or log
  prefixes; changes to `tools.py` and `k1b/redaction.py`; `MAX_MAP_ENTRIES` enforcement; any change to other patterns.
- Rollback: tag `pre-G4` on the base commit. No migration. Text already written with `<ENCODED_n>` stays as text.
- Reviewers: one correctness and one adversarial reviewer, fresh, given the diff, this ticket and evidence/G4-1.md only.
- Done: every invariant test green, FAIL-BEFORE recorded (78 ids), every mutant killed, the must-stay-green list green,
  ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit green, the result review clean.

## For SECURITY wording (after the build)
- A value written only in base64 (standard or URL-safe, padded or not, UTF-8 or UTF-16, wrapped at a fixed width, up
  to three levels deep) is masked whole as ENCODED by `redact_text` / `redact_untrusted`; `redact()` and `redact_many`
  do not decode. Not found: a blob glued to other base64-alphabet characters, split across fields or prefixed lines,
  base32, hex.
- A private host name is masked whole; a dotted name with no private suffix is not; `.svc` short names, `.cluster.local`
  and AWS's own names are kept on purpose.

## (A) How each review finding was handled
| finding | resolved in | or contested, why |
|---|---|---|
| g4r-B1 plug-in point; mapping into `out`; I1 false for held rows | 2 (steps 1-7), 3.3, 9.1, I1-I3 | resolved; deviation from the proposal "before pass 1": the decision uses pass 1 to skip held units, the replacement is on the input and a second pass 1 carries it into `out` (reason in 2) |
| g4r-B2 ENCODED creation, counters, `_PIECE`, reuse, label-set tests, I6 | 4, I6-I8, 11 | resolved |
| g4r-B3 host-key value grammar, position, group | 5.3, must-keep list, L2 | resolved; row 33 kept by requiring a digit or hyphen |
| g4r-B4 I3 vs rows 10/15/16; two keep mechanisms; tail grammar; suffix definition; restorable grammar | 5.1-5.4, 9.2, I12, L3, L5 | resolved; the tail is unbounded (a bound is fail-open, 5.2 point 4) |
| g4r-M5 decode rules; neutralise; recursion; depth | 3.2, 3.4, L4 | resolved |
| g4r-M6 join rule; candidate cap; budget; placeholders as candidates; I5 numbers; `redact_many` | 3.1, 3.3, 3.4, 7, 8, I16, 3.5 | resolved (placeholders are never candidates: `<`, `>` end a run; a held run is skipped) |
| g4r-M7 G7 order, sweep, property test, call counts | 2, I5, I17, 11 | resolved |
| g4r-M8 build default and fallback; defaults.py commit | 13, 7 | resolved |
| g4r-M9 test builders, per-row table, FAIL-BEFORE count, forced files, must-keep, mutants, `is_masked`, parity | 9, 10, 11, 12 | resolved; `is_masked` no longer referenced |
| readiness nits: symbol names; G4c by class; FAIL-BEFORE command; known value seen as base64 | whole ticket; 6; 12; 9.1 | resolved |
| g4c-B1 ENCODED needs label, `SECRET_KINDS`, public function, counter test; `STORED_KINDS` unchanged | 4, I6, I7 | resolved |
| g4c-B2 the 90 non-leaked rows change; JWT split | 3.3, 9.1, I2-I4 | resolved by the preferred fix (held rule); 5 rows still change kind and are listed |
| g4c-M1 21 of 24; second suffix list | 5.1, 9.2 | resolved |
| g4c-M2 host-key false positives, sweep and restore of words | 5.3 | resolved |
| g4c-M3 cost bound; clock per candidate; one concatenated view; join caps; gate apart from `scan` | 3.4, 7, 8, 2 step 2 | resolved; the remark that `MAX_MAP_ENTRIES` is enforced nowhere is CONTESTED for this ticket: a pre-existing gap of the whole redactor, not G4's; G4 bounds its own growth by `B64_MAX_UNITS` |
| g4c-M4 `_clean`, `undo`, `fits_after_nfkc`, printable after decode, LE/BE | 3.2, 3.4 point 5 | resolved |
| g4c-M5 glued prefix, padding, row 83, `\/`, `%3D`, views, `Basic` | 3.1, 3.2, 9.1, L6 | resolved; glued prefix is a stated limit (offset 0, lead's rule: no failing probe row) |
| g4c-M6 tail and the Java guard; underscore; non-ASCII; `[.]`; `_KEPT_HOST` | 5.2, 5.4, I11 | resolved; Java over-masking accepted and pinned (L-H1) |
| g4c-M7 prerequisites; G7 pins | 0, 2, 11, I17 | resolved |
| code nits: docstring wording; numbers skip; HIGHENTROPY conditions; ENCODED not in PATTERNS | 6; 14 (numbers may skip: no caller depends on it, G7 dz-8); 1 and 9.1 (HIGHENTROPY rows taken as measured); 4 point 1 | resolved |
| reviewers' leak count (51 of 52) and must-keep suggestions | 9.1, I4 | resolved: 52 of 52 by prototype (row 2 needs the join, row 83 the 12 minimum) |

## (B) RUNG TABLE and NEEDED-CHECK (CODE-LAST v1, scale of 2026-11-06)
NEEDED-CHECK. Read: runmap.py `redact_text`, `_views`, `undo`, `_clean`, `fits_after_nfkc`, `_decoded_masks`, `_GRAMMAR`,
`storable`, `restore_text`, `enforce_map`, `snapshot`; redact.py `PATTERNS` (HOSTNAME, BASIC, BEARER, JWT, HIGHENTROPY),
`_KEPT_HOST`, `_LABELS`, `_OWN_OUTPUT`, `_Redactor.__init__` counters, `_decide`, `_mask_ex`, `_place`, `settle` (MJ-B in the
working tree), `SECRET_KINDS`, `_sweep`, `redact_many`; defaults.py `REDACT_BUDGET_S`, `MAX_REDACT_CHARS`,
`PRIVATE_SUFFIX_LABELS`, `CLUSTER_SUFFIXES`, `STORED_KINDS`; tools.py `_B64_TOKEN`, `_b64_holds`, `_derived`;
k1b/redaction.py `_pair`. grep `b64decode|base64` in src/hadavin_sdk/guard: no decoder (comments only). Verdict: NEEDED
for G4a and G4c; G4d is a docstring and a pin. One place per job: decoding for redaction in runmap.py beside the views;
host grammar in the HOSTNAME entries of redact.py.
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| base64 decoded view | a secret only written in base64 is masked | 2 core: `_views` (no base64), `tools._b64_holds` (known handed-out values only, `errors="ignore"`, not on the `redact_text` path, SPINE's file), `k1b._pair` (one Kubernetes value under a credential key); 3 tools: none in-process; 4 library: stdlib `base64` is the decoder (no new dependency); detect-secrets / gitleaks style scanners: UNVERIFIED, not fetched, and not usable in-process on the redaction path | probe 2026-11-20; drafter's prototype 2026-11-20 | decode tied to the redactor's patterns, map, views, caps and deadline | KEEP-CODE, small |
| kind ENCODED | a mask that says "decoded blob", never restorable | 2 core: SECRET kind exists | section 4 | the label only | KEEP-CODE (fallback SECRET, L1) |
| whole host name, host key | the full dotted name is masked | 2 core: HOSTNAME pattern exists, too narrow; 4 library: a public-suffix list package could tell public from private, UNVERIFIED and it needs a list update path | probe; prototype | - | KEEP-CODE: a pattern change, not a new component |
| bare numbers | written down | 2 core: decision order 64 item 4 | probe | - | CUT to a docstring and a pin |

## (C) NOT CHECKED
- Nothing was built and no repository test was run. Every "prototype" number comes from scratch code on a clean export
  of main 51c9fc4 (no G7, no MJ-B, no fold scan); the integrated tree was not run by the drafter.
- The post-G7 / post-MJ-B baseline and worst case (only estimated from G7's numbers); timing on Windows or under load.
- Rows 31 and 41 (non-ASCII) and any row through the integrated fold scan.
- The must-stay-green suites under G4 (only their sources were read; they call `redact()` directly or hold no base64).
- A short UTF-16-BE sample, a short triple-base64 sample, a decoded PEM header in a decoded view (I15) as real runs.
- Base64 inside text that a non-empty run map already partly masked, apart from one constructed row.
- How the gate (`model_gate`, `enforce_map`) and approval cards show ENCODED to an operator.
- Whether `\w` (Unicode) in the HOSTNAME label class changes other suites' expectations beyond the corpora run here.
