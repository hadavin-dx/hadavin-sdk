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


def test_no_reference_file_is_tracked():
    """Hash every file whatever its suffix (a renamed copy or a .webp/.gif/no-extension copy must not slip by)."""
    bad = []
    for rel in _tracked():
        path = ROOT / rel
        if not path.is_file() or rel in SELF:
            continue
        if BAD_NAMES.match(path.name):
            bad.append(f"{rel}: screenshot-style file name")
        elif hashlib.sha256(path.read_bytes()).hexdigest() in HASHES:
            bad.append(f"{rel}: identical to a reference image/PDF from the course source folder")
    assert not bad, "reference material in the repo: " + "; ".join(bad)


def test_no_vendor_brand_string_is_tracked():
    """Scan every text file (any suffix, e.g. .tsx/.svg); binary files are skipped; undecodable text FAILS."""
    bad = []
    for rel in _tracked():
        if rel in SELF:
            continue
        try:
            raw = (ROOT / rel).read_bytes()
        except OSError as exc:
            bad.append(f"{rel}: unreadable ({exc.__class__.__name__})")
            continue
        if b"\0" in raw:  # binary: covered by the hash test
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            bad.append(f"{rel}: not UTF-8 text, cannot be scanned for vendor strings")
            continue
        bad += [f"{rel}: {s!r}" for s in BANNED if s in text]
    assert not bad, "vendor brand strings or unscannable files in the repo: " + "; ".join(bad)


def test_the_guard_catches_a_planted_copy(tmp_path):
    assert HASHES, "hash list is empty: the guard would guard nothing"
    planted = tmp_path / "Screenshot 2026-10-29 224803.png"
    assert BAD_NAMES.match(planted.name)
