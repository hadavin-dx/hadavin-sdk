"""fill_flows: write a filled COPY of n8n flow files for a take, outside any git repo.

Replaces every `$env.DESK_*` / `$env.MF_*` token inside node strings with the literal value
from a KEY=VALUE file, and the six placeholder names when the values file carries them.
Stdlib only. Values are never printed or logged: messages name keys, files and line numbers
only. See README.md for the rules and exit codes.

Usage:
  fill_flows.py fill   --in DIR --values FILE --out DIR   (DIR for --out must not exist)
  fill_flows.py check  DIR [--tokens-only]                (read-only scan)
  fill_flows.py delete --out DIR [--force-hash] [--no-manifest] [--remove-others]

Needs Linux, macOS or WSL (Windows Subsystem for Linux, in its Linux home folder): it refuses
to start where the operating system cannot open files without following symlinks. It also
refuses to start on a Python older than 3.11 (the oldest version the tests were run on).
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import signal
import stat
import sys
import unicodedata

EXIT_OK = 0
EXIT_REFUSED = 1  # any refusal; usage errors from argparse are 2
EXIT_INCOMPLETE = 3  # fill wrote the copy, but placeholders are left: NOT READY TO IMPORT
EXIT_NOTHING = 4  # fill found no token at all (already filled, or the wrong folder)
EXIT_INTERRUPTED = 130  # Ctrl-C (the usual shell code: 128 + SIGINT)
HAS_NOFOLLOW = hasattr(os, "O_NOFOLLOW") and hasattr(os, "getuid")
MIN_PYTHON = (3, 11)
# Size limits: a flow file or manifest larger than this is refused instead of read into memory.
MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_VALUES_BYTES = 1024 * 1024
# Folders that a sync or backup program copies to other places: a values file or a filled copy
# must not sit there (checked on the folder names of the real path, lower case, start of name).
SYNCED_MARKS = (
    "dropbox",
    "onedrive",
    "icloud",
    "mobile documents",
    "com~apple~clouddocs",
    "cloudstorage",
    "google drive",
    "googledrive",
    "nextcloud",
    "owncloud",
    "pcloud",
    "box sync",
)

NAME_OK = re.compile(r"^(DESK|MF)_[A-Z0-9_]+$")
KEY_OK = re.compile(r"^[A-Z][A-Z0-9_]*$")
DIGITS = re.compile(r"^[0-9]+$")
TOKEN = re.compile(r"\$env(?:\.([A-Za-z_][A-Za-z0-9_]*)|\[\s*(['\"])([^'\"\]]*)\2\s*\])")
ANY_ENV = re.compile(r"\$env")
BRACES = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
# The six placeholder names: a node string that equals one of them exactly is a placeholder.
PLACEHOLDERS = (
    "PG_CREDENTIAL_ID",
    "SMTP_CREDENTIAL_ID",
    "SUB_WORKFLOW_ID",
    "HS_CRED_PLACEHOLDER",
    "FROM_ADDRESS_PLACEHOLDER",
    "INTAKE_ADDRESS_PLACEHOLDER",
)
# Any of the six names, also inside a longer string (counted as "left").
PH_RE = re.compile("|".join(PLACEHOLDERS))
# Node fields that hold program code: a token there would become a syntax error or worse.
CODE_KEYS = ("jsCode", "functionCode", "pythonCode")
MANIFEST_SUFFIX = ".manifest.json"
MANIFEST_FORMAT = "fill_flows-manifest-1"
# A small file written first into every output folder. `delete --no-manifest` needs it, so a
# lost fingerprint file cannot make an unrelated folder look like this tool's output.
MARKER_NAME = ".fill_flows-output"
MARKER_FORMAT = "fill_flows-output-1"
# Written into a copy that still holds placeholder names, so nobody imports it by mistake.
NOT_READY_NAME = "NOT-READY-DO-NOT-IMPORT.txt"
# Plain (not `=`) fields where a $env token may be filled. n8n does not evaluate a plain field,
# so a token there is only meaningful where the field is a literal address. The real v5 flows
# hold no token in a plain field at all (every token is inside an `={{ }}` expression), so this
# list is only room for new nodes; anywhere else a plain token is refused.
PLAIN_KEYS = ("url", "toEmail", "fromEmail", "ccEmail", "bccEmail")
DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _not_ready_bytes() -> bytes:
    return (
        b"NOT READY TO IMPORT.\n"
        b"fill_flows wrote this copy but placeholder names are still in the files.\n"
        b"Do not import it. Add the missing values, fill again into a new folder, and run check.\n"
    )


def _a(x) -> str:
    """A name from a file or a flow, safe to print (no control or look-alike characters)."""
    return ascii(str(x))[1:-1]


def _say(text: str = "", err: bool = False) -> None:
    """Print one line. A reader that has gone away (a closed pipe, `| head`) must not turn a
    finished run into a failure, so a write error here is ignored; the exit code still tells."""
    try:
        print(text, file=sys.stderr if err else sys.stdout, flush=True)
    except OSError:  # BrokenPipeError is an OSError
        pass


class Refused(Exception):
    """A refusal. The message never contains a value."""


# ---------------------------------------------------------------- values file


def _bad_char(ch: str) -> bool:
    return unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") or ch == "\x7f"


def under_mnt(path: str) -> bool:
    """True for a path on /mnt (a Windows drive mounted into Linux: file modes do not hold)."""
    rp = os.path.realpath(path)
    return rp == "/mnt" or rp.startswith("/mnt/")


def in_synced_folder(path: str) -> bool:
    """True when a folder name on the real path is a known sync or backup folder (Dropbox,
    OneDrive, iCloud Drive, Google Drive, ...): such a folder copies files to other places."""
    parts = os.path.realpath(path).split(os.sep)
    return any(p.lower().startswith(SYNCED_MARKS) for p in parts if p)


def _fd_path(fd: int, fallback: str) -> str:
    """The real place an OPEN file or folder lives, asked of the open handle (so a path swapped
    after the lexical checks cannot fool the next check). Linux: /proc/self/fd; macOS:
    F_GETPATH. Elsewhere the fallback (the checked path) is returned."""
    try:
        real = os.readlink(f"/proc/self/fd/{fd}")
        if real.startswith("/"):
            return real.removesuffix(" (deleted)")
    except OSError:
        pass
    try:
        import fcntl  # Unix only; imported here so the platform refusal can speak first

        if hasattr(fcntl, "F_GETPATH"):
            buf = fcntl.fcntl(fd, fcntl.F_GETPATH, b"\0" * 1024)
            real = os.fsdecode(buf.split(b"\0", 1)[0])
            if real.startswith("/"):
                return real
    except (ImportError, OSError):
        pass
    return fallback


def _check_open_place(fd: int, lexical: str, what: str) -> None:
    """Re-run the /mnt and git checks on the place the OPEN handle really is in."""
    real = _fd_path(fd, os.path.realpath(lexical))
    if under_mnt(real):
        raise Refused(f"{what} is under /mnt (Windows drive): file modes do not protect it")
    if inside_git(real):
        raise Refused(f"{what} is inside a git repository (a parent folder has .git)")
    if in_synced_folder(real):
        raise Refused(f"{what} is inside a cloud-synced or backed-up folder (it would be copied)")


class _Stopped(BaseException):
    """The tool was asked to stop by a signal (terminate or hang-up). It is raised so the
    clean-up runs; a kill that cannot be caught (SIGKILL, power loss) skips it."""


_STOP_SIGNALS = tuple(
    getattr(signal, n) for n in ("SIGINT", "SIGTERM", "SIGHUP") if hasattr(signal, n)
)


@contextlib.contextmanager
def _stop_signals():
    """While a fill or delete runs, a terminate or hang-up signal ends it through the normal
    clean-up path (like Ctrl-C does) instead of killing the process on the spot."""

    def handler(signum, _frame):
        raise _Stopped(signum)

    old: dict = {}
    try:
        for n in ("SIGTERM", "SIGHUP"):
            if hasattr(signal, n):
                old[getattr(signal, n)] = signal.signal(getattr(signal, n), handler)
    except ValueError:  # not the main thread: handlers cannot be set
        pass
    try:
        yield
    finally:
        for sig, prev in old.items():
            signal.signal(sig, prev)


@contextlib.contextmanager
def _sigint_blocked():
    """Hold Ctrl-C, terminate and hang-up back for a few lines, so 'create the file' and 'write
    it down for clean-up' (and the clean-up itself) cannot be split by them. A signal that comes
    in is delivered right after."""
    mask = getattr(signal, "pthread_sigmask", None)
    if mask is None:
        yield
        return
    old = mask(signal.SIG_BLOCK, set(_STOP_SIGNALS))
    try:
        yield
    finally:
        mask(signal.SIG_SETMASK, old)


def _read_capped(fh, cap: int, what: str) -> bytes:
    """Read a whole open file, but refuse one larger than `cap` bytes."""
    raw = fh.read(cap + 1)
    if len(raw) > cap:
        raise Refused(f"{what} is larger than {cap} bytes; nothing was done")
    return raw


def read_values(path: str) -> dict[str, str]:
    rp = os.path.realpath(path)
    if under_mnt(path):
        raise Refused("values file is under /mnt (Windows drive): file modes do not protect it")
    if inside_git(os.path.dirname(rp)):
        raise Refused("values file is inside a git repository (move it out; it holds secrets)")
    if in_synced_folder(rp):
        raise Refused(
            "values file is inside a cloud-synced or backed-up folder (it would be copied)"
        )
    try:
        # O_NONBLOCK: opening a pipe must not wait for a writer
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        raise Refused("values file: cannot open it (missing, a symlink, or not readable)") from None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise Refused("values file is not a regular file")
        real = _fd_path(fd, rp)  # the place of the OPEN file, in case the path was swapped
        if under_mnt(real):
            raise Refused("values file is under /mnt (Windows drive): file modes do not protect it")
        if inside_git(os.path.dirname(real)):
            raise Refused("values file is inside a git repository (move it out; it holds secrets)")
        if in_synced_folder(os.path.dirname(real)):
            raise Refused(
                "values file is inside a cloud-synced or backed-up folder (it would be copied)"
            )
        if st.st_uid != os.getuid():
            raise Refused(
                "values file is not owned by you (a file of another user cannot be trusted)"
            )
        if st.st_mode & 0o077:
            raise Refused("values file can be read by other users (run: chmod 600 on it)")
        with os.fdopen(fd, "rb") as fh:
            fd = -1
            raw = _read_capped(fh, MAX_VALUES_BYTES, "values file")
    except OSError:
        raise Refused("values file: cannot open it (missing, a symlink, or not readable)") from None
    finally:
        if fd >= 0:
            os.close(fd)
    if raw.startswith(b"\xef\xbb\xbf"):
        raise Refused("values file starts with a BOM (byte order mark): save it as plain UTF-8")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("values file: cannot read it as UTF-8 text") from None
    values: dict[str, str] = {}
    for no, line in enumerate(text.split("\n"), 1):
        if line.strip() == "" or line.lstrip().startswith("#"):
            continue
        if "=" not in line:
            raise Refused(f"values file line {no}: no '=' (expected KEY=VALUE)")
        key, value = line.split("=", 1)
        if not KEY_OK.match(key):
            raise Refused(f"values file line {no}: bad key name (A-Z, 0-9, _ only, no spaces)")
        if key in values:
            raise Refused(f"values file line {no}: key {key} appears twice")
        if any(_bad_char(c) for c in value):
            raise Refused(
                f"values file line {no}: value of {key} has a control or line-break "
                "character (Windows line ends count)"
            )
        if "$env" in value:
            raise Refused(f"values file line {no}: value of {key} contains '$env'")
        if value.startswith("="):
            raise Refused(
                f"values file line {no}: value of {key} starts with '=' (n8n would read the "
                "field as an expression)"
            )
        if key.endswith("_MS") and not DIGITS.match(value):
            raise Refused(f"values file line {no}: value of {key} must be digits only")
        if "{{" in value or "}}" in value:
            raise Refused(f"values file line {no}: value of {key} contains '{{{{' or '}}}}'")
        if value != value.strip():
            raise Refused(f"values file line {no}: value of {key} has a space at its start or end")
        if value[:1] in ("'", '"') or value[-1:] in ("'", '"'):
            raise Refused(
                f"values file line {no}: value of {key} starts or ends with a quote mark "
                "(write the value without quotes; quotes are not removed)"
            )
        if " #" in value:
            _say(
                f"warning: values file line {no}: value of {key} contains ' #'; it is kept as "
                "part of the value (there are no inline comments)",
                err=True,
            )
        if key.endswith("_URL") and value.endswith("/"):
            _say(
                f"warning: values file line {no}: value of {key} ends with '/'; the flows add "
                "their own '/path', so the address would get a double slash",
                err=True,
            )
        values[key] = value
    return values


# ---------------------------------------------------------------- substitution


ESCAPE = re.compile(r"\\u\{([0-9a-fA-F]{1,6})\}|\\u([0-9a-fA-F]{4})|\\x([0-9a-fA-F]{2})")


def _unescaped(s: str) -> str:
    """The text with JavaScript \\uXXXX, \\u{X} and \\xXX escapes decoded: n8n might read an
    identifier written this way as the same name, so `$env` could hide behind an escape."""

    def one(m: re.Match) -> str:
        try:
            return chr(int(m.group(1) or m.group(2) or m.group(3), 16))
        except (ValueError, OverflowError):
            return m.group(0)

    return ESCAPE.sub(one, s)


def _js_literal(value: str) -> str:
    """JS double-quoted string literal. ASCII only; braces escaped so '}}' cannot end the
    n8n expression early."""
    return json.dumps(value, ensure_ascii=True).replace("{", "\\u007b").replace("}", "\\u007d")


TEMPLATE = (
    "a $env token sits in an expression that holds a backtick or '${' (a template string; "
    "not filled)"
)
QUOTED = "a $env token sits inside a quoted JS string in an expression (not filled; edit the flow)"
OUTSIDE = "a $env token sits outside a clean {{ }} part of an expression (not filled)"


class Subst:
    def __init__(self, values: dict[str, str]):
        self.values = values
        self.used: set[str] = set()
        self.ph_used: set[str] = set()
        self.bad: set[str] = set()  # names we cannot fill (not DESK_/MF_, missing, empty)
        self.empty_ph: set[str] = set()  # placeholder names whose value is empty: left as they are

    def _name(self, m: re.Match) -> str:
        return m.group(1) or m.group(3)

    def _repl(self, m: re.Match, as_js: bool) -> str:
        name = self._name(m)
        if not NAME_OK.match(name or "") or not self.values.get(name):
            self.bad.add(name or "<empty>")
            return m.group(0)
        self.used.add(name)
        v = self.values[name]
        return _js_literal(v) if as_js else v

    def _expr_part(self, part: str) -> str:
        """Text between '{{' and '}}': fill tokens outside JS strings, refuse inside them."""
        out: list[str] = []
        i, quote, comment, hit, slash = 0, None, False, False, False
        while i < len(part):
            m = TOKEN.match(part, i)
            if m:
                if quote is not None:
                    raise Refused(QUOTED)
                before = part[:i].rstrip()[-1:]
                if before and (before.isalnum() or before in "_$."):
                    raise Refused(
                        "a $env token follows a name character or a dot (a different name such "
                        "as a$env or x.$env, not the n8n one; not filled)"
                    )
                hit = True
                out.append(self._repl(m, True))
                i = m.end()
                continue
            ch = part[i]
            if quote is not None:
                if ch == "\\":
                    out.append(part[i : i + 2])
                    i += 2
                    continue
                if ch == quote:
                    quote = None
            elif ch in "'\"`":
                quote = ch
            elif part.startswith(("//", "/*"), i):
                comment = True
            elif ch == "/":
                slash = True
            out.append(ch)
            i += 1
        if hit and ("`" in part or "${" in part):
            raise Refused(TEMPLATE)
        if hit and comment:
            raise Refused("a $env token sits in an expression that holds a // or /* comment")
        if hit and slash:
            raise Refused(
                "a $env token sits in an expression with a '/' outside a string "
                "(a division or a regex literal; not filled)"
            )
        return "".join(out)

    def _expr(self, s: str) -> str:
        out: list[str] = []
        pos = 0
        for m in BRACES.finditer(s):
            outside = s[pos : m.start()]
            if "$env" in outside or "{{" in outside or "}}" in outside or "{{" in m.group(1):
                raise Refused(OUTSIDE)
            out.append(outside + "{{" + self._expr_part(m.group(1)) + "}}")
            pos = m.end()
        tail = s[pos:]
        if "$env" in tail or "{{" in tail or "}}" in tail:
            raise Refused(OUTSIDE)
        return "".join(out) + tail

    def string(self, s: str, ctx: str | None = None, field: str | None = None) -> str:
        if s in PLACEHOLDERS and s in self.values:
            if ctx in CODE_KEYS:
                raise Refused(
                    f"a placeholder name sits in a {ctx} field (program code; not filled)"
                )
            if not self.values[s]:  # an empty value is the same as no value: the name stays
                self.empty_ph.add(s)
                return s
            self.ph_used.add(s)
            return self.values[s]
        if "$env" not in s:
            if "$env" in _unescaped(s):
                raise Refused("a $env name is written with an escape (\\u or \\x form; not filled)")
            return s
        if ctx in CODE_KEYS:
            raise Refused(f"a $env token sits in a {ctx} field (program code; not filled)")
        if not s.startswith("="):  # plain field: n8n does not evaluate it
            if field not in PLAIN_KEYS:
                where = "a key name" if field is None else f"the field {_a(field)}"
                raise Refused(
                    f"a $env token sits in a plain text ({where}); plain fields are filled only "
                    f"in: {', '.join(PLAIN_KEYS)}"
                )
            return TOKEN.sub(lambda m: self._repl(m, False), s)
        return self._expr(s)

    def walk(self, o, ctx: str | None = None, field: str | None = None):
        """`ctx`: the code key above (if any); `field`: the nearest key above this value."""
        if isinstance(o, dict):
            out = {}
            for k, v in o.items():
                nk = self.string(k)
                if nk in out:
                    raise Refused("two keys of one object become the same key after filling")
                out[nk] = self.walk(v, k if k in CODE_KEYS else ctx, k)
            return out
        if isinstance(o, list):
            return [self.walk(v, ctx, field) for v in o]
        if isinstance(o, str):
            return self.string(o, ctx, field)
        return o


def iter_strings(o):
    """Every string and every dict key in a parsed JSON value."""
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from iter_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from iter_strings(v)
    elif isinstance(o, str):
        yield o


def _no_const(_name):
    raise ValueError("NaN or Infinity")


def _no_float(text):
    value = float(text)
    if value in (float("inf"), float("-inf")):  # 1e999 reads as infinity, which JSON cannot hold
        raise ValueError("number too large")
    return value


def load_json(raw: bytes):
    return json.loads(raw.decode("utf-8"), parse_constant=_no_const, parse_float=_no_float)


def dump(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def shape(obj) -> tuple[int, dict]:
    nodes = obj.get("nodes", []) if isinstance(obj, dict) else []
    return len(nodes), (obj.get("connections", {}) if isinstance(obj, dict) else {})


# ---------------------------------------------------------------- file helpers


def sha256_at(name: str, dir_fd: int) -> str:
    # O_NONBLOCK: opening a pipe (FIFO) put in the place of a file must not wait for a writer
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    h = hashlib.sha256()
    with os.fdopen(fd, "rb") as fh:
        if not stat.S_ISREG(os.fstat(fh.fileno()).st_mode):
            raise OSError("not a regular file")
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def list_json(directory: str) -> list[str]:
    if os.path.islink(directory) or not os.path.isdir(directory):
        raise Refused("input folder: not a real folder (missing, or a symlink)")
    names = sorted(n for n in os.listdir(directory) if n.lower().endswith(".json"))
    for n in names:
        p = os.path.join(directory, n)
        if not n.endswith(".json"):
            raise Refused(f"input file {_a(n)}: the ending must be lower case .json")
        if os.path.islink(p) or not os.path.isfile(p):
            raise Refused(f"input file {_a(n)}: symlink or not a regular file")
    return names


def read_json_file(directory: str, n: str):
    try:
        fd = os.open(os.path.join(directory, n), os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as fh:
            return load_json(_read_capped(fh, MAX_JSON_BYTES, _a(n)))
    except (OSError, ValueError, RecursionError) as e:
        raise Refused(f"{_a(n)}: not valid JSON ({type(e).__name__})") from None


def inside_git(path: str) -> bool:
    p = os.path.realpath(path)
    while True:
        if os.path.lexists(os.path.join(p, ".git")):
            return True
        parent = os.path.dirname(p)
        if parent == p:
            return False
        p = parent


def _write_new(name: str, data: bytes, dir_fd: int, created: list | None = None) -> None:
    """Create `name` inside the open folder `dir_fd` (never through a path that could be
    swapped), then check on the open file that it really is 0600 and ours: on a disk that
    ignores file modes this refuses and leaves nothing. The new file is added to `created`
    (the clean-up list) in the same step as its creation, with Ctrl-C held back, so no
    interrupt can leave a file that the clean-up does not know."""
    with _sigint_blocked():
        fd = os.open(
            name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dir_fd
        )
        if created is not None:
            created.append((dir_fd, name))
    try:
        os.fchmod(fd, 0o600)
        st = os.fstat(fd)
        if st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o600:
            raise Refused(
                "file modes do not hold on this disk (a new file is not private); "
                "use a folder on a normal Linux or macOS disk"
            )
        with os.fdopen(fd, "wb") as fh:
            fd = -1
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
    except BaseException:
        # the file is ours (O_EXCL made it): remove it so a re-run is not blocked by a stub
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(name, dir_fd=dir_fd)
        except OSError:
            pass  # the entry stays in `created`: the clean-up retries and reports it
        else:
            if created is not None and (dir_fd, name) in created:
                created.remove((dir_fd, name))
        raise


def _check_parent_links(parent: str) -> None:
    """Refuse a parent path that goes through a symlink made by another user. A link owned by
    you or by root (for example /tmp on macOS) is accepted: its target is still checked for
    /mnt and for git, and the files are 0600 in a 0700 folder."""
    me = os.getuid()
    p = os.path.abspath(parent)
    while True:
        try:
            st = os.lstat(p)
        except OSError:
            st = None
        if st is not None and stat.S_ISLNK(st.st_mode) and st.st_uid not in (me, 0):
            raise Refused("a folder in the output path is a symlink made by another user")
        up = os.path.dirname(p)
        if up == p:
            return
        p = up


# ---------------------------------------------------------------- modes


_CANNOT_FILL = (
    "cannot fill these names (missing or empty in the values file, or not a DESK_/MF_ name): "
)


def _plain_name(n) -> bool:
    return isinstance(n, str) and n not in ("", ".", "..") and not any(c in n for c in "/\\\0")


def _clean_file_name(n) -> bool:
    """A file name safe to carry into the output and the manifest: one plain name, no control,
    look-alike or lone-surrogate characters."""
    return _plain_name(n) and not any(_bad_char(c) or unicodedata.category(c) == "Cs" for c in n)


def _marker_bytes(folder_name: str) -> bytes:
    return f"{MARKER_FORMAT}\n{folder_name}\n".encode("utf-8", "surrogateescape")


def do_fill(in_dir: str, values_path: str, out_dir: str, allow_placeholders: bool = False) -> int:
    out_dir = os.path.abspath(out_dir.rstrip("/") or "/")
    manifest_path = out_dir + MANIFEST_SUFFIX
    if under_mnt(os.path.dirname(out_dir)) or under_mnt(out_dir):
        raise Refused("output path is under /mnt (Windows drive): file modes do not protect it")
    _check_parent_links(os.path.dirname(out_dir))
    if inside_git(os.path.dirname(out_dir)):
        raise Refused("output path is inside a git repository (a parent folder has .git)")
    if in_synced_folder(os.path.dirname(out_dir)):
        raise Refused(
            "output path is inside a cloud-synced or backed-up folder (it would be copied)"
        )
    if os.path.lexists(out_dir) or os.path.lexists(manifest_path):
        raise Refused(
            "output folder or its manifest already exists (run delete --out on it first; add "
            "--force-hash if a kill cut the manifest short)"
        )
    if not os.path.isdir(os.path.dirname(out_dir)):
        raise Refused("output parent folder does not exist")
    rin, rout = os.path.realpath(in_dir), os.path.realpath(out_dir)
    if rout == rin or rout.startswith(rin.rstrip(os.sep) + os.sep):
        raise Refused("output folder is the input folder or inside it")

    if not _clean_file_name(os.path.basename(out_dir)):
        raise Refused("output folder name is not a plain name (path or control character)")
    values = read_values(values_path)
    names = list_json(in_dir)
    if not names:
        raise Refused("input folder has no .json files")
    for n in names:
        if not _clean_file_name(n):
            raise Refused(f"input file {_a(n)}: the name holds a path or control character")
    sub = Subst(values)
    outputs: dict[str, bytes] = {}
    found_any = False
    ph_left = 0
    for n in names:
        obj = read_json_file(in_dir, n)
        before = shape(obj)
        if any(ANY_ENV.search(_unescaped(t)) for t in iter_strings(obj)):
            found_any = True
        try:
            new = sub.walk(obj)
        except Refused as e:
            raise Refused(f"{_a(n)}: {e}") from None
        if shape(new) != before:
            raise Refused(f"{_a(n)}: node count or connections changed (internal check)")
        if sub.bad:
            bad_names = ", ".join(_a(b) for b in sorted(sub.bad))
            raise Refused(f"{_a(n)}: " + _CANNOT_FILL + bad_names)
        data = dump(new)
        if ANY_ENV.search(_unescaped(data.decode("utf-8"))):
            raise Refused(f"{_a(n)}: a $env token is left after substitution (dynamic or odd form)")
        ph_left += sum(len(PH_RE.findall(t)) for t in iter_strings(new))
        outputs[n] = data
    if not found_any and not sub.ph_used:
        _say(
            "nothing to fill: no $env token in the input (already filled, or wrong folder)",
            err=True,
        )
        return EXIT_NOTHING
    if ph_left and not allow_placeholders:
        raise Refused(
            f"{ph_left} placeholder name(s) would be left in the copy because the values file "
            "has no value for them; add the values, or add --allow-placeholders to write a "
            "copy that is marked NOT READY (for the credential walk-through); nothing written"
        )
    for k in sorted(sub.empty_ph):
        _say(f"warning: key {k} is empty in the values file; the placeholder stays", err=True)
    for k in sorted(set(values) - sub.used - sub.ph_used - sub.empty_ph):
        _say(f"warning: key {k} in the values file is not used by any node", err=True)

    folder_name = os.path.basename(out_dir)
    marker = _marker_bytes(folder_name)
    hashes = {n: hashlib.sha256(d).hexdigest() for n, d in outputs.items()}
    hashes[MARKER_NAME] = hashlib.sha256(marker).hexdigest()
    # the not-ready note is always listed: it is written first and removed last (a copy that
    # was cut short by a kill is then still marked), so `delete` must know it
    hashes[NOT_READY_NAME] = hashlib.sha256(_not_ready_bytes()).hexdigest()
    manifest = {"format": MANIFEST_FORMAT, "files": dict(sorted(hashes.items()))}
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    manifest_name = folder_name + MANIFEST_SUFFIX
    created: list[tuple[int, str]] = []  # (open folder, name) in creation order
    pfd = os.open(os.path.dirname(out_dir), DIR_FLAGS & ~os.O_NOFOLLOW)
    dfd = -1
    made_dir = False
    try:
        # the paths were checked by name above; check again on the folder we really opened
        _check_open_place(pfd, os.path.dirname(out_dir), "output path")
        # the manifest goes first: if this stops half way, `delete` can still find every file
        _write_new(manifest_name, manifest_bytes, pfd, created)
        with _sigint_blocked():  # the folder and the note that it exists, in one step
            os.mkdir(folder_name, 0o700, dir_fd=pfd)
            made_dir = True
        dfd = os.open(folder_name, DIR_FLAGS, dir_fd=pfd)
        _check_open_place(dfd, out_dir, "output folder")
        os.fchmod(dfd, 0o700)
        dst = os.fstat(dfd)
        if dst.st_uid != os.getuid() or stat.S_IMODE(dst.st_mode) != 0o700:
            raise Refused(
                "file modes do not hold on this disk (the new folder is not private); "
                "use a folder on a normal Linux or macOS disk"
            )
        # the "not ready" note goes in first and comes out last: a copy cut short by a kill
        # that nothing can catch is still marked, and `check` refuses a folder with the note
        _write_new(NOT_READY_NAME, _not_ready_bytes(), dfd, created)
        _write_new(MARKER_NAME, marker, dfd, created)
        for n, d in outputs.items():
            _write_new(n, d, dfd, created)
        if not ph_left:
            with _sigint_blocked():
                os.unlink(NOT_READY_NAME, dir_fd=dfd)
                created.remove((dfd, NOT_READY_NAME))
    except BaseException:
        left: list[str] = []  # what the clean-up could not remove
        with _sigint_blocked():  # a second Ctrl-C must not cut the clean-up short
            for fd, nm in reversed(created):
                try:
                    os.unlink(nm, dir_fd=fd)
                except FileNotFoundError:
                    pass
                except OSError:
                    left.append(nm)
            if made_dir:
                try:
                    os.rmdir(folder_name, dir_fd=pfd)
                except FileNotFoundError:
                    pass
                except OSError:
                    left.append(folder_name + "/")
        if left:
            _say(
                "clean-up did not finish; left behind: "
                + ", ".join(_a(x) for x in left)
                + "; run delete --out on the output folder (add --force-hash if needed)",
                err=True,
            )
        raise
    finally:
        if dfd >= 0:
            os.close(dfd)
        os.close(pfd)
    _say(f"filled {len(outputs)} files, {len(sub.used)} names and {len(sub.ph_used)} placeholders")
    if ph_left:
        _say(
            f"NOT READY TO IMPORT: {ph_left} placeholders left "
            f"(the folder holds {NOT_READY_NAME}; create the credentials, import the sub-flow, "
            "fill again, then run check)",
            err=True,
        )
        return EXIT_INCOMPLETE
    _say("no placeholders left; run check before importing")
    return EXIT_OK


def _marked_folder_problems(dfd: int, folder_name: str, present: set) -> int:
    """For a folder that carries this tool's marker: the marker must be this tool's and name
    this folder (a renamed or copied folder fails), and the folder and files must still be
    private (mode 0700 and 0600, yours): `cp -r` or a restore can loosen them."""
    me = os.getuid()
    bad = 0
    ms = _lstat_or_none(MARKER_NAME, dfd)
    if ms is None or not stat.S_ISREG(ms.st_mode):
        _say(f"{MARKER_NAME}: not a plain file")
        bad += 1
    else:
        try:
            same = _read_at(MARKER_NAME, dfd) == _marker_bytes(folder_name)
        except OSError:
            same = False
        if not same:
            _say(
                f"{MARKER_NAME}: does not name this folder (the folder was renamed or copied; "
                "fill again instead of copying)"
            )
            bad += 1
    fs = os.fstat(dfd)
    if fs.st_uid != me or stat.S_IMODE(fs.st_mode) != 0o700:
        _say("the folder is not mode 0700 and yours (a copy can loosen it; run chmod 700)")
        bad += 1
    for n in sorted(present):
        ls = _lstat_or_none(n, dfd)
        loose = ls is not None and stat.S_ISREG(ls.st_mode)
        if loose and (ls.st_uid != me or stat.S_IMODE(ls.st_mode) != 0o600):
            _say(f"{_a(n)}: not mode 0600 and yours (a copy can loosen it; run chmod 600)")
            bad += 1
    return bad


def _check_output_folder(directory: str) -> int:
    """Checks that only make sense for a folder that `fill` wrote: the marker file, the modes,
    and the comparison with the manifest (the fingerprint file) that sits next to the folder.
    Always says whether the comparison ran. Returns the number of problems. A folder with no
    marker and no manifest (an input folder) has nothing of this kind to check."""
    d = os.path.abspath(directory.rstrip("/") or "/")
    folder_name = os.path.basename(d)
    manifest_name = folder_name + MANIFEST_SUFFIX
    bad = 0
    try:
        pfd = os.open(os.path.dirname(d), DIR_FLAGS & ~os.O_NOFOLLOW)
    except OSError:
        _say("folder check: the parent folder cannot be opened, so nothing was compared")
        return 1
    try:
        dfd = os.open(folder_name, DIR_FLAGS, dir_fd=pfd)
    except OSError:
        os.close(pfd)
        _say("folder check: the folder cannot be opened, so nothing was compared")
        return 1
    try:
        present = set(os.listdir(dfd))
        marked = MARKER_NAME in present
        if marked:
            bad += _marked_folder_problems(dfd, folder_name, present)
        if _lstat_or_none(manifest_name, pfd) is None:
            if marked:
                _say(
                    f"{_a(manifest_name)}: not next to the folder, so the folder was NOT compared "
                    "with it (a copied or moved folder, or the file was lost); it cannot be "
                    "shown unchanged"
                )
                bad += 1
            else:
                _say(
                    "manifest compare: not run (no fingerprint file next to the folder and no "
                    "marker file: an input folder has neither)"
                )
            return bad
        try:
            files = _load_manifest(manifest_name, pfd)
        except Refused as e:
            _say(f"manifest: {e}")
            return bad + 1
        for n in sorted(present - set(files)):
            _say(f"{_a(n)}: not in the manifest (a file that fill did not write)")
            bad += 1
        for n, h in sorted(files.items()):
            if n not in present:
                if n != NOT_READY_NAME:
                    _say(f"{_a(n)}: listed in the manifest but missing")
                    bad += 1
                continue
            try:
                same = sha256_at(n, dfd) == h
            except OSError:
                same = False
            if not same:
                _say(f"{_a(n)}: differs from the manifest (changed since fill wrote it)")
                bad += 1
        _say(f"manifest compare: ran against {_a(manifest_name)}")
    except OSError:
        _say("folder check: the folder cannot be read, so it was not fully compared")
        bad += 1
    finally:
        os.close(dfd)
        os.close(pfd)
    return bad


def do_check(directory: str, tokens_only: bool) -> int:
    names = list_json(directory)
    if not names:
        if os.path.lexists(os.path.join(directory, NOT_READY_NAME)):
            raise Refused(
                f"no .json files in the folder (nothing was checked), and {NOT_READY_NAME} is in "
                "it: this is a copy that fill left unfinished (placeholders left, or a kill); "
                "do not import it; run delete --out on it"
            )
        raise Refused("no .json files in the folder (nothing was checked)")
    bad = _check_output_folder(directory)
    for n in names:
        try:
            obj = read_json_file(directory, n)
        except Refused as e:
            _say(f"{_a(n)}: {e}")
            bad += 1
            continue
        ph: dict[str, int] = {}
        for text in iter_strings(obj):
            for m in TOKEN.finditer(text):
                _say(f"{_a(n)}: token $env {_a(m.group(1) or m.group(3))}")
                bad += 1
            c = len(ANY_ENV.findall(_unescaped(TOKEN.sub("", text))))
            if c:
                _say(f"{_a(n)}: {c} other $env use(s) (dynamic form)")
                bad += c
            for name in PH_RE.findall(text):
                ph[name] = ph.get(name, 0) + 1
        if not tokens_only:
            for p, c in sorted(ph.items()):
                _say(f"{_a(n)}: placeholder {p} x{c}")
                bad += c
    if tokens_only:
        _say("placeholders: not checked (--tokens-only); the copy may still be NOT READY")
    if os.path.lexists(os.path.join(directory, NOT_READY_NAME)):
        _say(f"{NOT_READY_NAME} is in the folder: fill left placeholders; do not import")
        bad += 1
    _say(f"check: {len(names)} files, {bad} problem(s)")
    return EXIT_REFUSED if bad else EXIT_OK


def _load_manifest(manifest_name: str, pfd: int) -> dict:
    try:
        fd = os.open(manifest_name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=pfd)
        with os.fdopen(fd, "rb") as fh:
            man = json.loads(_read_capped(fh, MAX_JSON_BYTES, "manifest").decode("utf-8"))
        files = man["files"]
        if man.get("format") != MANIFEST_FORMAT or not isinstance(files, dict):
            raise ValueError
    except (OSError, ValueError, KeyError, AttributeError, TypeError, RecursionError):
        raise Refused("manifest is not a valid fill_flows manifest; nothing deleted") from None
    for n, h in files.items():
        if not _plain_name(n):
            raise Refused("manifest names a path that is not a plain file name; nothing deleted")
        if not isinstance(h, str):
            raise Refused("manifest has a bad hash entry; nothing deleted")
    return files


def _read_at(name: str, dir_fd: int) -> bytes:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    with os.fdopen(fd, "rb") as fh:
        return _read_capped(fh, MAX_JSON_BYTES, _a(name))


def _lstat_or_none(name: str, dir_fd: int):
    try:
        return os.lstat(name, dir_fd=dir_fd)
    except FileNotFoundError:
        return None


def _signature_ok(dfd: int, folder_name: str, present: set, force_hash: bool) -> None:
    """Without a manifest, delete only a folder that looks exactly like this tool's output:
    the folder 0700 and the files 0600, all owned by the current user, the marker file this
    tool writes first (right format and this folder's name), and plain .json files that parse
    as JSON and hold no $env text. Anything else is refused (nothing is deleted)."""
    me = os.getuid()
    st = os.fstat(dfd)
    if st.st_uid != me or stat.S_IMODE(st.st_mode) != 0o700:
        raise Refused(
            "no manifest, and the folder is not marked as this tool's output (it must be "
            "mode 0700 and yours); nothing deleted"
        )
    if MARKER_NAME not in present:
        raise Refused(
            "no manifest, and the folder has no marker file written by this tool "
            f"({MARKER_NAME}); nothing deleted"
        )
    for n in sorted(present):
        ls = os.lstat(n, dir_fd=dfd)
        own = (MARKER_NAME, NOT_READY_NAME)
        if not stat.S_ISREG(ls.st_mode) or not (n in own or n.endswith(".json")):
            raise Refused(f"{_a(n)}: not a plain .json file; nothing deleted")
        if ls.st_uid != me or stat.S_IMODE(ls.st_mode) != 0o600:
            raise Refused(
                f"{_a(n)}: not marked as this tool's output (mode 0600, yours); nothing deleted"
            )
        try:
            raw = _read_at(n, dfd)
        except OSError:
            raise Refused(f"{_a(n)}: cannot be read; nothing deleted") from None
        if n == MARKER_NAME:
            if raw != _marker_bytes(folder_name):
                raise Refused("the marker file is not this tool's, or is for another folder name")
            continue
        if n == NOT_READY_NAME:
            if raw != _not_ready_bytes():
                raise Refused("the not-ready note is not this tool's; nothing deleted")
            continue
        if force_hash:
            continue
        try:
            text = raw.decode("utf-8")
            load_json(raw)
        except ValueError:  # UnicodeDecodeError is a ValueError
            raise Refused(
                f"{_a(n)}: does not parse as JSON (a file cut short by a kill needs "
                "--force-hash); nothing deleted"
            ) from None
        if ANY_ENV.search(text):
            raise Refused(f"{_a(n)}: holds $env text (looks like an input folder); nothing deleted")


def _stray_files(dfd: int, extra: list, me: int, remove_others: bool, why: str) -> list:
    """Files in the folder that the manifest does not list. Without --remove-others they stop
    the delete (named, so a person can look). With it, a plain file that is yours is taken
    along (a .DS_Store or an editor's .swp file); anything else still stops the delete."""
    if not extra:
        return []
    if not remove_others:
        raise Refused(
            f"folder holds files {why}: {', '.join(_a(e) for e in extra)}; nothing deleted "
            "(stray plain files of yours, such as .DS_Store, go with --remove-others)"
        )
    for n in extra:
        ls = os.lstat(n, dir_fd=dfd)
        if not stat.S_ISREG(ls.st_mode) or ls.st_uid != me:
            raise Refused(
                f"{_a(n)}: not a plain file of yours, so --remove-others does not remove it; "
                "nothing deleted"
            )
    return list(extra)


def _folder_left_behind(dfd: int, folder_name: str, has_man: bool) -> Refused:
    """The message when the folder could not be removed at the end (a file appeared)."""
    try:
        names = ", ".join(_a(x) for x in sorted(os.listdir(dfd))) or "nothing I can see"
    except OSError:
        names = "unknown"
    hint = (
        "run delete again (add --remove-others for stray files of yours)"
        if has_man
        else "look at it and remove it by hand"
    )
    return Refused(
        f"folder left behind: {_a(folder_name)} (it holds: {names}); the files this tool "
        f"listed were removed; {hint}"
    )


def do_delete(
    out_dir: str, force_hash: bool, no_manifest: bool = False, remove_others: bool = False
) -> int:
    out_dir = os.path.abspath(out_dir.rstrip("/") or "/")
    parent = os.path.dirname(out_dir)
    folder_name = os.path.basename(out_dir)
    manifest_name = folder_name + MANIFEST_SUFFIX
    _check_parent_links(parent)
    try:
        pfd = os.open(parent, DIR_FLAGS & ~os.O_NOFOLLOW)
    except OSError:
        raise Refused("output parent folder cannot be opened; nothing deleted") from None
    dfd = -1
    me = os.getuid()
    try:
        dst = _lstat_or_none(folder_name, pfd)
        mst = _lstat_or_none(manifest_name, pfd)
        has_dir, has_man = dst is not None, mst is not None
        if has_dir and not stat.S_ISDIR(dst.st_mode):
            raise Refused("output folder is a symlink or not a folder; nothing deleted")
        if has_man and not stat.S_ISREG(mst.st_mode):
            raise Refused("manifest is a symlink or not a file; nothing deleted")
        if not has_dir and not has_man:
            _say("nothing to delete: the output folder and its manifest are both missing")
            return EXIT_OK
        files: dict = {}
        if not no_manifest and not has_man:
            raise Refused(
                "manifest is missing; nothing deleted (to remove the folder anyway, use "
                "--no-manifest: it removes only the marker, the not-ready note and .json files "
                "that look like this tool's output: mode 0600, yours, valid JSON)"
            )
        manifest_loaded = False
        if has_man:
            # A manifest we rely on or remove must be valid, unless --force-hash says the person
            # knows it is cut short (a kill during its write); then it must at least be a plain
            # file of ours.
            if force_hash and (no_manifest or not has_dir):
                if mst.st_uid != me:
                    raise Refused("manifest is not owned by you; nothing deleted")
                if no_manifest:  # a manifest that still reads fine is still the list to keep to
                    with contextlib.suppress(Refused):
                        files = _load_manifest(manifest_name, pfd)
                        manifest_loaded = True
            else:
                files = _load_manifest(manifest_name, pfd)
                manifest_loaded = True
        if not has_dir:  # a fill was stopped after the manifest and before the folder
            os.unlink(manifest_name, dir_fd=pfd)
            _say("deleted the manifest (the folder was not there)")
            return EXIT_OK
        try:
            dfd = os.open(folder_name, DIR_FLAGS, dir_fd=pfd)
        except OSError:
            raise Refused("output folder is a symlink or not a folder; nothing deleted") from None
        present = set(os.listdir(dfd))
        todo: list[str] = []
        others: list[str] = []
        if no_manifest:
            if manifest_loaded:  # a good manifest exists: the folder must hold nothing beyond it
                others = _stray_files(
                    dfd, sorted(present - set(files)), me, remove_others, "not in the manifest"
                )
            elif remove_others:  # no list to keep to: every plain file that is not ours goes
                own = (MARKER_NAME, NOT_READY_NAME)
                stray = sorted(n for n in present if n not in own and not n.endswith(".json"))
                others = _stray_files(dfd, stray, me, True, "")
            _signature_ok(dfd, folder_name, present - set(others), force_hash)
            todo = sorted(present - set(others))
        else:
            if os.fstat(dfd).st_uid != me:
                raise Refused("output folder is not owned by you; nothing deleted")
            others = _stray_files(
                dfd, sorted(present - set(files)), me, remove_others, "not in the manifest"
            )
            for n, h in sorted(files.items()):
                ls = _lstat_or_none(n, dfd)
                if ls is None:
                    continue
                if not stat.S_ISREG(ls.st_mode):
                    raise Refused(f"{_a(n)}: symlink or not a regular file; nothing deleted")
                if ls.st_uid != me:
                    raise Refused(f"{_a(n)}: not owned by you; nothing deleted")
                if sha256_at(n, dfd) != h and not force_hash:
                    raise Refused(
                        f"{_a(n)}: content changed since it was written (use --force-hash); "
                        "nothing deleted"
                    )
                todo.append(n)
        # the not-ready note and the marker go last: a delete that is cut short leaves a folder
        # that is still marked, so a re-run finds it and `check` still refuses it
        last = (NOT_READY_NAME, MARKER_NAME)
        todo = others + [n for n in todo if n not in last] + [n for n in last if n in todo]
        done = False
        held = False
        try:
            with _sigint_blocked():
                for n in todo:
                    os.unlink(n, dir_fd=dfd)
                try:
                    os.rmdir(folder_name, dir_fd=pfd)
                except OSError:
                    raise _folder_left_behind(dfd, folder_name, has_man) from None
                if has_man:
                    os.unlink(manifest_name, dir_fd=pfd)
                done = True
        except (_Stopped, KeyboardInterrupt):
            # a stop that came in while the removal was shielded is delivered right after it;
            # if the removal had finished, say so instead of reporting a refusal
            if not done:
                raise
            held = True
        count = len([n for n in todo if n not in (MARKER_NAME, NOT_READY_NAME, *others)])
        _say(f"deleted {count} files, the folder and the manifest")
        if others:
            _say(f"also removed {len(others)} other file(s): {', '.join(_a(o) for o in others)}")
        if held:
            _say(
                "a stop signal came in while the removal ran; it was held until the removal was "
                "finished, so nothing is left"
            )
        return EXIT_OK
    finally:
        if dfd >= 0:
            os.close(dfd)
        os.close(pfd)


def main(argv=None) -> int:
    if sys.version_info < MIN_PYTHON:
        _say(
            f"refused: this needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer (the oldest "
            "version the tests were run on); nothing was done",
            err=True,
        )
        return EXIT_REFUSED
    if not HAS_NOFOLLOW:
        _say(
            "refused: this needs Linux, macOS or WSL (it must open files without following "
            "symlinks, which this system cannot do); nothing was done",
            err=True,
        )
        return EXIT_REFUSED
    ap = argparse.ArgumentParser(prog="fill_flows", description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="mode", required=True)
    f = sp.add_parser("fill")
    f.add_argument("--in", dest="in_dir", required=True)
    f.add_argument("--values", required=True)
    f.add_argument("--out", required=True)
    f.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="write a copy marked NOT READY when placeholder values are missing",
    )
    c = sp.add_parser("check")
    c.add_argument("dir")
    c.add_argument("--tokens-only", action="store_true", help="do not list placeholders")
    d = sp.add_parser("delete")
    d.add_argument("--out", required=True)
    d.add_argument("--force-hash", action="store_true")
    d.add_argument("--no-manifest", action="store_true", help="folder has no usable manifest")
    d.add_argument(
        "--remove-others",
        action="store_true",
        help="also remove stray plain files of yours that the manifest does not list",
    )
    a = ap.parse_args(argv)
    try:
        with _stop_signals():
            if a.mode == "fill":
                return do_fill(a.in_dir, a.values, a.out, a.allow_placeholders)
            if a.mode == "check":
                return do_check(a.dir, a.tokens_only)
            return do_delete(a.out, a.force_hash, a.no_manifest, a.remove_others)
    except _Stopped:
        _say(
            "refused: stopped by a signal; if a line above says something was left behind, "
            "run delete --out on that folder",
            err=True,
        )
        return EXIT_REFUSED
    except Refused as e:
        _say(f"refused: {e}", err=True)
        return EXIT_REFUSED
    except RecursionError:
        _say("refused: a file is nested too deeply to read; nothing was written", err=True)
        return EXIT_REFUSED

    # Any other error is not caught here: the command-line entry (run) reports it by its type
    # name only, because the text of an unexpected error could carry a path or a value.


def _quiet_hook(exc_type, _exc, _tb) -> None:
    """Report an unexpected error by its type name only (never the text or a traceback: they
    could carry a path or a value). Python then exits with code 1."""
    _say(f"failed: {exc_type.__name__}", err=True)


def run() -> int:
    """The command-line entry: like main, but an unexpected error is reported by type name
    only, and Ctrl-C ends with one plain line and the usual exit code 130 (no traceback)."""
    sys.excepthook = _quiet_hook
    try:
        return main()
    except KeyboardInterrupt:
        _say(
            "refused: stopped by Ctrl-C; if a line above says something was left behind, "
            "run delete --out on that folder",
            err=True,
        )
        return EXIT_INTERRUPTED


if __name__ == "__main__":
    sys.exit(run())
