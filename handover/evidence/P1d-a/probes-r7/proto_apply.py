"""P9 prototype: apply the six gate edits of the ticket's Code shape to a tree.  usage: python proto_apply.py <tree>/src/hadavin_sdk
Every old text must occur exactly once (assert).  Tree stamp: see stamp.sh."""
import sys, pathlib
root = pathlib.Path(sys.argv[1]) / "approvals"

def edit(path, pairs):
    s = path.read_text(encoding="utf-8")
    for old, new in pairs:
        assert s.count(old) == 1, (path.name, s.count(old), old[:70])
        s = s.replace(old, new)
    path.write_text(s, encoding="utf-8")

edit(root / "gate.py", [
('''def _defang_outside_code(line: str) -> str:
    """Domains are defanged except inside inline code, where no renderer makes a link. Only when the
    line's backticks are unambiguous (no double run) - otherwise everything is defanged."""
    parts = [line] if "``" in line else _INLINE_CODE.split(line)
    return "".join(
        part
        if i % 2
        else _DOMAIN.sub(_defang, _NON_ASCII_HOST.sub(_defang, _WIDE_DOTS.sub(".", part)))
        for i, part in enumerate(parts)
    )
''',
'''_PLACEHOLDER_DOT = re.compile(r"(<[A-Z][A-Z0-9]*_[0-9]+>)\\.(?=[\\w-])")
_LEGACY_DOT = re.compile(r"(?<=[\\w-])\\[\\.\\](?=[\\w-])")


def _defang_plain(part: str) -> str:
    return _DOMAIN.sub(_defang, _NON_ASCII_HOST.sub(_defang, _WIDE_DOTS.sub(".", part)))


def _defang_prose(part: str) -> str:
    part = _WIDE_DOTS.sub(".", part)
    part = _PLACEHOLDER_DOT.sub(r"\\1[.]", part)
    return _defang_plain(part)


def _wide_ascii(part: str) -> str:
    return _WIDE_DOTS.sub(".", part)


def _per_part(line: str, fix: Callable[[str], str]) -> str:
    parts = [line] if "``" in line else _INLINE_CODE.split(line)
    return "".join(part if i % 2 else fix(part) for i, part in enumerate(parts))


def _defang_outside_code(line: str) -> str:
    """Domains are defanged except inside inline code, where no renderer makes a link. Only when the
    line's backticks are unambiguous (no double run) - otherwise everything is defanged."""
    return _per_part(line, _defang_plain)
'''),
("def _clean_line(line: str) -> str:", "def _clean_line(line: str, defang: bool) -> str:"),
("    return _defang_outside_code(line)\n\n\ndef _clean_prose(lines: list[str]) -> list[str]:",
 "    return _defang_outside_code(line) if defang else _per_part(line, _wide_ascii)\n\n\ndef _clean_prose(lines: list[str], defang: bool) -> list[str]:"),
("    out = [_clean_line(line) for line in joined]\n", "    out = [_clean_line(line, defang) for line in joined]\n    seen = out if defang else [_defang_outside_code(c) for c in out]\n"),
('''        "\\u200b" + c if _ANY_BLOCK.match(c) and not (same and c == lines[i]) else c
        for i, c in enumerate(out)''',
'''        "\\u200b" + c if _ANY_BLOCK.match(d) and not (same and d == lines[i]) else c
        for i, (c, d) in enumerate(zip(out, seen, strict=True))'''),
('''def _all_prose(lines: list[str]) -> str:
    return "\\n".join(_clean_prose(lines))


def sanitise_text(text: str) -> str:''',
'''def _outside_code(text: str, fix: Callable[[str], str]) -> str:
    body = {i for s, e, ch in _closed_fences(text) if ch == "`" for i in range(s + 1, e)}
    return "\\n".join(
        line if i in body else _per_part(line, fix) for i, line in enumerate(text.split("\\n"))
    )


def defang_text(text: str) -> str:
    return _outside_code(text, _defang_prose)


def undefang_text(text: str) -> str:
    return _outside_code(text, lambda part: _LEGACY_DOT.sub(".", part))


def _all_prose(lines: list[str], defang: bool) -> str:
    return "\\n".join(_clean_prose(lines, defang))


def sanitise_text(text: str, *, defang: bool = True) -> str:'''),
("    for start, last, char in _closed_fences(\"\\n\".join(lines)):\n        opener, closer = _FENCE_LINE.match(lines[start]), _FENCE_LINE.match(lines[last])\n        if not opener or not closer:\n            return _all_prose(lines)\n        out += _clean_prose(lines[pos:start])",
 "    for start, last, char in _closed_fences(\"\\n\".join(lines)):\n        opener, closer = _FENCE_LINE.match(lines[start]), _FENCE_LINE.match(lines[last])\n        if not opener or not closer:\n            return _all_prose(lines, defang)\n        out += _clean_prose(lines[pos:start], defang)"),
("char * 3 + _clean_line(opener.group(3)))", "char * 3 + _clean_line(opener.group(3), defang))"),
("            else [_clean_line(line) for line in body]", "            else [_clean_line(line, defang) for line in body]"),
("    out += _clean_prose(lines[pos:])\n    result", "    out += _clean_prose(lines[pos:], defang)\n    result"),
('''    ):
        return _all_prose(lines)
    return result''', '''    ):
        return _all_prose(lines, defang)
    return result'''),
])
g = (root / "gate.py").read_text(encoding="utf-8")
if "from collections.abc import Callable" not in g:
    assert g.count("\nimport re\n") == 1
    g = g.replace("\nimport re\n", "\nimport re\nfrom collections.abc import Callable\n")
    (root / "gate.py").write_text(g, encoding="utf-8")

edit(root / "channel.py", [
("from hadavin_sdk.approvals.gate import sanitise_text, withhold_commands",
 "from hadavin_sdk.approvals.gate import defang_text, sanitise_text, withhold_commands"),
("    out = runmap.redact_text(text, mapping, neutralise=_neutralise)", "    out = redact_for_card(text, mapping)"),
("        alt = runmap.redact_text(joined, joined_map, neutralise=_neutralise)", "        alt = redact_for_card(joined, joined_map)"),
("def _neutralise(text: str) -> str:", '''def redact_for_card(text: str, mapping: Mapping[str, str]) -> str:
    return defang_text(runmap.redact_text(text, mapping, neutralise=_neutralise_for_redaction))


def _neutralise_for_redaction(text: str) -> str:'''),
("    return withhold_commands(sanitise_text(text))", "    return withhold_commands(sanitise_text(text, defang=False))"),
])
edit(root / "slack_channel.py", [
("from hadavin_sdk.approvals.channel import _neutralise, clean", "from hadavin_sdk.approvals.channel import clean, redact_for_card"),
("from hadavin_sdk.approvals.gate import withhold_commands", "from hadavin_sdk.approvals.gate import undefang_text, withhold_commands"),
("        withheld = withhold_commands(req.summary)", "        withheld = withhold_commands(undefang_text(req.summary))"),
("        shown = runmap.redact_text(withheld, seeded, neutralise=_neutralise)", "        shown = redact_for_card(withheld, seeded)"),
])
