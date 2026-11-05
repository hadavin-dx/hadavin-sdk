"""Errors shared by ``config`` and ``backends``, kept here so neither has to import the other."""


class ConfigError(ValueError):
    """The client config is invalid; the process must not start."""


class SwitchChanged(RuntimeError):
    """``Limits.reset(expect=...)``: the durable stop is not the one the caller wrote (someone stopped it since); it was NOT cleared."""
