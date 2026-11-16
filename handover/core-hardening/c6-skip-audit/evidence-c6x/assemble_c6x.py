"""c6x: puts the two appendix files back into the main report at their marker lines '@@INCLUDE <file>@@' (the file must sit next to the main file and be
named REPORT-c6x-TABLE.md or REPORT-c6x-COVERAGE.md). Returns (assembled_text, list_of_included_files). A text with no marker is returned unchanged."""
import re, os
ALLOWED = ("REPORT-c6x-TABLE.md", "REPORT-c6x-COVERAGE.md")
def assemble(path):
    raw = open(path, encoding="utf-8").read()
    inc = []
    def rep(m):
        f = m.group(1)
        if f not in ALLOWED:
            raise SystemExit("include of an unexpected file: " + f)
        body = open(os.path.join(os.path.dirname(os.path.abspath(path)), f), encoding="utf-8").read()
        inc.append(f)
        return body.split("\n", 2)[2] if body.startswith("# ") else body   # the first two lines of an appendix file are its own heading and a blank line
    return re.sub(r"^@@INCLUDE ([^@\n]+)@@\n", lambda m: rep(m), raw, flags=re.M), inc
