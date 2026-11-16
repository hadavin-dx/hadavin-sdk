import sys, io, contextlib
from datetime import date
sys.path.insert(0, ".")
from tools import policy_page as pp
for d in (date(2026,12,11), date(2026,12,12)):
    for mode in ("--write","--check"):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = pp.main([mode], today=d)
        print(f"today={d} {mode} rc={rc} stderr={err.getvalue().strip()[:600]!r}")
