# Ticket PR H (rev 3, the LAST plan round; the lead freezes it with errata): remove hidden control characters and escape sequences once, at the one place all text passes, before anything else reads it

Source: decision D-018 (handover/AUTONOMOUS-DECISIONS.md), with D-016 and D-017; design review reviews/PR77/round8-design-zoomout-full.md; plan review round 1: reviews/PRH/plan-r1-readiness-full.md and reviews/PRH/plan-r1-design-full.md; plan review round 2: reviews/PRH/plan-r2-design-full.md (5 Majors D1-D4, D7; minors D5, D6, D8-D10) and reviews/PRH/plan-r2-readiness-full.md (9 Majors M1-M9; minors m1-m9); round-7 result reviews; sibling sweep F1 to F4; independent evidence evidence/PR77/97fd202/RESULTS.md; lead addendum of 2026-11-11.
Branch: NEW `core/prh-strip-hidden-controls` from origin/main (2a8c2aac on 2026-11-11); ready pull request against main; the builder never merges.
Path class: redaction (and placeholder forgery, a security matter). Extended review: yes, no round cap; the stop rule is in section 6.3.
Depends on: nothing. Pull request 77 rebases on this afterwards. PR H-c is no longer a prerequisite of any promise (W0). All file:line references are for origin/main 2a8c2aac (the directory `/home/user/build/q8a2-dryrun/main-2a8c2aa/` is the same commit, 7-character name).
Status: written by a ticket author. Nothing is built. The author gives no verdict on anyone's work. Rev 3 evidence: `handover/evidence/PRH-plan/r3/` (scripts in `r3/scripts/`); every number below that comes from there names its file.

## Rev 3: what is still NOT settled (read this first)

1. **Standards text is still not read.** `www.unicode.org` and `www.ecma-international.org` gave no answer again on 2026-11-11 17:08 UTC (`r3/hosts-check.out`: code 000). Every ECMA-48 clause number, the CWE names and the Unicode licence text stay "from memory", UNVERIFIED. Next step: the lead or owner fetches the Unicode licence text (questions-for-lead, PR H rev 3, item 1). The build does not wait for it: the range file is 17 lines of numbers produced from perl's and the `regex` package's own tables, and the file header says the licence check is open.
2. **The rev-3 rules are proven on the author's prototype and on reference scripts only**, never on a build: the overlap rule (W0), the `_scrub` rule (W3), dropping the views of the joined reading (D4), the step-6 refusal (W2). The prototype is the author's own code (Read first 2).
3. **The cost numbers of section 4.4 are composed estimates**, measured on main with the rev-3 cost-relevant pieces swapped in (`r3/cost-r3-main.out`), not an end-to-end run of the built design. The build's own T9 and acceptance 9 measure the real thing; section 4.4 says what happens when a limit fails.
4. **The worst shape W (Persian text, a colour change inside a word and a percent sign on every line) is estimated at 4.21 s CPU at the size cap** under load (limit 6 s). On a machine about 1.4 times slower it is refused (`InputTooLarge`). That is stated, not fixed (section 3, "not promised").
5. **One package was not judged:** `stransi` 0.3.0 (my adapter called a wrong method and raised on every row, `r3/rung3-compare.out`). The verdict of the reader row does not rest on it (section 4, rung table).
6. **The full suite, ruff, bandit, the mutation runner and the Python 3.12 suite were not run** by the author in any round.

## Changes since rev 2 (every round-2 finding and where it is answered)

| Id | Finding (short) | Answer in rev 3 | Where | Evidence (rev 3) |
|---|---|---|---|---|
| D1 | promise 2 broken by `_scrub`'s second branch and the step-6 fallback | `_scrub` finds on the joined copy but RETURNS the spaced copy with the found secret masked by the gap pattern, never the joined text; a backstop withholds the result (fail closed). Step 6 no longer returns the joined result: it raises `RedactionError` (fail closed); counted 0 firings over the author's inputs and the 43 files | W2 step 6, W3 `_scrub`, promise 2, T2 rows D1a-D1d, mutants 23, 31, 42 | `r3/d1-scrub-{main,proto,rev3}.out`; `r3/step6-count.txt`, `r3/targeted-r3-probe.log` |
| D2 | longest-first sort misses partial overlap, equal length, mixed domains; root deferred to PR H-c | new work package W0: ONE span rule for every place that puts known values back (the redactor's sweep, `_keep_earlier_masks`, `_redact_stripped` step 5): every occurrence is a span, contained spans dropped, a chain of partially overlapping spans gets ONE newly issued placeholder whose value is the merged text (restore stays exact). Main itself leaks on partial overlap (sweep and `_keep_earlier_masks`), so W0 fixes main | W0, T4, mutants 27, 38-41; PR H-c stub updated | `r3/d2-overlap-main.out` |
| D3 | 1.25x unproven, not a gate, Hindi 1.59x | measured: the Hindi excess was the prototype's slow reader, not `canonical` (per-character rule 1.04x, one compiled class 0.99x of main); composed estimates 1.00-1.04x on the five hidden-free shapes. Gates G1-G4 defined; G1-G3 are test assertions (pass counts, no extra decode, seconds), G4 the ratio in the evidence | 4.4, T9, acceptance 9 | `r3/cost-r3-main.out` |
| D4 | 18 passes unmeasured, ends in refusal | the views of the escaped joined reading are dropped (the decoded reading with hidden items removed in every round covers the same cuts: 0 verdict changes over the author's checks); at most 10 passes; W estimated 4.21 s CPU at the cap (rev-2 bound: 7.61 s, refused above about 206,700 characters) | 3 "Number of passes", W2 pseudo-code, T9 | `r3/cost-r3-main.out`, `r3/check-diff.txt`, `r3/repro-diff.txt` (both empty) |
| D5 (minor) | refusal above 256 needed values hits real input | stated in the CHANGELOG list; T9's M1 shape uses 300 distinct CUT values | 3 "not promised", T9 | - |
| D6 (minor) | step-5 pattern linear only by assertion | the gap ` ?` is placed only between two neighbouring WORD characters of the value (the glue rule only inserts a space there), so no optional space ever competes with a space of the value: one way to match at each position; T9 shape "spaced value + 10,000 spaces" | W2 step 5, T9, mutant 22 | - |
| D7 | rung-3 row UNVERIFIED | researched on PyPI (reachable): `regex` 2026.9.29 carries the property and equals the pinned file (4,174); strip-ansi 0.1.1 agrees with the grammar on 1 of 36 rows; pyte is a terminal emulator under LGPL-3.0; ansi2txt lists AGPL-3.0 and MIT. Ignorable table verdict now CUT-TO-CONFIG+GLUE (17 ranges of data, two independent sources); reader stays KEEP-CODE with the evidence; rows added for the policy rung, the generator, the oracle, `_scrub`, W0 | 4 rung table | `r3/rung3-pypi-metadata.out`, `r3/rung3-compare.out` |
| D8 (minor) | scope wider than the title | kept: one definition of "ignorable" for redaction AND grounding is the class fix (two definitions is the bug class of this ticket); the behaviour changes are listed in the CHANGELOG rules | 6.1 CHANGELOG rules | - |
| D9 (minor) | data file, generator modes, version time bomb, licence | `--from-ucd` mode dropped (no sample to test it); the equality test is gated by `unicodedata.unidata_version` (equality on 15.0.0 and 15.1.0; on any other version a superset check, and a FAILURE when `HADAVIN_REQUIRE_PINNED_UNIDATA=1`, which CI already sets) | W6, T10 | `r3/oracle-python.out`, `r3/oracle-python3.12.out` |
| D10 (minor) | jargon | "choke point", "oracle", "mutant", "glue rule", "held", "needed", "seed entry" defined in section 1 before use | 1 | - |
| M1 | `_first_decoded` "NO change" is wrong | confirmed on main (tools.py:786-791 calls `_decoded(char)[:1]`); rev 3: `_first_decoded` is EDITED to call `runmap.undo(char)[:1]` directly, keeping its `try/except` | W3, T12, mutant 33 | grep of main, this ticket 4.2 |
| M2 | reader grammar ambiguous; scope of `strip_sequences`; no oracle | the grammar is a complete state table (every state, every terminator, ESC inside a string, line end, end of text); `strip_sequences` = items that start with ESC or a C1 opener, nothing else; reference oracle with 38 grammar rows and 10 glue rows, linear, idempotent over 20,000 random strings | 4.1, T10 | `r3/scripts/hidden_ref_oracle.py`, `r3/oracle-*.out` |
| M3 | T5/T1 sources not in the snapshot | the files exist on branch `core/cloud-handover`; absolute paths and an extraction rule given | T5 | `ls` in this round |
| M4 | tests not mapped, killers unnamed, mutants 35/36 unkillable | table test -> file -> function name; must-fail naming rule `test_mf_*`; every mutant with its killer; 35/36 killed by direct unit tests of `_refuse_forgery` | 5, 5.2 | - |
| M5 | "four shapes" undefined; Hindi may fail; no remedy | five hidden-free shapes S1-S5 with their exact lines; Hindi measured 0.99x with the compiled class; remedy rule written | 4.4, acceptance 9 | `r3/cost-r3-main.out` |
| M6 | environment set-up | exact commands for worktree, venv, offline `uv`, `heavy.sh` with redirects, the main run for the skip list, Postgres | 6.0 | - |
| M7 | WP2 too big; stop rule vs green commits | seven work packages, each one commit, each sized to fit 60 minutes; per-commit check command; an unfinished package is handed over as a patch file, never as a red commit | 6.1, 6.2 | - |
| M8 | invisible characters, scan_repo, gitleaks found late | rule: every control or invisible character as an escape; the hash constant is named `RANGE_FILE_SHA256`; gitleaks and `tools/scan_repo.py` run after every work package; this ticket's own invisible literals rewritten as code points | 6.2, 2.4, 2.5, 4.1 | `r3/m8-gitleaks.out` (a 64-hex value named `hash_token_key` IS flagged by `generic-api-key`; `RANGE_FILE_SHA256` is not) |
| M9 | oracle's ignorable derivation not buildable | the two range lists are in the oracle script and in section 1; derived set equals the perl file on Python 3.13.18 (Unicode 15.1.0) and 3.12.3 (Unicode 15.0.0) | 1, T10 | `r3/oracle-*.out` |
| m1-m9, nits | see section 8.6 | | 8.6 | |

## Changes in rev 2 (history; each answered a round-1 finding; the full table is section 8.4)

1. **Case 790 diagnosed and the design changed** (readiness B2, design B1): the leak on the card path came from the order in which the redactor puts back earlier masks in a decoded reading (shorter value first). Design answer: one sorted list, longest spelling first (W2, `_keep_earlier_masks`). With that change the failing test passes under the author prototype, and 7,505 tests of 43 redaction-related files pass, also with every other rev-2 change (sections 8.1, 8.3).
2. **Line continuation split out** to its own ticket `tickets/PRH-b-line-continuation-matching.md` (readiness B1, design section 3). PR H leaves a backslash and a line end exactly as written; a key cut that way is "not promised", like a key cut by a tab or a line break.
3. **Map clean-up (old W5) split out** to `tickets/PRH-c-map-entries-hygiene.md` (design M4). The old test T4 (map invariants) and the old mutants 32, 33 are gone; the number T4 is reused for the case-790 test.
4. **Glue rule defined per run** of removed items, with an example table (design M3; section 4.1).
5. **The 256 limit**: only values that need the gap are counted; more than 256 refuse the text (`InputTooLarge`), as main's `_decoded_masks` does; values under 4 characters are replaced only as a whole word (design M1 and design section 3).
6. **One more decoded reading** that removes hidden items at the end of every decoding round, so a hidden item that cuts an encoding token (`%4` + `%1b[0m` + `1KIA...`) is read (design M2; reproduced on main and fixed in the prototype).
7. **Removing hidden items never creates a placeholder or a marker**, for every caller, including the approval card and model-written text (design M5; reproduced on main).
8. **Model-written inputs and grounding** now in the contract, with tests (design M6, readiness M1).
9. **`_first_decoded` stays on the plain decode** (design scope note, readiness M2); `_sanitise` second call site and the digest decided (readiness M3).
10. **Exact order of steps** as pseudo-code (readiness M4); Unicode data file decided: name, format, hash, version (readiness M5); constants built from parts (M6); fixtures recorded from main named with their command (M7); stop rule (M8); who runs what, time boxes and slots (M9); acceptance commands that an independent runner can run (all minors).
11. **Corrections**: OSC ended by U+009C row (checked by running main); no F1f; the hash of the data file must NOT go into `reference_material_sha256.txt` (that file is a deny-list of course material: a hash listed there makes `tests/test_no_reference_material.py` fail on the file); "reading" (a version of the text) and "pass" (one run of all patterns) now keep one meaning each; control-character names explained.

## Read first: what is not established

1. **Not verified from the standards themselves.** The hosts for the standards cannot be reached from the build machine (`curl -m 8 https://www.unicode.org/Public/15.1.0/ucd/DerivedCoreProperties.txt` and the ECMA-48 page both ended with code 000, no answer). Every statement about ECMA-48 clause numbers and about the Unicode derivation rule is marked "from memory" where it appears.
2. **"Author prototype" numbers are not independent evidence.** The author applied the planned design to a clean import of main by monkeypatching (throwaway, never committed). Rev 1 files: `/home/user/build/prh-author/scratch/proto.py`, drivers `check.py`, `fuzz.py`. Rev 2 files: `/home/user/build/prh-author/errata/prh_proto.py` (a copy of proto.py, renamed because a test file imports a third-party package called `proto`), `errata/fixes.py` (the rev-2 design changes on top), `errata/fix790.py`, `errata/repro.py`, `errata/c790*.py`, `errata/check2.py`, `errata/cost2.py`; raw outputs copied to `handover/evidence/PRH-plan/`. Rev 3 runs the same prototype through `r3/scripts/run_without_joined_views.py` and `r3/scripts/plug_r3.py` (one line changed in memory, see 8.6). The prototype's escape-sequence reader is the author's own quick version and is NOT the rev-3 grammar; the rev-3 grammar is in `r3/scripts/hidden_ref_oracle.py`. Prototype counts are not cited as evidence that the design is correct. The builder's tests must not share code with the implementation (section 5).
3. **Not run by the author:** the full suite, ruff, bandit, `tools/scan_repo.py`, gitleaks, the `perf` tests, the mutation runner, Python 3.12 tests. The 43 files of section 8.3 (every test file that imports the redaction modules, including `tests/warden_port/test_gate.py` and `test_gate_render.py`; list in `handover/evidence/PRH-plan/target-files.txt`) were run under the prototype only.
4. **Handed-out secrets were checked with two inputs only** (L6, L12 below).
5. **The inputs of rounds 5 and 6 were not re-read one by one.** The regression file (section 5, T5) names the source files the builder must take every input from.
6. **"The six leak inputs on main"** are not listed anywhere the author could find (AUTONOMOUS-LOG line 33 gives only the count). The author reproduced twelve on main and names them L1 to L12.
7. Whether the judge and the vendor screen should escape placeholder-shaped text (open question 1) was decided from a grep, not from a full trace of every call chain. Rev 2 narrows the risk: removing hidden items can no longer create a placeholder or a marker on those callers (W2 step "no created shapes").
8. M4 of the design review (map clean-up dropping a protecting entry) was NOT reproduced: 0 of 3,000 generated inputs. It was split out anyway (section 8.2, row M4).

## 1. Problem in plain words

Before any text reaches a model, a log or the audit trail, the package replaces secrets and personal data with stand-ins such as `<EMAIL_1>` (this is "redaction"; the stand-in is a "placeholder"). It does this by looking for known shapes: an access key, an e-mail address, `password=` followed by a value.

Some characters are not shown on a screen at all. Examples: the colour codes a terminal program prints (an "escape sequence": the escape character, then a few more characters that say "switch to green"), a backspace, a bell, a zero-width character. If one of these sits in the middle of a key, a person reading the screen sees the key whole, but the redactor sees two halves, recognises neither, and lets both through. On main today this is the case: `AKIA` + escape `[0m` + `IOSFODNN7EXAMPLE` comes out with both halves readable (section 2).

The same trick works the other way round. Untrusted text (a document, a tool's answer) must never contain a real-looking placeholder or the marker line that ends a tool's answer, so the package escapes those shapes. But it removes escape sequences only later, inside the redactor. So `<` + escape `[0m` + `IPV4_2>` passes the escaping step as harmless, and the later removal then assembles a real-looking `<IPV4_2>`. On main today this happens on every untrusted path and on the approval card (sections 2.5 and 8.2).

**Bug class:** the text is changed (hidden items removed) AFTER the safety checks have read it, and different places read escape sequences by different rules. In the common catalogue of software weaknesses this is "validate before canonicalize" (CWE-180) and "improper neutralization of escape, meta or control sequences" (CWE-150); both names from memory.

**Notation.** Every invisible or control character in this ticket is written as its Python escape (`\u200b`, `\x1b`), never literally; inside a value column the escape stands for the one character.

**Names of character groups used in this ticket, in plain words** (from ECMA-48, the standard for control characters, the same text as ISO/IEC 6429; from memory):
- *control character*: a character that is an instruction to a terminal or printer, not a letter. *C0* = the 32 control characters U+0000 to U+001F (backspace, bell, tab, line feed, escape ...). *DEL* = U+007F. *C1* = the 32 control characters U+0080 to U+009F (rarely used on purpose; they also appear when Windows-1252 text is decoded wrongly).
- *ESC* = the escape character U+001B, which starts an escape sequence. *BEL* = bell U+0007. *NUL* = U+0000. *CAN* (cancel, U+0018) and *SUB* (substitute, U+001A) abort a sequence that has started.
- *CSI* ("control sequence introducer") = ESC `[` or the single character U+009B. A *control sequence* is CSI, then digits and a few punctuation characters, then one letter-like final character; colour codes are of this kind (ESC `[0m`).
- *string sequences*: OSC (operating-system command: ESC `]`, used to set a window title), DCS (device control string: ESC `P`), SOS (ESC `X`), PM (ESC `^`), APC (ESC `_`), and their single-character C1 forms. Each carries a text that is not shown and ends with *ST* ("string terminator": ESC backslash or U+009C); OSC also ends at BEL.
- *nF*, *Fp*, *Fe*, *Fs* (ECMA-35, from memory): short escape sequences of ESC plus one or two more characters (ESC `(B` selects a character set; ESC `7` saves the cursor; ESC `M` moves the cursor; ESC `c` resets the terminal).
- *Default_Ignorable_Code_Point* (Unicode Standard Annex 44, data file `DerivedCoreProperties.txt`): the characters a display shows as nothing when it has no special handling for them (zero-width characters, variation selectors, Hangul fillers, tag characters).

**Standards the fix follows:**
- **ECMA-48** (5th edition 1991): what a control character and an escape sequence are. C0 = U+0000 to U+001F; DEL = U+007F; C1 = U+0080 to U+009F; control sequence = CSI, parameter bytes 0x30 to 0x3F, intermediate bytes 0x20 to 0x2F, one final byte 0x40 to 0x7E; string sequences end at ST. Clause numbers 5.2 to 5.6 and 8.3: from memory. ECMA-48 does not say what to do with a control character inside a control sequence or with a string that never ends; the usual reference for that is Paul Williams' state diagram of the DEC terminals (from memory; not a standard). Section 4.1 writes the exact rules down, so the build does not depend on anyone's memory of the diagram.
- **Unicode Default_Ignorable_Code_Point**. Python's `unicodedata` does not carry this property. Facts checked on this machine on 2026-11-11 (`handover/evidence/PRH-plan/di-312-313.out`; rev 3: `r3/oracle-python.out`, `r3/oracle-python3.12.out`, `r3/rung3-compare.out`): perl 5.38.2 carries the property for Unicode 15.0.0 and lists 4,174 code points in 17 ranges; the `regex` package 2026.9.29 (PyPI, uploaded 2026-09-29) carries it too and gives the same 4,174; the derivation rule below gives the same 4,174 with Python 3.13.18 (`unicodedata.unidata_version` 15.1.0) AND Python 3.12.3 (`/usr/bin/python3.12`, 15.0.0). 32 characters of category Cf are not in the property (for example U+0600 to U+0605, U+FFF9 to U+FFFB); main already ignores them in `canonical`, and PR H keeps that.
  **The derivation rule, written out so the oracle can be built from this ticket (M9)** (the list of Other_Default_Ignorable_Code_Point and Variation_Selector ranges is from memory and is cross-checked by the equality above, not by the standard's text):
  - start with these ranges (Other_Default_Ignorable_Code_Point and Variation_Selector): U+034F; U+115F..U+1160; U+17B4..U+17B5; U+180B..U+180D; U+180F; U+2065; U+3164; U+FE00..U+FE0F; U+FFA0; U+FFF0..U+FFF8; U+E0000; U+E0002..U+E001F; U+E0080..U+E0FFF;
  - add every code point whose `unicodedata.category` is `Cf`;
  - remove U+FFF9..U+FFFB, U+13430..U+1343F, and the Prepended_Concatenation_Mark characters U+0600..U+0605, U+06DD, U+070F, U+0890..U+0891, U+08E2, U+110BD, U+110CD (no Cf character is White_Space, so that exclusion removes nothing).
  The result is 17 ranges: `00AD 034F 061C 115F..1160 17B4..17B5 180B..180F 200B..200F 202A..202E 2060..206F 3164 FE00..FE0F FEFF FFA0 FFF0..FFF8 1BCA0..1BCA3 1D173..1D17A E0000..E0FFF` (`r3/oracle-python.out`, line "ranges").

## 2. Facts on main

Clean worktree: `git -C /home/user/hadavin-sdk worktree add --detach /home/user/build/prh-author/main origin/main` (HEAD 2a8c2aac); environment `UV_PROJECT_ENVIRONMENT=/home/user/build/prh-author/venv uv sync --all-extras --group test` (exit 0). Every probe ran as `env -i PATH=/usr/bin:/bin HOME=/root /home/user/build/prh-author/venv/bin/python <script>` from that worktree (no cloud configuration in the environment). Outputs show only verdict words. First line of every rev-1 probe: `python 3.13.18 unidata 15.1.0 cap 262144 budget 6.0`.

**Constants (made-up, built from parts; every test, fixture and evidence script uses exactly these):**

| Name | Python expression | Length |
|---|---|---|
| KEY | `"AKIA" + "IOSFODNN7EXAMPLE"` | 20 |
| KEY2 | `"AKIA" + "ZZZZODNN7EXAMPL2"` | 20 |
| MAIL | `"bob.smith" + "@" + "example.com"` | 21 |
| PW | `"hunter" + "2secretXYZ"` | 16 |
| HAND (a secret handed out to a tool) | `"Tr0ub4dor" + "-3xyzQ"` | 15 |
| TOK (a bearer token) | `"abcDEF123456" + "ghiJKL7890mnop"` | 26 |
| IP | `"10.20.30.44"` | 11 |
| PH | `"<" + "IPV4_2" + ">"` | 8 |
| ESC, BEL | `"\x1b"`, `"\x07"` | 1 |

G1 = `"user" + BEL + KEY`; G2 = `"user" + ESC + "[0m" + KEY`; G3 = `"a " + KEY[:4] + ESC + "[0m" + KEY[4:] + " b user" + BEL + KEY2`.

### 2.1 Where untrusted text enters redaction (grep over `src/`)

`redact_text` (guard/runmap.py:464) is the one function all of these reach ("the choke point"; `guard/producers.py:1-9` says so and `tests/test_k5_producers.py` enforces it):

| Entry | file:line | Escaping step ("neutralise") given? | Feeds |
|---|---|---|---|
| `redact_untrusted` | runmap.py:346-350 | yes, `neutralise_untrusted` | see callers |
| document | runtime/agent_loop.py:412 | yes | model |
| tool result | tools.py:936 `prepare_output` -> :967 -> `redact_layered` :976-984 | yes | model, inside the `<<TOOL RESULT ...>>` frame (agent_loop.py:580) |
| tool error text | tools.py:987 `error_reason` -> :1005 `redact_bounded` | yes | model |
| case bundle | k1b/redaction.py:188 | yes | model |
| eval case document | evals.py:63 | yes | model |
| approval card text | approvals/channel.py:29 and :36; approvals/slack_channel.py:81 | its own step (the approval gate's cleaning, `channel._neutralise` :47), not the marker and placeholder escaping | a person |
| judge input | guard/judge.py:71 | **no** | model (the judge) |
| vendor screen input | guard/bedrock_guardrail.py:98 | **no** | vendor service |
| grounding check | runtime/evidence.py:154 | **no** (a value the model typed) | comparison only |
| proposal inputs, tool-call arguments | runtime/evidence.py:191, runtime/agent_loop.py:534 -> `redact_value` runmap.py:568, :590, :593 | **no** (model-written) | store, audit trail, card, and (restored) the executor |
| short messages | `safe_head` runmap.py:532-541 -> `redact_bounded` :554 | **no** | log lines (runtime/tick.py:292, guard/injection.py:96), stored raw model reply (k1b/loop.py:187, :194), validation errors (extract.py:58; the error text at extract.py:62 is fed back to the MODEL) |

Other readers of the same characters, outside the choke point: `runmap.canonical` is also used by `runmap.nfkc` (runmap.py:103-109), which runs inside every round of `undo` (runmap.py:141), so it reaches the scrub of handed-out secrets (`tools._decoded`), the decoded readings (`_views`, runmap.py:410) and `_decoded_masks`; and directly for comparison in runtime/evidence.py:57, :87, :88, :151. The approval gate has its own set and its own views (approvals/gate.py:125-137 `_CONTROL_CHARS`, :162 `strip_controls`, :200-205 `normalise`, :212-220 `_views`) and imports `strip_ansi` from the redactor (gate.py:74). `store/migration_numbers.py:76` has an unrelated set for SQL files.

Answer to the lead's point 2: the callers WITHOUT the escaping step that feed a model, a vendor, a log or the audit trail are the six "no" rows above. By grep, the result frame is written in one place only (agent_loop.py:580) and its content comes from `prepare_output` (with escaping); no "no" row feeds that frame. This is a grep result, not a full trace. What PR H does for them: section 3, promise 3b, and open question 1.

### 2.2 Order of the steps today

`redact_text` (runmap.py:486-526): (1) size cap :486; (2) `_clean` :488 deletes U+0000 and repairs lone surrogates; (3) the caller's escaping step :489-490; (4) decide whether other readings are needed :491 (only for non-ASCII text or text holding a backslash, `%` or `&`) and build them :492; (5) `redact()` :494, whose `find` (redact.py:919-923) FIRST calls `strip_ansi` :920 and THEN runs the patterns; (6) each other reading is escaped :512-513, earlier masks are put back in it (`_keep_earlier_masks` :514, in LIST order), then it is redacted :515, and it REPLACES the output when it found something new :517-518; (7) `_clean` again :519. So escape sequences are removed at step 5, after the escaping at step 3. Characters other than escape sequences (backspace, bell, DEL, the C1 set) are never removed.

Tool path `prepare_output` (tools.py:949-973): (1) `_sanitise` :951 turns U+0000 into U+FFFD (the choke point DELETES it: two rules for one character); (2) size cuts; (3) scrub of handed-out secrets :959 on the text as it came (`_scrub` :898, `_scrub_layers` :906-933, decoded reading `_decoded` :726 = `runmap.undo`); (4) `redact_layered` :967, which is the order above. So the scrub also runs before any escape sequence is removed. `error_reason`: scrub :1002, then the choke point :1005. The tool runner calls `_sanitise` a second time at tools.py:1194, BEFORE the digest `ToolOutput.sha256` is computed at :1197 and before `prepare_output`.

`safe_head` adds nothing of its own: it calls `redact_bounded` and cuts (runmap.py:539-541). It does not collapse line ends; `tick.py:292` replaces only the line feed.

### 2.3 How many readers of escape sequences, and what each accepts

Command: `python scratch/probe2.py` (file `scratch/probe2.out`); the OSC-with-U+009C row was rerun for rev 2 (`handover/evidence/PRH-plan/repro-main.out`, last line).

There is ONE real escape-sequence reader on main: the pattern `_ANSI` (redact.py:820-822), used through `strip_ansi` (:825-838) by `find` (:920), by the bank-word check (:877, :1254) and by the approval gate (gate.py:205, :217). There are three more places that treat the same bytes by other rules: `gate._ANSI_AS_TEXT` (gate.py:197, an escape written out as text such as backslash-x-1-b), `gate._CONTROL_CHARS` (single characters deleted, gate only), and `runmap.canonical` (:276-282), which keeps every one of them. The "three parsers that disagree" of the round-7 reports exist on the pull-request branch; on main the disagreement is between these four places.

| Family (built from parts) | `strip_ansi` on main | `canonical` on main | gate (`strip_controls(strip_ansi)`) |
|---|---|---|---|
| CSI: ESC `[0m`, ESC `[?25l`, ESC `[1 q`, U+009B `0m` | removed whole | kept whole | removed whole |
| CSI with a bell or DEL inside | not recognised, all left | kept | leaves `[0m` |
| OSC ended by bell, by ESC backslash | removed whole | kept | removed |
| OSC ended by U+009C (**corrected in rev 2**) | U+009C is NOT read as the end: everything after the opener is removed up to the next bell or ESC or the end of the text, including the following lines (`'a ' + ESC + ']0;title' + '\x9c' + 'visible after' + LF + 'line two'` -> `'a '`) | kept | same loss |
| OSC never ended, followed by two more lines | removed TOGETHER WITH the following lines (`'a ' + ESC + ']0;t' + LF + 'line two' + LF + 'line three'` -> `'a '`) | kept | same loss |
| OSC with the C1 introducer U+009D | not recognised | kept | leaves `0;t` |
| DCS (ESC `P` ... ST), SOS (ESC `X`), PM (ESC `^`), APC (ESC `_`) | only the two-character opener and closer removed, the payload stays as text | kept | payload stays |
| C1 DCS U+0090 ... U+009C | not recognised | kept | payload stays |
| ESC `(B`, ESC `#8` (nF) | not recognised | kept | leaves `(B`, `#8` |
| ESC `7`, ESC `=` (Fp); ESC `c` (Fs) | not recognised | kept | leaves `7`, `=`, `c` |
| ESC `M` (Fe) | removed | kept | removed |
| lone ESC, lone U+009B | left | kept | removed |

Single facts from the same runs:
- Glue rule on main: `strip_ansi('ab' + ESC + '[0m' + 'cd')` -> `'ab cd'` (a space where a sequence stood between two word characters), `strip_ansi('ab-' + ESC + '[0mcd')` -> `'ab-cd'`.
- `tools._sanitise('a' + NUL + 'b')` -> `'a�b'`; `runmap._clean` of the same -> `'ab'`.
- `canonical` removes category Cf only: of zero-width space, U+FE0F, backspace, ESC, U+3164, U+034F it removes only the zero-width space (and turns U+3164 into U+1160, which is also invisible).
- Categories: U+FE0F and U+034F are Mn, U+3164 is Lo, backspace, U+009B and U+0085 are Cc, U+2028 is Zl.
- `str.isspace()` is True for tab, U+000B, U+000C, U+001C to U+001F, U+0085, U+2028, U+2029.
- The gate's set holds every C0 character except tab and line feed, and all of U+007F to U+009F; carriage return is in it.
- Main has no `is_hidden`, no `textnorm`, no ignorable table, no `_refuse_forgery`, no `_mask_in_place`. What main does have and PR H improves: `canonical`, `_canonical_view`, `replace_canonical`, `strip_ansi`, `_keep_earlier_masks`, `_decoded_masks`, `undo`.

### 2.4 Leaks reproduced on main

Command: `python scratch/check.py --main` (file `scratch/check-main.out`). Verdict LEAKED = a named piece of the secret stands in the output; MASKED = none does. Paths: untrusted = `runmap.redact_untrusted(t, {})`; tool = `tools.prepare_output(t, {}, 4000, secrets)`; error = `tools.error_reason(ValueError(t), secrets)`; head = `runmap.safe_head(t, 4000)`. Constants: see the table above.

| Id | Input, as a Python expression | untrusted | tool | error | head |
|---|---|---|---|---|---|
| L1 | `"id " + KEY[:4] + ESC + "[0m" + KEY[4:]` | LEAKED | LEAKED | LEAKED | LEAKED |
| L2 | `"id " + KEY[:4] + "\ufe0f" + KEY[4:]` | LEAKED | LEAKED | LEAKED | LEAKED |
| L3 | `"id " + KEY[:4] + "\x08" + KEY[4:]` | LEAKED | LEAKED | LEAKED | LEAKED |
| L4 | `"to " + MAIL[:i] + "\ufe0f" + MAIL[i:]`, `i = MAIL.index("exam") + 4` | LEAKED | LEAKED | LEAKED | LEAKED |
| L5 | `"pass\u034fword=" + PW` | LEAKED | LEAKED | LEAKED | LEAKED |
| L6 | `"auth failed for " + HAND[:9] + ESC + "[0m" + HAND[9:]`, HAND handed out | (no list) | LEAKED | LEAKED | (no list) |
| L7 | `"password=" + PW[:6] + ESC + "[0m" + PW[6:]` (the tail stays) | LEAKED | LEAKED | LEAKED | LEAKED |
| L8 | `"id " + KEY[:4] + "\x00" + KEY[4:]` | MASKED | LEAKED | MASKED | MASKED |
| L9 | `"id " + KEY[:4] + ESC + "(B" + ESC + "[m" + KEY[4:]` (what `tput sgr0` prints) | LEAKED | LEAKED | LEAKED | LEAKED |
| L10 | `"id " + KEY[:4] + "\u3164" + KEY[4:]` | LEAKED | LEAKED | LEAKED | LEAKED |
| L11 | `"id " + KEY[:4] + "%1b[0m" + KEY[4:]` (the escape character percent-encoded) | LEAKED | LEAKED | LEAKED | LEAKED |
| L12 | `"x " + HAND[:5] + "\x9b0m" + HAND[5:]`, HAND handed out | (no list) | LEAKED | LEAKED | (no list) |
| M2a | `"id %4%1b[0m1KIA" + KEY[4:]` (new in rev 2: a hidden item cuts the percent-encoded first letter of the key) | LEAKED | LEAKED | - | - |
| M2b | `"id %4\\x1b[0m1KIA" + KEY[4:]` (the same, escape written as backslash text) | LEAKED | LEAKED | - | - |
| G3 | see constants | LEAKED | LEAKED | LEAKED | LEAKED |

Controls, same run: the plain key, the plain address, the plain `password=` pair and the plain handed-out secret are MASKED on their paths; the key cut by a zero-width space (category Cf) is MASKED; `"id %41KIA" + KEY[4:]` is MASKED. A wider table (19 hidden items times 6 carriers) is in `scratch/probe1.out`.

Visible separators, same run, for the contract's "not promised" list: KEY cut by a tab, by U+2028, by a form feed, and by backslash + line break: LEAKED on all four paths on main.

Two behaviours of main that a simple "delete everything hidden" would BREAK: G1 and G2 are MASKED on all four paths today, because the hidden item acts as a word boundary; so are `"user" + BEL + BEL + KEY` and `"user" + ESC + "[0m" + ESC + "[1m" + KEY` (rev 2, `repro-main.out`, rows M3a, M3b). The plain text `"user" + KEY` is not masked on main (`scratch/probe3.py`). On the tool path, `"user" + NUL + KEY` is masked today (the U+FFFD is a boundary).

### 2.5 Forgery on main

Same command. "FORGED PLACEHOLDER" = a genuine-shaped placeholder that this call's map does not hold stands in the output; "FORGED MARKER" = the result-marker shape stands in the output or in its canonical form. The ids skip F1f: that letter was given to a candidate input that did not forge anything and was dropped; the other ids are kept so they match the scratch outputs.

| Id | Input | untrusted | tool | error |
|---|---|---|---|---|
| F1a | `"log <" + ESC + "[0m<END TOOL RESULT>> more"` | FORGED MARKER | FORGED MARKER | FORGED MARKER |
| F1b | `"peer <" + ESC + "[0m" + "IPV4_2> refused, seen from 10.0.0.5"` | FORGED PLACEHOLDER | FORGED PLACEHOLDER | FORGED PLACEHOLDER |
| F1c | `"<\x9b0m<END TOOL RESULT>>"` | FORGED MARKER | FORGED MARKER | FORGED MARKER |
| F1d | `"peer <" + ESC + "\u200b[0m" + "IPV4_2> refused"` | FORGED PLACEHOLDER | FORGED PLACEHOLDER | FORGED PLACEHOLDER |
| F1e | `"<%1b[0m" + "IPV4_2>"` | FORGED PLACEHOLDER | FORGED PLACEHOLDER | FORGED PLACEHOLDER |
| F1g | `"<<END TOOL" + ESC + "M RESULT>> x"` | FORGED MARKER | FORGED MARKER | FORGED MARKER |
| B1 | `"id: \x9b" + "<IPV4_1>" + " is down"` | handled | handled | handled |
| B1b | `"id: " + ESC + "[" + "<IPV4_1>" + " is down"` | handled | handled | handled |
| B2 | `"log <<END\x0cTOOL\x0cRESULT>> more"` | handled | handled | handled |
| B2b | `"log <<END TOOL RES\x9bULT>> more"` | handled | handled | handled |
| M5a (card, rev 2) | `channel.clean("<" + ESC + "[0mIPV4_1> and 10.0.0.5")` | card shows `<IPV4_1> and <IPV4_1>`: one forged placeholder and the real one, the same name for two things (`repro-main.out`) | | |

So the two forgery inputs of the round-7 review (B1, B2) are handled on main and must stay handled. Main is NOT free of this class: six inputs forge a marker or a placeholder on every untrusted path (sweep finding F1, reproduced by running), and M5a forges one on the approval card. PR H must fix these seven and keep the four.

### 2.6 Cost on main at the size cap

The cap is `defaults.MAX_REDACT_CHARS` = `MAX_DOCUMENT_BYTES` = 262,144 characters (defaults.py:31, :38); the time budget is `defaults.REDACT_BUDGET_S` = 6.0 s (defaults.py:49), checked between readings (runmap.py:496, :508). Command: `python scratch/cost.py` (file `scratch/cost.out`), one run per row, `redact_untrusted`, machine under other load (load averages near 5), so read these as rough.

| Shape (one line repeated to the size) | 131,072 chars: wall / CPU | 262,144 chars: wall / CPU | output equals input |
|---|---|---|---|
| plain ASCII log | 0.27 s / 0.19 s | 0.39 s / 0.39 s | yes |
| tab-separated table | 0.22 s / 0.20 s | 0.40 s / 0.40 s | yes |
| JSON lines | 0.22 s / 0.20 s | 0.42 s / 0.40 s | yes |
| coloured output (four colour codes per line) | 0.13 s / 0.12 s | 0.24 s / 0.24 s | no (codes removed) |
| Hindi | 0.42 s / 0.39 s | 0.86 s / 0.80 s | yes |
| Persian with zero-width non-joiner and emoji | 0.76 s / 0.72 s | 1.56 s / 1.43 s | yes |

### 2.7 Other facts used by the design

- Fact 14, ignorable table: see section 1 (4,174 code points, 17 ranges, equal on Python 3.12.3 and 3.13.18; perl 5.38.2 reports Unicode 15.0.0). The `regex` package is not installed (`ModuleNotFoundError`).
- Fact 15, map entries: moved to `tickets/PRH-c-map-entries-hygiene.md`.
- Fact 16, known values glued to a word (`scratch/probe3.py`): with the value already in the map, a key and an e-mail address glued to word characters are masked by the redactor's sweep of known values; an IP address and a host name are not.
- Fact 17: `tests/test_k5_tools.py` replaces `runmap.redact` with a failing stand-in (lines 306-317, not re-checked by the readiness reviewer because the tests were not in its snapshot; the author read them in the worktree). The new code in runmap.py must keep calling the redactor through the module-level name `redact`.
- Fact 18 (rev 2), the cause of case 790: section 8.1.
- Fact 19 (rev 2): `tests/fixtures/reference_material_sha256.txt` is read by `tests/test_no_reference_material.py:13` as a deny-list ("a tracked file with one of these hashes means vendor or course material was copied into the repo"). Rev 1 wanted to pin the data file's hash there; that would make the guard test fail on our own file. Rev 2 pins it in the unit test instead (W6).
- Fact 20 (rev 2): `python -c "import sys, hadavin_sdk.guard.redact; print(sorted(m for m in sys.modules if m.startswith('hadavin_sdk')))"` on main prints `['hadavin_sdk', 'hadavin_sdk.defaults', 'hadavin_sdk.guard', 'hadavin_sdk.guard.egress', 'hadavin_sdk.guard.injection', 'hadavin_sdk.guard.redact', 'hadavin_sdk.guard.runmap', 'hadavin_sdk.models']` (used by acceptance 8).

## 3. The contract

**Words** (each keeps this one meaning everywhere in the ticket, the code comments and the CHANGELOG):
- A *hidden item* is one member of the classes "removed", "space-like" or "ignorable" in the table below, or one whole escape sequence (section 4.1).
- A *run* is a longest stretch of removed items and escape sequences with nothing else between them.
- A *reading* is one version of the text that the patterns are run over. The *joined reading*: every run deleted, every space-like item turned into one space. The *spaced reading*: the same, except that where a run has a word character (letter, digit or underscore) directly on both sides, one space is left in its place. Ignorable items stay in both readings (they are not removed, and they are not word characters). The other readings are the *canonical reading* (NFKC, ignorables removed) and the *decoded readings* (percent, entity, backslash and JSON escapes undone), as on main, plus one new decoded reading (W2).
- A *pass* is one run of all the patterns over one reading.
- *Find* means: run the patterns over the joined reading to learn which values are secrets. *Mask* means: put placeholders into the spaced reading, which is what the reader is given.

**The promise ("hidden items never help"):**
1. *Masking.* Every value that the redactor masks in the joined reading of a text is unreadable in the output for that text, on every producer path. A value cut by hidden items is masked like the same value uncut. This includes the decoded readings: a hidden item that a decoder produces, or that cuts an encoding token, is treated the same way (row M2a, M2b).
2. *No step back.* Every value that main masks today because a hidden item acted as a word boundary (G1, G2, runs of them) stays masked, on every path, also when the same text holds a handed-out secret (rows D1a, D1b) or a value cut by hidden items. Rev 3 has NO designed exception: no step returns the joined reading as output (`_scrub` returns the spaced copy, W3; `_redact_stripped` step 6 refuses instead of falling back, W2). Where the design cannot keep both promises for one text, it refuses the text (`RedactionError` or the scrub's withheld marker), it never shows it.
3. *Forgery.* (a) On the untrusted paths, the output holds no result-marker shape and no genuine-shaped placeholder that the redactor did not issue, read both as written and in canonical form. (b) On the callers listed in 2.1 (untrusted paths, the approval card, model-written text, the judge and vendor-screen inputs, short messages), for removal of the items of the class table below: removing hidden items never creates a genuine-shaped placeholder or a marker shape; one that would appear only after the removal is written in the escaped look-alike form (`‹IPV4_1›`, the same form `escape_placeholders` writes). A placeholder or marker spelled plainly behaves exactly as on main.
4. *Model-written text.* Tool-call arguments and proposal inputs reach the store, the audit trail, the approval card and (restored) the executor with removed items deleted (a space left between two word characters) and space-like items turned into one space. Example: a "write note" argument with a form feed in it now carries a space.
5. *Grounding.* The grounding check compares values with every ignorable item ignored (main ignores only category Cf): an identifier the model typed that holds any ignorable item is refused (main refuses only Cf), and an evidence text with an ignorable item inside a name grounds that name (main does that only for Cf).

**This is deliberately NOT worded "as a terminal shows it".** D-018 uses that wording; the author's check shows it would be a false claim. A terminal moves its cursor: `AKIA` + `X` + backspace + the rest of the key is shown as the whole key (the next letter overwrites the `X`), and no reading that only deletes items contains that key. PR H does not imitate a terminal.

| Class | Members (exact) | Treatment | Why | Not promised |
|---|---|---|---|---|
| removed | C0: U+0000 to U+0008, U+000E to U+001B (ESC included); DEL U+007F; C1: U+0080 to U+0084, U+0086 to U+009F; every escape sequence of section 4.1. In all: 55 single characters | removed from the text itself, once, before anything else reads it; one space is left where a RUN stood with a word character on both sides | a reader does not see them; the checks must read what the reader reads; the space keeps promise 2 | cursor movement is not imitated (backspace overstrike, carriage-return overwrite, cursor and erase sequences). Honest data changes: nroff bold `N` + backspace + `N` becomes `NN`; a mis-decoded Windows-1252 byte such as U+0092 inside a word becomes a space; a stored raw model reply (k1b/loop.py:187) and model-written arguments lose these characters (promise 4) |
| space-like | U+000B, U+000C, U+001C to U+001F, U+0085, U+2028, U+2029 (9) | turned into one U+0020 in the text itself | D-018: white space is white space; all are `str.isspace()`; several are line breaks to some readers | a value with any white space inside it is masked only up to that white space, exactly as with a plain space today (CHANGELOG, "stated limits of redaction") |
| kept white space | tab U+0009, space, and the no-break and wide spaces | untouched | a tab-separated table must come out as it went in; round 7 turned a six-cell row into one placeholder when tabs were deleted | a key or value with a tab or a space inside it is not masked as one value |
| line end | U+000A, U+000D | untouched | lines stay lines | a key or value with a line break inside it is not masked as one value; **also a backslash directly before a line end** (a shell "line continuation"): kept as written, not masked across (moved to `tickets/PRH-b-line-continuation-matching.md`) |
| ignorable | every Default_Ignorable_Code_Point (4,174 code points in 17 ranges of the pinned table: zero-width characters, variation selectors, the combining grapheme joiner U+034F, the Hangul fillers, the tag characters, ...), plus the rest of category Cf that main already ignores | ignored for MATCHING only (the canonical reading drops them), kept in the output. Exception, unchanged from main: when a value is found only in a reading without them, that reading is what is returned for this one text (runmap.py:517-518) | deleting them from the text breaks Persian (zero-width non-joiner) and emoji sequences | a combining mark or a visible foreign letter inside a key (a reader sees it; look-alike work belongs to pull request 77) |

Further "not promised", each with its reason:
- **Mixed glue and cut inside one token:** `user` + ESC `[0m` + first half of a key + ESC `[0m` + second half. The joined reading is `user` + key with no boundary, which main does not mask as plain text either. Vendor keys glued to a word are a separate ledger row (D-018).
- **Fixed-length remainder:** when an escape sequence swallows letters that were part of a fixed-length value (a UUID, a card number), the rest no longer has the right length and stays visible. The swallowed letters are absent from the output.
- **A string sequence that never ends** (OSC, DCS, SOS, PM, APC without its terminator) blanks the rest of ITS LINE. Main today deletes all following lines too (2.3); PR H loses less.
- **Encoded forms of pattern-shaped secrets** (lead point 4): base64, hex and quoted-printable spellings of a key or `name=value` are not masked on main (RESULTS.md lines 153-155) and are not masked by PR H. Main promises base64, base32, hex and URL-quoting only for HANDED-OUT secrets on the tool path (CHANGELOG, "what the scrub undoes"); that stays.
- **Hidden items inside a base64, base32 or hex spelling of a handed-out secret** are not promised (percent, entity and backslash spellings ARE covered, promise 1).
- **An entity cut by a hidden item does not spell the character**: Python's entity decoder reads `&#6` without its semicolon as U+0006, so `&#6&#27;[0m5;KIA...` decodes to U+0006 + ESC `[0m5;KIA...`, which spells no key in any reading (`repro-protofixes.out`, row M2c, reported LEAKED by the check because the input's literal tail is the key's tail). Nothing is shown that a reader could decode into the key.
- **A decoded NUL leaves no glue space**: a NUL that only exists after decoding (`user%00AKIA...`) is deleted by `_views`' `_clean` (runmap.py:411, unchanged) with no space; a raw NUL is a removed item with the glue rule. Kept from main on purpose (the prototype's passing runs used main's `_views`); T1 pins main's verdict for it.
- **Log-line forging by a carriage return or line feed in a short message** (sweep F9) is not changed here (open question 3).
- **Text that holds too much work is refused, not shown** (D4, D5): more than 256 needed values in one reading raise `InputTooLarge`, as main's `_decoded_masks` does; a text whose readings cannot all be read within the 6-second budget raises `InputTooLarge`. Measured estimate for the worst shape W at the size cap: 4.21 s CPU (section 4.4), so a machine about 1.4 times slower than this one refuses it. Main shows both texts (with a leak). This is an availability change, stated in the CHANGELOG.
- **Dictionary keys of model-written arguments** (`redact_value`, runmap.py:593) lose control characters like the values (promise 4); a tool's argument schema may then reject the key. Stated in the CHANGELOG (readiness m5).
- **Two known values that overlap partially** come back as ONE new placeholder for the merged text (W0); a reader sees one placeholder where main showed one placeholder plus a readable piece.

**Number of passes** (a pass = all patterns over one reading of at most 262,144 characters). Main today: 1 for the text, plus up to 3 other readings (canonical; canonical with JSON escapes undone; all layers undone) when the text is non-ASCII or holds a backslash, `%` or `&`: at most 4 passes. After PR H:
- the text: **1** pass when the joined and spaced readings are equal (no run between two word characters: plain logs, tables, JSON, colour codes at word edges); **2** passes otherwise (find on the joined reading, then mask on the spaced reading);
- other readings: the same up to 3 as today, built from the escaped original text as today, plus the new decoded reading of W2 (only when the text or its plain decode holds a removed or space-like item, and it differs from the others). Rev 3 drops rev 2's "same up to 4 built from the escaped joined reading" (D4): the new decoded reading removes hidden items in every decoding round and covers the same cuts (author's checks: 0 verdict changes, `r3/check-diff.txt` and `r3/repro-diff.txt` are empty); each other reading costs 1 or 2 passes by the same rule;
- so at most 2 + 4 x 2 = **10** passes, reached only by text that has hidden items inside words AND an escape character (`\`, `%`, `&`) AND non-ASCII characters (shape W of 4.4). The 6-second budget check runs before every pass (the first one included), so one call overruns the budget by at most one pass. Main: at most 4 passes.
Author prototype, passes counted at the cap (rev 1, slow reader): plain ASCII 1, tab table 1, JSON 1, coloured output 1, colour change inside a word 2, Hindi 1, Persian 2 (main: 2).

## 4. Design

**Ladder line (R447, R448).** Rungs were tried in order for each component; the table says which rung holds. (1) no-code tool, MCP server, retrieval, model feature: none applies to cleaning a string inside the redactor (a model cannot be asked to find hidden characters reliably, and the text must be cleaned BEFORE any model sees it). (2) ready-made libraries: researched on PyPI on 2026-11-11 (rev 3, D7; PyPI was reachable, the standards hosts were not): results in the table. (3) redaction before the model is on the R448 list of guarantees that stay our code; what only our code gives is stated per row.

### RUNG TABLE (CODE-LAST v1)

| component | need | rung tried | evidence (source, date) | what only our code gives | verdict |
|---|---|---|---|---|---|
| escape-sequence reader | one reader with written rules for strings that never end, C0 inside a CSI, CAN/SUB, ESC inside a string | 3: strip-ansi 0.1.1 (2020-06-20, no licence in its metadata); pyte 0.8.2 (terminal emulator, LGPL-3.0); ansi2txt 0.2.0 (lists AGPL-3.0 and MIT); stransi 0.3.0 (MIT) | `r3/rung3-pypi-metadata.out`; `r3/rung3-compare.out`: strip-ansi agrees with the rev-3 grammar on 1 of 36 rows (it leaves C1 CSI, private CSI, C0 inside CSI, nF, Fp, strings with payloads); pyte imitates cursor movement, which this ticket deliberately does not promise (section 3), and its licence would need a decision; ansi2txt: licence unclear; stransi: NOT judged (author's adapter error) | fail-closed rules for unterminated strings (blank to the line end, never past it), CAN/SUB, one definition shared with `canonical` and the scrub; no new dependency on the redaction path | KEEP-CODE (leaf module, about 150 lines, standard library only) |
| ignorable table | Default_Ignorable_Code_Point | 3: `regex` 2026.9.29 (Apache-2.0 AND CNRI-Python) carries the property; perl 5.38.2 carries it | `r3/rung3-compare.out`: `regex` gives 4,174 code points, equal to the perl file; `r3/oracle-*.out`: the written rule over `unicodedata` gives the same on 3.12 and 3.13 | the data is 17 ranges; adding `regex` as a runtime dependency for 17 constants would need a kind and an alternative (no-single-dependency) | CUT-TO-CONFIG+GLUE: the 17 ranges are DATA (a pinned file plus a generated literal), checked against two independent sources; no code beyond one compiled character class |
| ignorable table, generator | turn perl's code points into the range file; print the literal | 2: a 40-line tool | W6 | - | KEEP-CODE, two modes only (`--from-codepoints`, default); `--from-ucd` dropped (no sample to test it, D9) |
| policy rung: refuse or replace instead of removing | promise 1 | 2 (design alternative) | refusing every text with a control character would refuse every coloured tool output (shape H1 of 4.4); replacing each hidden item with a visible mark (U+FFFD) keeps word boundaries but does not join a cut key (`AKIA` + U+FFFD + `IOSF...` still matches nothing; row L1) | finding on the joined reading needs removal | removal (this ticket) |
| "find joined, mask spaced" step | promises 1 and 2 together | 2: reuse `redact` with the run's map | author prototype rows of 8.2 and 8.6 | - | KEEP-CODE (about 40 lines in runmap.py) |
| W0 span rule for known values | promise 1 when two known values overlap | 2: extend the sweep (redact.py:1011-1049) and `_keep_earlier_masks` (runmap.py:455-461) | `r3/d2-overlap-main.out`: main leaks on partial overlap; the reference rule masks all 7 rows, restore exact | one rule for three call sites | KEEP-CODE (one helper, about 30 lines) |
| no created shapes, last forgery check | promise 3 | 2: reuse `_MARKER`, `PLACEHOLDER`, `canonical`, `escape_markers`, the look-alike spelling of `escape_placeholders` | absent on main (2.5) | - | KEEP-CODE (about 20 lines) |
| decoded reading with hidden items removed each round | promise 1 for encoded tokens (M2) | 2: a keyword on the existing `undo` | rows M2a, M2b (section 8.2) | - | KEEP-CODE (about 5 lines) |
| `_scrub` on the joined copy, output spaced | promise 1 and 2 for handed-out secrets | 2: the existing `_scrub_layers` called twice | `r3/d1-scrub-*.out` | - | KEEP-CODE (about 20 lines) |
| reference oracle (tests only) | an answer the implementation cannot influence | 3 for the ignorable part (`regex`: used once in the evidence, not as a test dependency, because acceptance 1 forbids a lock-file change); 2 for the reader | `r3/scripts/hidden_ref_oracle.py` | an independent second reading of the grammar | KEEP-CODE in tests (copied from the r3 script) |

**Single-dependency line.** Standard library only (`re`, `unicodedata`). No new package, no vendor. The one external input is Unicode data: the text file `tests/fixtures/default_ignorable_perl5382_unicode1500.txt` (W6), produced from perl 5.38.2's Unicode 15.0.0 tables and equal to the `regex` package's table and to the written rule. Licence: Unicode data files are under the Unicode License v3 (from memory, UNVERIFIED: unicode.org gave no answer, `r3/hosts-check.out`; question for the lead, rev 3 item 1). The file holds 17 lines of numbers produced by perl, not a copy of a Unicode file; the file is copied byte for byte (its SHA-256 is pinned, W6), so its existing header line stays as it is (`# Default_Ignorable_Code_Point, Unicode 15.0.0, from perl 5.38.2 (Unicode::UCD); one inclusive range per line, ascending`); the open licence check is written in the docstring of `tools/gen_default_ignorable.py` and in the CHANGELOG line. The build does not wait for the answer. Export path: the file is plain text. Alternative source, with its trigger: the `regex` package (already checked equal) if perl is unavailable; a `DerivedCoreProperties.txt` with a known SHA-256 when the lead supplies one (then the generator gains a reader for it in a separate change).

### 4.1 New leaf module `src/hadavin_sdk/guard/hidden.py`

Imports nothing from `hadavin_sdk` (standard library `re` and `unicodedata` only). Importing it loads `hadavin_sdk.guard`'s `__init__`, which imports `redact`, which imports `hidden`: no cycle, because `hidden` imports nothing back. Public names:
- `REMOVED_CHARS`, `SPACE_LIKE`: frozensets, exactly the single-character members of the contract table (55 and 9).
- `IGNORABLE_RANGES` (tuple of 17 inclusive pairs, generated), `UNICODE_DATA_VERSION = "15.0.0"`, `is_ignorable(ch) -> bool`, and `IGNORABLE_RE`: ONE compiled character class of the 17 ranges plus every Cf code point above U+007F (built once at import from `IGNORABLE_RANGES` and `unicodedata`). `canonical` removes ignorables with `IGNORABLE_RE.sub("", nfkc_text)`, not with a per-character Python test (rev 3, D3: measured 0.99x main on Hindi against 1.04x for the per-character test, `r3/cost-r3-main.out`). `is_ignorable(ch)` = `IGNORABLE_RE.match(ch) is not None`, for `_canonical_view` (which works per character anyway).
- `strip(text) -> tuple[str, str]`: the joined reading and the spaced reading (the same object twice when they are equal). One left-to-right pass, linear, no backtracking. Fast path: `_ANY = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u2028\u2029]")`; when `_ANY.search(text)` is None the text is returned untouched twice (ignorables are not handled by `strip`; tab, line feed and carriage return are not members).
- `strip_sequences(text) -> str`: the same reader, but only SEQUENCE items are removed: an item that starts with ESC or with a C1 opener (U+009B, U+009D, U+0090, U+0098, U+009E, U+009F), i.e. every row of the grammar table whose "Opens with" column is filled, plus the lone ESC row. Every other removed or space-like character stays as written (a stray U+009C, BEL, NUL, U+0085 stay). The glue rule applies to runs of sequence items. Used by `strip_ansi`. Changes against main, stated in the CHANGELOG: a lone ESC and a lone U+009B are now removed by `strip_ansi` (main left them, 2.3); the families main missed are removed. Oracle: `readings(text, sequences_only=True)[1]` of the reference oracle (M2).
- Every public function is idempotent: applying it to its own output changes nothing (T10 checks `strip` and `strip_sequences`).

**Glue rule, per run** (design M3). Examples, each checked with the prototype (`repro-protofixes.out`, lines "M3 strip table") and, in rev 3, with the reference oracle (`r3/oracle-*.out`, lines starting `glue PASS`):

| Input (Python) | joined reading | spaced reading | Why |
|---|---|---|---|
| `"ab" + BEL + "cd"` | `abcd` | `ab cd` | a run between two word characters |
| `"ab" + BEL + BEL + "cd"` | `abcd` | `ab cd` | one run of two items: one space, not two, not none |
| `"ab" + ESC + "[0m" + ESC + "[1m" + "cd"` | `abcd` | `ab cd` | two sequences with nothing between them are one run |
| `"ab" + BEL + "\u200b" + BEL + "cd"` | `ab\u200bcd` | `ab\u200bcd` | the ignorable splits the stretch into two runs; neither has a word character on both sides; the zero-width space itself is already a boundary for the patterns |
| `"ab" + BEL + "-cd"` | `ab-cd` | `ab-cd` | `-` is not a word character |
| `"ab" + BEL + " cd"` | `ab cd` | `ab cd` | a space after the run |
| `"ab" + "\x0c" + BEL + "cd"` | `ab cd` | `ab cd` | the form feed becomes a space; the run (BEL) then sits between a space and `c` |
| `"ab" + NUL + "cd"` | `abcd` | `ab cd` | NUL is a removed item like the others |
| `ESC + "[0mab"` | `ab` | `ab` | a run at the start has no left neighbour |
| `"ab\\" + "\n" + "cd"` | unchanged | unchanged | a backslash and a line end are kept (out of scope) |

**The ONE escape-sequence reader (rev 3: complete state table, M2).** A left-to-right state machine; it never looks more than ONE character ahead, so it is linear (no scanning ahead for a terminator). "Read afresh" means: the item ends BEFORE this character, and this character is then read in state GROUND. Names are explained in section 1; byte ranges are code points. Reference implementation: `r3/scripts/hidden_ref_oracle.py` (38 grammar rows and 10 glue rows, all PASS on Python 3.13.18 and 3.12.3, linear: 4x the text costs 3.4 to 4.3x the time; `r3/oracle-*.out`).

| State | Next character | Action | Next state |
|---|---|---|---|
| GROUND | ESC U+001B | start an item | ESC |
| GROUND | U+009B (C1 CSI) | start an item | CSI |
| GROUND | U+009D (OSC), U+0090 (DCS), U+0098 (SOS), U+009E (PM), U+009F (APC) | start an item; remember "OSC" or "other string" | STRING |
| GROUND | any other member of "removed" (including a stray U+009C) | one removed item | GROUND |
| GROUND | a member of "space-like" | one space-like item | GROUND |
| GROUND | anything else (letters, tab, line end, ignorables) | kept | GROUND |
| ESC | `[` | - | CSI |
| ESC | `]` (OSC); `P` (DCS), `X` (SOS), `^` (PM), `_` (APC) | - | STRING |
| ESC | 0x20-0x2F (nF intermediate) | - | ESC-INTER |
| ESC | any other 0x30-0x7E (Fp, Fe, Fs; also a stray ESC backslash) | the item is ESC plus this character, removed | GROUND |
| ESC | anything else (another ESC, a control, DEL, a line end, a non-ASCII character) or the end of the text | the item is the lone ESC, removed; this character is read afresh | GROUND |
| ESC-INTER | 0x20-0x2F | - | ESC-INTER |
| ESC-INTER | 0x30-0x7E (final) | the item is ESC + intermediates + final, removed | GROUND |
| ESC-INTER | anything else, or the end of the text | only the ESC is removed; the intermediates are read afresh as ordinary text | GROUND |
| CSI | 0x20-0x3F (parameter and intermediate, any order) | - | CSI |
| CSI | 0x40-0x7E (final) | the whole item removed | GROUND |
| CSI | CAN U+0018 or SUB U+001A | the item so far AND the CAN/SUB removed | GROUND |
| CSI | U+0000-U+0009, U+000B, U+000C, U+000E-U+0017, U+0019, U+001C-U+001F, U+007F | dropped (part of the item), the sequence continues | CSI |
| CSI | anything else (line end, ESC, a C1 character, a character above U+007F) or the end of the text | the item so far removed; this character is read afresh | GROUND |
| STRING | ST = U+009C, or ESC directly followed by backslash | the item including the terminator removed | GROUND |
| STRING (OSC only) | BEL U+0007 | the item including BEL removed | GROUND |
| STRING | CAN or SUB | the item including CAN/SUB removed | GROUND |
| STRING | ESC NOT followed by backslash (another sequence starts), or a line end U+000A / U+000D | the item so far removed; this character is read afresh (so the line end is KEPT, and ESC `[0m` after an unended OSC is read as a CSI) | GROUND |
| STRING | the end of the text | the item so far removed | - |
| STRING | anything else (letters, BEL in DCS/SOS/PM/APC, C1 openers, other controls) | part of the payload | STRING |

So a string sequence's body never contains a line end: it ends at whichever comes first of its terminator, an ESC that is not ST, the line end, or the end of the text. An unterminated opener repeated n times costs O(n) (measured, `r3/oracle-python.out`, row `linear '\x1b]'`).

Classification for the glue rule and for `strip_sequences`: every item started in GROUND by ESC or a C1 opener is a SEQUENCE item; every other removed character is a SINGLE item. A *run* is a longest stretch of removed items (either kind) with nothing else between them.

Not read as sequences, on purpose: an escape written out as text (backslash-x-1-b, `%1b`). Those are undone by the existing layer decoding (`runmap.undo`), and every decoded reading goes through `strip` (W2), which is what fixes L11 and F1e; the new decoded reading of W2 fixes M2a and M2b.

### 4.2 Work items, file by file (line numbers on main)

**W0 (new in rev 3, D2) `guard/redact.py` and `guard/runmap.py`: one span rule for putting known values back.** Bug class: overlapping known values are replaced one after another, so the first replacement breaks the second value and a piece of it stays readable. Main has it in the redactor's own sweep (redact.py:1011-1049, longest first, one `replace` after another) and in `_keep_earlier_masks` (runmap.py:455-461, list order); `r3/d2-overlap-main.out` shows main leaking a 4-character piece on partial overlap in both places, and through `redact_text` / `redact_untrusted` with the run's map. Rev 2's longest-first sort fixed only the nested case.
- New helper in redact.py, `mask_spans(text, spans, mapping) -> str`, where `spans` are `(start, end, placeholder)` found on `text` as it stands. Rule: (1) sort by start, longer first at equal start; (2) drop every span that lies inside another kept span (nested values: the longer one wins, as main's sweep intends); (3) a chain of spans that partially overlap (each starts before the previous one ends) is ONE merged span; (4) a merged span of one span gets that span's placeholder; a merged span of two or more gets ONE placeholder issued for the merged text through the redactor's own numbering (`_Redactor._place`, kind = the kind of the longest member, leftmost on a tie), or the existing placeholder when the map already holds that exact text. So `restore` gives back exactly the merged text (the reference rule restores exactly in all 7 probe rows).
- Callers: the sweep (spans of every present value on the ORIGINAL segment: every copy for `_EVERY_COPY` values, standalone copies only for the others, judged on the original segment, not on a partly replaced one); `_keep_earlier_masks(view, pairs, mapping)` (spans of every pair's spelling; a merged placeholder is issued into the mapping passed in, which is the copy `_redact_stripped` then uses, so a view that needed a merged placeholder replaces the output by the existing rule at runmap.py:517-518); `_redact_stripped` step 5 (spans of the gap patterns).
- This replaces rev 2's `sorted(pairs, key=lambda p: -len(p[1]))`. It is the fix for case 790 AND for the root condition named in PR H-c (fragment values inside other values): with W0, a fragment entry can no longer cut a longer value, so PR H-c becomes map hygiene only, not a prerequisite of any promise (stub updated).
- Commit 1 of the branch (WP0), on main's behaviour only, before any hidden-item work: it fixes a leak of main by itself.

**W1 `guard/redact.py`.** `_ANSI` (:820-822) is deleted; `strip_ansi` (:825-838) keeps its name, its signature and its glue rule and becomes `return hidden.strip_sequences(text)`. Its three call sites stay as they are (:877, :920, :1254). The call in `find` (:920) is NOT removed: after W2 no escape sequence reaches `find` from the choke point (T7 proves it with stand-ins on `runmap.redact` AND on `_Redactor.find`), while direct callers of `redact()`, `redact_many()` and `sweep()` keep today's behaviour, and a stored map from an older run may still hold an original with ESC in it. Improve, do not replace. So the claim is "one reader, used by the choke point, the scrub and `strip_ansi`", not "one call".

**W2 `guard/runmap.py`.**
- `canonical` (:276-282) and `_canonical_view` (:285-295): the test `category != "Cf"` becomes `not hidden.is_ignorable(c)`. Nothing else changes in them; `replace_canonical` (:298-320) is reused as it is. Ripple, intended and tested: `nfkc` (:103-109) calls `canonical`, and `nfkc` runs inside every round of `undo` (:141), so the scrub of handed-out secrets (`tools._decoded`), the decoded readings (`_views` :410) and `_decoded_masks` now drop every ignorable, not only Cf; the grounding check (evidence.py:57, :87, :88, :151) changes as stated in promise 5 (test T11).
- New `_repair(text)` next to `_clean`: lone surrogates only (`text.encode("utf-8", "replace").decode("utf-8", "replace")`). `_clean` stays for :411 and :519.
- `undo(text, clean=False, strip_hidden=False)`: new keyword. With `strip_hidden=True`, each round ends with `step = _no_created_shapes(step, hidden.strip(step)[0])` after the five decoders (the created-shape rule must run INSIDE the round: without it, `"<%1b[0m" + "IPV4_2>"` (F1e) still forged a placeholder on `safe_head` and plain `redact_text` in the author's first rev-2 run: lines `F1e | safe_head | forged placeholder: True` and `F1e | redact_text(...) | forged placeholder: True`; that output file was overwritten by the rerun, a slip of the author, so the two lines are quoted here; with the rule, both `False`, `cost-protofixes.out`). Default False keeps every existing caller unchanged.
- `_views` (:401-415): one more reading, `fits_after_nfkc(undo(text, strip_hidden=True))`, appended (after `_clean`, like the others) ONLY when the text holds `\`, `%` or `&` AND either the text or `undo(text)` (which `_views` already computes, :410) holds a member of "removed" or "space-like" (`hidden.ANY.search`), and it differs from the readings already in the list. Reason (D3, the reviewer's "hidden extra undo"): a decoder never removes a control character, so when neither holds one, the stripped decode equals the plain one and is not computed; a JSON, URL or HTML log with no hidden item pays no second decode (gate G2 of 4.4 counts `undo` calls). `_views`' own `_clean` stays (a decoded NUL is deleted with no space, as on main; "not promised" list).
- `_keep_earlier_masks(view, pairs, mapping)` (:455-461): the W0 span rule over every occurrence of every pair's spelling (replaces rev 2's longest-first sort; D2). A merged placeholder is issued into `mapping`. This is a change at the choke point for every list of pairs, on main's own pairs as well as the new ones.
- `redact_text` (:486-526), new order, as pseudo-code (names of existing helpers as on main):

```
_within_cap(text)                                   # :486, unchanged
started = monotonic(); cache = getattr(mapping, "redact_cache", None)               # as main :495
text = fits_after_nfkc(_repair(text))               # NUL is no longer deleted here: it is a removed item
joined, spaced = hidden.strip(text)                 # no removed/space-like item: (text, text), the same object
if joined is not text:
    joined, spaced = _no_created_shapes(text, joined), _no_created_shapes(text, spaced)
esc = (lambda t: fits_after_nfkc(neutralise(t))) if neutralise else (lambda t: t)
e_text = esc(text)                                  # the escaped ORIGINAL, as main :489-490
e_joined = e_text if joined is text else esc(joined)                                # no second escaping of hidden-free text
e_spaced = e_joined if spaced is joined else esc(spaced)
check_budget(started)                               # before the first pass too (m2)
out, current = _redact_stripped(e_joined, e_spaced, dict(mapping), cache, started)  # 1 or 2 passes
scan = (not e_text.isascii()) or any(c in e_text for c in "\\%&")
readings = _views(e_text) if scan else []           # rev 3: views of the escaped ORIGINAL only (D4)
readings = [v for v in readings if v not in (e_joined, e_spaced)]
pairs = []
if readings:
    for base in dict.fromkeys((e_spaced, e_joined)):                                # each base once
        pairs += [p for p in _decoded_masks(current, base) if p not in pairs]
if neutralise: pairs += [(ph, n) for ph, d in pairs if (n := esc(d)) != d and len(n) >= 4 and (ph, n) not in pairs]   # as main :498-505
pairs += [(ph, sj) for ph, d in pairs if (sj := hidden.strip(d)[0]) != d and len(sj) >= 4 and (ph, sj) not in pairs]
for view in readings:
    check_budget(started)
    j, s = hidden.strip(view)
    if j is not view: j, s = _no_created_shapes(view, j), _no_created_shapes(view, s)
    work = dict(current)                                                            # merged placeholders (W0) go here
    j = _keep_earlier_masks(esc(j), pairs, work)
    s = j if s is j else _keep_earlier_masks(esc(s), pairs, work)
    vt, vm = _redact_stripped(j, s, work, cache, started)
    if vm != current or _held(vt) > _held(out): out, current = vt, vm               # :517-518, unchanged
out = _clean(out)                                                                   # :519, unchanged
if neutralise is neutralise_untrusted: _refuse_forgery(out, current)
mapping.clear(); mapping.update(current)                                            # :524-525, unchanged
```
`check_budget(started)` raises `InputTooLarge` when `monotonic() - started > defaults.REDACT_BUDGET_S` (main's test at :496 and :508, now also before the first pass and before step 6 of every `_redact_stripped`).
  The error handling around it (:521-523) is unchanged. `fits_after_nfkc` sits where main has it (after the repair, after every escaping). No extra cap check is needed on the joined and spaced readings: neither is longer than the text (a run becomes at most one space; a space-like item becomes one space).
- New helper `_no_created_shapes(before, after) -> str`: when `after == before` it returns at once (nothing was removed, so nothing can be created; this also keeps it from doing an NFKC of the whole text before the size checks: the author's first rev-2 run broke three cap tests exactly that way, section 8.3). Otherwise it works on `fits_after_nfkc` of both texts: for every genuine-shaped placeholder string (`PLACEHOLDER` regex) that occurs more often in `after` than in `before`, every occurrence of it in `after` is written as `‹NAME_N›` (U+2039, U+203A: the spelling `escape_placeholders` writes); if `_MARKER` matches `canonical(after)` more often than `canonical(before)`, `after = escape_markers(after)`. Counting, not positions (no position map; section 4.3). Cost: two `findall` over the reading. Consequence, stated: when a text holds the same placeholder both plainly AND forged by a hidden item, both are written in the escaped form (fail to the escaped spelling). For model-written text this means the value is not restored for that one placeholder (the executor gets the look-alike), which a grounding or validation step then refuses.
- New helper `_redact_stripped(joined, spaced, mapping, cache, started) -> (text, mapping)`, which calls the module-level name `redact` (fact 17):
  1. `joined == spaced`: one `redact(spaced)`. Done.
  2. Otherwise `found = redact(joined)` (the find pass). Take the placeholders that stand in `found.text` and are in `found.mapping` ("held").
  3. Of these, the "needed" ones are those whose value does NOT occur as written in `spaced` and is not a seed entry (`"\0seed"` original, the card's numbering seeds). A value that occurs as written is masked by the sweep of known values in step 6.
  4. More than `MAX_DECODED_MASKS` (256, runmap.py:423) needed values: raise `InputTooLarge` (nothing shown), exactly as `_decoded_masks` does (runmap.py:441-442). Never skipped, never the joined result.
  5. Build one gap pattern per needed value: the escaped characters of the value, with ` ?` (one optional space) inserted ONLY between two neighbouring characters that are both word characters (letter, digit, underscore), because the glue rule only ever leaves a space there (D6). A value of fewer than 4 characters gets `(?<!\w)` before and `(?!\w)` after (the sweep's length rule: 4 or more anywhere, 3 only as a whole word). Every match of every pattern on `spaced` is a span; the W0 span rule replaces them in one pass (no longest-first loop). Linear: an optional space never competes with a character of the value (a space of the value is matched literally and gets no ` ?` next to it), so at each position there is at most one way to continue; T9 has a shape for it.
  6. Budget check, then `out = redact(that text, mapping=found.mapping)` (the mask pass). If any held placeholder (or the merged placeholder that replaced it under W0) is missing from `out.text`, raise `RedactionError("held value lost")`: nothing is shown (rev 3, D1: rev 2 returned the joined result here, which gave up promise 2). Measured reachability with the author's prototype: 0 firings over the author's check rows, the reproduction rows and the 43 redaction test files (`r3/step6-count.txt`, section 8.6). Mutant 23 and its killer: section 5.2. Else return `out`.
- `_refuse_forgery(out, mapping)`, called from `redact_text` only when the escaping step is `neutralise_untrusted`: if `_MARKER` matches `out` or `canonical(out)`, or a genuine-shaped placeholder in either is not a key of the map, raise `RedactionError` (the callers already turn that into a fixed note or an abstention). A backstop; in rev 1 and rev 2 prototype runs it never fired.
- `safe_head` (:532-541): no edit. It reaches all of the above through `redact_bounded` -> `redact_text`. T1 runs every row on `safe_head`.

**W3 `tools.py`.**
- `_sanitise` (:730-732): repairs lone surrogates only; NUL is left for the choke point, which removes it with the glue rule. One rule for NUL instead of two. Its second call site, tools.py:1194, feeds the digest at :1197: `ToolOutput.sha256` is then the SHA-256 of the tool's text with NUL kept, instead of with U+FFFD. Decision: accepted. Reason: the digest is recorded with the call (agent_loop.py:536 `output_sha256`) and, by grep, never recomputed and compared later; the new value is the hash of what the tool really returned. Test T12 pins it; the CHANGELOG says it ("the recorded digest of a tool result that contains NUL changes").
- `_scrub` (:898-904), rev 3 (D1): `joined, spaced = hidden.strip(raw)`. (a) `joined is raw` (no hidden item): the existing body on `raw`, unchanged from main. (b) Otherwise the existing body (`_scrub_layers`) runs on `joined` to FIND; when its result equals `joined` (no handed-out secret), return `raw` untouched, so the choke point still sees the hidden items and keeps boundaries. (c) When it found one: replace, in `spaced`, every spelling of every handed-out secret (`_secret_forms`) by `MARKER` with the step-5 gap pattern, then run the existing body on that text and return its result: hidden items are gone, but where they stood between two word characters a space remains, so a key glued by a hidden item stays separated (promise 2; rows D1a, D1b: `r3/d1-scrub-rev3.out` MASKED where the rev-2 prototype LEAKED, `r3/d1-scrub-proto.out`). (d) Backstop: if any spelling of a handed-out secret still stands in `hidden.strip(result)[0]` or in `_decoded` of it, return `MARKER + TRUNCATED` (the whole result withheld, as main does for `TooDeep`), never the joined text. `TooDeep` handling unchanged.
- `_decoded` (:726-727): `hidden.strip(undo(text, strip_hidden=True))[0]`, so a handed-out secret cut by a percent-encoded escape, or by an escape that cuts a percent token, is found.
- `_first_decoded` (:786-791): EDITED (rev 3, M1: main's version calls `_decoded(char)[:1]`, and W3 changes `_decoded`, so "no change" would have made it use the stripped decode). New body: `return runmap.undo(char)[:1]` inside the existing `try/except runmap.RedactionError: return char`. Reason: with the stripped decode, a control character reads as `""`, and `"" in "&\\%"` is True, so the skip guard at :867 stops skipping and every such position costs one `_decoded_clean` over the tail. Reproduced with the prototype (`repro-proto.out`: `_first_decoded '\x07' -> ''`, skip guard does not skip; the prototype rebinds it exactly this way, `scripts/fixes.py` line 80: `-> '\x07'`, skips). `_decoded_clean` (:794): no change (the fragment scan of a cut tail stays on the plain decode; the choke point strips the result afterwards anyway).
- `prepare_output`, `error_reason`, `redact_layered`: no edit (they call the above).

**W4 the approval gate.** NO edit of `approvals/gate.py`, `approvals/channel.py`, `approvals/slack_channel.py`. The gate keeps its own set and its own readings. T8 asserts that the gate's set contains every member of `hidden.REMOVED_CHARS` and of `hidden.SPACE_LIKE` except U+2028 and U+2029 (which the gate does not hold today; reported, not changed). Two behaviours of the card do change without a gate edit, both stated in the CHANGELOG and tested (T8): (1) through the gate's import of `strip_ansi`, the gate recognises the families of 4.1 that main's pattern missed; the payloads of DCS, SOS, PM and APC strings are now deleted instead of shown, so the approver sees less than the sender wrote (what a terminal also hides); (2) through `redact_text`, a placeholder forged by a hidden item on the card is written in the escaped look-alike form (M5a: `‹IPV4_1› and <IPV4_1>`). If any test in `tests/warden_port/test_gate*.py` changes its result, the builder stops and reports to the lead instead of editing a gate test (open question 2).

**W5** (map clean-up): removed from PR H; see `tickets/PRH-c-map-entries-hygiene.md`.

**W6 data and generator.** The committed file is `tests/fixtures/default_ignorable_perl5382_unicode1500.txt`, copied BYTE FOR BYTE (`cp`) from `handover/evidence/PRH-plan/default_ignorable_perl5382_unicode1500.txt`: one header comment line, then 17 inclusive ranges `XXXX..YYYY` (upper-case hex, at least four digits), ascending, a final line feed; SHA-256 `b14f5d758ff48a8c5e5c92e45d6aa48856db50d732103077435fa4a40aa457f6` (recomputed in rev 3 with `sha256sum`, same value). The builder needs no perl. `tools/gen_default_ignorable.py` has TWO modes (rev 3 drops `--from-ucd`, D9 and readiness m3): `--from-codepoints` reads decimal code points on standard input (the output of `perl -e 'for my $c (0..0x10FFFF){ next if $c>=0xD800 && $c<=0xDFFF; print "$c\n" if chr($c) =~ /\p{Default_Ignorable_Code_Point}/ }'`), merges adjacent code points into ranges and writes the range file; with no option it reads the range file and prints the `IGNORABLE_RANGES` literal. Its docstring says the Unicode licence check is open (questions-for-lead, PR H rev 3 item 1). Tests (`tests/test_prh_hidden_unit.py`): the literal equals the file; the file's SHA-256 equals the constant `RANGE_FILE_SHA256` (that name: a 64-hex value next to a name with key, token or secret in it IS flagged by gitleaks' `generic-api-key` rule, `r3/m8-gitleaks.out`); NOT in `reference_material_sha256.txt` (fact 19). Unicode version gate (D9): when `unicodedata.unidata_version` is 15.0.0 or 15.1.0 the oracle's derived set must EQUAL the file; on any other version the test checks that every pinned code point is still derived (superset) and prints the new ones, and it FAILS instead when `HADAVIN_REQUIRE_PINNED_UNIDATA=1` (the variable CI already sets, ci.yml:91). The project supports Python 3.12 and later (`requires-python = ">=3.12"`); CI runs 3.13 and 3.12. If the builder regenerates the file and gets a different hash, the builder stops and reports to the lead.

**W7 documents.** CHANGELOG "Unreleased" (rules in section 6), SECURITY.md where it lists redaction limits, the docstrings of `redact_text`, `canonical`, `undo`, `prepare_output`, `_sanitise`, `strip_ansi`, `_keep_earlier_masks`. `guard/producers.py`: no edit.

### 4.3 NOT to build (each belongs elsewhere or failed before)

- Rewriting patterns to tolerate hidden items; any use of the private modules of Python's regular-expression library (`re._parser`, `re._compiler`).
- A stand-in character for a gap; private sentinel characters that carry placeholders.
- One table shared with the approval gate; any edit of gate logic or of channel.py / slack_channel.py.
- A reading with tabs deleted, for any kind.
- Matching across a backslash and a line end (PR H-b).
- Dropping map entries (PR H-c).
- Any look-alike (confusables) work, mark-on-ASCII rules, wide-dot mapping: pull request 77.
- A terminal emulator (cursor movement, overstrike, erase).
- A position map between readings (the gap pattern of `_redact_stripped` step 5 and the counting rule of `_no_created_shapes` replace it).
- Per-line withholding on a spent time budget.
- A general "which reading wins" rule for the decoded readings (design M6 of round 7): separate ledger row.
- Changing the judge, the vendor screen or `safe_head` to the untrusted variant (open question 1). Collapsing line ends in `safe_head` (open question 3).
- Base64, hex or quoted-printable decoding for pattern-shaped secrets.

### 4.4 Cost: bound, measurement and gates (rev 3: D3, D4, M5)

**Bound.** `strip` is one pass and returns at once on text with no removed or space-like item (one compiled search); at most 10 passes (section 3); the span rule is one pass over the matches; the 6-second budget stays the hard wall and is checked before every pass.

**Shapes** (each is ONE line repeated to the size by `(line * (n // len(line) + 1))[:n]`; the exact lines are in `r3/scripts/cost_r3.py`, dictionary `SHAPES`, and T9 copies them):
- hidden-free (the ratio gate): **S1** plain ASCII log line; **S2** tab-separated table row; **S3** JSON line; **S4** Hindi sentence; **S5** Persian sentence with a zero-width non-joiner, an emoji with U+FE0F and a joiner sequence;
- with hidden items (time limit only): **H1** coloured test output (four colour codes per line, at word edges); **H2** a colour change inside a word; **W** the worst shape: Persian + a colour change inside a word + `50%25` on every line (reaches the 10-pass bound).

**Measured in rev 3** (`r3/cost-r3-main.out`; main 2a8c2aac, Python 3.13.18; CPU by `time.process_time`, median of 5; main and each variant interleaved in ONE process; load average 4.6 to 5.7 with all three heavy slots busy). "rev-3 estimate" = main with `canonical` using the one compiled class of 4.1, plus the measured cost of rev 3's added checks on hidden-free text (`ANY.search` on the text and, as an upper bound, on a full `undo(text)`). It is composed from measured parts, not a run of the built design.

| Shape | chars | main CPU s | rev-2 per-character `canonical` | rev-3 compiled class | rev-3 estimate | estimate / main |
|---|---|---|---|---|---|---|
| S1 plain ASCII | 262,144 | 0.393 | 0.395 | 0.392 | 0.393 | 1.00 |
| S2 tab table | 262,144 | 0.403 | 0.406 | 0.404 | 0.405 | 1.01 |
| S3 JSON | 262,144 | 0.392 | 0.397 | 0.392 | 0.393 | 1.00 |
| S4 Hindi | 262,144 | 0.786 | 0.814 | 0.741 | 0.782 | 0.99 |
| S5 Persian | 262,144 | 1.417 | 1.438 | 1.313 | 1.446 | 1.02 |
| S1 to S5 | 65,536 | 0.098 to 0.341 | | | | 0.88 to 1.04 |

Reading: the rev-2 Hindi figure of 1.59 times main came from the prototype's slow per-character reader (rev-2 text, 4.4), NOT from `canonical`: the per-character rule costs 1.04 times main on Hindi and the compiled class 0.94 times (0.741 / 0.786). The added checks cost 0.0007 s on S1 to S3 and at most 0.13 s on S5 (a full second `undo`, which rev 3 does not compute: `_views` reuses its own). H1: 0.24 s, H2: 0.32 s on main; rev 3 adds one pass for H2 (estimate under 0.7 s).

**Worst case W (D4)**, same file: one pass 0.410 s, the views 0.118 s, main end-to-end 1.566 s. Rev-2 bound (18 passes, two view sets): 7.61 s, over the budget, so refused above about 206,700 characters. Rev-3 bound (10 passes, one view set): **4.21 s**, under the 6-second budget at the cap on this machine under this load; a machine about 1.4 times slower refuses it (section 3, "not promised").

**Gates** (what the build must show; who checks it):
- **G1, pass count (test assertion, T9):** for S1 to S5 at the cap, the branch makes exactly as many `redact` calls per `redact_text` call as main does (counting stand-in on `runmap.redact`; main's counts recorded in `prh_main_corpus.json` by `record_prh_main.py`). H2: main's count plus at most 1 per reading. W: at most 10.
- **G2, no extra decode (test assertion, T9):** for S1 to S5, the branch makes exactly as many `runmap.undo` calls as main (counting stand-in).
- **G3, seconds and growth (test assertion, T9, `perf` marker):** every S and H shape at the cap under 3.0 s CPU (`time.process_time`, median of 5); W finishes OR raises `InputTooLarge`, never running past the budget by more than one pass; growth by `tests/fixtures/timing.py` `is_superlinear(measure, line, 65_536, 262_144)` is False (the rule on main: `PER_SIZE = 3.0`, so 4 times the text may cost at most 12 times the time; rev 2 wrongly wrote "2.5 times for doubling").
- **G4, ratio to main (evidence only, acceptance 9):** S1 to S5 at the cap, branch median CPU at most **1.25** times main's, both measured in ONE process with the same file (`python tests/test_prh_perf.py --compare-main PATH` runs two child processes alternately, five times each: one with `PYTHONPATH=PATH/src` (main), one with the branch; it prints both medians per shape). The limit stays 1.25 although the estimate is 1.00 to 1.04: the estimate is composed, and 1.25 leaves room for the real `strip` and `_no_created_shapes` identity checks without hiding a slow reader.
- **Remedy when a gate fails:** G1 or G2 fail = a design error: the builder stops and reports to the lead (never edits the gate). G3 or G4 fail = the builder profiles the failing shape (`python -m cProfile -s cumtime`, top 15 lines saved to the checkpoint note), fixes the hot spot inside the design (for example a per-character loop where a compiled class fits), and re-measures once; a second failure goes to the lead with the profile. The limits are never raised by the builder.

## 5. Test design

Files and what each holds (M4). Every test that must FAIL on main has a name starting `test_mf_` (or a parameter id starting `mf_`); every other test in these files must PASS on main, except the file `tests/test_prh_hidden_unit.py`, which needs the new module and is not run on main ("no old behaviour").

| File | Tests (T-id) | Function names (prefix) |
|---|---|---|
| `tests/hidden_oracle.py` (not collected) | the oracle, copied from `handover/evidence/PRH-plan/r3/scripts/hidden_ref_oracle.py` (docstring adapted; the self-check `main()` dropped) | - |
| `tests/test_prh_hidden_unit.py` | T10, the W6 table and hash tests, the T8 set test | `test_grammar_row[<row name>]`, `test_glue_row[<input>]`, `test_random_equals_oracle`, `test_strip_sequences_equals_oracle`, `test_idempotent`, `test_classes_exact`, `test_ignorable_equals_file_and_rule`, `test_range_file_hash`, `test_oracle_imports_nothing`, `test_gate_set_holds_removed_and_space_like` |
| `tests/test_prh_spans.py` | T4 (W0) | `test_mf_sweep_partial_overlap`, `test_mf_keep_earlier_masks_partial_overlap`, `test_mf_span_rule_generator`, `test_nested_restore_exact`, `test_mf_merged_entry_reused`, `test_case_790_regression` |
| `tests/test_prh_contract.py` | T1, T3, the `_redact_stripped` and `_refuse_forgery` unit tests | `test_mf_masked_singles`, `test_mf_masked_pairs`, `test_no_step_back`, `test_not_promised_counts`, `test_mf_forgery_untrusted[<id>]`, `test_mf_no_created_shapes[<id>-<path>]`, `test_step6_refuses`, `test_needed_count_only`, `test_over_256_needed_refuses`, `test_short_value_whole_word_only`, `test_gap_only_between_word_chars`, `test_refuse_forgery_reads_canonical`, `test_refuse_forgery_called` |
| `tests/test_prh_regressions.py` + `tests/fixtures/prh_regressions.json` | T5 | `test_regression_row[<id>]` (id `mf_<row>` for rows that fail on main) |
| `tests/test_prh_clean_corpus.py` | T6 | `test_corpus_item[<name>]` (`mf_` for colour-inside-a-word, C1 inside a word, nroff overstrike) |
| `tests/test_prh_grounding.py` | T11 | `test_mf_grounding_refuses[<cp>]`, `test_mf_contains_finds[<cp>]`; the zero-width space rows without `mf_` |
| `tests/test_prh_tools.py` | T2, T12, the D1 rows | `test_mf_handed_out_cut[<item>-<offset>]`, `test_mf_handed_out_encoded_cut`, `test_scrub_keeps_boundary[D1a]`, `test_mf_scrub_cut_and_boundary[D1b]`, `test_scrub_backstop_withholds`, `test_first_decoded_plain`, `test_bells_tail_cost`, `test_mf_digest_keeps_nul`, `test_mf_l8_through_runner` |
| `tests/test_prh_wiring.py` | T7, T8 card tests | `test_no_hidden_item_reaches_redact`, `test_no_hidden_item_reaches_find`, `test_mf_card_dcs_payload_deleted`, `test_mf_card_m5a` |
| `tests/test_prh_perf.py` (marker `perf`) | T9, gates G1-G3; `__main__` for acceptance 9 | `test_pass_count[<shape>]`, `test_undo_count[<shape>]`, `test_seconds[<shape>]`, `test_linear[<shape>]`, `test_worst_w`, `test_over_256_cut_values`, `test_spaced_value_long_spaces` |
| `tests/prh_mutants.py` (not collected) | section 5.2 | runner, same shape as `tests/migration_numbers_mutants.py` |
| `tests/record_prh_main.py` (not collected) | 5.1 | - |
| fixtures | `prh_regressions.json`, `prh_main_verdicts.json`, `prh_main_corpus.json`, `default_ignorable_perl5382_unicode1500.txt` | - |

**The oracle shares no code with the implementation except the redactor's patterns.** `tests/hidden_oracle.py` imports nothing from `hadavin_sdk`. It holds: (a) a hand-written state machine for section 4.1 with named states (ground, escape, escape-intermediate, csi, string), rev 3: the author's reference `r3/scripts/hidden_ref_oracle.py` (written from the 4.1 state table, never from `hidden.py`; 48 rows PASS on 3.13.18 and 3.12.3); a test asserts the file has no `import hadavin_sdk`, no `from hadavin_sdk` and no `import re`; (b) the class sets typed out again as code-point lists; (c) the ignorable set read from the pinned file, AND a second, independent derivation: the rule written out in section 1 over `unicodedata` categories; the test asserts file, rule and `hidden.IGNORABLE_RANGES` are equal over all 1,114,112 code points, with the Unicode version gate of W6 (both checked equal on 2026-11-11, `r3/oracle-*.out`); (d) `joined(text)` and `spaced(text)` with the run rule. The expected class "masked" (T1) is computed IN THE TEST FILE (not in the oracle) by running the package's own `redact()` on the oracle's joined reading: the oracle shares the redactor's patterns, nothing else (readiness m4). `tests/record_prh_main.py` imports the oracle but never `hadavin_sdk.guard.hidden`, which main lacks.

**T1 generator** (`test_prh_contract.py`), run on main (for the fixtures) and on the branch:
- kinds (9): vendor-prefix key, three-part signed token, UUID, `name=value` password, `Bearer` token, e-mail address, command flag (`-p` value), a PEM block, a handed-out secret (tool and error paths with the list passed);
- items (95): one per member of "removed" (55; ESC, U+009B and the other C1 openers here stand alone or before a non-sequence character), one per space-like member (9), one per sequence family and opener form of 4.1 (16: both CSI openers, private and intermediate forms, CSI with a C0 inside, CSI aborted by CAN, OSC with each of its three terminators, OSC never ended, DCS, SOS, PM, APC in both opener forms, nF, Fp, Fe, Fs, lone ESC), 12 ignorables (zero-width space, joiner and non-joiner, U+FE0F, U+034F, U+115F, U+1160, U+3164, U+FFA0, U+00AD, one tag character, one variation selector above U+E0100), and the visible separators tab, space, line feed;
- **run length axis (design M3/M7):** runs of 1, 2 and 3 items, mixed families (a C0 character, a CSI, an nF), and runs mixed with one space-like or one ignorable item between them;
- **encoding axis (design M2/M7):** the item spelled raw, percent-encoded (`%1b`), as backslash text (`\x1b`, `\033`, `\u001b`) and as an entity (`&#27;`); the key spelled plain and with its first letter percent-encoded (`%41KIA...`), including the item placed INSIDE the encoding token (`%4` + item + `1KIA...`);
- **NFKC axis:** the key with two letters in full-width form plus one item;
- positions (7): inside the key name, at the separator, value start, inside the value, value end, line end, directly before a placeholder-shaped literal; and for single items EVERY offset of the token;
- **size seam:** one item placed at character 262,143 (the last one inside the cap) and one at the `prepare_output` cut (`max_bytes` boundary);
- paths: `redact_untrusted`, `prepare_output`, `error_reason`, `safe_head`, `channel.clean`, `redact_value` (model-written), and `redact_many` / plain `redact()` (direct callers, expected: today's behaviour plus the new reader through `strip_ansi`);
- counts, asserted and printed: singles, one case = one (input, path) pair, at least 9,000; pairs: ALL 4,465 unordered pairs of two DIFFERENT items (95 x 94 / 2; readiness m1), one input each, the position drawn with `random.Random(77)`; a run with zero counted cases fails;
- each case carries its expected class, computed from the contract table by the oracle, never by the implementation: **masked** (no piece of the value of 5 or more characters, cut at the item offsets, may stand in the output), or **not promised** with one of the reasons of section 3. "Not promised" cases are counted per reason and the counts are asserted against a pinned table, so the class cannot silently grow;
- **no step back:** for every case, if main masks the value (fixture `prh_main_verdicts.json`, recorded from main, section 5.1) the branch masks it. Expected exceptions are listed by input, not by a rule: the author found exactly one shape, where main masks a WRONG value made of a sequence's left-over byte (`peer10` + ESC `7` + `.20.30.44`: main masks `7.20.30.44`); any other difference fails the test.

**T2 handed-out secrets:** every item at every offset of HAND and of one alphanumeric handed-out secret (`"Zq9" + "xw7Ty3pL4m"`), on `prepare_output` and `error_reason`, plus the encoding axis of T1 for the "removed" items; assert no piece of 5 or more characters.

**T3 forgery invariants, asserted on EVERY output of T1 and T2 and on a dedicated list** (2.5, M5a, plus each item inside and around a marker and a placeholder-shaped literal, at every offset): on the untrusted paths, on the output as written AND on `canonical(output)`: no `_MARKER` match; every genuine-shaped placeholder is a key of the call's map; with a pre-filled map `{"<IPV4_2>": <a value not in the text>}`, `<IPV4_2>` never stands in the output. On every other path (card, `redact_value`, `safe_head`, plain `redact_text` as the judge and vendor screen use it): a placeholder or marker shape that exists only after hidden items are removed appears only in the escaped form (promise 3b); for an input with no hidden item the output equals main's (recorded fixture).

**T4 overlapping known values (W0, D2; `tests/test_prh_spans.py`):** (a) `test_mf_sweep_partial_overlap` and `test_mf_keep_earlier_masks_partial_overlap`: the rows of `r3/scripts/probe_d2_overlap.py` (partial overlap in both list orders, equal length, nested short-first, three-chain, mixed spelling domains), through `redact(text, mapping=run_map)`, `_keep_earlier_masks` and `redact_untrusted`; assert no piece of 4 or more characters of any known value stands in the output (main fails: `r3/d2-overlap-main.out`); (b) `test_mf_span_rule_generator`: 2,000 seeded pairs (`random.Random(790)`) of made-up values with an overlap of 1 to 12 characters in every kind (partial, nested, equal length, same start) and both list orders; same assertion plus `restore(output) == input`; (c) `test_nested_restore_exact` (a value nested in another: output holds only the longer value's placeholder and restore is exact; passes on main, a guard against mutant 38) and `test_mf_merged_entry_reused` (the same partially overlapping pair in two texts of one run gets the same merged placeholder; fails on main, which leaks); (d) `test_case_790_regression`: the exact case-790 input (seed 20261104, case index 790 of `tests/test_k5_round12_fuzz.py`'s generator, or the reduced form of 8.1) on `channel.clean` and the Slack producer: passes on main, regression guard.

**T5 regression file** `tests/fixtures/prh_regressions.json`: every entry is a list of parts (`{"lit": ...}`, `{"const": "KEY", "slice": [0, 4]}`, `{"cp": "1B"}`), so the file holds no control byte and no secret-shaped string; each entry has an id, its source, the paths, and the expected verdict. Sources, all of them: L1 to L12, M2a, M2b, G1 to G3, F1a to F1e, F1g, B1, B1b, B2, B2b, M1a, M1b, M3a to M3d, M5a of this ticket; sweep F1 to F4 (every listed input); round-7 design B1, B2, M3, M4, M5 and codebase M1, M2, M4; every input in the round-5 and round-6 reviews; every input row of the PR 77 probes. **Where these files are (readiness M3):** they are on branch `core/cloud-handover`, NOT on main; the builder reads them from the checkout `/home/user/hadavin-sdk` (do not copy them into the PR H branch): `handover/reviews/PR77/round7-design.md`, `round7-codebase.md`, `round5-src.md`, `round5-tests-hostile.md`, `round5-textnorm-docs.md`, `round6-changelog-textnorm.md`, `round6-src-redact.md`, `round6-tests-mutants.md`; `handover/evidence/PR77/97fd202/probe-5ab-findings-and-forged-markers.txt`, `probe-5-matrix.txt` (the single-case table), `RESULTS.md` (lines 153-155: encoded forms). Extraction rule: every input written as a Python expression or a quoted string in those files becomes one entry; an entry records `source` as `<file>:<line>`; an input that needs a value the files do not give (a secret, a key) uses the constants of section 2; an input the builder cannot rebuild exactly is listed in the checkpoint note with its file and line and reported to the lead (never dropped silently). The lead's brief for WP2c attaches these paths. Inputs whose class is "not promised" or "pull request 77" (look-alikes, wide dots, encoded forms, F7, M2c) are IN the file with that verdict and a strict expectation of today's output shape, so a later change is noticed.

**T6 clean corpus** (`test_prh_clean_corpus.py`): tab tables (`kubectl`-style rows, the six-cell row of round-7 M2), logs, JSON, coloured test output, a coloured `grep` match inside a word, Hindi, Persian with zero-width non-joiner, emoji with joiners and U+FE0F, shell with continuations (a `curl` command, a Dockerfile `RUN`, a Makefile rule, a Windows path ending in a backslash at a line end), nroff overstrike, a text with a Windows-1252 C1 character. For each: output equals the oracle's spaced reading exactly; the number of placeholders is not above main's (fixture `prh_main_corpus.json`); ignorables are all still present.

**T7 wiring:** stand-ins for `runmap.redact` AND for `guard.redact._Redactor.find` record their inputs: no call from any producer path receives a member of "removed" or "space-like". `tests/test_k5_tools.py` stays green unedited.

**T8 gate:** the set test of W4; a card test that a DCS payload is deleted (`channel.clean("a " + ESC + "Pq payload" + ESC + "\\" + " b")` holds no `payload`); a card test for M5a (exactly one `<IPV4_1>`, one `‹IPV4_1›`).

**T9 time** (`perf`, `tests/test_prh_perf.py`): gates G1, G2 and G3 of 4.4 on the shapes S1-S5, H1, H2 and W (exact lines copied from `r3/scripts/cost_r3.py`); `test_over_256_cut_values`: 300 distinct e-mail addresses, each CUT by a colour code inside its local part (so each is a needed value), must raise `InputTooLarge` (design D5); `test_spaced_value_long_spaces`: `password="a b c d"` followed by 10,000 spaces and repeated to the cap, under 3.0 s (design D6); every shape: never past the budget by more than one pass.

**T10 unit tests of `hidden.py`** against the oracle: every row of the oracle's `GRAMMAR_ROWS` (38) and `GLUE_TABLE` (10), each also at the start, middle and end of a text, nested openers, every abort rule, 20,000 seeded random strings over an alphabet of the class members plus 12 ordinary characters (`strip` equals the oracle's `readings`; `strip_sequences` equals `readings(text, sequences_only=True)[1]`; both applied twice equal once; an unterminated opener repeated to 200,000 characters is linear by the `timing.py` rule; the joined reading holds no member of "removed" or "space-like"); the table equality of the oracle (c) and the file hash.

**T11 grounding** (`test_prh_grounding.py`): for each of the 12 ignorables of T1: `evidence.grounded` refuses an identifier that holds it, and `evidence.contains` finds `pod-1` in an evidence text that holds it inside the name; the zero-width space (Cf) rows pass on main too.

**T12 tools** (`test_prh_tools.py`): `_first_decoded(c) == c` for every member of "removed"; a cut tail of 4,000 bells makes no `_decoded_clean` call per bell (stand-in counter: at most the count main makes); `ToolOutput.sha256` of a stand-in tool returning `"a" + NUL + "b"`, run with a context whose `digest()` returns None (so tools.py:1197 takes its fallback; readiness m6), equals `sha256(("a" + NUL + "b").encode())`; L8 through the tool runner (not only `prepare_output`) is MASKED. D1 rows (`test_scrub_keeps_boundary[D1a]`, passes on main; `test_mf_scrub_cut_and_boundary[D1b]`, fails on main because main leaks the cut handed-out secret, `r3/d1-scrub-main.out`): D1a `"auth failed for " + HAND + " ; INFO user" + ESC + "[0m" + KEY` and D1b `"auth failed for " + HAND[:9] + ESC + "[0m" + HAND[9:] + " ; user" + BEL + KEY`, on `prepare_output` and `error_reason` with HAND handed out: the key and every piece of HAND masked (main masks the key; the rev-2 design leaked it, `r3/d1-scrub-proto.out`).

**5.2 Mutants and their killers** (`tests/prh_mutants.py`; each reverts one guard; the runner runs only the killer named here and expects it to FAIL; last line `43 of 43 good; problems: []`, or the real count if the builder adds mutants, never fewer; a mutant whose `old` text occurs more than once is refused by the runner (keep the runner's occurrence guard; D-018)):

| # | Mutant | Killer (node id) |
|---|---|---|
| 1 | CSI final-byte range ends at 0x7D | `tests/test_prh_hidden_unit.py::test_grammar_row[csi final 0x7E]` |
| 2 | C1 CSI opener U+009B not recognised | `tests/test_prh_hidden_unit.py::test_grammar_row[csi c1]` |
| 3 | C0 inside a CSI aborts instead of being dropped | `tests/test_prh_hidden_unit.py::test_grammar_row[csi c0 inside dropped]` |
| 4 | DEL inside a CSI not dropped | `tests/test_prh_hidden_unit.py::test_grammar_row[csi del inside dropped]` |
| 5 | OSC does not end at BEL | `tests/test_prh_hidden_unit.py::test_grammar_row[osc BEL]` |
| 6 | ST as U+009C not recognised | `tests/test_prh_hidden_unit.py::test_grammar_row[osc C1 ST]` |
| 7 | a string never ended runs past the line end | `tests/test_prh_hidden_unit.py::test_grammar_row[osc never ended, line end kept]` |
| 8 | DCS payload kept | `tests/test_prh_hidden_unit.py::test_grammar_row[dcs C1]` |
| 9 | nF final byte not consumed | `tests/test_prh_hidden_unit.py::test_grammar_row[nF]` |
| 10 | Fp range missing | `tests/test_prh_hidden_unit.py::test_grammar_row[Fp]` |
| 11 | lone ESC kept | `tests/test_prh_hidden_unit.py::test_grammar_row[lone ESC at end]` |
| 12 | U+0000 not in "removed" | `tests/test_prh_hidden_unit.py::test_classes_exact` |
| 13 | U+0085 treated as removed, not space-like | `tests/test_prh_hidden_unit.py::test_classes_exact` |
| 14 | U+2028 left untouched | `tests/test_prh_hidden_unit.py::test_classes_exact` |
| 15 | tab moved into space-like | `tests/test_prh_hidden_unit.py::test_classes_exact` |
| 16 | glue space dropped | `tests/test_prh_hidden_unit.py::test_glue_row[ab\x07cd]` |
| 17 | glue space added at every removed item | `tests/test_prh_hidden_unit.py::test_glue_row[ab\x07-cd]` |
| 18 | glue decided per item, not per run | `tests/test_prh_hidden_unit.py::test_glue_row[ab\x07\x07cd]` |
| 19 | `is_ignorable` / `IGNORABLE_RE` back to category Cf only | `tests/test_prh_hidden_unit.py::test_ignorable_equals_file_and_rule` |
| 20 | `strip` moved after the escaping step in `redact_text` | `tests/test_prh_contract.py::test_mf_forgery_untrusted[F1b]` |
| 21 | decoded readings not stripped | `tests/test_prh_regressions.py::test_regression_row[mf_L11]` |
| 22 | the gap pattern without the space alternative | `tests/test_prh_regressions.py::test_regression_row[mf_L1]` |
| 23 | step 6 returns the joined result instead of raising (rev 3 meaning) | `tests/test_prh_contract.py::test_step6_refuses` (a stand-in for `runmap.redact` drops one held placeholder on the mask pass; expects `RedactionError`) |
| 24 | step 3 counts every held value, not only the needed ones | `tests/test_prh_regressions.py::test_regression_row[M1a]` |
| 25 | more than 256 needed values returns the joined result instead of raising | `tests/test_prh_contract.py::test_over_256_needed_refuses` |
| 26 | values under 4 characters replaced anywhere | `tests/test_prh_contract.py::test_short_value_whole_word_only` |
| 27 | W0 not applied in `_keep_earlier_masks` (back to one replace after another) | `tests/test_prh_spans.py::test_mf_keep_earlier_masks_partial_overlap` |
| 28 | the `strip_hidden` decoded reading removed from `_views` | `tests/test_prh_regressions.py::test_regression_row[mf_M2a]` |
| 29 | `_no_created_shapes` removed | `tests/test_prh_contract.py::test_mf_no_created_shapes[F1b-safe_head]` |
| 30 | `_scrub` finds on the raw text | `tests/test_prh_tools.py::test_mf_handed_out_cut[L6]` |
| 31 | `_scrub` returns the scrubbed JOINED text when it found a secret (rev 2's design) | `tests/test_prh_tools.py::test_scrub_keeps_boundary[D1a]` |
| 32 | `_decoded` not stripped | `tests/test_prh_tools.py::test_mf_handed_out_encoded_cut` |
| 33 | `_first_decoded` calls the stripped `_decoded` | `tests/test_prh_tools.py::test_first_decoded_plain` |
| 34 | `_sanitise` turns NUL into U+FFFD again | `tests/test_prh_tools.py::test_mf_digest_keeps_nul` |
| 35 | `_refuse_forgery` reads only the AS-WRITTEN form (rev 3: rev 2's "only the canonical form" was an equivalent mutant, no test can kill it, because a placeholder that stands as written also stands in the canonical form) | `tests/test_prh_contract.py::test_refuse_forgery_reads_canonical` (direct call with an output holding a full-width placeholder `\uff1cIPV4_9\uff1e` and an empty map; expects `RedactionError`) |
| 36 | `_refuse_forgery` not called | `tests/test_prh_contract.py::test_refuse_forgery_called` (stand-in: `runmap._no_created_shapes` replaced by `lambda before, after: after`; input F1b on `redact_untrusted`; expects `RedactionError`) |
| 37 | the paired joined spelling of earlier masks removed | `tests/test_prh_spans.py::test_case_790_regression; if the runner reports it survives, the builder adds the smallest input where a decoded reading needs the joined spelling, or, if none exists, reports the mutant to the lead as equivalent with the reason` (never deletes it silently) |
| 38 | W0: a span inside another kept (both placeholders emitted) | `tests/test_prh_spans.py::test_nested_restore_exact` |
| 39 | W0: a merged span emits only its first member's placeholder | `tests/test_prh_spans.py::test_mf_span_rule_generator` |
| 40 | W0 not applied in the redactor's sweep | `tests/test_prh_spans.py::test_mf_sweep_partial_overlap` |
| 41 | W0: a merged placeholder is issued anew although the map holds the merged text | `tests/test_prh_spans.py::test_mf_merged_entry_reused` |
| 42 | `_scrub` backstop removed | `tests/test_prh_tools.py::test_scrub_backstop_withholds` (stand-in `_scrub_layers` returns its input on the second call; expects `MARKER + TRUNCATED`) |
| 43 | step 5: ` ?` inserted between every pair of characters | `tests/test_prh_contract.py::test_gap_only_between_word_chars` (value `x-y1234`, text `x -y1234` with a real space: must NOT be masked as the value) |

**Must FAIL on main** (behaviour assertions through public entry points only; a failure by "missing name" does not count): every test whose name starts `test_mf_` or whose parameter id starts `mf_` in the files of acceptance 7 (members include L1 to L5, L7, L9 to L12, M2a, M2b, F1a to F1e, F1g, M5a, G3, the non-Cf ignorable grounding rows, L8 through the runner, the W0 partial-overlap rows). **Must PASS on main**: every other test in those files (members: B1, B1b, B2, B2b, G1, G2, M1a, M1b, M3a to M3d, D1a, the Cf controls, case 790, nested restore, the clean-corpus items without `mf_`, T7). **No old behaviour** (not run on main): `tests/test_prh_hidden_unit.py`, which imports the new module.

### 5.1 Fixtures recorded from main

`tests/record_prh_main.py` (not collected) builds the T1 and T6 inputs with the oracle and writes, per case id, whether main masks the value (`prh_main_verdicts.json`) and, per corpus item, main's output placeholder count (`prh_main_corpus.json`). Its first output line is `hadavin_sdk loaded from <path>` so the record shows which code ran. Command (the branch's own venv, main's source first on the import path; PYTHONPATH entries come before the venv's `.pth` entry):

```
git -C <repo> worktree add --detach /home/user/build/PRH-main origin/main
cd /home/user/build/PRH && env -i PATH=/usr/bin:/bin HOME=/root PYTHONPATH=/home/user/build/PRH-main/src <branch venv>/bin/python tests/record_prh_main.py --out tests/fixtures > /home/user/build/PRH/record-main.log 2>&1; rc=$?; head -n 1 record-main.log; tail -n 2 record-main.log
```
Pass: rc 0, first line names `/home/user/build/PRH-main/src/hadavin_sdk/__init__.py`, last line `recorded <N> verdicts and <M> corpus counts`.

## 6. Acceptance checklist, who runs what, stop rule

### 6.0 Environment set-up (rev 3, M6; every command is literal, no placeholders except `<sha7>`, the first 7 characters of the head being checked)

Builder, once, before WP0:
```
git -C /home/user/hadavin-sdk fetch origin main
git -C /home/user/hadavin-sdk worktree add -b core/prh-strip-hidden-controls /home/user/build/PRH origin/main
cd /home/user/build/PRH && UV_PROJECT_ENVIRONMENT=/home/user/build/PRH-venv uv sync --locked --no-build --all-extras --group test > /home/user/build/PRH-uvsync.log 2>&1; echo rc=$?
git -C /home/user/hadavin-sdk worktree add --detach /home/user/build/PRH-main origin/main     # main's source, for 5.1 and G4
```
Every later command in the builder's worktree runs as `cd /home/user/build/PRH && env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u VAULT_TOKEN UV_PROJECT_ENVIRONMENT=/home/user/build/PRH-venv uv run --no-sync <tool> ...` (`--no-sync`: never resolve or download during a run; the venv was made once by the locked sync above, which is CI's own install command, ci.yml:78). Network: PyPI answered on 2026-11-11 (`r3/hosts-check.out`); if it does not, the sync fails visibly and the builder reports it (no offline fallback is invented). Postgres: the local runs do NOT set `HADAVIN_TEST_PG_DSN`, so the database tests skip in BOTH the head run and the main run, and the skip-list diff compares like with like; CI runs them with its service (ci.yml:89).
`heavy.sh` runs its arguments as a command, with no shell, so a redirect is written OUTSIDE it: `/home/user/build/heavy.sh env -u ... UV_PROJECT_ENVIRONMENT=... uv run --no-sync pytest ... > /home/user/build/PRH-full.log 2>&1; rc=$?; tail -n 3 /home/user/build/PRH-full.log`.

Evidence runner, once per head: `git -C /home/user/hadavin-sdk worktree add --detach /home/user/build/EV-PRH-<sha7>/wt <sha>`; `cd /home/user/build/EV-PRH-<sha7>/wt && UV_PROJECT_ENVIRONMENT=/home/user/build/EV-PRH-<sha7>/venv uv sync --locked --no-build --all-extras --group test`; for Python 3.12 the same with `UV_PROJECT_ENVIRONMENT=/home/user/build/EV-PRH-<sha7>/venv312 uv sync --locked --no-build --python /usr/bin/python3.12 --all-extras --group test`; a main worktree for item 3's skip list and items 7 and 9: `git -C /home/user/hadavin-sdk worktree add --detach /home/user/build/EV-PRH-<sha7>/main origin/main` with its own venv the same way. In 6.1, `uv run` means `env -u ... UV_PROJECT_ENVIRONMENT=<that venv> uv run --no-sync`.

### 6.1 Acceptance (each item is a command for the evidence runner)

Run from the repository root of the branch head (`/home/user/build/EV-PRH-<sha7>/wt`); environment and `uv run` as in 6.0; gate on the command's own exit code (`cmd > log 2>&1; rc=$?; tail -n 3 log`), never on a pipe. Heavy items (3, 5-mutants, 6, 7) run through the slot wrapper `/home/user/build/heavy.sh <command>` (at most 3 heavy commands machine-wide; checked 2026-11-11: the queue scripts `qsubmit.sh`/`qrun.sh` named in the machine profile are not present on this machine, `heavy.sh` is). Items 4 and 9 run alone (below).

1. `git diff --name-only origin/main...HEAD > files.txt; rc=$?` and `! grep -v -x -E 'src/hadavin_sdk/guard/(hidden|redact|runmap)\.py|src/hadavin_sdk/tools\.py|tools/gen_default_ignorable\.py|tests/(hidden_oracle|test_prh_[a-z_]+|prh_mutants|record_prh_main)\.py|tests/fixtures/(prh_regressions|prh_main_verdicts|prh_main_corpus)\.json|tests/fixtures/default_ignorable_perl5382_unicode1500\.txt|\.github/workflows/ci\.yml|CHANGELOG\.md|SECURITY\.md' files.txt` (exit 0 = no other file).
2. `uv run --all-extras --group test ruff check` and `uv run --all-extras --group test ruff format --check`: exit 0. `! git diff origin/main...HEAD | grep -q -E '^\+.*(noqa|type: ignore|nosec)'`: exit 0.
3. Python 3.13: `uv run --all-extras --group test pytest -p no:cacheprovider -q -m "not live and not perf" -rs > full313.log 2>&1; rc=$?`. Python 3.12: `UV_PROJECT_ENVIRONMENT=/home/user/build/EV-PRH-<sha7>/venv312 uv sync --python /usr/bin/python3.12 --all-extras --group test` then `UV_PROJECT_ENVIRONMENT=/home/user/build/EV-PRH-<sha7>/venv312 uv run --python /usr/bin/python3.12 --all-extras --group test pytest -p no:cacheprovider -q -m "not live and not perf" -rs > full312.log 2>&1; rc=$?`. Pass: both rc 0. Skip list: `grep '^SKIPPED' full313.log | sed 's/ in [0-9.]*s//' | sort > skips-head.txt`, the same on a main worktree run (`skips-main.txt`), `diff skips-main.txt skips-head.txt` exit 0. The main run (rev 3, M6): `cd /home/user/build/EV-PRH-<sha7>/main && /home/user/build/heavy.sh env -u ... UV_PROJECT_ENVIRONMENT=/home/user/build/EV-PRH-<sha7>/main-venv uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs > fullmain.log 2>&1`, one heavy slot, run once per evidence pass (main does not change).
4. Perf, alone (no other heavy job): the runner takes all three slots by nesting the locks, which waits instead of racing (readiness m8): `flock /tmp/heavy-slot-1.lock flock /tmp/heavy-slot-2.lock flock /tmp/heavy-slot-3.lock env -u ... UV_PROJECT_ENVIRONMENT=... uv run --no-sync pytest -p no:cacheprovider -q -m perf -rs > perf.log 2>&1; rc=$?`. Pass: rc 0.
5. `uv run --all-extras --group test bandit -q -r src demos tools -ll`: exit 0. `uv run --all-extras --group test python tools/scan_repo.py`: exit 0. `uv run --all-extras --group test python tests/stage_mutants.py`: exit 0. gitleaks: `/home/user/build/bin/gitleaks git --config .gitleaks.toml --redact --exit-code 1 --log-opts "origin/main..HEAD"` (binary present on 2026-11-11). Pass: exit 0. If the binary is absent the item is FAILED-NOT-RUN, not replaced.
6. `uv run --all-extras --group test python tests/prh_mutants.py > mutants.log 2>&1; rc=$?; tail -n 1 mutants.log`: rc 0 and last line `43 of 43 good; problems: []` (or the real count if the builder adds mutants; never fewer).
7. The fail-on-main proof: in a worktree at origin/main, copy only `tests/hidden_oracle.py`, the `tests/test_prh_*.py` files and the `tests/fixtures/` files of section 5; run `uv run --all-extras --group test pytest -p no:cacheprovider -q -rA --continue-on-collection-errors tests/test_prh_spans.py tests/test_prh_contract.py tests/test_prh_regressions.py tests/test_prh_clean_corpus.py tests/test_prh_grounding.py tests/test_prh_tools.py tests/test_prh_wiring.py > failmain.log 2>&1; rc=$?`. Pass: rc 1 (some fail); every test whose node id contains `test_mf_` or `[mf_` is FAILED with an assertion (`grep -E '^(PASSED|FAILED|ERROR) ' failmain.log` lists them; rev 3 naming rule, M4) (not an import or name error: `! grep -E 'ImportError|AttributeError|NameError' failmain.log` exits 0 for those tests); every other test PASSED. The runner pastes the counts and the list of tests that passed unexpectedly.
8. `python -c "import sys, hadavin_sdk.guard.hidden; print(sorted(m for m in sys.modules if m.startswith('hadavin_sdk')))"` (in the venv): prints exactly `['hadavin_sdk', 'hadavin_sdk.defaults', 'hadavin_sdk.guard', 'hadavin_sdk.guard.egress', 'hadavin_sdk.guard.hidden', 'hadavin_sdk.guard.injection', 'hadavin_sdk.guard.redact', 'hadavin_sdk.guard.runmap', 'hadavin_sdk.models']` (main's list of fact 20 plus `hidden`). `! grep -n -E '^(from|import) hadavin_sdk' src/hadavin_sdk/guard/hidden.py` exits 0.
9. Cost table (gate G4 of 4.4): `python tests/test_prh_perf.py --compare-main /home/user/build/EV-PRH-<sha7>/main > cost.log 2>&1` in the head worktree, alone (the same three-lock form as item 4). It prints `shape | chars | head median cpu | main median cpu | ratio | passes` for S1-S5, H1, H2, W at 65,536 and 262,144 characters, five runs each, alternating. Pass: S1-S5 ratio at most 1.25 at 262,144; every S and H row under 3.0 s CPU; W finished or `InputTooLarge`; the raw lines pasted. A failure is reported as FAILED with the lines; the remedy rule of 4.4 applies to the builder, not to the runner.
10. `git diff --stat origin/main...HEAD -- tests/warden_port tests/test_k5_round12_fuzz.py tests/test_k5_tools.py tests/test_k5_producers.py` prints nothing, and `uv run --all-extras --group test pytest -p no:cacheprovider -q tests/test_k5_round12_fuzz.py tests/test_k5_tools.py tests/test_k5_producers.py tests/warden_port/` exits 0 (already inside item 3; listed so the result is quoted on its own).
11. The rows of section 2 rerun on the head by the evidence runner's OWN script (the runner types the inputs from the constants table and the row expressions; it does not import the builder's tests): L1 to L12, M2a, M2b, G1 to G3 MASKED on their paths; F1a to F1e, F1g, B1, B1b, B2, B2b handled or refused, none forged; M5a: the card output holds exactly one `<IPV4_1>`. Pass line per row.
12. CHANGELOG: `git diff origin/main...HEAD -- CHANGELOG.md | grep '^+' > cl.txt`; `! grep -n -i -E 'guarantee|tamper|as a terminal shows|every hidden|all hidden|any hidden' cl.txt` exits 0; every `tests/test_prh_*.py` name that cl.txt mentions exists (`grep -o 'tests/test_prh_[a-z_]*\.py' cl.txt | xargs ls` exits 0); the "not promised" rows of section 3 are present (the runner lists each with the cl.txt line number). The last part is a reading check and is reported as such.

**Work packages = commits (rev 3, M7).** WP n is commit n. Each is sized to fit one 60-minute box; each commit must pass, before it is made, ruff, `ruff format --check`, its own new test files, and the 43 redaction test files of `handover/evidence/PRH-plan/target-files.txt` (paths relative to the repository root; one heavy slot, measured 169 to 216 s). The FULL suite runs once, at WP6, on the final head.

| WP / commit | Content | Tests that must pass at this commit | Must-fail tests added |
|---|---|---|---|
| WP0 | W0 span rule (redact.py sweep, `_keep_earlier_masks`, `mask_spans`, merged placeholder issue) | `tests/test_prh_spans.py` + the 43 files | `test_mf_*` of `test_prh_spans.py` (fail on main) |
| WP1 | `hidden.py`, generator, range file, oracle copy, `tests/test_prh_hidden_unit.py` (T10, W6, T8 set test); W1 (`strip_ansi` delegates) | the unit file + the 43 files (any gate test result change: stop, open question 2) | none (no old behaviour) |
| WP2a | W2 choke point: `canonical` with `IGNORABLE_RE`, `_repair`, `undo(strip_hidden=)`, `_views`, `redact_text` order, `_redact_stripped`, `_no_created_shapes`, `_refuse_forgery`; `tests/test_prh_contract.py` WITHOUT the T1 generator (T3, the unit tests of 5.2 for steps 3-6 and `_refuse_forgery`); `tests/test_prh_wiring.py` (T7, T8 card) | those two files + the 43 files | T3 rows, T8 card rows |
| WP2b | W3 tools.py (`_sanitise`, `_scrub`, `_decoded`, `_first_decoded`); `tests/test_prh_tools.py` (T2, T12, D1 rows); `tests/test_prh_grounding.py` (T11) | those two files + the 43 files | T2, T12, D1b, T11 rows |
| WP2c | `tests/record_prh_main.py` and its two fixtures (5.1, run once); T1 generator in `test_prh_contract.py`; T5 `test_prh_regressions.py` + `prh_regressions.json`; T6 `test_prh_clean_corpus.py` | those files + the 43 files | T1, T5, T6 `mf_` rows |
| WP3 | `tests/prh_mutants.py` (5.2), the CI step, `tests/test_prh_perf.py` (T9, gates G1-G3, `__main__` for G4) | mutant runner once (`43 of 43 good`), perf once alone | none |
| WP4 | W7 documents: CHANGELOG, SECURITY.md, docstrings | ruff; the 43 files; then the FULL suite once on 3.13 through `heavy.sh` (this is the final head for the evidence runner) | none |

CI step (WP3): one new step in the job `check`, directly after "Stage-rename mutants" (ci.yml:93-94): `name: PR H hidden-item mutants (each reverted guard must be killed by its named test) (blocks)`, `run: python tests/prh_mutants.py`. Nothing else in ci.yml changes. Commits end with the trailer the lead's session gives.

**Stop rule inside a box (M7).** At 60 minutes the builder stops. If the package's tests are green, it commits and reports. If they are NOT green, it does NOT commit on the branch: it saves `git diff > /home/user/build/checkpoints/PRH-WP<n>.patch` and `git status --short > /home/user/build/checkpoints/PRH-WP<n>.status`, writes the checkpoint note (done / next / failing test ids / the patch path), resets the worktree to the last green commit (`git stash` is not used; the patch file is the hand-over), and reports. A fresh agent applies the patch (`git apply`) and continues. So every commit on the branch is green; no red commit and no squash is needed.

**Repository scanners after every work package (M8):** `uv run --no-sync python tools/scan_repo.py` and `/home/user/build/bin/gitleaks git --config .gitleaks.toml --redact --exit-code 1 --log-opts "origin/main..HEAD"` (gitleaks 8.30.1, checked 2026-11-11) both exit 0 before the WP's report. Writing rule for every committed file: every control or invisible character is written as an escape (`"​"`, `"\x1b"`), never literally; the fixtures use `{"cp": "1B"}` parts; the hash constant is named `RANGE_FILE_SHA256`.

**CHANGELOG wording rules.** Say what was reproduced and fixed, with the test file names. No "any", "all", "every hidden character" or "one reading": give the class members, the families of 4.1 and the pass counts of section 3 (1 or 2 for the text; at most 18). Use "reading" and "pass" only in the meanings of section 3, each explained once. Say "removed", "read as a space", "ignored for matching" in those words, each explained once. State every "not promised" row, the honest-data changes (overstrike, C1 characters inside words, model-written arguments and stored raw model replies lose control characters, the digest of a tool result with NUL changes, card payloads of DCS/SOS/PM/APC are deleted, an identifier with an ignorable character is refused by grounding). State that a tool result or document now comes back without colour codes and control characters. Do not say "tamper", "guarantee" or "as a terminal shows it". No number that was not measured on the final head.

### 6.2 Who runs what, time boxes and slots (studio rules: faster-builds-time-boxes-and-batching, review-loop-speed-rules, machine profile)

| Step | Who | What runs | Slots / time |
|---|---|---|---|
| WP0 to WP4 (section 6.1 table) | builder (Sonnet 5.5), own worktree `/home/user/build/PRH`, venv `/home/user/build/PRH-venv` (6.0); a fresh agent per package when the previous one stopped | its own test files while iterating; the 43 files once per package through `heavy.sh`; record main fixtures once (WP2c); mutant runner once and perf once alone (WP3); ONE full suite on 3.13 (WP4) | 1 heavy slot per 43-file run; perf alone; time box 60 min per package |
| Evidence | separate EVIDENCE RUNNER agent (general-purpose, brief says "EVIDENCE RUNNER") | acceptance 1 to 12 on the final head only | items 3 (two Pythons), 6, 7 through `heavy.sh`; items 4 and 9 alone; no reruns for unchanged heads |
| Result review | lead starts the egm:* reviewers in parallel with the evidence runner, from one snapshot of the head (snapshot-before-review rule) | - | - |

Every builder brief says: write a checkpoint note to `/home/user/build/checkpoints/PRH-WP<n>.md` every 30 minutes (done / next / blockers / commit SHA); at 60 minutes apply the stop rule of 6.1. Durations measured: the 43 files 169 to 216 s (8.3; `r3/targeted-r3-probe.log`). Not measured by the author: the full suite on this machine (the Q8b evidence log `handover/evidence/Q8b/be53718/02-full-pytest.log` gives the current figure) and the mutant runner (43 mutants; each runs only its killer).

### 6.3 Stop rule (redaction path, no round cap)

Done when ALL hold: (a) a result-review round by fresh egm:* reviewers finds 0 blockers and 0 majors on the final head; (b) the independent evidence for acceptance 1 to 12 is attached for that exact head (the sha in the evidence equals the reviewed snapshot); (c) every minor is fixed in the same push or written as a ledger row with a date; (d) `egm:egm-drift-report` has run. A new review round starts only for a blocker or a major. A round that finds a blocker in the design (not in the build) sends the ticket back to plan review instead of a fix batch.

**What later packages must do.**
- Pull request 77: restart from its own head 76adadb, rebase on PR H (conflicts are certain in redact.py, runmap.py, tools.py and CHANGELOG.md), drop its own escape handling in favour of `hidden.py`, rerun all its fail-before proofs, restate its pass count on top of PR H's.
- Q8b (`tickets/Q8b-partial-mask-and-card-redaction.md`): its edit list (line 6) and PR H's share two files: `.github/workflows/ci.yml` (each adds one step) and `CHANGELOG.md` (each adds lines under "Unreleased"); both additive; whoever merges second rebases those two. Q8b's hard limit (no edit of redact.py, runmap.py, tools.py) is respected from its side. **Instruction for the Q8b builder after PR H merges** (the coupling is larger than rev 1 said; design review, Q8b overlap): Q8b's own coupling list (its lines 13-14) says `canonical` and `strip_ansi` decide which spellings its N4 and ESC rows mask, and PR H changes both, and the card now gets text without controls from the choke point and escapes forged placeholders. So: rebase on the new main; rerun Q8b's XPASS check and its fail-on-base procedure with the new main as the base; any Q8b test that now passes on the base is reclassified with a reason (never deleted); report the changed rows to the lead. Q8b's merge-order sentence ("PR77 lands first", its line 9) is stale; the lead decides the order (questions-for-lead, PR H section).
- Separate ledger rows stay separate (D-018): the scrub comparing in two domains (F7), the "which reading wins" rule (round-7 M6), vendor key glued to a word, F10; plus PR H-b and PR H-c.

## 7. Open questions, with the safe default taken

1. **Should the judge input (judge.py:71), the vendor screen input (bedrock_guardrail.py:98) and `safe_head` escape markers and placeholder-shaped text (lead point 2)?** Default taken: no change of the escaping step in PR H. Reasons: the judge is given text the caller has already redacted, and the comment at judge.py:69-70 says placeholders must pass unchanged; switching to the untrusted variant would rewrite genuine placeholders. Rev 2 adds promise 3b: on these callers a hidden item can no longer CREATE a placeholder or marker. Next step: a dated ledger row for the lead to decide after a full trace of the six "no" rows of 2.1; proposed date 2026-11-18.
2. **`strip_ansi` delegates to the new reader, so the approval gate recognises more sequence families without an edit of gate.py.** Default taken: delegate (one reader), and stop if any gate test changes. Alternative if reviewers want zero gate change: keep the old pattern under a private name for the gate's import only (then two readers remain, and the ticket title's claim becomes "one reader on the redaction path").
3. **Collapsing carriage return and line feed in `safe_head` (sweep F9).** Default taken: not in PR H; `safe_head` also stores a raw multi-line model reply (k1b/loop.py:187), which collapsing would change. Next step: dated ledger row; proposed date 2026-11-18.
4. **Line continuation** (lead point 1): decided in rev 2: split out to PR H-b (both plan reviewers asked for it).
5. **Tab rule** (D-018, already logged as an owner question): white space is white space.
6. **Source of the ignorable table.** Default taken: the perl-derived Unicode 15.0.0 file, cross-checked by the from-memory rule over Python's 15.1.0 and 15.0.0 categories (equal, 4,174). Needs a third party or the owner: a copy of `DerivedCoreProperties-15.1.0.txt` with a known SHA-256, and the Unicode licence text. Until then the CHANGELOG says "Unicode 15.0.0 list".
7. **U+2028 and U+2029 are not in the gate's set.** Default taken: report only (T8 names the difference); no gate edit.
8. **Case 790:** answered (section 8.1); no open question left.
9. **Merge order of PR H and Q8b** (new): default taken: whichever is ready first merges first; the second rebases ci.yml and CHANGELOG.md and, if it is Q8b, follows the instruction of section 6.3. The lead decides (questions-for-lead).

## 8. ERRATA rev 2: what was run, what was found, what changed

Run on 2026-11-11 between 16:20 and 17:20 UTC (21:50 to 22:50 IST) by the ticket author, from the clean main worktree `/home/user/build/prh-author/main` (2a8c2aac), with `env -i PATH=/usr/bin:/bin HOME=/root /home/user/build/prh-author/venv/bin/python`. Raw outputs: `handover/evidence/PRH-plan/` (file names below). Prototype modes: `proto` = rev-1 design as monkeypatches; `protofix` = proto + the case-790 fix only; `protofixes` = proto + every rev-2 change (`errata/fixes.py`). These are the author's own runs, not independent evidence.

### 8.1 Case 790 (readiness B2, design B1)

- **Reproduced** under `proto` (`c790.out`): the existing fuzz test's case 790 (seed 20261104, `tests/test_k5_round12_fuzz.py`) is a `password` assignment with a markup tag inside the key word (`passw<i> </i>d`), whose value is `PART1` + `\U0000000b` (a vertical tab written as a backslash escape) + `PART2`, among 120 placeholder-shaped junk items. Main masks it; `proto` leaks `PART2` on `channel.clean` (and so on the Slack producer, which shows `clean`'s output). The reduced input `"note " + "passw<i> </i>d=" + PART1 + "\\U0000000b" + PART2 + " end"` leaks the same way, with no junk (`c790b` run, recorded in `c790d.out`).
- **Cause** (`c790d.out`, line "keep_earlier_masks view"): in the card's second call (tags deleted), the first pass masks the whole encoded value (`<SECRET_1>`) and, in another reading, a shorter piece that ends where the vertical tab is (`<SECRET_2>`, value = the last 9 characters of PART1 + the vertical tab). In the decoded reading, the prototype turns the vertical tab into a space and then puts the earlier masks back with `_keep_earlier_masks`. The pairs are applied in LIST order: the spellings of `<SECRET_1>` that are tried first (raw, escaped) are not in the reading, the escaped spelling of the SHORTER `<SECRET_2>` (the 9 characters, no tab) is, and it is applied before the joined spelling of `<SECRET_1>` (`PART1 PART2`, added last by the prototype). So the shorter value cuts PART1, the longer value no longer matches, the reading's own pass masks `passwd=` up to the space, and `PART2` stays. On main the joined spelling does not exist (no stripping), so the order never mattered there.
- **Bug class:** replacement of overlapping known values in list order instead of longest first (the redactor's own sweep of known values already goes longest first). Choke point: `_keep_earlier_masks`, the one function that puts earlier masks back for every reading. **Design answer:** sort longest spelling first (W2). Sibling search: the other replacement loops over map values in runmap.py are the sweep inside `redact` (already longest first) and `replace_canonical` (one pattern, no list); `_redact_stripped` step 5 is written longest first.
- **Verified with the prototype:** `fuzz-plug_proto.log`: 1 failed, 4 passed (the leak); `fuzz-plug_proto_fix.log`: 5 passed; `fuzz-plug_main_fix.log` (the sort alone on main): 5 passed. The 43 redaction-related test files under `protofix`: `targeted-proto-fix.log`, 7,505 passed, 1 skipped, 22 deselected, rc 0; under `protofixes`: `targeted-proto-fixes.log` (result in section 8.3).

### 8.2 Reproduction of the design reviewer's inputs (rows from `repro-main.out`, `repro-proto.out`, `repro-protofixes.out`)

| Id | Input (constants of section 2) | main | rev-1 prototype | rev-2 prototype | Verdict and design change |
|---|---|---|---|---|---|
| M1a | 300 distinct e-mail addresses + `" user" + BEL + KEY` | MASKED (untrusted, tool) | LEAKED (untrusted, tool) | MASKED | reproduced (a step back on the prototype). Fixed: count only needed values; over 256 raise `InputTooLarge`; never return the joined result for that reason (`_redact_stripped` steps 3-4) |
| M1b | M1a + `" x" + ESC + "[0my"` | MASKED | LEAKED | MASKED | reproduced; same fix |
| M2a | `"id %4%1b[0m1KIA" + KEY[4:]` | LEAKED | LEAKED | MASKED | reproduced, on MAIN too (a leak of main, not only of the design). Fixed: `undo(strip_hidden=True)` reading (W2) and in `tools._decoded` (W3) |
| M2b | `"id %4\\x1b[0m1KIA" + KEY[4:]` | LEAKED | LEAKED | MASKED | reproduced on main; same fix |
| M2c | `"id &#6&#27;[0m5;KIA" + KEY[4:]` | LEAKED | LEAKED | LEAKED | not a key spelling: Python's entity decoder reads `&#6` as U+0006 (no semicolon needed), so no reading spells the key; added to "not promised" with that reason |
| M3a | `"user" + BEL + BEL + KEY` | MASKED | MASKED | MASKED | not reproduced as a leak (the prototype already glued per run); the TEXT was ambiguous: fixed by the run definition and the glue table (4.1); mutant 18 |
| M3b | `"user" + ESC + "[0m" + ESC + "[1m" + KEY` | MASKED | MASKED | MASKED | as M3a |
| M3c, M3d | runs mixed with a zero-width space; with a form feed | MASKED | MASKED | MASKED | as M3a; both rows are in the glue table |
| M4 | 3,000 generated inputs (assignment values with an encoded separator, with and without a decode-only key), then a later text `"the password " + value + " failed"` with the returned map | (no clean-up on main) | 0 inputs where the clean-up changed the later verdict | same | NOT reproduced; split out anyway (`tickets/PRH-c-map-entries-hygiene.md`): different bug class, and the k1b two-pass argument stands |
| M5a | `channel.clean("<" + ESC + "[0mIPV4_1> and 10.0.0.5")` | `<IPV4_1> and <IPV4_1>` | same | `‹IPV4_1› and <IPV4_1>` | reproduced on MAIN (not a regression of the design). Fixed for every caller by `_no_created_shapes` (W2), no edit of channel.py; promise 3b |
| F1a-F1g on callers without the escaping step | F1a, F1b, F1c, F1e, F1g on `safe_head` and on plain `redact_text` (as the judge, the vendor screen and model-written text use it) | all five forge a marker or a placeholder (`cost-main.out`) | not run | none forges (`cost-protofixes.out`, after the in-round rule of W2 `undo`) | reproduced on MAIN; fixed by promise 3b (`_no_created_shapes`, also inside the decoding rounds) |
| M5b | `channel.clean("<IPV4_1> and 10.0.0.5")` (control) | `<IPV4_1> and <IPV4_2>` | same | same | unchanged, as required |
| M6a | grounding: identifier `"pod-1\ufe0f"` | accepted (`canonical(v) == v`) | refused | refused | reproduced (behaviour change); now in the contract (promise 5) with T11 |
| M6b | `evidence.contains("po\u034fd-1 is running", "pod-1")` | False | True | True | reproduced (behaviour change); promise 5, T11 |
| FD | `tools._first_decoded("\x07")` | `"\x07"`, skip guard skips | `""`, does not skip | `"\x07"`, skips | reproduced; `_first_decoded` stays on the plain decode (W3), T12, mutant 33 |
| OSC/U+009C | `strip_ansi("a " + ESC + "]0;title" + "\x9c" + "visible after" + LF + "line two")` | `'a '` | - | - | rev-1 row was wrong; corrected in 2.3 |

The rows of section 2.4 and 2.5 under `protofixes` (`check-protofixes.out`): L1 to L12, G1 to G3 MASKED on every path that has the needed list (L6 and L12 "LEAKED" on untrusted and head are the "(no list)" cells: those paths are not given the handed-out secret, as on main); N1 to N3 (tab, backslash + line break, U+2028) LEAKED, as "not promised"; N4 (backspace overstrike) MASKED; F1a to F1e, F1g, B1, B1b, B2, B2b and the extra rows X5 to X7 handled on the untrusted and tool paths. On `error_reason`, F1b is reported "FORGED PLACEHOLDER" by the check script because that path's map is internal to `error_reason` and the check passes an empty map; the output itself is `ValueError: peer ‹IPV4_2› refused, seen from <IPV4_1>` (`f1b-error-reason.out`): the forged one is escaped and `<IPV4_1>` is the genuine mask of the address. The forgery rows on `safe_head` and plain `redact_text` (the callers without the escaping step): `cost-protofixes.out`, first lines.

### 8.3 Results of the rev-2 prototype on the existing tests

The 43 files are listed in `target-files.txt` (every test file that imports runmap, redact, tools, channel, slack_channel, the gate, the judge or evidence).
- `protofix` (case-790 fix only): `targeted-proto-fix.log`: 7,505 passed, 1 skipped, 22 deselected, rc 0 (215.74 s).
- `protofixes`, FIRST run: `targeted-proto-fixes-run1.log`: 3 failed, 7,502 passed. The three failures (`tests/test_k5_fixes2.py::test_an_escape_that_decodes_to_an_expanding_character_is_refused_before_the_work`, `tests/test_k5_fixes3.py::test_a_tool_result_with_a_secret_and_an_expanding_text_is_refused_before_the_work`, `tests/test_k5_fixes3.py::test_percent_encoded_expanding_text_is_refused_after_the_decode`) were the author's own slip in the prototype of `_no_created_shapes`: it ran `canonical` (an NFKC) over the whole raw text even when nothing had been removed, before the size checks, so an expanding text was normalised before it was refused. The design text of W2 now says when the helper returns at once and that it works on `fits_after_nfkc` output. Rerun of those two files plus the round-12 fuzz file: `targeted-proto-fixes-rerun3.log`, 34 passed, 1 skipped, rc 0.
- `protofixes`, second full run of the 43 files (after that correction): `targeted-proto-fixes-run2.log`, 7,505 passed, 1 skipped, 22 deselected, rc 0.
- `protofixes`, third and final run, after the in-round created-shape rule of W2 `undo` was added: `targeted-proto-fixes.log`, 7,505 passed, 1 skipped, 22 deselected, rc 0 (169 s). The reproduction and leak rows were rerun on this final prototype (`repro-protofixes.out`, `check-protofixes.out`, `f1b-error-reason.out`, `cost-protofixes.out`).

### 8.4 Every round-1 finding and its answer

| Finding id | Answer | Where in the ticket |
|---|---|---|
| Readiness B1 (line continuation undefined in the readings) | split out to PR H-b; readings defined per run with a glue table; the gap is one space only | 3 Words, 4.1 glue table, `tickets/PRH-b-line-continuation-matching.md` |
| Readiness B2 (case 790: sequence, prototype access, which commit is red) | diagnosed and fixed in the design before any build; prototype files named and readable; no commit is expected red | 8.1, W2 `_keep_earlier_masks`, Read first 2, 6.1 commit split |
| Readiness M1 (canonical ripple through nfkc, undo, `_views`, evidence.py) | ripple named, intended, tested | W2 first bullet, promise 5, T11 |
| Readiness M2 (`_first_decoded`, `_decoded_clean`) | both unchanged on purpose, with the reproduced reason | W3, T12, mutant 33, 8.2 row FD |
| Readiness M3 (`_sanitise` at tools.py:1194, digest) | both call sites change; digest change accepted with reason; tested | 2.2, W3, T12, CHANGELOG rules |
| Readiness M4 (order of steps, `_views` input, `_clean` inside `_views`) | pseudo-code; views of the escaped original and of the escaped joined reading; `_views`' `_clean` unchanged and stated | W2 pseudo-code, 3 "not promised" (decoded NUL) |
| Readiness M5 (Unicode data: format, name, perl, version, both Pythons) | file name, format, hash, copy in evidence, `UNICODE_DATA_VERSION = "15.0.0"`, builder needs no perl, stop if the hash differs, equality must pass on 3.12 and 3.13 (checked) | 1, W6, 4.1, T10 |
| Readiness M6 (literals for MAIL, PW, HAND, G1, G2) | constants table with parts | 2 constants |
| Readiness M7 (fixtures recorded from main, corpus in the main run) | names, script, command, pass line; corpus file added to the fail-on-main command | 5.1, 6.1 item 7 |
| Readiness M8 (stop rule) | written | 6.3 |
| Readiness M9 (time boxes, slots, who runs what, durations) | table, checkpoint notes, queue, perf alone, measured duration of the 43 files; full-suite duration pointed to the Q8b log | 6.2 |
| Readiness m1 (grep -c exit code) | `! ... grep -q` | 6.1 item 2 |
| Readiness m2 (Python 3.12 command) | exact commands with `/usr/bin/python3.12` | 6.1 item 3 |
| Readiness m3 (bandit without uv run, gitleaks config) | `uv run ... bandit`; `.gitleaks.toml` and the scratch binary named | 6.1 item 5 |
| Readiness m4 (acceptance 8 script and list) | exact command and expected list | 6.1 item 8, fact 20 |
| Readiness m5 (measurement script path; 1.25x not a test) | `tests/test_prh_perf.py` `__main__`; 1.25x only in the evidence table | 4.4, 6.1 item 9 |
| Readiness m6 (which ci.yml step) | one step in job `check` after stage mutants | 6.1 commit split |
| Readiness m7 (red tests at commit 2) | whole suite green at every commit | 6.1 commit split |
| Readiness m8 (33 removed items wrong; case counting) | 55 removed, 9 space-like, 95 items; a case = (input, path) | 3 table, T1 |
| Readiness "further": one reader, three callers | wording changed | W1 |
| Readiness "further": `strip_sequences` idempotence | tested | 4.1, T10 |
| Readiness "further": import cycle | named, no cycle | 4.1 |
| Readiness "further": open question 4 vs B1 | settled by the split | 7.4 |
| Readiness "further": `is_ignorable` implementation and cost | frozenset + Cf test | 4.1 |
| Readiness decisions 1-7 (`_repair` name, fixture names, `fits_after_nfkc` place, `is_ignorable`, fast-path regex, ci step, digest and `_first_decoded`) | each decided | W2, 5.1, W2 pseudo-code, 4.1, 6.1, W3 |
| Design B1 (case 790) | as readiness B2 | 8.1 |
| Design M1 (256 fallback gives up promise 2) | reproduced; fixed | 8.2 M1, W2 steps 3-4, T9, mutants 24-25 |
| Design M2 (decoding-produced item cuts an encoding token) | reproduced on main and prototype; fixed | 8.2 M2, W2 `undo`, W3 `_decoded`, T1 encoding axis, mutant 28 |
| Design M3 (glue for runs undefined) | not reproduced as a leak; definition fixed | 3 Words, 4.1 table, mutant 18 |
| Design M4 (map clean-up drops a protecting entry) | not reproduced (0 of 3,000); split out | PR H-c, 8.2 M4 |
| Design M5 (card forges placeholders) | reproduced on main; fixed for every caller | promise 3b, W2 `_no_created_shapes`, W4, T3, T8, mutant 29 |
| Design M6 (model-written text mutated; grounding changes; digest) | in the contract and the CHANGELOG; tested | promises 4-5, W3, T11, T12 |
| Design M7 (generator axes; "no shared code" too strong; 14,132 not evidence) | axes added; wording changed; count no longer cited | T1, 5 oracle paragraph, Read first 2 |
| Design 2 "wrong": OSC/U+009C row | corrected after running main | 2.3 |
| Design 2 "wrong": no F1f | said | 2.5 |
| Design 2 "imprecise": extract.py feeds the model | said | 2.1 |
| Design 3: short-value over-masking in step 5 | values under 4 characters only as a whole word | W2 step 5, mutant 26 |
| Design 3: T7 covers only `runmap.redact` | stand-in on `_Redactor.find` too | T7 |
| Design 3: stored raw reply loses control characters | in the honest-data list | 3 table |
| Design 3: line continuation | split out | PR H-b |
| Design 5: `_first_decoded` cost | as readiness M2 | W3 |
| Design 5: Q8b coupling understated; merge-order sentence stale | instruction for the Q8b builder; question to the lead | 6.3, 7.9, questions-for-lead |
| Design 5: card payloads deleted (approver sees less) | stated and tested | W4, T8 |
| Design 6: acceptance items not commands (3, 4, 5, 8, 9, 11, 12; Python 3.12) | each now a command with a pass line; item 12's last part is labelled a reading check | 6.1 |
| Design 7: licence from memory; rung 3 unresearched | dated next steps (2026-11-18), question to the lead | 4 ladder line, single-dependency line, questions-for-lead |
| Design 7: step-5 cost unmeasured; hostile >256 shape; Hindi/Persian not under 1.25x; budget only between readings | hostile rows measured roughly; budget check before every pass; 1.25x applies only to the four shapes without hidden items | 4.4, 3 pass counts, T9 |
| Design 8: "reading" two meanings; C0/C1/CSI/ST/CAN/SUB/DEL/nF/Fp/Fe/Fs unexplained; "fail to the safe side", "found", "joined", "gap" internal | "reading" vs "pass" fixed; names explained in section 1; "find", "mask", "joined", "spaced", "run" defined in section 3; "fail to the safe side" replaced by what happens | 1, 3 Words, W2 |

### 8.5 What failed or was not checked in this errata pass

- Failed and fixed during this pass (the author's own prototype slips, both now rules in the design text): the created-shape check normalised the whole text before the size checks (3 cap tests failed, 8.3); the created-shape check did not run inside the decoding rounds (F1e still forged on two callers, W2 `undo`).
- M2c stays LEAKED by the check script; judged "not a key spelling" (section 3, not promised). A reviewer may disagree.
- The 1.25-times cost limit for plain shapes is not shown by any run (prototype 1.34 times on plain ASCII, single runs under load).
- The `_keep_earlier_masks` order problem was not shown to trigger on main itself.
- Not run: full suite, ruff, bandit, gitleaks on the repository, mutation runner, perf tests, Python 3.12 tests.

## What I did not verify

- Any clause number or wording of ECMA-48, ECMA-35 or Unicode Annex 44; the CWE numbers; the Unicode licence name and text.
- The full suite, lint, bandit, repository scan, gitleaks, perf tests, mutation runner, Python 3.12 tests (none run). The 43 redaction-related test files were run under the prototype only (section 8.1, 8.3).
- The design under an independent oracle (the prototype is the author's own code); handed-out secrets beyond L6 and L12; the PEM, UUID, signed-token and command-flag kinds; `redact_many` and `redact_value` paths of T1.
- The cost limits of 4.4 with a fast reader (only the slow prototype was timed; single runs under machine load, other agents' evidence runs active).
- Whether the `_keep_earlier_masks` order problem can be triggered on main itself (main's pairs list has the same shape: raw spellings, then escaped spellings); the author did not find a main input; the fix applies to main's lists too.
- Every input of rounds 5 and 6; the pull request head 76adadb (not opened); the full call chains of the six callers without the escaping step; `demos/` (not searched for direct `redact()` callers).
- That no ready-made library fits (no live research possible from this machine).
