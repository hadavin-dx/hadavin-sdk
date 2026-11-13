# REVIEW round 4, lane3-fix-3-r4.patch, egm-codebase-details (security path); saved by lane lead; reviewer ran nothing
BLOCKER none. MAJOR none. This pass found nothing real. MINOR: 1 _LyingStr.strip ignores args: rename *_args. 2 boom() message "embedded null byte" describes input _text refuses earlier: reword. 3 tests check "--f" in the message but not that the value is absent: add not-in asserts. 4 Windows two-drive test never runs on Linux: use ntpath.commonpath/normcase via monkeypatch, drop the skip.
All four applied by lane lead in lane3-fix-3-r5.patch: 414 passed, 5 skipped (new file + old path-confinement tests + hygiene), 0 lines over 120.
CHECKED CORRECT: line length, imports, hygiene, each test vs spec (M03 M08 B1 M11 M15 B2 M20), messages, determinism, mutants per evidence, other threats covered in the old file (by grep).
UNREVIEWED: nothing run; ruff/mypy/bandit not shown; Windows/macOS/other Python versions; old file body.
