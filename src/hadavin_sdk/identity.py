"""Principals (``principals.yaml``): people and service identities, their rights and approver roles."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from hadavin_sdk.hidden_input import HiddenInputModel


class Principal(HiddenInputModel, BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    kind: Literal["person", "service"]
    rights: list[str] = []
    approver_of: list[str] = []
