"""Class: a script that reads a file the person NAMED (or parses its content) ends with ONE plain `refused:` or "cannot
read" line, never a Python traceback and never a wait for ever. Two causes: (1) a pipe (FIFO) has no end, so a plain
read waits for ever; (2) JSON nested 100000 deep ends the parser in a RecursionError. Every script and tool reads such a
file through `lead_desk.regfile` (open_regular, a size cap, one FileRefused for a bad content); the files of
load_tools/ and demo_only/ are pinned in test_tools_and_fakes_pipes.py (a pipe case per tool and a scan that finds no
plain read or write call), the CA file in test_ca_file_reads.py, and a guard over every folder of code in
test_file_call_guard.py (a static reading of the text; its own docstring says what it cannot see). Files that this
repository reads at a fixed place of its own (the database schema, the pattern lists of tools/hygiene.py) are not
named by a person and are not covered.
Also pins the literal exit codes (2 refused, 3 unreachable) from OUTSIDE the constants in scripts/refusals.py and the
edges of --index.
Every script runs in its own process with a 5 second limit; made-up data only; no network."""

from __future__ import annotations

import json
import os
import socket
import subprocess  # noqa: S404
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from feed import FeedRefused, build_envelope
from support import run_program, text_file

from lead_desk.constants import EXIT_BAD_SETTING_OR_PATH

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"

LEADS = json.loads((REPO / "demo_only" / "canned_leads.json").read_text(encoding="utf-8"))
FIFO = pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="no named pipes on this platform")
DEEP = "[" * 100000 + "]" * 100000


def _child(args: list[str], cwd: Path = REPO, limit: float = 5, **env: str) -> tuple[int, str]:
    """Run a script in its own process; a child that is still running after `limit` seconds fails the test."""
    base = {k: v for k, v in os.environ.items() if not k.startswith(("DESK_", "N8N_"))}
    base.update(PYTHONPATH=str(REPO / "src"), PYTHONDONTWRITEBYTECODE="1", **env)
    try:
        done = run_program(
            [sys.executable, *args],
            cwd=cwd,
            env=base,
            capture_output=True,
            text=True,
            timeout=limit,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"the script was still waiting after {limit} seconds (a pipe or a hang)")
    return done.returncode, done.stdout + done.stderr


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _canned_in(tmp_path: Path, how: str) -> Path:
    folder = tmp_path / "demo_only"
    folder.mkdir()
    target = folder / "canned_leads.json"
    if how == "fifo":
        os.mkfifo(target)
    else:
        target.write_text(DEEP, encoding="utf-8")
    return tmp_path


# -- (1) the file readers ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("how", ["deep", pytest.param("fifo", marks=FIFO)])
def test_feed_canned_file_that_is_deeply_nested_or_a_pipe_is_one_refusal_line(tmp_path: Path, how: str) -> None:
    root = _canned_in(tmp_path, how)
    code, out = _child(
        [str(SCRIPTS / "feed.py"), "--source", "form", "--index", "1"], cwd=root, DESK_PORT=str(_free_port())
    )
    assert "Traceback" not in out and "RecursionError" not in out, out
    assert code == 2, (code, out)
    assert out.strip().startswith("refused: canned leads: demo_only/canned_leads.json cannot be read"), out
    assert len(out.strip().splitlines()) == 1, out


@pytest.mark.parametrize("how", ["deep", pytest.param("fifo", marks=FIFO), "folder"])
def test_scrub_input_that_is_deeply_nested_a_pipe_or_a_folder_is_one_refusal_line(tmp_path: Path, how: str) -> None:
    src = tmp_path / "in.json"
    if how == "fifo":
        os.mkfifo(src)
    elif how == "folder":
        src.mkdir()
    else:
        src.write_text(DEEP, encoding="utf-8")
    code, out = _child(["-m", "tools.scrub_n8n_export", str(src), str(tmp_path / "out.json")])
    assert "Traceback" not in out and "RecursionError" not in out, out
    assert code == 2 and out.strip().startswith("refused: in.json: "), (code, out)
    assert len(out.strip().splitlines()) == 1, out
    assert not (tmp_path / "out.json").exists()


@FIFO
def test_n8n_api_key_file_and_workflow_file_that_are_pipes_are_refused_not_waited_for(tmp_path: Path) -> None:
    pipe = tmp_path / "pipe"
    os.mkfifo(pipe)
    code, out = _child([str(SCRIPTS / "n8n_api.py"), "list"], N8N_API_KEY_FILE=str(pipe), N8N_URL="http://127.0.0.1:1")
    assert (code, out) == (EXIT_BAD_SETTING_OR_PATH, "the n8n API key file cannot be read\n")  # was 1 before round 7
    key = tmp_path / "key"
    key.write_text("abc12345\n", encoding="utf-8")
    code, out = _child(
        [str(SCRIPTS / "n8n_api.py"), "import", str(pipe)],
        cwd=tmp_path,
        N8N_API_KEY_FILE=str(key),
        N8N_URL="http://127.0.0.1:1",
        LEAD_DESK_PATH_ROOTS=str(tmp_path),
    )
    assert "Traceback" not in out and code != 0 and "cannot read a workflow" in out, (code, out)


def test_n8n_api_workflow_file_nested_too_deeply_is_refused(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("abc12345\n", encoding="utf-8")
    wf = tmp_path / "wf.json"
    wf.write_text(DEEP, encoding="utf-8")
    code, out = _child(
        [str(SCRIPTS / "n8n_api.py"), "import", str(wf)],
        cwd=tmp_path,
        N8N_API_KEY_FILE=str(key),
        N8N_URL="http://127.0.0.1:1",
        LEAD_DESK_PATH_ROOTS=str(tmp_path),
    )
    assert "Traceback" not in out and code != 0 and "cannot read a workflow" in out, (code, out)


@FIFO
def test_run_real_check_config_that_is_a_pipe_is_refused_not_waited_for(tmp_path: Path) -> None:
    """load_env is what reads the settings file (main asks for a terminal first, so it is called here directly)."""
    pipe = tmp_path / "config.env"
    os.mkfifo(pipe)
    prog = (
        "import sys, pathlib; sys.path.insert(0, sys.argv[1]); import run_real_check as r\n"
        "try:"
        + "\n    r.load_env(pathlib.Path(sys.argv[2]))\nexcept (OSError, ValueError)"
        + ":\n    print('REFUSED')\n"
    )
    code, out = _child([text_file(prog), str(SCRIPTS), str(pipe)])  # the path check refuses it (a ValueError) at once
    assert code == 0 and out.strip() == "REFUSED", (code, out)
    deep = tmp_path / "deep.env"
    deep.write_bytes(b"\xff\xfe")
    code, out = _child([text_file(prog), str(SCRIPTS), str(deep)])
    assert code == 0 and out.strip() == "REFUSED", (code, out)


def test_the_one_reader_refuses_every_bad_content_with_one_error_type(tmp_path: Path) -> None:
    from lead_desk.regfile import MAX_JSON_BYTES, FileRefused, load_json_file, read_regular_text

    for name, data in {
        "deep": DEEP.encode(),
        "rubbish": b"{bad",
        "not-utf8": b"\xff\xfe\x00[]",
        "big": b" " * (MAX_JSON_BYTES + 1),
    }.items():
        p = tmp_path / name
        p.write_bytes(data)
        with pytest.raises(FileRefused) as seen:
            load_json_file(p)
        assert str(p) not in str(seen.value)
    edge = tmp_path / "edge"
    edge.write_bytes(b"[1]" + b" " * (MAX_JSON_BYTES - 3))
    assert load_json_file(edge) == [1]  # exactly the cap is accepted
    with pytest.raises(FileRefused):
        read_regular_text(edge, MAX_JSON_BYTES - 1)
    with pytest.raises(OSError):
        load_json_file(tmp_path)  # a folder
    with pytest.raises(OSError):
        load_json_file(tmp_path / "missing")


# The guard that no file call slips past the one reader is in test_file_call_guard.py.


# -- (2) the two survivors --------------------------------------------------------------------------------------------


def test_feed_index_edges_last_valid_index_is_accepted_and_the_two_neighbours_are_refused() -> None:
    last = len(LEADS)
    assert build_envelope("form", last, LEADS)["source_ref"] == f"canned-{last}"
    assert build_envelope("form", 1, LEADS)["source_ref"] == "canned-1"
    for bad in (0, last + 1, -1):
        with pytest.raises(FeedRefused):
            build_envelope("form", bad, LEADS)


def test_feed_last_valid_index_reaches_the_desk_step_and_the_next_one_does_not() -> None:
    last = len(LEADS)
    port = str(_free_port())  # nothing listens there
    code, out = _child([str(SCRIPTS / "feed.py"), "--source", "form", "--index", str(last)], DESK_PORT=port)
    assert code == 3 and out.startswith("refused: the desk: "), (code, out)  # the index was accepted
    code, out = _child([str(SCRIPTS / "feed.py"), "--source", "form", "--index", str(last + 1)], DESK_PORT=port)
    assert code == 2 and out.startswith("refused: --index: "), (code, out)
    code, out = _child([str(SCRIPTS / "feed.py"), "--source", "form", "--index", "0"], DESK_PORT=port)
    assert code == 2 and out.startswith("refused: --index: "), (code, out)


def test_the_exit_codes_are_two_and_three_whatever_the_constants_say() -> None:
    """The numbers are part of what run_live_check.py, run_real_check.py and the .sh files rely on: pinned as
    literals, seen from outside the process (the constants in scripts/refusals.py are not imported here)."""
    port = str(_free_port())
    code, _ = _child([str(SCRIPTS / "feed.py"), "--source", "form", "--index", "0"], DESK_PORT=port)
    assert code == 2
    code, _ = _child([str(SCRIPTS / "feed.py"), "--source", "form", "--index", "1"], DESK_PORT=port)
    assert code == 3
    code, _ = _child(["-m", "tools.scrub_n8n_export", "only-one-argument"])
    assert code == 2


@pytest.mark.parametrize(
    "text",
    ["NaN", "Infinity", "-Infinity", "1e999", "-1e999", "[1, NaN]", '{"a": [1, {"b": Infinity}]}', '{"a": [[-1e999]]}'],
)
def test_the_one_reader_refuses_a_number_that_is_not_finite(tmp_path: Path, text: str) -> None:
    """Round-3 finding 8: JSON as Python reads it accepts NaN and Infinity and turns 1e999 into infinity."""
    from lead_desk.regfile import FileRefused, load_json_file

    p = tmp_path / "n.json"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(FileRefused) as seen:
        load_json_file(p)
    assert str(seen.value) == "the file is not JSON that can be read"
    ok = tmp_path / "ok.json"
    ok.write_text('{"a": [1, 2.5, -1e300, null, "NaN"]}', encoding="utf-8")  # finite numbers and the WORD NaN are fine
    assert load_json_file(ok) == {"a": [1, 2.5, -1e300, None, "NaN"]}


def test_a_script_meets_a_number_that_is_not_finite_with_one_refusal_line(tmp_path: Path) -> None:
    src = tmp_path / "in.json"
    src.write_text('{"x": NaN}', encoding="utf-8")
    code, out = _child(["-m", "tools.scrub_n8n_export", str(src), str(tmp_path / "out.json")])
    assert "Traceback" not in out and code == 2 and out.strip().startswith("refused: in.json: "), (code, out)
    assert len(out.strip().splitlines()) == 1 and not (tmp_path / "out.json").exists()


@pytest.mark.parametrize("odd", ["\u00a0", "\u2003", "\u3000", "\u200b"])
def test_run_real_check_config_value_with_an_odd_space_is_not_silently_trimmed(tmp_path: Path, odd: str) -> None:
    """Only a plain space and a tab around a name or a value are dropped; a no-break or wide space stays in the value,
    so the setting's own check refuses it (before round 7 str.strip() hid it)."""
    sys.path.insert(0, str(SCRIPTS))
    try:
        import run_real_check as rrc
    finally:
        sys.path.remove(str(SCRIPTS))
    cfg = tmp_path / "c.env"
    cfg.write_text(
        f"DESK_SMTPP_USER=bob@example.test{odd}\nREAL_IMAP_1_USER={odd}carol@example.test\n", encoding="utf-8"
    )
    got = rrc.load_env(cfg)
    assert got["DESK_SMTPP_USER"] == f"bob@example.test{odd}"
    assert got["REAL_IMAP_1_USER"] == f"{odd}carol@example.test"
    cfg.write_text(" \tDESK_SMTPP_USER \t=\t bob@example.test \t\n", encoding="utf-8")
    assert rrc.load_env(cfg) == {"DESK_SMTPP_USER": "bob@example.test"}  # plain space and tab are still dropped
