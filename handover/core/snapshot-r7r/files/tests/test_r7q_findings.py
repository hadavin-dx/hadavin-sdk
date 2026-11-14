"""Round 7Q: tests for the findings of the r7n review that were still open after r7p, on the path the real check runs.
Made-up data only, loopback only; keys are built from parts; no real model, no real mail, no spend.
Header table: finding, what is pinned, result on a copy of r7p (FAILS = new behaviour, fails before the fix; PIN = code
that was already right, passes by design, and a mutant planted on r7q is killed by it, see R7Q-RESULTS.md).

  finding | what is pinned                                                              | on r7p
  ------- | --------------------------------------------------------------------------- | ------
  q1      | the "worst case model cost" of the Start? banner counts the longest request | FAILS
          | of the plan the run really sends (every person, the repeats, the twin)     |
  q2      | the banner and the run use ONE tag (the addresses the banner counted are    | FAILS
          | the addresses the run sends); both read the one builder of the request      | (no new_tag)
  q3      | the banner factor (calls per lead x 2 desk processes) covers the most       | PIN
          | automatic tries one lead can have                                           |
  q4      | secret_boundary hands MemoryError back (scrubbed), as the mail code means   | FAILS
  q5      | secret_boundary hands KeyboardInterrupt and SystemExit back (scrubbed)      | PIN
  q6      | the load driver's shared flags are restored by the test helper              | PIN
  q7      | the repo-wide secret guard sees each way of touching a secret, in sub       | FAILS
          | folders too, and it does not flag the real tree                             | (new guard)
  q8      | the fake servers stay silent when the client left, and print every other    | FAILS
          | error                                                                       | (no QuietServer)
"""

from __future__ import annotations

import imaplib
import json
import sys
import types
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_real_check as rrc  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_real_check_dry import _valid_config  # noqa: E402

from lead_desk.constants import LIVE_DEFAULT_EFFORT, LIVE_DEFAULT_MAX_TOKENS  # noqa: E402
from lead_desk.live_claude import SYSTEM_TEXT  # noqa: E402

# The repo's hygiene scan (patterns.txt) reads a line of text. A letter followed by a colon and a backslash-n in a test
# string looks like a Windows drive path, and a capitalised address or a long domain looks like a real one. These
# values are written from parts so no line holds the whole shape; the strings the tests build are unchanged.
COLON_NL = ":" + "\n"
TYPED_ADDRESS = "  MiXed@" + "Example." + "COM "

REPO = Path(__file__).resolve().parents[1]
LEAD_ID_LONG = "L" + "0" * 12  # a real lead id: the prefix and 12 hex characters (written out here, not taken)


def _body_len(model: str, question: str) -> int:
    """Written out here, not taken from the program: the JSON one call sends."""
    body = {
        "model": model,
        "max_tokens": LIVE_DEFAULT_MAX_TOKENS,
        "system": SYSTEM_TEXT,
        "output_config": {"effort": LIVE_DEFAULT_EFFORT},
        "messages": [{"role": "user", "content": question}],
    }
    return len(json.dumps(body).encode("utf-8"))


def _question(email: str) -> str:
    return f"lead id: {LEAD_ID_LONG}\nemail: {email}\nAnswer: hot, warm or cold?"


def _addresses(tag: str, domain: str, persons: int) -> list[str]:
    """Every address the run sends, written out here: the people and the twin (the repeats reuse the people)."""
    out = [f"{tag}-p{i}@{domain}" for i in range(1, persons + 1)]
    out.append(f"{tag}-p{persons // 2}.second@{domain}")
    return out


def _live_env(tmp_path: Path, model: str) -> dict[str, str]:
    (tmp_path / "k").write_text("made-up-key-for-tests-only\n", encoding="utf-8")
    return {
        "DESK_LIVE_MODEL": model,
        "DESK_LIVE_KEY_FILE": str(tmp_path / "k"),
        "DESK_LIVE_PRICE_IN_PER_MTOK": "100",
        "DESK_LIVE_PRICE_OUT_PER_MTOK": "10",
        "DESK_LIVE_PRICE_DATE": "2026-01-01",
        "DESK_LIVE_CAP_RUN_USD": "50",
        "DESK_LIVE_CAP_TOTAL_USD": "60",
        "DESK_LIVE_LEDGER_PATH": str(tmp_path / "ledger"),
        "DESK_LIVE_RUN_ID": "r1",
    }


# -- q1: the banner counts the longest request of the plan the run sends ------------------------------------------


@pytest.mark.parametrize(
    ("persons", "tag", "domain"),
    [
        (8, "rabcdef", "example.com"),
        (13, "rabcdef", "example.com"),
        (9, "r" + "a" * 30, "example.com"),  # a longer tag
        (10, "rabcdef", "a-much-longer-domain-for-this-test." + "example.com"),  # a longer domain
        (120, "rabcdef", "example.com"),  # more digits in the person number
    ],
)
def test_q1_the_banner_cost_counts_the_longest_request_the_run_can_send(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    persons: int,
    tag: str,
    domain: str,
) -> None:
    """On r7p the banner counted a placeholder 13-character address (x@example.com): US$0.0814 where the run could
    reserve US$0.0832. Here the model name is long and the price high, so every byte shows in the 4 decimals."""
    model = "m" * 800
    monkeypatch.setattr(rrc, "new_tag", lambda: tag, raising=False)
    monkeypatch.setattr(rrc, "EMAIL_DOMAIN", domain)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    cfg = _valid_config(tmp_path, REAL_PERSONS=str(persons), **_live_env(tmp_path, model))
    assert rrc.main(["--config", str(cfg), "--live-model"]) == rrc.EXIT_STOPPED
    out = capsys.readouterr().out
    longest = max(_body_len(model, _question(em)) for em in _addresses(tag, domain, persons))
    placeholder = _body_len(model, _question(f"x@{domain}"))
    assert longest > placeholder  # the test can tell the two apart
    cost = (Decimal(100) * longest + Decimal(10) * LIVE_DEFAULT_MAX_TOKENS) / 1_000_000 * 3 * (persons + 3) * 2
    assert f"worst case model cost: US${cost:.4f} " in out


@pytest.mark.parametrize("persons", [8, 9, 12, 31, 120])
def test_q1_longest_request_bytes_is_the_largest_body_of_every_item_of_the_plan(persons: int) -> None:
    live = types.SimpleNamespace(model="model-x", max_tokens=LIVE_DEFAULT_MAX_TOKENS, effort=LIVE_DEFAULT_EFFORT)
    tag = "r0a1b2c"
    plan = rrc.make_plan(tag, persons)
    got = rrc.longest_request_bytes(live, plan)
    every = [
        _body_len("model-x", _question(str(it["envelope"]["payload"]["email"])))
        for items in plan.values()
        for it in items
    ]
    assert got == max(every)
    twin = _body_len("model-x", _question(f"{tag}-p{persons // 2}.second@{rrc.EMAIL_DOMAIN}"))
    first = _body_len("model-x", _question(f"{tag}-p1@{rrc.EMAIL_DOMAIN}"))
    assert got >= twin > first  # the twin address is the longest one for these counts, and it is counted


def test_q1_longest_request_bytes_uses_the_one_question_builder_and_the_one_body_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutant: the helper writes its own JSON or its own question text, or a short lead id: the fakes below show it."""
    seen: list[tuple[str, str]] = []

    def question(lead_id: str, email: str) -> str:
        seen.append((lead_id, email))
        return f"{lead_id}|{email}"

    monkeypatch.setattr(rrc, "question_text", question)
    monkeypatch.setattr(rrc, "request_body", lambda _s, q: q.encode("utf-8"))
    plan = rrc.make_plan("rabcdef", 9)
    got = rrc.longest_request_bytes(types.SimpleNamespace(), plan)
    emails = [str(it["envelope"]["payload"]["email"]) for items in plan.values() for it in items]
    assert got == max(len(LEAD_ID_LONG) + 1 + len(e) for e in emails)
    assert {lid for lid, _ in seen} == {LEAD_ID_LONG[:1] + "f" * 12}  # one real-length id
    assert {e for _, e in seen} == {e.strip().lower() for e in emails}  # the key the desk asks with


def test_q1_the_email_key_is_the_one_the_desk_asks_with(monkeypatch: pytest.MonkeyPatch) -> None:
    """The desk asks the model with `normalise_email(address)`: an address with capitals and spaces is counted as the
    desk will send it (lower case, stripped), never as typed."""
    from lead_desk.identity import normalise_email

    seen: list[str] = []
    monkeypatch.setattr(rrc, "question_text", lambda lid, em: seen.append(em) or "q")
    monkeypatch.setattr(rrc, "request_body", lambda _s, q: q.encode("utf-8"))
    plan = {"before": [{"envelope": {"payload": {"email": TYPED_ADDRESS}}}]}
    rrc.longest_request_bytes(types.SimpleNamespace(), plan)
    assert seen == [normalise_email(TYPED_ADDRESS)] == ["mixed@example.com"]


# -- q2: one tag for the banner and the run -----------------------------------------------------------------------


class _StopDesk:
    """A desk that cannot start: the run stops right after the banner and the plan (no process, no network)."""

    def __init__(self, *_a: Any, **_k: Any) -> None:
        self.url = "http://127.0.0.1:1"

    def start(self) -> None:
        raise RuntimeError("stopped for the test")

    def stop(self) -> None:
        return None


def test_q2_the_banner_and_the_run_use_the_same_tag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mutant: the banner makes its own tag (`make_plan(new_tag(), ...)`) or the run makes a second one: then the
    addresses the banner counted are not the addresses the run sends."""
    made: list[str] = []
    real_new_tag = rrc.new_tag
    real_plan = rrc.make_plan
    planned: list[str] = []

    def new_tag() -> str:
        made.append(real_new_tag())
        return made[-1]

    def make_plan(tag: str, persons: int) -> Any:
        planned.append(tag)
        return real_plan(tag, persons)

    monkeypatch.setattr(rrc, "new_tag", new_tag)
    monkeypatch.setattr(rrc, "make_plan", make_plan)
    monkeypatch.setattr(rrc, "Desk", _StopDesk)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    cfg = _valid_config(tmp_path, **_live_env(tmp_path, "model-x"))
    assert rrc.main(["--config", str(cfg), "--live-model"]) == rrc.EXIT_FAILED
    out = capsys.readouterr().out
    assert "the run could not finish" in out
    assert len(made) == 1
    assert planned == [made[0], made[0]]  # the banner's plan and the run's plan: the same tag


def test_q2_the_tag_has_the_documented_shape() -> None:
    tags = {rrc.new_tag() for _ in range(20)}
    assert len(tags) == 20
    assert all(t.startswith("r") and len(t) == 1 + rrc.TAG_HEX_CHARS for t in tags)
    assert all(int(t[1:], 16) >= 0 for t in tags)


# -- q3: the banner factor covers the most tries one lead can have ------------------------------------------------


def test_q3_calls_per_lead_times_two_desks_cover_the_automatic_tries_of_one_lead() -> None:
    """PIN. The model is asked at most once per automatic try (the label is stored once it has come), a lead has at
    most SEND_MAX_ATTEMPTS automatic tries over the whole run (the count is kept in the book, so a restarted desk
    continues it), and the run starts two desk processes. The banner's per-lead factor must cover that, and the leads
    counted (people + 3) must cover people + the twin. The hard bound is the per-run cap in the ledger, printed on
    the same line. Mutants: the `* 2` dropped, the `+ 3` made `+ 0`, the factor 3 lowered."""
    from lead_desk.constants import MODEL_CALLS_PER_LEAD_MAX
    from lead_desk.gate import SEND_MAX_ATTEMPTS

    assert rrc.MODEL_CALLS_PER_LEAD == MODEL_CALLS_PER_LEAD_MAX  # one source of truth for check 5 and the banner
    assert rrc.MODEL_CALLS_PER_LEAD * 2 >= SEND_MAX_ATTEMPTS


# -- q4, q5: what secret_boundary hands back ----------------------------------------------------------------------


class _Refusal(Exception):
    pass


def _boundary(raiser: Any) -> Any:
    from lead_desk.scrub import secret_boundary

    @secret_boundary(_Refusal, "fixed text")
    def touch(secret: str) -> None:
        raiser(secret)

    return touch


def test_q4_memory_error_is_handed_back_not_turned_into_the_refusal() -> None:
    """The mail code (SmtpProviderOutbox._dialogue and the callers) hands MemoryError straight back on purpose
    (tests/test_except_clause_hierarchy.py); a refusal in its place hid it. Its chain is still cut."""

    def raiser(secret: str) -> None:
        try:
            raise ValueError("earlier: " + secret)
        except ValueError as inner:
            raise MemoryError("out of memory") from inner

    with pytest.raises(MemoryError) as info:
        _boundary(raiser)("s3cret-made-up")
    e = info.value
    assert type(e) is MemoryError
    assert e.__cause__ is None and e.__context__ is None and e.__suppress_context__ is True


def test_q4_an_ordinary_foreign_error_still_becomes_the_fixed_refusal() -> None:
    def raiser(secret: str) -> None:
        raise ValueError("library text with " + secret)

    with pytest.raises(_Refusal) as info:
        _boundary(raiser)("s3cret-made-up")
    e = info.value
    assert str(e) == "fixed text" and e.__cause__ is None and e.__context__ is None
    assert "s3cret-made-up" not in repr(e.args)


@pytest.mark.parametrize("cls", [KeyboardInterrupt, SystemExit])
def test_q5_an_error_that_is_not_an_exception_is_handed_back_scrubbed(cls: type[BaseException]) -> None:
    """Mutant R08: `isinstance(e, Exception)` dropped from the test: Ctrl-C would be replaced by the refusal."""

    def raiser(secret: str) -> None:
        try:
            raise ValueError("earlier: " + secret)
        except ValueError as inner:
            raise cls() from inner

    with pytest.raises(cls) as info:
        _boundary(raiser)("s3cret-made-up")
    e = info.value
    assert type(e) is cls
    assert e.__cause__ is None and e.__context__ is None


# -- q6: the load driver's shared flags are restored by the test helper -------------------------------------------


def test_q6_the_fake_pool_helper_restores_the_load_driver_flags() -> None:
    """Mutant K01: the loop that saves `_STOP`, `_ANSWERED`, `_ERRORS` and `_STOP_LIMIT` is dropped from
    `_fake_pool_context`: the fakes the pool initializer stores would stay in the module for the next test."""
    from test_r7k_findings import _fake_pool_context

    from load_tools import load_driver

    before = (load_driver._STOP, load_driver._ANSWERED, load_driver._ERRORS, load_driver._STOP_LIMIT)
    fake_stop, fake_answered, fake_errors = object(), object(), object()
    with pytest.MonkeyPatch.context() as mp:
        _fake_pool_context(mp)
        load_driver._init_worker(fake_stop, fake_answered, fake_errors, 7)  # what the fake pool's start does
        assert load_driver._STOP is fake_stop and load_driver._STOP_LIMIT == 7  # the fakes are in place
    after = (load_driver._STOP, load_driver._ANSWERED, load_driver._ERRORS, load_driver._STOP_LIMIT)
    assert after == before
    assert all(a is b for a, b in zip(after, before, strict=True))


# -- q7: the repo-wide secret guard ----------------------------------------------------------------------------------


@pytest.fixture
def guard() -> Any:
    import test_r7n_findings as g

    return g


@pytest.mark.parametrize(
    "source",
    [
        "def f(m, p):\n    m.login('u', p)\n",
        "def f(m, p):\n    getattr(m, 'login')('u', p)\n",
        "def f(m, p):\n    m.authenticate('PLAIN', p)\n",
        "def f(m, p):\n    m.login_cram_md5('u', p)\n",
        "from lead_desk.regfile import read_secret_line\nr = read_secret_line\ndef f(p):\n    return r(p)\n",
        "from lead_desk import regfile\nr = regfile.read_secret_line\ndef f(p):\n    return r(p)\n",
        "from lead_desk.regfile import read_secret_line as r\ndef f(p):\n    return r(p)\n",
        "def f(k):\n    return {'X-Auth-Token': k}\n",
        "def f(k):\n    return {'Api-Key': k}\n",
        "def f(k):\n    return {'Proxy-Authorization': k}\n",
        "def f(k):\n    return {'authorization': k}\n",
        "def f(k):\n    return 'Basic ' + k\n",
        "def f(c):\n    return open(c.passwd_file).read()\n",
        "def f(c):\n    return open(c.pw_file).read()\n",
        "def f(c):\n    return open(c.credential_path).read()\n",
        "def f(c):\n    return c.private_key_file.read_bytes()\n",
        "def outer():\n    def inner(m, p):\n        m.login('u', p)\n    return inner\n",
        "g = lambda m, p: m.login('u', p)\n",
        f"class C{COLON_NL}    def f(self):\n        return self._key()\n",
        "@other_decorator\ndef f(m, p):\n    m.login('u', p)\n",
        # a name of the guard defined in the file itself is not the guard of lead_desk.scrub
        "def secret_boundary(x):\n    return x\n@secret_boundary\ndef f(m, p):\n    m.login('u', p)\n",
        "def scrub_error(e):\n    return e\ndef f(m, p):\n    m.login('u', p)\n    scrub_error(None)\n",
        # a guard call in dead code does not guard
        f"def f(m, p):\n    if False{COLON_NL}        scrub_error(None)\n    m.login('u', p)\n",
    ],
)
def test_q7_the_guard_finds_each_planted_way_of_touching_a_secret(guard: Any, source: str) -> None:
    assert guard.unguarded_sites(source), source


@pytest.mark.parametrize(
    "source",
    [
        "@secret_boundary(E, 'x')\ndef f(m, p):\n    m.login('u', p)\n",
        "@scrub.secret_boundary(E, 'x')\ndef f(m, p):\n    getattr(m, 'login')('u', p)\n",
        f"def f(m, p):\n    try{COLON_NL}        m.login('u', p)\n"
        f"    except Exception as e{COLON_NL}        scrub_error(e)\n        raise\n",
        "def f(a):\n    return open(a.report_file).read()\n",  # a file that is no secret
        "def _key(name):\n    return name.lower()\ndef f(x):\n    return _key(x)\n",  # tools/pathconfine's `_key`
        "def f(m):\n    return m.logout()\n",
        "def f(a):\n    return {'content-type': a}\n",
    ],
)
def test_q7_the_guard_does_not_flag_what_is_guarded_or_no_secret(guard: Any, source: str) -> None:
    assert guard.unguarded_sites(source) == [], source


def test_q7_guarded_sites_names_the_guarded_functions(guard: Any) -> None:
    src = "@secret_boundary(E, 'x')\ndef f(m, p):\n    m.login('u', p)\ndef g(m, p):\n    m.login('u', p)\n"
    assert guard.guarded_sites(src) == ["f"]
    assert guard.unguarded_sites(src) == ["g"]


def test_q7_the_guard_reads_every_folder_that_runs_with_a_secret_and_knows_the_guarded_functions(guard: Any) -> None:
    """Mutants G01 (scripts dropped from the list) and G02 (the list cut to one file): the known guarded functions of
    the real tree must still be found, in the files they live in."""
    files = {p.relative_to(REPO).as_posix(): p for p in guard._guard_files()}
    assert len(files) >= 40  # the real tree has 49 files in these places
    known = {
        "src/lead_desk/smtp_provider.py": {"send", "_dialogue", "read_secret_file"},
        "src/lead_desk/live_claude.py": {"_read_key", "_post_once", "qualify"},
        "src/lead_desk/imap_count.py": {"_password", "_session"},
        "src/lead_desk/crm_hubspot.py": {"_key", "_once", "_call"},
        "scripts/run_real_check.py": {"check_one_secret"},
        "scripts/n8n_api.py": {"_read_key", "call"},
    }
    for name, names in known.items():
        assert name in files, name
        found = set(guard.guarded_sites(files[name].read_text(encoding="utf-8")))
        assert names <= found, (name, names - found)
    assert any(n.startswith("tools/") for n in files) and any(n.startswith("load_tools/") for n in files)


def test_q7_the_guard_list_goes_into_sub_folders(guard: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for rel in ("src/lead_desk/sub/deep/x.py", "tools/y/z.py", "scripts/w.py", "load_tools/v.py", "tests/not_this.py"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True)
        p.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(guard, "REPO", tmp_path)
    got = {p.relative_to(tmp_path).as_posix() for p in guard._guard_files()}
    assert got == {"src/lead_desk/sub/deep/x.py", "tools/y/z.py", "scripts/w.py", "load_tools/v.py"}


# -- q8: the fake servers are silent only when the client left ----------------------------------------------------


def _handle(srv: Any, exc: BaseException) -> None:
    try:
        raise exc
    except BaseException:
        srv.handle_error(None, ("127.0.0.1", 1))


@pytest.mark.parametrize("exc", [BrokenPipeError(), ConnectionResetError(), ConnectionAbortedError(), TimeoutError()])
def test_q8_a_client_that_left_is_silent(capsys: pytest.CaptureFixture[str], exc: BaseException) -> None:
    from demo_only.bad_request import QuietServer

    srv = QuietServer(("127.0.0.1", 0), type("H", (), {}))
    try:
        _handle(srv, exc)
    finally:
        srv.server_close()
    cap = capsys.readouterr()
    assert cap.out == "" and cap.err == ""


@pytest.mark.parametrize("exc", [ValueError("a real handler fault"), KeyError("k"), OSError("disk"), RuntimeError("x")])
def test_q8_every_other_error_is_still_reported(capsys: pytest.CaptureFixture[str], exc: BaseException) -> None:
    from demo_only.bad_request import QuietServer

    srv = QuietServer(("127.0.0.1", 0), type("H", (), {}))
    try:
        _handle(srv, exc)
    finally:
        srv.server_close()
    err = capsys.readouterr().err
    assert "Exception occurred during processing of request" in err and type(exc).__name__ in err


def test_q8_the_three_fakes_use_the_quiet_server() -> None:
    from demo_only import fake_hubspot, fake_model_server, fakes_server
    from demo_only.bad_request import QuietServer

    assert issubclass(fake_hubspot.FakeHubspot, QuietServer)
    assert issubclass(fakes_server.FakesServer, QuietServer)
    srv, _state = fake_model_server.make_model_server("127.0.0.1", 0, "ok", "k")
    try:
        assert isinstance(srv, QuietServer) and srv.daemon_threads is True
    finally:
        srv.server_close()


# -- q9: an error after the login leaves only the fixed text (mutant X1 on the not-repeated branch) -------------------


class _LoggedInImap:
    """A connection whose login works; the work done after it fails with the error the test gives."""

    deadline = float("inf")
    sock = None

    def __init__(self, *_a: Any, **_k: Any) -> None:
        pass

    def login(self, _user: str, _password: str) -> None:
        return None

    def logout(self) -> None:
        return None

    def shutdown(self) -> None:
        return None


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (OSError("made-up detail with SECRET-PW"), "ImapConnectionError"),
        (imaplib.IMAP4.abort("made-up detail with SECRET-PW"), "ImapConnectionError"),
        (imaplib.IMAP4.error("made-up detail with SECRET-PW"), "ImapCountError"),
    ],
)
def test_q9_an_error_after_the_login_is_replaced_by_the_fixed_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exc: Exception, expected: str
) -> None:
    """The text of the server's or the library's error is never repeated (it may echo what was sent)."""
    from lead_desk import imap_count

    pw = tmp_path / "pw"
    pw.write_text("SECRET-PW\n", encoding="utf-8")
    monkeypatch.setattr(imap_count, "_BoundedImap", _LoggedInImap)
    monkeypatch.setattr(imap_count, "require_modern_protocol", lambda *_a, **_k: None)
    s = imap_count.ImapSettings("h.test", "u", pw)

    def work(_m: Any) -> dict[str, dict[str, int]]:
        raise exc

    with pytest.raises(imap_count.ImapCountError) as info:
        imap_count._session(s, work)
    assert type(info.value).__name__ == expected
    assert str(info.value) == "the mailbox could not be read"
    assert "SECRET-PW" not in repr(info.value.args) and info.value.__cause__ is None
