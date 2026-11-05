"""Hand-back outcome log: what a person did with what Jagrat said, kept for the pilot numbers.

After an incident the approver records whether the diagnosis and the proposed action were right, wrong or unclear
to them. The label is an outcome record, not a credential: who decided comes from the core approval decision (its
principal), so nothing here is signed. `record` appends one audit row through the `log` the caller passes (any object
with `append(incident_id, kind, body)` and `entries(kinds=...)`); mapping those rows onto the export is the exporter's
job (design 4.5.2).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Judgement = Literal["right", "wrong", "unsure"]
KIND = "label"


class Label(BaseModel):
    incident_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    approver: str = Field(min_length=1, max_length=64)
    diagnosis: Judgement
    action: Judgement
    note: str = Field(default="", max_length=500)
    at: datetime


def make(
    *,
    incident_id: str,
    approver: str,
    diagnosis: str,
    action: str,
    note: str = "",
    now: datetime | None = None,
) -> Label:
    return Label(
        incident_id=incident_id,
        approver=approver,
        diagnosis=diagnosis,
        action=action,
        note=note,
        at=now or datetime.now(UTC),
    )


def record(log: Any, label: Label) -> list[str]:
    """Append the label. An invalid label never gets here (the model refuses it); returns the reasons it was not
    recorded (none today: a write failure raises)."""
    log.append(label.incident_id, KIND, label.model_dump(mode="json"))
    return []


def export(log: Any) -> list[dict]:
    """Every recorded label, oldest first."""
    return [e["body"] for e in log.entries(kinds=(KIND,))]
