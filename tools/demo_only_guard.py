"""The demo-only folder guard.

The rule in plain words: everything that exists only for demos (made-up data, example prompts, recorded model replies,
test fixtures) lives in one folder, and the product never depends on it. The product is the code that is shipped to a
client; deleting the folder must leave a build whose tests still pass. The folder name is in tools/demo_only_guard.toml.

The scan works from one list, `git ls-files` (see `tracked_paths`), and fails (exit 1) for each of these, in every file
under the product folders listed in the settings file (a symlink pointing into the folder from anywhere else fails too):
  * a symlink of any kind (it could point into the folder, out of the repository, or nowhere);
  * the folder inside a product folder, at any depth, or any file or folder name that holds the folder name;
  * a line that names the folder (upper or lower case; "-", "_" and a space count as the same separator);
  * a made-up record id (the patterns are listed in the settings file);
  * a submodule (a git link, which is a folder, not a file) under a product folder: its files cannot be scanned;
  * a file that is not text and is not on the skip list of known binary endings (it cannot be read, so it is refused);
  * a loader file (the one place that may pick the folder by configuration) that names it more often than the cap;
  * the folder being present while the copy run is not wired (see the marker file in the settings).
Every other file type is read, including files without an ending. A file with a known binary ending is skipped only
when its first 8192 bytes hold a NUL byte or it is not valid text; a text file renamed to a picture ending is read like any other.
Output per hit: path:line: rule (the matched text is
never printed). Limits: only files git lists are read, so a file the repository ignores (.gitignore) is not checked, and
only the product folders in the settings are scanned, so the packaging files at the repository root (for example
pyproject.toml) are not; a folder the packaging config adds to the product from outside the listed folders is the
copy run's job. A name built from pieces at run time (for example "demo" + "_only") cannot be found by any text scan;
the copy run (`--without-folder`) is the check for that case, because the tests fail when the folder is really gone.

Usage:
  python tools/demo_only_guard.py                       scan: exit 1 on any hit
  python tools/demo_only_guard.py --require             also exit 2 if the folder is missing (CI of a demo repo)
  python tools/demo_only_guard.py --without-folder [-- PYTEST ARGS...]
                                                        copy the repository without the folder and run pytest there
  python tools/demo_only_guard.py --without-folder-if-present [-- PYTEST ARGS...]
                                                        the same, but exit 0 at once when the repository has no folder
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKIP_DIRS = {  # left out of the copy (copy run) only
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}
# Endings of files that are known not to be text; every other file is read.
DEFAULT_SKIP_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".whl",
    ".woff", ".woff2", ".pyc", ".so",
)  # fmt: skip
DEFAULT_MARKER = "tools/demo_only_guard.copy_run"
_SEP = r"[ _-]+"


@dataclass(frozen=True)
class GuardConfig:
    folder: str
    product_roots: tuple[str, ...]
    loaders: tuple[str, ...]
    fake_id_patterns: tuple[re.Pattern[str], ...]
    skip_suffixes: tuple[str, ...] = DEFAULT_SKIP_SUFFIXES
    exempt_files: tuple[
        str, ...
    ] = ()  # files that must hold the name (the guard's own settings); skipped whole
    allowed_phrases: tuple[
        str, ...
    ] = ()  # exact phrases that are not the folder (for example a constant's name)
    product_packages: tuple[str, ...] = ()  # packages the copy run must import from the copy
    loader_max_lines: int = 1
    copy_run_marker: str = DEFAULT_MARKER


def _list_of_text(raw: dict, key: str, path: Path, *, default: list | None = None) -> list[str]:
    value = raw.get(key, default)
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise SystemExit(
            f"demo_only_guard: '{key}' in {path.name} must be a list of non-empty text"
        )
    return value


def load_config(path: Path) -> GuardConfig:
    """Read and check the settings. A bad setting stops the guard: it never runs with the check quietly off."""
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    folder = raw.get("folder")
    if (
        not isinstance(folder, str)
        or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", folder)
        or not re.search(r"[A-Za-z0-9]", folder)
    ):
        raise SystemExit(f"demo_only_guard: 'folder' in {path.name} must be one plain folder name")
    roots = raw.get("product_roots")
    if not isinstance(roots, list) or not roots or not all(isinstance(r, str) and r for r in roots):
        raise SystemExit(
            f"demo_only_guard: 'product_roots' in {path.name} must be a non-empty list of folders"
        )
    loaders = raw.get("loaders", [])
    ids = raw.get("fake_id_patterns", [])
    if not isinstance(loaders, list) or not isinstance(ids, list):
        raise SystemExit(
            f"demo_only_guard: 'loaders' and 'fake_id_patterns' in {path.name} must be lists"
        )
    skip = _list_of_text(raw, "skip_suffixes", path, default=list(DEFAULT_SKIP_SUFFIXES))
    if not all(s.startswith(".") for s in skip):
        raise SystemExit(
            f"demo_only_guard: every 'skip_suffixes' entry in {path.name} starts with a dot"
        )
    cap = raw.get("loader_max_lines", 1)
    if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
        raise SystemExit(
            f"demo_only_guard: 'loader_max_lines' in {path.name} must be a whole number of 1 or more"
        )
    marker = raw.get("copy_run_marker", DEFAULT_MARKER)
    if not isinstance(marker, str) or not marker:
        raise SystemExit(f"demo_only_guard: 'copy_run_marker' in {path.name} must be a file path")
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
    return GuardConfig(
        folder,
        tuple(roots),
        tuple(loaders),
        patterns,
        tuple(s.lower() for s in skip),
        tuple(_list_of_text(raw, "exempt_files", path, default=[])),
        tuple(_list_of_text(raw, "allowed_phrases", path, default=[])),
        tuple(_list_of_text(raw, "product_packages", path, default=[])),
        cap,
        marker,
    )


def _name_pattern(folder: str) -> re.Pattern[str]:
    """The folder name in any case, with "_", "-" and a space read as one separator (Demo_Only, demo-only, demo only)."""
    parts = [p for p in re.split(_SEP, folder) if p]
    return re.compile(_SEP.join(re.escape(p) for p in parts), re.IGNORECASE)


def _phrase_patterns(phrases: tuple[str, ...]) -> dict[str, re.Pattern[str]]:
    # an allowed phrase counts only as a whole word group, in the exact case written: "DEMO_ONLY/x", "xDEMO_ONLY",
    # "DEMO_ONLY-x" and "x-DEMO_ONLY" are still a path or a name; the same word in lower case is not the phrase
    return {p: re.compile(r"(?<![\w/\\-])" + re.escape(p) + r"(?![\w/\\-])") for p in phrases}


def tracked_paths(repo: Path) -> list[str]:
    """The ONE list of paths the scan looks at: what `git ls-files` says the repository holds (tracked files, plus
    files not yet added and not ignored), as repository-relative paths with "/". Directories are not listed by git, and
    a symlink is one entry that is never followed. Not a git checkout, or git failing, stops the guard: it does not guess."""
    if not (repo / ".git").exists():
        raise SystemExit(
            f"demo_only_guard: {repo} is not a git checkout; the scan lists files with git and will not guess"
        )
    done = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
        ["git", "-C", str(repo), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        capture_output=True,
        check=False,
    )
    if done.returncode != 0:
        raise SystemExit(
            "demo_only_guard: git ls-files failed; refusing to scan with an unknown file list"
        )
    text = done.stdout.decode("utf-8", errors="surrogateescape")
    return sorted({p for p in text.split("\0") if p})


def _under(rel: str, roots: tuple[str, ...]) -> str | None:
    for root in roots:
        r = root.strip("/")
        if rel == r or rel.startswith(r + "/"):
            return r
    return None


def scan(repo: Path, cfg: GuardConfig) -> list[str]:
    """Every way product code can depend on the demo-only folder, as `path:line: rule` lines (empty = clean)."""
    hits: list[str] = []
    name = _name_pattern(cfg.folder)
    phrases = _phrase_patterns(cfg.allowed_phrases)
    used: set[str] = set()
    loaders = set(cfg.loaders)
    exempt = set(cfg.exempt_files) | {cfg.copy_run_marker}
    for root in cfg.product_roots:
        top = repo / root
        # a root that is itself a symlink is reported by the walk below, like any other symlink
        if not top.is_dir():
            hits.append(
                f"{root}: product-root-missing (a missing root would make the scan prove nothing)"
            )
        if any(name.fullmatch(part) for part in Path(root).parts):
            hits.append(
                f"{root}: folder-inside-product-root (it would be packaged with the product)"
            )
    for rel in sorted(loaders):
        f = repo / rel
        if not f.is_file():
            hits.append(f"{rel}: stale-loader-entry (file does not exist)")
        elif not name.search(f.read_text(encoding="utf-8", errors="replace")):
            hits.append(f"{rel}: stale-loader-entry (file does not name the folder)")
    for rel in sorted(set(cfg.exempt_files)):
        if not (repo / rel).is_file():
            hits.append(f"{rel}: stale-exempt-entry (file does not exist)")
    if (repo / cfg.folder).is_dir() and not (repo / cfg.copy_run_marker).is_file():
        hits.append(
            f"{cfg.copy_run_marker}: copy-run-not-wired (the folder exists, so CI must run the copy run "
            "and the marker file must say so)"
        )
    folder_target = (repo / cfg.folder).resolve()
    roots = tuple(r.strip("/") for r in cfg.product_roots)
    seen_dirs: set[str] = set()
    for rel in tracked_paths(repo):
        full = repo / rel
        try:
            is_link = full.is_symlink()
            # git lists a submodule (a git link) as a folder
            is_folder = not is_link and full.is_dir()
            if not is_link and not is_folder and not full.is_file():
                continue  # listed by git but gone from the disk
        except OSError:
            continue
        root = _under(rel, roots)
        if is_folder:
            if root is not None and rel not in exempt:
                hits.append(f"{rel}: submodule-in-product-root (its files cannot be scanned)")
            continue
        if root is None:
            # outside the product folders: only a link that points into the demo-only folder matters
            if is_link and full.resolve().is_relative_to(folder_target):
                hits.append(f"{rel}: symlink-to-demo-only-folder")
            continue
        if rel in exempt:
            continue
        if is_link:
            hits.append(f"{rel}: symlink-in-product-root")
            continue
        parts = rel.split("/")
        for depth in range(len(root.split("/")) + 1, len(parts)):
            d = "/".join(parts[:depth])
            if d in seen_dirs or d in loaders or not name.search(parts[depth - 1]):
                continue
            seen_dirs.add(d)
            same = (
                "folder-inside-product-root"
                if name.fullmatch(parts[depth - 1])
                else "path-names-demo-only-folder"
            )
            hits.append(f"{d}: {same}")
        if rel not in loaders and name.search(parts[-1]):
            hits.append(f"{rel}: path-names-demo-only-folder")
        if full.suffix.lower() in cfg.skip_suffixes and _looks_binary(full):
            continue
        hits += _scan_file(full, rel, cfg, name, phrases, used, rel in loaders)
    hits += [
        f"tools/demo_only_guard.toml: stale-allowed-phrase ({p})"
        for p in cfg.allowed_phrases
        if p not in used
    ]
    return list(dict.fromkeys(hits))


def _looks_binary(path: Path) -> bool:
    """True when a file with a known binary ending really is not text: a NUL byte in its first 8192 bytes, or bytes that
    are not valid UTF-8. A text file renamed to a binary ending is read by the scan instead of skipped."""
    try:
        data = path.read_bytes()
    except OSError:
        return True  # unreadable: the scan cannot read it either, and the ending says binary
    if b"\0" in data[:8192]:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def _scan_file(
    path: Path,
    rel: str,
    cfg: GuardConfig,
    name: re.Pattern[str],
    phrases: dict[str, re.Pattern[str]],
    used: set[str],
    is_loader: bool,
) -> list[str]:
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return [f"{rel}: unreadable-file (not text and not on the list of known binary endings)"]
    hits: list[str] = []
    loader_lines = 0
    for n, line in enumerate(text.splitlines(), 1):
        shown = line
        for phrase, rx in phrases.items():
            shown, count = rx.subn("\0", shown)
            if count:
                used.add(phrase)
        if name.search(shown):
            if not is_loader:
                hits.append(f"{rel}:{n}: names-demo-only-folder")
            else:
                loader_lines += 1
                if loader_lines > cfg.loader_max_lines:
                    hits.append(f"{rel}:{n}: loader-names-folder-too-often")
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


_IMPORT_CHECK = (
    "import importlib, pathlib, sys\n"
    "m = importlib.import_module(sys.argv[1])\n"
    "f = pathlib.Path(m.__file__).resolve()\n"
    "sys.exit(0 if f.is_relative_to(pathlib.Path(sys.argv[2]).resolve()) else 3)\n"
)


def run_without_folder(repo: Path, cfg: GuardConfig, pytest_args: list[str]) -> int:
    """Run pytest in a copy that has no demo-only folder; its exit code is the answer. The child sees ONLY the copy's
    `src` on its import path (an inherited path or an editable install of the original checkout cannot win), and each
    product package is first checked to be imported from the copy: a pass that tested the original proves nothing."""
    if not cfg.product_packages:
        raise SystemExit(
            "demo_only_guard: 'product_packages' is empty; without a package to check the copy run could test the original"
        )
    with tempfile.TemporaryDirectory(prefix="demo-only-guard-") as tmp:
        dest = Path(tmp) / "copy"
        copy_without_folder(repo, cfg, dest)
        if (dest / cfg.folder).exists():
            raise SystemExit(
                "demo_only_guard: the copy still holds the folder; refusing to report a pass"
            )
        env = {**os.environ, "PYTHONPATH": str(dest / "src")}
        for package in cfg.product_packages:
            checked = subprocess.run(  # noqa: S603 (our own interpreter; arguments are a list, no shell)
                [sys.executable, "-c", _IMPORT_CHECK, package, str(dest)],
                cwd=dest,
                env=env,
                check=False,
            )
            if checked.returncode != 0:
                print(
                    f"demo_only_guard: package {package} is not imported from the copy: no pass reported"
                )
                return checked.returncode or 3
        return subprocess.run(  # noqa: S603 (our own interpreter; arguments are a list, no shell)
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *pytest_args],
            cwd=dest,
            env=env,
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
        "--without-folder-if-present",
        action="store_true",
        help="like --without-folder, but exit 0 at once when there is no folder",
    )
    ap.add_argument(
        "pytest_args", nargs="*", help="after --: arguments for pytest (with --without-folder)"
    )
    a = ap.parse_args(argv)
    repo = Path(a.root).resolve()
    cfg = load_config(Path(a.config))
    if a.without_folder_if_present and not (repo / cfg.folder).is_dir():
        return 0
    if a.without_folder or a.without_folder_if_present:
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
