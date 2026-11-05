"""tools/make_secrets.py: creates the four non-owner values, never prints one, never overwrites or reorders a line, idempotent."""

from __future__ import annotations

import os
import re
import stat
import sys

import pytest

from intake import secret_store as ss
from tools import make_secrets as ms


def read(tmp_path) -> str:
    return (tmp_path / "secrets" / "secrets.env").read_text(encoding="utf-8")


def test_creates_the_file_with_only_the_four_names_and_all_pass_the_rules(tmp_path):
    added = ms.make_secrets(tmp_path)
    assert added == [ss.WEBHOOK_SECRET, ss.APPROVER_PASSPHRASE, ss.N8N_ENCRYPTION_KEY, ss.N8N_PASSWORD, ms.PASSPHRASE_FILE]
    assert set(ss.parse(tmp_path / "secrets" / "secrets.env")) == set(ms.CREATED)  # the API key is the owner's: not created
    assert {n: ss.status(n, tmp_path) for n in ms.CREATED} == dict.fromkeys(ms.CREATED, "ok")
    assert ss.status(ss.API_KEY, tmp_path) == "key_name_missing"


def test_idempotent_and_never_overwrites_or_reorders(tmp_path):
    d = tmp_path / "secrets"
    d.mkdir()
    owner = "# the owner's file\n" + ss.API_KEY + "=" + "sk" + "-" + "k" * 30 + "\n" + ss.N8N_PASSWORD + "=" + "Mine" + "1" * 30 + "\n"
    (d / "secrets.env").write_text(owner, encoding="utf-8", newline="\n")
    added = ms.make_secrets(tmp_path)
    assert ss.N8N_PASSWORD not in added and ss.API_KEY not in added
    after = read(tmp_path)
    assert after.startswith(owner)  # existing lines untouched and first
    again = ms.make_secrets(tmp_path)
    assert again == [] and read(tmp_path) == after  # second run changes nothing


def test_file_without_final_newline_is_not_joined_to_the_first_new_line(tmp_path):
    d = tmp_path / "secrets"
    d.mkdir()
    (d / "secrets.env").write_bytes((ss.API_KEY + "=" + "sk" + "-" + "k" * 30).encode())
    ms.make_secrets(tmp_path)
    assert ss.status(ss.API_KEY, tmp_path) == "ok" and ss.status(ss.WEBHOOK_SECRET, tmp_path) == "ok"


def test_refuses_to_append_to_a_corrupt_or_non_utf8_file(tmp_path):
    d = tmp_path / "secrets"
    d.mkdir()
    (d / "secrets.env").write_bytes(b"\xff\xfe junk")
    with pytest.raises(ss.SecretError) as ei:
        ms.make_secrets(tmp_path)
    assert ei.value.code == "key_encoding"
    assert (d / "secrets.env").read_bytes() == b"\xff\xfe junk"


def test_n8n_password_complexity_loop(monkeypatch, tmp_path):
    # call order: webhook, passphrase, n8n key, then the password, which is redrawn until it has a digit, an upper-case and a lower-case letter
    seq = iter(["w" * 32, "p" * 32, "k" * 43, "a" * 32, "A" * 32, "1" * 32, "aA1" + "b" * 29])
    monkeypatch.setattr(ms.secrets, "token_urlsafe", lambda n: next(seq))
    ms.make_secrets(tmp_path)
    assert ss.get(ss.N8N_PASSWORD, local=tmp_path) == "aA1" + "b" * 29
    assert next(seq, None) is None  # all drawn values were consumed: the loop ran exactly three redraws


def test_passphrase_copy_holds_only_the_passphrase_and_can_be_recreated(tmp_path):
    ms.make_secrets(tmp_path)
    p = tmp_path / "secrets" / ms.PASSPHRASE_FILE
    assert p.read_text().strip() == ss.get(ss.APPROVER_PASSPHRASE, local=tmp_path)
    p.unlink()
    assert ms.make_secrets(tmp_path) == []  # not recreated unprompted
    assert ms.make_secrets(tmp_path, passphrase_file=True) == [ms.PASSPHRASE_FILE]
    assert p.read_text().strip() == ss.get(ss.APPROVER_PASSPHRASE, local=tmp_path)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_files_are_owner_only(tmp_path):
    ms.make_secrets(tmp_path)
    for n in ("secrets.env", ms.PASSPHRASE_FILE):
        assert stat.S_IMODE(os.stat(tmp_path / "secrets" / n).st_mode) == 0o600


def test_main_prints_only_names_and_done(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path))
    assert ms.main([]) == 0
    out = capsys.readouterr()
    vals = ss.parse(tmp_path / "secrets" / "secrets.env")
    for v in sum(vals.values(), []):
        assert v not in out.out + out.err
    assert out.out.splitlines()[-1] == "done" and "added HADAVIN_WEBHOOK_SECRET" in out.out
    assert ms.main(["--bogus"]) == 3


def test_main_without_local_is_exit_3(monkeypatch, capsys):
    monkeypatch.delenv("HADAVIN_LOCAL", raising=False)
    assert ms.main([]) == 3
    assert "local_unset" in capsys.readouterr().err


# ---- review fixes: lock, OS errors, torn last line, passphrase copy, notes, folder mode ----------------------------------------------------------
def test_two_sequential_runs_append_nothing_the_second_time_and_leave_no_lock(tmp_path):
    ms.make_secrets(tmp_path)
    first = read(tmp_path)
    assert ms.make_secrets(tmp_path) == [] and read(tmp_path) == first
    assert not (tmp_path / "secrets" / ms.LOCK_NAME).exists()


def test_a_held_lock_stops_the_run_names_the_lock_and_the_remedy_and_is_not_deleted_by_the_loser(tmp_path, monkeypatch, capsys):
    (tmp_path / "secrets").mkdir()
    lock = tmp_path / "secrets" / ms.LOCK_NAME
    lock.write_text("x")
    with pytest.raises(ms.ConfigError) as ei:
        ms.make_secrets(tmp_path)
    assert ms.LOCK_NAME in ei.value.text and "delete it" in ei.value.text
    assert lock.exists()  # the holder's lock stays
    assert not (tmp_path / "secrets" / "secrets.env").exists()
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path))
    assert ms.main([]) == 3 and ms.LOCK_NAME in capsys.readouterr().err


def test_main_turns_an_os_error_into_a_fixed_message_without_a_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path))

    def boom(*a, **k):
        raise FileExistsError(17, "exists", str(tmp_path / "secrets" / "secrets.env"))

    monkeypatch.setattr(ms, "_atomic_write", boom)
    assert ms.main([]) == 3
    err = capsys.readouterr().err
    assert err.strip() == "error: bad_config: file error" and str(tmp_path) not in err
    assert not (tmp_path / "secrets" / ms.LOCK_NAME).exists()  # the lock is removed in finally


def test_a_torn_last_line_is_refused_and_the_file_is_untouched(tmp_path):
    d = tmp_path / "secrets"
    d.mkdir()
    raw = (ss.API_KEY + "=" + "sk" + "-" + "k" * 30 + "\n" + ss.N8N_ENCRYPTION_KEY + "=abc").encode()
    (d / "secrets.env").write_bytes(raw)
    with pytest.raises(ss.SecretError) as ei:
        ms.make_secrets(tmp_path)
    assert ei.value.code == "key_malformed" and (d / "secrets.env").read_bytes() == raw
    assert not (d / ms.LOCK_NAME).exists()


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks need privileges on Windows")
def test_the_passphrase_copy_never_follows_a_symlink_or_keeps_an_old_mode(tmp_path):
    ms.make_secrets(tmp_path)
    p = tmp_path / "secrets" / ms.PASSPHRASE_FILE
    target = tmp_path / "victim.txt"
    target.write_text("keep me")
    p.unlink()
    p.symlink_to(target)
    ms.make_secrets(tmp_path, passphrase_file=True)
    assert target.read_text() == "keep me" and not p.is_symlink()
    p.chmod(0o666)
    ms.make_secrets(tmp_path, passphrase_file=True)
    assert stat.S_IMODE(p.stat().st_mode) == 0o600


def test_the_passphrase_copy_is_replaced_by_a_fresh_file(tmp_path):
    ms.make_secrets(tmp_path)
    p = tmp_path / "secrets" / ms.PASSPHRASE_FILE
    p.write_text("stale and longer than the passphrase " * 5)
    ms.make_secrets(tmp_path, passphrase_file=True)
    assert p.read_text().strip() == ss.get(ss.APPROVER_PASSPHRASE, local=tmp_path) and len(p.read_text()) < 100


def test_a_kept_name_with_an_unusable_value_is_noted_on_stderr_by_name_only(tmp_path, capsys):
    d = tmp_path / "secrets"
    d.mkdir()
    (d / "secrets.env").write_text(ss.N8N_PASSWORD + "=tiny9\n" + ss.WEBHOOK_SECRET + "=\n", encoding="utf-8")
    ms.make_secrets(tmp_path)
    err = capsys.readouterr().err
    assert f"kept existing {ss.N8N_PASSWORD} (run intake check)" in err and f"kept existing {ss.WEBHOOK_SECRET} (run intake check)" in err
    assert "tiny9" not in err
    assert "tiny9" in read(tmp_path)  # and the value was not overwritten


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_the_secrets_folder_is_created_0700(tmp_path):
    ms.make_secrets(tmp_path)
    assert stat.S_IMODE(os.stat(tmp_path / "secrets").st_mode) == 0o700


def test_a_truncated_value_that_is_still_long_enough_counts_as_torn(tmp_path):
    d = tmp_path / "secrets"
    d.mkdir()
    for n, keep in ((ss.N8N_ENCRYPTION_KEY, 40), (ss.WEBHOOK_SECRET, 31)):
        # a created value has an exact length (43 and 32); a shorter last line without a newline may be a torn write, even above the minimum
        raw = (n + "=" + "k" * keep).encode()
        (d / "secrets.env").write_bytes(raw)
        with pytest.raises(ss.SecretError) as ei:
            ms.make_secrets(tmp_path)
        assert ei.value.code == "key_malformed" and (d / "secrets.env").read_bytes() == raw
    (d / "secrets.env").write_bytes((ss.N8N_ENCRYPTION_KEY + "=" + "k" * 43).encode())  # the exact created length is a complete line
    assert ss.N8N_ENCRYPTION_KEY not in ms.make_secrets(tmp_path)


def test_created_lengths_match_token_urlsafe():
    import secrets as std

    for name, n in ms.CREATED.items():
        assert ms._created_length(name) == len(std.token_urlsafe(n))


def test_the_passphrase_copy_is_never_written_through_a_hard_link(tmp_path):
    """Survivor of the earlier mutation sample (O_TRUNC instead of unlink + O_EXCL): a hard link works on Windows and POSIX alike."""
    ms.make_secrets(tmp_path)
    p = tmp_path / "secrets" / ms.PASSPHRASE_FILE
    p.write_text("STALE" + chr(10))
    victim = tmp_path / "victim.txt"
    os.link(p, victim)
    ms.make_secrets(tmp_path, passphrase_file=True)
    assert victim.read_text() == "STALE" + chr(10)  # the other name of the old inode is untouched (O_TRUNC would have rewritten it)
    assert p.read_text().strip() == ss.get(ss.APPROVER_PASSPHRASE, local=tmp_path) and os.stat(p).st_nlink == 1


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_an_existing_loose_key_file_is_tightened_with_a_note(tmp_path, capsys):
    ms.make_secrets(tmp_path)
    f = tmp_path / "secrets" / "secrets.env"
    f.chmod(0o644)
    ms.make_secrets(tmp_path)
    assert stat.S_IMODE(os.stat(f).st_mode) == 0o600 and "tightened" in capsys.readouterr().err


def test_relative_hadavin_local_is_exit_3(monkeypatch, capsys):
    monkeypatch.setenv("HADAVIN_LOCAL", "relative/dir")
    assert ms.main([]) == 3 and "absolute" in capsys.readouterr().err


def test_a_duplicated_passphrase_with_passphrase_file_changes_nothing(tmp_path):
    d = tmp_path / "secrets"
    d.mkdir()
    raw = (ss.APPROVER_PASSPHRASE + "=" + "p" * 30 + chr(10)) * 2
    (d / "secrets.env").write_text(raw, encoding="utf-8", newline=chr(10))
    before = (d / "secrets.env").read_bytes()
    with pytest.raises(ss.SecretError) as ei:
        ms.make_secrets(tmp_path, passphrase_file=True)
    assert ei.value.code == "key_duplicate" and (d / "secrets.env").read_bytes() == before  # no new names appended before validation
    assert not (d / ms.PASSPHRASE_FILE).exists() and not (d / ms.LOCK_NAME).exists()


def test_every_created_level_exists_and_the_run_works_in_a_deep_new_folder(tmp_path):
    deep = tmp_path / "a" / "b" / "c"
    ms.make_secrets(deep)
    assert (deep / "secrets" / "secrets.env").is_file()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_every_created_level_is_0700_and_a_loose_passphrase_copy_is_tightened(tmp_path, capsys):
    deep = tmp_path / "a" / "b"
    ms.make_secrets(deep)
    for d in (deep, deep / "secrets", tmp_path / "a"):
        assert stat.S_IMODE(os.stat(d).st_mode) == 0o700, d
    copy = deep / "secrets" / ms.PASSPHRASE_FILE
    copy.chmod(0o644)
    ms.make_secrets(deep)
    assert stat.S_IMODE(os.stat(copy).st_mode) == 0o600 and "tightened" in capsys.readouterr().err


def test_a_bad_existing_passphrase_without_passphrase_file_keeps_it_and_adds_the_rest(tmp_path, capsys):
    d = tmp_path / "secrets"
    d.mkdir()
    (d / "secrets.env").write_text(ss.APPROVER_PASSPHRASE + "=tiny9" + chr(10), encoding="utf-8")
    added = ms.make_secrets(tmp_path, passphrase_file=False)
    assert ss.APPROVER_PASSPHRASE not in added and ms.PASSPHRASE_FILE not in added and not (d / ms.PASSPHRASE_FILE).exists()
    assert {ss.WEBHOOK_SECRET, ss.N8N_ENCRYPTION_KEY, ss.N8N_PASSWORD} <= set(added)
    assert f"kept existing {ss.APPROVER_PASSPHRASE}" in capsys.readouterr().err
    assert ss.status(ss.APPROVER_PASSPHRASE, tmp_path) == "key_short"  # and the value was not replaced
    with pytest.raises(ss.SecretError):  # the same bad value with --passphrase-file stops before any change
        ms.make_secrets(tmp_path, passphrase_file=True)


def test_the_torn_write_refusal_says_what_to_do(tmp_path):
    d = tmp_path / "secrets"
    d.mkdir()
    (d / "secrets.env").write_bytes((ss.N8N_ENCRYPTION_KEY + "=abc").encode())
    with pytest.raises(ss.SecretError) as ei:
        ms.make_secrets(tmp_path)
    assert "repair or remove that line" in ei.value.text and "newline" in ei.value.text


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_an_existing_loose_folder_is_set_to_0700_with_a_note(tmp_path, capsys):
    (tmp_path / "secrets").mkdir(mode=0o755)
    (tmp_path / "secrets").chmod(0o755)
    ms.make_secrets(tmp_path)
    assert stat.S_IMODE(os.stat(tmp_path / "secrets").st_mode) == 0o700
    assert "existing key folder to 0700" in capsys.readouterr().err


def test_the_key_file_is_replaced_atomically_and_a_failed_replace_leaves_the_old_file(tmp_path, monkeypatch):
    d = tmp_path / "secrets"
    d.mkdir()
    old = (ss.API_KEY + "=" + "sk" + "-" + "k" * 30 + chr(10)).encode()
    (d / "secrets.env").write_bytes(old)

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(ms.os, "replace", boom)
    with pytest.raises(OSError):
        ms.make_secrets(tmp_path)
    assert (d / "secrets.env").read_bytes() == old  # not torn, not partly appended
    assert not (d / "secrets.env.tmp").exists() and not (d / ms.LOCK_NAME).exists()
    monkeypatch.undo()
    ms.make_secrets(tmp_path)
    assert (d / "secrets.env").read_bytes().startswith(old) and not (d / "secrets.env.tmp").exists()


def test_generated_values_are_printable_ascii_and_have_the_exact_length(monkeypatch, tmp_path):
    ms.make_secrets(tmp_path)
    for name in ms.CREATED:
        v = ss.get(name, local=tmp_path)
        assert re.fullmatch(r"[A-Za-z0-9_-]+", v) and len(v) == ms._created_length(name)
    seq = iter(["has space" + "a" * 23, "ünï" + "a" * 29, "a" * 31, "w" * 32, "p" * 32, "k" * 43, "aA1" + "b" * 29])
    monkeypatch.setattr(ms.secrets, "token_urlsafe", lambda n: next(seq))
    (tmp_path / "x").mkdir()
    ms.make_secrets(tmp_path / "x")
    assert ss.get(ss.WEBHOOK_SECRET, local=tmp_path / "x") == "w" * 32  # the three bad draws (space, non-ASCII, wrong length) were redrawn


def test_repo_root_is_none_for_an_installed_wheel(monkeypatch, tmp_path):
    monkeypatch.setattr(ss, "REPO_ROOT", None)
    assert ss.inside_repo(tmp_path) is False


def test_a_stale_temporary_key_file_is_removed_under_the_lock_with_a_message_naming_it(tmp_path, capsys):
    d = tmp_path / "secrets"
    d.mkdir()
    (d / "secrets.env").write_text(ss.API_KEY + "=" + "sk" + "-" + "k" * 30 + chr(10), encoding="utf-8")
    stale = d / "secrets.env.tmp"
    stale.write_text("left behind by a crash: holds key file content")
    added = ms.make_secrets(tmp_path)
    assert not stale.exists() and ss.WEBHOOK_SECRET in added
    assert "removed a stale temporary key file (secrets.env.tmp)" in capsys.readouterr().err
    assert ss.status(ss.WEBHOOK_SECRET, tmp_path) == "ok" and ss.status(ss.API_KEY, tmp_path) == "ok"


def test_the_atomic_write_goes_through_replace_never_in_place(tmp_path, monkeypatch):
    """Behaviour, not a call shape: when the replace step fails nothing at all is written to the key file (an in-place write would have succeeded)."""
    d = tmp_path / "secrets"
    d.mkdir()
    old = (ss.API_KEY + "=" + "sk" + "-" + "k" * 30 + chr(10)).encode()
    (d / "secrets.env").write_bytes(old)
    monkeypatch.setattr(ms.os, "replace", lambda *a, **k: (_ for _ in ()).throw(OSError("replace refused")))
    with pytest.raises(OSError):
        ms.make_secrets(tmp_path)
    assert (d / "secrets.env").read_bytes() == old
    assert not (d / "secrets.env.tmp").exists()
