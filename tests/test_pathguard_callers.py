"""pathguard through the real callers: ``score`` and ``replay`` on an outputs folder that holds links out of it.

On main a digest file (``outputs.sha256``) that was a link out of its run folder was followed, and a NUL in the outputs
folder was a bare ``ValueError``; now they are refused: those tests fail on (a). A run folder or a case file that is a link
out of the outputs folder was already refused on main, and a clean folder still scores: those three tests are controls.

Labels, measured by real runs on (a) origin/main source plus this change's ``pathguard.py`` and (b) origin/main as it is (``pathguard`` does not exist on main, so for a file that imports it an empty stand-in module let the file load; a test that calls the module fails there): ``test_control_*`` passes on (a) and (b); ``test_pin_*`` passes on (a) and fails on (b); every other name fails on (a). This file: 3 control, 0 pin, 2 other. Nothing here says a test "fails on old main".
"""

from __future__ import annotations

import os
import shutil

import pytest

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.hashing import hash_files
from hadavin_sdk.k1b.replay import outputs_files
from hadavin_sdk.k1b.score import score
from tests.k1b_support import (
    cause,
    make_bundle,
    make_cause_list,
    record,
    write_answers,
    write_outputs,
)

OK = cause("api", "bad_deploy")
DIAG = {"causes": [OK], "not_sure": False}


def _fixture(tmp_path):
    bundles = tmp_path / "bundles"
    cases = ["case-001", "case-002"]
    for c in cases:
        make_bundle(bundles, c)
    cause_dir = make_cause_list(
        tmp_path / "cause", services=("api", "db"), faults=("bad_deploy", "oom")
    )
    answers = write_answers(
        tmp_path / "answers.json", {c: ([("api", "bad_deploy")], False) for c in cases}
    )
    out = tmp_path / "out"
    write_outputs(out, bundles, cause_dir, [{c: record(c, DIAG) for c in cases}])
    return out, answers, cause_dir, bundles


def _link(target, link, *, directory):
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")


def test_control_a_clean_outputs_folder_still_scores(tmp_path):
    out, answers, cause_dir, bundles = _fixture(tmp_path)
    assert score(out, answers, cause_dir, bundles).runs[0].hits == 2


def test_control_a_run_folder_that_is_a_link_out_of_the_outputs_folder_is_refused(tmp_path):
    out, answers, cause_dir, bundles = _fixture(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    shutil.move(str(out / "run1"), str(elsewhere))
    _link(elsewhere, out / "run1", directory=True)
    with pytest.raises(ConfigError, match="escapes its folder"):
        score(out, answers, cause_dir, bundles)


def test_control_a_case_file_that_is_a_link_out_of_the_outputs_folder_is_refused(tmp_path):
    out, answers, cause_dir, bundles = _fixture(tmp_path)
    stolen = tmp_path / "stolen.json"
    shutil.move(str(out / "run1" / "case-001.json"), str(stolen))
    _link(stolen, out / "run1" / "case-001.json", directory=False)
    with pytest.raises(ConfigError):
        score(out, answers, cause_dir, bundles)


def test_a_replay_digest_file_that_is_a_link_out_counts_as_unreadable_not_as_missing(tmp_path):
    out, answers, cause_dir, bundles = _fixture(tmp_path)
    digest = out / "outputs.sha256"
    other = tmp_path / "other.sha256"
    # the TRUE digest of these outputs: an outside file that is trusted would make the outputs read as unchanged
    other.write_text(hash_files(out, outputs_files(out)) + "\n", encoding="utf-8")
    if digest.exists():
        digest.unlink()
    _link(other, digest, directory=False)
    result = score(out, answers, cause_dir, bundles)
    assert result.outputs_changed is True, "an outside digest file was trusted"
    assert result.warnings == [], "an outside digest file was reported as missing"


def test_a_nul_in_the_outputs_folder_is_a_refusal_not_a_crash(tmp_path):
    out, answers, cause_dir, bundles = _fixture(tmp_path)
    with pytest.raises(ConfigError, match="outputs folder: contains a control character"):
        score(type(out)(str(out) + "\x00x"), answers, cause_dir, bundles)
