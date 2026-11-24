"""No AWS client of the package takes its endpoint from the environment (`hadavin_sdk.aws_client.config`).

AWS_ENDPOINT_URL and AWS_ENDPOINT_URL_<SERVICE> would send a signed request (a secret read, a signature, a
prompt) to another host. The two Bedrock clients have their own cases in tests/warden_port/
test_bedrock_provider_r16.py and tests/test_p6_detectors.py; here are the helper and the other four.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

boto3 = pytest.importorskip("boto3", reason="needs extra aws")

from hadavin_sdk import aws_client
from hadavin_sdk.actions import secrets_aws
from hadavin_sdk.audit import anchor_s3, signer_aws
from hadavin_sdk.store import auth_aws

REGION = "contract-region-1"
EVIL = "http://evil.example"
SRC = Path(aws_client.__file__).parent


def test_only_the_six_aws_kind_modules_use_the_helper():
    users = {
        path.relative_to(SRC).as_posix()
        for path in SRC.rglob("*.py")
        if "aws_client" in path.read_text(encoding="utf-8") and path.name != "aws_client.py"
    }
    assert users == {
        "actions/secrets_aws.py",
        "audit/anchor_s3.py",
        "audit/signer_aws.py",
        "guard/bedrock_guardrail.py",
        "llm/bedrock.py",
        "store/auth_aws.py",
    }
    # ... and each of them builds its client with it: no boto3 client in src without the helper's config.
    for name in users:
        source = (SRC / name).read_text(encoding="utf-8")
        assert source.count("boto3.client(") == source.count("aws_client.config(") == 1, name


@pytest.fixture
def built(monkeypatch):
    """Every boto3 client a module builds while the environment names another endpoint."""
    made, real = [], boto3.client
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: made.append(real(*a, **kw)) or made[-1])
    for name in (
        "AWS_ENDPOINT_URL",
        "AWS_ENDPOINT_URL_SECRETS_MANAGER",
        "AWS_ENDPOINT_URL_KMS",
        "AWS_ENDPOINT_URL_RDS",
        "AWS_ENDPOINT_URL_S3",
    ):
        monkeypatch.setenv(name, EVIL)
    return made


def _s3(endpoint_url):
    settings = SimpleNamespace(
        region=REGION, endpoint_url=endpoint_url, bucket="b", mode="COMPLIANCE", retain_days=1
    )
    return anchor_s3.build(settings, None)


def test_the_helper_sets_the_flag_and_keeps_the_options():
    config = aws_client.config(read_timeout=7)
    assert config.ignore_configured_endpoint_urls is True and config.read_timeout == 7


def test_boto3_itself_would_follow_the_environment(built):
    """The control: without the helper the variable wins, so the cases below test something."""
    assert boto3.client("kms", region_name=REGION).meta.endpoint_url == EVIL


@pytest.mark.parametrize(
    "service, build",
    [
        (
            "secretsmanager",
            lambda: secrets_aws.build(SimpleNamespace(region=REGION, ttl_s=60), None),
        ),
        ("kms", lambda: signer_aws.build(SimpleNamespace(region=REGION, key_id="k"), None)),
        ("rds", lambda: auth_aws.rds_iam(REGION)),
        ("s3", lambda: _s3(None)),
    ],
)
def test_the_endpoint_never_comes_from_the_environment(monkeypatch, built, service, build):
    monkeypatch.setattr(
        signer_aws, "probe", lambda signer, label: signer
    )  # no KMS call at start-up
    build()
    [client] = built
    url = client.meta.endpoint_url
    assert url.startswith(f"https://{service}.") and url.endswith(".amazonaws.com")


def test_the_s3_kinds_own_endpoint_setting_still_works(built):
    _s3("https://minio.example:9000")
    assert built[0].meta.endpoint_url == "https://minio.example:9000"


def test_an_endpoint_in_the_shared_aws_config_file_is_ignored(monkeypatch, tmp_path):
    """The flag covers the config file too, not only the two environment variables."""
    config = tmp_path / "config"
    config.write_text(f"[default]\nendpoint_url = {EVIL}\n", encoding="utf-8")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.setattr(
        boto3, "DEFAULT_SESSION", None
    )  # the session reads the file when it is made
    assert boto3.client("kms", region_name=REGION).meta.endpoint_url == EVIL  # the control
    monkeypatch.setattr(signer_aws, "probe", lambda signer, label: signer)
    made, real = [], boto3.client
    monkeypatch.setattr(boto3, "client", lambda *a, **kw: made.append(real(*a, **kw)) or made[-1])
    signer_aws.build(SimpleNamespace(region=REGION, key_id="k"), None)
    assert made[0].meta.endpoint_url == f"https://kms.{REGION}.amazonaws.com"
