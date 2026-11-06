"""``THIRD-PARTY-NOTICES.md`` carries the Unicode License v3 text that the look-alike data requires next to every copy of it.

The test is not circular: the grant sentence is written here once as a literal (copied from the licence text; a reviewer compares it with
the official page), the file must hold it, name the covered files, and the sha256 of the licence text between the two marker lines,
recomputed here, must equal both the value on the first lines of the file and the value pinned in ``tests/fixtures/third_party_notices.json``.
A later edit of the licence text therefore fails until the pin is changed on purpose. The mutation runs do not list this file (the notices
file is not copied into a mutant tree).
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTICES = ROOT / "THIRD-PARTY-NOTICES.md"
PIN = json.loads(
    (Path(__file__).parent / "fixtures" / "third_party_notices.json").read_text(encoding="utf-8")
)
BEGIN, END = "<!-- LICENSE-TEXT-BEGIN -->", "<!-- LICENSE-TEXT-END -->"
GRANT = "Permission is hereby granted, free of charge, to any person obtaining a copy of data files and any associated documentation"
COVERED = (
    "tools/data/confusables.txt",
    "tools/data/Scripts.txt",
    "src/hadavin_sdk/guard/_confusables.py",
    "src/hadavin_sdk/guard/_scripts.py",
    "tools/gen_confusables.py",
)


def _licence_text(text):
    assert text.count(BEGIN) == 1 and text.count(END) == 1, "the marker lines must each occur once"
    start = text.index(BEGIN) + len(BEGIN) + 1  # past the marker line and its newline
    return text[start : text.index(END)]


def test_the_notices_file_holds_the_licence_grant_and_names_the_covered_files():
    text = NOTICES.read_text(encoding="utf-8")
    licence = _licence_text(text)
    assert GRANT in " ".join(licence.split()), (
        "the grant sentence of the Unicode License is not in the file"
    )
    assert "UNICODE LICENSE V3" in licence
    for path in COVERED:
        assert path in text, path
        assert (ROOT / path).is_file(), path
    assert "https://www.unicode.org/license.txt" in text
    assert "15.1.0" in text and "2023-08-11" in text and "2023-07-28" in text


def test_the_licence_text_is_the_pinned_one():
    text = NOTICES.read_text(encoding="utf-8")
    actual = hashlib.sha256(_licence_text(text).encode("utf-8")).hexdigest()
    first_lines = "\n".join(text.splitlines()[:12])
    on_file = re.search(r"sha256 of the licence text[^:]*: ([0-9a-f]{64})", first_lines)
    assert on_file, "the sha256 of the licence text is not on the first lines"
    assert on_file[1] == actual, "the licence text changed but the value on the first lines did not"
    assert PIN["licence_sha256"] == actual, (
        "the licence text changed: update tests/fixtures/third_party_notices.json on purpose"
    )


def test_the_data_sha256_in_the_notices_is_the_one_the_generator_pins():
    text = NOTICES.read_text(encoding="utf-8")
    generator = (ROOT / "tools" / "gen_confusables.py").read_text(encoding="utf-8")
    pinned = re.search(r'PINNED_SHA256 = "([0-9a-f]{64})"', generator)[1]
    assert pinned in text
    assert (
        hashlib.sha256((ROOT / "tools" / "data" / "confusables.txt").read_bytes()).hexdigest()
        == pinned
    )
    scripts = re.search(r'PINNED_SCRIPTS_SHA256 = "([0-9a-f]{64})"', generator)[1]
    assert scripts in text
    assert (
        hashlib.sha256((ROOT / "tools" / "data" / "Scripts.txt").read_bytes()).hexdigest()
        == scripts
    )
