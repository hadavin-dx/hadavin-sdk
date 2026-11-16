# Q8a-1 fix batch b8 (builder notes)

Branch core/q8a-1-live-override-refusals. Base a18696556beacbf13664da0299cabf56d48d1ddf. Builder head: see the end of this file
(filled in at hand-over): 18741c8cfdfc67e073139ad4e5df0f744d96b495. No merge, no PR, no spend, no live call.

## What was asked (round 8 report, 10 issues) and what was done

| Issue | Where fixed (choke point) | Proof |
|---|---|---|
| 1 Plain-id filter showed any lower-case text typed as an id | `errors.shown_name` / `word_like` / `loaded_ids` (ContextVar); loaders set the active set | `test_the_name_filter_is_a_shape_and_membership_check_only`, `test_a_name_with_a_long_run...`, `test_a_secret_shaped_text_typed_as_an_id_is_not_shown_by_any_loaded_id_message` (6 shapes), `test_a_word_like_loaded_id_prints_as_itself...`; mutants M16j, M17x, M18a, M18b |
| 2 Files opened from a configured path could leak OS text or be read as empty | `errors.read_configured` / `list_configured` / `unreadable`; every open driven by a config value goes through them | `test_read_configured_*`, `test_list_configured_*`, `test_a_config_file_that_is_a_loop_of_links...` (5 files), `test_an_actions_file_a_tools_manifest...`, `test_a_tls_ca_file_...`, `test_the_other_configured_paths_say_a_fixed_sentence...`, `test_a_prompt_or_golden_file_...`; mutants M16h, M17q, M17r, M18c-e, M18t, M18u |
| 3 Pins: a pasted credential in a pin position | `Config._pins_are_digests` (position only), `errors.is_digest` / `digest_prefix` | `test_a_tool_module_pin_must_be_a_sha256...`, `test_a_module_whose_pin_does_not_match...`; M18f, M18g |
| 4 Names quoted in secrets / model / source / tool / approval messages | each site goes through `shown_name(name, <loaded collection>)` or says the position / field; guard test | `test_no_config_derived_name_is_put_in_a_message_outside_the_one_filter` (fails on a1869655: 31 hits, passes now: 0), vault, alias, fetch-echo, `_own_secrets` tests; M17t, M17u, M18m-p, M18s |
| 5 / 7 Library errors (Decimal etc.) and unreadable config | `config.load_config` catches `ArithmeticError`; OSError removed because the reader owns it; `confined()` resolve errors | `test_a_decimal_error_out_of_a_validator...`, `test_confined_refuses...`; M18h |
| 6 `System.base_url` | now `ConfigUrl` (one URL type); `url_has_login` removed (nothing used it) | `test_a_login_inside_a_system_base_url...`; M15a, M16c |
| 8 Empty manifest narrowed `tools_allowed` | `registry._load_tools` checks only `if specs` | `test_an_empty_tools_manifest...`; M17p, M18k |
| 9 Non-text manifest key, ports message | `tools.parse_manifest` catches `(TypeError, ValueError)`; ports message shows a count | `test_a_manifest_entry_with_a_non_text_key...`; M18q |
| 10 Nits | docstring reworded; chains-as-folder assertion exact; `__suppress_context__` assertion added to the probe-row test (it holds for all 127 rows: no real context leak); every member of `_FIXED_SENTENCE_TYPES` is now produced by a case (13 cases added, one assertion that the set is covered); CHANGELOG updated | `test_every_pydantic_message_type_that_is_shown_as_written_holds_no_typed_value` |

Extra siblings found and fixed in the same batch (class-level, not asked by name):
- `registry._is_config_file`: an over-long `ca_file` or `prompt_file` raised a bare `OSError` (found by my own new test); same helper now used by both.
- Run-time opens of prompt, golden set, golden documents, judge.jsonl, qualified.jsonl (`registry.py`, `evals.py`, `runtime/agent_loop.py`, `guard/judge.py`) were bare `read_text/read_bytes`: now `read_configured`.
- `KubernetesSettings` was a plain model that echoed the refused URL (login) in the raw pydantic text: `hide_input_in_errors=True`.
- The probe set showed 3 tool-call rows that quoted host, operation and method (they quote nothing now).

## New wording of each stale test (updated on purpose, none weakened)

| Test | Old text expected | New text expected |
|---|---|---|
| tests/contracts/test_secrets.py | `'missing' cannot be read` | `secret missing cannot be read at start-up \(` |
| tests/test_s3_gate.py | old chain_id message with the id | `action lookup_record: chain_id names no chain` |
| tests/test_p2_postgres.py | `'pg-dsn' cannot be read` | `secret pg-dsn cannot be read at start-up (KeyError)` |
| tests/warden_port/test_audit_chain.py | old | `could not verify: secret pg-dsn cannot be read at start-up (KeyError)` |
| tests/test_p4b_secrets.py (4) | `VAULT_TOKEN is not set`; `approle sign-in refused`; `cannot read ...gone`; `no field 'nope'` | `the configured environment variable is not set`; `the configured auth mount: sign-in refused (400)`; `jwt_path): cannot be read (FileNotFoundError)`; `secret db has no field named by .field. in Vault` |
| tests/test_stage_names.py | filter test (64 chars, no colon) | renamed; 40 characters, colon allowed, digit first hidden, long runs hidden |
| tests/test_stage_names.py | `principal svc:test-agent: rights entry 1 ...` etc. | `principal svc:test-agent: rights entry 1 names no action`, `principal user:a: approver_of entry 1 names no chain` |
| tests/test_stage_names.py | platform_secrets `bound` sentence | `may read only the secrets named in its own settings (a name that is not one of them is never quoted)` |
| tests/test_stage_names.py | CA empty sentence | `the CA bundle is empty` |
| tests/test_stage_names.py | `base_url must not contain a login` | `systems.fixture-records.base_url` and `a URL must not contain a login` (the one URL type's sentence) |
| tests/test_k3_pilot_env.py | unchanged: passes because `approver_ids` are checked only for a chain a principal names |

## Rung table (tool ladder)

| Component | Rung | Why lower rungs were rejected |
|---|---|---|
| One reader for configured files, name filter, guard test | 1 reuse: extended `errors.py` / `config.py` / `registry.py` choke points | nothing lower; no new module, no new dependency |
| Probes | 1 reuse: the evidence runner's probe scripts, repointed | none |

## Decisions and things to know (read these)

1. CONTRADICTION with the brief, not fixable: "the 7 lower-case plain-id markers should read 0". Those probe rows put the marker `zq-probe-mk4417` as the id of a loaded thing (agent, action, chain, principal). D-2322 shows a word-like name that is the id of something loaded, so such a marker prints when it really is the id. At this head 6 of those probe rows read the marker (see probes-head.txt, group PLAINID); the 7th (a duplicate-id row) is refused by a position-only message. Realistic secret shapes (32 or 64 hex digits, a 54 character token, a 24 digit run, 41 characters, `sk-` plus hex) typed in the same places read 0 (probes-b8.txt: 24 SHAPE rows, 0 readable; and the parametrised test). Short lower-case words that are ids cannot be told from a secret by any filter; this is the designed limit.
2. The 2 validator rows "ConfigValueError holding the marker (author slip, for contrast)" and the 7 `K8S api_url` rows are labelled LEAK-READABLE by the probe script on purpose or because it also looks at the raw pydantic string of a settings class built directly; the text the loader prints (`config_error_text`) is clean for all of them. The Kubernetes class now also hides the input in its raw string (see above); the 7 rows still show `pydantic str has marker` for the OTHER URL classes the script builds directly. Not hidden here: see "what I did not check".
3. `confined()` no longer lets a `RuntimeError` / `OSError` / `ValueError` out; a loop or an over-long name does resolve (non-strict `resolve`), and the open that follows is refused by the reader.
4. CLI key commands (`load_private_key`, `load_public_key`, key-dir paths in `audit/signer.py`) were left alone on purpose: those paths are typed by the operator on a command line, not read from a configuration file. They are in the guard's allowed list with that reason.
5. `store/migrate.py`, `store/migration_numbers.py`, `guard/judge.py` PROMPT (a file shipped in the package) are not configured paths and were left alone.

## What I did not check
- Run-time opens not in start-up or gate paths: `audit/local_dir.py` object reads other than the index, `actions/secrets_file.py` (`os.open` on a mounted secret path), `audit/signer.py` key-dir paths, `replay_records.py`. (The six secret-provider modules now never quote a configured secret name and are in the guard.) They take their folder from configuration but I did not change them; they are the next candidates if a reviewer wants the class complete there.
- Windows behaviour (permission, long-path rules): all runs are on Linux; the permission-denied cases use a monkeypatched `os.listdir` because the session runs as root (the probes ran as user nobody).
- Live services: none called.

## Final counts
See handover/evidence/Q8a-1/b8/RESULTS.md: full pytest 11024 passed 1 skipped; 160 of 160 mutants good; 50 failures on old src.
