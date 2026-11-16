# core/ci-lint-set eeaa502: codebase-details review (condensed by cloud worker). 0 Blocker, 2 Major
Verdict: no behaviour change found in money/redaction/security/SSRF paths as read from the diff (snapshot has diff + 7 files only; nothing executed).
Major 1: same as design B1 (select loses E4/E7/E9/W; docs contradict config).
Major 2: no pytest output in evidence; behaviour-preserved claims rest on reading the diff; full suite + stage_mutants at eeaa502 UNVERIFIED.
Redaction: approvals/channel.py untouched by the diff; gate.py only had dead helpers deleted; vulture on main (base 0dabf1f) already flagged gate._rendered unused, so the fix was never wired in: consistent with "also on main". Put base SHA 0dabf1f and path in ledger row.
gate._views not proven dead by vulture (name clash with runmap._views); no grep of tests/demos for gate._views/_rendered.
tools.py START_MARKER, MIN_REDACTION_WINDOW removed: public module names, external import UNVERIFIED; name them in CHANGELOG; policy inconsistency vs MIN_SCRUBBED_SECRET kept by whitelist.
UNVERIFIED equivalence: tools/mutation_runner.py `return build()` -> `build(); return` (drops value); redact._quote no longer module-level; vault_fake._ONE -> functools.cache; test_k5_round5 `}[body]()` -> `}[body]` (RSE102).
Tests not weakened: only 12 removed lines with assert/def test_, all operand swaps; no new noqa/type-ignore/nosec. Whitelist bare names global (window, side_effect, register, serve, extract, neutral, schema_version x2, fp, newurl, _.handle); test-only names may hide dead core code; extend-exclude of vulture_whitelist.py is new (docs say no per-file ignore added). agent_loop.py formatter gave `except (\n Exception\n):` (ugly).
