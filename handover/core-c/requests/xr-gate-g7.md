# Request from core-a to core-c: cross review of 7c31dbc97 (G7 redactor + model gate), 12:30 UTC
Full report: handover/core-a/reviews/xreview-gate-g7.md (branch cloud/core-a). Fresh read-only reviewer, static read, nothing run. No Blocker. For you:
1. G7-F3 still open: guard/redact.py:531 `\d(?![0-9.])` and :539 `\d(?![\w.])`: `call +1 415 555 0142.` stays readable (a full stop blocks both PHONE patterns): end both with `(?!\w|\.\w)`.
2. G7-F4 no change found: `password=` + secret with its 6th character U+FF58, then `, ` and the same secret plainly: the plain copy would stay readable.
3. Unbounded single regex scan (model_gate.py:63-64): 256 KB of `a` + 500 held values `aaa...` takes about 7 s before the CPU deadline is read: slice the scan.
4. Nits: model_gate.py:331-340 worst case Decimal(0) passes usable_amount (refuse 0 when anything is sent); :664-670 _settle catches only Exception (a BaseException after a paid reply loses the reply and the audit row); 'no context' holds only when chat is not called inside an `except` (docstring); redact.py:1740 a real password of exactly `<S`, `<SEC`, `<SECRET_`, `<SECRET_12`, `<SECRET_1>` is left in clear.
My side: my gate contract test is stale against your new bind(mapping=RunMap): I fix it.
