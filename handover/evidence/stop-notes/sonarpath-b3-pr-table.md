# sonarpath batch 3: one row per path site still listed in the package (first-pass origin word)

Origin words: operator = typed by a person, config = a path in the config file, fixed = a constant of ours or not a file, package = a file shipped in the package, checked = validated by a function the scan cannot follow (named in the validator column). These words are a first pass by the builder and were not confirmed by a reviewer.

Package sites (src/hadavin_sdk): 75 listed groups, 82 hits in all, from tests/fixtures/pathguard_exceptions.txt (the tripwire test fails if a hit is added or removed without a row). Every site that takes a person-typed or file-typed name is guarded in code in this change, not listed.

| file | function | call | hits | origin | validator |
|---|---|---|---|---|---|
| src/hadavin_sdk/actions/executor.py | Executor._caller.call | .open | 1 | fixed | - |
| src/hadavin_sdk/actions/secrets_vault.py | VaultProvider.call | .open | 1 | fixed | - |
| src/hadavin_sdk/app.py | _tls_context | .read_text | 1 | checked | confined |
| src/hadavin_sdk/audit/chain.py | _Db.memory | sqlite3.connect | 1 | fixed | - |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._append_index | .exists | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._append_index | .read_bytes | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._append_index | .stat | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._append_index | open | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._entries | .exists | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._entries | .read_text | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._fsync_dir | os.open | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._write | .mkdir | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._write | .read_bytes | 1 | checked | _object |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._write | .unlink | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._write | os.link | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink._write | tempfile.mkstemp | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink.events | .read_text | 1 | checked | _object |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink.reconcile | .exists | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink.reconcile | .glob | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink.reconcile | os.replace | 1 | checked | join |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink.verify_object | .read_bytes | 1 | checked | _object |
| src/hadavin_sdk/audit/local_dir.py | LocalDirSink.write_outcome | .mkdir | 1 | checked | operator_dir |
| src/hadavin_sdk/audit/signer.py | _create | .unlink | 1 | checked | key_path |
| src/hadavin_sdk/audit/signer.py | _create | os.open | 1 | checked | key_path |
| src/hadavin_sdk/audit/signer.py | generate_key | .exists | 1 | checked | key_path |
| src/hadavin_sdk/audit/signer.py | generate_key | .unlink | 1 | checked | key_path |
| src/hadavin_sdk/audit/signer.py | key_path | .is_symlink | 1 | operator | operator_text |
| src/hadavin_sdk/audit/signer.py | key_path | .mkdir | 1 | operator | operator_text |
| src/hadavin_sdk/audit/signer.py | key_path | .resolve | 2 | operator | operator_text |
| src/hadavin_sdk/config.py | _read_yaml | .exists | 1 | operator | operator_dir |
| src/hadavin_sdk/config.py | _read_yaml | .read_text | 1 | operator | operator_dir |
| src/hadavin_sdk/evals.py | gate | .exists | 1 | config | confined |
| src/hadavin_sdk/evals.py | gate | .read_bytes | 2 | config | confined |
| src/hadavin_sdk/evals.py | gate | .stat | 1 | config | confined |
| src/hadavin_sdk/evals.py | gate | open | 1 | config | confined |
| src/hadavin_sdk/guard/judge.py | <module> | .read_text | 1 | package | - |
| src/hadavin_sdk/k1b/atomic.py | atomic_write | os.path.islink | 1 | checked | join |
| src/hadavin_sdk/k1b/bundle.py | load_bundle | .is_dir | 1 | operator | operator_dir |
| src/hadavin_sdk/k1b/bundle.py | load_bundle | .is_file | 1 | operator | operator_dir |
| src/hadavin_sdk/k1b/bundle.py | load_bundle | .is_symlink | 2 | operator | operator_dir |
| src/hadavin_sdk/k1b/replay.py | outputs_files | .is_file | 1 | checked | join |
| src/hadavin_sdk/k1b/score.py | _check_layout | .is_file | 1 | checked | operator_dir |
| src/hadavin_sdk/llm/common.py | post_json | .open | 1 | fixed | - |
| src/hadavin_sdk/registry.py | Registry.golden_sha256 | .is_file | 2 | checked | confined |
| src/hadavin_sdk/registry.py | Registry.golden_sha256 | .read_bytes | 2 | checked | confined |
| src/hadavin_sdk/registry.py | Registry.prompt | .read_text | 1 | checked | confined |
| src/hadavin_sdk/registry.py | Registry.prompt_sha256 | .read_bytes | 1 | checked | confined |
| src/hadavin_sdk/registry.py | _cross_check | .is_file | 1 | checked | confined |
| src/hadavin_sdk/registry.py | _load_tools | .glob | 1 | config | operator_dir |
| src/hadavin_sdk/registry.py | _load_tools | .is_dir | 1 | config | operator_dir |
| src/hadavin_sdk/registry.py | _load_tools | .is_file | 1 | config | operator_dir |
| src/hadavin_sdk/registry.py | _yaml | .exists | 1 | config | operator_dir |
| src/hadavin_sdk/registry.py | _yaml | .read_text | 1 | config | operator_dir |
| src/hadavin_sdk/registry.py | load_registry | .glob | 1 | config | operator_dir |
| src/hadavin_sdk/replay_records.py | read_records | .exists | 1 | config | operator_dir |
| src/hadavin_sdk/replay_records.py | read_records | .read_bytes | 1 | config | operator_dir |
| src/hadavin_sdk/runtime/agent_loop.py | _check_golden_refs | .is_file | 1 | checked | confined |
| src/hadavin_sdk/runtime/agent_loop.py | _check_golden_refs | .read_text | 1 | checked | confined |
| src/hadavin_sdk/runtime/agent_loop.py | qualified_runs | .exists | 1 | config | operator_dir |
| src/hadavin_sdk/runtime/agent_loop.py | qualified_runs | .read_bytes | 1 | config | operator_dir |
| src/hadavin_sdk/store/migrate.py | _migration_files | .glob | 1 | package | - |
| src/hadavin_sdk/store/migrate.py | _scan | .read_text | 1 | package | - |
| src/hadavin_sdk/store/migrate.py | migrate | .read_text | 1 | package | - |
| src/hadavin_sdk/store/migration_numbers.py | check_ledger | .is_file | 1 | package | - |
| src/hadavin_sdk/store/migration_numbers.py | check_migration_numbers | .is_symlink | 1 | package | - |
| src/hadavin_sdk/store/migration_numbers.py | check_migration_numbers | os.scandir | 1 | package | - |
| src/hadavin_sdk/store/migration_numbers.py | list_migration_files | os.scandir | 1 | package | - |
| src/hadavin_sdk/store/migration_numbers.py | read_files | .read_text | 1 | package | - |
| src/hadavin_sdk/store/migration_numbers.py | released_problems | .is_file | 1 | package | - |
| src/hadavin_sdk/store/migration_numbers.py | released_problems | .read_bytes | 1 | package | - |
| src/hadavin_sdk/store/postgres.py | ca_file | tempfile.mkstemp | 1 | fixed | - |
| src/hadavin_sdk/tools.py | ToolContext.fetch | .open | 1 | fixed | - |
| src/hadavin_sdk/tools.py | _module_files | .is_file | 3 | config | _module_files |
| src/hadavin_sdk/tools.py | load_tool_module | .read_bytes | 1 | config | _module_files |
| src/hadavin_sdk/tools.py | module_sha256 | .read_bytes | 1 | config | _module_files |

## Demos (not reviewed in this change)

The demos still hold path sites that nobody has reviewed in this change: demos are out of scope by decision of the lead. The list below is the earlier first-pass grep from batch 2 (origin guessed, to be confirmed by each demo owner); it is not exhaustive and not a claim that these sites are safe.

| file | line | code | origin |
|---|---|---|---|
| demos/ask-your-data/askdata/evalcli.py | 196 | `rep = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))` | to check |
| demos/ask-your-data/askdata/evalcli.py | 210 | `dest.write_text(clean(text) if fmt != "html" else text, encoding="utf-8", newline="\n")` | to check |
| demos/ask-your-data/askdata/evalcli.py | 221 | `ra, rb = (json.loads((p / "report.json").read_text(encoding="utf-8")) for p in (a, b))` | to check |
| demos/ask-your-data/askdata/config.py | 85 | `raw = yaml.safe_load(path.read_text(encoding="utf-8"))` | to check |
| demos/ask-your-data/askdata/ledger.py | 154 | `with open(self.path, "ab") as f:` | to check |
| demos/ask-your-data/askdata/ledger.py | 163 | `with open(self.path, "rb") as f:` | to check |
| demos/ask-your-data/askdata/ledger.py | 171 | `raw = self.path.read_bytes().split(b"\n")` | to check |
| demos/ask-your-data/askdata/pgsource.py | 148 | `_send(cur, VERIFY_SQL.read_text(encoding="utf-8"), prepare=True)` | to check |
| demos/ask-your-data/askdata/derive_allowlist.py | 29 | `for line in (DATA / "gold.jsonl").read_text(encoding="utf-8").splitlines():` | to check |
| demos/ask-your-data/askdata/derive_allowlist.py | 34 | `for line in (DATA / "exemplars.jsonl").read_text(encoding="utf-8").splitlines():` | to check |
| demos/ask-your-data/askdata/derive_allowlist.py | 64 | `COMMITTED.write_text(text, encoding="utf-8", newline="\n")` | to check |
| demos/ask-your-data/askdata/meter.py | 131 | `data = json.loads(self.path.read_text(encoding="utf-8"))` | to check |
| demos/ask-your-data/askdata/meter.py | 145 | `with open(tmp, "w", encoding="utf-8", newline="\n") as f:` | to check |
| demos/ask-your-data/askdata/meter.py | 149 | `os.replace(tmp, self.path)` | to check |
| demos/ask-your-data/askdata/meter.py | 156 | `with open(lock, "a+b") as f:` | to check |
| demos/ask-your-data/askdata/meter.py | 264 | `self.path.write_text("off\n", encoding="utf-8")` | to check |
| demos/ask-your-data/askdata/meter.py | 267 | `self.path.unlink(missing_ok=True)` | to check |
| demos/ask-your-data/askdata/evalrun.py | 79 | `with open(self.path, "a", encoding="utf-8", newline="\n") as f:` | to check |
| demos/ask-your-data/askdata/evalrun.py | 517 | `with open(out_dir / "results.jsonl", "w", encoding="utf-8", newline="\n") as f:` | to check |
| demos/ask-your-data/askdata/evalrun.py | 521 | `(out_dir / "report.json").write_text(` | to check |
| demos/ask-your-data/askdata/evalrun.py | 526 | `(out_dir / "report.md").write_text(render_md(report), encoding="utf-8", newline="\n")` | to check |
| demos/ask-your-data/askdata/evalrun.py | 527 | `(out_dir / "meter.json").write_text(` | to check |
| demos/ask-your-data/askdata/fixtures.py | 85 | `(recorded_dir / f"{key}-{n}.json").write_text(` | to check |
| demos/ask-your-data/askdata/fixtures.py | 110 | `fresh = {p.name: p.read_bytes() for p in Path(tmp).glob("*.json")}` | to check |
| demos/ask-your-data/askdata/fixtures.py | 111 | `have = {p.name: p.read_bytes() for p in Path(recorded_dir).glob("*.json")}` | to check |
| demos/ask-your-data/askdata/evalset.py | 102 | `for n, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):` | to check |
| demos/ask-your-data/askdata/evalset.py | 116 | `return hashlib.sha256(Path(path).read_bytes()).hexdigest()` | to check |
| demos/ask-your-data/askdata/evalset.py | 148 | `return Lock.model_validate_json(lock_path(eval_dir).read_text(encoding="utf-8"))` | to check |
| demos/ask-your-data/askdata/evalset.py | 156 | `with open(tmp, "w", encoding="utf-8", newline="\n") as f:` | to check |
| demos/ask-your-data/askdata/evalset.py | 160 | `os.replace(tmp, path)` | to check |
| demos/ask-your-data/askdata/prompt.py | 62 | `(template_path or TEMPLATE).read_text(encoding="utf-8"),` | to check |
| demos/ask-your-data/askdata/allowed.py | 67 | `(Path(__file__).resolve().parent.parent / "data" / "dataset_contract.json").read_text(` | to check |
| demos/ask-your-data/askdata/opscli.py | 128 | `dest.write_text(text, encoding="utf-8", newline="\n")` | to check |
| demos/ask-your-data/data/goldcheck.py | 95 | `json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()` | to check |
| demos/ask-your-data/data/goldcheck.py | 115 | `"plants": json.loads((root / "dataset_contract.json").read_text(encoding="utf-8")),` | to check |
| demos/ask-your-data/data/goldcheck.py | 116 | `"manifest": json.loads((root / "manifest.json").read_text(encoding="utf-8"))` | to check |
| demos/ask-your-data/data/goldcheck.py | 554 | `(DATA / "manifest.json").write_text(` | to check |
| demos/ask-your-data/db/build_verify.py | 33 | `checks = CHECKS.read_text(encoding="utf-8").strip().rstrip(";").strip() + "\n"` | to check |
| demos/ask-your-data/db/build_verify.py | 41 | `current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""` | to check |
| demos/ask-your-data/db/build_verify.py | 46 | `OUT.write_text(text, encoding="utf-8", newline="\n")` | to check |
| demos/ask-your-data/db/lumen.py | 737 | `MANIFEST_FILE.write_text(text, encoding="utf-8", newline="\n")` | to check |
