"""The mypy rollout list may only shrink. Fails when a module in the `ignore_errors` override of pyproject.toml is
clean (remove it from the list) or does not exist (remove or rename it), or when a module outside the list has a
finding. It runs mypy twice in effect: once on the real configuration is the normal gate (`mypy`); this script runs it
on the same configuration WITHOUT the override, so the listed modules report their findings.

Usage: python tools/mypy_ratchet.py   (from the repository root, with the lint group installed)
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def listed_modules() -> list[str]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    mods: list[str] = []
    for ov in data["tool"]["mypy"].get("overrides", []):
        if ov.get("ignore_errors"):
            mods += ov["module"] if isinstance(ov["module"], list) else [ov["module"]]
    return mods


def module_file(mod: str) -> Path:
    base = ROOT / "src" / Path(*mod.split("."))
    return base.with_suffix(".py") if base.with_suffix(".py").exists() else base / "__init__.py"


def config_without_overrides() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    start = text.index("[tool.mypy]")
    end = text.index("[[tool.mypy.overrides]]", start)
    return text[start:end]


def main() -> int:
    mods = listed_modules()
    problems = [
        f"{m}: no such module (remove or rename the line)"
        for m in mods
        if not module_file(m).exists()
    ]
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / "mypy-no-override.toml"
        cfg.write_text(config_without_overrides(), encoding="utf-8")
        run = subprocess.run(
            [sys.executable, "-m", "mypy", "--config-file", str(cfg), "--no-error-summary"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    stdout = run.stdout
    failing = {
        Path(m.group(1)).as_posix()
        for m in re.finditer(r"^(\S+?\.py):\d+: error:", stdout, re.MULTILINE)
    }
    listed = {module_file(m).relative_to(ROOT).as_posix() for m in mods if module_file(m).exists()}
    problems += [f"{p}: listed but clean (delete its line)" for p in sorted(listed - failing)]
    problems += [f"{p}: has findings but is not listed" for p in sorted(failing - listed)]
    print(f"{len(listed)} listed, {len(failing)} with findings, {len(problems)} problems")
    for line in problems:
        print("  " + line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
