"""EVIDENCE probe (throwaway, outside the repo). usage: PYTHONPATH=<src> python probe.py out.json"""
import json, sys
from datetime import UTC, datetime
import hadavin_sdk
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
from hadavin_sdk.tools import redact_layered
from hadavin_sdk.k1b.bundle import Bundle
from hadavin_sdk.k1b.redaction import redact_bundle

COOKIE_KEYS = ["session_cookie", "session-cookie", "x_session_cookie", "Cookie"]
COOKIE_VALUES = {
    "amp": ("Aq1bcd&Zx9tail", ["Aq1bcd", "Zx9tail"]),
    "lsq": ("Bq2bcd[Zy8tail", ["Bq2bcd", "Zy8tail"]),
    "lbr": ("Cq3bcd{Zw7tail", ["Cq3bcd", "Zw7tail"]),
    "bsl": ("Dq4bcd\\Zv6tail", ["Dq4bcd", "Zv6tail"]),
    "jar": ("sid=Eq5sidval; theme=Fq5theme; lang=Gq5lang trailing Hq5prose words", ["Eq5sidval", "Fq5theme", "Gq5lang"]),
    "plain": ("Iq6plainvalue", ["Iq6plainvalue"]),
}
FLAGS_MASK = ["newpass", "oldpass", "postgresauth", "authorization", "dbpass", "confirmpass", "rootauth", "oauth"]
FLAGS_KEEP = ["bypass", "compass", "obsession", "author"]
FLAG_VALUES = {"one": ("Jq7oneword", ["Jq7oneword"]), "two": ("Kq8first Lq8second", ["Kq8first", "Lq8second"])}
KEEP_VALUE = ("Mq9ordinary", ["Mq9ordinary"])

def bundle(**kw):
    base = dict(case_id="case-ev", alert_time=datetime(2026, 1, 1, 10, tzinfo=UTC), alert_time_text="2026-01-01T10:00:00Z",
                alert={}, metrics=(), logs=(), deploys=(), k8s=(), runbooks=(), ids=frozenset(), manifest_sha256="0" * 64)
    base.update(kw)
    return Bundle(**base)

def paths_text(text):
    out = {}
    out["card"] = clean(text)
    out["tool"] = redact_layered(text, {})
    out["run"] = runmap.redact_text(text, {})
    out["log"] = runmap.safe_head(text, 4000, {})
    b = bundle(logs=(("l.jsonl", ({"ts": "2026-01-01T10:00:00Z", "message": text},)),))
    out["record_msg"] = redact_bundle(b)[0].logs[0][1][0]["message"]
    return out

def record_key(key, value):
    b = bundle(logs=(("l.jsonl", ({"ts": "2026-01-01T10:00:00Z", key: value},)),), alert={key: value})
    r = redact_bundle(b)[0]
    return {"record_key_log": json.dumps(r.logs[0][1][0], ensure_ascii=False), "record_key_alert": json.dumps(r.alert, ensure_ascii=False)}

cells = []  # (group, label, path, readable_frags, output)
def add(group, label, texts_fn, frags):
    for path, out in texts_fn.items():
        rd = [f for f in frags if f in out]
        cells.append({"group": group, "cell": label, "path": path, "readable": rd, "out": out})

for k in COOKIE_KEYS:
    for vn, (v, frags) in COOKIE_VALUES.items():
        for form, tmpl in (("eq", "note {k}={v} end of note"), ("colon", "header {k}: {v}"), ("json", '{{"{k}": "{v}"}} tail')):
            try:
                outs = paths_text(tmpl.format(k=k, v=v))
            except Exception as e:
                outs = {"ERR": repr(e)[:100]}
            add("cookie", f"{k}|{vn}|{form}", outs, frags)
        try:
            outs = record_key(k, v)
        except Exception as e:
            outs = {"ERR": repr(e)[:100]}
        add("cookie", f"{k}|{vn}|record", outs, frags)

for fl in FLAGS_MASK + FLAGS_KEEP:
    grp = "flag_mask" if fl in FLAGS_MASK else "flag_keep"
    for vn, (v, frags) in (FLAG_VALUES.items() if grp == "flag_mask" else [("one", KEEP_VALUE), ("two", ("Mq9ordinary Nq9second", ["Mq9ordinary", "Nq9second"]))]):
        for form, tmpl in (("space", "ran tool --{f} {v} --verbose"), ("eq", "ran tool --{f}={v} --verbose"), ("bare", "cfg {f}={v} more words")):
            try:
                outs = paths_text(tmpl.format(f=fl, v=v))
            except Exception as e:
                outs = {"ERR": repr(e)[:100]}
            add(grp, f"{fl}|{vn}|{form}", outs, frags)
        try:
            outs = record_key(fl, v)
        except Exception as e:
            outs = {"ERR": repr(e)[:100]}
        add(grp, f"{fl}|{vn}|record", outs, frags)
json.dump({"src": hadavin_sdk.__file__, "cells": cells}, open(sys.argv[1], "w"), indent=0)
print(hadavin_sdk.__file__, len(cells))
