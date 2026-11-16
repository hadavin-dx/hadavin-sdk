# P5c round 3, adversarial review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

P5c ticket review, round 3 (adversarial, money/redaction path). Target: handover/tickets/P5c.md revision 3, all 770 lines read.

Method limit: I had Read/Grep/Glob only, with no shell, so I ran no python3 -I probe. Everything below is by reading redact.py, defaults.py, config.py and runmap.py on disk. The disk tree is not 124258b, so the runmap.py and agent_loop.py cites cannot be checked.

**Verdict on the round-2 Blocker: the fix holds on paper. I found no Blocker in revision 3.**
- `_mask` (redact.py:929) takes the first non-None group.
- None of `_NOT_IN_WORD`, `_BANK_KV`, `_ACCT_WORD` or the BANKCODE-then-digits pattern's prefix contains a capturing group. So group 1 of both BANKACCT patterns (redact.py:332-349) is the digits group inside `_ACCT_DIGITS`.
- `_ACCT_STRONG.match(m.string, m.start(), m.start(1))` reads only the text before the digits. The second BANKACCT pattern starts with `<`, so `match` returns None and nothing raises.
- Under M50, `m.start(1)` collapses to `m.start()`, which gives an empty slice. The clause is False, the digits stay in clear, and ACC-2's "digits absent" assertion kills M50.
- Residual risks are in the table (R3-ADV-5, -7, -11).

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-ADV-1 | Major | 216, 480 (T2-15) | `check` says "a session original of 4 or more characters ... where `_Redactor.sweep` would have masked it", but the sweep's rule differs. `_sweep` (redact.py:1202-1217) skips originals under 3 characters, skips all-digit identifiers under 6, and skips `_COMMON` words ("prod", "admin", "test"). It uses "every copy" only for SECRET_KINDS (which includes IBAN and CREDITCARD, not BANKACCT) at 4 or more characters. Read literally, a stored TENANT "prod" or digits "5000" left unswept after the wrapper's re-mask makes `check` refuse every call (false abstain). The prose does not say "same function". | State that `check` calls `_sweep(placeholder, original)` itself and uses no length of its own. Add T2-15 cases for a `_COMMON` word, a 5-digit identifier and a 3-character identifier (each gives ONE inner call, no refusal), and a mutant that gives `check` its own threshold. |
| R3-ADV-2 | Major | 216, 285-286, 446 (T1-15) | `check` runs on trusted `system`, `tools` and `output_schema`. A planted document value (for example `tenant_id=<a word that appears in the agent's own prompt or schema>`, or `token=<such a word>` for a SECRET kind, which is checked anywhere) becomes a session original. From then on every call carries that word in its config, so every call is refused `self_check_failed`. Main does not refuse here. This is an availability attack from document text. It fails safe, but the false-abstain cost is not argued. | Add a hostile row for it. Either exempt text that is byte-identical to the registered prompt and schema, or state the accepted denial in the README and test it. Cite the false-abstain ceiling. |
| R3-ADV-3 | Major | 128, 173, 180, 224-226, 391 | G6 ("run map has no end of life") and problem 3 ("can be copied and used after the run") are listed as closed, and "a session that cannot leak" is claimed. But the session wraps the run loop's own `RunMap` as a seed and the loop keeps its reference (lines 225-226), so the plain map can still be copied and read after close. The ticket never says what `close()` does to the seeded map. If it clears it, the loop's later uses (`:645-648` and others) break. If it does not, G6 stays open. T1-06 tests the session object only. | Define `close()` on the seeded map: clear it, or detach it. Drop G6 from the closed list or add a row. Reword line 180 and problem 3. |
| R3-ADV-4 | Major | 454 (ACC-2-NEG), 397-400 (b), 425-429, 682 (V4) | ACC-2-NEG pins `Account: <8 digits>` and bare `acc`/`account` with digits as NOT masked, so an invoice supplier account number goes to the model in clear and a test asserts it. These weak-keyword forms are not in the "stays open" list, not in the xfail records (ACC-1a, ACC-1b, ACC-3) and not in V4 (V4 covers only 8-9 or 17+ digits with no keyword, glued digits and JSON numbers). The README "not masked" item (b) says only "plain account numbers". On a money path this is a leak pinned as correct. | Add a strict xfail record plus a V4 clause for "weak keyword plus 6-17 digits". Name it in the README list. Weaken ACC-2-NEG so it records the leak and does not bless it. The owner should decide this knowingly, since Intake's use case is invoices. |
| R3-ADV-5 | Major | 247-248, 453, 576 | The `_ACCT_STRONG` regex text is nowhere in the ticket, only prose: "then any characters up to the digits". `_BANK_KV` allows one line break (redact.py:73) and quotes, marks and nbsp. If the builder writes `.*` without DOTALL, then `Account No:\n<digits>` or `"account_no": "<digits>"` finds no strong form and the digits stay in clear (the leak the Blocker was about). Also, `match` with an `endpos` needs no tail at all, so the "any characters" part is unneeded and unclear. ACC-2's 59 cases vary only the keyword and suffix, not the separator (` `, `_`, `-`, nbsp), the KV form (`:`, `=`, `#`, line break, quotes, markdown) or the digit shape (dashed, 4-4 groups). I did not run this. | Put the exact `_ACCT_STRONG` pattern in the ticket, with DOTALL or `[\s\S]` stated. Add ACC-2 cases for separators, line break, JSON key and digit shapes, each with the digits-absent and keyword-kept assertions. Add a mutant that drops DOTALL. |
| R3-ADV-6 | Major | 410-411, 699 (PL8), 132, 394 | A bare 12-digit bank number is masked ACCOUNTID, is stored and is put back into plans (`defaults.py` STORED_KINDS contains ACCOUNTID). The G10 rationale is that bank numbers must never be put back, but only the PHONE route is closed. Only the keyword form is closed (ACC-12b). Plans can lead to payments. "Cloud agents need account ids" is the only reason given. | The owner should decide explicitly. Option: restore ACCOUNTID only for agents or contracts that declare it. Option: pin the exposure in the README and in a money-path hostile row. Do not leave it as "recommended keep". |
| R3-ADV-7 | Minor | 576 (M50), 246 | M50 is killed because the new clause itself fails (empty slice), not by the Blocker's real failure mode (keyword used as the value while context is true by another route). The rule "a pattern's first capturing group is the value" is prose only. | Add one ACC-2 case with context from another clause (a masked BSB code before the keyword) asserting the digits are gone. Add a test over `PATTERNS` that the first group of each BANKACCT pattern is the digits. |
| R3-ADV-8 | Minor | 313, 331, 359, 556 | `tests/p5c_mutants.py` is created in P5c-1. M20-M55 belong to P5c-2 to P5c-4, but those Files lists do not list the file (P5c-2 says "No other file"). Done requires "50 of 50". | Add "extend tests/p5c_mutants.py" to P5c-2, P5c-3 and P5c-4. |
| R3-ADV-9 | Minor | 494, 500, 502, 504, 598 | Behaviours with no mutant: the gate's strict decode (T3-05b; M33 covers only the run loop), the `extract` decode (T3-03e), the `cli gate` audit-down path (T3-10b), the judge audit path (T3-12b), the k1b context copy (T3-11b), the `_RunEnded` wiring. The 50 mutants each have a killer, but these rows are unguarded. M39's killer, T4-02, "is written later" (line 608), so it is a placeholder. | Add mutants for each of these, or state why not. |
| R3-ADV-10 | Minor | 552 (T2-P) | The perf row has "budget UNVERIFIED", so it cannot fail. It is the only test of the time-budget path. | Fix a number before build, or relabel it a measurement and keep it out of the Done gate. |
| R3-ADV-11 | Minor | 247, 244 | `_ACCT_STRONG` is a second copy of `_ACCT_WORD` (redact.py:82). If the strong table and the keyword list drift apart, the weak/strong split is wrong. | Derive both from one table. |
| R3-ADV-12 | Minor | 235, 240 | The fingerprint hashes files in list order with no length or name separator (ambiguous concatenation). A bytecode-only install makes the import raise. Both are acknowledged as UNVERIFIED. | Hash each file separately with its name, then hash the list. |
| R3-ADV-13 | Minor | 16-18, 225, 335-340 and others | Cites not checkable here: the ticket's `runmap.py` lines (98, 340, 345, 384, 464, 588, 607) do not match the disk file (TooDeep 53, neutralise_untrusted 293, redact_untrusted 298, RunMap 337, redact_text 417, _redact_value 541, restore_value 560). The ticket discloses that disk is not 124258b. `agent_loop.py`, `tools.py`, `evals.py` and `k1b` lines are UNVERIFIED for the same reason. | None needed beyond the disclosure. The result review must re-check against the PR head. |
| R3-ADV-14 | Nit | 3, 405, 480(d), 554, 143 | The sentence "Round 2 had 1 Blocker ... so round 3 is allowed" misapplies the stated rule (round 3 is allowed by the 3-round cap). Line 405 merges bullets (f2) and (g). T2-15(d) says "stored ... SECRET-kind", but secrets are never stored (the word means "in the session"). Row counts use T3-15a..f as 6 rows and ACC-2 (59 cases) as 1. The template's "Extended review: yes/no" is not answered literally. | Reword. |

**Verified (by reading)**
- Code cites that match disk:
  - redact.py: 107-113, 82, 93-94, 332-349, 353, 444, 447, 476, 925-956, 929, 939-941, 1011, 1202, 1223.
  - defaults.py: 38, 40, 44, 49, 108, and PHONE at 120.
  - config.py: 215 and 256.
- Both BANKACCT patterns have no capturing group before the digits.
- BANKACCT is not in SECRET_KINDS and not in STORED_KINDS.
- STORED_KINDS minus PHONE is 12 kinds in the order T4-11 expects.
- Counts add up:
  - Test rows are 16 + 14 + 17 + 32 + 12 = 91, with T2-P making 92.
  - The 4 strict xfails are named.
  - The mutants are 19 + 15 + 11 + 5 = 50, each with a named killer. I walked each mutant against its killer and found a plausible kill for every one except M39.
  - ACC-2 is 16 + 2 + 16 + 1 + 8 + 16 = 59.
  - ACC-2-NEG is 5.
- All 17 template fields are present, with an extra Order 11(5) section. No real-looking secrets were seen.

**Not checked**
- No probe was run, because no shell tool was available. The `_bank_context` clause is argued by reading only, as the ticket itself says.
- All content of tickets P2d, P4b1, P4c, P5a, P5b3, designs and lead orders. LEAD-ORDERS.md, amendments.md and TICKET-TEMPLATE.md were not read except the template.
- Anything at 124258b or on the PR heads: agent_loop.py, tools.py, evals.py, k1b, injection.py and judge.py cites, the 14 and 21 test-file counts, and the 42 raw-model grep lines.
- NAME regex behaviour: probe (b), NAME-DECOMPOSED and NAME-CAPS were reasoned only.
- Whether T3-12, T3-09 and T3-03 fail before on real code.
- P1m's runner. Windows behaviour. Python 3.12 and 3.14.
- handover/reviews/ and handover/evidence/ were not read, as instructed.