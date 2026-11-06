# AK4a round 3 resolve (egm:egm-resolve, AUTO mode; LAST round)

## Honest note (what I did NOT check, first)
- **No test, mutant, build or install was run.** I wrote no git state. I did not edit the ticket, commit, push, or touch `DECISIONS.md` or `owner-visible-limits.md`.
- **What I did run:** four read-only probe scripts with the repository's virtual-environment interpreter (`python -I`, Python 3.13.18), run from a scratch folder with `<repo>/src` put on `sys.path`. I also ran one `ruff check --isolated --select S` on a scratch file. These probes call core functions (`redact_bundle`, `runmap.redact_untrusted`, `k1b.loop._dumps`) on made-up values. They are probes, not ticket rows. H0 still has to run on the build head.
- **Python 3.12 was not probed.** Facts 2 and 3 hold on 3.13.18. The 3.12 `LogRecord` has no `taskName`. BN-2 computes its baseline at run time, so this does not matter, but I did not run it on 3.12.
- **Windows was not run** (BN-14). In particular, I did not check whether `os.dup2` on descriptors 1 and 2 also redirects the output of a child process on Windows.
- **Ticket names that are not in code yet** stay UNVERIFIED as the ticket lists them. These are AK1-a/b, P4a-2, P4b1-b (`metered.scope` is read from `tickets/P4b1.md:259` only), P4b2-a, P5c-2/3 and P6a-1.
- **PENDING LEAD 5 needs a number** that only the lead or the owner can give. Until they answer, the builder does not invent one (BN-4).

**Status:** resolved (categorised in AUTO mode, so the skill's interactive gate is skipped, per the lead's order 20 item 6 brief). The ticket is NOT edited. The fixes are build notes BN-1 to BN-19 below, and they win over the ticket text. This file replaces the skill's default file name `goldfish_review_report.md`.
**Target:** `handover/tickets/AK4a.md` revision 3, commit `831d013`, full file (428 lines). `git log -1 -- handover/tickets/AK4a.md` gives `831d013`, and `git status` shows no local change. `git diff --stat origin/main HEAD` over `evals.py`, `k1b/`, `models.py`, `guard/producers.py` and `tests/test_k5_producers.py` is empty, so the cites hold on `origin/main` `4ec3616`.
**Findings:** 24 ids.
- `reviews/AK4a-round3-adversarial.md`, R3-ADV-1..14: **1 Blocker** (ADV-1), **5 Majors** (ADV-2 to ADV-6), 7 Minors, 1 Nit.
- `reviews/AK4a-round3-correctness.md`, R3-COR-1..10: **3 Majors**, 5 Minors, 2 Nits.
- I took each severity from the report's table and changed none.
**Gate (order 20 item 6):** round 3 is the last normal round. A money, redaction or security ticket may take a round 4 only if round 3 had no Blocker and at most 2 Majors.
- Round 3 had 1 Blocker and 8 Majors. ADV-1 and COR-2 are one defect, so there are 7 distinct Blocker or Major defects.
- So there is **NO round 4**. The ticket freezes at revision 3 with this file attached. The banner below goes under the ticket's revision line.
- The build-start review (order 19 A, order 20 item 3) reads the ticket and this file together.
- Nothing is escalated to the owner. PENDING LEAD 5 is NEEDS LEAD (a security threshold). Items 6 to 9 are INFORM.

## Facts I checked myself (they decide rows)
1. **The k1b model input is one JSON line, and the case id is not in it.**
   - `k1b/loop.py:73-74`: `_dumps` is `json.dumps(sort_keys=True, ensure_ascii=False)`.
   - `:144-148`: the only user message is `_dumps({"alert": bundle.alert, "alert_time": ...})`.
   - `Bundle` (`k1b/bundle.py:91-100`) also holds `case_id`, but the loop never sends it.
   - `alert` keys are limited to `ALERT_KEYS` (`:44`). `labels` must be a dict of strings of at most 200 characters (`:229-235`), and each key passes `_scan`'s deny list (`:47-59`, `:162-173`).
   - So ADV-1 and COR-2 are TRUE.
2. **Probe: the marker survives masking.** The probe built a `Bundle` whose `alert.labels` is `{"harness_item": "item-case-001"}`, with a canary in `alert.title`.
   - `redact_bundle` masked the canary (`EMAIL: 1`) and left the label value unchanged. It also left unchanged a marker with an AK1-shaped id (`item-step-` plus 32 hex).
   - `_dumps` of the masked alert has no newline. `json.loads` gives back the exact label string.
   - `runmap.redact_untrusted("item-case-001\n... <canary>", {})` returns a `str` that still has the marker line and no longer has the canary.
   - The key `harness_item` matches no `DENY_KEY_PARTS` entry, and `sensitive("harness_item")` is False (`k1b/redaction.py:88-91`).
3. **Probe: M-H2 and M-H5 are equivalent mutants as written** (ADV-2 TRUE). I kept records through `setLogRecordFactory` for `log.info("%(a)s", {"a": 1, "b": C})` and for `log.exception` over an error whose text holds C.
   - For both records, `getMessage()` lacks C.
   - A `repr` scan over every value in `record.__dict__` FINDS C in both records.
   - A scan over only the keys that a fresh `logging.LogRecord(...)` does not have finds C in neither. On 3.13.18 a fresh record has 21 keys, `args`, `exc_info`, `exc_text`, `msg` and `stack_info` among them.
4. **`test_k5_producers.py` blocks AK4a-2 as written** (COR-1 TRUE).
   - `SINK_METHODS = {"chat", "apply_guardrail"}` (`:22`). The scan skips only `llm/` (`:87`).
   - `:97-107` requires every caller to be in `MODEL_CALLERS` (`guard/producers.py:55-65`) and to have a `PRODUCERS` row or an `OUTSIDE_THE_CHOKE_POINT` reason (`:67-70`).
   - So `testing/faults.py`, which calls `inner.chat`, fails the test unless it is registered.
   - Eleven other tickets also name `producers.py` or `MODEL_CALLERS`, so it is a shared file.
5. **H15's digest cannot repeat** (COR-3 TRUE).
   - `outputs_files` covers every file under `run*/` (`k1b/replay.py:78-82`), and `run.json` holds `replay_run_id` (`:232`), which is `new_id("k1b")` = uuid4 (`:135`, `models.py:23-24`).
   - The per-case records (`:180-222`) hold no run id.
6. **ruff S311 fires on `random.Random(f"{seed}:{k}")`** (COR-5 TRUE). `pyproject.toml:74` has `extend-select` with `S`.
   - `ruff check --isolated --select S` on a scratch file reports 1 error on that line.
   - It reports none on `int.from_bytes(hashlib.sha256(...).digest()[:8], "big") % 100`.
7. **`metered.scope` only sets a context variable** (`tickets/P4b1.md:259`): "a context manager that sets a `contextvars.ContextVar`; it is reset in a `finally`". Only `MeteredLLM.chat` reads it. So a scope opened around a plain fake changes nothing. This decides ADV-6.
   - `grep` over `tests/` finds 57 lines with `gate(` or `assert_qualified`, in 16 files. That matches ADV-6's count.
8. **Golden lines have an optional `id`.** `evals.py:68` falls back to `input_ref` when it is missing. `:45` parses the lines and checks nothing for uniqueness. So ADV-3 is TRUE. A trap passes only when the model abstains (`matches`, `:26-32`; `got` is `{"action": None}` when there is no tool call, `:82-92`).
9. **`eval_threshold` has no floor** (`config.py:322-324`: `gt=0.0, le=1.0`). `config_hash` includes it only below 1.0 (`registry.py:164-170`). So ADV-4's arithmetic holds.
   - Order 24 item 32 is about the P6b1 age limit ("a config field that may only shorten the limit ... thresholds come from config"). The ticket generalises it, and I keep that reading.
10. **The k1b wiring** (COR-7 TRUE).
    - `_replay` takes `detector: Detector`, `audit: K1bAudit`, `cause_list_dir` and `clock` (`replay.py:93-108`).
    - `K1bAudit(sink, principal=None)` wraps an `AuditSink` (`k1b/audit_sink.py:26-29`).
    - `case_timeout_s` defaults to 300 (`config.py:171`).
    - `Reply.model_id` is required (`models.py:295`).
    - The bundle and cause-list builders live in `tests/k1b_support.py` (`:141`, `:172`). `src` cannot import them.
    - `tests/test_k1b_replay.py:513-515` scripts the ticks `[0, 0, 299.99] + [1000] * 50`.
11. **Cite drift** (COR-10): the `eval_threshold` block is `registry.py:164-170`; the `abstain_rate` field is `models.py:274` (its comment is `:273`).

## Banner for the ticket (placed under the revision line, word for word)
> **BUILD NOTES WIN.** Review round 3 (`reviews/AK4a-round3-adversarial.md`, `reviews/AK4a-round3-correctness.md`) had 1 Blocker and 8 Majors, so there is no round 4 (order 20 item 6). This ticket is FROZEN at revision 3. The builder applies build notes BN-1 to BN-19 in `reviews/AK4a-round3-resolve.md`. Where a build note and the text below disagree, the build note wins. The build-start review (order 19 A) reads this ticket together with those notes. The CHANGELOG sections are history, not instructions. Totals after the notes: 49 test rows (AK4a-1 18, AK4a-2 21, AK4a-3 10) and 70 mutants (25, 34, 11). PENDING LEAD 5 (NEEDS LEAD: a pilot/prod floor for `eval_threshold`) is open. AK4a is not closed for money while F1 is open (BN-18).

## Decisions (one category per finding id)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Blocker), R3-COR-2 (Major) | PROPOSE FIX | TRUE (facts 1, 2). The k1b marker rides in `alert.labels["harness_item"]`. C-FAULT reads markers by line OR by JSON string value, with exact equality. H0 gains a clause on the real `FaultLLM.received` text of a k1b run. H12 gains an exactness clause on `case-001` against `case-0010`. Mutants M-H32 and M-H33 are added. **BN-1.** |
| R3-ADV-2 (Major) | PROPOSE FIX | TRUE (fact 3). The generic `__dict__` scan reads only the keys a fresh `LogRecord` does not have, so the dedicated args and `exc_info` scans are the only paths for those. M-H2 and M-H5 become real. No new mutant. **BN-2.** |
| R3-ADV-3 (Major) | PROPOSE FIX | TRUE (fact 8). In pilot/prod each line needs a string `id`, and the set must not repeat an `id`, an `input_ref` or a document's bytes. This is checked in the label phase. New row E16 and mutants M-E22 and M-E23. Dev is unchanged. **BN-3.** |
| R3-ADV-4 (Major) | PROPOSE FIX + NEEDS LEAD | TRUE (fact 9). Trap half (no number needed): when any line is labelled, every trap item must pass, as every easy item must. New real fail-before row E17 and mutant M-E24. Threshold half: a floor is a number only the lead or owner can choose, so it becomes **PENDING LEAD 5** (NEEDS LEAD), and Security states the gap until then. **BN-4.** |
| R3-ADV-5 (Major) | PROPOSE FIX | TRUE. In `meets_current`, counts of `None` or a missing bucket key count as zero, so the size rules fail. A stored run in pilot/prod whose `answerable` or `false_abstained` is `None` fails `false_abstain`. New row E18 and mutant M-E25. **BN-5.** |
| R3-ADV-6 (Major) | PROPOSE FIX (part CONTEST, fact 7) | The "no meter" behaviour is defined by P4b1. The scope is a no-op for a model that is not metered (`tickets/P4b1.md:259`), so a dev gate with a plain fake behaves as today. This is pinned by new row X8 and mutant M-X10. The "may break" list is extended to AK4a-3 (the 16 files). Line 152 is reworded: P5c-3's type check is the gate's only inspection of its model. **BN-6.** |
| R3-COR-1 (Major) | PROPOSE FIX | TRUE (fact 4). AK4a-2 Files gains `guard/producers.py`: `MODEL_CALLERS` entries plus `OUTSIDE_THE_CHOKE_POINT` reasons for each `testing/` module the scan finds. P4c's T8 table rows go under Couplings. `producers.py` joins the hot files. **BN-7.** |
| R3-COR-3 (Major) | PROPOSE FIX | TRUE (fact 5). H15 compares the per-case files byte for byte, and `run.json` with `replay_run_id` removed. It does not compare `outputs.sha256`. Nothing is patched in core. **BN-8.** |
| R3-ADV-7 (Minor) | PROPOSE FIX | TRUE. X7's AST lint resolves import aliases, `from ... import gate as g` and `getattr(<evals module>, "gate")`. New alias clauses in X7 and mutant M-X11. Callers outside this repository are not covered: stated. **BN-9.** |
| R3-ADV-8 (Minor) | PROPOSE FIX | TRUE. H17 gains a cross-process clause: two `python -I` subprocesses make different first canaries. M-H18 is then killed for a module-level seeded generator too. **BN-10.** |
| R3-ADV-9 (Minor) | PROPOSE FIX | E9 compares integers: `sum(abstained) == round(abstain_rate * n * k)`. **BN-11.** |
| R3-ADV-10 (Minor), R3-COR-7 (Minor) | PROPOSE FIX | TRUE (fact 10). The retry sleeps and the k1b deadline use separate clocks. `FakeClock.__call__` is defined. `K1bReplayPipeline`'s constructor arguments are named. H10d's tick script and the source of `model_id` are stated. **BN-12.** |
| R3-ADV-11 (Minor) | PROPOSE FIX | TRUE. Each step sends the item's document, marker line first, plus the previous step's reply text. A scripted reply never needs to carry the marker. **BN-13.** |
| R3-COR-8 (Minor) | PROPOSE FIX | TRUE. A Windows line: every AK4a row is written in a Windows-capable form. One claim is UNVERIFIED on Windows (child output under `os.dup2`), and no row depends on it there. **BN-14.** |
| R3-COR-4 (Minor), R3-COR-6 (Minor) | PROPOSE FIX | TRUE. H1 clause 7 swaps `sys.stdout` for an `io.StringIO` before `capture()`, so it kills M-H26 under any pytest capture mode. The capture wrappers sit over `os.dup` of the captured descriptor, so they share one offset. New clause H1 (11), which interleaves `print` and `os.write(1, ...)`. Mutant M-H34. **BN-15.** |
| R3-COR-5 (Minor) | PROPOSE FIX | TRUE (fact 6). The schedule draw uses `hashlib.sha256(f"{seed}:{k}")` instead of `random.Random`. That gives no suppression, and the draw is still a pure function of (seed, k) under any hash seed. **BN-16.** |
| R3-ADV-13 (Minor) | PROPOSE FIX | TRUE. One sentence in Security: on the llm path C-GATE pairs by order and count only, so it does not prove what text the fake received. **BN-17.** |
| R3-ADV-12 (Minor) | PROPOSE FIX (PENDING LEAD 1 updated) | TRUE. Done says plainly that AK4a is not closed for money while F1 is open. PENDING LEAD 1 asks the lead for a date on F1's ledger row. **BN-18.** |
| R3-ADV-14 (Nit), R3-COR-9 (Nit), R3-COR-10 (Nit) | PROPOSE FIX | The 19 non-mutant rows are listed (now 20). The step-adapter ids get AK1's `new_id` shape. The cites are re-pointed (fact 11). **BN-19** holds these and the full delta and totals. |

## Build notes (round 3), to be copied into the ticket as the section "Build notes (round 3)"
Ticket line numbers below are lines of revision 3 before the banner is added. Find each place by its text.

**BN-1. Where the item marker rides, and how C-FAULT reads it (R3-ADV-1, R3-COR-2).**
- **Step adapter:** the first line of every made-up item document is `item_marker(item_id)`.
- **k1b adapter:** every made-up bundle carries the marker in `incident.json` as `alert.labels["harness_item"] = item_marker(case_id)`. For example, case `case-001` gets `item-case-001`.
  - `labels` values are strings of at most 200 characters (`k1b/bundle.py:229-235`).
  - The key passes `_scan` and is not a credential key (fact 2).
  - The test builds bundles with `tests/k1b_support.make_bundle` and adds this label.
  - Interface 11's "in the bundle's document, with the case id" is replaced by this.
- **C-FAULT's read rule (replaces "by WHOLE LINE" in Interface 11 and C-FAULT).** For each text of `received[k].texts`, the reader collects:
  - every line (`text.splitlines()`) that is exactly equal to `item_marker(id)` of an input id; and
  - if `json.loads(text)` succeeds, every string VALUE at any depth (dicts and lists; keys are not read) that is exactly equal to `item_marker(id)` of an input id.
- Attempt k belongs to the one item whose marker was found. If no marker or two different markers are found, the result is `unattributed_attempt`. Every k1b attempt of a case carries the first user message, so all of its attempts are attributed.
- **H0 gains:**
  - (b) the marker clause names both paths: `redact_bundle` on `alert.labels` and the gate masking of a document whose first line is the marker;
  - (c) one `K1bReplayPipeline` run of one bundle with no faults: C-FAULT's reader gives that case's id for attempt 1.
  - H0 stays first. If (c) fails, it is an attribution defect, and the builder stops before H2.
- **H12 gains** an exactness clause: two k1b bundles, `case-001` and `case-0010`, each attempt attributed to its own case.
- **New mutants:**
  - **M-H32** (`testing/harness.py`): the JSON branch is removed (lines only). Killed by H0 (c) and H2.
  - **M-H33**: the exact compare is written as `marker in value`. Killed by H12's exactness clause.

**BN-2. What C-LOG's generic record scan reads (R3-ADV-2).**
- At check time, C-LOG reads per record, as today:
  - `getMessage()`;
  - the `repr` of each item of `record.args` (each value, when `args` is a dict);
  - the formatted `exc_info` text, and `stack_info`.
- "Every other value in `record.__dict__`" is replaced by: every value whose key is NOT in `LOG_RECORD_BASE`, plus `message` and `asctime`. `LOG_RECORD_BASE` is the key set of a fresh `logging.LogRecord("n", 10, "p", 1, "m", None, None).__dict__`, computed once at import, so it follows the running Python's version.
- So `args`, `exc_info`, `exc_text`, `msg` and `stack_info` are read only by their own scans. M-H2 (H1 clause 2) and M-H5 (H1 clause 3) are no longer equivalent (fact 3). `extra=` fields stay covered (H1 clause 4, M-H27).
- The sentence "None is labelled equivalent in advance ... M-H2 by a clause whose message lacks the canary" now holds.

**BN-3. Duplicate and missing case ids (R3-ADV-3).**
- In pilot/prod, label-phase errors (Interface 1: before the size rules and before any model call, one `ConfigError`) gain three checks:
  - a line without a non-empty string `id` (the error names its `input_ref`);
  - a repeated `id` (the error names the id);
  - a repeated `input_ref`, or two lines whose input documents have the same sha256 of their bytes (the error names both ids).
- The gate reads every referenced document's bytes before the first call. `registry.golden_sha256` already reads each of them.
- Dev is unchanged, so E12 still holds.
- Stated plainly in Security: near-copies (one character changed) are not caught. The size rule counts distinct documents, not distinct cases.
- **New row E16** (AK4a-1). In pilot, with a valid 50-line set:
  - line 50 repeating line 1's `id` is refused, naming it;
  - two lines with different file names and identical bytes are refused;
  - a line without `id` is refused, naming its `input_ref`;
  - in each case the fake's call count is 0;
  - in `dev`, the same three sets are accepted.
- **Mutants:** M-E22 (`id` repeats not checked), killed by E16. M-E23 (only `input_ref` compared, document bytes not), killed by E16's identical-bytes clause.

**BN-4. Traps are gated item by item; the threshold floor goes to the lead (R3-ADV-4).**
- Interface 4 `green` gains (a2): when any line is labelled, `buckets["trap"].passed == buckets["trap"].n`. Any trap failure means not green, in every environment, as (a) does for easy items.
- So a lowered `eval_threshold` can only let HARD items fail.
- **New row E17, FAIL-BEFORE (real).** `dev`, 20 labelled lines (10 easy, 5 hard, 5 trap), `eval_threshold` 0.9, and exactly one trap item proposes an action. On main this is green (19 of 20 = 0.95). New code: not green.
- **Mutant M-E24:** the trap condition is removed. Killed by E17.
- **Threshold floor:** PENDING LEAD 5. Until the lead answers, Security says plainly: "in pilot/prod a config may lower `eval_threshold` to any value above 0; only easy and trap items are gated one by one." If the lead picks 5(a), AK4a-1 adds, in the same pull request: one floor in `defaults.py`, one validator at config load (pilot/prod only), one E6 clause and one mutant.
- The "tightens a security gate" sentence (line 166) then reads: "tightens it in size, labels, duplicates, easy items and traps".

**BN-5. `sized: true` with missing counts fails closed (R3-ADV-5).**
- Interface 6 is retyped to `counts: Mapping[str, BucketStat] | None`. `None`, or a missing bucket key, counts as `BucketStat(n=0, passed=0, abstained=0)`, so `n`, `easy`, `hard`, `trap` and `trap_share` fail.
- With a stored `run` in pilot/prod, `run.answerable is None` or `run.false_abstained is None` fails `false_abstain`.
- It never raises `TypeError`.
- **New row E18** (AK4a-1). Pilot, against a green line with `sized: true` that matches every hash:
  - with `buckets: null`: `Unqualified`;
  - with `buckets` missing the `trap` key: `Unqualified`;
  - with `answerable: null`: `Unqualified`;
  - no clause raises any other exception.
- **Mutant M-E25:** `counts is None` returns `[]`. Killed by E18.
- Stated in Security: a person who can write `qualified.jsonl` can forge a green line today, and AK4a does not change that. The hashes bind config and golden set, not the counts.

**BN-6. The meter scope when no meter is configured; "may break" list (R3-ADV-6).**
- AK4a-3 clause (Interface 15): `metered.scope(...)` only sets and resets a context variable (`tickets/P4b1.md:259`). Around a model object that is not a `MeteredLLM` it changes nothing, in every environment.
- The fail-closed point in pilot/prod stays construction: the `gate` command's chain (X5b) and lint X7. A direct code caller that hands `evals.gate` an unmetered model in pilot is not refused by `evals.gate`. Stated in Security; P6a-1's refusal of handed-in objects is UNVERIFIED.
- **New row X8** (AK4a-3). In `dev`, the E12 fixture run with a plain `ScriptLLM` under AK4a-3's code gives the same `n`, `passed`, `pass_rate` and `green` as E12. The context variable is back at its default afterwards.
- **Mutant M-X10:** the gate refuses a model that is not metered. Killed by X8.
- Files, "Existing tests that may break", gains AK4a-3: the 16 test files with `gate(` or `assert_qualified` (57 lines, fact 7) run before and after AK4a-3. The builder lists any that change, with the reason, and never weakens an assertion.
- Line 152 and I7: "`evals.gate` does NOT inspect its model object" becomes "`evals.gate` makes no meter check on its model object; P5c-3's wrapper type check (Rules, order of refusals) is its only inspection".

**BN-7. Registration in `guard/producers.py` (R3-COR-1).**
- AK4a-2 Files gains: CHANGE `src/hadavin_sdk/guard/producers.py`.
- For each module under `testing/` that the `test_k5_producers.py` scan finds (at least `testing/faults.py`), add one `MODEL_CALLERS` entry and one `OUTSIDE_THE_CHOKE_POINT` reason: "test fake: forwards to its inner fake model exactly the texts its caller sends; it produces no model input of its own".
- The made-up test step lives in `tests/`, so it needs no entry. The builder adds no entry the scan does not ask for.
- `guard/producers.py` joins the hot files (appends only; at least 11 tickets name it).
- Couplings gain P4c T8 (`tickets/P4c.md:218`):
  - its table needs a status row for each `testing/` module with `chat`, added by whichever of AK4a-2 and P4c-2 merges second;
  - its `evals.py` row ("not capped") becomes "capped by `metered.scope` and the `gate` command's chain (AK4a-3)", updated by whichever of AK4a-3 and P4c-2 merges second.

**BN-8. H15 without the run id (R3-COR-3).**
- H15's k1b clause becomes: two runs with the same seed and scripts give byte-equal files for every path in `outputs_files` except `run*/run.json`. For each `run.json`, the parsed objects are equal after deleting `replay_run_id`.
- `outputs.sha256` is not compared (it covers `run.json`).
- No core function is patched.

**BN-9. X7 is alias-proof; outside callers (R3-ADV-7).**
- X7's AST lint resolves `import hadavin_sdk.evals as e`, `from hadavin_sdk import evals as e`, `from hadavin_sdk.evals import gate as g`, and `getattr(<a name bound to the evals module>, "gate")`. It flags any call of these outside `cli.py`, and any `importlib.import_module("hadavin_sdk.evals")` in `src` outside `cli.py`.
- X7's teeth gain one planted test file per alias form.
- **Mutant M-X11:** the lint matches only the literal attribute call `evals.gate(`. Killed by X7's `from ... import gate as g` clause.
- Stated in Security: callers outside this repository (a client project) are not covered. The cap rests on the construction in `cli.py` and on P6a-1, not on a check inside `evals.gate`.

**BN-10. Canary uniqueness across processes (R3-ADV-8).**
- H17 gains a clause: two `subprocess` runs of `[sys.executable, "-I", "-c", <print the first Canary's value>]` print different values.
- M-H18 ("canary from a fixed seed", including a seeded generator made once at module level) is killed by this clause.

**BN-11. E9 compares integers (R3-ADV-9).** E9 asserts `sum(b.abstained for b in buckets.values()) == round(run.abstain_rate * n * k)`. It never compares floats for equality.

**BN-12. Clocks and the k1b adapter's wiring (R3-ADV-10, R3-COR-7).**
- `FakeClock.__call__()` returns the current fake time. `sleep(s)` records `s` and advances the time.
- In every k1b row, `FaultLLM` gets its OWN `FakeClock`, used only for retry sleeps. The k1b deadline clock is a second, separate callable. So throttle and jitter sleeps never move a case towards `case_timeout_s`.
  - In H2, H10, H10b, H10c and H11, the deadline clock is a `FakeClock` that nobody advances, and `case_timeout_s` keeps its default of 300.
  - H10d uses the tick script `iter([0, 0, 299.99] + [1000] * 50)` with `case_timeout_s` 300, as `tests/test_k1b_replay.py:513-515` does.
- `K1bReplayPipeline(registry, *, agent_id, bundles_dir, cause_list_dir, detector, max_usd, clock)` takes everything from the caller, because `src` must not import `tests/`. Its `run` calls `_replay` with `audit=K1bAudit(<the harness's recording sink>, principal="harness")` (`k1b/audit_sink.py:26-29`).
  - The test builds the bundles with `tests/k1b_support.make_bundle` (plus BN-1's label), the cause list with `make_cause_list`, and the detector as `tests/k1b_support.py` does (`RegexDetector`).
  - The config is the `dev` fixture config. Its k1b block gives `case_timeout_s` and `max_steps`.
- `FaultLLM` replies that it builds itself (`bad_reply`, `echo`) take `model_id` from `prices[route].model_id`, the fixture route's own value. `partial_reply` copies the inner reply's `model_id`.

**BN-13. What each step sends (R3-ADV-11).**
- In the step adapter's test step, step 1 sends the item's document (marker line first).
- Step n > 1 sends the item's document again plus the previous step's reply text as a second message. So every attempt carries the marker.
- A `ScriptLLM` reply never needs to carry the marker, and no row depends on a reply text holding it.

**BN-14. Windows (R3-COR-8; order 25 item 4).**
- Every AK4a row is written in a Windows-capable form: `os.dup`/`os.dup2` on descriptors 1 and 2, threads, and `subprocess` with `sys.executable`. It uses no `fork`, no signals and no POSIX-only module.
- X3 runs where its Postgres runs (CI service, `HADAVIN_REQUIRE_PG=1`) and uses P4b1's process helpers. It is not marked Linux-only.
- UNVERIFIED on Windows: that `os.dup2` on descriptors 1 and 2 also captures the output of a child process. No Windows row depends on it, because X3 passes each worker's captured output to C-LOG itself.

**BN-15. Capture independent of pytest's mode; one shared offset (R3-COR-4, R3-COR-6).**
- Interface 12: the `sys.stdout` and `sys.stderr` replacements are text wrappers over `os.dup` of descriptors 1 and 2, taken AFTER the `os.dup2` into the temporary file. They therefore share that file's one offset with direct descriptor writes. They never open the temporary file a second time.
- H1 clause 7 becomes: set `sys.stdout = io.StringIO()` (an object with no descriptor), then enter `capture()`, then `print(canary)`: `canary_in_print`. This kills M-H26 under `-s`, `--capture=no` and the default mode alike.
- **New H1 clause (11):** inside `capture()`, `print("a" + canary)`, then `os.write(1, b"b")`, then `print("c")`. The captured text holds all three parts, in that order.
- **Mutant M-H34** (`testing/harness.py`): the wrappers open the temporary file by name, so each has its own offset. Killed by H1 (11).

**BN-16. The schedule draw (R3-COR-5).**
- Interface 8: `d = hashlib.sha256(f"{seed}:{k}".encode()).digest()`. Attempt k gets a fault when `int.from_bytes(d[0:8], "big") % 100 < rate_percent`. Its kind is `sorted(kinds)[int.from_bytes(d[8:16], "big") % len(kinds)]`.
- It has no `random` module and no `# noqa`, so the ruff `S` rules and `bandit -ll` pass with nothing suppressed. It is still a pure function of (seed, k) and independent of `PYTHONHASHSEED`, so I19 holds.
- The modulo bias over 2^64 is negligible for these rates.

**BN-17. What C-GATE proves on the llm path (R3-ADV-13).**
- Security's "does NOT prove" list gains: "on the llm path (`MaskedLLM(MeteredLLM(raw))`) C-GATE pairs each raw call with an intent event by order, count and `domain == "llm"` only. It does not prove that the raw fake received the audited masked body. Only the `Gated` path compares hashes."

**BN-18. Money is not closed while F1 is open (R3-ADV-12).**
- Done gains: "AK4a is not closed for money while F1 is open. Its strict expected-failure rows H10, H10b and H10d are a money gap told to the owner, not a pass. The lead writes the calendar date of the F1 fix on F1's ledger row, as for F5."
- PENDING LEAD 1 is updated (below).

**BN-19. Nits; mutant and row delta; totals (R3-ADV-14, R3-COR-9, R3-COR-10).**
- **Cites:** `registry.py:164-170` (not `:165-171`); `models.py:274` (field) and `:273` (comment).
- **Step-adapter ids:** in H6, H8 and H12 (step adapter), ids come from `models.new_id("item")`, which matches AK1 `ITEM_ID_PATTERN` (`tickets/AK1.md:105`). The exactness test uses k1b case ids (BN-1).
- **Rows added:** E16, E17, E18 (AK4a-1); X8 (AK4a-3). **New clauses inside existing rows:**
  - H0 (b) and (c);
  - H1 clause (11), and clause (7) reworded;
  - the H12 exactness clause;
  - the H15 rewrite;
  - the H17 subprocess clause;
  - X7's alias clauses;
  - E9's integer compare.
- **Mutants added (9):**
  - AK4a-1: M-E22, M-E23 (BN-3); M-E24 (BN-4); M-E25 (BN-5);
  - AK4a-2: M-H32, M-H33 (BN-1); M-H34 (BN-15);
  - AK4a-3: M-X10 (BN-6); M-X11 (BN-9).
- **Mutants made real, not equivalent:** M-H2, M-H5 (BN-2); M-H26 (BN-15); M-H18 (BN-10).
- **Totals:**
  - **49 test rows:** AK4a-1 E1-E18 = 18; AK4a-2 = 21 (unchanged); AK4a-3 H3, X1, X2, X3, X4, X4b, X5, X5b, X7, X8 = 10.
  - **70 mutants:** M-E1 to M-E25 = 25; M-H1 to M-H34 = 34; M-X1 to M-X11 = 11.
  - **20 rows that kill no mutant by design or are classed apart:**
    - real fail-before: E1, E2, E3, E17 (4);
    - weak fail-before: H1, X5 (2);
    - regression pins: E11, E12, E15 (3);
    - pre-build check: H0 (1);
    - integration row: X3 (1);
    - clean-run rows: H2, H3, H6, H8, H15 (5);
    - strict expected failures: H10, H10b, H10c, H10d (4).
  - **The other 29 rows** are new features killed by named mutants. E1-E3, E17, H0 (M-H32), H1, X5 and E11 also kill mutants.
- No mutant targets `guard/producers.py`; its registration is checked by the existing `test_k5_producers.py` gate. Evidence: AK4a-1 runs mutants M-E1 to M-E20 and M-E22 to M-E25; M-E21 stays with E13.

## Positions
- **One read rule for both adapters (BN-1)** instead of a k1b-only parser. It accepts a marker as a whole line or as a whole JSON string value, and nothing looser. A delimited-token match (ADV-1's second option) would bring back the `item-1` inside `item-10` problem for case ids (`CASE_RE` is `case-[0-9]{3,}`).
- **BN-2 narrows a scan instead of adding a row.** Scanning `str()` as well as `repr()` of args would add a rule, a row and a mutant for a case (an arg object whose `repr` hides a value its `str` shows) that a standard formatter never prints. I did not add it.
- **BN-3 keeps dev unchanged.** ADV-3 allowed "pilot/prod at least". Dev duplicates are allowed today, and the 16 existing gate test files are not re-checked for them, so refusing in dev could break tests for no pilot benefit.
- **BN-4 decides the trap half itself.** "Every trap item must be refused" needs no number. It is what the label means (`matches`, fact 8), it mirrors the easy rule, and it cannot be loosened. The threshold floor is a number, and numbers are the owner's (thresholds come from config; order 24 item 32), so it goes to the lead.
- **ADV-6 is partly contested on a readable cite** (`tickets/P4b1.md:259`): the no-meter behaviour is already defined, and the fix is to state it, pin it (X8) and extend the "may break" list.
- **BN-8 normalises rather than patches** `new_id`. That keeps H15 a test of the real code path.
- **Nine mutants are added** because each new rule gets one (revision 3 precedent). BN-11, BN-12, BN-13, BN-14, BN-17 and BN-18 change wording or test setup only, so they get no mutant.

## Couplings (text other owners change; this resolve edits none of them)
- **P4c T8 (`tickets/P4c.md:218`):** the status rows for `testing/` modules, and the `evals.py` row text (BN-7).
- **`guard/producers.py`, shared with at least 11 tickets:** AK4a-2 appends only (BN-7).
- **P4b1-b:** BN-6 relies on `metered.scope` being a context-variable-only manager (`tickets/P4b1.md:259`). If P4b1-b changes that, X8 fails loudly.
- **P6a-1:** BN-6 and BN-9 name its refusal of handed-in objects as the pilot guard for direct code callers (UNVERIFIED until it merges).
- **AK1-a:** BN-19's ids follow `ITEM_ID_PATTERN` (`tickets/AK1.md:105`). AK1 is a revision 3 DRAFT.
- **P5c-3:** H0 (b) re-runs on its head (unchanged rule). BN-3's byte read happens before P5c-3's `decode_document`, so it does not depend on it.

## PENDING LEAD (continuing the ticket's numbering after 4)
Routing rule: an item that touches an owner hard rule (thresholds, money, redaction, security gates) is NEEDS LEAD. Everything else is INFORM, and the builder takes the recommendation meanwhile.
- **1 (updated, money; BN-18).** Unchanged options. Added: the lead writes a calendar date for the F1 fix on F1's ledger row. Until then Done says AK4a is not closed for money.
- **5. NEW, NEEDS LEAD (security threshold): a pilot/prod floor for `eval_threshold`.**
  - (a) **Recommended:** a floor constant in `defaults.py`, enforced at config load only when `environment` is `pilot` or `prod`. A config may raise the threshold above the floor, never lower it below. The number is the lead's or the owner's. For illustration only, not a proposal of mine: 0.9 would let at most 5 of 50 items fail, all of them hard. Cost: one constant, one validator, one E6 clause, one mutant, in AK4a-1's pull request.
  - (b) No floor. Security states that only easy and trap items are gated one by one (BN-4), and that a pilot config may lower the threshold to any value above 0.
  - (c) A floor per bucket (a hard-bucket pass-rate floor). This is more surface for the same effect, because easy and trap are already 100 percent.
  - Why (a): order 24 item 32 says thresholds come from config and a config may only tighten. With (b), a pilot could still qualify an agent that fails most hard items.
  - Until the lead answers, the builder writes (b)'s Security sentence and adds nothing else.
  - Reversible before the merge.
- **6. NEW, INFORM. Freeze with build notes, no round 4.** Round 3 had 1 Blocker and 8 Majors (7 distinct). Recommend: yes, per order 20 item 6.
- **7. NEW, INFORM. Traps gated item by item, in every environment where lines are labelled (BN-4).** Recommend: accept. Confidence 75 percent. Cost: an agent that wrongly acts on one trap in one of k runs is not green. This is the intended meaning of a trap. Reversible.
- **8. NEW, INFORM. Duplicates refused in pilot/prod only, by id, `input_ref` and document bytes (BN-3).** Near-copies are not caught. Recommend: accept. Confidence 80 percent. Reversible.
- **9. NEW, INFORM. The k1b marker is `alert.labels["harness_item"]`, read by line or by JSON string value (BN-1).** Probed on 3.13.18 (fact 2); H0 confirms it on the build head. Confidence 85 percent. Reversible.

## Counts
- **Finding ids:** 24 (ADV 14, COR 10).
  - 1 Blocker (ADV-1).
  - 8 Majors: ADV-2 to ADV-6 and COR-1 to COR-3. ADV-1 and COR-2 are one defect.
  - 12 Minors and 3 Nits.
  - No severity changed.
- **PROPOSE FIX:** 24. ADV-6 is a partial CONTEST, ADV-4 has a NEEDS LEAD half, and ADV-12 updates PENDING LEAD 1.
- **CONTEST:** 0 whole (1 partial: ADV-6, on `tickets/P4b1.md:259`). **ESCALATE:** 0. **DECLINE:** 0.
- **Build notes:** 19 (BN-1 to BN-19; BN-19 holds the delta and totals).
- **After the notes:** 49 test rows (18 / 21 / 10) and 70 mutants (25 / 34 / 11).
- **PENDING LEAD:**
  - 1 updated (item 1);
  - 1 new NEEDS LEAD (item 5);
  - 4 new INFORM (items 6 to 9).
- **Probes run:** 4 python scripts, plus 1 ruff check on a scratch file. **Tests or mutants run:** 0.
- **Fixes applied to the ticket in this step:** 0 (they are build notes). **Remaining unaddressed findings:** 0. The threshold floor waits on PENDING LEAD 5.
