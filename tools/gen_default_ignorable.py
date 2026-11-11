"""Make or print the table of Default_Ignorable_Code_Point ranges that `hadavin_sdk.guard.hidden` uses.

The table is DATA: 17 inclusive ranges of code points that a display shows as nothing (zero-width characters, variation
selectors, the combining grapheme joiner, the Hangul fillers, the tag characters, ...). Source: the property of
perl 5.38.2 (Unicode 15.0.0), which equals the `regex` package 2026.9.29 and the derivation rule in the PR H ticket
(checked on 2026-11-11). Python's `unicodedata` does not carry this property.

Two modes (no `--from-ucd`: there is no sample file to test it with):
  --from-codepoints  reads decimal code points, one per line, on standard input (the output of
                     perl -e 'for my $c (0..0x10FFFF){ next if $c>=0xD800 && $c<=0xDFFF;
                                print "$c\\n" if chr($c) =~ /\\p{Default_Ignorable_Code_Point}/ }')
                     merges adjacent code points into ranges and writes the range file to standard output.
  (no option)        reads the range file named by the one argument and prints the `IGNORABLE_RANGES` literal that is
                     pasted into `src/hadavin_sdk/guard/hidden.py`.

LICENCE CHECK IS OPEN: the Unicode data files are published under the Unicode License v3 (from memory, unverified:
www.unicode.org gave no answer from the build machine on 2026-11-11). The range file holds 17 lines of numbers produced
by perl's own tables, not a copy of a Unicode file; the lead or owner must fetch the licence text and confirm.
"""

from __future__ import annotations

import sys

HEADER = (
    "# Default_Ignorable_Code_Point, Unicode 15.0.0, from perl 5.38.2 (Unicode::UCD); "
    "one inclusive range per line, ascending"
)


def merge(points: list[int]) -> list[tuple[int, int]]:
    """Adjacent code points merged into inclusive ranges, ascending."""
    out: list[tuple[int, int]] = []
    for c in sorted(set(points)):
        if out and out[-1][1] == c - 1:
            out[-1] = (out[-1][0], c)
        else:
            out.append((c, c))
    return out


def format_ranges(ranges: list[tuple[int, int]]) -> str:
    return HEADER + "\n" + "".join(f"{a:04X}..{b:04X}\n" for a, b in ranges)


def parse_range_file(text: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lo, _, hi = line.partition("..")
        out.append((int(lo, 16), int(hi or lo, 16)))
    return out


def format_literal(ranges: list[tuple[int, int]]) -> str:
    rows = "".join(f"    (0x{a:04X}, 0x{b:04X}),\n" for a, b in ranges)
    return "IGNORABLE_RANGES: tuple[tuple[int, int], ...] = (\n" + rows + ")\n"


def main(argv: list[str]) -> int:
    if argv == ["--from-codepoints"]:
        points = [int(line) for line in sys.stdin.read().split()]
        sys.stdout.write(format_ranges(merge(points)))
        return 0
    if len(argv) == 1 and not argv[0].startswith("-"):
        with open(argv[0], encoding="ascii") as fh:
            sys.stdout.write(format_literal(parse_range_file(fh.read())))
        return 0
    sys.stderr.write("usage: gen_default_ignorable.py --from-codepoints < points | RANGE_FILE\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
