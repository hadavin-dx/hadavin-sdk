Status: resolved (fixes applied to `handover/tickets/P1d-a.md` as revision 3)

# P1d-a plan review round 2: resolve (egm-resolve method, headless)

**Written:** 2026-11-09T07:55Z (IST 13:25), by `date -u`. **Target:** ticket rev 2 (full file). **Findings:** `round2-design.md` (0 Blocker / 4 Major / 6 Nit) + `round2-readiness.md` (0 Blocker / 8 Major / 7 Nit) = 25 findings, merged into 18 groups (R2-G1..G18).
**Orders read (real text, `handover/LEAD-ORDERS.md`):** 165, 166 (item 2: over-mask accepted, measured, reported apart), 167, 168 (item 3: no silent best effort), 177 (split; no P1b dependency; HELD not on P1d-a), 178 (max 3 heavy runs, queue the rest), 179, 180 (q392-1: H28a-b stay in P1d = rev-2 NEEDS LEAD 2 CLOSED; q392-6: `&` ends a URL-query value only right after `?` or `&`, `test_query_param_credentials_are_masked` unchanged = D2 confirmed), 181 (q394-2: mutation runner R1 PR adds opt-in keywords, among them `forbid_skips`; R1 before relying on mutant evidence).
**Path class:** redaction, no round cap.

**Read on disk by the resolver (no test or probe run):** `origin/main` = `0dabf1fa7a2e`; `gate.py` symbols `_DOMAIN`, `_ANY_BLOCK` (ordered-list item `\d{1,9}[.)]` included), `_defang`, `_defang_outside_code`, `_clean_line` (last statement `return _defang_outside_code(line)`), `_clean_prose` (ZWSP comprehension `"​" + c if _ANY_BLOCK.match(c) and not (same and c == lines[i]) else c`), `_closed_fences`, `sanitise_text`; `channel.clean` (`return alt`, `return out`), `_neutralise`, `FakeChannel.send` (`clean(req.summary)`); `slack_channel._blocks` (`withheld = withhold_commands(req.summary)`, `shown = runmap.redact_text(withheld, seeded, neutralise=_neutralise)`, then `if len(shown) > self.max_card_chars`); `runmap.redact_text` (view loop `for view in views:`; the caller's map is filled in place by `mapping.clear(); mapping.update(current)`); `redact.py` generic SECRET entry (value `((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=]))+)`); `tools/mutation_runner.py` (`Mutant(name, file, old, new, expect, ..., only_test)`, `run_mutants(root, mutants, tests, *, extra_dirs, only, ...)`; no `forbid_skips` yet); `tests/stage_mutants.py` (registration pattern); `tests/test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook`. `git grep "\.summary"` in `src` and `demos` on main: only `FakeChannel.send` and `SlackChannel._blocks`. `/home/user/build/qsubmit.sh` does NOT exist (only `heavy.sh`, `evid.sh`, `evid-chain.sh`, `pgstart.sh`, `pgstop.sh`, `pulse.sh`); `/home/user/hadavin-sdk-handover` does NOT exist (the handover branch is checked out at `/home/user/hadavin-sdk`); no R1 mutation-runner branch on origin yet (R1 builder started 07:49Z per `cloud-register.md`).

**Counts:** 25 findings, 18 groups. PROPOSE FIX 25 (all applied). CONTEST 0. NEEDS LEAD 3 (end of file). Unaddressed 0.

---

## Majors

### R2-G1 global `[.]` undo hits code (design M1). PROPOSE FIX
Valid: `replace("[.]", ".")` also rewrites inline code and fence bodies, which the old gate never defanged. **Fix:** new `gate.undefang_text(text)`: on prose parts only (outside closed backtick fence bodies and inline code, the same split `defang_text` uses), `_LEGACY_DOT = (?<=[\w-])\[\.\](?=[\w-])` -> `.` (the old `_defang` wrote `[.]` only between name characters). Rows L10 (inline code kept), L11 (fence body kept), L12 (`see [.] here` kept). Mutants A3d (undo on the whole text), A3e (lookarounds removed). Stored summaries: decided (rev 2 NEEDS LEAD 3 stays open only for the render change).

### R2-G2 ZWSP rule under-specified (design M2). PROPOSE FIX
**Fix (exact):** in `_clean_prose(lines, defang)`: `seen = out if defang else [_defang_outside_code(c) for c in out]`; prefix `"​"` when `_ANY_BLOCK.match(d) and not (same and d == lines[i])` with `d = seen[i]`. Row Z4 `1。 x` (wide dot makes an ordered-list item only after defang). Mutant A13 = `seen = out`, killed by Z4 and the differential.

### R2-G3 D3 order versus wide dots (design M3; readiness M4 part, M7 part). PROPOSE FIX
Valid: D3 before the wide-dot rewrite leaves `<HOSTNAME_1>.example.com` and is not idempotent. **Fix:** per prose part: (1) `_WIDE_DOTS` -> `.`, (2) `_PLACEHOLDER_DOT`, (3) `_NON_ASCII_HOST`, (4) `_DOMAIN`. Row D3e `<HOSTNAME_1>。example.com` -> `<HOSTNAME_1>[.]example[.]com`; mutant A17 (steps 1 and 2 swapped) killed by D3e and `test_defang_text_idempotent`.

### R2-G4 BS-1 cannot measure the CHANGELOG promise (design M4; readiness M6). PROPOSE FIX
**Fix:** corpus fully specified in the ticket (BS-1): secret alphabet, length 8-40, `&` placement, tail model (5 tail kinds), 7 shapes S1-S7 incl. the `=`-less query segment S3 and the grammar case S7, 30 made-up real-format lines (REAL), both paths, leak = a run of 4 secret characters in the output that occurs nowhere else in the input, hidden run = tail length minus the longest tail suffix that ends the output. Gates are exact per-shape predictions, not one loose ceiling; all numbers go to the lead as proposals with their basis (NEEDS LEAD 1).

### R2-G5 BS0 cell rule and hard stop ambiguous; who copies BS0 outputs (readiness M1). PROPOSE FIX
**Fix:** STOP rule by class (fb row whose base equals its expected; pb row whose base differs from its expected; ow row whose base equals its expected; any literal "on base" cell that differs; any named assert of L8/T1/W1 failing on base; a path difference where one string is written for two paths). The tool writes `tests/fixtures/p1d_a_base_rows.json`; the builder commits it unchanged; nobody copies by hand.

### R2-G6 corpus tool and base worktree named only (readiness M2). PROPOSE FIX
**Fix:** `tools/p1d_corpus.py` modes `--rows`, `--freeze-gate`, `--kind amp`, with inputs, output formats, exit codes; D3a-d and the other new names on base print `NEW_SURFACE: <name> missing`; base worktree commands with its own venv (no PYTHONPATH trick), the import-path line in the output proves which code ran.

### R2-G7 evidence paths and worktrees mixed; `qsubmit.sh` absent (readiness M3). PROPOSE FIX
**Fix:** one paths table: handover `/home/user/hadavin-sdk` (as found on disk; the machine profile's `/home/user/hadavin-sdk-handover/handover` does not exist), build `/home/user/build/P1d-a`, base `/home/user/build/P1d-a-base`, evidence snapshot `/home/user/build/EV-P1d-a-<sha7>/wt`, raw output under `handover/evidence/P1d-a/<sha7>/`. Heavy runs through `/home/user/build/heavy.sh <log> <cmd>` (exists; appends `exit=<rc>`), started as background jobs, at most 3 (ORDER 178).

### R2-G8 mutants lack exact edits and registration; A15 undecided; missing mutants (readiness M4; brief: R1 dependency). PROPOSE FIX
**Fix:** a "Code shape" block gives the exact new lines; each mutant names file, symbol, exact `old` -> `new` and the killer's assertion fragment (`ROW <id>`). Registration: `tests/p1d_a_mutants.py` builds `tools.mutation_runner.Mutant` entries and calls `run_mutants(..., forbid_skips=True)` in the `tests/stage_mutants.py` pattern. New mutants: A3d, A3e, A17, A18 (`~~~` body loses the flag; E1), A19 (info string loses the flag; new row I2), A20 (`#` dropped from the continuation look-ahead; Q10), A21 (white space dropped; Q11). **A15 decided EQUIVALENT** (removing the query lookbehind changes results only where the key is preceded by more than 40 key characters, where the plain entry refuses too; the only effect is more masking; no row pins it). **A22 (closer line verbatim) decided EQUIVALENT** (a closing fence line holds only markers and the container prefix `[ \t>*+\-0-9.)]`, never a name with a top-level domain). **Dependency:** the mutant run uses `forbid_skips` from the R1 runner PR (ORDER 181); P1d-a mutant evidence waits for R1 (merged, or the R1 branch, named in the evidence).

### R2-G9 card map unreadable (readiness M5; design N2). PROPOSE FIX
**Fix:** `test_card_masks_what_model_masks` uses an oracle that needs no internals: every EMAIL and HOSTNAME original in the model path's map is absent from `card.replace("[.]", ".")`. (A spy on `channel._seeded` would also work, because `redact_text` fills the map in place; not needed.)

### R2-G10 D3 "exact" test cannot see the defect (readiness M7). PROPOSE FIX
Valid: `_DOMAIN`'s lookbehind refuses `.example.com` after `.`. **Fix:** `test_no_link_outside_code_on_card` checks each text token outside code for four patterns: `_DOMAIN`, `_NON_ASCII_HOST`, `_PLACEHOLDER_DOT`, `_WIDE_DOTS`. The guarantee is relabelled "exact for the shape placeholder + `.` + name character; whether a renderer links it: UNVERIFIED".

### R2-G11 literal-form ambiguities (readiness M8). PROPOSE FIX
**Fix:** a "How to read a row" line: cells are Python string bodies; `\n`, `​` are escapes; `\|` in a cell is a plain `|` (Markdown table escape); where two paths are listed the string holds for both and BS-0 records each path (a difference is a STOP). Z rows written with `​`.

## Nits (PROPOSE FIX, one edit each)
- **R2-G12 (design N3)** `&amp;` query rows: Q7 (`&amp;user=bob` kept), Q8 (`&amp;` inside the secret, assertion row).
- **R2-G13 (design N4)** non-goals N4 (a query secret holding `&name=` is read as two fields, per the URL grammar) and N5 (a host written with wide dots is not recognised as a host on either path; it is defanged on the card; recognition is a redactor-grammar matter: NEEDS LEAD 2).
- **R2-G14 (design N5)** readers of stored summaries: fact R7 (FakeChannel.send, `_blocks`), BS-0 re-greps with a STOP if a new reader shows a stored summary to a person.
- **R2-G15 (design N6; readiness nits)** AST collector covers direct literal arguments only (stated; count printed); D3a-d and L10-L12 fail as `NEW_SURFACE`; link property run once on base (recorded, informative); must-run test named (`test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook`); time bound: the new test file at most 120 s, else numbers to the lead (no silent cut).
- **R2-G16 (design N1; readiness nit)** line references replaced by symbols in the ticket body.
- **R2-G17 (readiness nits)** D3 constant named `_PLACEHOLDER_DOT`; pb rows without a mutant are intentional (they pin unchanged behaviour); a typed `[.]` between name characters outside code is read as `.` before redaction (more masking; shown as `[.]` again after defang); `test_validate_harm.py[dblink-connect]` needs `PGUSER` (machine profile): a failure there counts as known only if identical on the base worktree; template fields re-checked.
- **R2-G18 (readiness nit "rows without mutants")** merged into G17.

---

## NEEDS LEAD
1. **BS-1 gates (proposals with basis, ORDER 165):** leaks 0 in S1-S6 and REAL, both paths; hidden run 0 in S1, S2, S4, S5; S3 hidden run exactly the `=`-less flag segments; S6 (plain form body) hidden run exactly the tail up to the first space, quote or `;`; REAL over-mask exactly the lines listed in the fixture; S7 (secret holding `&name=` in a query) reported only, expected to show the part after `&name=` (non-goal N4). Confirm or change.
2. **Wide-dot host names** (`db01。corp。example。com`) are not recognised as hosts on either path (read from the code, not run). Not P1d-a's class; proposed ledger row for P1d (redactor grammar). Also from reading only: the generic key pattern allows at most 40 key characters before the key word, so a key preceded by 41+ key characters is not masked by that entry; BS-0 runs it once (line INFO-K41) and reports.
3. **Stored requests render change** (rev 2 item 3, narrowed by R2-G1): `_blocks` reads a `[.]` between name characters outside code as `.` before redacting, so requests stored before the fix are masked too.

Closed since rev 2: H28a-b stay in P1d (ORDER 180 q392-1).
