"""Honest sizes: the largest finder build (characters of `_rules` keys, what the trie holds) over
(a) the 1,836-input property corpus through its own `check` (two redact_text passes per input),
(b) the tests/test_k5_perf and test_k5_round10 shapes, (c) a 262,144-char document of 2,000 HIGHENTROPY values of 131.
Run from the scratch copy root (so `tests` imports): python m_honest.py"""
import importlib
import sys
import time

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]
from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap

seen = {"max": 0, "builds": 0}
_orig = R._Redactor._build


def _build(self):
    _orig(self)
    seen["builds"] += 1
    seen["max"] = max(seen["max"], sum(map(len, self._rules)))


R._Redactor._build = _build


def measure(label, fn):
    seen["max"], seen["builds"] = 0, 0
    t = time.thread_time()
    res = fn()
    print(f"{label}: builds={seen['builds']} max_finder_chars={seen['max']} cpu_s={time.thread_time() - t:.2f} {res}", flush=True)


prop = importlib.import_module("tests.test_redact_idempotent_property")


def corpus():
    worst, outcomes = ("", 0), {}
    for case_id, text in prop.CORPUS:
        before = seen["max"]
        seen["max"] = 0
        st, _ = prop.check(text)
        outcomes[st] = outcomes.get(st, 0) + 1
        if seen["max"] > worst[1]:
            worst = (case_id, seen["max"])
        seen["max"] = max(before, seen["max"])
    return f"inputs={len(prop.CORPUS)} outcomes={outcomes} worst={worst}"


measure("property corpus", corpus)


def k5_full_run():
    rmap = runmap.RunMap()
    doc = " ".join(f"10.{i // 60000}.{(i // 250) % 240}.{i % 250 + 1}" for i in range(1500))
    runmap.redact_untrusted(doc, rmap)
    for i in range(40):
        runmap.redact_value({f"k{j}": f"value {i} {j} 10.9.9.{j}" for j in range(5)}, rmap)
    return f"entries={len(rmap)} value_chars={sum(map(len, set(rmap.values())))}"


measure("k5_round10 full-size run (1,500 IPs + 40 x 5 args)", k5_full_run)


def k5_cap(unit):
    def go():
        text = (unit * (defaults.MAX_REDACT_CHARS // len(unit) + 1))[: defaults.MAX_REDACT_CHARS]
        m = runmap.RunMap()
        try:
            runmap.redact_untrusted(text, m)
        except runmap.RedactionError as exc:
            return f"refused {exc}"
        return f"entries={len(m)} value_chars={sum(map(len, set(m.values())))}"

    return go


k5 = importlib.import_module("tests.test_k5_perf")
for unit in [*getattr(k5, "E2E_UNITS", []), "curl -u "]:
    measure(f"k5_perf unit {unit!r} at the cap", k5_cap(unit))


def he_doc():
    import random
    import string

    rng = random.Random(3)
    a = string.ascii_letters + string.digits
    doc = "\n".join("tok " + "".join(rng.choices(a, k=131)) for _ in range(2000))
    m = runmap.RunMap()
    runmap.redact_untrusted(doc[: defaults.MAX_REDACT_CHARS], m)
    return f"entries={len(m)} value_chars={sum(map(len, set(m.values())))} kinds={sorted({R.kind_of(p) for p in m})}"


measure("2,000 HIGHENTROPY of 131 (one document)", he_doc)
