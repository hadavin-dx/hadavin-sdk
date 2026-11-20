"""The mutants of ticket G8 (glued-rest gap), run by ``tools/mutation_runner.py``. Not collected by pytest.

Each mutant edits ONE guard in a temp copy of the package; the named test must fail first and its first failing line must
hold ``expect`` (the ``ROW <id> ...``, ``OPAQUE ...``, ``UNTRUSTED ...`` or ``SWEEP ...`` start of the assertion message).
Every ``old`` is a fragment that ``ruff format`` leaves as it is (ticket G8 v5, section 8 phase 4). Run from the repo root:

    python tests/g8_mutants.py            # all mutants; exit 1 if any is not good
    python tests/g8_mutants.py G8-P       # only mutants whose name contains the text
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
RD = "src/hadavin_sdk/guard/redact.py"
TEST = "tests/test_redact_glued_rest.py"
PIN = "tests/test_redact_glued_rest::"
UU = r'r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
E6 = (
    '    (\n        "PHONE",\n        re.compile(\n'
    '            r"(?<![0-9.\\-])\\+(?!\\d{4}-\\d\\d-\\d\\d)\\d(?:(?!\\d{4}-\\d\\d-\\d\\d)[\\d \\-]){8,14}\\d(?![0-9.])"\n'
    "        ),\n    ),\n"
)
MAIN = (
    '    (\n        "PHONE",\n        re.compile(\n            r"(?<![\\w.\\-])(?!\\d{4}-\\d\\d-\\d\\d)"\n'
    '            r"(?!(?:19|20)\\d\\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\\d|3[01])(?:[01]\\d|2[0-3])[0-5]\\d[0-5]\\d(?!\\d))"\n'
    '            r"\\+?\\d(?:(?!\\d{4}-\\d\\d-\\d\\d)[\\d \\-]){8,14}\\d(?![\\w.])"\n        ),\n    ),\n'
)
TS = r'r"(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))"'
J5 = '_JOINS = {"PHONE": frozenset(string.digits)}'


def m(name, old, new, killer, expect, file=RD):
    # the pinned id names the parametrized case the expect names: "ROW 36 " -> [row36], "ROW K2 " / "OPAQUE K75" -> [K2] / [K75]
    tag = expect.split()[1] if expect.startswith(("ROW ", "OPAQUE ", "UNTRUSTED ")) else ""
    case = "" if not tag else f"[row{tag}]" if tag.isdigit() else f"[{tag}]"
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer + case
    )


GR, KEEP, SW = (
    "test_glued_rows_are_masked",
    "test_must_keep_rows",
    "test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only",
)
OPQ = "test_an_iban_never_starts_inside_an_opaque_token"
UNT = "test_untrusted_placeholder_literal_keeps_its_number"
IS = '_IBAN_START\n            + r"(?:AD|AE'
E7 = r'r"\d{10,16}(?![0-9A-Za-z.>›])"'
M = [
    m("G8-I1 IBAN end back to \\b", r'r"\d{2}[A-Za-z0-9]{11,30}" + _IBAN_END', r'r"\d{2}[A-Za-z0-9]{11,30}\b"', GR, "ROW 36 "),
    m("G8-I2 IBAN start back to \\b", IS, 'r"\\b(?:AD|AE', GR, "ROW 41 "),
    m("G8-I3 IBAN start with the camelCase part (v2, F1)", IS, '_NOT_IN_WORD\n            + r"(?:AD|AE', OPQ, "OPAQUE K75"),
    m("G8-I4 IBAN start after any _ (v3, M1)", r'r"(?:(?<![A-Za-z0-9+/_\-])"', r'r"(?:(?<![A-Za-z0-9])"', OPQ, "OPAQUE K83"),
    m("G8-I5 IBAN after - + / may end at _ (M1)", r'r"|(?<=[+/\-])(?![A-Z]{2}\d{2}[A-Za-z0-9]{11,30}_)"', r'r"|(?<=[+/\-])"', OPQ, "OPAQUE K84"),
    m("G8-U1 UUID end \\b", UU + '"', UU + r'\b"', GR, "ROW 14 "),
    m("G8-U2 UUID start \\b", r'r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}', r'r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}', GR, "ROW 51 "),
    m("G8-V1 IPV4 dotted end \\b", r'(?:\d{1,3}\.){3}\d{1,3}(?![0-9])"', r'(?:\d{1,3}\.){3}\d{1,3}\b"', GR, "ROW 2 "),
    m("G8-V2 IPV4 dotted start \\b", r'r"(?<![0-9])(?<!(?<![A-Za-z])[vV])', r'r"\b(?<!(?<![A-Za-z])[vV])', GR, "ROW 7 "),
    m("G8-V3 IPV4 drop the digit look-behind", r'r"(?<![0-9])(?<!(?<![A-Za-z])[vV])', r'r"(?<!(?<![A-Za-z])[vV])', KEEP, "ROW K2 "),
    m("G8-V4 IPV4 drop the lone-v look-behind", r'r"(?<![0-9])(?<!(?<![A-Za-z])[vV])', r'r"(?<![0-9])', KEEP, "ROW K1 "),
    m("G8-V5 EC2 end \\b", r'(\d{1,3}(?:-\d{1,3}){3})(?![0-9])"', r'(\d{1,3}(?:-\d{1,3}){3})\b"', GR, "ROW 72 "),
    m("G8-V6 EC2 start back to \\b", r'r"(?<![A-Za-z0-9])(?:ip|ec2)-', r'r"\b(?:ip|ec2)-', GR, "ROW 81 "),
    m("G8-V7 pod DNS start back to \\b", r'r"(?<![0-9])(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod', r'r"\b(\d{1,3}(?:-\d{1,3}){3})\.[\w-]+\.pod', GR, "ROW 83 "),
    m("G8-C1 card start back to \\b", r'r"(?<![0-9])\d{4}[ \-]\d{4}', r'r"\b\d{4}[ \-]\d{4}', KEEP, "ROW K36 "),
    m("G8-C2 card end back to \\b", r'[ \-]\d{4}(?![0-9])"', r'[ \-]\d{4}\b"', KEEP, "ROW K74 "),
    m("G8-P1 the + entry after the main PHONE entry", E6 + MAIN, MAIN + E6, GR, "ROW 21 "),
    m("G8-P2 the + entry removed", E6, "", GR, "ROW 18 "),
    m("G8-P3 the + entry refuses a letter before +", r'r"(?<![0-9.\-])\+(?!', r'r"(?<![\w.\-])\+(?!', GR, "ROW 21 "),
    m("G8-P4 the + entry takes a number without +", r'r"(?<![0-9.\-])\+(?!\d{4}-\d\d-\d\d)\d(?:', r'r"(?<![0-9.\-])\+?(?!\d{4}-\d\d-\d\d)\d(?:', KEEP, "ROW K5 "),
    m("G8-P5 the + entry end back to the main guard", r'[\d \-]){8,14}\d(?![0-9.])"', r'[\d \-]){8,14}\d(?![\w.])"', GR, "ROW 18 "),
    m("G8-P8 the _ entry allows a letter after", E7, r'r"\d{10,16}(?![0-9.>›])"', KEEP, "ROW K8 "),
    m("G8-P9 the _ entry without the timestamp guard", '|(?=\\d{10,16}_))"\n            ' + TS + "\n", '|(?=\\d{10,16}_))"\n', KEEP, "ROW K16 "),
    m("G8-P10 the _ entry without the > guard", E7, r'r"\d{10,16}(?![0-9A-Za-z.›])"', KEEP, "ROW K64 "),
    m("G8-P11 the _ entry needs _ before", r'(?:(?<=_)|(?=\d{10,16}_))', r'(?<=_)', GR, "ROW 26 "),
    m("G8-P12 keyword entry without tel", "(?:tel|phone|mobile|cell|fax)", "(?:phone|mobile|cell|fax)", GR, "ROW 28 "),
    m("G8-P13 the _ entry without the \u203a guard (M2)", E7, r'r"\d{10,16}(?![0-9A-Za-z.>])"', UNT, "UNTRUSTED U1"),
    m("G8-P14 the + entry without its date guard after + (N4)", r'\+(?!\d{4}-\d\d-\d\d)\d(?:', r'\+\d(?:', KEEP, "ROW K81 "),
    m("G8-S1 _JOINS empty", J5, "_JOINS = {}", GR, "ROW 31 "),
    m("G8-S2 sweep call without joins", "original, placeholder, _joins(placeholder)", "original, placeholder", GR, "ROW 31 "),
    m("G8-S3 HOSTNAME given digits", J5, '_JOINS = {"PHONE": frozenset(string.digits), "HOSTNAME": frozenset(string.digits)}', SW, "SWEEP host"),
    m("G8-S4 IPV4 given digits", J5, '_JOINS = {"PHONE": frozenset(string.digits), "IPV4": frozenset(string.digits)}', SW, "SWEEP ipv4"),
    m("G8-S5 TENANT given digits", J5, '_JOINS = {"PHONE": frozenset(string.digits), "TENANT": frozenset(string.digits)}', SW, "SWEEP tenant"),
    m("G8-S6 PHONE copy beside a digit replaced too", J5, '_JOINS = {"PHONE": frozenset()}', SW, "SWEEP phone digit"),
]  # fmt: skip

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in mm.name for mm in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:200], flush=True)

    first_lines: dict[str, str] = {}
    res = run_mutants(
        ROOT,
        M,
        [TEST, "tests/g8_cases.py", "tests/__init__.py", "tests/conftest.py"],
        extra_dirs=("tests/fixtures", "tools"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
