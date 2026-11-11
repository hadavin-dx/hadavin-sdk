"""The one way a configured value is split into URL parts. A leaf module: it imports only the standard library, so
every other module (config, backends, app, tools, guard, llm) can use it at the top of the file.

Why it exists. `urllib.parse.urlsplit` raises a `ValueError` whose text holds the value it was given (for a host
that changes under NFKC into one with `/ ? # @ :` it quotes the whole host, a login included; a bad port is quoted
too). A configured URL can hold a pasted secret, so that text must never reach an error message, a log or the
terminal. `safe_urlsplit` turns every such error into the same fixed sentence and drops the cause. It also reads the
port once, inside the same guard, so a later `.port` on the result cannot raise a value-carrying error.
"""

from __future__ import annotations

from urllib.parse import SplitResult, urlsplit

NOT_A_URL = "not a valid URL"


class InvalidUrl(ValueError):
    """A configured value could not be read as a URL. The text is always `NOT_A_URL`, never the value."""


def safe_urlsplit(value: str) -> SplitResult:
    """`urlsplit(value)`, or `InvalidUrl` (a `ValueError` with a fixed sentence and no cause) when it cannot be read."""
    try:
        parts = urlsplit(value)
        parts.port  # noqa: B018 - read here, so an invalid port fails inside this guard (its text quotes the port)
    except ValueError:
        raise InvalidUrl(NOT_A_URL) from None
    return parts
