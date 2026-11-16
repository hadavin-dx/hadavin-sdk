"""Independent reference scorer: standard library only, no hadavin_sdk import.

A regression check for the shipped scorer, not independence: the same author wrote both. It reproduces the
per-run class counts (Hits, no-evidence Hits, Misses, Not sure) from the files and nothing else.
"""

import json
import unicodedata
from pathlib import Path


def _n(text):
    return unicodedata.normalize("NFC", text).strip()


def reference_counts(out, answers_path, cause_dir):
    """One dict (hits, hne, misses, not_sure) per runN folder, in order."""
    answers = json.loads(Path(answers_path).read_text(encoding="utf-8"))["cases"]
    services = {
        _n(s) for s in json.loads((Path(cause_dir) / "services.json").read_text(encoding="utf-8"))
    }
    faults = {
        _n(s)
        for s in json.loads((Path(cause_dir) / "fault_types.json").read_text(encoding="utf-8"))
    }
    result = []
    run = 1
    while (Path(out) / f"run{run}").is_dir():
        tally = {"hits": 0, "hne": 0, "misses": 0, "not_sure": 0}
        for case_id, ans in answers.items():
            rec = json.loads(
                (Path(out) / f"run{run}" / f"{case_id}.json").read_text(encoding="utf-8")
            )
            tally[_bucket(rec, ans, services, faults)] += 1
        result.append(tally)
        run += 1
    return result


def _bucket(rec, ans, services, faults):
    diag = rec["diagnosis"]
    if rec["status"] != "ok" or diag is None:
        return "misses"
    unsure = diag["not_sure"] is True
    if ans["no_evidence"]:
        return "hne" if unsure and "converted" not in rec else "misses"
    if unsure:
        return "not_sure"
    accepted = {(_n(a["service"]), _n(a["fault_type"])) for a in ans["accepted"]}
    hit = False
    for c in diag["causes"][:3]:
        pair = (_n(c["service"]), _n(c["fault_type"]))
        if pair[0] not in services or pair[1] not in faults:
            return "misses"
        hit = hit or pair in accepted
    return "hits" if hit else "misses"
