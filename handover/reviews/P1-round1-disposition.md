# P1 round 1: disposition of the 43 findings

Ticket revised: `handover/tickets/P1.md` (revision 3). Author: Sonnet 5.5 drafting agent, 2026-11-05 (UTC). Findings: `P1-round1-adversarial.md` (A1-A23), `P1-round1-correctness.md` (C1-C20). Decisions applied: amendments A9 (F3, F4), A12, A13. Every finding was re-checked in code before the edit; all numbers are against PR #50 local head `748849c` (snapshot `/tmp/claude-0/-home-user/203f6188-e1bc-5eda-aaab-325ff81324d2/scratchpad/snap/pr50-748849c`). Verdict FIXED = the ticket text now says it. No finding was rejected outright; where part of a claim was not reproduced it is said in the line.

Counts: FIXED 39, REJECTED 0, ESCALATED 4 (A4, A16, A20, C20; each also has the recommended position written into the ticket marked PENDING LEAD).

Commands used to re-verify (read-only, `python3 -I` on the PR #50 fold files, `git show`, `grep`, `sha256sum`, `diff`): probes of `fold`, `fold_key`, `squeeze`, `allow_equal`, `has_mixed_script`, `html.unescape`; generator `build` filters re-run against `tools/data/confusables.txt`; line numbers of both snapshots, `ci.yml`, `defaults.py`, `invoicecheck.py`.

| id | severity | verdict | ticket section | one line |
|---|---|---|---|---|
| A1 | BLOCKER | FIXED | Interface, "The DENY key-set"; P1b Ze row | Identity is one string (Ze reads 3); both Ze readings only in the key-set; encoding, match rule and non-transitivity stated |
| A2 | BLOCKER | FIXED | Interface, "The DENY key-set" | Whole-text readings, at most 2x2x2 = 8 keys, `TEXTNORM_MAX_SCAN_KEYS`, `ScanKeysExceeded` fails closed; hostile test with 20,000 Eta; construction is mine (decision 3) |
| A3 | BLOCKER | FIXED | Interface, errors | `TextnormError(Exception)`, not `ValueError`; any error on a deny path means refuse; cap equals `MAX_REDACT_CHARS` (`defaults.py` lines 31-38) |
| A4 | MAJOR | ESCALATED | Interface, unidata pin; Decisions 2 | `check_pinned_unidata` and `TEXTNORM_PINNED_UNIDATA` in P1a, wiring in P6a; the CI env var `HADAVIN_REQUIRE_PINNED_UNIDATA` is a workflow edit only the lead can make |
| A5 | MAJOR | FIXED | Interface, P1b stored keys | Churn cost stated (every `fold1` key refused after P1b); callers that store keys must keep raw text or name who decides |
| A6 | MAJOR | FIXED | Interface, P1b stored keys; Tests (P1b) | `MalformedStoredKey`, keyword-only arguments, version text shown only if it matches the format, canary test through `stored=`, `args`, `__cause__`, `__context__`, `repr` |
| A7 | MAJOR | FIXED | P1b gap 1 row | Whole pipeline looped, `TEXTNORM_MAX_PASSES = 3`, `FoldNotConverged`; probe: U+0130 already folds to `i` on `748849c`, so the risk is in the proposed loop, not today's output |
| A8 | MAJOR | FIXED | P1b gap 2 row; Files (vendored data) | Table applies before the drop only for category Cn; exact count run with the generator's filters: 56 skipped entries, all Cn, none Mn/Cf/Co (677 to 733 entries, not about 1,700); test and diff review added |
| A9 | MAJOR | FIXED | Interface (FOLD_VERSION); Tests (P1a) | `TABLE_DIGEST` computed from the live table, compared to a literal in CI; table and `LOOKALIKES` read-only (`textnorm.py` lines 46-47 are plain dicts today) |
| A10 | MAJOR | FIXED | Tests (P1a), differential test | Row relations come from a stated principle with a source; statuses current, p1b (strict xfail), not_taken; disagreements decided in the ticket |
| A11 | MAJOR | FIXED | Interface, views | `is_empty_key`, `require_key`, `EmptyKey`; `fold_key("​")` and `squeeze("発票")` both return empty (probed); `stored_key` refuses empty |
| A12 | MAJOR | FIXED | "Intake `_f` call sites" | Every one of the 13 calls on 10 lines classified ALLOW or DENY; ALLOW sites use `allow_equal`, never `id_key(loose=True)`; Intake owner confirms (UNVERIFIED) |
| A13 | MAJOR | FIXED | P1b gap 7 row | After 8 rounds a still-changing text raises `UnresolvedEntities`; depth 9 is a refusal test; limit is a `defaults.py` constant; cap checked on raw input first |
| A14 | MAJOR | FIXED | Constants; Security; Tests (P1b) | Cache specified: entries and text-length bounds (byte bound computed), no cache above 256 characters, `clear_cache()`, eviction hammer test; byte-count race removed by design |
| A15 | MAJOR | FIXED | Interface, input rules; Constants | `type(x) is str` everywhere, cap on both arguments of every comparison, hostile `__eq__` probed (`allow_equal` returned EQUAL) and tested; quadratic worry NOT reproduced (20,000 descending marks 0.002 s, 262,144 marks 0.034 s), kept as a perf test run alone |
| A16 | MAJOR | ESCALATED | Mutation plan; Decisions 1 | Runner moved to its own tiny pull request "P1m" (verbatim from `748849c`: 295 + 105 lines); P1a no longer exports stored keys (they ship in P1b); lead decides id, tier and the wheel question |
| A17 | MAJOR | FIXED | Tests (P1a), golden test; P1b tests | Golden per view and `alg` frozen in a fixture, test forces an `alg` bump when a golden changes, frozen `fold1` literal for the loud-failure test, CI fails if the pinned interpreter is absent (when the env var is set) |
| A18 | MINOR | FIXED | Words; Interface, P1b stored keys | Digest called a pseudonym; optional salt gives HMAC and `hmac.compare_digest` |
| A19 | MINOR | FIXED | P1b gap 5 row | Exact categories that become a space (Cf, Cc, Zl, Zp, Co, fillers); Mn, Me, Cn, Cs removed without a space; NFD "résumé" row |
| A20 | MINOR | ESCALATED | Constants in `defaults.py`; Decisions 5 | All numbers now named in `defaults.py`; cap is `MAX_REDACT_CHARS`; the lead decides whether to lower it if the measured key-set time at the cap exceeds `REDACT_BUDGET_S` (6.0) |
| A21 | MINOR | FIXED | Tests (P1a), fail-before | Fail-before runs against a shim with the new names and old behaviour, so failures are assertions, not ImportError |
| A22 | MINOR | FIXED | Tests (P1a), known limit | Probe: Tamil and Runic beside Latin return False on `748849c`; hostile row and a docstring limit added |
| A23 | MINOR | FIXED | "Words used in this ticket" | key, digest, view, DENY, ALLOW, key-set, FOLD_VERSION defined once at the top |
| C1 | MAJOR | FIXED | Files, P1a change | `tests/test_no_hardcoded_values.py` ALLOWED entry for `guard/_confusables.py` added (header holds a URL; entry exists in `748849c` and not in `ce70eb5`, checked) |
| C2 | MAJOR | FIXED | P1b gap 4 row | Verified `squeeze` already equates U+2010; the map goes into `identity_key` and scan keys only; quote rows added |
| C3 | MAJOR | FIXED | Interface, key-set; P1b Ze row | Same fix as A1; the missing Ze row and its fail-before assertion added |
| C4 | MAJOR | FIXED | Tests (P1b), fail-before | Runs on the merged P1a head AND on `748849c` through a shim; each row fails on an assertion |
| C5 | MAJOR | FIXED | Tests (P1a), unit | Tests at `748849c` lines 869 and 1863 call `egress_text.check_text` (lines 873, 1869); listed as edited; new modules import only textnorm |
| C6 | MAJOR | FIXED | Files, vendored data | Data file stays out (P7n); test at line 2068 reads it with no skip, so it is changed to a visible skip and run by the evidence runner; CI integrity via `TABLE_DIGEST` |
| C7 | MAJOR | FIXED | Interface, input rules; fail-before | `fold(123)` already raises `TypeError` (probed), so that item is no longer a fail-before; `allow_equal(1, 1)` EQUAL and `has_mixed_script(b"abc")` AttributeError are fixed by `NotText` |
| C8 | MAJOR | FIXED | P1b gap 7 row; Constants | Property rewritten: cap on raw input and on NFKC-expanded length (`&#xFDFA;` is 8 characters, 18 after); `runmap.py` lines 139-156 cited as the model; hostile rows added |
| C9 | MAJOR | FIXED | Interface, key-set | Exact element list, fixed maximum, whole-text readings, order and `line_view` errors stated |
| C10 | MAJOR | FIXED | Header; Source; Tests; Mutation plan | Every number named for `748849c` (tests lines, 295 and 105 runner lines, 11-file manifest, 2,149-line mutants file); `2e8a28c` differences stated |
| C11 | MINOR | FIXED | Files | Full file list incl. `tests/textnorm_mutants.py`, runner files (P1m), gate entry, the four manifest files named, constants in `defaults.py` |
| C12 | MINOR | FIXED | Mutation plan | "Re-point the 27 mutants to the new text and test ids" added to P1a and again to P1b |
| C13 | MINOR | FIXED | Source; Intake table | `_unescape` 447-454, `_f` 465-481; 13 calls on 10 lines (recounted with grep) |
| C14 | MINOR | FIXED | Header fields; Reviewers | Template order kept at top level; "Extended review (no round cap): yes" stated; review file names follow the folder convention |
| C15 | MINOR | FIXED | Tests (P1a), mapping table | Claim kept but sourced: PR #49 file read with `git show origin/core/promote-refunds-r8:...` (cd62212, 131 lines; the finding said no PR #49 file was on disk in the snapshots, which is true of the snapshots, not of the remote branch); `mixed_script` row says both directions; `fold_key` role explained |
| C16 | MINOR | FIXED | Interface, input rules | Cap applies to `squeeze`, `same_person`, `allow_equal` (both arguments), `names_equal`; over cap on an ALLOW path means refuse |
| C17 | MINOR | FIXED | Interface, FOLD_VERSION | `tbl=` is the digest of the live table, `ucd=` the data version, file sha and data sha named separately; digest called a pseudonym |
| C18 | MINOR | FIXED | Tests (P1a); Evidence | Timing and thread tests marked `perf`, run alone (`ci.yml` lines 88-94) |
| C19 | MINOR | FIXED | Evidence | CI's exact commands used (`ruff check src tests demos`, `bandit -q -r src demos -ll`); 3.12 side stated as local only |
| C20 | MINOR | ESCALATED | Depends on; Decisions 4 and 7 | Downstream split written (P2d after P1a, P2a/P3b/P5a after P1b); P2a/P2d manifest claim withdrawn (memo-5 line 28 lists only P1); P8b must update the plan rows; the `dev_only`/identity declaration is assigned to P6b2 |

## ESCALATED (stays PENDING LEAD in the ticket)
1. A16: the mutation runner as its own pull request "P1m" (id, Tier B) versus inside P1a; the judge module ships in the wheel under `src/hadavin_sdk/testing/`.
2. A4: the pinned Python is 3.13 (`15.1.0`); the lead adds `HADAVIN_REQUIRE_PINNED_UNIDATA=1` to the CI job (workflow edit); P6a wires the strict check into the client profile.
3. A20: cap equals `MAX_REDACT_CHARS`; lower it in the one place if the measured key-set time at the cap exceeds `REDACT_BUDGET_S`.
4. C20: update the plan's Depends-on rows for P2a, P2d, P3b, P5a after the P1a/P1b split; P0e answers whether P2a stores names.
Also flagged for review round 2 (not escalated): the key-set construction (2 x 2 x 2 = 8 keys) is the drafting agent's proposal.
