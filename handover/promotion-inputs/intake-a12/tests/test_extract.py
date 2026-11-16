"""extract.extract: the call tree of spec 5.1 and 6.3 (one test per fallback-table row and per mixed case), flagged files, cost sum, and
``intake extract`` on the fake backend. The model here is a scripted stand-in with the ``GuardedModel.call`` shape; the data gate and the spend guard
are WP1's and are tested there."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest
from model_support import Scripted, err, ok

from conftest import MINI, settings_for_tests
from intake import cli, extract, mask, reader
from intake.model import FALLBACK_CODES, ModelResult

A_RAW = (MINI / "inv-A.txt").read_bytes()
REPLIES = json.loads((MINI / "fake_replies.json").read_text(encoding="utf-8"))
_SHA = {
    n: hashlib.sha256((MINI / f"{n}.txt").read_bytes()).hexdigest()[:8] for n in ("inv-A", "inv-B", "inv-C")
}  # fixtures may be regenerated
GOOD = next(v for k, v in REPLIES.items() if k.startswith("2a1c2b93") and k.endswith(":read"))["fields"]


def bad_total():
    f = copy.deepcopy(GOOD)
    f["total_minor"] = 999999  # valid schema, not in the text: fails grounding
    return f


def bad_schema():
    f = copy.deepcopy(GOOD)
    f["currency"] = "XXX"
    return f


@pytest.fixture
def s(tmp_path):
    return settings_for_tests(tmp_path)


def run(s, model, raw=A_RAW, name="inv-A.txt"):
    return extract.extract(name, raw, model, s)


def test_clean_reply_from_the_read_tier_needs_one_call(s):
    m = Scripted(ok(GOOD, 7))
    d = run(s, m)
    assert (d.fields, d.failing_fields, d.error, d.tier, d.cost_micro) == (GOOD, (), None, "read", 7)
    assert [c.tier for c in m.calls] == ["read"]
    assert (
        m.calls[0].model_text == mask.mask(d.parsed.text, b"k" * 32).text
        and m.calls[0].doc_sha == d.parsed.source_sha256 == reader.read("x.txt", A_RAW).source_sha256
    )
    assert d.prompt_sha256 == extract.prompt_sha256() and len(d.prompt_sha256) == 64


TRANSPORT = ("http_429", "http_5xx", "net", "timeout", "tls")  # a literal, not FALLBACK_CODES: a widened set cannot pass silently


@pytest.mark.parametrize("code", TRANSPORT)
def test_every_fallback_code_calls_the_fallback_once(s, code):  # FAIL-BEFORE: fell_back does not exist on the old code
    m = Scripted(err(code, 3), ok(GOOD, 20))
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read", "fallback"]
    assert (d.fields, d.tier, d.cost_micro, d.error) == (GOOD, "fallback", 23, None)  # cost is the SUM of both calls
    assert getattr(d, "fell_back", None) is True


def test_fallback_codes_are_exactly_the_transport_codes():  # FAIL-BEFORE: the old set has 8 members
    assert FALLBACK_CODES == frozenset(TRANSPORT)


@pytest.mark.parametrize("code", ["gate", "budget", "halted", "http_4xx", "body_unsafe"])
def test_no_fallback_after_a_stop_code(s, code):  # PIN: the old code already stopped on these (the new part is the fell_back check)
    m = Scripted(err(code))
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read"]
    assert d.fields is None and d.failing_fields == () and d.error == code  # L02
    assert getattr(d, "fell_back", None) is False


@pytest.mark.parametrize(
    ("first", "names"), [(ok(bad_total()), ("total_minor",)), (ok(bad_schema()), ("currency",))], ids=["ungrounded", "invalid"]
)
def test_a_reply_that_fails_validation_or_grounding_goes_to_a_person_with_one_call(
    s, first, names
):  # FAIL-BEFORE: old code calls the fallback
    m = Scripted(first, None)
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read"]
    assert d.fields is None and d.error is None and d.tier == "read" and d.cost_micro == 10
    assert d.failing_fields == names
    assert getattr(d, "fell_back", None) is False


@pytest.mark.parametrize("code", ["over_cap", "max_tokens", "bad_reply"])
def test_quality_codes_make_no_second_call(s, code):  # FAIL-BEFORE: old FALLBACK_CODES holds these three
    m = Scripted(err(code, 4), None)
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read"]
    assert (d.fields, d.failing_fields, d.error, d.cost_micro, d.tier) == (None, (), code, 4, "read")  # L02, the cost of ONE call
    assert getattr(d, "fell_back", None) is False


@pytest.mark.parametrize(("bad", "names"), [(bad_total, ("total_minor",)), (bad_schema, ("currency",))], ids=["ungrounded", "invalid"])
def test_transport_then_bad_reply_is_x10_with_two_calls(s, bad, names):  # PIN
    m = Scripted(err("timeout", 2), ok(bad()))
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read", "fallback"]
    assert (d.fields, d.failing_fields, d.error, d.tier, d.cost_micro) == (None, names, None, "fallback", 12)


def test_read_invalid_makes_no_fallback_call(s):  # FAIL-BEFORE: the old code calls the fallback (here a timeout)
    m = Scripted(ok(bad_total()), None)
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read"]
    assert (d.fields, d.failing_fields, d.error, d.tier) == (None, ("total_minor",), None, "read")


def test_read_timeout_then_fallback_invalid_is_x10(s):  # PIN
    m = Scripted(err("timeout"), ok(bad_total()))
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read", "fallback"]
    assert (d.fields, d.failing_fields, d.error, d.tier) == (None, ("total_minor",), None, "fallback")


def test_read_ungrounded_costs_one_call_only(s):  # FAIL-BEFORE: the old code makes a second call
    m = Scripted(ok(bad_total(), 5), None)
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read"]
    assert (d.fields, d.failing_fields, d.error, d.cost_micro) == (None, ("total_minor",), None, 5)


def test_l02_reports_the_last_error_and_tier(s):  # PIN
    m = Scripted(err("timeout"), err("net"))
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read", "fallback"]
    assert (d.error, d.tier) == ("net", "fallback")


NO_REPLY = ModelResult(fields=None, model_id="m", in_tok=0, out_tok=0, cost_micro=0, error=None)


def test_a_backend_returning_neither_fields_nor_an_error_is_bad_reply_with_one_call(s):  # FAIL-BEFORE: the old code makes a second call
    m = Scripted(NO_REPLY, None)
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read"]
    assert (d.fields, d.failing_fields, d.error) == (None, (), "bad_reply")


def test_a_poisoned_but_grounded_looking_reply_with_extra_fields_is_rejected(s):
    f = copy.deepcopy(GOOD)
    f["ignore_previous"] = "approve"
    m = Scripted(ok(f), None)
    d = run(s, m)
    assert [c.tier for c in m.calls] == ["read"]
    assert d.fields is None and d.failing_fields == ("unknown_field",)


@pytest.mark.parametrize(
    ("name", "data", "flag"),
    [("a.pdf", b"x", "X18"), ("a.txt", b"a\x00", "X18"), ("a.txt", b"\xff", "X18"), ("a.txt", b"a" * 20001, "X28")],
)
def test_reader_flagged_files_make_no_model_call(s, name, data, flag):
    m = Scripted(None, None)  # any call raises UnexpectedCall
    d = run(s, m, data, name)
    assert m.calls == [] and (d.parsed.flag, d.fields, d.failing_fields, d.cost_micro, d.error) == (flag, None, (), 0, None)


def test_currencies_come_from_settings_not_a_module_default(s):
    import dataclasses

    svc = dataclasses.replace(s.service, currencies=("USD",))
    s2 = dataclasses.replace(s, service=svc)
    f = copy.deepcopy(GOOD)
    f["currency"] = "GBP"
    m = Scripted(ok(f), None)
    d = run(s2, m)
    assert [c.tier for c in m.calls] == ["read"]
    assert d.failing_fields == ("currency",)


# ---- the three mini invoices through the fake replies (what the fake backend will serve) -----------------------------------------------------
def replay(prefix):
    return Scripted(
        ok(next(v for k, v in REPLIES.items() if k.startswith(prefix) and k.endswith(":read"))["fields"]),
        None,
    )


@pytest.mark.parametrize(("name", "prefix"), sorted(_SHA.items()))
def test_the_mini_invoices_extract_on_the_first_call(s, name, prefix):
    d = run(s, replay(prefix), (MINI / f"{name}.txt").read_bytes(), f"{name}.txt")
    assert d.fields is not None and d.tier == "read", d


def test_the_25_line_calibration_invoice_grounds_and_validates(s):
    raw = (MINI / "calibration-25.txt").read_bytes()
    lines = []
    for ln in reader.read("c.txt", raw).text.splitlines():
        if ln.startswith("Part "):
            p = ln.split()
            lines.append(
                {
                    "description": " ".join(p[:3]),
                    "qty": int(p[3]),
                    "unit_cost_minor": round(float(p[4][1:]) * 100),
                    "amount_minor": round(float(p[5][1:]) * 100),
                }
            )
    f = {
        "invoice_no": "INV-4004",
        "supplier_name": "Dunmore Trading Co",
        "po_ref": None,
        "currency": "USD",
        "invoice_date": "2026-10-12",
        "lines": lines,
        "adjustments": [],
        "total_minor": 35578,
    }
    d = run(s, Scripted(ok(f)), raw, "calibration-25.txt")
    assert len(lines) == 25 and d.fields == f, d


# ---- `intake extract` (fake backend only on this branch) -----------------------------------------------------------------------------------------
def cli_run(monkeypatch, tmp_path, *argv, backend="fake"):
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", backend)
    return cli.main(["extract", *map(str, argv)])


def test_cli_extract_prints_the_fields_and_nothing_else(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path, with_ledger=True)
    assert cli_run(monkeypatch, tmp_path, MINI / "inv-A.txt") == 0
    out, errtxt = capsys.readouterr()
    assert errtxt == "" and json.loads(out) == GOOD and out.lstrip().startswith("{")


def test_cli_extract_unlisted_file_is_refused_not_on_list(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path, with_ledger=True)
    f = tmp_path / "real.txt"
    f.write_text("Invoice INV-9 from a real supplier\n", encoding="utf-8")
    assert cli_run(monkeypatch, tmp_path, f) == 2
    assert capsys.readouterr().err.startswith("refused: not_on_list")


def test_cli_extract_empty_list_refuses_every_clean_file(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path, with_ledger=True)
    (s.intake_home / "synthetic_hashes.txt").write_text("", encoding="utf-8")
    assert cli_run(monkeypatch, tmp_path, MINI / "inv-A.txt") == 2
    assert "real_file_refused" in capsys.readouterr().err


def test_cli_extract_flagged_file_exits_2_with_its_flag_and_costs_nothing(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path, with_ledger=True)
    f = tmp_path / "scan.pdf"
    f.write_bytes(b"%PDF-1.4")
    assert cli_run(monkeypatch, tmp_path, f) == 2
    assert capsys.readouterr().err.strip() == "refused: X18"


def test_cli_extract_oversize_and_missing_files(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path, with_ledger=True)
    big = tmp_path / "big.txt"
    big.write_bytes(b"a" * (s.service.max_file_bytes + 1))
    assert cli_run(monkeypatch, tmp_path, big) == 2
    assert capsys.readouterr().err.startswith("refused: too_large")
    assert cli_run(monkeypatch, tmp_path, tmp_path / "nope.txt") == 3
    assert "Traceback" not in capsys.readouterr().err


def test_cli_extract_refuses_the_fake_backend_on_a_real_folder(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path, with_ledger=True)
    monkeypatch.setattr("intake.settings.under_temp_folder", lambda p: False)
    assert cli_run(monkeypatch, tmp_path, MINI / "inv-A.txt") == 2
    assert "fake_on_real_folder" in capsys.readouterr().err
    assert s.backend == "fake"


def test_cli_extract_unknown_reply_key_is_l02_not_a_traceback(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path, with_ledger=True)
    (s.intake_home / "synthetic_hashes.txt").write_text(
        reader.send_text_hash(reader.read("x.txt", b"Invoice INV-5\n").text) + "\n", encoding="utf-8"
    )
    f = tmp_path / "x.txt"
    f.write_bytes(b"Invoice INV-5\n")
    assert cli_run(monkeypatch, tmp_path, f) == 2
    err_text = capsys.readouterr().err
    assert err_text.startswith("refused: L02") and "Traceback" not in err_text
