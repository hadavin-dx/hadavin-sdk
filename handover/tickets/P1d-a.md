# Package ticket P1d-a: approval cards show e-mail addresses and internal host names unmasked (the `[.]` step runs before the redactor), and a password containing `&` shows the part after the `&`. DRAFT revision 5 (plan review round 4 resolved; round 5 next)

**Why over 250 lines:** this is a redaction-path ticket (no review cap) whose build is judged row by row: the rows, the mutants, the generator procedure and the 30 real-format corpus lines must be exact text a builder copies, and four review rounds found a defect each time a part was left to the builder. Prose was cut instead.

**Status (2026-11-09T08:41Z UTC; IST 14:11):** text only, no code, no pull request. Split from P1d by lead ORDER 177. **Base: `origin/main` `0dabf1fa7a2e`** (holds `tools/mutation_runner.py`). Prototype on `core/cloud-handover` `6d8699a`: `handover/evidence/P1d/rev8-probes/`; probe P6: `handover/evidence/P1d-a/probes-r4/`. Resolves: `handover/reviews/P1d-a/round1-resolve.md` to `round4-resolve.md`. Source: ledger rows BL-core-p1d-002 and 007; ORDER 177. Marker: CODE-LAST v1.

## The problem in plain words
Before a person sees an approval card, two steps run on its text: a cleaning step (the "gate") and a redactor that replaces secrets and personal data with placeholders such as `<EMAIL_1>`. The gate runs FIRST and writes every dot of a web address or host name as `[.]`, so a chat app does not turn it into a link. After that the redactor no longer recognises `anna.m@example[.]org` as an e-mail address or `db01[.]corp[.]example[.]com` as an internal host name, so both are shown in full. Separately, the redactor treats `&` as the end of a password, so `password=ab12&cd34ef56gh78ij` shows `cd34ef56gh78ij`, on cards and in text sent to the model.

## Words used (defined once)
- **Gate** = `approvals/gate.py::sanitise_text` plus `withhold_commands`, called through `channel._neutralise`. **Defang** = writing each `.` of a domain or host as `[.]`.
- **Redactor** = `guard/runmap.py::redact_text`, the one function every caller goes through to redact (the "choke point"); it runs the `neutralise` hook on its input and on each decoded view BEFORE redacting.
- **Card path** = `channel.clean` and `SlackChannel._blocks`. **Model path** = `redact_text` with no `neutralise`.
- **Prose part** = text outside the body lines of a closed backtick fence and outside inline code (split by `_closed_fences` and `_INLINE_CODE`, as the gate does).
- **Query form** = an assignment whose key comes right after `?`, `&` or `&amp;` (`?password=x&next=/home`). **Plain form** = any other assignment (`password=x` in a config line or a message).
- **`&amp;` unit** = the five characters `&amp;` read as one character of a value (D2).
- **Over-mask** = text that is not secret but is hidden because it follows a secret (accepted by ORDER 166 item 2; measured apart from leaks). **Leak** = see BS-1.
- **Idempotent** = running it twice gives the same text as once. **Lookbehind / look-ahead** = a regex condition on the characters just before / after a position.
- Row classes: **fb** = fails on the base, passes after; **pb** = passes on the base with the same output; **ow** = accepted over-mask, counted.

## Code facts (R = read on `0dabf1f` by symbol; P = probe)
- R0: between `6d8699a` and main, `gate.py` differs only in its header, `channel.py` and `slack_channel.py` not at all, `redact.py` in two unrelated `_COMMON` words, `runmap.py` by 54 lines. BS-0 re-runs every row on main.
- R1: `channel._neutralise(text) = withhold_commands(sanitise_text(text))`. `clean` redacts the text, and when tags were removed also the joined view, and returns `alt` or `out`; it calls `runmap.redact_text` through the module. `SlackChannel._blocks(req, approver_ids)`: `withhold_commands(req.summary)`, then `redact_text(..., neutralise=_neutralise)`, then the `max_card_chars` length check.
- R2: `_clean_line` ends with `return _defang_outside_code(line)`; before that it rewrites a character reference with `_ENTITY` (`&name;` -> `&amp;name;`, `&amp;` itself left). `_clean_line` runs on prose lines (`_clean_prose`), the fence opener's info string and `~~~` fence bodies; backtick fence bodies and inline code are never defanged. `sanitise_text` reaches lines through `_clean_prose` (head and tail of each fence), the info string, the `~~~` body and two `_all_prose` fallbacks (opener or closer not matched; output fences differ from the plan), both written `return _all_prose(lines)`. `_clean_prose` prefixes a zero-width space (ZWSP, U+200B) to a CHANGED line that matches `_ANY_BLOCK` (heading, quote, list item incl. `1.`, fence, indented code), so it starts no block. `_defang_outside_code` treats a line holding a double backtick as all prose. `sanitise_text` has no other caller in `src`; `_clean_line`, `_clean_prose`, `_all_prose`, `_defang_outside_code` have no caller outside `gate.py`.
- R3: generic assignment SECRET entry in `redact.py`: key `(?i)(?<![\w.\-])[\w.\-]{0,40}(?:password|...)[\w.\-]{0,20}[\"']?\s*[:=]\s*[\"']?`; value `((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=]))+)`; its comment is lines 609-614. Pinned: `tests/warden_port/test_redaction.py::test_query_param_credentials_are_masked` (`?password=SuperSecretPw99&next=/home` keeps `/home`); ORDER 180 q392-6 keeps it unchanged.
- R4: `redact()` applies `PATTERNS` in order with `pattern.sub`: the order of two overlapping entries decides the result.
- R5: `redact` is imported into runmap by name; a spy patches `hadavin_sdk.guard.runmap.redact`. `redact_text` fills the caller's map in place.
- R6 (siblings of "`&` ends a value"): hex-key entry (`[0-9a-f]{32,}`), HIGHENTROPY (base64 alphabets), AZURESAS `sig=` (a query value by grammar), `_PIECE` (splits a learned secret: only adds masks): not siblings. Row KV1 pins the whole known value.
- R7 (readers of a stored `req.summary` in `src` and `demos`): `FakeChannel.send` (`clean(req.summary)`, a test fake fed by current code) and `SlackChannel._blocks`. `clean` does not undo `[.]`, so any other reader of a stored summary is a BS-0 STOP.
- R8: `tools/mutation_runner.py` lines 73-88 and 365-376: `Mutant(name, file, old, new, expect, allow_crash, crash_type, crash_markers, test_file, pinned, only_test)`; `expect` is a fragment (4+ characters) of the failing assertion message; `pinned` is written `tests/test_x::test_y`; `run_mutants` has no `forbid_skips` yet (ORDER 181). `tools/` is a package (`tools/__init__.py`). `/home/user/build/heavy.sh` runs `"$@"`: an environment assignment needs `env`.
- P1 (base): H26 card `contact anna.m@example[.]org please`; H27 card `host db01[.]corp[.]example[.]com down`; H34a both paths `password=<SECRET_1>&cd34ef56gh78ij`; H34b `password=<SECRET_1>&amp;4xKp2Vb9Lr3NcW8dYh6uJs`.
- P2 (prototype of the flag, the `clean` change and the `&` split only): H26 `contact <EMAIL_1> please`; H27 `host <HOSTNAME_1>.example.com down` (hence D3); H34a-c masked whole; with `&` allowed in both forms the pinned query test failed (hence D2).
- P3 (base, `round3-resolve.md`): card of `password=ab12&cd34ef56; next` = `password=<SECRET_1>&amp;cd34ef56; next`; model `password=<SECRET_1>&cd34ef56; next`. P5 (base Slack): L13-L16 inputs shown unchanged.
- P6 (`probes-r4/`, round 4 resolver): `0dabf1f`'s `src` with its SECRET entry replaced by the two D2 entries exactly as in Code shape; model path and card (base gate, so D1 absent; these inputs hold no dot). Every "expected after" of the rows H34a-d, Q2-Q17, KV1, ENT, F16, F17, SC1, NE1, PU1 came out as written, including the placeholder numbers; the 30 REAL lines: 0 mismatches (the rev-4 grammar: 1 line, base: 20). D1, D3, `undefang_text`: designed, NOT probed; proven by rows and mutants.

## Design
- **D1 Defang after the redactor.** `sanitise_text(text, *, defang: bool = True)`; the internal helpers take `defang` as a REQUIRED argument (`_clean_line(line, defang)`, `_clean_prose(lines, defang)`, `_all_prose(lines, defang)`), so a call site that forgets it raises `TypeError` when it runs, and a row reaches every call site (PF1, PF2, E1, I2, FB1, FB2, H26). With `defang=False` `_clean_line` skips defang. **ZWSP rule kept:** with `defang=False` the "changed" test and the block test read `d = _defang_outside_code(c)`, so every line that gets a ZWSP today still gets one (Z1-Z4). `channel._neutralise` passes `defang=False`. New `gate.defang_text(text)`: fences are read on the FINAL text (what a renderer reads); body lines of a closed backtick fence stay as they are; on every prose part, in this order: wide dots to `.`, D3, `_NON_ASCII_HOST`, `_DOMAIN`. The default `sanitise_text` keeps today's defang without D3 (`_defang_outside_code` keeps its expression, now through `_per_part`). New `gate.undefang_text(text)`: on prose parts only, `[.]` between two name characters becomes `.` (the old gate wrote `[.]` only there). `clean` returns `defang_text(alt)` or `defang_text(out)`. `_blocks`: (1) `undefang_text(req.summary)` (summaries stored by the old code hold defanged, unmasked addresses); (2) `withhold_commands`; (3) `redact_text`; (4) `defang_text`; (5) length check on the shown text. Model path unchanged.
- **D2 `&` follows the URL query grammar.** The generic entry becomes two, same kind, PLAIN FIRST then QUERY (R4). Plain: key lookbehinds `(?<![\w.\-?&])(?<!&amp;)`; value as today with `&` and the `&amp;` unit allowed (stops at white space, quote, `;`, the comma rule). Query: key lookbehind `(?:(?<=[?&])|(?<=&amp;))` (a key after `&amp;`, as in an HTML-escaped address, is a query key: row Q15); value as today plus the alternative `&(?![^\s&#\"'=]*=)`: it continues past `&` unless the next segment (up to `&`, white space, `#` or a quote) holds `=`. Basis: in `application/x-www-form-urlencoded` `&` separates pairs and a literal `&` is `%26` (WHATWG URL Standard, section 5.1: UNVERIFIED, the network refused the page on 2026-11-09; BS-0 step 8 reads it and records the date). **`&amp;` unit:** the gate writes `&name;` as `&amp;name;` (R2), and `;` ends a value, so without it the card showed the part after `&` (P3). Plain reads `&amp;` as one character always; query reads it with the same `key=value` test as `&`: `&amp;(?![^\s&#\"'=]*=)`. Both are tried before the single-character class. The fix sits in the redactor (all callers), not in the gate (whose rewrite is a reviewed defence).
- **D3 Placeholder next to a dot.** The redactor masks only the internal part of a host (`<HOSTNAME_1>.example.com`), and `_DOMAIN` does not start a name after `.`, so `example.com` would stay (linking by Slack or GFM: UNVERIFIED; defanged on the safe side). `_PLACEHOLDER_DOT` writes `<KIND_n>.` + name character as `<KIND_n>[.]`. `\w` is Unicode. No left boundary (more defang, never less). `<A_1>.<B_2>` unchanged.

### Code shape (exact text the mutants edit; ruff may reflow it: the builder keeps the tokens and sets each mutant's `old` to the formatted text, still unique)
```python
# src/hadavin_sdk/approvals/gate.py   (imports: from collections.abc import Callable)
_PLACEHOLDER_DOT = re.compile(r"(<[A-Z][A-Z0-9]*_[0-9]+>)\.(?=[\w-])")
_LEGACY_DOT = re.compile(r"(?<=[\w-])\[\.\](?=[\w-])")
def _defang_plain(part: str) -> str:
    return _DOMAIN.sub(_defang, _NON_ASCII_HOST.sub(_defang, _WIDE_DOTS.sub(".", part)))
def _defang_prose(part: str) -> str:
    part = _WIDE_DOTS.sub(".", part)
    part = _PLACEHOLDER_DOT.sub(r"\1[.]", part)
    return _defang_plain(part)
def _per_part(line: str, fix: Callable[[str], str]) -> str:
    parts = [line] if "``" in line else _INLINE_CODE.split(line)
    return "".join(part if i % 2 else fix(part) for i, part in enumerate(parts))
def _defang_outside_code(line: str) -> str:        # docstring kept; body:
    return _per_part(line, _defang_plain)
def _outside_code(text: str, fix: Callable[[str], str]) -> str:
    body = {i for s, e, ch in _closed_fences(text) if ch == "`" for i in range(s + 1, e)}
    return "\n".join(line if i in body else _per_part(line, fix) for i, line in enumerate(text.split("\n")))
def defang_text(text: str) -> str:
    return _outside_code(text, _defang_prose)
def undefang_text(text: str) -> str:
    return _outside_code(text, lambda part: _LEGACY_DOT.sub(".", part))
# def _clean_line(line: str, defang: bool) -> str: ... last line:   return _defang_outside_code(line) if defang else line
# def _clean_prose(lines: list[str], defang: bool) -> list[str]:   out = [_clean_line(line, defang) for line in joined]
#   seen = out if defang else [_defang_outside_code(c) for c in out]
#   out = ["​" + c if _ANY_BLOCK.match(d) and not (same and d == lines[i]) else c for i, (c, d) in enumerate(zip(out, seen, strict=True))]
# def _all_prose(lines: list[str], defang: bool) -> str:            return "\n".join(_clean_prose(lines, defang))
# def sanitise_text(text: str, *, defang: bool = True) -> str:
#   if not opener or not closer: return _all_prose(lines, defang)
#   out += _clean_prose(lines[pos:start], defang) ; _clean_line(opener.group(3), defang) ; [_clean_line(line, defang) for line in body]
#   out += _clean_prose(lines[pos:], defang) ; (fences differ) return _all_prose(lines, defang) / return result
# src/hadavin_sdk/approvals/channel.py: return withhold_commands(sanitise_text(text, defang=False)) ; return defang_text(alt) ; return defang_text(out)
# src/hadavin_sdk/approvals/slack_channel.py: withheld = withhold_commands(undefang_text(req.summary))
#   shown = defang_text(runmap.redact_text(withheld, seeded, neutralise=_neutralise))
# src/hadavin_sdk/guard/redact.py plain key:  r"(?i)(?<![\w.\-?&])(?<!&amp;)[\w.\-]{0,40}" + the R3 key alternation and tail, unchanged
# plain value:  ((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|&amp;|[^\s\"';,]|,(?!\s*[\w.\-]+\s*[:=]))+)
# query key:    r"(?i)(?:(?<=[?&])|(?<=&amp;))[\w.\-]{0,40}" + the same key alternation and tail
# query value:  ((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|&amp;(?![^\s&#\"'=]*=)|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=])|&(?![^\s&#\"'=]*=))+)
# redact.py comment: the sentence "`&` stops a URL query-param value at the next parameter." (lines 610-611) becomes:
#   "Plain form: `&` is part of the value. Query form (key right after `?`, `&` or `&amp;`): `&` ends the value only
#    before a `name=value` segment, as in application/x-www-form-urlencoded. `&amp;` is one character of the value
#    in both: the approval gate writes `&name;` as `&amp;name;` before redaction."
```

## RUNG TABLE (2026-11-06 scale: 1 no-code, 2 own core modules, 3 existing free tools, 4 free libraries, 5 own new code last)
Rung test: core change, no client, no fee, no new dependency; rung 1 closed (R447: inside the choke point). **exact** = holds for every input of a named set, checked by a test over that set; **best effort** = tested rows only.
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| defang order | the redactor sees `.` before `[.]` is written | 2 (existing defang helpers behind a flag) | R1, R2, P2 | one flag, one call order | exact on G-EH (`test_card_masks_what_model_masks`); best effort beyond | CUT-TO-CONFIG+GLUE |
| placeholder-dot rule | no linkable remainder after a masked host | 2 (`runmap.PLACEHOLDER` shape, existing defang) | designed, not probed | one substitution | exact on G-TXT for the shape placeholder + `.` + name character; renderer linking UNVERIFIED | CUT-TO-CONFIG+GLUE |
| legacy undo | stored summaries masked too | 2 (same split as defang) | R7, P5 | one substitution | exact on rows L7, L10-L16 and `test_stored_card_round_trip` | CUT-TO-CONFIG+GLUE |
| `&` in a value | mask a password containing `&` | 2 (existing entry split); 4 detect-secrets/gitleaks do not run inside our run map (UNVERIFIED) | R3, P2, P3, P6 | the query/plain split and the `&amp;` unit | exact on corpus BS-1 shapes S1-S6, S2x, S5x and REAL; best effort beyond | KEEP-CODE (one entry) |
**80 percent (R448):** all needs met by existing code moved or split; no new module. Cost estimate: build 3-4 agent-hours; 0 fees, 0 model tokens.

## Goals and Non-Goals
**Goals.** (G1) E-mail addresses and internal host names are masked on cards as on the model path, including requests stored before the fix. (G2) No linkable name outside code in the FINAL card text. (G3) In plain form `&` no longer ends a password: the value runs to the first white space, quote, `;` or comma that starts `key=value`, as today (`password=ab&cd34;ef56` hides `ab&cd34` and shows `;ef56`, row SC1). In query form a value ends at `&` or `&amp;` only before a `key=value` segment. The card hides exactly what the model path hides for these values, including where the gate rewrote `&name;` (H34d, Q12, NE1). (G4) Card structure and command withholding unchanged (exact differential; the new card may withhold more, never less).
**Non-Goals.** (N1) Addresses split by formatting (H28a-b): P1d (ORDER 180). (N2) Over-mask in plain form (`password=hunter22&user=bob` hides `&user=bob`; `password=&user=bob` hides `&user=bob`) and of `=`-less query segments: accepted, measured by BS-1. (N3) Which names count as hosts. (N4) A query secret holding `&name=` is read as two fields, as the URL grammar says; the part after `&name=` is shown (measured as S7, not gated). (N5) A host written with wide dots is not recognised as a host on either path (it is defanged on the card): NEEDS LEAD 2.

## Failing inputs (`tests/test_p1d_a_rows.py`; literals in `tests/fixtures/p1d_cases.py`, built from parts: EM = `"anna" + "." + "m" + "@" + "example" + "." + "org"`, SV_A = `"Tq7mZ"`, SV_B = `"4xKp2Vb9Lr3NcW8dYh6uJs"`; H34 requires SV_A and SV_B masked as ONE value)
**How to read a row:** cells are Python string bodies; `\n` and `​` (ZWSP) are escapes; `\|` is a plain `|` (Markdown escape). Where two paths are listed the string holds for both. BS0 = filled by BS-0 (rules in BS-0). Entries: card = `channel.clean(x)`; slack = `SlackChannel._blocks(req, None)[0]["text"]["text"]` with `SlackChannel.__new__`, `max_card_chars = 2900`, `req = SimpleNamespace(summary=x, current_step=0, steps=[1], approval_id="a", status="PENDING")` (as `tests/test_k5_round11.py::test_the_slack_block_never_shows_a_decoded_view_that_was_not_sanitised`); model = `runmap.redact_text(x, runmap.RunMap())`; defang = `gate.defang_text(x)`; gate = `gate.sanitise_text(x, defang=False)` with the patch named in the row.
**Test layout:** one function per row and entry, `test_row_<id>_<entry>` (for example `test_row_H26_card`, `test_row_D3a_defang`); every assertion message starts `ROW <id> <entry>:` (mutant `expect`). A call that reaches a name the base lacks (`defang_text`, `undefang_text`, the `defang` argument) goes through one helper that fails with `NEW_SURFACE: <name>`. Imports: `from hadavin_sdk.approvals import channel, gate, slack_channel`; `from hadavin_sdk.guard import runmap`; `from tests.fixtures import p1d_cases`.
| row | class | entry | input | on base | expected after |
|---|---|---|---|---|---|
| H26 | fb | card | `contact <EM> please` | `contact anna.m@example[.]org please` | `contact <EMAIL_1> please` |
| H27 | fb | card | `host db01.corp.example.com down`; spy R5 | `host db01[.]corp[.]example[.]com down` | `host <HOSTNAME_1>[.]example[.]com down`; spy: some call's text holds `db01.corp.example.com`, none holds `[.]` |
| H36a | fb | card | `anna%2Em%40example%2Eorg` | same as input | `<EMAIL_1>` |
| H36b | fb | card | `anna&#46;m&#64;example&#46;org` | `anna&amp;#46;m&amp;#64;example&amp;#46;org` | `<EMAIL_1>` |
| E1 | fb | card | `~~~\nmail <EM>\n~~~` | BS0 | `~~~\nmail <EMAIL_1>\n~~~` |
| I2 | fb | card | "```mail <EM>\nx\n```" | BS0 | "```mail <EMAIL_1>\nx\n```" |
| PF1 | fb | card | "mail <EM>\n```\nx\n```" | BS0 | "mail <EMAIL_1>\n```\nx\n```" |
| PF2 | fb | card | "```\nx\n```\nmail <EM>" | BS0 | "```\nx\n```\nmail <EMAIL_1>" |
| FB1 | fb | gate; patch `gate._closed_fences` to `lambda text: [(0, 1, "`")]` (forces the first fallback) | `mail evil.com\nx` | `NEW_SURFACE` | `mail evil.com\nx` |
| FB2 | fb | gate; patch as `test_gate_review3.py::test_output_whose_fences_differ_from_the_plan_is_all_prose` (first call real, later `[]`; forces the second fallback) | "```\nmail evil.com\n```" | `NEW_SURFACE` | asserts: `mail evil.com` present, no `[.]`, no "```" |
| L7 | fb | slack | `contact anna.m@example[.]org please` | same as input | `contact <EMAIL_1> please` |
| L16 | fb | slack | `see //evil[.]com/p now` | same as input (P5) | `see [link removed] now` |
| H34a | fb | card, model | `password=ab12&cd34ef56gh78ij` | `password=<SECRET_1>&cd34ef56gh78ij` | `password=<SECRET_1>` |
| H34b | fb | card, model | `password=<SV_A>&amp;<SV_B>` | `password=<SECRET_1>&amp;<SV_B>` | `password=<SECRET_1>` |
| H34c | fb | card, model | `password=<SV_A>&<SV_B> end` | `password=<SECRET_1>&<SV_B> end` | `password=<SECRET_1> end` |
| H34d | fb | card, model | `password=ab12&cd34ef56; next` | card `password=<SECRET_1>&amp;cd34ef56; next`; model `password=<SECRET_1>&cd34ef56; next` (P3) | `password=<SECRET_1>; next` |
| SC1 | fb | card, model | `password=ab&cd34;ef56` | card `password=<SECRET_1>&amp;cd34;ef56`; model `password=<SECRET_1>&cd34;ef56` (P6) | `password=<SECRET_1>;ef56` |
| PU1 | fb | card, model | `password=ab&amp; x` | `password=<SECRET_1>&amp; x` (P6) | `password=<SECRET_2> x` |
| Q4 | fb | card, model | `?password=ab&cd34ef56&user=bob x` | BS0 | `?password=<SECRET_1>&user=bob x` |
| Q5 | fb | model | `?password=ab&cd34ef56` | BS0 | `?password=<SECRET_1>` |
| Q8 | fb | model | `?password=ab&amp;cd34ef56&amp;user=bob x` | BS0 | `?password=<SECRET_1>&amp;user=bob x` |
| Q10 | fb | model | `?password=ab&cd34#x=1 y` | BS0 | `?password=<SECRET_1> y` |
| Q11 | fb | model | `?password=ab&cd34 x=1` | BS0 | `?password=<SECRET_1> x=1` |
| Q12 | fb | card, model | `?password=ab&cd34; x` | card `?password=<SECRET_1>&amp;cd34; x`; model `?password=<SECRET_1>&cd34; x` (P3) | `?password=<SECRET_1>; x` |
| Q14 | fb | card, model | `?user=bob&password=ab&cd34ef56 x` | `?user=bob&password=<SECRET_1>&cd34ef56 x` (P6) | `?user=bob&password=<SECRET_1> x` |
| Q16 | fb | card, model | `?password=ab&cd34"x=1 y` | `?password=<SECRET_1>&cd34"x=1 y` (P6) | `?password=<SECRET_1>"x=1 y` |
| Q17 | fb | model | `?password=ab&amp;cd34"x=1 y` | `?password=<SECRET_1>&amp;cd34"x=1 y` (P6) | `?password=<SECRET_1>"x=1 y` |
| KV1 | fb | model | `password=ab12&cd34ef56gh78ij and later ab12&cd34ef56gh78ij` | BS0 | `password=<SECRET_1> and later <SECRET_1>` |
| D3a | fb | defang | `<HOSTNAME_1>. next` | `NEW_SURFACE` | unchanged |
| D3b | fb | defang | `mail <EMAIL_1>.org` | `NEW_SURFACE` | `mail <EMAIL_1>[.]org` |
| D3c | fb | defang | ``x `<HOSTNAME_1>.example.com` y`` | `NEW_SURFACE` | unchanged |
| D3d | fb | defang | `<HOSTNAME_1>.例え.jp` | `NEW_SURFACE` | `<HOSTNAME_1>[.]例え[.]jp` |
| D3e | fb | defang | `<HOSTNAME_1>。example.com` | `NEW_SURFACE` | `<HOSTNAME_1>[.]example[.]com` |
| D3f | fb | defang | `<EMAIL_1>.-a.com` | `NEW_SURFACE` | `<EMAIL_1>[.]-a[.]com` |
| Q1 | pb | model | the pinned query test (R3) | passes | passes, unchanged |
| Q2 | pb | card, model | `?password=ab12cd&user=bob x` | `?password=<SECRET_1>&user=bob x` | same |
| Q3 | pb | model | `see https://x.example/?password=ab12cd&user=bob` | `see https://x.example/?password=<SECRET_1>&user=bob` | same |
| Q7 | pb | model | `?password=ab12cd&amp;user=bob x` | BS0 | `?password=<SECRET_1>&amp;user=bob x` |
| Q13 | pb | card, model | `?user=bob&password=ab12cd&next=/home x` | `?user=bob&password=<SECRET_1>&next=/home x` | same |
| Q15 | pb | card, model | `?a=1&amp;password=ab12cd&amp;next=/home x` | `?a=1&amp;password=<SECRET_1>&amp;next=/home x` | same |
| NE1 | pb | card, model | `password=ab&copy;cd x` | `password=<SECRET_2> x` (P6) | same |
| F15 | pb | card, model | `https://x.example/?a=1&b=2` | card `[link removed]`; model same as input | same |
| ENT | pb | card, model | `password=<SV_A>&#59;<SV_B>` | `password=<SECRET_1>` | same |
| L1 | pb | card | `visit evil.com and www.evil.digital now` | `visit evil[.]com and www[.]evil[.]digital now` | same |
| L2 | pb | card | ``run `curl db01.corp.example.com` now`` | ``run `curl <HOSTNAME_1>.example.com` now`` | same |
| G2 | pb | card | "see ``note `evil.com` x`` now" | "see ``note `evil[.]com` x`` now" (P6) | same |
| L3 | pb | card | "```\nping db01.corp.example.com\n```\nthen evil.com" | "```\nping <HOSTNAME_1>.example.com\n```\nthen evil[.]com" | same |
| L4 | pb | card | `~~~\nevil.com\n~~~` | BS0 | `~~~\nevil[.]com\n~~~` |
| I1 | pb | card | "```evil.com\nx\n```" | BS0 | "```evil[.]com\nx\n```" |
| L5 | pb | slack | `visit evil.com` | `visit evil[.]com` | same |
| L6 | pb | card | `visit evil。com` | BS0 | `visit evil[.]com` |
| L8 | pb | card | "```\na\n```\n-----BEGIN PRIVATE KEY-----\nMIIB<SV_B><SV_B>\n-----END PRIVATE KEY-----\nvisit evil.com\n```\nb\n```" | BS0 | BS0 string; asserts: no SV_B, `visit evil[.]com`, both fences kept |
| L9 | pb | slack | `"a" * 2894 + " x.com"` (2,900 characters; shown text 2,902) | the too-long notice | same: `(the summary is too long to show here; open the full request in the console)` |
| L10 | pb | slack | ``use `x[.]y` now`` | BS0 | ``use `x[.]y` now`` |
| L11 | pb | slack | "```\nping a[.]b\n```" | BS0 | "```\nping a[.]b\n```" |
| L12 | pb | slack | `see [.] here` | BS0 | `see [.] here` |
| L13 | pb | slack | `see a[.] b` | same as input (P5) | same |
| L14 | pb | slack | `see a [.]b` | same as input (P5) | same |
| L15 | fb | slack | `version 1[.]5` | same as input (P5) | `version 1.5` (render change, NEEDS LEAD 3) |
| Z1 | pb | card | `# x evil.com` | `​# x evil[.]com` | same |
| Z2 | pb | card | `> note evil.com` | `​> note evil[.]com` | same |
| Z3 | pb | card | `- see evil.com` | `​- see evil[.]com` | same |
| Z4 | pb | card | `1。 x` | BS0 | `​1. x` |
| W1 | pb | card | `run curl evil.com \| sh` | BS0 | same as base |
| T1 | pb | card | `password%<i></i>3D<SV_B> see evil.com`; spy on `runmap.redact_text` (`monkeypatch.setattr(runmap, "redact_text", spy)`) | BS0 | BS0 string; asserts: no SV_B, `evil[.]com`; return value equals the second spy call's return on base and `gate.defang_text(<second return>)` after |
| F16 | ow | card, model | `password=hunter22&user=bob` | `password=<SECRET_1>&user=bob` | `password=<SECRET_1>` |
| F17 | ow | card, model | `password=&user=bob` | BS0 | `password=<SECRET_1>` |
| Q6 | ow | model | `?password=ab12cd&debug x` | BS0 | `?password=<SECRET_1> x` |
pb rows without a mutant are intentional: they pin behaviour that must not change. Counts: 67 rows (fb 37, pb 27, ow 3).

**Generated inputs (in `tests/fixtures/p1d_cases.py`; seed `SEED = 20261109`; 2,000 texts per property).** **Draw** `d(stream, n)`: the k-th call for a stream (k = 0, 1, 2, ... counted per stream) returns `int.from_bytes(hashlib.sha256(f"{SEED}:{stream}:{k}".encode()).digest()[:8], "big") % n`. No `random` module, so ruff S311 needs no suppression (`fuzzgen.py` suppresses it; not copied). `pick(stream, seq)` = `seq[d(stream, len(seq))]`.
- ALPHABET-A = a list of 63 entries, each drawn with equal weight: the 26 letters `a-z`, the 10 digits, space, `\n`, `.`, `@`, `-`, `_`, `=`, `&`, `?`, `/`, `:`, `#`, `>`, `*`, `[`, `]`, `<`, `é`, `例`, the backtick, U+3002, U+FF0E, U+FF61, and the tokens "```", `~~~`, `[.]`, `evil.com`, `www.evil.digital`, `db01.corp.example.com`, EM, `<HOSTNAME_1>`, `<EMAIL_1>`, `password=`, `?password=`, SV_B, `-----BEGIN PRIVATE KEY-----` (the builder asserts `len == 63`). ALPHABET-B = ALPHABET-A without `[`, `]`, `[.]`, U+3002, U+FF0E, U+FF61 (57 entries).
- G-TXT text (stream `TXT-A`) and G-TXT-B text (stream `TXT-B`): `n = d(s, 201)`; then `n` times `pick(s, ALPHABET)`; entries concatenated with no joiner.
- G-EH text (stream `EH`): `lines = 1 + d(s, 3)`; per line `words = 1 + d(s, 6)`; per word `k = d(s, 4)`: 0 or 1 a word of `1 + d(s, 8)` letters, 2 an address `w(3-8) + "." + w(1) + "@" + "example" + "." + "org"`, 3 a host `"db" + digit + digit + "." + "corp" + "." + "example" + "." + "com"`; `w(a-b)` = `a + d(s, b - a + 1)` letters, each `pick(s, "abcdefghijklmnopqrstuvwxyz")`; digit = `pick(s, "0123456789")`; words joined by one space, lines by `\n`.
- LIT = every string literal passed DIRECTLY as an argument to `sanitise_text`, `clean` or `withhold_commands` in `tests/warden_port/test_gate.py`, `test_gate_render.py`, `test_gate_review2.py`, `test_gate_review3.py`, `tests/test_g4_parity.py`, `test_k5_round9.py`, `test_k5_round11.py`, `test_p5p6_followups.py`, collected by AST (parametrised and computed inputs are not collected; the count is printed in `bs0-base.txt`).
**Property tests:** `test_defang_text_idempotent` (G-TXT); `test_defang_text_only_rewrites_dots` (G-TXT-B: `defang_text(x).replace("[.]", ".") == x`); `test_sanitise_text_default_unchanged` (LIT: `sanitise_text(x) == sanitise_text(x, defang=True) == frozen[x]`, message `DEFAULT CHANGED`); `test_pre_redaction_differential` (LIT and G-TXT; left = `defang_text(withhold_commands(sanitise_text(x, defang=False)))`, right = `defang_text(withhold_commands(sanitise_text(x)))`, the same final step as D1 on both sides; compared line by line; a line may differ only when the left line holds `WITHHELD`, the right line does not, and the right line starts with the left line's text before `WITHHELD`; any other difference is a defect, message `DIFFERENTIAL`); `test_no_link_outside_code_on_card` (G-TXT: in markdown-it's token stream of the final `clean(x)`, no `text` token outside code matches `_DOMAIN`, `_NON_ASCII_HOST`, `_PLACEHOLDER_DOT` or `_WIDE_DOTS`); `test_card_masks_what_model_masks` (G-EH: no EMAIL or HOSTNAME original in the model path's map occurs in `clean(x).replace("[.]", ".")`); `test_stored_card_round_trip` (G-TXT-B, texts with `len(clean(x)) <= 2900`: the slack entry for `summary=clean(x)` equals `clean(x)`, message `ROUND TRIP`; G-TXT-B because a typed `[.]` is read as `.` by design, L15).
**When a row or a property fails after build:** the builder may change product code to meet it. If the builder judges the expected string, seed, count, alphabet, allowed difference or assertion wrong, it STOPS and sends the lead the row id (or seed and index), input, output and expected string; it edits none of them. They change only by a ticket revision.
**Time:** the file's run time is recorded at fail-before (base) and after build; target at most 300 s on the cloud machine; over that, the number goes to the lead (no silent cut of the counts).
**Must stay green unchanged:** `tests/test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook`, `tests/warden_port/test_redaction.py::test_query_param_credentials_are_masked`, `tests/warden_port/test_gate_review3.py::test_output_whose_fences_differ_from_the_plan_is_all_prose`.

## Mutation plan (`tests/p1d_a_mutants.py`; every mutant required; a survivor is a defect unless the lead accepts a written equivalence)
Registration, as `tests/stage_mutants.py`: one `tools.mutation_runner.Mutant` per row below with `file` = the full path, `old`/`new` as written, `expect = "ROW <id> <entry>:"` (or the property message), `only_test` = the killer, `pinned = "tests/test_p1d_a_rows::" + only_test`; then `run_mutants(ROOT, M, ["tests/test_p1d_a_rows.py"], extra_dirs=("tests", "tools"), only=sys.argv[1:], on_result=..., forbid_skips=True)`; exit 1 if any is not good. **Depends on the R1 runner PR (ORDER 181) for `forbid_skips`:** the mutant evidence is run after R1 merges and P1d-a is rebased, or on the R1 branch; the evidence names which. Files: GATE = `src/hadavin_sdk/approvals/gate.py`, CH = `src/hadavin_sdk/approvals/channel.py`, SL = `src/hadavin_sdk/approvals/slack_channel.py`, RD = `src/hadavin_sdk/guard/redact.py`, RM = `src/hadavin_sdk/guard/runmap.py`. An `old` shown with `\n` includes the line before as an anchor. QLB = `(?:(?<=[?&])|(?<=&amp;))`; QAMP = `&(?![^\s&#\"'=]*=)`.
| mutant | file :: symbol | exact edit (`old` -> `new`) | killer (`only_test`) |
|---|---|---|---|
| A1 | CH :: `_neutralise` | `sanitise_text(text, defang=False)` -> `sanitise_text(text)` | `test_row_H26_card` |
| A2 | CH :: `clean` | `return defang_text(out)` -> `return out` | `test_row_L1_card` |
| A11 | CH :: `clean` | `return defang_text(alt)` -> `return alt` | `test_row_T1_card` |
| A3 | SL :: `_blocks` | `shown = defang_text(runmap.redact_text(withheld, seeded, neutralise=_neutralise))` -> `shown = runmap.redact_text(withheld, seeded, neutralise=_neutralise)` | `test_row_L5_slack` |
| A3b | SL :: `_blocks` | `withhold_commands(undefang_text(req.summary))` -> `withhold_commands(req.summary)` | `test_row_L7_slack` |
| A3c | SL :: `_blocks` | `if len(shown) > self.max_card_chars` -> `if len(shown.replace("[.]", ".")) > self.max_card_chars` | `test_row_L9_slack` |
| A3d | GATE :: `undefang_text` | `return _outside_code(text, lambda part: _LEGACY_DOT.sub(".", part))` -> `return _LEGACY_DOT.sub(".", text)` | `test_row_L10_slack` |
| A3e | GATE :: `_LEGACY_DOT` | `r"(?<=[\w-])\[\.\](?=[\w-])"` -> `r"\[\.\]"` | `test_row_L12_slack` |
| A3f | GATE :: `_LEGACY_DOT` | `r"(?<=[\w-])\[\.\](?=[\w-])"` -> `r"\[\.\](?=[\w-])"` | `test_row_L14_slack` |
| A3g | GATE :: `_LEGACY_DOT` | `r"(?<=[\w-])\[\.\](?=[\w-])"` -> `r"(?<=[\w-])\[\.\]"` | `test_row_L13_slack` |
| A4 | GATE :: `_defang_prose` | `part = _PLACEHOLDER_DOT.sub(r"\1[.]", part)` -> `part = part` | `test_row_H27_card` |
| A17 | GATE :: `_defang_prose` | `part = _WIDE_DOTS.sub(".", part)\n    part = _PLACEHOLDER_DOT.sub(r"\1[.]", part)` -> `part = _PLACEHOLDER_DOT.sub(r"\1[.]", part)\n    part = _WIDE_DOTS.sub(".", part)` | `test_row_D3e_defang` |
| A41 | GATE :: `_PLACEHOLDER_DOT` | `_[0-9]+>)\.(?=[\w-])"` -> `_[0-9]+>)\.(?=\w)"` | `test_row_D3f_defang` |
| A42 | GATE :: `_PLACEHOLDER_DOT` | `_[0-9]+>)\.(?=[\w-])"` -> `_[0-9]+>)\.(?=-)"` | `test_row_D3b_defang` |
| A5 | GATE :: `_per_part` | `parts = [line] if "``" in line else _INLINE_CODE.split(line)` -> `parts = [line]` | `test_row_L2_card` |
| A43 | GATE :: `_per_part` | `parts = [line] if "``" in line else _INLINE_CODE.split(line)` -> `parts = _INLINE_CODE.split(line)` | `test_row_G2_card` |
| A38 | GATE :: `_per_part` | `part if i % 2 else fix(part)` -> `fix(part) if i % 2 else part` | `test_row_L2_card` |
| A6 | GATE :: `_outside_code` | `for s, e, ch in _closed_fences(text)` -> `for s, e, ch in []` | `test_row_L3_card` |
| A37 | GATE :: `_outside_code` | `if ch == "`"` -> `if ch in "`~"` | `test_row_L4_card` |
| A12 | GATE :: `_outside_code` | `range(s + 1, e)` -> `range(s, e)` | `test_row_I1_card` |
| A13 | GATE :: `_clean_prose` | `seen = out if defang else [_defang_outside_code(c) for c in out]` -> `seen = out` | `test_row_Z4_card` |
| A10 | GATE :: `sanitise_text` | `def sanitise_text(text: str, *, defang: bool = True) -> str:` -> `def sanitise_text(text: str, *, defang: bool = False) -> str:` | `test_sanitise_text_default_unchanged` (expect `DEFAULT CHANGED`) |
| A28 | GATE :: `_clean_prose` | `out = [_clean_line(line, defang) for line in joined]` -> `out = [_clean_line(line, True) for line in joined]` | `test_row_H26_card` |
| A29 | GATE :: `_clean_line` | `return _defang_outside_code(line) if defang else line` -> `return _defang_outside_code(line)` | `test_row_H26_card` |
| A30 | GATE :: `_all_prose` | `_clean_prose(lines, defang))` -> `_clean_prose(lines, True))` | `test_row_FB1_gate` |
| A27 | GATE :: `sanitise_text` | `if not opener or not closer:\n            return _all_prose(lines, defang)` -> same with `True` | `test_row_FB1_gate` |
| A25 | GATE :: `sanitise_text` | `out += _clean_prose(lines[pos:start], defang)` -> `out += _clean_prose(lines[pos:start], True)` | `test_row_PF1_card` |
| A19 | GATE :: `sanitise_text` | `_clean_line(opener.group(3), defang)` -> `_clean_line(opener.group(3), True)` | `test_row_I2_card` |
| A18 | GATE :: `sanitise_text` | `[_clean_line(line, defang) for line in body]` -> `[_clean_line(line, True) for line in body]` | `test_row_E1_card` |
| A26 | GATE :: `sanitise_text` | `out += _clean_prose(lines[pos:], defang)` -> `out += _clean_prose(lines[pos:], True)` | `test_row_PF2_card` |
| A31 | GATE :: `sanitise_text` | `return _all_prose(lines, defang)\n    return result` -> `return _all_prose(lines, True)\n    return result` | `test_row_FB2_gate` |
| A7 | RD :: plain entry | `[^\s\"';,]\|` -> `[^\s\"';,&]\|` | `test_row_H34a_model` |
| A9 | RD :: plain entry | `(?<![\w.\-?&])` -> `(?<![\w.\-])` | `test_row_Q2_model` |
| A33 | RD :: plain entry | `(?<![\w.\-?&])` -> `(?<![\w.\-?])` | `test_row_Q13_model` |
| A35 | RD :: plain entry | `(?<!&amp;)` -> `` (removed) | `test_row_Q15_model` |
| A23 | RD :: plain entry | `\|&amp;\|` -> `\|` | `test_row_H34d_card` |
| A15 | RD :: query entry | QLB -> `` (removed) | run; expected survivor, NEEDS LEAD 4 |
| A32 | RD :: query entry | QLB -> `(?:(?<=[?])\|(?<=&amp;))` | `test_row_Q14_model` |
| A34 | RD :: query entry | QLB -> `(?<=[?&])` | `test_row_Q15_model` |
| A8 | RD :: query entry | `\|` + QAMP -> `\|&` | `test_row_Q2_model` |
| A14 | RD :: query entry | `\|` + QAMP -> `` (removed) | `test_row_Q5_model` |
| A20 | RD :: query entry | `\|` + QAMP -> `\|&(?![^\s&\"'=]*=)` | `test_row_Q10_model` |
| A21 | RD :: query entry | `\|` + QAMP -> `\|&(?![^&#\"'=]*=)` | `test_row_Q11_model` |
| A39 | RD :: query entry | `\|` + QAMP -> `\|&(?![^\s&#=]*=)` | `test_row_Q16_model` |
| A24 | RD :: query entry | `&amp;(?![^\s&#\"'=]*=)\|` -> `` (removed) | `test_row_Q12_card` |
| A36 | RD :: query entry | `&amp;(?![^\s&#\"'=]*=)\|` -> `&amp;\|` | `test_row_Q7_model` |
| A40 | RD :: query entry | `&amp;(?![^\s&#\"'=]*=)\|` -> `&amp;(?![^\s&#=]*=)\|` | `test_row_Q17_model` |
| A16 | RM :: `redact_text` | `for view in views:` -> `for view in ():` | `test_row_H36a_card` |
(`\|` in this table is a plain `|`.) Counts: 49 mutants run (48 with a killer, A15 run as an expected survivor). **A15:** removing the query lookbehind changes the result only where a key is preceded by more than 40 key characters (the plain entry refuses there; the mutant masks it, as INFO-K41 shows): more masking, never less; the evidence prints A15's verdict and the INFO-K41 output under it. **Decided equivalent (not run):** A22 (closer line kept verbatim: a closing fence line holds only markers and the prefix `[ \t>*+\-0-9.)]`, never a name with a top-level domain). Removing the `defang` argument at a call site is not a mutant: it raises `TypeError` (D1).

## Template fields
- **Package:** P1d-a, "defang after the redactor; `&` inside a password". Branch `core/P1d-a` from `0dabf1f`; one pull request. **Path class:** redaction; no round cap. **Source:** BL-core-p1d-002, BL-core-p1d-007; ORDER 177.
- **Depends on:** no product dependency (ORDER 177; HELD belongs to P1d-learn, ORDER 180). Mutant evidence depends on the R1 runner PR (ORDER 181). Ships first; P1d builds on it.
- **Class (R337):** "a step that changes the text runs before the step that must read it" (defang; also the gate's `&amp;` rewrite before the value grammar) and "a separator ends a value outside the grammar where it is a separator" (`&`, `;` of `&amp;`). Siblings: R6, R7; a forgotten `defang` argument is made impossible (required argument).
- **Neutral default / alternative:** no vendor; `defang=True` keeps every other caller's behaviour.
- **Files:** change `src/hadavin_sdk/approvals/gate.py` (flag, required helper argument, ZWSP check, `_defang_plain`, `_per_part`, `defang_text`, `undefang_text`, D3); `src/hadavin_sdk/approvals/channel.py` (`_neutralise`, `clean`; the comment "Nothing transforms the text after its final redaction" becomes "After the final redaction only `defang_text` runs: it writes `.` as `[.]` and wide dots as `.`"); `src/hadavin_sdk/approvals/slack_channel.py` (`_blocks` order); `src/hadavin_sdk/guard/redact.py` (entry split, `&amp;` unit, comment as in Code shape); `CHANGELOG.md`. Create `tests/test_p1d_a_rows.py`, `tests/p1d_a_mutants.py`, `tests/fixtures/p1d_cases.py` (rows, generators, BS-1 corpus; P1d adds to it), `tests/fixtures/p1d_a_base_rows.json` (`{"base": "<sha>", "rows": {"<id>/<entry>": "<output>" or "NEW_SURFACE: <name>"}}`) and `tests/fixtures/p1d_a_gate_base.json` (`{"base": "<sha>", "count": <n>, "frozen": {"<input>": "<sanitise_text output>"}}`), both written by the tool on base and committed unchanged; `tools/p1d_corpus.py` (run as `python -m tools.p1d_corpus` from the worktree root, so `tests` and `tools` import).
- **Interface:** `gate.sanitise_text(text, *, defang: bool = True) -> str`; `gate.defang_text(text) -> str`; `gate.undefang_text(text) -> str`. No other public change.
- **Reused:** `_defang_outside_code` (its expression, now `_defang_plain`), `_closed_fences`, `_INLINE_CODE`, `_DOMAIN`, `_NON_ASCII_HOST`, `_WIDE_DOTS`, `runmap.PLACEHOLDER` shape, the decoded-view pass of `redact_text`, `tools/mutation_runner.py`, the review3 fallback patch. Checked, not needed: hashing, k1b, stats, evals, store. Not reused: running the whole redactor before the gate (broke two fuzz tests, P1d V8); changing the gate's `_ENTITY` (a reviewed defence, one caller only); `fuzzgen.py`'s `random.Random` (needs an S311 suppression).
- **Hostile inputs:** encoded addresses (H36), entities (H34b, H34d, Q12, ENT, NE1, PU1, Q7, Q8, Q15, Q17), key after `&` or `&amp;` (Q13-Q15), quotes in a query segment (Q16, Q17), key between fences (L8), tag-split assignment (T1), wide dots (L6, Z4, D3e), placeholder look-alikes (D3), double backticks (G2), typed `[.]` (L10-L16), length boundary (L9), forced fallbacks (FB1-FB2). Contract suite: not applicable (no kind interface changes).
- **Security and least privilege:** no identity, right or secret. Link protection unchanged or stronger (G2 property). Test values built from parts. A typed `[.]` between name characters outside code is read as `.` before redaction (more masking; shown as `[.]` again after defang).
- **Race / process tests:** none (no shared state).
- **Rollback:** tag `pre-P1d-a`; revert commit. Summaries stored by the new code hold placeholders and `[.]`; old and new `_blocks` both show them correctly (new: `test_stored_card_round_trip`); no loud-failure test needed.
- **Reviewers:** fresh `egm-codebase-details` (correctness) + `egm-design` (adversarial), given the diff, this ticket and the evidence only.
- **Done =** a fresh round finds no blocker or major; gates green (tests 3.12 and 3.13, ruff check, ruff format --check, `scan_repo.py`, `stage_mutants.py`, perf, bandit, pip-audit, semgrep, zizmor, gitleaks, Trivy, guard tests, CodeQL, SonarCloud, CodeRabbit); BS-1 within the gates the lead confirms; ledger rows BL-core-p1d-002 and 007 FIXED-VERIFIED; the lead merges.

## Paths (measured 2026-11-09)
| what | path |
|---|---|
| handover worktree (branch `core/cloud-handover`) | `/home/user/hadavin-sdk` (the machine profile's `/home/user/hadavin-sdk-handover/handover` does not exist) |
| build worktree (branch `core/P1d-a`) | `/home/user/build/P1d-a`: `git -C /home/user/hadavin-sdk worktree add -b core/P1d-a /home/user/build/P1d-a 0dabf1fa7a2e` |
| base worktree (detached, thrown away) | `/home/user/build/P1d-a-base`: `git -C /home/user/hadavin-sdk worktree add --detach /home/user/build/P1d-a-base 0dabf1fa7a2e`; removed at the end with `git worktree remove` (never prune) |
| evidence snapshot (has a `.git`, for the gitleaks-ignore check) | `/home/user/build/EV-P1d-a-<sha7>/wt`: `git -C /home/user/hadavin-sdk worktree add --detach /home/user/build/EV-P1d-a-<sha7>/wt <head sha>`; removed with `git worktree remove` |
| raw output | `/home/user/hadavin-sdk/handover/evidence/P1d-a/base-0dabf1f/` (BS-0, fail-before) and `.../P1d-a/<head sha7>/` (BS-1, evidence, mutants) |
`<s>` = a folder under the session scratchpad. Heavy runs (both full test runs, the perf run, the mutant run) go through `/home/user/build/heavy.sh <log> env VAR=value ... <command...>` started as a background job (it appends `exit=<rc>`); at most 3 at once (ORDER 178). `qsubmit.sh` does not exist on this machine.

## Build steps
- **BS-0 (HARD STOP; test tooling only, no product code).** In the build worktree write `tests/fixtures/p1d_cases.py`, `tools/p1d_corpus.py`, `tests/test_p1d_a_rows.py` first. Then: (1) `git -C /home/user/hadavin-sdk fetch origin`; `git rev-parse origin/main` = `0dabf1f`, or `git diff 0dabf1f origin/main -- src/hadavin_sdk/approvals/gate.py src/hadavin_sdk/approvals/channel.py src/hadavin_sdk/approvals/slack_channel.py src/hadavin_sdk/guard/redact.py src/hadavin_sdk/guard/runmap.py` is empty; (2) copy those three files to the same paths in the base worktree (never committed there); (3) `cd /home/user/build/P1d-a-base && UV_PROJECT_ENVIRONMENT=<s>/vbase uv sync --locked --no-build --python 3.13 --all-extras --group test`; (4) `UV_PROJECT_ENVIRONMENT=<s>/vbase uv run --no-sync python -m tools.p1d_corpus --rows --out /home/user/hadavin-sdk/handover/evidence/P1d-a/base-0dabf1f/bs0-base.txt --fixture tests/fixtures/p1d_a_base_rows.json > <s>/bs0.log 2>&1; rc=$?; tail -n 3 <s>/bs0.log; echo rc=$rc`; (5) same with `--freeze-gate --out tests/fixtures/p1d_a_gate_base.json`; copy both JSON files back to the build worktree unchanged; (6) `git grep -n "sanitise_text\|_neutralise\|_defang\|_clean_line\|_clean_prose\|_all_prose\|PATTERNS\[\|\.summary\b"` in `src`, `demos`, `tests` on main, recorded in `bs0-base.txt`; (7) read the two fuzz tests P1d V8 names; (8) read WHATWG URL section 5.1, record the section number and date.
  **`--rows` output:** line 1 `base <full sha>`; line 2 `hadavin_sdk <path of the imported package>` (must be under `P1d-a-base`); then one line per row and entry: `<row>\t<entry>\t<json.dumps(output, ensure_ascii=True)>\t<FIT|MISMATCH|MISFIT: reason>`; a missing new name prints `NEW_SURFACE: <name> missing` and is FIT for fb rows; one `INFO-K41` line: the model output of `"a" * 41 + "password=hunter22 x"` (reported, no gate); the count of LIT. Exit 0 if all FIT, 3 otherwise.
  **STOP rule (exit 3):** a written "on base" cell differs (MISMATCH); a cell written once for two entries must hold on each entry, and a cell written per entry (F15, H34d, Q12, SC1) on its own entry; BS0 cells are recorded per entry and two different strings there are not a STOP; a BS0 cell does not fit its class (MISFIT): fb whose base equals its expected after, pb whose base differs from a written expected after, ow whose base equals its expected after; a named assert of L8, T1 (base form) or W1 fails on base; a grep hit that shows a stored summary to a person outside R7 or calls one of the changed helpers outside `gate.py`. On STOP: no product code; report to the lead; ticket revision.
- **Fail-before:** in the base worktree, `UV_PROJECT_ENVIRONMENT=<s>/vbase uv run --no-sync pytest -q tests/test_p1d_a_rows.py -rA --durations=0 > .../base-0dabf1f/fail-before.txt 2>&1` (base SHA prepended on line 1). Every fb row fails on its `ROW <id> <entry>:` assertion or with `NEW_SURFACE:` (D3a-f, FB1-FB2 and the properties that call new names); every pb row passes; ow rows F16, F17 and Q6 fail. The link property is also run once there and its result recorded (informative).
- **Build**, then **BS-1** on the build head.
- **BS-1 over-mask and leak corpus** (`python -m tools.p1d_corpus --kind amp --seed 1 --path both --out .../<sha7>/bs1-overmask.txt`; exit 0 within the gates, 4 otherwise = build stops, numbers and failing texts to the lead, no pull request until the lead decides). Until the lead answers NEEDS LEAD 1 the builder runs BS-1 with the proposed gates and continues to evidence and review, but opens no pull request.
  **Draws** use `d` with stream `BS1-<shape>` and `SEED = 1`. Secret S: length `8 + d(s, 33)`, each character `pick(s, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!$%*+-./:@^_~")` (no white space, quote, `;`, `,`, `=`, `#`, `&`, `<`, `>`, `?`, backtick). An S for which `runmap.redact_text("x " + S + " y", runmap.RunMap())` differs from its input (another entry would mask part of it) is drawn again from the same stream; redraws are counted per shape. `&` shapes: count `1 + d(s, 3)`; each position `1 + d(s, len(S) - 2)`, drawn again if it equals or neighbours an earlier one; the character there becomes `&` and the next one `pick(s, letters)`. Key = `pick(s, KEYS)`, KEYS = `password, passwd, pwd, api_key, token, client_secret, auth_token`. Plain tail = `pick(s, [END, WORDS, SEMI, QUOTE])`. WORDS = space + `1 + d(s, 6)` words `pick(s, WORDS20)` joined by spaces; WORDS20 = `alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa quebec romeo sierra tango`. FIELDS = `1 + d(s, 3)` of `&k=v`, k = `pick(s, ["user", "next", "page", "lang", "id", "ref"])`, v = `1 + d(s, 12)` of `pick(s, "abcdefghijklmnopqrstuvwxyz0123456789")`; "(+ WORDS)" = WORDS added when `d(s, 2) == 1`. SEMI = `;` + WORDS; QUOTE = `"` + WORDS; END = nothing. Tails are at most 100 characters (a longer draw is cut at the last space before 100). Query shapes use the prefix `GET /p?` (no scheme, so the card does not remove it as a link). S3 flags: `1 + d(s, 2)` of `pick(s, ["&debug", "&raw", "&x1"])`. S7: A and B each `4 + d(s, 9)` characters of the S alphabet, name `pick(s, letters)` twice.
  | shape | count | text | gate (proposal, NEEDS LEAD 1) |
  |---|---|---|---|
  | S1 | 50 | query, S without `&`, FIELDS (+ WORDS) | exact; hidden 0 |
  | S2 | 25 | query, S with `&`, FIELDS | exact; hidden 0 |
  | S2x | 67 | query, exhaustive `&` placement (below), FIELDS | exact; hidden 0 |
  | S3 | 25 | query, S, S3 flags, FIELDS | exact; hidden run = the flag segments |
  | S4 | 50 | plain, S without `&`, plain tail | exact; hidden 0 |
  | S5 | 50 | plain, S with `&` (H34 shape), plain tail | exact; hidden 0 |
  | S5x | 268 | plain, exhaustive `&` placement, each of END/WORDS/SEMI/QUOTE | exact; hidden 0 |
  | S6 | 50 | plain form body `<key>=S` + FIELDS (+ WORDS) (F16 shape) | exact; hidden run = tail up to the first space, quote or `;` |
  | S7 | 20 | query, S = A + `&` + name + `=` + B, FIELDS | reported only (non-goal N4) |
  | REAL | 30 | the lines below | exact; over-mask exactly on R6 and R14 |
  Total 635 samples. **Exhaustive placement (S2x, S5x):** one base string of each length 8, 9 and 10 (stream `BS1-X`, characters `pick(s, A-Za-z0-9)`); `&` replaces the character at every inner position and at every non-adjacent pair of inner positions (16 + 22 + 29 = 67 secrets); the character after each `&` is forced to a letter, so every SEMI sample meets the gate's `&amp;` rewrite and post-`&` segments of 1-3 characters occur.
  **REAL lines (made up; the secret is hidden as one placeholder, everything else shown; P6: 30 of 30 on both paths):** R1 `"GET /login?user=bob&password=Xy7&kQ2pLm HTTP/1.1" 200 512` (S `Xy7&kQ2pLm`); R2 `"GET /api?token=Ab12Cd34Ef56&page=2 HTTP/1.1" 200 90` (`Ab12Cd34Ef56`); R3 `"POST /cb?api_key=Zz9&Yy8Xx7&lang=en HTTP/1.1" 302 0` (`Zz9&Yy8Xx7`); R4 `"GET /r?ref=home&client_secret=Qw3&Er4Ty5 HTTP/1.1" 200 7` (`Qw3&Er4Ty5`); R5 `"GET /s?pwd=Mn8Bv7Cx6&id=41&next=/home HTTP/1.1" 200 3` (`Mn8Bv7Cx6`); R6 `"GET /t?auth_token=Pl0&Ok9Ij8&debug HTTP/1.1" 200 1` (hidden `Pl0&Ok9Ij8&debug`: over-mask `&debug`); R7 `DB_PASSWORD=Hg5&Fd4Sa3`; R8 `API_KEY=Jk2Lm3&Np4 # rotated`; R9 `client_secret: "Rt6&Yu7Io8"`; R10 `      - POSTGRES_PASSWORD=Vb1&Nm2Qw3`; R11 `export TOKEN='As4&Df5Gh6'`; R12 `passwd=Ze7&Xc8Vb9;user=app` (`Ze7&Xc8Vb9`); R13 `curl -d 'user=bob&password=Wq1&Er2Ty3' /login`; R14 `curl -d 'password=Ui4&Op5As6&user=bob' /login` (hidden `Ui4&Op5As6&user=bob`: over-mask `&user=bob`); R15 `./backup --password=Df7&Gh8Jk9 shop`; R16 `curl -H 'Accept: text/plain' -d 'token=Lz1&Xc2Vb3' /api`; R17 `./migrate --dsn "password=Nm4&Qw5Er6 user=app"`; R18 `wget '/dl?user=bob&api_key=Ty7&Ui8Op9'`; R19 `Server=db;Database=shop;User Id=app;Password=Aa1&Bb2Cc3;`; R20 `Data Source=db;Password=Dd4&Ee5Ff6;Encrypt=true`; R21 `Host=db;Port=5432;Password=Gg7&Hh8Ii9;Pooling=true`; R22 `Password=Jj1&Kk2Ll3;Timeout=30`; R23 `{"level":"info","password":"Mm4&Nn5Oo6","user":"bob"}`; R24 `{"event":"login","token":"Pp7&Qq8Rr9"}`; R25 `{"msg":"retry","api_key":"Ss1&Tt2Uu3","n":2}`; R26 `{"client_secret":"Vv4&Ww5Xx6"}`; R27 `link=/login?user=bob&amp;password=Yy7&amp;Zz8Aa9&amp;next=/home` (`Yy7&amp;Zz8Aa9`); R28 `link=/cb?token=Bb1Cc2Dd3&amp;page=2` (`Bb1Cc2Dd3`); R29 `img=/i?api_key=Ee4&amp;Ff5Gg6 x` (`Ee4&amp;Ff5Gg6`); R30 `link=/r?ref=x&amp;pwd=Hh7&amp;Ii8Jj9` (`Hh7&amp;Ii8Jj9`). Where no secret is named, it is the value after `=` or `:` up to the next quote, space or `;`. The fixture holds each line with its hidden string; the corpus tool builds the expected output from them.
  **Measures, per sample and per path (card = `clean`, model = `redact_text`):** the tool writes the EXPECTED output (the input with the predicted hidden span replaced by one placeholder). Both strings are normalised (each placeholder written `<P>`, `[.]` read as `.`, ZWSP dropped). Gate = exact equality. Each mismatch is printed with input, output and expected and labelled LEAK (between the predicted prefix and the predicted visible tail the output holds anything other than exactly one `<P>`), OVERMASK (the visible tail is shorter than predicted) or OTHER. Counts per shape and path: samples, redraws, exact, LEAK, OVERMASK, OTHER, longest hidden run. Basis: ORDER 165 (0 for ordinary secrets), ORDER 166 item 2 (over-mask measured apart), and the grammar of D2 (each output is predicted exactly, so any other value is a defect).

## Evidence commands (EVIDENCE RUNNER, in the evidence snapshot; raw output to `/home/user/hadavin-sdk/handover/evidence/P1d-a/<sha7>/evidence-<n>.md`, line 1 `git rev-parse HEAD`; same steps as `.github/workflows/ci.yml` on main; each `> <s>/out 2>&1; rc=$?; tail -n 3 <s>/out; echo rc=$rc`; lines marked H through `heavy.sh <log> env ...`, as one background job each)
```
UV_PROJECT_ENVIRONMENT=<s>/v313 uv sync --locked --no-build --python 3.13 --all-extras --group test
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync ruff check src tests demos tools
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync ruff format --check src tests demos tools
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync python tools/scan_repo.py
H: env UV_PROJECT_ENVIRONMENT=<s>/v313 HADAVIN_REQUIRE_PINNED_UNIDATA=1 HADAVIN_TEST_PG_DSN=<dsn> PGUSER=postgres uv run --no-sync pytest -q -m "not live and not perf" -rs
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync python tests/stage_mutants.py
H: env UV_PROJECT_ENVIRONMENT=<s>/v313 HADAVIN_TEST_PG_DSN=<dsn> PGUSER=postgres uv run --no-sync pytest -q -m perf -rs
UV_PROJECT_ENVIRONMENT=<s>/v312 uv sync --locked --no-build --python 3.12 --all-extras --group test
H: env UV_PROJECT_ENVIRONMENT=<s>/v312 HADAVIN_TEST_PG_DSN=<dsn> PGUSER=postgres uv run --no-sync pytest -q -m "not live and not perf" -rs
UV_PROJECT_ENVIRONMENT=<s>/scan uv sync --locked --no-build --only-group scan
uv export --locked --all-extras --all-groups --no-emit-project --format requirements-txt -o <s>/locked.txt && UV_PROJECT_ENVIRONMENT=<s>/scan uv run --no-sync pip-audit -r <s>/locked.txt --require-hashes --disable-pip
UV_PROJECT_ENVIRONMENT=<s>/scan uv run --no-sync bandit -q -r src demos tools -ll
uvx --no-build --exclude-newer 2026-10-21T00:00:00Z --from "semgrep==1.181.0" semgrep scan --config p/python --config p/secrets --metrics=off --error --quiet src tests demos tools
UV_PROJECT_ENVIRONMENT=<s>/scan uv run --no-sync zizmor --offline --format plain .github
H: env UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync python tests/p1d_a_mutants.py        # alone; needs R1
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync python -m tools.p1d_corpus --kind amp --seed 1 --path both --out /home/user/hadavin-sdk/handover/evidence/P1d-a/<sha7>/bs1-overmask.txt
```
`<dsn>` = a cluster from `/home/user/build/pgstart.sh` (one per run, `initdb -E UTF8 --locale=C.UTF-8 -A trust -U postgres`, stopped after). The Vault service of CI does not run here: Vault-backed tests show as skips under `-rs`, and their result comes from the pull request's CI run. A failure of `tests/demo_askdata/test_validate_harm.py[dblink-connect]` counts as known only if it fails identically in the base worktree. Semgrep or pip-audit blocked by the network, the gitleaks-ignore check, gitleaks and Trivy: result taken from the pull request's CI run (job link in the evidence file). If no local Postgres runs, the perf line also comes from CI.

## Owner-facing wording (CHANGELOG)
"Approval cards now hide e-mail addresses and internal server names behind placeholders, as text sent to the model already did; this also applies to requests saved before this change. Before, they were shown with `[.]` in place of each dot. A password written with an `&` inside it is now hidden up to the next space, quote or semicolon; in a web address, the part after `&` is treated as the next field only when it has the form name=value. Some text right after such a password may also be hidden (measured: see the evidence)."

## Ledger rows closed
BL-core-p1d-002 (BLOCKER, defang before redaction, H26-H27; H28a-b stay with P1d under row 001) and BL-core-p1d-007 (MAJOR, `&` ends a value, H34).

## NEEDS LEAD
1. BS-1 gates as proposed in the BS-1 table (ORDER 165: proposed ceilings go to the lead with the number and the basis). Until answered: no pull request (BS-1).
2. Wide-dot host names are not recognised as hosts on either path (non-goal N5; read from the code, not run): proposed ledger row for P1d (redactor grammar). Same for INFO-K41 if BS-0 shows the secret.
3. `_blocks` reads `[.]` between name characters outside code as `.` before redacting, so requests stored before the fix are masked too (changes how stored requests render: L15 `version 1[.]5` shows `version 1.5`; L16 a stored `//evil[.]com/p` becomes `[link removed]`).
4. Mutant A15 (query lookbehind removed) is expected to survive every row: it differs only for a key preceded by more than 40 key characters, where it masks MORE (INFO-K41). Accept it as a written equivalence, or rule that INFO-K41 is fixed here (then A15 gets a killer row and the plain entry changes).

## Revision log
Rev 1 (2026-11-09): split from P1d rev 7 by ORDER 177; D2 query/plain split after the prototype broke the pinned query test with `&` allowed everywhere; D3 after the prototype left `<HOSTNAME_1>.example.com` linkable; H36a-b moved here; H28a-b left in P1d.
Rev 2 (2026-11-09): plan review round 1 resolved (`round1-resolve.md`, 33 findings): base pinned to main `0dabf1f` with a BS-0 hard stop; seeded stdlib generators; exact bracket invariant; exact strings per row; guarantee classes; ZWSP rule kept; pre-redaction differential; final-text link property; `alt`, `~~~`, info-string, legacy-summary and length rows; D3 regex; query continuation; BS-1 ceilings; sibling search; CI-form commands; mutants A3b-c, A11-A16.
Rev 3 (2026-11-09T07:55Z): plan review round 2 resolved (`round2-resolve.md`, 25 findings, all PROPOSE FIX, applied): legacy `[.]` undo limited to prose parts between name characters (`undefang_text`; rows L10-L12; mutants A3d-e); exact ZWSP rule on the would-be-defanged line (row Z4; A13); defang order wide dots, D3, hosts, domains (row D3e; A17); BS-1 corpus fully specified with seven shapes, a real-format sample, leak and hidden-run definitions and exact per-shape gates sent to the lead; BS-0 STOP rule per row class, tool modes and output format, base worktree with its own venv, fixtures written by the tool; one paths table, `heavy.sh` instead of the absent `qsubmit.sh`; Code shape block with exact mutant edits, registration with `forbid_skips` and the R1 dependency (ORDER 181); new mutants A17-A21, rows E1/I2 linked, Q10-Q11; A15 and A22 decided equivalent; card-map oracle; link property extended to placeholder dots and wide dots; literal-form reading rule; `&amp;` query rows Q7-Q8; non-goals N4-N5; R7 readers of stored summaries; references by symbol; ORDER 180 closed rev-2 NEEDS LEAD 2 (H28a-b) and confirmed D2.
Rev 4 (2026-11-09T08:16Z): plan review round 3 resolved (`round3-resolve.md`, 27 findings, all PROPOSE FIX, applied): `&amp;` read as one value unit in both redactor entries, settled by reading `_ENTITY` and probe P3 (rows H34d, Q12; H34b and Q8 now exact `<SECRET_1>`; mutants A23-A24); `defang` a required argument of the gate helpers, a mutant per call site (A25-A31) with rows P1, P2, FB1, FB2; `_defang_outside_code` reuses `_per_part` so A5 is unique, A10 on the full signature; legacy-undo rows L13-L16, mutants A3f-g, property `test_stored_card_round_trip`; BS-1 exact expected output per sample with LEAK/OVERMASK labels and exhaustive shapes S2x, S5x; one test per row and entry with `expect`/`only_test`/`pinned` per mutant and full file paths; T1 oracle `defang_text(second call)`; STOP rule allows per-entry cells (F15); property-failure escalation rule; differential on G-TXT allowing only more withholding; row F17; 300 s time bound; `Source` field; evidence list aligned with `ci.yml` (scan_repo, pinned Unicode data, stage mutants, pip-audit, semgrep, zizmor; gitleaks and Trivy from CI); `heavy.sh` with `env`; snapshot as a worktree; JSON schemas; imports.
Rev 5 (2026-11-09T08:41Z): plan review round 4 resolved (`round4-resolve.md`, 30 findings in 19 groups, 29 PROPOSE FIX applied, 1 part-CONTEST): probe P6 ran the D2 grammar in the real redactor on `0dabf1f` (every redactor row's expected string and 30 REAL lines confirmed); a key after `&amp;` is a query key (row Q15; mutants A34-A35); key after `&` rows Q13-Q14 (A32-A33); G3 and CHANGELOG say a plain value still ends at `;` and quotes (rows SC1, NE1); plain `&amp;` unit without look-ahead (row PU1); new mutants A36-A43 with rows Q16, Q17, D3f, G2; A15 run, not assumed (NEEDS LEAD 4); round-trip property on G-TXT-B; differential right side ends with `defang_text`; exact hash-based draw procedure (no `random`, no S311 suppression) for every generator and the BS-1 corpus; BS-1 words, filter and the 30 REAL lines written out; row-failure rule; no pull request before NEEDS LEAD 1; `python -m tools.p1d_corpus`; `Callable` import, `zip(..., strict=True)`, ZWSP written as `​`; rows P1/P2 renamed PF1/PF2; R8 read; WHATWG citation marked UNVERIFIED.
