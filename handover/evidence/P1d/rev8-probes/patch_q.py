import sys, pathlib, re
p = pathlib.Path(sys.argv[1]) / "src/hadavin_sdk/guard/redact.py"; s = p.read_text()
start = s.index('            r"(?i)(?<![\\w.\\-])[\\w.\\-]{0,40}"')
tuple_start = s.rindex("\n    (\n        \"SECRET\",", 0, start) + 1
end = s.index("\n    ),\n", start) + len("\n    ),\n")
block = s[tuple_start:end]
generic = block.replace(r'(?<![\w.\-])[\w.\-]{0,40}', r'(?<![\w.\-?&])[\w.\-]{0,40}', 1)
query = block.replace(r'(?<![\w.\-])[\w.\-]{0,40}', r'(?<=[?&])[\w.\-]{0,40}', 1).replace(r"|[^\s\"';,]|,(?!", r"|[^\s\"';,&]|,(?!", 1)
assert generic != block and query != block and query != generic
s = s[:tuple_start] + query + generic + s[end:]
p.write_text(s); print("ok")
