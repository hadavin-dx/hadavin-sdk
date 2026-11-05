"""Hidden warnings, first lot (owner, 2026-10-17): every blind `except Exception` either names what the call really
raises, or stays broad with its reason on the line - and then leaves a record of what it caught, never swallows it.

These pin the narrowed catches (a malformed request is still answered, never a crash) and the records the kept ones
now write."""

from __future__ import annotations

import base64
import json
import logging

import pytest

from test_bench_approver import _page, _plan
from test_killswitch_reset_g10m import World
from test_killswitch_stop_page import _off
from test_platform_db import _Conn, _platform
from test_revert_config_history_g10d3 import ECS, Fake, _p
from warden import bounds, environments, slack_login
from warden.approval_page import STOP_INVITE, ApprovalPage


def test_a_signed_approval_of_the_wrong_shape_is_refused_whole(tmp_path):
    page, _, _, sent = _page(tmp_path, _plan())
    for body in ({"approver": "bench"}, {"approver": "bench", "workflow_id": ["not", "a", "string"]}):
        got = page.handle("POST", "/a/signed/approve", json.dumps(body))
        assert got.status == 400
        assert json.loads(got.body) == {"error": "not a signed approval"}
    assert not sent


@pytest.mark.parametrize("body", ["not json", "[1, 2]", '"a string"', "\xff"])
def test_a_stop_request_that_is_not_an_object_stops_nothing_and_never_crashes(tmp_path, body):
    w = World(tmp_path)
    token = w.link(STOP_INVITE)
    assert w.page.handle("POST", f"/x/{token}/options", body).status == 400


@pytest.mark.parametrize("body", ["not json", "[1, 2]", json.dumps({"reason": "stop now"}),
                                  json.dumps({"reason": "stop now", "response": "not an assertion"})])
def test_a_stop_answer_that_cannot_be_read_stops_nothing(tmp_path, body):
    w = World(tmp_path)
    _off(w)
    token = w.link(STOP_INVITE)
    assert w.page.handle("POST", f"/x/{token}/options", json.dumps({"reason": "stop now"})).status == 200
    assert w.page.handle("POST", f"/x/{token}/on", body).status in (400, 403)
    assert bounds.killswitch(w.log) is None


def test_the_filter_offers_only_any_when_the_environment_policy_cannot_be_read(monkeypatch):
    def broken():
        raise environments.EnvironmentPolicyError("environment policy is not valid YAML")

    monkeypatch.setattr(environments, "default_environment_policies", broken)
    assert ApprovalPage._environment_choices(None) == ()
    assert ApprovalPage._environment_choices({"dev"}) == ("dev",)


def _token(claims) -> str:
    part = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return f"header.{part}.signature"


@pytest.mark.parametrize("claims", [["a", "list"], "a string", 7, None])
def test_a_slack_answer_whose_claims_are_not_an_object_is_unreadable_never_a_crash(claims):
    login = slack_login.SlackLogin("client", "s3cret-not-real",
                                   post=lambda url, form: {"ok": True, "id_token": _token(claims)})
    with pytest.raises(slack_login.SlackLoginError, match="could not be read"):
        login.member("c", redirect_uri="r", nonce="n")


@pytest.mark.parametrize("token", ["header.!!!.signature", "header.bm90IGpzb24.signature", "header./w.signature"])
def test_a_slack_token_whose_payload_is_not_base64_utf8_json_is_unreadable(token):
    login = slack_login.SlackLogin("client", "s3cret-not-real", post=lambda url, form: {"ok": True, "id_token": token})
    with pytest.raises(slack_login.SlackLoginError, match="could not be read"):
        login.member("c", redirect_uri="r", nonce="n")


@pytest.mark.parametrize("error", [TimeoutError("no route"), ValueError("not json"), OSError("reset")])
def test_slack_unreachable_or_unreadable_is_a_sign_in_that_did_not_happen(error):
    def post(url, form):
        raise error

    login = slack_login.SlackLogin("client", "s3cret-not-real", post=post)
    with pytest.raises(slack_login.SlackLoginError, match=f"could not be reached \\({type(error).__name__}\\)"):
        login.member("c", redirect_uri="r", nonce="n")


def test_a_failed_aws_health_check_is_not_healthy_and_says_why(caplog):
    class Broken(Fake):
        def describe_services(self, *a, **kw):
            raise RuntimeError("throttled")

    with caplog.at_level(logging.WARNING, logger="warden.platforms"):
        assert _p(Broken()).healthy("warden-dev-orders", "ecs_rollback_service", ECS) is False
    assert "the health check for ecs_rollback_service failed (RuntimeError): not healthy" in caplog.text


def test_a_failed_aws_live_read_allows_nothing_and_says_why(caplog):
    f = Fake()

    def boom(*a, **kw):
        raise KeyError("Services")

    f.describe_services = boom
    with caplog.at_level(logging.WARNING, logger="warden.platforms"):
        assert _p(f).live("ecs_restore_desired", ECS) == {}
    assert "the live read for ecs_restore_desired failed (KeyError): nothing is allowed" in caplog.text


def test_an_unreadable_database_is_not_healthy_allows_nothing_and_says_why(caplog):
    with caplog.at_level(logging.WARNING, logger="warden.platforms"):
        assert _platform(conn=_Conn(fail=True)).live("db_terminate_idle_in_tx", {}) == {}
        assert _platform(conn=_Conn(fail=True)).healthy("orders") is False
    assert "the database could not be read" in caplog.text


_DEEP = "[" * 100_000 + "]" * 100_000  # json.loads raises RecursionError past its nesting depth


@pytest.mark.parametrize("body", ["[1, 2]", '"a string"', "7", "null", _DEEP])
def test_a_signed_request_that_is_not_a_json_object_is_refused_never_a_crash(tmp_path, body):
    page, _, _, sent = _page(tmp_path, _plan())
    for step in ("approve", "plan"):
        assert page.handle("POST", f"/a/signed/{step}", body).status == 400
    assert not sent


def test_a_stop_request_nested_too_deep_stops_nothing(tmp_path):
    w = World(tmp_path)
    _off(w)
    token = w.link(STOP_INVITE)
    assert w.page.handle("POST", f"/x/{token}/options", _DEEP).status == 400
    assert w.page.handle("POST", f"/x/{token}/options", json.dumps({"reason": "stop now"})).status == 200
    assert w.page.handle("POST", f"/x/{token}/on", _DEEP).status in (400, 403)
    assert bounds.killswitch(w.log) is None


@pytest.mark.parametrize("listed", ["[dev, prod]", "dev", "[]"])
def test_an_environment_list_that_is_not_a_mapping_is_a_policy_error(tmp_path, listed):
    path = tmp_path / "env.yaml"
    path.write_text(f"version: 1\ndefault: {{}}\nenvironments: {listed}\n", encoding="utf-8")
    with pytest.raises(environments.EnvironmentPolicyError):
        environments.EnvironmentPolicies.load(path)


def test_slack_answers_nested_too_deep_are_a_sign_in_that_did_not_happen():
    deep = slack_login.SlackLogin("client", "s3cret-not-real",
                                  post=lambda url, form: {"ok": True, "id_token": _token(json.loads("[" * 50 + "]" * 50))})
    with pytest.raises(slack_login.SlackLoginError, match="could not be read"):
        deep.member("c", redirect_uri="r", nonce="n")
    token = f"header.{base64.urlsafe_b64encode(_DEEP.encode()).decode()}.signature"
    payload = slack_login.SlackLogin("client", "s3cret-not-real", post=lambda url, form: {"ok": True, "id_token": token})
    with pytest.raises(slack_login.SlackLoginError, match="could not be read"):
        payload.member("c", redirect_uri="r", nonce="n")

    def nested(url, form):
        raise RecursionError("maximum recursion depth exceeded while decoding a JSON array")

    unreadable = slack_login.SlackLogin("client", "s3cret-not-real", post=nested)
    with pytest.raises(slack_login.SlackLoginError, match="could not be reached \\(RecursionError\\)"):
        unreadable.member("c", redirect_uri="r", nonce="n")


def test_a_service_name_with_a_newline_is_logged_on_one_line(caplog):
    from warden.platforms.k8s import KubernetesPlatform

    platform = KubernetesPlatform.__new__(KubernetesPlatform)

    def unreadable(service):
        raise RuntimeError("gone")

    platform._read = unreadable
    with caplog.at_level(logging.DEBUG, logger="warden.platforms"):
        assert platform.healthy("orders\n2026-10-27 INFO warden: approved") is False
        assert platform.knows("orders\nforged") is False
    assert [r.getMessage() for r in caplog.records] == [
        "deployment orders could not be read (RuntimeError): not healthy",
        "deployment orders not read (RuntimeError): not this platform's"]


@pytest.mark.parametrize("faults", ["[[]]", "[{a: 1}]", "[[dev]]"])
def test_a_fault_environment_that_is_not_a_name_is_a_policy_error(tmp_path, faults):
    path = tmp_path / "env.yaml"
    path.write_text(f"version: 1\ndefault: {{}}\nenvironments: {{dev: {{tier: nonprod}}}}\nfault_environments: {faults}\n",
                    encoding="utf-8")
    with pytest.raises(environments.EnvironmentPolicyError, match="fault_environments"):
        environments.EnvironmentPolicies.load(path)


def test_an_environment_policy_nested_too_deep_is_a_policy_error_and_the_records_list_still_offers_choices(tmp_path,
                                                                                                         monkeypatch):
    path = tmp_path / "env.yaml"
    path.write_text("version: 1\ndefault: {}\nenvironments: " + "[" * 5000 + "]" * 5000 + "\n", encoding="utf-8")
    with pytest.raises(environments.EnvironmentPolicyError, match="nested too deeply"):
        environments.EnvironmentPolicies.load(path)
    monkeypatch.setenv("WARDEN_ENV_POLICY_PATH", str(path))
    monkeypatch.setattr(environments, "_DEFAULT", None)  # read afresh, from the file above
    from warden.approval_page import ApprovalPage

    assert ApprovalPage._environment_choices(None) == ()  # the records list's fallback, never a RecursionError
