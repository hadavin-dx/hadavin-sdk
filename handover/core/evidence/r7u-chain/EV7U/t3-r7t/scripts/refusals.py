"""The one refusal line shared by the helper scripts. A script ends a wrong command line (or a desk that cannot be
reached) with ONE plain line that starts `refused:`, never with a Python traceback. The line never repeats what was
typed (it can hold a key or a path). Exit codes: 2 refused (a wrong input), 3 the thing the script talks to cannot be
reached or did not answer (the codes run_live_check.py and run_real_check.py use).

One source of truth: the line and the codes live in tools/refusing_args.py (the command-line parser needs them too);
this module only re-exports them for the scripts that import them by this name."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the repository folder, for tools/
from tools.refusing_args import EXIT_REFUSED, EXIT_UNREACHABLE, refusal

__all__ = ["EXIT_REFUSED", "EXIT_UNREACHABLE", "refusal"]
