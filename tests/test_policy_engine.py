"""Guard "a real engine refuses" for the two Vault kinds (ticket Q8c, PR 1; owner rule least privilege).

The policy text generated from a kind's `POLICY` literal is given to a REAL Vault server, a token is created that
holds only that policy, and the kind's own code runs with that token:

  B1 the allowed requests work;
  B2 with one grant removed, the request that grant serves is refused, seen in the kind's own error;
  B3 the requests on the never-list are refused (403);
  B4 control: the same requests with the admin token are answered 200 or 204, so each refusal is the policy's
     doing and not a mistyped path or a broken request.
Plants that must make the refusal check fail: a policy widened to the whole mount, a policy with the old
"everything below the prefix" form, and the admin token used in place of the runtime token.

NOT RUN YET: no machine that built this file had a Vault server. Until a CI run shows these tests as passed
(not skipped), nothing here is evidence; `ENGINE_RUN` in tools/policy_page.py is None and the page says so.
The status codes expected from the admin controls were written from the vendor documentation, not seen.

These tests need a real server: they run when HADAVIN_TEST_VAULT_ADDR is set (the CI service container). The
local fake (tests/contracts/vault_fake.py) enforces no policy, so on a machine without a server they are
SKIPPED with a visible reason; CI sets HADAVIN_REQUIRE_VAULT_ENGINE=1, which turns that skip into a failure.

What this does not show: a server that denies by default shows that the generated text grants no more than
intended; it is not proof that the never-list is complete. OpenBao is not run. The token is created directly
(`no_default_policy`, source id V-TOK in tests/fixtures/policy_sources_2026-11-11.txt); sign-in through an
AppRole or Kubernetes role is not exercised.

Clean-up: each test removes what it made (the policies, the tokens, the secrets, both Transit keys), best
effort, when it ends. The Transit mount that the shared fixture enables stays enabled, as on main. A test
that is killed leaves its objects behind, so point HADAVIN_TEST_VAULT_ADDR only at a throwaway server.
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
    admin_token: str = dataclasses.field(repr=False)  # never printed by a failing assertion
    # requests that undo what a test made, sent with the admin token when the test ends
    undo: list[tuple[str, str, dict | None]] = dataclasses.field(
        default_factory=list, repr=False, compare=False
    )

    def clean_up(self) -> None:
        """Best effort: a clean-up request that fails must not hide the test's own result."""
        admin = self.admin()
        while self.undo:
            method, path, body = self.undo.pop()
            try:
                admin.authed(method, path, body)
            except (VaultError, OSError):
                continue

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
        self.undo.append(("DELETE", f"sys/policies/acl/{name}", None))
        body = {"policies": [name], "no_default_policy": True, "ttl": LIFETIME, "renewable": False}
        status, answer = admin.authed("POST", "auth/token/create", body)
        assert status == 200, f"creating the runtime token answered {status}"
        del body
        policies = list(answer["auth"]["policies"])
        token = answer["auth"]["client_token"]
        del answer  # the answer holds the token: keep it out of any assertion message below
        self.undo.append(("POST", "auth/token/revoke", {"token": token}))
        held_only_the_policy = policies == [name]  # nothing else, not even `default`
        assert held_only_the_policy, policies
        return token


@pytest.fixture
def engine():
    mode, reason = engine_mode(os.environ)
    if mode == "fail":
        pytest.fail(reason)
    if mode == "skip":
        pytest.skip(reason)
    made = Engine(*vault_target())
    yield made
    made.clean_up()


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
    """Control: the same requests with the admin token are answered 200 or 204. A 404 (a mistyped path)
    or any other answer fails: it would show nothing about the request the refusal was meant for."""
    admin = engine.admin()
    for what, method, path, body in requests:
        status, _ = admin.authed(method, path, body)
        assert status in (200, 204), (
            f"control, {what}: {method} {path} answered {status} for the admin token, expected 200 or 204"
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
            ("read two levels below the prefix", "GET", f"{mount}/data/{here}deep/alpha", None),
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
    for p in (prefix, other, prefix + "deep/"):
        status, _ = admin.authed("POST", f"secret/data/{p}alpha", {"data": {"value": "v-" + p}})
        assert status in (200, 204), status
        engine.undo.append(("DELETE", f"secret/metadata/{p}alpha", None))
    values = {"mount": "secret", "path_prefix": prefix}
    return SecretsCase(engine, policy_of("secrets/vault"), values, prefix, other)


def test_vault_secrets_the_allowed_read_works_with_only_the_generated_policy(secrets_case):
    case = secrets_case
    token = case.engine.runtime_token(pp.render_vault(case.policy, case.values))
    value = case.provider(token, case.prefix).get("alpha")
    del token
    assert value == "v-" + case.prefix


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
    value = case.provider(token, case.prefix).get("alpha")  # the token is valid
    del token
    assert value == "v-" + case.prefix
    not_refused_for_admin(case.engine, case.never_requests())


def test_plant_a_vault_policy_widened_to_the_whole_mount_fails_the_refusal_check(secrets_case):
    case = secrets_case
    text = pp.render_vault(case.policy, case.values)
    widened = text.replace(f'"secret/data/{case.prefix}+"', '"secret/data/*"')
    assert widened != text
    token = case.engine.runtime_token(widened)
    with pytest.raises(
        AssertionError, match="read outside the prefix: .* answered 200, expected 403"
    ):
        refused(case.engine, token, case.never_requests()[1:])


def test_plant_the_old_everything_below_the_prefix_form_fails_the_refusal_check(secrets_case):
    """Result review Major 2: `<prefix>*` also lets the token read below the one path part the code reads."""
    case = secrets_case
    text = pp.render_vault(case.policy, case.values)
    old_form = text.replace(f'"secret/data/{case.prefix}+"', f'"secret/data/{case.prefix}*"')
    assert old_form != text
    token = case.engine.runtime_token(old_form)
    with pytest.raises(
        AssertionError, match="read two levels below the prefix: .* answered 200, expected 403"
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
    for name in (key, spare):  # undone last-in first-out: allow deletion, then delete
        engine.undo.append(("DELETE", f"transit/keys/{name}", None))
        engine.undo.append(("POST", f"transit/keys/{name}/config", {"deletion_allowed": True}))
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


# ------------------------------------------------------------- checks of this file itself (no server needed)


def test_the_refused_requests_are_the_ones_the_page_names():
    """The page prints `REFUSALS` as what these tests send; this keeps the two lists equal."""
    secrets = SecretsCase(None, None, {"mount": "secret"}, "here/", "other/")
    transit = TransitCase(None, None, {"transit_mount": "transit"}, "key", "spare")
    assert [r[0] for r in secrets.never_requests()] == list(pp.REFUSALS["secrets/vault"])
    assert [r[0] for r in transit.never_requests("key")] == list(
        pp.REFUSALS["signer/vault_transit"]
    )
    assert set(pp.REFUSALS) == {
        k for k, p in pp.load_all(ROOT_DIR).items() if p.platform == "vault"
    }
    deep = secrets.never_requests()[0]
    assert deep[1:3] == ("GET", "secret/data/here/deep/alpha")  # two path parts below the prefix


def test_a_failing_assertion_cannot_print_a_token():
    made_up = f"made-up-{uuid.uuid4().hex}"
    engine = Engine("http://127.0.0.1:8200", made_up)
    engine.undo.append(("POST", "auth/token/revoke", {"token": made_up}))
    secrets = SecretsCase(engine, None, {"mount": "secret"}, "here/", "other/")
    transit = TransitCase(engine, None, {"transit_mount": "transit"}, "key", "spare")
    for thing in (engine, secrets, transit):
        assert made_up not in repr(thing) and made_up not in str(thing)
    assert "admin_token" not in repr(engine)


def test_the_admin_control_fails_on_an_answer_that_is_not_200_or_204():
    """A mistyped path answers 404 for the admin token: the control must not accept that."""

    class Answers:
        def __init__(self, status: int) -> None:
            self.status = status

        def admin(self):
            return self

        def authed(self, method, path, body=None):
            return self.status, {}

    request = [("read a path that does not exist", "GET", "secret/data/nope", None)]
    for status in (200, 204):
        not_refused_for_admin(Answers(status), request)
    for status in (403, 404, 405, 500):
        with pytest.raises(AssertionError, match=f"answered {status} for the admin token"):
            not_refused_for_admin(Answers(status), request)


def test_clean_up_sends_every_undo_request_and_survives_a_failure():
    sent = []

    class Recorder(Engine):
        def admin(self):
            outer = self

            class Admin:
                def authed(self, method, path, body=None):
                    sent.append((method, path))
                    if path == "boom":
                        raise VaultError("made-up failure")
                    return 204, {}

            del outer
            return Admin()

    engine = Recorder("http://127.0.0.1:8200", "unused")
    engine.undo.extend([("DELETE", "a", None), ("DELETE", "boom", None), ("POST", "c", {})])
    engine.clean_up()
    assert sent == [("POST", "c"), ("DELETE", "boom"), ("DELETE", "a")] and engine.undo == []
