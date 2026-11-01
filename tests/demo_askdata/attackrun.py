"""How one corpus attack is judged, shared by the corpus test and the mutation test."""

from __future__ import annotations

from contextlib import nullcontext
from unittest import mock

import askdata.validate as validate_module
from askdata.validate import Rejected, validate

from .corpus import Attack


def _drifting_generator():
    """A generator with a bug: every regeneration appends `+ 0`, so the text never settles (a stand-in for the
    generator disagreement V11 exists for; no real sqlglot 30.24 case was found in the fuzz runs)."""
    real = validate_module._gen

    def drift(node):
        return real(node).replace("SELECT 1", "SELECT 1 + 0", 1)

    return mock.patch.object(validate_module, "_gen", drift)


def outcome(attack: Attack) -> str:
    """The rule id that refused the attack, or 'ACCEPTED', or 'CRASH <exception>'."""
    with _drifting_generator() if attack.category == "reparse-identity" else nullcontext():
        try:
            validate(attack.sql)
        except Rejected as err:
            return err.rule
        except Exception as err:  # noqa: BLE001  # the verdict must be a Rejected; anything else is reported
            return f"CRASH {type(err).__name__}"
        return "ACCEPTED"
