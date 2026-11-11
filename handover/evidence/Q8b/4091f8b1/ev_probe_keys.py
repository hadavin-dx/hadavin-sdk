"""EVIDENCE RUNNER probe (own script, typed from the ticket tables and the coordinator add-on). Records only.
Usage: python ev_probe_keys.py <label>  (PYTHONPATH selects head or main). Prints JSON."""
import json, re, sys
import hadavin_sdk; print("MODULE", hadavin_sdk.__file__, file=sys.stderr)
from datetime import UTC, datetime
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.tools import redact_layered
from hadavin_sdk.k1b.bundle import Bundle
from hadavin_sdk.k1b.redaction import redact_bundle
import importlib; R = importlib.import_module("hadavin_sdk.guard.redact")

P1, P2, P3 = "Zq7" + "xV", "Kp9" + "wT", "Hn4" + "bL"  # made-up pieces, built from parts
VALUES = {  # name -> (text after the key sign, raw value for the record walk)
    "dq": (f'"{P1};{P2} {P3}"', f"{P1};{P2} {P3}"),
    "sq": (f"'{P1} {P2} {P3}'", f"{P1} {P2} {P3}"),
    "bare": (f"{P1};{P2}{P3}", f"{P1};{P2}{P3}"),
}
PIECES = (P1, P2, P3)

def bundle(**kw):
    base = dict(case_id="case-q8b", alert_time=datetime(2026, 1, 1, 10, tzinfo=UTC), alert_time_text="2026-01-01T10:00:00Z",
                alert={}, metrics=(), logs=(), deploys=(), k8s=(), runbooks=(), ids=frozenset(), manifest_sha256="0" * 64)
    base.update(kw)
    return Bundle(**base)

def walk(obj):
    return json.dumps(obj, default=str, ensure_ascii=False)

def p_card(key, vt, raw):
    return clean(f"set {key}={vt} now") + "\n" + clean(f"{key}: {vt}")
def p_tool(key, vt, raw):
    return redact_layered(f"{key}={vt} tail", {}) + "\n" + redact_layered(f'{{"{key}": "{raw}"}}', {})
def p_log(key, vt, raw):
    b = bundle(logs=(("app.log", ({"ts": "2026-01-01T09:00:00Z", "msg": f"{key}={vt} end"},),),))
    return walk(redact_bundle(b)[0].logs)
def p_walk(key, vt, raw):
    b = bundle(deploys=({key: raw, "n": {key: raw}},), alert={key: [raw]})
    o = redact_bundle(b)[0]
    return walk(o.deploys) + walk(o.alert)
PATHS = {"card": p_card, "tool": p_tool, "log": p_log, "walk": p_walk}

def readable(out):
    return [p for p in PIECES if p in out]

def run(keys, label):
    res = {}
    for key in keys:
        for pn, pf in PATHS.items():
            for vn, (vt, raw) in VALUES.items():
                try:
                    out = pf(key, vt, raw)
                    res[f"{key}|{pn}|{vn}"] = readable(out)
                except Exception as e:
                    res[f"{key}|{pn}|{vn}"] = "ERR " + type(e).__name__
    return res

ADDON = ["passcode", "passkey", "pass_code", "session_key", "sessionkey", "session_cookie", "newpass", "oldpass",
         "confirmpass", "defaultpass", "postgresauth", "jenkinssession", "supersession", "bypass", "compass", "oauth", "obsession"]

def spellings(fragment):
    out = [re.sub(r"\(\?=[^()]*\)", "", fragment).replace("\\.", ".")]
    out = [o.replace("[_\\-]?", s) for o in out for s in ("", "_", "-")]
    more = []
    for o in out:
        m = re.search(r"\(\?:([a-z]+)\)\?", o)
        more += [o.replace(m.group(0), ""), o.replace(m.group(0), m.group(1))] if m else [o]
    return more

def corpus_keys():
    base = []
    for frag in getattr(R, "KEY_ALTERNATIVES", ()):
        base += spellings(frag)
    base = sorted(set(base))
    keys = set()
    for b in base:
        for k in (b, b.upper(), b.title(), b.replace("_", "-").upper()):
            keys.update({k, "db_" + k, "My-" + k, k + "_value", "x" + k.title()})
    return sorted(keys)

BENIGN = ["host", "name", "level", "service", "status", "region", "namespace", "pod", "image", "version", "message", "user",
          "email_domain", "max_tokens", "tokens_used", "keyboard", "monkey", "turkey", "donkey", "hockey", "bypass", "compass",
          "oauth", "passenger", "password_policy_enabled", "token_count", "primary_key", "sort_key", "cache_key", "partition_key",
          "key", "keys", "id", "trace_id", "duration_ms", "error", "reason", "kind", "path", "port", "env", "stage"]

if __name__ == "__main__":
    label = sys.argv[1]
    which = sys.argv[2] if len(sys.argv) > 2 else "addon"
    if which == "addon":
        print(json.dumps(run(ADDON, label), indent=0))
    elif which == "corpus":
        import os
        kf = os.environ.get("KEYFILE")
        if kf and os.path.exists(kf):
            keys = json.load(open(kf))
        else:
            keys = corpus_keys()
            if kf:
                json.dump(keys, open(kf, "w"))
        res = run(keys, label)
        # nested record walk with deeper nesting and a mixed-case separator form
        bad = {k: v for k, v in res.items() if v}
        errs = {k: v for k, v in res.items() if isinstance(v, str)}
        # benign: masked count in a record walk
        masked = []
        for k in BENIGN:
            b = bundle(deploys=({k: "orders-svc-eu"},))
            if "orders-svc-eu" not in walk(redact_bundle(b)[0].deploys):
                masked.append(k)
        print(json.dumps({"keys": len(keys), "probes": len(res), "readable_secret_probes": len(bad), "errors": len(errs),
                          "readable_by_path": {p: sum(1 for k in bad if k.split("|")[1] == p) for p in PATHS},
                          "readable_by_value_style": {v: sum(1 for k in bad if k.split("|")[2] == v) for v in VALUES},
                          "readable_by_path_style": {k2: sum(1 for k in bad if "|".join(k.split("|")[1:]) == k2) for k2 in sorted({"|".join(k.split("|")[1:]) for k in bad})},
                          "readable_by_piece": {p: sum(1 for v in bad.values() if p in v) for p in PIECES},
                          "readable_by_key_sample": sorted({k.split("|")[0] for k in bad})[:40],
                          "benign_total": len(BENIGN), "benign_masked": masked}, indent=1))
