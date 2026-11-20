"""G4c (ticket G4, section 10.4): whole host names and the host-key rule, through `runmap.redact_text` and `redact_untrusted`.

Every assertion message starts with its TB id and one space (the mutants of tests/b64_mutants.py use it as `expect`).
"""

from __future__ import annotations

import importlib
import time

import pytest

from hadavin_sdk.guard import runmap
from tests.warden_port import privacy_corpus

redact_mod = importlib.import_module("hadavin_sdk.guard.redact")


def red(text: str, mapping=None) -> str:
    return runmap.redact_text(text, {} if mapping is None else mapping)


def both(text: str) -> tuple[str, str]:
    return runmap.redact_text(text, {}), runmap.redact_untrusted(text, {})


def test_host_key_masks_db01():
    rows = {
        "host db01 is down": "host <HOSTNAME_1> is down",
        "host: db01": "host: <HOSTNAME_1>",
        "hostname=db01 state=down": "hostname=<HOSTNAME_1> state=down",
        "psql --host db01 --port 5432": "psql --host <HOSTNAME_1> --port 5432",
        "host web-1 down": "host <HOSTNAME_1> down",
    }
    for text, want in rows.items():
        assert red(text) == want, f"TB-4.1 {text}"


KEPT = [
    "host ec2 failed",
    "host k8s node",
    "host x86 box",
    "host http2 on",
    "host x86_64",
    "host eth0 up",
    "host arm64 runner",
    "host: x86_64-unknown-linux-gnu",
    "hostname: Web2",
    "host web1 down",
    "host s3 bucket",
    "server db01 down",
    "host db01.example ok",
    "host x64 build",
    "host win32 target",
    "host win64 target",
    "host x86-64 runner",
    "host riscv64 build",
    "host mips64 build",
    "host sparc64 build",
    "host ia64 build",
    "host wasm32 target",
    "host wasm64 target",
    "host loongarch64 build",
    "host s390 box",
    "host arm32 board",
    "host aarch32 board",
    "host ppc32 box",
    "host riscv32 board",
    "host mips32 board",
    "host ia32 box",
]


def test_host_key_keeps_tech_words():
    for text in KEPT:
        assert red(text) == text, f"TB-4.2 {text}"
    assert red("host srv64 down") == "host <HOSTNAME_1> down", "TB-4.2 the CPU list stays closed"


def test_host_key_cross_compile_triples_are_masked_as_a_stated_over_mask():
    """TB-4.12 (design round 8 N3). A triple is not on the closed list; it is masked after `host` (an over-mask, never a leak)."""
    for text in (
        "host x86_64-w64-mingw32 build",
        "host i686-w64-mingw32 build",
        "host x86_64-apple-darwin20 build",
    ):
        out = red(text)
        assert out == "host <HOSTNAME_1> build", f"TB-4.12 {text}"


def test_host_key_sweep_side_effect():
    text = "host ec2 failed; see ec2.internal, k8s.io, s3://b and x86_64 builds"
    assert red(text) == text, "TB-4.3 no entry for a kept word"
    assert (
        red("host db01 down; tail db01.log") == "host <HOSTNAME_1> down; tail <HOSTNAME_1>.log"
    ), "TB-4.3 sweep"


def test_host_key_two_digit_words_are_masked():
    assert red("host py311 image") == "host <HOSTNAME_1> image", "TB-4.4 py311"
    assert red("host sha256 sum") == "host <HOSTNAME_1> sum", "TB-4.4 sha256"


def test_host_suffix_hyphen_rest():
    for text in (
        "db01.corp-prod",
        "x.local-dev",
        "x.internal-api",
        "db01.corp-prod.example",
        "x.local-dev.foo",
    ):
        assert red(text) == "<HOSTNAME_1>", f"TB-4.5 {text}"


def test_host_start_after_a_bracket_or_a_lone_dot():
    seed = runmap.RunMap({"<HOSTNAME_1>": "\0seed"})
    assert "db-7" not in red("(x<HOSTNAME_1>&.]db-7.corp.internalx", seed), "TB-4.6 after a bracket"
    assert red("x/.db01.corp.example") == "x/.<HOSTNAME_1>", "TB-4.6 after a lone dot"
    assert red("..db01.corp") == "..<HOSTNAME_1>", "TB-4.6 after two dots"


def test_host_starts_after_a_non_ascii_word_character():
    """TB-4.13. `\\w` holds CJK and accented letters, so a start look-behind on `\\w` left no start for `-_db-7...` glued after one."""
    glued = "mail_9\u4f8b-_db-7.corp.internal_\u00e9\u4f8b"
    out = red(glued)
    assert "db-7" not in out and "corp" not in out, f"TB-4.13 after a CJK letter and `-_`: {out!r}"
    assert red("x \u4f8bdb01.corp.example y") == "x \u4f8b<HOSTNAME_1> y", (
        "TB-4.13 glued after a CJK letter"
    )
    assert "db01" not in red("\u00e9-_db01.corp.example"), (
        "TB-4.13 after an accented letter and `-_`"
    )


def test_host_ends_before_a_non_ascii_word_character():
    """TB-4.13 (trailing glue, G4d). The lookahead after the suffix names ASCII label characters, so a CJK glue does not hide the name."""
    for text, want in (
        ("db01.corp\u4f8b", "<HOSTNAME_1>\u4f8b"),
        ("db01.local\u4f8b", "<HOSTNAME_1>\u4f8b"),
        ("a db01.corp\u4f8b b", "a <HOSTNAME_1>\u4f8b b"),
        ("db01.local-x\u4f8b", "<HOSTNAME_1>\u4f8b"),
        ("db01.corp.example\u4f8b", "<HOSTNAME_1>\u4f8b"),
    ):
        assert red(text) == want, f"TB-4.13 trailing glue {text!r}"
    assert red("threading.local()") == "threading.local()", "TB-4.13 local() guard"
    assert red("jdk.internal.reflect.Method") == "jdk.internal.reflect.Method", (
        "TB-4.13 internal.reflect guard"
    )


def test_host_key_glued_to_a_non_ascii_word_character():
    """TB-4.13 (HOSTKEY, G4d). The host-key look-behind and look-ahead name ASCII characters."""
    assert red("\u4f8bhost=db01-7") == "\u4f8bhost=<HOSTNAME_1>", "TB-4.13 HOSTKEY glued before"
    assert red("host=db01-7\u4f8b") == "host=<HOSTNAME_1>\u4f8b", "TB-4.13 HOSTKEY glued after"
    assert red("host=db01-7") == "host=<HOSTNAME_1>", "TB-4.13 HOSTKEY plain"


@pytest.mark.xfail(
    strict=True,
    reason="L-H5 (G4d): labels are ASCII (L11); a non-ASCII letter inside a label leaves the part before it readable",
)
def test_host_non_ascii_inside_a_label_is_masked():
    assert red("db\u4f8b01.corp.example") == "<HOSTNAME_1>", "TB-4.14 non-ASCII inside a label"


def test_host_whole_names():
    rows = {
        "db01.corp.example": "<HOSTNAME_1>",
        "db01.corp.example.": "<HOSTNAME_1>.",
        "com.acme.corp.billing.Service": "<HOSTNAME_1>",
        "db_01.corp.example": "<HOSTNAME_1>",
        "db01[.]corp[.]example": "<HOSTNAME_1>",
        "x[.]svc[.]cluster[.]local": "<HOSTNAME_1>",
        "db01.corp.example.com_x": "<HOSTNAME_1>",
    }
    for text, want in rows.items():
        assert red(text) == want, f"TB-4.7 {text}"


def test_host_kept_names():
    rows = [
        "x.svc.cluster.local",
        "x.svc.cluster.local.foo",
        "eu-west-1.compute.internal",
        "ec2.internal",
        "jdk.internal.reflect.Method",
        "threading.local()",
        "dial db01.corp.example.svc.cluster.local now",
    ]
    for text in rows:
        assert red(text) == text, f"TB-4.8 {text}"


def test_host_privacy_rows_new_strings():
    rows = [t for texts in privacy_corpus.MASKED.values() for t in texts]
    for text, want in (
        (rows[26], "db at <HOSTNAME_1>:5432"),
        (rows[27], "smb://<HOSTNAME_1>/share"),
    ):
        assert both(text) == (want, want), f"TB-4.9 {text}"


@pytest.mark.perf
def test_host_patterns_are_linear():
    texts = ["a[.]" * 12500, "a.-_" * 12500, "a-" * 25000 + ".corp", "a." * 25000, "ab-cd." * 8000]
    pats = [p for label, p in redact_mod.PATTERNS if label == "HOSTNAME"]
    for t in texts:
        for p in pats:
            t0 = time.perf_counter()
            p.findall(t)
            assert time.perf_counter() - t0 < 0.05, "TB-4.10 a host pattern is not linear"


def test_host_label_class_is_ascii():
    """TB-4.11. A Cyrillic letter in the first label: pinned from the measured output (the fold scan masks the line first)."""
    text = "dial db\u0430" + "01.corp.example now"
    assert red(text) == RED_CYRILLIC, "TB-4.11 non-ASCII label"


RED_CYRILLIC = "[line withheld: look-alike text hid a protected value] <HOSTNAME_1>"


@pytest.mark.xfail(strict=True, reason="L-H4: a label with one trailing digit is not masked")
def test_limit_host_single_trailing_digit():
    assert "web1" not in red("host web1 down"), "TB-4.L-H4 web1"
