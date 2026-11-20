"""d-fix27: only the STORE step may count as "store down". An OSError from reading a configuration file
(config.yaml, the registry files) is a configuration error: exit 2 naming the file and the cause, at start and on
every degraded re-check; a connectivity OSError from the store step still degrades and recovers in process."""

from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk.errors import ConfigError as AnyConfigError
from hadavin_sdk.triggers import worker
from tests.triggers.test_d_fix26_degraded_fatal import (
    _fast_recheck,
    _good_registry,
    _patch_start,
    _run_main_in_thread,
)
from tests.triggers.test_worker import (
    _app,
    _settings,
    rt,  # noqa: F401 - fixture
)


@pytest.fixture(autouse=True)
def _no_worker_log_handler():
    yield
    worker._unlog_stderr()


def _no_build(*_a, **_k):
    raise AssertionError("build must not be reached: the configuration cannot be read")


def _degraded_marker(monkeypatch):
    seen: list[int] = []
    monkeypatch.setattr(worker, "_serve_degraded", lambda *_a: seen.append(1) or 99)
    return seen


# --- (a) config.yaml unreadable at start ---------------------------------------------------------------


@pytest.mark.parametrize("how", ["directory", "permission", "undecodable"])
def test_a_config_yaml_that_cannot_be_read_exits_2_naming_the_file(
    monkeypatch, capsys, tmp_path, how
):
    import hadavin_sdk.app

    monkeypatch.setattr(hadavin_sdk.app, "build", _no_build)
    degraded = _degraded_marker(monkeypatch)
    cfg = tmp_path / "config.yaml"
    if how == "directory":
        cfg.mkdir()
    elif how == "undecodable":
        cfg.write_bytes(b"\xff\xfe\x00bad")
    else:
        cfg.write_text("environment: demo\n")
        real = Path.read_text

        def read_text(self, *a, **k):
            if self.name == "config.yaml":
                raise PermissionError(13, "Permission denied")  # no filename on purpose
            return real(self, *a, **k)

        monkeypatch.setattr(Path, "read_text", read_text)
    code = worker.main(["--port", "0", "--config-dir", str(tmp_path)])
    err = capsys.readouterr().err
    assert (code, degraded) == (2, [])
    assert "config.yaml" in err and "could not be read" in err
    assert {"directory": "IsADirectoryError", "permission": "PermissionError"}.get(
        how, "UnicodeDecodeError"
    ) in err


# --- (b) the registry files unreadable at start --------------------------------------------------------


@pytest.mark.parametrize("how", ["directory", "undecodable", "permission"])
def test_a_registry_file_that_cannot_be_read_exits_2_naming_the_file(
    monkeypatch, capsys, tmp_path, how
):
    import hadavin_sdk.app
    import hadavin_sdk.config

    monkeypatch.setattr(hadavin_sdk.app, "build", _no_build)
    monkeypatch.setattr(
        hadavin_sdk.config,
        "load_config",
        lambda _d=None: SimpleNamespace(triggers=_settings(), environment="demo", root=tmp_path),
    )
    degraded = _degraded_marker(monkeypatch)
    path = tmp_path / "principals.yaml"
    if how == "directory":
        path.mkdir()
    elif how == "undecodable":
        path.write_bytes(b"\xff\xfe\x00bad")
    else:
        path.write_text("[]\n")
        real = Path.read_text

        def read_text(self, *a, **k):
            if self.name == "principals.yaml":
                raise PermissionError(13, "Permission denied")
            return real(self, *a, **k)

        monkeypatch.setattr(Path, "read_text", read_text)
    code = worker.main(["--port", "0"])
    err = capsys.readouterr().err
    assert (code, degraded) == (2, [])
    # the class name always; the real file path when the error carries one (never only the generic fallback text,
    # which also contains "principals.yaml")
    cls = {"directory": "IsADirectoryError", "permission": "PermissionError"}.get(
        how, "UnicodeDecodeError"
    )
    assert cls in err
    if how == "directory":
        assert str(path) in err
    assert "could not be read" in err


# --- (c) the file becomes unreadable while degraded -----------------------------------------------------


def test_a_config_file_that_becomes_unreadable_during_degraded_retries_exits_2(
    monkeypatch, capsys, tmp_path
):
    _fast_recheck(monkeypatch)
    import hadavin_sdk.config

    state = {"readable": True}
    calls: list[int] = []

    def load_config(_d=None):
        if not state["readable"]:
            raise IsADirectoryError(21, "Is a directory", str(tmp_path / "config.yaml"))
        return SimpleNamespace(triggers=_settings(), environment="demo", root=tmp_path)

    def build(*_a, **_k):
        calls.append(1)
        state["readable"] = (
            False  # the first attempt fails as the store is down; then the file breaks
        )
        raise ConnectionRefusedError("down")

    _patch_start(monkeypatch, _settings(), build)
    monkeypatch.setattr(hadavin_sdk.config, "load_config", load_config)
    out, thread = _run_main_in_thread(["--port", "0"])
    assert not thread.is_alive(), "the degraded worker retried an unreadable config file forever"
    assert out == [2] and calls == [1]
    err = capsys.readouterr().err
    assert "config.yaml" in err and "IsADirectoryError" in err


def test_a_registry_file_that_becomes_unreadable_during_degraded_retries_exits_2(
    monkeypatch, capsys, tmp_path
):
    _fast_recheck(monkeypatch)
    import hadavin_sdk.registry

    state = {"readable": True}

    calls: list[int] = []

    def build(*_a, **_k):
        calls.append(1)
        state["readable"] = False
        raise ConnectionRefusedError("down")

    def load_registry(_c):
        if not state["readable"]:
            raise PermissionError(13, "Permission denied", str(tmp_path / "principals.yaml"))
        return _good_registry()

    _patch_start(monkeypatch, _settings(), build)
    monkeypatch.setattr(hadavin_sdk.registry, "load_registry", load_registry)
    out, thread = _run_main_in_thread(["--port", "0"])
    assert not thread.is_alive()
    assert out == [2] and len(calls) == 1
    err = capsys.readouterr().err
    assert "principals.yaml" in err and "PermissionError" in err


def test_a_config_file_error_inside_build_is_a_config_error_not_store_down(
    monkeypatch, capsys, tmp_path
):
    """`build` reads the config again: a file error under the config folder is not a connectivity error."""
    import hadavin_sdk.config

    def build(*_a, **_k):
        raise PermissionError(13, "Permission denied", str(tmp_path / "config.yaml"))

    _patch_start(monkeypatch, _settings(), build)
    monkeypatch.setattr(
        hadavin_sdk.config,
        "load_config",
        lambda _d=None: SimpleNamespace(triggers=_settings(), environment="demo", root=tmp_path),
    )
    degraded = _degraded_marker(monkeypatch)
    assert worker.main(["--port", "0"]) == 2
    assert degraded == []
    assert "config.yaml" in capsys.readouterr().err


# --- (d) connectivity OSError of the store step still degrades and recovers -----------------------------


def test_a_connection_refused_from_the_store_step_degrades_and_recovers_in_process(
    monkeypatch,
    capsys,
    rt,  # noqa: F811
):
    _fast_recheck(monkeypatch)
    settings = _settings()
    app = _app(rt, settings)
    calls: list[int] = []

    def build(*_a, **_k):
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionRefusedError(111, "Connection refused")
        return app

    _patch_start(monkeypatch, settings, build)
    stopped = threading.Event()
    real_serve = worker.serve

    def serve(server, runner):
        def later():
            while len(calls) < 3 or not getattr(runner, "_runner", None):
                if stopped.wait(0.02):
                    return
            server.shutdown()

        threading.Thread(target=later, daemon=True).start()
        try:
            return real_serve(server, runner)
        finally:
            stopped.set()

    monkeypatch.setattr(worker, "serve", serve)
    out, thread = _run_main_in_thread(["--port", "0"])
    assert not thread.is_alive()
    assert out == [0]
    assert len(calls) == 3  # two refusals retried in process, then served
    assert "config error" not in capsys.readouterr().err


def test_a_connection_refused_is_not_a_file_error_even_with_a_config_root(
    monkeypatch, capsys, tmp_path
):
    import hadavin_sdk.config

    def build(*_a, **_k):
        raise ConnectionRefusedError(111, "Connection refused")

    _patch_start(monkeypatch, _settings(), build)
    monkeypatch.setattr(
        hadavin_sdk.config,
        "load_config",
        lambda _d=None: SimpleNamespace(triggers=_settings(), environment="demo", root=tmp_path),
    )
    degraded = _degraded_marker(monkeypatch)
    assert worker.main(["--port", "0"]) == 99
    assert degraded == [1]


# --- a secret file read error and a migrate/grant error after the store returns are fatal ----------------


def test_an_oserror_reading_a_secret_is_a_config_error_on_a_retry(
    monkeypatch,
    capsys,
    rt,  # noqa: F811
):
    _fast_recheck(monkeypatch)
    settings = _settings()
    app = _app(rt, settings)

    def broken(_name):
        raise PermissionError(13, "Permission denied", "/secrets/sender")

    app.trigger_secret = broken
    calls: list[int] = []

    def build(*_a, **_k):
        calls.append(1)
        if len(calls) < 2:
            raise ConnectionRefusedError("down")
        return app

    _patch_start(monkeypatch, settings, build)
    out, thread = _run_main_in_thread(["--port", "0"])
    assert not thread.is_alive()
    assert out == [2]
    assert "a secret could not be read" in capsys.readouterr().err


def test_a_migrate_or_grant_config_error_from_build_after_the_store_returns_is_fatal(
    monkeypatch, capsys
):
    _fast_recheck(monkeypatch)
    calls: list[int] = []

    def build(*_a, **_k):
        calls.append(1)
        if len(calls) == 1:
            raise ConnectionRefusedError("down")
        raise AnyConfigError("migration 7 not applied: grant missing")

    _patch_start(monkeypatch, _settings(), build)
    out, thread = _run_main_in_thread(["--port", "0"])
    assert not thread.is_alive()
    assert out == [2] and len(calls) == 2
    assert "config error" in capsys.readouterr().err


def test_the_module_text_states_that_a_build_config_error_is_fatal():
    doc = worker.__doc__
    assert "migrate" in doc and "grant" in doc and "exit 2" in doc


def test_the_comment_does_not_claim_a_defaults_name_that_does_not_exist():
    from hadavin_sdk import defaults

    src = Path(worker.__file__).read_text()
    head = src[: src.index("MAX_RUNNING_CEILING: Final")]
    if not hasattr(defaults, "TRIGGER_MAX_RUNNING"):
        assert "defaults.TRIGGER_MAX_RUNNING" not in head
        assert "not yet in this tree" in head


def test_a_config_file_that_is_a_symlink_to_a_target_outside_the_root_is_a_config_error(tmp_path):
    root = tmp_path / "cfg"
    root.mkdir()
    outside = tmp_path / "mounted" / "secret.yaml"
    outside.parent.mkdir()
    outside.write_text("x: 1\n")
    link = root / "principals.yaml"
    link.symlink_to(outside)
    exc = PermissionError(13, "Permission denied", str(link))
    assert worker._is_config_file_error(exc, root) is True  # lexically under the root
    assert worker._is_config_file_error(PermissionError(13, "x", str(outside)), root) is False
    assert (
        worker._is_config_file_error(PermissionError(13, "x", str(root / "a.yaml")), root) is True
    )
    assert worker._is_config_file_error(PermissionError(13, "x"), root) is False


@pytest.mark.parametrize("raised", [SystemExit(5), GeneratorExit(), KeyboardInterrupt()])
def test_a_base_exception_from_a_recheck_is_fatal_exit_3_not_a_silent_dead_thread(
    monkeypatch, capsys, raised
):
    _fast_recheck(monkeypatch)
    calls: list[int] = []

    def build(*_a, **_k):
        calls.append(1)
        if len(calls) == 1:
            raise ConnectionRefusedError("down")
        raise raised

    _patch_start(monkeypatch, _settings(), build)
    out, thread = _run_main_in_thread(["--port", "0"])
    assert not thread.is_alive(), "the recover thread died and the worker stayed degraded forever"
    assert out == [3] and len(calls) == 2
    err = capsys.readouterr().err
    assert type(raised).__name__ in err and "Traceback" not in err
