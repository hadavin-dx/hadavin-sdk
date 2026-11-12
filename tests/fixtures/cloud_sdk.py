"""A stand-in for the cloud SDK, shared by the tests of the sign-in (r19 group 7: it lived in `tests/test_migration_verify.py`
and two other test files imported it from there)."""

from __future__ import annotations


def a_cloud_sdk_whose_token_request_fails(monkeypatch, error):
    """The real sign-in helper (`store/auth_aws.py`) on a stand-in client whose token request raises `error`."""
    import boto3

    class Rds:
        def generate_db_auth_token(self, **kwargs):
            raise error

    monkeypatch.setattr(boto3, "client", lambda service, **kwargs: Rds())
