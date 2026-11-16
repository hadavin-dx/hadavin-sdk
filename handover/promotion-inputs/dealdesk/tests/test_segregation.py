"""segregation (segregation) and repo hygiene (client-repo hygiene): no other demo's or client's name, no learned state, one namespace, byte-identical outputs with another
demo absent or present (with a canary), and no read outside this demo's folder."""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from engine_kit import D

from dealdesk import store

PARTS = {  # other demos' identifiers and studio-internal names, built from parts so this file does not contain them as literals
    "ape" + "xc",
    "ask-your" + "-data",
    "text-to-" + "sql",
    "bho" + "vix",
    "Port" + ".io",
    "Context " + "Lake",
    "AI Software " + "Factory",
    "r-" + "ref-",
    "r-" + "intake-",
    "demos/" + "refunds",
    "demos/" + "intake",
    "hadavin-demos-" + "refunds",
    "hadavin-demos-" + "intake",
}
SKIP_DIRS = {".venv", "__pycache__", ".ruff_cache", ".pytest_cache", "mutation", "tests_oneshot"}
SKIP_FILES = {"uv.lock", "test_segregation.py", "test_doc_consistency.py", "mutation_check.py", "RESULTS.txt"}
BANNED_SUFFIX = {
    ".pt",
    ".pth",
    ".onnx",
    ".safetensors",
    ".gguf",
    ".bin",
    ".faiss",
    ".index",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pkl",
    ".parquet",
    ".ipynb",
}


def files():
    for p in D.rglob("*"):
        if p.is_file() and not (set(p.relative_to(D).parts) & SKIP_DIRS) and p.name not in SKIP_FILES:
            yield p


def test_hygiene_scan_no_other_demo_or_studio_names_no_learned_state_no_binaries():
    hits, bad_types, big = [], [], []
    for p in files():
        if p.suffix.lower() in BANNED_SUFFIX:
            bad_types.append(str(p.relative_to(D)))
        if p.stat().st_size > 300_000:
            big.append((str(p.relative_to(D)), p.stat().st_size))
        text = p.read_text(encoding="utf-8", errors="ignore").lower()
        hits += [(str(p.relative_to(D)), n) for n in PARTS if n.lower() in text]
    assert not bad_types and not big, (bad_types, big)
    assert hits == [], hits


def test_notebooks_with_outputs_and_models_do_not_exist():
    assert not list(D.rglob("*.ipynb")) and not any(p.suffix in {".bin", ".safetensors"} for p in files())


def test_every_store_key_lives_in_the_one_dealdesk_namespace():
    s = store.TenantStore("t-a")
    for kind in store.KINDS:
        assert s.key(kind, "n").startswith("dealdesk/t-a/")
    assert store.CLIENT_ID == "dealdesk"
    assert {
        "cache",
        "memory",
        "feedback",
        "prompts",
        "fewshot",
        "golden",
        "eval",
        "logs",
        "index",
        "embeddings",
        "secrets",
        "model_config",
    } <= set(store.KINDS)


def _run(root: Path, parent_extra: bool) -> dict:
    out = subprocess.run([sys.executable, "-m", "dealdesk.selfrun", "--root", str(root)], capture_output=True, text=True, cwd=root, check=False,
                         env={"PYTHONPATH": str(root / "src"), "PATH": "", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")})  # fmt: skip
    assert out.returncode == 0, (parent_extra, out.stdout[-600:], out.stderr[-600:])
    return json.loads(out.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("canary", ["CANARY-OTHER-DEMO-9f3a"])
def test_outputs_are_byte_identical_with_another_demo_absent_or_present_and_nothing_outside_is_read(canary):
    tmp = Path(tempfile.mkdtemp())
    try:
        results = []
        for present in (False, True):
            base = tmp / ("with" if present else "without")
            demo = base / "demos" / "dealdesk"
            shutil.copytree(
                D,
                demo,
                ignore=shutil.ignore_patterns(
                    ".venv", "__pycache__", ".ruff_cache", ".pytest_cache", "mutation", "tests_oneshot", "uv.lock"
                ),
            )
            if present:
                other = base / "demos" / "other"
                other.mkdir(parents=True)
                (other / "data.json").write_text(json.dumps({"deal-7001": canary, "account_name": canary}), encoding="utf-8")
            results.append(_run(demo, present))
        assert results[0] == results[1] and results[0]["outside_reads"] == []
        assert canary not in json.dumps(results)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_module_imports_a_sibling_demo_or_a_vendor_sdk_outside_its_kind_module():
    for p in (D / "src").rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"^\s*(?:from|import)\s+(?:demos|refunds|intake|apexc)\b", text, re.MULTILINE), p.name
        assert not re.search(
            r"^\s*(?:from|import)\s+(?:boto3|anthropic|openai|azure|google\.cloud|psycopg|requests)\b", text, re.MULTILINE
        ), p.name


STUDIO_TERMS = (  # built from parts: internal working vocabulary must not ship in a demo repo (docs, source, config)
    r"\b" + "EG" + "M\b", r"\b" + "bib" + "le\b", r"\b" + "stu" + "dio\b", "HARD " + "RULE", r"\bthe " + "lead\b", r"\blead" + "'s\b",
    r"owner (?:" + "rule|step|decision|yes)", "discovery " + "calls?", "bench " + "item", "topic " + r"\d+", r"egm" + r"\\",
)  # fmt: skip


def test_shipped_docs_source_and_config_carry_no_internal_working_vocabulary():
    hits = []
    for p in files():
        if p.suffix not in (".md", ".py", ".json", ".yaml", ".toml", ".yml") or p.name in ("test_segregation.py", "uv.lock"):
            continue
        if p.parent.name == "tests" or p.name == "mutation_check.py":
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        hits += [
            (str(p.relative_to(D)), pat) for pat in STUDIO_TERMS if re.search(pat, text, re.IGNORECASE if pat.islower() else 0)
        ]
    assert hits == [], hits
