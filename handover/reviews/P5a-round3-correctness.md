# P5a round 3, correctness review (ticket revision 3)

Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority).

Reviewer type: egm:egm-codebase-details. Read-only.

TICKET REVIEW round 3, CORRECTNESS, handover/tickets/P5a.md (revision 3). Read-only. I read the persona file, LEAD-ORDERS 6-21, amendments.md, TICKET-TEMPLATE.md and all 240 lines of the ticket. I did not open handover/reviews/ or handover/evidence/.

Summary: 0 Blockers, 1 Major, 5 Minors, 3 Nits.
I found no place where the ticket states current code behaviour that the code contradicts. Every file:line cite I checked holds on this tree.
Caveat: this tree is not a git repository and I had no execution tool (Read, Grep and Glob only). I could not run Python, so every "probed" claim and both hash values are UNVERIFIED by me (see "Not checked").

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-COR-1 | Major | 146 (`foreign_driver` row), 164 | The class lists real `openai`, `sqlalchemy` and `httpx` libraries. No extra in `pyproject.toml` (lines 23-44: anthropic, aws, signer, pg, askdata, azure, gcp) installs `openai` or `sqlalchemy`. Neither is in `.venv/.../site-packages`, and I found no `httpx` there either (may be a glob miss). Line 164 says a skipped `foreign_driver` row is a FAILED evidence run unless the library is "genuinely uninstallable". With the current dependencies the gate cannot pass, or the builder is pushed to add dependencies (conflicts with the pinned-dependency policy and the no-single-dependency rule). | Split the 8 rows. Require real classes only for libraries the extras install (`psycopg`, `urllib3`, `botocore`, `pydantic_core`, `anthropic`). For `openai`, `sqlalchemy` and `httpx`, say the row uses a hand-built class with a set `__module__`, labelled "not the real class". Remove those names from the "skipped = failed" rule. |
| R3-COR-2 | Minor | 119-121 (strict xfail), 17 | `xfail(strict=True)` is described without `raises=`. Today's writers can crash on the hostile rows: `tick.py:289` does `type(exc).__module__.split(".")`, which raises `AttributeError` for a non-str `__module__`. `tick.py:292` calls `str(exc)`, which raises for a hostile `__str__`. Both run inside the `except` handler at `:315-317`, outside any `try`, so the error escapes `_run_step`. An unmarked crash would count as a green XFAIL and hide adapter bugs. A crash is also not a "leak", so those rows would be mislabelled in `OLD_WRITER_LEAKS`. | Use `raises=AssertionError`. Have the adapter catch a writer crash and record it as its own outcome (e.g. "writer crashed", with a note in the row). State that outcome in the `OLD_WRITER_LEAKS` rules. |
| R3-COR-3 | Minor | 47, 51, 93 | Line 51 speaks of "the frozen `FACT_PRIORITY` test", but the only test listed (`test_fact_priority_equals_fact_key_members`) checks equal sets, not order. The order decides which 12 facts survive and the line order. A mutant that swaps two keys is killed only if a golden line happens to contain both (T4's sqlstate and phase, T6's type and count). Appendix B has no mutant or killer for the order. | Add `test_fact_priority_order_is_the_d9_literal` (the 20 names as a literal tuple) and an Appendix B mutant "two keys swapped". |
| R3-COR-4 | Minor | 146, 7, 146 end | The class minimums are not what the text lists. `hostile_class` lists 16 distinct situations (I counted: dynamic class, 9 raise variants, str-subclass args, exception args, recursion, 1 MiB, canary in every attribute, BaseException `__getattr__`) against a minimum of 14. `secret_shapes` lists 6 against 8. The pii_encoded entries are ambiguous (8 vs 9). Yet "134 active, 163 total" is repeated as a claim in the changelog. The arithmetic itself is correct: 134 = sum of the minimums, 134+27+2 = 163, and 27 = 6+5+3+2+8+3. | Say once that 134 and 163 are minimums computed by the meta-test, or align each list to its minimum. |
| R3-COR-5 | Minor | 75 vs 72 | The sentence "a longer traceback gives locator `-` and code `foreign_exception` under rule 4" is ambiguous. The text keeps the innermost 32 frames (so a locator exists for 33-2000 links) and rule 4 says foreign only when the walk exceeds `DIAG_TB_STEPS` = 2000. "Longer" is unclear (32 or 2000). | Write: more than 2000 links gives `-` and `foreign_exception`. 33 to 2000 links keeps the innermost 32. |
| R3-COR-6 | Minor | 104, 237 | The killer for the "`DIAG_TB_STEPS` bound removed" mutant needs a traceback of more than 2000 links. Python's default recursion limit is 1000, so such a traceback cannot occur naturally. The ticket does not say how it is built. It needs hand-built `types.TracebackType` links or a raised recursion limit, otherwise the mutant is not killable. | State the construction (hand-built `TracebackType` chain). Say the mutant is "equivalent in practice" if it cannot be built. |
| R3-COR-7 | Nit | 114 | "`_Strict`, `config.py:52`": the class is at `config.py:50`. Line 52 is its `model_config` line (`extra="forbid"`). | Write `config.py:50-52`. |
| R3-COR-8 | Nit | 71, 100 | Group rule: the code comes from the first member, but facts are read "from `exc` itself only". A group whose first member is a `TimeoutError` therefore gets `code=timeout` and no facts, while the bare member would get facts. The behaviour is consistent but not stated. | Add one sentence: for a group, facts are those of the group (none). |
| R3-COR-9 | Nit | 146, 237 | The `locator_frames` row with a `co_filename` of `"a\x00b"` has no mutant that it kills (the NUL-raise went away with the `realpath` cut). Nothing kills removing the `type(co_filename) is str` check of rule (c). | Mark the NUL row "coverage only", or add a non-str `co_filename` row and a mutant for it. |

Verified (checked against the tree; the cited source files all exist and carry the cited text)
- Row counts. Active 134 is the sum of the 18 class minimums. Later 27 = ast_taint 6 + logging_layer 5 + writer_wiring 3 + classification 2 + provider_attrs 8 + chain 3. Not applicable 2. Total 163.
- Appendix A. 33 base active ids + 16 later + 2 not applicable = 51. `handover/ledger-seed.md` has BL-core-c18a-001 to 051 with no gap. 007 and 018 are process findings. 004, 010 and 032 are AST-guard rows. 005 and 033 fit "classification". 026, 030 and 045-047 are logging rows.
- Test files and constants. Nine created test-side files, matching the "2 source, 9 test" line. Nine `defaults.py` constants listed (DIAG_VERSION, LINE_CHARS, KEY_CHARS, STEP_CHARS, KIND_CHARS, MAX_FACTS, TB_STEPS, MAX_FRAMES, MAX_ERRORS). None exists yet in `src/` (grep `DIAG_` finds nothing). `guard/diagnostic.py`, `codes.py`, `tests/data/`, `tools/` and `src/hadavin_sdk/testing/` do not exist, as the ticket says.
- Code has 21 members (counted from the list) and `RESERVED_FOR` has 5 entries. `FactKey` has 20 members, matching the D9 order in `design-v3-FROZEN-amendments.md` line 41. The 8+8+4 split of fact sources sums to 20. `FACT_BOUNDS` covers the 11 number keys.
- Own exception classes: 22 on this tree (grep), exactly as the ticket lists them. The first 17 match the design's 17. All 22 appear in the `OWN_CODES` mapping.
- Class cites hold: `errors.py:4`, `bundle.py:67`, `store/protocol.py:25/41/45`, `runs.py:25`, `fake.py:17`, `llm/protocol.py:10/14` (the class has no attributes), `audit/protocol.py:10/14`, `anchors.py:12`, `egress.py:9`, `agent_loop.py:97`, `k1b/loop.py:77`, `secrets_vault.py:37`, `slack_channel.py:29`, `sources/__init__.py:25`, `tools.py:66`, `runmap.py:38/42/53`. `StoreUnavailable` subclasses `ConfigError`, so the table order matters and the ticket handles it by MRO.
- Writer cites: `extract.py:58` and `:34`; `tick.py:284/289/287-292/316/317/324/335`; `injection.py:96`; `cli.py:75/205/301/304`; `producers.py:33/36/37`.
- The six tick step names at `tick.py:249-266` match `TICK_STEPS`.
- `runmap.py` 417 and 485 are correct for this tree. Line 3's statement that `origin/main` differs for `runmap.py` is consistent with this tree being `ce70eb5`.
- ToolRefused sites `tools.py:503-601, 521, 620, 1030, 1130, 1137, 1148, 1150, 1180` all exist. Extra sites also exist (`:1106`, `:1184`, `:1188`, `:623`, `:627`), which the ticket's "all map to tool_refused" covers.
- Vault: `VaultError` is raised at `secrets_vault.py:91, 93, 119, 133`; `ConfigError` sites are `:112-180`; the 404 case is `:117`, as T7 says.
- Config: `config.py:120/316/436/453-454` and `registry.py:224`, `llm/anthropic.py:56` hold. `Config` is built from `_Strict` with `extra="forbid"`, so the T6 reasoning about `load_config` wrapping holds.
- `stats.upper_error_bound(5, 3)` raises `ValueError` at `stats.py:16` with a numbers-only message (read the source).
- Guard and project cites: `pyproject.toml` lines 6, 14-19, 16, 27 (pg extra), 81 (S101); `test_lockin_guard.py` 68-69 and 520; `test_k5_producers.py:118`; `ci.yml:42`; `fuzzgen.py:1`; `tests/__init__.py` exists; `tests/data/` absent; the five guard test files exist; `k1b/diagnosis.py`, `k1b/redaction.py` and `k1b/atomic.py` names match; `portal-kit/tools/mutation.py:84` has `Mutant`; `design-v3.md:30` mentions `token40`.
- Pydantic: `pydantic_core.core_schema.ErrorType` has 111 names on the installed 2.50.1 core (pydantic 2.14.1). All 26 closed names are present.
- Validation text bound: the longest closed name is 17 characters and the 108-character bound holds (85 + 8 + 14, inside the claimed 15 for the tail).
- Cross-ticket cites: `P5b1.md` lines 10, 33, 41 and `P5b3.md` lines 48, 87, 128, 136, 227 mention the cited items; `P2a.md:45` names SwitchChanged; `P1.md` lines 41 and 72 hold; `amendments.md:22` (F6) holds.
- Mutants: every mutant in Appendix B names a killer, and every named killer is defined somewhere in the Tests section (checked all ~45). The exceptions are the issues in R3-COR-3, 6 and 9.
- Template: all 17 fields appear in the template's order. Order 6(g), 7(3), 8(2), 8(5), 9(2), 20 items 4-6 and 21 item 17 are cited correctly. No real-looking secret in the ticket (the AWS example key is built from parts).

Not checked / UNVERIFIED
- No execution tool, so these are unconfirmed:
  - the sha256 values `FALLBACK_FP` = `2a1e659d` and the T10 `fp` = `ed342ffb`;
  - the probes: `"__main__" not in sys.stdlib_module_names`, the `gaierror` attributes, `sys.modules.get([])` raising `TypeError`, the `os.environ` frame, the psycopg sqlstates, the module/qualname identity of the library classes, and `co_filename == __file__` for `stats`;
  - the rendered golden lines T4-T10 (the ticket itself marks these UNVERIFIED);
  - whether `pydantic_core.ValidationError` can be subclassed;
  - whether the `tests/test_no_hardcoded_values.py` and `tests/test_lockin_guard.py` guards accept `FACT_BOUNDS`, `TICK_STEPS` and a `pydantic` import in `guard/diagnostic.py`.
- Whether this tree equals `ce70eb5`, and the `origin/main` 397ec97 changes (no git here).
- All statements about round 2 (finding ids, 29 fixed, 3 contested), the P5b1 round-2 resolve and the P5b1/P5b3 contents beyond the cited lines (reviews/ not read, by instruction).
- The `Mutant` signature, P1m file names and `scan_keyset` key-set semantics (from `tickets/P1.md` only; no code exists).
- `P4d`/`P4a` additions and which of P2a's four names are exception classes.
- That the throwaway worktree plan collects and runs (no run possible).

Verdict for the lead: with R3-COR-1 fixed, the correctness side supports a freeze. The remaining Minors can be fixed in the build notes (order 20 item 3) rather than in revision 4.
