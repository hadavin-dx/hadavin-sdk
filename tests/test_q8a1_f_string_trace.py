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
    assert err.value.__cause__ is None and err.value.__suppress_context__ is True


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
    operator asked for, never put in a message or a log). The region and the bucket are validated by a pattern
    (`^[A-Za-z0-9-]+$`; the bucket by the S3 pattern); a value that does not match is refused at load by a fixed
    sentence (round 8). The list itself names them: a host name is the defining id (open question q-q8a1-hide-ids)."""
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
