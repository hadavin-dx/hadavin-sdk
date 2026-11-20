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
