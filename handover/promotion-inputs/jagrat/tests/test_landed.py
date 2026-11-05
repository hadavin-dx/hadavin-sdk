from datetime import UTC, datetime, timedelta

from jagrat import landed
from jagrat.record_kinds import APPLIED

T0 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


class Log:
    def __init__(self, rows):
        self.rows = rows

    def entries(self, kinds, since):
        assert kinds == (APPLIED,)
        return [r for r in self.rows if r["at"] >= since]


def fix(run, at, service="web"):
    return {"at": at, "body": {"service": service, "action_class": "scale_up", "workflow_id": run}}


def call(log, changes="absent", **kw):
    args = {
        "target": "web",
        "workflow_id": "run-1",
        "applied_at": T0,
        "now": T0 + timedelta(minutes=5),
        "log": log,
    }
    if changes != "absent":
        args["changes"] = changes
    return landed.since_fix(**{**args, **kw})


def test_other_run_on_same_target_counts_own_run_and_other_targets_do_not():
    log = Log(
        [
            fix("run-2", T0 + timedelta(minutes=1)),
            fix("run-1", T0 + timedelta(minutes=2)),
            fix("run-3", T0 + timedelta(minutes=2), service="db"),
            fix("run-0", T0 - timedelta(minutes=1)),
        ]
    )
    got, unread, unchecked = call(log)
    assert [g["what"] for g in got] == ["scale_up by fix run run-2"]
    assert unread == [] and unchecked and "no change reader" in unchecked[0]


def test_changes_are_merged_filtered_by_target_and_time():
    rows = [
        {
            "at": T0 + timedelta(minutes=1),
            "source": "deploy",
            "what": "rev 8",
            "who": "ci",
            "target": "web",
        },
        {
            "at": T0 + timedelta(minutes=2),
            "source": "deploy",
            "what": "rev 9",
            "who": "ci",
            "target": "db",
        },
        {
            "at": T0 - timedelta(seconds=30),
            "source": "deploy",
            "what": "old",
            "who": "ci",
            "target": "web",
        },
    ]
    got, unread, unchecked = call(Log([]), changes=lambda s, u: rows)
    assert [g["what"] for g in got] == ["rev 8"] and unread == [] and unchecked == []


def test_unreadable_change_log_is_unknown_not_empty():
    def boom(since, until):
        raise OSError("down")

    got, unread, _ = call(Log([]), changes=boom)
    assert got == [] and unread == ["change log (OSError)"]
    assert "could not be read" in landed.said(got, unread)


def test_said_names_the_first_change_and_redacts_secret_shapes():
    key = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
    rows = [
        {"at": T0 + timedelta(minutes=1), "source": "deploy", "what": "x " + key, "who": "ci"},
        {"at": T0 + timedelta(minutes=2), "source": "deploy", "what": "y", "who": "ci"},
    ]
    got, unread, _ = call(Log([]), changes=lambda s, u: rows)
    text = landed.said(got, unread)
    assert key not in text and "and 1 more" in text and "a person decides" in text
    assert all(key not in str(v) for r in landed.shown(got) for v in r.values())
