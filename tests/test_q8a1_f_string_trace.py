"""Round 10, Issue 2 of Q8a-1: the eleven places in `src` where a configured name (a project, a region, a bucket, a
namespace, a schema, a role) is put into an f-string were traced one by one. For each place this file plants a made-up
marker as the configured value, drives the code that uses it, and checks that the marker is in no message, log line,
exception text or traceback (the text a person could see). The table in `handover/evidence/Q8a-1/b11/pr-notes.md`
says, for each place, what it is for and which test here covers it.

Each marker is built from parts at run time: it is made up and is not a credential. A test that passes on the old
code is a CONTROL: it proves a place that was already clean stays clean (its docstring says so); the others failed on
the head `f4acee28` (the evidence list says which)."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from hadavin_sdk.errors import ConfigError
from tests.test_stage_names import _everything_shown

MARKER = (
    "zq" + "-probe-" + "mk4417"
)  # a lower-case word with digits: a legal project, bucket, region, namespace
SECRET_LOOKING = "Zq9x" + "-Pw-" + "4417"  # capital letters: not a legal namespace or role name


def _seen(exc: BaseException, caplog) -> str:
    return _everything_shown(exc) + "\n" + caplog.text


# ---- hit 1: actions/secrets_gcp.py:39 `projects/{project_id}/secrets/{name}/versions/latest` ------------------------
@pytest.mark.parametrize(
    "error_text", ["permission denied on {path}", "{path} is not allowed", "{name}"]
)
def test_a_cloud_error_that_quotes_the_secret_path_is_never_passed_on(error_text, caplog):
    """The path holds the configured project id and the secret name; a cloud library quotes the path in its errors
    (GCP: the resource name, AWS: the ARN, Azure: the URL). The shared base of the cloud kinds says the class only."""
    pytest.importorskip("google.cloud.secretmanager", reason="needs extra gcp")
    from hadavin_sdk.actions.secrets_gcp import GcpSecretManagerProvider

    class Client:
        def access_secret_version(self, name, retry=None, timeout=None):
            raise RuntimeError(error_text.format(path=name, name=MARKER))

    provider = GcpSecretManagerProvider(Client(), project_id=MARKER)
    with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as err:
        provider.get("a_secret")
    assert str(err.value) == "secrets: reading a secret failed (RuntimeError)"
    assert MARKER not in _seen(err.value, caplog)
    assert err.value.__cause__ is None and err.value.__context__ is None


def test_the_aws_and_azure_kinds_say_the_class_of_a_library_error_only(caplog):
    """Sibling of hit 1 (same class, other kinds of the shared base): a library error that quotes the name."""
    pytest.importorskip("boto3", reason="needs extra aws")
    pytest.importorskip("azure.keyvault.secrets", reason="needs extra azure")
    from hadavin_sdk.actions.secrets_aws import SecretsManagerProvider
    from hadavin_sdk.actions.secrets_azure import AzureKeyVaultProvider

    class Aws:
        def get_secret_value(self, SecretId):  # the library's own keyword
            raise RuntimeError(
                f"not authorised on arn:partition:service:region:account:secret:{SecretId}"
            )

    class Azure:
        def get_secret(self, name):
            raise RuntimeError(f"https://{MARKER}.vault.example.invalid/secrets/{name}")

    for provider in (SecretsManagerProvider(Aws()), AzureKeyVaultProvider(Azure())):
        with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as err:
            provider.get(MARKER)
        assert str(err.value) == "secrets: reading a secret failed (RuntimeError)"
        assert MARKER not in _seen(err.value, caplog)


def test_a_sentence_this_package_wrote_still_passes_through_the_shared_base():
    """CONTROL (passes on the old code too): a `ConfigError` of the kind itself (a secret that is not found) is a
    fixed sentence and is shown as it is."""
    from hadavin_sdk.actions.secrets_cache import CachedSecrets

    class Kind(CachedSecrets):
        def _fetch(self, name):
            raise ConfigError("the secret was not found in the store")

    with pytest.raises(ConfigError, match="was not found"):
        Kind().get("x")


# ---- hits 2 and 3: llm/anthropic.py:32 and :33, the region in the Vertex base URL -------------------------------------
def test_a_client_library_error_that_quotes_the_base_url_is_not_passed_on(monkeypatch, caplog):
    """The region is in the base URL (`https://<region>-aiplatform.googleapis.com/v1`); a library `ValueError` can
    quote the URL. The refusal is a fixed sentence with the error class."""
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    from hadavin_sdk.llm import anthropic as wire

    class Vertex:
        def __init__(self, **kw):
            raise ValueError(f"bad base_url {kw['base_url']} for region {kw['region']}")

    monkeypatch.setattr(wire.anthropic, "AnthropicVertex", Vertex)
    settings = SimpleNamespace(
        platform="vertex", region=MARKER, project_id=MARKER, call_timeout_s=5, resource=None
    )
    with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as err:
        wire.client(settings, None)
    assert "the client refused the settings (ValueError)" in str(err.value)
    assert MARKER not in _seen(err.value, caplog)
    assert err.value.__cause__ is None and err.value.__suppress_context__ is True


def test_the_real_client_library_does_not_quote_the_resource_in_its_refusal(monkeypatch, caplog):
    """The real library, with the variable set that makes it refuse (ANTHROPIC_FOUNDRY_RESOURCE beside our explicit
    base URL): the refusal does not hold the configured resource."""
    pytest.importorskip("anthropic", reason="needs extra anthropic")
    from hadavin_sdk.llm import anthropic as wire

    monkeypatch.setenv("ANTHROPIC_FOUNDRY_RESOURCE", "elsewhere")
    settings = SimpleNamespace(
        platform="foundry", resource=MARKER, region=None, project_id=None, call_timeout_s=5
    )
    with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as err:
        wire.client(settings, "k")
    assert MARKER not in _seen(err.value, caplog)


# ---- hits 4 and 5: sources/kubernetes.py:237 and :251, the namespace in an API path --------------------------------
def test_a_fetch_error_that_quotes_the_api_path_never_shows_the_namespace(caplog):
    """CONTROL (passes on the old code too): the namespace is only in the request path. A fetch that raises with the
    path in its text (a transport error does) is turned into "kubernetes: <class>" and the cause is dropped; the
    evidence ids of a successful answer carry the namespace the caller asked for (records, not messages)."""
    from hadavin_sdk.sources import SourceError
    from hadavin_sdk.sources.kubernetes import KubernetesSettings, KubernetesSource

    def fetch(method, url, **kw):
        raise OSError(f"{method} {url} refused")

    settings = KubernetesSettings(api_url="https://k8s.example.invalid", namespaces=(MARKER,))
    source = KubernetesSource(fetch, settings)
    with caplog.at_level(logging.DEBUG):
        for call in (
            lambda: source.recent_changes(MARKER, "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"),
            lambda: source.query_logs(
                MARKER + "/pod", "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", 5
            ),
            source.probe_scope,
        ):
            with pytest.raises(SourceError) as err:
                call()
            assert str(err.value) == "kubernetes: OSError"
            assert MARKER not in _seen(err.value, caplog)


# ---- hit 6: store/migration_numbers.py:251 `SET search_path TO "{schema}"` ------------------------------------------
def test_the_hand_recipe_prints_only_a_plain_schema_name_and_refuses_any_other_with_a_fixed_sentence():
    """CONTROL (passes on the old code too): the schema is `current_schema()` read from the database inside the
    transaction (database state, not text of the configuration file). The recipe is text for a database
    administrator and must name the schema; a name that is not a plain lower-case identifier gets no recipe, and
    the refusal does not hold it."""
    from pathlib import Path

    from hadavin_sdk.store.migration_numbers import hand_recipe, order_problems

    late = Path("0001_first.sql")  # a file numbered below one this database already applied

    assert 'SET search_path TO "public";' in hand_recipe([("0001_x", "SELECT 1;")], "public")
    for odd in (SECRET_LOOKING, 'a"b', MARKER + "-x"):
        with pytest.raises(ValueError) as err:
            hand_recipe([("0001_x", "SELECT 1;")], odd)
        assert str(err.value) == "the schema name has unusual characters"
        assert odd not in str(err.value)
        text = "\n".join(order_problems(["0002_second"], [late], {late: "SELECT 1;"}, odd))
        assert "No recipe is printed" in text and odd not in text


# ---- hits 7 and 8: store/migrate.py:212 `{role}: can CREATE in schema {schema}` ------------------------------------
def test_a_database_role_option_that_is_not_a_plain_name_is_refused_by_option_never_by_text():
    """The roles come from the command line of the person who runs `migrate`, and the schema from the database.
    Both are printed only after the role passed `_ROLE` (a plain lower-case identifier). A role that does not pass
    used to be echoed with `!r`; now the option is named and the text is not."""
    from hadavin_sdk.store.migrate import migrate

    for option in ("runtime_role", "portal_role", "purge_role"):
        with pytest.raises(ConfigError) as err:
            migrate("dsn-not-used", **{option: SECRET_LOOKING})
        assert str(err.value).startswith(f"{option}: not a plain database role name"), str(
            err.value
        )
        assert SECRET_LOOKING not in _everything_shown(err.value)


# ---- hits 9 to 11: backends/table.py:367, 379, 380, 394 (region and bucket in a host name) -------------------------
def test_a_region_or_bucket_is_in_the_suggested_host_list_and_in_no_error_text():
    """CONTROL (passes on the old code too): `hosts()` returns the suggested `egress.yaml` list (a returned value the
    operator asked for, never put in a message or a log; no caller prints it today). Every field that feeds a
    host name carries a pattern: Anthropic region and resource `^[A-Za-z0-9-]+$`, the AWS, S3, KMS and Postgres
    regions `^[a-z0-9-]+$`, the S3 bucket the AWS naming rules (rows below, Issue 1 of round 11); a value that does not
    match is refused at load by a fixed sentence (round 8). The list itself names them: a host name is the defining id (open question q-q8a1-hide-ids)."""
    from pydantic import ValidationError

    from hadavin_sdk.backends.table import (
        AnthropicSettings,
        S3ObjectLockSettings,
        _anthropic_hosts,
        _s3_anchor_hosts,
    )

    vertex = AnthropicSettings(
        kind="anthropic", platform="vertex", region=MARKER, project_id=MARKER
    )
    assert _anthropic_hosts(vertex)[0] == f"{MARKER}-aiplatform.googleapis.com"
    for bad in (SECRET_LOOKING + " x", MARKER + "/x"):
        with pytest.raises(ValidationError) as err:
            AnthropicSettings(kind="anthropic", platform="vertex", region=bad, project_id=MARKER)
        assert bad not in str(err.value)
    s3 = S3ObjectLockSettings(kind="s3_object_lock", bucket=MARKER, region="eu-west-1")
    assert _s3_anchor_hosts(s3) == [f"{MARKER}.s3.eu-west-1.amazonaws.com"]


# ---- Issue 1 of round 11: the region and bucket fields of AWS secrets, S3, KMS and Postgres carried no pattern -------
_BAD_HOST_PARTS = (
    SECRET_LOOKING + " x",
    MARKER + "/x",
    MARKER + ".evil.example/",
    "UPPER-" + MARKER,
)


def _aws_secrets(**kw):
    from hadavin_sdk.backends.table import AwsSecretsManagerSettings

    return AwsSecretsManagerSettings(kind="aws_secrets_manager", **{"region": "eu-west-1", **kw})


def _s3(**kw):
    from hadavin_sdk.backends.table import S3ObjectLockSettings

    return S3ObjectLockSettings(
        kind="s3_object_lock", **{"bucket": "a-bucket", "region": "eu-west-1", **kw}
    )


def _kms(**kw):
    from hadavin_sdk.backends.table import AwsKmsSettings

    return AwsKmsSettings(kind="aws_kms", **{"key_id": "k1", "region": "eu-west-1", **kw})


def _postgres(**kw):
    from hadavin_sdk.backends.table import PostgresSettings

    return PostgresSettings(kind="postgres", **{"dsn_secret_name": "dsn", **kw})


@pytest.mark.parametrize("bad", _BAD_HOST_PARTS)
@pytest.mark.parametrize(
    ("build", "field"),
    [
        (_aws_secrets, "region"),
        (_s3, "region"),
        (_s3, "bucket"),
        (_kms, "region"),
        (_postgres, "region"),
    ],
    ids=["aws-secrets-region", "s3-region", "s3-bucket", "kms-region", "postgres-region"],
)
def test_a_region_or_bucket_that_is_not_a_host_name_part_is_refused_and_not_quoted(
    build, field, bad
):
    """Fails on `c6028abb` (these four region fields and the bucket were plain `str`, so the value was accepted and
    went into a host name). Now each is refused at load, and the refusal does not quote the value."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as err:
        build(**{field: bad})
    assert bad not in _everything_shown(err.value)


def test_a_legal_region_and_bucket_are_still_accepted_and_make_the_host_names():
    from hadavin_sdk.backends.table import _aws, _s3_anchor_hosts

    assert _s3_anchor_hosts(_s3(bucket="my.bucket-1", region="cn-north-1")) == [
        "my.bucket-1.s3.cn-north-1.amazonaws.com.cn"
    ]
    assert _aws("secretsmanager")(_aws_secrets(region="us-gov-west-1")) == [
        "secretsmanager.us-gov-west-1.amazonaws.com"
    ]
    assert _postgres(region="eu-west-1").region == "eu-west-1"
    assert _kms().region == "eu-west-1"


@pytest.mark.parametrize("bucket", ["ab", "-abc", "abc-", ".abc", "abc.", "A" * 3, "a" * 64])
def test_the_s3_bucket_pattern_follows_the_aws_naming_rules(bucket):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _s3(bucket=bucket)


# ---- Issue 3 of round 11: `raise ... from exc` carried the library error (and its text) in the chain ---------------
def _assert_no_chain_and_no_marker(exc: BaseException, caplog=None) -> None:
    """The error holds no cause and no context, so nothing the library said can be reached from it, and the text a
    person could see (message, repr, whole traceback with the chain) has no marker."""
    assert exc.__cause__ is None, "the library error is still the cause"
    assert exc.__context__ is None, (
        "the library error is still the context (raise after the except block)"
    )
    assert (
        MARKER not in _seen(exc, caplog)
        if caplog is not None
        else MARKER not in _everything_shown(exc)
    )


def test_a_signing_error_that_quotes_the_key_leaves_no_trace_in_the_error(caplog):
    from hadavin_sdk.audit.signer import probe

    class Signer:
        key_id, alg = "k", "ed25519"

        def public_key(self):
            raise RuntimeError(f"AccessDenied on key arn:x:kms:{MARKER}")

        def sign(self, message):
            raise RuntimeError(MARKER)

    with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as err:
        probe(Signer(), "audit signer")
    assert str(err.value) == "audit signer: cannot sign at start-up (RuntimeError)"
    _assert_no_chain_and_no_marker(err.value, caplog)


def test_a_failing_audit_folder_says_the_class_only_and_leaves_no_trace(
    tmp_path, monkeypatch, caplog
):
    from hadavin_sdk.audit.local_dir import LocalDirSink
    from hadavin_sdk.audit.protocol import AuditUnavailable
    from hadavin_sdk.models import AuditEvent

    sink = LocalDirSink(tmp_path)

    def boom(event):
        raise OSError(13, "Permission denied", str(tmp_path / MARKER))

    monkeypatch.setattr(sink, "_write", boom)
    event = AuditEvent(run_id="r", domain="d", operation="o", principal="p", source="s")
    with caplog.at_level(logging.DEBUG), pytest.raises(AuditUnavailable) as err:
        sink.write_intent(event)
    assert str(err.value).endswith(": PermissionError")
    _assert_no_chain_and_no_marker(err.value, caplog)


def test_a_failing_audit_chain_says_the_class_only_and_leaves_no_trace(monkeypatch, caplog):
    from hadavin_sdk.audit import chain
    from hadavin_sdk.audit.protocol import AuditUnavailable
    from hadavin_sdk.models import AuditEvent

    log = chain.ChainAudit(chain._Db.memory())

    def boom(event):
        raise RuntimeError(f'connection to server at "{MARKER}" failed')

    monkeypatch.setattr(log, "_append", boom)
    event = AuditEvent(run_id="r", domain="d", operation="o", principal="p", source="s")
    with caplog.at_level(logging.DEBUG), pytest.raises(AuditUnavailable) as err:
        log.write_intent(event)
    assert str(err.value).endswith(": RuntimeError")
    _assert_no_chain_and_no_marker(err.value, caplog)


def test_a_guardrail_read_error_that_quotes_the_id_leaves_no_trace(caplog):
    from hadavin_sdk.guard.bedrock_guardrail import check_filter

    class Control:
        def get_guardrail(self, **kw):
            raise RuntimeError(f"not authorised on guardrail/{MARKER}")

    with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as err:
        check_filter(Control(), "gid", "1")
    assert str(err.value).endswith("cannot read the guardrail (RuntimeError)")
    _assert_no_chain_and_no_marker(err.value, caplog)


def test_an_unreadable_file_in_a_hash_set_leaves_no_trace(tmp_path, monkeypatch, caplog):
    from pathlib import Path

    from hadavin_sdk.hashing import hash_files

    (tmp_path / "f.txt").write_text("x", encoding="utf-8")
    real = Path.read_bytes

    def boom(self):
        if self.name == "f.txt":
            raise OSError(5, "Input/output error", str(tmp_path / MARKER))
        return real(self)

    monkeypatch.setattr(Path, "read_bytes", boom)
    with caplog.at_level(logging.DEBUG), pytest.raises(ConfigError) as err:
        hash_files(tmp_path, ["f.txt"])
    assert str(err.value) == "cannot read: f.txt"
    _assert_no_chain_and_no_marker(err.value, caplog)


@pytest.mark.parametrize("attempts", [1, 3])
def test_a_provider_error_that_quotes_the_request_leaves_no_trace(attempts, caplog):
    from hadavin_sdk.llm.protocol import ProviderError
    from hadavin_sdk.llm.retry import with_retry

    class Down(Exception):
        status_code = 503

    def call():
        raise Down(f"https://{MARKER}-aiplatform.googleapis.com/v1 failed")

    with caplog.at_level(logging.DEBUG), pytest.raises(ProviderError) as err:
        with_retry(call, label="llm", max_attempts=attempts, sleep=lambda s: None)
    _assert_no_chain_and_no_marker(err.value, caplog)


def test_every_wrapped_library_error_in_src_is_raised_without_a_cause():
    """The class, by reading `src`: no `raise ... from <name>` is left (the guard test also refuses one without an
    allowance). `from None` is the only form that is allowed in the source."""
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "src" / "hadavin_sdk"
    left = []
    for path in sorted(root.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Raise) and node.cause is not None:
                if not (isinstance(node.cause, ast.Constant) and node.cause.value is None):
                    left.append(f"{path.relative_to(root)}:{node.lineno}")
    assert left == [], left


# ---- Issue 4 of round 11: an unknown setting key was named in pydantic's "extra forbidden" text --------------------
def _every_settings_class():
    """Every class that inherits `KindSettings` (all backend kinds), found by walking the subclasses."""
    import hadavin_sdk.backends.table as table

    found, todo = {}, [table.KindSettings]
    while todo:
        cls = todo.pop()
        for sub in cls.__subclasses__():
            if sub not in found.values():
                found[sub.__name__] = sub
                todo.append(sub)
    return found


def test_every_kind_settings_class_refuses_an_unknown_key_without_naming_it():
    """Fails on `c6028abb` (9 rows of probe 5: the text of the pydantic error holds the key). A mistyped or pasted
    key can be a secret, so the refusal says the position and the names of this kind, which are written in code."""
    from pydantic import ValidationError

    classes = _every_settings_class()
    assert len(classes) >= 25, sorted(classes)
    for name, cls in sorted(classes.items()):
        for key in (MARKER, SECRET_LOOKING, "9f" * 16):
            with pytest.raises(ValidationError) as err:
                cls(**{key: 1})
            shown = _everything_shown(err.value) + repr(err.value.errors(include_input=False))
            assert key not in shown, (name, key)
            assert "unknown setting at position 1 (name not shown)" in shown, (name, shown)


def test_the_position_of_each_unknown_key_is_said_counted_from_1():
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as err:
        _aws_secrets(**{MARKER: 1, SECRET_LOOKING: 2})
    # `kind` is not counted: region is setting 1, then the two unknown keys are 2 and 3
    assert "unknown setting at position 2, 3 (name not shown)" in str(err.value)
    assert "the settings here are: kind, region, ttl_s" in str(err.value)


def test_the_models_built_straight_from_a_section_share_the_base_class():
    """The models that code builds directly from one section of a file all inherit the one refusal. The whole-file
    models (config, registry, tool manifest) are built by the loader only and show `<unknown key>` (tests in
    `tests/test_stage_names.py`: `test_an_unknown_key_in_..._is_not_shown`)."""
    import hadavin_sdk.sources.kubernetes as kube
    from hadavin_sdk.backends.table import KindSettings
    from hadavin_sdk.strict_model import StrictConfigModel

    for cls in (KindSettings, kube.KubernetesSettings):
        assert issubclass(cls, StrictConfigModel), cls
        assert cls.model_config.get("hide_input_in_errors") is True, cls
