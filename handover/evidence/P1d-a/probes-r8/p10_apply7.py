"""P10 step 7 (HL2, found by the hostile-token battery): `_IMAGE` (`!\\[..\\]\\([^)]*\\)`) and `_MDLINK` scan to the end of the line for every
`![](` start when no `)` follows, so `![](` repeated is O(n^2) on the base tree and on P9 (8,000 repeats = 32,000 characters: 17 s).
Fix: match the head only, find the next `)` once; when none exists no later head can match either, so stop. Same output as the two
regexes (fuzz: p10_dest.py). usage: python p10_apply7.py <tree>/src/hadavin_sdk"""
import sys, pathlib
gp = pathlib.Path(sys.argv[1]) / "approvals" / "gate.py"
s = gp.read_text(encoding="utf-8")
pairs = [
('''_IMAGE = re.compile(r"!" + _LABEL + r"\\([^)]*\\)")''',
 '''_IMAGE_HEAD = re.compile(r"!" + _LABEL + r"\\(")'''),
('''_MDLINK = re.compile(_LABEL + r"\\(\\s*[^)\\s]+[^)]*\\)")''',
 '''_MDLINK_HEAD = re.compile(_LABEL + r"\\(")


def _drop_targets(head: re.Pattern[str], line: str, repl: Callable[[re.Match[str]], str], blank_ok: bool) -> str:
    """Replace `head` + target up to the next `)`; linear: with no `)` left no later head can match, so stop. A link needs a target that is not
    only spaces (`blank_ok` False)."""
    out, pos, at = [], 0, 0
    while (m := head.search(line, at)) is not None:
        close = line.find(")", m.end())
        if close < 0:
            break
        if not blank_ok and not line[m.end() : close].strip():
            at = m.start() + 1
            continue
        out += [line[pos : m.start()], repl(m)]
        pos = at = close + 1
    return "".join(out) + line[pos:]'''),
('''        line = _IMAGE.sub("[image removed]", line)
        line = _MDLINK.sub(r"\\1 [link removed]", line)''',
 '''        line = _drop_targets(_IMAGE_HEAD, line, lambda m: "[image removed]", True)
        line = _drop_targets(_MDLINK_HEAD, line, lambda m: m.group(1) + " [link removed]", False)'''),
]
for old, new in pairs:
    assert s.count(old) == 1, (s.count(old), old[:50])
    s = s.replace(old, new)
gp.write_text(s, encoding="utf-8")
print("ok7")
