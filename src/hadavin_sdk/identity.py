"""Principals (``principals.yaml``): people and service identities, their rights and approver roles."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

AdminRight = Literal["stop", "reset", "clear_override", "approve_label_import"]


class Principal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    kind: Literal["person", "service"]
    rights: list[str] = []
    approver_of: list[str] = []
    # Separate from action `rights`: what a person may do to the pilot itself, by a signed channel action. The CLI
    # records an asserted name only (it says so); signed actions and reviewed config PRs are the authority.
    admin_rights: list[AdminRight] = []
