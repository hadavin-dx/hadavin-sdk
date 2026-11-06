# P5c round 2, adversarial review
Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

R2 ADVERSARIAL review of P5c rev 2 (<repo>/handover/tickets/P5c.md). Verdict: no Blocker found. 3 Majors, 4 Minors, 2 Nits. Orders 6-24 were not read. I read only the parts of the ticket and common brief I needed, plus the cited code on disk.

Cite status: the disk `src/` is `ce70eb5`. `redact.py` line numbers match the ticket (:82, :107, :335, :353, :444, :447). The `agent_loop.py` cites match (:284, :295, :349, :367). `runmap.py` lines are about 47 lower on disk, as the ticket says. Those cites were not re-checked against `124258b`.

| id | sev | ticket line | problem | fix |
|---|---|---|---|---|
| R2-ADV-1 | Major | 199-200 (item 5 ii, "named group for the keyword") | The BANKACCT pattern is a single regex whose group 1 is the digits (`_ACCT_DIGITS`, `redact.py:335` and :87). `_mask` (`redact.py:929`) takes `original = next(g for g in m.groups() if g is not None)`. A keyword group placed before the digits becomes the first non-None group. The keyword text would then be masked and replaced as the "original", and the digits left in clear. That is a redaction leak, and a builder following the text literally will hit it. The ticket says nothing about it. The `redact_many` and fold-scan path shares `_mask` (:925-956), so it breaks too. | Say how the keyword is read without shifting `groups()`. Options: a lookbehind-free named group placed AFTER the digits, or `m.group(0)` re-matched with `_ACCT_STRONG` inside `_bank_context` (no new group). Add a row that asserts the stored original equals the digits, e.g. `Account No: 12345678` gives `Account No: <BANKACCT_1>`. ACC-2 only checks the label, so mutants M15 and M16 would not catch this leak. |
| R2-ADV-2 | Major | 180-183 vs 242, 382, 383 (T1-17) | Contradiction. Item 3 lists `restore` in `guard/redactor.py` as a `_map_of` caller, but item 8 makes `restore` take a plain map, not a session. Also, T1-17 sits in P5c-1 and pins "exactly" the `agent_loop.py` callers (toolbox call, `_run_tool`, `prepare_output`, `storable`). P5c-1 changes no call site (line 101), and `agent_loop` first uses the session in P5c-3. As written, T1-17 either fails in P5c-1 or is vacuous. | Remove `restore` from the caller list. Split T1-17: in P5c-1 assert only `redactor.py` callers, then extend the list in P5c-3, with the AST test updated in that PR. |
| R2-ADV-3 | Major | 414 (T2-15c), 174 | The behaviour of a benign collision is a builder decision. `check` refuses with `self_check_failed` when a session original of 4 or more characters appears in the text as written. T2-15c says "the result is written down" and the rate is UNVERIFIED. The two outcomes are a run that goes to a person (`self_check_failed`) or a wrapper that tolerates it. They differ in safety, and the ticket does not pick one. This is a decision left to guess on the redaction path. Names and e-mail local parts of 4+ characters inside longer words are realistic. | State the required outcome (refuse, since fail-closed), what the operator sees, and make T2-15c assert it. If refusal would be too noisy, define "occurs as written" (word boundary or not) in the ticket. |
| R2-ADV-4 | Minor | 190-195, 369 (fingerprint) | `MASKING_SOURCES` is limited to `guard/*` files, but the masking caps and budget (`defaults.MAX_REDACT_CHARS`, `REDACT_BUDGET_S`) and `STORED_KINDS` live in `defaults.py`. Changing them changes what reaches the model, or what is put back, with no new gate run. T1-02's AST walk covers only `hadavin_sdk.guard` modules. Separately, `redactor.py` is itself in the list, so P5c-4 (and any P5c-3 edit to `redactor.py`) changes the fingerprint again and every agent needs another gate run. The Rollback section says only that P5c-1 changes the hash once. | Either add `defaults.py`, or hash the relevant constants into the fingerprint. Say in Rollback and the CHANGELOG that P5c-1, P5c-3 and P5c-4 each may change the fingerprint, or land `restore` into `redactor.py` before the fingerprint is first frozen. |
| R2-ADV-5 | Minor | 213 (item 6) | `Registry.config_hash(agent_id)` (`registry.py:105`) has only `self.config`. It has no redactor object. "ALWAYS adds `redactor.fingerprint`" does not say where the fingerprint comes from: a built redactor handed to `Registry`, or a lookup from the `redactor` kind. This is a signature change in a hot file (P4c, P5b3). T1-04 can pass either way. | Name the source and the signature change, and say how P4c's edit to the same function is merged. |
| R2-ADV-6 | Minor | 563, 301, 575 (PHONE removal) | `config.py:256` rejects any `stored_kinds` entry not in `defaults.STORED_KINDS`. After PHONE is removed, an existing config that lists PHONE fails to load. This is an operator-visible break that the CHANGELOG list does not mention. `restore`'s `ValueError` on a non-subset has the same effect at run time. T4-07 does not cover it. | Decide whether a config listing PHONE is refused at load or silently narrowed. Add a row and a CHANGELOG line. |
| R2-ADV-7 | Minor | 220-221 (b), 226 | Content blocks in messages that are not text (an image block's base64 `data`, a `tool_use` input) are also `str` leaves. Masking and checking them with PHONE and digit patterns can corrupt the payload, or hit the cap or the time budget. Only bytes documents get the (a) decode and signature refusal. | State that only text-typed leaves are masked, or that non-text blocks are refused (`unsupported_input`), and add a row. |
| R2-ADV-8 | Minor | 229 (e) | An `outbound` event is written with `write_intent`, but no outcome event follows. Other uses pair an intent with an outcome (`audit/protocol.py:19-25`). I did not check whether reconcile or verification flags unpaired intents. The CHANGELOG says "roughly doubles the audit rows"; with one intent and no outcome it would not. | Confirm that an intent with no outcome is acceptable to the audit readers. Otherwise write an outcome after the call, which also gives a failure record. UNVERIFIED either way. |
| R2-ADV-9 | Nit | 212 | `[A-Z][^\W\d_]+` also matches upper-case letters, so `Dear MARY` masks and `Dear JohnSmith` masks whole. The ticket says "a name part", which is slightly wider than stated. | Pin the intended width with a row, or say so. |
| R2-ADV-10 | Nit | 472, 388 | The row count is right: 16 + 13 + 16 + 25 + 9 = 79, and 80 with T2-P. T4-04 is counted in P5c-4's 9 but lives in `test_c1_acceptance.py`, so `test_p5c4_putback.py` has 8 rows plus ACC-12b, not 9. | Reword the count line. |

Template check: all 17 fields are present, in order (lines 100-577).

Verified (read or counted by me):
- Mutant count: P5c-1 17, P5c-2 13, P5c-3 9, P5c-4 5, total 44, each with a named killer.
- ACC-2: 59 parametrised cases and 5 negative cases both add up. The suffix list has 8 forms, matching `_ACCT_WORD` at `redact.py:82`.
- Pattern order: BANKACCT (:333, :340) comes before ACCOUNTID (:353), so the `Account Number: <12 digits>` to BANKACCT claim is plausible. `_mask` gates BANKACCT on `bank_near or _bank_context` (:939-941), and the single path is `_bank_context` (:107). Without bank context the match is returned unmasked and ACCOUNTID then catches 12 digits.
- Code cites: NAME at `redact.py:444` and :447, and the current `[A-Z][a-z]+` form. `agent_loop.py` :284, :295, :349, :367, :425. `tools.py:1178`. `evals.py:63`, `evals.py:73`, `extract.py:47`, `judge.py:72`, `k1b/loop.py:94`. `defaults.py:108-120`, with PHONE at :120. `runmap.py:181` PHONE grammar (disk line). `models.py:199` `inputs_hash` is optional.
- `AuditSink.write_intent` exists and raises `AuditUnavailable`.
- The ticket's account of what is wrong with main (G2, G3, G4) holds for the `.chat(` sites I grepped.

Not checked (UNVERIFIED):
- All test rows, mutants and fail-before claims (hand arguments, as the ticket states).
- The `124258b` versions of `runmap.py` and `agent_loop.py` (disk is `ce70eb5`).
- C1a branch lines.
- P1, P2d, P4b1, P4c and P5a names.
- The counts of 14, 21 and 42 files and lines.
- That 11 "golden" paths are strict UTF-8.
- Whether `tools.py` importing `redactor.py` makes an import cycle.
- Python probes (a) and (b).
- `hashing.sha256_hex`, `lockin` table lines, `backends/table.py` lines, and `cli.py` :120, :150, :221.
- Whether any audit reader flags unpaired intents.
- Reconcile behaviour for the new `llm` domain.
- Whether `demos/ask-your-data` can use the wrapper.
- Orders 6-24 and `amendments.md` (not read; this review is limited to the ticket and the cited code).
