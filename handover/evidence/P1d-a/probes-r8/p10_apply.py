"""P10 prototype step 1 (N9): wide dots first in the defang=False branch of _clean_line.
usage: python p10_apply.py <tree>/src/hadavin_sdk   (tree = P9 tree: P9 = atomic redact.py of probes-r6/diff-orig-vs-atomq.patch + probes-r7/proto_apply.py)
Every old text must occur exactly once."""
import sys, pathlib
p = pathlib.Path(sys.argv[1]) / "approvals" / "gate.py"
s = p.read_text(encoding="utf-8")
pairs = [
('''    line = normalise(line)
    # To a fixed point''', '''    line = normalise(line)
    if not defang:
        line = _per_part(line, _wide_ascii)
    # To a fixed point'''),
('''    return _defang_outside_code(line) if defang else _per_part(line, _wide_ascii)''',
 '''    return _defang_outside_code(line) if defang else line'''),
]
for old, new in pairs:
    assert s.count(old) == 1, (s.count(old), old[:60])
    s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("ok")

# ---- step 2 (N8): defang_text decides inline code per paragraph, from markdown-it's own code_inline tokens
s = p.read_text(encoding="utf-8")
old = '''def _outside_code(text: str, fix: Callable[[str], str]) -> str:
    body = {i for s, e, ch in _closed_fences(text) if ch == "`" for i in range(s + 1, e)}
    return "\\n".join(
        line if i in body else _per_part(line, fix) for i, line in enumerate(text.split("\\n"))
    )
'''
new = '''def _cm_code(inner: str) -> str:
    """The content CommonMark gives a code span: one leading and one trailing space dropped when both are there."""
    if len(inner) > 2 and inner[0] == inner[-1] == " " and inner.strip(" "):
        return inner[1:-1]
    return inner


def _unsafe_lines(text: str, lines: list[str]) -> set[int]:
    """Lines of a paragraph where our per-line reading of inline code differs from the renderer's (CommonMark pairs
    backticks across the lines of a paragraph; `_INLINE_CODE` reads one line). Such a paragraph is all prose."""
    bad: set[int] = set()
    for t in _MD.parse(text):
        if t.type != "inline" or not t.map:
            continue
        real = [_cm_code(c.content) for c in (t.children or []) if c.type == "code_inline"]
        mine: list[str] = []
        for line in lines[t.map[0] : t.map[1]]:
            if "``" not in line:
                mine += [_cm_code(m.group(1)[1:-1]) for m in _INLINE_CODE.finditer(line)]
        if real != mine:
            bad.update(range(t.map[0], t.map[1]))
    return bad


def _outside_code(text: str, fix: Callable[[str], str]) -> str:
    lines = text.split("\\n")
    body = {i for s, e, ch in _closed_fences(text) if ch == "`" for i in range(s + 1, e)}
    bad = _unsafe_lines(text, lines)
    return "\\n".join(
        line if i in body else fix(line) if i in bad else _per_part(line, fix)
        for i, line in enumerate(lines)
    )
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("ok2")

# ---- step 3: defang_text reaches a fixed point (one pass writes `[.]` that lets a host name match on the next)
s = p.read_text(encoding="utf-8")
old = '''    part = _PLACEHOLDER_DOT.sub(r"\\1[.]", part)
    return _defang_plain(part)
'''
new = '''    part = _PLACEHOLDER_DOT.sub(r"\\1[.]", part)
    for _ in range(4):
        done = _defang_plain(part)
        if done == part:
            break
        part = done
    return part
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("ok3")

# ---- step 4 (round-trip, first-pass leak): `anna.m@example.org` + `anna.m@example.org` written without a separator:
# the e-mail pattern takes `anna.m@example.organna` (the top-level name swallows the next local part) and leaves `.m@example.org`,
# which no pattern accepts (its local part may not follow a letter). One more pass over the result, only when a placeholder is
# followed by such a rest, masks it. Model path and card path (redact_text is the choke point).
rm = pathlib.Path(sys.argv[1]) / "guard" / "runmap.py"
s = rm.read_text(encoding="utf-8")
pairs = [
('''def redact_text(
    text: str, mapping: dict[str, str], neutralise''', '''_EMAIL_REST = re.compile(r">[.\\-+_][A-Za-z0-9._+\\-]{0,254}(?:@|%40)")


def redact_text(
    text: str, mapping: dict[str, str], neutralise'''),
('''        out, current = result.text, result.mapping
        if views and time.monotonic()''', '''        out, current = result.text, result.mapping
        if _EMAIL_REST.search(out):
            rest = redact(out, mapping=current, _cache=cache)
            out, current = rest.text, rest.mapping
        if views and time.monotonic()'''),
]
for old, new in pairs:
    assert s.count(old) == 1, (s.count(old), old[:50])
    s = s.replace(old, new)
if "\nimport re\n" not in s:
    assert s.count("\nimport time\n") == 1
    s = s.replace("\nimport time\n", "\nimport re\nimport time\n")
rm.write_text(s, encoding="utf-8")
print("ok4")

# ---- step 5 (HL2, found while timing the card path on the base tree): the link-label pattern `_LABEL` has no length bound, so a line
# of `[` characters costs O(n^2) in `_IMAGE`, `_MDLINK`, `_REFDEF` (16,384 characters: 6.3 s; 262,144: about 1,600 s on the base tree).
# Bound the label to 128 characters (linear: 262,144 characters about 1.5 s). A longer label is not matched as a label; its target
# is still removed by `_URL`.
gp = pathlib.Path(sys.argv[1]) / "approvals" / "gate.py"
s = gp.read_text(encoding="utf-8")
old = '_LABEL = r"\\[((?:[^\\]\\\\\\n]|\\\\.)*)\\]"'
new = '_LABEL = r"\\[((?:[^\\]\\\\\\n]|\\\\.){0,128})\\]"'
assert s.count(old) == 1, s.count(old)
gp.write_text(s.replace(old, new), encoding="utf-8")
print("ok5")

# ---- step 6 (HL2): markdown-it's inline parse is quadratic on a line of `[` (its link-label scan; 32,768 characters: 6 s on the card
# path). `_closed_fences` needs block tokens only (fences): parse with the inline core rule off. `_unsafe_lines` needs the inline parse
# (code spans, as a renderer reads them): it runs only on a text that holds a backtick and is at most 16,384 characters; a longer
# text has every line defanged as prose (more defang, never less; Slack shows at most 2,900 characters, so no real card is that long).
# A reduced inline parser (link rules off) was tried first: 5 of 2,000 texts differed from the full parser (a link destination
# that holds a backtick), so it was dropped.
s = gp.read_text(encoding="utf-8")
pairs = [
('_MD = MarkdownIt("commonmark")\n', '_MD = MarkdownIt("commonmark")\n_MD_BLOCK = MarkdownIt("commonmark").disable("inline")\n_CODE_SPAN_MAX = 16384\n'),
('    spans = []\n    for t in _MD.parse(text):', '    spans = []\n    for t in _MD_BLOCK.parse(text):'),
('    bad: set[int] = set()\n    for t in _MD.parse(text):', '    bad: set[int] = set()\n    if "`" not in text:\n        return bad\n    if len(text) > _CODE_SPAN_MAX:\n        return set(range(len(lines)))\n    for t in _MD.parse(text):'),
]
for old, new in pairs:
    assert s.count(old) == 1, (s.count(old), old[:40])
    s = s.replace(old, new)
gp.write_text(s, encoding="utf-8")
print("ok6")

exec(open(pathlib.Path(__file__).with_name("p10_apply7.py")).read())
