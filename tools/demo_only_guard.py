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
  * a submodule (a git link) under a product folder, even when its folder is missing: its files cannot be scanned;
  * a file ending in .pyc, .so, .zip, .whl, .gz, .tgz, .tar, .bz2 or .xz under a product folder, and a file of ANY ending whose
    first bytes are the mark of a zip, an ELF program, a gzip, bzip2 or xz file, a tar archive or compiled Python (it cannot
    be read, or it packs what it holds; renaming it to .png does not help);
  * a file or folder entry git lists that cannot be read (a permission error, a pipe, a socket): it is a hit, never a skip;
  * a file larger than `max_file_bytes` in the settings (it is not read; a hit says so);
  * a file that is not text and is not on the skip list of known binary endings (it cannot be read, so it is refused);
  * a loader file (the one place that may pick the folder by configuration) that names it more often than the cap;
  * the folder being present while the copy run is not wired (see the marker file in the settings).
Every other file type is read, including files without an ending. A file with another known binary
ending is not read as text when its first 8192 bytes hold a NUL byte or it is not valid text; its bytes are searched for the
name instead (as UTF-8, UTF-16 and UTF-32 text, little- and big-endian, no byte-order mark). A text file renamed to a picture ending is read like
any other. Every line and every path part is normalised (NFKC) before it is compared, so a full-width spelling of the name,
which Python reads as the same identifier, is a hit. A file that holds NUL bytes is also searched for the name written as
UTF-16 or UTF-32 without a byte-order mark. Output per hit: path:line: rule (the matched text is
never printed; a path is printed with control characters escaped as \\xNN, and a path that starts with "::" starts with
\\x3a: instead, so a hit can never be read as a CI workflow command or hide a line). Limits: the byte search of a binary file looks for the name as written (it is not normalised with NFKC, because a binary has
no text to normalise), a name the compiler assembles from pieces at build time is not found, and the made-up record id patterns are
not run on binary files (only on text). Only files git lists are read, so a file the repository ignores (.gitignore) is not checked, and
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
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unicodedata
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
# Endings that are never accepted in a product folder: an importable or loadable file that cannot be read (a sourceless
# .pyc, a compiled .so) or a packed archive (.zip, .whl, .gz, .tgz, .tar, .bz2, .xz) that hides what is inside.
REFUSED_SUFFIXES = (".pyc", ".so", ".zip", ".whl", ".gz", ".tgz", ".tar", ".bz2", ".xz")
# The same files by their first bytes, whatever the ending (a zip renamed to .png is still a zip); see `_magic_kind`.
MAX_FILE_BYTES = 8 * 1024 * 1024  # the default cap on one file (the settings file may change it)
# Names the copy run never copies when git does not track them (secrets that sit in a working folder), matched on the name.
DEFAULT_COPY_EXCLUDE = (
    ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", ".netrc", ".npmrc", ".pypirc",
    "id_rsa*", "id_ed25519*", "id_ecdsa*", "*.kdbx", "credentials*",
)  # fmt: skip
# The only environment names the copy run's child process receives (no token, no key, no connection string).
DEFAULT_CHILD_ENV = (
    "PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "TERM",
    "VIRTUAL_ENV", "HADAVIN_REQUIRE_NODE",
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
    max_file_bytes: int = MAX_FILE_BYTES
    copy_exclude: tuple[str, ...] = DEFAULT_COPY_EXCLUDE
    child_env_allowed: tuple[str, ...] = DEFAULT_CHILD_ENV


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
    max_bytes = raw.get("max_file_bytes", MAX_FILE_BYTES)
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
        raise SystemExit(
            f"demo_only_guard: 'max_file_bytes' in {path.name} must be a whole number of 1 or more"
        )
    copy_exclude = _list_of_text(raw, "copy_exclude", path, default=list(DEFAULT_COPY_EXCLUDE))
    child_env = _list_of_text(raw, "child_env_allowed", path, default=list(DEFAULT_CHILD_ENV))
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
        max_bytes,
        tuple(copy_exclude),
        tuple(child_env),
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


def _gitlinks(repo: Path) -> set[str]:
    """The paths git holds as git links (a submodule: mode 160000), whether or not their folder is on the disk."""
    done = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
        ["git", "-C", str(repo), "ls-files", "-s", "-z", "--cached"],  # noqa: S607
        capture_output=True,
        check=False,
    )
    if done.returncode != 0:
        raise SystemExit(
            "demo_only_guard: git ls-files -s failed; refusing to scan with an unknown file list"
        )
    out = set()
    for entry in done.stdout.decode("utf-8", errors="surrogateescape").split("\0"):
        info, _, path = entry.partition("\t")
        if path and info.startswith("160000 "):
            out.add(path)
    return out


def _magic_kind(data: bytes) -> str:
    """What a file's first bytes say it is, when it is a compiled or packed file ("" when they say nothing): a zip (also an
    empty or spanned one), an ELF program or library, a gzip, bzip2 or xz file, a tar archive, or compiled Python (a 2-byte
    version number, little-endian, 3000 to 3999, then "\\r\\n"). The ending of the file name is not consulted."""
    head = data[:512]
    if head[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"):
        return "zip"
    if head[:4] == b"\x7fELF":
        return "ELF"
    if head[:2] == b"\x1f\x8b":
        return "gzip"
    if head[:3] == b"BZh" and head[4:10] == b"1AY&SY":
        return "bzip2"
    if head[:6] == b"\xfd7zXZ\x00":
        return "xz"
    if len(head) > 262 and head[257:262] == b"ustar":
        return "tar"
    if head[2:4] == b"\r\n" and 3000 <= int.from_bytes(head[:2], "little") < 4000:
        return "compiled Python"
    return ""


def printable(line: str) -> str:
    """A hit line made safe to print: a control, format, separator or unpaired-surrogate character in a path is shown as
    \\xNN, \\uNNNN or \\UNNNNNNNN, and a line that starts with "::" starts with \\x3a: instead (a CI runner reads a line that
    starts with "::" as a workflow command)."""
    out = []
    for ch in line:
        if unicodedata.category(ch) in ("Cc", "Cf", "Cs", "Zl", "Zp", "Co", "Cn"):
            n = ord(ch)
            out.append(
                f"\\x{n:02x}" if n < 0x100 else f"\\u{n:04x}" if n < 0x10000 else f"\\U{n:08x}"
            )
        else:
            out.append(ch)
    text = "".join(out)
    return "\\x3a:" + text[2:] if text.startswith("::") else text


def _cached_paths(repo: Path) -> set[str]:
    """The paths git tracks (in its index). No git checkout, or git failing, gives the empty set: then nothing counts as
    tracked and every secret-shaped file is left out of a copy (the safe direction)."""
    if not (repo / ".git").exists():
        return set()
    done = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
        ["git", "-C", str(repo), "ls-files", "-z", "--cached"],  # noqa: S607
        capture_output=True,
        check=False,
    )
    if done.returncode != 0:
        return set()
    return {p for p in done.stdout.decode("utf-8", errors="surrogateescape").split("\0") if p}


def _nfkc(text: str) -> str:
    """The text as Python reads an identifier: NFKC (full-width letters become plain ones)."""
    return unicodedata.normalize("NFKC", text)


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
        if any(name.fullmatch(_nfkc(part)) for part in Path(root).parts):
            hits.append(
                f"{root}: folder-inside-product-root (it would be packaged with the product)"
            )
    for rel in sorted(loaders):
        f = repo / rel
        if not f.is_file():
            hits.append(f"{rel}: stale-loader-entry (file does not exist)")
        elif not name.search(_nfkc(f.read_text(encoding="utf-8", errors="replace"))):
            hits.append(f"{rel}: stale-loader-entry (file does not name the folder)")
    listed = tracked_paths(repo)  # first: it stops the run when this is not a git checkout
    gitlinks = _gitlinks(repo)
    byte_names = _byte_patterns(cfg.folder)  # compiled once for the whole scan
    for rel in sorted(set(cfg.exempt_files)):
        if not (repo / rel).is_file() and rel not in gitlinks:
            hits.append(f"{rel}: stale-exempt-entry (neither a file nor a git link that exists)")
    if (repo / cfg.folder).is_dir() and not (repo / cfg.copy_run_marker).is_file():
        hits.append(
            f"{cfg.copy_run_marker}: copy-run-not-wired (the folder exists, so CI must run the copy run "
            "and the marker file must say so)"
        )
    folder_target = (repo / cfg.folder).resolve()
    roots = tuple(r.strip("/") for r in cfg.product_roots)
    seen_dirs: set[str] = set()
    for rel in listed:
        full = repo / rel
        if (
            rel in gitlinks
        ):  # a submodule counts whether or not its folder is on the disk (fail closed)
            if _under(rel, roots) is not None and rel not in exempt:
                hits.append(f"{rel}: submodule-in-product-root (its files cannot be scanned)")
            continue
        root = _under(rel, roots)
        try:
            is_link = full.is_symlink()
            # git lists a submodule (a git link) as a folder
            is_folder = not is_link and full.is_dir()
            is_file = not is_link and not is_folder and full.is_file()
            if not is_link and not is_folder and not is_file:
                if not os.path.lexists(full):
                    continue  # listed by git but gone from the disk
                raise OSError("not a regular file, folder or link (a pipe or socket)")
        except OSError:
            if root is not None and rel not in exempt:
                hits.append(f"{rel}: unreadable-file (the entry cannot be inspected)")
            continue
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
            part = _nfkc(parts[depth - 1])
            if d in seen_dirs or not name.search(part):
                continue
            seen_dirs.add(d)
            same = (
                "folder-inside-product-root"
                if name.fullmatch(part)
                else "path-names-demo-only-folder"
            )
            hits.append(f"{d}: {same}")
        if rel not in loaders and name.search(_nfkc(parts[-1])):
            hits.append(f"{rel}: path-names-demo-only-folder")
        hits += _scan_file(full, rel, cfg, name, phrases, used, rel in loaders, byte_names)
    hits += [
        f"tools/demo_only_guard.toml: stale-allowed-phrase ({p})"
        for p in cfg.allowed_phrases
        if p not in used
    ]
    return list(dict.fromkeys(hits))


def _looks_binary(data: bytes) -> bool:
    """True when the bytes of a file with a known binary ending really are not text: a NUL byte in the first 8192 bytes,
    or bytes that are not valid UTF-8. A text file renamed to a binary ending is read by the scan instead."""
    if b"\0" in data[:8192]:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


BYTE_ENCODINGS = ("utf-8", "utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be")


def _byte_patterns(folder: str) -> dict[str, re.Pattern[bytes]]:
    """The folder name as bytes in each spelling a text could hold it: UTF-8, UTF-16 and UTF-32, little- and big-endian
    (no byte-order mark), in any ASCII case, with "_", "-" and a space as one separator."""
    parts = [p for p in re.split(_SEP, folder) if p]
    out = {}
    for enc in BYTE_ENCODINGS:
        sep = b"(?:" + b"|".join(re.escape(c.encode(enc)) for c in " _-") + b")+"
        out[enc] = re.compile(sep.join(re.escape(p.encode(enc)) for p in parts), re.IGNORECASE)
    return out


def _scan_file(
    path: Path,
    rel: str,
    cfg: GuardConfig,
    name: re.Pattern[str],
    phrases: dict[str, re.Pattern[str]],
    used: set[str],
    is_loader: bool,
    byte_names: dict[str, re.Pattern[bytes]],
) -> list[str]:
    """The hits of one file in a product folder. The file is read once, and never when it is over `max_file_bytes`."""
    suffix = path.suffix.lower()
    if suffix in REFUSED_SUFFIXES:
        return [
            f"{rel}: binary-in-product-root (a {suffix} file cannot be read or hides what it packs)"
        ]
    try:
        size = path.stat().st_size
        if size > cfg.max_file_bytes:
            return [f"{rel}: file-too-large (over {cfg.max_file_bytes} bytes; it is not read)"]
        with path.open("rb") as handle:
            data = handle.read(
                cfg.max_file_bytes + 1
            )  # a file that grew since the size check is still bounded
    except OSError:
        return [f"{rel}: unreadable-file (it cannot be read)"]
    if len(data) > cfg.max_file_bytes:
        return [f"{rel}: file-too-large (over {cfg.max_file_bytes} bytes; it is not read)"]
    if kind := _magic_kind(data):
        return [f"{rel}: binary-in-product-root (the file is {kind}, whatever its ending says)"]
    if suffix in cfg.skip_suffixes and _looks_binary(data):
        hit = any(rx.search(data) for rx in byte_names.values())
        return [f"{rel}: names-demo-only-folder (inside a binary file)"] if hit else []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return [f"{rel}: unreadable-file (not text and not on the list of known binary endings)"]
    hits: list[str] = []
    loader_lines = 0
    for n, raw in enumerate(text.splitlines(), 1):
        line = _nfkc(raw)
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
    if b"\0" in data and any(byte_names[e].search(data) for e in BYTE_ENCODINGS[1:]):
        hits.append(f"{rel}: names-demo-only-folder (as UTF-16 or UTF-32 text)")
    return hits


def copy_without_folder(repo: Path, cfg: GuardConfig, dest: Path) -> None:
    """A copy of the repository (no version history, no caches, no virtual environment) without the demo-only folder. A
    file whose name looks like a secret (`copy_exclude` in the settings: `.env`, keys, certificates) is not copied unless
    git tracks it, so an untracked key file that sits in the working folder never reaches the copy."""
    tracked = _cached_paths(repo)

    def ignore(directory: str, names: list[str]) -> set[str]:
        skip = {n for n in names if n in SKIP_DIRS}
        here = Path(directory).resolve()
        if here == repo.resolve():
            skip.add(cfg.folder)
        base = here.relative_to(repo.resolve()).as_posix()
        for n in names:
            rel = n if base == "." else f"{base}/{n}"
            if rel not in tracked and any(
                fnmatch.fnmatchcase(n.lower(), pat.lower()) for pat in cfg.copy_exclude
            ):
                skip.add(n)
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
        # only the names the settings allow (no token, key or connection string of the caller reaches the child)
        env = {k: v for k, v in os.environ.items() if k in cfg.child_env_allowed}
        env["PYTHONPATH"] = str(dest / "src")
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
        print("\n".join(printable(h) for h in hits))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
