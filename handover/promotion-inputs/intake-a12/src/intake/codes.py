"""The closed set of refusal and error codes the intake service may name, and the two exception types that carry them.

Every code used by a ``Refused``, ``ConfigError`` or ``SecretError`` call (or as a ``ModelResult.error``) must be listed here;
``tests/test_codes.py`` scans the source and fails on a code that is used but not listed."""

from __future__ import annotations

# model errors (the backend maps; a response body is never stored or logged)
MODEL_ERRORS = frozenset(
    {
        "gate",
        "budget",
        "halted",
        "timeout",
        "net",
        "tls",
        "http_429",
        "http_4xx",
        "http_5xx",
        "over_cap",
        "bad_reply",
        "max_tokens",
        "body_unsafe",
        "provider_limit",  # the provider says its own spending limit is reached (HTTP 429 spend cap or a console limit as HTTP 400)
    }
)
# secret store parse and shape codes
SECRET_CODES = frozenset(
    {
        "key_file_missing",
        "key_name_missing",
        "key_empty",
        "key_malformed",
        "key_duplicate",
        "key_encoding",
        "key_short",
        "key_mode",
        "secrets_in_repo",
    }
)
# data gate, spend guard, configuration
GATE_BUDGET_CODES = frozenset(
    {
        "real_file_refused",
        "not_on_list",
        "owner_sentence_missing",
        "fake_on_real_folder",
        "prices_missing",
        "provider_limit_missing",
        "ledger_missing",
        "ledger_inconsistent",
        "budget_total",
        "budget_halted",
        "window_ended",
        "budget_day",
        "budget_run",
        "provider_limit",
        "transport_cooldown",
        "cap_too_small_for_worst_case",
        "settle_failed",
        "local_unset",
        "bad_config",
        "bad_backend",
    }
)
# scan, decisions, queue, exporter, service
SERVICE_CODES = frozenset(
    {
        "too_large",
        "bad_name",
        "outside_inbox",
        "invalid_reason",
        "already_decided",
        "stale_content",
        "reject_only",
        "purge_refused",
        "row_id_conflict",
        "approval_mismatch",
        "not_found",
        "kill_switch",
        "already_exported",
        "not_approved",
        "not_approvable",
        "sink_locked",
        "not_configured",
        "unexplained_number",  # the reason text of flag D12
        "bad_decision",
        "state_conflict",
        "id_collision",
        "sink_error",
        "db_error",
        "exported",
        "db_busy",
        "stored_data_bad",
        "service_running",
        "not_demo_home",
        # WP6 (errata 51.2, W-15): the service, sign-in and request codes
        "unauthorized",
        "login_failed",
        "bad_host",
        "bad_origin",
        "csrf_failed",
        "role_denied",
        "token_not_allowed",
        "bad_request",
        "bad_query",
        "length_required",
        "body_too_large",
        "method_not_allowed",
        "not_a_file",
        "serve_running",
        "port_in_use",
        "internal",
        "too_many_attempts",
    }
)
# the refusal codes that mean "the spending wall is up": the scan stops calling the model and the page shows the wall text (pinned by test_codes)
WALL_CODES = frozenset(
    {
        "budget_total",
        "budget_halted",
        "window_ended",
        "budget_day",
        "budget_run",
        "provider_limit",  # mut:wall_provider_limit
        "transport_cooldown",
    }
)
# a scan also stops on a refusal that will repeat for every document (nothing to spend against, no prices, no sentence): it must not walk the queue
SCAN_STOP_CODES = WALL_CODES | frozenset(
    {
        "ledger_missing",
        "ledger_inconsistent",
        "prices_missing",
        "provider_limit_missing",
        "owner_sentence_missing",
        "cap_too_small_for_worst_case",
    }
)
CODES = MODEL_ERRORS | SECRET_CODES | GATE_BUDGET_CODES | SERVICE_CODES

# the class names whose first argument is a code (the test scans for them)
CODE_RAISERS = ("Refused", "ConfigError", "SecretError")


class Refused(Exception):  # noqa: N818 (name fixed by the spec)
    """A refusal with a closed code; the command line prints ``refused: <code>: <text>`` and exits 2."""

    def __init__(self, code: str, text: str = "") -> None:
        super().__init__(f"{code}: {text}" if text else code)
        self.code = code
        self.text = text


class ConfigError(Exception):
    """Bad input or configuration; the command line exits 3."""

    def __init__(self, code: str, text: str = "") -> None:
        super().__init__(f"{code}: {text}" if text else code)
        self.code = code
        self.text = text


class SecretError(Refused):
    """A secrets-file problem. The text names the secret, never a value. ``line`` is the 1-based number of a malformed line (never its content)."""

    def __init__(self, code: str, text: str = "", line: int | None = None) -> None:
        super().__init__(code, text)
        self.line = line
