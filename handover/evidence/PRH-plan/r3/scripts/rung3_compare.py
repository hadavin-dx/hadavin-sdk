"""Rung-3 check (PR H rev 3, D7): do ready-made packages cover the need? Run in a throwaway environment:
  uv run --no-project --with regex==2026.9.29 --with strip-ansi==0.1.1 --with stransi==0.3.0 python -I rung3_compare.py ORACLE_DIR PERL_FILE
(a) `regex` \\p{Default_Ignorable_Code_Point}: count and equality with the pinned perl 15.0.0 file;
(b) strip-ansi 0.1.1 and stransi 0.3.0 against the rev-3 oracle's grammar rows (joined reading = expected)."""
import sys, unicodedata
sys.path.insert(0, sys.argv[1])
import hidden_ref_oracle as o
import regex
print("python", sys.version.split()[0], "unidata", unicodedata.unidata_version, "| regex", regex.__version__)
pat = regex.compile(r"\p{Default_Ignorable_Code_Point}")
got = frozenset(c for c in range(0x110000) if not 0xD800 <= c <= 0xDFFF and pat.match(chr(c)))
perl = o.read_range_file(sys.argv[2])
print("(a) regex DI count", len(got), "equal to perl 15.0.0 file:", got == perl, "only regex", [f"{c:04X}" for c in sorted(got - perl)][:10], "only perl", [f"{c:04X}" for c in sorted(perl - got)][:10])
cands = {}
try:
    from strip_ansi import strip_ansi as sa
    cands["strip-ansi 0.1.1"] = sa
except Exception as e:
    print("strip-ansi import failed", type(e).__name__, e)
try:
    import stransi
    def st(t):
        return "".join(x for x in stransi.Ansi(t).escapeless() if isinstance(x, str))
    cands["stransi 0.3.0"] = st
except Exception as e:
    print("stransi import failed", type(e).__name__, e)
for name, f in cands.items():
    agree = 0
    rows = []
    for row, x, j in o.GRAMMAR_ROWS:
        try:
            g = f(x)
        except Exception as e:
            g = "RAISED " + type(e).__name__
        if g == j:
            agree += 1
        else:
            rows.append(f"{row}: {ascii(g)} (oracle {ascii(j)})")
    print(f"(b) {name}: agrees with the oracle on {agree} of {len(o.GRAMMAR_ROWS)} grammar rows; differences:")
    for r in rows:
        print("    ", r)
