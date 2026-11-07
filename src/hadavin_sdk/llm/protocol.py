"""Model adapter Protocol. Kinds: ``fake``, ``anthropic``, ``bedrock``, ``openai_compat``, ``gemini``."""

from __future__ import annotations

from typing import Any, Protocol

from hadavin_sdk.codes import ProviderErrorType
from hadavin_sdk.llm.provider_facts import (
    clean_count,
    clean_error_type,
    clean_flag,
    clean_request_id,
    clean_status,
)
from hadavin_sdk.models import Reply


class ProviderError(RuntimeError):
    """The provider refused the request (a bad key, a malformed request): retrying would fail the same way.

    Five checked facts ride on the error (all keyword-only, all ``None`` when unknown): ``status`` (HTTP, 100 to 599),
    ``error_type`` (a ``ProviderErrorType``), ``request_id`` (one of two closed shapes), ``retryable`` (a ``bool``) and
    ``retry_count`` (requests started, up to and including the failing one). An invalid value is dropped, never raised on.
    """

    status: int | None = None
    error_type: ProviderErrorType | None = None
    request_id: str | None = None
    retryable: bool | None = None
    retry_count: int | None = None

    def __init__(
        self,
        *args: object,
        status: int | None = None,
        error_type: ProviderErrorType | None = None,
        request_id: str | None = None,
        retryable: bool | None = None,
        retry_count: int | None = None,
    ) -> None:
        super().__init__(*args)
        self.status = clean_status(status)
        self.error_type = clean_error_type(error_type)
        self.request_id = clean_request_id(request_id)
        self.retryable = clean_flag(retryable)
        self.retry_count = clean_count(retry_count)


class ProviderExhausted(ProviderError):
    """The provider throttled or failed after its retries."""


class LLM(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str,
        route: str,
        tools: list[dict[str, Any]] | None = None,
        documents: list[bytes] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> Reply: ...
