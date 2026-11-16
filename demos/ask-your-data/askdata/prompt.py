"""PART_A of the model input: the rendered prompt template (design 8.2). Pure text work, no I/O except `load`.

The template holds `{{AS_OF}}`, `{{CATALOG}}`, `{{GLOSSARY}}`, `{{EXEMPLARS}}` and `{{FUNCTIONS}}`. The date comes from
config, never from the clock. `prompt_sha256` covers the RENDERED text, so a change to catalog, glossary or exemplars
changes it (and every fake-model recording key).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from askdata.allowed import FUNCTIONS, SCHEMA, VIEWS

TEMPLATE = Path(__file__).resolve().parent.parent / "config" / "prompts" / "generate.md"
SLOTS = ("AS_OF", "CATALOG", "GLOSSARY", "EXEMPLARS", "FUNCTIONS")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def catalog_text(views: dict[str, tuple[str, ...]] | None = None) -> str:
    """One line per exposed view: `schema.view(col, col, ...)`."""
    return "\n".join(
        f"{SCHEMA}.{v}({', '.join(cols)})" for v, cols in sorted((views or VIEWS).items())
    )


@dataclass(frozen=True)
class Prompt:
    text: str  # PART_A
    prompt_sha256: str
    catalog_sha256: str


def render(
    template: str,
    *,
    as_of: str,
    catalog: str,
    glossary: str = "",
    exemplars: str = "",
    functions: str | None = None,
) -> Prompt:
    values = {
        "AS_OF": as_of, "CATALOG": catalog, "GLOSSARY": glossary, "EXEMPLARS": exemplars,
        "FUNCTIONS": functions if functions is not None else ", ".join(sorted(FUNCTIONS)),
    }  # fmt: skip
    text = template
    for slot in SLOTS:
        text = text.replace("{{" + slot + "}}", values[slot])
    text = text.strip()
    return Prompt(text, sha256_text(text), sha256_text(catalog))


def load(
    *, as_of: str, glossary: str = "", exemplars: str = "", template_path: Path | None = None
) -> Prompt:
    return render(
        (template_path or TEMPLATE).read_text(encoding="utf-8"),
        as_of=as_of, catalog=catalog_text(), glossary=glossary, exemplars=exemplars,
    )  # fmt: skip
