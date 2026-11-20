"""N2 (xr-abc-lead-1): AuditEvent identifier fields are bounded and free of prose, so a long run id is refused at
construction (not by the btree index with 54000 at write time)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hadavin_sdk.models import AuditEvent

BASE = {"run_id": "run-1", "domain": "d", "operation": "o", "principal": "p", "source": "s"}
TOKENS = ("principal", "object_ref", "result", "rule_id", "error_code")


def _event(**kw):
    return AuditEvent(**{**BASE, **kw})


@pytest.mark.parametrize("field", ("run_id", "domain", "operation", "source", *TOKENS))
def test_a_value_over_the_limit_is_refused_at_construction(field):
    with pytest.raises(ValidationError):
        _event(**{field: "a" * 129})
    assert _event(**{field: "a" * 128})  # the limit itself passes


@pytest.mark.parametrize("field", TOKENS)
@pytest.mark.parametrize(
    "bad", ["two words", "line\nbreak", "tab\t", "semi;colon", "quote'", 'q"', "<x>"]
)
def test_prose_and_control_characters_are_refused(field, bad):
    with pytest.raises(ValidationError):
        _event(**{field: bad})


@pytest.mark.parametrize("field", TOKENS)
@pytest.mark.parametrize(
    "good",
    [
        "system:tick",
        "alice@example.com",
        "run-0123abcd",
        "approval_missing",
        "a/b.c-d+e=f#g~h",
        "booked",
    ],
)
def test_the_codes_callers_use_pass(field, good):
    assert getattr(_event(**{field: good}), field) == good


def test_a_run_id_of_the_shape_the_runtime_makes_passes():
    assert _event(run_id="run-" + "0" * 32).run_id == "run-" + "0" * 32


def test_audit_ref_keeps_a_fitting_value_and_hashes_the_rest():
    from hadavin_sdk.models import audit_ref

    assert audit_ref(None) is None
    assert audit_ref("run-1:1,run-1:2") == "run-1:1,run-1:2"
    long = ",".join(f"run-{'0' * 32}:{i}" for i in range(6))
    for text in (long, "has space", "x\ny"):
        ref = audit_ref(text)
        assert ref.startswith("sha256:") and _event(object_ref=ref)
