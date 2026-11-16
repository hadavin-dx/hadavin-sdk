"""Every code named in the product code is listed in ``intake.codes``. An AST scan: a first string argument of Refused, ConfigError or SecretError,
or a string assigned to an ``error=`` / ``code=`` keyword, must be a member of CODES."""

from __future__ import annotations

import ast
from pathlib import Path

from conftest import ROOT
from intake import codes, flags

SRC = ROOT / "src" / "intake"


def used_codes(source: str) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
            if name in codes.CODE_RAISERS and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                out.append((node.args[0].value, node.lineno))
            for kw in node.keywords:
                if kw.arg in ("error", "code") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    out.append((kw.value.value, node.lineno))
    return out


def unlisted(source: str) -> list[str]:
    return [c for c, _ in used_codes(source) if c not in codes.CODES]


def test_no_code_is_used_but_not_listed():
    bad = []
    for p in sorted(SRC.rglob("*.py")):
        if "core_copy" in p.parts:
            continue
        bad += [(p.name, c) for c in unlisted(p.read_text(encoding="utf-8"))]
    assert not bad, bad


def test_the_scan_catches_an_unlisted_code():
    assert unlisted("raise Refused('made_up_code', 'x')") == ["made_up_code"]
    assert unlisted("raise SecretError('key_short')") == []
    assert unlisted("ModelResult(error='nope')") == ["nope"]
    assert unlisted("x = decisions.Refused('stale_content', 'y')") == []
    assert unlisted("raise ConfigError(code='zzz')") == ["zzz"]


def test_every_code_the_spec_names_is_listed():
    spec = (
        "gate budget halted timeout net tls http_429 http_4xx http_5xx over_cap bad_reply max_tokens key_file_missing key_name_missing key_empty "
        "key_malformed key_duplicate key_encoding key_short real_file_refused not_on_list owner_sentence_missing prices_missing "
        "provider_limit_missing ledger_missing ledger_inconsistent budget_total budget_halted cap_too_small_for_worst_case settle_failed "
        "fake_on_real_folder too_large bad_name outside_inbox invalid_reason already_decided stale_content purge_refused row_id_conflict "
        "approval_mismatch not_found kill_switch already_exported not_approved not_approvable sink_locked not_configured"
    ).split()
    assert not [c for c in spec if c not in codes.CODES]


def test_codes_are_lowercase_identifiers_and_never_flag_codes():
    assert all(c.islower() or "_" in c or c[0].isalpha() for c in codes.CODES)
    assert all(c == c.lower() for c in codes.CODES)
    assert not set(codes.CODES) & {c.lower() for c in flags.FLAGS}


def test_exception_types():
    e = codes.SecretError("key_short", "NAME is too short")
    assert isinstance(e, codes.Refused) and e.code == "key_short" and "key_short" in str(e)
    assert not isinstance(codes.ConfigError("bad_config"), codes.Refused)
    assert Path(codes.__file__).is_file()


def test_wall_codes_are_pinned_and_listed():
    wall = frozenset({"budget_total", "budget_halted", "window_ended", "budget_day", "budget_run", "provider_limit", "transport_cooldown"})
    assert getattr(codes, "WALL_CODES", None) == wall
    assert wall <= codes.CODES and wall <= codes.GATE_BUDGET_CODES


def test_provider_limit_is_a_valid_model_error():
    from intake import budget, model

    assert "provider_limit" in codes.MODEL_ERRORS and "provider_limit" in codes.GATE_BUDGET_CODES
    assert model.ModelResult(None, "m", 0, 0, 0, "provider_limit").error == "provider_limit"
    assert "provider_limit" not in budget.BREAKER_CODES  # a spend wall is a halt of its own, not a breaker count
    assert "provider_limit" in model.NO_FALLBACK_CODES and not model.fallback_allowed("provider_limit")


def test_model_result_carries_the_new_usage_classes_with_zero_defaults():
    from intake import model

    r = model.ModelResult(None, None, 1, 1, 0, None)
    assert (getattr(r, "cache_write_tok", None), getattr(r, "cache_read_tok", None), getattr(r, "thinking_tok", None)) == (0, 0, 0)
