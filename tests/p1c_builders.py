"""The three input builders of the P1c probe, moved here from handover/core-c/evidence/p1c_probe.py (G7 fix round 4, codebase M5/M4).

tests/test_redact_idempotent_property.py builds its `p1c-gap1`, `p1c-gap2` and `p1c-gap3` inputs (16 + 44 + 43) from them. The property
test no longer loads an evidence file: a pruned handover folder cannot take the whole collection down. The bodies are copied
unchanged, with the same module-level `RNG`; `reseed()` puts it where the probe's own seed puts it, so the rows are the same on
every run. They were checked ONCE against the probe file (G7 fix round 5: gap1 8 rows, gap2 44, gap3 43, all equal, from the same seed, run
by a throwaway check whose output is in handover/core-c/evidence/G7-1.md) and that check was then deleted: no test reads the probe or any
other handover file. Every credential is made up from parts (the documented AWS example id is the only literal of its kind).
"""

from __future__ import annotations

import json
import random
import string

SEED = 20261120
RNG = random.Random(SEED)  # noqa: S311 - the probe's seeded generator, not a secret


def reseed() -> None:
    """Back to the probe's seed: the builders called in the order gap1_values, gap2_cases, gap3_cases give the same rows every time."""
    RNG.seed(SEED)


def rand(n: int, alphabet: str = string.ascii_letters + string.digits) -> str:
    """n characters with at least one upper, one lower and one digit (so it looks like a real credential)."""
    while True:
        s = "".join(RNG.choice(alphabet) for _ in range(n))
        if alphabet != string.ascii_letters + string.digits:
            return s
        if (
            any(c.isupper() for c in s)
            and any(c.islower() for c in s)
            and any(c.isdigit() for c in s)
        ):
            return s


def gap1_values() -> list[dict]:
    pw = rand(14)
    tok = rand(28)
    akia = "AKIA" + "IOSFODNN7" + "EXAMPLE"  # AWS's documented example id, nothing else
    mail = "ann.lee" + "@" + "mail.acme.example"
    host = "db01.prod.corp"
    ip = "10.20.30.40"
    cpw = rand(12)
    jpw = rand(12)
    return [
        {
            "name": "kv secret",
            "protected": pw,
            "short": "pwd=" + pw,
            "long": "2026-11-20T10:00:00Z deploy step db_password=" + pw + " applied",
            "shape": "pwd={pw14} / log line with db_password={pw14}",
        },
        {
            "name": "bearer token",
            "protected": tok,
            "short": "Bearer " + tok,
            "long": "GET /v1/items Authorization: Bearer " + tok + " status 200",
            "shape": "Bearer {tok28} / request line with Authorization: Bearer {tok28}",
        },
        {
            "name": "AWS key id (doc example)",
            "protected": akia,
            "short": akia,
            "long": "boto error: key id " + akia + " is not allowed to call sts",
            "shape": "AKIAIOSFODNN7EXAMPLE / error line holding it",
        },
        {
            "name": "e-mail address",
            "protected": mail,
            "short": mail,
            "long": "refund mail queued for " + mail + " at 10:02:11 by worker 3",
            "shape": "ann.lee@mail.acme.example / log line holding it",
        },
        {
            "name": "internal host name",
            "protected": host,
            "short": host,
            "long": "connection refused while dialling " + host + " on port 5432",
            "shape": "db01.prod.corp / log line holding it",
        },
        {
            "name": "private IPv4",
            "protected": ip,
            "short": ip,
            "long": "upstream " + ip + " timed out after 30 seconds, retrying",
            "shape": "10.20.30.40 / log line holding it",
        },
        {
            "name": "connection string",
            "protected": cpw,
            "short": "pg://u:" + cpw + "@db/x",
            "long": "DATABASE_URL is postgres://app:" + cpw + "@db.acme.example:5432/orders",
            "shape": "pg://u:{pw12}@db/x / postgres://app:{pw12}@db.acme.example:5432/orders",
        },
        {
            "name": "JSON with password",
            "protected": jpw,
            "short": json.dumps({"password": jpw}),
            "long": json.dumps({"user": "app", "password": jpw, "port": 5432}),
            "shape": '{"password": "{pw12}"} / {"user": "app", "password": "{pw12}", "port": 5432}',
        },
    ]


def gap2_cases() -> list[tuple[str, str, str]]:
    """(shape, name, text). The name is made up; the sentence around it shares no label with it."""
    cpw = rand(10)
    c = [
        ("corp + .example", "db01.corp.example", "dial db01.corp.example now"),
        (
            "4 labels, corp + .example",
            "billing-db.prod.corp.example",
            "dial billing-db.prod.corp.example now",
        ),
        ("name ends at corp", "db01.prod.corp", "dial db01.prod.corp now"),
        ("a.b.c.internal", "a.b.c.internal", "dial a.b.c.internal now"),
        ("words under .internal", "orders.payments.internal", "dial orders.payments.internal now"),
        (
            ".internal then more labels",
            "db01.internal.acme.example",
            "dial db01.internal.acme.example now",
        ),
        ("host.local", "printer7.local", "dial printer7.local now"),
        (".local then more labels", "db01.local.acme.example", "dial db01.local.acme.example now"),
        (
            "k8s service, cluster.local",
            "billing.payments.svc.cluster.local",
            "dial billing.payments.svc.cluster.local now",
        ),
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
        (
            ".internal inside a URL with port",
            "a.b.c.internal",
            "GET http://a.b.c.internal:8080/v1/items done",
        ),
        (
            "inside a URL with credentials",
            "db01.corp.example",
            "use postgres://app:" + cpw + "@db01.corp.example:5432/orders now",
        ),
        ("e-mail domain", "mail.corp.example", "write to ops@mail.corp.example now"),
        ("e-mail domain .internal", "mail.acme.internal", "write to ops@mail.acme.internal now"),
        ("upper case", "DB01.CORP.EXAMPLE", "dial DB01.CORP.EXAMPLE now"),
        ("upper case .INTERNAL", "A.B.C.INTERNAL", "dial A.B.C.INTERNAL now"),
        ("trailing dot", "db01.corp.example", "dial db01.corp.example. now"),
        (".internal trailing dot", "a.b.c.internal", "dial a.b.c.internal. now"),
        (".local trailing dot + word", "printer7.local", "dial printer7.local.\nnext line"),
        (
            "punycode label + corp.example",
            "xn--bcher-kva.corp.example",
            "dial xn--bcher-kva.corp.example now",
        ),
        ("punycode label + .internal", "xn--bcher-kva.internal", "dial xn--bcher-kva.internal now"),
        ("non-ASCII label + .internal", "b\u00fccher.internal", "dial b\u00fccher.internal now"),
        ("underscore in a label", "db_01.corp.example", "dial db_01.corp.example now"),
        ("single label after 'host'", "db01", "host db01 is down"),
        ("single label, host: key", "db01", "host: db01"),
        ("single label, hostname= key", "db01", "hostname=db01 state=down"),
        ("single label, --host flag", "db01", "psql --host db01 --port 5432"),
        ("key=value host=", "db01.corp.example", "host=db01.corp.example port=5432"),
        (
            "JSON value",
            "db01.corp.example",
            json.dumps({"host": "db01.corp.example", "port": 5432}),
        ),
        (
            "JSON-escaped dots (\\u002e)",
            "db01.corp.example",
            "dial db01\\u002ecorp\\u002eexample now",
        ),
        ("percent-encoded dots", "db01.corp.example", "dial db01%2Ecorp%2Eexample now"),
        ("full-width dots", "db01.corp.example", "dial db01\uff0ecorp\uff0eexample now"),
        (
            "AWS private DNS name",
            "ip-10-0-3-22.eu-west-1.compute.internal",
            "node ip-10-0-3-22.eu-west-1.compute.internal ready",
        ),
        ("defanged dots [.]", "db01.corp.example", "dial db01[.]corp[.]example now"),
        (
            "two names in one line",
            "db01.corp.example",
            "from db01.corp.example to db02.corp.example done",
        ),
    ]
    return c


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

    def g(s: str, sep: str) -> str:
        return sep.join(s[i : i + 4] for i in range(0, len(s), 4))

    def d(k: int) -> str:
        return rand(1, "123456789") + rand(k - 1, string.digits)

    n6, n7, n9, n10, n11, n12, n14 = d(6), d(7), d(9), d(10), d(11), d(12), d(14)
    area, line = "415", "555" + "01" + rand(2, string.digits)
    ssn = (
        rand(1, "1234578")
        + rand(2, string.digits)
        + "-"
        + rand(1, "123456789")
        + rand(1, string.digits)
        + "-"
        + rand(1, "123456789")
        + rand(3, string.digits)
    )
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
        (
            "15 digits Luhn ok (4-6-5 groups)",
            c15,
            "card " + c15[:4] + " " + c15[4:10] + " " + c15[10:] + " declined",
        ),
        ("15 digits Luhn ok, contiguous", c15, "card " + c15 + " declined"),
        ("13 digits Luhn ok, contiguous", c13, "card " + c13 + " declined"),
        ("last four only", c16[-4:], "card ending " + c16[-4:] + " declined"),
        (
            "phone, +1 and hyphens",
            area + line,
            "call +1 " + area + "-" + line[:3] + "-" + line[3:] + " today",
        ),
        ("phone, contiguous 10 digits", area + line, "call " + area + line + " today"),
        (
            "phone, brackets",
            area + line,
            "call (" + area + ") " + line[:3] + "-" + line[3:] + " today",
        ),
        ("phone, dots", area + line, "call " + area + "." + line[:3] + "." + line[3:] + " today"),
        ("phone, 7 digits", line, "call " + line[:3] + "-" + line[3:] + " today"),
        ("phone, phone= key", area + line, "phone=" + area + line),
        ("SSN shape 3-2-4", ssn.replace("-", ""), "ssn " + ssn + " on file"),
        (
            "SSN digits, contiguous",
            ssn.replace("-", ""),
            "ssn " + ssn.replace("-", "") + " on file",
        ),
    ]
