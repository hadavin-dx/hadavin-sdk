# P2d-1: one gap-tolerant view (design note, round 6)

Why the view list failed: each hiding technique (tab-like run, escape sequence, mark) had its own view, so a key that used two of them, or a 4th run, was in no view.

Design built (sounder than "drop all, then decide the boundary per edge" on the dropped text, because the patterns are 75 regexes with their own boundary rules and cannot be told about edges after the fact):
1. ONE view per line holds every hidden item (white-space-like controls, whole escape sequences, characters the fold drops, with `marks` also spacing marks and modifier letters). Each maximal run of them becomes ONE private-use character `GAP` (U+E000: no word character, no white space). A position map keeps where each GAP starts and stops in the written line.
2. Each pattern is rewritten once (from the regex parse tree, `re._parser`/`re._compiler`) so that every item it reads may be followed by any number of GAPs, and the item itself never matches a GAP (guard in front), so a GAP is read in one way only and matching stays linear. Boundary assertions are untouched: they see GAP, which is a non-word character, so an edge next to a gap is a boundary (the gap may stand for a space) while an interior gap is skipped. Backtracking decides each edge on its own. Look-aheads are rewritten, look-behinds are not.
3. A match maps back to the written line and covers the gaps inside it; GAPs at its two ends are trimmed so the tab or sequence beside a value stays in the text.
4. The primary view (everything as written, tabs read as spaces) stays for real separators. Escape sequences have two readings (2: the last character of the sequence is a real letter of the key); those are the only extra views.
5. Cost: views per line = primary + 1 (+1 with escape sequences) (+ marks variants), no run limit. The `strip_ansi` pass no longer cuts placeholders.
Not covered / unchanged: the rewrite relies on private Python modules (`re._parser`, `re._compiler`, Python 3.12/3.13 tested); a test pins that every pattern is rewritten.
