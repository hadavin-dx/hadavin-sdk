"""Mechanical cite fix (no meaning change). usage: python -I fix_ambig.py <doc>...
(1) A bare ':N' that is not directly after another cite gets the nearest preceding path written in front.
(2) A folder-less config.py, cli.py or tools.py gets src/hadavin_sdk/ (the same names exist in demos/ and k1b/)."""
import re
import sys

PATH = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)*[\w-]+\.(?:py|sql|yml|yaml|md|toml|sh))")
NUM = r":(\d+)(?:-(\d+))?"
CITE = re.compile(PATH.pattern + r"((?:" + NUM + r")(?:\s*(?:,|and|;)?\s*(?::\d+(?:-\d+)?))*)")
BARE = re.compile(r"(?<![\w/.)-])" + NUM + r"(?![\d:])")
for doc in sys.argv[1:]:
    out, n1, n2 = [], 0, 0
    for line in open(doc, encoding="utf-8").read().split("\n"):
        spans = [(m.start(), m.end()) for m in CITE.finditer(line)]
        ins = []
        for m in BARE.finditer(line):
            if any(s <= m.start() < e for s, e in spans):
                continue
            pm = list(PATH.finditer(line[: m.start()]))
            if not pm:
                continue
            prev = [x for x in spans if x[1] <= m.start()]
            gap = line[max(x[1] for x in prev) : m.start()] if prev else "xx"
            spans.append((m.start(), m.end()))
            if prev and re.fullmatch(r"\s*(,|;|and|/|,\s*and)?\s*", gap):
                continue
            ins.append((m.start(), pm[-1].group(1)))
        for pos, p in sorted(ins, reverse=True):
            line = line[:pos] + p + line[pos:]
            n1 += 1
        line, k = re.subn(r"(?<![/\w-])(config|cli|tools)\.py(?=:\d)", r"src/hadavin_sdk/\1.py", line)
        n2 += k
        out.append(line)
    open(doc, "w", encoding="utf-8").write("\n".join(out))
    print(doc, "bare cites given a path:", n1, "folder-less names expanded:", n2)
