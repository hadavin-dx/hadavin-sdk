# PR77 / P2d-1 round w4, slice SRC (head 62acddd, redaction path)
Reviewer: fresh egm design agent, read-only; ALL inputs derived by reading, UNRUN. Ticket P2d-1.md not found by the reviewer. Saved by the cloud lead.
VERDICT: NOT CLEAN. 1 Major.
M1 MAJOR (new in this head; regression vs 8b2b716): a masked value keeps its leading or trailing Mc/Lm/Sk characters in clear.
 Where: redact.py:1301-1311 runs marks-dropped views BEFORE the primary view; :1196-1200 skips dropped chars so where[] has no entry; :1251 cuts body[where[s]:where[e-1]+1] (excludes edge marks); :1393-1396 _decide refuses to match "<SECRET_1>^".
 Failing input: "café password=Hunter2abc^" (any non-ASCII char) -> "café password=<SECRET_1>^". Leading: "café password=^Hunter2abc" -> "password=^<SECRET_1>". Tail of marks: "Abc123´´´´". Any Sk/Lm/Mc at a value edge.
 Not covered: test_redact_marks.py:71-79 puts marks inside the value only.
 Fix class: extend the cut over adjacent dropped chars on both sides (also in _withhold/blocks), or run primary view first; property test: adding a mark before/after an open-ended value must not change what is masked.
Minor: m1 ASCII ^ and backtick not marks on an all-ASCII line (redact.py:948-951, :976-977; runmap.py:506): "AKIA^IOSFODNN7EXAMPLE" not masked, with one é it is. Major only if the ticket promises every Sk on ASCII lines (unchecked).
 m2 over-withholding fail closed (redact.py:1301-1311): "ᾳ josé@example.com" withholds the whole line; 8b2b716 masked in place. Usability regression.
 m3 clock read once per round but a round runs up to 4 views; 262k-char line can overrun 6 s by about one round (still fail closed); check per view.
 m4 Hangul 90000 still refused whole (documented, test_marks_15). m5 PuTTY-first ordering: no tail case found (Nit).
W3 findings: F1 fixed, F2 partly (memo for >=1024 chars), F3 documented, F4 fixed (redact.py:1168-1171), F5 fixed, F6 fixed, F7 documented.
Checked, no failing input: position map interior cuts, hidden categories (open: tag-character GAP-1 declared), PuTTY/PEM order, work/time caps.
COVERAGE: DELTA.patch 1-570; redact.py 480-700 and 860-1459 (1-479, 700-859, 1460-end NOT read); textnorm.py 225-624 (1-224, 625-end not read); runmap.py 225-544 (1-224, 545-end not read); defaults.py delta only; _confusables.py not read; tests/test_redact_marks.py 150-250. Not a clean pass for unread ranges.
