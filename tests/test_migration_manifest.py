"""Forward-only enforcement: a migration file that has been released is never edited (P3a-2).

`tests/migration_manifest.json` holds the SHA-256 of every released file (the bytes; `.gitattributes` fixes line
endings to LF). A released file whose bytes change, or that disappears, fails the test. A file that is not in the
manifest is a new, unreleased file: it must be numbered above the highest released file. When a release is tagged,
the lead adds that release's new files to the manifest in the same change (never edits an existing line)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from hadavin_sdk.store.migration_numbers import MIGRATIONS, list_migration_files

MANIFEST = Path(__file__).parent / "migration_manifest.json"


def manifest_problems(folder: Path, manifest: dict[str, str]) -> list[str]:
    problems = []
    for name, digest in sorted(manifest.items()):
        path = folder / name
        if not path.is_file():
            problems.append(f"{name}: a released migration file is missing")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            problems.append(
                f"{name}: a released migration file was edited (forward-only: add a new file)"
            )
    highest = max((int(n[:4]) for n in manifest), default=0)
    for path in list_migration_files(folder):
        if path.name not in manifest and path.name[:4].isdigit() and int(path.name[:4]) <= highest:
            problems.append(
                f"{path.name}: not released, but numbered at or below released migration {highest:04d}"
            )
    return problems


def _manifest() -> dict[str, str]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_released_migration_files_are_unchanged():
    manifest = _manifest()
    assert len(manifest) >= 5, "the manifest must list the released files"
    assert manifest_problems(MIGRATIONS, manifest) == []


def test_every_manifest_digest_is_a_sha256():
    assert all(len(d) == 64 and set(d) <= set("0123456789abcdef") for d in _manifest().values())


@pytest.fixture
def copy(tmp_path):
    for p in list_migration_files(MIGRATIONS):
        (tmp_path / p.name).write_bytes(p.read_bytes())
    return tmp_path


def test_an_edited_released_file_fails(copy):
    target = copy / "0003_approvals_tick.sql"
    target.write_text(target.read_text(encoding="utf-8") + "\n-- edited\n", encoding="utf-8")
    assert manifest_problems(copy, _manifest()) == [
        "0003_approvals_tick.sql: a released migration file was edited (forward-only: add a new file)"
    ]


def test_a_removed_released_file_fails(copy):
    (copy / "0002_audit_chain.sql").unlink()
    assert any(
        "0002_audit_chain.sql: a released migration file is missing" in p
        for p in manifest_problems(copy, _manifest())
    )


def test_a_new_file_above_the_released_ones_passes(copy):
    (copy / "0006_new.sql").write_text("SELECT 1;\n", encoding="utf-8")
    assert manifest_problems(copy, _manifest()) == []


def test_a_new_file_below_the_released_ones_fails(copy):
    (copy / "0003_approvals_tick.sql").rename(copy / "0003_renamed.sql")
    problems = manifest_problems(copy, _manifest())
    assert any("0003_renamed.sql: not released" in p for p in problems), problems
    assert any(
        "0003_approvals_tick.sql: a released migration file is missing" in p for p in problems
    )
