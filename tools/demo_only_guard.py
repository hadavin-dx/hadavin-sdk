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
    first bytes are the mark of one of `MAGIC_KINDS` (zip, ELF, gzip, bzip2, xz, tar, compiled Python, Mach-O, PE: it cannot
    be read, or it packs what it holds); the first 512 bytes decide (the PE header offset may reach further), data appended
    after a valid mark is not looked at, and an exempt file gets the same check;
  * a file with a picture, font or PDF ending (`ENDING_MARKS`: .png .jpg .jpeg .gif .ico .pdf .woff .woff2 .webp .ttf .otf)
    whose first bytes are not the mark of that kind: the content decides what a file is, not its name (zstd, 7z, rar, lz4 and
    the like named logo.png are hits). `.svg` is text (XML) and is not listed: it is read as text like any other file;
  * a file or folder entry git lists that cannot be inspected or read (a permission error, a pipe, a socket, a parent folder
    that cannot be entered, a loop of links), including a product root, a loader file and the demo-only folder itself: it is a
    hit (or counts as present), never a skip; only "no such file" means the entry is gone (see `_stat_kind`);
  * a file larger than `max_file_bytes` in the settings (it is not read; a hit says so), including a file on the exempt list;
  * a file that is not text and is not on the skip list of known binary endings (it cannot be read, so it is refused);
  * a loader file (the one place that may pick the folder by configuration) that names it more often than the cap;
  * the folder being present while the copy run is not wired (see the marker file in the settings): the marker must be a
    regular file of size 0, not a link or a folder, and an exempt file must not be a link.
Every other file type is read, including files without an ending. A file with a known picture, font or PDF ending that has the
right first bytes is not read as text when its first 8192 bytes hold a NUL byte or it is not valid text; its bytes are searched for the
name instead (as UTF-8, UTF-16 and UTF-32 text, little- and big-endian, no byte-order mark). Every line and every path part is
normalised (NFKC) before it is compared, so a full-width spelling of the name,
which Python reads as the same identifier, is a hit. A file that holds NUL bytes is also searched for the name written as
UTF-16 or UTF-32 without a byte-order mark. Output per hit: path:line: rule (the matched text is
never printed; a path is printed with control characters escaped as \\xNN, \\uNNNN or \\UNNNNNNNN, and a path that starts with "::" starts with
\\x3a: instead, so a hit can never be read as a CI workflow command or hide a line). Limits: the byte search of a binary file looks for the name as written (it is not normalised with NFKC, because a binary has
no text to normalise), a name the compiler assembles from pieces at build time is not found, and the made-up record id patterns are
not run on binary files (only on text). Paths are matched as git lists them; on a case-insensitive file system a
differently-cased spelling of a product folder is not matched (the scan runs on git's own path list, on Linux in CI). A file
that names the folder only inside a quoted string `"DEMO_ONLY"` is still a hit: over-detection is the safe side, and a product
file that must name the folder for a real reason goes on the exempt list with its reason. Only files git lists are read, so a file the repository ignores (.gitignore or .git/info/exclude of the repository: they say what the project does not track) is not checked; the person's own ignore file (core.excludesFile, the XDG one) is not applied, so it cannot hide a file; and
only the product folders in the settings are scanned, so the packaging files at the repository root (for example
pyproject.toml) are not; a folder the packaging config adds to the product from outside the listed folders is the
copy run's job. A name built from pieces at run time (for example "demo" + "_only") cannot be found by any text scan;
the copy run (`--without-folder`) is the check for that case, because the tests fail when the folder is really gone.

Usage:
  python tools/demo_only_guard.py                       scan: exit 1 on any hit
  python tools/demo_only_guard.py --require             also exit 2 if the folder is missing (CI of a demo repo)
  python tools/demo_only_guard.py --without-folder [-- PYTEST ARGS...]
                                                        copy the files git tracks, without the folder, and run pytest there
  python tools/demo_only_guard.py --without-folder-if-present [-- PYTEST ARGS...]
                                                        the same, but exit 0 at once when the repository has no folder
`--require`, `--without-folder` and `--without-folder-if-present` exclude each other (exit 2), and pytest arguments are
accepted only with a copy-run flag (exit 2). The scan runs first inside the copy run and its hits stop it. The copy holds exactly the files `git ls-files --cached` names (what git
tracks), minus the folder and the marker; a tracked symlink is copied only when relative, inside the copy and away from the folder, any other stops the run; a file that is only new (not added) or ignored is not copied. Its child process
sees only the environment variables listed in `child_env_allowed` (HOME and PATH among them): that limits the environment,
not the files the child can reach. The variables of the database and Vault tests are left out on purpose, so those tests
skip in the copy.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The first bytes a file with each of the endings that may hold a non-text file must start with. The content decides: a
# file with one of these endings that does not start with the mark of its kind is a hit.
ENDING_MARKS: dict[str, tuple[bytes, ...]] = {
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".ico": (b"\x00\x00\x01\x00",),
    ".pdf": (b"%PDF-",),
    ".woff": (b"wOFF",),
    ".woff2": (b"wOF2",),
    ".webp": (b"RIFF",),  # and "WEBP" at byte 8 (`_EXTRA_MARKS`)
    ".ttf": (b"\x00\x01\x00\x00", b"true"),
    ".otf": (b"OTTO",),
}
# What else must hold, beyond the first bytes, for an ending whose mark is not a plain start: a webp file is a RIFF
# container, and "WEBP" stands at bytes 8 to 11 (any other RIFF file, such as a wav, is not a webp).
_EXTRA_MARKS: dict[str, Callable[[bytes], bool]] = {".webp": lambda d: d[8:12] == b"WEBP"}


def has_mark(suffix: str, data: bytes) -> bool:
    """True when `data` starts like a file of the kind the ending `suffix` names (see `ENDING_MARKS`)."""
    return data.startswith(ENDING_MARKS[suffix]) and _EXTRA_MARKS.get(suffix, lambda _d: True)(data)


# Endings of files that are known not to be text; every other file is read. Every one needs a row in ENDING_MARKS.
DEFAULT_SKIP_SUFFIXES = tuple(ENDING_MARKS)
# Endings that are never accepted in a product folder: an importable or loadable file that cannot be read (a sourceless
# .pyc, a compiled .so) or a packed archive (.zip, .whl, .gz, .tgz, .tar, .bz2, .xz) that hides what is inside.
REFUSED_SUFFIXES = (".pyc", ".so", ".zip", ".whl", ".gz", ".tgz", ".tar", ".bz2", ".xz")
# The same files by their first bytes, whatever the ending (a zip renamed to .png is still a zip); see `_magic_kind`.
MAX_FILE_BYTES = 8 * 1024 * 1024  # the default cap on one file (the settings file may change it)
# The only environment variable names the copy run's child process receives (no token, no key, no connection string).
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
    ] = ()  # files that must hold the name (the guard's own settings); their content is not searched
    allowed_phrases: tuple[
        str, ...
    ] = ()  # exact phrases that are not the folder (for example a constant's name)
    product_packages: tuple[str, ...] = ()  # packages the copy run must import from the copy
    loader_max_lines: int = 1
    copy_run_marker: str = DEFAULT_MARKER
    max_file_bytes: int = MAX_FILE_BYTES
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
    if unknown := [s for s in skip if s.lower() not in ENDING_MARKS]:
        raise SystemExit(
            f"demo_only_guard: 'skip_suffixes' in {path.name} names an ending with no known first bytes ({unknown[0]}); "
            f"allowed: {', '.join(ENDING_MARKS)}"
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
    if "copy_exclude" in raw:
        raise SystemExit(
            f"demo_only_guard: 'copy_exclude' in {path.name} is gone: the copy holds exactly the files git tracks"
        )
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


# `-c core.excludesFile=<nothing>` overrides the global, XDG and system setting of git's own ignore file, so a file the person
# running the guard (or a CI image) ignores for themselves is still listed. What stays honoured, on purpose: `.gitignore` files
# and `.git/info/exclude` of the repository itself (they say what the project does not track; only tracked files are copied).
GIT_NO_USER_EXCLUDES = ("-c", f"core.excludesFile={os.devnull}")


def _git_env() -> dict[str, str]:
    """The environment of every git call: the caller's, without any `GIT_*` variable (GIT_DIR, GIT_INDEX_FILE, GIT_WORK_TREE
    and the like would make `git -C <repo>` list another tree than the one asked for)."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def tracked_paths(repo: Path, *, include_new: bool = True) -> list[str]:
    """The ONE list of paths the scan looks at: what `git ls-files` says the repository holds (tracked files, plus,
    unless `include_new` is False, files not yet added and not ignored), as repository-relative paths with "/".
    Directories are not listed by git, and a symlink is one entry that is never followed. Not a git checkout, or git
    failing, stops the guard: it does not guess. The copy run asks for the tracked files only (`include_new=False`)."""
    if not (repo / ".git").exists():
        raise SystemExit(
            f"demo_only_guard: {repo} is not a git checkout; the scan lists files with git and will not guess"
        )
    flags = ["--cached", "--others", "--exclude-standard"] if include_new else ["--cached"]
    done = subprocess.run(  # noqa: S603 (fixed argument list, no shell)
        ["git", "-C", str(repo), *GIT_NO_USER_EXCLUDES, "ls-files", "-z", *flags],  # noqa: S607
        capture_output=True,
        check=False,
        env=_git_env(),
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
        env=_git_env(),
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


def _is_pe(data: bytes) -> bool:
    """A Windows program or library: "MZ", then at byte 0x3C a 4-byte little-endian offset, and "PE\\0\\0" at that offset. A
    file too short to hold the offset or the signature there is not read as one (the header cannot say). The offset may lie
    beyond the first 512 bytes, so the whole of `data` is used for it."""
    if data[:2] != b"MZ" or len(data) < 0x40:
        return False
    at = int.from_bytes(data[0x3C:0x40], "little")
    return at + 4 <= len(data) and data[at : at + 4] == b"PE\x00\x00"


# (kind, does the head say so): ONE table; `MAGIC_KINDS` and `_magic_kind` both come from it, and the CHANGELOG sentence
# about first bytes is checked against it by a test. A compiled Python file has a 2-byte version number (little-endian,
# 3000 to 3999) and "\r\n"; Mach-O is the four 32- and 64-bit magic values in both byte orders.
_MAGIC_CHECKS: tuple[tuple[str, Callable[[bytes], bool]], ...] = (
    ("zip", lambda d: d[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")),
    ("ELF", lambda d: d[:4] == b"\x7fELF"),
    ("gzip", lambda d: d[:2] == b"\x1f\x8b"),
    ("bzip2", lambda d: d[:3] == b"BZh" and d[4:10] == b"1AY&SY"),
    ("xz", lambda d: d[:6] == b"\xfd7zXZ\x00"),
    ("tar", lambda d: len(d) > 262 and d[257:262] == b"ustar"),
    (
        "compiled Python",
        lambda d: d[2:4] == b"\r\n" and 3000 <= int.from_bytes(d[:2], "little") < 4000,
    ),
    (
        "Mach-O",
        lambda d: (
            d[:4]
            in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe")
        ),
    ),
    ("PE", _is_pe),
)
MAGIC_KINDS: tuple[str, ...] = tuple(kind for kind, _ in _MAGIC_CHECKS)


def _magic_kind(data: bytes) -> str:
    """What a file's first bytes say it is, when it is a compiled or packed file ("" when they say nothing): one of
    `MAGIC_KINDS`. The first 512 bytes decide (a PE file's header offset may reach further); anything appended after a
    valid mark is not looked at here. The ending of the file name is not consulted."""
    head = data[:512]
    for kind, says in _MAGIC_CHECKS:
        if says(data if kind == "PE" else head):
            return kind
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


def _nfkc(text: str) -> str:
    """The text as Python reads an identifier: NFKC (full-width letters become plain ones)."""
    return unicodedata.normalize("NFKC", text)


def _under(rel: str, roots: tuple[str, ...]) -> str | None:
    for root in roots:
        r = root.strip("/")
        if rel == r or rel.startswith(r + "/"):
            return r
    return None


def _stat_kind(full: Path) -> str:
    """What the entry at `full` is, decided by ONE call that does not swallow errors (`os.lstat`, which never follows a link):
    "gone" only when the system says there is no such file (FileNotFoundError); "link", "folder" or "file" for those kinds;
    "unreadable" for everything else (a pipe, a socket, a device, and any other OSError such as a permission error, a parent
    that is not a folder, a loop of links). `Path.is_symlink`, `is_dir` and `is_file` answer False for some errors on some
    Python versions, which would read an entry that cannot be inspected as gone."""
    try:
        mode = os.lstat(full).st_mode
    except FileNotFoundError:
        return "gone"
    except OSError:
        return "unreadable"
    if stat.S_ISLNK(mode):
        return "link"
    if stat.S_ISDIR(mode):
        return "folder"
    if stat.S_ISREG(mode):
        return "file"
    return "unreadable"


def _folder_present(repo: Path, cfg: GuardConfig) -> bool:
    """True unless the system says the demo-only folder is not there (`_stat_kind` "gone"). An entry that cannot be
    inspected, a link or a loop counts as present: the stricter reading wins."""
    return _stat_kind(repo / cfg.folder) != "gone"


def _shape_hits(repo: Path, cfg: GuardConfig, gitlinks: set[str]) -> list[str]:
    """The hits of the special files: the copy-run marker must be a regular file of size 0, and an exempt file must be a
    regular file (not a link, not unreadable) no larger than `max_file_bytes`. Their content is not searched (they hold the
    folder name on purpose), but their shape is."""
    hits: list[str] = []
    marker = cfg.copy_run_marker
    kind = _stat_kind(repo / marker)
    if kind == "file" and os.lstat(repo / marker).st_size != 0:
        hits.append(
            f"{marker}: copy-run-marker-not-empty (the marker must be an empty regular file)"
        )
    elif kind in ("link", "folder", "unreadable"):
        hits.append(f"{marker}: copy-run-marker-not-a-regular-file (a {kind} cannot be the marker)")
    for rel in sorted(set(cfg.exempt_files)):
        if rel in gitlinks:
            continue
        kind = _stat_kind(repo / rel)
        if kind == "link":
            hits.append(f"{rel}: symlink-exempt-file (an exempt file must be a regular file)")
        elif kind == "unreadable":
            hits.append(f"{rel}: unreadable-file (the entry cannot be inspected)")
        elif kind == "file" and os.lstat(repo / rel).st_size > cfg.max_file_bytes:
            hits.append(f"{rel}: file-too-large (over {cfg.max_file_bytes} bytes; it is not read)")
        elif kind == "file":
            try:
                with (repo / rel).open("rb") as handle:
                    magic = _magic_kind(handle.read(cfg.max_file_bytes + 1))
            except OSError:
                hits.append(f"{rel}: unreadable-file (it cannot be read)")
                continue
            if magic:
                hits.append(
                    f"{rel}: binary-in-product-root (the exempt file is {magic}, whatever its ending says)"
                )
    return hits


def scan(repo: Path, cfg: GuardConfig, *, running_copy_run: bool = False) -> list[str]:
    """Every way product code can depend on the demo-only folder, as `path:line: rule` lines (empty = clean).
    `running_copy_run` is True only when the copy run itself calls this: the copy run IS the wiring, so the marker rule
    (`copy-run-not-wired`) is not asked then; every other rule is."""
    hits: list[str] = []
    name = _name_pattern(cfg.folder)
    phrases = _phrase_patterns(cfg.allowed_phrases)
    used: set[str] = set()
    loaders = set(cfg.loaders)
    exempt = set(cfg.exempt_files) | {cfg.copy_run_marker}
    for root in cfg.product_roots:
        # a root that is itself a symlink is reported by the walk below, like any other symlink
        top_kind = _stat_kind(repo / root)
        if top_kind == "unreadable":
            hits.append(f"{root}: unreadable-file (the entry cannot be inspected)")
        elif top_kind not in ("folder", "link"):
            hits.append(
                f"{root}: product-root-missing (a missing root would make the scan prove nothing)"
            )
        if any(name.fullmatch(_nfkc(part)) for part in Path(root).parts):
            hits.append(
                f"{root}: folder-inside-product-root (it would be packaged with the product)"
            )
    for rel in sorted(loaders):
        f = repo / rel
        loader_kind = _stat_kind(f)
        if loader_kind == "unreadable":
            hits.append(f"{rel}: unreadable-file (the entry cannot be inspected)")
            continue
        if loader_kind != "file":
            hits.append(f"{rel}: stale-loader-entry (file does not exist)")
            continue
        try:
            loader_text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            hits.append(f"{rel}: unreadable-file (it cannot be read)")
            continue
        if not name.search(_nfkc(loader_text)):
            hits.append(f"{rel}: stale-loader-entry (file does not name the folder)")
    listed = tracked_paths(repo)  # first: it stops the run when this is not a git checkout
    gitlinks = _gitlinks(repo)
    byte_names = _byte_patterns(cfg.folder)  # compiled once for the whole scan
    for rel in sorted(set(cfg.exempt_files)):
        if _stat_kind(repo / rel) in ("gone", "folder") and rel not in gitlinks:
            hits.append(f"{rel}: stale-exempt-entry (neither a file nor a git link that exists)")
    hits += _shape_hits(repo, cfg, gitlinks)
    if (
        not running_copy_run
        and _folder_present(repo, cfg)
        and _stat_kind(repo / cfg.copy_run_marker) != "file"
    ):
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
        kind = _stat_kind(full)
        if kind == "gone":
            continue  # listed by git but gone from the disk (the system says: no such file)
        if kind == "unreadable":
            if (
                root is not None and rel not in exempt
            ):  # an exempt file's shape is checked by `_shape_hits`
                hits.append(f"{rel}: unreadable-file (the entry cannot be inspected)")
            continue
        is_link, is_folder = (
            kind == "link",
            kind == "folder",
        )  # git lists a submodule (a git link) as a folder
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
    hits: list[str] = []
    if suffix in cfg.skip_suffixes and not has_mark(suffix, data):
        hits.append(
            f"{rel}: ending-does-not-match-content (a {suffix} file must start with the mark of its kind)"
        )
    if suffix in cfg.skip_suffixes and _looks_binary(data):
        if any(rx.search(data) for rx in byte_names.values()):
            hits.append(f"{rel}: names-demo-only-folder (inside a binary file)")
        return hits
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return [
            *hits,
            f"{rel}: unreadable-file (not text and not on the list of known binary endings)",
        ]
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


def _link_stays_in_copy(source: Path, rel: str, root: Path, folder: str) -> bool:
    """True when the tracked symlink at `rel` points to a place inside the copy that is not the demo-only folder, written as
    a relative path. An absolute target is refused (it would point at the original checkout, so the copy run would prove
    nothing for that path), and so is any target that leaves the copy or lands in the folder. The target is worked out
    by text (`os.path.normpath`), not followed: a swapped or looping path cannot lead the check elsewhere."""
    target = os.readlink(source)
    if os.path.isabs(target):
        return False
    placed = Path(os.path.normpath(root / rel / ".." / target))
    return placed.is_relative_to(root) and not placed.is_relative_to(root / folder)


def _copy_regular(source: Path, target: Path) -> None:
    """Copy one regular file without ever following a link: the file is opened with O_NOFOLLOW (and without blocking) and
    checked to be a regular file on the open handle, so a path swapped for a link or a pipe after the earlier check is
    refused, never copied through."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(source, flags)
    except OSError as exc:
        raise SystemExit(
            f"demo_only_guard: {source.name} could not be opened as a plain file; refusing"
        ) from exc
    with os.fdopen(fd, "rb") as src:
        info = os.fstat(src.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise SystemExit(
                f"demo_only_guard: {source.name} is not a regular file any more; refusing"
            )
        with target.open("wb") as out:
            shutil.copyfileobj(src, out)
            os.fchmod(out.fileno(), stat.S_IMODE(info.st_mode))
    os.utime(target, ns=(info.st_atime_ns, info.st_mtime_ns))


def copy_without_folder(repo: Path, cfg: GuardConfig, dest: Path) -> None:
    """A copy of the files git tracks (`tracked_paths(repo, include_new=False)`, the same list the scan reads, with no
    second rule of names): no version history, no cache, no virtual environment, no file git does not track, and without
    the demo-only folder and the copy-run marker. Copied file by file, so a tracked folder is copied whatever its name, and
    an untracked key file, an ignored build folder or a `.pgpass` in the working folder never reaches the copy. A tracked
    symlink is copied only when it is a relative one that stays inside the copy and avoids the folder; any other
    (absolute, leading out of the copy, into the folder) stops the run, as the scan refuses links in a product folder."""
    folder = cfg.folder.strip("/")
    marker = cfg.copy_run_marker
    root = dest.resolve()
    for rel in tracked_paths(repo, include_new=False):
        if rel == marker or rel == folder or rel.startswith(folder + "/"):
            continue
        source = repo / rel
        kind = _stat_kind(source)
        if kind in ("gone", "folder"):
            continue  # deleted since the last commit; a submodule folder is not copied (the scan reports it)
        target = dest / rel
        if not target.resolve().parent.is_relative_to(root):
            raise SystemExit(
                "demo_only_guard: a tracked path leads out of the copy; refusing to copy"
            )
        if kind == "unreadable":
            raise SystemExit(
                f"demo_only_guard: {rel} cannot be copied (not a file or a link); refusing"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        if kind == "link":
            if not _link_stays_in_copy(source, rel, root, folder):
                raise SystemExit(
                    f"demo_only_guard: the symlink {printable(rel)} is absolute or leads out of the copy or into the "
                    "folder; the copy run would prove nothing for it, refusing"
                )
            os.symlink(os.readlink(source), target)
        else:
            _copy_regular(source, target)


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
    # the scan comes first, enforced here and not by the order of the caller's calls
    if hits := scan(repo, cfg, running_copy_run=True):
        print("\n".join(printable(h) for h in hits))
        print("demo_only_guard: the scan found the hits above; the copy run is not started")
        return 1
    if new := sorted(set(tracked_paths(repo)) - set(tracked_paths(repo, include_new=False))):
        print(
            f"demo_only_guard: {len(new)} file(s) are not added to git and are not in the copy (git add them to test them): "
            + ", ".join(printable(n) for n in new[:5])
            + (" ..." if len(new) > 5 else "")
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
    mode = (
        ap.add_mutually_exclusive_group()
    )  # one mode at a time: argparse exits 2 with a message otherwise
    mode.add_argument(
        "--require", action="store_true", help="exit 2 if the demo-only folder is missing"
    )
    mode.add_argument(
        "--without-folder", action="store_true", help="run pytest in a copy without the folder"
    )
    mode.add_argument(
        "--without-folder-if-present",
        action="store_true",
        help="like --without-folder, but exit 0 at once when there is no folder",
    )
    ap.add_argument(
        "pytest_args", nargs="*", help="after --: arguments for pytest (with --without-folder)"
    )
    a = ap.parse_args(argv)
    if a.pytest_args and not (a.without_folder or a.without_folder_if_present):
        ap.error(
            "pytest arguments are accepted only with --without-folder or --without-folder-if-present"
        )
    repo = Path(a.root).resolve()
    cfg = load_config(Path(a.config))
    if a.without_folder_if_present and not _folder_present(repo, cfg):
        return 0
    if a.without_folder or a.without_folder_if_present:
        return run_without_folder(repo, cfg, a.pytest_args)
    if a.require and not _folder_present(repo, cfg):
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
