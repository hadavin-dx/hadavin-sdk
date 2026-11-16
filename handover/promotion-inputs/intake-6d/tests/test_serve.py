"""``intake serve``: the start sequence, exit codes and stop (package 6d, brief-v3 12). The scanner is a scripted stand-in until the inbox package is merged."""

from __future__ import annotations

import dataclasses
import socket
import threading

import pytest
from service_helpers import HOSTS, NAV, FakeScanner, build, fast_limits, get, install_stand_ins, raw, reset_scanner, start_service

from conftest import settings_for_tests
from intake import budget, cli, inbox, lockfile, model, service, settings, workqueue
from intake.codes import ConfigError, Refused


def free_port() -> int:
    """A port that is free on all three test addresses."""
    for _ in range(50):
        with socket.socket() as s0:
            s0.bind(("127.0.0.1", 0))
            port = s0.getsockname()[1]
        ok = True
        for h in HOSTS.values():
            with socket.socket() as s1:
                try:
                    s1.bind((h, port))
                except OSError:
                    ok = False
        if ok:
            return port
    raise RuntimeError("no free port")


@pytest.fixture
def fake_scanner(monkeypatch):
    install_stand_ins(monkeypatch)
    reset_scanner()
    monkeypatch.setattr(inbox, "Scanner", FakeScanner)


def with_ledger(tmp_path, **kw):
    return settings_for_tests(tmp_path, with_ledger=True)


def test_serve_refuses_changed_name_regex(tmp_path, fake_scanner):
    s = with_ledger(tmp_path)
    bad = dataclasses.replace(s, service=dataclasses.replace(s.service, name_regex="^[a-z]{1,10}$"))
    with pytest.raises(ConfigError) as e:
        service.start(bad, hosts=HOSTS, limits=fast_limits())
    assert e.value.code == "bad_config"
    assert not lockfile.is_held(s.intake_home / "serve.lock")


def test_second_serve_exit_3_and_lock_released(tmp_path, monkeypatch, fake_scanner):
    s = with_ledger(tmp_path)
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=0))
    run = service.start(s, hosts=HOSTS, limits=fast_limits())
    try:
        with pytest.raises(ConfigError) as e:
            service.start(s, hosts=HOSTS, limits=fast_limits())
        assert e.value.code == "serve_running"
    finally:
        run.stop()
    assert not lockfile.is_held(s.intake_home / "serve.lock")
    run2 = service.start(s, hosts=HOSTS, limits=fast_limits())  # the lock is free again after a normal stop
    run2.stop()


def test_port_in_use_exit_3(tmp_path, fake_scanner):
    s = with_ledger(tmp_path)
    port = free_port()
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=port))
    blocker = socket.socket()
    blocker.bind((HOSTS["dash"], port))  # one of the three addresses is taken
    blocker.listen()
    try:
        with pytest.raises(ConfigError) as e:
            service.start(s, hosts=HOSTS, limits=fast_limits())
        assert e.value.code == "port_in_use"
        for h in (HOSTS["token"], HOSTS["work"]):  # the two that were bound were closed again
            with socket.socket() as probe:
                probe.bind((h, port))
        assert not lockfile.is_held(s.intake_home / "serve.lock")
    finally:
        blocker.close()
    run = service.start(s, hosts=HOSTS, limits=fast_limits())
    run.stop()


def test_ledger_missing_exit_3(tmp_path, fake_scanner):
    s = settings_for_tests(tmp_path)  # no `intake init`: no spend ledger
    with pytest.raises(ConfigError) as e:
        service.start(s, hosts=HOSTS, limits=fast_limits())
    assert e.value.code == "ledger_missing"
    assert not lockfile.is_held(s.intake_home / "serve.lock")


def test_schema_mismatch_exit_3(tmp_path, fake_scanner):
    s = with_ledger(tmp_path)
    workqueue.connect(s).close()
    c = workqueue.connect(s)
    try:
        from queue_helpers import drop_triggers

        drop_triggers(c)
        c.execute("DELETE FROM meta WHERE k = 'schema_version'")  # the version row is not the one this build wants
        c.commit()
    finally:
        c.close()
    with pytest.raises((ConfigError, Refused)) as e:
        service.start(s, hosts=HOSTS, limits=fast_limits())
    assert e.value.code == "bad_config"
    assert not lockfile.is_held(s.intake_home / "serve.lock")


def test_fake_on_real_folder_exit_2(tmp_path, monkeypatch, fake_scanner):
    s = with_ledger(tmp_path)
    monkeypatch.setattr(settings, "under_temp_folder", lambda local: False)
    with pytest.raises(Refused) as e:
        service.start(s, hosts=HOSTS, limits=fast_limits())
    assert e.value.code == "fake_on_real_folder"
    assert not lockfile.is_held(s.intake_home / "serve.lock")


def test_deferred_start_exit_2(tmp_path, monkeypatch, fake_scanner):
    s = with_ledger(tmp_path)
    real = model.build_guarded

    def deferred(st=None):
        g = real(st)
        g.deferred = "prices_missing"
        return g

    monkeypatch.setattr(model, "build_guarded", deferred)
    with pytest.raises(Refused) as e:
        service.start(s, hosts=HOSTS, limits=fast_limits())
    assert e.value.code == "prices_missing"
    assert not lockfile.is_held(s.intake_home / "serve.lock")


def test_recover_received_at_start(tmp_path, fake_scanner):
    s = with_ledger(tmp_path)
    rec = workqueue.insert_received(s, "r.txt", "d" * 64, "text", s.tenant_id, "r")
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=0))
    run = service.start(s, hosts=HOSTS, limits=fast_limits())
    try:
        got = workqueue.get(s, rec.id)
        assert got.state == "NEEDS_PERSON" and "L02" in got.flags
    finally:
        run.stop()


def test_start_lines_and_log_level(tmp_path, capsys, fake_scanner):
    s = with_ledger(tmp_path)
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=0))
    run = service.start(s, hosts=HOSTS, limits=fast_limits())
    try:
        out = capsys.readouterr().out.splitlines()
        assert out[0] == "config: ok" and out[1] == "queue: ok (recovered 0)"
        assert out[2] == "key HADAVIN_WEBHOOK_SECRET: ok" and out[3] == "key HADAVIN_APPROVER_PASSPHRASE: ok"
        p = run.ports
        assert (
            out[4]
            == f"serving: token http://127.0.0.1:{p['token']}/ work http://127.0.0.21:{p['work']}/ dashboards http://127.0.0.22:{p['dash']}/"
        )
        assert out[5] == "backend: fake" and out[6] == "log: normal"
    finally:
        run.stop()


def test_settle_failed_503_then_exit_3(tmp_path, monkeypatch, fake_scanner):
    s = with_ledger(tmp_path)
    port = free_port()
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=port))
    FakeScanner.script = [ConfigError("settle_failed", "x")]
    code = []
    t = threading.Thread(target=lambda: code.append(service.serve(s, hosts=HOSTS, limits=fast_limits())))
    t.start()
    token = {"X-Hadavin-Token": __import__("conftest").fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]}
    import time

    for _ in range(50):
        try:
            r = raw((HOSTS["token"], port), build("POST", "/events/scan", f"{HOSTS['token']}:{port}", token, b""))
            break
        except OSError:
            time.sleep(0.05)
    assert r.status == 503 and r.text == '{"error": "settle_failed"}'
    t.join(5)
    assert code == [3]  # the service stopped itself: exit 3


def test_normal_stop_returns_0(tmp_path, monkeypatch, fake_scanner):
    s = with_ledger(tmp_path)
    port = free_port()
    s = dataclasses.replace(s, service=dataclasses.replace(s.service, port=port))
    live = []
    real = service.start
    monkeypatch.setattr(service, "start", lambda *a, **k: live.append(real(*a, **k)) or live[-1])
    code = []
    t = threading.Thread(target=lambda: code.append(service.serve(s, hosts=HOSTS, limits=fast_limits())))
    t.start()
    import time

    for _ in range(100):
        if live:
            break
        time.sleep(0.05)
    assert raw((HOSTS["work"], port), build("GET", "/login", f"{HOSTS['work']}:{port}", NAV)).status == 200
    live[0].shared.stop.set()  # what Ctrl+C and a process stop do
    t.join(5)
    assert code == [0] and not lockfile.is_held(s.intake_home / "serve.lock")


def test_purge_while_serving(tmp_path, monkeypatch, fake_scanner, capsys):
    from queue_helpers import new_item

    e = start_service(tmp_path, monkeypatch)
    try:
        it = new_item(e.s, "inv1")
        monkeypatch.setenv("HADAVIN_LOCAL", str(e.s.local))
        monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
        assert cli.main(["purge", it.id, "--yes"]) == 0
        assert workqueue.get(e.s, it.id) is None
        assert get(e, "work", "/login", NAV).status == 200
    finally:
        e.close()


def test_cli_serve_exit_codes_and_no_traceback(tmp_path, monkeypatch, capsys, fake_scanner):
    s = settings_for_tests(tmp_path)  # no ledger: ledger_missing
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    assert cli.main(["serve"]) == 3
    err = capsys.readouterr().err
    assert "ledger_missing" in err and "Traceback" not in err
    budget.init(s)
    lock = lockfile.acquire(s.intake_home / "serve.lock")  # another serve holds the lock
    try:
        assert cli.main(["serve"]) == 3
        assert "serve_running" in capsys.readouterr().err
    finally:
        lockfile.release(lock)


# ---- the real scanner behind the service (package 6a's inbox) --------------------------------------------------------------------------------------
def _put(env, name):
    import os
    import time

    from conftest import MINI

    p = env.s.intake_home / "inbox" / name
    p.write_bytes((MINI / name).read_bytes())
    t = time.time() - 100
    os.utime(p, (t, t))


def test_real_scan_decide_export_end_to_end(tmp_path, monkeypatch):
    from urllib.parse import urlencode  # noqa: F401

    from service_helpers import form_post, sign_in

    from conftest import fake_secret_values
    from intake import exporter
    from intake.content_code import content_code

    order = []
    real_insert, real_call = workqueue.insert_received, model.GuardedModel.call
    monkeypatch.setattr(workqueue, "insert_received", lambda *a, **k: order.append("insert") or real_insert(*a, **k))
    monkeypatch.setattr(model.GuardedModel, "call", lambda self, req: order.append("model") or real_call(self, req))
    e = start_service(tmp_path, monkeypatch, with_scanner=False)
    try:
        for n in ("inv-A.txt", "inv-B.txt", "inv-C.txt"):
            _put(e, n)
        tok = {"X-Hadavin-Token": fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]}
        th, tp = e.token
        r = raw(e.token, build("POST", "/events/scan", f"{th}:{tp}", tok, b""))
        assert r.status == 200
        body = __import__("json").loads(r.body)
        assert set(body) == {"examined", "new", "refused", "duplicates", "remaining"} and body["examined"] == 3
        assert order[0] == "insert" and "model" in order  # the item is stored before the first model call
        assert order.index("insert") < order.index("model")
        items = workqueue.list_items(e.s)
        assert len(items) == len(body["new"]) == 2
        ready = [i for i in items if i.state == "READY"]
        assert ready, [i.state for i in items]
        it = ready[0]
        cookie, csrf = sign_in(e)
        p = "pass" + "P" * 30
        r = form_post(
            e,
            f"/item/{it.id}/decide",
            {"csrf": csrf, "decision": "approve", "reason": "", "content_code": content_code(it), "version": str(it.version)},
            cookies=cookie,
        )
        assert r.status == 200 and workqueue.get(e.s, it.id).state == "APPROVED"
        r = form_post(e, "/export", {"csrf": csrf, "passphrase": p}, cookies=cookie)
        assert r.status == 200 and exporter.csv_path(e.s).exists()
        assert workqueue.get(e.s, it.id).state == "EXPORTED"
        r2 = raw(
            e.token, build("POST", "/events/scan", f"{th}:{tp}", tok, b"")
        )  # scan_max_files is 2: the second scan takes the third file
        assert len(__import__("json").loads(r2.body)["new"]) == 1
        r3 = raw(e.token, build("POST", "/events/scan", f"{th}:{tp}", tok, b""))  # then everything is a duplicate
        assert __import__("json").loads(r3.body)["new"] == []
    finally:
        e.close()
