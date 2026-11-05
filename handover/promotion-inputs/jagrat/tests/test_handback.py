import pytest
from pydantic import ValidationError

from jagrat import handback


class Log:
    def __init__(self):
        self.rows = []

    def append(self, incident, kind, body):
        self.rows.append({"incident": incident, "kind": kind, "body": body})

    def entries(self, kinds):
        return [r for r in self.rows if r["kind"] in kinds]


def test_record_then_export_roundtrip_unsigned():
    log = Log()
    label = handback.make(
        incident_id="inc-1", approver="role:oncall", diagnosis="right", action="wrong", note="n"
    )
    assert handback.record(log, label) == []
    out = handback.export(log)
    assert len(out) == 1 and out[0]["action"] == "wrong" and "signature" not in out[0]


@pytest.mark.parametrize(
    "kw",
    [
        {"diagnosis": "maybe"},
        {"action": ""},
        {"incident_id": "../x"},
        {"note": "x" * 501},
        {"approver": ""},
    ],
)
def test_invalid_labels_are_refused(kw):
    base = {"incident_id": "inc-1", "approver": "a", "diagnosis": "right", "action": "right"}
    with pytest.raises(ValidationError):
        handback.make(**{**base, **kw})
