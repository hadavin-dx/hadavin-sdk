"""The Unreleased pathguard entry in CHANGELOG.md makes claims about the code. Each claim is checked against the code in its
own test, so the text cannot drift from what runs. The entry is the heading bullet and the indented bullets under it.

Labels, measured by real runs on (a) origin/main source plus this change's ``pathguard.py`` and (b) origin/main as it is (``pathguard`` does not exist on main, so for a file that imports it an empty stand-in module let the file load; a test that calls the module fails there): ``test_control_*`` passes on (a) and (b); ``test_pin_*`` passes on (a) and fails on (b); every other name fails on (a). This file: 23 control, 12 pin, 32 other. Nothing here says a test "fails on old main".
"""

from __future__ import annotations

import ast
import logging
import os
import re
from pathlib import Path

import pytest

from hadavin_sdk import pathguard
from hadavin_sdk.config import confined
from hadavin_sdk.errors import ConfigError

ROOT = Path(__file__).resolve().parent.parent
LINES = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
START = next(i for i, line in enumerate(LINES) if line.startswith("- **Path checks:"))
END = next((i for i in range(START + 1, len(LINES)) if LINES[i].startswith("- ")), len(LINES))
ENTRY = "\n".join(LINES[START:END])
BULLETS = [line.strip() for line in LINES[START + 1 : END] if line.startswith("  - ")]


def bullet(start: str) -> str:
    found = [b for b in BULLETS if b.startswith(f"- **{start}")]
    assert len(found) == 1, f"expected one bullet that starts with {start!r}, found {len(found)}"
    return found[0]


def test_control_the_heading_is_narrow_and_names_the_scan_it_depends_on():
    assert LINES[START].startswith(
        "- **Path checks: `hadavin_sdk/pathguard.py` holds the rules for the file operations"
    )
    assert "package tripwire test lists" in LINES[START]
    assert "tests/fixtures/pathguard_exceptions.txt" in ENTRY


def test_pin_the_module_docstring_makes_the_same_narrow_claim():
    first = (pathguard.__doc__ or "").splitlines()[0]
    assert "listed by the package tripwire test" in first


@pytest.mark.parametrize("n", range(1, 14))
def test_control_every_rule_from_r1_to_r13_is_named_as_a_whole_word(n):
    assert re.search(rf"\(R{n}\)|\bR{n}\b", bullet("The rules (R1 to R13)")), f"R{n} is not named"


def test_control_the_rule_list_does_not_name_a_rule_that_does_not_exist():
    text = bullet("The rules (R1 to R13)")
    named = {int(m) for m in re.findall(r"\bR(\d+)\b", text)}
    assert named <= set(range(1, 14))


def test_pin_the_numbers_in_the_entry_are_the_numbers_in_the_code():
    assert f"at most {pathguard.MAX_COMPONENT_BYTES} bytes" in ENTRY
    assert f"at most {pathguard.MAX_PATH_BYTES} bytes in all" in ENTRY
    assert f"{pathguard.MAX_WRITE_NAME_BYTES} bytes" in ENTRY
    assert f"the {len(pathguard.CONTROL_RANGES)} ranges" in ENTRY


@pytest.mark.parametrize("name", ["con", "aux", "com1"])
def test_pin_device_names_named_in_the_entry_are_refused(name):
    assert f"`{name}`" in ENTRY
    with pytest.raises(pathguard.PathRefused):
        pathguard.component(name, what="n")


@pytest.mark.parametrize(
    ("rule", "name"),
    [("R3", "a:b"), ("R6", "x."), ("R6", "x "), ("R7", "con"), ("R12", "a?b")],
)
def test_pin_r3_r6_r7_and_r12_each_refuse_a_data_name_in_component_and_join(tmp_path, rule, name):
    assert rule in bullet("R3, R6, R7 and R12 apply to")
    for call in (
        lambda: pathguard.component(name, what="n"),
        lambda: pathguard.join(tmp_path, name, what="n"),
    ):
        with pytest.raises(pathguard.PathRefused) as caught:
            call()
        assert caught.value.rule == rule


@pytest.mark.parametrize("name", ["vault:token", "con", "x.", "a?b"])
def test_a_name_the_caller_typed_is_refused_where_the_join_pattern_reads_it(tmp_path, name):
    """The entry lists these names: ``inside``, ``operator_file`` and ``config.confined`` still accept them (nothing reads
    after them), the three flagged reads (``hash_files``, the secrets reader, the answers file) refuse them."""
    from hadavin_sdk.actions.secrets_file import MountedFileProvider
    from hadavin_sdk.hashing import hash_files

    assert f"`{name}`" in bullet("R3, R6, R7 and R12 apply to")
    (tmp_path / name).write_text("v", encoding="utf-8")
    (tmp_path / name).chmod(0o400)
    assert pathguard.inside(tmp_path, tmp_path / name, what="n", must_exist=True, kind="file")
    assert pathguard.operator_file(tmp_path / name, what="n")
    assert confined(tmp_path, name) == (tmp_path / name).resolve()
    with pytest.raises(pathguard.PathRefused):
        hash_files(tmp_path, [name])
    with pytest.raises(pathguard.PathRefused):
        MountedFileProvider(tmp_path, 1).get(name)


def test_each_message_the_entry_quotes_is_the_message_the_code_gives(tmp_path):
    from types import SimpleNamespace

    from hadavin_sdk.actions.secrets_file import MountedFileProvider, build
    from hadavin_sdk.hashing import hash_files
    from hadavin_sdk.k1b.bundle import load_bundles
    from hadavin_sdk.k1b.score import outputs_dir

    text = bullet("A refusal from `pathguard`")
    for quoted in (
        "path escapes its folder: <name as written>",
        "not a file: <name>",
        "secret '<name>' not found in the mounted folder",
        "no key file at <the key path as typed in the config>",
        "outputs folder: contains a control character",
    ):
        assert quoted in text, quoted

    def said(fn, *a, **k):
        try:
            fn(*a, **k)
        except (
            ConfigError,
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            AttributeError,
        ) as exc:  # the usual types: the text is what is compared
            return str(exc)
        return ""

    assert said(confined, tmp_path, "../x") == "path escapes its folder: ../x"
    assert said(hash_files, tmp_path, ["nope"]) == "not a file: nope"
    assert (
        said(MountedFileProvider(tmp_path, 1).get, "nope")
        == "secret 'nope' not found in the mounted folder"
    )
    assert said(outputs_dir, tmp_path / "gone") == "outputs folder does not exist"
    assert said(load_bundles, tmp_path / "gone") == "bundles folder does not exist"
    assert said(hash_files, tmp_path / "gone", ["a"]) == "hash folder does not exist"
    assert (
        said(build, SimpleNamespace(dir=str(tmp_path / "gone"), ttl_s=1), None)
        == f"secrets mounted_file: {tmp_path / 'gone'} is not a folder"
    )
    assert said(outputs_dir, str(tmp_path) + chr(0x202E)) == (
        "outputs folder: contains a control character"
    )


def test_control_the_signer_says_where_the_key_was_as_typed_and_never_the_resolved_path(tmp_path):
    from types import SimpleNamespace

    from hadavin_sdk.audit.signer import build_local

    typed = str(tmp_path / "keys" / ".." / "nokey.pem")
    settings = SimpleNamespace(
        passphrase_secret_name=None, private_key_secret_name=None, private_key_path=typed
    )
    with pytest.raises(ConfigError) as caught:
        build_local(settings, None)
    assert str(caught.value) == f"signer ed25519_local: no key file at {typed}"


def test_the_atomic_write_signature_temp_name_mode_and_untouched_taken_name(tmp_path, monkeypatch):
    from hadavin_sdk.k1b import atomic

    text = bullet("`k1b.atomic.atomic_write(path, text)` is now")
    for claim in ("`.<name>.<random>.tmp`", "mode 0o600", "0o644"):
        assert claim in text, claim
    seen = []
    real_open = os.open

    def spy(path, flags, mode=0o777, **kw):
        seen.append((os.fspath(path), mode))
        return real_open(path, flags, mode, **kw)

    monkeypatch.setattr(os, "open", spy)
    atomic.atomic_write(tmp_path, "f.txt", "x")
    monkeypatch.undo()
    assert [p.name for p in tmp_path.iterdir()] == ["f.txt"]
    assert (tmp_path / "f.txt").stat().st_mode & 0o777 == 0o600
    temp = [Path(p).name for p, _ in seen if Path(p).name.startswith(".f.txt.")]
    assert temp and re.fullmatch(r"\.f\.txt\.[0-9a-f]{16}\.tmp", temp[0]), temp
    assert all(mode == 0o600 for p, mode in seen if Path(p).name.startswith(".f.txt."))
    with pytest.raises(
        TypeError, match=r"atomic_write\(\) missing 1 required positional argument: 'text'"
    ):
        atomic.atomic_write(tmp_path / "f.txt", "x")  # the old two-argument form is gone


def test_atomic_write_refuses_what_it_cannot_replace_without_a_path(tmp_path):
    from hadavin_sdk.k1b.atomic import atomic_write

    text = bullet("`atomic_write` refuses what it cannot replace")
    for claim in ("(R8)", "(R13)", "233 bytes", "hard link", "without the temp path"):
        assert claim in text, claim
    assert pathguard.MAX_WRITE_NAME_BYTES == 233
    (tmp_path / "target.txt").write_text("keep", encoding="utf-8")
    (tmp_path / "link.txt").symlink_to(tmp_path / "target.txt")
    (tmp_path / "d").mkdir()
    for name, rule in (("link.txt", "R8"), ("d", "R13"), ("x" * 234, "R5")):
        with pytest.raises(pathguard.PathRefused) as caught:
            atomic_write(tmp_path, name, "new")
        assert caught.value.rule == rule, name
        assert str(tmp_path) not in str(caught.value)
    assert (tmp_path / "target.txt").read_text(encoding="utf-8") == "keep"
    (tmp_path / "hard.txt").write_text("old", encoding="utf-8")
    os.link(tmp_path / "hard.txt", tmp_path / "other.txt")
    atomic_write(tmp_path, "hard.txt", "new")
    assert (tmp_path / "other.txt").read_text(encoding="utf-8") == "old"
    assert (tmp_path / "hard.txt").read_text(encoding="utf-8") == "new"


def test_atomic_write_os_errors_carry_no_path_and_no_chain(tmp_path, monkeypatch):
    from hadavin_sdk.k1b.atomic import atomic_write

    assert "without a chained earlier error" in bullet(
        "`atomic_write` refuses what it cannot replace"
    )

    def fail(*_a, **_k):
        raise PermissionError(13, "denied", str(tmp_path / "secret-folder-name"))

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(PermissionError) as caught:
        atomic_write(tmp_path, "f.txt", "x")
    assert "secret-folder-name" not in str(caught.value) and str(tmp_path) not in str(caught.value)
    assert caught.value.__cause__ is None and caught.value.__context__ is None
    assert [p.name for p in tmp_path.iterdir()] == []  # the temp file is removed


def test_a_digest_file_that_is_a_link_out_is_unreadable_and_a_nul_gives_exit_2(tmp_path, capsys):
    from hadavin_sdk.cli import main
    from hadavin_sdk.k1b.score import _recorded_digest
    from tests.conftest import make_cfg

    text = bullet("`score` reads its `outputs.sha256` digest file only")
    assert "exit code 2" in text and "on origin/main" in text
    outside = tmp_path / "outside.txt"
    outside.write_text("abc\n", encoding="utf-8")
    run = tmp_path / "run"
    run.mkdir()
    (run / "outputs.sha256").symlink_to(outside)
    assert _recorded_digest(run) == "", (
        "a digest behind a link must count as unreadable, not as missing"
    )
    code = main(
        [
            "--config",
            str(make_cfg(tmp_path)),
            "score",
            "--outputs",
            str(tmp_path / "out") + chr(0),
            "--answers",
            str(tmp_path / "a.json"),
            "--cause-list",
            str(tmp_path),
            "--bundles",
            str(tmp_path),
        ]
    )
    assert code == 2
    assert "outputs folder: contains a control character" in capsys.readouterr().err


def test_outputs_files_raises_for_a_missing_folder(tmp_path):
    from hadavin_sdk.k1b.replay import outputs_files

    assert "raises a `ConfigError` for a missing outputs folder" in bullet("`replay.outputs_files`")
    with pytest.raises(ConfigError):
        outputs_files(tmp_path / "missing")


def test_paths_are_resolved_and_absolute_whatever_the_current_folder(tmp_path, monkeypatch):
    from hadavin_sdk.config import load_config
    from hadavin_sdk.k1b.score import outputs_dir
    from tests.conftest import make_cfg

    assert "no longer depend on the current folder" in bullet(
        "Paths are now the resolved, absolute path."
    )
    cfg_dir = make_cfg(tmp_path)
    (tmp_path / "out").mkdir()
    monkeypatch.chdir(tmp_path)
    cfg = load_config(Path("config"))
    assert cfg.root == cfg_dir.resolve() and cfg.root.is_absolute()
    assert cfg.golden_dir == (tmp_path / "golden").resolve()
    assert cfg.inputs_dir == (tmp_path / "inputs").resolve()
    assert outputs_dir(Path("out")) == (tmp_path / "out").resolve()
    link = tmp_path / "linked"
    link.symlink_to(tmp_path / "out")
    assert outputs_dir(link) == (tmp_path / "out").resolve()


def test_confined_keeps_its_escape_text_and_refuses_the_wide_set_and_a_long_path(tmp_path):
    text = bullet("`config.confined` refuses")
    for claim in (
        "path escapes its folder: <name>",
        "path: too long",
        "path: contains a control character",
    ):
        assert claim in text, claim
    with pytest.raises(ConfigError, match="^path escapes its folder: ../x$"):
        confined(tmp_path, "../x")
    for name, said in (
        ("a" * (pathguard.MAX_PATH_BYTES + 1), "path: too long"),
        ("a" + chr(0x202E), "path: contains a control character"),
        ("a\x00b", "path: contains a control character"),
        ("a" + chr(0x2800), "path: contains a control character"),
    ):
        with pytest.raises(ConfigError) as caught:
            confined(tmp_path, name)
        assert str(caught.value) == said
        assert isinstance(caught.value, ValueError)
    for allowed in ("a:b", "con", "x.", "a?b"):  # the Windows name rules are not added
        assert confined(tmp_path, allowed) == (tmp_path / allowed).resolve()


def test_golden_and_inputs_dir_may_point_outside_the_config_folder(tmp_path):
    from hadavin_sdk.config import load_config
    from tests.conftest import make_cfg

    assert "may still point outside the config folder" in bullet("`golden_dir` and `inputs_dir`")
    cfg = load_config(make_cfg(tmp_path))
    assert cfg.golden_dir == (tmp_path / "golden").resolve()
    assert not cfg.golden_dir.is_relative_to(cfg.root)


def test_a_bundles_entry_with_a_reserved_name_is_a_path_refusal_and_a_plain_wrong_name_is_not(
    tmp_path,
):
    from hadavin_sdk.k1b.bundle import BundleError, load_bundles

    assert "raises `PathRefused` for that entry before the case-id check" in bullet(
        "A bundles folder that holds"
    )
    (tmp_path / "con").mkdir()
    with pytest.raises(pathguard.PathRefused):
        load_bundles(tmp_path)
    (tmp_path / "con").rmdir()
    (tmp_path / "notacase").mkdir()
    with pytest.raises(BundleError):
        load_bundles(tmp_path)


def test_key_path_checks_before_it_makes_a_folder_and_its_messages_hold_no_path(tmp_path):
    from hadavin_sdk.audit.signer import key_path, load_private_key, load_public_key

    bullet("`signer.key_path` resolves the whole target")
    folder = tmp_path / ("a" + chr(0x202E))
    with pytest.raises(pathguard.PathRefused) as caught:
        key_path(folder / "k.pem", folder)
    assert not folder.exists(), "a folder was made before the check"
    assert str(tmp_path) not in str(caught.value)
    outside = tmp_path / "elsewhere.pem"
    outside.write_text("x", encoding="utf-8")
    (tmp_path / "keys").mkdir()
    with pytest.raises(ValueError) as caught:
        key_path(outside, tmp_path / "keys")
    assert str(tmp_path) not in str(caught.value)
    for loader, target in ((load_private_key, tmp_path / "none.pem"), (load_public_key, tmp_path)):
        with pytest.raises(pathguard.PathRefused) as caught:
            loader(target)
        assert str(tmp_path) not in str(caught.value)


def test_the_failure_audit_code_of_score_is_the_refusal_name(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from hadavin_sdk import cli
    from hadavin_sdk.k1b import report as report_mod
    from hadavin_sdk.k1b import score as score_mod
    from hadavin_sdk.k1b.score import REPORT_DIR

    assert "`PathRefused`" in bullet("The failure audit code of `score`")
    out = tmp_path / "out"
    out.mkdir()

    def fake_score(
        *_a, **_k
    ):  # runs after the folder check; plants the folder that blocks the report name
        (out / REPORT_DIR / "score-report.md").mkdir(parents=True)
        return SimpleNamespace(answers_sha256="a", outputs_digest="b", runs=[])

    monkeypatch.setattr(score_mod, "score", fake_score)
    monkeypatch.setattr(report_mod, "render_score_report", lambda _res: "x")
    events = []

    class Audit:
        def emit(self, *a, **k):
            events.append(("emit", k.get("result")))

        def emit_outcome(self, *a, **k):
            events.append(("outcome", k.get("result"), k.get("error_code")))

    args = SimpleNamespace(
        outputs=out, answers=tmp_path / "a", cause_list=tmp_path, bundles=tmp_path
    )
    with pytest.raises(pathguard.PathRefused):
        cli.score_cmd(Audit(), args)
    assert ("outcome", "failed", "PathRefused") in events


def test_local_dir_refuses_an_id_drops_the_outcome_and_skips_a_link(tmp_path, caplog):
    from hadavin_sdk.audit import LocalDirSink
    from hadavin_sdk.audit.protocol import AuditUnavailable
    from hadavin_sdk.models import AuditEvent

    text = bullet("`LocalDirSink` refuses an event id")
    for claim in (
        "is NOT written",
        "`refused_events`",
        "a link inside the outbox is skipped",
        "only for such an id",
        "takes the same outbox path",
    ):
        assert claim in text, claim

    def event(event_id):
        item = AuditEvent(
            run_id="r1", domain="run", operation="state", principal="p", source="runtime"
        )
        item.event_id = event_id
        return item

    sink = LocalDirSink(tmp_path / "aud")
    with pytest.raises(AuditUnavailable) as caught:
        sink.write_intent(event("a:b"))
    assert "a:b" not in str(caught.value)
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.audit.local_dir"):
        assert sink.write_outcome(event("c?d")) is None
    assert sink.refused_events == 1 and sink._pending == []
    assert not list(sink.objects.glob("*")) if sink.objects.exists() else True
    assert all("c?d" not in r.getMessage() for r in caplog.records)
    sink.outbox.mkdir(parents=True, exist_ok=True)
    (sink.outbox / "target.json").write_text("not json", encoding="utf-8")
    (sink.outbox / "linked.json").symlink_to(sink.outbox / "target.json")
    sink.reconcile()
    assert not (sink.outbox / "corrupt" / "linked.json").exists()


def test_pin_an_error_from_the_operating_system_is_a_fixed_refusal(tmp_path):
    text = bullet("An error from the operating system while a typed path is checked")
    for claim in (
        "R10",
        "`PathRefused: <argument>: cannot be resolved`",
        "File name too long",
        "a NUL",
        "`signer.key_path`",
        "`registry`",
        "at most 252 bytes",
        "13 sites",
    ):
        assert claim in text, claim
    assert pathguard.MAX_COMPONENT_BYTES == 255
    with pytest.raises(
        pathguard.PathRefused, match="^folder: too long$"
    ):  # over 255 bytes: R5, before the system
        pathguard.operator_dir(tmp_path / ("a" * 256), what="folder", must_exist=False)


def test_the_entry_names_the_link_to_another_folder_case_and_the_vault_risk():
    """The break for operator-typed files is named in plain words, and so is the weaker Vault form (read from the code)."""
    text = bullet("R3, R6, R7 and R12 apply to")
    for claim in (
        "a link pointing into a different folder is refused",
        "the link's target must lie inside the link's own folder, subfolders included",
        "/run/secrets.d/1/key",
        "without `must_exist` or `kind`",
        "nothing here says that any SonarCloud finding is cleared",
    ):
        assert claim in text, claim
    vault = (Path(pathguard.__file__).parent / "actions" / "secrets_vault.py").read_text(
        encoding="utf-8"
    )
    call = vault[vault.index("pathguard.join(", vault.index("vault sign-in token file") - 200) :][
        :200
    ]
    assert "must_exist" not in call and "kind=" not in call, (
        "the entry says the vault read is the weaker form"
    )


def test_the_sweep_sites_the_entry_counts_are_the_ones_in_the_source():
    """The 13 sites in 10 files named in the sweep sentence: each is a place where a derived name is built, found by a text
    search of its file (a site that is built twice in one file is listed once per site, with how many times the text occurs)."""
    src = Path(pathguard.__file__).parent
    sites = [  # (site, file, text, at least this many times in the file)
        ("replay output name", "k1b/replay.py", 'f"{b.case_id}.json"', 1),
        ("atomic_write temp name", "k1b/atomic.py", 'f".{name}.{secrets.token_hex(8)}.tmp"', 1),
        ("score read name", "k1b/score.py", 'f"{case_id}.json"', 1),
        ("bundle write limit", "k1b/bundle.py", 'f"{case}.json"', 1),
        ("LocalDirSink object name", "audit/local_dir.py", 'key = f"{event.event_id}.json"', 1),
        ("LocalDirSink outbox temp name", "audit/local_dir.py", 'f".tmp-{event.event_id}"', 1),
        (
            "LocalDirSink outbox final name",
            "audit/local_dir.py",
            'self.outbox, f"{event.event_id}.json"',
            1,
        ),
        ("evals golden name", "evals.py", 'f"{agent_id}.jsonl"', 1),
        ("registry golden name", "registry.py", 'f"{agent_id}.jsonl"', 1),
        ("registry tools file", "registry.py", 'f"{agent_id}.yaml"', 1),
        ("tool module file", "tools.py", 'f"{parts[-1]}.py"', 1),
        ("llm.fake recording", "llm/fake.py", 'f"{digest}-{attempt}.json"', 1),
        ("audit anchor name", "audit/anchors.py", 'f"{PREFIX}{seq:012d}.json"', 1),
    ]
    assert len(sites) == 13 and len({file for _, file, _, _ in sites}) == 10
    assert "13 sites in 10 files" in ENTRY
    missing = [
        name
        for name, file, text, least in sites
        if (src / file).read_text(encoding="utf-8").count(text) < least
    ]
    assert not missing, missing


def test_what_is_accepted_facts_in_the_entry_are_true(tmp_path):
    from hadavin_sdk.k1b.atomic import atomic_write

    text = bullet("What is accepted")
    for claim in (
        "255 bytes",
        "`sub/../real.txt`",
        "joiner and variation",
        "a link",
        "22 more bytes",
    ):
        assert claim in text, claim
    name = "n" * pathguard.MAX_COMPONENT_BYTES
    assert pathguard.component(name, what="n") == name
    assert pathguard.join(tmp_path, name, what="n").name == name
    assert pathguard.inside(tmp_path, tmp_path / name, what="n").name == name
    with pytest.raises(pathguard.PathRefused):
        atomic_write(tmp_path, name, "x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "real.txt").write_text("x", encoding="utf-8")
    assert (
        pathguard.inside(tmp_path, tmp_path / "sub" / ".." / "real.txt", what="n").name
        == "real.txt"
    )
    with pytest.raises(pathguard.PathRefused):
        pathguard.join(tmp_path, "sub", "..", "real.txt", what="n")
    for char in (chr(0x200D), chr(0xFE0F), chr(0xAD)):
        with pytest.raises(pathguard.PathRefused):
            pathguard.operator_dir(tmp_path / f"a{char}b", what="n", must_exist=False)


def test_control_a_replay_that_stops_writes_failed_txt_and_never_hides_the_first_error():
    """The behaviour is run in ``test_a_failed_replay_writes_the_marker_even_into_an_empty_folder`` and the two tests next to
    it (error, refusal, Ctrl-C, a marker that cannot be written); here the entry's words are tied to them."""
    text = bullet("When `replay` stops after the output folder exists")
    for claim in (
        "`FAILED.txt`",
        "also into an empty folder",
        "Ctrl-C",
        "`pathguard.operator_dir`",
        "a note",
    ):
        assert claim in text, claim
    batch3 = (ROOT / "tests" / "test_pathguard_batch3.py").read_text(encoding="utf-8")
    batch4 = (ROOT / "tests" / "test_pathguard_batch4.py").read_text(encoding="utf-8")
    for name in (
        "test_a_failed_replay_writes_the_marker_even_into_an_empty_folder",
        "test_a_marker_that_cannot_be_written_never_replaces_the_original_error",
    ):
        assert f"def {name}(" in batch3, name
    assert (
        "def test_replay_keeps_the_first_error_and_names_it_when_marking_is_interrupted(" in batch4
    )


def test_hash_files_fake_llm_judge_and_secrets_folder_go_through_pathguard():
    root = ROOT / "src" / "hadavin_sdk"
    assert "`FakeLLM` also checks the recording file name" in bullet(
        "`hashing.hash_files`, `FakeLLM`"
    )
    for rel in ("hashing.py", "llm/fake.py", "guard/judge.py", "actions/secrets_file.py"):
        assert "pathguard." in (root / rel).read_text(encoding="utf-8"), rel


# (file, function, the guard that returns the checked path): the read follows within SPAN lines of the check
LAST_CHECKS = [
    ("k1b/score.py", "load_answers", "join"),
    ("k1b/score.py", "_recorded_digest", "join"),
    ("hashing.py", "hash_files", "join"),
    ("actions/secrets_file.py", "MountedFileProvider._fetch", "join"),
    ("audit/signer.py", "build_local", "join"),
    ("audit/signer.py", "load_private_key", "join"),
    ("audit/signer.py", "load_public_key", "join"),
    ("guard/judge.py", "qualify", "join"),
    ("actions/secrets_vault.py", "connect", "join"),
]
SPAN = 14  # the refusal handling and, for the secrets reader, the open flags sit between the check and the read


def _function(tree: ast.AST, dotted: str) -> ast.AST:
    scope: ast.AST = tree
    for part in dotted.split("."):
        scope = next(
            n
            for n in ast.walk(scope)
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part
        )
    return scope


@pytest.mark.parametrize(("rel", "func", "guard"), LAST_CHECKS)
def test_the_last_check_sits_on_the_lines_right_before_the_read_and_only_its_path_is_read(
    rel, func, guard
):
    text = bullet("One last check right before each read.")
    assert f"`pathguard.{guard}`" in text
    tree = ast.parse((ROOT / "src" / "hadavin_sdk" / rel).read_text(encoding="utf-8"))
    fn = _function(tree, func)
    guards = {}  # name -> line of the assignment from the guard
    for node in ast.walk(fn):
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == guard
            and isinstance(node.targets[0], ast.Name)
        ):
            guards[node.targets[0].id] = node.lineno
    assert guards, f"{rel}:{func} holds no {guard} assignment"
    reads = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            receiver = f.value if isinstance(f, ast.Attribute) else None
            first = node.args[0] if node.args else None
            for target in (receiver, first):
                if (
                    isinstance(target, ast.Name)
                    and target.id in guards
                    and getattr(f, "attr", getattr(f, "id", ""))
                    in {"read_bytes", "read_text", "open"}
                ) or (
                    isinstance(target, ast.Name)
                    and target.id in guards
                    and (isinstance(f, ast.Attribute) and f.attr == "open")
                ):
                    reads.append((target.id, node.lineno))
    assert reads, f"{rel}:{func} reads no guarded path"
    assert all(0 <= line - guards[name] <= SPAN for name, line in reads), (reads, guards)


def test_errors_in_the_cause_list_bundle_and_hashing_checks_have_no_chain(tmp_path):
    from hadavin_sdk.hashing import hash_files
    from hadavin_sdk.k1b.bundle import load_bundle
    from hadavin_sdk.k1b.causelist import load_cause_list

    bullet("Errors in the cause-list, bundle and hashing checks")
    (tmp_path / "cause").mkdir()
    (tmp_path / "cause" / "services.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "case-001").mkdir()
    (tmp_path / "case-001" / "manifest.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "x").mkdir()
    for call in (
        lambda: load_cause_list(tmp_path / "cause"),
        lambda: load_bundle(tmp_path / "case-001"),
        lambda: hash_files(tmp_path / "bad", ["x"]),
    ):
        raised: BaseException | None = None
        try:
            call()
        except (
            ConfigError,
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            AttributeError,
        ) as exc:  # the usual classes: only the chain is asserted
            raised = exc
        assert raised is not None
        assert raised.__cause__ is None
        assert raised.__suppress_context__ or raised.__context__ is None


def test_control_the_sonar_claim_says_nothing_is_cleared():
    text = bullet("What this does not claim")
    assert "does not claim that any SonarCloud finding is cleared" in text
    assert not re.search(r"(?<!not )\b(clears|fixes) the SonarCloud", ENTRY)


def test_control_the_entry_states_the_limits_it_knows():
    text = bullet("What this does not claim")
    for limit in ("260 characters", "hard links", "mount points", "junctions"):
        assert limit in text


def test_control_the_entry_does_not_say_for_any_reason_or_everywhere():
    assert "for any reason" not in ENTRY and "everywhere" not in ENTRY.lower()


def test_control_the_exception_list_the_entry_names_has_seven_columns_and_a_reason_each():
    path = ROOT / "tests" / "fixtures" / "pathguard_exceptions.txt"
    rows = [
        r
        for r in path.read_text(encoding="utf-8").splitlines()
        if r.strip() and not r.startswith("#")
    ]
    assert rows and all(len(r.split(" | ")) == 7 and r.split(" | ")[6].strip() for r in rows)


def test_control_the_backslash_is_written_once_in_the_rules():
    assert "`/` or `\\`" in bullet("The rules (R1 to R13)")
    assert "`\\\\`" not in bullet("The rules (R1 to R13)")


# What the suppression bullet says: created or rewritten in full (no suppression of any kind) and edited (the count of each
# marker it had on origin/main, stated here so a new one cannot be added).
REWRITTEN = {
    "src/hadavin_sdk/pathguard.py",
    "src/hadavin_sdk/pathtext.py",
    "src/hadavin_sdk/k1b/atomic.py",
    "src/hadavin_sdk/k1b/score.py",
    "src/hadavin_sdk/k1b/replay.py",
    "src/hadavin_sdk/k1b/bundle.py",
    "src/hadavin_sdk/k1b/causelist.py",
    "src/hadavin_sdk/hashing.py",
    "src/hadavin_sdk/llm/fake.py",
    "src/hadavin_sdk/actions/secrets_file.py",
    "src/hadavin_sdk/guard/judge.py",
    "src/hadavin_sdk/audit/signer.py",
}
EDITED_BASELINE = {  # file -> {marker: count on origin/main}
    "src/hadavin_sdk/cli.py": {"no" + "qa": 4},
    "src/hadavin_sdk/config.py": {"no" + "qa": 2, "type:" + " ignore": 1, "no" + "sec": 1},
    "src/hadavin_sdk/audit/local_dir.py": {"no" + "qa": 4},
    "src/hadavin_sdk/registry.py": {},
    "src/hadavin_sdk/tools.py": {"no" + "qa": 5, "no" + "sec": 2},
    "src/hadavin_sdk/actions/secrets_vault.py": {"no" + "qa": 1},
}
MARKERS = (
    "no" + "sonar",
    "no" + "qa",
    "no" + "sec",
    "type:" + " ignore",
    "fmt:" + " skip",
    "fmt:" + " off",
    "pragma:" + " no cover",
)


def test_the_suppression_bullet_matches_the_files_and_the_counts():
    text = bullet("Suppression comments.")
    for name in (
        "config.py",
        "cli.py",
        "audit/local_dir.py",
        "audit/signer.py",
        "actions/secrets_vault.py",
        "registry.py",
        "tools.py",
    ):
        assert f"`{name}`" in text, name
    src = ROOT / "src" / "hadavin_sdk"
    importing = {
        p.relative_to(ROOT).as_posix()
        for p in src.rglob("*.py")
        if "pathguard" in p.read_text(encoding="utf-8")
    }
    # every package file that calls pathguard is in the stated lists: a new caller must be added here, on purpose
    assert importing <= REWRITTEN | set(EDITED_BASELINE) | {"src/hadavin_sdk/audit/signer.py"}, (
        sorted(importing - REWRITTEN - set(EDITED_BASELINE))
    )
    for rel in sorted(REWRITTEN | set(EDITED_BASELINE)):
        lowered = (ROOT / rel).read_text(encoding="utf-8").lower()
        allowed = EDITED_BASELINE.get(rel, {})
        for marker in MARKERS:
            assert lowered.count(marker) <= allowed.get(marker, 0), f"{rel}: {marker}"


def test_control_every_bullet_of_the_entry_is_named_by_a_claim_test():
    """A new bullet with no test of its own fails here: each bullet must be looked up by ``bullet(...)`` in this file."""
    used = re.findall(r'bullet\(\s*"([^"]+)"', Path(__file__).read_text(encoding="utf-8"))
    missing = [b[:60] for b in BULLETS if not any(b.startswith(f"- **{u}") for u in used)]
    assert missing == []


def test_pin_every_range_count_in_the_entry_is_the_length_of_the_code_table():
    """The count is derived, not typed: every ``<number> ranges`` in the entry must equal ``len(CONTROL_RANGES)``, and the
    entry must give it at least twice (the rule list and the accepted list)."""
    counts = [int(n) for n in re.findall(r"\b(\d+) ranges\b", ENTRY)]
    assert len(counts) >= 2, counts
    assert set(counts) == {len(pathguard.CONTROL_RANGES)}, (counts, len(pathguard.CONTROL_RANGES))
