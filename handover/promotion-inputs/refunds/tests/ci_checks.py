"""CI helpers that have to name the demo folder, so that no workflow or product file does.

python tests/ci_checks.py gen   # the generated demo data regenerates byte for byte
python tests/ci_checks.py cut   # the CUT TEST: copy the repo, delete the demo folder, run lint + tests + a wheel build there, and check the wheel holds none of it
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = "demo" + "_only"


def run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=cwd, check=False)
    if r.returncode:
        sys.exit(f"FAILED ({r.returncode}): {' '.join(cmd)}")


def gen() -> None:
    run([sys.executable, str(ROOT / DEMO / "data" / "gen.py"), "--check"], ROOT)


def cut() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "repo"
        shutil.copytree(
            ROOT,
            dst,
            ignore=shutil.ignore_patterns(".venv*", "__pycache__", ".git", ".ruff_cache", ".pytest_cache", "dist", "out"),
        )
        shutil.rmtree(dst / DEMO)
        uv = ["uv", "run", "--locked", "--all-extras", "--group", "test"]
        run([*uv, "ruff", "format", "--check", "."], dst)
        run([*uv, "ruff", "check", "."], dst)
        run([*uv, "pytest", "-q"], dst)
        run([*uv, "bandit", "-q", "-r", "src"], dst)
        run(["uv", "build", "--wheel", "--out-dir", str(dst / "dist")], dst)
        wheels = list((dst / "dist").rglob("*.whl"))
        assert len(wheels) == 1, wheels
        names = zipfile.ZipFile(wheels[0]).namelist()
        bad = [n for n in names if DEMO in n or n.startswith(("tests/", "data/", "eval/"))]
        assert not bad, bad
        assert any(n.startswith("refunds/") for n in names), names[:5]
    print("cut test: ok")


if __name__ == "__main__":
    {"gen": gen, "cut": cut}[sys.argv[1]]()
