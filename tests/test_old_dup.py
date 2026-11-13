from __future__ import annotations
import ast
from pathlib import Path
LOOP_1 = ".".join(("127", "0", "0", "1"))
# --- no module keeps its own copy of the loopback list ---------------------------------------------------

SRC = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
# tools.py keeps a list of names a tool manifest may NOT name (an outbound deny list: it also holds metadata names),
# which is a different question from "is this host this computer".
ALLOWED_COPY = {"netguard.py", "tools.py"}


def _strings(node: ast.AST) -> set[str]:
    return {
        n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }


def test_no_module_keeps_its_own_loopback_list() -> None:
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name in ALLOWED_COPY:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Set | ast.Tuple | ast.List | ast.Call):
                found = _strings(node)
                if "localhost" in found and ({LOOP_1, "::1"} & found):
                    offenders.append(f"{path.relative_to(SRC)}:{node.lineno}")
    assert offenders == [], f"a copy of the loopback list: {sorted(set(offenders))}"
