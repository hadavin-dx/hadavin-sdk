"""Where the runtime finds its data files. The kit is vendored as ONE tree with this layout:

    <root>/hadavin_kit/   the package          <root>/schema/demo-export.v1.json
    <root>/console/       the console sources  <root>/KIT.lock (written by tools/vendor.py)

`<root>` is the parent of the package directory, or `HADAVIN_KIT_ROOT` when set. A copy that took only the package
fails with `KitLayoutError` and says what is missing, instead of with a crash deep inside a check.
"""

from __future__ import annotations

import os
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("HADAVIN_KIT_ROOT") or PKG.parent).resolve()
SCHEMA = ROOT / "schema" / "demo-export.v1.json"
CONSOLE = ROOT / "console"
LOCK = ROOT / "KIT.lock"


class KitLayoutError(RuntimeError):
    pass


def require(path: Path) -> Path:
    if not path.exists():
        raise KitLayoutError(
            f"the vendored kit is incomplete: {path} is missing. Vendor the whole tree "
            "(hadavin_kit/, schema/, console/) with portal-kit/tools/vendor.py copy, not just the package."
        )
    return path
