"""K6 third review round: the clear guard, nonce release, one demotion per episode, ties, report claim, unknown
counts, concurrent enforce, nonce purge, BOM, and the clear card's wrongs note."""

from __future__ import annotations

import threading
import time
from datetime import timedelta

import pytest

from hadavin_sdk import measure
from hadavin_sdk.measure import Ceiling
from hadavin_sdk.models import RunState
from tests.test_k6_measure import ACTION, CEIL, NOW, WEEK, World, day

S = RunState


def demotions(w):
    return [e for e in w.store.list_level_events() if e.kind == "demote"]


# --- 1: the clear guard looks at the whole episode, not at the last event ---------------------------------------


def test_r3_clear_is_refused_while_breached_even_when_a_later_wrong_episode_demoted_last(tmp_path):
    w = World(tmp_path, ceiling=Ceiling(CEIL.metric, 0, 90, CEIL.source))
    w.labelled("harmful", 1, when=day(5))
    assert any(e.reason.startswith("ceiling:") for e in w.measure.enforce(NOW))
    w.labelled(
        "wrong", 3, when=day(2)
    )  # a wrong-episode demotion is now the LAST event of the action
    assert demotions(w)[-1].reason.startswith("wrong_x3:")
    assert w.measure.ceiling_status().breached
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "ceiling_breached")
    assert ("test-agent", ACTION) in w.store.current_overrides()
    # once the sponsor raises max in writing the breach is over and the owner may clear
    w.measure.ceiling = Ceiling(CEIL.metric, 5, 90, CEIL.source)
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "cleared")


# --- 2: a click that did not take effect gives its nonce back ------------------------------------------------------


def test_r3_a_store_failure_does_not_spend_the_signed_request(tmp_path):
    w = World(tmp_path)
    rid = w.run()
    real = w.store.add_labels

    def down(items, *, may_lower_harmful):
        raise OSError("db down")

    w.store.add_labels = down
    assert w.click("u1", f"label|{rid}|agree", ts=NOW)[0] == 503
    w.store.add_labels = real
    assert (
        w.click("u1", f"label|{rid}|agree", ts=NOW)[0] == 200
    )  # the very same signed request, delivered again
    assert [x.label for x in w.store.list_labels(rid)] == ["agree"]
    assert w.click("u1", f"label|{rid}|agree", ts=NOW)[0] == 200  # but now it is spent
    assert len(w.store.list_labels(rid)) == 1


def test_r3_an_exception_in_the_action_also_gives_the_nonce_back(tmp_path):
    w = World(tmp_path)
    rid = w.run()
    real = w.measure._dispatch
    w.measure._dispatch = lambda user, parsed: (_ for _ in ()).throw(RuntimeError("bug"))
    assert w.click("u1", f"label|{rid}|agree", ts=NOW)[0] == 503
    w.measure._dispatch = real
    assert w.click("u1", f"label|{rid}|agree", ts=NOW)[0] == 200
    assert len(w.store.list_labels(rid)) == 1


# --- 3: one demotion per episode ------------------------------------------------------------------------------------


def test_r3_four_wrongs_a_minute_apart_make_one_demotion_one_audit_entry_one_card(tmp_path):
    w = World(tmp_path)
    for i in range(4):
        w.label(w.run(), "wrong", when=NOW - timedelta(days=2) + timedelta(minutes=i))
    assert [e.reason.split(":")[0] for e in demotions(w)] == ["wrong_x3"]
    assert len([e for e in w.audit.events() if e.operation == "demote"]) == 1
    assert len(w.channel.cards) == 1
    w.measure.enforce(NOW)  # the tick re-check adds nothing either
    assert len(demotions(w)) == 1 and len(w.channel.cards) == 1


def test_r3_a_second_harmful_while_demoted_adds_no_second_demotion_but_after_a_clear_it_does(
    tmp_path,
):
    w = World(tmp_path)
    w.label(w.run(), "harmful", when=day(3))
    w.label(w.run(), "harmful", when=day(2))
    assert len(demotions(w)) == 1 and len(w.channel.cards) == 1
    w.measure.ceiling = Ceiling(CEIL.metric, 9, 90, CEIL.source)
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "cleared")
    assert w.label(w.run(), "harmful", when=day(1)).demoted
    assert len(demotions(w)) == 2


# --- 4: a csv harmful row is one verdict, whether pending or approved -----------------------------------------------


def test_r3_a_harmful_csv_row_demotes_and_announces_once_across_import_and_approval(tmp_path):
    w = World(tmp_path, ceiling=None)  # no ceiling rows in the way
    rid = w.run()
    text = f"run_id,label\n{rid},harmful\n"
    assert w.measure.import_csv(text, "fake:u1")[0] == 1
    assert len(demotions(w)) == 1
    cards = len(w.channel.cards)
    assert w.click("owner", f"approve_import|{measure.csv_import_id(text)}", ts=NOW)[0] == 200
    # approval is not a second verdict (the approved harmful label may breach the ceiling: that is its own row)
    assert len([e for e in demotions(w) if e.reason.startswith("harmful:")]) == 1
    assert len([e for e in w.audit.events() if e.operation == "demote"]) == 1
    assert len(w.channel.cards) == cards


def test_r3_approving_an_old_import_after_a_clear_does_not_demote_again(tmp_path):
    w = World(tmp_path)
    w.measure.ceiling = Ceiling(CEIL.metric, 9, 90, CEIL.source)
    rid = w.run()
    text = f"run_id,label\n{rid},harmful\n"
    w.measure.import_csv(text, "fake:u1")
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "cleared")
    w.measure.approve_import("fake:owner", measure.csv_import_id(text))
    assert (
        "test-agent",
        ACTION,
    ) not in w.store.current_overrides()  # the cleared verdict stays cleared


# --- 5: equal timestamps ---------------------------------------------------------------------------------------------


def test_r3_a_fourth_wrong_at_the_same_instant_after_a_clear_demotes(tmp_path):
    w = World(tmp_path)
    w.labelled("wrong", 3, when=day(2))  # three wrongs at one instant
    assert len(demotions(w)) == 1
    w.measure.ceiling = Ceiling(CEIL.metric, 9, 90, CEIL.source)
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "cleared")
    assert w.label(w.run(), "wrong", when=day(2)).demoted  # same instant, newest by insertion
    assert len(demotions(w)) == 2


@pytest.mark.parametrize("order", [("a", "z"), ("z", "a")])
def test_r3_latest_label_is_the_last_inserted_whatever_the_ids_and_timestamps(tmp_path, order):
    from hadavin_sdk.models import Label, latest_labels

    w = World(tmp_path)
    rid = w.run()
    t = NOW
    for name, lid in zip(("agree", "partial"), order, strict=True):
        w.store.add_labels(
            [
                (
                    Label(
                        label_id=lid,
                        run_id=rid,
                        label=name,
                        principal_id="fake:u1",
                        channel="chat",
                        created_at=t,
                    ),
                    None,
                )
            ],
            may_lower_harmful=True,
        )
    assert (
        latest_labels(w.store.list_labels(rid))[rid].label == "partial"
    )  # inserted last, ids or not


# --- 6: the weekly report is announced once even when ticks overlap ----------------------------------------------------


def test_r3_overlapping_ticks_announce_the_report_once(tmp_path):
    w = World(tmp_path)
    w.labelled("agree", 2, when=day(7))
    real = w.channel.notify

    def slow(who, text):
        time.sleep(0.15)
        real(who, text)

    w.channel.notify = slow
    results = []
    start = threading.Barrier(4)

    def tick():
        start.wait()
        try:
            results.append(w.measure.weekly_report(NOW))
        except RuntimeError:
            results.append("failed")

    threads = [threading.Thread(target=tick) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(w.channel.notices) == 1  # one line owner told once
    assert len([r for r in results if r]) == 1
    assert w.store.get_report(WEEK) is not None


def test_r3_a_failed_announcement_gives_the_week_back_for_the_next_tick(tmp_path):
    w = World(tmp_path)
    real = w.channel.notify
    w.channel.notify = lambda who, text: (_ for _ in ()).throw(OSError("down"))
    with pytest.raises(RuntimeError, match="not announced"):
        w.measure.weekly_report(NOW)
    w.channel.notify = real
    assert w.measure.weekly_report(NOW + timedelta(seconds=30))  # not blocked by a stale claim
    assert len(w.channel.notices) == 1


# --- 7: an unknown count is never shown as zero ---------------------------------------------------------------------


def test_r3_an_unreadable_audit_never_shows_zero_lowered_verdicts(tmp_path):
    w = World(tmp_path)
    rid = w.run(created=day(7))
    w.label(rid, "harmful", when=day(7))
    w.label(rid, "agree", who="owner", when=day(7, 13))
    ok = w.measure.render_report(WEEK, NOW)
    assert "lowered by a line owner: 1 this week" in ok
    w.audit.events = lambda run_id=None: (_ for _ in ()).throw(OSError("audit down"))
    bad = w.measure.render_report(WEEK, NOW)
    assert "COULD NOT BE READ" in bad and "lowered by a line owner: 0" not in bad


# --- 8: audit and announce only what was really inserted ---------------------------------------------------------------


def test_r3_two_enforce_passes_at_once_audit_and_announce_once(tmp_path):
    w = World(tmp_path, ceiling=Ceiling(CEIL.metric, 0, 90, CEIL.source))
    w.labelled("harmful", 1, when=day(5))
    base = len([e for e in w.audit.events() if e.operation == "demote"])
    cards = len(w.channel.cards)
    results = []
    start = threading.Barrier(2)

    def go():
        start.wait()
        results.append(w.measure.enforce(NOW))

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    inserted = sum(len(r) for r in results)
    ceiling_rows = [e for e in demotions(w) if e.reason.startswith("ceiling:")]
    assert (
        inserted == len(ceiling_rows) == len(w.measure._pairs())
    )  # each row once, however many passes ran
    assert len([e for e in w.audit.events() if e.operation == "demote"]) == base + len(ceiling_rows)
    assert len(w.channel.cards) == cards  # ceiling demotions send a breach notice, not a card each
    assert (
        len([t for t in w.channel.notices if "Ceiling breached" in t[1]]) == 1
    )  # one notice, once


# --- 10: the nonce table does not grow for ever -----------------------------------------------------------------------------


def test_r3_old_click_nonces_are_purged_and_recent_ones_kept(tmp_path):
    w = World(tmp_path)
    w.store.claim_action("old", NOW - timedelta(minutes=11))
    w.store.claim_action("recent", NOW - timedelta(minutes=2))
    assert w.measure.purge_seen(NOW) == 1  # older than twice the five-minute signature window
    assert w.store.claim_action("old", NOW) is True  # gone
    assert w.store.claim_action("recent", NOW) is False  # still guarded


# --- 11: a spreadsheet's byte order mark ------------------------------------------------------------------------------------


def test_r3_a_utf8_bom_csv_imports_and_has_the_same_id(tmp_path):
    w = World(tmp_path)
    rid = w.run()
    text = f"run_id,label\n{rid},agree\n"
    assert w.measure.import_csv("﻿" + text, "fake:u1") == (1, [])
    assert w.store.list_csv_import(
        measure.csv_import_id(text)
    )  # the id is of the file without the mark


def test_r3_the_cli_reads_a_bom_file(tmp_path):
    from types import SimpleNamespace

    from hadavin_sdk import cli

    w = World(tmp_path)
    rid = w.run()
    f = tmp_path / "labels.csv"
    f.write_bytes(b"\xef\xbb\xbf" + f"run_id,label\n{rid},agree\n".encode())
    app = SimpleNamespace(
        measure=w.measure, store=w.store, config=SimpleNamespace(environment="dev")
    )
    ns = SimpleNamespace(cmd="label", action="import", file=f, by="fake:u1", approved_by=None)
    assert cli.measure_cmd(app, ns) == 0
    assert w.store.list_labels(rid)


# --- the question: a clear does not erase recent wrongs ---------------------------------------------------------------------


def test_r3_the_card_says_recent_wrongs_still_count_until_a_date(tmp_path):
    w = World(tmp_path)
    for i in range(3):
        w.label(w.run(), "wrong", when=day(4 - i))
    (card,) = w.channel.cards
    until = (NOW - timedelta(days=3)) + timedelta(days=14)  # the second-newest wrong ages out then
    assert f"Recent wrongs still count until {until:%Y-%m-%d} UTC" in card.text
    assert "does not erase them" in card.text


def test_r3_one_new_wrong_after_a_clear_demotes_at_once_while_two_old_ones_remain(tmp_path):
    w = World(tmp_path)
    w.labelled("wrong", 3, when=day(2))
    w.measure.ceiling = Ceiling(CEIL.metric, 9, 90, CEIL.source)
    assert w.measure.clear("fake:owner", "test-agent", ACTION) == (200, "cleared")
    assert w.label(
        w.run(), "wrong", when=day(1)
    ).demoted  # intended: an owner's clear cannot erase the pattern
