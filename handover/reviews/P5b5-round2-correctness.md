# P5b5 ticket review, round 2, correctness

Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority)
Reviewer type: correctness (egm:egm-codebase-details)
Target: tickets/P5b5.md revision 2

---

TICKET REVIEW round 2, CORRECTNESS, P5b5 revision 2. Verdict: no Blocker and no Major. Four Minors, two Nits.

Snapshot rule: I read core code only from the snapshot `.../snap/cd2243f/src` and `.../tests`. The on-disk `[path removed]` differs. Example: `def safe_head` is at `runmap.py:485` on disk and `guard/runmap.py:532` in the snapshot. The ticket's header says the same, and the snapshot confirms it. Stdlib text was read from the local `/usr/lib/python3.13/http/server.py` (3.13.18) and the 3.12 grep (`/usr/lib/python3.12`, 3.12.3).

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Minor | 48 (F2b) | The text calls `redact_text`, `redact_untrusted`, `redact_value`, `redact_layered`, `redact_bounded` and `clean` "choke-family members". Actual `CHOKE_FAMILY` (`guard/producers.py:44-51`) has six keys: `redact_untrusted`, `redact_bounded`, `safe_head`, `redact_value`, `redact_layered`, `clean`. `redact_text` is not in it (it is `CHOKE_POINT`, `:52`). The producer rows run `:15-40`, not `:17-40`. | Reword to "the other `CHOKE_FAMILY` members plus the choke point `redact_text`". Cite `:15-40`. |
| R2-COR-2 | Minor | 68, 177 (C7) | The ticket says P8b's `docs/kinds/diagnostic.md` "(`P8b.md:137`) links to it and does not restate it", and that P8b's "wording check covers it" (T6 at `:15`). `P8b.md:137` only lists `diagnostic.md` among the 15 pages to create. `P8b.md:15` and `:153` define T6 as checks on Backends-row roles, the redactor phrases and the root README paragraph. Nothing there covers `diagnostic.md` or links to `docs/diagnostics.md`. | Say this is a request to P8b, not a fact in P8b. Drop "the wording check covers it", or note that P8b must add it. |
| R2-COR-3 | Minor | 177 (C4), 50 | Cites `P5b3.md:146` for "the loader refuses an entry whose file, function or `stmt_hash` matches nothing". Line 146 says only: entries `{file, function, stmt_hash, reason, expires}`, at most 10, an expired waiver fails. The stale-match refusal is not on that line. I did not read `:147` onward for it, so UNVERIFIED. | Re-cite the line that holds the refusal, or say P5b3 does not state it. |
| R2-COR-4 | Minor | 57 (rule 2) | Only the 3.13 line (`http/server.py:590`) is cited. The repo requires `>=3.12` (`pyproject.toml:6`), where `log_message` is at `:575` and `sys.stderr.write` at `:596`. | Add "3.12: `:575`, same behaviour" so the claim holds for both versions in the supported range. |
| R2-COR-5 | Nit | 22 | "order 16 header: the two-clean-rounds rule stays for RESULT review". That sentence is in the Finding paragraph (`LEAD-ORDERS.md:47`), not in the header (`:46`). | Say "order 16 finding paragraph". |
| R2-COR-6 | Nit | 39 (L1), 177 | Several lines cited in P5b4 and P5b3 were only partly read. `P5b4.md:181` is not shown to say "removes `log_message`". `P5b3.md:195` and `:128` were confirmed by grep. | None needed. See UNVERIFIED below. |

**Handler.log_message claim: correct.**
- `BaseHTTPRequestHandler.log_request` (3.13 `:560-569`) calls `log_message('"%s" %s %s', self.requestline, code, size)`.
- `log_message` (`:590-613`) does `sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), ...))`. That is the client address plus the request line (the path), written straight to stderr, not through `logging`.
- `send_response` calls `log_request`. `log_error` also routes to `log_message`.
- At `cd2243f`, `receiver.py:62-63` is `_LOG.debug(format, *args)`. `Handler` is nested in `serve` (`:40-43`). With no root logging configured this is silent below WARNING, so T4 passes on `cd2243f` and fails when the method is deleted (M6). Both match the ticket.
- Whether `capfd` sees the server thread's `sys.stderr` write is not run. The ticket marks it UNVERIFIED.

**Verified**
- Header: base `cd2243f`; `safe_head` at 485 on disk versus 532 in the snapshot. UTC/IST times are consistent (03:25 = 08:55, 02:40 = 08:10).
- F0: `guard/` holds exactly the nine `.py` files listed plus `judge_prompt.md`. No `safe_str`, `safe_message`, `validation_text`, `with_class`, `def class_name`, `def locator`, `_Stderr`, `_NoTraceback`, `_TICK_LOGGING_READY` or `lastResort` in `src` or `tests`. The only `safe_text` is `agent_loop.py:367` (also `:368`, `:387`, `:454`).
- F1 cites, each at the stated line:
  - `tick.py:284`, `:287-292` (`:289` module check, `:292` call)
  - `extract.py:58`
  - `injection.py:91-97` (call at `:96`)
  - `cli.py:74-75`, `:81-82` (`import traceback` at `:32`), `:287`
  - `receiver.py:62-63`
  - `producers.py:30-37`
- F2: exactly five `safe_head(` calls in `src`: `extract.py:58`, `injection.py:96`, `tick.py:292`, `k1b/loop.py:187` and `:194`. `run_case` is defined at `loop.py:125` and both calls sit inside it. `producers.py:19` is the k1b row. `CHOKE_FAMILY` is `:44-51` and holds six members.
- `test_k5_producers.py:46-53`: "does not exist" at `:50`, "no longer calls" at `:51-52`.
- Fail-before keys for T1: `extract.py::extract`, `guard/injection.py::injection_check` (def at `injection.py:85`), `runtime/tick.py::_message`. T2: only importer is `cli.py:32` (no `from traceback`, no `__import__`); only `basicConfig` is `cli.py:287`. T3: body is `_LOG.debug`.
- F3: `protocol.py:29-38`; callers `cli.py:366-368`, `:395`, `:408`; `tick.py:342`, `:362`; `chain.py:533`. `test_p7_tick.py:606-617` with `__module__` `"psycopg.errors"` (`:606-607`). The real-socket pattern is at `:282-286`.
- Counts: 7 real-tree rows (T1-T7) + 14 plant rows (N1-N14) = 21. 24 mutants (M1-M24). 31 CHANGELOG finding ids (27 FIX, 2 CONTEST, 2 DECLINE; the table has 31 rows). 8 couplings (C1-C8), which I take to be the "8 relays".
- Mutant killers: I walked M1-M24. Each named killer exists, and the plant or row logic does kill it, including M18 (subset, killed by N5) and M24 (killed by N14, a negative plant). T4 kills M6.
- P5a: revision 3; `STEPS` at `:128`, `CORPUS_STEP` at `:127`; `Code` has 21 members at `:43`; `FactKey` has 20 at `:47`; ledger `BL-core-c18a-001..051` and "exactly one BASE" at `:147`; Grammar B and `detail` cut at `:8`.
- P5b3 lines confirmed: `:72`, `:111`, `:118`, `:123-131`, `:139`/`:143` (`exc_info` listed as an OBJECT sink), `:185` (no test file deleted), `:195`, `:280` (M25 killer is `test_receiver_logs_nothing`, using `caplog`). Stale S0 EXIT text at `:52` and `:330`.
- P5b4 lines confirmed: `:59` (says P5b3 removes `log_message`, which conflicts with `P5b3.md:131`, as C2 states), `:88`, `:118` (L4b conflict, C3), `:147`, `:155`/`:309` (`CORPUS_STEP` "R2"), `:173`, `:191`, `:216`, `:217`, `:222` (S1), `:251` (K2 killed by U6), `:330` (PL 2: null device, no `capture_fd2`). Stale S0 EXIT text at `:34` and `:336`.
- P5c: `:112` and `:605` (PL 12), `:103` and `:290` (`k1b/loop.py` edits). P4a cites `:47` and `:88` mention `k1b/loop`.
- CI and config: `requires-python` at `pyproject.toml:6`; `python-version: "3.13"` at `ci.yml:73` and `:109`; `bandit -q -r src demos -ll` at `ci.yml:119`.
- Quoted strings: the `HADAVIN_DEBUG` text and the `refused:` print are as quoted.
- Template: the ticket has all 17 fields, in the template's order (Package id through Rollback), and the Rollback field covers tag, no migration, and revertibility.
- Order cites 6(b), 7(3), 8(1)(3)(5), 19 A, 20 items 3-6 and 21 item 17 are accurate.
- No real-looking secrets. The only test strings are placeholders.

**Not checked / UNVERIFIED**
- `design-v3.md` lines 68 and 73, and `design-v3-FROZEN-amendments.md` D1 (`:6`), D11 (`:47`) and D12 (`:50`): not in my read set.
- The old branch `198a6b6`.
- `P5b4.md:181` content.
- `P5b3.md:147` onward, for the loader refusal.
- The P5a `Code` and `FactKey` member lists at the P5b5 head.
- Whether P5a's built `diagnose` imports `traceback` (affects `TRACEBACK_IMPORTERS`).
- Whether `capfd` captures the `Handler` thread's stderr write in T4.
- The P1m runner arguments.
- Nothing was run: no tests, no checker, no mutants.
- Exit code 4 from `is_connectivity_error` callers.
- `design-v3.md` line 73's "3-4 agent-hours" estimate.
- Whether `tests/test_p7_tick.py:110` and `:112` pin the tick strings as the ticket claims.