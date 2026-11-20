# Ticket G4: P1c redactor gaps, written new (ORDER 006 item 1)

Written by core-c, 2026-11-20. Rule from the lead: build ONLY the gaps a failing input proves against today's redactor; a gap with no failing input is cut. Small.
Evidence: evidence/P1c-probe.md (re-runnable: evidence/p1c_probe.py), run on a clean export of main 51c9fc4, empty map, seed 20261120, two identical runs.
Step type: shipping code on the redaction path (guarantee class). Path class: redaction.
Depends on: G0 (the `_scan` split in guard/runmap.py) being committed, because G4 edits the same function family. Independent of the fold (G1); a later fold or P2d-1 port must keep G4's tests green.

## What the probe proved
| gap | cases | leaked | verdict |
|---|---|---|---|
| 1 base64 | 142 | 52 | PROVEN: there is no decoded view. A base64 blob shorter than 40 characters passes unchanged (41 of 41), also inside a sentence, a JSON string or after `data=`. Long blobs wrapped at 32 characters pass unchanged (3 of 3); wrapped at 64, the short last line stays. Long unbroken blobs are already masked whole as HIGHENTROPY (64 of 64), `Basic <b64>` and `data:` URLs too |
| 2 host names | 44 | 28 | PROVEN for 24; 4 are kept on purpose by the code's own comments (`.cluster.local`, AWS `compute.internal`, `.internal` / `.local` followed by more labels; redact.py:380-386) and stay as they are. `db01.corp.example` becomes `<HOSTNAME_1>.example` (15 partial). Whole name readable (13): a single-label host after `host` / `hostname=` / `--host`, a name with no private suffix (`db01.acme.example`), an underscore or non-ASCII label, `[.]` dots |
| 3 bare numbers | 43 | 24 not masked | NOT A GAP: accepted property by the old decision (order 64 item 4). Only written down and pinned |
| 4 corpus test | - | - | CUT: the 30-row hostile corpus is not in this repository; the probe script and G4's own tests are the permanent cases |

## NEEDED-CHECK and RUNG TABLE (CODE-LAST v1, scale of 2026-11-06)
Read: guard/runmap.py `_views` 401-414 (views: NFKC, JSON-unescape, percent/entity decode; no base64); guard/redact.py PATTERNS 153 on, HOSTNAME 380-399, `_KEPT_HOST` 934, HIGHENTROPY. Nothing in src decodes base64 for scanning (grep b64decode in guard/: no hit, survey 2). Verdict: NEEDED for gaps 1 and 2. One place per job: decoding for scanning lives beside the other views in runmap.py; host-name grammar stays in the HOSTNAME pattern in redact.py.
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| base64 scan | a secret that is only base64-encoded is found | 2 core: none; 4 library: Python stdlib `base64` is the decoder (no new dependency) | probe 2026-11-20 | decode tied to the redactor's own patterns and map | KEEP-CODE, small |
| whole host name | the full dotted name is masked | 2 core: HOSTNAME pattern exists, too narrow | probe | - | KEEP-CODE: a pattern change, not a new component |

## Design
### G4a base64 (guard/runmap.py, inside `_scan`, after the existing views)
1. Candidates: maximal runs of the base64 alphabets (standard and URL-safe, optional `=` padding) of at least `defaults.B64_MIN_CHARS` (16) characters; runs split by line breaks are also tried joined (wrapped blobs), up to the size cap.
2. A candidate counts only if it decodes strictly and the bytes are text: UTF-8, or UTF-16 with a byte-order mark or NUL-interleaved ASCII; at least 90 percent printable. Otherwise it is left alone (must-keep: hashes, ids, ordinary words that are base64-shaped).
3. The decoded text is redacted with the run's map by the same `redact()` the views use. If that finds anything (the map would grow, or the placeholder multiset changes), the WHOLE encoded run in the written text is replaced by one placeholder of kind ENCODED, stored like a SECRET (never restorable to a tool: not in STORED_KINDS). Nothing found: the run stays as written.
4. One level of nesting: if the decoded text is itself a candidate, it is decoded once more (double base64 was probed). Deeper: left to HIGHENTROPY. Budget and caps are those of `_scan`; over budget raises InputTooLarge as today.
5. `is_masked` sees it automatically (shared `_scan`).
Trade-off (BEST-FIRST): masking the whole blob loses the non-secret part of the blob; the simpler option (leave short blobs) is what leaks today. A new kind name ENCODED needs the lead's OK (generic word, no project word).

### G4b host names (guard/redact.py HOSTNAME pattern)
1. A name under a private suffix is masked WHOLE including any public-looking tail after the private label (`db01.corp.example` -> one placeholder; with port, in a URL, upper case, trailing dot, punycode, in JSON, after `host=`).
2. A single-label or non-private name directly after an explicit host key (`host`, `hostname`, `--host`, `server`, followed by `=`, `:` or space) is masked as HOSTNAME. Without such a key a non-private name (`db01.acme.example`) is NOT masked: it is indistinguishable from a public site (documented limit).
3. Labels with underscore or non-ASCII letters, and `[.]` dots, are accepted by the same pattern.
4. The four kept-on-purpose shapes stay kept (`_KEPT_HOST`), pinned by a test.

### G4c bare numbers
One sentence in the guard/redact.py module docstring: "A bare number with no label or context (for example `ref 55556666 paid`) is not masked, by decision; 10 to 16 contiguous digits and card-shaped groups are." Pinned by a test of the probe's 43 rows as they behave today. If a row differs at build time: report, change no pattern.

## Invariants
- G4-I1 every one of the 52 leaked base64 probe rows ends with no part of the protected value readable; the 90 non-leaked rows do not change.
- G4-I2 must-keep: base64 that decodes to text with nothing secret, hex digests, UUIDs, long ordinary words and the existing must-keep rows of the redactor suites are unchanged (no new false masking in any existing test).
- G4-I3 the 24 proven host rows are masked whole; the 4 kept rows and the 16 already-masked rows do not change; e-mail domains stay whole EMAIL.
- G4-I4 `redact_text(redact_text(t, m), m)` adds nothing for every probe row (the gate's round trip).
- G4-I5 cost: a 100,000-character text with no base64 run costs at most 10 percent more than before (perf mark, fixed ceiling measured at build); a text of 2,000 short base64 runs stays inside REDACT_BUDGET_S or raises InputTooLarge, never returns unmasked.
- G4-I6 an ENCODED placeholder is never put back by restore_text / restore_value.
Tests: new tests/test_p1c_gaps.py generated from evidence/p1c_probe.py's case builders (values built from parts), expected results per row as above; FAIL-BEFORE: the same file run on main fails exactly the 52 + 24 rows (recorded in the evidence file). Mutants: decode but mask only the found span inside the decoded text (killed by I1: the written blob must go); drop the wrapped-line join; accept non-text bytes; drop the host-key rule; unkeep `.cluster.local`.

## Files
Create: tests/test_p1c_gaps.py. Modify: src/hadavin_sdk/guard/runmap.py, src/hadavin_sdk/guard/redact.py (both TEXT's), src/hadavin_sdk/defaults.py (+2 constants; SPINE's file: separate commit). Migration: none.

## Evidence commands
`uv run --all-extras --group test ruff check <files>`; `... pytest tests/test_p1c_gaps.py -q`; then the existing redactor suites once (the files that import redact or runmap); `uv run --group scan bandit -q -r src/hadavin_sdk/guard -ll`. Raw output to evidence/G4-1.md.

## Lead decisions (recommended first)
1. New placeholder kind name ENCODED: OK?
2. Host key list `host, hostname, --host, server`: OK, or shorter?
3. Non-private names without a host key stay unmasked (documented limit): OK?

## NOT CHECKED
A 40+ character blob with no digit (HIGHENTROPY's digit rule); hex, base32, gzip forms; a non-empty run map; `redact_many`; behaviour on the fold head and with P2d-1's fold scan; the old plan's 30 hostile inputs (not available).
