"""Guard "a real engine refuses" for the two Vault kinds (ticket Q8c, PR 1; owner rule least privilege).

The policy text generated from a kind's `POLICY` literal is given to a REAL Vault server, a token is created that
holds only that policy, and the kind's own code runs with that token:

  B1 the allowed requests work;
  B2 with one grant removed, the request that grant serves is refused, seen in the kind's own error;
  B3 the requests on the never-list are refused (403);
  B4 control: the same requests with the admin token get any status other than 403, so each refusal is the
     policy's doing and not a broken request.
Two plants must make the refusal check fail: a policy widened to the whole mount, and the admin token used in
place of the runtime token.

These tests need a real server: they run when HADAVIN_TEST_VAULT_ADDR is set (the CI service container). The
local fake (tests/contracts/vault_fake.py) enforces no policy, so on a machine without a server they are
SKIPPED with a visible reason; CI sets HADAVIN_REQUIRE_VAULT_ENGINE=1, which turns that skip into a failure.

What this does not show: a server that denies by default shows that the generated text grants no more than
intended; it is not proof that the never-list is complete. OpenBao is not run. The token is created directly
(`no_default_policy`, source id V-TOK in tests/fixtures/policy_sources_2026-11-11.txt); sign-in through an
AppRole or Kubernetes role is not exercised.
"""

from __future__ import annotations

import base64
import dataclasses
import os
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest
import yaml
from tools import policy_page as pp

from hadavin_sdk.actions.secrets_vault import VaultError, VaultProvider
from hadavin_sdk.audit.signer import probe
from hadavin_sdk.audit.signer_vault import VaultTransitSigner
from tests.contracts.kinds.audit_neutral import transit_key
from tests.contracts.kinds.secrets_neutral import vault_target

ROOT_DIR = Path(__file__).resolve().parents[1]
ADDR_VAR, REQUIRE_VAR = "HADAVIN_TEST_VAULT_ADDR", "HADAVIN_REQUIRE_VAULT_ENGINE"
SKIP_REASON = (
    f"needs a real Vault server ({ADDR_VAR} is not set): the local fake enforces no policy, so a refusal "
    "there would show nothing. CI runs these against its Vault service and requires them."
)
LIFETIME = "15m"  # how long the throwaway runtime token lives
NOTHING = (
    'path "q8c-no-such-path" {\n  capabilities = ["deny"]\n}\n'  # a policy with every grant removed
)
Request = tuple[str, str, str, dict | None]  # (what it is in plain words, method, path, body)


def engine_mode(env: Mapping[str, str]) -> tuple[str, str]:
    """("run" | "skip" | "fail", reason) for these tests in the given environment."""
    if env.get(ADDR_VAR):
        return "run", ""
    if env.get(REQUIRE_VAR) == "1":
        return (
            "fail",
            f"{REQUIRE_VAR}=1 but {ADDR_VAR} is not set: the Vault engine tests must run here",
        )
    return "skip", SKIP_REASON


def test_the_engine_tests_run_skip_or_fail_by_the_environment():
    assert engine_mode({ADDR_VAR: "http://127.0.0.1:8200", REQUIRE_VAR: "1"}) == ("run", "")
    assert engine_mode({ADDR_VAR: "http://127.0.0.1:8200"}) == ("run", "")
    assert engine_mode({}) == ("skip", SKIP_REASON)
    assert engine_mode({REQUIRE_VAR: "0"})[0] == "skip"
    mode, reason = engine_mode({REQUIRE_VAR: "1"})
    assert mode == "fail" and "must run here" in reason
    assert engine_mode({REQUIRE_VAR: "1", ADDR_VAR: ""})[0] == "fail"


def test_ci_requires_the_engine_tests_in_both_jobs_that_have_a_vault_service():
    """The workflow sets the variable exactly where a Vault service container and its address are set."""
    jobs = yaml.safe_load((ROOT_DIR / ".github/workflows/ci.yml").read_text(encoding="utf-8"))[
        "jobs"
    ]
    with_vault = sorted(j for j, job in jobs.items() if "vault" in (job.get("services") or {}))
    assert with_vault == ["check", "tests-py312"]
    for name in with_vault:
        envs = [s.get("env") or {} for s in jobs[name]["steps"] if ADDR_VAR in (s.get("env") or {})]
        assert len(envs) == 1, name
        assert envs[0].get(REQUIRE_VAR) == "1", (
            f"job {name}: {REQUIRE_VAR} is not set beside {ADDR_VAR}"
        )
    others = [j for j, job in jobs.items() if j not in with_vault and REQUIRE_VAR in str(job)]
    assert others == []


@dataclasses.dataclass(frozen=True)
class Engine:
    """The admin side (set-up, controls) and a way to make a runtime token that holds one policy only."""

    address: str
    admin_token: str

    def client(self, token: str, **kw) -> VaultProvider:
        return VaultProvider(self.address, lambda p: token, ttl_s=0, renewable=False, **kw)

    def admin(self) -> VaultProvider:
        return self.client(self.admin_token)

    def runtime_token(self, policy_text: str) -> str:
        """Write `policy_text` as a new policy; return a short-lived token that holds ONLY that policy (a
        token gets Vault's `default` policy too unless `no_default_policy` is set)."""
        name = f"q8c-{uuid.uuid4().hex[:12]}"
        admin = self.admin()
        status, _ = admin.authed("PUT", f"sys/policies/acl/{name}", {"policy": policy_text})
        assert status in (200, 204), f"writing the policy answered {status}"
        body = {"policies": [name], "no_default_policy": True, "ttl": LIFETIME, "renewable": False}
        status, answer = admin.authed("POST", "auth/token/create", body)
        assert status == 200, f"creating the runtime token answered {status}"
        auth = answer["auth"]
        assert auth["policies"] == [name], auth["policies"]  # nothing else, not even `default`
        return auth["client_token"]


@pytest.fixture
def engine() -> Engine:
    mode, reason = engine_mode(os.environ)
    if mode == "fail":
        pytest.fail(reason)
    if mode == "skip":
        pytest.skip(reason)
    return Engine(*vault_target())


def policy_of(kind: str) -> pp.Policy:
    policy = pp.load(ROOT_DIR / pp.KIND_MODULES[kind])
    assert policy is not None, f"no POLICY in {pp.KIND_MODULES[kind]}"
    return policy


def text_without(policy: pp.Policy, grant_id: str, values: dict[str, str]) -> str:
    """The policy text with one grant removed (a policy that grants nothing when it was the only one)."""
    assert grant_id in {g.id for g in policy.grants}
    kept = tuple(g for g in policy.grants if g.id != grant_id)
    if not kept:
        return NOTHING
    used = {name for g in kept for name in pp._FIELD.findall(g.resource)}
    return pp.render_vault(
        dataclasses.replace(policy, grants=kept), {k: v for k, v in values.items() if k in used}
    )


def refused(engine: Engine, token: str, requests: list[Request]) -> None:
    """Every request, sent with `token`, must be refused by the server (403)."""
    client = engine.client(token)
    for what, method, path, body in requests:
        status, _ = client.call(method, path, body, token=token)
        assert status == 403, f"{what}: {method} {path} answered {status}, expected 403 (refused)"


def not_refused_for_admin(engine: Engine, requests: list[Request]) -> None:
    """Control: the same requests with the admin token get any status other than 403."""
    admin = engine.admin()
    for what, method, path, body in requests:
        status, _ = admin.call(method, path, body, token=engine.admin_token)
        assert status != 403, (
            f"control, {what}: {method} {path} is refused even for the admin token"
        )


# ------------------------------------------------------------------------------------ vault (secrets): R17


@dataclasses.dataclass(frozen=True)
class SecretsCase:
    engine: Engine
    policy: pp.Policy
    values: dict[str, str]
    prefix: str
    other: str  # a second prefix in the same mount that the policy does not cover

    def provider(self, token: str, prefix: str) -> VaultProvider:
        return self.engine.client(token, mount=self.values["mount"], path_prefix=prefix)

    def never_requests(self) -> list[Request]:
        mount, here = self.values["mount"], self.prefix
        return [
            ("read outside the prefix", "GET", f"{mount}/data/{self.other}alpha", None),
            (
                "write under the prefix",
                "POST",
                f"{mount}/data/{here}alpha",
                {"data": {"value": "x"}},
            ),
            ("delete under the prefix", "DELETE", f"{mount}/data/{here}alpha", None),
            ("read the metadata path", "GET", f"{mount}/metadata/{here}alpha", None),
            ("destroy a version", "PUT", f"{mount}/destroy/{here}alpha", {"versions": [1]}),
            ("read the server's mounts", "GET", "sys/mounts", None),
        ]


@pytest.fixture
def secrets_case(engine: Engine) -> SecretsCase:
    prefix, other = f"q{uuid.uuid4().hex[:12]}/", f"o{uuid.uuid4().hex[:12]}/"
    admin = engine.admin()
    for p in (prefix, other):
        status, _ = admin.authed("POST", f"secret/data/{p}alpha", {"data": {"value": "v-" + p}})
        assert status in (200, 204), status
    values = {"mount": "secret", "path_prefix": prefix}
    return SecretsCase(engine, policy_of("secrets/vault"), values, prefix, other)


def test_vault_secrets_the_allowed_read_works_with_only_the_generated_policy(secrets_case):
    case = secrets_case
    token = case.engine.runtime_token(pp.render_vault(case.policy, case.values))
    assert case.provider(token, case.prefix).get("alpha") == "v-" + case.prefix


def test_vault_secrets_the_read_is_refused_when_its_grant_is_removed(secrets_case):
    case = secrets_case
    assert [g.id for g in case.policy.grants] == ["R17"]  # a new grant needs its own removal test
    token = case.engine.runtime_token(text_without(case.policy, "R17", case.values))
    with pytest.raises(VaultError, match="secret 'alpha': Vault answered 403"):
        case.provider(token, case.prefix).get("alpha")


def test_vault_secrets_the_never_list_requests_are_refused_and_the_admin_control_is_not(
    secrets_case,
):
    case = secrets_case
    token = case.engine.runtime_token(pp.render_vault(case.policy, case.values))
    with pytest.raises(VaultError, match="secret 'alpha': Vault answered 403"):
        case.provider(token, case.other).get("alpha")  # the kind's own code, outside the prefix
    refused(case.engine, token, case.never_requests())
    assert (
        case.provider(token, case.prefix).get("alpha") == "v-" + case.prefix
    )  # the token is valid
    not_refused_for_admin(case.engine, case.never_requests())


def test_plant_a_vault_policy_widened_to_the_whole_mount_fails_the_refusal_check(secrets_case):
    case = secrets_case
    text = pp.render_vault(case.policy, case.values)
    widened = text.replace(f'"secret/data/{case.prefix}*"', '"secret/data/*"')
    assert widened != text
    token = case.engine.runtime_token(widened)
    with pytest.raises(
        AssertionError, match="read outside the prefix: .* answered 200, expected 403"
    ):
        refused(case.engine, token, case.never_requests())


def test_plant_the_admin_token_in_place_of_the_runtime_token_fails_the_refusal_check(secrets_case):
    case = secrets_case
    with pytest.raises(AssertionError, match="expected 403"):
        refused(case.engine, case.engine.admin_token, case.never_requests())


# ----------------------------------------------------------------------- vault_transit (signer): R18, R19


@dataclasses.dataclass(frozen=True)
class TransitCase:
    engine: Engine
    policy: pp.Policy
    values: dict[str, str]
    key: str
    spare: (
        str  # a second, throwaway key: exportable and deletable, used only by refusals and controls
    )

    def signer(self, token: str) -> VaultTransitSigner:
        return VaultTransitSigner(
            self.engine.client(token), self.values["transit_mount"], self.key, 1
        )

    def never_requests(self, key: str) -> list[Request]:
        mount = self.values["transit_mount"]
        message = {"input": base64.b64encode(b"q8c").decode()}
        return [
            ("sign with another key", "POST", f"{mount}/sign/{self.spare}", message),
            (
                "change the key's settings",
                "POST",
                f"{mount}/keys/{key}/config",
                {"deletion_allowed": True},
            ),
            ("export the key", "GET", f"{mount}/export/signing-key/{key}", None),
            ("back the key up", "GET", f"{mount}/backup/{key}", None),
            ("read the server's mounts", "GET", "sys/mounts", None),
            ("delete the key", "DELETE", f"{mount}/keys/{key}", None),
        ]


@pytest.fixture
def transit_case(engine: Engine) -> TransitCase:
    _, key = transit_key()  # admin side: enables the Transit engine and makes a fresh ed25519 key
    spare = f"spare-{uuid.uuid4().hex[:10]}"
    admin = engine.admin()
    body = {"type": "ed25519", "exportable": True, "allow_plaintext_backup": True}
    status, _ = admin.authed("POST", f"transit/keys/{spare}", body)
    assert status in (200, 204), status
    status, _ = admin.authed("POST", f"transit/keys/{spare}/config", {"deletion_allowed": True})
    assert status in (200, 204), status
    values = {"transit_mount": "transit", "key_name": key}
    return TransitCase(engine, policy_of("signer/vault_transit"), values, key, spare)


def test_vault_transit_signing_and_the_public_key_work_with_only_the_generated_policy(transit_case):
    case = transit_case
    token = case.engine.runtime_token(pp.render_vault(case.policy, case.values))
    probe(case.signer(token), "signer vault_transit")  # start-up: sign, read the public key, verify


# grant id -> (the request of the kind's own code that the grant serves, the kind's own error for a refusal)
TRANSIT_NEEDS: dict[str, tuple[Callable[[VaultTransitSigner], object], str]] = {
    "R18": (lambda signer: signer.sign(b"q8c"), "transit sign .*: Vault answered 403"),
    "R19": (lambda signer: signer.public_key(), "transit keys .*: Vault answered 403"),
}


@pytest.mark.parametrize("grant_id", sorted(TRANSIT_NEEDS))
def test_vault_transit_a_request_is_refused_when_its_grant_is_removed(transit_case, grant_id):
    case = transit_case
    assert set(TRANSIT_NEEDS) == {
        g.id for g in case.policy.grants
    }  # a stale or missing entry fails
    token = case.engine.runtime_token(text_without(case.policy, grant_id, case.values))
    signer = case.signer(token)
    for other in sorted(set(TRANSIT_NEEDS) - {grant_id}):
        TRANSIT_NEEDS[other][0](signer)  # the grant that was kept still works: the token is valid
    request, error = TRANSIT_NEEDS[grant_id]
    with pytest.raises(VaultError, match=error):
        request(signer)


def test_vault_transit_the_never_list_requests_are_refused_and_the_admin_control_is_not(
    transit_case,
):
    case = transit_case
    token = case.engine.runtime_token(pp.render_vault(case.policy, case.values))
    refused(case.engine, token, case.never_requests(case.key))  # on the signing key itself
    probe(
        case.signer(token), "signer vault_transit"
    )  # the token is valid and the key is still there
    not_refused_for_admin(case.engine, case.never_requests(case.spare))  # on the throwaway key


def test_plant_a_transit_policy_widened_to_every_key_fails_the_refusal_check(transit_case):
    case = transit_case
    text = pp.render_vault(case.policy, case.values)
    widened = text.replace(f'"transit/sign/{case.key}"', '"transit/sign/*"')
    assert widened != text
    token = case.engine.runtime_token(widened)
    with pytest.raises(
        AssertionError, match="sign with another key: .* answered 200, expected 403"
    ):
        refused(case.engine, token, case.never_requests(case.key))


def test_plant_the_admin_token_in_place_of_the_transit_runtime_token_fails_the_refusal_check(
    transit_case,
):
    case = transit_case
    with pytest.raises(AssertionError, match="expected 403"):
        refused(case.engine, case.engine.admin_token, case.never_requests(case.spare))
