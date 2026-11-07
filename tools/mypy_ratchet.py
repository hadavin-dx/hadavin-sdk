"""The mypy rollout list may only shrink, and no listed module may get worse.

The modules in the `ignore_errors` override of pyproject.toml still have mypy findings that the normal `mypy` run does
not report. This script runs mypy on the same configuration WITHOUT those overrides and compares per file with
tools/mypy_baseline.json (file -> number of findings). It fails when
  - a listed module does not exist, or is clean (delete it from the list and from the baseline);
  - a listed module has MORE findings than its baseline (growth), or fewer (lower the baseline, so a gain stays a gain);
  - a module that is not listed has a finding, or a file in the baseline is not listed.

Usage: python tools/mypy_ratchet.py            (from the repository root, with the lint group installed)
       python tools/mypy_ratchet.py --write    (rewrite the baseline from the current counts; review the diff)
"""

from __future__ import annotations

import collections
import json
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "tools" / "mypy_baseline.json"
OVERRIDE_BLOCK = re.compile(
    r"^\[\[tool\.mypy\.overrides\]\]\n.*?(?=^\[|\Z)", re.MULTILINE | re.DOTALL
)


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
    """The [tool.mypy] table of pyproject.toml with every [[tool.mypy.overrides]] block removed."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    start = text.index("[tool.mypy]")
    nxt = re.search(r"^\[(?!\[tool\.mypy\.overrides)", text[start + 1 :], re.MULTILINE)
    table = text[start : start + 1 + nxt.start()] if nxt else text[start:]
    return OVERRIDE_BLOCK.sub("", table)


def counts() -> dict[str, int]:
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
    found = re.findall(r"^(\S+?\.py):\d+: error:", run.stdout, re.MULTILINE)
    return dict(collections.Counter(Path(f).as_posix() for f in found))


def main(argv: list[str]) -> int:
    now = counts()
    if "--write" in argv:
        BASELINE.write_text(
            json.dumps(dict(sorted(now.items())), indent=2) + "\n", encoding="utf-8"
        )
        print(f"baseline written: {len(now)} files, {sum(now.values())} findings")
        return 0
    base: dict[str, int] = json.loads(BASELINE.read_text(encoding="utf-8"))
    mods = listed_modules()
    problems = [
        f"{m}: no such module (remove or rename the line)"
        for m in mods
        if not module_file(m).exists()
    ]
    listed = {module_file(m).relative_to(ROOT).as_posix() for m in mods if module_file(m).exists()}
    problems.extend(
        f"{f}: listed but clean (delete its line and its baseline entry)"
        for f in sorted(listed - set(now))
    )
    problems.extend(
        f"{f}: has {now[f]} finding(s) but is not listed" for f in sorted(set(now) - listed)
    )
    for f in sorted(listed & set(now)):
        if f not in base:
            problems.append(f"{f}: listed but missing from the baseline")
        elif now[f] > base[f]:
            problems.append(f"{f}: {now[f]} findings, baseline {base[f]} (it got worse)")
        elif now[f] < base[f]:
            problems.append(
                f"{f}: {now[f]} findings, baseline {base[f]} (lower the baseline: --write)"
            )
    problems.extend(
        f"{f}: in the baseline but not listed (delete the entry)"
        for f in sorted(set(base) - listed)
    )
    print(f"{len(listed)} listed, {sum(now.values())} findings, {len(problems)} problems")
    for line in problems:
        print("  " + line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
