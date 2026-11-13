"""The demo-only folder guard.

The rule in plain words: everything that exists only for demos (made-up data, example prompts,
recorded model replies, test fixtures) lives in one folder, and the product never depends on it. The
product is the code that is shipped to a client; deleting the folder must leave a build whose tests
still pass. The folder name is in tools/demo_only_guard.toml.

The scan works from one list, `git ls-files` (see `tracked_paths`), and fails (exit 1) for each of
these, in every file under the product folders listed in the settings file (a symlink pointing into
the folder from anywhere else fails too):
  * a symlink of any kind (it could point into the folder, out of the repository, or nowhere),
    including a folder on the way to a listed file that has been swapped for a link since git listed
    the file (each parent is looked at with `os.lstat`);
  * the folder inside a product folder, at any depth, or any file or folder name that holds the
    folder name;
  * a line that names the folder (upper or lower case; "-", "_" and a space count as the same
    separator);
  * a made-up record id (the patterns are listed in the settings file);
  * a submodule (a git link) under a product folder, even when its folder is missing: its files
    cannot be scanned;
  * a file ending in .pyc, .so, .zip, .whl, .gz, .tgz, .tar, .bz2 or .xz under a product folder, and
    a file of ANY ending whose first bytes are the mark of one of `MAGIC_KINDS` (zip, ELF, gzip,
    bzip2, xz, tar, compiled Python, Mach-O, fat Mach-O or Java class file, PE, RAR, DOS or Windows
    program: it cannot be read, or it packs what it holds; bzip2 needs a level 1 to 9 and a valid
    block or end-of-stream mark, so a file that has only the three letters or a level 0 is not one:
    on purpose, it is not valid bzip2); the first 512 bytes decide (the PE header offset may reach
    further), data appended after a valid mark is not looked at, and an exempt file gets the same
    check;
  * a file with a picture, font or PDF ending (`ENDING_MARKS`: .png .jpg .jpeg .gif .ico .pdf .woff
    .woff2 .webp .ttf .otf) whose first bytes are not the mark of that kind: the content decides
    what a file is, not its name (zstd, 7z, rar, lz4 and the like named logo.png are hits). `.svg`
    is text (XML) and is not listed: it is read as text like any other file;
  * a file or folder entry git lists that cannot be inspected or read (a permission error, a pipe, a
    socket, a parent folder that cannot be entered, a loop of links), including a product root, a
    loader file and the demo-only folder itself: it is a hit (or counts as present), never a skip;
    only "no such file" means the entry is gone (see `_stat_kind`);
  * a file larger than `max_file_bytes` in the settings (it is not read; a hit says so), including a
    file on the exempt list;
  * a file that is not text and is not on the skip list of known binary endings (it cannot be read,
    so it is refused);
  * a loader file (the one place that may pick the folder by configuration) that names it more often
    than the cap;
  * the folder being present while the copy run is not wired (see the marker file in the settings):
    the marker must be a regular file of size 0, not a link or a folder, and an exempt file must not
    be a link. Every other file type is read, including files without an ending. A file with a known
    picture, font or PDF ending that has the right first bytes is not read as text when its first
    8192 bytes hold a NUL byte or it is not valid text; its bytes are searched for the name instead
    (as UTF-8, UTF-16 and UTF-32 text, little- and big-endian, no byte-order mark). Every line and
    every path part is normalised (NFKC) before it is compared, so a full-width spelling of the
    name, which Python reads as the same identifier, is a hit. A file that holds NUL bytes is also
    searched for the name written as UTF-16 or UTF-32 without a byte-order mark. Output per hit:
    path:line: rule (the matched text is never printed; a path is printed with control characters
    escaped as \\xNN, \\uNNNN or \\UNNNNNNNN, and a path that starts with "::" starts with \\x3a:
    instead, so a hit can never be read as a CI workflow command or hide a line). Limits: the byte
    search of a binary file looks for the name as written (it is not normalised with NFKC, because a
    binary has no text to normalise), a name the compiler assembles from pieces at build time is not
    found, and the made-up record id patterns are not run on binary files (only on text). Paths are
    matched as git lists them; on a case-insensitive file system a differently-cased spelling of a
    product folder is not matched (the scan runs on git's own path list, on Linux in CI). A file
    that names the folder only inside a quoted string `"DEMO_ONLY"` is still a hit: over-detection
    is the safe side, and a product file that must name the folder for a real reason goes on the
    exempt list with its reason. Only files git lists are read, so a file the repository ignores
    (.gitignore or .git/info/exclude of the repository: they say what the project does not track) is
    not checked; the person's own ignore file (core.excludesFile, the XDG one) is not applied, so it
    cannot hide a file; and only the product folders in the settings are scanned, so the packaging
    files at the repository root (for example pyproject.toml) are not; a folder the packaging config
    adds to the product from outside the listed folders is the copy run's job. A name built from
    pieces at run time (for example "demo" + "_only") cannot be found by any text scan; the copy run
    (`--without-folder`) is the check for that case, because the tests fail when the folder is
    really gone.

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
import errno
import importlib.util
import os
import re
import shutil
import stat
import sys
import tempfile
import tomllib
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


def _load_fixed_run():
    """The program starter next to this file, read by its file path: never an installed or foreign
    `tools` package, and it works when the file is run alone with `-I` (the script folder is not on
    the path then). The same body is in `tools/demo_only_guard.py` and `tools/scan_repo.py`: each
    must load the starter before it can import anything, so the two copies stay and
    `test_the_two_loaders_of_the_program_starter_are_the_same` compares them."""
    from importlib import util

    spec = util.spec_from_file_location(
        "fixed_run", Path(__file__).resolve().with_name("fixed_run.py")
    )
    if spec is None or spec.loader is None:
        raise SystemExit("the program starter next to this file (fixed_run.py) cannot be read")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_fixed


run_fixed = _load_fixed_run()

HERE = Path(__file__).resolve().parent
# The first bytes a file with each of the endings that may hold a non-text file must start with. The
# content decides: a file with one of these endings that does not start with the mark of its kind is
# a hit.
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
# What else must hold, beyond the first bytes, for an ending whose mark is not a plain start: a webp
# file is a RIFF container, and "WEBP" stands at bytes 8 to 11 (any other RIFF file, such as a wav,
# is not a webp).
_EXTRA_MARKS: dict[str, Callable[[bytes], bool]] = {".webp": lambda d: d[8:12] == b"WEBP"}


def has_mark(suffix: str, data: bytes) -> bool:
    """True when `data` starts like a file of the kind the ending `suffix` names (see
    `ENDING_MARKS`)."""
    return data.startswith(ENDING_MARKS[suffix]) and _EXTRA_MARKS.get(suffix, lambda _d: True)(data)


# Endings of files that are known not to be text; every other file is read. Every one needs a row in
# ENDING_MARKS.
DEFAULT_SKIP_SUFFIXES = tuple(ENDING_MARKS)
# Endings that are never accepted in a product folder: an importable or loadable file that cannot be
# read (a sourceless .pyc, a compiled .so) or a packed archive (.zip, .whl, .gz, .tgz, .tar, .bz2,
# .xz) that hides what is inside.
REFUSED_SUFFIXES = (".pyc", ".so", ".zip", ".whl", ".gz", ".tgz", ".tar", ".bz2", ".xz")
MAX_FILE_BYTES = 8 * 1024 * 1024  # the default cap on one file (the settings file may change it)
# The only environment variable names the copy run's child process receives (no token, no key, no
# connection string).
DEFAULT_CHILD_ENV = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TMPDIR",
    "TEMP",
    "TMP",
    "SYSTEMROOT",
    "TERM",
    "VIRTUAL_ENV",
    "HADAVIN_REQUIRE_NODE",
)
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
    """Read and check the settings. A bad setting stops the guard: it never runs with the check
    quietly off."""
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
    """The folder name in any case, with "_", "-" and a space read as one separator (Demo_Only,
    demo-only, demo only)."""
    parts = [p for p in re.split(_SEP, folder) if p]
    return re.compile(_SEP.join(re.escape(p) for p in parts), re.IGNORECASE)


def _phrase_patterns(phrases: tuple[str, ...]) -> dict[str, re.Pattern[str]]:
    # an allowed phrase counts only as a whole word group, in the exact case written: "DEMO_ONLY/x",
    # "xDEMO_ONLY", "DEMO_ONLY-x" and "x-DEMO_ONLY" are still a path or a name; the same word in
    # lower case is not the phrase
    return {p: re.compile(r"(?<![\w/\\-])" + re.escape(p) + r"(?![\w/\\-])") for p in phrases}


# `-c core.excludesFile=<nothing>` overrides the global, XDG and system setting of git's own ignore
# file, so a file the person running the guard (or a CI image) ignores for themselves is still
# listed. What stays honoured, on purpose: `.gitignore` files and `.git/info/exclude` of the
# repository itself (they say what the project does not track; only tracked files are copied).
GIT_NO_USER_EXCLUDES = ("-c", f"core.excludesFile={os.devnull}")


def _git_env() -> dict[str, str]:
    """The environment of every git call: the caller's, without any `GIT_*` variable (GIT_DIR,
    GIT_INDEX_FILE, GIT_WORK_TREE and the like would make `git -C <repo>` list another tree than the
    one asked for)."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


# The line masker `_hide_secrets` hides secrets in git's own error line before the guard prints it.
# It copies five passes of the core rules (`hadavin_sdk.guard.redact`); it is a check on copied demo
# text, not a replacement for the core redactor. It is NOT the same as the core: it hides more in
# some places and shows what the core hides in one. The CHANGELOG paragraph "the line masker (batch
# 15)" is the one place that lists both directions and what is not covered; a test runs every
# example of that paragraph through this code. The passes, in this order:
#  1. everything after a literal `Authorization:` header name, to the end of the line, whatever the
#  scheme;
#  2. a bare scheme word and its token (`Bearer abc...`, `Basic abc...`): first the two rules of the
#  core
#     (BEARER: token of 12 or more characters; BASIC: 8 or more; the same patterns, copied here
#     because the guard
#     runs without importing the product package; a test compares the pattern text with the core),
#     then ONE extra
#     rule that hides more: a token (letters, digits and `. _ ~ + / - < >`, then `=` padding) of 16
#     or more
#     characters, or one that holds a letter and a digit, is hidden at any length. This pass runs
#     BEFORE the pairs:
#     in `authorization=Bearer <token>` the pair value stops at the first white space, so a pair
#     pass that ran
#     first would hide only the word `Bearer`;
#  3. the user and password part of a URL, between `://` and the LAST `@` before the next white
#  space;
#  4. the value of a `name=value` pair whose NAME holds key, token, secret, password, passwd, pwd,
#  auth or
#     credential (any case): a value that starts with a quote runs to the matching quote (a
#     backslash escapes),
#     any other value runs to white space. A bare name `bypass` is hidden unless its value is one of
#     true, false,
#     yes, no, on, off, 0, 1 (any case) AND only white space follows it on the line. After a name
#     that holds
#     `auth` and a value that is a scheme word (Bearer, Basic, Digest) the pair also takes what
#     follows: the token
#     at any length (a quoted value whole), and for Digest every part to the end of the line.
# Not covered (the masker reads only the `name=value` form): the colon form (`password: x`), a
# quoted JSON pair (`"token": "x"`), `--password x`, `"authorization": "Bearer x"`, JWT text, API
# keys and other high-entropy runs, cookies. Each pass is linear (no nested repetition), so a very
# long line costs time in proportion to its length (a test counts the reads).
_BEARER = re.compile(r"(?i)\bbearer\s+([a-z0-9._~+/\-<>]{12,}=*)")
_BASIC = re.compile(r"(?i)\bbasic\s+([a-z0-9+/<>_]{8,}={0,2})")
_AUTH_HEADER = re.compile(r"(?i)(authorization:)[^\n]*")
_SECRET_NAME = re.compile(r"(?i)key|token|secret|passw(?:or)?d|pwd|auth|credential")
_HIDDEN = "<hidden>"


def _is_name_char(c: str) -> bool:
    return c.isalnum() or c in "_.-"


def _hide_urls(line: str) -> str:
    out: list[str] = []
    pos = 0
    while (at := line.find("://", pos)) >= 0:
        start = at + 3
        end = start
        while end < len(line) and not line[end].isspace():
            end += 1
        last = line.rfind("@", start, end)
        if last >= 0:
            out.append(line[pos:start] + _HIDDEN)
            pos = last  # the `@` and the host stay
        else:
            out.append(line[pos:end])
            pos = end
            continue
        out.append(line[pos:end])
        pos = end
    out.append(line[pos:])
    return "".join(out)


_BARE_WORD = "bypass"
_PLAIN_FLAGS = frozenset({"true", "false", "yes", "no", "on", "off", "0", "1"})
_SCHEME_WORDS = frozenset({"bearer", "basic", "digest"})
_SCHEME_TOKEN = re.compile(r"(?i)\b(?:bearer|basic)\s+([a-z0-9._~+/\-<>_]+={0,2})")


def _looks_secret_shaped(token: str) -> bool:
    """A token after a bare scheme word that is long (16 or more characters) or mixes letters and
    digits."""
    body = token.rstrip("=")
    return len(body) >= 16 or (any(c.isalpha() for c in body) and any(c.isdigit() for c in body))


def _hide_shaped_scheme_token(line: str) -> str:
    return _SCHEME_TOKEN.sub(
        lambda m: (
            m.group(0).replace(m.group(1), _HIDDEN, 1)
            if _looks_secret_shaped(m.group(1)) and _HIDDEN not in m.group(1)
            else m.group(0)
        ),
        line,
    )


def _value_end(line: str, start: int) -> int:
    """Where the value that begins at `start` ends: a value that starts with a quote runs to the
    matching quote (a backslash escapes), any other value runs to white space."""
    n = len(line)
    end = start
    if end < n and line[end] in "'\"":
        quote = line[end]
        end += 1
        while end < n and line[end] != quote:
            end += 2 if line[end] == "\\" else 1
        return min(end + 1, n)
    while end < n and not line[end].isspace():
        end += 1
    return end


def _hide_pairs(line: str) -> str:
    out: list[str] = []
    pos = 0
    n = len(line)
    # a plain on/off value of the bare word is shown only when nothing but white space follows it on
    # the line
    last_text = len(line.rstrip())
    at = line.find("=")
    while at >= 0:
        start = at
        while start > pos and _is_name_char(line[start - 1]):
            start -= 1
        name = line[start:at]
        named_secret = bool(_SECRET_NAME.search(name)) if start < at else False
        if start < at and (named_secret or name.lower() == _BARE_WORD):
            end = _value_end(line, at + 1)
            value = line[at + 1 : end]
            if not named_secret and value.lower() in _PLAIN_FLAGS and end >= last_text:
                at = line.find("=", at + 1)  # a bare flag word with a plain on/off value is shown
                continue
            if "auth" in name.lower() and value.lower() in _SCHEME_WORDS:
                tail = end
                while tail < n and line[tail].isspace() and line[tail] != "\n":
                    tail += 1
                stop = _value_end(line, tail)
                if value.lower() == "digest":
                    # Digest holds several name=value parts: all of them, to the end of the line
                    stop = line.find("\n", tail) if "\n" in line[tail:] else n
                if stop > tail and line[tail:stop] != _HIDDEN:
                    end = stop  # `authorization=Bearer <token>`: the scheme word and the token, whatever the length
            out.append(line[pos : at + 1] + _HIDDEN)
            pos = end
            at = line.find("=", pos)
        else:
            at = line.find("=", at + 1)
    out.append(line[pos:])
    return "".join(out)


def _hide_group(pattern: re.Pattern[str], line: str) -> str:
    return pattern.sub(lambda m: m.group(0).replace(m.group(1), _HIDDEN, 1), line)


def _hide_header(line: str) -> str:
    return _AUTH_HEADER.sub(lambda m: m.group(1) + " " + _HIDDEN, line)


def _hide_bearer(line: str) -> str:
    return _hide_shaped_scheme_token(_hide_group(_BEARER, line))


def _hide_basic(line: str) -> str:
    return _hide_group(_BASIC, line)


# The passes of `_hide_secrets`, in this order (the list above the patterns says what each one
# hides). A test counts them, and the CHANGELOG states the count.
_MASK_PASSES: tuple[Callable[[str], str], ...] = (
    _hide_header,
    _hide_bearer,
    _hide_basic,
    _hide_urls,
    _hide_pairs,
)


def _hide_secrets(line: str) -> str:
    for step in _MASK_PASSES:
        line = step(line)
    return line


def _git_failure(what: str, stderr: bytes, repo: Path) -> str:
    """The message of a failed git call: what failed, then the FIRST line of git's own error (so
    "dubious ownership" is not hidden behind a generic message). The line is made safe to print
    (`printable`), the repository path in it is replaced by "<repo>" and it is cut at 200
    characters; nothing else of git's output is shown."""
    first = stderr.decode("utf-8", errors="replace").strip().splitlines()[:1]
    shown = (
        printable(_hide_secrets(first[0].replace(str(repo), "<repo>")))[:200]
        if first
        else "no message"
    )
    return f"demo_only_guard: {what}; refusing to scan with an unknown file list. git said: {shown}"


def _git_listing(repo: Path, *, include_new: bool) -> list[str]:
    """What `git ls-files` says (see `tracked_paths`), with no refusal of an empty answer."""
    if not (repo / ".git").exists():
        raise SystemExit(
            f"demo_only_guard: {repo} is not a git checkout; the scan lists files with git and will not guess"
        )
    flags = ["--cached", "--others", "--exclude-standard"] if include_new else ["--cached"]
    done = run_fixed(
        ["git", "-C", str(repo), *GIT_NO_USER_EXCLUDES, "ls-files", "-z", *flags],
        capture_output=True,
        check=False,
        env=_git_env(),
    )
    if done.returncode != 0:
        raise SystemExit(_git_failure("git ls-files failed", done.stderr, repo))
    text = done.stdout.decode("utf-8", errors="surrogateescape")
    return sorted({p for p in text.split("\0") if p})


def tracked_paths(repo: Path, *, include_new: bool = True) -> list[str]:
    """The ONE list of paths the scan looks at: what `git ls-files` says the repository holds
    (tracked files, plus, unless `include_new` is False, files not yet added and not ignored), as
    repository-relative paths with "/". Directories are not listed by git, and a symlink is one
    entry that is never followed. Not a git checkout, or git failing, stops the guard: it does not
    guess. An empty list stops the guard too, with a message that says which list was empty. The
    copy run asks for the tracked files only (`include_new=False`)."""
    paths = _git_listing(repo, include_new=include_new)
    if not paths:
        what = "files" if include_new else "tracked files (git add the files you want in the copy)"
        raise SystemExit(
            f"demo_only_guard: git listed no {what} in {repo}; refusing to scan an empty list"
        )
    return paths


def _gitlinks(repo: Path) -> set[str]:
    """The paths git holds as git links (a submodule: mode 160000), whether or not their folder is
    on the disk."""
    done = run_fixed(
        ["git", "-C", str(repo), "ls-files", "-s", "-z", "--cached"],
        capture_output=True,
        check=False,
        env=_git_env(),
    )
    if done.returncode != 0:
        raise SystemExit(_git_failure("git ls-files -s failed", done.stderr, repo))
    out = set()
    for entry in done.stdout.decode("utf-8", errors="surrogateescape").split("\0"):
        info, _, path = entry.partition("\t")
        if path and info.startswith("160000 "):
            out.add(path)
    return out


def _is_pe(data: bytes) -> bool:
    """A Windows program or library: "MZ", then at byte 0x3C a 4-byte little-endian offset, and
    "PE\\0\\0" at that offset. A file too short to hold the offset or the signature there is not
    read as one (the header cannot say). The offset may lie beyond the first 512 bytes, so the whole
    of `data` is used for it."""
    if data[:2] != b"MZ" or len(data) < 0x40:
        return False
    at = int.from_bytes(data[0x3C:0x40], "little")
    return at + 4 <= len(data) and data[at : at + 4] == b"PE\x00\x00"


# A compiled Python file starts with a 2-byte version number (little-endian) and "\r\n". Python 3
# numbers start at 3000; the upper end is the running interpreter's own number
# (`importlib.util.MAGIC_NUMBER`) plus 1000, at least 3999, and never above 8191 (the second byte of
# such a number is a control character, so no text file starts with one). Python 2 files (numbers
# from 20121) are NOT covered: their first two bytes are ordinary letters and the check would hit
# text.
_PYC_MAGIC_MAX = min(
    8191, max(3999, int.from_bytes(importlib.util.MAGIC_NUMBER[:2], "little") + 1000)
)

# (kind, does the head say so): ONE table; `MAGIC_KINDS` and `_magic_kind` both come from it, and
# the CHANGELOG sentence
# about first bytes is checked against it by a test. A compiled Python file has a 2-byte version
# number (little-endian, from
# 3000 up to `_PYC_MAGIC_MAX`: that end follows the interpreter that RUNS the guard, 4531 on Python
# 3.12, 4627 on 3.14) and
# "\r\n"; Mach-O is four magic values (32 and 64 bit, each in both byte orders; the fat form is a
# separate kind below); bzip2
# needs a level 1 to 9 and then a block or end-of-stream mark.
_MAGIC_CHECKS: tuple[tuple[str, Callable[[bytes], bool]], ...] = (
    ("zip", lambda d: d[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")),
    ("ELF", lambda d: d[:4] == b"\x7fELF"),
    ("gzip", lambda d: d[:2] == b"\x1f\x8b"),
    (
        "bzip2",
        lambda d: (
            d[:3] == b"BZh"
            and len(d) > 3
            and 0x31 <= d[3] <= 0x39
            and d[4:10] in (b"1AY&SY", b"\x17rE8P\x90")
        ),
    ),
    ("xz", lambda d: d[:6] == b"\xfd7zXZ\x00"),
    ("tar", lambda d: len(d) > 262 and d[257:262] == b"ustar"),
    (
        "compiled Python",
        lambda d: d[2:4] == b"\r\n" and 3000 <= int.from_bytes(d[:2], "little") <= _PYC_MAGIC_MAX,
    ),
    (
        "Mach-O",
        lambda d: (
            d[:4]
            in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe")
        ),
    ),
    # the fat (universal) Mach-O and the Java class file share the first four bytes (CAFEBABE,
    # either byte order): both are compiled code that has no place in a product folder, so they are
    # ONE kind and one hit, with no byte-count rule
    (
        "fat Mach-O or Java class file",
        lambda d: (
            d[:4]
            in (
                b"\xca\xfe\xba\xbe",  # fat Mach-O 32-bit offsets and Java class, either byte order
                b"\xbe\xba\xfe\xca",
                b"\xca\xfe\xba\xbf",  # fat Mach-O with 64-bit offsets, either byte order
                b"\xbf\xba\xfe\xca",
            )
        ),
    ),
    ("PE", _is_pe),
    # two marks that are valid UTF-8 text, so a file that holds only them (and NUL bytes) would be
    # read as text and pass: a RAR archive, and a DOS or Windows program header ("MZ" followed only
    # by NUL bytes up to byte 64; a program that is not a PE file has no PE header to check). A NUL
    # byte alone is NOT a hit: text in UTF-16 or UTF-32 holds them and is searched.
    ("RAR", lambda d: d[:6] == b"Rar!\x1a\x07" and d[6:7] in (b"\x00", b"\x01")),
    ("DOS or Windows program", lambda d: d[:2] == b"MZ" and len(d) > 2 and not any(d[2:64])),
)
MAGIC_KINDS: tuple[str, ...] = tuple(kind for kind, _ in _MAGIC_CHECKS)


def _magic_kind(data: bytes) -> str:
    """What a file's first bytes say it is, when it is a compiled or packed file ("" when they say
    nothing): one of `MAGIC_KINDS`. The first 512 bytes decide (a PE file's header offset may reach
    further); anything appended after a valid mark is not looked at here. The ending of the file
    name is not consulted."""
    head = data[:512]
    for kind, says in _MAGIC_CHECKS:
        if says(data if kind == "PE" else head):
            return kind
    return ""


def printable(line: str) -> str:
    """A hit line made safe to print: a control, format, separator or unpaired-surrogate character
    in a path is shown as \\xNN, \\uNNNN or \\UNNNNNNNN, and a line that starts with "::" starts
    with \\x3a: instead (a CI runner reads a line that starts with "::" as a workflow command)."""
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


def _stat_info(full: Path | str) -> tuple[str, int]:
    """(kind, size) of the entry at `full`, decided by ONE call that does not swallow errors
    (`os.lstat`, which never follows a link): kind "gone" only when the system says there is no such
    file (FileNotFoundError); "link", "folder" or "file" for those kinds; "unreadable" for
    everything else (a pipe, a socket, a device, and any other OSError such as a permission error, a
    parent that is not a folder, a loop of links). The size is of the same call (0 when not a file),
    so a file that is deleted between two calls cannot raise here. `Path.is_symlink`, `is_dir` and
    `is_file` answer False for some errors on some Python versions, which would read an entry that
    cannot be inspected as gone."""
    try:
        info = os.lstat(full)
    except FileNotFoundError:
        return "gone", 0
    except OSError:
        return "unreadable", 0
    mode = info.st_mode
    if stat.S_ISLNK(mode):
        return "link", 0
    if stat.S_ISDIR(mode):
        return "folder", 0
    if stat.S_ISREG(mode):
        return "file", info.st_size
    return "unreadable", 0


def _parent_is_link(repo: Path, rel: str) -> bool:
    """True when a folder on the way to `rel` (below `repo`) is a link, or cannot be inspected:
    `os.lstat` of the entry alone reads through such a folder. Each component is looked at with
    `os.lstat`; the walk ends at the first component that is a link or cannot be inspected (True); a
    component that is gone, or is a file, does not end it (the entry below is then gone or
    unreachable, which the caller sees from the entry itself)."""
    walked = repo
    for part in rel.split("/")[:-1]:
        walked = walked / part
        if _stat_kind(walked) in ("link", "unreadable"):
            return True
    return False


def _entry_info(repo: Path, rel: str) -> tuple[str, int]:
    """`_stat_info` of `repo/rel` that never reads through a link on the way: when a folder on the
    way is a link (or cannot be inspected) the entry is a "link" (it would be read through that
    folder), unless it is gone."""
    kind, size = _stat_info(repo / rel)
    if kind != "gone" and _parent_is_link(repo, rel):
        return "link", 0
    return kind, size


def _stat_kind(full: Path | str) -> str:
    """What the entry at `full` is: the kind of `_stat_info`."""
    return _stat_info(full)[0]


def _link_rule(full: Path, folder_target: Path) -> str:
    """The rule a tracked link outside the product folders breaks, or "": a loop of links, or a
    chain too long for the system to follow (both are ELOOP: the system does not tell them apart),
    is a hit (it cannot be followed); a link whose place, worked out by the file system
    (`os.path.realpath`, which never raises on a loop), is the demo-only folder or inside it is a
    hit. No `Path.resolve()`: it raises RuntimeError on a loop on Python 3.12, and a traceback is
    never an answer here."""
    try:
        os.stat(full)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            return "symlink-loop (a loop of links, or a chain too long to follow)"
    if Path(os.path.realpath(full)).is_relative_to(folder_target):
        return "symlink-to-demo-only-folder"
    return ""


def _folder_present(repo: Path, cfg: GuardConfig) -> bool:
    """True unless the system says the demo-only folder is not there (`_stat_kind` "gone"). An entry
    that cannot be inspected, a link or a loop counts as present: the stricter reading wins."""
    return _stat_kind(repo / cfg.folder) != "gone"


def _shape_hits(repo: Path, cfg: GuardConfig, gitlinks: set[str]) -> list[str]:
    """The hits of the special files: the copy-run marker must be a regular file of size 0, and an
    exempt file must be a regular file (not a link, not unreadable) no larger than `max_file_bytes`.
    Their content is not searched (they hold the folder name on purpose), but their shape is."""
    hits: list[str] = []
    marker = cfg.copy_run_marker
    kind, size = _entry_info(repo, marker)
    if kind == "file" and size != 0:
        hits.append(
            f"{marker}: copy-run-marker-not-empty (the marker must be an empty regular file)"
        )
    elif kind in ("link", "folder", "unreadable"):
        hits.append(f"{marker}: copy-run-marker-not-a-regular-file (a {kind} cannot be the marker)")
    for rel in sorted(set(cfg.exempt_files)):
        if rel in gitlinks:
            continue
        kind, size = _entry_info(repo, rel)
        if kind == "link":
            hits.append(f"{rel}: symlink-exempt-file (an exempt file must be a regular file)")
        elif kind == "unreadable":
            hits.append(f"{rel}: unreadable-file (the entry cannot be inspected)")
        elif kind == "file" and size > cfg.max_file_bytes:
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
    """Every way product code can depend on the demo-only folder, as `path:line: rule` lines (empty
    = clean). `running_copy_run` is True only when the copy run itself calls this: the copy run IS
    the wiring, so the marker rule (`copy-run-not-wired`) is not asked then; every other rule is."""
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
        loader_kind = _entry_info(repo, rel)[0]
        if loader_kind == "unreadable":
            hits.append(f"{rel}: unreadable-file (the entry cannot be inspected)")
            continue
        if loader_kind == "link":
            hits.append(
                f"{rel}: symlink-loader-entry (a loader must be a regular file, reached through no link)"
            )
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
        and _entry_info(repo, cfg.copy_run_marker)[0] != "file"
    ):
        hits.append(
            f"{cfg.copy_run_marker}: copy-run-not-wired (the folder exists, so CI must run the copy run "
            "and the marker file must say so)"
        )
    folder_target = Path(os.path.realpath(repo / cfg.folder))
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
        kind, size = _stat_info(full)
        if kind != "gone" and _parent_is_link(repo, rel):
            kind, size = (
                "link",
                0,
            )  # a folder on the way was swapped for a link: the entry is read through it, so it is a link hit
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
            if is_link and (rule := _link_rule(full, folder_target)):
                hits.append(f"{rel}: {rule}")
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
        hits += _scan_file(full, rel, cfg, name, phrases, used, rel in loaders, byte_names, size)
    hits += [
        f"tools/demo_only_guard.toml: stale-allowed-phrase ({p})"
        for p in cfg.allowed_phrases
        if p not in used
    ]
    return list(dict.fromkeys(hits))


def _looks_binary(data: bytes) -> bool:
    """True when the bytes of a file with a known binary ending really are not text: a NUL byte in
    the first 8192 bytes, or bytes that are not valid UTF-8. A text file renamed to a binary ending
    is read by the scan instead."""
    if b"\0" in data[:8192]:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


BYTE_ENCODINGS = ("utf-8", "utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be")


def _byte_patterns(folder: str) -> dict[str, re.Pattern[bytes]]:
    """The folder name as bytes in each spelling a text could hold it: UTF-8, UTF-16 and UTF-32,
    little- and big-endian (no byte-order mark), in any ASCII case, with "_", "-" and a space as one
    separator."""
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
    size: int,
) -> list[str]:
    """The hits of one file in a product folder. `size` is from the one `lstat` of this file
    (`_stat_info`); the file is read once, and never when it is over `max_file_bytes`."""
    suffix = path.suffix.lower()
    if suffix in REFUSED_SUFFIXES:
        return [
            f"{rel}: binary-in-product-root (a {suffix} file cannot be read or hides what it packs)"
        ]
    try:
        if size > cfg.max_file_bytes:
            return [f"{rel}: file-too-large (over {cfg.max_file_bytes} bytes; it is not read)"]
        # the read is bounded, and a file that is gone or swapped since the lstat is an
        # unreadable-file hit, not an exception
        with path.open("rb") as handle:
            data = handle.read(cfg.max_file_bytes + 1)
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


def _dotdot_after_link(dest: Path, rel: str, target: str) -> bool:
    """True when the link target walks "..", after a component that is itself a link of the copy:
    text cannot say where that leads (`dir/k -> ..` then `dir/l -> k/../../outside`), so it is
    refused."""
    cur = dest / rel
    cur = cur.parent
    seen_link = False
    for part in target.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if seen_link:
                return True
            cur = cur.parent
            continue
        cur = cur / part
        if os.path.islink(cur):
            seen_link = True
    return False


def _link_problem(dest: Path, rel: str, root: Path, folder: str) -> str:
    """Why the copied link at `rel` is not allowed ("" when it is): checked AFTER every file is
    copied, against the copy with its links in place, never by text alone. Refused: an absolute
    target (it would point at the original checkout), a ".." after another link component, a loop of
    links, and a target that the file system (`os.path.realpath` of the copy) places outside the
    copy or inside the demo-only folder."""
    link = dest / rel
    try:
        target = os.readlink(link)
    except (
        OSError
    ):  # the link was swapped for a file or removed after it was copied: refuse, never a traceback
        return "changed while it was being checked"
    if os.path.isabs(target):
        return "is absolute"
    if _dotdot_after_link(dest, rel, target):
        return "walks '..' after another link"
    try:
        os.stat(link)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            return "is a link chain that is too long or loops"
    placed = Path(os.path.realpath(link))
    if not placed.is_relative_to(root):
        return "leads out of the copy"
    if placed.is_relative_to(root / folder):
        return "leads into the folder"
    return ""


_CAN_WALK = (
    hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY") and os.open in os.supports_dir_fd
)  # a platform without these (Windows) cannot open a file component by component: `_copy_regular` then refuses any link


def _copy_regular(repo: Path, rel: str, target: Path) -> None:
    """Copy the regular file `rel` of `repo` without ever following a link. Where `os.open` takes
    `dir_fd` and the system has O_NOFOLLOW and O_DIRECTORY (Linux, macOS), the path is walked one
    component at a time from the repository folder, every parent opened with O_DIRECTORY|O_NOFOLLOW
    and the file with O_NOFOLLOW (and without blocking), then checked to be a regular file on the
    open handle: a parent folder or the file swapped for a link or a pipe after an earlier check is
    refused, never copied through. Where it does not (Windows), a link on any component of the path
    is refused (checked with `os.lstat` just before the open: there a swap in that gap is not
    caught, which is why Linux CI is the check)."""
    parts = rel.split("/")
    opened: list[int] = []
    try:
        if _CAN_WALK:
            fd = os.open(repo, os.O_RDONLY | os.O_DIRECTORY)
            opened.append(fd)
            for part in parts[:-1]:
                fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                opened.append(fd)
            fd = os.open(
                parts[-1],
                os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
                dir_fd=fd,
            )
        else:
            walked = repo
            for part in parts:
                walked = walked / part
                if _stat_kind(walked) == "link":
                    raise OSError("a link on the path")
            fd = os.open(repo / rel, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    except OSError as exc:
        raise SystemExit(
            f"demo_only_guard: {parts[-1]} could not be opened as a plain file; refusing"
        ) from exc
    finally:
        for o in opened:
            os.close(o)
    with os.fdopen(fd, "rb") as src:
        info = os.fstat(src.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise SystemExit(
                f"demo_only_guard: {parts[-1]} is not a regular file any more; refusing"
            )
        with target.open("wb") as out:
            shutil.copyfileobj(src, out)
            if hasattr(os, "fchmod"):  # absent on Windows before Python 3.13
                os.fchmod(out.fileno(), stat.S_IMODE(info.st_mode))
            else:
                os.chmod(target, stat.S_IMODE(info.st_mode))
    os.utime(target, ns=(info.st_atime_ns, info.st_mtime_ns))


def copy_without_folder(repo: Path, cfg: GuardConfig, dest: Path) -> None:
    """A copy of the files git tracks (`tracked_paths(repo, include_new=False)`, the same list the
    scan reads, with no second rule of names): no version history, no cache, no virtual environment,
    no file git does not track, and without the demo-only folder and the copy-run marker. Copied
    file by file, so a tracked folder is copied whatever its name, and an untracked key file, an
    ignored build folder or a `.pgpass` in the working folder never reaches the copy. A tracked
    symlink is copied as a link, and after ALL files are copied each link is checked against the
    copy with its links in place (`_link_problem`): an absolute one, one that leads out of the copy
    or into the folder, one with ".." after another link, or a loop stops the run, as the scan
    refuses links in a product folder."""
    folder = cfg.folder.strip("/")
    marker = cfg.copy_run_marker
    root = Path(os.path.realpath(dest))
    links: list[str] = []
    for rel in tracked_paths(repo, include_new=False):
        if rel == marker or rel == folder or rel.startswith(folder + "/"):
            continue
        source = repo / rel
        kind = _stat_kind(source)
        if kind in ("gone", "folder"):
            continue  # deleted since the last commit; a submodule folder is not copied (the scan reports it)
        target = dest / rel
        if not Path(os.path.realpath(target.parent)).is_relative_to(root):
            raise SystemExit(
                "demo_only_guard: a tracked path leads out of the copy; refusing to copy"
            )
        if kind == "unreadable":
            raise SystemExit(
                f"demo_only_guard: {rel} cannot be copied (not a file or a link); refusing"
            )
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if kind == "link":
                os.symlink(os.readlink(source), target)
                links.append(rel)
            else:
                _copy_regular(repo, rel, target)
        except OSError as exc:  # an entry swapped after `_stat_kind`, or a write that failed: refuse, never a traceback
            raise SystemExit(
                f"demo_only_guard: {printable(rel)} changed or could not be copied ({type(exc).__name__}); refusing"
            ) from exc
    for rel in links:
        if problem := _link_problem(dest, rel, root, folder):
            raise SystemExit(
                f"demo_only_guard: the symlink {printable(rel)} {problem}; the copy run would prove nothing for it, refusing"
            )


_IMPORT_CHECK = (
    "import importlib, pathlib, sys\n"
    "m = importlib.import_module(sys.argv[1])\n"
    "f = pathlib.Path(m.__file__).resolve()\n"
    "sys.exit(0 if f.is_relative_to(pathlib.Path(sys.argv[2]).resolve()) else 3)\n"
)


def run_without_folder(repo: Path, cfg: GuardConfig, pytest_args: list[str]) -> int:
    """Run pytest in a copy that has no demo-only folder; its exit code is the answer. The child
    sees ONLY the copy's `src` on its import path (an inherited path or an editable install of the
    original checkout cannot win), and each product package is first checked to be imported from the
    copy: a pass that tested the original proves nothing."""
    if not cfg.product_packages:
        raise SystemExit(
            "demo_only_guard: 'product_packages' is empty; without a package to check the copy run could test the original"
        )
    # the scan comes first, enforced here and not by the order of the caller's calls
    if hits := scan(repo, cfg, running_copy_run=True):
        print("\n".join(printable(h) for h in hits))
        print("demo_only_guard: the scan found the hits above; the copy run is not started")
        return 1
    tracked = _git_listing(repo, include_new=False)
    if new := sorted(set(_git_listing(repo, include_new=True)) - set(tracked)):
        print(
            f"demo_only_guard: {len(new)} file(s) are not added to git and are not in the copy (git add them to test them): "
            + ", ".join(printable(n) for n in new[:5])
            + (" ..." if len(new) > 5 else "")
        )
    if not tracked:
        raise SystemExit(
            f"demo_only_guard: git tracks no files in {repo}, so the copy would be empty; git add the files first"
        )
    with tempfile.TemporaryDirectory(prefix="demo-only-guard-") as tmp:
        dest = Path(tmp) / "copy"
        copy_without_folder(repo, cfg, dest)
        if (dest / cfg.folder).exists():
            raise SystemExit(
                "demo_only_guard: the copy still holds the folder; refusing to report a pass"
            )
        # only the names the settings allow (no token, key or connection string of the caller
        # reaches the child)
        env = {k: v for k, v in os.environ.items() if k in cfg.child_env_allowed}
        env["PYTHONPATH"] = str(dest / "src")
        for package in cfg.product_packages:
            checked = run_fixed(
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
        return run_fixed(
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
    repo = Path(os.path.realpath(a.root))
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
