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
    # Which agents this person may label: agent ids, or "*" for all. None = not stated: allowed in dev,
    # refused in pilot and prod (a labeller there is named). Separate from every other right.
    label_agents: list[str] | None = None
