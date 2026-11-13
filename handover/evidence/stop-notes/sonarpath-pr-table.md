# sonarpath PR table: demo sites NOT changed in this PR (demos are out of scope by lead decision)

Origin: operator = typed by a person, config = path in a config file, data = from a data file. File | line | call | origin (guess, to be confirmed by the demo owner)

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
