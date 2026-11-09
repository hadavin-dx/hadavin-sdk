"""The mutants of P1d-a (ticket revision 5, plus K41/A44/A45 from lead ORDER 192), run by ``tools/mutation_runner.py``.

Each mutant edits ONE guard in a temp copy of the package; the test in ``killer`` must fail first and its first failing line
must hold ``expect`` (the ``ROW <id> <entry>:`` start of the assertion message). Not collected by pytest. Run from the repo root:

    python tests/p1d_a_mutants.py            # all mutants; exit 1 if any is not good
    python tests/p1d_a_mutants.py A7         # only mutants whose name contains the text

``run_mutants`` has no ``forbid_skips`` argument on this base (ORDER 181 is not merged): the call below omits it; the
killers are plain row tests that cannot be skipped.
"""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_p1d_a_rows.py"
PIN = "tests/test_p1d_a_rows::"
GATE = "src/hadavin_sdk/approvals/gate.py"
CH = "src/hadavin_sdk/approvals/channel.py"
SL = "src/hadavin_sdk/approvals/slack_channel.py"
RD = "src/hadavin_sdk/guard/redact.py"
RM = "src/hadavin_sdk/guard/runmap.py"
QLB = "(?:(?<=[?&])|(?<=&amp;))"
LD = r"(?<=[\w-])\[\.\](?=[\w-])"
PD = r"_[0-9]+>)\.(?=[\w-])"
QV = "|&(?![^\\s&#\\\"'=]*=))+)"  # the last alternative of the query value
QA = "&amp;(?![^\\s&#\\\"'=]*=)|"


def row(name):
    return f"ROW {name}:"


def m(name, file, old, new, killer, expect=None):
    exp = expect or row(killer.removeprefix("test_row_").replace("_", " ", 1))
    return Mutant(name, file, old, new, exp, test_file=TEST, only_test=killer, pinned=PIN + killer)


S = "sanitise_text"
M = [
    m("A1", CH, "sanitise_text(text, defang=False)", "sanitise_text(text)", "test_row_H26_card"),
    m("A2", CH, "return defang_text(out)", "return out", "test_row_L1_card"),
    m("A11", CH, "return defang_text(alt)", "return alt", "test_row_T1_card"),
    m(
        "A3",
        SL,
        "shown = defang_text(runmap.redact_text(withheld, seeded, neutralise=_neutralise))",
        "shown = runmap.redact_text(withheld, seeded, neutralise=_neutralise)",
        "test_row_L5_slack",
    ),
    m(
        "A3b",
        SL,
        "withhold_commands(undefang_text(req.summary))",
        "withhold_commands(req.summary)",
        "test_row_L7_slack",
    ),
    m(
        "A3c",
        SL,
        "if len(shown) > self.max_card_chars",
        'if len(shown.replace("[.]", ".")) > self.max_card_chars',
        "test_row_L9_slack",
    ),
    m(
        "A3d",
        GATE,
        'return _outside_code(text, lambda part: _LEGACY_DOT.sub(".", part))',
        'return _LEGACY_DOT.sub(".", text)',
        "test_row_L10_slack",
    ),
    m("A3e", GATE, 'r"(?<=[\\w-])\\[\\.\\](?=[\\w-])"', 'r"\\[\\.\\]"', "test_row_L12_slack"),
    m(
        "A3f",
        GATE,
        'r"(?<=[\\w-])\\[\\.\\](?=[\\w-])"',
        'r"\\[\\.\\](?=[\\w-])"',
        "test_row_L14_slack",
    ),
    m(
        "A3g",
        GATE,
        'r"(?<=[\\w-])\\[\\.\\](?=[\\w-])"',
        'r"(?<=[\\w-])\\[\\.\\]"',
        "test_row_L13_slack",
    ),
    m(
        "A4",
        GATE,
        'part = _PLACEHOLDER_DOT.sub(r"\\1[.]", part)',
        "part = part",
        "test_row_H27_card",
    ),
    m(
        "A17",
        GATE,
        'part = _WIDE_DOTS.sub(".", part)\n    part = _PLACEHOLDER_DOT.sub(r"\\1[.]", part)',
        'part = _PLACEHOLDER_DOT.sub(r"\\1[.]", part)\n    part = _WIDE_DOTS.sub(".", part)',
        "test_row_D3e_defang",
    ),
    m("A41", GATE, "_[0-9]+>)\\.(?=[\\w-])", "_[0-9]+>)\\.(?=\\w)", "test_row_D3f_defang"),
    m("A42", GATE, "_[0-9]+>)\\.(?=[\\w-])", "_[0-9]+>)\\.(?=-)", "test_row_D3b_defang"),
    m(
        "A5",
        GATE,
        'parts = [line] if "``" in line else _INLINE_CODE.split(line)',
        "parts = [line]",
        "test_row_L2_card",
    ),
    m(
        "A43",
        GATE,
        'parts = [line] if "``" in line else _INLINE_CODE.split(line)',
        "parts = _INLINE_CODE.split(line)",
        "test_row_G2_card",
    ),
    m(
        "A38",
        GATE,
        "part if i % 2 else fix(part)",
        "fix(part) if i % 2 else part",
        "test_row_L2_card",
    ),
    m("A6", GATE, "for s, e, ch in _closed_fences(text)", "for s, e, ch in []", "test_row_L3_card"),
    m("A37", GATE, 'if ch == "`"', 'if ch in "`~"', "test_row_L4_card"),
    m("A12", GATE, "range(s + 1, e)", "range(s, e)", "test_row_I1_card"),
    m(
        "A13",
        GATE,
        "seen = out if defang else [_defang_outside_code(c) for c in out]",
        "seen = out",
        "test_row_Z4_card",
    ),
    m(
        "A10",
        GATE,
        "def sanitise_text(text: str, *, defang: bool = True) -> str:",
        "def sanitise_text(text: str, *, defang: bool = False) -> str:",
        "test_sanitise_text_default_unchanged",
        "DEFAULT CHANGED",
    ),
    m(
        "A28",
        GATE,
        "out = [_clean_line(line, defang) for line in joined]",
        "out = [_clean_line(line, True) for line in joined]",
        "test_row_H26_card",
    ),
    m(
        "A29",
        GATE,
        "return _defang_outside_code(line) if defang else line",
        "return _defang_outside_code(line)",
        "test_row_H26_card",
    ),
    m(
        "A30",
        GATE,
        "_clean_prose(lines, defang))",
        "_clean_prose(lines, True))",
        "test_row_FB1_gate",
    ),
    m(
        "A27",
        GATE,
        "if not opener or not closer:\n            return _all_prose(lines, defang)",
        "if not opener or not closer:\n            return _all_prose(lines, True)",
        "test_row_FB1_gate",
    ),
    m(
        "A25",
        GATE,
        "out += _clean_prose(lines[pos:start], defang)",
        "out += _clean_prose(lines[pos:start], True)",
        "test_row_PF1_card",
    ),
    m(
        "A19",
        GATE,
        "_clean_line(opener.group(3), defang)",
        "_clean_line(opener.group(3), True)",
        "test_row_I2_card",
    ),
    m(
        "A18",
        GATE,
        "[_clean_line(line, defang) for line in body]",
        "[_clean_line(line, True) for line in body]",
        "test_row_E1_card",
    ),
    m(
        "A26",
        GATE,
        "out += _clean_prose(lines[pos:], defang)",
        "out += _clean_prose(lines[pos:], True)",
        "test_row_PF2_card",
    ),
    m(
        "A31",
        GATE,
        "return _all_prose(lines, defang)\n    return result",
        "return _all_prose(lines, True)\n    return result",
        "test_row_FB2_gate",
    ),
    m("A7", RD, "&amp;|[^\\s\\\"';,]|,", "&amp;|[^\\s\\\"';,&]|,", "test_row_H34a_model"),
    m("A9", RD, "(?<![\\w.\\-?&])", "(?<![\\w.\\-])", "test_row_Q2_model"),
    m("A33", RD, "(?<![\\w.\\-?&])", "(?<![\\w.\\-?])", "test_row_Q13_model"),
    m("A35", RD, "(?<!&amp;)", "", "test_row_Q15_model"),
    m("A23", RD, "|&amp;|[^\\s\\\"';,]|,", "|[^\\s\\\"';,]|,", "test_row_H34d_card"),
    m(
        "A15",
        RD,
        "(?i)" + QLB + "[\\w.\\-]*",
        "(?i)[\\w.\\-]*",
        "test_row_K41q_model",
        "A15 expected survivor",
    ),
    m("A32", RD, QLB, "(?:(?<=[?])|(?<=&amp;))", "test_row_Q14_model"),
    m("A34", RD, QLB, "(?<=[?&])", "test_row_Q15_model"),
    m("A8", RD, QV, "|&)+)", "test_row_Q2_model"),
    m("A14", RD, QV, ")+)", "test_row_Q5_model"),
    m("A20", RD, QV, "|&(?![^\\s&\\\"'=]*=))+)", "test_row_Q10_model"),
    m("A21", RD, QV, "|&(?![^&#\\\"'=]*=))+)", "test_row_Q11_model"),
    m("A39", RD, QV, "|&(?![^\\s&#=]*=))+)", "test_row_Q16_model"),
    m("A24", RD, QA, "", "test_row_Q12_card"),
    m("A36", RD, QA, "&amp;|", "test_row_Q7_model"),
    m("A40", RD, QA, "&amp;(?![^\\s&#=]*=)|", "test_row_Q17_model"),
    m("A16", RM, "for view in views:", "for view in ():", "test_row_H36a_card"),
    # lead ORDER 192: the key prefix has no bound (INFO-K41)
    m("A44", RD, "(?<!&amp;)[\\w.\\-]*", "(?<!&amp;)[\\w.\\-]{0,40}", "test_row_K41_model"),
    m(
        "A45",
        RD,
        "(?i)" + QLB + "[\\w.\\-]*",
        "(?i)" + QLB + "[\\w.\\-]{0,40}",
        "test_row_K41q_model",
    ),
]

if __name__ == "__main__":
    results = run_mutants(
        ROOT,
        M,
        [TEST],
        extra_dirs=("tests", "tools"),
        only=sys.argv[1:],
        on_result=lambda r: print(r, flush=True),
    )
    sys.exit(0 if all(good for *_, good in results) else 1)
