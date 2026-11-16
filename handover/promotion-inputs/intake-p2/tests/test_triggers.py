"""The database guard triggers (spec 7, errata 32; a second line behind ``decisions.approve_refusal``; the exporter's recompute is the final check).

Every scenario is a hand-written SQL statement. The state it needs is FORGED with all triggers dropped, then exactly ONE trigger is installed and the
statement must fail with that trigger's message; with no trigger installed the same statement must succeed (the stub: a missing trigger fails the
suite). Because the other triggers are absent while the statement runs, a scenario can only be killed by its own trigger, and a mutant that weakens the
trigger's condition fails the scenario that exercises that condition."""

from __future__ import annotations

import sqlite3

import pytest
from queue_helpers import (
    GOOD_FIELDS,
    REASON,
    assertive_all,
    drop_triggers,
    new_item,
    only_disabled_trigger,
    only_triggers,
    raw_decision,
    raw_export,
    raw_insert,
)

from conftest import settings_for_tests
from intake import decisions, flags, queue_schema, workqueue
from intake.content_code import content_code

F = GOOD_FIELDS
H = "c" * 64  # a plain content code
INS = "INSERT INTO items (id, source_name, source_sha256, tenant_id, state, fields_json, flags_json, created_at) VALUES (?, 'a', ?, 't', ?, ?, ?, 'z')"


def _ins(iid, state, fields="{}", flags_="[]"):
    return INS, (iid, "h-" + iid, state, fields, flags_)


def scenarios():
    """(scenario id, trigger name, message part, builder). A builder gets a forged connection (no triggers) and returns (sql, params)."""
    out: list = []

    def add(sid, trig, msg):
        def deco(fn):
            out.append((sid, trig, msg, fn))
            return fn

        return deco

    # ---- (a) reject-only: each state, each code, insert and update
    for code in flags.reject_only_codes():
        for state in ("APPROVED", "EXPORTED"):
            add(f"a_insert_{state}_{code}", "intake_a_reject_only_insert", "reject_only")(
                lambda c, st=state, cd=code: _ins("a1", st, "{}", f'["D06","{cd}"]')
            )

            def upd(c, st=state, cd=code):
                raw_insert(c, "a2", "NEEDS_PERSON", F, f'["{cd}"]')
                return f"UPDATE items SET state = '{st}' WHERE id = 'a2'", ()

            add(f"a_update_{state}_{code}", "intake_a_reject_only_update", "reject_only")(upd)
    add("a_insert_json_escape", "intake_a_reject_only_insert", "reject_only")(
        lambda c: _ins("a3", "APPROVED", "{}", '["\\u0044\\u0031\\u0030"]')
    )

    def a_update_escape(c):
        raw_insert(c, "a4", "NEEDS_PERSON", F, '["\\u0044\\u0031\\u0030"]')
        return "UPDATE items SET state = 'APPROVED' WHERE id = 'a4'", ()

    add("a_update_json_escape", "intake_a_reject_only_update", "reject_only")(a_update_escape)

    # ---- (b) immutable columns, one scenario each
    for col, val in (
        ("fields_json", "'{}'"),
        ("flags_json", "'[\"D06\"]'"),
        ("source_sha256", "'other'"),
        ("tenant_id", "'other'"),
        ("id", "'other-id'"),
        ("source_text", "'changed text'"),
        ("text_sha256", "'other'"),
        ("source_name", "'other.txt'"),
        ("model_id", "'other-model'"),
        ("tier", "'fallback'"),
        ("prompt_sha256", "'other'"),
        ("cost_micro", "999"),
        ("failing_fields_json", "'[\"x\"]'"),
        ("created_at", "'2030-01-01T00:00:00Z'"),
    ):
        for old in ("READY", "NEEDS_PERSON", "APPROVED", "REJECTED", "EXPORTED"):
            if old != "READY" and col != "flags_json":
                continue

            def b(c, col=col, val=val, old=old):
                raw_insert(c, "b1", old, F, "[]")
                return f"UPDATE items SET {col} = {val} WHERE id = 'b1'", ()

            add(f"b_{col}_{old}", "intake_b_immutable", "immutable")(b)

    def b_uid(c):
        raw_insert(c, "b2", "READY", F)
        return "UPDATE items SET uid = 500 WHERE id = 'b2'", ()

    add("b_uid", "intake_b_immutable", "immutable")(b_uid)

    # ---- (c) null fields
    for state in ("READY", "APPROVED", "EXPORTED"):
        add(f"c_insert_{state}", "intake_c_null_fields_insert", "without fields")(lambda c, st=state: (INS, ("c1", "hc1", st, None, "[]")))

        def c_upd(c, st=state):
            raw_insert(c, "c2", "NEEDS_PERSON", None, '["X18"]')
            return f"UPDATE items SET state = '{st}' WHERE id = 'c2'", ()

        add(f"c_update_{state}", "intake_c_null_fields_update", "without fields")(c_upd)

    # ---- (d) delete protection and append-only tables
    for st in ("APPROVED", "EXPORTED"):

        def d_del(c, st=st):
            raw_insert(c, "d1", st, F)
            return "DELETE FROM items WHERE id = 'd1'", ()

        add(f"d_delete_item_{st}", "intake_d_items_delete", "cannot be deleted")(d_del)

    def forge_rows(c):
        uid = raw_insert(c, "d2", "READY", F)
        raw_decision(c, uid)
        raw_export(c, uid)
        c.execute("INSERT INTO purges (item_id, item_uid, state, purged_by, at) VALUES ('x', 1, 'READY', 'cli', 'z')")

    for tab, sql_u, sql_d in (
        ("decisions", "UPDATE decisions SET reason = 'edited'", "DELETE FROM decisions"),
        ("exports", "UPDATE exports SET row_json = 'edited'", "DELETE FROM exports"),
        ("purges", "UPDATE purges SET purged_by = 'edited'", "DELETE FROM purges"),
    ):
        add(f"d_update_{tab}", f"intake_d_{tab}_update", "append-only")(lambda c, q=sql_u: (forge_rows(c), (q, ()))[1])
        add(f"d_delete_{tab}", f"intake_d_{tab}_delete", "append-only")(lambda c, q=sql_d: (forge_rows(c), (q, ()))[1])

    # ---- (d) an explicit key that exists is refused (INSERT OR REPLACE would delete the old row)
    def forge_one(c):
        uid = raw_insert(c, "dx", "READY", F)
        raw_decision(c, uid)
        raw_export(c, uid)
        c.execute("INSERT INTO purges (item_id, item_uid, state, purged_by, at) VALUES ('x', 1, 'READY', 'cli', 'z')")
        return uid

    def rep_decision(c):
        uid = forge_one(c)
        return (
            "INSERT OR REPLACE INTO decisions (seq, item_uid, decision, approver, content_code, at) VALUES (1, ?, 'reject', 'x', ?, 'z')",
            (uid, H),
        )

    add("d_replace_decision_by_seq", "intake_d_decisions_insert_exists", "append-only")(rep_decision)

    def rep_purge(c):
        forge_one(c)
        return "INSERT OR REPLACE INTO purges (seq, item_id, item_uid, state, purged_by, at) VALUES (1, 'y', 2, 'READY', 'cli', 'z')", ()

    add("d_replace_purge_by_seq", "intake_d_purges_insert_exists", "append-only")(rep_purge)
    for key, val in (("seq", "1"), ("row_id", "'" + "r" * 64 + "'"), ("item_uid", "UID")):

        def rep_export(c, key=key, val=val):
            uid = forge_one(c)
            vals = {"seq": "2", "row_id": "'other-row'", "item_uid": "77"}
            vals[key] = val.replace("UID", str(uid))
            return (
                "INSERT OR REPLACE INTO exports (seq, row_id, item_uid, content_code, row_json, at) "
                f"VALUES ({vals['seq']}, {vals['row_id']}, {vals['item_uid']}, '{H}', '{{}}', 'z')"
            ), ()

        add(f"d_replace_export_by_{key}", "intake_d_exports_insert_exists", "append-only")(rep_export)

    # ---- (e) export needs the latest approve with the same content code
    def e_state(st):
        def f(c):
            uid = raw_insert(c, "e1", st, F)
            raw_decision(c, uid, "approve", H)
            return "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES ('r1', ?, ?, '{}', 'z')", (uid, H)

        return f

    for st in ("READY", "NEEDS_PERSON", "REJECTED", "EXPORTED", "RECEIVED"):
        add(f"e_item_state_{st}", "intake_e_exports_insert", "export needs")(e_state(st))

    def e_missing_item(c):
        return "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES ('r1', 999, ?, '{}', 'z')", (H,)

    add("e_missing_item", "intake_e_exports_insert", "export needs")(e_missing_item)

    def e_stale(c):
        uid = raw_insert(c, "e2", "APPROVED", F)
        raw_decision(c, uid, "approve", H)
        return "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES ('r1', ?, ?, '{}', 'z')", (uid, "d" * 64)

    add("e_stale_code", "intake_e_exports_insert", "export needs")(e_stale)

    def e_no_decision(c):
        uid = raw_insert(c, "e3", "APPROVED", F)
        return "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES ('r1', ?, ?, '{}', 'z')", (uid, H)

    add("e_no_decision", "intake_e_exports_insert", "export needs")(e_no_decision)

    def e_later_reject(c):
        uid = raw_insert(c, "e4", "APPROVED", F)
        raw_decision(c, uid, "approve", H)
        raw_decision(c, uid, "reject", H)  # the latest decision is a reject
        return "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES ('r1', ?, ?, '{}', 'z')", (uid, H)

    add("e_latest_is_reject", "intake_e_exports_insert", "export needs")(e_later_reject)

    def e_only_reject(c):
        uid = raw_insert(c, "e5", "APPROVED", F)
        raw_decision(c, uid, "reject", H)
        return "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES ('r1', ?, ?, '{}', 'z')", (uid, H)

    add("e_only_reject", "intake_e_exports_insert", "export needs")(e_only_reject)

    # ---- (f) transitions
    for old, new in (
        ("REJECTED", "READY"),
        ("REJECTED", "APPROVED"),
        ("EXPORTED", "READY"),
        ("EXPORTED", "APPROVED"),
        ("APPROVED", "REJECTED"),
        ("APPROVED", "READY"),
        ("READY", "RECEIVED"),
        ("READY", "NEEDS_PERSON"),
        ("NEEDS_PERSON", "READY"),
        ("NEEDS_PERSON", "RECEIVED"),
        ("RECEIVED", "REJECTED"),
        ("RECEIVED", "APPROVED"),
        ("RECEIVED", "EXPORTED"),
        ("READY", "EXPORTED"),
        ("NEEDS_PERSON", "EXPORTED"),
    ):

        def f(c, old=old, new=new):
            raw_insert(c, "f1", old, F if old != "RECEIVED" else None)
            return f"UPDATE items SET state = '{new}', fields_json = COALESCE(fields_json, '{{}}') WHERE id = 'f1'", ()

        add(f"f_{old}_to_{new}", "intake_f_transitions", "state move")(f)

    # ---- (g) APPROVED needs a latest approve; (h) EXPORTED needs an export row
    def g_none(c):
        raw_insert(c, "g1", "READY", F)
        return "UPDATE items SET state = 'APPROVED' WHERE id = 'g1'", ()

    add("g_no_decision", "intake_g_approved_needs_decision", "approve decision")(g_none)

    def g_reject(c):
        uid = raw_insert(c, "g2", "READY", F)
        raw_decision(c, uid, "reject")
        return "UPDATE items SET state = 'APPROVED' WHERE id = 'g2'", ()

    add("g_latest_reject", "intake_g_approved_needs_decision", "approve decision")(g_reject)

    def g_reject_after_approve(c):
        uid = raw_insert(c, "g5", "READY", F)
        raw_decision(c, uid, "approve")
        raw_decision(c, uid, "reject")  # the oldest decision is an approve, the latest a reject
        return "UPDATE items SET state = 'APPROVED' WHERE id = 'g5'", ()

    add("g_latest_reject_after_approve", "intake_g_approved_needs_decision", "approve decision")(g_reject_after_approve)

    def g_other_item(c):
        raw_insert(c, "g3", "READY", F)
        u2 = raw_insert(c, "g4", "READY", F)
        raw_decision(c, u2, "approve")  # an approve for ANOTHER item
        return "UPDATE items SET state = 'APPROVED' WHERE id = 'g3'", ()

    add("g_decision_of_another_item", "intake_g_approved_needs_decision", "approve decision")(g_other_item)

    def h_none(c):
        uid = raw_insert(c, "h1", "APPROVED", F)
        raw_decision(c, uid, "approve")
        return "UPDATE items SET state = 'EXPORTED' WHERE id = 'h1'", ()

    add("h_no_export", "intake_h_exported_needs_export", "export row")(h_none)

    def h_other(c):
        uid = raw_insert(c, "h2", "APPROVED", F)
        u2 = raw_insert(c, "h3", "APPROVED", F)
        raw_export(c, u2, "r9")
        return f"UPDATE items SET state = 'EXPORTED' WHERE uid = {uid}", ()

    add("h_export_of_another_item", "intake_h_exported_needs_export", "export row")(h_other)

    # ---- (k) a new row is never decided and never replaces an existing one
    for st in ("APPROVED", "REJECTED", "EXPORTED"):
        add(f"k_insert_state_{st}", "intake_k_insert_states", "decided state")(lambda c, st=st: _ins("k1", st, "{}", "[]"))

    def k_replace_same_id(c):
        raw_insert(c, "k2", "READY", F)
        return (
            "INSERT OR REPLACE INTO items (id, source_name, source_sha256, tenant_id, state, fields_json, flags_json, created_at) VALUES ('k2', 'a', 'other-hash', 't', 'RECEIVED', NULL, '[]', 'z')",
            (),
        )

    add("k_replace_same_id", "intake_k_insert_exists", "already exists")(k_replace_same_id)

    def k_replace_same_hash(c):
        raw_insert(c, "k3", "READY", F, sha_="same-hash")
        return (
            "INSERT OR REPLACE INTO items (id, source_name, source_sha256, tenant_id, state, fields_json, flags_json, created_at) VALUES ('k3b', 'a', 'same-hash', 't', 'RECEIVED', NULL, '[]', 'z')",
            (),
        )

    add("k_replace_same_hash", "intake_k_insert_exists", "already exists")(k_replace_same_hash)

    def k_replace_by_uid(c):
        uid = raw_insert(c, "k4", "REJECTED", F)
        return (
            "INSERT OR REPLACE INTO items (uid, id, source_name, source_sha256, tenant_id, state, fields_json, flags_json, created_at) "
            f"VALUES ({uid}, 'k4x', 'a', 'hk4x', 't', 'RECEIVED', NULL, '[]', 'z')"
        ), ()

    add("k_replace_by_uid", "intake_k_insert_exists", "already exists")(k_replace_by_uid)

    def k_replace_by_id(c):
        raw_insert(c, "k5", "READY", F)
        return (
            "INSERT OR REPLACE INTO items (id, source_name, source_sha256, tenant_id, state, fields_json, flags_json, created_at) VALUES ('k5', 'a', 'hk5x', 't', 'READY', '{}', '[]', 'z')",
            (),
        )

    add("k_replace_by_id", "intake_k_insert_exists", "already exists")(k_replace_by_id)

    # ---- (i) decisions need an undecided item and a plain content code
    for st in ("RECEIVED", "APPROVED", "REJECTED", "EXPORTED"):

        def i_state(c, st=st):
            uid = raw_insert(c, "i1", st, F if st != "RECEIVED" else None)
            return "INSERT INTO decisions (item_uid, decision, approver, content_code, at) VALUES (?, 'reject', 'ap-a', ?, 'z')", (uid, H)

        add(f"i_item_state_{st}", "intake_i_decisions_item", "undecided item")(i_state)
    add("i_missing_item", "intake_i_decisions_item", "undecided item")(
        lambda c: ("INSERT INTO decisions (item_uid, decision, approver, content_code, at) VALUES (999, 'reject', 'ap-a', ?, 'z')", (H,))
    )
    for sid, code in (
        ("short", "c" * 63),
        ("long", "c" * 65),
        ("upper", "C" * 64),
        ("nonhex", "g" * 64),
        ("empty", ""),
        ("space", " " * 64),
    ):

        def i_code(c, code=code):
            uid = raw_insert(c, "i2", "READY", F)
            return "INSERT INTO decisions (item_uid, decision, approver, content_code, at) VALUES (?, 'reject', 'ap-a', ?, 'z')", (
                uid,
                code,
            )

        add(f"i_code_{sid}", "intake_i_decisions_code", "content code")(i_code)

    # ---- (j) an approve needs a record and no reject-only flag
    for code in flags.reject_only_codes():

        def j_flag(c, code=code):
            uid = raw_insert(c, "j1", "NEEDS_PERSON", F, f'["{code}"]')
            return "INSERT INTO decisions (item_uid, decision, approver, content_code, at) VALUES (?, 'approve', 'ap-a', ?, 'z')", (uid, H)

        add(f"j_flag_{code}", "intake_j_approve_guard", "approve not allowed")(j_flag)

    def j_null(c):
        uid = raw_insert(c, "j2", "NEEDS_PERSON", None, '["D06"]')  # approvable flag, so ONLY the null-fields clause can refuse
        return "INSERT INTO decisions (item_uid, decision, approver, content_code, at) VALUES (?, 'approve', 'ap-a', ?, 'z')", (uid, H)

    add("j_null_fields", "intake_j_approve_guard", "approve not allowed")(j_null)

    # ---- (j2) an approve of a flagged item needs a non-empty reason
    for rid, reason in (("null", "NULL"), ("empty", "''"), ("blank", "'   '")):

        def j2(c, reason=reason):
            uid = raw_insert(c, "j2x", "NEEDS_PERSON", F, '["D06"]')
            sql = f"INSERT INTO decisions (item_uid, decision, approver, reason, content_code, at) VALUES ({uid}, 'approve', 'ap-a', {reason}, '{H}', 'z')"
            return sql, ()

        add(f"j2_reason_{rid}", "intake_j2_approve_reason", "needs a reason")(j2)

    # ---- (d) the meta table (schema version) is append-only
    add("d_update_meta", "intake_d_meta_update", "append-only")(lambda c: ("UPDATE meta SET v = '9'", ()))
    add("d_delete_meta", "intake_d_meta_delete", "append-only")(lambda c: ("DELETE FROM meta", ()))
    add("d_insert_or_replace_meta", "intake_d_meta_insert_exists", "append-only")(
        lambda c: ("INSERT OR REPLACE INTO meta (k, v) VALUES ('schema_version', '9')", ())
    )  # erratum 91

    # ---- (l, m, n) the mask map, the per-item key and the trace (WP2c)
    mm = "INSERT INTO item_mask_map (item_uid, placeholder, kind, span_start, span_end, fingerprint, detector) VALUES (?, '<BANK_1>', 'BANK', 0, 3, 'abcdef01', 'd')"
    mm_replace = mm.replace("INSERT INTO", "INSERT OR REPLACE INTO")
    ky = "INSERT INTO item_keys (item_uid, fp_key) VALUES (?, ?)"
    ky_replace = ky.replace("INSERT INTO", "INSERT OR REPLACE INTO")
    tr = "INSERT INTO item_trace (item_uid, step, at, result) VALUES (?, 'mask', 'z', 'pass')"
    key = "a" * 64
    add("l_insert_unknown_item", "intake_l_item_mask_map_insert_state", "while the item is received")(lambda c: (mm, (999,)))
    add("m_insert_unknown_item", "intake_m_item_keys_insert_state", "while the item is received")(lambda c: (ky, (999, key)))
    for st in ("READY", "NEEDS_PERSON", "APPROVED", "REJECTED", "EXPORTED"):
        add(f"l_insert_{st}", "intake_l_item_mask_map_insert_state", "while the item is received")(
            lambda c, st=st: (
                mm,
                (raw_insert(c, "l1", st, F if st != "NEEDS_PERSON" else None, '["D06"]' if st == "NEEDS_PERSON" else "[]"),),
            )
        )
        add(f"m_insert_{st}", "intake_m_item_keys_insert_state", "while the item is received")(
            lambda c, st=st: (
                ky,
                (raw_insert(c, "m1", st, F if st != "NEEDS_PERSON" else None, '["D06"]' if st == "NEEDS_PERSON" else "[]"), key),
            )
        )

    def l_replace(c):
        uid = raw_insert(c, "l2", "RECEIVED")
        c.execute(mm, (uid,))
        return mm_replace, (uid,)

    add("l_insert_or_replace_span", "intake_l_item_mask_map_insert_exists", "not replaced")(l_replace)

    def m_replace(c):
        uid = raw_insert(c, "m2", "RECEIVED")
        c.execute(ky, (uid, key))
        return ky_replace, (uid, "b" * 64)

    add("m_insert_or_replace_key", "intake_m_item_keys_insert_exists", "not replaced")(m_replace)

    def l_update(c):
        uid = raw_insert(c, "l3", "RECEIVED")
        c.execute(mm, (uid,))
        return "UPDATE item_mask_map SET span_end = 9", ()

    add("l_update", "intake_l_item_mask_map_update", "not updated")(l_update)

    def m_update(c):
        uid = raw_insert(c, "m3", "RECEIVED")
        c.execute(ky, (uid, key))
        return "UPDATE item_keys SET fp_key = ?", ("b" * 64,)

    add("m_update", "intake_m_item_keys_update", "not updated")(m_update)
    for st in ("APPROVED", "EXPORTED"):

        def l_delete(c, st=st):
            uid = raw_insert(c, "l4", st, F)
            c.execute(mm, (uid,))
            return "DELETE FROM item_mask_map", ()

        add(f"l_delete_{st}", "intake_l_item_mask_map_delete", "of a decided item")(l_delete)

        def m_delete(c, st=st):
            uid = raw_insert(c, "m4", st, F)
            c.execute(ky, (uid, key))
            return "DELETE FROM item_keys", ()

        add(f"m_delete_{st}", "intake_m_item_keys_delete", "of a decided item")(m_delete)

        add(f"n_insert_{st}", "intake_n_item_trace_insert_open", "after a decision")(lambda c, st=st: (tr, (raw_insert(c, "n4", st, F),)))

    def n_row(c):
        uid = raw_insert(c, "n1", "RECEIVED")
        c.execute(tr, (uid,))
        return uid

    add("n_update", "intake_n_item_trace_update", "append-only")(lambda c: (n_row(c) and "UPDATE item_trace SET result = 'fail'", ()))
    add("n_delete", "intake_n_item_trace_delete", "append-only")(lambda c: (n_row(c) and "DELETE FROM item_trace", ()))
    add("n_insert_or_replace_seq", "intake_n_item_trace_delete", "append-only")(
        lambda c: (
            n_row(c) and "INSERT OR REPLACE INTO item_trace (seq, item_uid, step, at, result) VALUES (1, 1, 'mask', 'z', 'pass')",
            (),
        )
    )
    add("n_insert_unknown_item", "intake_n_item_trace_insert_item", "needs an item")(lambda c: (tr, (999,)))

    def n_replace_by_seq(c):  # erratum 87: refused by the insert trigger itself, without the delete trigger or recursive_triggers
        uid = raw_insert(c, "n5", "RECEIVED")
        c.execute(tr, (uid,))
        return "INSERT OR REPLACE INTO item_trace (seq, item_uid, step, at, result) VALUES (1, ?, 'mask', 'z', 'fail')", (uid,)

    add("n_insert_or_replace_explicit_seq", "intake_n_item_trace_insert_item", "a new seq")(n_replace_by_seq)

    def l_replace_rowid(c):  # erratum 87: the same rowid, another primary key
        uid = raw_insert(c, "l5", "RECEIVED")
        c.execute(mm, (uid,))
        return (
            "INSERT OR REPLACE INTO item_mask_map (rowid, item_uid, placeholder, kind, span_start, span_end, fingerprint, detector) "
            "VALUES (1, ?, '<EMAIL_1>', 'EMAIL', 20, 25, 'abcdef01', 'd')",
            (uid,),
        )

    add("l_insert_or_replace_explicit_rowid", "intake_l_item_mask_map_insert_exists", "not replaced")(l_replace_rowid)
    return out


SCEN = scenarios()


def test_every_trigger_has_a_scenario_and_every_scenario_a_trigger():
    assert {t for _, t, _, _ in SCEN} == set(queue_schema.trigger_sql())  # a new trigger without a test fails here


def test_the_triggers_exist_after_connect(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        have = {r["name"] for r in c.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    assert have == set(queue_schema.trigger_sql())


@pytest.mark.parametrize("sid,trig,msg,build", SCEN, ids=[x[0] for x in SCEN])
def test_the_statement_fails_with_only_its_trigger_and_succeeds_without_it(sid, trig, msg, build, tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path / "with")) as c:
        drop_triggers(c)
        sql, params = build(c)
        only_triggers(c, trig)
        with pytest.raises(sqlite3.IntegrityError, match=msg):
            c.execute(sql, params)
    with workqueue.opened(settings_for_tests(tmp_path / "without")) as c:
        drop_triggers(c)
        sql, params = build(c)
        c.execute(sql, params)  # the stub: no trigger, no refusal


@pytest.mark.parametrize("sid,trig,msg,build", SCEN, ids=[x[0] for x in SCEN])
def test_a_disabled_trigger_fails_its_scenario_by_an_assertion_not_an_exception(sid, trig, msg, build, tmp_path):
    """The 'drop trigger' mutants make the trigger never fire (``WHEN 0``). Proof, per scenario, that this is DETECTED by an assertion failure
    (pytest 'DID NOT RAISE'), not by a KeyError or another exception that a mutation judge would call a crash."""
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        drop_triggers(c)
        sql, params = build(c)
        only_disabled_trigger(c, trig)
        with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
            with pytest.raises(sqlite3.IntegrityError, match=msg):
                c.execute(sql, params)


# ---- controls: what must still pass ---------------------------------------------------------------------------------------------------------
def test_a_is_exact(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        only_triggers(c, "intake_a_reject_only_insert")
        raw_insert(c, "ok1", "APPROVED", F, '["D06"]')  # D06 is approvable
        raw_insert(c, "ok2", "APPROVED", F, '["XD10"]')  # not the exact quoted code
        raw_insert(c, "ok3", "APPROVED", F, '["D100"]')
        raw_insert(c, "ok4", "READY", F, '["D10"]')  # only APPROVED/EXPORTED are guarded


def test_b_free_while_received(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        only_triggers(c, "intake_b_immutable")
        raw_insert(c, "r", "RECEIVED")
        c.execute(
            "UPDATE items SET fields_json = '{}', flags_json = '[\"D06\"]', source_sha256 = 'x', tenant_id = 'y', id = 'r2' WHERE id = 'r'"
        )


def test_c_other_states_may_lack_fields(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        only_triggers(c, "intake_c_null_fields_insert", "intake_c_null_fields_update")
        raw_insert(c, "n", "NEEDS_PERSON", None, '["X18"]')
        raw_insert(c, "r", "RECEIVED")


def test_d_other_states_can_be_deleted(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        only_triggers(c, "intake_d_items_delete")
        for st in ("RECEIVED", "READY", "REJECTED", "NEEDS_PERSON"):
            raw_insert(c, f"d-{st}", st, F if st != "RECEIVED" else None)
            c.execute("DELETE FROM items WHERE id = ?", (f"d-{st}",))


def test_e_the_one_valid_combination_passes_and_an_earlier_reject_does_not_block(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        only_triggers(c, "intake_e_exports_insert")
        uid = raw_insert(c, "e", "APPROVED", F)
        raw_decision(c, uid, "reject", H)
        raw_decision(c, uid, "approve", H)  # the latest decision is the approve
        raw_export(c, uid, "r1", H)


def test_f_the_allowed_moves_pass(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        only_triggers(c, "intake_f_transitions")
        for i, (old, new) in enumerate(
            [
                ("RECEIVED", "READY"),
                ("RECEIVED", "NEEDS_PERSON"),
                ("READY", "REJECTED"),
                ("READY", "APPROVED"),
                ("NEEDS_PERSON", "APPROVED"),
                ("NEEDS_PERSON", "REJECTED"),
                ("APPROVED", "EXPORTED"),
            ]
        ):
            uid = raw_insert(c, f"ok{i}", old, F if old != "RECEIVED" else None)
            c.execute("UPDATE items SET state = ?, fields_json = COALESCE(fields_json, '{}') WHERE uid = ?", (new, uid))
        uid = raw_insert(c, "same", "READY", F)
        c.execute("UPDATE items SET cost_micro = 5 WHERE uid = ?", (uid,))  # no state change: always allowed


def test_g_h_the_valid_moves_pass(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        only_triggers(c, "intake_g_approved_needs_decision", "intake_h_exported_needs_export")
        uid = raw_insert(c, "g", "READY", F)
        raw_decision(c, uid, "approve")
        c.execute("UPDATE items SET state = 'APPROVED' WHERE uid = ?", (uid,))
        raw_export(c, uid)
        c.execute("UPDATE items SET state = 'EXPORTED' WHERE uid = ?", (uid,))


def test_i_j_valid_decisions_pass(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        only_triggers(c, "intake_i_decisions_item", "intake_i_decisions_code", "intake_j_approve_guard")
        uid = raw_insert(c, "ok", "READY", F)
        raw_decision(c, uid, "approve", "0123456789abcdef" * 4)
        u2 = raw_insert(c, "ok2", "NEEDS_PERSON", None, '["X18"]')
        raw_decision(c, u2, "reject", H)  # a reject of a null-field, reject-only item is allowed
        u3 = raw_insert(c, "ok3", "NEEDS_PERSON", F, '["D06"]')
        raw_decision(c, u3, "approve", H)


# ---- the flag table, REPLACE and the pragma -------------------------------------------------------------------------------------------------
def test_a_follows_the_flag_table_at_every_connect(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    workqueue.connect(s).close()
    monkeypatch.setattr(flags, "reject_only_codes", lambda: ("D10", "ZZ9"))
    with workqueue.opened(s) as c:  # reconnect: the triggers are recreated from the changed table
        only_triggers(c, "intake_a_reject_only_insert")
        with pytest.raises(sqlite3.IntegrityError, match="reject_only"):
            raw_insert(c, "n1", "APPROVED", F, '["ZZ9"]')
    monkeypatch.setattr(flags, "reject_only_codes", lambda: ("D10",))
    with workqueue.opened(s) as c:
        only_triggers(c, "intake_a_reject_only_insert")
        raw_insert(c, "n2", "APPROVED", F, '["ZZ9"]')  # no longer reject-only: the old trigger is gone, not stale
        with pytest.raises(sqlite3.IntegrityError, match="reject_only"):
            raw_insert(c, "n3", "APPROVED", F, '["D10"]')


def test_a_codes_are_checked_before_they_go_into_sql(monkeypatch):
    monkeypatch.setattr(flags, "reject_only_codes", lambda: ("D10', 1) OR (1",))
    with pytest.raises(ValueError):
        queue_schema.trigger_sql()


def _exported(s):
    it = new_item(s, "exp")
    decisions.decide(s, it.id, "approve", "ap-a", None, content_code(it), it.version)
    with workqueue.opened(s) as c:
        raw_export(c, it.uid, "r" * 64, content_code(it))
        c.execute("UPDATE items SET state = 'EXPORTED' WHERE uid = ?", (it.uid,))
    return it


def test_insert_or_replace_over_an_exported_item_fails_with_all_triggers(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _exported(s)
    with workqueue.opened(s) as c:
        for sql, params in (
            (
                "INSERT OR REPLACE INTO items (uid, id, source_name, source_sha256, tenant_id, state, fields_json, flags_json, created_at) VALUES (?, ?, 'x', 'newhash', 't', 'READY', '{}', '[]', 'z')",
                (it.uid, it.id),
            ),
            (
                "INSERT OR REPLACE INTO items (id, source_name, source_sha256, tenant_id, state, fields_json, flags_json, created_at) VALUES (?, 'x', 'newhash2', 't', 'READY', '{}', '[]', 'z')",
                (it.id,),
            ),
        ):
            with pytest.raises(sqlite3.IntegrityError):
                c.execute(sql, params)
        assert c.execute("SELECT state FROM items WHERE uid = ?", (it.uid,)).fetchone()[0] == "EXPORTED"


def test_insert_or_replace_over_a_rejected_or_ready_row_fails(tmp_path):
    s = settings_for_tests(tmp_path)
    rej, rdy = new_item(s, "rej"), new_item(s, "rdy")
    decisions.decide(s, rej.id, "reject", "ap-a", REASON, content_code(rej), rej.version)
    with workqueue.opened(s) as c:
        for it in (rej, rdy):
            with pytest.raises(sqlite3.IntegrityError):
                c.execute(
                    "INSERT OR REPLACE INTO items (uid, id, source_name, source_sha256, tenant_id, state, fields_json, flags_json, created_at) VALUES (?, ?, 'x', 'nh', 't', 'RECEIVED', NULL, '[]', 'z')",
                    (it.uid, it.id),
                )
        assert {r[0] for r in c.execute("SELECT state FROM items")} == {"REJECTED", "READY"}


def test_recursive_triggers_pragma_is_set_and_matters_for_delete_triggers(tmp_path):
    """``connect`` sets the pragma. Control: with it off, a REPLACE that removes a row does NOT fire the DELETE trigger."""
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        assert c.execute("PRAGMA recursive_triggers").fetchone()[0] == 1
    plain = sqlite3.connect(":memory:", isolation_level=None)
    for pragma, fires in (("OFF", False), ("ON", True)):
        plain.execute(f"PRAGMA recursive_triggers={pragma}")
        plain.execute("CREATE TABLE t (id TEXT PRIMARY KEY, v TEXT)")
        plain.execute("CREATE TRIGGER d BEFORE DELETE ON t BEGIN SELECT RAISE(ABORT, 'del'); END")
        plain.execute("INSERT INTO t VALUES ('a', 'x')")
        try:
            plain.execute("INSERT OR REPLACE INTO t VALUES ('a', 'y')")
            fired = False
        except sqlite3.IntegrityError:
            fired = True
        assert fired is fires
        plain.execute("DROP TABLE t")
    plain.close()


def test_insert_or_replace_on_decisions_and_exports_fails(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _exported(s)
    with workqueue.opened(s) as c:
        with pytest.raises(sqlite3.IntegrityError):
            c.execute(
                "INSERT OR REPLACE INTO decisions (seq, item_uid, decision, approver, content_code, at) VALUES (1, ?, 'reject', 'x', ?, 'z')",
                (it.uid, H),
            )
        with pytest.raises(sqlite3.IntegrityError):
            c.execute(
                "INSERT OR REPLACE INTO exports (row_id, item_uid, content_code, row_json, at) VALUES (?, ?, ?, '{}', 'z')",
                ("r" * 64, it.uid, H),
            )
        assert (
            c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1 and c.execute("SELECT COUNT(*) FROM exports").fetchone()[0] == 1
        )


def test_the_whole_normal_flow_passes_every_trigger(tmp_path):
    """Control for over-blocking: approve through the API, then the export insert and the EXPORTED move succeed, and a purge of another item works."""
    s = settings_for_tests(tmp_path)
    it = new_item(s, "ok", flags=["D06"])
    gone = new_item(s, "gone")
    decisions.decide(s, it.id, "approve", "ap-a", REASON, content_code(it), it.version)
    with workqueue.opened(s) as c:
        with workqueue.transaction(c):
            raw_export(c, it.uid, "r" * 64, content_code(it))
            c.execute("UPDATE items SET state = 'EXPORTED', version = version + 1 WHERE uid = ?", (it.uid,))
    workqueue.purge(s, gone.id)
    assert workqueue.get(s, it.id).state == "EXPORTED" and workqueue.get(s, gone.id) is None


def test_j2_allows_an_unflagged_approve_without_a_reason_and_a_flagged_one_with_a_reason(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        only_triggers(c, "intake_j2_approve_reason")
        ready = raw_insert(c, "r", "READY", F)
        raw_decision(c, ready, "approve", H)  # no flags: the reason is optional (raw_decision stores NULL)
        flagged = raw_insert(c, "f", "NEEDS_PERSON", F, '["D06"]')
        c.execute(
            "INSERT INTO decisions (item_uid, decision, approver, reason, content_code, at) VALUES (?, 'approve', 'ap-a', ?, ?, 'z')",
            (flagged, REASON, H),
        )
        c.execute(
            "INSERT INTO decisions (item_uid, decision, approver, reason, content_code, at) VALUES (?, 'reject', 'ap-a', NULL, ?, 'z')",
            (flagged, H),
        )  # a reject is not covered


assertive_all(globals())
