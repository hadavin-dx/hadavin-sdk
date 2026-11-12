# Evidence: PD part 2 (public-bind refusal, shared loopback check), head e75f9f25529c3108227b22a28836898e204c901f (EVIDENCE RUNNER, no judgement)

Head `e75f9f25` of `origin/wip/cloud-pd-bind` (3 commits on `2a8c2aac`) checked out in a clean detached worktree (`git rev-parse HEAD` equals the sha, `git status` clean before and after). Python 3.13.18. Own venv, own temp folder, own Postgres 16 on a private port; cloud and token variables unset. Raw logs: `/home/user/build/evidence-raw/pdbind-e75f9f25/` (outside the repo).

## Not run / deviations (first)
- **The first full run had 1 failure, caused by how I started Postgres, not by the code under test.** `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]` runs `dblink_connect('dbname=postgres')`, which connects through the server's default socket (`/var/run/postgresql`) and my server listens on port 54871 in its own folder: `could not establish connection ... .s.PGSQL.5432 failed`. I restarted Postgres with `PGHOST=127.0.0.1 PGPORT=54871` in the server's environment and re-ran only that file: `253 passed in 30.64s`, exit 0. I did NOT re-run the whole suite after the restart. So there is no single full-suite run with exit 0; the record is `1 failed, 10642 passed, 1 skipped` plus the file re-run.
- 1 test skipped in the full run: `tests/contracts/test_llm.py:95` (Stubber refuses a malformed Converse shape). No Vault tests were skipped (they were not in this run's skip list); I did not check whether `HADAVIN_TEST_VAULT_ADDR` is needed by tests that are deselected.
- `uv sync --locked --no-build` was not used (it failed in an earlier evidence run for the editable package); I used `uv sync --locked --all-extras --group test` (exit 0).
- `bandit` is not in the venv; I ran it with `uv run --no-sync --with bandit bandit -q -r src demos tools -ll`.
- Item 3: line `ok  CRASH  B6 ...` is how `bind_mutants.py` reports a mutant that makes the test crash instead of fail; the script counts it as good.
- Fail-before (item 5) on old code: the test files cannot be collected at all (the module `netguard` does not exist there). The "no module keeps its own loopback list" test was therefore run from a copy of its body (lines 201-225 of `tests/test_bindguard.py`) in a separate file.
- Hostile probes (item 6) use 45 spellings (the brief asked for 30). The bind-refusal probe sets one backend kind at a time on the fixture config (not validated, only `.kind` is read, same as `tests/test_bindguard.py`); it does not probe `systems` or `sources` entries.
- The mutation script `stage_mutants.py` and `bind_mutants.py` ran one after the other in the same worktree, after the full suite (no overlap with a gate).
- Not run: perf-marked and live-marked tests (excluded by the brief), CodeQL, SonarCloud, CodeRabbit.

## Results
| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 Full suite | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (own PG, `HADAVIN_TEST_PG_DSN` set) | 1 | `1 failed, 10642 passed, 1 skipped, 28 deselected in 402.26s` (the failure is the dblink test, see above) |
| 1b Re-run of the failing file | same, `tests/demo_askdata/test_validate_harm.py`, PG restarted with `PGHOST`/`PGPORT` | 0 | `253 passed in 30.64s` |
| 2 Stage mutants | `heavy.sh uv run --no-sync python tests/stage_mutants.py` | 0 | `37 of 37 good; problems: []` |
| 3 Bind mutants | `heavy.sh uv run --no-sync python tests/bind_mutants.py` | 0 | `18 of 18 good; problems: []` (17 `KILLED`, 1 `CRASH`: B6) |
| 4a ruff check | `ruff check src tests demos tools` | 0 | `All checks passed!` |
| 4b ruff format | `ruff format --check src tests demos tools` | 0 | `324 files already formatted` |
| 4c bandit | `bandit -q -r src demos tools -ll` (via `uv run --with bandit`) | 0 | only warnings (comment test names, `nosec` at `src/hadavin_sdk/tools.py:389` with no failed test); no issue lines |
| 4d scan_repo | `python tools/scan_repo.py` | 0 | no output apart from the uv warning |
| 4e gitleaks | `gitleaks git --redact --no-banner --config .gitleaks.toml --log-opts origin/main..HEAD` | 0 | `no leaks found` |
| 5a Fail-before: the 3 new test files on old `2a8c2aac` src | `PYTHONPATH=<old>/src pytest tests/test_bindguard.py tests/test_loopback_sites.py tests/test_netguard.py` (import path checked: `hadavin_sdk` came from the old src) | 2 | `3 errors in 0.52s`: all three `ImportError: cannot import name 'netguard' from 'hadavin_sdk'` (collection error, 0 tests ran) |
| 5b Fail-before: "no module keeps its own loopback list" body on old src | same method, copy of `test_no_module_keeps_its_own_loopback_list` | 1 | `1 failed`: `a copy of the loopback list: ['actions/secrets_vault.py:67', 'backends/table.py:68', 'config.py:166', 'guard/http.py:22', 'llm/openai_compat.py:37']`; same copy on head: `1 passed` |
| 6 Hostile probes | `python -I probe.py` (script at `.../pdbind-e75f9f25/probe.py`) | 0 | tables below |

`tests/bind_mutants.py` added 18 mutants; `tests/test_*.py` files added: `test_bindguard.py`, `test_loopback_sites.py`, `test_netguard.py` (git diff `2a8c2aac..HEAD -- tests`: 4 files added, `bind_mutants.py` the fourth).

## Hostile probes (item 6)
### `netguard.is_loopback_host` against Python `ipaddress.ip_address` on the same text
"Python ipaddress says" = whether `ip_address(text)` parses and its `is_loopback` flag (for a mapped IPv6 address also the flag of the IPv4 address inside). Python 3.13.18. Spellings of loopback are built from parts in the script.

| # | label | input (repr) | is_loopback_host | Python ipaddress says |
|---|---|---|---|---|
| 1 | plain v4 loopback | `'127.0.0.1'` | True | parses 4; is_loopback=True |
| 2 | v4 loopback range | `'127.255.255.254'` | True | parses 4; is_loopback=True |
| 3 | decimal int | `'2130706433'` | False | ValueError |
| 4 | octal dotted | `'0177.0.0.1'` | False | ValueError |
| 5 | octal int | `'017700000001'` | False | ValueError |
| 6 | hex dotted | `'0x7f.0.0.1'` | False | ValueError |
| 7 | hex int | `'0x7f000001'` | False | ValueError |
| 8 | short 127.1 | `'127.1'` | False | ValueError |
| 9 | short 127.0.1 | `'127.0.1'` | False | ValueError |
| 10 | trailing dot ip | `'127.0.0.1.'` | False | ValueError |
| 11 | trailing dot localhost | `'localhost.'` | False | ValueError |
| 12 | localhost upper | `'LOCALHOST'` | True | ValueError |
| 13 | localhost mixed | `'LocalHost'` | True | ValueError |
| 14 | userinfo trick | `'localhost@10.0.0.1'` | False | ValueError |
| 15 | userinfo trick 2 | `'127.0.0.1@evil.example.test'` | False | ValueError |
| 16 | prefix name | `'127.0.0.1.example.test'` | False | ValueError |
| 17 | suffix name | `'localhost.example.test'` | False | ValueError |
| 18 | unicode fullwidth digits | `'１２７.０.０.１'` | False | ValueError |
| 19 | unicode long-s localhost | `'localhoſt'` | False | ValueError |
| 20 | look-alike letter (capital I for l) | `'locaIhost'` | False | ValueError |
| 21 | v6 loopback | `'::1'` | True | parses 6; is_loopback=True |
| 22 | v6 loopback bracketed | `'[::1]'` | True | ValueError |
| 23 | v6 zone | `'::1%eth0'` | False | parses 6; is_loopback=True |
| 24 | v6 expanded | `'0:0:0:0:0:0:0:1'` | True | parses 6; is_loopback=True |
| 25 | v6 mapped loopback | `'::ffff:127.0.0.1'` | True | parses 6; is_loopback=True; mapped_inner_loopback=True |
| 26 | v6 mapped private | `'::ffff:10.0.0.1'` | False | parses 6; is_loopback=False; mapped_inner_loopback=False |
| 27 | v6 mapped hex | `'::ffff:7f00:1'` | True | parses 6; is_loopback=True; mapped_inner_loopback=True |
| 28 | v4 bracketed | `'[127.0.0.1]'` | False | ValueError |
| 29 | unbalanced bracket | `'[::1'` | False | ValueError |
| 30 | leading space | `' 127.0.0.1'` | False | ValueError |
| 31 | trailing space | `'localhost '` | False | ValueError |
| 32 | tab | `'localhost\t'` | False | ValueError |
| 33 | newline | `'localhost\n'` | False | ValueError |
| 34 | NUL suffix | `'localhost\x00'` | False | ValueError |
| 35 | NUL inside | `'127.0.0.1\x00.example.test'` | False | ValueError |
| 36 | wildcard v4 | `'0.0.0.0'` | False | parses 4; is_loopback=False |
| 37 | wildcard v6 | `'::'` | False | parses 6; is_loopback=False |
| 38 | empty | `''` | False | ValueError |
| 39 | all-zeros v6 bracketed | `'[::]'` | False | ValueError |
| 40 | v4-compatible v6 | `'::127.0.0.1'` | False | parses 6; is_loopback=False |
| 41 | ipv6 loopback with port | `'[::1]:8080'` | False | ValueError |
| 42 | v4 with port | `'127.0.0.1:8080'` | False | ValueError |
| 43 | not text: None | `None` | False | n/a (not text) |
| 44 | not text: bytes | `b'localhost'` | False | n/a (not text) |
| 45 | not text: int | `2130706433` | False | n/a (not text) |

### `bindguard.public_bind_problem` per backend kind
One kind swapped in at a time on the fixture config (all stand-ins; `real_services` of the untouched fixture config is `()`). Public bind = a private-range address; loopback bind = the 127.0.0.1 form. "table class" = which set of `backends/table.py` the kind is in.

| capability | kind | table class | real service? | public_bind_problem(public bind) | public_bind_problem(loopback) |
|---|---|---|---|---|---|
| secrets | fake | DEMO_ONLY | no | None (allowed) | None (allowed) |
| secrets | env | DEMO_ONLY | no | None (allowed) | None (allowed) |
| secrets | aws_secrets_manager | (none: real) | yes | refused | None (allowed) |
| secrets | vault | (none: real) | yes | refused | None (allowed) |
| secrets | azure_key_vault | (none: real) | yes | refused | None (allowed) |
| secrets | gcp_secret_manager | (none: real) | yes | refused | None (allowed) |
| secrets | mounted_file | IN_PROCESS | no | None (allowed) | None (allowed) |
| signer | none | NOT_PROD | no | None (allowed) | None (allowed) |
| signer | ed25519_local | IN_PROCESS | no | None (allowed) | None (allowed) |
| signer | aws_kms | (none: real) | yes | refused | None (allowed) |
| signer | azure_key_vault_key | (none: real) | yes | refused | None (allowed) |
| signer | gcp_kms | (none: real) | yes | refused | None (allowed) |
| signer | vault_transit | (none: real) | yes | refused | None (allowed) |
| anchor | none | NOT_PROD | no | None (allowed) | None (allowed) |
| anchor | s3_object_lock | (none: real) | yes | refused | None (allowed) |
| anchor | azure_immutable_blob | (none: real) | yes | refused | None (allowed) |
| anchor | gcs_retention_lock | (none: real) | yes | refused | None (allowed) |
| store | memory | DEMO_ONLY | no | None (allowed) | None (allowed) |
| store | postgres | (none: real) | yes | refused | None (allowed) |
| audit | local_dir | DEMO_ONLY | no | None (allowed) | None (allowed) |
| audit | chain | IN_PROCESS | no | None (allowed) | None (allowed) |
| llm | fake | DEMO_ONLY | no | None (allowed) | None (allowed) |
| llm | anthropic | (none: real) | yes | refused | None (allowed) |
| llm | bedrock | (none: real) | yes | refused | None (allowed) |
| llm | openai_compat | (none: real) | yes | refused | None (allowed) |
| llm | gemini | (none: real) | yes | refused | None (allowed) |
| detector | regex | IN_PROCESS | no | None (allowed) | None (allowed) |
| detector | llm_judge | IN_PROCESS | no | None (allowed) | None (allowed) |
| detector | bedrock_guardrail | (none: real) | yes | refused | None (allowed) |
| channel | fake | DEMO_ONLY | no | None (allowed) | None (allowed) |
| channel | slack | (none: real) | yes | refused | None (allowed) |

Counts from the second table: 31 kinds in the backend table; 18 count as a real service (a public bind is refused), 13 count as no real service (DEMO_ONLY 6, IN_PROCESS 5, NOT_PROD 2). A loopback bind was allowed for all 31. In the first table, rows where the two answers differ although Python parses an address: 23 (`::1%eth0`: Python says loopback, `is_loopback_host` says False). Rows where `is_loopback_host` says True and `ip_address` does not parse the text: 12, 13 (`localhost` in other letter case) and 22 (`[::1]` in brackets).
