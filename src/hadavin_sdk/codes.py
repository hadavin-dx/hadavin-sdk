"""Closed lists for diagnostics: failure codes, steps, fact keys, bounds and the table of this package's own exception classes.

Standard library only; this module imports nothing from the package (a test checks it). It is data, not logic: the lists are
enumerations and tables, and a value outside a list is dropped by ``guard/diagnostic.py``, never printed. Adding a member to
``Code`` is a reviewed change to the frozen test ``tests/test_diagnostic_codes.py``.
"""

from __future__ import annotations

import enum
import sys
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final


class Code(enum.StrEnum):
    """What kind of failure it is (design D4, plus ``tool_refused``). 21 members."""

    config_invalid = "config_invalid"
    store_unavailable = "store_unavailable"
    store_conflict = "store_conflict"
    provider_http = "provider_http"
    provider_timeout = "provider_timeout"
    provider_rate_limit = "provider_rate_limit"
    provider_invalid_request = "provider_invalid_request"
    provider_auth = "provider_auth"
    provider_exhausted = "provider_exhausted"
    audit_unavailable = "audit_unavailable"
    egress_refused = "egress_refused"
    unqualified = "unqualified"
    validation_failed = "validation_failed"
    scan_failed = "scan_failed"
    timeout = "timeout"
    os_error = "os_error"
    db_error = "db_error"
    internal_bug = "internal_bug"
    foreign_exception = "foreign_exception"
    session_closed = "session_closed"
    tool_refused = "tool_refused"


# Members that no class on this tree yields yet; the named package makes each reachable.
RESERVED_FOR: Final[Mapping[str, str]] = MappingProxyType(
    {
        "session_closed": "P5c",
    }
)


class ProviderErrorType(enum.StrEnum):
    rate_limit = "rate_limit"
    overloaded = "overloaded"
    invalid_request = "invalid_request"
    authentication = "authentication"
    permission = "permission"
    not_found = "not_found"
    server_error = "server_error"
    timeout = "timeout"
    connection = "connection"
    throttled = "throttled"
    quota = "quota"
    other = "other"


class Phase(enum.StrEnum):
    """The ``phase`` fact: the sqlstate class of a database error."""

    auth = "auth"
    connect = "connect"
    query = "query"
    unknown = "unknown"


class Where(enum.StrEnum):
    """The step where the failure happened (design D3)."""

    extract = "extract"
    model_call = "model_call"
    scan = "scan"
    audit = "audit"
    config_load = "config_load"
    registry_load = "registry_load"
    cli = "cli"
    other = "other"


# The six tick step names (``runtime/tick.py`` STEPS); a test compares this set with that list.
TICK_STEPS: Final = frozenset(
    {"sweep", "reconcile", "stuck", "checkpoint", "purge_evidence", "reprobe_sources"}
)


class StepToken:
    """A tick step name that passed the closed list. Made only by ``StepToken.of``; holds a member of ``TICK_STEPS``."""

    __slots__ = ("value",)
    value: str

    def __init_subclass__(cls, **kw: object) -> None:
        raise TypeError("StepToken is final")

    def __init__(self, value: str) -> None:
        if type(value) is not str or value not in TICK_STEPS:
            raise ValueError("not a tick step")
        object.__setattr__(self, "value", next(m for m in TICK_STEPS if m == value))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("StepToken is immutable")

    @staticmethod
    def of(value: object) -> StepToken | Where:
        """A tick step name becomes a ``StepToken``; a ``Where`` member stays; anything else is ``Where.other``. Never raises."""
        if type(value) is Where:
            return value
        if type(value) is str and value in TICK_STEPS:
            return StepToken(value)
        return Where.other


class FactKey(enum.StrEnum):
    type = "type"
    key = "key"
    http_status = "http_status"
    sqlstate = "sqlstate"
    phase = "phase"
    cause_kind = "cause_kind"
    provider_error_type = "provider_error_type"
    request_id = "request_id"
    retryable = "retryable"
    errno = "errno"
    winerror = "winerror"
    gai = "gai"
    count = "count"
    position = "position"
    line = "line"
    column = "column"
    field = "field"
    retry_count = "retry_count"
    attempt = "attempt"
    duration_ms = "duration_ms"


# The order facts are printed in and the order the first DIAG_MAX_FACTS are kept (design D9).
FACT_PRIORITY: Final = (
    FactKey.type,
    FactKey.key,
    FactKey.http_status,
    FactKey.sqlstate,
    FactKey.phase,
    FactKey.cause_kind,
    FactKey.provider_error_type,
    FactKey.request_id,
    FactKey.retryable,
    FactKey.errno,
    FactKey.winerror,
    FactKey.gai,
    FactKey.count,
    FactKey.position,
    FactKey.line,
    FactKey.column,
    FactKey.field,
    FactKey.retry_count,
    FactKey.attempt,
    FactKey.duration_ms,
)

# The ONE place for numeric bounds (inclusive). Protocol bounds, not configuration.
FACT_BOUNDS: Final[Mapping[FactKey, tuple[int, int]]] = MappingProxyType(
    {
        FactKey.http_status: (100, 599),
        FactKey.retry_count: (0, 1000),
        FactKey.attempt: (0, 1000),
        FactKey.errno: (0, 20000),
        FactKey.winerror: (0, 20000),
        FactKey.gai: (-20000, 20000),
        FactKey.count: (0, 10**6),
        FactKey.position: (0, 10**9),
        FactKey.line: (0, 10**9),
        FactKey.column: (0, 10**9),
        FactKey.duration_ms: (0, 10**9),
    }
)

# The 26 closed names ``validation_text`` and the ``type`` fact may print; any other pydantic type prints ``other``.
VALIDATION_TYPES: Final = frozenset(
    {
        "missing",
        "extra_forbidden",
        "literal_error",
        "int_parsing",
        "float_parsing",
        "bool_parsing",
        "string_type",
        "int_type",
        "dict_type",
        "list_type",
        "too_short",
        "too_long",
        "greater_than",
        "less_than",
        "string_too_short",
        "string_too_long",
        "decimal_parsing",
        "date_parsing",
        "datetime_parsing",
        "enum",
        "url_parsing",
        "json_invalid",
        "model_type",
        "union_tag_invalid",
        "value_error",
        "assertion_error",
    }
)
VALIDATION_OTHER: Final = "other"

# Top-level packages whose exception class names may be printed as ``module.qualname`` (no cloud or model vendor name).
FOREIGN_PACKAGES_OK: Final = frozenset(sys.stdlib_module_names) | frozenset(
    {"pydantic", "pydantic_core", "pydantic_settings", "psycopg", "yaml", "markdown_it"}
)

_P = "hadavin_sdk."
# ``"module:Qualname"`` -> code. A subclass not listed takes its nearest listed base (method resolution order).
OWN_CODES: Final[Mapping[str, Code]] = MappingProxyType(
    {
        _P + "errors:ConfigError": Code.config_invalid,
        _P + "config:_RenamedStage": Code.config_invalid,
        _P + "k1b.bundle:BundleError": Code.config_invalid,
        # A shipped SQL file with an unclosed quote, comment or `$` body is a defect in this package's own data, not an operator
        # mistake. Nothing at run time raises it today (a dev/CI tool does); the row is required so that an own class never falls
        # back to its ValueError base. The closed list has no better fit: `config_invalid` (operator input), `validation_failed`
        # (a pydantic model) and `foreign_exception` (not ours) are wrong.
        _P + "store.migration_numbers:SqlReadError": Code.internal_bug,
        _P + "llm.fake:UnknownRecording": Code.config_invalid,
        _P + "store.protocol:StoreUnavailable": Code.store_unavailable,
        _P + "store.protocol:StaleState": Code.store_conflict,
        _P + "store.protocol:NotFound": Code.store_conflict,
        _P + "runtime.runs:IllegalTransition": Code.store_conflict,
        _P + "audit.protocol:DuplicateEvent": Code.store_conflict,
        _P + "audit.anchors:AnchorConflict": Code.store_conflict,
        _P + "llm.protocol:ProviderError": Code.provider_http,
        _P + "approvals.slack_channel:SlackError": Code.provider_http,
        _P + "sources:SourceError": Code.provider_http,
        _P + "actions.secrets_vault:VaultError": Code.provider_http,
        _P + "llm.protocol:ProviderExhausted": Code.provider_exhausted,
        _P + "audit.protocol:AuditUnavailable": Code.audit_unavailable,
        _P + "guard.egress:EgressRefused": Code.egress_refused,
        _P + "runtime.agent_loop:Unqualified": Code.unqualified,
        # nearest fit: a caller-chosen argument; not a pydantic model (so not validation_failed), not a gate state (so not unqualified)
        _P + "runtime.agent_loop:InvalidRunId": Code.config_invalid,
        # A shipped SQL file with an unclosed quote, comment or `$` body is a defect in this package's own data, not an operator mistake
        # (nothing at run time raises it today; a dev/CI tool does). The row is required so that an own class never falls back to its
        # ValueError base. `config_invalid` (operator input), `validation_failed` (a pydantic model) and `foreign_exception` are wrong fits.
        _P + "store.migration_numbers:SqlReadError": Code.internal_bug,
        _P + "k1b.loop:CallTimeout": Code.timeout,
        _P + "tools:ToolRefused": Code.tool_refused,
        _P + "guard.runmap:RedactionError": Code.scan_failed,
        _P + "guard.runmap:InputTooLarge": Code.scan_failed,
        _P + "guard.runmap:TooDeep": Code.scan_failed,
        _P + "guard.textnorm:TextnormError": Code.scan_failed,
    }
)


# --- provider failure facts: how a checked HTTP status and a checked error type choose a code ---------------------------
# 408 is an extension of design D6 (a request timeout); 500 to 599 are all server errors.
STATUS_ERROR_TYPE: Final[Mapping[int, ProviderErrorType]] = MappingProxyType(
    {
        429: ProviderErrorType.rate_limit,
        401: ProviderErrorType.authentication,
        403: ProviderErrorType.permission,
        400: ProviderErrorType.invalid_request,
        404: ProviderErrorType.invalid_request,
        422: ProviderErrorType.invalid_request,
        408: ProviderErrorType.timeout,
        **{n: ProviderErrorType.server_error for n in range(500, 600)},
    }
)
# The statuses that choose a code on a plain ``ProviderError``; any other valid status gives ``provider_http``.
CODED_STATUSES: Final = frozenset({400, 401, 403, 404, 422, 429})
# All 12 error types; a type that is not a problem with the caller's request or key is a plain ``provider_http``.
ERROR_TYPE_CODE: Final[Mapping[ProviderErrorType, Code]] = MappingProxyType(
    {
        ProviderErrorType.rate_limit: Code.provider_rate_limit,
        ProviderErrorType.throttled: Code.provider_rate_limit,
        ProviderErrorType.quota: Code.provider_rate_limit,
        ProviderErrorType.authentication: Code.provider_auth,
        ProviderErrorType.permission: Code.provider_auth,
        ProviderErrorType.invalid_request: Code.provider_invalid_request,
        ProviderErrorType.not_found: Code.provider_invalid_request,
        ProviderErrorType.timeout: Code.provider_timeout,
        ProviderErrorType.overloaded: Code.provider_http,
        ProviderErrorType.server_error: Code.provider_http,
        ProviderErrorType.connection: Code.provider_http,
        ProviderErrorType.other: Code.provider_http,
    }
)
# The two request-id shapes a provider reply may carry. Always used through ``re.fullmatch``; the keys are neutral names.
REQUEST_ID_SHAPES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "prefixed": r"req_[A-Za-z0-9]{8,36}",
        "uuid": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
    }
)
