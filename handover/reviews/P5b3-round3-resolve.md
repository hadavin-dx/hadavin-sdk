# P5b3 round 3 resolve report (egm:egm-resolve, auto mode)

Status: resolved (categorised). The ticket is NOT edited here. Round 3 had 0 Blocker and 7 Majors (adversarial 4: R3-ADV-1 to 4; correctness 3: R3-COR-1 to 3), more than the "at most 2 Majors" of order 20 item 6, so there is NO round 4. P5b3 freezes at revision 3 (`9d55273`). Every fix below is a numbered build note BN-1 to BN-15, which wins over the revision 3 text.
Target: `handover/tickets/P5b3.md` revision 3, commit `9d55273` (809 lines, full file read; path class REDACTION, Tier A). `git status` shows the file unchanged since that commit.
Inputs: `reviews/P5b3-round3-adversarial.md` (R3-ADV-1..12: 4 Major, 7 Minor, 1 Nit) and `reviews/P5b3-round3-correctness.md` (R3-COR-1..15: 3 Major, 9 Minor, 3 Nit). 27 finding ids. Severity is taken from the tables and never changed here.
Gate: the skill's "wait for the user" step is skipped (auto mode, per the brief). This file replaces the skill's default file name `goldfish_review_report.md`. Two items are redaction-path decisions: NEEDS LEAD 24 (R3-ADV-1) and 25 (R3-COR-3), each with options and a recommendation. Each build note names the default the builder takes meanwhile, and what changes under another answer. Item 26 is INFORM.
Facts: see "Facts I checked myself". Honest note: first, below.

## Honest note (what I did NOT check, first)
- I ran no pytest, no mutant, no `uv`, no install, no network call and no git write. I ran one read-only `python3 -I` probe from a scratch folder that imports `<repo>/src` by path (Python 3.13.18, pydantic 2.13.5, both printed by the probe), plus `python3 -I` arithmetic for the counts. A probe is not evidence; the builder's runs are.
- I read `src/` on disk only. The ticket says `tools.py` below line 832 differs on `origin/main` (`4ec3616`). I did not re-read `tools.py:985-1012`, `:1100-1190` or `actions/contract.py` on `origin/main`. All `tools.py` cites below are DISK lines.
- P5a, P5b1, P5b2 and P1m code does not exist. Everything I say about `diagnose`, `render`, `class_name_of`, the identity rule, `dynamic_class`, the corpus and the mutation runner is read from the frozen tickets and their build notes, not run. In particular I did not verify that `class_name_of` never raises (BN-2 makes the builder prove it).
- I did not run the taint guard (it does not exist). The base hit count of "about 70" in BN-9 is an estimate: the ticket's 56 listed call hits, about 4 return hits, and the unlisted hits both reviewers name. I did not decide whether `audit/local_dir.py:52` (`e["key"]`, a subscript, which no TXT rule names) is a hit.
- I did not check whether P1m's runner can mutate a file under `tests/` (R3-ADV-10). BN-12 gives a fallback.
- I did not read `P5b1.md` beyond grep lines, `P4c.md`, `P6b2.md`, or `audit/chain.py:343-358`. I did not check where `bundle.py:190`'s text is printed (a P5b2 build-note relay, Couplings).
- I did not re-verify every off-by-one cite of R3-COR-9. BN-1 replaces them with cites by section name or id instead.
- NEEDS LEAD 24 and 25 are not decided by me. The build-note defaults are my recommendations.

## Facts I checked myself (disk lines; "probe" marks a run)
- **`ToolRefused`** is a public class at `tools.py:66`. `grep -rn "ToolRefused(" src` gives 31 lines: the class line, 29 constructions in `tools.py` (28 `raise` plus `err = ToolRefused(...)` at `:627`) and 1 in `app.py:325`. So 30 constructions (R3-ADV-5, R3-COR-6 TRUE).
- **The tool body's thread.** `_call` (`tools.py:1100-1138`) runs the body in a thread; `box["error"] = exc` (`:1114`) and `raise err` for any `Exception` (`:1133-1134`). The `ToolContext` checks that raise `ToolRefused` (`secret` at `:503`, `:505`, `:509`; the fetch checks at `:521-627`) run INSIDE that thread, because the body calls them. So a refusal of our own and a `ToolRefused` that the body builds itself arrive at `invoke`'s `except` (`:1191`) by the same path (R3-ADV-1 TRUE; this is why the reviewer's option (b), wrapping at `_call`, would also turn our own `ctx` refusals into class-only text).
- No `src/` code catches `ToolRefused` (only `isinstance` at `tools.py:993`, `:995`). All 22 test uses are `pytest.raises(ToolRefused, ...)` or the one direct call at `tests/test_k5_fixes9.py:73`. No test or demo tool body raises `ToolRefused`.
- **Error text to the model** is `ERROR_PREFIX + error_reason(...)` (`tools.py:1193`), then `_sanitise` and `prepare_output(raw, mapping, ...)` (`:1194-1200`). The tool NOTE at `tools.py:490-493` says a tool body is trusted in-process code; the manifest limits what it is given, not what it can do.
- **`:1184`** raises `"arguments invalid: " + ", ".join(bad)`, where `bad = self._arg_errors(spec.input_schema, restored)` and `arg_errors=schema_errors` (`app.py:457`). In `actions/contract.py:155-185` the only text taken from the input is `f"unexpected {k}"` (`:181`), where `k` is a key the model wrote. Every other entry is a schema key or fixed words (`expected {want}`, `not in enum`, `too long`, `too short`, `pattern mismatch`, `missing {k}` with a schema key). No input VALUE is ever echoed. `restore_value` (`guard/runmap.py:560-567`) restores values, never keys, so the echoed key is exactly the masked text the model sent. The other caller, `actions/authorizer.py:41`, uses only the truthiness of the list. No test pins the `unexpected <key>` text (grep `unexpected` in `tests`). (R3-COR-3 TRUE as a path; it carries no text the model did not already write.)
- **`:1188`** `ToolRefused(why)`: `why` comes from `app.py:401-410` and is fixed words plus a source name from the operator's configuration.
- **`config.py:120` (probe).** All 28 kind settings models in `backends/table.py` `TABLE` subclass `KindSettings` and have `hide_input_in_errors=True` (`backends/table.py:24`). For `KindSettings(kind="x", <unknown key>=<value>)`, `str(exc)` holds the unknown KEY name (in `loc`) and NOT the value, over 4 lines (R3-COR-2 TRUE).
- **`hide_input_in_errors=True`** is set at `config.py:52` (`_Strict`), `backends/table.py:24` (`KindSettings`) and `scrub_settings.py:12`. `tools.py:73` `ToolSpec` sets none. So FB1's sentence "Only `config.py:52` does" is false (R3-COR-2 TRUE).
- **Tick (`runtime/tick.py:295-330`)**: `_run_step` reads only `ctx.app.store` (`:296`) and `step.interval` (`:300`), and calls `_message(exc)` twice (`:316`, `:317`) inside the `except` handler. `_message` (`:287-292`) reads `type(exc).__module__.split(".")` and `str(exc)`, so a non-`str` `__module__` or a raising `__str__` escapes the handler (P5a BN-2's crash case, read, not run).
- **P5a** (`tickets/P5a.md:4`): "Revision 3 is FROZEN after round 3"; its build notes are the section "Build notes (round 3 resolve; these win over the text above)" (`P5a.md:243`). BN-2 adds `OLD_WRITER_CRASHES` and `xfail(strict=True, raises=AssertionError)`; BN-5 makes an own class print its bare name only if (a) the identity walk holds, (b) its module is `hadavin_sdk` or under it, and (c) the qualname matches `^[A-Za-z0-9_.]{1,80}$`, else `dynamic_class`; BN-7 says `diagnose` never raises on bad `facts=`; BN-14 asks P5b3 for a `token40` constructor (moot: P5b3 cut `token40`, V14). P5a's discovery test resolves a class through its base (`P5a.md:94`), so a subclass or a flag on `ToolRefused` needs no new code row (R3-COR-1 TRUE).
- **P5b2** (`tickets/P5b2.md:4`): FROZEN, "Build notes (round 3 resolve; these win over the text above)" at `:275`. Its BN-3 adds raiser-call rows (0 expected), BN-14 makes 31 or more FOREIGN rows a STOP titled `STOP: FOREIGN=<n>`. `P5b2.md:40` still says "P5b3 rewrites this place with `from_cause`", which revision 3 cut.
- **P5b4** (`tickets/P5b4.md:1`) is revision 3. Its writer is `output_guard.emit` (`:87`). Its section "Boundary with P5b3" is at `:470-475` and says "revision 2 said `handle.emit`" (R3-COR-8 TRUE). Its coupling (1) asks P5b3 to drop "the `run_tick` move" from PENDING LEAD 2.
- **F6** (`studio-notes/amendments.md:22`) lists `llm/anthropic.py (P4a, P5b3, P6b1)`. `P5b1.md:53` lists `llm/anthropic.py: P4a, P5b1, P5b3, then P6b1`. So the ticket copied P5b1's list, not F6's (R3-COR-13 TRUE).
- **`error_reason(` in tests**: 11 call lines in 5 files (fixes9 3, layers 3, round12_fuzz 1, round8 2, round9 2), plus the comment at `test_k5_producers.py:143` (R3-ADV-8, R3-COR-5 TRUE).
- **`traceback` in `src/`**: only `cli.py:32` (import) and `:82` (`traceback.print_exc()`). `excepthook` does not appear in `src/`. `P5b4.md` plans no `import traceback` in `src/` (grep). Under revision 3's rules, `traceback.print_exception(exc)` written as a bare statement is TEXT (TXT-5) with no sink, so it is not flagged either (my own finding, R3-RES-1, folded into BN-6).
- **`tests/test_k5_producers.py:46-53`** checks `any(_called_names(f) & chokes)` (R3-ADV-4 TRUE).
- **`tests/test_k1b_cli.py:196-216`** monkeypatches `atomic.atomic_write`, reads `LocalDirSink(cfg_dir / "audit").events()` and asserts `error_code == "OSError"` (R3-COR-10 TRUE).
- **ruff** (`pyproject.toml`) selects `B, DTZ, I, S, TID, UP` on top of the defaults; no `SLF` rule, so `app.py` may call a private `tools` function.

## Banner for the ticket (placed directly under line 3, word for word)
> **BUILD NOTES WIN.** Revision 3 is FROZEN after round 3 (0 Blockers, 7 Majors; order 20 item 6 allows no round 4). The section "Build notes (round 3 resolve; these win over the text above)" at the end of this ticket replaces any text above that it names. Where a build note and the text above disagree, the build note is right. Source: `handover/reviews/P5b3-round3-resolve.md`. NEEDS LEAD 24 and 25 (redaction path) are open: until the lead answers, the builder takes the default each build note names. The CHANGELOG sections are history, not instructions. Cites into other tickets are by section name or id (BN-1); code cites are found by name at the rebased head.

## Decisions (one category per finding id)

| id(s) | category | decision |
|---|---|---|
| R3-ADV-1 (Major) | ESCALATE (redaction path, NEEDS LEAD 24; default (a)) | TRUE (Facts). Default: our own refusal sites build `ToolRefused` through one private factory that sets an instance flag; `own_text` keeps a `ToolRefused` sentence only when the flag is in the instance's own dict. A `ToolRefused` the tool body builds gets the rendered diagnostic. Reviewer option (b) is rejected with evidence: `ctx` refusals arrive by the same thread path. FB15, mutants M40-M42. **BN-3.** |
| R3-ADV-2 (Major) | PROPOSE FIX | TRUE, and wider (R3-RES-1): `traceback.print_exception(exc)` as a statement has no sink either. New rule TB-1: the `traceback` module is banned in `src/`, with no allow-list. M14's killers gain FB8 and the TB-1 row. **BN-6.** |
| R3-ADV-3 (Major) | PROPOSE FIX | TRUE. OBJ-2 splits into OBJ-2 (`exc_info=`) and OBJ-3 (`.exception(...)`); M20's killer is the `_LOG.error("x", exc_info=True)` row. **BN-6.** |
| R3-ADV-4 (Major) | PROPOSE FIX | TRUE. Chosen: the reviewer's option 1. M27 becomes M27a-d, "no call to any column-4 name", one per row. `_run_step` calls `render` once. Partial removals are named mutants of their own (M1, M2, M3a, M3b, M5, M38, M40). The producers test is not changed. **BN-7.** |
| R3-ADV-5 (Minor) | PROPOSE FIX | Sentence corrected (30 constructions; `:503`/`:509` hold a name chosen in the tool's code; `:1184` echoes model keys; `:1188` a configured source name). The non-ASCII key row is in BN-4. **BN-3, BN-4.** |
| R3-ADV-6 (Minor) | PROPOSE FIX | The tick driver is named: `MemoryStore`, a `SimpleNamespace` app, `TickContext`, a raising `TickStep`, and `last_error` plus `caplog` read back. The same driver serves round8 and round12_fuzz. **BN-10.** |
| R3-ADV-7 (Minor) | PROPOSE FIX | `actions/contract.py` joins Files and the hot files; `e` at `:184` becomes `msg`. A non-exception `e`/`err`/`ex`/`exc` is renamed, and each rename is listed in evidence 5. **BN-9.** |
| R3-ADV-8 (Minor) | PROPOSE FIX | "11 call lines in 5 files, plus 1 comment" (Facts). **BN-14.** |
| R3-ADV-9 (Minor) | PROPOSE FIX | Spoof rows carry a printable-ASCII sentence with a canary, the `ToolRefused` spoof also carries the flag, and the assertion is the exact `dynamic_class` line. **BN-5.** |
| R3-ADV-10 (Minor) | PROPOSE FIX | The guard engine moves to `tests/taint_guard_rules.py` (an importable helper, like `tests/k5_support.py`). The builder checks P1m's runner first, with a fallback stated. **BN-12.** |
| R3-ADV-11 (Minor) | PROPOSE FIX | New `test_own_tool_refusal_masks_every_spelling` in `tests/test_k5_round9.py`. It is a separate test, because `DRIVERS` must equal the `PRODUCERS` names. **BN-10.** |
| R3-ADV-12 (Nit) | DECLINE | The network branch is kept "as today" (ticket :229). Nothing to do. |
| R3-COR-1 (Major) | PROPOSE FIX | TRUE. P5a and P5b2 are FROZEN with build notes that win. `OLD_WRITER_CRASHES == {}` and `OLD_WRITER_LEAKS == ()`, and every row is a plain `outcome == "clean"` assert. `own_text`'s rule (a) is P5a's BN-5 own-class predicate. A crash row that still crashes at the head is a STOP. **BN-1, BN-2, BN-5.** |
| R3-COR-2 (Major) | PROPOSE FIX | TRUE (probe). There is a canary table per place. At both pydantic places the canary is an unknown KEY NAME; at the other three it is a message raised by a monkeypatched callee. FB1's sentence is corrected. **BN-8.** |
| R3-COR-3 (Major) | ESCALATE (redaction path, NEEDS LEAD 25; default (b)) | TRUE as an unstated path (Facts: no new text reaches the model). Default (b): `schema_errors` prints `unexpected key` with no name, which closes the path at its source. FB16 and M43. Option (a) keeps the text, and the owner-visible entry text is given. **BN-4.** |
| R3-COR-4 (Minor) | PROPOSE FIX | "four rows". **BN-14.** |
| R3-COR-5 (Minor) | PROPOSE FIX | Same as R3-ADV-8. **BN-14.** |
| R3-COR-6 (Minor) | PROPOSE FIX | Same as R3-ADV-5 (30 = 29 + 1). **BN-3.** |
| R3-COR-7 (Minor) | PROPOSE FIX | The floor is restated as about 70. STOP stays at 80 (PENDING LEAD 18 unchanged), with a margin of about 10. `contract.py` is added. **BN-9.** |
| R3-COR-8 (Minor) | PROPOSE FIX | `output_guard.emit`; P5b4 revision 3, cited by section; the Boundary was re-checked (Facts). PENDING LEAD 2 drops "the `run_tick` move". **BN-1.** |
| R3-COR-9 (Minor) | PROPOSE FIX | Cites into other tickets are by section name or id. The status words are fixed. **BN-1.** |
| R3-COR-10 (Minor) | PROPOSE FIX | FB11 uses the `test_k1b_cli.py:196-216` pattern; the hedge is dropped. **BN-11.** |
| R3-COR-11 (Minor) | PROPOSE FIX | Same as R3-ADV-9. **BN-5.** |
| R3-COR-12 (Minor) | PROPOSE FIX | Same as R3-ADV-3. **BN-6.** |
| R3-COR-13 (Nit) | PROPOSE FIX | F6 says (P4a, P5b3, P6b1); P5b1's own ticket adds itself. Relay to the lead's F6 table. **BN-1.** |
| R3-COR-14 (Nit) | PROPOSE FIX | The count is 18. The row check stays as a check, and a mismatch is a STOP. The stale `P5b2.md:40` sentence is relayed. **BN-13.** |
| R3-COR-15 (Nit) | PROPOSE FIX | Every module that gains an import of `guard.diagnostic` is imported alone in a fresh process. **BN-13.** |

## Build notes (round 3 resolve; these win over the text above)
Text to be copied into the ticket as its last section, under that heading. "Ticket :N" means revision 3 line N.

**BN-1. Dependencies, status words and cites (R3-COR-1 part, R3-COR-8, R3-COR-9, R3-COR-13).**
- Replace the "Depends on (ticket revisions; none is clean yet)" list (ticket :25-31) with:
  - "`tickets/P5a.md` revision 3, FROZEN, with the build notes in its section 'Build notes (round 3 resolve; these win over the text above)'. Those notes win over any P5a text this ticket cites.
  - `tickets/P5b1.md` revision 2, as changed by `reviews/P5b1-round2-resolve.md`.
  - `tickets/P5b2.md` revision 3, FROZEN, with the build notes in its section 'Build notes (round 3 resolve; these win over the text above)'.
  - `tickets/P4b1.md` and `tickets/P4c.md` (merge before P5b3, A4), and `tickets/P4a.md` (FROZEN).
  - `tickets/P5b4.md` revision 3, section 'Boundary with P5b3'. It was re-checked for this build note: P5b4 owns the writer `output_guard.emit`, and P5b3 owns the text and deletes the `HADAVIN_DEBUG` branch."
- **Cite rule.** Every cite into another ticket is by section name, build-note id or row id. The line numbers in revision 3 (for example `P5a.md:29`, `:64`, `:74`, `:114`, `:121-122`, `:167`, `:171`, `:195`; `P5b2.md:38`, `:58`, `:64`, `:94`, `:132-133`, `:181`, `:191`, `:199-204`, `:232`; `P5b4.md:154`, `:414-419`) are informative only and may be off by one or more.
- Replace "P5b2 round 3 next" and "Round 3 is next" (ticket :28 and Couplings "P5b2 (revision 3, round 3 next)") with "P5b2 revision 3, FROZEN with build notes".
- Replace `handle.emit` with `output_guard.emit` in: list item 9 of "Not taken" (ticket :108), the `main()` bullet under "Other `cli.py` lines" (ticket :193), and Couplings "P5b4" (ticket :604).
- PENDING LEAD 2 (ticket :635): delete "the `run_tick` move" (P5b4 Boundary: nothing is moved).
- Hot files (ticket :74 and :82): `llm/anthropic.py` reads "(F6: P4a, P5b3, P6b1; `P5b1.md` adds P5b1, which edits the provider text there)". The lead adds P5b1 to F6 (relayed under PENDING LEAD 12).

**BN-2. P5a's old-writer file: crash rows and leak rows both become plain asserts (R3-COR-1).**
- Replace the `tests/test_diagnostics_old_writers.py` bullet (ticket :330) with: "every row asserts `outcome == "clean"` as a plain assert. Every `pytest.mark.xfail(strict=True, raises=AssertionError, ...)` mark is removed, whether the row is listed in `OLD_WRITER_LEAKS` or in `OLD_WRITER_CRASHES`. `OLD_WRITER_LEAKS` becomes `()` and `OLD_WRITER_CRASHES` becomes `{}`. A row left marked XPASSes and fails the run (strict)."
- Done (ticket :570) reads: "no strict expected-failure mark is left in `tests/test_diagnostics_old_writers.py`, `OLD_WRITER_LEAKS == ()` and `OLD_WRITER_CRASHES == {}`." This brings P5a's own Done line ("empty at P8b") forward to P5b3, because P5b3 deletes `_message`, the code that crashes.
- **Tick handler rule.** Inside `_run_step`'s `except` handler, the only calls on `exc` are `diagnose(exc, step=...)` (P5a BN-7: never raises) and `class_name_of(exc)`. There is no `str(exc)`, no `type(exc).__module__` and no f-string of `exc`. `render` is called once (BN-7).
- **New writer-wiring row** `test_tick_writer_survives_hostile_exceptions` (in `tests/test_p5b3_writers.py`, head only). It is parametrised over P5a's `hostile_class` corpus rows that the adapter listed as `crashed` on the base, and it uses the same `run_tick(app, now, steps=[TickStep("x", 0, fn)])` adapter. Each case must: return from `run_tick`; leave a `last_error` that passes `grammar_ok`; and leave exactly one ERROR record with `step=x`.
- **STOP.** If a `crashed` row still crashes at the P5b3 head, `class_name_of` or `diagnose` raises. That is a P5a defect, and the builder stops and reports it to the lead. It is not fixed by a `try` in the tick.
- M1 and M2 gain the crash rows as killers, because a `str(exc)` on a raising `__str__` crashes the row again. M35 covers a crash row that keeps its mark.

**BN-3. Only our own `ToolRefused` sentences reach the model (R3-ADV-1, R3-ADV-5, R3-COR-6; NEEDS LEAD 24, default (a)).**
- **Factory.** `tools.py` gains a private function `_refusal(text: str) -> ToolRefused`. It builds `ToolRefused(text)`, sets the instance attribute `_hadavin_own = True`, and returns it. Each of the 30 constructions becomes `_refusal(...)`: the 29 in `tools.py` (including `err = _refusal(...)` at `:627`, which keeps `err.too_large = True`) and `app.py:325` (`tools_mod._refusal(...)`). The class `ToolRefused` and its printed name do not change, so the 22 `pytest.raises(ToolRefused, ...)` uses still pass, and no log or CLI line changes its class name.
- **`own_text` rule (b)** (ticket :121) is replaced by: "(b) `type(exc)` is `ConfigError` or a subclass, or `type(exc)` is `ToolRefused` or a subclass AND `exc.__dict__.get("_hadavin_own") is True`. The flag is read from the instance's own dict, so a class attribute cannot set it. Both are checked by P5a's own-class predicate (BN-5)." The rest of the bullet's sentence is replaced by: "There are 30 constructions (`grep -rn "ToolRefused(" src` gives 31 lines, including the class line `tools.py:66`): 29 in `tools.py` and 1 in `app.py`. Their text is fixed words plus: manifest values (`port`, `operation!r`, `method!r`, `host!r`, `cap`, `code`); a secret name chosen by the tool's own code (`:503`, `:509`, `name!r`); a source name from the operator's configuration (`:1188`, `app.py:325`); and argument keys the model wrote (`:1184`, see BN-4)."
- **`error_reason`** (ticket :230): the `ToolRefused` branch keeps `message = own_text(exc)` and the existing `_cut`, `_scrub` and `redact_bounded` steps, then `message[:200]`. A `ToolRefused` that the tool body built (no flag), a spoofed subclass or a non-ASCII text gives the rendered diagnostic, `ToolRefused: diag_v=1 code=tool_refused step=cli at=<...> fp=<8 hex>`, with no message. The row in BN-3's tests asserts `len(out) <= 200`. If any such line is longer, that is a STOP, because the cut would break the Grammar A line.
- **What a tool body can still do, stated (Security notes, new item (f)):** "a tool body is trusted in-process code (`tools.py:490-493`). Careless code that raises `ToolRefused(str(upstream_error))` no longer sends that text to the model. Code that sets the private flag itself, or returns the text as its result, is outside this control. A tool's normal result goes through `prepare_output` as today. The control there is code review of tool modules." This is the owner-visible entry 2 (NEEDS LEAD 25 has the text).
- **Tests.**
  - **FB15** `test_fail_before_body_raised_tool_refusal_text_not_sent`. It calls `tools.error_reason(ToolRefused("a <made-up name> b"), [])` with the PUBLIC class, as a tool body would build it. On the base the result holds the name (`tools.py:1010-1011`). At the head it is the diagnostic line, with the name absent and `grammar_ok` true. It imports only names that exist on the base.
  - Head row `test_own_refusal_raised_in_the_body_thread_keeps_its_sentence`: a tool body calls `ctx.secret("not_listed")` through `ToolBox.invoke`. The `ERROR:` text holds `secret 'not_listed' is not named in the manifest`, which proves the flag survives `_call`'s `raise err`.
  - Head row `test_tool_refusals_are_built_by_the_factory`: an AST scan of `src/hadavin_sdk/**/*.py`. Exactly one call `ToolRefused(` exists, inside `tools.py::_refusal`.
  - `tests/test_own_text.py` gains: a factory refusal with an ASCII sentence is kept; a public `ToolRefused` with the same sentence gives the diagnostic; a factory refusal with a non-ASCII canary gives the diagnostic.
- **Test migration:** `tests/test_k5_fixes9.py:73` and every "`ToolRefused` twin" of ticket :342 build their refusal with `tools_mod._refusal(...)`, so they keep today's scrub assertion.
- **Mutants.**
  - **M40:** `error_reason`'s refusal branch uses `str(exc)` instead of `own_text(exc)`. Killer: the factory refusal with a non-ASCII canary (its `error_reason` row asserts canary absent and `grammar_ok`).
  - **M41:** `own_text` ignores the flag (any `ToolRefused` passes). Killer: FB15 at the head.
  - **M42:** one own site (for example `tools.py:533`) builds `ToolRefused(...)` directly. Killer: `test_tool_refusals_are_built_by_the_factory`.
- If the lead answers **(c)** (keep revision 3): delete this build note, delete FB15 and M40-M42, and add the plain-words limit "a tool's own error message can carry any single-line text to the model" to `handover/owner-visible-limits.md`.

**BN-4. Argument key names the model wrote are not echoed (R3-COR-3, R3-ADV-5 part; NEEDS LEAD 25, default (b)).**
- **Default (b).** `actions/contract.py:181` `f"unexpected {k}"` becomes the fixed string `"unexpected key"`, one entry per unexpected key. The line `:184` stays `f"{k}: {msg}"`, where `k` is a schema property name (the manifest's) and `msg` is the renamed loop variable (BN-9). After this, `schema_errors` prints only schema keys and fixed words. `tools.py:1184` is unchanged.
- Add `actions/contract.py` to Files ("Change (`src/`)") and to the hot files (PENDING LEAD 12).
- CHANGELOG.md upgrade step: "`ERROR: arguments invalid: unexpected key` no longer names the key".
- **FB16** `test_fail_before_schema_errors_do_not_echo_input_keys`: `schema_errors({"type": "object", "properties": {}, "additionalProperties": False}, {<canary key>: 1})`. On the base the list holds the canary key. At the head it is `["unexpected key"]`. A second case uses a non-ASCII key (R3-ADV-5's row) with the same assertion.
- **M43:** `:181` goes back to `f"unexpected {k}"`. Killer: FB16 at the head.
- **Under answer (a)** (keep the echo): delete FB16 and M43. The FB16 case becomes a head row asserting that a non-ASCII key gives the diagnostic through `own_text`. The lead appends the owner-visible entry 2 variant (a) (text under NEEDS LEAD 25).

**BN-5. `own_text` uses P5a's BN-5 own-class predicate, and the spoof rows are exact (R3-COR-1 part, R3-ADV-9, R3-COR-11).**
- `own_text` rule (a) (ticket :120) reads: "(a) `type(exc)` passes P5a's own-class predicate, the same one that decides between a bare name and `dynamic_class` (P5a build note BN-5): the identity walk, a module that is `hadavin_sdk` or starts with `hadavin_sdk.`, and a qualname matching `^[A-Za-z0-9_.]{1,80}$`. `own_text` calls P5a's predicate; it does not keep a copy."
- `tests/test_own_text.py` spoof rows (ticket :446, :449):
  - Each spoofed class carries a printable-ASCII sentence that holds a made-up canary (for example `"owner Jane_Doe_Invoice is wrong"`, built from parts).
  - The `ToolRefused` spoof instance ALSO has `_hadavin_own = True`, so only the identity walk can refuse it.
  - The assertion is exact: the canary is absent, and `own_text(x)` matches `^dynamic_class: diag_v=1 code=config_invalid step=cli at=\S+ fp=[0-9a-f]{8}$` (or `code=tool_refused` for the `ToolRefused` spoof).
- M6 and M8 keep their killers. These rows now kill M8 whatever check (e) does.

**BN-6. The guard rule table: TB-1, and OBJ-2 split (R3-ADV-2, R3-ADV-3, R3-COR-12, R3-RES-1).**
- Replace the OBJ-2 row of the rule table (ticket :257) with two rows, and add TB-1:
  - `OBJ-2 | OBJECT sink | exc_info= on any logger call (any value but the literal False or None), because exc_info prints the message.`
  - `OBJ-3 | OBJECT sink | Any logger .exception(...) call, inside or outside an except, because it sets exc_info itself.`
  - `TB-1 | writer module | In any src/ file: (i) import traceback or from traceback import ... (any alias); (ii) a call whose callee is a bare name or attribute named print_exc, format_exc, print_exception, format_exception, format_exception_only, print_last, print_tb, format_tb or TracebackException; (iii) __import__ or importlib.import_module called with the literal "traceback". There is no allow-list: no src/ file needs the module after P5b3 (cli.py:32 and :82 are its only uses, and both are deleted).`
- Why TB-1 is a module ban and not a text form: `traceback.print_exc()` takes no argument, and `traceback.print_exception(exc)` is a writer whose TEXT has no sink, so neither TXT-5 nor SINK-CALL sees it. TB-1 is the only rule that flags either.
- **Guard unit rows** (tagged): `import traceback` alone (TB-1); `from traceback import format_exc as f` (TB-1); `traceback.print_exc()` inside an `except` (TB-1); `traceback.print_exception(exc)` as a bare statement (TB-1); `__import__("traceback").print_exc()` (TB-1); `_LOG.error("x", exc_info=True)` (OBJ-2 only); `log.exception("x")` (OBJ-3 only); `_LOG.error("x", exc_info=False)` (clean).
- Known limit, added to the guard's "Known limit" (ticket :270): a module name built at run time (for example `importlib.import_module("trace" + "back")`) escapes TB-1 (iii). The reviewers check it.
- **Mutation table:**
  - M14 "Killed by" becomes "FB7; FB8 at head (TB-1 flags the restored `import traceback` and `traceback.print_exc()`)".
  - M20 "Killed by" becomes "guard unit `_LOG.error("x", exc_info=True)` row (OBJ-2 only)".
  - Dropping TB-1 or OBJ-3 is killed in process by `test_every_rule_has_a_row_that_needs_it`.
- Rule ids: 20 become 22 (SRC 4, TXT 6, PROP 3, SINK 3, OBJ 3, SAFE 2, TB 1).
- Coupling to P5b4: if P5b4's `output_guard.py` later needs the `traceback` module, that is a change to the frozen P5b3 rule and goes to the lead. It is not a waiver.

**BN-7. M27 and the producers rows (R3-ADV-4).**
- `_run_step` (ticket :197-199) computes `line = render(diagnose(exc, step=StepToken.of(step.name)))` once. `error = line`, and the log call is `_LOG.error("step=%s error_kind=%s message=%s", step.name, class_name_of(exc), line)`.
- Replace M27 in the mutation table with four rows:
  - **M27a-d**: in the row's function (`error_reason`; `injection_check`; `extract`; `_run_step`), every call to every name in that row's column 4 is removed, and the value it produced is replaced by `str(exc)`. Killer: `test_each_producer_calls_its_redaction_function`, for that row.
- A partial removal is a separate mutant with a behavioural killer:
  - tick: M1 (`error`) and M2 (log line);
  - extract: **M3a** (the `ValidationError` branch appends `str(exc)`; killer FB4) and **M3b** (the other branch appends `str(exc)`; killer the extract writer-wiring corpus rows of kind `exception` and golden case 9). These replace M3;
  - injection: M5;
  - tool error: M38 (foreign branch) and M40 (refusal branch, BN-3).
- `tests/test_k5_producers.py` is not changed.

**BN-8. Where the canary goes at each rewritten place (R3-COR-2).**
- Replace layer (1) of `test_rewritten_places_drop_foreign_text` (ticket :434) with this table. Each case asserts that the canary is absent from `str(exc_info.value)` and from `exc_info.value.args[0]`.

  | Place | Cause in the test | Canary | Why |
  |---|---|---|---|
  | `config.py:120` | `ValidationError` from a kind settings model (`KindSettings`, which hides input) | an unknown KEY name in the backend entry | `loc` shows the key; the value is hidden even on the mutant (probe) |
  | `tools.py:120` | `ValidationError` from `ToolSpec` (does not hide input) | an unknown KEY name in the tool entry | the key shows whether or not the input is hidden |
  | `config.py:454` | (i) `TypeError(<canary sentence>)` raised by a monkeypatched `config._read_yaml`; (ii) a `config.yaml` with an unknown top-level KEY name (`Config` is `_Strict` and hides input) | a message canary; a key name | (i) is single-line ASCII, (ii) is pydantic |
  | `registry.py:224` | (i) `TypeError(<canary sentence>)` raised by a monkeypatched `registry._yaml`; (ii) FB1's principal with a wrong-type field and an e-mail value (`Principal` does not hide input) | a message canary; a value canary | both are shown on the mutant |
  | `llm/anthropic.py:56` | `ValueError(<canary sentence>)` from a stubbed `anthropic.Anthropic` | a message canary | single-line ASCII |

- Layer (2) (ticket :435) uses the same monkeypatched `TypeError` for `registry.py:224` and `config.py:454`.
- M10' "Killed by" reads: "layer (1), at each place with the canary of this table".
- FB1 (ticket :404): replace "Only `config.py:52` does." with "`config.py:52` (`_Strict`), `backends/table.py:24` (`KindSettings`) and `scrub_settings.py:12` do; `identity.py`, the `registry.py` models, `actions/contract.py:47` and `tools.py:73` (`ToolSpec`) do not."

**BN-9. Sweep floor, `actions/contract.py` and renames (R3-ADV-7, R3-COR-7).**
- Replace "revision 3's floor is at least 56 call hits plus about 4 return hits, about 60" (ticket :271) and the matching sentences (:268, :287, PENDING LEAD 18, Verified :681) with: "a floor of 56 listed call hits, about 4 return hits, and about 10 hits that revision 3 did not list. Examples of those: `extract.py:58`; `runtime/tick.py:316` to `:324` (`last_error=error`); the body of `error_reason` (`:996-1012`); `actions/contract.py:184` (`e` is a loop variable); `runtime/agent_loop.py:801`; and the TB-1 hits `cli.py:32` and `:82`. That is about 70 in all. STOP stays at more than 80 (PENDING LEAD 18), so the margin is about 10."
- **Renames.** A hit on a name `e`, `exc`, `err` or `ex` that is not an exception is fixed by renaming the variable (for example `actions/contract.py:184` `e` becomes `msg`). That is a fix in `src/`, not a waiver. Evidence 5 lists every rename with the line. A rename of a variable that holds a REAL exception, made to escape SRC-3, is a review defect: the result reviewers check every rename in the list.
- Add `actions/contract.py` to Files and to the hot files (PENDING LEAD 12). It is also BN-4's file.

**BN-10. Round9, round8 and round12_fuzz tick driver, and the refusal spelling matrix (R3-ADV-6, R3-ADV-11).**
- In `tests/test_k5_round9.py`, define `_tick(s, rq)`:
  - `store = MemoryStore()`;
  - `ctx = TickContext(app=types.SimpleNamespace(store=store), now=datetime(2026, 1, 1, tzinfo=UTC))`;
  - `step = TickStep("probe", 0, fn)`, where `fn` raises `ValueError(f"a {s} b")`;
  - `caplog = rq.getfixturevalue("caplog")` at level ERROR, then `tick_mod._run_step(ctx, step)`;
  - return `store.get_tick_state("probe").last_error + "\n" + "\n".join(r.getMessage() for r in caplog.records)`.
  - `_run_step` reads only `ctx.app.store` and `step.interval` (`tick.py:296`, `:300`).
- The "tick error message" `DRIVERS` entry becomes `_tick`. Its closed-text check is `grammar_ok` on the first line and on the text after `message=` in the second line.
- `tests/test_k5_round8.py:73` and `tests/test_k5_round12_fuzz.py:132` use the same driver, imported from round9 or copied as a 6-line helper. The builder picks one and says which.
- New test `test_own_tool_refusal_masks_every_spelling` in `tests/test_k5_round9.py` (it is not a `DRIVERS` row, because `test_there_is_a_driver_for_every_registry_row` pins `DRIVERS` to `PRODUCERS`). For each spelling: `tools_mod.error_reason(tools_mod._refusal(f"a {s} b"), [])`. The test asserts no needle, AND a placeholder is present or the output passes `grammar_ok` (a non-ASCII spelling falls back to the diagnostic). Under NEEDS LEAD 24 (c) the refusal is built with `ToolRefused(...)`.

**BN-11. FB11 reads the audit as an existing test does (R3-COR-10).**
- FB11 (ticket :414) reads: "the score-report write raises a dynamically named `OSError` subclass. The test follows `tests/test_k1b_cli.py:196-216`: monkeypatch `k1b.atomic.atomic_write`, run the score command, read `LocalDirSink(cfg_dir / "audit").events()`, and assert that the made-up name is absent from the failed event's `error_code`. On the base it is present (`cli.py:268-269`)."
- Delete "How the fake audit is read in a test is UNVERIFIED" there and in Verified (ticket :680).

**BN-12. Where the guard's code lives, for its mutants (R3-ADV-10).**
- The rule table, the scanner and `SAFE`/`SAFE_BODIES` live in `tests/taint_guard_rules.py`, an importable helper next to `tests/k5_support.py`. `tests/test_taint_guard.py` imports it and holds the tests. Add the file to "Create" (5 files).
- M18-M21, M23, M29 and M39 target `tests/taint_guard_rules.py`.
- **First build step:** the builder checks that P1m's runner can mutate a file under `tests/`, and that the killer test file runs in each mutant run. If either fails, the builder applies each of these 7 mutants as a hand patch in a throwaway worktree, runs the killer file once per mutant, and pastes the pytest exit code and the failing assertion. No new runner is written.

**BN-13. Small fixes (R3-COR-14, R3-COR-15, R3-COR-4 is in BN-14).**
- Site counts (ticket :178, :329, evidence 4, Couplings P5b2): `tools.py:120` is a row (`P5b2.md`, its line 40, says it is locked FOREIGN), so the count is 18. The builder still checks the row exists in the regenerated table. If it does not, that is a STOP, not a switch to 17.
- Relay to P5b2 (Couplings): the sentence at `P5b2.md:40` "P5b3 rewrites this place with `from_cause`" is stale. P5b3 rewrites it to a plain message with `validation_text`, and the row becomes OPERATOR under the not-taint rule.
- Evidence 7 gains: "for every `src/` module that gains an import from `hadavin_sdk.guard.diagnostic`, `uv run --all-extras --group test python -c "import hadavin_sdk.<module>"` exits 0, one fresh process per module. If one fails with an import cycle, that import moves inside the function, as in `errors.py`." Delete "UNVERIFIED" on the `errors.py` cycle (ticket :129, :677), and keep the function-local import there.

**BN-14. Counts and words (R3-ADV-8, R3-COR-4, R3-COR-5).**
- Ticket :106: "the three rows stay in `PRODUCERS`" becomes "the four rows stay in `PRODUCERS`".
- Ticket :342 and PENDING LEAD 21: "11 references in 6 files" becomes "11 call lines in 5 files, plus 1 comment (`tests/test_k5_producers.py:143`)".

**BN-15. New totals (defaults: NEEDS LEAD 24 (a), 25 (b)).**
- Fail-before rows: 14 become **16** (FB15, FB16).
- Mutant rows: 33 become **41**. M27 is replaced by M27a-d (+3), M3 by M3a and M3b (+1), and M40, M41, M42 and M43 are new (+4).
- Guard rule ids: 20 become **22** (OBJ-3, TB-1).
- New test files: 4 become **5** (`tests/taint_guard_rules.py`, a helper).
- New head rows: `test_tick_writer_survives_hostile_exceptions`, `test_own_refusal_raised_in_the_body_thread_keeps_its_sentence`, `test_tool_refusals_are_built_by_the_factory`, `test_own_tool_refusal_masks_every_spelling`, 3 `test_own_text` rows and 8 guard unit rows.
- Source files added to Change: `actions/contract.py`.
- PENDING LEAD: 23 become **26**.
- Other answers:
  - 24 (c): 15 FB rows and 38 mutants.
  - 25 (a): 15 FB rows and 40 mutants.
  - Both: 14 FB rows and 37 mutants.

## Positions
- **One CONTEST inside an accepted finding.** R3-ADV-1's option (b) ("`_call` wraps a body `ToolRefused`") is rejected with evidence the reviewer could read. The `ctx.secret` and fetch refusals at `tools.py:503-627` run in the body's thread and arrive through the same `raise err` (`:1134`), so (b) would also blank our own sentences. The reviewer said the same ("(a) is the cleaner one").
- **Flag, not private subclass, for BN-3.** A subclass would print `_OwnRefusal` wherever `class_name_of` names a refusal, and that is a format change. The flag keeps the class and its name as they are, and it needs no P5a code row (P5a's discovery test resolves through the base anyway). Against a careless tool author both give the same protection. Against a hostile one, neither helps (trusted in-process code, stated).
- **R3-COR-3: (b) over (a).** The echo carries no text the model did not write (keys are not restored, `runmap.py:564`), so it is not a leak today. But the studio rule says fix, do not document, and the fix is one line in a file BN-9 already touches, with no test pinning the old text. The cost: the model is told "unexpected key" without the name, and it can see its own arguments and the schema.
- **R3-ADV-4: option 1 (mutant definition) over option 2 (changing the producers test).** Changing `any` to `all` is a stronger test, but it still cannot see a duplicate call of `render`. BN-7 removes the duplicate call instead, and the partial removals have behavioural killers.
- **R3-ADV-2: module ban, with no allow-list.** A pinned allow-list would be a waiver in all but name, and the ticket has none (PENDING LEAD 15). No `src/` file needs `traceback` after P5b3.
- **Order 8 (cut surface).** BN-7 deletes a duplicate `render` call. BN-4 deletes model text from an error at its source instead of documenting it. BN-12 writes no new runner. BN-13 deletes three hedges. No new kind, module in `src/` or public name is added: `_refusal` is private.

## Couplings
- BN-2 and BN-7: the tick handler calls `render` once and touches `exc` only through `diagnose` and `class_name_of`. The crash rows prove both.
- BN-3, BN-5 and BN-10: the `ToolRefused` spoof row sets the flag (BN-5), so M8 is killed by identity alone, and the round9 refusal test uses `_refusal` (BN-10).
- BN-3 and BN-4: under both defaults, the model's refusal text holds only fixed words, manifest values, names chosen in the tool's code and configured source names.
- BN-4 and BN-9: both edit `actions/contract.py` (`:181`, `:184`); one hot-file entry.
- BN-6 and P5b4: TB-1 bans `traceback` in `src/`. P5b4's hooks are assignments to `sys.excepthook` and the like, and they are not flagged. If P5b4 needs the module, it goes to the lead (BN-6).
- To P5a (relay): its coupling "P5b3 adds its own `token40` constructor (BN-14)" is moot, because P5b3 cut `token40` (V14). P5a's "empty at P8b" for `OLD_WRITER_CRASHES` is met at P5b3 (BN-2).
- To P5b2 (relay): the stale `P5b2.md:40` sentence (BN-13). P5b2's BN-3 raiser rows and BN-14 (`STOP: FOREIGN=<n>` at 31 or more) feed P5b3's FOREIGN work list unchanged: every FOREIGN row is still rewritten or is a STOP. P5b2's BN-11 says `bundle.py:190` "control characters are not escaped here (P5b3)". On the `refused:` line, `own_text` check (e) already turns such a text into the diagnostic (UNVERIFIED where else that text is printed).
- To P5b4 (relay): the P5b3 text now says `output_guard.emit` and drops the `run_tick` move (BN-1), which answers P5b4's couplings (1) to (3).
- To the lead's F6 table: add P5b1 to `llm/anthropic.py` (BN-1); add `actions/contract.py` for P5b3 (BN-4, BN-9).
- To `handover/owner-visible-limits.md`: entry 2 below, appended by the lead or the next author (this step edits no other file).

## PENDING LEAD (continuing the ticket's numbering after 23)
- **24. NEEDS LEAD (redaction path): a `ToolRefused` built by a tool's own code sends its text to the model (R3-ADV-1).**
  - Default meanwhile: (a).
  - (a) RECOMMENDED: own sites build refusals through the private `_refusal` factory, which sets an instance flag. `own_text` keeps the sentence only with the flag. Anything else gives the diagnostic. FB15, M40-M42 (BN-3).
  - (b) `_call` turns any `ToolRefused` from the body into class-only text. Not recommended: it also blanks our own `ctx.secret` and fetch refusals, which come by the same path (Facts).
  - (c) Keep revision 3 and add an owner-visible limit ("a tool's own error message can carry any single-line ASCII text, including a person's name, to the model").
  - Confidence 80%. Reversible (text and one private function).
- **25. NEEDS LEAD (redaction path): argument key names the model wrote are echoed in `arguments invalid` (R3-COR-3).**
  - Default meanwhile: (b).
  - (a) Accept, and append owner-visible entry 2 with variant (a).
  - (b) RECOMMENDED: `schema_errors` prints `unexpected key` with no name. FB16, M43 (BN-4).
  - Confidence 75%. The echo carries only text the model wrote (Facts), so (a) is defensible. (b) is one line and removes the path. Reversible.
  - **Owner-visible entry 2, ready to append** (the base text holds under (b); under (a) add the last bullet):
    > ## 2. What the AI model is told when a tool call fails
    >
    > Added <date> (UTC and IST).
    >
    > - **What can go wrong.** When a tool the AI uses fails, the program tells the AI a short reason so that it can try again. If the reason held text from a document or a reply from another system, a person's name could reach the AI that way.
    > - **What the program checks.** For a failure in the tool's own code, the AI is told only the kind of error (for example "ValueError (tool error)"), never its message. For a refusal written by our own core (a host, port or secret that is not allowed), the AI is told our fixed sentence, which can name the host, port, operation or secret name from the tool's settings. A sentence that is not plain one-line text is replaced by a short coded line.
    > - **What it does not check.** A tool's program code is trusted. A tool written to do so can still put its own words in front of the AI, in an error or in its normal result. Its normal result is masked as today, but a name that the masking does not recognise passes.
    > - **What a person must do, and when.** Before the first pilot with real client data, a person reviews every tool module the client's agents use and checks that none of them passes document or system text into an error on purpose.
    > - (Only under answer (a).) **Also:** when the AI calls a tool with a wrong argument name, the error repeats that name back to the AI. The name is the AI's own text; nothing new is revealed.
    > - Studio reference: package P5b3, decisions 24 and 25, build notes BN-3 and BN-4 of the round 3 resolve, follow-up row P5b3-V15.
- **26. INFORM: guard and test changes with no owner rule** (R3-ADV-2, -3, -4, -10, R3-COR-1, -2). These are TB-1 (module ban, no allow-list), the OBJ-2/OBJ-3 split, M27a-d with a single `render` call, `OLD_WRITER_CRASHES == {}` at P5b3 with a STOP if a crash row still crashes, the per-place canary table, and the guard engine in `tests/taint_guard_rules.py`. Proceeding with these. Reversible before the build starts.
- **PENDING LEAD 18 is unchanged** (STOP above 80 base hits). Only the stated margin changes, from about 20 to about 10 (BN-9). If the lead wants a margin of 20 back, the number to choose is 90. I do not recommend it, because the number is a re-plan trigger, not a limit.

## Counts
- Finding ids 27 (ADV 12, COR 15). Majors 7 (ADV-1 to ADV-4, COR-1 to COR-3). No Blocker. No round 4 (order 20 item 6).
- PROPOSE FIX 24:
  - ADV-2 to ADV-11 (10);
  - COR-1, COR-2, COR-4 to COR-15 (14).
  - Duplicates merged inside them: ADV-3 = COR-12, ADV-5 ≈ COR-6, ADV-7 ≈ COR-7, ADV-8 = COR-5, ADV-9 = COR-11.
- ESCALATE 2 (ADV-1 as NEEDS LEAD 24, COR-3 as NEEDS LEAD 25). DECLINE 1 (ADV-12). CONTEST 0 (one option inside ADV-1 is contested with evidence; the finding itself is accepted). Check: 24 + 2 + 1 = 27 (`python3 -I`).
- Own finding: R3-RES-1 (a bare `traceback.print_exception(exc)` statement has no sink), folded into BN-6.
- Build notes 15 (BN-1 to BN-15). New totals under the defaults: 16 FB rows, 41 mutants, 22 guard rule ids, 5 new test files, 26 PENDING LEAD items (BN-15 has the variants).
- Fixes applied to the ticket in this step: 0 (they are build notes). Remaining unaddressed findings: 0.
