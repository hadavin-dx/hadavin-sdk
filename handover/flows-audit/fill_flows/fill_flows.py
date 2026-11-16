"""fill_flows: write a filled COPY of n8n flow files for a take, outside any git repo.

Replaces every `$env.DESK_*` / `$env.MF_*` token inside node strings with the literal value
from a KEY=VALUE file, and the six placeholder names when the values file carries them.
Stdlib only. Values are never printed or logged: messages name keys, files and line numbers
only. See README.md for the rules and exit codes.

Usage:
  fill_flows.py fill   --in DIR --values FILE --out DIR   (DIR for --out must not exist)
  fill_flows.py check  DIR [--tokens-only]                (read-only scan)
  fill_flows.py delete --out DIR [--force-hash] [--no-manifest]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata

EXIT_OK = 0
EXIT_REFUSED = 1  # any refusal; usage errors from argparse are 2
EXIT_NOTHING = 4  # fill found no token at all (already filled, or the wrong folder)

NAME_OK = re.compile(r"^(DESK|MF)_[A-Z0-9_]+$")
KEY_OK = re.compile(r"^[A-Z][A-Z0-9_]*$")
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
# Node fields that hold program code: a token there would become a syntax error or worse.
CODE_KEYS = ("jsCode", "functionCode", "pythonCode")
MANIFEST_SUFFIX = ".manifest.json"
MANIFEST_FORMAT = "fill_flows-manifest-1"


class Refused(Exception):
    """A refusal. The message never contains a value."""


# ---------------------------------------------------------------- values file


def _bad_char(ch: str) -> bool:
    return unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") or ch == "\x7f"


def under_mnt(path: str) -> bool:
    """True for a path on /mnt (a Windows drive mounted into Linux: file modes do not hold)."""
    rp = os.path.realpath(path)
    return rp == "/mnt" or rp.startswith("/mnt/")


def read_values(path: str) -> dict[str, str]:
    rp = os.path.realpath(path)
    if under_mnt(path):
        raise Refused("values file is under /mnt (Windows drive): file modes do not protect it")
    if inside_git(os.path.dirname(rp)):
        raise Refused("values file is inside a git repository (move it out; it holds secrets)")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as fh:
            st = os.fstat(fh.fileno())
            if not stat.S_ISREG(st.st_mode):
                raise Refused("values file is not a regular file")
            if st.st_mode & 0o077:
                raise Refused("values file can be read by other users (run: chmod 600 on it)")
            raw = fh.read()
    except OSError:
        raise Refused("values file: cannot open it (missing, a symlink, or not readable)") from None
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
            print(
                f"warning: values file line {no}: value of {key} contains ' #'; it is kept as "
                "part of the value (there are no inline comments)",
                file=sys.stderr,
            )
        values[key] = value
    return values


# ---------------------------------------------------------------- substitution


def _js_literal(value: str) -> str:
    """JS double-quoted string literal. ASCII only; braces escaped so '}}' cannot end the
    n8n expression early."""
    return json.dumps(value, ensure_ascii=True).replace("{", "\\u007b").replace("}", "\\u007d")


QUOTED = "a $env token sits inside a quoted JS string in an expression (not filled; edit the flow)"
OUTSIDE = "a $env token sits outside a clean {{ }} part of an expression (not filled)"


class Subst:
    def __init__(self, values: dict[str, str]):
        self.values = values
        self.used: set[str] = set()
        self.ph_used: set[str] = set()
        self.bad: set[str] = set()  # names we cannot fill (not DESK_/MF_, missing, empty)

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
        i, quote, comment, hit = 0, None, False, False
        while i < len(part):
            m = TOKEN.match(part, i)
            if m:
                if quote is not None:
                    raise Refused(QUOTED)
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
            out.append(ch)
            i += 1
        if hit and comment:
            raise Refused("a $env token sits in an expression that holds a // or /* comment")
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

    def string(self, s: str, ctx: str | None = None) -> str:
        if s in PLACEHOLDERS and s in self.values:
            if not self.values[s]:
                self.bad.add(s)
                return s
            self.ph_used.add(s)
            return self.values[s]
        if "$env" not in s:
            return s
        if ctx in CODE_KEYS:
            raise Refused(f"a $env token sits in a {ctx} field (program code; not filled)")
        if not s.startswith("="):  # plain field: n8n does not evaluate it
            return TOKEN.sub(lambda m: self._repl(m, False), s)
        return self._expr(s)

    def walk(self, o, ctx: str | None = None):
        if isinstance(o, dict):
            return {self.string(k): self.walk(v, k) for k, v in o.items()}
        if isinstance(o, list):
            return [self.walk(v, ctx) for v in o]
        if isinstance(o, str):
            return self.string(o, ctx)
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


def load_json(raw: bytes):
    return json.loads(raw.decode("utf-8"), parse_constant=_no_const)


def dump(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def shape(obj) -> tuple[int, dict]:
    nodes = obj.get("nodes", []) if isinstance(obj, dict) else []
    return len(nodes), (obj.get("connections", {}) if isinstance(obj, dict) else {})


# ---------------------------------------------------------------- file helpers


def sha256_nofollow(path: str) -> str:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    h = hashlib.sha256()
    with os.fdopen(fd, "rb") as fh:
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
            raise Refused(f"input file {n}: the ending must be lower case .json")
        if os.path.islink(p) or not os.path.isfile(p):
            raise Refused(f"input file {n}: symlink or not a regular file")
    return names


def read_json_file(directory: str, n: str):
    try:
        fd = os.open(os.path.join(directory, n), os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as fh:
            return load_json(fh.read())
    except (OSError, ValueError) as e:
        raise Refused(f"{n}: not valid JSON ({type(e).__name__})") from None


def inside_git(path: str) -> bool:
    p = os.path.realpath(path)
    while True:
        if os.path.lexists(os.path.join(p, ".git")):
            return True
        parent = os.path.dirname(p)
        if parent == p:
            return False
        p = parent


def _write_new(path: str, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)


# ---------------------------------------------------------------- modes


def _plain_name(n) -> bool:
    return isinstance(n, str) and n not in ("", ".", "..") and not any(c in n for c in "/\\\0")


def do_fill(in_dir: str, values_path: str, out_dir: str) -> int:
    out_dir = os.path.abspath(out_dir.rstrip("/") or "/")
    manifest_path = out_dir + MANIFEST_SUFFIX
    if under_mnt(os.path.dirname(out_dir)) or under_mnt(out_dir):
        raise Refused("output path is under /mnt (Windows drive): file modes do not protect it")
    if inside_git(out_dir) or inside_git(os.path.dirname(out_dir)):
        raise Refused("output path is inside a git repository (a parent folder has .git)")
    if os.path.lexists(out_dir) or os.path.lexists(manifest_path):
        raise Refused("output folder or its manifest already exists (delete it first)")
    if not os.path.isdir(os.path.dirname(out_dir)):
        raise Refused("output parent folder does not exist")
    if os.path.realpath(out_dir) == os.path.realpath(in_dir):
        raise Refused("output equals input")

    values = read_values(values_path)
    names = list_json(in_dir)
    if not names:
        raise Refused("input folder has no .json files")
    sub = Subst(values)
    outputs: dict[str, bytes] = {}
    found_any = False
    ph_left = 0
    for n in names:
        obj = read_json_file(in_dir, n)
        before = shape(obj)
        if any(ANY_ENV.search(t) for t in iter_strings(obj)):
            found_any = True
        try:
            new = sub.walk(obj)
        except Refused as e:
            raise Refused(f"{n}: {e}") from None
        if shape(new) != before:
            raise Refused(f"{n}: node count or connections changed (internal check)")
        data = dump(new)
        if ANY_ENV.search(data.decode("utf-8")):
            left = sorted(set(sub.bad)) or ["<dynamic $env use>"]
            raise Refused(f"{n}: a $env token is left after substitution ({', '.join(left)})")
        ph_left += sum(1 for t in iter_strings(new) if t in PLACEHOLDERS)
        outputs[n] = data
    if sub.bad:
        raise Refused(
            "cannot fill these names (missing or empty in the values file, or not a "
            "DESK_/MF_ name): " + ", ".join(sorted(sub.bad))
        )
    if not found_any and not sub.ph_used:
        print(
            "nothing to fill: no $env token in the input (already filled, or wrong folder)",
            file=sys.stderr,
        )
        return EXIT_NOTHING
    for k in sorted(set(values) - sub.used - sub.ph_used):
        print(f"warning: key {k} in the values file is not used by any node", file=sys.stderr)

    manifest = {
        "format": MANIFEST_FORMAT,
        "files": {n: hashlib.sha256(d).hexdigest() for n, d in sorted(outputs.items())},
    }
    created: list[str] = []
    made_dir = False
    try:
        # the manifest goes first: if this stops half way, `delete` can still find every file
        _write_new(manifest_path, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
        created.append(manifest_path)
        os.mkdir(out_dir, 0o700)
        made_dir = True
        os.chmod(out_dir, 0o700)
        for n, d in outputs.items():
            _write_new(os.path.join(out_dir, n), d)
            created.append(os.path.join(out_dir, n))
    except BaseException:
        for p in reversed(created):
            try:
                os.unlink(p)
            except OSError:
                pass
        if made_dir:
            try:
                os.rmdir(out_dir)
            except OSError:
                pass
        raise
    print(f"filled {len(outputs)} files, {len(sub.used)} names and {len(sub.ph_used)} placeholders")
    if ph_left:
        print(
            f"NOT READY TO IMPORT: {ph_left} placeholders left "
            "(create the credentials, import the sub-flow, fill again, then run check)"
        )
    else:
        print("no placeholders left; run check before importing")
    return EXIT_OK


def do_check(directory: str, tokens_only: bool) -> int:
    names = list_json(directory)
    bad = 0
    for n in names:
        try:
            obj = read_json_file(directory, n)
        except Refused as e:
            print(f"{n}: {e}")
            bad += 1
            continue
        ph: dict[str, int] = {}
        for text in iter_strings(obj):
            for m in TOKEN.finditer(text):
                print(f"{n}: token $env {m.group(1) or m.group(3)}")
                bad += 1
            c = len(ANY_ENV.findall(TOKEN.sub("", text)))
            if c:
                print(f"{n}: {c} other $env use(s) (dynamic form)")
                bad += c
            if text in PLACEHOLDERS:
                ph[text] = ph.get(text, 0) + 1
        if not tokens_only:
            for p, c in sorted(ph.items()):
                print(f"{n}: placeholder {p} x{c}")
                bad += c
    print(f"check: {len(names)} files, {bad} problem(s)")
    return EXIT_REFUSED if bad else EXIT_OK


def _load_manifest(manifest_path: str) -> dict:
    try:
        fd = os.open(manifest_path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as fh:
            man = json.loads(fh.read().decode("utf-8"))
        files = man["files"]
        if man.get("format") != MANIFEST_FORMAT or not isinstance(files, dict):
            raise ValueError
    except (OSError, ValueError, KeyError, AttributeError, TypeError):
        raise Refused("manifest is not a valid fill_flows manifest; nothing deleted") from None
    for n, h in files.items():
        if not _plain_name(n):
            raise Refused("manifest names a path that is not a plain file name; nothing deleted")
        if not isinstance(h, str):
            raise Refused("manifest has a bad hash entry; nothing deleted")
    return files


def do_delete(out_dir: str, force_hash: bool, no_manifest: bool = False) -> int:
    out_dir = os.path.abspath(out_dir.rstrip("/") or "/")
    manifest_path = out_dir + MANIFEST_SUFFIX
    has_dir = os.path.lexists(out_dir)
    has_man = os.path.lexists(manifest_path)
    if has_dir and (os.path.islink(out_dir) or not os.path.isdir(out_dir)):
        raise Refused("output folder is a symlink or not a folder; nothing deleted")
    if has_man and (os.path.islink(manifest_path) or not os.path.isfile(manifest_path)):
        raise Refused("manifest is a symlink or not a file; nothing deleted")
    if not has_dir and not has_man:
        raise Refused("output folder and manifest are both missing; nothing to delete")
    files: dict = {}
    if not no_manifest:
        if not has_man:
            raise Refused(
                "manifest is missing; nothing deleted (to remove the folder anyway, use "
                "--no-manifest: it removes only plain .json files)"
            )
        files = _load_manifest(manifest_path)
    if not has_dir:  # a fill was stopped after the manifest and before the folder
        os.unlink(manifest_path)
        print("deleted the manifest (the folder was not there)")
        return EXIT_OK
    present = set(os.listdir(out_dir))
    todo = []
    if no_manifest:
        for n in sorted(present):
            p = os.path.join(out_dir, n)
            if not n.endswith(".json") or os.path.islink(p) or not os.path.isfile(p):
                raise Refused(f"{n}: not a plain .json file; nothing deleted")
            todo.append(p)
    else:
        extra = sorted(present - set(files))
        if extra:
            raise Refused(
                f"folder holds files not in the manifest: {', '.join(extra)}; nothing deleted"
            )
        for n, h in sorted(files.items()):
            p = os.path.join(out_dir, n)
            if not os.path.lexists(p):
                continue
            if os.path.islink(p) or not os.path.isfile(p):
                raise Refused(f"{n}: symlink or not a regular file; nothing deleted")
            if sha256_nofollow(p) != h and not force_hash:
                raise Refused(
                    f"{n}: content changed since it was written (use --force-hash); nothing deleted"
                )
            todo.append(p)
    for p in todo:
        os.unlink(p)
    os.rmdir(out_dir)
    if has_man:
        os.unlink(manifest_path)
    print(f"deleted {len(todo)} files, the folder and the manifest")
    return EXIT_OK


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fill_flows", description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="mode", required=True)
    f = sp.add_parser("fill")
    f.add_argument("--in", dest="in_dir", required=True)
    f.add_argument("--values", required=True)
    f.add_argument("--out", required=True)
    c = sp.add_parser("check")
    c.add_argument("dir")
    c.add_argument("--tokens-only", action="store_true", help="do not list placeholders")
    d = sp.add_parser("delete")
    d.add_argument("--out", required=True)
    d.add_argument("--force-hash", action="store_true")
    d.add_argument("--no-manifest", action="store_true", help="folder has no usable manifest")
    a = ap.parse_args(argv)
    try:
        if a.mode == "fill":
            return do_fill(a.in_dir, a.values, a.out)
        if a.mode == "check":
            return do_check(a.dir, a.tokens_only)
        return do_delete(a.out, a.force_hash, a.no_manifest)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return EXIT_REFUSED
    except Exception as e:  # noqa: BLE001  never print the exception text: it could carry a path or value
        print(f"failed: {type(e).__name__}", file=sys.stderr)
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
