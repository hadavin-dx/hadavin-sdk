"""Typed errors. Every public entry point ends in a deny/verdict or one of these, never a raw KeyError/TypeError (review class: typed Malformed)."""


class DealDeskError(Exception):
    pass


class Malformed(DealDeskError, ValueError):
    """An input or a port record is structurally wrong. Fail closed; nothing is computed."""


class InputError(Malformed):
    """R-DEALDESK-001: a tool input is malformed (bool, float, negative, zero seats, out of range, missing key)."""


class MatrixError(Malformed):
    """R-DEALDESK-040: the matrix or policy is unusable; every decision is a deny."""


class CrossTenantAccess(DealDeskError, PermissionError):
    """R-DEALDESK-094: a key, id or record of another tenant was addressed."""


class NotPermitted(DealDeskError, PermissionError):
    """The calling identity does not hold the action (identities.py)."""


class ConfigError(DealDeskError, ValueError):
    """A configuration or key set is unusable (fails loudly at construction, never open)."""


class ReadThrottled(DealDeskError):
    """The read-only role exceeded its request-rate cap (blast radius): the caller retries later; production is never slowed."""
