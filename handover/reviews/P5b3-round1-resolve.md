# P5b3 round 1 resolve (ticket revision 1)

- **Status:** RESOLVED (AUTO mode). This file holds the decisions only. The ticket is NOT edited: revision 2 applies this table. Nothing was committed or pushed.
- **Target:** `tickets/P5b3.md` revision 1, the full file (352 lines).
- **Findings:** `reviews/P5b3-round1-adversarial.md` (R1-ADV-1..13: 5 Majors, 6 Minors, 2 Nits) and `reviews/P5b3-round1-correctness.md` (R1-COR-1..18: 6 Majors, 9 Minors, 3 Nits). Neither report has a Blocker. I also add six findings of my own (RES-1..6). Both reviewers missed them because neither read `tickets/P5a.md`.
- **Gate:** order 20 item 6. This is a redaction package, so it may take at most 3 ticket-review rounds counting from round 1, plus one more round only if round 3 has no Blocker and at most 2 Majors. **Round 2 is next.** The "What round 2 needs" section says what it needs.
- **Facts I checked myself** (by reading files and running `git show cd2243f:<path>`; I ran no tests):
  - **Test files and producer rows.**
    - Five test files call `tick_mod._message`: `test_k5_round7.py:42`, `test_k5_fixes3.py:120`, `test_k5_round8.py:73`, `test_k5_round9.py:196` and `test_k5_round12_fuzz.py:132`.
    - `extract.py` is registered only by the `PRODUCERS` row "extract validation errors" (`guard/producers.py:36`).
    - `test_each_producer_calls_its_redaction_function` checks only for a DIRECT call to a name in column 4. The choke-point walk runs over `CHOKE_FAMILY` alone.
    - `test_k5_round9.py:204` checks the `PRODUCERS` key set.
    - The format grep (`error_kind=`, `refused: `, `tick: config error`, `last_error`) gives 10 lines in **6** files.
    - `test_k1b_cli.py:188` (`test_debug_env_prints_the_traceback`) asserts that `Traceback` is printed.
  - **Source on `cd2243f`.**
    - `guard/runmap.py:523` on `cd2243f` IS `raise RedactionError(type(exc).__name__) from None`. On the working copy, which matches `ce70eb5`, that line is `:476`.
    - `registry.py:329` `out.append(str(exc))` takes the text of our own `ConfigError` from `tools.module_sha256`.
    - `audit/chain.py:357` puts `type(exc).__name__` into `problems`, and `cli.py:354` prints it to stdout.
    - `tools.py:618-620` holds `code = exc.code` and then `f"HTTP {code}"`.
    - `config.py:43` is the helper `_money`.
    - `Principal` is defined at `identity.py:10`. `registry.py:33-62` holds `Budget`, `AgentRecord` and `Chain`.
    - `backends/table.py:386` `TABLE` holds the closed set of capability names. `AnthropicSettings.platform` is `Literal["api", "vertex", "foundry"]` (`table.py:44`).
  - **Main has moved.** `origin/main` is now `4ec3616`. Between `cd2243f` and `origin/main`, `src/` changed only in `approvals/gate.py` and `guard/redact.py`. P5b3 changes neither file.
  - **What P5a revision 3 changed.** P5b3 revision 1 was written against P5a revision 1 plus its resolve. P5a revision 3 has since:
    - CUT `token40` (`P5a.md:29`, `:64`);
    - CUT `chain` and `dropped_facts` from `Diagnostic` (`:63`);
    - reduced `validation_text` to `validation_text(exc)`, one argument, which prints closed type names only, prints no `loc`, and calls `errors()` with `include_context=False` (`:68`, `:77`);
    - created `tests/test_diagnostics_old_writers.py` as strict expected-failure rows that P5b3 must flip (`:7`, `:171`, `:215`).
  - **What P5b2 revision 3 changed.**
    - The 13 class-name rows stay locked `FOREIGN` (`P5b2.md:199`).
    - No carry is built. Those rows come back as new rows that the P5b3 builder labels (`:200`).
    - The `code` column is cut (`:204`).
    - `from_cause` calls are not sites (`:64`, `:201`).
- **Honest note (read first):**
  1. I invoked `egm:egm-resolve` through the Skill tool. Following the brief, I skipped the skill's interactive gate and its Step 5, the edit of the target. The skill's default output, `goldfish_review_report.md`, is replaced by this file.
  2. Four decisions go beyond what the reviewers asked for, because the facts that P5a revision 3 changed make the revision 1 interface impossible. They are:
     - replace `from_cause` with plain messages (PL13);
     - cut D8 (PL14);
     - cut the waiver file (PL15);
     - widen the guard's attribute rule (RES-4).

     Each one changes the shape of the ticket, so each is PENDING LEAD with my recommendation. If the lead overrules PL13, the fallback for each finding it touches is written in that row.
  3. Thirty of the 31 reviewer findings are accepted as fixes, and one is contested. That ratio is high, but each acceptance below rests on a fact I checked myself, not only on what the reviewer said. Two rows, ADV-4 and ADV-5, turn down part of the reviewer's proposed fix and give the reason.
  4. Not checked:
     - the taint-guard hit total (no guard exists);
     - whether `errors.py` can import `guard/diagnostic.py` without an import cycle;
     - P5b1's final `llm/retry.py`;
     - the reviewers' count of 11 interpolating validator lines (I read the 21 `raise` lines but did not open each multi-line message);
     - the drivers in `test_k5_round8.py` and `test_k5_round9.py` beyond the lines cited.
  5. One residual risk can only be accepted, not removed by code: an ASCII secret or name inside a mislabelled `OPERATOR` row still prints on the `refused:` line. It is PL19, and the owner should see it.

## Decisions (one per finding id; revision 2 applies each)
| id(s) | category | decision for revision 2 |
|---|---|---|
| R1-ADV-1 (Major) | PROPOSE FIX | M6 survives FB1 and FB2. Under PL13, path (1) of `_refusal_text` is gone. Re-point M6 to these rows: the ESC/U+202E/U+2028 rows, the test-module-subclass row, and a NEW row that raises a plain `ConfigError(f"... {non_ascii} ...")` and expects the rendered diagnostic. Add the table rule "a killer must FAIL ON THE MUTANT, not only on the old code". I re-checked M1-M5, M14 and M15 under that rule: each killer still differs between the mutant and the correct code. |
| R1-ADV-2 (Major) | PROPOSE FIX | Every fail-before row is named `test_fail_before_*`. Evidence command 2 runs `-k fail_before` over ALL the new test files. **FB8 is rewritten** as the guard's real-tree test (`test_taint_guard_real_tree_is_clean`). It fails by assertion on the base, which has today's hits, and passes at the head. The planted-source test becomes a plain unit test. New rows: **FB9**, a class-name raise site fed a dynamic class (`tools.py:397`, the module-load path), so the `refused:` line shows the name on the base; **FB10**, one `Delivery.reason` place (`app.py:192`); **FB11**, the audit `error_code` (`cli.py:268`); **FB12**, the receiver at DEBUG (`caplog` holds the request path canary); **FB13**, `audit verify` unreadable (`chain.py:357` to `cli.py:354`, stdout). The injection log is FB5 already. The D8 row is moot (ADV-5). Collection rule (P5a resolve ADV-A13): a fail-before test imports at module level only names that exist on the base. Names that are new at the head are imported inside the head-only tests. |
| R1-ADV-3 (Major) | PROPOSE FIX | The guard keeps "any call not on the SAFE list" as a TEXT sink. Redaction path, so the conservative rule stays, but it is now bounded by process rules. (1) **First build step:** run the guard on the base and paste the full hit list (evidence 5) before any sweep edit. (2) **Every hit is fixed in `src/`.** There are no waivers (PL15). A hit with no fix in `src/` is a STOP that goes to the lead. (3) **More than 80 hits on the base** is also a STOP: the lead re-plans before the sweep (PL18). (4) Add to the sweep: `registry.py:329`, which becomes `out.append(own_text(exc))`, and `audit/chain.py:357` (ADV-11). The estimate becomes "8-12 h if the first run shows at most 80 hits", stated as unmeasured. |
| R1-ADV-4 (Major) | PROPOSE FIX (the mechanical test is turned down) | (a) The paragraph at line 28 is changed to match limit (b): "no stored field or log line, and no `refused:` line from a FOREIGN place". (b) V1's trigger becomes concrete: "before the first pilot with real client data, the lead re-reads every `OPERATOR` row that interpolates a function parameter" (P5b2's own sampling rule). (c) The test that would allow only certain "name kinds" is NOT added. An AST cannot tell a secret's name from a secret's value inside the same variable. A rule keyed on variable names would give false assurance and could be dodged by renaming. The residual risk goes to PL19 for the lead and the owner. |
| R1-ADV-5 (Major) | PROPOSE FIX (the default split is turned down) | **Cut D8 to v1.1 (PL14).** One more fact supports the cut: P5a revision 3's `validation_text` calls `errors()` with `include_context=False` and prints no `loc` (`P5a.md:68`, `:77`). So the planned rule "`ctx["error"]` is an `SdkValueError`, print `<where>: ...`" would need a P5a design change. Removed with D8: `ConfigReason`, `SdkValueError`, the `OWN_CODES` row (P5b3 no longer edits `codes.py`), the 21 validator edits (P5b3 no longer edits `backends/table.py`), the `validation_text` rule, M16, M17 and `tests/test_sdk_value_error.py`. No leak opens: P5a prints a bare `value_error`. Row V5 is rewritten as "SdkValueError reasons; trigger: an operator cannot fix a start-up error from code, type and count". **Cut the waiver machinery (PL15):** the waiver JSON, its expiry, `stmt_hash`, `TAINT_WAIVERS_MAX` and M22. Splitting the package by default is turned down: the cuts above (and PL13) make the PR smaller than revision 1's split halves. The fallback split stays (PENDING LEAD 11). |
| R1-ADV-6, R1-COR-4 (Minor, Major) | PROPOSE FIX | Both are true on P5a revision 3, which CUT `token40` altogether (`P5a.md:29`, `:64`). Under PL13 there is no `key` parameter: the operator part stays in the message as today, for example `backends.{cap} ({kind})`, and these are our own capability and kind names. If the lead overrules PL13, `key` becomes `SafeToken \| None`, built by the caller as `SafeToken.of(cap, frozenset(TABLE))` and `SafeToken.of(settings.platform, frozenset(get_args(...)))`, with one test row per call. |
| R1-ADV-7 (Minor) | PROPOSE FIX | Under PL13 each of the 5 places keeps its fixed words and operator part, and swaps only the pasted text. `config.py:120` keeps `backends.{cap} ({kind}):` and adds `validation_text(exc)`. `tools.py:120` keeps `{where}: invalid tool entry` and adds `validation_text(exc)` (the `loc` field paths are dropped, an accepted loss). `config.py:454` keeps its fixed words and adds `render(diagnose(exc, step=Where.config_load))`. `registry.py:224` keeps its fixed words and adds the same render with the step that fits. `llm/anthropic.py:56` keeps `backend llm 'anthropic' ({settings.platform}):` and adds the render. All five use `from None`. One golden line per place goes in the ticket. |
| R1-ADV-8, R1-COR-11 (Minor, Minor) | PROPOSE FIX | Combined with RES-4. Any attribute read of a tainted exception counts as TEXT, unless a SAFE call wraps it. So `tools.py:620` stays a hit and is fixed as `code = int(exc.code)`. `int` stays on the SAFE list, and the raise count stays 24 (floor). Revision 1's statement that `tools.py:620` is clean was wrong: the guard as written would not have flagged `exc.code`, and the same gap lets `.reason`, `.strerror`, `.filename` and `.problem` through. |
| R1-ADV-9 (Minor) | PROPOSE FIX | `test_receiver_logs_nothing` lives in `tests/test_p5b3_writers.py` (named in the "Create" list). M9 mutates `tools/gen_config_error_sites.py`, so it runs through P5b2's own pattern (`tests/config_error_sites_mutants.py`: a tree copy, `P5b2.md:132-133`) and is added there as a P5b3 row. It is not run by P1m's runner on `src/`. |
| R1-ADV-10 (Minor) | PROPOSE FIX | The CHANGELOG and rollback text list every changed format: every `refused:` place that printed an exception class or library text; `failed:` (the class name is replaced by the diagnostic); `could not verify:` on both streams; `last_error`; the tick log `message=`; `DeadLetter.errors` and the retry prompt; `Delivery.reason`; audit `error_code`; the `HADAVIN_DEBUG` output. It also lists the cost from COR-5: an own message with a non-ASCII value now prints the diagnostic. |
| R1-ADV-11 (Minor) | PROPOSE FIX | Checked. `result.problems` is built in `audit/chain.py`. `:357` carries `type(exc).__name__`, which joins the sweep and becomes `class_name_of(exc)` (FB13). The other entries are fixed words and sequence numbers. `:502` uses `names[i]!r`, an anchor object name read back from storage. That is stored data, not an exception, so it is outside the guard's sources and is listed under V4. |
| R1-ADV-12 (Nit) | PROPOSE FIX | The field reads: "one pull request; split into P5b3-a and P5b3-b only if result-review round 2 still has a Major". |
| R1-ADV-13 (Nit) | CONTEST | Both files exist. `studio-notes/design-v3-FROZEN-amendments.md` holds D1-D16, the D-numbers the ticket cites. `studio-notes/amendments.md` holds plan-v3's A-numbers. Line 17 names the correct file for "D-number". No change. |
| R1-COR-1 (Major) | PROPOSE FIX | List all 5 files in "Change" and in evidence command 1. Replacements, each driven through the real `_run_step` with a fake failing step: `test_k5_round7.py:41-42` becomes "the canary is absent from `last_error` and from the log line, and the line passes `grammar_ok`". `test_k5_fixes3.py:112-120` becomes "a 1 MiB message gives `len(last_error) <= DIAG_LINE_CHARS`". The `round8`, `round9` and `round12_fuzz` drivers call `_run_step` instead of `_message`. Each replacement is stronger, and no test is deleted. |
| R1-COR-2 (Major) | PROPOSE FIX (a different fix from the reviewer's) | The three rows do NOT move. They stay in `PRODUCERS` with new columns 3 and 4: `("injection screen log line", "guard/injection.py", "injection_check", {"render"})`, `("extract validation errors", "extract.py", "extract", {"validation_text", "render"})`, `("tick error message", "runtime/tick.py", "_run_step", {"render"})`. Then `extract.py` stays registered, the `round9:204` key set is unchanged (only its tick driver changes, COR-1), and the existing direct-call test checks the rows. Cut: the `DIAGNOSTIC_WRITERS` tuple and its new test. M27's killer becomes `test_each_producer_calls_its_redaction_function`. The `_LOG` text and the module docstring get one sentence: "three rows are diagnostic writers; column 4 names the safe renderer". |
| R1-COR-3 (Major) | PROPOSE FIX | Use P5b2 revision 3's baseline. The 13 rows are locked `FOREIGN` (`P5b2.md:199`), and no carry exists (`:200`). Arithmetic: FOREIGN at the head = P5b2's reviewed FOREIGN count − 13 (class-name rows, relabelled) − 5 (the rewritten places) − the number of "FOREIGN, no cause" rows that P5b3 turns into fixed words (`:202`). Under PL13 the 5 places stay sites and come back as `OPERATOR` rows, so OPERATOR rises by 18 plus those rows. Every new row gets a builder label and a reason under Tier A review. Line 109's carry sentence is deleted. The exact numbers are UNVERIFIED until P5b2's reviewed table exists. |
| R1-COR-5 (Major) | PROPOSE FIX | `_refusal_text` (which becomes `errors.own_text`, see Couplings) no longer falls back to the diagnostic because of length. An own `ConfigError` whose text is printable ASCII is printed cut to `defaults.REFUSAL_CHARS` (2000, P5b3 block), with the marker ` [cut: N more chars]`. Cutting our own text cannot add a leak. A non-ASCII own text still falls back to the diagnostic: that backstop stays, its cost goes in the CHANGELOG and in PENDING LEAD 5, and a test row covers it. The builder pastes the longest static message template it finds. New test row: a `"; ".join` of 30 problems is kept, then cut. M7 stays, and a new mutant M28 ("no cut") is killed by the 1 MiB row. |
| R1-COR-6 (Major) | PROPOSE FIX | Depends on: add P4b1 and P4c (A4: "P4b before P5b3", "P4c after P4b and before P5b3"; F6 hot files `config.py` and `registry.py`) and P4a (F6, `llm/anthropic.py`). The merge order becomes: the order-20 chain (P4a included), then P4b1 and P4c, then P5a, P5b1, P5b2, **P5b3**, P5b4, P5b5. |
| R1-COR-7 (Minor) | PROPOSE FIX (made moot by ADV-5) | D8 leaves the package. Row V5 states "11 of the 21 messages interpolate values (the reviewer's count; the P5c-era builder recounts)". |
| R1-COR-8 (Minor) | PROPOSE FIX (made moot by ADV-5) | The validator list leaves the ticket. Row V5 notes that `config.py:43` `_money` is a helper. |
| R1-COR-9 (Minor) | PROPOSE FIX | Cite `registry.py:33-62` (`Budget`, `AgentRecord`, `Chain`), `identity.py:10-11` (`Principal`, used by FB1) and `actions/contract.py:47`. |
| R1-COR-10 (Minor) | PROPOSE FIX (the cite part is CONTESTED) | The cite `runmap.py:523` is correct on the ticket's base `cd2243f` (`git show cd2243f:src/hadavin_sdk/guard/runmap.py` line 523). The reviewer's `:476` is the `ce70eb5` working copy. The wording part is accepted: the text of `evals.py:67` is a foreign class name produced at `runmap.py:523`. So the sweep fixes `runmap.py:523` before `evals.py:67`'s message is called operator-safe. Line 100 is reworded. |
| R1-COR-12 (Minor) | PROPOSE FIX | Cite `llm/retry.py:79` (where `describe` builds `type(exc).__name__`) plus the raises at `:99` and `:101`. P5b1 owns the file; P5b3 fixes it only if the text is still present on P5b3's base. |
| R1-COR-13 (Minor) | PROPOSE FIX | PENDING LEAD 1 is closed by order 21 item 17: the standing S0 EXIT applies to P5b3 after its freeze and its build-start review. |
| R1-COR-14 (Minor) | PROPOSE FIX | `codes.py` leaves P5b3's file list completely, because the D8 cut removes P5b3's only `OWN_CODES` row. Where `codes.py` is mentioned, it says P5a creates it. |
| R1-COR-15 (Minor) | PROPOSE FIX | "Problem in plain words" is cut to 4 sentences. The file and line detail moves to Interface. |
| R1-COR-16 (Nit) | PROPOSE FIX | Under PL13 the `args[0]` bound has nothing to attach to and is deleted. If PL13 is overruled, it is stated as `len(summary) + 3 + DIAG_LINE_CHARS`. |
| R1-COR-17 (Nit) | PROPOSE FIX | Write "10 lines in 6 files" (checked). The noisy second count ("20 files") is dropped. The migration table comes from the builder's own grep. |
| R1-COR-18 (Nit) | PROPOSE FIX | Write "Extended review: no round cap on result review; ticket review follows order 20 item 6". |
| RES-1 (Major, found by me) | PROPOSE FIX | The ticket uses names that P5a revision 3 cut or changed: `token40`, `dropped_facts`, `d.chain` (debug branch), and `validation_text(exc, root=schema)` (extract). Fixes: extract calls `validation_text(exc)`; the debug branch prints one rendered line and no chain (RES-6); the `token40` lines go (ADV-6). The Depends field cites P5a revision 3 and P5b2 revision 3 (RES-5). |
| RES-2 (Major, found by me) | PROPOSE FIX | P5a revision 3 hands P5b3 the job of flipping every strict expected-failure row of `tests/test_diagnostics_old_writers.py` to a plain assert, and of composing T6's two outputs (`P5a.md:171`, `:215`). Add that file to "Change", to evidence command 1 and to "Done". A row left as expected-failure fails the run when it starts to pass, and P5a's `test_old_writer_marks_follow_their_later_row` checks this. |
| RES-3 (Minor, found by me) | PROPOSE FIX | `tests/test_k1b_cli.py:188` `test_debug_env_prints_the_traceback` fails once `print_exc` is removed. P5b3 rewrites it as P5b4 planned (`P5b4.md:154`): "boom" is absent, `Traceback` is absent, and one Grammar A line is present. The rewrite moves from P5b4 to P5b3 (see "Debug branch"). |
| RES-4 (Major, found by me) | PROPOSE FIX | The guard's TEXT list names some attributes (`.args`, `.msg`, `.message`, ...) and lets every other attribute through. That lets `exc.reason` (URLError), `.strerror`, `.filename`, `.problem` (YAML), `.text` (SyntaxError) and `.doc` pass. New rule: **every attribute read of a tainted exception is TEXT**, unless the read is wrapped in a SAFE call (`int(exc.code)`, `isinstance(exc.reason, X)`). New guard unit rows for `.reason` and `.strerror`. New mutant M29 (the attribute rule goes back to the listed attributes only), killed by the `.reason` row. |
| RES-5 (Minor, found by me) | PROPOSE FIX | The Depends field cites stale revisions. Revision 2 depends on `tickets/P5a.md` revision 3, `tickets/P5b2.md` revision 3 and `tickets/P5b1.md` as current, each marked "not yet clean". Main is now `4ec3616`. Since `cd2243f`, `src/` changed only in `approvals/gate.py` and `guard/redact.py`, and neither is in P5b3's list. |
| RES-6 (Minor, found by me) | PROPOSE FIX | The `failed:` hint reads "(set HADAVIN_DEBUG=1 for the cause chain)", but the chain is cut (P5a). New text: `failed: <render(diagnose(exc, step=Where.cli))>`. Under `HADAVIN_DEBUG=1` the branch prints the same single line and no traceback. New v1.1 row V8: "debug cause chain as one rendered line per link; trigger: an operator cannot locate a crash cause from `at=` and `fp=`". |

## Positions (the larger shape decisions, with the reasons)
- **PL13: `from_cause` is replaced, not narrowed.** Every reason for `from_cause` is gone, or simpler without it:
  - its `key` fact needed `token40`, which P5a cut;
  - its literal `summary` lost the operator part (ADV-7);
  - its path (1) in `_refusal_text` is what let M6 survive (ADV-1).

  The replacement: each of the 5 places becomes `ConfigError(f"<fixed words> <operator part>: {validation_text(exc) | render(diagnose(exc, step=...))}") from None`. The text is closed by P5a's own guarantees, and the operator keeps the file, capability or platform name. What this removes: `from_cause` itself, `_hd_diagnostic`, the `summary` `TypeError`, guard rules F1 and F2 (the 5 places carry `from None`, and a test checks `__cause__ is None`), M10-M13 and M24, and the `from_cause` special case in P5b2's interface. The new mutants are M10' ("a rewritten place puts `str(exc)` back", killed by FB1 and FB2) and M11' ("`from exc` instead of `from None`", killed by the `__cause__` row). The P5b2 generator rule widens from "`class_name_of(NAME)` does not taint" to "a call to `class_name_of`, `validation_text` or `render` does not taint, whatever its arguments", stated once in `tainted_names`. This deviates from frozen D7, so it is PENDING LEAD. It supersedes PENDING LEAD 3.
- **`own_text` instead of a private `_refusal_text`.** `registry.py:329` needs the same own-text gate as the CLI. So the gate becomes `errors.own_text(exc) -> str`, with these rules: our own `ConfigError` subclass by P5a's identity rule, exactly one `str` argument, printable ASCII, cut at `REFUSAL_CHARS`; anything else gives `render(diagnose(exc, step=Where.cli))`. The four CLI sites and `registry.py:329` call it, and it goes on the guard's SAFE list. `errors.py` imports `guard/diagnostic.py` inside the function: an import cycle check is UNVERIFIED. It stays one function in a hot file. D8's classes leave that file.
- **Guard bound (ADV-3).** The rule "any non-SAFE call is a sink" stays, because narrowing it to "calls that leave the process" would miss a helper that logs text it received. The bound comes from process instead: a base run first, no waivers, a STOP on an unfixable hit, and a STOP above 80 hits. A count is not a design reason to weaken the sink set.
- **Debug branch: P5b3 should own it, and P5b4 should follow.** Reasons:
  1. Two earlier documents already give it to P5b3: `P5a.md` (sink list) and `reviews/P5b1-round1-resolve.md` ADV-A14. Only `P5b4.md:334` disagrees.
  2. P5b3 merges first. P5b1 deliberately keeps the raw provider error as `__cause__`, and `traceback.print_exc()` prints it. If P5b4 owned the branch, that leak would stay open through the P5b3 merge.
  3. P5b3's claim "no own line carries foreign text" is false while `print_exc` remains.
  4. The edit is two lines plus one test rewrite (RES-3).
  5. P5b4 already wrote the fallback: "If P5b3 already rewrote `cli.py:81-82`, P5b4 only adds rows U20 and K29" (`P5b4.md:319`). That also answers `reviews/P5b4-round1-correctness.md` R1-COR-1 and R1-COR-2: the U20/K29 fail-before moves to P5b3 FB7, and P5b4 keeps the `main()` wrapper structure (`BaseException`, exit code 130, `SystemExit`).
- **D8 cut (PL14).** It is a usability feature, not a redaction fix. Without it, a validator's sentence is lost. With it, P5a's `validation_text` would have to read `ctx` (a P5a design change). That cost is stated; it is not hidden.

## Couplings (other tickets that must follow)
- **P5a (revision 3):** no change asked. P5b3 consumes `diagnose`, `render`, `class_name_of`, `validation_text(exc)`, `Where.cli`, `Where.extract`, `Where.scan`, `Where.config_load`, `StepToken.of`, the corpus, `grammar_ok` and `leaks`. P5b3 takes up the flip of `test_diagnostics_old_writers.py` and the T6 composition (RES-2). It takes up neither `token40` nor `FIXED_TEXT`.
- **P5b2 (revision 3, round 3 next):**
  - (a) under PL13 the special case "a `from_cause` call is not a site" (`P5b2.md:64`, `:201` and its PENDING LEAD 7) can be cut;
  - (b) the not-taint rule that P5b3 adds covers `class_name_of`, `validation_text` and `render` calls;
  - (c) `node_hash` for waivers is moot (PL15);
  - (d) the 5 places stay rows (OPERATOR) instead of dropping out.

  The lead relays (a)-(d) to P5b2's round 3 resolve.
- **P5b4:** the debug branch goes to P5b3, as recommended above. P5b4 drops its rewrite of `test_k1b_cli.py:188` (`P5b4.md:154`) and its FB for U20, and keeps U20 and K29 as regression rows. U20's "one Grammar A line" matches RES-6. P5b4's line `:148` (the four tick writes go through `handle.emit`; "their text is P5b3's") is unchanged.
- **P5b1:** `llm/retry.py:79`, `:99` and `:101` (COR-12). If P5b1 already fixes them, P5b3 does nothing there.
- **P4b1, P4c, P4a:** merge before P5b3 (COR-6). The lead adds this to the order table.
- **P5c:** owns row V5 (D8) if its trigger fires, together with `FactKey.reason` (`P5a.md:195`).

## PENDING LEAD (continuing the ticket's numbering; recommendations first)
- **1:** CLOSED by order 21 item 17 (COR-13).
- **3:** superseded by 13.
- **6:** superseded by 14.
- **12:** changed. Remove `codes.py` and `backends/table.py` from P5b3's hot files. Add `registry.py:329` (already a P5b3 file). Keep `runtime/agent_loop.py`, `app.py`, `store/postgres.py`, `tools.py` and `guard/runmap.py`.
13. **Replace `from_cause` with plain messages that carry `validation_text` or `render`, raised `from None` (Positions, PL13).** Recommended: yes. Alternative: keep `from_cause` with `key: SafeToken | None` (ADV-6 fallback), with M6 re-pointed as in ADV-1.
14. **Cut D8 (`SdkValueError`, `ConfigReason`) to v1.1 row V5.** Recommended: yes. Alternative: keep D8, which needs P5a to read `ctx` in `validation_text` (a P5a revision 4 change).
15. **Cut the waiver file and expiry. An unfixable guard hit is a STOP that goes to the lead.** Recommended: yes.
16. **The debug branch belongs to P5b3; P5b4 follows (Positions).** Recommended: yes. This answers P5b4's PENDING LEAD 6.
17. **`own_text` cuts our own text at `REFUSAL_CHARS = 2000` instead of falling back by length. Non-ASCII still falls back.** Recommended: yes. Alternative: no cap, which would let a 1 MiB own text reach the terminal.
18. **Guard STOP threshold: more than 80 hits on the first base run means the lead re-plans before the sweep.** Recommended: yes. The number is my choice and UNVERIFIED as best: the floor scan found 45.
19. **Owner-visible residual risk:** an ASCII secret, a URL with credentials, or a name inside a mislabelled `OPERATOR` configuration message still prints on the `refused:` line. The controls are P5b2's labelling, the Tier A sample, and the V1 re-read before the first pilot. The ASCII backstop catches only non-ASCII text and control characters. Recommended: the lead shows this to the owner the way order 19 B did. No mechanical fix exists without the cut `t1()`.

## What round 2 needs
- Revision 2 applies every row above. Where the lead has not yet answered PL13-PL19, it is written on my recommendation and those items are marked PENDING. Revision 2 also re-reads its cites on `origin/main` (`4ec3616`) and says so.
- Round 2 is two fresh reviewers, correctness and adversarial, run in parallel on one snapshot. They read revision 2, `tickets/P5a.md` revision 3, `tickets/P5b2.md` (latest), `tickets/P5b4.md` (latest) and the code. They do not read this file, per reviewer independence. They are told the round number and the cap.
- Suggested focus for round 2:
  - (a) the five PL13 rewrites and `own_text`, against the P5a guarantees;
  - (b) the attribute rule (RES-4) and the STOP rules;
  - (c) whether the fail-before set collects on the base and fails by assertion;
  - (d) the producers rows kept in place (COR-2);
  - (e) the cuts: whether D8 or the waiver cut leaves a real leak rather than lost detail.
- Cap: round 2, then round 3. A round 4 is allowed only if round 3 has no Blocker and at most 2 Majors (order 20 item 6, redaction package).

## Counts
- Findings: 31 from the reviewers (11 Major, 15 Minor, 5 Nit; no Blocker) plus 6 of my own (RES-1, RES-2 and RES-4 Major; RES-3, RES-5 and RES-6 Minor). Total 37.
- Categories:
  - PROPOSE FIX: 36. Four are made moot by cuts: COR-7, COR-8, COR-16 and part of ADV-2. Two turn down part of the reviewer's proposal: ADV-4 and ADV-5.
  - CONTEST: 1 (ADV-13), plus the cite half of COR-10.
  - ESCALATE: 0.
  - DECLINE: 0.
- New PENDING LEAD items: 7 (13-19). Changed or closed: 4 (1, 3, 6, 12).
- Surface cut by these decisions (if PL13-15 are accepted):
  - `from_cause` and its rules F1 and F2;
  - D8 (2 classes, 21 edits, 1 test file);
  - the waiver file;
  - `DIAGNOSTIC_WRITERS`;
  - two hot files (`codes.py`, `backends/table.py`);
  - mutants M10-M13, M16, M17, M22 and M24.
- Surface added: `own_text`, `REFUSAL_CHARS`, FB9-FB13, the attribute rule, and mutants M10', M11', M28 and M29.
