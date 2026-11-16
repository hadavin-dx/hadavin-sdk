# run.py r12 security review (egm-design, condensed copy of the inline report), 2026-11-16T18:26:22Z
Read-only, nothing run. Verdict: 0 blockers, 1 major, 5 minors. r11 holes (positional extras, env=None, absolute /bin/sh) closed.
## Failures first
- M1 Child program allow-list checks only the file name (run.r12.py:373-376): any absolute .../git, .../patch or .../.venv/bin/python passes, not tied to --root. Docstring (148), comments (370, 375) and REPORT-runpy13 point 3 overstate. Arguments (git -c, python -c) and stdin/stdout/env values unchecked. T100a has no accept case for another folder's git. Fix: compare realpath with what tool() found; python must be <ROOT>/.venv/bin/python; add cases.
- m1 "ruff clean, 0 noqa" has no command or output in evidence-r12; repo pyproject excludes handover, so name the file; T98c is a text check only.
- m2 --raw with .. can create a folder inside --root past the check (2986-3028); reasoned, not run.
- m3 T100a accepts any TypeError; unused marker; no case for an env name outside the allow-list.
- m4 total-size comment "can never be reached" is wrong (about 97 KB plus PATH against 131072; effect is a refusal).
- m5 plain --restore clamp is partial (group-write and execute bits from a forged marker still written); say so in the NOTE (limit d).
- m6 open and unfixed: start-up signal window, limit (d), pointer file; mutation controls N0-N10 not run (T100e, T100g, T99g have no mutation proof).
## Not checked
Nothing run; sha256 not recomputed; run.py lines 1094-1589, 1720-1795, 2115-2590, 2700-2830, 3045-3171 not read; hostile-git risk; pid reuse; pointer file design.
