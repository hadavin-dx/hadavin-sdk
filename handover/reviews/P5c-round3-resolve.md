# P5c round 3 resolve report (egm:egm-resolve, auto mode)

Status: resolved (categorised). The ticket is NOT edited here. Round 3 had 0 Blocker and 9 Majors (adversarial 6, correctness 3), so order 20 item 6 allows NO round 4. Every fix below is a numbered build note BN-1 to BN-18, which wins over the revision 3 text.
Target: `handover/tickets/P5c.md` revision 3 (770 lines, full file read; path class REDACTION and MONEY-ADJACENT, Tier A).
Inputs: `P5c-round3-adversarial.md` (R3-ADV-1..14: 0 Blocker, 6 Major, 7 Minor, 1 Nit) and `P5c-round3-correctness.md` (R3-COR-1..10: 0 Blocker, 3 Major, 5 Minor, 2 Nit). 24 finding ids. Severity is taken from the tables and never changed here.
Gate: the skill's "wait for the user" step is skipped (auto mode, per the brief). This file replaces the skill's default file name `goldfish_review_report.md`. Three items are owner-rule decisions (money or redaction). They are NEEDS LEAD 34, 35 and 36, each with options and a recommendation. Each build note states the default the builder takes meanwhile, and what changes if the lead picks another option.
Facts: see "Facts I checked myself". Honest note: first, below.

## Honest note (what I did NOT check, first)
- I ran no pytest, no mutant, no `uv`, no install, no network call and no git write. I ran three read-only `python3 -I` probe scripts from a scratch folder, which import `<repo>/src` by path (Python 3.13.18; I ran `python3 --version` myself). Probe 1 ran the real BANKACCT patterns against a hand-copied `_ACCT_STRONG`. Probe 2 monkeypatched `_bank_context` in-process and ran the real `runmap.redact_text`. These probes are not evidence. The builder's runs are.
- The disk tree is not `124258b`. I read `redact.py`, `runmap.py`, `agent_loop.py`, `evals.py`, `judge.py`, `producers.py`, `defaults.py`, `config.py` and `tests/test_k5_producers.py` on disk. Every line number below is a DISK line. The `runmap.py` lines at `124258b` are about 47 higher (the ticket says so; I did not run `git show`).
- Code from P4c-2 (`_RunEnded`, the `Runtime` check), P4b1-b (`MeteredLLM`), P2d-2 and P5b3 does not exist yet. BN-9, BN-11 and BN-12 place new `except` clauses on today's `agent_loop.py`, and the builder re-places them on the rebased file.
- I did not check whether `extract.py` catches a wrapper refusal broadly (relevant to BN-9's "other call sites"), or which existing tests rely on ACCOUNTID being PUT BACK (4 files name ACCOUNTID: `tests/warden_port/test_redaction.py`, `test_redaction_bank.py`, `privacy_corpus.py`, `tests/test_k5_classes.py`).
- I did not measure any false-abstain rate (R3-ADV-2). No ceiling exists in the ticket. NEEDS LEAD 35 proposes one.
- I did not run either reviewer's "fails before" claims, or T3-09, T3-12 or T3-03 against real code.
- NEEDS LEAD 34, 35 and 36 are not decided by me. The build-note defaults are my recommendations.

## Facts I checked myself (disk lines; "probe" marks a run)
- **`_sweep` (`redact.py:1202-1217`)** returns None for an original under 3 characters. It returns "every copy" only for a SECRET kind with 4 or more characters. It returns None for an all-digit identifier under 6 characters or a `_COMMON` word (`:1158-1187`: prod, admin, test and others). Otherwise it returns "standalone". So a 3-character SECRET-kind value falls through to the identifier rule, and a 3-character non-common identifier IS swept standalone. Revision 3's "4 or more characters" (ticket :216) is wrong both ways (R3-ADV-1 TRUE).
- **BANKACCT patterns (`redact.py:333-349`)**: probe 1 printed `groups == 1` for both. For every probed form, group 1 is the digits. `_bank_context` (`:107-113`) already treats `m.group(0)[:4] == "bank"` as context.
- **Probe 1, `_ACCT_STRONG` exactly as in BN-5, over the real pattern 1.** Strong (True): `Account No:`, `Account_No:`, `Account-No:`, `Account<nbsp>No:`, `Account No:` + line break, `"account_no": "<d>"`, `\"acct\":\"<d>\"`, `*Acct No:* <d>`, `A/C # <d>`, `acc. no. <d>`, `Acct = <d>`, `Account Number - <d>`, dashed `4-4` and grouped `4 4` digits. Weak (False): `Account:`, `accounts`, `acc:`, `Acc.`, `Account <d>`, `Account (no):`, `Account (number):`.
- **Probe 2, end to end with the clause patched in:** `Account No: <8 d>` becomes `Account No: <BANKACCT_1>`. The same holds over a line break and for the JSON key. The map holds one BANKACCT entry. Without the patch (base), these forms all stay in clear. `Account: <8 d>` stays in clear on base AND patched (R3-ADV-4 TRUE). `Account No: <12 d>` is ACCOUNTID on base and BANKACCT patched (ACC-12b holds). A bare `id <12 d>` is ACCOUNTID in both.
- **Existing pins touched by NEEDS LEAD 34:**
  - `tests/warden_port/test_redaction_bank.py:240-241` pins `account <8 d>` unmasked with no bank word.
  - `:289-292` (W2) pins an account past the 100-character window unmasked.
  - `:296-298` pins `account <12 d> assumed role` as ACCOUNTID (cloud audit-log lines).
- **Chat site (`agent_loop.py:424-439`)** catches only `ProviderError`. `handle` (`:325`) has no outer `try`. So a `RedactionError` raised from `self.llm.chat` leaves `handle` uncaught after `_to(run, WORKING)` (`:350`) (R3-COR-3 TRUE).
- **Map saves (`agent_loop.py`)**: `:363`, `:379`, `:475`, `:498`, `:648` (only when `validate_proposal` is set). None follows a chat (R3-COR-7 TRUE). The model's tool input IS masked into `rmap` at `:489` and saved at `:498`.
- **`rmap`** is a local of `handle` (`:352`). Its last uses are inside `handle` (`:468-502`, and `_submit`'s `mapping` at `:645-648`). `RunMap(mapping or {})` copies the caller's dict. So clearing the seed at the end of `handle` breaks nothing on today's tree (R3-ADV-3).
- **Gate (`evals.py:58-70`)**: `redact_untrusted(doc.decode("utf-8", "replace"), {})` runs once per case, BEFORE the `for _ in range(k)` loop, and every `RedactionError` becomes `ConfigError`. `redact_untrusted` takes a `dict` (`runmap.py:298`). `judge.qualify(judge.JudgeDetector(llm, ...), path)` (`evals.py:109`) runs after the case loop, outside any per-case scope. `qualify` (`judge.py:99-108`) calls `injection_check` per case, and `check` calls `self.llm.chat` (`judge.py:72`) (R3-COR-1 and R3-COR-2 TRUE).
- **`tests/test_k5_producers.py:47-53`** requires each `PRODUCERS` row's function to CALL a name in its set (`_called_names`: `Name.id` or `Attribute.attr`). The gate row is `("eval case document", "evals.py", "gate", {"redact_untrusted"})` (`producers.py:40`), and the judge row is `{"redact_text"}` (`:28`). So both rows go red if P5c-3 removes those calls with no replacement token (R3-COR-2(a) TRUE).
- **Reassigned model in tests:** `rt.llm.chat =` at `test_p1a_fixes.py:35`, `test_p5p6_followups.py:102`, `test_p5_llm.py:56` and `:168`; `rt.llm =` at `test_k5_tools.py:608` (5 sites, R3-COR-4 TRUE).
- **`GUARD_STOP_REASONS`** (`agent_loop.py:83-85`) lists proposal catches only. `document_too_large` is not in it. Its comment (`:80-82`) says a failure to produce a proposal carries no `caught_by`.
- **`Config.evidence.stored_kinds`** defaults to `defaults.STORED_KINDS` (`config.py:215`), and `:256` refuses any kind outside it. ACCOUNTID has the grammar `[0-9]{12}` (`runmap.py:169`).
- **Judge comment** is at `judge.py:69-70` on disk (R3-COR-9).

## Banner for the ticket (placed under the title line, word for word)
> **Build notes win.** Revision 3 is frozen text (no round 4: round 3 had 9 Majors). Where a build note BN-1 to BN-18 (from `handover/reviews/P5c-round3-resolve.md`, copied into the section "Build notes (round 3)" at the end of this ticket) differs from the revision 3 text, the build note wins. NEEDS LEAD 34, 35 and 36 (money and redaction) are open: until the lead answers, the builder takes the default each build note names. The CHANGELOG sections are history, not instructions. Find every code cite by its name at the rebased head, not by its line number (BN-17).

## Decisions (one category per finding id)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Major) | PROPOSE FIX | TRUE (Facts). `check` calls `_sweep` itself, with no length rule of its own. T2-15 boundary cases and mutant M56. **BN-1.** |
| R3-ADV-2 (Major) | ESCALATE (redaction-path owner decision, NEEDS LEAD 35; default (a)) | TRUE as an availability attack. It fails closed (never a leak), and a benign case exists too: a prompt and a document that share an identifier. Hostile row T2-20 and a false-abstain ceiling. **BN-2.** |
| R3-ADV-3 (Major) | PROPOSE FIX | TRUE. `close()` empties the seeded `RunMap` and drops it. G6 is closed for the run loop's map. What stays outside (the caller's `mapping`, the store) is stated. Row T1-06b, mutant M57. **BN-3.** |
| R3-ADV-4 (Major) | ESCALATE (money-path owner decision, NEEDS LEAD 34; default (c)) | TRUE (probe 2: `Account: <8 d>` in clear on base and after revision 3). Options and existing pins are in NEEDS LEAD 34. ACC-2-NEG no longer blesses the leak. **BN-4.** |
| R3-ADV-5 (Major) | PROPOSE FIX (the DOTALL part CONTESTED by probe: the pattern has no tail, so DOTALL is not needed) | The exact `_ACCT_STRONG` text is given. ACC-2 gains separator, line-break, JSON, markdown and digit-shape cases. Mutant M58. **BN-5.** |
| R3-ADV-6 (Major) | ESCALATE (money-path owner decision, NEEDS LEAD 36; default (b)) | TRUE. A bare 12-digit bank number is stored and put back. Default: ACCOUNTID leaves the DEFAULT stored kinds, and an agent config may opt in. Row T4-13, mutant M70. **BN-6.** |
| R3-ADV-7 (Minor) | PROPOSE FIX | ACC-2 gains a case where context comes from another clause (a masked bank code before the keyword). A new row ACC-GROUPS asserts that each BANKACCT pattern has exactly 1 group (probe: 1). **BN-5.** |
| R3-ADV-8 (Minor) | PROPOSE FIX | TRUE. `tests/p5c_mutants.py` joins the Files lists of P5c-2, P5c-3 and P5c-4. **BN-13.** |
| R3-ADV-9 (Minor) | PROPOSE FIX (the `_RunEnded` part CONTESTED: it is P4c-2's code and has P4c's own mutants) | 5 mutants M65-M69 with named killers. M39 stays a placeholder under PENDING LEAD 11, stated in the Done line. **BN-14.** |
| R3-ADV-10 (Minor) | PROPOSE FIX | T2-P becomes a recorded measurement, outside the Done gate. **BN-15.** |
| R3-ADV-11 (Minor) | PROPOSE FIX | `_ACCT_WORD` and `_ACCT_STRONG` are built from one suffix string. Row ACC-TABLE. **BN-5.** |
| R3-ADV-12 (Minor) | PROPOSE FIX | Each file is hashed with its name, then the list is hashed. A bytecode-only install stays fail-closed (stated). **BN-16.** |
| R3-ADV-13 (Minor) | PROPOSE FIX (no new design) | The cites are re-read by name at the rebased head and the result review re-checks them. **BN-17.** |
| R3-ADV-14 (Nit) | DECLINE (the T2-15(d) wording part is fixed inside BN-1) | Frozen header and count wording; changes no builder action. |
| R3-COR-1 (Major) | PROPOSE FIX | TRUE. Each judge qualification case runs in its own run (code identity "gate"), with the text escaped. A refusal fails that case, and audit down stops the gate. Row T3-10c, mutant M59. **BN-7.** |
| R3-COR-2 (Major) | PROPOSE FIX | (a) Exact call `llm.redactor.mask(...)`, with the `PRODUCERS` and `CHOKE_FAMILY` rows set. (b) ONE run per CASE (k calls inside it), and the escape stays before the k loop. (c) `except RedactorRefusal` before the `ConfigError` branch. Mutants M60, M65. **BN-8.** |
| R3-COR-3 (Major) | PROPOSE FIX | TRUE. The chat block catches `AuditUnavailable` and `RedactionError` (the second goes to `_redaction_failed`). Row T3-13b, mutant M61. **BN-9.** |
| R3-COR-4 (Minor) | PROPOSE FIX | `Runtime.llm` is read-only and `MaskedLLM` refuses attribute assignment. The 5 test sites build their fake with the behaviour. Rows T2-19 and T3-06c, mutants M62 and M63. **BN-10.** |
| R3-COR-5 (Minor) | PROPOSE FIX | The NFKC second pass is cited by name. **BN-17.** |
| R3-COR-6 (Minor) | PROPOSE FIX | T3-05 asserts a subsequence. Where the handler sits is fixed. `unsupported_input` stays OUT of `GUARD_STOP_REASONS`. **BN-11.** |
| R3-COR-7 (Minor) | PROPOSE FIX | The run loop saves the map after every chat. Row T3-19, mutant M64. **BN-12.** |
| R3-COR-8 (Minor) | PROPOSE FIX | The `_ACCT_STRONG` body is given (BN-5). `Account (no):` and `Account (number):` join the weak cases (BN-4). **BN-5.** |
| R3-COR-9 (Nit) | PROPOSE FIX (one cite) | `judge.py:69-70` on disk. `python3 --version` = 3.13.18 (re-run by me). **BN-17.** |
| R3-COR-10 (Nit) | DECLINE | Frozen text. The Words section already defines the three terms (ticket :100-109). |

## Build notes (round 3) - to be copied into the ticket as the section "Build notes (round 3)"

**BN-1. `check` calls `_sweep` itself, with no length rule of its own (R3-ADV-1).**
- **Rule.** `check(text, session)` refuses `self_check_failed` exactly when the sweep would have changed `text`. The sweep here means `_Redactor.sweep`, the same split on placeholder tokens and the same `_sweep(placeholder, original)` / `_replace_standalone`, run over the session's map.
  - The builder may implement it by running that sweep on the text and comparing: any difference is a refusal.
  - `check` has NO threshold of its own. The ticket's "of 4 or more characters" (:216) is deleted.
  - The `forged_mark` half is unchanged and runs first.
- What this means, from `redact.py:1202-1217`:
  - an original under 3 characters: never;
  - a SECRET kind with 4 or more characters: any copy;
  - a 3-character SECRET-kind value: standalone copies only (it falls through to the identifier rule);
  - an all-digit identifier under 6 characters, or a `_COMMON` word: never;
  - any other identifier: standalone copies only.
- **T2-15 gains 5 cases.** (e) to (g) give ONE inner call and no refusal; (h) and (i) are the boundaries. Each uses a stubbed masker:
  - (e) a session TENANT `prod`, standalone in a leaf: one inner call;
  - (f) a 5-digit identifier, standalone: one inner call;
  - (g) a 2-character identifier: one inner call;
  - (h) a 3-character, non-common identifier, standalone: `self_check_failed`;
  - (i) a 3-character SECRET-kind value inside a longer word: one inner call.
- T2-15 (d) reads "a SECRET-kind value held in the session (never stored)".
- **Mutant M56** (P5c-2): `check` uses its own rule `len(original) >= 4` in place of `_sweep`. Killers: T2-15 (e) (`prod` is refused) and (h) (the 3-character value is not refused).

**BN-2. A document value equal to a word of the prompt or schema (R3-ADV-2; NEEDS LEAD 35, default (a)).**
- Default (a): the config check stays as written. It refuses, which fails closed and never leaks.
- New hostile row **T2-20** `test_planted_config_word_refused_not_sent`:
  - a made-up document line `tenant_id=<a standalone word of the system prompt>` (not a `_COMMON` word) puts that word in the session;
  - the next call gives `self_check_failed`, zero inner calls and no `outbound` row;
  - through the run loop, the run ends NEEDS_PERSON `redaction_error` (BN-9).
- **False-abstain ceiling (new, rule false-abstain-reporting).** The builder runs the 10 golden inputs and every repository fixture document through the wrapper with each fixture agent's prompt, and writes the count of `self_check_failed` refusals to `P5c-2-false-abstain.txt`.
  - The ceiling is 0 on that set. Any refusal there fails the build, and the builder names the shared value.
  - The live rate is unknown, and the README says so in the "not masked" list item (g): "a document value that equals a word of the agent's prompt or schema stops the run for a person".
- If the lead answers (b): add `RunCtx.trust_config(system, tools, output_schema)`.
  - It can be called once per run, before the first chat. The run loop and the gate call it with their registry-built config; the judge registers its constant `PROMPT`/`SCHEMA`.
  - `check` skips a config leaf that is byte-identical (system) or equal by canonical-JSON sha256 (tools, schema) to the trusted one. A caller-built `extract` `system` is still checked in full.
  - Adds one row (T2-20 then asserts ONE inner call) and one mutant.
- If the lead answers (c): drop the `self_check_failed` half of the config check (`forged_mark` stays), and cut T1-15 and M12.

**BN-3. What `close()` does to the seeded map (R3-ADV-3).**
- `MaskSession.close()` sets `_closed`, then empties the seed (`self._map.clear()` and `self._map.redact_cache.clear()`), then sets `self._map = None`.
- It runs in `handle`'s `finally`, after the last map save. On today's tree no use of `rmap` follows the `with` block (Facts). The builder re-checks this on the P4c-2-rebased file and records it in the evidence.
- **G6 is closed for the run loop's map:** after the run, the originals are gone from that object.
- What stays, stated in Security notes ("The plain run map") and the README "where personal data is kept":
  - the caller's own `mapping` dict (`handle` copies it: `RunMap(mapping or {})`);
  - the stored kinds in the store.
- Ticket :180 reads "a session that cannot be copied and whose run map is emptied when the run ends". Problem item 3 reads "The masking state of a run can be copied, and it outlives the run."
- **Row T1-06b** `test_close_empties_the_seed_map`: a seeded `RunMap` holding 2 made-up entries is empty after `close()`, and `redact_cache` is empty.
- **Mutant M57** (P5c-1): `close()` leaves the seed untouched. Killer: T1-06b.

**BN-4. Weak keyword plus digits (R3-ADV-4; NEEDS LEAD 34, default (c)).**
- Default (c): a WEAK form (`account`, `accounts`, `acc`, `acc.` with no suffix) also counts as bank context, EXCEPT when the digit group, without separators, has exactly 12 digits.
  - Then BANKACCT leaves the match, and ACCOUNTID (`redact.py:353`) masks it as today, so cloud audit lines `account <12 d> assumed role` keep their kind (pin `test_redaction_bank.py:296-298` unchanged).
  - The clause becomes `_ACCT_STRONG.match(m.string, m.start(), m.start(1)) is not None or len(re.sub(r"\D", "", m.group(1))) != 12`.
  - Nothing with an account keyword and 6-17 digits then reaches the model in clear.
- **ACC-2-NEG is renamed ACC-2-WEAK** (FB). It has 11 cases:
  - each of the 4 weak forms with 8 made-up digits: masked BANKACCT, digits absent, keyword kept;
  - each of the 4 weak forms with 12 digits: ACCOUNTID;
  - `Account: <5 digits>`: not masked (under 6);
  - `Account (no): <8 d>` and `Account (number): <8 d>`: masked (R3-COR-8).
  - M16 keeps a killer: a bare `account` made strong turns the 12-digit cases into BANKACCT.
- **Mutant M71** (P5c-1): the "not 12 digits" carve removed. Killer: ACC-2-WEAK's 12-digit cases.
- **Existing pins that change (listed in the evidence, never weakened):** `test_redaction_bank.py:240-241` (`account <8 d>` becomes masked) and `:289-292` (W2: an 8-digit account past the window becomes masked). README item (b) reads "plain account numbers with no account keyword".
- If the lead answers (b): rewrite ACC-2-NEG as strict-xfail record ACC-2-WEAK-LEAK (5 cases plus the two parenthesised cases, which still kills M16 when it XPASSes) and drop M71.
  - V4 gains "a weak keyword (`account`, `accounts`, `acc`) plus 6-17 digits".
  - README (b) names that form, and the owner-visible limits file lists it.
  - Strict xfails go to 5.
- If the lead answers (a): drop the 12-digit carve and M71. The pins `:296-298` also change (cloud ids written `account <12 d>` become BANKACCT, never put back).

**BN-5. The exact `_ACCT_STRONG`, one source table, shape cases (R3-ADV-5, R3-ADV-7, R3-ADV-11, R3-COR-8).**
- In `redact.py`, replacing the literal at `:82` with the same bytes built from parts:
  ```
  _ACCT_SUFFIX = r"(?:number|num\.?|nbr\.?|no\.?|#)"
  _ACCT_WORD = r"(?:accounts?|acct\.?|acc\.?|a/c)(?:[ _\-\xa0]?" + _ACCT_SUFFIX + r")?"
  _ACCT_STRONG = re.compile(
      r"(?i)(?:bank[ _\-]?)?(?:accounts?[ _\-\xa0]?" + _ACCT_SUFFIX
      + r"|acct\.?|a/c|acc\.?[ _\-\xa0]?" + _ACCT_SUFFIX + r")"
  )
  ```
- **No tail and no DOTALL.** `Pattern.match(string, pos, endpos)` anchors at `pos` and does not need to reach `endpos`. So the separator text (`_BANK_KV`: quotes, marks, `:`, `=`, `#`, a dash, one line break) is never matched by `_ACCT_STRONG`. Probe 1 and probe 2 (Facts) show the line-break and JSON-key forms read as strong.
- **ACC-2 gains 13 cases (59 to 72)**, each with the three assertions (digits absent; keyword kept; one BANKACCT entry equal to the digits):
  - separator between keyword and suffix: `_`, `-`, nbsp (3);
  - `Account No:` + line break; `"account_no": "<d>"`; `\"acct\":\"<d>\"`; `*Acct No:* <d>`; `Acct = <d>`; `A/C # <d>`; `Account Number - <d>` (7);
  - digits `4-4` dashed and `4 4` grouped (2);
  - **context from another clause** (R3-ADV-7): `<BANKCODE_1> Account No: <d>`. Under M50 the keyword becomes the value and the digits stay, so "digits absent" fails. This is the Blocker's own failure mode (1).
- **New row ACC-TABLE** (P5c-1 patterns):
  - `_ACCT_WORD` equals the `:82` string byte for byte;
  - each of the 59 table strings fullmatches `_ACCT_WORD` and matches `_ACCT_STRONG`;
  - each weak form fullmatches `_ACCT_WORD` and does not match `_ACCT_STRONG`.
- **New row ACC-GROUPS:** each `PATTERNS` entry labelled BANKACCT has `pattern.groups == 1`.
- **Mutant M58** (P5c-1): `_ACCT_STRONG` drops `[ _\-\xa0]?`. Killer: ACC-2's `_`, `-` and nbsp cases.
- The reviewer's DOTALL mutant is not added: with no `.` in the pattern it is an equivalent mutant.

**BN-6. Bare 12-digit numbers (R3-ADV-6; NEEDS LEAD 36, default (b)).**
- Default (b): `defaults.py` gains `DEFAULT_STORED_KINDS` = `STORED_KINDS` minus ACCOUNTID (11 kinds).
  - `Config.evidence.stored_kinds` defaults to it (`config.py:215`).
  - `STORED_KINDS` stays the 12-kind allowed set (T4-11 unchanged), so a config that names ACCOUNTID loads (`:256`).
  - `DEFAULT_STORED_KINDS` joins `MASKING_VALUES` (BN-16).
- A cloud-operation agent writes `evidence.stored_kinds` with ACCOUNTID, and its config hash shows it.
- **Row T4-13** `test_bare_12_digits_not_stored_by_default`: with the default config, a bare made-up 12-digit number is masked ACCOUNTID and absent from the stored map. With `stored_kinds` naming ACCOUNTID it is stored.
- **Mutant M70** (P5c-4): the default includes ACCOUNTID. Killer: T4-13.
- The builder lists every existing test and fixture that relied on an ACCOUNTID put-back (4 files name ACCOUNTID; reliance UNVERIFIED) and adds the field there. The check is never loosened.
- Security notes (b) and the CHANGELOG line read "a bare 12-digit number is masked; it is stored and put back only for an agent whose config lists ACCOUNTID".
- If the lead answers (a): T4-13 and M70 drop, and the README and a hostile row ACC-12c pin "a bare 12-digit bank number is stored and can be put back into a plan".

**BN-7. Judge qualification runs inside runs (R3-COR-1).**
- `judge.qualify` keeps its signature. For case `i` it opens `with judge.llm.run(f"gate-judge-{tag}-{i}", "gate") as ctx:`. `tag` is one `uuid4().hex` per call of `qualify`.
- It escapes the raw golden text with `judge.llm.redactor.mask(case["text"], ctx.session, untrusted=True)`, then calls `injection_check`.
- Results:
  - `RedactionError` (now re-raised by `injection_check`): the case FAILS (the docstring's "a judge error fails its case");
  - `AuditUnavailable`: propagates, so the gate stops and is never GREEN (BN-8, T3-10b).
- `JudgeDetector.check` takes the run's session for its own re-mask through a new read-only `MaskedLLM.current()` (it returns the `RunCtx`, and raises `SessionClosed` outside a run). It calls `self.llm.redactor.mask(text, self.llm.current().session, untrusted=False)`. So the judge row in `producers.py:28` becomes `{"mask"}` and the AST guard stays real (see BN-8).
- **Row T3-10c** `test_gate_judge_qualification_runs_in_runs`: a gate with an `llm_judge` completes, makes one run per judge case, and raises no `SessionClosed`. A judge case holding a forged `<EMAIL_9>` arrives escaped.
- **Mutant M59** (P5c-3): `qualify` calls without a run. Killer: T3-10c.

**BN-8. The gate's exact calls (R3-COR-2).**
- **(b) One run per CASE.** Each case opens `with llm.run(f"gate-{tag}-{case_id}", "gate") as ctx:`, and its k calls run inside it. The document is decoded and escaped ONCE, before the k loop, as on disk. T3-10's name ("fresh per case") stands. Ticket :348's per-(case, k) run id is void.
- **(a) The call:** `doc = llm.redactor.mask(decode_document(raw), ctx.session, untrusted=True).encode("utf-8")`. `runmap.redact_untrusted` is no longer called in `gate`.
- **(c) Order of handlers:** `except RedactorRefusal as exc` with `exc.code == "unsupported_input"` comes FIRST. The case then counts as FAILED with reason `unsupported_input` (`case_passes = 0`, no model call, all k counted failed). Every other `RedactionError` keeps the `ConfigError` branch (exit 2).
- **`producers.py` and `tests/test_k5_producers.py` (T3-17):**
  - the gate row (`:40`) becomes `frozenset({"mask"})`, and so does the judge row (`:28`) (BN-7);
  - `CHOKE_FAMILY` gains `"mask": "guard/redactor.py"`, so `test_every_redaction_function_reaches_the_one_choke_point` proves `mask` reaches `redact_text`;
  - `REDACTORS` gains `"mask"`.
- **Mutants:** M60 (P5c-3): `RedactorRefusal` falls into the `ConfigError` branch. Killer: T3-05b, which then sees exit 2, not a FAILED case. M65 is in BN-14.

**BN-9. Wrapper refusals at the chat call (R3-COR-3).**
- The chat block (`agent_loop.py:424-439`) catches, in this order:
  - `AuditUnavailable`: NEEDS_PERSON `audit_unavailable`;
  - `RedactionError`, `RedactorRefusal` included: `self._redaction_failed(run, cited)`;
  - then `ProviderError` as today.
- **Row T3-13b** `test_wrapper_refusal_at_chat_needs_person`: parametrised over `forged_mark`, `self_check_failed` and `unsupported_input` (non-text block). The run ends NEEDS_PERSON `redaction_error`, is not left in WORKING, and makes zero inner calls for that step.
- **Mutant M61** (P5c-3): the `RedactionError` clause removed. Killer: T3-13b.

**BN-10. No reassignment around the wrapper (R3-COR-4).**
- `Runtime` keeps the model in `self._llm` and exposes a read-only `llm` property (no setter).
- `MaskedLLM` has `__slots__` and a `__setattr__` that raises `AttributeError` once `__init__` is done.
- The 5 sites (Facts) build their fake with the wanted behaviour before `Runtime` (or patch the raw model object they hold). They are never rewritten to patch around the wrapper.
- Evidence gains `git grep -n -E 'rt\.llm( |\.chat) ?=' HEAD -- tests demos`, which must print nothing at the head.
- **Row T2-19** `test_wrapper_attributes_read_only` (P5c-2): assigning `chat`, `inner` or `redactor` raises. **Row T3-06c** `test_runtime_llm_read_only` (P5c-3).
- **Mutants:** M62 (P5c-2): the `__setattr__` refusal removed. Killer: T2-19. M63 (P5c-3): `llm` a plain attribute. Killer: T3-06c.

**BN-11. Strict decode placement (R3-COR-6).**
- In `handle`, `decode_document(document)` runs in its own `try` right before the `redact_untrusted` `try` (`:366`). `except RedactorRefusal` gives `_note(... "unsupported_input")` and then `_abstain(... "unsupported_input")`. The generic `except Exception` (`:376`) never sees it.
- `unsupported_input` is NOT added to `GUARD_STOP_REASONS`. It is a failure to produce a proposal, like `document_too_large` (`:80-85`), so it has no `caught_by`.
- T3-05 asserts the events in order as a subsequence: `received`, then the `guard`/`document` `stopped` event. The `state` WORKING event lies between them (`test_s5_runtime.py:137`).

**BN-12. Map saved after each chat (R3-COR-7).**
- Right after `self.llm.chat(...)` returns, and before the reply is used, the run loop calls `self._save_map(run, rmap)` in its own `try`. A failure goes to `_evidence_unavailable(run, cited, "map")`.
- **Row T3-19** `test_map_saved_after_each_chat`: `validate_proposal` is None and the model's first reply text holds a raw made-up e-mail. After the second call, the stored map holds the EMAIL entry the wrapper minted.
- **Mutant M64** (P5c-3): the post-chat save removed. Killer: T3-19.

**BN-13. Mutant file in every sub-PR (R3-ADV-8).** The Files lists of P5c-2, P5c-3 and P5c-4 each add "extend `tests/p5c_mutants.py` with this PR's mutants". P5c-2's "No other file" reads "No other `src/` file".

**BN-14. Mutants for unguarded rows (R3-ADV-9).**
- M65 (P5c-3): the gate decodes with `replace`. Killer: T3-05b.
- M66 (P5c-3): `extract` decodes with `replace`. Killer: T3-05's `extract` case (T3-03e).
- M67 (P5c-3): `cli gate` writes `qualified.jsonl` after `AuditUnavailable`. Killer: T3-10b.
- M68 (P5c-3): `_screen` drops the `AuditUnavailable` catch. Killer: T3-12b.
- M69 (P5c-3): k1b's thread runs `work` without `copy_context()`. Killer: T3-11b.
- `_RunEnded` is P4c-2's code with P4c's own mutants. A broken end through it fails T3-12 and T3-12b here.
- M39's killer T4-02 is written once the P2d-2 marker form is read (PENDING LEAD 11). The Done line reads "every listed mutant killed, M39 included once T4-02 exists; if the marker form is still unknown at P5c-4, the lead decides before merge".

**BN-15. T2-P is a measurement (R3-ADV-10).** T2-P runs alone and writes its time to `P5c-2-perf.txt`. It has no pass/fail budget and is not counted in the Done gate or in the row totals. A budget number becomes a gate only by a lead order.

**BN-16. Fingerprint formula (R3-ADV-12).**
- `FINGERPRINT = "regex@" + REGEX_VERSION + ":" + FOLD_VERSION + ":" + sha256(b"".join(rel_path.encode("utf-8") + b"\0" + sha256(lf_bytes).digest() for rel_path in MASKING_SOURCES) + b"\0" + repr(MASKING_VALUES).encode("utf-8")).hexdigest()[:16]`.
- `rel_path` is the path under `hadavin_sdk/`, with `/`.
- `MASKING_VALUES` gains `DEFAULT_STORED_KINDS` (BN-6) after `STORED_KINDS`.
- A missing `.py` source (bytecode-only install) keeps the fail-closed import error. The CHANGELOG states "installs must ship sources".
- T1-02 adds: swapping the contents of two listed files changes the fingerprint.

**BN-17. Cites by name (R3-ADV-13, R3-COR-5, R3-COR-9).**
- At P5c-1's base the builder re-reads by name every `runmap.py`, `agent_loop.py`, `tools.py`, `evals.py` and `k1b` cite in the ticket, and writes the "name -> line at base" table into the evidence. The result review checks that table at the PR head.
- The NAME-DECOMPOSED argument cites "the second pass over the canonical view in `redact_text`". It is at `:452-471` on disk, so at about `:499-518` at `124258b` (offset only, UNVERIFIED).
- The judge comment is `judge.py:69-70`.

**BN-18. Counts after BN-1 to BN-17 (defaults of NEEDS LEAD 34, 35, 36).**
- Rows (each counted once in its own sub-PR):
  - P5c-1 redactor 17 (+T1-06b);
  - P5c-1 patterns 16 (+ACC-TABLE, ACC-GROUPS; ACC-2-NEG renamed ACC-2-WEAK);
  - P5c-2 19 (+T2-19, T2-20);
  - P5c-3 36 (+T3-06c, T3-10c, T3-13b, T3-19);
  - P5c-4 13 (+T4-13).
  - **101 rows**, plus the T2-P measurement. Strict xfail: 4 (unchanged).
  - ACC-2: 72 cases. ACC-2-WEAK: 11 cases. T2-15: 9 cases (a-i).
- Mutants:
  - P5c-1 22 (+M57, M58, M71);
  - P5c-2 17 (+M56, M62);
  - P5c-3 21 (+M59, M60, M61, M63, M64, M65, M66, M67, M68, M69);
  - P5c-4 6 (+M70).
  - **66 mutants** (M56-M71 new). Done's "50 of 50" reads "66 of 66".
- Other answers:
  - NEEDS LEAD 34 (b): 101 rows, 5 strict xfail, 65 mutants.
  - NEEDS LEAD 36 (a): 101 rows (ACC-12c replaces T4-13), 65 mutants.
  - NEEDS LEAD 35 (b): +1 mutant. (c): -1 row (T1-15) and -1 mutant (M12).

## Positions
- **Three ESCALATEs, no CONTEST of a Major.** R3-ADV-2, -4 and -6 are true. Each trades a leak or a put-back of a money number against cloud-agent use or availability. The owner's rules (mask before the model; least privilege) make that his call. The defaults chosen meanwhile are the masking-side options. Each says exactly what reverts.
- **BN-4 default (c) over (a).** (a) masks more, but turns every CloudTrail-style `account <12 d>` into a never-put-back BANKACCT (pin `:296-298`). (c) closes every keyworded 6-17 digit case and keeps 12-digit ids in their current kind. ADV-6 (BN-6) then decides separately whether such ids are put back.
- **BN-5 contests only DOTALL, by probe.** The pattern is given in full. A tail-free `match` with `endpos` needs no `.`, and the probe shows the line-break and JSON forms read as strong.
- **BN-7 adds one public method (`MaskedLLM.current()`).** The alternative was dropping the judge row from the producers guard, which would weaken a guard test (studio rule). One read-only method keeps the AST guard real.
- **BN-8 chooses one run per case, not per (case, k).** It changes the fewest lines (the escape stays before the k loop, as on disk) and matches T3-10's name. The k calls of one case see identical masked bodies anyway.
- **Order 8 (cut surface):** BN-15 cuts a gate that could not fail, and BN-5's mutant for DOTALL is not added. The added rows and mutants each guard a real line, and no new kind or module is added.

## Couplings
- BN-1 and BN-2: T2-20 relies on BN-1's rule (a non-common standalone word). Under NEEDS LEAD 35 (b), T2-20 flips to one inner call.
- BN-2, BN-9 and T3-13b: through the run loop, a config refusal ends `redaction_error` only because BN-9 catches it at the chat call.
- BN-3 and BN-12: the last map save (BN-12, and `:498`/`:648`) happens before `close()` empties the seed. The builder keeps that order.
- BN-4 and BN-6: under (c), `account <12 d>` stays ACCOUNTID, so BN-6 decides whether it is put back. Under BN-4 (a), BN-6 matters only for bare numbers.
- BN-4 and BN-5: ACC-2-WEAK and ACC-TABLE share the weak-form list. M16 is killed by ACC-2-WEAK's 12-digit cases under (c), and by the XPASS under (b).
- BN-6 and BN-16: `DEFAULT_STORED_KINDS` is a masking value, so it changes the fingerprint at P5c-4 (one gate run per agent, already stated in Rollback).
- BN-7, BN-8 and P4c: the gate's audit sink (PENDING LEAD 29) receives the judge runs' `outbound` rows too.
- BN-10 and P4b1-b: tests still read `rt.llm.inner.calls`. Only assignment is refused.
- BN-11 and P4c-2: the `try` placement is re-done on the P4c-2-rebased `handle`.
- To P6a (BN-12 of `P6a-round3-resolve.md`): P6a's T5 rows stop before `Runtime`, so BN-10's read-only `llm` does not touch them.
- To the lead's `handover/owner-visible-limits.md` (order 24 item 39): NEEDS LEAD 34 (b), 35 (a) and 36 (a) each add one owner-visible line if chosen.

## PENDING LEAD (continuing the ticket's numbering after 33)
- **34. NEEDS LEAD (money path): an account keyword without a suffix plus 6-17 digits (R3-ADV-4).**
  - Default meanwhile: (c).
  - (a) Every keyword form counts as bank context. It is the most masking, but cloud ids written `account <12 d>` become BANKACCT and are never put back (pins `:296-298` change).
  - (b) Keep revision 3. `Account: <8 d>` (an invoice supplier account) goes to the model in clear. It is recorded as a strict xfail, a V4 clause, a README item and an owner-visible limit.
  - (c) RECOMMENDED: the weak forms count except at exactly 12 digits, which stay ACCOUNTID. Nothing keyworded of 6-17 digits goes in clear. Pins `:240-241` and `:289-292` change.
  - Confidence 70%. Reversible until P5c-1 merges, and after that with one gate run per agent.
- **35. NEEDS LEAD (redaction path): a document value equal to a prompt or schema word refuses every call (R3-ADV-2).**
  - Default meanwhile: (a).
  - (a) RECOMMENDED: keep the check (fails closed), add hostile row T2-20, and set the ceiling at 0 refusals over the golden inputs and fixtures. The README states it.
  - (b) Trusted-config exemption (`trust_config`, one method, one mutant). It closes the denial and keeps the check for caller-built `extract` config.
  - (c) Drop the `self_check_failed` half on config. It is the smallest, but a caller-built `extract` `system` holding a document value is then sent.
  - Confidence 60%. The live false-abstain rate is unmeasured. Reversible.
- **36. NEEDS LEAD (money path, least privilege): bare 12-digit numbers are stored and put back (R3-ADV-6).**
  - Default meanwhile: (b).
  - (a) Keep. Argument for it: cloud-operation agents read and act on account ids (pins `:296-298`), and a plan passes the approval gate before any executor. Against it: a bare 12-digit bank number on an invoice can go back into a plan.
  - (b) RECOMMENDED: ACCOUNTID leaves the DEFAULT stored kinds, and an agent opts in by config (deny by default; one constant, one row, one mutant).
  - (c) Remove ACCOUNTID from `STORED_KINDS`. No agent gets ids back, which breaks cloud-operation agents.
  - Confidence 70%. Reversible with one gate run per agent.
- **37. INFORM: gate runs are per case; judge cases each get a run; `MaskedLLM.current()` and a read-only `Runtime.llm` are added** (R3-COR-1, -2, -4). There is no owner rule here. Reversible before P5c-3 merges.

## Counts
- Finding ids 24 (ADV 14, COR 10). Majors 9 (ADV-1 to ADV-6, COR-1 to COR-3). No Blocker.
- PROPOSE FIX 19:
  - ADV-1, 3, 5, 7, 8, 9, 10, 11, 12, 13 (10);
  - COR-1 to COR-9 (9).
  - Partial contests inside them: 2 (ADV-5 DOTALL; ADV-9 `_RunEnded`). One DECLINE has a part fixed anyway (ADV-14's T2-15(d) wording, in BN-1).
- ESCALATE 3 (ADV-2, ADV-4, ADV-6, as NEEDS LEAD 35, 34, 36). DECLINE 2 (ADV-14, COR-10). CONTEST 0. Check: 19 + 3 + 2 = 24.
- Build notes 18. New rows 10: T1-06b, ACC-TABLE, ACC-GROUPS, T2-19, T2-20, T3-06c, T3-10c, T3-13b, T3-19, T4-13. New mutants 16 (M56-M71).
- New totals (defaults): **101 rows (was 91) plus the T2-P measurement; 4 strict xfail; 66 mutants (was 50)**. The variants for other lead answers are in BN-18.
- PENDING LEAD: 4 new (34, 35, 36 NEEDS LEAD; 37 INFORM).
- Fixes applied to the ticket in this step: 0 (they are build notes). Remaining unaddressed findings: 0.
