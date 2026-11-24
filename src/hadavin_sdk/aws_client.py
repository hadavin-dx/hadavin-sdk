"""The one botocore ``Config`` every AWS client of this package is built with (`pip install hadavin-sdk[aws]`).

A helper of the AWS kinds, not a kind: it exists so that no AWS client takes its endpoint URL from the
environment. Only the endpoint URL: the FIPS and dual-stack variables (AWS_USE_FIPS_ENDPOINT,
AWS_USE_DUALSTACK_ENDPOINT) still choose between AWS's own endpoints and are left to the host.
"""

from __future__ import annotations

from typing import Any

from botocore.config import Config


def config(**options: Any) -> Config:
    """``Config(**options)`` that ignores endpoint URLs configured outside our settings: AWS_ENDPOINT_URL,
    AWS_ENDPOINT_URL_<SERVICE> and ``endpoint_url`` in the shared AWS config file would send a signed request
    to another host. An ``endpoint_url`` argument given to the client itself (a kind's own validated setting)
    still wins (botocore 1.43.122 args.py:387-395, configprovider.py:1060-1081; checked 2026-11-24)."""
    return Config(ignore_configured_endpoint_urls=True, **options)
