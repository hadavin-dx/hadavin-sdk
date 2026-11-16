"""K1b phase 1: the moved error bound and the file-set digest."""

import hashlib

import pytest

from hadavin_sdk import evals, hashing, stats
from hadavin_sdk.errors import ConfigError


def test_bound_hand_checked_and_edges():
    assert 1 - stats.upper_error_bound(2, 4) == pytest.approx(0.0976, abs=0.001)
    assert stats.upper_error_bound(0, 0) is None
    assert stats.upper_error_bound(4, 4) == 1.0
    with pytest.raises(ValueError):
        stats.upper_error_bound(5, 4)


def test_evals_keeps_the_same_function():
    assert evals.upper_error_bound is stats.upper_error_bound


def test_hash_files_known_value_and_order_independence(tmp_path):
    (tmp_path / "b.txt").write_bytes(b"two")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.txt").write_bytes(b"one")

    def inner(data):
        return hashlib.sha256(data).hexdigest()

    expect = hashlib.sha256(
        b"b.txt\0"
        + inner(b"two").encode()
        + b"\n"
        + b"sub/a.txt\0"
        + inner(b"one").encode()
        + b"\n"
    ).hexdigest()
    assert hashing.hash_files(tmp_path, ["sub/a.txt", "b.txt"]) == expect
    assert hashing.hash_files(tmp_path, ["b.txt", "sub/a.txt", "b.txt"]) == expect


def test_hash_files_changes_with_content_and_name(tmp_path):
    (tmp_path / "a").write_bytes(b"x")
    h1 = hashing.hash_files(tmp_path, ["a"])
    (tmp_path / "a").write_bytes(b"y")
    assert hashing.hash_files(tmp_path, ["a"]) != h1


@pytest.mark.parametrize("bad", ["../x", "/etc/passwd", "sub/../../x"])
def test_hash_files_refuses_escapes(tmp_path, bad):
    with pytest.raises(ConfigError):
        hashing.hash_files(tmp_path, [bad])


def test_hash_files_canonical_names_and_errors(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").write_bytes(b"x")
    base = hashing.hash_files(tmp_path, ["a/b"])
    assert hashing.hash_files(tmp_path, ["a/b", "./a/b", "a//b", "a/../a/b"]) == base
    for bad in ["a", "missing", "a" + chr(92) + "b", "a" + chr(0) + "b"]:
        with pytest.raises(ConfigError):
            hashing.hash_files(tmp_path, [bad])
