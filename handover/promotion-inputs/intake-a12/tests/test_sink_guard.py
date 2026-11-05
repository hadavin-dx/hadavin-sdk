"""CSV cell guard (spec 9): the table of the spec, property checks over hostile alphabets, the numeric columns and the whole-row rules."""

from __future__ import annotations

import csv
import errno
import io
import random
import stat
import sys

import pytest

from intake import csvsink, sink_guard
from intake.sink_guard import COLUMNS, BadCell, guard_cell, guard_row
from intake.textfold import fold_text

# invisible and look-alike characters are built at run time (no invisible character in a tracked file)
ZW = chr(0x200B)
FULL_EQ = chr(0xFF1D)  # fullwidth equals sign
FULL_AT = chr(0xFF20)
NBSP = chr(0xA0)
UE = chr(0xFC)  # u with diaeresis

TABLE = [
    ("=1+1", "'=1+1"),
    ("@SUM(A1)", "'@SUM(A1)"),
    (FULL_EQ + "cmd|' /C calc'!A0", "'" + FULL_EQ + "cmd|' /C calc'!A0"),
    (" =1+1", "' =1+1"),
    ("-Acme Ltd", "'-Acme Ltd"),
    ("\t=1+1", "' =1+1"),  # the tab becomes a space, then guarded
    (ZW + "=1+1", "'" + ZW + "=1+1"),  # the folded first character is "="
    ("M" + UE + "ller GmbH", "M" + UE + "ller GmbH"),  # unchanged and hash-consistent
    ("+1", "'+1"),
    ("\r=1", "' =1"),
    ("\n=1", "' =1"),
    (NBSP + "=1", "'" + NBSP + "=1"),  # folds to a space then "="
    ("Acme =1", "Acme =1"),  # only the FIRST character matters
    ("", ""),
    (None, ""),
    ("'=1+1", "'=1+1"),  # already guarded: unchanged (idempotent)
    ("a\tb\r\nc", "a b  c"),  # breaks inside a cell become spaces
]


@pytest.mark.parametrize("raw,want", TABLE)
def test_table(raw, want):
    assert guard_cell("supplier_name", raw) == want


@pytest.mark.parametrize("col", [c for c in COLUMNS if c not in sink_guard.NUMERIC])
def test_every_text_column_is_guarded_including_the_approver(col):
    assert guard_cell(col, "=cmd") == "'=cmd"
    assert guard_cell("approved_by", "@evil") == "'@evil"


def test_trigger_set_is_the_one_of_the_spec():
    assert set(sink_guard.TRIGGERS) == set("=+-@ " + chr(9) + chr(13) + chr(10))


def test_numeric_columns():
    assert guard_cell("total_minor", 3300) == "3300"
    assert guard_cell("line_count", "2") == "2"
    assert guard_cell("total_minor", 0) == "0"
    for bad in ("-1", "=1+1", "1e3", "1.0", " 1", "1 ", "", "12\n", chr(0x0661), chr(0xFF11), 1.5, True, None, -3, [1]):
        with pytest.raises(BadCell):
            guard_cell("total_minor", bad)
    with pytest.raises(BadCell):
        guard_cell("line_count", "+3")
    assert guard_cell("total_minor", "007") == "7"  # str(int(...)): no leading zero


def test_nul_and_non_text_are_errors():
    for bad in ("a\x00b", "\x00", 5, ["x"], b"x", True):
        with pytest.raises(BadCell):
            guard_cell("invoice_no", bad)
    with pytest.raises(BadCell):
        guard_cell("not_a_column", "x")


def test_guard_changes_only_the_text_not_the_hashed_value():
    # the content code covers the UNGUARDED value; the guard only prefixes (spec 9)
    assert guard_cell("supplier_name", "=1+1")[1:] == "=1+1"


def test_row_needs_exactly_the_14_columns():
    row = dict.fromkeys(COLUMNS, "x")
    row["total_minor"] = row["line_count"] = "1"
    assert list(guard_row(row)) == list(COLUMNS)
    with pytest.raises(BadCell):
        guard_row({k: v for k, v in row.items() if k != "approved_by"})
    with pytest.raises(BadCell):
        guard_row({**row, "extra": "x"})
    with pytest.raises(BadCell):
        guard_row({**row, "approved_by": "a\x00"})


def test_guard_is_idempotent_and_prefixes_once():
    rnd = random.Random(7)
    alphabet = [
        "=",
        "+",
        "-",
        "@",
        " ",
        "\t",
        "\r",
        "\n",
        ZW,
        FULL_EQ,
        FULL_AT,
        NBSP,
        "'",
        "a",
        "Z",
        "0",
        chr(0x301),
        chr(0xFE62),
        chr(0x2028),
        "|",
        '"',
        UE,
    ]
    for _ in range(3000):
        v = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 8)))
        once = guard_cell("supplier_name", v)
        assert guard_cell("supplier_name", once) == once
        assert once == v.translate(sink_guard._BREAKS) or once == "'" + v.translate(sink_guard._BREAKS)


def test_property_no_written_cell_starts_with_a_trigger_raw_or_folded():
    rnd = random.Random(11)
    alphabet = [
        "=",
        "+",
        "-",
        "@",
        " ",
        "\t",
        "\r",
        "\n",
        ZW,
        FULL_EQ,
        FULL_AT,
        NBSP,
        chr(0xFE62),
        chr(0xFF0B),
        chr(0xFF0D),
        chr(0x301),
        "a",
        "1",
        chr(0x2028),
    ]
    for _ in range(5000):
        v = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 6)))
        out = guard_cell("approved_by", v)
        assert out[:1] not in sink_guard.TRIGGERS, repr(v)
        assert fold_text(out)[:1] not in sink_guard.TRIGGERS, repr(v)
        assert not any(c in out for c in "\t\r\n")


def test_cell_cap_and_unencodable_values_are_refused_not_truncated():
    assert guard_cell("supplier_name", "A" * sink_guard.MAX_CELL) == "A" * sink_guard.MAX_CELL
    assert guard_cell("supplier_name", "=" + "A" * (sink_guard.MAX_CELL - 1)) == "'=" + "A" * (sink_guard.MAX_CELL - 1)
    for bad in ("A" * (sink_guard.MAX_CELL + 1), "=" + "A" * 1_000_000, "a" + chr(0xD800), chr(0xDFFF)):
        with pytest.raises(BadCell):
            guard_cell("invoice_no", bad)
    assert sink_guard.MAX_CELL == 4096


def _row(**kw):
    row = dict.fromkeys(COLUMNS, "x")
    row["total_minor"] = row["line_count"] = "1"
    row.update(kw)
    return row


def test_csvsink_format_and_guard_choke_point(tmp_path):
    p = tmp_path / "out" / "invoices.csv"
    rows = [_row(supplier_name="=HYPERLINK(1)", approved_by="@x", invoice_no="M" + UE + 'ller\nGmbH, "Q"'), _row(po_ref=None)]
    assert csvsink.regenerate(p, rows) == 2
    raw = p.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw  # UTF-8 without BOM, LF only
    text = raw.decode("utf-8")
    assert text.splitlines()[0] == ",".join(f'"{c}"' for c in COLUMNS)  # QUOTE_ALL
    got = list(csv.reader(io.StringIO(text, newline="")))
    assert got[1][3] == "'=HYPERLINK(1)" and got[1][12] == "'@x"  # the approver column too
    assert got[1][2] == "M" + UE + 'ller GmbH, "Q"'  # the newline became a space; quotes round-trip
    assert got[2][4] == ""
    for r in got[1:]:
        assert all(c[:1] not in sink_guard.TRIGGERS for c in r)


def test_csvsink_bad_row_leaves_the_old_file_untouched(tmp_path):
    p = tmp_path / "invoices.csv"
    csvsink.regenerate(p, [_row()])
    before = p.read_bytes()
    with pytest.raises(BadCell):
        csvsink.regenerate(p, [_row(), _row(total_minor="-5")])
    assert p.read_bytes() == before
    assert not (tmp_path / "invoices.csv.tmp").exists()


def test_csvsink_locked_file_is_sink_locked_and_leaves_no_tmp(tmp_path, monkeypatch):
    p = tmp_path / "invoices.csv"
    csvsink.regenerate(p, [_row()])
    before = p.read_bytes()

    def deny(src, dst):
        raise OSError(errno.EBUSY, "locked")

    monkeypatch.setattr(csvsink.os, "replace", deny)
    with pytest.raises(csvsink.SinkLocked):
        csvsink.regenerate(p, [_row(), _row()])
    assert p.read_bytes() == before and not (tmp_path / "invoices.csv.tmp").exists()


def test_other_os_errors_are_sink_error_not_sink_locked_and_leave_no_tmp(tmp_path, monkeypatch):
    p = tmp_path / "out" / "invoices.csv"
    csvsink.regenerate(p, [_row()])
    before = p.read_bytes()
    for err in (OSError(errno.ENOSPC, "disk full"), PermissionError(errno.EACCES, "denied")):

        def boom(src, dst, err=err):
            raise err

        monkeypatch.setattr(csvsink.os, "replace", boom)
        with pytest.raises(csvsink.SinkError):
            csvsink.regenerate(p, [_row(), _row()])
        assert p.read_bytes() == before and not list(p.parent.glob("*.tmp"))
    monkeypatch.undo()


def test_tmp_is_removed_on_any_exception_even_a_kill_signal(tmp_path, monkeypatch):
    p = tmp_path / "invoices.csv"

    def boom(src, dst):
        raise KeyboardInterrupt

    monkeypatch.setattr(csvsink.os, "replace", boom)
    with pytest.raises(KeyboardInterrupt):
        csvsink.regenerate(p, [_row()])
    assert not list(tmp_path.glob("*.tmp")) and not p.exists()


def test_concurrent_regeneration_leaves_one_whole_file(tmp_path):
    import threading

    p = tmp_path / "out" / "invoices.csv"
    errs: list[str] = []

    def go(n):
        try:
            csvsink.regenerate(p, [_row(invoice_no=f"INV-{n}-{i}") for i in range(30)])
        except (csvsink.SinkLocked, csvsink.SinkError) as e:  # Windows can refuse a replace under a concurrent open
            errs.append(type(e).__name__)

    ts = [threading.Thread(target=go, args=(n,)) for n in range(6)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    rows = list(csv.reader(open(p, encoding="utf-8", newline="")))
    assert rows[0] == list(COLUMNS) and len(rows) == 31 and len({r[2].split("-")[1] for r in rows[1:]}) == 1  # one writer's whole set
    assert not list(p.parent.glob("*.tmp"))


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX mode bits")
def test_folder_and_file_modes_are_private_and_mode_state_reports_them(tmp_path):
    p = tmp_path / "out" / "invoices.csv"
    csvsink.regenerate(p, [_row()])
    assert stat.S_IMODE(p.stat().st_mode) == 0o600 and stat.S_IMODE(p.parent.stat().st_mode) == 0o700
    assert csvsink.mode_state(p) == "ok"
    p.chmod(0o644)
    assert (
        csvsink.mode_state(p) == "warn invoices.csv"
    )  # a warning line only (documented in csvsink.mode_state), never "fail"; the file name says what is loose
    p.chmod(0o600)
    p.parent.chmod(0o755)
    assert csvsink.mode_state(p) == "warn out"


def test_guard_raw_and_folded_branches_are_each_sufficient(monkeypatch):
    # raw branch alone: the fold is stubbed to something harmless
    for stub in ("x", ""):
        monkeypatch.setattr(sink_guard, "fold_text", lambda raw, stub=stub, **k: stub)
        for raw in ("=1+1", " a", "-a", "@a", "+a"):
            assert guard_cell("supplier_name", raw) == "'" + raw, (raw, stub)
        assert guard_cell("supplier_name", "plain") == "plain"
    monkeypatch.undo()
    # folded branch alone: the raw trigger set is stubbed empty, so only the fold can see a fullwidth equals sign
    monkeypatch.setattr(sink_guard, "TRIGGERS", frozenset("="))
    monkeypatch.setattr(sink_guard, "fold_text", lambda raw, **k: "=" + raw[1:] if raw[:1] == chr(0xFF1D) else raw)
    assert guard_cell("supplier_name", chr(0xFF1D) + "cmd") == "'" + chr(0xFF1D) + "cmd"
    assert guard_cell("supplier_name", "plain") == "plain"
