import re,sys
files=["README.md","docs/limits.md","docs/settings.md","docs/tests.md","load_tools/README.md"]
kw=re.compile(r"(connection|503|busy|body|header|timeout|burst|drain|per second|rate|LOAD_N|simultaneous|at once|concurren|bytes|KiB|MiB|MB|\b\d{2,}\b ?(s|seconds|ms|requests|connections|leads|threads))",re.I)
num=re.compile(r"\d")
for f in files:
    for i,l in enumerate(open(f,encoding="utf-8"),1):
        for s in re.split(r"(?<=[.;:])\s+(?=[A-Z`*(])",l.strip()):
            if kw.search(s) and num.search(s):
                print(f"{f}:{i}\t{s[:600]}")
