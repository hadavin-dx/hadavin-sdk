"""Guard: no third-party reference material (vendor UI screenshots, course images, PDFs) and no vendor brand
strings may enter this repo. Reference material stays in the owner's studio folder (owner rule 2026-11-01;
Client deliveries are self-contained and we never copy a vendor's name, logo, text, icons or screens)."""

import hashlib
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HASHES = {
    line.strip()
    for line in (ROOT / "tests" / "fixtures" / "reference_material_sha256.txt")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip() and not line.startswith("#")
}
# Brand strings of the vendor product our client portal is inspired by. Case-sensitive on purpose.
BANNED = (
    "getport.io",
    "demo.port.io",
    "app.port.io",
    "Port.io",
    "Port MCP",
    "Agent Control Center",
    "Skills Marketplace",
    "MCP Hub",
    "Context Lake",
    "Golden Path",
)
# Screenshot-style file names (browser capture, phone export) never belong in the repo.
BAD_NAMES = re.compile(r"^(Screenshot[ _]\d{4}-\d{2}-\d{2}|WhatsApp Image)", re.IGNORECASE)
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".sql",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".cfg",
}
SELF = {"tests/test_no_reference_material.py", "tests/fixtures/reference_material_sha256.txt"}


def _tracked():
    """Every file under the repo root except VCS/venv/cache folders (untracked copies count too)."""
    skip = {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        ".ruff_cache",
        ".pytest_cache",
        ".mypy_cache",
    }
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip]
        found += [(Path(dirpath) / f).relative_to(ROOT).as_posix() for f in filenames]
    return found


def test_no_reference_image_or_pdf_is_tracked():
    bad = []
    for rel in _tracked():
        path = ROOT / rel
        if not path.is_file():
            continue
        if BAD_NAMES.match(path.name):
            bad.append(f"{rel}: screenshot-style file name")
        elif (
            path.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf"}
            and hashlib.sha256(path.read_bytes()).hexdigest() in HASHES
        ):
            bad.append(f"{rel}: identical to a reference image/PDF from the course source folder")
    assert not bad, "reference material in the repo: " + "; ".join(bad)


def test_no_vendor_brand_string_is_tracked():
    bad = []
    for rel in _tracked():
        if rel in SELF or Path(rel).suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = (ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        bad += [f"{rel}: {s!r}" for s in BANNED if s in text]
    assert not bad, "vendor brand strings in the repo: " + "; ".join(bad)


def test_the_guard_catches_a_planted_copy(tmp_path):
    assert HASHES, "hash list is empty: the guard would guard nothing"
    planted = tmp_path / "Screenshot 2026-10-29 224803.png"
    assert BAD_NAMES.match(planted.name)
