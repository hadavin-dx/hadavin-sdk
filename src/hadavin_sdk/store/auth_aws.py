"""RDS IAM sign-in for the postgres store (`iam_auth: true`; `pip install hadavin-sdk[aws]`).

The only place the store touches an AWS SDK: a 15-minute IAM token stands in for the password, so no database
password exists anywhere and the task role's `rds-db:connect` decides. Ported from WARDEN `audit.py:_pg_connect`
(main a1e76cbf).
"""

from __future__ import annotations

from collections.abc import Callable

import boto3  # the extra: a missing install is turned into the install hint by store.postgres

from hadavin_sdk.errors import SignInError


def _refused(kind: str) -> SignInError:
    # Round 17 group 3 (b) and round 18 group 1: the SDK's words are not printed (they can hold an account name) and the SDK
    # error itself is not kept on the refusal either (`__context__` and `__cause__` are both empty): every caller holds only
    # the NAME of the error class, leaves its `except` block, and raises from there, so no exception is being handled when
    # the refusal is made. `raise ... from None` alone would hide it from the printed traceback and nothing more.
    return SignInError(
        f"the sign-in for the database connection failed ({kind}); "
        "check the cloud login of this process and the region."
    )


def rds_iam(region: str | None) -> Callable[[str, int, str], str]:
    failed = ""
    try:
        client = boto3.client("rds", region_name=region)
    except Exception as exc:  # noqa: BLE001 - any failure of the sign-in step, not two library types (round 18 group 2); only the class name is kept
        failed = type(exc).__name__
    if failed:
        raise _refused(failed)

    def password(host: str, port: int, user: str) -> str:
        failed = ""
        try:
            return client.generate_db_auth_token(DBHostname=host, Port=port, DBUsername=user)
        except Exception as exc:  # noqa: BLE001 - same as above; KeyboardInterrupt and SystemExit are not `Exception` and pass
            failed = type(exc).__name__
        raise _refused(failed)

    return password
