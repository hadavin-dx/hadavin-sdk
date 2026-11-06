# P6a round 2, adversarial review (ticket revision 2)

Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority).

Reviewer type: egm:egm-design. Read-only.

TICKET REVIEW round 2, ADVERSARIAL: handover/tickets/P6a.md, revision 2 (333 lines in my view)
Verdict: no Blocker. 4 Major, 7 Minor, 2 Nit. The design is sound and the arithmetic adds up. The Majors are test-plan and semantics defects that a builder would have to guess around.
I did not read handover/reviews/ or handover/evidence/. I read the code and tests cited, plus handover/tickets/P5c.md (rev 2) for coupling. This tree is not a git repo, so I did not run any `git show` or `git diff` from the ticket (see Not checked).

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R2-ADV-1 | Major | 163-168 (fail-before part 1), 145 (T5 l), 138 (T5 d) | The plan copies the whole test file onto the base and expects 18 FAIL and 34 PASS. T5 (l) needs `app._test_doubles_given`, and T5 (d) and T2 (d) need P5c's `MaskedLLM` and its suite. If any of these is a module-level import, pytest hits a collection error and all 54 rows report ERROR. The "34 pins pass on base" claim is then false and the table is meaningless. The ticket says T5 (l) fails "because the function does not exist" but never says the import must be inside the test body. | Say that every name that exists only after P6a or P5c (`_test_doubles_given`, `MaskedLLM`, the redactor suite) is imported inside the test body, or via `pytest.importorskip` or a `getattr` guard. Add a base-run check that collection yields 54 items. |
| R2-ADV-2 | Major | 75, 79, 134 (T5 d), 252 (PL1), mutants 1-37 | The positive path "`allow_test_doubles=True` lets the build through" is tested only by T5 (d), which needs Postgres and skips without `HADAVIN_TEST_PG_DSN`. No mutant covers "switch ignored, always refuse" (for example `and not allow_test_doubles` dropped). Locally, and under any mutation run without PG, that mutant survives. It would also survive if CI's PG service failed to start and the row skipped. The same applies to mutant 11. | Add a non-PG row: pilot, `llm=` plus `allow_test_doubles=True`, with `app.platform_secrets.check` patched to raise a sentinel. Assert the sentinel is reached (same trick as T5 m). Add the mutant "switch ignored" with that row as killer. Make the evidence say when T5 (d) skipped. |
| R2-ADV-3 | Major | 38, 76, 79, 252 | S2 refuses every build keyword in a live profile, with the message "for tests; pass allow_test_doubles=True only from a test". `hold_run_ids` is a production hook: `runtime/tick.py:189-208` documents it as the purge hold, and `app.build` is the only way to set it. `cli._tick` passes none, so a Python operator who needs purge holds must now pass a switch whose name and message say "test". `clock` and `secrets` can also be legitimate for an embedding operator. Once the switch is routine in production code, the accident guard stops guarding. The ticket neither notes this nor offers an alternative in PL1. | Add a PL1 option (d): the check covers only parts that replace a configured backend (`secrets`, `channel`, `detector`, `llm`) plus `clock`. Production hooks (`hold_run_ids`, `timeout_s`) are exempt, via a per-parameter marker or a short test-checked list. Or rename the switch to something that does not say "test", and reword the message and CHANGELOG. The lead must decide before the build, because T5 (b) and (c) counts depend on it. |
| R2-ADV-4 | Major | 94, 112-115, 130 | The evidence for S2 and PL1 does not recount live builds that use the keywords after P5c. P5c rev 2 (`tickets/P5c.md:282`) makes `build(llm=raw)` wrap in `MaskedLLM`. Its T3-07 (d) scans `demos/ask-your-data/askdata/pipeline.py`, while P6a PL6 and V2 keep demos out of the wrapper test. This is a live contradiction between two draft tickets over the same scanner `model_call_sites`. P6a also says P5c has "revision 1 (revision 2 being written)", but the P5c file on disk is already DRAFT revision 2 with a new T3-07 shape. | Re-read P5c rev 2 and update every "PENDING P5c" name (`build_llm`, T3-07 file and rows, `MaskedLLM.of`, suite path). Resolve the T3-07 (d) versus PL6 overlap in the ticket text (say which test owns demos). Rewrite the Depends-on line "P5c revision 1". |
| R2-ADV-5 | Minor | 144, 193 (T5 j, mutant 16) | T5 (j) cannot work as written unless the fixture supplies a complete secrets double or patches `platform_secrets.check`. With the unpopulated `mounted_file` dir, the build fails at `app.py:122` before any `make("signer")` at :144. The recorded set stays within `{"secrets"}` whether or not the check is misplaced. Mutant 16 is in fact killed by T5 (a)/(b), because their `match=` fails on the earlier error. But a "placed after `platform_secrets.check`" mutant is missing, and it would survive once the builder populates a secrets folder (item 111 allows that). | State the fixture for (j): the recording wrapper appends before delegating, and `platform_secrets.check` is patched to pass. Add the mutant "check after `platform_secrets.check`" with killer (j). |
| R2-ADV-6 | Minor | 218-223 | The evidence commands use `2>&1 \| tee`, so the exit code is tee's. This breaks repo rule `verify-tests-and-evals` and P5c's own `> file; echo rc=$?` form. Step 3 of fail-before also writes to `handover/evidence/P6a/...` from inside a scratch worktree of the base commit. A core-main base has no `handover/` directory, so the write fails. | Use `> file 2>&1; echo rc=$?`, with absolute paths into the handover checkout. |
| R2-ADV-7 | Minor | 107-111, 136, 141 | Refusal rows must never let a base build reach the store connect. If the builder populates secrets (item 111 allows it), a base-run T5 (b) `clock=` row proceeds to `make("store")` against a fake DSN. The ticket does not say how the rows avoid a network or Postgres attempt. | Say that every refusal row patches `app.make` (or the store make) to raise a sentinel, so the base fails fast and offline. |
| R2-ADV-8 | Minor | 37, 130-132 | S1/T2 leaves decisions to the builder. `CLIENT_REVIEWED` has no content: roughly 20 kinds, each needing a one-line reason. It is not stated whether the `NOT_PROD` pairs (`signer/none`, `anchor/none`, allowed in pilot) go in `CLIENT_REVIEWED`. It is also not stated whether `llm/fake` variants such as `recorded_dir` count as one pair. | List the `TABLE` pairs and their sets in the ticket. State the `NOT_PROD` rule. |
| R2-ADV-9 | Minor | 132-133 | T2 (d) reads P5c's redactor backend list, and "how it is read is PENDING P5c". A P6a-2 builder cannot write it until that is fixed. P5c rev 2 exists on disk now. | Pin the reading (a module-level constant or a registry call) from P5c rev 2, or move T2 (d) to P5c's own suite. |
| R2-ADV-10 | Minor | 53, 259, 64-66 | The split option (a) puts P6a-1 on `app.py` before P5c-3, but Depends-on and hot files say "P6a last". The row counts per sub-PR are not given. P6a-1 and P5c-3 both edit `tests/test_k3_pilot_env.py:185`, and P6a-2 and P5c-3 both edit `_sink_callers`. | Give row counts per sub-PR. Say which PR owns the `test_k3_pilot_env.py:185` edit and which owns `_sink_callers`. |
| R2-ADV-11 | Minor | 141 (T5 g) | The tripwire misses `b = app.build; b(**opts)` and `build = getattr(app, "build")`. The text already admits it is a tripwire, but it names only three planted forms. | Add one line stating the aliased-call limit. A planted alias row is optional. |
| R2-ADV-12 | Minor | 78, 82 | The order is `secrets = secrets or make("secrets", ...)` (:82), then `live` (:83), then the refusal. A configured `vault` or `mounted_file` secrets kind is constructed before a test double is refused. The ticket says no network is touched and "all checks run in the process"; I could not confirm that for vault construction. | Either compute `live` and refuse before :82 (this makes the first-statement record unnecessary), or state that the secrets constructor runs first and check that it does no I/O. |
| R2-ADV-13 | Nit | 162, 330 | PL count "12 (2 closed, 3 answered by fact, 8 to 10 ...)" reads as if items 2 and 3 were counts. | Reword: "items 2 and 3 closed; 8-10 from the resolve; 11-12 new". |
| R2-ADV-14 | Nit | 161 (T6 g) | The list is keyed by (module, function). A second dynamic `getattr` in the same function is invisible. The CHANGELOG declines per-site counting. That is acceptable, but it should be one line in the Security notes (c). | Add the line. |

Template check (17 fields): all 17 are present and in order. Rollback gives revertibility, as the template allows.
Cap rule: the header (line 3) matches order 20 item 6. Round 3 is the last; the extra round applies only to money and redaction.
No real-looking secrets: the placeholders `<made-up bucket>` and `<made-up region>` are fine.

Verified (read in code, cites hold on this tree):
- `app.py`: lines 62-75, 82, 83, 84-85, 86-89, 90-98, 107-110, 122, 144, 146, 162, 170, 173, 182, 225.
- Config and table:
  - `config.py:70`, `:74` (the `entries` function), `:317`, `:365-373`, `:377-397`.
  - `table.py:582-589`, `:593-602`, `:604`.
  - `deferred.py:33` (`LIVE = ("pilot", "prod")`).
  - `models.py:19` (`now`, the `clock` default).
- Settings fields in `table.py` that the `prod_cfg` fixture relies on: lines 156, 163-164, 217-218, 223-224. Exactly one of `private_key_path` and `private_key_secret_name` must be set.
- `tests/test_p1b_backends.py:89-102` is as described. It does not cover `secrets: env`.
- `tests/test_k5_producers.py`: `SINK_METHODS` at :22, `_sink_callers` at :78-95 (call-only, skips `llm/`, roots as stated), and :98 for the registry test.
- `tests/test_k3_pilot_env.py:35-74` (no anchor, signer with a key path) and `:184-191`.
- `tests/test_k5_round5.py:222-226`, and `test_k5_round8_postgres.py:40` is a live build with doubles.
- `ci.yml:73`, `:86`, `:93`, `:109`, and `pyproject.toml:58`.
- Item 7 scanner facts:
  - Six `.chat` / `apply_guardrail` sites outside `llm/`, matching `MODEL_CALLERS` plus `demos/ask-your-data/askdata/pipeline.py:155`.
  - `make("llm"...)` appears in 3 places: `app.py:162`, `cli.py:150`, `cli.py:221`.
  - Non-constant `getattr`: I counted the same 12 sites in 11 functions.
  - `tools.py:389` exec: I did not re-read the line itself.
- Arithmetic:
  - Rows: 1+3+7+29+14 = 54. T5 = 1+14+1+1+1+1+4+1+1+1+1+2 = 29. T6 = 14.
  - Fail-before: 18 + 2 + 34 = 54.
  - Mutants run 1 to 37. Dropping T6 (f) takes 37 to 36 and 54 to 53.
  - V-rows: 6.
- The 5 planted alias forms of part 2 are all missed by the old call-only scan, so the base PASS and head FAIL expectation is right.
- Mutants 7, 8, 12, 15, 17, 18, 19 have killers that can actually fail. Mutant 17 is killed by T5 (m), which is a good correction (N1).
- The no-`build`-call claim for `demos/` and `src/`: only `cli.py:299` in src (I grepped the `build(` forms; the `build(` hits under `tests/` are test helpers).

Not checked (UNVERIFIED):
- The `git diff --stat 124258b HEAD` and `git show 124258b:...` claims (no git repo in this tree). I cannot say whether main differs from the cited commit; all file-and-line cites above were read in the checkout as it stands.
- That `tools.py:389` is the single `exec`, and that `agent_loop.py:425` sits in `Runtime.handle` with no nested function.
- Whether `mounted_file` secrets construct without a secrets directory (the ticket flags this itself).
- That `prod_cfg` loads (T0), and any P1m runner behaviour, P6b1/P6b2 interactions, or `ci.yml` lint step lines other than those listed.
- The other `build` callers' environments: I checked `pilot_cfg` use and a few helpers, not every config that sets `environment: pilot` through other helpers (the ticket's own script recount covers this).
- The contents of `handover/reviews/` and `handover/evidence/`, by instruction.
