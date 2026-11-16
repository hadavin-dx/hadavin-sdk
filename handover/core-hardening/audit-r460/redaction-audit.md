# R460 static audit: masking of personal data and secrets in src/hadavin_sdk (condensed copy of the auditor's inline report, 2026-11-16)
Read only; nothing run; regex behaviour is by reading, not executing; no old-code or mutation run seen. Not read: guard/bedrock_guardrail.py, guard/egress.py, guard/http.py, runtime/evidence.py, runtime/plan.py, approvals/*, audit/local_dir.py, every store/*, most of k1b/*, sources/kubernetes.py, actions/*, llm adapter bodies, demos/, most tests.
Verdict: NOT clean. 1 Blocker, several Majors. Masker core is strong; weak points are one unmasked model call, no single enforced exit, and formats the patterns miss. Core fixes belong to the lead's core PR (not mine).

## Paths
- 1.1 BLOCKER extract.py:47-53 sends `documents=[document]` raw to llm.chat; also the assistant turn text (59-63). producers.py:36 and 55-65 list extract.py as covered (false assurance). tests/test_k5_round9.py:91-109 driver never inspects `documents`. Ledger row R1-AK1-ADV-1 (handover/ledger.md:1807) already names it, OPEN. Fix: mask with runmap.redact_untrusted before the call, fail closed; add a driver capturing documents; re-record fake recordings.
- 1.2 MAJOR no single exit to the model: llm.chat called from extract.py:47, evals.py:73, judge.py:72, agent_loop.py:425, k1b/loop.py:94; masking is per caller. Fix: a MaskedLLM wrapper returned by the factory; test bans unwrapped use. guard/__init__ exports bare redact/redact_many (footgun, Nit). demos/ask-your-data pipeline exempted as "only the typed question" (unverified Major).
- 1.3 MAJOR cli.py:75 and 300-305 print exception text raw; ConfigError wraps str(exc) of pydantic/YAML (registry.py:223, config.py:120, 453); models.py Shape lacks hide_input_in_errors. Fix: safe_head once in main()/_tick(), hide_input_in_errors, strip YAML snippet.
- 1.4 NIT HADAVIN_DEBUG traceback raw (cli.py:81); root logger INFO (cli.py:287); receiver.py:63 debug request line.
- 1.5 MAJOR (defence in depth) AuditEvent fields free str (models.py:188-215; k1b/audit_sink.py:31-49; audit/chain.py:180-205). Fix: allowlist pattern validation.
- 1.6 NIT OS user name in audit rows (audit_sink.py:29, 52-56). 1.7 NIT redaction map stores raw originals by design (defaults.py:108-120); retention and role access not verified.
- Fine: judge.py:71, evals.py:63, agent_loop.py:367, tools.py:967, error_reason, injection.py:96, tick.py:292, llm/retry.py:77-80, audit/chain.py failure logs; cut-after-redact ordering tested.

## Patterns missed (guard/redact.py; by reading)
- 2.1 Major phone with ( ) . / separators. 2.2 Major IBAN in spaced groups or lower case. 2.3 Major card numbers other than 4-4-4-4 (17-19 digit, 15-digit Amex grouping, dot separated).
- 2.4 Major email with non-ASCII local part or domain; quoted local part; quoted-printable soft break.
- 2.5 Major credentials in pre-signed URL signatures, reset-link path tokens, webhook URLs of unlisted services, missing vendor key prefixes.
- 2.6 Major JSON name/value pair split (`{"name": "DB_PASSWORD", "value": ...}`) leaks on the runtime path, handled in the k1b path (inconsistency); bare `passphrase`, `cvv`, `pin`, `dob` keys.
- 2.7 Major base64-encoded personal data not decoded in the second pass.
- 2.8 Nit values the masker deliberately skips (`<hunter` without closing `>`; escaped quote ends the match). 2.9 Nit values split across fields (inherent, k1b states it).
- Time: one hostile text can hold a worker about 13 s (fail closed; Nit).

## Choke point and tests
- runmap.redact_text is a real choke point for text; reaching it is per caller (16 producer rows plus a source-parsing test). extract.py is the sibling miss.
- Tests weak: extract driver would pass on the leaking code; no tests for the pattern gaps above; no recorded failing-before runs seen.
- Fake-credential rule: literal fake passwords/keys remain in many test files (Nit); literal card test number in test_k5_tools.py:371 and a fixture (not on the allowed-literal list).
- Hardcoded: vendor endpoints fixed in llm/anthropic.py:23,54, llm/gemini.py:20, backends/table.py:370,540 (Nit); redaction limits are module constants, not config (Nit).

## Priority
1 extract.py Blocker; 2 MaskedLLM wrapper; 3 ConfigError masking + AuditEvent validation; 4 pattern gaps with a canary test each; 5 nits.
