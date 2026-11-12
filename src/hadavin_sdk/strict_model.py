"""The base class of the models that code builds straight from one section of a file (backend settings, the
Kubernetes settings): round 12, Issue 4 of Q8a-1.

pydantic's own "extra forbidden" error puts the unknown key in the place line of its text. A mistyped or misplaced
key can be a secret (a paste that landed in the key position). The loader hides the key (`<unknown key>`, see
`errors.error_where`) for the whole file, but these models are also built directly, and then pydantic's text is what
a person sees. So they refuse an unknown key here, once: the error says the position of each unknown key (counted from
1, not counting `kind`) and the setting names of the model, which are written in code. The typed key is never shown, in the message, in the
place line (`loc`) or in the refused input (`hide_input_in_errors`). The models of the whole file (`Config` and its
parts, the agent registry, the tool manifest) are built only by the loader and keep its `<unknown key>` text: a
position inside the whole file is not known to a part, and a refusal here would hide the other problems of the file."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from hadavin_sdk.errors import ConfigValueError
from hadavin_sdk.hidden_input import HiddenInputModel


class StrictConfigModel(
    HiddenInputModel, BaseModel
):  # BaseModel is named too so the linter knows this is a pydantic model
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="before")
    @classmethod
    def _unknown_settings_are_not_named(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        known = set(cls.model_fields)
        # counted among the settings, not the `kind` word (the loader hands the model the keys without it)
        unknown = [
            i for i, key in enumerate((k for k in data if k != "kind"), start=1) if key not in known
        ]
        if not unknown:
            return data
        raise ConfigValueError(
            f"unknown setting at position {', '.join(str(i) for i in unknown)} (name not shown); "
            f"the settings here are: {', '.join(sorted(known))}"
        )
