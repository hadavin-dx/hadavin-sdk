# P5a round 2, correctness review (ticket rev 2, 154 lines) - agent a715f7254d97e4143
Status: REPORTED (saved by the lead from the hand-back, condensed; model output, not user authority). Read-only; code read on current tree; git diff ce70eb5 HEAD not checkable.
Verdict: 1 Blocker, 7 Major (COR-2..8), 6 Minor, 3 Nit. Cites and counts check out; defects are in how tests are specified.
| id | sev | lines | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Blocker | 66,89,107 | test_real_writers_* are in the P5a diff and must fail on today's writers, but P5a wires nothing; Done demands the file passes at merge commit. (Same as R2-ADV-1.) | Evidence-only script, or strict xfail/later rows flipped by P5b3. |
| R2-COR-2 | Major | 63,66,87-89 | No named test runs each active row through diagnose/render/validation_text and applies expect; no row-to-writer adapter for fail-before. | Add test_active_rows_hold_on_new_code (parametrised) + adapter table (exception rows via run_tick, validation rows via extract). |
| R2-COR-3 | Major | 66 vs 28,49 | Fail-before worktree lacks guard/diagnostic.py; writer tests live in the file that imports it -> ImportError at collection. (Same as ADV-2.) | Own file tests/test_diagnostics_old_writers.py; name in Files and worktree command. |
| R2-COR-4 | Major | 152,43 | Mutant "frame check (f_globals is module dict) removed" killer compile() case also fails rule (c) so mutant survives. | Row exec(compile(src, real file, "exec"), {"__name__": real module}) passing (a),(c), failing only (b). |
| R2-COR-5 | Major | 41,152 | Mutant "type(name) is str removed": row passes on both versions (outer except gives fallback). | Make it a golden row with expect_code (OSError subclass with __module__ = [] -> code=os_error, real fp). |
| R2-COR-6 | Major | 43,101,152 | realpath mutant killed only by wheel/venv test that may be UNVERIFIED; equivalent on editable layout. (Same as ADV-6.) | Deterministic tmp_path symlink/relative __file__ unit test; wheel test bonus. |
| R2-COR-7 | Major | 45,65 | FIXED_TEXT content not given; T6 assembly (render has no validation_text slot) unspecified. (Same as ADV-3b.) | Table type -> fixed sentence/none; state T6 assembly. |
| R2-COR-8 | Major | 34,37,58 | Fact sources unspecified: pydantic errors() builds msg/input/loc (would trip instrumentation); gaierror has no gai attr (errno -2 outside 0..20000); cause_kind/field/key domains. | Name exact calls (errors(include_input=False, include_context=False) or error_count()); gai = errno for gaierror, errno omitted; give domains or "unused in P5a". |
| R2-COR-9 | Minor | 38,40,42 | chain/lib_frame stored not rendered; cannot be output-leak tests. | Cut to P5b3 or assert on record. |
| R2-COR-10 | Minor | 43 | realpath on co_filename with NUL may raise; one bad frame loses the code. | Local try/except per frame; row with "a\x00b". |
| R2-COR-11 | Minor | 35 | VaultError mapped to config_invalid but raised for HTTP status/response body (secrets_vault.py:91,93,119,133). | Map to provider_http; keep config_invalid for :112-180 ConfigError. |
| R2-COR-12 | Minor | 41 | Rule for other statuses (408,409,413,5xx,529) missing. | "Any other status keeps provider_http" + row. |
| R2-COR-13 | Minor | 37,38,40 | Fallback fp value, dropped= printing, locator/lib_frame regex, wrong-type step, BaseException input unspecified. | One line each. |
| R2-COR-14 | Minor | 65,144 | T10 names no function ("none identified"); ~50 raise sites in 14 files. | Name one (e.g. from stats.py). |
| R2-COR-15 | Minor | 87 | Oracle substring match with short canary keys matches almost any output. | Canaries >= 8 chars; meta-test no canary key shorter than P1 needle minimum. |
| R2-COR-16 | Nit | 24,27,54,144 | Stale UNVERIFIED on producers.py rows and test_repo_rules/test_no_reference_material (verified present). | Remove labels. |
| R2-COR-17 | Nit | 42 | __main__ may be in stdlib_module_names. | Explicit deny + row. |
Verified: 22 own classes at cited lines (17+5); tick.py/extract.py/runmap/injection/cli/tools/config/registry/anthropic/store cites; ErrorType 111 names with all 26 closed names; counts 21 Code, 20 FactKey, 12 ProviderErrorType, 13 constants, 140+16+2=158, Appendix A 51 ids once; 17 fields in order; P1 cites; orders 3,5,6,16,17.
Not checked: git diff ce70eb5 HEAD; scratch probes (pydantic 2.14.1, psycopg 3.3.6); P1 SK-1..6; Mutant signature; P2a class names; k1b/diagnosis.py clash; design-v3 beyond 20-41; NUL realpath; stdlib_module_names contents.
