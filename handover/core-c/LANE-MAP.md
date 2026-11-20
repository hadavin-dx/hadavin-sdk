# LANE-MAP: session core-c (lane "text, redaction, diagnostics", role TEXT)

Made 2026-11-20 on branch `cloud/core-c` by a read-only lookup (queue item Q2). Paths are under `src/hadavin_sdk/`.
Line numbers are the `def` / `class` lines found by search in the files as they stand on this branch. The "tests"
column lists test files (under `tests/`) whose text names the module or its public names; that is a text match,
not a proof of coverage (no test was run). `warden_port/` is a folder inside `tests/`.

| File (lines) | Purpose in plain words | Public names (line) | Tests that name it |
|---|---|---|---|
| `guard/redact.py` (1256) | The pattern redactor: finds known secret and identifier shapes (keys, tokens, e-mail, bank numbers, cloud resource names) and swaps each for a numbered placeholder such as `<EMAIL_1>` | `PATTERNS` (153), `strip_ansi` (825), `RedactionResult` (842), `redact` (862), `SECRET_KINDS` (1140), `redact_many` (1246); also `ARN_TAIL` (147), `ARN_CHAR` (152) | `warden_port/test_redaction*.py` (6 files), `test_k5_fixes1.py`, `test_k5_round10.py`, `test_k5_round11.py`, `test_k5_round9b.py`, `test_k5_perf.py`, `test_k1b_redaction_layers.py`, `test_p5p6_followups.py`, `test_lockin_guard.py` |
| `guard/runmap.py` (625) | The one choke point for redaction: makes text one spelling (Unicode NFKC form, invisible characters removed, escapes decoded), enforces the size cap, runs the redactor, keeps the per-run map of placeholder to original, and restores originals | `RedactionError` (38), `InputTooLarge` (42), `partial_escape_start` (87), `TooDeep` (98), `nfkc` (103), `hex_unescape` (126), `undo` (141), `fits_after_nfkc` (197), `storable_original` (244), `storable` (265), `canonical` (276), `replace_canonical` (298), `escape_placeholders` (322), `escape_markers` (333), `neutralise_untrusted` (340), `redact_untrusted` (345), `json_unescape` (366), `RunMap` (384), `redact_text` (464), `safe_head` (532), `drop_margin` (545), `redact_bounded` (554), `redact_value` (568), `restore_text` (601), `restore_value` (607), `has_placeholder` (617) | `test_runmap_partial_escape.py`, `test_k5_layers.py`, `test_k5_classes.py`, `test_k5_fixes1.py`, `_fixes2`, `_fixes3`, `_fixes9`, `test_k5_round5.py` to `test_k5_round12_fuzz.py`, `test_k5_review.py`, `test_k5_tools.py`, `test_k5_perf.py`, `test_k1b_redaction_layers.py`, `test_repo_rules.py`, `test_no_hardcoded_values.py` |
| `guard/egress.py` (30) | Outbound allowlist: refuses a call to any host not listed in `egress.yaml`; one spelling per host name | `EgressRefused` (9), `normalise_host` (13), `egress_check` (25) | `test_s4_llm_guard.py`, `test_http_metadata.py`, `test_k5_round10.py`, `test_cuj.py`, `test_repo_rules.py` |
| `guard/producers.py` (70) | Data only: the list of every function that produces text for a model, a vendor screen, a card or a log, and the redaction function each must call | `PRODUCERS` (14), `CHOKE_FAMILY` (44), `CHOKE_POINT` (52), `MODEL_CALLERS` (55), `OUTSIDE_THE_CHOKE_POINT` (67) | `test_k5_producers.py`, `test_k5_round8.py`, `test_k5_round9.py`, `test_k5_round12_fuzz.py` |
| `guard/injection.py` (101) | Screens text for "ignore your instructions" style attacks (prompt injection) with fixed patterns; writes a redacted log line | `Detector` (19), `RegexDetector` (38, `check` 50), `AnyOf` (61, `check` 69), `combine` (81), `injection_check` (85) | `test_s4_llm_guard.py`, `test_p6_detectors.py`, `test_p1a_fixes.py`, `test_p5p6_followups.py`, `test_k5_round5.py`, `_round7`, `_round8`, `_round9`, `contracts/test_capabilities.py` |
| `guard/judge.py` (109) | A second injection screen that asks a model; its input goes through `redact_text` first | `make` (39), `JudgeDetector` (62, `check` 68), `qualify` (100), `PROMPT` (26), `SCHEMA` (28) | `test_p6_detectors.py`, `test_p5p6_followups.py`, `test_k5_round7.py`, `_round8`, `_round9`, `_round11` |
| `guard/bedrock_guardrail.py` (114) | Same screen through a vendor service (Amazon Bedrock Guardrails); input redacted first | `check_filter` (43), `make` (61), `GuardrailDetector` (88, `check` 95) | `test_p6_detectors.py`, `test_p5p6_followups.py`, `test_k5_round8.py`, `_round9`, `_round11`, `test_client_profile.py`, `test_lockin_guard.py` |
| `guard/__init__.py` (14) | Re-exports `redact`, `egress_check`, `EgressRefused`, the detectors | (re-exports only) | UNVERIFIED |
| `approvals/gate.py` (698) | Cleans text before a person sees it on an approval card: removes control and invisible characters, makes links and mentions harmless, and replaces any command that could change something with the fixed wording `WITHHELD` | `strip_controls` (162), `normalise` (200), `sanitise_text` (312), `WITHHELD` (388), `withhold_commands` (681) | `warden_port/test_gate.py`, `test_gate_render.py`, `test_gate_review2.py`, `test_gate_review3.py`, `test_g4_parity.py`, `test_k5_round9.py`, `_round11`, `test_p5p6_followups.py`, `test_lockin_guard.py` |
| `approvals/channel.py` (126) | `clean`: the function every approval card text passes through (redaction, then the gate cleaning) | `clean` (18), `Channel` (69), `FakeChannel` (85) | UNVERIFIED (not searched) |
| `approvals/cards.py` (111) | The fixed headers and labels of the cards (wording a person reads) | `SHADOW_HEADER` (18), `ABSTAIN_HEADER` (19), `LABELS` (20), `Card` (28), `would_be_text` (52), `render_shadow` (66), `render_abstain` (99) | `test_k3_pilot.py`, `test_k3_review_fixes.py`, `test_k5_tools.py`, `test_k5_postgres.py` |
| `tools.py` (1206), lines 663-1012 only | Scrubs a tool result of the secrets the tool was handed, in every encoding it can undo; cuts long text safely | `truncate` (663), `prepare_output` (936), `redact_layered` (976), `error_reason` (987) | `test_k5_fixes5.py` to `test_k5_fixes9.py` and `test_k5_layers.py` per CHANGELOG line 21 (UNVERIFIED by search) |
| `scrub_settings.py` (26) | The validated settings (with allowed ranges) for that tool-result scrub; defaults live in `defaults.py` lines 60-74 | `ScrubSettings` (15) | `test_k5_fixes9.py`, `test_k5_layers.py`, `test_runmap_partial_escape.py` |
| `errors.py` (5) | One shared error: the client config is invalid, the process must not start | `ConfigError` (4) | named in about 48 test files; start with `test_s1_foundation.py`, `test_client_profile.py` |
| `k1b/redaction.py` (195) | Masks every value of a recorded incident bundle before replay; masks whole values under sensitive key names | `SCHEME` (36), `LIMITS` (41), `MASKED` (86), `SENSITIVE_KEY` (88), `sensitive` (97), `redact_bundle` (172) | `test_k1b_redaction.py`, `test_k1b_redaction_layers.py`, `test_k5_round7.py`, `_round8`, `_round9` |
| `k1b/diagnosis.py` (122) | "Diagnostics" here: the strict shape and strict JSON parsing of the model's diagnosis (list of causes) | `DIAGNOSIS_SCHEMA` (26), `Cause` (56), `Diagnosis` (69), `parse_diagnosis` (87), `strict_json_loads` (110), `parse_diagnosis_text` (115) | `test_k1b_diagnosis.py`, `test_k1b_bundle.py` |
| `guard/textnorm*` | Named in the plan as owned by this lane. **Does not exist on this branch.** Only traces: `.gitleaks.toml` lines 40-44 and `tests/test_ci_gitleaks_scope.py` line 174 allow a fixture `tests/fixtures/textnorm_golden.json`, which is also absent | none | none |

Duplicates to know before building `textnorm`: text normalisation already lives in four places: `runmap.nfkc` /
`canonical` (103, 276), `gate.normalise` / `strip_controls` (200, 162), `egress.normalise_host` (13) and
`redact.strip_ansi` (825). Two different private functions are both called `_views` (`runmap.py` 401, `gate.py` 212)
and two `_kind` (`redact.py` 1191, `k1b/redaction.py` 50). Whether they overlap in behaviour is UNVERIFIED.

## The repo's own lint and test commands

- Install: `uv sync --group test` (README, "Running the tests").
- Lint: `ruff check src tests demos tools` and `ruff format --check src tests demos tools` (`.github/workflows/ci.yml` lines 80, 82; rules in `pyproject.toml` `[tool.ruff]`, line length 100, relative imports banned).
- Fast tests, as CI runs them: `pytest -q -n 3 -m "not live and not perf"` (use `-n 2` on a 2-core machine).
- Timing tests, alone and without `-n`: `pytest -q -m perf`. Tests marked `live` call paid services: never without the owner's yes.
- Security scan: `bandit -q -r src demos tools -ll` (`ci.yml` line 181).
- The studio preamble (rule 8) wraps these as `uv run --all-extras --group test ruff check|format` and `uv run --all-extras --group test pytest`.

## NOT CHECKED

- Nothing was run: no test, no lint, no install. "Tests that name it" is a text search, not measured coverage.
- Function bodies were not read, except `egress.py`, `errors.py`, `scrub_settings.py`, `producers.py` and `guard/__init__.py` (read whole). Purposes of the other files come from names, docstring heads, README and CHANGELOG.
- Private names (leading underscore), `guard/http.py` (network address checks, not text), `runtime/`, `llm/`, `audit/`, `store/`, `cli.py`, `demos/` and the mutation-test files (`tests/stage_mutants.py`, `tools/`) were not mapped.
- CHANGELOG below line 60, `handover/core-c/ORDERS.md` and `inputs/plan-v*.md` (where `textnorm` is defined) were not read.
- Which tests cover `approvals/channel.py` and `guard/__init__.py`; whether any listed public name is unused (dead code).
