"""D-config hardening, round 4 (the third hostile review): a path-shaped secret name is refused only where it can
alias a file (senders exist, or the mounted_file kind), a path-shaped reset or release ref gets its own message,
the Windows separator counts, and file systems that fold names are covered. Each test was written before its fix
and failed on the code at the start of the round."""

from __future__ import annotations

from datetime import date

import pytest

from hadavin_sdk import app as app_mod
from hadavin_sdk import cli
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.actions.secrets_file import MountedFileProvider
from hadavin_sdk.backends import platform_secrets
from hadavin_sdk.config import ConfigError, load_config
from hadavin_sdk.registry import load_registry
from hadavin_sdk.secret_name import collides, has_dot_segment
from tests.conftest import make_cfg, qualify
from tests.test_stop_state_unit import _postgres

AWS_STYLE = "/hadavin/prod/dsn"


class Provider:
    def __init__(self):
        self.calls: list = []

    def get(self, name):
        self.calls.append(name)
        return "v" * 40


# --- M1 (a): nothing to compare, nothing to refuse -------------------------------------------------------------------


def test_collides_with_no_names_is_false_even_for_a_path_shaped_ref():
    assert not collides(AWS_STYLE, [])
    assert not collides("a/../x", [])


def test_collides_does_not_fail_closed_for_a_plain_provider():
    assert not collides(AWS_STYLE, ["unrelated"])
    assert not collides("unrelated", [AWS_STYLE])
    assert collides(AWS_STYLE, ["hadavin-prod-dsn"])  # still folded and compared


def test_collides_fails_closed_for_a_file_backed_provider_when_there_is_something_to_compare():
    assert collides("/x", ["unrelated"], file_backed=True)
    assert collides("unrelated", ["a/../x"], file_backed=True)
    assert not collides("/x", [], file_backed=True)


# --- M1 (b): the refusal belongs to senders -------------------------------------------------------------------------


def test_check_senders_with_no_senders_accepts_an_aws_style_name_elsewhere():
    provider = Provider()
    platform_secrets.check_senders(provider, {}, {AWS_STYLE, "x/"})
    platform_secrets.check_senders(provider, {"s": []}, {AWS_STYLE})
    assert provider.calls == []


def test_check_senders_accepts_a_leading_or_trailing_slash_for_a_plain_provider():
    platform_secrets.check_senders(Provider(), {"s": ["slack_token"]}, {AWS_STYLE, "team/x/"})


@pytest.mark.parametrize("other", ["/slack_token", "slack_token/", "/hadavin/prod/dsn"])
def test_check_senders_refuses_a_leading_or_trailing_slash_for_a_file_backed_provider(other):
    provider = Provider()
    with pytest.raises(ConfigError):
        platform_secrets.check_senders(provider, {"s": ["slack_token"]}, {other}, file_backed=True)
    assert provider.calls == []


def test_a_mounted_file_provider_says_it_is_file_backed(tmp_path):
    assert MountedFileProvider(tmp_path).file_backed is True
    with pytest.raises(ConfigError):
        platform_secrets.check_senders(
            MountedFileProvider(tmp_path), {"s": ["slack_token"]}, {"/slack_token"}
        )


@pytest.mark.parametrize("other", ["a/../slack_token", "./slack_token"])
def test_a_dot_segment_other_name_is_refused_for_every_provider(other):
    with pytest.raises(ConfigError):
        platform_secrets.check_senders(Provider(), {"s": ["slack_token"]}, {other})


@pytest.mark.parametrize("name", ["a/../x", "./x", "x/.."])
def test_a_dot_segment_sender_name_is_always_refused(name):
    provider = Provider()
    with pytest.raises(ConfigError):
        platform_secrets.check_senders(provider, {"s": [name]}, set())
    assert provider.calls == []


# --- M1 (c): a path-shaped reset or release ref gets its own message -----------------------------------------------


def _build(cfg_dir):
    qualify(load_registry(load_config(cfg_dir)))
    return app_mod.build(cfg_dir, ["test-agent"], secrets=Provider())


def _with_ref(monkeypatch, cfg_dir, ref, field="reset_credential_ref"):
    monkeypatch.setattr(type(load_config(cfg_dir).backends.store), field, ref, raising=False)


@pytest.mark.parametrize("field", ["reset_credential_ref", "release_credential_ref"])
def test_an_aws_style_ref_starts_when_nothing_else_collides(tmp_path, monkeypatch, field):
    cfg = make_cfg(tmp_path)
    _with_ref(monkeypatch, cfg, AWS_STYLE, field)
    assert _build(cfg) is not None


@pytest.mark.parametrize("field", ["reset_credential_ref", "release_credential_ref"])
def test_a_dot_segment_ref_gets_a_path_form_message_not_the_collision_text(
    tmp_path, monkeypatch, field
):
    cfg = make_cfg(tmp_path)
    _with_ref(monkeypatch, cfg, "a/../x", field)
    with pytest.raises(ConfigError) as caught:
        _build(cfg)
    text = str(caught.value)
    assert field in text and "path-shaped" in text
    assert "also reads" not in text and "a/../x" not in text


def test_the_reset_command_gives_the_path_form_message(tmp_path, monkeypatch, capsys):
    cfg = _postgres(make_cfg(tmp_path), "a/../x")
    monkeypatch.setattr(cli, "make", lambda *a, **k: pytest.fail("connected"))
    code = cli.main(["--config", str(cfg), "limits", "reset", "--by", "user:op"])
    err = capsys.readouterr().err
    assert code == 2 and "path-shaped" in err and "names the same secret" not in err


def test_the_release_command_gives_the_path_form_message(tmp_path, monkeypatch, capsys):
    cfg = load_config(_postgres(make_cfg(tmp_path)))
    store = cfg.backends.store.model_copy(update={"release_credential_ref": "/x/../rel"})
    cfg = cfg.model_copy(update={"backends": cfg.backends.model_copy(update={"store": store})})
    monkeypatch.setattr(cli, "make", lambda *a, **k: pytest.fail("connected"))
    assert cli.release_expired_cmd(cfg, "a", date(2025, 1, 31), "u") == 2
    err = capsys.readouterr().err
    assert "path-shaped" in err and "names the same secret" not in err


def test_the_reset_command_accepts_an_aws_style_ref_up_to_the_collision_check(
    tmp_path, monkeypatch, capsys
):
    cfg = _postgres(make_cfg(tmp_path), AWS_STYLE)
    monkeypatch.setattr(
        cli,
        "make",
        lambda cap, *a, **k: FakeSecretProvider(
            {"pg-dsn": "postgresql://a/db", AWS_STYLE: "postgresql://a/db"}
        ),
    )
    cli.main(["--config", str(cfg), "limits", "reset", "--by", "user:op"])
    err = capsys.readouterr().err
    assert "path-shaped" not in err and "names the same secret" not in err


# --- L1: the Windows separator ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["a\\..\\x", "..\\x", "a/..\\x", "x\\.."])
def test_the_dot_segment_rule_splits_on_the_backslash_too(name):
    assert has_dot_segment(name)
    assert collides(name, ["unrelated"], file_backed=True)
    with pytest.raises(ConfigError):
        platform_secrets.check_senders(Provider(), {"s": ["x"]}, {name})


def test_a_backslash_in_a_plain_name_is_not_a_dot_segment():
    assert not has_dot_segment("a\\b.c")


# --- L2: file systems that fold names -----------------------------------------------------------------------------

KELVIN = "\u212alack_token"  # NFKC: "Klack_token"
LONG_S = "\u017flack_token"  # folds to "slack_token"
SENDER_OF = {KELVIN: "klack_token", LONG_S: "slack_token"}


@pytest.mark.parametrize("fold", [KELVIN, LONG_S])
def test_a_folding_file_system_name_collides_with_the_sender_for_mounted_file(fold):
    sender = SENDER_OF[fold]
    assert collides(fold, [sender], file_backed=True)
    with pytest.raises(ConfigError):
        platform_secrets.check_senders(Provider(), {"s": [sender]}, {fold}, file_backed=True)


def test_the_env_provider_fold_is_unchanged():
    assert not collides(
        LONG_S, ["slack_token"]
    )  # the env kind turns each into one "_": a different variable
