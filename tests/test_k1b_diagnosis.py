"""K1b phase 2: strict diagnosis parse and the Cause List."""

import json

import pytest

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.k1b.causelist import load_cause_list
from hadavin_sdk.k1b.diagnosis import DIAGNOSIS_SCHEMA, parse_diagnosis, parse_diagnosis_text

C = {"service": "checkout", "fault_type": "bad_deploy", "evidence_ids": ["logs/001.jsonl#3"]}
GOOD = [
    {"causes": [C]},
    {"causes": [C], "not_sure": False},
    {"causes": [C], "reason": "why"},
    {"causes": [], "not_sure": True},
    {"not_sure": True},  # causes omitted: a valid abstain
    {"causes": [C, C, C, C, C]},  # more than 3 is valid
]
BAD = [
    {"causes": [C], "not_sure": True},  # both
    {"causes": []},  # neither
    {"causes": [], "not_sure": False},
    {"causes": [], "not_sure": "true"},  # wrong type
    {"causes": [C], "not_sure": "false"},
    {"causes": [C], "extra": 1},  # extra key
    {"causes": [{**C, "extra": 1}]},
    {"causes": [{**C, "evidence_ids": []}]},  # empty ids
    {"causes": [{**C, "evidence_ids": [3]}]},
    {"causes": [{"service": "x", "fault_type": "y"}]},  # no ids
    {"not_sure": False},  # causes missing without not_sure true
    {"reason": "no cause"},  # neither form
    {"not_sure": "true"},  # causes missing, wrong type
    {"not_sure": True, "extra": 1},  # omitted causes keep every other strictness
    {"not_sure": True, "causes": None},
    {"causes": "none", "not_sure": True},
    {"causes": [C], "reason": 5},
]


@pytest.mark.parametrize("obj", GOOD)
def test_good_forms_parse_from_dict_and_text(obj):
    assert parse_diagnosis(obj) is not None
    assert parse_diagnosis_text(json.dumps(obj)) is not None


@pytest.mark.parametrize("obj", BAD)
def test_bad_forms_are_unreadable(obj):
    assert parse_diagnosis(obj) is None
    assert parse_diagnosis_text(json.dumps(obj)) is None


@pytest.mark.parametrize(
    "text",
    [
        "```json\n" + json.dumps({"causes": [C]}) + "\n```",  # fenced
        "Here: " + json.dumps({"causes": [C]}),  # prose before
        json.dumps({"causes": [C]}) + " done",  # prose after
        '{"causes": [], "not_sure": true, "not_sure": true}',  # duplicate key
        '{"causes": [], "not_sure": true, "reason": NaN}',
        "[]",
        "",
        "null",
    ],
)
def test_text_must_be_exactly_one_object(text):
    assert parse_diagnosis_text(text) is None


def test_non_dict_inputs():
    for v in (None, [], "x", 3):
        assert parse_diagnosis(v) is None


def test_only_first_three_are_scored_and_duplicates_keep_rank():
    other = {**C, "service": "db"}
    d = parse_diagnosis({"causes": [C, C, other, {**C, "service": "q"}]})
    assert [c.service for c in d.scored] == ["checkout", "checkout", "db"]


def test_schema_has_no_max_items_and_forbids_extras():
    assert DIAGNOSIS_SCHEMA["additionalProperties"] is False
    assert "maxItems" not in json.dumps(DIAGNOSIS_SCHEMA)


def _write(d, services, faults, enc="utf-8"):
    (d / "services.json").write_bytes(json.dumps(services).encode(enc))
    (d / "fault_types.json").write_bytes(json.dumps(faults).encode(enc))


def test_cause_list_loads_hashes_and_matches_nfc(tmp_path):
    _write(tmp_path, ["café", "db"], ["bad_deploy"])
    cl = load_cause_list(tmp_path)
    assert cl.contains("café ", "bad_deploy")  # NFD plus space equals NFC entry
    assert not cl.contains("CAFÉ", "bad_deploy")  # case sensitive
    assert not cl.contains("db", "other")
    assert len(cl.services_sha256) == 64 and cl.services_sha256 != cl.fault_types_sha256


def test_cause_list_accepts_bom(tmp_path):
    _write(tmp_path, ["a"], ["f"], enc="utf-8-sig")
    assert load_cause_list(tmp_path).contains("a", "f")


@pytest.mark.parametrize(
    ("services", "faults"),
    [
        ([], ["f"]),
        (["a", "a"], ["f"]),
        (["a", " a"], ["f"]),  # duplicate after strip
        (["a"], [f"f{i}" for i in range(16)]),  # 16 fault types
        ([f"s{i}" for i in range(201)], ["f"]),
        (["a", 3], ["f"]),
        (["  "], ["f"]),
        ("a", ["f"]),
        (["a"], []),
    ],
)
def test_cause_list_violations_refuse(tmp_path, services, faults):
    _write(tmp_path, services, faults)
    with pytest.raises(ConfigError):
        load_cause_list(tmp_path)


def test_cause_list_limits_edge_ok(tmp_path):
    _write(tmp_path, [f"s{i}" for i in range(200)], [f"f{i}" for i in range(15)])
    assert len(load_cause_list(tmp_path).services) == 200


def test_cause_list_missing_or_bad_json(tmp_path):
    with pytest.raises(ConfigError):
        load_cause_list(tmp_path)
    (tmp_path / "services.json").write_text("{nope", encoding="utf-8")
    (tmp_path / "fault_types.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_cause_list(tmp_path)


def test_empty_strings_and_null_reason_are_unreadable():
    assert parse_diagnosis({"causes": [{**C, "service": ""}]}) is None
    assert parse_diagnosis({"causes": [{**C, "evidence_ids": [""]}]}) is None
    assert parse_diagnosis({"causes": [C], "reason": None}) is None


def test_cause_list_deep_nesting_and_surrogate(tmp_path):
    (tmp_path / "fault_types.json").write_text('["f"]', encoding="utf-8")
    (tmp_path / "services.json").write_text("[" * 5000, encoding="utf-8")
    with pytest.raises(ConfigError):
        load_cause_list(tmp_path)
    (tmp_path / "services.json").write_text('["' + chr(92) + 'ud800"]', encoding="utf-8")
    with pytest.raises(ConfigError):
        load_cause_list(tmp_path)


# The real Sonnet 5.5 smoke run (2026-11-01): a no_evidence incident got this reply text (synthetic wording, same
# shape): a bare JSON object with not_sure and a reason, no `causes` key. It was a correct abstain.
REAL_SHAPE = (
    '{"not_sure": true, "reason": "The snapshot does not show a cause. The gateway looks healthy and the '
    'logs name no dependency. A downstream service may be the cause, but the snapshot has nothing on it."}'
)


def test_real_omitted_causes_abstain_parses_as_not_sure_from_text_and_tool_input():
    d = parse_diagnosis_text(REAL_SHAPE)
    assert d is not None and d.not_sure and d.causes == [] and d.reason.startswith("The snapshot")
    assert parse_diagnosis(json.loads(REAL_SHAPE)) == d


@pytest.mark.parametrize(
    "text",
    [
        "```json\n" + REAL_SHAPE + "\n```",  # fenced
        "Here is my answer: " + REAL_SHAPE,  # surrounded text
        '{"not_sure": true, "not_sure": true}',  # duplicate key
        '{"not_sure": true, "reason": NaN}',
        '{"not_sure": true, "reason": 5}',
        '{"not_sure": 1}',
    ],
)
def test_omitted_causes_keeps_every_other_strictness(text):
    assert parse_diagnosis_text(text) is None


def test_schema_and_prompt_tell_the_model_causes_may_be_left_out():
    from hadavin_sdk.k1b import loop
    from hadavin_sdk.k1b.diagnosis import DIAGNOSIS_SCHEMA
    from hadavin_sdk.k1b.tools import SUBMIT, TOOL_SPECS

    assert "required" not in DIAGNOSIS_SCHEMA
    spec = next(t for t in TOOL_SPECS if t["name"] == SUBMIT)
    assert "no causes" in spec["description"] and "causes may be left out" in loop.SYSTEM_PROMPT
