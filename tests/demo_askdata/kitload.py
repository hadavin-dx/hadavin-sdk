"""Loads the VENDORED portal kit for the tests (never for the runtime: `askdata` does not import it).

The kit sits in demos/ask-your-data/vendor/portal-kit (an interim copy of kit PR hadavin-dx/hadavin-demos#5, see
vendor/KIT.lock and the README-INTERIM.md next to it). Its own rules and checker are the judge of an export:
`kit_problems` is the schema plus the cross-field rules plus the chain recomputation, `kitcheck_dir` is the CLI check.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DEMO = Path(__file__).resolve().parents[2] / "demos" / "ask-your-data"
KIT_ROOT = DEMO / "vendor" / "portal-kit"
KIT_LOCK = DEMO / "vendor" / "KIT.lock"
sys.path.insert(0, str(KIT_ROOT))

from hadavin_kit import chain as kit_chain
from hadavin_kit import export_rules, kitcheck, validate

__all__ = ["DEMO", "KIT_LOCK", "KIT_ROOT", "export_rules", "kit_chain", "kit_commit", "kit_problems", "kitcheck", "kitcheck_dir", "rule_problems"]  # fmt: skip


def kit_problems(doc: Any) -> list[str]:
    """Every problem the kit finds in `doc` (empty = valid and internally consistent)."""
    return [str(p) for p in validate.validate(doc)]


def rule_problems(doc: dict[str, Any]) -> list[str]:
    """Only the cross-field rules (export_rules.check), without the schema."""
    return [str(p) for p in export_rules.check(doc)]


def kitcheck_dir(
    doc_text: str, directory: Path, *, deny: list[str] | None = None, lock: bool = True
) -> dict[str, Any]:
    """Write export.json into `directory` and run the kit's own checker on it, as `kitcheck --demo askdata` does."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "export.json").write_text(doc_text, encoding="utf-8", newline="\n")
    return kitcheck.run(directory, demo="askdata", deny=deny, kit_lock=KIT_LOCK if lock else None)


def kit_commit() -> str:
    return json.loads(KIT_LOCK.read_text("utf-8"))["kit_commit"]
