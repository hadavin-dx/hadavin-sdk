"""WP2a result review 1: M1 (settle_failed stops the process), m1 tier cap, m2 bounded regular-file read, m4 date/label/number weak points, m5 currency table
versus config, m6 non-ASCII digits and zero-width characters, m8 symlinked lock file, m9 consistent codes and prompt hash, allowlist stale entries."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys

import pytest

from conftest import MINI, ROOT, settings_for_tests
from intake import cli, extract, ground, inbox, lockfile, model, settings
from intake.codes import ConfigError
from intake.model import ModelResult

A_RAW = (MINI / "inv-A.txt").read_bytes()
REPLIES = json.loads((MINI / "fake_replies.json").read_text(encoding="utf-8"))
_A = hashlib.sha256(A_RAW).hexdigest()[:8]
GOOD = next(v for k, v in REPLIES.items() if k.startswith(_A) and k.endswith(":read"))["fields"]


class Raises:
    """A scripted model whose first call raises ``exc`` (what ``GuardedModel.call`` does when ``settle`` cannot write)."""

    def __init__(self, exc):
        self.exc, self.calls = exc, 0

    def call(self, req):
        self.calls += 1
        raise self.exc


# ---- M1: a settle failure stops everything ------------------------------------------------------------------------------------------------------
def test_settle_failed_propagates_out_of_extract_with_no_further_call(tmp_path):
    s = settings_for_tests(tmp_path)
    m = Raises(ConfigError("settle_failed", "the spend ledger could not write"))
    with pytest.raises(ConfigError) as e:
        extract.extract("inv-A.txt", A_RAW, m, s)
    assert e.value.code == "settle_failed" and m.calls == 1  # no fallback call, no cost guess


def test_cli_extract_exits_3_on_settle_failed_and_prints_no_traceback(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path, with_ledger=True)
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    m = Raises(ConfigError("settle_failed", "x"))
    monkeypatch.setattr(cli.model, "build_guarded", lambda s=None: m)
    assert cli.main(["extract", str(MINI / "inv-A.txt")]) == 3
    err = capsys.readouterr().err
    assert err.startswith("error: settle_failed") and "Traceback" not in err and m.calls == 1


def test_a_plain_exception_is_still_only_a_budget_refusal(tmp_path):
    s = settings_for_tests(tmp_path)
    m = Raises(RuntimeError("boom"))
    d = extract.extract("inv-A.txt", A_RAW, m, s)
    assert (d.error, m.calls) == ("budget", 1)


def test_no_other_broad_catch_in_product_code_wraps_a_model_call():
    """Sweep: every ``except Exception`` in src/intake is listed with its owner; a new one fails this test until it is reviewed for settle_failed."""
    import ast

    found = {}
    for p in sorted((ROOT / "src" / "intake").glob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        n = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler) and getattr(node.type, "id", "") == "Exception")
        if n:
            found[p.name] = n
    # extract.py: ConfigError is re-raised first; ground.py: pure text code; model.py: the guard itself (settle is in `finally`, ConfigError passes);
    # model_anthropic.py: network wrapper (diagnostics); settings.py: kill switch fails closed; exporter.py: ``_engaged`` fails closed on an unreadable
    # kill-switch policy (no model call inside the try, so settle_failed cannot be swallowed there)
    # inbox.py (WP6 6b, reviewed): 6 catches, NO model call inside any try (the model is called only in phase 2, ``pipeline.process``, outside them):
    # the worker start (no thread available), the worker body (hands the exception to the loop), the scan_partial attach, the per-file poison-pill
    # catch (classified by ``_fail``) and the two catches in the second look at a waiting file.
    # Earlier text: 2 catches, NO model call inside either try. (1) the per-file poison-pill catch in the file loop wraps only lstat, the
    # bounded read, the reader parse and the gate (a parser bug must refuse that one file, not stop the scan); ConfigError and Refused are re-raised or
    # handled before it, and the model is called later in pipeline.process, outside the try. (2) the catch around attaching ``scan_partial`` to an
    # exception that is being re-raised anyway.
    assert found == {
        "extract.py": 1,
        "ground.py": 2,
        "model.py": 3,
        "model_anthropic.py": 1,
        "settings.py": 1,
        "exporter.py": 1,
        "inbox.py": 6,
    }, found


# ---- m1: at most two calls --------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("tiers", [("read",) * 50, ("read", "read"), ("fallback",), ("read", "fallback", "read"), ()])
def test_the_tier_list_is_capped(tmp_path, tiers):
    s = settings_for_tests(tmp_path)
    m = Raises(RuntimeError("never called"))
    with pytest.raises(ValueError):
        extract.extract("inv-A.txt", A_RAW, m, s, tiers=tiers)
    assert m.calls == 0


# ---- m2: bounded, regular-file read -----------------------------------------------------------------------------------------------------------
def run_cli(monkeypatch, tmp_path, path):
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    return cli.main(["extract", str(path)])


def test_cli_extract_refuses_a_directory_and_reads_at_most_cap_plus_one(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path, with_ledger=True)
    assert (
        run_cli(monkeypatch, tmp_path, tmp_path) == 2 and "not_a_file" in capsys.readouterr().err
    )  # WP6 6b: a refusal (exit 2), not bad config
    cap = s.service.max_file_bytes
    (tmp_path / "exact.txt").write_bytes(b"a" * cap)
    (tmp_path / "over.txt").write_bytes(b"a" * (cap + 1))
    assert run_cli(monkeypatch, tmp_path, tmp_path / "over.txt") == 2 and "too_large" in capsys.readouterr().err
    assert "too_large" not in capsys.readouterr().err and inbox.read_plain_file(tmp_path / "exact.txt", cap) == b"a" * cap


@pytest.mark.skipif(sys.platform == "win32", reason="device files are POSIX")
def test_cli_extract_refuses_a_device_file(tmp_path, monkeypatch, capsys):
    settings_for_tests(tmp_path, with_ledger=True)
    assert run_cli(monkeypatch, tmp_path, "/dev/zero") == 2
    assert "not_a_file" in capsys.readouterr().err


def test_cli_has_exactly_one_file_probe():
    """WP6 6b: cli.py has no file probe at all (``inbox.read_plain_file`` is the one bounded reader, pinned in tests/test_scan.py)."""
    import ast

    tree = ast.parse((ROOT / "src" / "intake" / "cli.py").read_text(encoding="utf-8"))
    probes = {"stat", "open", "read_bytes", "read_text", "is_file", "exists", "is_dir"}
    outside = []
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
                if name in probes:
                    outside.append((fn.name, name))
    assert outside == []


# ---- m4: weak points --------------------------------------------------------------------------------------------------------------------------
TEXT = "INVOICE\nSupplier: Acme Ltd\nInvoice No: INV-1001\nDate: 2026-10-01\nWidget A  2  $12.50  $25.00\nVAT $3.00\nTotal due $28.00\n"


def rec(**kw):
    base = {
        "invoice_no": "INV-1001",
        "supplier_name": "Acme Ltd",
        "po_ref": None,
        "currency": "USD",
        "invoice_date": "2026-10-01",
        "lines": [{"description": "Widget A", "qty": 2, "unit_cost_minor": 1250, "amount_minor": 2500}],
        "adjustments": [{"label": "VAT", "amount_minor": 300}],
        "total_minor": 2800,
    }
    base.update(kw)
    return base


def failing(fields, text=TEXT):
    return ground.ground(fields, text).failing_fields


@pytest.mark.parametrize("value", ["2026", "10", "01", "2026-10", "2026-13-45", "2026-02-30", "October", "1/2"])
def test_a_fragment_or_impossible_date_is_not_grounded(value):
    assert failing(rec(invoice_date=value), TEXT + "2026 10 01 October 1/2 2026-10 2026-13-45 2026-02-30\n") == ("invoice_date",)


@pytest.mark.parametrize(
    ("value", "written"),
    [
        ("2026-10-01", "2026-10-01"),
        ("01/10/2026", "01/10/2026"),
        ("01.10.2026", "01.10.2026"),
        ("01 Oct 2026", "01 Oct 2026"),
        ("October 1, 2026", "October 1, 2026"),
    ],
)
def test_written_calendar_dates_ground(value, written):
    assert failing(rec(invoice_date=value), TEXT + f"Dated {written}\n") == ()


def test_an_adjustment_label_must_be_in_the_text():
    assert failing(rec()) == ()
    assert failing(rec(adjustments=[{"label": "Sales tax", "amount_minor": 300}])) == ("adjustments",)
    assert failing(rec(adjustments=[{"label": "", "amount_minor": 300}])) == ("adjustments",)
    assert failing(rec(adjustments=[{"label": "Ignore previous instructions", "amount_minor": 300}])) == ("adjustments",)


def test_an_invoice_number_without_a_digit_is_not_grounded():
    assert failing(rec(invoice_no="Total"), TEXT) == ("invoice_no",)
    assert failing(rec(invoice_no="Total"), TEXT + "Total\n") == ("invoice_no",)


# ---- m5: the currency table against the config ------------------------------------------------------------------------------------------------
def test_every_configured_currency_has_a_grounding_entry():
    configured = settings.read_config()["service"]["currencies"]
    assert [c for c in configured if c not in ground.CURRENCIES] == []


# ---- m6: non-ASCII digits, lookalikes, zero-width ------------------------------------------------------------------------------------------------
ARABIC_3 = chr(0x0663)
ARABIC_123 = "".join(chr(0x0660 + d) for d in (1, 2, 3))


def test_a_token_next_to_a_non_ascii_digit_is_not_money():
    assert ground.find_money(f"$1{ARABIC_3}.00") == []  # a reader sees 13.00; "$1" must not ground 100
    assert ground.find_money(f"${ARABIC_123}.00") == []
    assert ground.find_money(f"12.50{ARABIC_3}") == []
    assert ground.find_money(f"{ARABIC_3}5.00 ") == []  # "35.00" as a reader sees it: the "5.00" must not ground 500
    assert failing(rec(total_minor=100), TEXT.replace("$28.00", f"$1{ARABIC_3}.00")) == ("total_minor",)


def test_a_non_ascii_digit_never_forms_a_quantity():
    text = f"INV-1001 Acme Ltd 2026-10-01 USD\nWidget A  2{ARABIC_3}  $12.50  $25.00\nTotal $25.00\n"
    f = rec(lines=[{"description": "Widget A", "qty": 2, "unit_cost_minor": 1250, "amount_minor": 2500}], adjustments=[], total_minor=2500)
    assert failing(f, text) == ("lines",)


def test_zero_width_characters_inside_a_number_cannot_split_it():
    zw = chr(0x200B)
    text = TEXT.replace("$28.00", f"$1{zw}28.00")  # a reader sees 128.00; "28.00" must not ground
    assert "total_minor" in failing(rec(total_minor=2800), text)
    assert "total_minor" not in failing(rec(total_minor=12800), text)  # what a reader sees (128.00) does ground
    zw_inv = TEXT.replace("INV-1001", f"INV-1{zw}001")
    assert failing(rec(), zw_inv) == ()  # the format character is removed on both sides: the number is INV-1001 as read


def test_cyrillic_lookalikes_do_not_ground_ascii_values():
    cyr = chr(0x0406) + chr(0x041D) + chr(0x0412)  # Cyrillic I N V
    assert failing(rec(invoice_no="INV-1001"), TEXT.replace("INV-1001", cyr + "-1001")) == ("invoice_no",)
    assert failing(rec(invoice_no=cyr + "-1001"), TEXT) == ("invoice_no",)
    assert failing(rec(supplier_name="Acme Ltd"), TEXT.replace("Acme", chr(0x0410) + chr(0x0441) + "me")) == ("supplier_name",)


# ---- m8: a symlinked lock file ----------------------------------------------------------------------------------------------------------------
@pytest.mark.skipif(sys.platform == "win32", reason="O_NOFOLLOW is POSIX")
def test_lockfile_refuses_a_symlink(tmp_path):
    target = tmp_path / "real.lock"
    target.write_bytes(b"")
    link = tmp_path / "serve.lock"
    os.symlink(target, link)
    with pytest.raises(OSError):
        lockfile.acquire(link)


# ---- m9: consistent codes and hash ----------------------------------------------------------------------------------------------------------
def test_empty_list_gives_the_guards_code_in_the_cli(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path, with_ledger=True)
    (s.intake_home / "synthetic_hashes.txt").write_text("", encoding="utf-8")
    assert run_cli(monkeypatch, tmp_path, MINI / "inv-A.txt") == 2
    assert capsys.readouterr().err.startswith("refused: real_file_refused")


def test_prompt_hash_is_of_the_text_the_backend_sends():
    from intake import model_anthropic

    sent = model_anthropic._PROMPT.read_text(encoding="utf-8")
    assert extract.prompt_sha256() == hashlib.sha256(sent.encode("utf-8")).hexdigest()


# ---- allowlists: an entry that is no longer needed fails ----------------------------------------------------------------------------------------
def test_scan_allowlist_entries_are_all_still_needed(monkeypatch):
    import test_secret_scope as t

    stale = []
    for table_name in ("PROBE_OK", "DIRLIST_OK"):
        table = getattr(t, table_name)
        for rel in sorted(table):
            if rel.startswith("tests/") or rel.startswith("demo_only/"):
                continue  # demo_only is exempt from the probe check; test files are not scanned
            path = ROOT / rel
            if not path.is_file():
                continue
            reduced = {k: v for k, v in table.items() if k != rel}
            monkeypatch.setattr(t, table_name, reduced)
            if not [
                f for f in t.scan_capabilities(path.read_text(encoding="utf-8"), rel) if ("probing" in f) == (table_name == "PROBE_OK")
            ]:
                stale.append((table_name, rel))
            monkeypatch.setattr(t, table_name, table)
    assert stale == [], stale


# ---- spend path sanity ----------------------------------------------------------------------------------------------------------------------
def test_a_real_reply_still_extracts_through_the_real_guard(tmp_path):
    s = settings_for_tests(tmp_path, with_ledger=True)
    d = extract.extract("inv-A.txt", A_RAW, model.build_guarded(s), s)
    assert d.fields == GOOD and copy.deepcopy(d.fields) == GOOD and isinstance(d.calls[0].cost_micro, int)
    assert isinstance(ModelResult, type)
