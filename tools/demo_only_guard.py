"""The demo-only folder guard (rule: .claude/rules/demo-only-folder-and-secrets.md).

Everything that exists only for demos lives in one folder (its name is in tools/demo_only_guard.toml). Product code
must not name that folder or hold a made-up record id; deleting the folder must leave a build whose tests still pass.

Usage:
  python tools/demo_only_guard.py                       scan: exit 1 if product code names the folder or a fake id
  python tools/demo_only_guard.py --require             also exit 2 if the folder is missing (CI of a demo repo)
  python tools/demo_only_guard.py --without-folder [-- PYTEST ARGS...]
                                                        copy the repository without the folder and run pytest there
Output per hit: path:line: rule (the matched text is never printed).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}


@dataclass(frozen=True)
class GuardConfig:
    folder: str
    product_roots: tuple[str, ...]
    loaders: tuple[str, ...]
    fake_id_patterns: tuple[re.Pattern[str], ...]
    suffixes: tuple[str, ...]


def load_config(path: Path) -> GuardConfig:
    """Read and check the settings. A bad setting stops the guard: it never runs with the check quietly off."""
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    folder = raw.get("folder")
    if not isinstance(folder, str) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", folder):
        raise SystemExit(f"demo_only_guard: 'folder' in {path.name} must be one plain folder name")
    roots = raw.get("product_roots")
    if not isinstance(roots, list) or not roots or not all(isinstance(r, str) and r for r in roots):
        raise SystemExit(
            f"demo_only_guard: 'product_roots' in {path.name} must be a non-empty list of folders"
        )
    loaders = raw.get("loaders", [])
    ids = raw.get("fake_id_patterns", [])
    suffixes = raw.get("suffixes")
    if not isinstance(loaders, list) or not isinstance(ids, list):
        raise SystemExit(
            f"demo_only_guard: 'loaders' and 'fake_id_patterns' in {path.name} must be lists"
        )
    if not isinstance(suffixes, list) or not suffixes:
        raise SystemExit(f"demo_only_guard: 'suffixes' in {path.name} must be a non-empty list")
    try:
        patterns = tuple(re.compile(p) for p in ids)
    except re.error as e:
        raise SystemExit(
            f"demo_only_guard: a fake_id_patterns entry is not a valid pattern: {e}"
        ) from e
    if any(p.search("") for p in patterns):
        raise SystemExit(
            "demo_only_guard: a fake_id_patterns entry matches the empty text (it would hit every file)"
        )
    return GuardConfig(folder, tuple(roots), tuple(loaders), patterns, tuple(suffixes))


def _files(root: Path, suffixes: tuple[str, ...]) -> Iterator[Path]:
    if not root.is_dir():
        return
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.is_file() and not p.is_symlink() and p.suffix in suffixes:
            yield p


def scan(repo: Path, cfg: GuardConfig) -> list[str]:
    """Every way product code can depend on the demo-only folder, as `path:line: rule` lines (empty = clean)."""
    hits: list[str] = []
    for root in cfg.product_roots:
        if not (repo / root).is_dir():
            hits.append(
                f"{root}: product-root-missing (a missing root would make the scan prove nothing)"
            )
    if cfg.folder in cfg.product_roots or any(
        (repo / r / cfg.folder).exists() for r in cfg.product_roots
    ):
        hits.append(
            f"{cfg.folder}: folder-inside-product-root (it would be packaged with the product)"
        )
    loaders = set(cfg.loaders)
    for rel in sorted(loaders):
        f = repo / rel
        if not f.is_file():
            hits.append(f"{rel}: stale-loader-entry (file does not exist)")
        elif cfg.folder not in f.read_text(encoding="utf-8", errors="replace"):
            hits.append(f"{rel}: stale-loader-entry (file does not name the folder)")
    for root in cfg.product_roots:
        for path in _files(repo / root, cfg.suffixes):
            rel = path.relative_to(repo).as_posix()
            if rel in loaders:
                continue
            for n, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if cfg.folder in line:
                    hits.append(f"{rel}:{n}: names-demo-only-folder")
                if any(p.search(line) for p in cfg.fake_id_patterns):
                    hits.append(f"{rel}:{n}: fake-record-id")
    return hits


def copy_without_folder(repo: Path, cfg: GuardConfig, dest: Path) -> None:
    """A copy of the repository (no version history, no caches, no virtual environment) without the demo-only folder."""

    def ignore(directory: str, names: list[str]) -> set[str]:
        skip = {n for n in names if n in SKIP_DIRS}
        if Path(directory).resolve() == repo.resolve():
            skip.add(cfg.folder)
        return skip

    shutil.copytree(repo, dest, ignore=ignore, symlinks=True, dirs_exist_ok=True)


def run_without_folder(repo: Path, cfg: GuardConfig, pytest_args: list[str]) -> int:
    """Run pytest in a copy that has no demo-only folder; its exit code is the answer."""
    with tempfile.TemporaryDirectory(prefix="demo-only-guard-") as tmp:
        dest = Path(tmp) / "copy"
        copy_without_folder(repo, cfg, dest)
        if (dest / cfg.folder).exists():
            raise SystemExit(
                "demo_only_guard: the copy still holds the folder; refusing to report a pass"
            )
        return subprocess.run(  # noqa: S603 (our own interpreter; arguments are a list, no shell)
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *pytest_args],
            cwd=dest,
            check=False,
        ).returncode


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--root", default=str(HERE.parent), help="the repository root")
    ap.add_argument("--config", default=str(HERE / "demo_only_guard.toml"))
    ap.add_argument(
        "--require", action="store_true", help="exit 2 if the demo-only folder is missing"
    )
    ap.add_argument(
        "--without-folder", action="store_true", help="run pytest in a copy without the folder"
    )
    ap.add_argument(
        "pytest_args", nargs="*", help="after --: arguments for pytest (with --without-folder)"
    )
    a = ap.parse_args(argv)
    repo = Path(a.root).resolve()
    cfg = load_config(Path(a.config))
    if a.without_folder:
        return run_without_folder(repo, cfg, a.pytest_args)
    if a.require and not (repo / cfg.folder).is_dir():
        print(
            f"demo_only_guard: the folder {cfg.folder} is missing but is required here: refusing to skip its tests"
        )
        return 2
    hits = scan(repo, cfg)
    if hits:
        print("\n".join(hits))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
