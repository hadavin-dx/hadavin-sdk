"""Cut-test support. With `demo_only/` present everything runs. With it deleted (the CI cut job), the test modules that read demo material are not
collected, and the header says which; the engine, controls, inbox, signature, leak and rule tests all still run (they use tests/fixtures)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
KEEP = {"test_demo_only_rule.py", "test_studio_leak.py"}  # these run with or without demo_only/
collect_ignore: list[str] = []
if (ROOT / "demo_only" / "data").exists():
    sys.path.insert(0, str(ROOT / "demo_only" / "data"))  # the generator modules (gen, gen_cases) import by name
if not (ROOT / "demo_only").exists():
    collect_ignore = sorted(
        p.name for p in HERE.glob("test_*.py") if p.name not in KEEP and "demo_only" in p.read_text(encoding="utf-8")
    )
    collect_ignore.append("../tests_oneshot")


def pytest_report_header(config):
    if collect_ignore:
        return f"demo_only/ is absent (cut test): {len(collect_ignore) - 1} demo-data test modules are not collected: {', '.join(collect_ignore[:-1])}"
    return "demo_only/ present"
