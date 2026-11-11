RESULT REVIEW Q8a-1 (package Q8a-1, live override refusals, security path), round 6 (delta), head 3f3d4b6c, persona: codebase details. Method: I read the files in the snapshot /home/user/build/snap/q8a1b5-3f3d4b6c and the unchanged main files under /home/user/build/B-Q8b-base. I ran nothing: no tests, no mutants, no lint.

Verdict: no Blocker, no Major. All 9 round-5 fixes are present at the cited lines. I found 1 Minor (a sibling YAML error site the choke point misses) and 2 Nits. The builder's claim about the two unkillable mutants is correct.

### [D1] Minor - A YAML error in `tools/<agent>.yaml` still escapes with its quoted line, and the CHANGELOG says `load_registry` is covered
Where: registry.py:261 (`parse_manifest(_yaml(path), where)`, inside `_load_tools`, called at registry.py:234). The `try` that wraps it in `config_error_text` ends at registry.py:230. CHANGELOG.md:13, the sentence "this holds for what `load_config` and `load_registry` raise (... a YAML error with its line and column only ...)".
What: `_yaml` (registry.py:180) calls `load_yaml`. Only the reads at registry.py:211-212 and 224-226 are inside the `except ... config_error_text` blocks. The `tools/*.yaml` read at 261 is outside any `try`. A malformed YAML file there raises a raw `yaml.YAMLError`. Its `str()` includes the scanner snippet of the offending line. I derived this by reading; I did not run it.
Why it matters (concrete input -> wrong output): a line such as `note: "<credential text> and no closing quote` in `tools/test-agent.yaml` makes `load_registry` raise a YAMLError whose text quotes that line. Anything that prints the exception shows it, or a log of the traceback does. `cli.main` prints only the class name for a non-`ConfigError` (cli.py:77 comment), so the command line is safe. The documented guarantee is still false for a library caller. The new tests pin broken YAML only for `config.yaml` and `agents.yaml` (test_stage_names.py:1158-1167). A `tools/` YAML file is the sibling case of the same class, and no test covers it.
Suggested fix: route it through `config_error_text(exc)` with `from None`, either by moving the `_load_tools` call inside a `try` or by wrapping `_yaml` itself. Add a test and a mutant. Or narrow the CHANGELOG sentence to the files named.

### [D2] Nit - Extra keys: the error shows the key name, but the docstring says it never shows the refused value
Where: config.py:505 (`".".join(str(p) for p in e["loc"])`), and the docstring at config.py:509-514 ("never the value that was refused (a mistyped key or a pasted login can be a secret)").
What: for `extra="forbid"` models (config.py:61, table.py:24, registry.py:35-60) pydantic puts the unknown key in `loc`. A YAML key that is itself pasted credential text, for example `<token text>: 1` at the top level, under `evidence:` or inside a backend entry, is printed. The CHANGELOG sentence (line 13: "does not cover the names of fields, kinds and items") is honest about this. The docstring wording ("mistyped key") reads as broader than the code. No test or mutant covers a key.
Suggested fix: change the docstring to say that names (field and key names) are shown. Or replace the unknown key in `loc` with `<unknown key>` when `e["type"] == "extra_forbidden"`.

### [D3] Nit - the copy sentence is attached to every given-time refusal
Where: tick.py:57-60 and tick.py:97.
What: fix 3 (`dataclasses.replace`) is implemented by one message. `NO_GIVEN_TIME_COPY` ends "A context is not copied by replace() ...; build a new TickContext(app)". It is raised for every `TickContext(app, <time>)` outside demo, not only for `replace`. A person who wrote `TickContext(app, t)` reads advice about `replace()` that does not match what they did. The code runs and the tests pin the text (test_stage_names.py:624, 653; test_q8a_live_overrides.py:763-767). It is only wording.
Suggested fix: leave as is, or word it "(a copy made with replace() carries the old time as a given one)".

## Verification of the 9 fixes (round-5 items 1-9)
1. Item 1, M1 value-free config errors: the class fix is in place.
   - `config_error_text` (config.py:509-522) is the one choke point. It gives a pydantic error with loc, msg and type only (config.py:499-506), a YAML error as line and column only, and any other error as its type.
   - Every wrapping site uses `from None`: config.py:134, 562, 564 and registry.py:216, 230. The result is a `ConfigError` with no `__cause__`.
   - The custom messages no longer carry a value:
     - config.py:408-421 (login, https, system name only)
     - config.py:413 (route)
     - config.py:290-309 (lists counted with `len(...)`)
     - config.py:114 (unknown kind)
     - config.py:465 (duplicate key, line number only)
     - config.py:489 (path)
     - registry.py:190 (duplicate id, entry number only)
   - The `_validation_text` rename branch (config.py:529-541) prints only `_RenamedStage` text and `loc` and `msg`.
   - The CHANGELOG sentence at line 13 now states exactly what is and is not covered, and it is true. Its exception is D1.
   - Tests at test_stage_names.py:1137-1302 use made-up credentials built from parts and `_everything_shown`, which covers str, repr, cause and traceback. `_assert_value_free` also asserts `exc.__cause__ is None`.
   - Mutants M15a to M15o (stage_mutants.py:253-297) each revert one site. I checked the anchor strings against the source and each is unique in its file.
2. Item 2, "four": tick.py:16 now says "Four refusals", and CHANGELOG.md:10 lists all four.
3. Item 3, `replace()`: refused with the copy sentence (tick.py:57-60, 97). The `TickContext` docstring names `replace()` (tick.py:74-76). The test covers `replace(ctx, now=...)` and `replace(ctx, results={})` (test_q8a_live_overrides.py:763-767). Mutant M14b makes the raise use `NO_GIVEN_TIME`, and the equality at test_stage_names.py:624 and 653 then fails. It can fail.
4. Item 4, subclass upgrade step: CHANGELOG.md:11 has the bold sentence "Test code that subclasses `TickContext` now fails at import with a `TypeError`...".
5. Item 5, mutants and tests: covered by the M15 series and the tests above. Only the two flags named below have no killer.
6. Item 6, wording: the CHANGELOG is split into headed bullets (lines 8-14 and the limits at 15-21). The plain sentence comes first at lines 7 and 15. "frozen", "stand-in" and the pickle are glossed.
7. Item 7, one copy of `STEPS`: `own_steps = tuple(STEPS)` at tick.py:458. The checks at 461 and 463 and the loop at 478 all use it.
   - The test (test_stage_names.py:1268-1296) cuts the list in place during the first store read, which happens after the checks.
   - Mutant M14a changes the loop back to `STEPS`. The mutated tick then runs one step and the assertion at 1296 fails. It can fail.
8. Item 8, measured figure: CHANGELOG.md:20 says "measured at ecd5dba1" and points to the evidence RESULTS.md. I did not read that file; it is not in the snapshot.
9. Item 9, same-process limits: CHANGELOG.md:15 and 19-20, tick.py:79-82 and 447-453, and app.py:118-123 state them. The three probes are named with their measured results, and the purge identity is named as the control.

## The builder's claim: `include_url=False` and `include_context=False` mutants cannot fail
The claim is correct. These are equivalent mutants.
- `_value_free_text` (config.py:499-506) builds its output only from `e["loc"]`, `e["msg"]` and `e["type"]`.
- The `include_url`, `include_input` and `include_context` flags only add the keys `url`, `input` and `ctx` to the dicts. They never change `msg`, `loc` or `type`, and the code never reads those added keys.
- So any of the three flags set to True gives byte-identical output. No test can tell them apart.
- `include_input=False` is the same: it is a no-op for this output, and the builder did not list it. The effective protection is "print only loc, msg and type".
- What would make a real mutant is changing the formatter to print `e.get("input")`, `e.get("url")` or `e.get("ctx")`.
- Suggested handling: delete the three dead flags, or keep them as belt and braces and say so in a comment. Add one mutant that appends `e.get("input")` to the printed line. It would be killed by `test_a_registry_validation_error_does_not_echo_the_value` (test_stage_names.py:1184), whose models do not hide input. Record the equivalent mutants in the ledger as accepted-equivalent, not as "cannot be made to fail" with no reason.

## Checked and found fine
- `_value_free_text` header layout uses `exc.title` and the plural form correctly (config.py:503).
- `config_error_text` handles a `MarkedYAMLError` with `problem_mark is None` through the generic `YAMLError` branch (config.py:517-521).
- The `_renamed_stage` path (config.py:392-402) and the `_validation_text` others-branch print `msg` only.
- Other error renderers I checked:
  - tools.py:118-120 prints field names only and uses `from None`.
  - registry.py:293, 302, 307 print names, not values.
  - app.py:376-382 print a CA name or path, with `from None`.
  - The `deferred.key_problems` keys come from a fixed set.
  - config.py:134 names the capability and the kind, which is a known table kind at that point.
- `run_tick` order is refuse keywords, copy, missing step, repeated name, then `TickContext` (tick.py:454-465). Nothing runs before a refusal.
- `_now` uses `type(ctx) is not TickContext` (tick.py:105). `__init_subclass__` raises `TypeError` (tick.py:84-87).
- Mutants M9d, M9e and M9f replace strings that occur once each in tick.py (lines 455, 96 and 105).
- CHANGELOG limit texts, tick.py docstrings and app.py docstring agree on the covered and not-covered lists.

## Not checked
- Any run (pytest, mutant runner, ruff, bandit, Postgres tests, the evidence at `handover/evidence/Q8a-1/ecd5dba/`).
- How a `ValidationError` raised inside the `SourceConfig` validator (config.py:330, `KINDS[...].settings(**...)`) is turned into a message. The new text path only reads `msg` and `loc`, so it is covered either way. The key issue is D2.
- The pydantic version pin. `errors(include_input=...)` needs a recent pydantic; pyproject.toml is not in the snapshot.
- agent_loop.py:129 and llm/anthropic.py:56 (`{exc}` with `from exc`). Both are unchanged files that run at build time or run time, not at config load. The CHANGELOG names them as out of scope ("errors raised later by `app.build` or a backend").
- DIFF.patch line by line; I read the final files.