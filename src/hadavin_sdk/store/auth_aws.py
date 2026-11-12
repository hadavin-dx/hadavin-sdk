"""RDS IAM sign-in for the postgres store (`iam_auth: true`; `pip install hadavin-sdk[aws]`).

The only place the store touches an AWS SDK: a 15-minute IAM token stands in for the password, so no database
password exists anywhere and the task role's `rds-db:connect` decides. Ported from WARDEN `audit.py:_pg_connect`
(main a1e76cbf).
"""

from __future__ import annotations

from collections.abc import Callable

import boto3  # the extra: a missing install is turned into the install hint by store.postgres
from botocore.exceptions import BotoCoreError, ClientError

from hadavin_sdk.errors import SignInError


def _refused(exc: Exception) -> SignInError:
    # Round 17 group 3 (b): the SDK's words are not printed (they can hold an account name); the kind of error is enough.
    return SignInError(
        f"the sign-in for the database connection failed ({type(exc).__name__}); "
        "check the cloud login of this process and the region."
    )


def rds_iam(region: str | None) -> Callable[[str, int, str], str]:
    try:
        client = boto3.client("rds", region_name=region)
    except (BotoCoreError, ClientError) as exc:
        raise _refused(exc) from None

    def password(host: str, port: int, user: str) -> str:
        try:
            return client.generate_db_auth_token(DBHostname=host, Port=port, DBUsername=user)
        except (BotoCoreError, ClientError) as exc:
            raise _refused(exc) from None

    return password
