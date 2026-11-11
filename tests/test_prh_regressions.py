"""PR H, T5: every input the earlier reviews and probes used, as one row of `fixtures/prh_regressions.json`.

Each row is a list of parts, so the file holds no control character and no secret-shaped string: `{"lit": ...}` is text,
`{"cp": "1B"}` is one code point (hex), `{"const": "KEY", "slice": [0, 4]}` is a made-up value of `CONSTS` (a slice is
optional; `"rep": n` on a `lit` repeats it n times). A row records where it came from (`source`, a file and a line or a finding id), the secrets it carries (names
of `CONSTS`), the handed-out secret list for the tool and error paths, the paths it is run on, and the expected
verdict per path:

* `masked`   no piece of five characters of any secret of the row stands in the output (a refusal shows nothing);
* `clean`    a row with no secret: no result-marker shape (as written or in its canonical form) and no genuine-shaped
             placeholder the call did not issue stands in the output;
* `shape:<16 hex>`  an input the promises do not cover ("not promised", or pull request 77): the first 16 hex digits of
             the SHA-256 of the exact output, so any later change of today's output shape is noticed.

A row whose id starts `mf_` fails on main (the old code); every other row passes on main. Every value is made up."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from hadavin_sdk import tools
from hadavin_sdk.approvals import channel
from hadavin_sdk.guard import runmap

FIXTURE = Path(__file__).parent / "fixtures" / "prh_regressions.json"

CONSTS: dict[str, str] = {
    "KEY": "AKIA" + "IOSFODNN7EXAMPLE",
    "KEY2": "AKIA" + "ZZZZODNN7EXAMPL2",
    "MAIL": "bob.smith" + "@" + "example.com",
    "MAILP": "bob" + "@" + "example" + ".com",
    "PW": "hunter" + "2secretXYZ",
    "HAND": "Tr0ub4dor" + "-3xyzQ",
    "TOK": "abcDEF123456" + "ghiJKL7890mnop",
    "IP": "10.20.30.44",
    "PH": "<" + "IPV4_2" + ">",
    "PWK": "pass" + "word=",
    "S7A": "Zx9" + "&lt;" + "Qw7" + "!pa" + "ss",
    "S7B": "pa" + "%41" + "ssw" + "0rd" + "-9",
    "S7C": "Qz7" + "+/k" + "9Lm" + "~~v" + "Xy2" + "??b",
    "S7D": "".join(f"{chr(65 + i)}{chr(97 + i)}{i % 10}" for i in range(18)),
    "CARD": "4242",
    "JWT0": "eyJhbGciOiJIUzI1NiJ9",
    "JWT1": "eyJzdWIiOiIxMjM0NTY3ODkwIn0",
    "JWT2": "sig1Abc2Def3Ghi4Jkl5Mno6Pqr7S",
    "H2A": "Hunter2" + "abc",
    "H2B": "Hunter2" + "abcdef",
    "GTAIL": "IOSFODNN7EXAMPLE" * 2,
    "GH36": "IOSFODNN7EXAMPLE12" + "IOSFODNN7EXAMPLE34",
    "LOW": "e"
    + "Yk3pQ9wRtZ",  # a handed-out secret that starts with a lower-case letter (round b4)
    "JWT": "eyJhbGciOiJIUzI1NiJ9"
    + "."
    + "eyJzdWIiOiIxMjM0NTY3ODkwIn0"
    + "."
    + "sig1Abc2Def3Ghi4Jkl5Mno6Pqr7S",
}
# names that are secrets (a piece of five characters standing in an output is a leak); the others are only text
SECRET_NAMES = {
    "KEY",
    "KEY2",
    "MAIL",
    "MAILP",
    "PW",
    "HAND",
    "TOK",
    "S7A",
    "S7B",
    "S7C",
    "S7D",
    "JWT2",
    "H2A",
    "H2B",
    "GTAIL",
    "GH36",
    "LOW",
    "JWT",
}
HANDED_NAMES = {"HAND", "LOW"}
PATHS_ALL = ("untrusted", "tool", "error", "head")
MARKER = re.compile(r"<<(?=\s*(?:end\s+)?tool\s+result)", re.IGNORECASE)
PLACEHOLDER = re.compile(r"<[A-Z][A-Z0-9]*_[0-9]+>")


def build(parts: list[dict]) -> str:
    out: list[str] = []
    for part in parts:
        if "lit" in part:
            out.append(part["lit"] * part.get("rep", 1))
        elif "cp" in part:
            out.append(chr(int(part["cp"], 16)))
        else:
            value = CONSTS[part["const"]]
            lo, hi = part.get("slice", [None, None])
            out.append(value[lo:hi])
    return "".join(out)


def run_path(path: str, text: str, handed: list[str]) -> str | None:
    try:
        if path == "untrusted":
            return runmap.redact_untrusted(text, {})
        if path == "tool":
            return tools.prepare_output(text, {}, 4000, handed)
        if path == "error":
            return tools.error_reason(ValueError(text), handed)
        if path == "head":
            return runmap.safe_head(text, 4000)
        if path == "card":
            return channel.clean(text)
    except Exception as exc:  # a refusal shows nothing
        if type(exc).__name__ in {"RedactionError", "InputTooLarge", "TooDeep"}:
            return None
        raise
    raise ValueError(path)


def leaked(out: str | None, secret: str, size: int = 5) -> bool:
    if out is None:
        return False
    return any(secret[i : i + size] in out for i in range(len(secret) - size + 1))


def forged(out: str | None, issued: set[str]) -> bool:
    if out is None:
        return False
    for form in (out, runmap.canonical(out)):
        if MARKER.search(form):
            return True
        if any(p not in issued for p in PLACEHOLDER.findall(form)):
            return True
    return False


def verdict(row: dict, path: str) -> str:
    """The verdict word of one row on one path (what the fixture stores)."""
    text = build(row["parts"])
    handed = [CONSTS[n] for n in row["handed"]]
    out = run_path(path, text, handed)
    secrets = [CONSTS[n] for n in row["secrets"]]
    if row.get(
        "pin"
    ):  # an input the promises do not cover: today's exact output shape is the verdict
        pass
    elif secrets:
        if not any(leaked(out, s) for s in secrets):
            return "masked"
    elif not forged(out, set(PLACEHOLDER.findall(text))):
        return "clean"
    digest = hashlib.sha256(
        ("\x00<refused>" if out is None else out).encode("utf-8", "surrogatepass")
    ).hexdigest()
    return "shape:" + digest[:16]


ROWS = (
    json.loads(FIXTURE.read_text(encoding="utf-8"))["rows"] if FIXTURE.exists() else []
)  # an empty list fails the count test


def _id(row: dict) -> str:
    return ("mf_" if row.get("mf") else "") + row["id"]


@pytest.mark.parametrize("row", ROWS, ids=_id)
def test_regression_row(row):
    for path in row["paths"]:
        assert verdict(row, path) == row["expect"][path], (
            f"{row['id']} [{path}] source {row['source']}"
        )


def test_every_row_is_rebuilt_and_sourced():
    """No row is dropped: each has a source, a path list and an expectation for every path; the file holds no control
    byte and no secret-shaped literal (`lit` parts never carry a made-up value of CONSTS whole, except through `const`)."""
    raw = FIXTURE.read_text(encoding="utf-8")  # a missing file fails here
    assert not any(ord(c) < 0x20 and c not in "\n" for c in raw)
    seen: set[str] = set()
    for row in ROWS:
        assert row["id"] not in seen, row["id"]
        seen.add(row["id"])
        assert row["source"] and set(row["paths"]) == set(row["expect"]), row["id"]
        assert set(row["paths"]) <= {*PATHS_ALL, "card"}
        for part in row["parts"]:
            if "lit" in part:
                assert not any(
                    len(v) >= 8 and v in part["lit"] for n, v in CONSTS.items() if n in SECRET_NAMES
                ), row["id"]
    assert len(ROWS) >= 100, len(ROWS)


# Rows with a secret whose verdict is NOT "masked": each is an input the ticket (section 3, "not promised") or pull request
# 77 / the line-continuation ticket leaves out. The row pins today's exact output, so a change is noticed.
NOT_PROMISED = {
    "tab, form feed or line separator inside the value (white space is white space, as with a plain space)": [
        "r5s_M3a",
        "r5t_M1a",
        "r5t_M1b",
        "r6s_M1a",
        "r6s_M1b",
        "r6s_M2",
        "r6t_M2",
        "r6t_M3",
        "r7c_M1a",
        "r7c_M1c",
        "r7c_M1d",
        "r7d_M4a",
        "t_vis_tab",
        "t_vis_2028",
        "t_vis_ff",
    ],
    "a word glued in front of the cut value (mixed glue and cut, ticket section 3)": [
        "r6s_m4a",
        "r6t_M1",
        "t_plain_user_key",
    ],
    "backslash before a line end (moved to PRH-b-line-continuation-matching)": [
        "p5ab_F8_4",
        "t_vis_bslash_lf",
    ],
    "look-alike letters and encoded spellings of pattern-shaped values (pull request 77, ticket section 3)": [
        "p5d_Cyrillic_a_U_0430_in_the_key_name_1",
        "p5d_Cyrillic_o_U_043E_in_the_key_name_1",
        "p5d_Cyrillic_a_c_o_p_in_the_key_name_1",
        "p5d_Cyrillic_capital_letters_in_the_key_A_K__1",
        "p5ab_F7_1",
        "p5ab_F7_2",
        "p5ab_F8_1",
        "p5ab_F8_5",
        "p5ab_F8_8",
        "r7d_M5a",
        "r7d_M5b",
    ],
}


def _ids(rows):
    return {r["id"] for r in rows}


def _leaks_somewhere(row) -> bool:
    text = build(row["parts"])
    handed = [CONSTS[n] for n in row["handed"]]
    secrets = [CONSTS[n] for n in row["secrets"]]
    return any(leaked(run_path(p, text, handed), s) for p in row["paths"] for s in secrets)


def _named_ids():
    return {i for ids in NOT_PROMISED.values() for i in ids}


def test_unmasked_secret_rows_are_named_not_promised():
    """A secret row whose verdict is not "masked", and every pinned row that carries a secret, needs a named reason."""
    unmasked = {
        r["id"]
        for r in ROWS
        if r["secrets"] and (r.get("pin") or any(v != "masked" for v in r["expect"].values()))
    }
    named = _named_ids() | set(PINNED_BUT_MASKED_TODAY)
    assert unmasked <= named, sorted(unmasked - named)


# Pinned rows that carry a secret but show none of it today on any path: pinned because the promise does not cover the
# input, so a later change in the shape is noticed. The converse test below checks each really is masked now.
PINNED_BUT_MASKED_TODAY = {
    "r6c_M3": "outside the promise, masked today",
    **{
        i: "encoded spelling outside the promise, masked today (pull request 77, ticket section 3)"
        for i in (
            "p5d_full_width_digits_in_the_value_1",
            "p5d_full_width_digit_in_the_key_1",
            "p5d_base64_of_the_key_1",
            "p5d_base64_of_name_value_1",
            "p5d_hex_of_the_key_1",
            "p5d_hex_of_name_value_1",
            "p5d_quoted_printable_every_letter_of_the_key_1",
            "p5d_quoted_printable_of_name_value_quopri_1",
            "p5d_percent_encoding_once_first_letter_of_th_1",
            "p5d_percent_encoding_once_every_letter_of_th_1",
            "p5d_percent_encoding_twice_first_letter_of_t_1",
            "p5d_percent_encoding_twice_every_letter_of_t_1",
            "p5d_percent_encoding_once_name_value_1",
            "p5d_percent_encoding_twice_name_value_1",
            "p5d_percent_encoding_once_the_only_1",
            "p5d_percent_encoding_twice_the_only_1",
        )
    },
}
NOT_PROMISED[
    "encoded first letter or soft line break of the key (pull request 77, ticket section 3)"
] = [
    "p5d_quoted_printable_first_letter_of_the_key_1",
    "p5d_quoted_printable_soft_line_break_inside__1",
]


def test_named_ids_exist_and_the_converse_holds():
    """Each id in the lists is a real row, and the lists are true: a NOT_PROMISED row leaks on some path; a row named
    as masked-today leaks on none (so a fixed gap is moved out of the list, not left as a stale excuse)."""
    by_id = {r["id"]: r for r in ROWS}
    for i in _named_ids():
        assert i in by_id, f"{i} is not a row"
        assert _leaks_somewhere(by_id[i]), f"{i} no longer leaks: take it out of NOT_PROMISED"
    for i in PINNED_BUT_MASKED_TODAY:
        row = by_id.get(i)
        assert row is not None, f"{i} is not a row"
        assert not _leaks_somewhere(row), f"{row['id']} leaks: name it in NOT_PROMISED"


def test_pinned_secret_rows_count():
    pinned = [r for r in ROWS if r.get("pin") and r["secrets"]]
    assert len(pinned) == 23 and len([r for r in ROWS if r.get("pin")]) == 32


def test_every_prh_mutant_still_applies():
    """The mutant list (`tests/prh_mutants.py`, run by CI) cannot rot: each `old` text is still in its file exactly once and
    each killer test still exists."""
    from tests import prh_mutants

    assert len(prh_mutants.M) >= 55
    assert prh_mutants.check_applies() == []
