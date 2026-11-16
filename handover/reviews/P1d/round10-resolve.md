Status: resolved (headless `egm:egm-resolve`, 2026-11-09 UTC; IST = UTC+5:30). Fixes applied as P1d rev 11, P1d-learn rev 4, P1d-gate rev 4. Not committed.

# Plan review round 10: resolve

**Targets:** `handover/tickets/P1d.md` (rev 10, full file), `P1d-learn.md` (rev 3, full file), `P1d-gate.md` (rev 3, full file).
**Findings:** `round10-design.md` (1 Blocker, 3 Major, 10 Nits) and `round10-readiness.md` (3 Blocker, 6 Major as counted by the reviewer's text: M1-M6, plus minors). Both reviewers ran nothing; neither did this resolve (all new rows are hand-traced, UNVERIFIED until BS-0).
**Lead decision received during this resolve:** ORDER 188 (1): design B-1 = option (a) "blank only values known BEFORE this call" plus (c) "state the residual as a measured limit"; not (b). Applied in G1; no longer a lead question.

## Code claims checked before categorising (read in this workspace, 2026-11-09)
| claim | file:line | result |
|---|---|---|
| APIKEY masks a prefix plus 8 or more token characters, so `ghp_` + 12 and `AKIAIOSFODNN` are masked whole as heads | `guard/redact.py:119-135` (`_KEY_PREFIXES` has `ghp_`, `sk-`, `AKIA`), `:195` | TRUE |
| URLCRED's value is `[^\s]{2,1024}?` up to the `@` before a host lookahead, so `Pa**ss1234**` is masked whole | `redact.py:226-229` | TRUE |
| the generic SECRET value class `[^\s"';,&]` holds `*` and ESC, so `secret=Qm8v**Rt2xLp5n**` + PV and `password=` + SV_A + ESC `[1m` + SV_B (model entry) are masked whole | `redact.py:614` | TRUE |
| on the card entry `neutralise` runs before pass one | `guard/runmap.py:441-443` | TRUE |
| the card neutraliser removes escapes and controls: `normalise` = `strip_ansi` (a space only between two word characters) then `strip_controls` (0x00-08, 0x0B-1F, 0x7F-9F deleted) | `approvals/gate.py:200-205`, `:125-136`, `:162-163`; `channel._neutralise` = `withhold_commands(sanitise_text(...))` (`channel.py:47-48`) | TRUE |
| `runmap.redact` is the function, not the module | `runmap.py:25` (`from hadavin_sdk.guard.redact import ... redact`) | TRUE |
| `test_k5_fixes2` asserts the 261,000-byte document is under `max_document_bytes` | `tests/test_k5_fixes2.py:98-99` | TRUE (the default becomes 30,000) |
| the document check compares `len(document)` of bytes | `runtime/agent_loop.py:349, 354` (`document.hex()`, so bytes) | TRUE (ticket text right) |
| markers registered in `pyproject.toml:87-90`; no `addopts`, so no `--strict-markers` | `pyproject.toml` | TRUE |

## Blockers

### G1 (design B-1) Split secret whose head pass one already masked: AI Suggestion PROPOSE FIX (lead decided, ORDER 188 (1))
- **Finding:** rev 3 blanks every known value, including values masked by this same call, so `ghp_Ab1Cd2Ef3Gh4**` + 24 characters leaves the 24-character tail unlearned and shown; H37a-c expect "learned" but the design would not learn them. Conflict with GLUE-UP, which needs K blanked.
- **Justification:** verified (APIKEY `{8,}` masks the head). Search for one fix that keeps both: a content-free rule cannot tell `ghp_<12>` + LF + `<24>` from K + LF + `region=eu` (both are "masked head, line break, word characters"), so no single fix closes every shape without a false learn. The lead chose (a) + (c).
- **Proposed edit (P1d-learn rev 4):** (1) **Blanked values** = known values that were already in the caller's map BEFORE this call (earlier texts of the run), not seeds, length at least `min_key_chars`, kind in `SECRET_KINDS` or `EMAIL`. (2) **This-call values** (masked by this call's pass one) are not blanked; instead the **line-join rule**: a candidate that holds a this-call value o, written x + o + y, is dropped only when the learning view d_sp shows `x + " " + o` or `o + " " + y` (the only thing joining o to the rest was a line break). This keeps GLUE-UP, GLUE-EMAIL and a new reversed guard row unlearned, keeps the planted-value attack (B1 rows, PV masked in the same text and glued without a line break) learned, and learns marker, escape, accent and look-alike splits of a value whose head this call masked (`AKIAIOSFODNN**7EXAMPLE`, H37a, H37c). (3) Stated, measured limits (c): N9 (head masked in an EARLIER text, then split) and N10 (head masked in this text, then split by a line break; line-wrapped tokens), in the client text, counted in BS-2 and reported, not claimed. (4) Named test `test_split_secret_rows` with fail-before rows SPLIT-AKIA, SPLIT-GH-8/12/20, SPLIT-SK-8/12/20 and measure rows WRAP-AKIA, WRAP-60, PRIOR-SPLIT, H37b. (5) Mutants M68 (line-join rule removed), M68b (containment filter), M68c (HOSTNAME in the rule's kinds), M68d (blanking removed), M68e (this-call values blanked, rev 3), M68f (one side only). (6) Property test `test_line_join_rule_never_hides_an_unknown_key` (seeded loop).

### G2 (readiness B1) Which text each view family is built from, per entry: PROPOSE FIX
- **Finding:** on the card entry the neutraliser removes ESC, BS, CR and C1 before pass one, and `_finish` builds residue views only from `dropped(shown)`, so rows that depend on those carriers (H11-kv, H12a-d-kv, H13-kv, H14-kv, H15c-kv, H16*-kv, C05-kv, C06-kv, SUM-1..5; mutants M20b, M51, M4) cannot withhold on the card.
- **Justification:** verified (`runmap.py:441-443`; `gate.py:200-205`). Example H15c-kv: `strip_controls` deletes the backspace, so shown holds SV_A + `x` + SV_B; overstrike is never applied.
- **Proposed edit (P1d rev 11):** a per-entry table. Model entry (`neutralise` None): one family, views of `dropped(shown)`. Card entry (`clean`, its joined pass, `card_text`): two families, views of `dropped(shown)` (the text returned) AND views of `dropped(rr)`, `rr = redact(r, mapping=dict(work)).text` on the RAW input (a throwaway copy of the work map; the caller's map and `work` are unchanged). Learning views (P1d-learn) are views of `r` on every entry (unchanged). `max_work`, the log line's `views` (0 to 10) and `test_views_at_most_ten` follow. New mutant M82 (card raw family removed), killers H15c-kv, H11-kv. A per-row line names which family catches each carrier row.

### G3 (readiness B2; design M-1) B1-URLCRED cannot fail before: PROPOSE FIX
- **Finding/justification:** verified; pass one masks `Pa**ss1234**` whole, so the base shows nothing and the row cannot kill M68c.
- **Proposed edit:** rebuilt as `https://svc:Pass1234` + LF + `@build-01.corp/x` (model): the line break before `@` stops URLCRED and EMAIL in pass one, so the base shows `Pass1234`; view d joins it and the URLCRED lookahead reads the unblanked host: learned. M68c's killer becomes the new B1-EMAIL-LF row (`mail anna.m@` + LF + `build-01.corp`).

### G4 (readiness B3; design M-1) B1-SECRET cannot fail before: PROPOSE FIX
- **Finding/justification:** verified; the SECRET class takes `*`, so the base masks the whole value.
- **Proposed edit:** rebuilt with the KEY NAME split: `"password=" + PV + " then sec**ret=" + "Qm8vRt2xLp5n" + PV`: no SECRET match on the base (key name broken), the PV copy is swept, so `Qm8vRt2xLp5n` shows (oracle); view d gives a candidate holding PV, kept by the line-join rule (no line break), learned. The readiness hint "separate PV by an excluded character" was for rev 3's blanking; under rev 4 the glued form is what kills M68b.

## Majors

### G5 (design M-2) Cost of the learning pass: PROPOSE FIX
- **Proposed edit (P1d-learn):** fast path: a learning view equal to one already searched, or equal to the text pass one read when no blanked form occurs in it, is skipped (plain ASCII text without carriers costs nothing, which covers most of the 5,000 leaves of `redact_value`); the blanking finder is one trie per form family, cached in `mapping.redact_cache` under `"p1dl_blank"` (frozenset, patterns), built lazily; the line-join check runs only for new candidates (at most candidates x this-call values substring tests); a deadline check on `REDACT_BUDGET_S` before each view (past it: `_Held("size")`, mutant M81, test `test_learning_respects_budget`); BS-4L gate: p95 with learning at 3,000 and 30,000 characters under `REDACT_BUDGET_S / 4`, and the 5,000-leaf `redact_value` under `REDACT_BUDGET_S`, else STOP to the lead.

### G6 (design M-3) Learning in `card_text` adds no coverage: PROPOSE FIX
- **Justification:** the P1d caller table routes every `send`, `update` and `decide` through `_card_check`, which rebuilds the summary with `clean` (which learns); `card_text` learning only adds a mismatch risk and Slack's 3-second budget.
- **Proposed edit:** keyword `learn: bool = True` on `redact_text` (P1d-learn); `card_text` passes `learn=False`; M54 restored (flag ignored); tests `test_card_text_does_not_learn` and `test_stored_unknown_split_withheld_by_card_check`. P1d's `card_text` line updated.

### G7 (readiness M1) Fail-before oracle strings: PROPOSE FIX
- **Proposed edit:** every P1d-learn fb row names its oracle: by default the unknown value; H14 `OSFODNN7EXAMPLE`; H25 SV_B; B1-EMAIL `anna.m`; B1-EMAIL-LF `anna.m@`; B1-SECRET `Qm8vRt2xLp5n`; B1-URLCRED `Pass1234`; SPLIT rows the part after the split. `leaks` for an oracle whose scan key is shorter than `TN_MIN` is a case-insensitive exact substring test (P1d harness text).

### G8 (readiness M2) L-H25 on the model entry: PROPOSE FIX
- **Justification:** verified; on the model entry SECRET takes ESC and masks the whole value; on the card entry `strip_ansi` leaves a space, so SV_B shows.
- **Proposed edit:** H25 fb on the card only; L-H25-model becomes pb (base output pinned).

### G9 (readiness M3) Fail-before harness gaps: PROPOSE FIX
- **Proposed edit (P1d, shared harness):** classes read by a small pytest plugin `tests/p1d_classes.py` (`-p`), which writes each test id's `p1d(cls=...)` to `classes.json` at collection (junit has no marker values); `p1d_fail_before.py` copies the listed test files, `tests/p1d_api.py`, `tests/p1d_classes.py` and `tests/fixtures/p1d_cases.py` into the base worktree (exit 1 if a same-named base file differs); accepted failure prefixes `LEAK:`, `NEW_SURFACE:`, `NO_REFUSAL:`; helpers `api_patch(monkeypatch, "runmap._finish", fn)` (absent name = `NEW_SURFACE:`) and `refused(build)` (no `ConfigError` = `NO_REFUSAL:`) for P1d-gate; vocabulary: the marker holds the first word of a row's group (`fb`, `pb`, `inv`, `ow`, `measure`); "conditional" rows are `measure` until BS-0 (q) decides; "(RS-4)", "(P8-1)", "new" are notes; each entry of a "card, model" row is its own test id; marker string `"p1d(cls): P1d family test class fb, pb, inv, ow or measure; read by tools/p1d_fail_before.py"`.

### G10 (readiness M4) `runmap.redact` is the function: PROPOSE FIX
- **Proposed edit:** P1d-learn imports `find_matches` and `add_known` by name into `runmap` (`from hadavin_sdk.guard.redact import add_known, find_matches`); the patch target is `runmap.find_matches` (P1d-gate C-LEARN test, P1d-learn pseudocode).

### G11 (readiness M5) `test_k5_fixes2` rewrite incomplete: PROPOSE FIX
- **Proposed edit:** `test_a_document_whose_views_are_over_the_cap_is_document_too_large` sets both `evidence.max_document_bytes` and `evidence.redaction.max_text_chars` to `MAX_REDACT_CHARS` (line 99's assertion then holds).

### G12 (readiness M6; design nit "M4 killer") H29b card-only vs M4's "model entry" killer: PROPOSE FIX
- **Proposed edit:** new row H29b-m (fb, model, same input): notice; M4 killers H29b-m and H15c-kv (card, raw family, G2).

## Minors and Nits (all PROPOSE FIX unless stated)
- G13 (design nit, N9 wording): rewritten under G1 (blanking also removes the prefix or key name that sits inside the earlier value).
- G14 (both, P1d:247 stale `inputs=`): interface line now `card_withheld_text(run_id=None)`.
- G15 (design nit, M54 moved vs deleted): resolved by G6 (M54 restored in P1d-learn; P1d's "moved" note now true).
- G16 (design nit, N6/N7 duplicate): merged into N6.
- G17 (design nit, pseudocode fall-through and `added` init): P1d-learn pseudocode initialises `added = []` and states that `_finish` runs only when nothing was learned.
- G18 (design nit, pin `textnorm.fold`): BS-0 pins `fold`'s signature and whether it changes case; forms use the same call as the view.
- G19 (design nit, H28a-b ORDER 180 (1) vs (2)): CONTEST the need for a new lead answer: ORDER 180 (2) says every learning pass goes to P1d-learn ("if P1d must keep any learning, it carries HELD too"), and (1)'s point is "not P1d-a"; H28a-b need learning, so P1d-learn. Ticket text changed from "NEEDS LEAD confirm" to "per ORDER 180 (1)-(2)".
- G20 (design nit, ledger row split): P1d's ledger table splits BL-core-p1d-001 into 001a (known values, P1d) and 001b (unknown values, P1d-learn). `handover/ledger.md` itself is the lead's file and was not edited.
- G21 (design nit, RK8 flooding): P1d-learn states it: at most 16 learned values per call, about 125 calls fill `max_map_entries`, after which documents are refused as `document_too_complex` (fail safe).
- G22 (readiness minor, `_withhold` signature): `_finish` returns `_Held(...)`; only `redact_text` calls `_withhold(held, ctx, mapping)`.
- G23 (readiness minor, `leaks` short-key definition): G7.
- G24 (readiness minor, `p1d_api` imports `textnorm` lazily): stated (inside `leaks`).
- G25 (readiness minor, backspace at text start): a BS with no character before it deletes only itself.

## Counts
Accepted fixes 24 (G1-G18, G20-G25); contested 1 (G19, evidence in ORDER 180 recorded in `handover/LEAD-ORDERS.md`); escalated 0; declined 0; unaddressed 0. P1d mutants 57 -> 58 (55 table rows; M82 added). P1d-learn mutants: M54, M68d, M68e, M68f, M81 added.

## NEEDS LEAD (not answered by ORDERS 165-168, 180, 188)
1. Merge order P1d-a, P1d, P1d-learn, P1d-gate (DEFAULT PENDING LEAD 4 in P1d and P1d-gate; round-8 M5). Default kept.
