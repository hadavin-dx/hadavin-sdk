"""`ConfigUrl`: the type of every settings field that holds a URL or an address (`base_url`, `address`,
`endpoint_url`, `account_url`, `vault_url`, `key_id`, `api_base`, `api_url`). One check for all of them, so a login
(`user:secret@host`) or a look-alike host written in a configuration file is refused at load with a fixed sentence,
whichever field it sits in. Imports pydantic and the two standard-library-only leaves `errors` and `safe_url`."""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator

from hadavin_sdk.errors import ConfigValueError
from hadavin_sdk.safe_url import NOT_A_URL, InvalidUrl, UrlHasLogin, config_urlsplit


def checked_url(value: str) -> str:
    """The value itself, or a `ConfigValueError` whose sentence never holds the value."""
    try:
        config_urlsplit(value)
    except UrlHasLogin:
        raise ConfigValueError("a URL must not contain a login") from None
    except InvalidUrl:
        raise ConfigValueError(f"{NOT_A_URL} (plain ASCII host, no percent sign)") from None
    return value


ConfigUrl = Annotated[str, AfterValidator(checked_url)]
