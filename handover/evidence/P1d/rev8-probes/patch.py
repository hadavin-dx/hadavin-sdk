import sys, re, pathlib
root = pathlib.Path(sys.argv[1]) / "src/hadavin_sdk"
g = root / "approvals/gate.py"; s = g.read_text()
s = s.replace("def _clean_line(line: str) -> str:", "def _clean_line(line: str, defang: bool = True) -> str:", 1)
s = s.replace("    return _defang_outside_code(line)\n\n\ndef _clean_prose(lines: list[str]) -> list[str]:",
              "    return _defang_outside_code(line) if defang else line\n\n\ndef _clean_prose(lines: list[str], defang: bool = True) -> list[str]:", 1)
s = s.replace("    out = [_clean_line(line) for line in joined]", "    out = [_clean_line(line, defang) for line in joined]", 1)
# thread defang through sanitise_text by a module flag (prototype only)
s = s.replace("def sanitise_text(text: str) -> str:", "_DEFANG = [True]\ndef sanitise_text(text: str, *, defang: bool = True) -> str:\n    _DEFANG.append(defang)\n    try:\n        return _sanitise(text)\n    finally:\n        _DEFANG.pop()\n\ndef _sanitise(text: str) -> str:", 1)
s = s.replace("def _clean_line(line: str, defang: bool = True) -> str:", "def _clean_line(line: str, defang: bool | None = None) -> str:\n    defang = _DEFANG[-1] if defang is None else defang", 1)
s = s.replace("def _clean_prose(lines: list[str], defang: bool = True) -> list[str]:", "def _clean_prose(lines: list[str], defang: bool | None = None) -> list[str]:", 1)
s += '''

def defang_text(text: str) -> str:
    lines = text.split("\\n")
    fences = _closed_fences(text)
    inside = set()
    for start, last, char in fences:
        if char == "`":
            inside.update(range(start + 1, last))
    return "\\n".join(l if i in inside else _defang_outside_code(l) for i, l in enumerate(lines))
'''
g.write_text(s)
c = root / "approvals/channel.py"; s = c.read_text()
s = s.replace("from hadavin_sdk.approvals.gate import sanitise_text, withhold_commands", "from hadavin_sdk.approvals.gate import defang_text, sanitise_text, withhold_commands")
s = s.replace("            return alt\n    return out", "            return defang_text(alt)\n    return defang_text(out)")
s = s.replace("return withhold_commands(sanitise_text(text))", "return withhold_commands(sanitise_text(text, defang=False))")
c.write_text(s)
if sys.argv[2] == "amp":
    r = root / "guard/redact.py"; s = r.read_text()
    old = r"|[^\s\"';,&]|,(?!"
    assert s.count(old) == 1, s.count(old)
    s = s.replace(old, r"|[^\s\"';,]|,(?!")
    r.write_text(s)
print("patched", sys.argv[2])
