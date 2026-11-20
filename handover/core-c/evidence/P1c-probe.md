# P1c probe: what today's redactor does with base64 text, internal host names and bare numbers

Evidence only: inputs, outputs, counts. No design verdict, no product code. Run on 2026-11-20.

## What was run
- Code under test: a clean export of `refs/inputs/main` (51c9fc4) in `/tmp/core-c-p1c` with its own `.venv`; the shared working tree was not run.
  The probe prints the module path it imported: `/tmp/core-c-p1c/src/hadavin_sdk/__init__.py`.
- Choke point: `hadavin_sdk.guard.runmap.redact_text(text, {})` and `redact_untrusted(text, {})`, a fresh empty map per case.
- Command (exit 0; run twice, the two outputs were byte-identical, seed 20261120):

```
mkdir -p /tmp/core-c-p1c && git -C /home/user/hadavin-sdk archive refs/inputs/main | tar -x -C /tmp/core-c-p1c
cd /tmp/core-c-p1c && uv sync --all-extras --group test
uv run python p1c_probe.py > out.md      # p1c_probe.py = a copy of handover/core-c/evidence/p1c_probe.py
```

- Secrets rule: every secret-like value is built at run time (seeded random, string parts). The only literal key id is AWS's documented
  example. Tables show a tag (`{B64}`, `{VALUE}`, `{N}`, `{pw14}`) where a built value or its encoding stood; host names, the e-mail
  address and `55556666` are made-up and shown as written.

## Summary of counts
| gap | cases | result |
|---|---|---|
| 1a baseline, plain form | 16 | 0 leaked (all 8 values are masked in plain form, short and long carrier) |
| 1b base64, 8 values x 2 carriers x 8 encodings | 128 | 48 LEAKED; the other 80 are masked whole as HIGHENTROPY |
| 1c base64, long blobs in other forms | 14 | 4 LEAKED; 8 held by HIGHENTROPY, 2 by BASIC |
| 1 total (1b + 1c) | 142 | 52 LEAKED |
| 2 host names | 44 | 28 LEAKED (15 in part, 13 whole name readable); 16 fully masked |
| 3 bare numbers (a list, not a verdict) | 43 | 24 NOT masked, 2 masked in part, 17 masked whole |

`redact_untrusted` gave the same LEAKED value as `redact_text` in all 142 base64 cases and the same output in all 87 host and number cases.

## What the tables show, in plain words
### Gap 1 (base64)
- No decoded view exists: `runmap._views` (runmap.py:401-414) returns 0 views for a plain ASCII base64 line. Its views are NFKC with
  invisible characters removed, JSON `\uXXXX` unescape, and percent / entity / backslash undo. In no case did the map hold the kind of
  the decoded value (SECRET, BEARER, APIKEY, EMAIL, HOSTNAME, IPV4, URLCRED): the only kinds seen were HIGHENTROPY and BASIC.
- What holds a blob today is its length, not its content: HIGHENTROPY (redact.py:638) needs an unbroken run of 40 or more characters
  (padding `=` not counted) with an upper-case letter, a lower-case letter and a digit. 1b by blob length (padding counted): under 40
  characters 41 cases, 41 leaked; 40 or more 87 cases, 7 leaked. The 7 are: 5 blobs of 38 characters plus `==` (rows 113, 114, 116,
  117, 120), row 39 (40 characters with padding) and row 70 (40 characters, not matched by HIGHENTROPY).
- Clearest failing shape: the standard base64 of a short line, for example `{B64}` of `pwd={pw14}` (24 characters), of
  `AKIAIOSFODNN7EXAMPLE` (28), of `ann.lee@mail.acme.example` (36), of `10.20.30.40` (16), of `{"password": "{pw12}"}` (38 + `==`):
  output UNCHANGED, alone, in a sentence, in a JSON string and after `data=`. A value of about 29 bytes or fewer always passes.
- A long blob leaks when it is wrapped: lines of 32 characters pass unchanged (1c rows 1, 5, 9). With lines of 64 or 76 the full lines
  are masked and the last, shorter line stays (1c rows 2, 3, 6, 7, 10, 11); in row 2 that last line held 11 of the 14 characters of
  the password. In the other rows the last line held only the tail of the carrier line, not the protected value.
- Not leaked: every long-carrier blob in 1b (64 of 64), the UTF-16 and double forms when they reach 40 characters, a `data:` URL, and
  `Basic {B64}` (kind BASIC).

### Gap 2 (host names)
- Pattern HOSTNAME (redact.py:388) ends the match at the private suffix. A name that goes on after `corp` keeps the rest:
  `db01.corp.example` becomes `<HOSTNAME_1>.example`. Same result with a port, in a URL, in a URL with credentials, upper case,
  trailing dot, punycode label, `host=` key, JSON value, and the three encoded-dot forms (15 "part" rows: 1, 2, 17, 19, 21, 24, 26,
  29, 37, 38, 39, 40, 41, 44, and row 42).
- Whole name readable (13 rows): `.internal` or `.local` followed by more labels (6, 8); a name under a reserved TLD only, with no
  private suffix (15, 16); Kubernetes names (9, 10); a non-ASCII label (31); an underscore label (32); a bare single-label host after
  `host`, `host:`, `hostname=`, `--host` (33-36); defanged dots `[.]` (43).
- Kept on purpose according to the code's own comments (recorded, not judged): `.cluster.local` and AWS's `compute.internal` /
  `ec2.internal` (`_KEPT_HOST`, redact.py:809, comment at 382; rows 9 and 42), and `.internal` / `.local` followed by another label
  (stack-trace names such as `jdk.internal.reflect`, comment at 384-386; rows 6 and 8).
- Fully masked (16 rows): names ending at `corp`, `internal`, `local`, `lan`, `intranet`, `home.arpa`, `localdomain`, with a port, in
  a URL, upper case, with a trailing dot, punycode + `.internal`, and both e-mail domains (the whole address is one EMAIL).

### Gap 3 (bare numbers; accepted property, the list is the output)
- NOT masked today (24 rows): 6 to 9 digits with any plain label (`ref`, `account`, `account number`, `account no:`, `acct=`,
  `invoice no`, `invoice #`, `order`, `card`, `id:`), also with `bank transfer to` before `account`; 8 digits split by hyphen, space
  or dot; an amount with decimals; a 16-digit Luhn-valid number glued between letters; the last four digits; phone with brackets, with
  dots, 7 digits; 9 contiguous digits after `ssn`.
- Masked in part (2 rows): 16 digits in groups joined by dots (the first 12 taken as MAC, last group left, row 29); 15 digits in 4-6-5
  groups (first 10 taken as PHONE, last 5 left, row 32).
- Masked whole (17 rows): 10, 11, 13, 14, 15 and 16 contiguous digits (PHONE), 12 digits (ACCOUNTID), 16 digits in 4-4-4-4 groups
  with spaces or hyphens (CREDITCARD), a phone with `+` and hyphens or after `phone=`, 3-2-4 with hyphens (SSN), `customer_id=` (TENANT),
  an account right after a BSB code (BANKCODE + BANKACCT).

## Pattern names involved (src/hadavin_sdk/guard/redact.py on main, `PATTERNS` from line 153)
| kind | line | seen in |
|---|---|---|
| HIGHENTROPY | 638 (40+ run, mixed case and digit), 692 (129+ run) | gap 1: the only thing that holds a blob |
| BASIC | 405 | gap 1c rows 13, 14 |
| SECRET, BEARER (403), APIKEY (195), EMAIL (236), URLCRED (227), IPV4 (357) | - | gap 1a baseline only |
| HOSTNAME | 388; kept names `_KEPT_HOST` 809, used at 934 | gap 1a, gap 2 |
| EMAIL, URLCRED, IPV4 (355) | 236, 227, 355 | gap 2 rows 21, 22, 23, 42 |
| PHONE | 472 | gap 3 |
| ACCOUNTID, CREDITCARD, SSN, TENANT, MAC | 353, 451, 409, 396, 374 | gap 3 |
| BANKCODE, BANKACCT | 265-326, 333 and 340 | gap 3 row 8 |
| views | runmap.py:401-414 (`_views`) | no base64 view |

## NOT RUN / not checked
- A long blob (40+ characters) with no digit, which HIGHENTROPY's digit rule would not match: NOT RUN. Three searches for such a line
  around the e-mail address and the host name found none (the two "NOT CONSTRUCTED" rows in 1c). Not proven either way.
- Other encodings: hex, base32, base85, gzip + base64, quoted-printable: not checked.
- A base64 blob with percent-encoded padding (`%3D`), with JSON-escaped slashes, or split across two JSON fields: not checked.
- `redact_many`, `redact_value`, `redact_bounded`, `safe_head` and the approval-card path: not checked; only `redact_text` and `redact_untrusted`.
- A non-empty run map (a value already known to the map, then seen encoded): not checked; every case starts with `{}`.
- The 30 hostile inputs, 48 must-mask and 14 must-keep lines of the old plan (gap 4, the permanent corpus test): not found and not run;
  the cases here are newly constructed.
- Whether a HIGHENTROPY placeholder can later be restored or shown: not checked.
- The branches core/P2d-1, core/P1d-a and the fold heads: not run; main only.
- The repository's test suite: not run.
- LEAKED is the probe's own measure (see the script): for base64 the output's base64-looking runs are decoded (both alphabets, four
  start offsets, UTF-8 and UTF-16, one more level, also with line breaks removed) and compared with the protected value; "part" means
  6 or more characters in a row, or half the value. For host names it means a label of the name is readable outside a placeholder.

## Probe script (also at `handover/core-c/evidence/p1c_probe.py`)
```python
"""P1c probe: what today's redaction choke point does with base64 text, internal host names and bare numbers.

Run from a clean export of main (never from a working tree other agents edit):

    mkdir -p /tmp/core-c-p1c && git -C /home/user/hadavin-sdk archive refs/inputs/main | tar -x -C /tmp/core-c-p1c
    cd /tmp/core-c-p1c && uv sync --all-extras --group test
    cp /home/user/hadavin-sdk/handover/core-c/evidence/p1c_probe.py . && uv run python p1c_probe.py > out.md

It only reads: it calls `hadavin_sdk.guard.runmap.redact_text(text, {})` and `redact_untrusted(text, {})` and prints
Markdown tables. Every secret-like value is built at run time from a seeded random generator; the only literal
key id is AWS's documented example. Printed inputs and outputs never show a built value: it is replaced by a tag.
"""

from __future__ import annotations

import base64
import binascii
import difflib
import json
import random
import re
import string
import sys

import hadavin_sdk
from hadavin_sdk.guard import runmap

RNG = random.Random(20261120)
PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9]*)_\d+>")
B64_RUN = re.compile(r"[A-Za-z0-9+/_\-]{8,}={0,2}")


def rand(n: int, alphabet: str = string.ascii_letters + string.digits) -> str:
    """n characters with at least one upper, one lower and one digit (so it looks like a real credential)."""
    while True:
        s = "".join(RNG.choice(alphabet) for _ in range(n))
        if alphabet != string.ascii_letters + string.digits:
            return s
        if any(c.isupper() for c in s) and any(c.islower() for c in s) and any(c.isdigit() for c in s):
            return s


def run(fn, text: str):
    """(output, kinds in the map) or ('RAISED <type>', [])."""
    mapping: dict[str, str] = {}
    try:
        out = fn(text, mapping)
    except Exception as exc:  # recorded, never hidden
        return f"RAISED {type(exc).__name__}", []
    kinds = sorted({m.group(1) for key in mapping for m in [PLACEHOLDER.fullmatch(key)] if m})
    return out, kinds


def lcs(a: str, b: str) -> int:
    if not a or not b:
        return 0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b)).size


def _decodings(token: str, depth: int = 2) -> list[str]:
    """Every text a reader could get out of one base64-looking run: both alphabets, any start offset (a run cut
    by a mask no longer starts on a 4-character boundary), UTF-8 and UTF-16, and once more for double encoding."""
    found: list[str] = []
    body = token.rstrip("=").replace("-", "+").replace("_", "/")
    for offset in range(4):
        piece = body[offset:]
        piece = piece[: len(piece) - (len(piece) % 4 == 1)]
        if len(piece) < 4:
            continue
        try:
            raw = base64.b64decode(piece + "=" * (-len(piece) % 4))
        except (binascii.Error, ValueError):
            continue
        for text in (
            raw.decode("utf-8", "replace"),
            raw.decode("utf-16-le", "replace"),
            raw[1:].decode("utf-16-le", "replace"),
            raw.decode("utf-16-be", "replace"),
        ):
            found.append(text)
            if depth > 1:
                for inner in B64_RUN.findall(text):
                    found.extend(_decodings(inner, depth - 1))
    return found


def readable(out: str) -> str:
    """The output plus everything that decodes out of the base64-looking runs left in it."""
    unslashed = out.replace("\\/", "/")
    parts = [out]
    bare = PLACEHOLDER.sub(" ", unslashed)
    # also with line breaks removed: a wrapped blob is one blob to its reader
    for token in B64_RUN.findall(bare) + B64_RUN.findall(re.sub(r"[\r\n]+", "", bare)):
        parts.extend(_decodings(token))
    return "\n".join(parts)


def leak_of(protected: str, out: str) -> tuple[str, int]:
    """LEAKED verdict for a protected value: whole / part (6 or more characters in a row, or half of it) / no."""
    n = lcs(protected, readable(out))
    if n >= len(protected):
        return "YES (whole)", n
    if n >= min(6, max(3, len(protected) // 2)):
        return f"YES (part, {n} of {len(protected)} chars)", n
    return "no", n


def show(out: str, hide: dict[str, str], runs: bool = True) -> str:
    """The output with built values replaced by tags (longest first), then any long run left replaced too."""
    for value in sorted(hide, key=len, reverse=True):
        out = out.replace(value, hide[value])

    def tag(m: re.Match[str]) -> str:
        return m.group(0) if len(m.group(0)) < 16 else f"{{b64-like run, {len(m.group(0))} chars}}"

    pieces = re.split(r"(<[A-Z][A-Z0-9]*_\d+>|\{[^{}]*\})", out)
    if runs:
        out = "".join(p if i % 2 else B64_RUN.sub(tag, p) for i, p in enumerate(pieces))
    return out.replace("|", "\\|").replace("\n", "\\n")


def cell(text: str) -> str:
    return "`" + text.replace("`", "'") + "`"


# ---------------------------------------------------------------------------------------------------------------
# Gap 1: base64
# ---------------------------------------------------------------------------------------------------------------
def gap1_values() -> list[dict]:
    pw = rand(14)
    tok = rand(28)
    akia = "AKIA" + "IOSFODNN7" + "EXAMPLE"  # AWS's documented example id, nothing else
    mail = "ann.lee" + "@" + "mail.acme.example"
    host = "db01.prod.corp"
    ip = ".".join(["10", "20", "30", "40"])
    cpw = rand(12)
    jpw = rand(12)
    return [
        dict(name="kv secret", protected=pw, short="pwd=" + pw, long="2026-11-20T10:00:00Z deploy step db_password=" + pw + " applied",
             shape="pwd={pw14} / log line with db_password={pw14}"),
        dict(name="bearer token", protected=tok, short="Bearer " + tok, long="GET /v1/items Authorization: Bearer " + tok + " status 200",
             shape="Bearer {tok28} / request line with Authorization: Bearer {tok28}"),
        dict(name="AWS key id (doc example)", protected=akia, short=akia, long="boto error: key id " + akia + " is not allowed to call sts",
             shape="AKIAIOSFODNN7EXAMPLE / error line holding it"),
        dict(name="e-mail address", protected=mail, short=mail, long="refund mail queued for " + mail + " at 10:02:11 by worker 3",
             shape="ann.lee@mail.acme.example / log line holding it"),
        dict(name="internal host name", protected=host, short=host, long="connection refused while dialling " + host + " on port 5432",
             shape="db01.prod.corp / log line holding it"),
        dict(name="private IPv4", protected=ip, short=ip, long="upstream " + ip + " timed out after 30 seconds, retrying",
             shape="10.20.30.40 / log line holding it"),
        dict(name="connection string", protected=cpw, short="pg://u:" + cpw + "@db/x", long="DATABASE_URL is postgres://app:" + cpw + "@db.acme.example:5432/orders",
             shape="pg://u:{pw12}@db/x / postgres://app:{pw12}@db.acme.example:5432/orders"),
        dict(name="JSON with password", protected=jpw, short=json.dumps({"password": jpw}), long=json.dumps({"user": "app", "password": jpw, "port": 5432}),
             shape='{"password": "{pw12}"} / {"user": "app", "password": "{pw12}", "port": 5432}'),
    ]


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


ENCODINGS = [
    ("standard", lambda s: (b64(s.encode()), "{B64}")),
    ("url-safe", lambda s: (base64.urlsafe_b64encode(s.encode()).decode(), "{B64URL}")),
    ("no padding", lambda s: (b64(s.encode()).rstrip("="), "{B64NOPAD}")),
    ("in a sentence", lambda s: ("please decode " + b64(s.encode()) + " and apply it", "please decode {B64} and apply it")),
    ("in a JSON string", lambda s: (json.dumps({"note": "config", "data": b64(s.encode())}), '{"note": "config", "data": "{B64}"}')),
    ("of UTF-16 text", lambda s: (b64(s.encode("utf-16-le")), "{B64 of UTF-16-LE}")),
    ("double", lambda s: (b64(b64(s.encode()).encode()), "{B64 of B64}")),
    ("after key data=", lambda s: ("data=" + b64(s.encode()), "data={B64}")),
]


def gap1() -> tuple[int, int, int]:
    print("## Gap 1: base64-encoded values\n")
    values = gap1_values()
    print("### 1a. Baseline: the plain form IS masked\n")
    print("| value | carrier | input shape | output | map kinds | LEAKED |")
    print("|---|---|---|---|---|---|")
    base_bad = 0
    for v in values:
        for carrier in ("short", "long"):
            out, kinds = run(runmap.redact_text, v[carrier])
            verdict, _ = leak_of(v["protected"], out)
            base_bad += verdict != "no"
            hide = {v["protected"]: "{VALUE}"} if v["name"] not in ("internal host name", "private IPv4", "e-mail address", "AWS key id (doc example)") else {}
            print(f"| {v['name']} | {carrier} ({len(v[carrier])} chars) | {cell(v['shape'])} | {cell(show(out, hide))} | {', '.join(kinds) or '-'} | {verdict} |")
    print(f"\nBaseline rows: {len(values) * 2}; plain form leaked in {base_bad}.\n")

    print("### 1b. The same values, base64-encoded\n")
    print("`short` = the value alone (or its smallest key=value form); `long` = the value inside a log line. "
          "`blob` = length of the base64 text. LEAKED = the protected value can be read by base64-decoding what the output still holds.\n")
    print("| # | value | carrier | encoding | blob | input shape | output (`redact_text`) | map kinds | LEAKED | `redact_untrusted` LEAKED |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    n = leaked = whole_he = 0
    per_enc: dict[str, list[int]] = {}
    per_len: list[tuple[int, bool]] = []
    for v in values:
        for carrier in ("short", "long"):
            for enc_name, enc in ENCODINGS:
                text, shape = enc(v[carrier])
                blob = max(B64_RUN.findall(text), key=len)
                out, kinds = run(runmap.redact_text, text)
                verdict, _ = leak_of(v["protected"], out)
                out_u, _ = run(runmap.redact_untrusted, text)
                verdict_u, _ = leak_of(v["protected"], out_u)
                n += 1
                is_leak = verdict != "no"
                leaked += is_leak
                whole_he += (not is_leak) and "HIGHENTROPY" in kinds
                per_enc.setdefault(enc_name, [0, 0])
                per_enc[enc_name][0] += 1
                per_enc[enc_name][1] += is_leak
                per_len.append((len(blob), is_leak))
                rendered = "UNCHANGED" if out == text else show(out, {blob: "{BLOB}", v["protected"]: "{VALUE}"})
                print(f"| {n} | {v['name']} | {carrier} | {enc_name} | {len(blob)} | {cell(shape)} | {cell(rendered)} | {', '.join(kinds) or '-'} | {verdict} | {verdict_u} |")
    print(f"\nGap 1b counts: cases {n}, leaked {leaked}, not leaked {n - leaked} (of these, HIGHENTROPY in the map: {whole_he}).\n")
    print("| encoding | cases | leaked |\n|---|---|---|")
    for enc_name, (c, k) in per_enc.items():
        print(f"| {enc_name} | {c} | {k} |")
    short_blobs = [x for x in per_len if x[0] < 40]
    long_blobs = [x for x in per_len if x[0] >= 40]
    print(f"\nBy blob length: under 40 characters: {len(short_blobs)} cases, {sum(k for _, k in short_blobs)} leaked; "
          f"40 or more: {len(long_blobs)} cases, {sum(k for _, k in long_blobs)} leaked.\n")
    extra = gap1_extra(values)
    return n + extra[0], leaked + extra[1], whole_he + extra[2]


def wrap(blob: str, width: int) -> str:
    return "\n".join(blob[i:i + width] for i in range(0, len(blob), width))


def no_digit_line(value: str) -> str | None:
    """A log line holding `value` whose base64 is 40 or more characters and has no digit: made-up lower-case
    words around it, searched in seeded order (a line of real words was not found in two earlier searches)."""
    letters = string.ascii_lowercase
    for _ in range(200_000):
        head = rand(RNG.choice([2, 5, 8]), letters) + RNG.choice([" ", ":", "="])
        tail = RNG.choice([" ", ",", ";"]) + rand(RNG.randint(3, 9), letters)
        line = head + value + tail
        blob = b64(line.encode())
        if len(blob.rstrip("=")) >= 40 and not any(ch.isdigit() for ch in blob):
            return line
    return None


def gap1_extra(values: list[dict]) -> tuple[int, int, int]:
    print("### 1c. Long blobs that HIGHENTROPY might not hold (the long carrier, 40 or more base64 characters)\n")
    print("| # | value | form | longest unbroken run | input shape | output (`redact_text`) | map kinds | LEAKED | `redact_untrusted` LEAKED |")
    print("|---|---|---|---|---|---|---|---|---|")
    by = {v["name"]: v for v in values}
    cases: list[tuple[dict, str, str, str]] = []
    for name in ("kv secret", "e-mail address", "internal host name"):
        v = by[name]
        blob = b64(v["long"].encode())
        cases.append((v, "wrapped at 32 characters", wrap(blob, 32), "{B64 lines of 32}"))
        cases.append((v, "wrapped at 64 characters (PEM style)", wrap(blob, 64), "{B64 lines of 64}"))
        cases.append((v, "wrapped at 76 characters (MIME style)", wrap(blob, 76), "{B64 lines of 76}"))
        cases.append((v, "data: URL", "data:text/plain;base64," + blob, "data:text/plain;base64,{B64}"))
    for name in ("e-mail address", "internal host name"):
        v = by[name]
        line = no_digit_line(v["protected"])
        if line is None:
            print(f"| - | {name} | blob with no digit | - | NOT CONSTRUCTED: no such line found in the search | - | - | - | - |")
            continue
        cases.append((v, "blob with no digit, 40+ characters", b64(line.encode()), "{B64 with no digit}"))
        cases.append((v, "blob with no digit, in a sentence", "please decode " + b64(line.encode()) + " and apply it", "please decode {B64 with no digit} and apply it"))
    v = by["kv secret"]
    cases.append((v, "HTTP Basic header (base64 of user:{pw14})", "Authorization: Basic " + b64(("app:" + v["protected"]).encode()), "Authorization: Basic {B64 of app:{pw14}}"))
    cases.append((v, "word Basic + short blob", "Basic " + b64(v["short"].encode()), "Basic {B64}"))
    n = leaked = held = 0
    for v, form, text, shape in cases:
        out, kinds = run(runmap.redact_text, text)
        verdict, _ = leak_of(v["protected"], out)
        out_u, _ = run(runmap.redact_untrusted, text)
        verdict_u, _ = leak_of(v["protected"], out_u)
        n += 1
        leaked += verdict != "no"
        held += verdict == "no" and "HIGHENTROPY" in kinds
        longest = max(len(x) for x in B64_RUN.findall(text))
        hide = {x: "{BLOB LINE}" for x in B64_RUN.findall(text) if len(x) >= 16}
        hide[v["protected"]] = "{VALUE}"
        rendered = "UNCHANGED" if out == text else show(out, hide)
        print(f"| {n} | {v['name']} | {form} | {longest} | {cell(shape)} | {cell(rendered)} | {', '.join(kinds) or '-'} | {verdict} | {verdict_u} |")
    print(f"\nGap 1c counts: cases {n}, leaked {leaked}, held by HIGHENTROPY {held}.\n")
    return n, leaked, held


# ---------------------------------------------------------------------------------------------------------------
# Gap 2: internal host names
# ---------------------------------------------------------------------------------------------------------------
def gap2_cases() -> list[tuple[str, str, str]]:
    """(shape, name, text). The name is made up; the sentence around it shares no label with it."""
    cpw = rand(10)
    c = [
        ("corp + .example", "db01.corp.example", "dial db01.corp.example now"),
        ("4 labels, corp + .example", "billing-db.prod.corp.example", "dial billing-db.prod.corp.example now"),
        ("name ends at corp", "db01.prod.corp", "dial db01.prod.corp now"),
        ("a.b.c.internal", "a.b.c.internal", "dial a.b.c.internal now"),
        ("words under .internal", "orders.payments.internal", "dial orders.payments.internal now"),
        (".internal then more labels", "db01.internal.acme.example", "dial db01.internal.acme.example now"),
        ("host.local", "printer7.local", "dial printer7.local now"),
        (".local then more labels", "db01.local.acme.example", "dial db01.local.acme.example now"),
        ("k8s service, cluster.local", "billing.payments.svc.cluster.local", "dial billing.payments.svc.cluster.local now"),
        ("k8s service, short form", "billing.payments.svc", "dial billing.payments.svc now"),
        (".lan", "nas02.office.lan", "dial nas02.office.lan now"),
        (".intranet", "wiki.acme.intranet", "dial wiki.acme.intranet now"),
        (".home.arpa", "router.home.arpa", "dial router.home.arpa now"),
        (".localdomain", "build03.localdomain", "dial build03.localdomain now"),
        ("reserved TLD only (.example)", "db01.acme.example", "dial db01.acme.example now"),
        ("reserved TLD only (.test)", "db01.acme.test", "dial db01.acme.test now"),
        ("with a port", "db01.corp.example", "dial db01.corp.example:5432 now"),
        (".internal with a port", "a.b.c.internal", "dial a.b.c.internal:8080 now"),
        ("inside a URL", "db01.corp.example", "GET https://db01.corp.example/v1/items done"),
        (".internal inside a URL with port", "a.b.c.internal", "GET http://a.b.c.internal:8080/v1/items done"),
        ("inside a URL with credentials", "db01.corp.example", "use postgres://app:" + cpw + "@db01.corp.example:5432/orders now"),
        ("e-mail domain", "mail.corp.example", "write to ops@mail.corp.example now"),
        ("e-mail domain .internal", "mail.acme.internal", "write to ops@mail.acme.internal now"),
        ("upper case", "DB01.CORP.EXAMPLE", "dial DB01.CORP.EXAMPLE now"),
        ("upper case .INTERNAL", "A.B.C.INTERNAL", "dial A.B.C.INTERNAL now"),
        ("trailing dot", "db01.corp.example", "dial db01.corp.example. now"),
        (".internal trailing dot", "a.b.c.internal", "dial a.b.c.internal. now"),
        (".local trailing dot + word", "printer7.local", "dial printer7.local.\nnext line"),
        ("punycode label + corp.example", "xn--bcher-kva.corp.example", "dial xn--bcher-kva.corp.example now"),
        ("punycode label + .internal", "xn--bcher-kva.internal", "dial xn--bcher-kva.internal now"),
        ("non-ASCII label + .internal", "b\u00fccher.internal", "dial b\u00fccher.internal now"),
        ("underscore in a label", "db_01.corp.example", "dial db_01.corp.example now"),
        ("single label after 'host'", "db01", "host db01 is down"),
        ("single label, host: key", "db01", "host: db01"),
        ("single label, hostname= key", "db01", "hostname=db01 state=down"),
        ("single label, --host flag", "db01", "psql --host db01 --port 5432"),
        ("key=value host=", "db01.corp.example", "host=db01.corp.example port=5432"),
        ("JSON value", "db01.corp.example", json.dumps({"host": "db01.corp.example", "port": 5432})),
        ("JSON-escaped dots (\\u002e)", "db01.corp.example", "dial db01\\u002ecorp\\u002eexample now"),
        ("percent-encoded dots", "db01.corp.example", "dial db01%2Ecorp%2Eexample now"),
        ("full-width dots", "db01.corp.example", "dial db01\uff0ecorp\uff0eexample now"),
        ("AWS private DNS name", "ip-10-0-3-22.eu-west-1.compute.internal", "node ip-10-0-3-22.eu-west-1.compute.internal ready"),
        ("defanged dots [.]", "db01.corp.example", "dial db01[.]corp[.]example now"),
        ("two names in one line", "db01.corp.example", "from db01.corp.example to db02.corp.example done"),
    ]
    return c


def gap2() -> tuple[int, int]:
    print("## Gap 2: internal host names\n")
    print("LEAKED = at least one label of the name is still readable in the output (`kept` lists them; a placeholder hides the rest). "
          "The sentence around the name shares no label with it.\n")
    print("| # | input shape | input | output (`redact_text`) | map kinds | kept labels | LEAKED | `redact_untrusted` same output |")
    print("|---|---|---|---|---|---|---|---|")
    n = leaked = whole = 0
    for shape, name, text in gap2_cases():
        out, kinds = run(runmap.redact_text, text)
        out_u, _ = run(runmap.redact_untrusted, text)
        residue = PLACEHOLDER.sub(" ", out).lower()
        residue = residue.replace("\\u002e", ".").replace("%2e", ".").replace("\uff0e", ".").replace("[.]", ".")
        labels = [x for x in re.split(r"\.", name.lower()) if x]
        if name == "db01.corp.example" and "db02" in text:
            labels.append("db02")
        kept = [x for x in dict.fromkeys(labels) if re.search(r"(?<![a-z0-9_\-\u00fc])" + re.escape(x) + r"(?![a-z0-9_\-\u00fc])", residue)]
        n += 1
        if kept and len(kept) == len(dict.fromkeys(labels)):
            verdict = "YES (whole name)"
            whole += 1
        elif kept:
            verdict = "YES (part)"
        else:
            verdict = "no"
        leaked += bool(kept)
        hide = {m: "{pw10}" for m in re.findall(r"app:([A-Za-z0-9]{10})@", text)}
        print(f"| {n} | {shape} | {cell(show(text, hide, False))} | {cell(show(out, hide, False))} | {', '.join(kinds) or '-'} | {', '.join(kept) or '-'} | {verdict} | {'yes' if out_u == out else 'NO: ' + cell(show(out_u, hide, False))} |")
    print(f"\nGap 2 counts: cases {n}, leaked {leaked} (whole name readable {whole}, part readable {leaked - whole}), fully masked {n - leaked}.\n")
    return n, leaked


# ---------------------------------------------------------------------------------------------------------------
# Gap 3: bare numbers (an accepted property: a list, not a verdict)
# ---------------------------------------------------------------------------------------------------------------
def luhn_number(length: int, prefix: str) -> str:
    body = prefix + rand(length - 1 - len(prefix), string.digits)
    total = 0
    for i, ch in enumerate(reversed(body)):
        d = int(ch)
        if i % 2 == 0:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return body + str((10 - total % 10) % 10)


def gap3_cases() -> list[tuple[str, str, str]]:
    """(shape, number, text)."""
    fixed = "5555" + "6666"
    c16 = luhn_number(16, "4")
    c15 = luhn_number(15, "37")
    c13 = luhn_number(13, "4")
    g = lambda s, sep: sep.join(s[i:i + 4] for i in range(0, len(s), 4))
    d = lambda k: rand(1, "123456789") + rand(k - 1, string.digits)
    n6, n7, n9, n10, n11, n12, n14 = d(6), d(7), d(9), d(10), d(11), d(12), d(14)
    area, line = "415", "555" + "01" + rand(2, string.digits)
    ssn = rand(1, "1234578") + rand(2, string.digits) + "-" + rand(1, "123456789") + rand(1, string.digits) + "-" + rand(1, "123456789") + rand(3, string.digits)
    return [
        ("the ticket's line, 8 digits, no label", fixed, "ref " + fixed + " paid"),
        ("8 digits alone", fixed, fixed),
        ("label account", fixed, "account " + fixed + " paid"),
        ("label account number", fixed, "account number " + fixed),
        ("label account no:", fixed, "account no: " + fixed),
        ("label acct=", fixed, "acct=" + fixed),
        ("account + bank word nearby", fixed, "bank transfer to account " + fixed + " failed"),
        ("after a BSB code", fixed, "BSB 062-000 account " + fixed),
        ("label invoice no", fixed, "invoice no " + fixed + " paid"),
        ("label invoice #", fixed, "invoice #" + fixed + " paid"),
        ("label order", n7, "order " + n7 + " shipped"),
        ("label card, 8 digits", fixed, "card " + fixed + " declined"),
        ("label customer_id=", fixed, "customer_id=" + fixed),
        ("label id:", fixed, "id:" + fixed),
        ("8 digits with a hyphen", fixed, "ref " + g(fixed, "-") + " paid"),
        ("8 digits with a space", fixed, "ref " + g(fixed, " ") + " paid"),
        ("8 digits with a dot", fixed, "ref " + g(fixed, ".") + " paid"),
        ("amount with decimals", fixed, "amount " + fixed + ".00 EUR"),
        ("6 digits", n6, "ref " + n6 + " paid"),
        ("9 digits", n9, "ref " + n9 + " paid"),
        ("10 digits", n10, "ref " + n10 + " paid"),
        ("11 digits", n11, "ref " + n11 + " paid"),
        ("12 digits", n12, "ref " + n12 + " paid"),
        ("14 digits (not a timestamp)", n14, "ref " + n14 + " paid"),
        ("16 digits Luhn ok, no label, contiguous", c16, "ref " + c16 + " paid"),
        ("16 digits Luhn ok, label card, contiguous", c16, "card " + c16 + " declined"),
        ("16 digits Luhn ok, groups with spaces", c16, "card " + g(c16, " ") + " declined"),
        ("16 digits Luhn ok, groups with hyphens", c16, "card " + g(c16, "-") + " declined"),
        ("16 digits Luhn ok, groups with dots", c16, "card " + g(c16, ".") + " declined"),
        ("16 digits Luhn ok, glued to a word", c16, "card" + c16 + "x declined"),
        ("16 digits Luhn ok, after id=", c16, "pan=" + c16),
        ("15 digits Luhn ok (4-6-5 groups)", c15, "card " + c15[:4] + " " + c15[4:10] + " " + c15[10:] + " declined"),
        ("15 digits Luhn ok, contiguous", c15, "card " + c15 + " declined"),
        ("13 digits Luhn ok, contiguous", c13, "card " + c13 + " declined"),
        ("last four only", c16[-4:], "card ending " + c16[-4:] + " declined"),
        ("phone, +1 and hyphens", area + line, "call +1 " + area + "-" + line[:3] + "-" + line[3:] + " today"),
        ("phone, contiguous 10 digits", area + line, "call " + area + line + " today"),
        ("phone, brackets", area + line, "call (" + area + ") " + line[:3] + "-" + line[3:] + " today"),
        ("phone, dots", area + line, "call " + area + "." + line[:3] + "." + line[3:] + " today"),
        ("phone, 7 digits", line, "call " + line[:3] + "-" + line[3:] + " today"),
        ("phone, phone= key", area + line, "phone=" + area + line),
        ("SSN shape 3-2-4", ssn.replace("-", ""), "ssn " + ssn + " on file"),
        ("SSN digits, contiguous", ssn.replace("-", ""), "ssn " + ssn.replace("-", "") + " on file"),
    ]


def gap3() -> tuple[int, int, int]:
    print("## Gap 3: bare numbers (accepted property: this is a list, not a verdict)\n")
    print("`{N}` stands for the number as written in the input (run-time digits are not printed). "
          "masked = `whole` (no digit run of 4 or more of the number is left), `part` or `NOT masked`.\n")
    print("| # | input shape | input | output (`redact_text`) | map kinds | masked today | `redact_untrusted` same output |")
    print("|---|---|---|---|---|---|---|")
    n = unmasked = part = 0
    for shape, number, text in gap3_cases():
        out, kinds = run(runmap.redact_text, text)
        out_u, _ = run(runmap.redact_untrusted, text)
        residue = PLACEHOLDER.sub("|", out)
        # digit runs left in the output, separators inside a number ignored
        squeezed = re.sub(r"(?<=\d)[ .\-()](?=\d)|(?<=\d)\) (?=\d)", "", residue)
        left = lcs(number, squeezed)
        if left >= len(number):
            state = "NOT masked"
            unmasked += 1
        elif left >= 4:
            state = f"part ({left} of {len(number)} digits left)"
            part += 1
        else:
            state = "whole"
        n += 1
        written = next((w for w in sorted(set(re.findall(r"[\d][\d .\-()]*\d", text)), key=len, reverse=True) if re.sub(r"\D", "", w).endswith(number[-4:])), number)
        hide = {} if number == "5555" + "6666" else {written: "{N}", number: "{N}"}
        print(f"| {n} | {shape} | {cell(show(text, hide, False))} | {cell(show(out, hide, False))} | {', '.join(kinds) or '-'} | {state} | {'yes' if out_u == out else 'NO: ' + cell(show(out_u, hide, False))} |")
    print(f"\nGap 3 counts: cases {n}, NOT masked {unmasked}, masked in part {part}, masked whole {n - unmasked - part}.\n")
    return n, unmasked, part


def main() -> None:
    print("# P1c probe output\n")
    print(f"- module: `{hadavin_sdk.__file__}`")
    print(f"- python: {sys.version.split()[0]}; seed 20261120")
    print(f"- views of `runmap._views` on a plain ASCII base64 line: {len(runmap._views('cGxhaW4gdGV4dA=='))} (0 = no decoded view exists)\n")
    g1 = gap1()
    g2 = gap2()
    g3 = gap3()
    print("## Totals\n")
    print("| gap | cases | leaked / not masked |\n|---|---|---|")
    print(f"| 1 base64 (1b + 1c) | {g1[0]} | {g1[1]} leaked ({g1[2]} of the rest held by HIGHENTROPY) |")
    print(f"| 2 host names | {g2[0]} | {g2[1]} leaked |")
    print(f"| 3 bare numbers | {g3[0]} | {g3[1]} not masked, {g3[2]} in part |")


if __name__ == "__main__":
    main()
```

## Full output of the run (verbatim)

#### Run header

- module: `/tmp/core-c-p1c/src/hadavin_sdk/__init__.py`
- python: 3.13.18; seed 20261120
- views of `runmap._views` on a plain ASCII base64 line: 0 (0 = no decoded view exists)

### Gap 1: base64-encoded values

#### 1a. Baseline: the plain form IS masked

| value | carrier | input shape | output | map kinds | LEAKED |
|---|---|---|---|---|---|
| kv secret | short (18 chars) | `pwd={pw14} / log line with db_password={pw14}` | `pwd=<SECRET_1>` | SECRET | no |
| kv secret | long (67 chars) | `pwd={pw14} / log line with db_password={pw14}` | `2026-11-20T10:00:00Z deploy step db_password=<SECRET_1> applied` | SECRET | no |
| bearer token | short (35 chars) | `Bearer {tok28} / request line with Authorization: Bearer {tok28}` | `Bearer <BEARER_1>` | BEARER | no |
| bearer token | long (75 chars) | `Bearer {tok28} / request line with Authorization: Bearer {tok28}` | `GET /v1/items Authorization: Bearer <BEARER_1> status 200` | BEARER | no |
| AWS key id (doc example) | short (20 chars) | `AKIAIOSFODNN7EXAMPLE / error line holding it` | `<APIKEY_1>` | APIKEY | no |
| AWS key id (doc example) | long (66 chars) | `AKIAIOSFODNN7EXAMPLE / error line holding it` | `boto error: key id <APIKEY_1> is not allowed to call sts` | APIKEY | no |
| e-mail address | short (25 chars) | `ann.lee@mail.acme.example / log line holding it` | `<EMAIL_1>` | EMAIL | no |
| e-mail address | long (72 chars) | `ann.lee@mail.acme.example / log line holding it` | `refund mail queued for <EMAIL_1> at 10:02:11 by worker 3` | EMAIL | no |
| internal host name | short (14 chars) | `db01.prod.corp / log line holding it` | `<HOSTNAME_1>` | HOSTNAME | no |
| internal host name | long (61 chars) | `db01.prod.corp / log line holding it` | `connection refused while dialling <HOSTNAME_1> on port 5432` | HOSTNAME | no |
| private IPv4 | short (11 chars) | `10.20.30.40 / log line holding it` | `<IPV4_1>` | IPV4 | no |
| private IPv4 | long (57 chars) | `10.20.30.40 / log line holding it` | `upstream <IPV4_1> timed out after 30 seconds, retrying` | IPV4 | no |
| connection string | short (24 chars) | `pg://u:{pw12}@db/x / postgres://app:{pw12}@db.acme.example:5432/orders` | `pg://u:<URLCRED_1>@db/x` | URLCRED | no |
| connection string | long (71 chars) | `pg://u:{pw12}@db/x / postgres://app:{pw12}@db.acme.example:5432/orders` | `DATABASE_URL is postgres://app:<URLCRED_1>@db.acme.example:5432/orders` | URLCRED | no |
| JSON with password | short (28 chars) | `{"password": "{pw12}"} / {"user": "app", "password": "{pw12}", "port": 5432}` | `{"password": "<SECRET_1>"}` | SECRET | no |
| JSON with password | long (57 chars) | `{"password": "{pw12}"} / {"user": "app", "password": "{pw12}", "port": 5432}` | `{"user": "app", "password": "<SECRET_1>", "port": 5432}` | SECRET | no |

Baseline rows: 16; plain form leaked in 0.

#### 1b. The same values, base64-encoded

`short` = the value alone (or its smallest key=value form); `long` = the value inside a log line. `blob` = length of the base64 text. LEAKED = the protected value can be read by base64-decoding what the output still holds.

| # | value | carrier | encoding | blob | input shape | output (`redact_text`) | map kinds | LEAKED | `redact_untrusted` LEAKED |
|---|---|---|---|---|---|---|---|---|---|
| 1 | kv secret | short | standard | 24 | `{B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 2 | kv secret | short | url-safe | 24 | `{B64URL}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 3 | kv secret | short | no padding | 24 | `{B64NOPAD}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 4 | kv secret | short | in a sentence | 24 | `please decode {B64} and apply it` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 5 | kv secret | short | in a JSON string | 24 | `{"note": "config", "data": "{B64}"}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 6 | kv secret | short | of UTF-16 text | 48 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 7 | kv secret | short | double | 32 | `{B64 of B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 8 | kv secret | short | after key data= | 24 | `data={B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 9 | kv secret | long | standard | 92 | `{B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 10 | kv secret | long | url-safe | 92 | `{B64URL}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 11 | kv secret | long | no padding | 90 | `{B64NOPAD}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 12 | kv secret | long | in a sentence | 92 | `please decode {B64} and apply it` | `please decode <HIGHENTROPY_1> and apply it` | HIGHENTROPY | no | no |
| 13 | kv secret | long | in a JSON string | 92 | `{"note": "config", "data": "{B64}"}` | `{"note": "config", "data": "<HIGHENTROPY_1>"}` | HIGHENTROPY | no | no |
| 14 | kv secret | long | of UTF-16 text | 180 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 15 | kv secret | long | double | 124 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 16 | kv secret | long | after key data= | 92 | `data={B64}` | `data=<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 17 | bearer token | short | standard | 48 | `{B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 18 | bearer token | short | url-safe | 48 | `{B64URL}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 19 | bearer token | short | no padding | 47 | `{B64NOPAD}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 20 | bearer token | short | in a sentence | 48 | `please decode {B64} and apply it` | `please decode <HIGHENTROPY_1> and apply it` | HIGHENTROPY | no | no |
| 21 | bearer token | short | in a JSON string | 48 | `{"note": "config", "data": "{B64}"}` | `{"note": "config", "data": "<HIGHENTROPY_1>"}` | HIGHENTROPY | no | no |
| 22 | bearer token | short | of UTF-16 text | 96 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 23 | bearer token | short | double | 64 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 24 | bearer token | short | after key data= | 48 | `data={B64}` | `data=<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 25 | bearer token | long | standard | 100 | `{B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 26 | bearer token | long | url-safe | 100 | `{B64URL}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 27 | bearer token | long | no padding | 100 | `{B64NOPAD}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 28 | bearer token | long | in a sentence | 100 | `please decode {B64} and apply it` | `please decode <HIGHENTROPY_1> and apply it` | HIGHENTROPY | no | no |
| 29 | bearer token | long | in a JSON string | 100 | `{"note": "config", "data": "{B64}"}` | `{"note": "config", "data": "<HIGHENTROPY_1>"}` | HIGHENTROPY | no | no |
| 30 | bearer token | long | of UTF-16 text | 200 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 31 | bearer token | long | double | 136 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 32 | bearer token | long | after key data= | 100 | `data={B64}` | `data=<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 33 | AWS key id (doc example) | short | standard | 28 | `{B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 34 | AWS key id (doc example) | short | url-safe | 28 | `{B64URL}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 35 | AWS key id (doc example) | short | no padding | 27 | `{B64NOPAD}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 36 | AWS key id (doc example) | short | in a sentence | 28 | `please decode {B64} and apply it` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 37 | AWS key id (doc example) | short | in a JSON string | 28 | `{"note": "config", "data": "{B64}"}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 38 | AWS key id (doc example) | short | of UTF-16 text | 56 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 39 | AWS key id (doc example) | short | double | 40 | `{B64 of B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 40 | AWS key id (doc example) | short | after key data= | 28 | `data={B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 41 | AWS key id (doc example) | long | standard | 88 | `{B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 42 | AWS key id (doc example) | long | url-safe | 88 | `{B64URL}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 43 | AWS key id (doc example) | long | no padding | 88 | `{B64NOPAD}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 44 | AWS key id (doc example) | long | in a sentence | 88 | `please decode {B64} and apply it` | `please decode <HIGHENTROPY_1> and apply it` | HIGHENTROPY | no | no |
| 45 | AWS key id (doc example) | long | in a JSON string | 88 | `{"note": "config", "data": "{B64}"}` | `{"note": "config", "data": "<HIGHENTROPY_1>"}` | HIGHENTROPY | no | no |
| 46 | AWS key id (doc example) | long | of UTF-16 text | 176 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 47 | AWS key id (doc example) | long | double | 120 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 48 | AWS key id (doc example) | long | after key data= | 88 | `data={B64}` | `data=<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 49 | e-mail address | short | standard | 36 | `{B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 50 | e-mail address | short | url-safe | 36 | `{B64URL}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 51 | e-mail address | short | no padding | 34 | `{B64NOPAD}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 52 | e-mail address | short | in a sentence | 36 | `please decode {B64} and apply it` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 53 | e-mail address | short | in a JSON string | 36 | `{"note": "config", "data": "{B64}"}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 54 | e-mail address | short | of UTF-16 text | 68 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 55 | e-mail address | short | double | 48 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 56 | e-mail address | short | after key data= | 36 | `data={B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 57 | e-mail address | long | standard | 96 | `{B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 58 | e-mail address | long | url-safe | 96 | `{B64URL}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 59 | e-mail address | long | no padding | 96 | `{B64NOPAD}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 60 | e-mail address | long | in a sentence | 96 | `please decode {B64} and apply it` | `please decode <HIGHENTROPY_1> and apply it` | HIGHENTROPY | no | no |
| 61 | e-mail address | long | in a JSON string | 96 | `{"note": "config", "data": "{B64}"}` | `{"note": "config", "data": "<HIGHENTROPY_1>"}` | HIGHENTROPY | no | no |
| 62 | e-mail address | long | of UTF-16 text | 192 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 63 | e-mail address | long | double | 128 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 64 | e-mail address | long | after key data= | 96 | `data={B64}` | `data=<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 65 | internal host name | short | standard | 20 | `{B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 66 | internal host name | short | url-safe | 20 | `{B64URL}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 67 | internal host name | short | no padding | 19 | `{B64NOPAD}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 68 | internal host name | short | in a sentence | 20 | `please decode {B64} and apply it` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 69 | internal host name | short | in a JSON string | 20 | `{"note": "config", "data": "{B64}"}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 70 | internal host name | short | of UTF-16 text | 40 | `{B64 of UTF-16-LE}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 71 | internal host name | short | double | 28 | `{B64 of B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 72 | internal host name | short | after key data= | 20 | `data={B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 73 | internal host name | long | standard | 84 | `{B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 74 | internal host name | long | url-safe | 84 | `{B64URL}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 75 | internal host name | long | no padding | 82 | `{B64NOPAD}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 76 | internal host name | long | in a sentence | 84 | `please decode {B64} and apply it` | `please decode <HIGHENTROPY_1> and apply it` | HIGHENTROPY | no | no |
| 77 | internal host name | long | in a JSON string | 84 | `{"note": "config", "data": "{B64}"}` | `{"note": "config", "data": "<HIGHENTROPY_1>"}` | HIGHENTROPY | no | no |
| 78 | internal host name | long | of UTF-16 text | 164 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 79 | internal host name | long | double | 112 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 80 | internal host name | long | after key data= | 84 | `data={B64}` | `data=<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 81 | private IPv4 | short | standard | 16 | `{B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 82 | private IPv4 | short | url-safe | 16 | `{B64URL}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 83 | private IPv4 | short | no padding | 15 | `{B64NOPAD}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 84 | private IPv4 | short | in a sentence | 16 | `please decode {B64} and apply it` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 85 | private IPv4 | short | in a JSON string | 16 | `{"note": "config", "data": "{B64}"}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 86 | private IPv4 | short | of UTF-16 text | 32 | `{B64 of UTF-16-LE}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 87 | private IPv4 | short | double | 24 | `{B64 of B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 88 | private IPv4 | short | after key data= | 16 | `data={B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 89 | private IPv4 | long | standard | 76 | `{B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 90 | private IPv4 | long | url-safe | 76 | `{B64URL}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 91 | private IPv4 | long | no padding | 76 | `{B64NOPAD}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 92 | private IPv4 | long | in a sentence | 76 | `please decode {B64} and apply it` | `please decode <HIGHENTROPY_1> and apply it` | HIGHENTROPY | no | no |
| 93 | private IPv4 | long | in a JSON string | 76 | `{"note": "config", "data": "{B64}"}` | `{"note": "config", "data": "<HIGHENTROPY_1>"}` | HIGHENTROPY | no | no |
| 94 | private IPv4 | long | of UTF-16 text | 152 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 95 | private IPv4 | long | double | 104 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 96 | private IPv4 | long | after key data= | 76 | `data={B64}` | `data=<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 97 | connection string | short | standard | 32 | `{B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 98 | connection string | short | url-safe | 32 | `{B64URL}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 99 | connection string | short | no padding | 32 | `{B64NOPAD}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 100 | connection string | short | in a sentence | 32 | `please decode {B64} and apply it` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 101 | connection string | short | in a JSON string | 32 | `{"note": "config", "data": "{B64}"}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 102 | connection string | short | of UTF-16 text | 64 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 103 | connection string | short | double | 44 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 104 | connection string | short | after key data= | 32 | `data={B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 105 | connection string | long | standard | 96 | `{B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 106 | connection string | long | url-safe | 96 | `{B64URL}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 107 | connection string | long | no padding | 95 | `{B64NOPAD}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 108 | connection string | long | in a sentence | 96 | `please decode {B64} and apply it` | `please decode <HIGHENTROPY_1> and apply it` | HIGHENTROPY | no | no |
| 109 | connection string | long | in a JSON string | 96 | `{"note": "config", "data": "{B64}"}` | `{"note": "config", "data": "<HIGHENTROPY_1>"}` | HIGHENTROPY | no | no |
| 110 | connection string | long | of UTF-16 text | 192 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 111 | connection string | long | double | 128 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 112 | connection string | long | after key data= | 96 | `data={B64}` | `data=<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 113 | JSON with password | short | standard | 40 | `{B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 114 | JSON with password | short | url-safe | 40 | `{B64URL}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 115 | JSON with password | short | no padding | 38 | `{B64NOPAD}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 116 | JSON with password | short | in a sentence | 40 | `please decode {B64} and apply it` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 117 | JSON with password | short | in a JSON string | 40 | `{"note": "config", "data": "{B64}"}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 118 | JSON with password | short | of UTF-16 text | 76 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 119 | JSON with password | short | double | 56 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 120 | JSON with password | short | after key data= | 40 | `data={B64}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 121 | JSON with password | long | standard | 76 | `{B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 122 | JSON with password | long | url-safe | 76 | `{B64URL}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 123 | JSON with password | long | no padding | 76 | `{B64NOPAD}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 124 | JSON with password | long | in a sentence | 76 | `please decode {B64} and apply it` | `please decode <HIGHENTROPY_1> and apply it` | HIGHENTROPY | no | no |
| 125 | JSON with password | long | in a JSON string | 76 | `{"note": "config", "data": "{B64}"}` | `{"note": "config", "data": "<HIGHENTROPY_1>"}` | HIGHENTROPY | no | no |
| 126 | JSON with password | long | of UTF-16 text | 152 | `{B64 of UTF-16-LE}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 127 | JSON with password | long | double | 104 | `{B64 of B64}` | `<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 128 | JSON with password | long | after key data= | 76 | `data={B64}` | `data=<HIGHENTROPY_1>` | HIGHENTROPY | no | no |

Gap 1b counts: cases 128, leaked 48, not leaked 80 (of these, HIGHENTROPY in the map: 80).

| encoding | cases | leaked |
|---|---|---|
| standard | 16 | 7 |
| url-safe | 16 | 7 |
| no padding | 16 | 7 |
| in a sentence | 16 | 7 |
| in a JSON string | 16 | 7 |
| of UTF-16 text | 16 | 2 |
| double | 16 | 4 |
| after key data= | 16 | 7 |

By blob length: under 40 characters: 41 cases, 41 leaked; 40 or more: 87 cases, 7 leaked.

#### 1c. Long blobs that HIGHENTROPY might not hold (the long carrier, 40 or more base64 characters)

| # | value | form | longest unbroken run | input shape | output (`redact_text`) | map kinds | LEAKED | `redact_untrusted` LEAKED |
|---|---|---|---|---|---|---|---|---|
| - | e-mail address | blob with no digit | - | NOT CONSTRUCTED: no such line found in the search | - | - | - | - |
| - | internal host name | blob with no digit | - | NOT CONSTRUCTED: no such line found in the search | - | - | - | - |
| 1 | kv secret | wrapped at 32 characters | 32 | `{B64 lines of 32}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 2 | kv secret | wrapped at 64 characters (PEM style) | 64 | `{B64 lines of 64}` | `<HIGHENTROPY_1>\n{BLOB LINE}` | HIGHENTROPY | YES (part, 11 of 14 chars) | YES (part, 11 of 14 chars) |
| 3 | kv secret | wrapped at 76 characters (MIME style) | 76 | `{B64 lines of 76}` | `<HIGHENTROPY_1>\n{BLOB LINE}` | HIGHENTROPY | no | no |
| 4 | kv secret | data: URL | 92 | `data:text/plain;base64,{B64}` | `data:text/plain;base64,<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 5 | e-mail address | wrapped at 32 characters | 32 | `{B64 lines of 32}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 6 | e-mail address | wrapped at 64 characters (PEM style) | 64 | `{B64 lines of 64}` | `<HIGHENTROPY_1>\n{BLOB LINE}` | HIGHENTROPY | no | no |
| 7 | e-mail address | wrapped at 76 characters (MIME style) | 76 | `{B64 lines of 76}` | `<HIGHENTROPY_1>\n{BLOB LINE}` | HIGHENTROPY | no | no |
| 8 | e-mail address | data: URL | 96 | `data:text/plain;base64,{B64}` | `data:text/plain;base64,<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 9 | internal host name | wrapped at 32 characters | 32 | `{B64 lines of 32}` | `UNCHANGED` | - | YES (whole) | YES (whole) |
| 10 | internal host name | wrapped at 64 characters (PEM style) | 64 | `{B64 lines of 64}` | `<HIGHENTROPY_1>\n{BLOB LINE}` | HIGHENTROPY | no | no |
| 11 | internal host name | wrapped at 76 characters (MIME style) | 76 | `{B64 lines of 76}` | `<HIGHENTROPY_1>\nNTQzMg==` | HIGHENTROPY | no | no |
| 12 | internal host name | data: URL | 84 | `data:text/plain;base64,{B64}` | `data:text/plain;base64,<HIGHENTROPY_1>` | HIGHENTROPY | no | no |
| 13 | kv secret | HTTP Basic header (base64 of user:{pw14}) | 24 | `Authorization: Basic {B64 of app:{pw14}}` | `Authorization: Basic <BASIC_1>` | BASIC | no | no |
| 14 | kv secret | word Basic + short blob | 24 | `Basic {B64}` | `Basic <BASIC_1>` | BASIC | no | no |

Gap 1c counts: cases 14, leaked 4, held by HIGHENTROPY 8.

### Gap 2: internal host names

LEAKED = at least one label of the name is still readable in the output (`kept` lists them; a placeholder hides the rest). The sentence around the name shares no label with it.

| # | input shape | input | output (`redact_text`) | map kinds | kept labels | LEAKED | `redact_untrusted` same output |
|---|---|---|---|---|---|---|---|
| 1 | corp + .example | `dial db01.corp.example now` | `dial <HOSTNAME_1>.example now` | HOSTNAME | example | YES (part) | yes |
| 2 | 4 labels, corp + .example | `dial billing-db.prod.corp.example now` | `dial <HOSTNAME_1>.example now` | HOSTNAME | example | YES (part) | yes |
| 3 | name ends at corp | `dial db01.prod.corp now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 4 | a.b.c.internal | `dial a.b.c.internal now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 5 | words under .internal | `dial orders.payments.internal now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 6 | .internal then more labels | `dial db01.internal.acme.example now` | `dial db01.internal.acme.example now` | - | db01, internal, acme, example | YES (whole name) | yes |
| 7 | host.local | `dial printer7.local now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 8 | .local then more labels | `dial db01.local.acme.example now` | `dial db01.local.acme.example now` | - | db01, local, acme, example | YES (whole name) | yes |
| 9 | k8s service, cluster.local | `dial billing.payments.svc.cluster.local now` | `dial billing.payments.svc.cluster.local now` | - | billing, payments, svc, cluster, local | YES (whole name) | yes |
| 10 | k8s service, short form | `dial billing.payments.svc now` | `dial billing.payments.svc now` | - | billing, payments, svc | YES (whole name) | yes |
| 11 | .lan | `dial nas02.office.lan now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 12 | .intranet | `dial wiki.acme.intranet now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 13 | .home.arpa | `dial router.home.arpa now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 14 | .localdomain | `dial build03.localdomain now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 15 | reserved TLD only (.example) | `dial db01.acme.example now` | `dial db01.acme.example now` | - | db01, acme, example | YES (whole name) | yes |
| 16 | reserved TLD only (.test) | `dial db01.acme.test now` | `dial db01.acme.test now` | - | db01, acme, test | YES (whole name) | yes |
| 17 | with a port | `dial db01.corp.example:5432 now` | `dial <HOSTNAME_1>.example:5432 now` | HOSTNAME | example | YES (part) | yes |
| 18 | .internal with a port | `dial a.b.c.internal:8080 now` | `dial <HOSTNAME_1>:8080 now` | HOSTNAME | - | no | yes |
| 19 | inside a URL | `GET https://db01.corp.example/v1/items done` | `GET https://<HOSTNAME_1>.example/v1/items done` | HOSTNAME | example | YES (part) | yes |
| 20 | .internal inside a URL with port | `GET http://a.b.c.internal:8080/v1/items done` | `GET http://<HOSTNAME_1>:8080/v1/items done` | HOSTNAME | - | no | yes |
| 21 | inside a URL with credentials | `use postgres://app:{pw10}@db01.corp.example:5432/orders now` | `use postgres://app:<URLCRED_1>@<HOSTNAME_1>.example:5432/orders now` | HOSTNAME, URLCRED | example | YES (part) | yes |
| 22 | e-mail domain | `write to ops@mail.corp.example now` | `write to <EMAIL_1> now` | EMAIL | - | no | yes |
| 23 | e-mail domain .internal | `write to ops@mail.acme.internal now` | `write to <EMAIL_1> now` | EMAIL | - | no | yes |
| 24 | upper case | `dial DB01.CORP.EXAMPLE now` | `dial <HOSTNAME_1>.EXAMPLE now` | HOSTNAME | example | YES (part) | yes |
| 25 | upper case .INTERNAL | `dial A.B.C.INTERNAL now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 26 | trailing dot | `dial db01.corp.example. now` | `dial <HOSTNAME_1>.example. now` | HOSTNAME | example | YES (part) | yes |
| 27 | .internal trailing dot | `dial a.b.c.internal. now` | `dial <HOSTNAME_1>. now` | HOSTNAME | - | no | yes |
| 28 | .local trailing dot + word | `dial printer7.local.\nnext line` | `dial <HOSTNAME_1>.\nnext line` | HOSTNAME | - | no | yes |
| 29 | punycode label + corp.example | `dial xn--bcher-kva.corp.example now` | `dial <HOSTNAME_1>.example now` | HOSTNAME | example | YES (part) | yes |
| 30 | punycode label + .internal | `dial xn--bcher-kva.internal now` | `dial <HOSTNAME_1> now` | HOSTNAME | - | no | yes |
| 31 | non-ASCII label + .internal | `dial bücher.internal now` | `dial bücher.internal now` | - | bücher, internal | YES (whole name) | yes |
| 32 | underscore in a label | `dial db_01.corp.example now` | `dial db_01.corp.example now` | - | db_01, corp, example | YES (whole name) | yes |
| 33 | single label after 'host' | `host db01 is down` | `host db01 is down` | - | db01 | YES (whole name) | yes |
| 34 | single label, host: key | `host: db01` | `host: db01` | - | db01 | YES (whole name) | yes |
| 35 | single label, hostname= key | `hostname=db01 state=down` | `hostname=db01 state=down` | - | db01 | YES (whole name) | yes |
| 36 | single label, --host flag | `psql --host db01 --port 5432` | `psql --host db01 --port 5432` | - | db01 | YES (whole name) | yes |
| 37 | key=value host= | `host=db01.corp.example port=5432` | `host=<HOSTNAME_1>.example port=5432` | HOSTNAME | example | YES (part) | yes |
| 38 | JSON value | `{"host": "db01.corp.example", "port": 5432}` | `{"host": "<HOSTNAME_1>.example", "port": 5432}` | HOSTNAME | example | YES (part) | yes |
| 39 | JSON-escaped dots (\u002e) | `dial db01\u002ecorp\u002eexample now` | `dial <HOSTNAME_1>.example now` | HOSTNAME | example | YES (part) | yes |
| 40 | percent-encoded dots | `dial db01%2Ecorp%2Eexample now` | `dial <HOSTNAME_1>.example now` | HOSTNAME | example | YES (part) | yes |
| 41 | full-width dots | `dial db01．corp．example now` | `dial <HOSTNAME_1>.example now` | HOSTNAME | example | YES (part) | yes |
| 42 | AWS private DNS name | `node ip-10-0-3-22.eu-west-1.compute.internal ready` | `node ip-<IPV4_1>.eu-west-1.compute.internal ready` | IPV4 | eu-west-1, compute, internal | YES (part) | yes |
| 43 | defanged dots [.] | `dial db01[.]corp[.]example now` | `dial db01[.]corp[.]example now` | - | db01, corp, example | YES (whole name) | yes |
| 44 | two names in one line | `from db01.corp.example to db02.corp.example done` | `from <HOSTNAME_1>.example to <HOSTNAME_2>.example done` | HOSTNAME | example | YES (part) | yes |

Gap 2 counts: cases 44, leaked 28 (whole name readable 13, part readable 15), fully masked 16.

### Gap 3: bare numbers (accepted property: this is a list, not a verdict)

`{N}` stands for the number as written in the input (run-time digits are not printed). masked = `whole` (no digit run of 4 or more of the number is left), `part` or `NOT masked`.

| # | input shape | input | output (`redact_text`) | map kinds | masked today | `redact_untrusted` same output |
|---|---|---|---|---|---|---|
| 1 | the ticket's line, 8 digits, no label | `ref 55556666 paid` | `ref 55556666 paid` | - | NOT masked | yes |
| 2 | 8 digits alone | `55556666` | `55556666` | - | NOT masked | yes |
| 3 | label account | `account 55556666 paid` | `account 55556666 paid` | - | NOT masked | yes |
| 4 | label account number | `account number 55556666` | `account number 55556666` | - | NOT masked | yes |
| 5 | label account no: | `account no: 55556666` | `account no: 55556666` | - | NOT masked | yes |
| 6 | label acct= | `acct=55556666` | `acct=55556666` | - | NOT masked | yes |
| 7 | account + bank word nearby | `bank transfer to account 55556666 failed` | `bank transfer to account 55556666 failed` | - | NOT masked | yes |
| 8 | after a BSB code | `BSB 062-000 account 55556666` | `BSB <BANKCODE_1> account <BANKACCT_1>` | BANKACCT, BANKCODE | whole | yes |
| 9 | label invoice no | `invoice no 55556666 paid` | `invoice no 55556666 paid` | - | NOT masked | yes |
| 10 | label invoice # | `invoice #55556666 paid` | `invoice #55556666 paid` | - | NOT masked | yes |
| 11 | label order | `order {N} shipped` | `order {N} shipped` | - | NOT masked | yes |
| 12 | label card, 8 digits | `card 55556666 declined` | `card 55556666 declined` | - | NOT masked | yes |
| 13 | label customer_id= | `customer_id=55556666` | `customer_id=<TENANT_1>` | TENANT | whole | yes |
| 14 | label id: | `id:55556666` | `id:55556666` | - | NOT masked | yes |
| 15 | 8 digits with a hyphen | `ref 5555-6666 paid` | `ref 5555-6666 paid` | - | NOT masked | yes |
| 16 | 8 digits with a space | `ref 5555 6666 paid` | `ref 5555 6666 paid` | - | NOT masked | yes |
| 17 | 8 digits with a dot | `ref 5555.6666 paid` | `ref 5555.6666 paid` | - | NOT masked | yes |
| 18 | amount with decimals | `amount 55556666.00 EUR` | `amount 55556666.00 EUR` | - | NOT masked | yes |
| 19 | 6 digits | `ref {N} paid` | `ref {N} paid` | - | NOT masked | yes |
| 20 | 9 digits | `ref {N} paid` | `ref {N} paid` | - | NOT masked | yes |
| 21 | 10 digits | `ref {N} paid` | `ref <PHONE_1> paid` | PHONE | whole | yes |
| 22 | 11 digits | `ref {N} paid` | `ref <PHONE_1> paid` | PHONE | whole | yes |
| 23 | 12 digits | `ref {N} paid` | `ref <ACCOUNTID_1> paid` | ACCOUNTID | whole | yes |
| 24 | 14 digits (not a timestamp) | `ref {N} paid` | `ref <PHONE_1> paid` | PHONE | whole | yes |
| 25 | 16 digits Luhn ok, no label, contiguous | `ref {N} paid` | `ref <PHONE_1> paid` | PHONE | whole | yes |
| 26 | 16 digits Luhn ok, label card, contiguous | `card {N} declined` | `card <PHONE_1> declined` | PHONE | whole | yes |
| 27 | 16 digits Luhn ok, groups with spaces | `card {N} declined` | `card <CREDITCARD_1> declined` | CREDITCARD | whole | yes |
| 28 | 16 digits Luhn ok, groups with hyphens | `card {N} declined` | `card <CREDITCARD_1> declined` | CREDITCARD | whole | yes |
| 29 | 16 digits Luhn ok, groups with dots | `card {N} declined` | `card <MAC_1>.9822 declined` | MAC | part (4 of 16 digits left) | yes |
| 30 | 16 digits Luhn ok, glued to a word | `card{N}x declined` | `card{N}x declined` | - | NOT masked | yes |
| 31 | 16 digits Luhn ok, after id= | `pan={N}` | `pan=<PHONE_1>` | PHONE | whole | yes |
| 32 | 15 digits Luhn ok (4-6-5 groups) | `card {N} declined` | `card <PHONE_1> 97954 declined` | PHONE | part (5 of 15 digits left) | yes |
| 33 | 15 digits Luhn ok, contiguous | `card {N} declined` | `card <PHONE_1> declined` | PHONE | whole | yes |
| 34 | 13 digits Luhn ok, contiguous | `card {N} declined` | `card <PHONE_1> declined` | PHONE | whole | yes |
| 35 | last four only | `card ending {N} declined` | `card ending {N} declined` | - | NOT masked | yes |
| 36 | phone, +1 and hyphens | `call +{N} today` | `call <PHONE_1> today` | PHONE | whole | yes |
| 37 | phone, contiguous 10 digits | `call {N} today` | `call <PHONE_1> today` | PHONE | whole | yes |
| 38 | phone, brackets | `call ({N} today` | `call ({N} today` | - | NOT masked | yes |
| 39 | phone, dots | `call {N} today` | `call {N} today` | - | NOT masked | yes |
| 40 | phone, 7 digits | `call {N} today` | `call {N} today` | - | NOT masked | yes |
| 41 | phone, phone= key | `phone={N}` | `phone=<PHONE_1>` | PHONE | whole | yes |
| 42 | SSN shape 3-2-4 | `ssn {N} on file` | `ssn <SSN_1> on file` | SSN | whole | yes |
| 43 | SSN digits, contiguous | `ssn {N} on file` | `ssn {N} on file` | - | NOT masked | yes |

Gap 3 counts: cases 43, NOT masked 24, masked in part 2, masked whole 17.

### Totals

| gap | cases | leaked / not masked |
|---|---|---|
| 1 base64 (1b + 1c) | 142 | 52 leaked (88 of the rest held by HIGHENTROPY) |
| 2 host names | 44 | 28 leaked |
| 3 bare numbers | 43 | 24 not masked, 2 in part |
