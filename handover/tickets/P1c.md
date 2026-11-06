# Package ticket P1c: redactor gaps from the library comparison (base64 decoded view, whole internal host names, the bare number as a decided property, a permanent corpus test). DRAFT revision 1

Revision 1, written 2026-11-06 after lead order 64 (stamped about 15:05 UTC / 20:35 IST; this container's clock is wrong, so no exact writing time). Author: Opus ticket author, `egm:egm-brainstorm` (brief `handover/egm/hadavin-sdk/p1c/concepts_brief.md`) then `egm:egm-draft`. The draft skill's `resources/execution_instructions.md` is NOT present in this plugin (`ls .../skills/egm-draft/` shows no `resources/`); I followed the SKILL.md steps in AUTO mode, with no section gates, and wrote straight to this ticket rather than to `design_draft.md`. Neither step had a sub-agent tool, so NO Goldfish has read this yet. The lead's worker runs the Goldfish review and the resolve next. Specification: lead order 64 items 1-6. Text only: no code, no PR, no suite run. Marker: CODE-LAST v1.
Cites: core `origin/main` = `db17c53`, re-read for this revision (`git show origin/main:<path>`). Line numbers are for information only and are never used as test literals. "UNVERIFIED" means I did not read it or could not run it. "PENDING LEAD" means a proposal the lead has not decided. Values in this ticket are placeholders; the only key-shaped literal allowed anywhere in the package is the AWS documentation example key.

## RUNG TABLE (R448; one page)
| component | need | rung tried | evidence (source, date) | what only our code gives | verdict |
|---|---|---|---|---|---|
| base64 decoding | strict base64 and base64url decode | 5 standard tool: stdlib `base64` (`b64decode(..., validate=True)`, `urlsafe_b64decode`) | Python 3.13 stdlib; my probe 2026-11-06: an invalid length raises `binascii.Error`, and a SHA-256 hex digest fails UTF-8 after decoding | nothing: the stdlib does all of it | CUT-TO-CONFIG+GLUE (stdlib, no own decoder) |
| decoded view inside `redact_text` | find a value that only the decoded form shows; mask the WHOLE token; same run map | 5 library: Presidio (default and extended), GLiNER, LLM Guard, scrubadub, detect-secrets, gitleaks | `evidence/redactor-eval/lead-reading-1.md` lines 3-7 (2026-11-06): no library beats ours; Presidio extended still misses 2 of the 3 base64 rows and alters 7 of 14 must-keep lines. Raw `evidence-1.md` and the `t_*.py` runners are NOT in the repository (UNVERIFIED beyond the lead's reading). TOOLS.md T-119 | guarantee "redaction before the model". The one property no tool gives: when our chokepoint finds a value in the decoded form, it either masks the whole encoded token with the run's own placeholders or refuses the text (fails closed), and it does this inside the same bounded call. No library has a decoded view feeding our map. Reproduction (R448): run the evidence's Presidio-extended runner on hostile rows 25-27, giving 2 of 3 MISS; then the same rows on P1c's `redact_text`, giving 3 FULL | KEEP-CODE, ONLY for the bounded, fail-closed wiring (about 30 lines and 4 constants); decoding stays stdlib |
| whole-hostname masking | an internal host name masked whole, with no client-domain tail left | 1 studio code (the existing HOSTNAME pattern) | `guard/redact.py:387-393`; my probe: must-mask rows 26 and 27 go from PARTIAL to FULL, and no must-keep line changes | a pattern edit in existing code, no new component | CUT-TO-CONFIG+GLUE (edit one pattern) |
| bare-number property | written down and pinned | none needed | order 64 item 4 | none (a docstring paragraph and one test) | CUT (no code) |
| look-alike rows | 2 rows owned by a later package | none | order 64 item 2 | none (2 strict-xfail rows) | CUT (no code) |
| corpus test | permanent span-level score | 1 studio code (`score_common.py` rule) | `evidence/redactor-eval/score_common.py` | none: test data plus the copied rule | CUT-TO-CONFIG+GLUE (test only) |
| second-layer detector | a model-based PII layer | 5 library | order 64 item 6; Presidio alters 7 of 14 must-keep lines | none | CUT (out of scope) |
Count for the KEEP-CODE row (R448's 80 percent rule): the row lists 4 needs (decode, find, whole-token mask, fail closed within the bounds). The stdlib covers 1 of the 4 (25 percent), so the 80 percent cut does not apply. It is a guarantee path in any case (redaction), so the cut would not apply to it anyway.

## Template fields
- **Package id and name:** P1c, "redactor gaps from the library comparison". One pull request on branch `core/P1c`, from current origin/main once P1b has merged. **Name clash:** the id P1c was once used for the dropped stored-key API (order 7(3); `tickets/P5a.md` says "P1c is out of v1"). This is a different package. PENDING LEAD 5: keep the new id and add one note line to P5a's build notes.
- **Path class:** redaction AND security. **Extended review (no round cap): yes**, for the plan review AND the result review (order 64).
- **Depends on (merged first):** P1a (PR 63, fold3) and P1b (it builds on P1a). Order 64 says the build starts AFTER P1b merges. **Honest note:** P1c's own code uses nothing from P1a or P1b. Only the 2 look-alike xfail rows refer to them, and by my reading the wrong package is named there (PENDING LEAD 3). P2d (P2d-1 changes `redact_text` and `redact.py`): P1c builds before P2d-1 in the chain (order 50 item 1 lists P1b, then P3a/P4d, P2a-1, P2d-1), so P2d-1 rebases onto P1c. That is a conflict in `runmap.py`, at the `redact_text` sites only. P5c BN-24 (`kept_host_suffixes`, `tickets/P5c.md:1030`) is NOT on main (`git grep kept_host_suffixes origin/main -- src` finds nothing), so its row is a strict xfail (PENDING LEAD 4). Merge order (order 20 item 4) is unchanged; P1c joins it after P1b.
- **Problem in plain words:** Hadavin replaces personal data and secrets with placeholders before any text reaches a model. All callers go through one function, `redact_text` (`guard/runmap.py:464`). We measured it against free libraries on our own test texts. None did better. But our function still lets 6 of 30 attack texts through, and on 2 of 48 must-hide lines it leaves part of a value visible. Three of the six are an e-mail address, a cloud key and a card number written in base64 (a common way to pack binary data as letters and digits). Two use look-alike letters from another alphabet; a later package fixes those. One is a plain number with no word next to it; we decide on purpose NOT to hide that. The two partial lines are internal host names (for example a name ending in `.corp.<domain>`): today the client's own domain at the end stays visible.
- **Source of the code and what is NOT taken:** no code is copied. The test texts come from `evidence/redactor-eval/corpus.json` (30 attack texts, 48 must-hide lines, 14 must-keep lines). The last two groups equal `tests/warden_port/privacy_corpus.py` (`MASKED`, `KEPT` at `:12`, `:65-80`). The scoring rule is copied from `evidence/redactor-eval/score_common.py` `fold`/`classify`. Not taken: the `run_tool` harness, `spans_mask`, and any library.
- **Target module and path in `src/hadavin_sdk/`:** `guard/runmap.py`: the new private helper `_b64_masks` and one call in `redact_text`. `guard/redact.py`: the HOSTNAME pattern at `:391` and the module docstring. `defaults.py`: one new block.
- **Interface (names, argument and return types, errors):** no public change. `redact_text(text, mapping, neutralise=None) -> str` keeps its signature. It now also masks base64 tokens whose decoded text holds a value, and can raise `InputTooLarge` for too many such tokens. New private `_b64_masks(out: str, current: dict[str, str], cache, started: float) -> tuple[str, dict[str, str]]`. **Behaviour, exactly:**
  1. **Where it runs.** In `redact_text`, after the loop over views (`runmap.py:507-518`) and before `out = _clean(out)` (`:519`), inside the same `try`. It runs on EVERY text: it is NOT behind the `scan` gate (`:491-492`), because a base64 token is plain ASCII with none of `\ % &`, and that gate would skip it. It reads the current output `out`, so tokens already masked are gone.
  2. **What is a candidate.** A maximal run of either the standard alphabet `[A-Za-z0-9+/]` or the URL-safe alphabet `[A-Za-z0-9_-]`, plus up to 2 `=`, not touching another alphabet character on either side. A run that holds both `+` or `/` AND `-` or `_` is rejected. The run's length, without the `=`, is from `B64_MIN_TOKEN_CHARS` (16) to `B64_MAX_TOKEN_CHARS` (8192). Missing padding is added when the length mod 4 is 2 or 3. When it is 1, the run is rejected.
  3. **What is accepted.** A strict decode (`validate=True`) followed by `bytes.decode("utf-8")` (strict). Then at least `B64_MIN_PRINTABLE_PERCENT` (90) percent of the characters must satisfy `isprintable()` or be one of `\t\n\r`. Only `binascii.Error` and `UnicodeDecodeError` are caught, and only to mean "not a candidate". Any other exception propagates to the existing `except Exception` at `:522-523` (`InputTooLarge`/`TooDeep` re-raised as they are, `:520-521`), which raises `RedactionError`: the call fails closed and nothing is sent.
  4. **What is masked.** For each accepted token, in text order, call `redact(decoded, mapping=current, _cache=cache)`, the plain pattern redactor at depth 1. If its map grew, or it placed a placeholder, replace EVERY copy of the token in `out` with the placeholders that the decoded result holds, joined in their order. No decoded character is ever emitted. Continue with the grown map. Secret kinds stay unstored as today (`runmap.py:27-29` `STORED_KINDS` allowlist).
  5. **Bounds, each with its reason.**
     - Depth 1: the decoded text is never searched for base64 again, and gets no NFKC or escape view. Each extra level multiplies the work, and calling `redact_text` again would be recursion.
     - No recursion: `_b64_masks` calls the plain `redact`, never `redact_text`.
     - Maximum token length 8192: bounds the work per token. It sits above the base64 of a 4096-bit PEM private key, which is how Kubernetes stores Secret values. I estimate that at about 4.4K characters (UNVERIFIED; the builder measures it). What happens to a longer token is PENDING LEAD 2.
     - At most `B64_MAX_DECODED_PER_TEXT` (32) accepted tokens per text. The 33rd raises `InputTooLarge`. Each accepted token costs one `redact` pass. This is the same fail-closed shape as `MAX_DECODED_MASKS` (`:423`, `:441-442`). Rejected candidates are not counted: they cost one linear decode each, and the text cap already bounds their total.
     - The existing `REDACT_BUDGET_S` check (`:509`) runs before each `redact` call.
  6. **HOSTNAME.** After a private suffix (`corp|lan|intranet|intra|localdomain|home\.arpa`, `redact.py:391`), the match goes on through up to 8 further DNS labels. It does not end in front of `(` and does not end on a dot. `internal|local` keep their guard `(?!\.\w|\()`. `_KEPT_HOST` (`:809-811`) is unchanged.
  7. **ACCEPTED PROPERTY**, added to `guard/redact.py`'s module docstring under "What this is not" (`:15-18`). That docstring is the redactor's spec on this tree; `guard/` has no README. Text: "Accepted property (lead order 64 item 4): a bare number in free prose with no account, bank or card word near it (for example `ref <8 digits> paid`) is NOT masked. It could be an invoice number, a reference or an account number, and masking it would alter the evidence lines we must keep. Money and account values are typed fields, masked by field, not guessed in prose. This is a decision, not a gap."
- **Neutral default / working alternative:** stdlib only; there is no external dependency. Alternative for the encoded case: a library recogniser (measured worse, rung table). Written outline with a trigger: hex and base32 views, and a depth-2 decode, get added if a client's sample text carries values encoded that way (v1.1 rows).
- **Files to create, change, delete:**
  - `src/hadavin_sdk/guard/runmap.py`: `_b64_masks` and its call (item 1).
  - `src/hadavin_sdk/guard/redact.py`: the HOSTNAME pattern and the docstring (items 6 and 7).
  - `src/hadavin_sdk/defaults.py`: a new block with `B64_MIN_TOKEN_CHARS`, `B64_MAX_TOKEN_CHARS`, `B64_MAX_DECODED_PER_TEXT`, `B64_MIN_PRINTABLE_PERCENT` (order 20 item 5: own block).
  - `tests/data/redactor_corpus.json` (new): the studio's own corpus, labelled "made-up data, no real values". A value that looks like a key is stored as a list of parts that the loader joins; only the AWS documentation key appears whole.
  - `tests/test_redactor_corpus.py`, `tests/test_redact_b64_view.py`, `tests/test_redact_hostname_whole.py`, `tests/test_redactor_accepted_properties.py` (all new).
  - `tests/redact_b64_mutants.py` (new; the P1m runner, not collected by pytest).
  - `CHANGELOG.md`: one line for the new masking and one for the property.
  - Nothing is deleted.
- **Existing core code reused (checked):** `redact`, `RedactionResult` (`redact.py:862-881`); `RedactionError`, `InputTooLarge` (`runmap.py:38`, `:42`); the `try/except` of `redact_text` (`:487-523`); `REDACT_BUDGET_S` and `MAX_REDACT_CHARS` (`defaults.py:49`, `:38`); `_held` (`runmap.py:417`) for "placed a placeholder"; the `privacy_corpus.py` lists. Not checked (no reason to touch them for this package): hashing, k1b/atomic, stats, evals, store/memory, tests/contracts.
- **Security and least-privilege notes:** no identity, no rights, no secrets, no new config. Personal data: the corpus is made up. The builder runs gitleaks on `tests/data/redactor_corpus.json` BEFORE the first commit (order 62 item 1 lesson). The view reaches only `redact_text` callers. The public `guard.redact` (`guard/__init__.py:3`) and `redact_many` do NOT get it, the same as with the existing views (`runmap.py:483-484`); that goes in the CHANGELOG line.
- **Stated limits (decisions, each pinned by a test; these are not deferrals):**
  - L1: depth 1, so base64 of base64 is not read (B8).
  - L2: with strict UTF-8, one invalid byte in front of the value hides it (B7; PENDING LEAD 1 offers a fix).
  - L3: a token over 8192 characters (B4; PENDING LEAD 2).
  - L4: no NFKC or escape view on the decoded text (B23).
  - L5: hex, base32 and compressed forms are not read.
  - L6: `redact()` and `redact_many` have no view.
  - Each limit gets a v1.1 row with the trigger "before any pilot with real client data", the same trigger as order 14 item 1.
- **Tests (123 rows; 3 strict xfail):**
  - **`test_redactor_corpus.py` (92 rows),** scored by the copied `classify` (after the NFKC and zero-width fold: value gone = FULL; a leftover of 5 or more characters = PARTIAL):
    - Attack texts (30): 27 rows assert FULL. 2 strict xfail (`reason="P1c: look-alike letters, owner P2d-1 fold scan; order 64 item 2"`, rows 14 and 15). 1 row asserts MISS under the test name `test_accepted_property_bare_number_not_masked_order64_item4` (row 6).
    - Must-hide lines (48): all assert FULL.
    - Must-keep lines (14): all assert the line comes back byte-identical.
    - **FAIL-BEFORE:** on `db17c53`, attack rows 25-27 and must-hide rows 26-27 fail (my probe gave the old scores: 24/0/6, 46/2/0, 14/0, the same as the lead's).
  - **`test_redact_b64_view.py` (23 rows):**
    - B1: an e-mail in base64 is masked whole (fail-before).
    - B2: base64url, no padding.
    - B3: a 15-character token is not decoded (spy on the decoder).
    - B4: a token of 8193 characters is not decoded (spy; L3).
    - B5: 33 accepted tokens raise `InputTooLarge`.
    - B6: invalid padding or length mod 4 = 1: text unchanged, no error.
    - B7: invalid UTF-8 (0xFF in front of an e-mail): `redact` is not called on it (spy; L2).
    - B8: base64 of base64: exactly one decode per token (spy; L1).
    - B9: mixed alphabets are rejected.
    - B10: decoded text under 90 percent printable is rejected.
    - B11: a planted `RuntimeError` in the decoder raises `RedactionError`.
    - B12: a planted error in the decoded `redact` call raises `RedactionError`.
    - B13: whole token: no 5-character piece of the token, and no word of the decoded remainder, is left in the output.
    - B14: base64 of a harmless sentence: the token is kept byte-identical.
    - B15: a hex digest, a git sha and a UUID are kept.
    - B16 (hostile): a text at `MAX_REDACT_CHARS` holding one huge token finishes within `REDACT_BUDGET_S` or raises `InputTooLarge`.
    - B17 (hostile): 10,000 candidates that fail to decode, same bound as B16.
    - B18: a plain ASCII text with no `\ % &` still gets the view (fail-before).
    - B19: base64 of a placeholder-shaped string never comes back as a real placeholder.
    - B20: the same token twice gets one placeholder.
    - B21: the clock is stubbed past the budget inside the loop, giving `InputTooLarge`.
    - B22: base64 of a made-up PEM block (header built from parts, body random at test time) is masked.
    - B23: base64 of a full-width e-mail is pinned as the outcome L4 gives (the builder records it).
  - **`test_redact_hostname_whole.py` (5 rows):**
    - H1: `billing-db.prod.corp.<domain>` is masked whole (fail-before).
    - H2: `smb://files.lan.<domain>/share`: the host goes, the path stays.
    - H3: 8 trailing labels are all masked.
    - H4: a stack-frame line `at <pkg>.corp.<Cls>.run(<file>:12)` is pinned. It is masked further than today (today the mask ends at `corp`); this cost is stated in the CHANGELOG.
    - H5: strict xfail `reason="P5c BN-24: kept_host_suffixes"`: with the suffix listed, the name is kept.
  - **`test_redactor_accepted_properties.py` (3 rows):**
    - A1: the bare number unchanged, in several prose forms.
    - A2: the same number after `account number` is masked (the edge of the property).
    - A3: the module docstring holds the "Accepted property (lead order 64 item 4)" sentence.
- **Mutation plan (14 mutants, each with its named killer; P1m runner):**
  - M1: no maximum length. Killed by B4.
  - M2: minimum length 16 becomes 4. Killed by B3.
  - M3: skips the fail-closed path (broad `except` then `continue`). Killed by B11 and B12.
  - M4: decodes twice. Killed by B8.
  - M5: masks only the decoded span (emits the redacted decoded text). Killed by B13.
  - M6: decodes non-UTF-8 (`errors="replace"`). Killed by B7.
  - M7: printable check removed. Killed by B10.
  - M8: view put behind the `scan` gate. Killed by B18.
  - M9: candidate cap removed. Killed by B5.
  - M10: budget check removed from the loop. Killed by B21.
  - M11: trailing-label group removed. Killed by H1 and must-hide rows 26-27.
  - M12: the `(` guard removed. Killed by H4. If it does not change H4's outcome, the builder writes the equivalence argument and the reviewers judge it.
  - M13: BANKACCT context check removed. Killed by A1 and the must-keep `Invoice #` line.
  - M14: mixed alphabet accepted. Killed by B9.
- **Evidence commands (exact; raw output to `handover/evidence/P1c/`):**
  - `uv run --all-extras --group test pytest tests/test_redactor_corpus.py tests/test_redact_b64_view.py tests/test_redact_hostname_whole.py tests/test_redactor_accepted_properties.py -q > evidence-tests.txt 2>&1; echo rc=$?`
  - The same 4 files on `db17c53` (fail-before), saved to `evidence-fail-before.txt`.
  - The full suite once on the final head.
  - `uv run python tools/mutation_runner.py tests/redact_b64_mutants.py > evidence-mutants.txt 2>&1`
  - The B16 and B17 timings on their own, saved to `evidence-hostile.txt`.
  - `gitleaks detect --no-git --source tests/data` saved to `evidence-gitleaks.txt`.
  - ruff check, ruff format --check, bandit -ll.
  - The P1m runner's command line is UNVERIFIED against its merged CLI; the builder copies it from P1m's README.
- **Reviewers:** for the plan, the lead's worker runs the Goldfish review, then resolve. For the result, a correctness reviewer and an adversarial reviewer, both fresh `egm:*` agents, with the diff, this ticket and the evidence only. Security path, NO round cap.
- **Done =** 123 rows pass as stated (120 pass, 3 strict xfail); 14 of 14 mutants killed (or an equivalence argument accepted by a reviewer); fail-before shown; and all gates green: tests, ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit, gitleaks.
- **Rollback:** tag `pre-P1c`. No migration and no stored data. The output change (more masking) can be reverted by reverting the PR.

## Relays and PENDING LEAD (recommendation first)
- **PL1, strict UTF-8 (order's text, kept as written) versus decoding with replacement.** The alternative decodes with replacement, counts U+FFFD as not printable, and keeps the 90 percent rule. It closes L2, the one-byte bypass. My probe: `'�'.isprintable()` is True, so the count must be explicit. **Recommend the replacement decode.** If accepted, M6 becomes "U+FFFD counted as printable" and B7 flips to "masked".
- **PL2, token over 8192 characters.** Skip it and state L3 (recommended: large base64 blobs such as images are common in tool results, and refusing them blocks real work), or refuse the text.
- **PL3, the look-alike xfail rows are owned by P2d-1, not P1b.** `tickets/P1.md` never names `redact_text`. P2d-1 is the fold scan in `redact()` for a new look-alike value (its problem paragraph and probe p2). Also, P1b merges before P1c exists, so P1b cannot remove the marks. **Recommend naming P2d-1.**
- **PL4, `kept_host_suffixes` is not on main.** H5 stays a strict xfail named P5c. **Relay to P5c BN-24:** an empty default will mask 2 of the 14 must-keep lines (`*.svc.cluster.local`, `*.compute.internal`, `privacy_corpus.py:68-69`). P5c must move those lines in `tests/data/redactor_corpus.json` and say so in its PR.
- **PL5, the id clash** (Package field above).
- **Draft reconciliation with the brief (SKILL.md step 6.1):** no contradiction. Two additions: B23/L4 (the decoded text gets no NFKC view) and H4 (the stack-frame cost). Neither changes the architecture.
