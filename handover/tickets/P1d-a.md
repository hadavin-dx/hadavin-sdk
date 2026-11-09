# Package ticket P1d-a: approval cards show e-mail addresses and internal host names unmasked (the `[.]` step runs before the redactor), and a password containing `&` shows the part after the `&`. DRAFT revision 3 (plan review round 2 resolved; round 3 next)

**Status (2026-11-09T07:55Z UTC; IST 13:25):** text only, no code, no pull request. Split from P1d by lead ORDER 177. **Base: `origin/main` `0dabf1fa7a2e`** (holds `tools/mutation_runner.py`). Prototype on `core/cloud-handover` `6d8699a`: `handover/evidence/P1d/rev8-probes/` (P = probe output there). Resolves: `handover/reviews/P1d-a/round1-resolve.md`, `round2-resolve.md`. Marker: CODE-LAST v1.

## The problem in plain words
Before a person sees an approval card, two steps run on its text: a cleaning step (the "gate") and a redactor that replaces secrets and personal data with placeholders such as `<EMAIL_1>`. The gate runs FIRST and writes every dot of a web address or host name as `[.]`, so a chat app does not turn it into a link. After that the redactor no longer recognises `anna.m@example[.]org` as an e-mail address or `db01[.]corp[.]example[.]com` as an internal host name, so both are shown in full. Separately, the redactor treats `&` as the end of a password, so `password=ab12&cd34ef56gh78ij` shows `cd34ef56gh78ij`, on cards and in text sent to the model.

## Words used (defined once)
- **Gate** = `approvals/gate.py::sanitise_text` plus `withhold_commands`, called through `channel._neutralise`. **Defang** = writing each `.` of a domain or host as `[.]`.
- **Redactor** = `guard/runmap.py::redact_text`, the one function every caller goes through to redact (the "choke point"); it runs the `neutralise` hook on its input and on each decoded view BEFORE redacting.
- **Card path** = `channel.clean` and `SlackChannel._blocks`. **Model path** = `redact_text` with no `neutralise`.
- **Prose part** = text outside the body lines of a closed backtick fence and outside inline code (split by `_closed_fences` and `_INLINE_CODE`, as the gate does).
- **Query form** = an assignment whose key comes right after `?` or `&` (`?password=x&next=/home`). **Plain form** = any other assignment (`password=x` in a config line or a message).
- **Over-mask** = text that is not secret but is hidden because it follows a secret (accepted by ORDER 166 item 2; measured apart from leaks). **Leak** = see BS-1.
- **Idempotent** = running it twice gives the same text as once. **Lookbehind / look-ahead** = a regex condition on the characters just before / after a position.
- Row classes: **fb** = fails on the base, passes after; **pb** = passes on the base with the same output; **ow** = accepted over-mask, counted.

## Code facts (R = read on `0dabf1f` by symbol; P = probe on `6d8699a`)
- R0: between `6d8699a` and main, `gate.py` differs only in its header, `channel.py` and `slack_channel.py` not at all, `redact.py` in two unrelated `_COMMON` words, `runmap.py` by 54 lines. BS-0 re-runs every row on main.
- R1: `channel._neutralise(text) = withhold_commands(sanitise_text(text))`. `clean` redacts the text, and when tags were removed also the joined view, and returns `alt` or `out`. `SlackChannel._blocks`: `withhold_commands(req.summary)`, then `redact_text(..., neutralise=_neutralise)`, then the `max_card_chars` length check.
- R2: `_clean_line` ends with `return _defang_outside_code(line)`. `_clean_line` runs on prose lines (`_clean_prose`), the fence opener's info string and `~~~` fence bodies; backtick fence bodies and inline code are never defanged. `_clean_prose` prefixes a zero-width space (ZWSP, U+200B) to a CHANGED line that matches `_ANY_BLOCK` (heading, quote, list item incl. `1.`, fence, indented code), so it starts no block. `sanitise_text` has no other caller in `src`.
- R3: generic assignment SECRET entry in `redact.py`: key lookbehind `(?<![\w.\-])`; value `((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=]))+)`. Pinned: `tests/warden_port/test_redaction.py::test_query_param_credentials_are_masked` (`?password=SuperSecretPw99&next=/home` keeps `/home`); ORDER 180 q392-6 keeps it unchanged.
- R4: `redact()` applies `PATTERNS` in order with `pattern.sub`: the order of two overlapping entries decides the result.
- R5: `redact` is imported into runmap by name; a spy patches `hadavin_sdk.guard.runmap.redact`. `redact_text` fills the caller's map in place.
- R6 (siblings of "`&` ends a value"): hex-key entry (`[0-9a-f]{32,}`), HIGHENTROPY (base64 alphabets), AZURESAS `sig=` (a query value by grammar), `_PIECE` (splits a learned secret: only adds masks): not siblings. Row KV1 pins the whole known value.
- R7 (readers of a stored `req.summary` in `src` and `demos`): `FakeChannel.send` (`clean(req.summary)`, a test fake fed by current code) and `SlackChannel._blocks`. BS-0 re-greps.
- P1 (base): H26 card `contact anna.m@example[.]org please`; H27 card `host db01[.]corp[.]example[.]com down`; H34a both paths `password=<SECRET_1>&cd34ef56gh78ij`; H34b `password=<SECRET_1>&amp;4xKp2Vb9Lr3NcW8dYh6uJs`.
- P2 (prototype of the flag, the `clean` change and the `&` split only): H26 `contact <EMAIL_1> please`; H27 `host <HOSTNAME_1>.example.com down` (hence D3); H34a-c masked whole (H34b `password=<SECRET_2>`); with `&` allowed in both forms the pinned query test failed (hence D2). D3, `_blocks`, `undefang_text`, the query continuation: designed, NOT probed; proven by rows and mutants.

## Design
- **D1 Defang after the redactor.** `sanitise_text(text, *, defang: bool = True)`; the flag reaches every `_clean_line` call (prose, info string, `~~~` body) and both `_all_prose` fallbacks; with `defang=False` `_clean_line` skips defang. **ZWSP rule kept:** with `defang=False` the "changed" test and the block test read `d = _defang_outside_code(c)` (Code shape), so every line that gets a ZWSP today still gets one (Z1-Z4). `channel._neutralise` passes `defang=False`. New `gate.defang_text(text)`: fences are read on the FINAL text (what a renderer reads); body lines of a closed backtick fence stay as they are; on every prose part, in this order: wide dots to `.`, D3, `_NON_ASCII_HOST`, `_DOMAIN`. New `gate.undefang_text(text)`: on prose parts only, `[.]` between two name characters becomes `.` (the old gate wrote `[.]` only there). `clean` returns `defang_text(alt)` or `defang_text(out)`. `_blocks`: (1) `undefang_text(req.summary)` (summaries stored by the old code hold defanged, unmasked addresses); (2) `withhold_commands`; (3) `redact_text`; (4) `defang_text`; (5) length check on the shown text. Model path unchanged.
- **D2 `&` follows the URL query grammar.** The generic entry becomes two, same kind, PLAIN FIRST then QUERY (R4). Plain: key lookbehind `(?<![\w.\-?&])`; value as today with `&` allowed (stops at white space, quote, `;`, the comma rule). Query: key lookbehind `(?<=[?&])`; value as today plus the alternative `&(?![^\s&#\"'=]*=)`: it continues past `&` unless the next segment (up to `&`, white space, `#` or a quote) holds `=`. Basis: in `application/x-www-form-urlencoded` `&` separates pairs and a literal `&` is `%26` (WHATWG URL Standard, section 5.1; BS-0 reads it and records the date). `&amp;` in plain form stops at its `;`; the decoded-view pass of `redact_text` then masks the whole value (P2 H34b).
- **D3 Placeholder next to a dot.** The redactor masks only the internal part of a host (`<HOSTNAME_1>.example.com`), and `_DOMAIN` does not start a name after `.`, so `example.com` would stay (linking by Slack or GFM: UNVERIFIED; defanged on the safe side). `_PLACEHOLDER_DOT` writes `<KIND_n>.` + name character as `<KIND_n>[.]`. `\w` is Unicode. No left boundary (more defang, never less). `<A_1>.<B_2>` unchanged.

### Code shape (exact text the mutants edit; ruff may reflow it: the builder keeps the tokens and sets each mutant's `old` to the formatted text)
```python
# gate.py
_PLACEHOLDER_DOT = re.compile(r"(<[A-Z][A-Z0-9]*_[0-9]+>)\.(?=[\w-])")
_LEGACY_DOT = re.compile(r"(?<=[\w-])\[\.\](?=[\w-])")
def _defang_prose(part: str) -> str:
    part = _WIDE_DOTS.sub(".", part)
    part = _PLACEHOLDER_DOT.sub(r"\1[.]", part)
    return _DOMAIN.sub(_defang, _NON_ASCII_HOST.sub(_defang, part))
def _per_part(line: str, fix: Callable[[str], str]) -> str:
    parts = [line] if "``" in line else _INLINE_CODE.split(line)
    return "".join(part if i % 2 else fix(part) for i, part in enumerate(parts))
def _outside_code(text: str, fix: Callable[[str], str]) -> str:
    body = {i for s, e, ch in _closed_fences(text) if ch == "`" for i in range(s + 1, e)}
    return "\n".join(line if i in body else _per_part(line, fix) for i, line in enumerate(text.split("\n")))
def defang_text(text: str) -> str:
    return _outside_code(text, _defang_prose)
def undefang_text(text: str) -> str:
    return _outside_code(text, lambda part: _LEGACY_DOT.sub(".", part))
# _clean_line(line, defang=True): last line   return _defang_outside_code(line) if defang else line
# _clean_prose(lines, defang=True):           out = [_clean_line(line, defang) for line in joined]
#   seen = out if defang else [_defang_outside_code(c) for c in out]
#   out = ["​" + c if _ANY_BLOCK.match(d) and not (same and d == lines[i]) else c for i, (c, d) in enumerate(zip(out, seen))]
# sanitise_text: _clean_line(opener.group(3), defang) ; else [_clean_line(line, defang) for line in body] ; _all_prose(lines, defang) ; _clean_prose(..., defang)
# channel.py: return withhold_commands(sanitise_text(text, defang=False)) ; return defang_text(alt) ; return defang_text(out)
# slack_channel.py: withheld = withhold_commands(undefang_text(req.summary))
#   shown = defang_text(runmap.redact_text(withheld, seeded, neutralise=_neutralise))
# redact.py plain value:  ((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|[^\s\"';,]|,(?!\s*[\w.\-]+\s*[:=]))+)
# redact.py query value:  ((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=])|&(?![^\s&#\"'=]*=))+)
```

## RUNG TABLE (2026-11-06 scale: 1 no-code, 2 own core modules, 3 existing free tools, 4 free libraries, 5 own new code last)
Rung test: core change, no client, no fee, no new dependency; rung 1 closed (R447: inside the choke point). **exact** = holds for every input of a named set, checked by a test over that set; **best effort** = tested rows only.
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| defang order | the redactor sees `.` before `[.]` is written | 2 (existing defang helpers behind a flag) | R1, R2, P2 | one flag, one call order | exact on G-EH (`test_card_masks_what_model_masks`); best effort beyond | CUT-TO-CONFIG+GLUE |
| placeholder-dot rule | no linkable remainder after a masked host | 2 (`runmap.PLACEHOLDER` shape, existing defang) | designed, not probed | one substitution | exact on G-TXT for the shape placeholder + `.` + name character; renderer linking UNVERIFIED | CUT-TO-CONFIG+GLUE |
| legacy undo | stored summaries masked too | 2 (same split as defang) | R7 | one substitution | exact on rows L7, L10-L12 | CUT-TO-CONFIG+GLUE |
| `&` in a value | mask a password containing `&` | 2 (existing entry split); 4 detect-secrets/gitleaks do not run inside our run map (UNVERIFIED) | R3, P2 | the query/plain split | exact on corpus C-AMP shapes S1-S6 and REAL (BS-1); best effort beyond | KEEP-CODE (one entry) |
**80 percent (R448):** all needs met by existing code moved or split; no new module. Cost estimate: build 3-4 agent-hours; 0 fees, 0 model tokens.

## Goals and Non-Goals
**Goals.** (G1) E-mail addresses and internal host names are masked on cards as on the model path, including requests stored before the fix. (G2) No linkable name outside code in the FINAL card text. (G3) A plain-form password with `&` is masked whole on both paths; a query value ends at `&` only before a `key=value` segment. (G4) Card structure and command withholding unchanged (exact differential).
**Non-Goals.** (N1) Addresses split by formatting (H28a-b): P1d (ORDER 180). (N2) Over-mask in plain form (`password=hunter22&user=bob` hides `&user=bob`) and of `=`-less query segments: accepted, measured by BS-1. (N3) Which names count as hosts. (N4) A query secret holding `&name=` is read as two fields, as the URL grammar says; the part after `&name=` is shown (measured as S7, not gated). (N5) A host written with wide dots is not recognised as a host on either path (it is defanged on the card): NEEDS LEAD 2.

## Failing inputs (`tests/test_p1d_a_rows.py`; literals in `tests/fixtures/p1d_cases.py`, built from parts: EM = `"anna" + "." + "m" + "@" + "example" + "." + "org"`, SV_A = `"Tq7mZ"`, SV_B = `"4xKp2Vb9Lr3NcW8dYh6uJs"`; H34 requires SV_A and SV_B masked as ONE value)
**How to read a row:** cells are Python string bodies; `\n` and `​` are escapes; `\|` is a plain `|` (Markdown escape). Where two paths are listed the string holds for both; BS-0 records each path separately. BS0 = filled by BS-0 (rules in BS-0). Card = `channel.clean(x)`; Slack = `_blocks` per `tests/test_k5_round11.py::test_the_slack_block_never_shows_a_decoded_view_that_was_not_sanitised` (`SlackChannel.__new__`, `max_card_chars = 2900`, `SimpleNamespace(summary=x, current_step=0, steps=[1], approval_id="a", status="PENDING")`, read `[0]["text"]["text"]`); model = `runmap.redact_text(x, runmap.RunMap())`. Every assertion message starts `ROW <id>` (mutant `expect`).
| row | class | entry | input | on base | expected after |
|---|---|---|---|---|---|
| H26 | fb | card | `contact <EM> please` | `contact anna.m@example[.]org please` | `contact <EMAIL_1> please` |
| H27 | fb | card | `host db01.corp.example.com down`; spy R5 | `host db01[.]corp[.]example[.]com down` | `host <HOSTNAME_1>[.]example[.]com down`; spy: some call's text holds `db01.corp.example.com`, none holds `[.]` |
| H36a | fb | card | `anna%2Em%40example%2Eorg` | same as input | `<EMAIL_1>` |
| H36b | fb | card | `anna&#46;m&#64;example&#46;org` | `anna&amp;#46;m&amp;#64;example&amp;#46;org` | `<EMAIL_1>` |
| E1 | fb | card | `~~~\nmail <EM>\n~~~` | BS0 | `~~~\nmail <EMAIL_1>\n~~~` |
| I2 | fb | card | "```mail <EM>\nx\n```" | BS0 | "```mail <EMAIL_1>\nx\n```" |
| L7 | fb | Slack | `contact anna.m@example[.]org please` | same as input | `contact <EMAIL_1> please` |
| H34a | fb | card, model | `password=ab12&cd34ef56gh78ij` | `password=<SECRET_1>&cd34ef56gh78ij` | `password=<SECRET_1>` |
| H34b | fb | card, model | `password=<SV_A>&amp;<SV_B>` | `password=<SECRET_1>&amp;<SV_B>` | `password=<SECRET_2>` |
| H34c | fb | card, model | `password=<SV_A>&<SV_B> end` | `password=<SECRET_1>&<SV_B> end` | `password=<SECRET_1> end` |
| Q4 | fb | card, model | `?password=ab&cd34ef56&user=bob x` | BS0 | `?password=<SECRET_1>&user=bob x` |
| Q5 | fb | model | `?password=ab&cd34ef56` | BS0 | `?password=<SECRET_1>` |
| Q8 | fb | model | `?password=ab&amp;cd34ef56&amp;user=bob x` | BS0 | assertion row: `cd34ef56` absent, `user=bob x` present; full string recorded in evidence |
| Q10 | fb | model | `?password=ab&cd34#x=1 y` | BS0 | `?password=<SECRET_1> y` |
| Q11 | fb | model | `?password=ab&cd34 x=1` | BS0 | `?password=<SECRET_1> x=1` |
| KV1 | fb | model | `password=ab12&cd34ef56gh78ij and later ab12&cd34ef56gh78ij` | BS0 | `password=<SECRET_1> and later <SECRET_1>` |
| D3a-e | fb | `defang_text` | `<HOSTNAME_1>. next`; `mail <EMAIL_1>.org`; ``x `<HOSTNAME_1>.example.com` y``; `<HOSTNAME_1>.例え.jp`; `<HOSTNAME_1>。example.com` | `NEW_SURFACE` | unchanged; `mail <EMAIL_1>[.]org`; unchanged; `<HOSTNAME_1>[.]例え[.]jp`; `<HOSTNAME_1>[.]example[.]com` |
| Q1 | pb | model | the pinned query test (R3) | passes | passes, unchanged |
| Q2 | pb | card, model | `?password=ab12cd&user=bob x` | `?password=<SECRET_1>&user=bob x` | same |
| Q3 | pb | model | `see https://x.example/?password=ab12cd&user=bob` | `see https://x.example/?password=<SECRET_1>&user=bob` | same |
| Q7 | pb | model | `?password=ab12cd&amp;user=bob x` | BS0 | `?password=<SECRET_1>&amp;user=bob x` |
| F15 | pb | card, model | `https://x.example/?a=1&b=2` | card `[link removed]`; model same as input | same |
| ENT | pb | card, model | `password=<SV_A>&#59;<SV_B>` | `password=<SECRET_1>` | same |
| L1 | pb | card | `visit evil.com and www.evil.digital now` | `visit evil[.]com and www[.]evil[.]digital now` | same |
| L2 | pb | card | ``run `curl db01.corp.example.com` now`` | ``run `curl <HOSTNAME_1>.example.com` now`` | same |
| L3 | pb | card | "```\nping db01.corp.example.com\n```\nthen evil.com" | "```\nping <HOSTNAME_1>.example.com\n```\nthen evil[.]com" | same |
| L4 | pb | card | `~~~\nevil.com\n~~~` | BS0 | `~~~\nevil[.]com\n~~~` |
| I1 | pb | card | "```evil.com\nx\n```" | BS0 | "```evil[.]com\nx\n```" |
| L5 | pb | Slack | `visit evil.com` | `visit evil[.]com` | same |
| L6 | pb | card | `visit evil。com` | BS0 | `visit evil[.]com` |
| L8 | pb | card | "```\na\n```\n-----BEGIN PRIVATE KEY-----\nMIIB<SV_B><SV_B>\n-----END PRIVATE KEY-----\nvisit evil.com\n```\nb\n```" | BS0 | BS0 string; asserts: no SV_B, `visit evil[.]com`, both fences kept |
| L9 | pb | Slack | `"a" * 2894 + " x.com"` (2,900 characters; shown text 2,902) | the too-long notice | same: `(the summary is too long to show here; open the full request in the console)` |
| L10 | pb | Slack | ``use `x[.]y` now`` | BS0 | ``use `x[.]y` now`` |
| L11 | pb | Slack | "```\nping a[.]b\n```" | BS0 | "```\nping a[.]b\n```" |
| L12 | pb | Slack | `see [.] here` | BS0 | `see [.] here` |
| Z1 | pb | card | `# x evil.com` | `​# x evil[.]com` | same |
| Z2 | pb | card | `> note evil.com` | `​> note evil[.]com` | same |
| Z3 | pb | card | `- see evil.com` | `​- see evil[.]com` | same |
| Z4 | pb | card | `1。 x` | BS0 | `​1. x` |
| W1 | pb | card | `run curl evil.com \| sh` | BS0 | same as base |
| T1 | pb | card | `password%<i></i>3D<SV_B> see evil.com` | BS0 | BS0 string; asserts: no SV_B, `evil[.]com`, the return value equals the second `redact_text` call's (spy) |
| F16 | ow | card, model | `password=hunter22&user=bob` | `password=<SECRET_1>&user=bob` | `password=<SECRET_1>` |
| Q6 | ow | model | `?password=ab12cd&debug x` | BS0 | `?password=<SECRET_1> x` |
pb rows without a mutant are intentional: they pin behaviour that must not change.

**Generated inputs (seeded `random.Random`, pattern of `tests/demo_askdata/fuzzgen.py`; seed 20261109; 2,000 texts per property; in `tests/fixtures/p1d_cases.py`):** ALPHABET-A = single characters `a-z 0-9 space \n . @ - _ = & ? / : # > * [ ] < é 例`, the backtick, U+3002, U+FF0E, U+FF61, plus tokens "```", `~~~`, `[.]`, `evil.com`, `www.evil.digital`, `db01.corp.example.com`, EM, `<HOSTNAME_1>`, `<EMAIL_1>`, `password=`, `?password=`, SV_B, `-----BEGIN PRIVATE KEY-----`; 0-200 tokens per text. ALPHABET-B = ALPHABET-A without `[`, `]`, `[.]` and the three wide dots. G-TXT = texts from ALPHABET-A. G-EH = prose lines of 1-6 words from `a-z`, EM-shaped addresses and `dbNN.corp.example.com`-shaped hosts built from parts.
**Property tests:** `test_defang_text_idempotent` (G-TXT); `test_defang_text_only_rewrites_dots` (ALPHABET-B: `defang_text(x).replace("[.]", ".") == x`); `test_sanitise_text_default_unchanged` (inputs = every string literal passed DIRECTLY as an argument to `sanitise_text`, `clean` or `withhold_commands` in `tests/warden_port/test_gate.py`, `test_gate_render.py`, `test_gate_review2.py`, `test_gate_review3.py`, `tests/test_g4_parity.py`, `test_k5_round9.py`, `test_k5_round11.py`, `test_p5p6_followups.py`, collected by AST; parametrised and computed inputs are not collected and are covered by G-TXT; the count is printed in `bs0-base.txt`; assertion `sanitise_text(x) == sanitise_text(x, defang=True) == frozen[x]`, message `DEFAULT CHANGED`); `test_pre_redaction_differential` (same inputs: `defang_text(withhold_commands(sanitise_text(x, defang=False))) == withhold_commands(sanitise_text(x))`; only exception: a placeholder followed by `.` and a name character, compared after applying `_PLACEHOLDER_DOT` to the right side; any other difference is a defect); `test_no_link_outside_code_on_card` (G-TXT: in markdown-it's token stream of the final `clean(x)`, no `text` token outside code matches `_DOMAIN`, `_NON_ASCII_HOST`, `_PLACEHOLDER_DOT` or `_WIDE_DOTS`); `test_card_masks_what_model_masks` (G-EH: no EMAIL or HOSTNAME original in the model path's map occurs in `clean(x).replace("[.]", ".")`). Time: the file runs in at most 120 s on the cloud machine; over that, the builder reports the number to the lead (no silent cut of the counts).
**Must stay green unchanged:** `tests/test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook`, `tests/warden_port/test_redaction.py::test_query_param_credentials_are_masked`.

## Mutation plan (`tests/p1d_a_mutants.py`; every mutant required; a survivor is a defect unless the lead accepts a written equivalence)
Registration, as `tests/stage_mutants.py`: a list of `tools.mutation_runner.Mutant(name, file, old, new, expect="ROW <killer>")`, then `run_mutants(ROOT, M, ["tests/test_p1d_a_rows.py"], extra_dirs=("tests", "tools"), only=..., on_result=..., forbid_skips=True)`; exit 1 if any is not good. **Depends on the R1 runner PR (ORDER 181) for `forbid_skips`:** the mutant evidence is run after R1 merges and P1d-a is rebased, or on the R1 branch; the evidence names which.
| mutant | file :: symbol | exact edit (`old` -> `new`) | killer |
|---|---|---|---|
| A1 | `approvals/channel.py :: _neutralise` | `sanitise_text(text, defang=False)` -> `sanitise_text(text)` | H26, H27 spy |
| A2 | `channel.py :: clean` | `return defang_text(out)` -> `return out` | L1 |
| A11 | `channel.py :: clean` | `return defang_text(alt)` -> `return alt` | T1 |
| A3 | `approvals/slack_channel.py :: _blocks` | `shown = defang_text(runmap.redact_text(withheld, seeded, neutralise=_neutralise))` -> `shown = runmap.redact_text(withheld, seeded, neutralise=_neutralise)` | L5 |
| A3b | `slack_channel.py :: _blocks` | `withhold_commands(undefang_text(req.summary))` -> `withhold_commands(req.summary)` | L7 |
| A3c | `slack_channel.py :: _blocks` | `if len(shown) > self.max_card_chars` -> `if len(shown.replace("[.]", ".")) > self.max_card_chars` | L9 |
| A3d | `approvals/gate.py :: undefang_text` | `return _outside_code(text, lambda part: _LEGACY_DOT.sub(".", part))` -> `return _LEGACY_DOT.sub(".", text)` | L10 |
| A3e | `gate.py :: _LEGACY_DOT` | `r"(?<=[\w-])\[\.\](?=[\w-])"` -> `r"\[\.\]"` | L12 |
| A4 | `gate.py :: _defang_prose` | `part = _PLACEHOLDER_DOT.sub(r"\1[.]", part)` -> `part = part` | H27, D3b |
| A17 | `gate.py :: _defang_prose` | the wide-dot line and the `_PLACEHOLDER_DOT` line swapped | D3e |
| A5 | `gate.py :: _per_part` | `parts = [line] if "``" in line else _INLINE_CODE.split(line)` -> `parts = [line]` | L2, D3c |
| A6 | `gate.py :: _outside_code` | `for s, e, ch in _closed_fences(text)` -> `for s, e, ch in []` | L3 |
| A12 | `gate.py :: _outside_code` | `range(s + 1, e)` -> `range(s, e)` | I1 |
| A13 | `gate.py :: _clean_prose` | `seen = out if defang else [_defang_outside_code(c) for c in out]` -> `seen = out` | Z4 |
| A18 | `gate.py :: sanitise_text` | `[_clean_line(line, defang) for line in body]` -> `[_clean_line(line) for line in body]` | E1 |
| A19 | `gate.py :: sanitise_text` | `_clean_line(opener.group(3), defang)` -> `_clean_line(opener.group(3))` | I2 |
| A10 | `gate.py :: sanitise_text` | `defang: bool = True` -> `defang: bool = False` | `DEFAULT CHANGED` |
| A7 | `guard/redact.py :: PATTERNS` plain entry | `[^\s\"';,]|` -> `[^\s\"';,&]|` (plain entry only; the string is unique) | H34a |
| A9 | `redact.py` plain entry | `(?<![\w.\-?&])` -> `(?<![\w.\-])` | Q2 |
| A8 | `redact.py` query entry | `&(?![^\s&#\"'=]*=)` -> `&` | Q2 |
| A14 | `redact.py` query entry | `|&(?![^\s&#\"'=]*=)` -> `` (removed) | Q4, Q5 |
| A20 | `redact.py` query entry | `[^\s&#\"'=]` -> `[^\s&\"'=]` | Q10 |
| A21 | `redact.py` query entry | `[^\s&#\"'=]` -> `[^&#\"'=]` | Q11 |
| A16 | `guard/runmap.py :: redact_text` | `for view in views:` -> `for view in ():` | H34b |
**Decided equivalent (not run):** A15 (query lookbehind removed: differs only where the key is preceded by more than 40 key characters, where the plain entry also refuses; the only effect is more masking). A22 (closer line kept verbatim: a closing fence line holds only markers and the prefix `[ \t>*+\-0-9.)]`, never a name with a top-level domain).

## Template fields
- **Package:** P1d-a, "defang after the redactor; `&` inside a password". Branch `core/P1d-a` from `0dabf1f`; one pull request. **Path class:** redaction; no round cap.
- **Depends on:** no product dependency (ORDER 177; HELD belongs to P1d-learn, ORDER 180). Mutant evidence depends on the R1 runner PR (ORDER 181). Ships first; P1d builds on it.
- **Class (R337):** "a step that changes the text runs before the step that must read it" (defang) and "a separator ends a value outside the grammar where it is a separator" (`&`). Siblings: R6, R7.
- **Neutral default / alternative:** no vendor; `defang=True` keeps every other caller's behaviour.
- **Files (under `src/hadavin_sdk/` unless top-level):** change `approvals/gate.py` (flag, ZWSP check, `defang_text`, `undefang_text`, D3); `approvals/channel.py` (`_neutralise`, `clean`; the comment "Nothing transforms the text after its final redaction" becomes "After the final redaction only `defang_text` runs: it writes `.` as `[.]` and wide dots as `.`"); `approvals/slack_channel.py` (`_blocks` order); `guard/redact.py` (entry split, comment); `CHANGELOG.md`. Create `tests/test_p1d_a_rows.py`, `tests/p1d_a_mutants.py`, `tests/fixtures/p1d_cases.py` (rows, generators, BS-1 corpus; P1d adds to it), `tests/fixtures/p1d_a_base_rows.json` and `tests/fixtures/p1d_a_gate_base.json` (written by the tool on base, committed unchanged), `tools/p1d_corpus.py`.
- **Interface:** `gate.sanitise_text(text, *, defang: bool = True) -> str`; `gate.defang_text(text) -> str`; `gate.undefang_text(text) -> str`. No other public change.
- **Reused:** `_defang_outside_code`, `_closed_fences`, `_INLINE_CODE`, `_DOMAIN`, `_NON_ASCII_HOST`, `_WIDE_DOTS`, `runmap.PLACEHOLDER` shape, the decoded-view pass of `redact_text`, `tools/mutation_runner.py`, the `fuzzgen.py` generator pattern. Checked, not needed: hashing, k1b, stats, evals, store. Not reused: running the whole redactor before the gate (broke two fuzz tests, P1d V8).
- **Hostile inputs:** encoded addresses (H36), entities (H34b, ENT, Q7, Q8), key between fences (L8), tag-split assignment (T1), wide dots (L6, Z4, D3e), placeholder look-alikes (D3), typed `[.]` (L10-L12), length boundary (L9). Contract suite: not applicable (no kind interface changes).
- **Security and least privilege:** no identity, right or secret. Link protection unchanged or stronger (G2 property). Test values built from parts. A typed `[.]` between name characters outside code is read as `.` before redaction (more masking; shown as `[.]` again after defang).
- **Race / process tests:** none (no shared state).
- **Rollback:** tag `pre-P1d-a`; revert commit. Summaries stored by the new code hold placeholders and `[.]`; old and new `_blocks` both show them correctly; no loud-failure test needed.
- **Reviewers:** fresh `egm-codebase-details` (correctness) + `egm-design` (adversarial), given the diff, this ticket and the evidence only.
- **Done =** a fresh round finds no blocker or major; gates green (tests 3.12 and 3.13, ruff check, ruff format --check, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit); BS-1 within the gates the lead confirms; ledger rows BL-core-p1d-002 and 007 FIXED-VERIFIED; the lead merges.

## Paths (measured 2026-11-09)
| what | path |
|---|---|
| handover worktree (branch `core/cloud-handover`) | `/home/user/hadavin-sdk` (the machine profile's `/home/user/hadavin-sdk-handover/handover` does not exist) |
| build worktree (branch `core/P1d-a`) | `/home/user/build/P1d-a`: `git -C /home/user/hadavin-sdk worktree add -b core/P1d-a /home/user/build/P1d-a 0dabf1fa7a2e` |
| base worktree (detached, thrown away) | `/home/user/build/P1d-a-base`: `git -C /home/user/hadavin-sdk worktree add --detach /home/user/build/P1d-a-base 0dabf1fa7a2e`; removed at the end with `git worktree remove` (never prune) |
| evidence snapshot | `/home/user/build/EV-P1d-a-<sha7>/wt` (detached at the PR head) |
| raw output | `/home/user/hadavin-sdk/handover/evidence/P1d-a/base-0dabf1f/` (BS-0, fail-before) and `.../P1d-a/<head sha7>/` (BS-1, evidence, mutants) |
`<s>` = a folder under the session scratchpad. Heavy runs (both full test runs, the perf run, the mutant run) go through `/home/user/build/heavy.sh <log> <command...>` started as a background job (it appends `exit=<rc>`); at most 3 at once (ORDER 178). `qsubmit.sh` does not exist on this machine.

## Build steps
- **BS-0 (HARD STOP; test tooling only, no product code).** In the build worktree write `tests/fixtures/p1d_cases.py`, `tools/p1d_corpus.py`, `tests/test_p1d_a_rows.py` first. Then: (1) `git -C /home/user/hadavin-sdk fetch origin`; `git rev-parse origin/main` = `0dabf1f`, or `git diff 0dabf1f origin/main -- src/hadavin_sdk/approvals/gate.py src/hadavin_sdk/approvals/channel.py src/hadavin_sdk/approvals/slack_channel.py src/hadavin_sdk/guard/redact.py src/hadavin_sdk/guard/runmap.py` is empty; (2) copy those three files to the same paths in the base worktree (never committed there); (3) `cd /home/user/build/P1d-a-base && UV_PROJECT_ENVIRONMENT=<s>/vbase uv sync --locked --no-build --python 3.13 --all-extras --group test`; (4) `UV_PROJECT_ENVIRONMENT=<s>/vbase uv run --no-sync python tools/p1d_corpus.py --rows --out /home/user/hadavin-sdk/handover/evidence/P1d-a/base-0dabf1f/bs0-base.txt --fixture tests/fixtures/p1d_a_base_rows.json > <s>/bs0.log 2>&1; rc=$?; tail -n 3 <s>/bs0.log; echo rc=$rc`; (5) same with `--freeze-gate --out tests/fixtures/p1d_a_gate_base.json`; copy both JSON files back to the build worktree unchanged; (6) `git grep -n "sanitise_text\|_neutralise\|_defang\|PATTERNS\[\|\.summary\b"` in `src`, `demos`, `tests` on main, recorded in `bs0-base.txt`; (7) read the two fuzz tests P1d V8 names; (8) read WHATWG URL section 5.1, record the date.
  **`--rows` output:** line 1 `base <full sha>`; line 2 `hadavin_sdk <path of the imported package>` (must be under `P1d-a-base`); then one line per row and path: `<row>\t<path>\t<json.dumps(output, ensure_ascii=True)>\t<FIT|MISMATCH|MISFIT: reason>`; a missing new name (`defang_text`, `undefang_text`) prints `NEW_SURFACE: <name> missing` and is FIT for fb rows; one `INFO-K41` line: the model output of `"a" * 41 + "password=hunter22 x"` (reported, no gate); the count of AST-collected literals. Exit 0 if all FIT, 3 otherwise.
  **STOP rule (exit 3):** a written "on base" cell differs (MISMATCH); a BS0 cell does not fit its class (MISFIT): fb whose base equals its expected after, pb whose base differs from a written expected after, ow whose base equals its expected after; a named assert of L8, T1 or W1 fails on base; a row with two paths gives two strings. A grep hit that shows a stored summary to a person outside R7 is also a STOP. On STOP: no product code; report to the lead; ticket revision.
- **Fail-before:** in the base worktree, `UV_PROJECT_ENVIRONMENT=<s>/vbase uv run --no-sync pytest -q tests/test_p1d_a_rows.py -rA > .../base-0dabf1f/fail-before.txt 2>&1` (base SHA prepended on line 1). Every fb row fails on its `ROW <id>` assertion (a new name is reached only after that assertion, through a helper that reports `NEW_SURFACE:`); every pb row passes; ow rows F16 and Q6 fail. The link property is also run once there and its result recorded (informative).
- **Build**, then **BS-1** on the build head.
- **BS-1 over-mask and leak corpus** (`tools/p1d_corpus.py --kind amp --seed 1 --path both --out .../<sha7>/bs1-overmask.txt`; exit 0 within the gates, 4 otherwise = build stops, numbers and failing texts to the lead, no pull request until the lead decides).
  Secret S: length 8-40 from `A-Z a-z 0-9 ! $ % * + - . / : @ ^ _ ~` (no white space, quote, `;`, `,`, `=`, `#`, `&`, `<`, `>`, `?`, backtick); `&` shapes insert 1-3 non-adjacent `&` at inner positions. Key from `password, passwd, pwd, api_key, token, client_secret, auth_token`. Tails (at most 100 characters): END (nothing); WORDS (space + 1-6 of 20 fixed lower-case words, no domains); FIELDS (1-3 of `&k=v`, k from `user, next, page, lang, id, ref`, v `[a-z0-9]{1,12}`); SEMI (`;` + WORDS); QUOTE (`"` + WORDS). Query shapes use the prefix `GET /p?` (no scheme, so the card does not remove it as a link).
  | shape | count | text | gate (proposal, NEEDS LEAD 1) |
  |---|---|---|---|
  | S1 | 50 | query, S without `&`, FIELDS (+ WORDS) | leak 0; hidden 0 |
  | S2 | 25 | query, S with `&`, FIELDS | leak 0; hidden 0 |
  | S3 | 25 | query, S, 1-2 of `&debug`/`&raw`/`&x1`, FIELDS | leak 0; hidden run = the flag segments exactly |
  | S4 | 50 | plain, S without `&`, END/WORDS/SEMI/QUOTE | leak 0; hidden 0 |
  | S5 | 50 | plain, S with `&` (H34 shape), END/WORDS/SEMI/QUOTE | leak 0; hidden 0 |
  | S6 | 50 | plain form body `<key>=S` + FIELDS (+ WORDS) (F16 shape) | leak 0; hidden run = tail up to the first space, quote or `;` exactly |
  | S7 | 20 | query, S = A + `&` + `[a-z]{2}=` + B, FIELDS | reported only (non-goal N4) |
  | REAL | 30 | made-up lines in real formats: 6 web-server access-log lines with query credentials, 6 `.env`/compose lines, 6 shell commands (`curl -d` form body, `mysql -p`), 4 connection strings with `;Password=`, 4 JSON log lines, 4 HTML-escaped URLs with `&amp;`; each with its secret(s) and its expected hidden text in the fixture | leak 0; over-mask exactly the listed lines |
  **Measures, per shape and per path (card = `clean`, model = `redact_text`):** leak = a run of 4 consecutive characters of S that occurs in the output (after removing placeholders, reading `[.]` as `.`, dropping ZWSP) and nowhere in the input outside S; hidden run = length of the tail minus the longest suffix of the tail that ends the normalised output. Leak and over-mask are printed as separate numbers, with the longest hidden run per shape. Basis of the gates: ORDER 165 (0 for ordinary secrets), ORDER 166 item 2 (over-mask measured apart), and the grammar of D2 (each hidden run is predicted exactly, so any other value is a defect).

## Evidence commands (EVIDENCE RUNNER, in `/home/user/build/EV-P1d-a-<sha7>/wt`; raw output to `/home/user/hadavin-sdk/handover/evidence/P1d-a/<sha7>/evidence-<n>.md`, line 1 `git rev-parse HEAD`; CI form from `.github/workflows/ci.yml` on main; each `> <s>/out 2>&1; rc=$?; tail -n 3 <s>/out; echo rc=$rc`, heavy ones through `heavy.sh`)
```
UV_PROJECT_ENVIRONMENT=<s>/v313 uv sync --locked --no-build --python 3.13 --all-extras --group test
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync ruff check src tests demos tools
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync ruff format --check src tests demos tools
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync pytest -q -m "not live and not perf" -rs
UV_PROJECT_ENVIRONMENT=<s>/v312 uv sync --locked --no-build --python 3.12 --all-extras --group test
UV_PROJECT_ENVIRONMENT=<s>/v312 uv run --no-sync pytest -q -m "not live and not perf" -rs
HADAVIN_TEST_PG_DSN=<dsn of a cluster from /home/user/build/pgstart.sh> PGUSER=postgres UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync pytest -q -m perf -rs
UV_PROJECT_ENVIRONMENT=<s>/scan uv sync --locked --no-build --only-group scan
UV_PROJECT_ENVIRONMENT=<s>/scan uv run --no-sync bandit -q -r src demos tools -ll
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync python tests/p1d_a_mutants.py        # alone; needs R1
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync python tools/p1d_corpus.py --kind amp --seed 1 --path both --out /home/user/hadavin-sdk/handover/evidence/P1d-a/<sha7>/bs1-overmask.txt
```
Postgres: one cluster per run, `initdb -E UTF8 --locale=C.UTF-8 -A trust -U postgres`, stopped after (machine profile). `tests/demo_askdata/test_validate_harm.py[dblink-connect]` needs `PGUSER`; a failure there counts as known only if it fails identically in the base worktree. If no local Postgres runs, the perf line comes from the pull request's CI run (job link in the evidence file).

## Owner-facing wording (CHANGELOG)
"Approval cards now hide e-mail addresses and internal server names behind placeholders, as text sent to the model already did; this also applies to requests saved before this change. Before, they were shown with `[.]` in place of each dot. A password written with an `&` inside it is now hidden up to the next space; in a web address, the part after `&` is treated as the next field only when it has the form name=value. Some text right after such a password may also be hidden (measured: see the evidence)."

## Ledger rows closed
BL-core-p1d-002 (BLOCKER, defang before redaction, H26-H27; H28a-b stay with P1d under row 001) and BL-core-p1d-007 (MAJOR, `&` ends a value, H34).

## NEEDS LEAD
1. BS-1 gates as proposed in the BS-1 table (ORDER 165: proposed ceilings go to the lead with the number and the basis).
2. Wide-dot host names are not recognised as hosts on either path (non-goal N5; read from the code, not run): proposed ledger row for P1d (redactor grammar). Same for INFO-K41 if BS-0 shows the secret.
3. `_blocks` reads `[.]` between name characters outside code as `.` before redacting, so requests stored before the fix are masked too (changes how stored requests render).

## Revision log
Rev 1 (2026-11-09): split from P1d rev 7 by ORDER 177; D2 query/plain split after the prototype broke the pinned query test with `&` allowed everywhere; D3 after the prototype left `<HOSTNAME_1>.example.com` linkable; H36a-b moved here; H28a-b left in P1d.
Rev 2 (2026-11-09): plan review round 1 resolved (`round1-resolve.md`, 33 findings): base pinned to main `0dabf1f` with a BS-0 hard stop; seeded stdlib generators; exact bracket invariant; exact strings per row; guarantee classes; ZWSP rule kept; pre-redaction differential; final-text link property; `alt`, `~~~`, info-string, legacy-summary and length rows; D3 regex; query continuation; BS-1 ceilings; sibling search; CI-form commands; mutants A3b-c, A11-A16.
Rev 3 (2026-11-09T07:55Z): plan review round 2 resolved (`round2-resolve.md`, 25 findings, all PROPOSE FIX, applied): legacy `[.]` undo limited to prose parts between name characters (`undefang_text`; rows L10-L12; mutants A3d-e); exact ZWSP rule on the would-be-defanged line (row Z4; A13); defang order wide dots, D3, hosts, domains (row D3e; A17); BS-1 corpus fully specified with seven shapes, a real-format sample, leak and hidden-run definitions and exact per-shape gates sent to the lead; BS-0 STOP rule per row class, tool modes and output format, base worktree with its own venv, fixtures written by the tool; one paths table, `heavy.sh` instead of the absent `qsubmit.sh`; Code shape block with exact mutant edits, registration with `forbid_skips` and the R1 dependency (ORDER 181); new mutants A17-A21, rows E1/I2 linked, Q10-Q11; A15 and A22 decided equivalent; card-map oracle; link property extended to placeholder dots and wide dots; literal-form reading rule; `&amp;` query rows Q7-Q8; non-goals N4-N5; R7 readers of stored summaries; references by symbol; ORDER 180 closed rev-2 NEEDS LEAD 2 (H28a-b) and confirmed D2.
