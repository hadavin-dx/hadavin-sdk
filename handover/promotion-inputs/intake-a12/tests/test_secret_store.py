"""Secret store: parse rules (fail closed), every code, every length rule, hostile inputs. Values are built from parts; none is printed or echoed."""

from __future__ import annotations

import sys

import pytest

from intake import secret_store as ss
from intake.codes import SecretError

KEY = "sk" + "-" + "x" * 30
GOOD = {
    ss.API_KEY: KEY,
    ss.WEBHOOK_SECRET: "w" * 32,
    ss.APPROVER_PASSPHRASE: "p" * 24,
    ss.N8N_ENCRYPTION_KEY: "e" * 32,
    ss.N8N_PASSWORD: "o" * 24,
}


def put(tmp_path, data: bytes | str):
    d = tmp_path / "secrets"
    d.mkdir(exist_ok=True)
    (d / "secrets.env").write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return tmp_path


def body(**over) -> str:
    vals = {**GOOD, **over}
    return "".join(f"{k}={v}\n" for k, v in vals.items() if v is not None)


def code(tmp_path, name, **kw) -> str:
    try:
        ss.get(name, local=tmp_path)
    except SecretError as e:
        assert not any(v in str(e) for v in GOOD.values()), "an error message echoed a value"
        return e.code
    return "ok"


def test_all_good(tmp_path):
    put(tmp_path, body())
    assert {n: code(tmp_path, n) for n in ss.NAMES} == dict.fromkeys(ss.NAMES, "ok")
    assert ss.get(ss.API_KEY, local=tmp_path) == KEY


def test_file_missing(tmp_path):
    assert code(tmp_path, ss.API_KEY) == "key_file_missing"


def test_name_missing(tmp_path):
    put(tmp_path, body(**{ss.N8N_PASSWORD: None}))
    assert code(tmp_path, ss.N8N_PASSWORD) == "key_name_missing"
    assert code(tmp_path, "NOT_A_NAME") == "key_name_missing"


def test_empty(tmp_path):
    put(tmp_path, body(**{ss.WEBHOOK_SECRET: ""}))
    assert code(tmp_path, ss.WEBHOOK_SECRET) == "key_empty"


@pytest.mark.parametrize(
    "bad", ['"' + "w" * 40 + '"', "'" + "w" * 40, "w" * 20 + " " + "w" * 20, "w" * 40 + "\t", "w" * 20 + chr(0xA0) + "w" * 20]
)
def test_malformed_values(tmp_path, bad):
    put(tmp_path, body(**{ss.WEBHOOK_SECRET: bad}))
    assert code(tmp_path, ss.WEBHOOK_SECRET) == "key_malformed"


def test_duplicate(tmp_path):
    put(tmp_path, body() + f"{ss.WEBHOOK_SECRET}={'z' * 40}\n")
    assert code(tmp_path, ss.WEBHOOK_SECRET) == "key_duplicate"
    assert code(tmp_path, ss.API_KEY) == "ok"  # other names are unaffected


@pytest.mark.parametrize("raw", [b"\xff\xfe\x00bad", b"\x80" + b"A=1\n", b"ANTHROPIC_API_KEY=\xc3\x28\n"])
def test_encoding(tmp_path, raw):
    put(tmp_path, raw)
    assert code(tmp_path, ss.API_KEY) == "key_encoding"


@pytest.mark.parametrize(
    "name,min_len", [(ss.WEBHOOK_SECRET, 32), (ss.APPROVER_PASSPHRASE, 24), (ss.N8N_ENCRYPTION_KEY, 32), (ss.N8N_PASSWORD, 24)]
)
def test_length_rules(tmp_path, name, min_len):
    put(tmp_path, body(**{name: "a" * (min_len - 1)}))
    assert code(tmp_path, name) == "key_short"
    put(tmp_path, body(**{name: "a" * min_len}))
    assert code(tmp_path, name) == "ok"


@pytest.mark.parametrize("n,expected", [(19, "key_short"), (20, "ok"), (300, "ok"), (301, "key_malformed")])
def test_api_key_length_and_shape(tmp_path, n, expected):
    put(tmp_path, body(**{ss.API_KEY: "a" * n}))
    assert code(tmp_path, ss.API_KEY) == expected


def test_api_key_bad_characters(tmp_path):
    put(tmp_path, body(**{ss.API_KEY: "a" * 15 + "!" + "a" * 15}))
    assert code(tmp_path, ss.API_KEY) == "key_malformed"
    put(tmp_path, body(**{ss.API_KEY: "a" * 15 + "é" + "a" * 15}))
    assert code(tmp_path, ss.API_KEY) == "key_malformed"
    put(tmp_path, body(**{ss.API_KEY: "a" * 15 + "１" + "a" * 15}))  # a fullwidth digit is not an ASCII digit
    assert code(tmp_path, ss.API_KEY) == "key_malformed"


def test_missing_final_newline_bom_crlf_comments_blank(tmp_path):
    text = "# a comment\n\n" + body().rstrip("\n")
    put(tmp_path, text)  # no final newline
    assert code(tmp_path, ss.N8N_PASSWORD) == "ok"
    put(tmp_path, b"\xef\xbb\xbf" + text.encode())  # BOM
    assert code(tmp_path, ss.API_KEY) == "ok"
    put(tmp_path, text.replace("\n", "\r\n"))  # CRLF
    assert code(tmp_path, ss.API_KEY) == "ok"
    assert ss.get(ss.WEBHOOK_SECRET, local=tmp_path) == GOOD[ss.WEBHOOK_SECRET]  # no trailing CR in the value


@pytest.mark.parametrize(
    "line", ["ANTHROPIC_API_KEY = " + "a" * 30, "ANTHROPIC_API_KEY =" + "a" * 30, "no equals sign here", "=novalue", "1BAD=x", "export A=b"]
)
def test_unparseable_lines_fail_closed_for_every_name(tmp_path, line):
    put(tmp_path, body() + line + "\n")
    assert {code(tmp_path, n) for n in ss.NAMES} == {"key_malformed"}


def test_lone_cr_inside_a_value_is_malformed(tmp_path):
    put(tmp_path, body(**{ss.WEBHOOK_SECRET: "a" * 20 + "\r" + "a" * 20}))
    assert code(tmp_path, ss.WEBHOOK_SECRET) == "key_malformed"


def test_nul_and_control_characters_are_not_accepted_in_a_value(tmp_path):
    put(tmp_path, body(**{ss.WEBHOOK_SECRET: "a" * 20 + "\x00" + "a" * 20}))
    assert code(tmp_path, ss.WEBHOOK_SECRET) == "key_malformed"
    put(tmp_path, body(**{ss.WEBHOOK_SECRET: "a" * 20 + "\x0b" + "a" * 20}))
    assert code(tmp_path, ss.WEBHOOK_SECRET) == "key_malformed"
    put(tmp_path, body(**{ss.WEBHOOK_SECRET: "a" * 20 + "\x7f" + "a" * 20}))
    assert code(tmp_path, ss.WEBHOOK_SECRET) == "key_malformed"


def test_a_key_file_over_64_kb_is_refused_before_any_line_is_read(tmp_path):
    put(tmp_path, body() + "# " + "x" * (70 * 1024) + "\n")  # one huge line
    assert code(tmp_path, ss.API_KEY) == "key_malformed"
    f = tmp_path / "secrets" / "secrets.env"
    assert f.stat().st_size > ss.MAX_FILE_BYTES
    with pytest.raises(SecretError) as ei:
        ss.present_names(f)
    assert ei.value.code == "key_malformed" and "64 KB" in ei.value.text
    put(tmp_path, body() + "# " + "x" * (50 * 1024) + "\n")  # a big comment under the cap is fine
    assert code(tmp_path, ss.API_KEY) == "ok"


def test_the_environment_is_never_consulted_for_a_secret(tmp_path, monkeypatch):
    put(tmp_path, body())
    for name in ss.NAMES:
        monkeypatch.setenv(name, "e" * 40)  # a stray environment value is ignored
    assert ss.get(ss.WEBHOOK_SECRET, local=tmp_path) == GOOD[ss.WEBHOOK_SECRET]
    put(tmp_path, body(**{ss.WEBHOOK_SECRET: None}))  # absent from the file: still refused, the environment does not fill the gap
    with pytest.raises(SecretError) as ei:
        ss.get(ss.WEBHOOK_SECRET, local=tmp_path)
    assert ei.value.code == "key_name_missing"


def test_there_is_no_file_only_parameter_any_more(tmp_path):
    put(tmp_path, body())
    for kw in (True, False):
        with pytest.raises(TypeError):
            ss.get(ss.WEBHOOK_SECRET, file_only=kw, local=tmp_path)  # type: ignore[call-arg]


def test_a_single_name_read_keeps_only_that_value_in_memory(tmp_path):
    put(tmp_path, body())
    f = tmp_path / "secrets" / "secrets.env"
    got = ss._read(f, frozenset({ss.WEBHOOK_SECRET}))
    assert set(got) == set(GOOD) and got[ss.WEBHOOK_SECRET] == [GOOD[ss.WEBHOOK_SECRET]]
    assert all(v == [] for k, v in got.items() if k != ss.WEBHOOK_SECRET)  # every other value was dropped as it was read
    assert ss.present_names(f) == set(GOOD)
    assert all(v == [] for v in ss._read(f, frozenset()).values())


def test_a_malformed_line_after_the_wanted_name_still_refuses_it(tmp_path):
    put(tmp_path, body() + "junk line" + chr(10))
    assert code(tmp_path, ss.WEBHOOK_SECRET) == "key_malformed"


def test_the_model_key_registry():
    assert ss.MODEL_KEYS["anthropic"] == ss.API_KEY and ss.API_KEY in ss.MODEL_KEY_NAMES


def test_junk_line_carries_its_line_number_and_no_content(tmp_path):
    put(tmp_path, "# c\n" + body() + "oops " + "z" * 30 + "\n")
    e = ss.parse_problem(tmp_path)
    assert e is not None and e.code == "key_malformed" and e.line == 7 and "z" * 30 not in str(e)
    put(tmp_path, body())
    assert ss.parse_problem(tmp_path) is None


def test_mode_problems_flag_group_and_other_bits_on_posix_only(tmp_path, monkeypatch):
    put(tmp_path, body())
    (tmp_path / "secrets" / ss.PASSPHRASE_COPY).write_text("x")
    monkeypatch.setattr(ss.sys, "platform", "linux")
    for mode, expect in [
        (0o100600, []),
        (0o100640, ["(folder)", "secrets.env", ss.PASSPHRASE_COPY]),
        (0o100604, ["(folder)", "secrets.env", ss.PASSPHRASE_COPY]),
        (0o100700, []),
    ]:
        monkeypatch.setattr(ss, "_stat_mode", lambda p, m=mode: m)
        assert ss.mode_problems(tmp_path) == expect
    monkeypatch.setattr(ss.sys, "platform", "win32")
    assert ss.mode_problems(tmp_path) == []  # mode bits mean nothing on Windows


def test_secrets_location(tmp_path):
    from pathlib import Path

    assert ss.secrets_location(Path.home() / "x") == "under_user_profile"
    assert ss.secrets_location(Path(Path.home().anchor) / "no-such-profile-folder") == "elsewhere"


def test_status_never_returns_a_value(tmp_path):
    put(tmp_path, body())
    assert all(ss.status(n, tmp_path) == "ok" for n in ss.NAMES)
    put(tmp_path, body(**{ss.WEBHOOK_SECRET: "tiny"}))
    assert ss.status(ss.WEBHOOK_SECRET, tmp_path) == "key_short"


def test_local_unset_is_a_refusal_not_a_crash(monkeypatch):
    monkeypatch.delenv("HADAVIN_LOCAL", raising=False)
    with pytest.raises(SecretError) as ei:
        ss.get(ss.API_KEY)
    assert ei.value.code == "key_file_missing"


def test_mode_state_text_is_honest_on_windows(tmp_path, monkeypatch):
    put(tmp_path, body())
    monkeypatch.setattr(ss.sys, "platform", "win32")
    assert ss.mode_state(tmp_path) == "not_checked (windows)"  # nothing is checked there: never claim ok
    monkeypatch.setattr(ss.sys, "platform", "linux")
    monkeypatch.setattr(ss, "_stat_mode", lambda p: 0o100600 if p.is_file() else 0o040700)
    assert ss.mode_state(tmp_path) == "ok"
    monkeypatch.setattr(ss, "_stat_mode", lambda p: 0o100640)
    assert ss.mode_state(tmp_path).startswith("fail key_mode ")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_mode_problems_on_real_files(tmp_path):
    put(tmp_path, body())
    d = tmp_path / "secrets"
    d.chmod(0o700)
    (d / "secrets.env").chmod(0o600)
    assert ss.mode_problems(tmp_path) == [] and ss.mode_state(tmp_path) == "ok"
    (d / "secrets.env").chmod(0o640)
    assert ss.mode_problems(tmp_path) == ["secrets.env"]
    (d / "secrets.env").chmod(0o600)
    d.chmod(0o750)
    assert ss.mode_problems(tmp_path) == ["(folder)"]


def test_relative_local_is_rejected(monkeypatch):
    with pytest.raises(SecretError) as ei:
        ss.secrets_path("relative/folder")
    assert ei.value.code == "key_file_missing"


def test_inside_repo_and_lock_state(tmp_path):
    assert ss.inside_repo(ss.REPO_ROOT / "secrets_here") is True
    assert ss.inside_repo(tmp_path) is False
    put(tmp_path, body())
    assert ss.lock_state(tmp_path) == "absent"
    (tmp_path / "secrets" / ss.LOCK_FILE).write_text("x")
    assert ss.lock_state(tmp_path) == "present"
