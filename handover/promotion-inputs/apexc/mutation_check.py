"""Reverts one fix at a time in a temp copy of this package and runs the targeted test; every mutant must be KILLED, i.e. the test
exits 1 (a failing assertion), not 5 (nothing ran) or 0 (survived). The unmutated copy must pass every target first.

A kill must also be for the intended reason (review 8, M6): (1) a mutant with a sixth field (an expected fragment) is killed only if that
fragment is in the failing test id or in the first assertion line; (2) every kill is pinned in `mutant_kills.json` (mutant -> the failing test
id seen in a reviewed baseline run) and a different failing test is `KILLED-OTHER-TEST`; (3) a kill whose first assertion line holds a crash
(KeyError, TypeError ...) or `internal_error` (the executor's `guarded` turns a crash into `denied:internal_error`) counts as a crash kill,
not an assertion kill; (4) every occurrence of the snippet is reverted, not only the first. A pin proves the kill is stable, not that it is
the best test: the sixth field is the statement of intent.

    uv run python mutation_check.py            # all mutants; fails on a survivor, a wrong reason or an unpinned kill
    uv run python mutation_check.py --record   # rewrite mutant_kills.json from this run (review the diff before committing)
    uv run python mutation_check.py <substring>  # only mutants whose name contains it
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix="apexc_mutation_"))  # unique per invocation: two runs never delete each other's copy
PY = Path(sys.executable)
sys.path.insert(0, str(SRC))
from mutation_judge import Verdict  # noqa: E402
from mutation_judge import judge as judge_core  # noqa: E402

C, R, P, F, N, T = (
    "src/apexc/classify.py",
    "src/apexc/rules.py",
    "src/apexc/ports.py",
    "src/apexc/fakes.py",
    "src/apexc/intake.py",
    "src/apexc/tools.py",
)
X = "src/apexc/executor.py"
RL, EX, TT, HL = "tests/test_rules.py", "tests/test_executor.py", "tests/test_tools.py", "tests/test_hand_labels.py"
IS = "tests/test_isolation.py"
PU = "tests/test_purpose.py"
UN = "tests/test_units.py"
AT = "tests/test_attacks.py"
V6 = "tests/test_v6.py"
V7 = "tests/test_v7.py"
V7B = "tests/test_v7b.py"
V8 = "tests/test_v8.py"
PO = "config/policy.json"
M = [  # name, file, old, new, pytest args
    ("cooling check removed", C, 'elif now < parse_ts(ver["ts"]) + timedelta(hours=win["cooling_off_hours"]):', "elif False:", [RL, "-k", "blocker"]),
    ("cooling < becomes <=", C, 'elif now < parse_ts(ver["ts"]) + timedelta', 'elif now <= parse_ts(ver["ts"]) + timedelta', [RL, "-k", "blocker"]),
    ("edit window >= becomes >", C, 'and parse_ts(e["ts"]) >= cutoff for e in ev)', 'and parse_ts(e["ts"]) > cutoff for e in ev)', [HL]),
    ("attester role not required", C, 'return has_step(ctx, attested_by, "attest_callback", pol) and', "return True and", [RL, "-k", "attester"]),
    ("later bank events ignored", C, "            and not later" + chr(10), "", [RL, "-k", "simultaneous"]),
    ("later event > instead of >=", C, 'later = [e for e in bank_ev if ver and parse_ts(e["ts"]) >= parse_ts(ver["ts"])]', 'later = [e for e in bank_ev if ver and parse_ts(e["ts"]) > parse_ts(ver["ts"])]', [RL, "-k", "simultaneous"]),
    ("submitter, changer and editors not excluded", C, 'editors = {b["changed_by"], sub} | {e["user"] for e in bank_ev}', "editors = set()", [RL, "-k", "attester or simultaneous or bad_verification"]),
    ("ledger: confirmed state not required", C, 'rec["state"] == "confirmed" and rec["vendor_id"]', 'rec["vendor_id"]', [RL, "-k", "bad_verification"]),
    ("ledger: topic not required", C, 'and rec["topic"] == purpose', "", [RL, "-k", "bad_verification"]),
    ("ledger: trusted number not required", C, 'rec["dialed"] in vendor["contact"]["trusted_phones"]', "True", [RL, "-k", "bad_verification"]),
    ("ledger: missing record accepted", C, "    if not rec:\n        return False\n    ok =", "    if not rec:\n        return True\n    ok =", [RL, "-k", "bad_verification"]),
    ("ruling trusted without a controller", C, 'return r["role"] == "finance_controller" if exact else True', "return True", [RL, "-k", "rulings_are_validated"]),
    ("ruling not bound to the invoice", C, 'if x.get("invoice_id") == inv["invoice_id"]), key=lambda x: parse_ts(x["ts"])):', 'if True), key=lambda x: parse_ts(x["ts"])):', [RL, AT, "-k", "rulings_are_validated or m8_a_ruling_for_another"]),
    ("rejection trusts a self-asserted role", C, '        and r["role"] in roles_of(ctx, r["by"])\n        and r["role"] in pol["reject_roles"]', '        and r["role"] in pol["reject_roles"]', [RL, "-k", "rejection_is_validated"]),
    ("rejecter may be the earlier submitter", C, '        and emp(ctx, r["by"]) != emp(ctx, h.get("submitted_by", ""))\n', "", [RL, "-k", "rejection_is_validated"]),
    ("rejecter may be the current submitter", C, '        and emp(ctx, r["by"]) != emp(ctx, sub)\n', "", [RL, "-k", "rejection_is_validated"]),
    ("supervisor may lift an exact duplicate", R, 'return "finance_controller" in roles if reason == "duplicate_exact" else True', "return True", [RL, "-k", "hold_lifting"]),
    ("evidence not required for lifts", R, '    need = pol["lift_evidence"].get(action)\n', '    return True\n    need = pol["lift_evidence"].get(action)\n', [RL, "-k", "evidence"]),
    ('sensitive edits unchecked', C, 'if _sensitive(e["field"], pol):  # M4: never ages out; only an authentic, independent verification clears it', 'if False:', [RL, AT, '-k', 'sensitive_edit or m4']),
    ("contact edits age out", C, "        if edits:  # a contact edit never ages out", "        if edits and (now - max(ts for ts, _ in edits)) < timedelta(days=30):  # ages out", [RL, "-k", "contact_edits"]),
    ("unknown field names ignored", C, 'return "unknown"  # fail closed', 'return "other"  # fail closed', [RL, "-k", "closed_list"]),
    ("payee_collision deleted", C, 't.add("payee_collision")', "pass", [RL, "-k", "collisions"]),
    ("tax_id_collision deleted", C, 't.add("tax_id_collision")', "pass", [RL, "-k", "collisions"]),
    ("cross_vendor_duplicate deleted", C, '            dup_t.add("cross_vendor_duplicate")', "            pass", [RL, "-k", "collisions or same_number"]),
    ("related link ignored", C, '            if related(v, o["vendor_id"], ctx, pol):\n                continue', "            if False:\n                continue", [RL, "-k", "collisions"]),
    ("empty tax ids collide", C, 'if ot and ot == norm_acct(v["tax_id"])', 'if ot == norm_acct(v["tax_id"])', [RL, "-k", "collisions"]),
    ('leading zeros not normalised', C, 'return s.lstrip("0") or ("0" if s else "")', 'return s', [RL, '-k', 'collisions']),
    ("fail-open employee id", C, 'raise ValueError(f"directory user {uid} has no employee_id")', 'return "?" + uid', [RL, "-k", "directory_failures"]),
    ("recurring evidence not required", C, '    v = ctx["vendor"]\n    for e in ctx.get("period_evidence", []):', '    return True\n    v = ctx["vendor"]\n    for e in ctx.get("period_evidence", []):', [RL, "-k", "claimed_period"]),
    ("recurring evidence source not checked", C, ' and e["source"] in pol["recurring_evidence_sources"]', "", [RL, "-k", "claimed_period"]),
    ('controller schedule not attested', C, 'if e["source"] != "controller_schedule" or attestation_ok(', 'if True or attestation_ok(', [RL, AT, '-k', 'claimed_period or m10']),
    ("cadence unbounded", C, 'return cad if cad is not None and w["recurring_cadence_min_days"] <= cad <= w["recurring_cadence_max_days"] else None', "return cad", [RL, "-k", "bounded"]),
    ("early repeat ignores the PO", C, ' and (same_po or not (inv["po_refs"] or h["po_refs"])):', ":", [HL]),
    ("early repeat counts negative entries", C, "if not near and cad is not None and htotal >= 0 and gap < cad - slack", "if not near and cad is not None and gap < cad - slack", [RL, "-k", "negative_history"]),
    ("near duplicate counts negative entries", C, "and htotal >= 0 and abs(htotal - total)", "and abs(htotal - total)", [RL, "-k", "negative_history"]),
    ("po_line_overbilled deleted", C, 't.add("po_line_overbilled")', "pass", [RL, "-k", "overbilled or over_receipt or blanket"]),
    ("blanket lines consumed", C, '            if p.get("blanket"):\n                continue', "            if False:\n                continue", [RL, "-k", "blanket"]),
    ("over_receipt deleted", C, 't.add("over_receipt")', "pass", [RL, "-k", "over_receipt"]),
    ("own record counts as history", C, 'return h["invoice_id"] != inv["invoice_id"] and not valid_reject', "return not valid_reject", [RL, "-k", "own_record"]),
    ("credit memo reduces exposure", C, 'max(0, minor(h["total_minor"]))', 'minor(h["total_minor"])', [RL, "-k", "credit_memos"]),
    ("unknown status not live", C, 'return h["invoice_id"] != inv["invoice_id"] and not valid_reject(h, ctx, pol, inv["submitted_by"])', 'return h["status"] in pol["statuses"]["known"] and h["invoice_id"] != inv["invoice_id"] and not valid_reject(h, ctx, pol, inv["submitted_by"])', [RL, "-k", "status"]),
    ("Unicode digits accepted", "src/apexc/normalise.py", 'r"-?[0-9]+"', r'r"-?\d+"', [RL, "-k", "credit_memos"]),
    ("SoD keyed on the account", C, 'return d["employee_id"]', 'return "?" + uid', [RL, "-k", "sod_is_keyed"]),
    ("binding: total and tier not bound", R, '"total_minor": str(minor(inv["total_minor"])), "currency": inv["currency"], "tier": tier,', "", [RL, "-k", "release_recheck"]),
    ("binding: tier not bound", R, '"currency": inv["currency"], "tier": tier,', '"currency": inv["currency"],', [RL, "-k", "new_live_invoice"]),
    ("binding: master_version optional", R, 'v["master_version"]', 'v.get("master_version", 0)', [RL, "-k", "master_version_is_required"]),
    ("recheck ignores the cleared ledger", R, "- cleared\n    if bad:", "\n    if bad:", [RL, "-k", "end_to_end"]),
    ("recheck allows new types", R, 'new = fresh - set(bound["types"])', "new = set()", [RL, "-k", "new_live_invoice or catches_payee or hard_block"]),
    ("cleared record needs no evidence", R, 'if r.get("evidence_id") and r["by"] in directory', 'if r["by"] in directory', [RL, "-k", "hard_block"]),
    ('check_unique: any truthy id bypasses', R, '        if not rid:\n            return collision\n', '        if rid:\n            return ""\n        if not rid:\n            return collision\n', [RL, '-k', 'ruling_bypass']),
    ("check_unique: ruling for another invoice", R, ' or r["invoice_id"] != new["invoice_id"]', "", [RL, "-k", "ruling_bypass"]),
    ('check_unique: reuse allowed', R, 'if any(x.get("duplicate_ruling_id") == rid and x["idempotency_key"] != new["idempotency_key"] for x in entries):\n            return "RulingReused"', 'if False:\n            return "RulingReused"', [RL, '-k', 'ruling_bypass']),
    ("check_unique: not a controller", R, ' or r["role"] != "finance_controller"', "", [RL, "-k", "ruling_bypass"]),
    ("ReleaseStore: conflict ignored", R, 'if row["blob"] != blob:\n                    raise IdempotencyConflict(key)', 'if False:\n                    raise IdempotencyConflict(key)', [RL, "-k", "idempotent_replay"]),
    ("ReleaseStore: dequeue not tracked", R, 'row["status"] = "dequeued"', "pass", [RL, "-k", "timeout_after_apply"]),
    ("idempotency key lacks the invoice id", P, "parts = (action, vendor_id, invoice_id, norm_number", "parts = (action, vendor_id, norm_number", [RL, "-k", "release_key_is"]),
    ("scope not enforced on tool ids", T, "        if k in args and args[k] not in allowed:", "        if False:", [TT, "-k", "scope or adversarial"]),
    ("hold cap fails open", R, '"place": True, "escalate"', '"place": n_held_invoices_for_vendor < 10, "escalate"', [RL, "-k", "hold_pressure"]),
    ("hold pressure never escalates", R, '"escalate": n_held_invoices_for_vendor >= h["max_open_invoices_per_vendor"]', '"escalate": False', [RL, "-k", "hold_pressure"]),
    ("long approver cap removed", R, ' and n_cleared_long < t["approver_cap_long"]', "", [RL, "-k", "approver_cap"]),
    ("approver cap keyed on the account", R, "c = counts.get(emp(ctx, u), {})", "c = counts.get(u, {})", [RL, "-k", "approver_cap"]),
    ("vendor cap ignored", R, 'if vendor_total_cleared >= pol["tiers"]["vendor_cap_per_window"]:', "if False:", [RL, "-k", "approver_cap"]),
    ("identities not enforced", R, 'return op in pol["identities"].get(identity, {}).get(kind, [])', "return True", [RL, "-k", "identities_are_enforced"]),
    ("identity conflicts not checked", R, 'if set(r["write"]) & set(c["approval_side"]) and set(r["write"]) & set(c["action_side"])', "if False", [RL, "-k", "identities_are_enforced"]),
    ("verdict: scripted green allowed", R, 'return "amber" if mode == "scripted" and color == "green" else color', "return color", [TT, "-k", "verdict"]),
    ('executor: one plan above the limit', X, 'return ["plan_1", "plan_2"] if hard or tier not in ("none", "human", "human_nonmoney") else ["plan_1"]', 'return ["plan_1"]', [EX, '-k', 'four_eyes']),
    ('executor: open hold ignored', X, 'if self.erp.open_holds(invoice_id):', 'if False:', [EX, '-k', 'hold_that_is_not_lifted']),
    ('executor: cooling ignored', X, 'if not cooling_ok(max(starts, key=parse_ts), self.clock.now(), self.pol):', 'if False:', [EX, '-k', 'cooling_off']),
    ("executor: approval TTL ignored", X, "if any(approval_expired(", "if False and any(approval_expired(", [EX, "-k", "stale_approvals"]),
    ("executor: failed audit write ignored", X, 'except AuditWriteError:\n            return "denied:audit_write_failed"', "except AuditWriteError:\n            pass", [EX, "-k", "audit"]),
    ('executor: shadow level ignored on release', X, 'if self.level != "suggest":\n            return "shadow_level" if self.level == "shadow" else "level_unknown"', 'if False:\n            return "shadow_level"', [EX, '-k', 'shadow']),
    ('executor: shadow level ignored on holds', X, 'if self.level != "suggest":\n            return []', 'if False:\n            return []', [EX, '-k', 'shadow']),
    ("executor: SoD ignored", X, "if sod_violations(steps, self.directory, self.pol):", "if False:", [AT, "-k", "b3_the_clearer or b3_the_attester_of"]),
    ("payments: unique indexes removed", F, "err = check_unique(others, probe, self.pol, self.directory, rulings)", "err = None", [EX, "-k", "unique_indexes"]),
    ("payments: key replay not absorbed", F, '            if row is not None:\n                if row["blob"] != blob:', '            if False:\n                if row["blob"] != blob:', [EX, "-k", "port_itself"]),
    ('callout: slots not validated', 'src/apexc/fakes.py', 'if not callback_slots_ok(template_id, slots, self.pol):\n            self._deny("slots_rejected"', 'if False:\n            self._deny("slots_rejected"', ['tests/test_executor.py', '-k', 'callout']),
    ("callout: number taken from the request", F, 'phone = self.erp.vendors[vendor_id]["contact"]["verified_phone"]', 'phone = slots.get("phone", "+1-555-0199")', [EX, "-k", "callout"]),
    ("reserve_receipt: no capacity check", F, "if (po_id, line, invoice_id) in self.reserved or used + qty > available:", "if (po_id, line, invoice_id) in self.reserved:", [EX, "-k", "reserve_the_same_receipt"]),
    ('intake: effect not idempotent', N, 'if receipt not in t.effects:', 'if True:', [EX, '-k', 'burst']),
    ('intake: tenant not in the key', N, '        t = self._tenant(tenant)\n        digest', '        t = self._tenant("")\n        digest', [EX, '-k', 'colliding_ids']),
    ("intake: reconciliation blind", N, '"missing": sorted(source_ids - mine)', '"missing": []', [EX, "-k", "never_arrived"]),
    ('intake: export unscoped', N, '        t = self._tenant(tenant)\n        with t.lock:\n            return [{', '        t = self._tenant(next(iter(self._t)))\n        with t.lock:\n            return [{', [EX, '-k', 'colliding_ids']),
    ("isolation: one audit chain for all tenants", F, 'prev = mine[-1]["sha256"] if mine else "0" * 64', 'prev = self.events[-1]["sha256"] if self.events else "0" * 64', [IS, "-k", "audit_chains"]),
    ("isolation: other demo's path read", X, "from __future__ import annotations", 'from __future__ import annotations' + chr(10) + 'PATH = "demos/refunds/data/gold.jsonl"', [IS, "-k", "reads_another"]),
    ("isolation: unknown namespace allowed", R, 'if kind not in pol["namespaces"]:' + chr(10) + '        raise KeyError(kind)', 'if False:' + chr(10) + '        raise KeyError(kind)', [IS, "-k", "namespace"]),
    ("isolation: ERP state shared between clients", F, "self.vendors: dict[str, dict] = {}", 'self.vendors = __import__("builtins").__dict__.setdefault("_apexc_v", {})', [IS, "-k", "never_feed"]),
    ("isolation: audit tenant hash leaks into the chain", F, 'prev = mine[-1]["sha256"] if mine else "0" * 64', 'prev = self.events[-1]["sha256"] if self.events else "0" * 64', [IS, "-k", "byte_identical or audit_chains"]),
    ('normalise: line breaks deleted instead of separating words', 'src/apexc/normalise.py', '" " if (ch in WHITESPACE_BREAKS or ch.isspace()) else ch', 'ch', ['tests/test_units.py', '-k', 'line_breaks']),
    ("purpose limitation: model sees the invoice account in full", R, '"invoice.remit_account_last4": last4(inv["remit"]["account"]),', '"invoice.remit_account_last4": inv["remit"]["account"],', [PU, "-k", "canary"]),
    ("purpose limitation: model sees the invoice tax id in full", R, '"invoice.tax_id_last4": last4(inv["vendor_claimed"]["tax_id"]),', '"invoice.tax_id_last4": inv["vendor_claimed"]["tax_id"],', [PU, "-k", "canary"]),
    ('purpose limitation: model sees the master account', R, '"vendor.name": cap((ctx["vendor"] or {}).get("name")),', '"vendor.name": ctx["vendor"]["bank"]["account"],', [PU, '-k', 'canary']),
    ('purpose limitation: read port gives the agent the full vendor', 'src/apexc/fakes.py', 'return v if full else {', 'return v if True else {', ['tests/test_purpose.py', '-k', 'read_only']),
    ("purpose limitation: reads not logged", F, 'self.audit.append(self.erp.tenant, "read", identity=identity, object=obj, purpose=purpose)', "pass", [PU, "-k", "read_only"]),
    ("purpose limitation: read right not checked", F, 'authorize_op(identity, obj, self.pol, "read")', "pass", [PU, "-k", "read_only"]),
    ('purpose limitation: read rate cap removed', 'src/apexc/fakes.py', 'limited = len(self._stamps) >= self.pol["limits"]["erp_reads_per_minute"]', 'limited = False', ['tests/test_purpose.py', '-k', 'read_rate or concurrency']),
    ("purpose limitation: connection cap removed", F, 'if outer._open >= outer.pol["limits"]["erp_connections"]:', "if False:", [PU, "-k", "read_rate"]),
    ("purpose limitation: dry-run ignored", X, "if not self.live:", "if False:", [PU, "-k", "dry_run"]),
    ('purpose limitation: daily count cap removed', 'src/apexc/executor.py', 'n_today >= lim["releases_per_day"] or', 'False or', ['tests/test_purpose.py', '-k', 'per_day']),
    ('purpose limitation: daily amount cap removed', 'src/apexc/executor.py', 'n_today >= lim["releases_per_day"] or total_today + amt > lim["release_minor_per_day"][cur]', 'n_today >= lim["releases_per_day"]', ['tests/test_purpose.py', '-k', 'per_day']),
    ('purpose limitation: kill switch ignored', 'src/apexc/executor.py', ['return "kill_switch" if (self.state.killed or self.cfg.blocked()) else None', 'with self.cfg.effect():  # M5: counted in flight until the queue time is recorded; the kill switch waits for it'], ['return None', 'if True:'], ['tests/test_purpose.py', '-k', 'kill_switch'], 'denied:kill_switch'),
    ('purpose limitation: kill switch open to anyone', 'src/apexc/executor.py', 'authorize_op(identity, "kill_switch", self._safe_pol)', 'pass', ['tests/test_purpose.py', '-k', 'kill_switch'], 'DID NOT RAISE'),
    ('purpose limitation: no compensation after the undo window', 'src/apexc/executor.py', 'if undo_window_open(queued_at, self.clock.now(), self._safe_pol):', 'if True:', ['tests/test_purpose.py', '-k', 'undo_then']),
    ('purpose limitation: anyone may request the undo', 'src/apexc/executor.py', 'authorize_op(requested_by, "request_dequeue", self._safe_pol)', 'pass', ['tests/test_purpose.py', '-k', 'undo_then']),
    ("purpose limitation: egress to a number not on file", F, 'if to not in c["trusted_phones"] or to != c["verified_phone"]:', "if False:", [PU, "-k", "egress"]),
    ("purpose limitation: egress to an address not on file", F, 'elif to != c["email_on_file"] or c.get("email_changed_at"):', "elif False:", [PU, "-k", "egress"]),
    ('purpose limitation: egress template not tied to the channel', 'src/apexc/fakes.py', 'if template_id not in self.pol["egress_templates"].get(channel, ()):', 'if False:', ['tests/test_purpose.py', '-k', 'egress']),
    ("purpose limitation: egress output check removed", F, "if any(len(s) >= 6 and s in body_key for s in secret):", "if False:", [PU, "-k", "egress"]),
    ('purpose limitation: egress cap removed', F, 'if sent_today >= self.pol["limits"]["egress_per_day"]:', 'if False:', [PU, '-k', 'egress']),
    ('B1: a plan label may repeat', X, 'if len(set(labels)) != len(labels):\n            return "denied:plan_repeated"', 'if False:\n            return "denied:plan_repeated"', [AT, '-k', 'b1_one_person']),
    ('B1: an unknown plan label is accepted', X, 'if any(lbl not in STEP_OF_PLAN for lbl in labels):\n            return "denied:plan_unknown"', 'if False:\n            return "denied:plan_unknown"', [AT, '-k', 'b1_one_person']),
    ('B1: a missing plan is not checked', 'src/apexc/executor.py', 'if set(need) - set(labels):', 'if False:', ['tests/test_v10.py', '-k', 'b1_the_label_check'], 'plans_unexpected'),
    ('B1: an extra plan is accepted', X, 'if set(labels) - set(need):', 'if False:', [AT, '-k', 'b1_one_person']),
    ("B1: the approver's role is not checked against the plan", X, 'if not set(roles_of(d, r["by"])) & set(sets[r["plan"]]):\n                return "denied:approver_role"', 'if False:\n                return "denied:approver_role"', [AT, '-k', 'b1_one_person or b1_random']),
    ('B1: distinct persons not required', X, 'if len({emp(d, r["by"]) for r in recs}) != len(recs):', 'if False:', [AT, '-k', 'b1_one_person or b1_random']),
    ('B1: an unknown approver is not named', X, 'if r["by"] not in self.directory:\n                return "denied:approver_unknown"', 'if False:\n                return "denied:approver_unknown"', [AT, '-k', 'b1_one_person']),
    ('B2: the replay/edit short-circuit removed', X, 'if seen is not None:', 'if False:', [AT, '-k', 'b2_an_edited']),
    ('B2: an edited invoice treated as the same', X, 'if not same:\n                return "denied:changed_after_release"', 'if False:\n                return "denied:changed_after_release"', [AT, '-k', 'b2_an_edited']),
    ('B2: approvals are not single use', 'src/apexc/executor.py', 'if ok and not self.erp.consume_approvals(APPR, approval_ids):', 'if False:', ['tests/test_attacks.py', '-k', 'b2_a_consumed']),
    ('B2: an approval for another invoice accepted', 'src/apexc/executor.py', 'if r is None or not validate_approval(r) or r["invoice_id"] != invoice_id:', 'if r is None or not validate_approval(r):', ['tests/test_attacks.py', '-k', 'b2_the_release_key']),
    ('B3: a clear is not re-proved at release', X, 'if not clear_evidence_ok(c["type"], c["evidence_id"], c["by"], case, self.pol):\n                return "denied:clear_evidence_invalid"', 'if False:\n                return "denied:clear_evidence_invalid"', [AT, '-k', 'b3_a_forged']),
    ('B3: no ledgered cooling start fails open', X, 'if not starts:\n                return "denied:cooling_start_missing"\n            if not cooling_ok(max(starts, key=parse_ts), self.clock.now(), self.pol):', 'if starts and not cooling_ok(max(starts, key=parse_ts), self.clock.now(), self.pol):', [AT, '-k', 'b3_no_ledgered']),
    ('B3: SoD ignores the clearer', X, 'steps.append((c["by"], "clear_hard_block"))', 'pass', [AT, '-k', 'b3_the_clearer']),
    ('B3: SoD ignores the evidence attester', X, 'steps.append((ctx["callbacks"][c["evidence_id"]]["attested_by"], "attest_callback"))  # clears AND new-vendor verifications', 'pass', [AT, V6, '-k', 'b3_the_attester_of or m1_the_new_vendor']),
    ('B3: clear evidence topic not checked', R, 'if rec is None or not attest_topic_ok(rec["topic"], typ, pol):', 'if rec is None:', [AT, '-k', 'b3_the_clear_evidence']),
    ('B3: clear attester not independent', R, 'excluded = master_editors(ctx) | {case["invoice"]["submitted_by"], clearer}', 'excluded = set()', [AT, '-k', 'b3_the_attester_is']),
    ('B3: the earlier verifier may attest the fresh call', R, 'return not (topic == "bank" and fresh_call and attest_conflict(prior, rec["attested_by"], ctx["directory"]))', 'return True', [AT, '-k', 'b3_the_earlier']),
    ('M1: a missing hold row is not checked', X, 'if any(t not in rows for t in types):\n            return "denied:hold_missing"', 'if False:\n            return "denied:hold_missing"', [AT, '-k', 'm1_an_exception or m1_a_partly']),
    ('M2: the executor reads a stale snapshot', X, 'return self.erp.read_case(invoice_id)', 'return self.__dict__.setdefault("_snap", {}).setdefault(invoice_id, self.erp.read_case(invoice_id))', [AT, '-k', 'm2_']),
    ('M3: the daily cap is checked but not reserved', X, 'self.state.count_by_day[day], self.state.minor_by_day[(cur, day)] = n_today + 1, total_today + amt', 'pass', [AT, '-k', 'm3_the_daily']),
    ('M3: a refused release keeps its reservation', X, 'self.state.count_by_day[day] = max(0, self.count_by_day.get(day, 0) - 1)', 'pass', [AT, '-k', 'm7_sixteen']),
    ('M7: a duplicate refusal escapes as an exception', X, 'except (DuplicateBusinessKey, DuplicateExposure) as e:', 'except ZeroDivisionError as e:', [AT, '-k', 'm7_sixteen']),
    ('M7: a definite refusal leaves the row pending', R, '            with self._lock:\n                del self.rows[key]\n            return "denied:" + e.reason, None', '            return "denied:" + e.reason, None', [AT, '-k', 'm7_sixteen']),
    ('M8: the executor does not carry the ledgered ruling', X, 'e["duplicate_ruling_id"] = max(mine, key=lambda r: parse_ts(r["ts"]))["ruling_id"]', 'pass', [AT, '-k', 'm8_']),
    ('M8: a ruling bypasses every earlier invoice', R, 'return collision if r["history_id"] != e["invoice_id"] else ""', 'return ""', [RL, AT, '-k', 'ruling_bypass or m8_']),
    ('M8: a revoked ruling still bypasses', R, 'or latest is not r\n', '\n', [RL, '-k', 'ruling_bypass']),
    ('M8: the ruler may be the submitter', R, '            or emp(ctx, r["by"]) == emp(ctx, new.get("submitted_by", ""))\n', '', [RL, '-k', 'ruling_bypass']),
    ('M6: a receipt id need not exist', R, 'return bool(g) and g["po_id"] in inv["po_refs"]', 'return True', [RL, AT, '-k', 'evidence_bearing or m6']),
    ('M6: a corrected ref need not exist', R, 'return bool(c) and c["invoice_id"] == inv["invoice_id"] and c["vendor_id"] == vendor_id', 'return True', [RL, AT, '-k', 'evidence_bearing or m6']),
    ('M6: a ruling row need not exist', R, '        if row is None:\n            return False\n', '', [RL, '-k', 'evidence_bearing']),
    ('M6: the second lifter need not have acted', R, 'and any(r["by"] == second for r in mine)', '', [RL, '-k', 'evidence_bearing']),
    ('M6: evidence may be re-used across invoices', R, 'if led.get("used_by", {}).get(val, inv["invoice_id"]) != inv["invoice_id"]:\n        return False', 'if False:\n        return False', [RL, AT, '-k', 'evidence_bearing or m6']),
    ('M9: lift_hold takes any identity', F, 'self._auth(identity, "lift_hold")', 'pass', [AT, '-k', 'm9_every_write']),
    ('M9: set_hold takes any identity', F, 'self._auth(identity, "hold")', 'pass', [AT, '-k', 'm9_every_write']),
    ('M9: the approval ledger takes any identity', 'src/apexc/fakes.py', 'self._auth(identity, "record_approval")\n        if not json_keys_ok(rec):', 'if not json_keys_ok(rec):', ['tests/test_attacks.py', '-k', 'm9_every_write']),
    ('M9: enqueue takes any identity', 'src/apexc/fakes.py', 'self._auth(identity, "enqueue")', 'pass', ['tests/test_attacks.py', '-k', 'm9_every_write']),
    ('M9: attest takes any identity', F, 'authorize_op(identity, "attest_callback", self.pol)', 'pass', [AT, '-k', 'm9_every_write']),
    ('M9: rulings take any identity', F, 'self._auth(identity, "ruling")', 'pass', [AT, '-k', 'm9_every_write']),
    ('M9: the approver cap is not enforced', X, 'if not approver_cap_ok(len(c["short"] - {invoice_id}), self.pol, len(c["long"] - {invoice_id})):', 'if False:', [AT, '-k', 'm9_the_helpers']),
    ('M9: hold aging is not enforced', X, 'if r["open"] and hold_aging_due(r["placed_at"], self.clock.now(), self.pol):', 'if False:', [AT, '-k', 'm9_the_helpers']),
    ('M9: may_reject is not enforced', X, 'if self._blocked() or not may_reject(', 'if self._blocked() or False and not may_reject(', [AT, '-k', 'm9_rejecting']),
    ("M5: an exempt vendor's same total is not suspect", C, 'if not near and cad is None and (ctx["vendor"] or {}).get("po_exempt") and gap <= win["same_po_same_total_days"]:', 'if False:', [AT, '-k', 'm5_a_po']),
    ('M10: a related link needs no ledger record', C, 'and attestation_ok(link.get("attestation_id"), link["attested_by"], "related_vendor", ctx, pol, master_editors(ctx))', 'and "finance_controller" in roles_of(ctx, link["attested_by"])', [AT, '-k', 'm10_an_attestation']),
    ('M10: an attester may be a master editor', C, '        and attester_ok(claimed_by, excluded, ctx, pol)\n', '        and attester_ok(claimed_by, set(), ctx, pol)\n', [AT, '-k', 'm10_an_attestation']),
    ('m1: a later ruling does not revoke', C, 'rulings[r["history_id"]] = r  # the LATEST', 'rulings.setdefault(r["history_id"], r)  # the LATEST', [AT, '-k', 'm1_latest']),
    ('m3: free text is not capped', R, 'return x[:FREE_TEXT_CAP] if isinstance(x, str) else x', 'return x', [AT, '-k', 'm3_every']),
    ('m4: the approver summary is not output-checked', 'src/apexc/tools.py', 'leaks = summary is not None and summary_leaks(', 'leaks = False and summary_leaks(', ['tests/test_attacks.py', '-k', 'm4_the'], 'routing'),
    ('m5: chain fields can be set by the caller', F, 'if self.RESERVED & fields.keys():', 'if False:', [AT, '-k', 'm5_the_audit']),
    ('m5: the egress destination is not masked', F, 'to=mask_dest(to)', 'to=to', [AT, '-k', 'm5_the_audit']),
    ('m6: a tampered redelivery is silent', N, 'elif row["sha256"] != digest:', 'elif False:', [AT, '-k', 'm6_']),
    ("m7: audit append scans the tenant's chain", F, 'prev = mine[-1]["sha256"] if mine else "0" * 64', 'prev = [x for x in self.events if x["tenant"] == tenant][-1]["sha256"] if mine else "0" * 64', [AT, '-k', 'm7_one']),
    ('m9: an all-zero account is the empty key', C, 'return s.lstrip("0") or ("0" if s else "")', 'return s.lstrip("0")', [AT, '-k', 'm9_all_zero']),
    ('m9: dequeued is an unknown status', PO, '      "dequeued",\n', '', [AT, '-k', 'm9_all_zero']),
    ('m11: a non-integer quantity is not rejected', C, 'if any(type(ln["qty"]) is not int for ln in inv["lines"]):', 'if False:', [AT, '-k', 'm11_']),
    ('B2: the release key is shared by every invoice', P, '("enqueue", tenant, invoice_id, "release")', '("enqueue", tenant, "release")', [RL, '-k', 'release_key_is']),
    ('B-1: evidence older than the change is accepted', C, 'return ts >= parse_ts(v["bank"]["changed_at"]) and not any(', 'return not any(', [V6, '-k', 'b1_an_old']),
    ('B-1: a later bank event does not void evidence', C, ' and not any(_bankish(e["field"], pol) and parse_ts(e["ts"]) >= ts for e in ev)', '', [V6, '-k', 'b1_a_later']),
    ('B-1: contact evidence freshness not checked', C, 'return all(t <= ts for t in times)', 'return True', [V6, '-k', 'b1_a_later']),
    ('B-1: master-edit evidence freshness not checked', C, 'return not any(_sensitive(e["field"], pol) and parse_ts(e["ts"]) > ts for e in ev)', 'return True', [V6, '-k', 'b1_a_later']),
    ('B-1: freshness not applied to a clear', R, 'and evidence_fresh(topic, rec["ts"], ctx, pol)', 'and True', [V6, '-k', 'b1_an_old']),
    ('M-1: the new-vendor attester is not a SoD step', X, 'steps.append((ctx["callbacks"][c["evidence_id"]]["attested_by"], "attest_callback"))', 'if c["kind"] == "clear":\n                steps.append((ctx["callbacks"][c["evidence_id"]]["attested_by"], "attest_callback"))', [V6, '-k', 'm1_the_new_vendor']),
    ('M-1: a master editor may take a step', X, 'if actors & {emp(d, e) for e in master_editors(ctx)}:', 'if False:', [V6, '-k', 'm1_a_master_editor']),
    ('M-1: a second lifter is not a SoD step', X, 'steps.append((ev["second_lifter"], "lift_hold"))', 'pass', [V6, '-k', 'm1_a_second']),
    ('M-2: release is not guarded', X, '@guarded("denied:internal_error")\n    def release(', 'def release(', [V6, '-k', 'm2_unexpected']),
    ('M-2: a malformed clear record is not fail-closed in the rule', R, 'except (KeyError, TypeError, ValueError, AttributeError):\n        return False', 'except ZeroDivisionError:\n        return False', [V6, '-k', 'm2_a_malformed']),
    ('M-2: compensate has no typed unknown key', 'src/apexc/executor.py', 'return "denied:unknown_key"', 'raise KeyError(key)', ['tests/test_v6.py', '-k', 'm2_unknown']),
    ('M-3: the queue time is not recorded', X, 'self.state.queued_at[key] = self.clock.now()', 'pass', [V6, '-k', 'm3_an_audit_outage']),
    ('M-3: an audit outage after the enqueue reaches the caller', X, '        except Exception:  # noqa: BLE001 - after an action that cannot be undone, ANY audit failure queues the event; nothing may raise here', '        except ZeroDivisionError:', [V6, '-k', 'm3_an_audit_outage']),
    ('M-3: reconcile does not record the queue time', X, 'self.state.queued_at.setdefault(key, self.clock.now())', 'pass', [V6, '-k', 'm3_reconcile']),
    ('M-3: a failed reconcile keeps the reservation', X, 'if out == "retry_safe":\n            self._unreserve(key)', 'if out == "retry_safe":\n            pass', [V6, '-k', 'm3_reconcile']),
    ('M-3: approvals are not audited', F, 'self._log(\n                "approval_recorded",', '(lambda *a, **k: None)(\n                "approval_recorded",', [V6, '-k', 'm3_every']),
    ('M-3: rulings are not audited', F, 'self._log(\n            "ruling_recorded",', '(lambda *a, **k: None)(\n            "ruling_recorded",', [V6, '-k', 'm3_every']),
    ('M-3: denials are not audited', 'src/apexc/executor.py', 'self._audit_soft("release_denied", cls=str(actor), invoice_id=invoice_id, why=out)', 'pass', ['tests/test_v6.py', '-k', 'm3_every']),
    ('M-3: a refused approval is not audited', X, 'self._audit_soft("approval_refused", invoice_id=invoice_id, by=by, plan=plan, why=str(e))', 'pass', [V6, '-k', 'm3_every']),
    ('M-3: consumption is not audited', X, 'self._audit_soft("approvals_consumed", invoice_id=invoice_id, approvals=list(approval_ids))', 'pass', [V6, '-k', 'm3_every']),
    ('M-3: callback attested without who and when', 'src/apexc/fakes.py', 'attested_by=rec["attested_by"], ts=rec["ts"], state=rec["state"]', '', ['tests/test_v6.py', '-k', 'm3_callback']),
    ('M-4: the callback ledger can be overwritten', F, 'if rec["callback_id"] in self.callbacks:', 'if False:', [V6, '-k', 'm4_']),
    ('M-5: the tenant is not in the release key', P, '("enqueue", tenant, invoice_id, "release")', '("enqueue", invoice_id, "release")', [RL, '-k', 'release_key_is']),
    ('M-5: mismatched tenants are accepted', X, 'if erp.tenant != payments.tenant:', 'if False:', [V6, '-k', 'm5_']),
    ('M-6: the kill switch is not in the shared state', 'src/apexc/executor.py', '        return self.gate.engaged', '        return False', ['tests/test_v6.py', '-k', 'm6_kill_switch_caps'], 'kill_switch'),
    ('M-6: the daily counts are not in the shared state', X, '        return self.state.count_by_day', '        return {}', [V6, '-k', 'm6_kill_switch_caps']),
    ('M-6: the enqueue recheck uses the stale snapshot', X, 'fresh = self._fresh(invoice_id)  # TOCTOU: re-read at enqueue time, not the snapshot the gates used', 'fresh = case', [V6, '-k', 'm6_the_enqueue']),
    ('M-6: an unknown level is accepted at construction', X, 'if level not in LEVELS:', 'if False:', [V6, '-k', 'm6_an_unknown']),
    ('M-6: an unknown level releases', X, 'if self.level != "suggest":\n            return "shadow_level" if self.level == "shadow" else "level_unknown"', 'if self.level == "shadow":\n            return "shadow_level"', [V6, '-k', 'm6_an_unknown']),
    ('M-6: the kill switch leaves the queue alone', 'src/apexc/executor.py', 'out.append(key)', 'pass', ['tests/test_v6.py', '-k', 'm6_the_kill_switch_stops'], 'dequeued'),
    ('M-6: one person can lift the kill switch', X, '        if emp(d, user_a) == emp(d, user_b):\n            return False', '        if False:\n            return False', [V6, '-k', 'm6_the_kill_switch_stops']),
    ('M-6: approvals ignore the kill switch', X, '        if self._blocked():\n            raise ApprovalRefused(self._blocked())', '        if False:\n            raise ApprovalRefused(self._blocked())', [V6, '-k', 'm6_the_kill_switch_stops']),
    ('M-7: the approver cap is not atomic with the write', X, ['with self.state.lock:  # cap check and write are one step: two concurrent approvals cannot both pass at cap - 1', 'with self._cfg_lock:\n                return self._approve(invoice_id, by, plan)'], ['if True:  # no lock', 'if True:\n                return self._approve(invoice_id, by, plan)'], [V6, '-k', 'm7_the_per_person']),
    ('M-7: the daily total at tier human is not enforced', X, 'if single and used + int(inv["total_minor"]) > self.pol["limits"]["approver_daily_minor"][cur]:', 'if False:', [V6, '-k', 'm7_one_person']),
    ('M-7: hold pressure is not wired', X, '            self._pressure(case)', '            pass', [V6, '-k', 'm7_hold_pressure']),
    ('M-7: the roster is not checked', X, 'gap = roster_gap(self.directory, case["invoice"]["submitted_by"])', 'gap = []', [V6, '-k', 'm7_hold_pressure']),
    ('M-7: an incomplete queue entry counts as success', X, 'if seen and seen["status"] != "queued":', 'if False:', [V6, '-k', 'm7_duplicate_key']),
    ('M-7: a replayed delivery is not absorbed', F, 'self.replays_absorbed += 1', 'pass', [V6, '-k', 'm7_duplicate_key']),
    ('D: a queued earlier invoice can be rejected away', X, 'if h is None or h["status"] in NOT_UNDONE or queued:', 'if h is None:', [V6, AT, '-k', 'd1_ or m9_rejecting']),
    ('D: approvals are not bound to the config version', X, ['if any(r.get("config_version") != self.config_version() for r in recs):', 'if any(r.get("config_version") != self.config_version() for r in recs):'], ['if False:', 'if False:'], [V6, '-k', 'd2_']),
    ('D: one person can change the config', X, 'ok = all(u in self.directory and "finance_controller" in roles_of(d, u) for u in (user_a, user_b)) and emp(d, user_a) != emp(\n                d, user_b\n            )', 'ok = True', [V6, '-k', 'd2_']),
    ("N-2: approvals are not bound to the invoice lines", R, '"lines": hashlib.sha256(json.dumps(inv["lines"], sort_keys=True).encode()).hexdigest()[:16], ', "", [V6, "-k", "n2_"]),
    ("N-2: approvals are not bound to the invoice number", R, '"invoice_number": inv["invoice_number"], ', "", [V6, "-k", "n2_"]),
    ("N-4: a non-terminal handler answer is stored as a state", N, 'if not isinstance(out, str) or not (out in ("processed", "abstained") or out.startswith("rejected:")):', "if False:", [V6, "-k", "n4_"]),
    # ---- v7: the two fresh reviews of v6 (code-6, design-6)
    ('B1: README names a config key that does not exist', "README.md", "(`queue.min_queue_to_run_hours` in `config/policy.json`, a demo default)", "(`queue.run_cutoff_local` in `config/policy.json`, a demo default)", [V7, '-k', 'b1_every']),
    ('B1: gate_rules names a cutoff key that does not exist', "gate_rules.md", "There is no cutoff-time key in the config.", "Cutoff in `queue.run_cutoff_local`.", [V7, '-k', 'b1_every']),
    ('M1: a lifter may also be plan 1', X, 'steps.append((row["lifted_by"], "lift_hold"))', 'steps.append((row["lifted_by"], "approve_resolution"))', [V7, '-k', 'm1_hostile']),
    ('M1: lift_hold is not a distinct duty', PO, '    "approve_resolution",\n    "lift_hold",\n    "approve_release",\n    "clear_hard_block",', '    "approve_resolution",\n    "approve_release",\n    "clear_hard_block",', [V7, '-k', 'm1_']),
    ('M2: cases keep a stale directory snapshot', F, 'ctx["directory"] = copy_deep(self.directory)  # M2: never the stale snapshot stored with the case', 'pass', [V7, '-k', 'm2_a_revoked']),
    ('M2: change_config skips the constructor checks', X, "if why := config_problem(pol, directory):  # M2: the constructor's checks run again on every change", 'if False:', [V7, '-k', 'm2_change']),
    ('M2: the constructor accepts an unusable configuration', X, 'if why := config_problem(pol, directory):\n            raise ValueError(f"unusable configuration: {why}")', 'if False:\n            raise ValueError(f"unusable configuration: {why}")', [V8, '-k', 'm2_a_constructor']),
    ('M2: config holders are not updated together', 'src/apexc/executor.py', '        bind_cfg(h, self.cfg)\n', '        pass\n', ['tests/test_v7.py', '-k', 'm2_change']),
    ('M3: the audit backlog is not persisted', X, '"rows": rows, "audit_backlog": self.audit_backlog,', '"rows": rows, "audit_backlog": [],', [V7, '-k', 'm3_queued']),
    ('M3: the escalations are not persisted', X, '"escalations": self.escalations, "escalations_dropped"', '"escalations": [], "escalations_dropped"', [V7, '-k', 'm3_queued']),
    ('M3: the rate-limited submitters are not persisted', X, '"limited": sorted(self.limited),', '"limited": [],', [V7, '-k', 'm3_a_submitter']),
    ('M3: to_json reads the state without the lock', X, 'with self.lock:\n            store_rows, rechecks, applies = self.store.snapshot()', 'if True:\n            store_rows, rechecks, applies = self.store.snapshot()', [V7, '-k', 'm3_to_json']),
    ('M3: the submitter rate limit is only audited', X, 'self.state.limited.add(f"{self._person(sub)}|{day}")', 'pass', [V7, '-k', 'm3_a_submitter']),
    ('M3: the submitter rate limit is not checked at release', X, "if f\"{self._person(inv['submitted_by'])}|{self.clock.now()[:10]}\" in self.state.limited:", 'if False:', [V7, '-k', 'm3_a_submitter']),
    ('M3: the vendor-wide approval cap is only advice', X, 'if invoice_id not in vendor_invoices and len(vendor_invoices) >= self.pol["tiers"]["vendor_cap_per_window"]:', 'if False:', [V7, '-k', 'm3_the_vendor']),
    ('M4: PROMISES drops the asserted-id sentence', "PROMISES.md", 'In stage 1 the actor is an asserted id, not an authenticated person:', 'In stage 1 the actor is a named person:', [V7, '-k', 'm4_']),
    ('M4: README drops the code-and-tests-only status', "README.md", '**Stage 1 is code and tests only**', '**Stage 1 is a demo**', [V7, '-k', 'm4_']),
    ('M5: grouped digits are not joined', 'src/apexc/egress_text.py', '    plain = _digitish_count(t, policy.letter_run_min)\n', '    plain = 0\n', ['tests/test_v7.py', 'tests/test_v7b.py', '-k', 'm5_the_summary or m6_every']),
    ('M5: zero-width characters are not dropped from a summary', 'src/apexc/textnorm.py', '{"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}', '{"Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}', ['tests/test_v10.py', '-k', 'word_joiner'], '0xad'),
    ('M5: grouped IBANs pass', 'src/apexc/egress_text.py', 'if _IBAN_GROUPS.search(t) or account_like.search(t):', 'if False:', ['tests/test_v7.py', 'tests/test_v7b.py', '-k', 'm5_the_summary or m6_every']),
    ('M5: protected values are compared raw', 'src/apexc/egress_text.py', 'sq = squeeze(text, loose=True)', 'sq = text', ['tests/test_v7.py', 'tests/test_v7b.py', '-k', 'm5_the_summary or m6_every']),
    ('M5: the egress secrets are not squeezed', F, '            squeeze(x)\n            for o in self.erp.all_vendors()', '            x\n            for o in self.erp.all_vendors()', [V7, '-k', 'm5_egress']),
    ("M5: other vendors' accounts are not protected on egress", F, '            for o in self.erp.all_vendors()\n            for x in (', '            for o in [v]\n            for x in (', [V7, '-k', 'm5_egress']),
    ('M5: email templates are not slot-validated at the gate', F, 'if not callback_slots_ok(template_id, slots, self.pol):  # M5: every template, email included, takes exactly its validated slots', 'if template_id in self.pol["callback_templates"] and not callback_slots_ok(template_id, slots, self.pol):', [V7, '-k', 'm5_egress']),
    ('M5: the slot rule does not know email templates', R, ' or pol["email_templates"].get(template_id)', '', [V7, '-k', 'm5_egress']),
    ('M6: the attestation is audited before the ledger', 'src/apexc/fakes.py', 'self._log("callback_attested", callback_id=rec["callback_id"], attested_by=rec["attested_by"], ts=rec["ts"], state=rec["state"])\n            self.callbacks[rec["callback_id"]] = rec', 'self.callbacks[rec["callback_id"]] = rec\n            self._log("callback_attested", callback_id=rec["callback_id"], attested_by=rec["attested_by"], ts=rec["ts"], state=rec["state"])', ['tests/test_v8.py', '-k', 'minor_5'], '[True]'),
    ('M6: the attester need not be a named person', F, 'if self.erp.directory is not None and attested_by not in self.erp.directory:', 'if False:', [V7, '-k', 'm6_']),
    ('N: the receipt does not separate tenant and message id', N, 'hashlib.sha256(json.dumps([tenant, msg_id]).encode())', 'hashlib.sha256(f"{tenant}{msg_id}".encode())', [V7, '-k', 'n_the_receipt']),
    ('N: alerts and dead letters are unbounded', N, 'if len(bucket) < self.max_diagnostics:', 'if True:', [V7, '-k', 'n_alerts']),
    ('N: raw bodies are unbounded', N, 'too_big = len(raw) > self.max_raw_bytes', 'too_big = False', [V7, '-k', 'n_alerts']),
    ('N: only an AuditWriteError is queued', X, 'except Exception:  # noqa: BLE001 - after an action that cannot be undone, ANY audit failure queues the event; nothing may raise here', 'except AuditWriteError:', [V7, '-k', 'n_any_audit']),
    ('N: audit fields are not made JSON-safe', 'src/apexc/executor.py', 'f = _clip(json.loads(json.dumps(f, default=str)))', 'f = _clip(f)', ['tests/test_v7.py', '-k', 'n_any_audit']),
    ('N: the invoice number is unbounded', X, 'if len(inv["invoice_number"]) > self.pol["limits"]["invoice_number_max"]:', 'if False:', [V7, '-k', 'n_the_invoice']),
    # ---- v8: the two fresh reviews of v7 (code-7, design-7)
    ('B1: the callback is placed before it is audited', F, 'self.audit.append(self.erp.tenant, "callback_requested", vendor_id=vendor_id, topic=topic)\n            ticket = f"tk-{len(self.tickets) + 1}"\n            self.tickets[key] = {"ticket": ticket, "vendor_id": vendor_id, "topic": topic, "dialed": phone, "state": "pending"}\n            self.dials.append({"vendor_id": vendor_id, "dialed": phone, "topic": topic})', 'ticket = f"tk-{len(self.tickets) + 1}"\n            self.tickets[key] = {"ticket": ticket, "vendor_id": vendor_id, "topic": topic, "dialed": phone, "state": "pending"}\n            self.dials.append({"vendor_id": vendor_id, "dialed": phone, "topic": topic})\n            self.audit.append(self.erp.tenant, "callback_requested", vendor_id=vendor_id, topic=topic)', [V7B, '-k', 'b1_a_failed']),
    ('B1: the message leaves before it is audited', F, 'self.audit.append(self.erp.tenant, "egress", channel=channel, to=mask_dest(to), template=template_id)\n            self.outbox.append(msg)', 'self.outbox.append(msg)\n            self.audit.append(self.erp.tenant, "egress", channel=channel, to=mask_dest(to), template=template_id)', [V7B, '-k', 'b1_a_failed']),
    ('B1: the README drops the after-the-write audits', 'README.md', 'only a hold placement and the events after a payment already queued are audited AFTER the write', 'some steps', [V7B, '-k', 'b1_the_docs']),
    ('M1: release trusts a row of any shape', 'src/apexc/executor.py', 'if r is None or not validate_approval(r) or r["invoice_id"] != invoice_id:', 'if r is None or r["invoice_id"] != invoice_id:', ['tests/test_v7b.py', '-k', 'm1_a_corrupted or m1_the_approval']),
    ('M1: the vendor count trusts a row of any shape', X, 'if validate_approval(a) and a["vendor_id"] == vendor_id', 'if a["vendor_id"] == vendor_id', [V7B, '-k', 'm1_a_corrupted']),
    ('M1: the daily total trusts a row of any shape', X, 'if validate_approval(a) and a["currency"] == cur', 'if a["currency"] == cur', [V7B, '-k', 'm1_a_corrupted']),
    ('M1: record_approval stores a row of any shape', F, 'if not validate_approval(row):\n                raise ValueError("approval row has the wrong shape")', 'if False:\n                raise ValueError("approval row has the wrong shape")', [V7B, V8, '-k', 'm1_the_approval or minor_1_shape']),
    ('M1: the recorded binding is not recomputed at release', X, 'if diff:\n            return "denied:binding_mismatch:" + ",".join(diff)', 'if False:\n            return "denied:binding_mismatch:" + ",".join(diff)', [V7B, '-k', 'm1_forged']),
    ('M1: the bound set is compared by repr, not canonically', X, 'json.dumps(r["bound"], sort_keys=True)', 'repr(r["bound"])', [V7B, '-k', 'm1_bound_equality']),
    ('M1: rulings of any shape are stored', F, 'if not validate_ruling(row):\n            raise ValueError("ruling has the wrong shape")', 'if False:\n            raise ValueError("ruling has the wrong shape")', [V7B, '-k', 'm1_rulings']),
    ('M1: clears of any shape are stored', F, 'if not validate_clear(rec):', 'if False:', [V7B, '-k', 'm1_rulings']),
    ('M1: lift evidence of any shape is stored', F, 'if not validate_evidence(evidence):', 'if False:', [V7B, '-k', 'm1_rulings']),
    ('M2: lift evidence is stored by reference', F, 'evidence=copy_deep(evidence)', 'evidence=evidence', [V7B, '-k', 'm2_lift_evidence']),
    ('M2: hold rows are handed out by reference', F, 'return {r["reason"]: copy_deep(r) for r', 'return {r["reason"]: dict(r) for r', [V7B, '-k', 'm2_lift_evidence']),
    ('M3: the release rows are read without the store lock', R, 'with self._lock:\n            return {k: dict(r) for k, r in self.rows.items()}, self.rechecks, self.applies', 'if True:\n            return {k: dict(r) for k, r in self.rows.items()}, self.rechecks, self.applies', [V7B, '-k', 'm3_to_json_waits']),
    ('M3: to_json stringifies an unknown object', X, '"store_counters": [rechecks, applies]}, sort_keys=True)', '"store_counters": [rechecks, applies]}, sort_keys=True, default=str)', [V7B, '-k', 'm3_to_json_never']),
    ('M3: the store counters are not persisted', X, '"store_counters": [rechecks, applies]', '"store_counters": [0, 0]', [V7B, '-k', 'm3_to_json_never']),
    ('M3: a flush takes events out before writing them', X, 'kind, f = self.state.audit_backlog[0]', 'kind, f = self.state.audit_backlog.pop(0)', [V7B, '-k', 'm3_a_snapshot']),
    ('M3: escalations are not capped', X, 'if len(self.escalations) < MAX_ESCALATIONS:', 'if True:', [V7B, '-k', 'm3_escalations']),
    ('M4: ports built on the ERP do not follow a config change', X, 'for port in getattr(h, "ports", []):', 'for port in []:', [V7, V8, '-k', 'm2_change or ports_built_before']),
    ('M4: change_config does not take turns', X, "with self._cfg_lock:  # two concurrent changes take turns; neither loses the other's update", 'if True:', [V7B, '-k', 'm4_two_concurrent']),
    ('M4: the config version is not re-tested at the enqueue', X, 'if any(r.get("config_version") != self.config_version() for r in recs):\n                return False, "config_changed"', 'if False:\n                return False, "config_changed"', [V7B, '-k', 'm4_a_config_change']),
    ('M4: a changed dry-run default is ignored', 'src/apexc/executor.py', '(not self.pol["release"]["dry_run_default"]) if self._live is None else self._live', 'False if self._live is None else self._live', ['tests/test_v7b.py', '-k', 'm4_a_changed'], 'False is True'),
    ('M4: a vendor missing from the live table is read from a stale snapshot', F, 'if vid is not None:\n            ctx["vendor"] = copy_deep(self.vendors[vid])', 'if vid in self.vendors:\n            ctx["vendor"] = copy_deep(self.vendors[vid])', [V7B, '-k', 'm4_a_vendor']),
    ('M5: the vendor cap refuses the second plan of a counted invoice', X, 'if invoice_id not in vendor_invoices and len(vendor_invoices)', 'if len(vendor_invoices)', [V7B, '-k', 'm5_plan_1']),
    ('M5: a lift does not count for the lifter', X, 'if r.get("lifted_by") and r.get("lifted_at")', 'if False', [V7B, '-k', 'm5_plan_1']),
    ('M6: separators are not removed from a summary', 'src/apexc/egress_text.py', '    plain = _digitish_count(t, policy.letter_run_min)\n', '    plain = 99 if re.search(r"\\d{8,}", "".join(ch for ch in t if ch.isalnum())) else 0\n', ['tests/test_v7b.py', '-k', 'm6_every']),
    ('M6: a single letter between digit groups is not bridged', 'src/apexc/egress_text.py', '        elif ch in _DIGITISH:\n            strong += 1', '        elif False:\n            strong += 1', ['tests/test_v7b.py', 'tests/test_v9.py', '-k', 'm6_every or m1_latin']),
    ('M6: look-alike letters are not folded', 'src/apexc/textnorm.py', '.translate(_DIGITS).translate(_TABLE)', '.translate(_DIGITS)', ['tests/test_v7b.py', 'tests/test_v8.py', '-k', 'm6_every or m3_every_uppercase']),
    ('M6: combining marks are not dropped', 'src/apexc/textnorm.py', '{"Cc", "Cf", "Mn", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}', '{"Cc", "Cf", "Me", "Zl", "Zp", "Co", "Cs", "Cn"}', ['tests/test_v7b.py', '-k', 'm6_every']),
    ('M6: O/0 and I/l/1 are not folded for protected values', 'src/apexc/textnorm.py', 's = s.translate(_LOOSE)', 'pass', ['tests/test_v7b.py', '-k', 'm6_every']),
    ('M6: any eight digits count as a date', 'src/apexc/egress_text.py', 'date(y, m, d)', 'pass', ['tests/test_v7b.py', 'tests/test_v8.py', '-k', 'm6_every or m3_dates']),
    ('M6: a scope without protected values is accepted', T, 'if "protected" not in scope:', 'if False:', [V7B, '-k', 'm6_a_scope']),
    ("M6: the case's own invoice number is not set aside", 'src/apexc/egress_text.py', 'for a in allowed:', 'for a in ():', ['tests/test_v7b.py', '-k', 'm6_what_is_allowed']),
    ('M7: the egress cap is a lifetime cap', F, 'sent_today = sum(1 for m in self.outbox if m["day"] == day)', 'sent_today = len(self.outbox)', [V7B, '-k', 'm7_the_egress']),
    ('M7: a non-string slot raises instead of failing', R, 'type(v) is str and re.fullmatch', 're.fullmatch', [V7B, '-k', 'm7_slot_checks']),
    ('N: unknown ids grow the chain', 'src/apexc/executor.py', 'if not (\n                out == "denied:approval_not_usable" and actor == "-"\n            ):', 'if True:', ['tests/test_v7b.py', '-k', 'n_garbage']),
    ('N: the release intent is audited before the cheap checks', X, 'if self._blocked():\n            return "denied:" + self._blocked()\n        try:\n            case = self._fresh(invoice_id)', 'if self._blocked():\n            return "denied:" + self._blocked()\n        self.audit.append(self.erp.tenant, "release_intent", invoice_id=invoice_id)\n        try:\n            case = self._fresh(invoice_id)', [V7B, '-k', 'n_garbage']),
    ('N: a supervisor role loses lift_hold', PO, '"ap_supervisor": [\n      "approve_resolution",\n      "lift_hold"\n    ],', '"ap_supervisor": [\n      "approve_resolution"\n    ],', [V7B, '-k', 'n_every_role']),
    ('B1: the policy and directory views accept in-place edits', 'src/apexc/config_view.py', '__setitem__ = __delitem__ = update = pop = popitem = clear = setdefault = __ior__ = _refuse', '__ior__ = _refuse', ['tests/test_v8.py', '-k', 'b1_policy_and_directory_are_deeply'], 'DID NOT RAISE'),
    ('B1: nested lists of the config accept in-place edits', 'src/apexc/config_view.py', 'sort = reverse = __iadd__ = __imul__ = _refuse', 'pass', ['tests/test_v8.py', 'tests/test_v9.py', '-k', 'b1_policy_and_directory_are_deeply or sort_reverse'], 'DID NOT RAISE'),
    ("B1: freeze shares the caller's nested objects", 'src/apexc/config_view.py', 'dict.__init__(d, {k: _freeze(v, depth + 1, budget) for k, v in o.items()})', 'dict.__init__(d, o)', ['tests/test_v8.py', '-k', 'b1_frozen_views'], ': [1, {'),
    ('B1: the executor hands out a plain copy of the policy', 'src/apexc/executor.py', '"""Read-only (deep-frozen): the policy changes only through `change_config` (two controllers, chained, versioned)."""\n        return self.cfg.pol', '"""x"""\n        return thaw(self.cfg.pol)', ['tests/test_v8.py', '-k', 'b1_policy_and_directory_are_deeply'], 'DID NOT RAISE'),
    ('B1: the ERP keeps its own copy of the directory', 'src/apexc/fakes.py', 'return self.cfg.directory  # the ONE directory source', 'return dict(self.cfg.directory)  # the ONE directory source', ['tests/test_v8.py', '-k', 'b1_policy_and_directory_are_deeply'], 'DID NOT RAISE'),
    ('B1: the ports are not pointed at the shared holder', 'src/apexc/executor.py', '        bind_cfg(h, self.cfg)\n', '        pass\n', ['tests/test_v8.py', '-k', 'b1_every_port'], 'False'),
    ('M1: a second executor builds its own config holder', 'src/apexc/executor.py', '        self._cfg = erp.cfg\n', '        self._cfg = type(erp.cfg)(pol, directory)\n', ['tests/test_v8.py', '-k', 'm1_a_second'], '0> is <apexc.config.ConfigHolder object '),
    ('M2: the kill switch does not wait for a release in flight', 'src/apexc/stop_gate.py', 'drained = self._cond.wait_for(lambda: self._inflight - own <= 0, timeout=timeout)', 'drained = True', ['tests/test_v8.py', '-k', 'm2_a_release_past'], 'dequeued'),
    ('M2: one failing undo stops the sweep', 'src/apexc/executor.py', 'except Exception as e:  # noqa: BLE001 - per-item choke point: the rest are still undone', 'except ZeroDivisionError as e:', ['tests/test_v8.py', '-k', 'm2_one_failing'], 'k-bad'),
    ('M2: the egress gate ignores the kill switch', 'src/apexc/fakes.py', 'with self.cfg.effect():  # M5 (review 9): in flight until the message is audited and in the outbox', 'if True:', ['tests/test_v8.py', '-k', 'm2_ports_refuse'], 'DID NOT RAISE'),
    ('M2: the callout ignores the kill switch', 'src/apexc/fakes.py', 'with self.cfg.effect():  # M5 (review 9): in flight until the call is placed and audited; the kill switch waits for it', 'if True:', ['tests/test_v8.py', '-k', 'm2_ports_refuse'], 'DID NOT RAISE'),
    ('M2: the holder does not see a watching control state', 'src/apexc/config.py', 'return any(s.killed for s in states)', 'return False', ['tests/test_v9.py', '-k', 'm4_the_switch_is_seen'], 'another watched state'),
    ('M3: uppercase Cyrillic S, I, J and Y are not folded', 'src/apexc/_confusables.py', '    0x0405: "S",\n    0x0406: "I",\n    0x0408: "J",\n', '', ['tests/test_v8.py', '-k', 'm3_every_uppercase'], 'E           AssertionError: 0x405'),
    ('M3: any year is a date', 'src/apexc/egress_text.py', 'if not years[0] <= y <= years[1]:', 'if False:', ['tests/test_v8.py', '-k', 'm3_dates']),
    ('M3: only contiguous digits are refused', 'src/apexc/egress_text.py', '    plain = _digitish_count(t, policy.letter_run_min)\n', '    plain = 99 if re.search(r"\\d{8,}", "".join(ch for ch in t if ch.isalnum())) else 0\n', ['tests/test_v8.py', '-k', 'm3_fuzz']),
    ('M3: PO ids are not set aside', 'src/apexc/tools.py', 'allowed_patterns=[_PO_REF]', 'allowed_patterns=[]', ['tests/test_v8.py', '-k', 'm3_what_still_passes']),
    ('M4: a lift is written with no audit event', 'src/apexc/fakes.py', 'self._log("hold_lifted", invoice_id=invoice_id, reason=reason, by=by)', 'pass', ['tests/test_v8.py', 'tests/test_v9.py', '-k', 'm4_a_failed_audit_write_lifts or lift_without_a_clear'], 'hold_lifted'),
    ('M4: a clear row is written even when the lift did nothing', 'src/apexc/fakes.py', '                    return True\n        return False\n\n    def record_clear', '                    return True\n        if clear is not None:\n            self.clears.append(dict(clear))\n        return False\n\n    def record_clear', ['tests/test_v8.py', '-k', 'm4_a_lift_that_did_nothing'], 'E       AssertionError: assert 2 == 1'),
    ('M4: the clear is written before its audit', 'src/apexc/fakes.py', '            self._log(\n                "clear_recorded", invoice_id=rec["invoice_id"], type=rec["type"], by=rec["by"], clear_kind=rec["kind"]\n            )  # M4: audit BEFORE the write\n            self.clears.append({**rec, "ts": self._now()})', '            self.clears.append({**rec, "ts": self._now()})\n            self._log(\n                "clear_recorded", invoice_id=rec["invoice_id"], type=rec["type"], by=rec["by"], clear_kind=rec["kind"]\n            )', ['tests/test_v8.py', '-k', 'm4_record_clear'], 'invoice_id...'),
    ('M5: aging iterates the live ledger', 'src/apexc/executor.py', 'for inv_id, rows in self.erp.snapshot_holds().items():  # M5: a copy under the ERP lock; the flag is set through the ERP, once', 'for inv_id, rows in self.erp.holds.items():', ['tests/test_v8.py', '-k', 'm5_a_concurrent_hold'], 'assert ([])'),
    ('M5: the snapshot is taken without the ERP lock', 'src/apexc/fakes.py', '        with self._lock:\n            return {i: [copy_deep(r) for r in rows] for i, rows in self.holds.items()}', '        if True:\n            return {i: [copy_deep(r) for r in rows] for i, rows in self.holds.items()}', ['tests/test_v8.py', '-k', 'm5_a_concurrent_hold'], 'assert ([])'),
    ('design M1: get_po hands out the live ERP object', 'src/apexc/fakes.py', 'return copy_deep(self.erp.pos.get(po_id))  # design M1: a copy, never the live ERP object', 'return self.erp.pos.get(po_id)', ['tests/test_v8.py', '-k', 'design_m1'], 'po_id'),
    ('design M1: the master accessors hand out live vendors', 'src/apexc/fakes.py', '            return [copy_deep(v) for v in self.vendors.values()]  # copies: a reader never holds a handle on the live master', '            return list(self.vendors.values())', ['tests/test_v8.py', '-k', 'design_m1'], 'HACKED'),
    ('design M2: a refused attempt is not audited', 'src/apexc/fakes.py', 'port.audit.append_capped(port.erp.tenant, kind, cap, port.clock.now()[:10], **f)', 'pass', ['tests/test_v8.py', '-k', 'design_m2'], 'callback_de...'),
    ('design M2: the denied-attempt audit is uncapped', 'src/apexc/fakes.py', '                row = n_over <= 0', '                row = True', ['tests/test_v8.py', '-k', 'design_m2'], '12 == 3'),
    ('design M2: an audit outage changes the refusal', 'src/apexc/fakes.py', '    except Exception:  # noqa: BLE001 - the refusal itself is what matters; the drop is COUNTED (Audit.dropped), not hidden', '    except ZeroDivisionError:', ['tests/test_v10.py', '-k', 'm6_a_lost'], 'ap_clerk may not write request_vendor_confirmation'),
    ('design M3: the bound set is not compared with the ledgers', 'src/apexc/fakes.py', 'if binding_fields(self.read_case(inv_id), self.pol, cleared) != row["bound"]:', 'if False:', ['tests/test_v8.py', '-k', 'minor_1'], 'DID NOT RAISE'),
    ('design M4: the docs name a studio-root path', 'README.md', 'They are open asks in `schema-asks.md` in this folder.', 'They are open asks in `eg' + 'm' + chr(92) + 'apexc' + chr(92) + 'schema-asks.md`.', ['tests/test_v8.py', '-k', 'docs_do_not_point'], 'README.md'),
    ('design M5: the stage-2 I/O obligation is missing from the spec', 'spec_stage2.md', 'The config lock is never held across I/O.', 'The config lock is a detail.', ['tests/test_v8.py', '-k', 'design_m5'], 'never held across'),
    ('design m4: one vendor can use the whole egress cap', 'src/apexc/fakes.py', '>= self.pol["limits"]["egress_per_vendor_per_day"]', '>= 10**9', ['tests/test_v8.py', '-k', 'design_m4'], 'DID NOT RAISE'),
    ('minor 1: lifting and approving share an identity', 'config/policy.json', '        "lift_hold",\n        "record_clear"\n      ]', '        "lift_hold",\n        "record_clear",\n        "record_approval"\n      ]', ['tests/test_v8.py', '-k', 'minor_7'], 'eError: approval row has the wrong shape'),
    ('minor 2: a crashing recheck strands a row and a reservation', 'src/apexc/executor.py', 'except Exception as e:  # noqa: BLE001 - minor 2: a recheck that crashes applied nothing: deny it, strand no row and no reservation', 'except ZeroDivisionError as e:', ['tests/test_v8.py', '-k', 'minor_2'], '({} == {}'),
    ('minor 3: a second release double-counts a reservation', 'src/apexc/executor.py', 'if self.live and key not in self.state.reservations:', 'if self.live:', ['tests/test_v8.py', '-k', 'minor_3'], '(2 == 1)'),
    ('minor 5: a key replays a different request', 'src/apexc/fakes.py', 'if (t["vendor_id"], t["topic"]) != (vendor_id, topic):', 'if False:', ['tests/test_v8.py', '-k', 'minor_5'], 'DID NOT RAISE'),
    ('minor 6: a message in process is processed again', 'src/apexc/intake.py', 'if row["state"] == "processing":', 'if False:', ['tests/test_v8.py', '-k', 'minor_6'], 'processed'),
    ('minor: release attempts on one invoice are uncapped', 'src/apexc/executor.py', 'if n_att > self.pol["limits"]["release_attempts_per_invoice_per_day"]:', 'if False:', ['tests/test_v8.py', '-k', 'minor_flood'], 'attempt_limit'),
    ('r9 B1: set-aside tokens are uncapped', 'src/apexc/egress_text.py', 't.count(_MARK) > policy.max_exempt_tokens', 'False', ['tests/test_v10.py', '-k', 'each_layer'], 'seven small tokens'),
    ('r9 B1: side-by-side set-aside tokens pass', 'src/apexc/egress_text.py', 'or _MARK_RUN.search(t)', '', ['tests/test_v9.py', '-k', 'b1_token_floods'], 'PO-1234 PO-5678'),
    ('r9 B1: amounts need no currency', 'src/apexc/egress_text.py', '(anchored if policy.amounts_need_currency else any_amount)', 'any_amount', ['tests/test_v10.py', '-k', 'each_layer'], 'Remit 1234.56 and 89.00'),
    ('r9 M1: digit-like letters are not counted', 'src/apexc/egress_text.py', '        elif ch in _DIGITISH:\n            strong += 1', '        elif False:\n            strong += 1', ['tests/test_v9.py', '-k', 'm1_latin'], '8 O 1 l 5 S 7 B 3 2 Z'),
    ('r9 M1: S B Z G Q are not mapped for protected values', 'src/apexc/textnorm.py', '_LOOSE = str.maketrans("OILSBZGQ", "01158269")', '_LOOSE = str.maketrans("OIL", "011")', ['tests/test_v9.py', '-k', 'm1_latin'], 'pay SBZGS now'),
    ('r9 M2: a protected number is not found through junk', 'src/apexc/egress_text.py', 'any(kd in s for s in sq_digits)', 'False', ['tests/test_v9.py', '-k', 'm2_junk'], 'pay 123 abc 4567'),
    ('r9 M2: a short protected value is skipped silently', 'src/apexc/egress_text.py', '        else:\n            words.append(fv)', '        else:\n            pass', ['tests/test_v9.py', '-k', 'm2_junk'], 'pay ab now'),
    ('r9 M2: a scope with a short protected value passes', 'src/apexc/tools.py', 'return "scope_protected_invalid"', 'return None', ['tests/test_v9.py', '-k', 'm2_junk'], 'scope_protected_invalid'),
    ('r9 M3: an allowed value is replaced anywhere', 'src/apexc/egress_text.py', 'r"(?<![A-Za-z0-9])" + re.escape(fa) + r"(?![A-Za-z0-9])"', 're.escape(fa)', ['tests/test_v9.py', '-k', 'm3_the_allowed'], 'xINV-26-04829999'),
    ('r9 M3: an empty allowed value is injected everywhere', 'src/apexc/egress_text.py', '        if fa:', '        if True:', ['tests/test_v9.py', '-k', 'm3_the_allowed'], 'folds to nothing'),
    ('r9 M4: an executor builds its own control state', 'src/apexc/executor.py', 'state = bound or ControlState()', 'state = ControlState()', ['tests/test_v9.py', '-k', 'm4_a_default'], 'ControlState'),
    ('r9 M4: another control state is accepted without rebind', 'src/apexc/executor.py', 'elif bound is not None and state is not bound and not rebind:', 'elif False:', ['tests/test_v9.py', '-k', 'm4_a_default'], 'DID NOT RAISE'),
    ('r9 M4: the blocked check ignores the other states', 'src/apexc/executor.py', 'return "kill_switch" if (self.state.killed or self.cfg.blocked()) else None', 'return "kill_switch" if self.state.killed else None', ['tests/test_v9.py', '-k', 'm4_the_switch_is_seen'], 'another watched state'),
    ('r9 M5: a message is not counted in flight', 'src/apexc/fakes.py', 'with self.cfg.effect():  # M5 (review 9): in flight until the message is audited and in the outbox', 'if True:', ['tests/test_v9.py', '-k', 'm5_the_kill_switch_waits'], 'is False'),
    ('r9 M5: a release is not counted in flight', 'src/apexc/executor.py', 'with self.cfg.effect():  # M5: counted in flight until the queue time is recorded; the kill switch waits for it', 'if True:', ['tests/test_v9.py', '-k', 'm5_a_release_in_flight'], 'dequeued'),
    ('r9 M6: release denials are uncapped', 'src/apexc/executor.py', 'if kind in CAPPED_KINDS:', 'if False:', ['tests/test_v9.py', '-k', 'm6_a_flood'], '<= 200'),
    ('r9 M6: audit text is not bounded', 'src/apexc/executor.py', 'f = _clip(json.loads(json.dumps(f, default=str)))', 'f = json.loads(json.dumps(f, default=str))', ['tests/test_v9.py', '-k', 'm6_a_flood'], 'unbounded text'),
    ('r9 M6: a denied kill switch call leaves no row', 'src/apexc/executor.py', 'self._audit_soft("kill_switch_denied", by=identity)', 'pass', ['tests/test_v9.py', '-k', 'm6_a_flood'], 'kill_switch_denied'),
    ('r9 M6: a denied compensate call leaves no row', 'src/apexc/executor.py', 'self._audit_soft("compensate_denied", by=requested_by)', 'pass', ['tests/test_v9.py', '-k', 'm6_a_flood'], 'compensate_denied'),
    ('r9 M6: a denied ledger write leaves no row', 'src/apexc/fakes.py', '            if self.audit is not None:  # M6 (review 9)', '            if False:  # M6 (review 9)', ['tests/test_v9.py', '-k', 'm6_a_flood'], 'erp_denied'),
    ('r9 M6: a denied attestation leaves no row', 'src/apexc/fakes.py', 'self._deny("attest_identity", e, identity)', 'raise', ['tests/test_v9.py', '-k', 'm6_a_denied_attestation'], 'False'),
    ('r9 m1: a frozen value can be re-initialised', 'src/apexc/config_view.py', 'if getattr(self, "_sealed", False):', 'if False:', ['tests/test_v9.py', '-k', 'm1_the_config_view'], 'DID NOT RAISE'),
    ('r9 m2: a call naming no approval is counted', 'src/apexc/executor.py', 'if not recs or len(set(approval_ids)) < len(self.plans_for(tier, hard)):', 'if False:', ['tests/test_v9.py', '-k', 'm2_release_with_no_approval'], 'internal_error'),
    ('r9 m3: reject runs without the config lock', 'src/apexc/executor.py', 'with self._cfg_lock:  # m3: the not-queued check and the rejection are one step against a release', 'if True:  # m3', ['tests/test_v9.py', '-k', 'm3_reject'], 'not True'),
    ('r9 m5: reconcile trusts a partial queue entry', 'src/apexc/rules.py', 'if found.get("status") != "queued":', 'if False:', ['tests/test_v9.py', '-k', 'm5_reconcile'], 'pending'),
    ('r9 m6: the root of trust changes while the kill switch is on', 'src/apexc/executor.py', 'if self._blocked():  # m6: the root of trust is frozen while the kill switch is on', 'if False:', ['tests/test_v9.py', '-k', 'm6_the_root'], 'not True'),
    ('r9 m7: a second audit chain is accepted', 'src/apexc/executor.py', 'if erp.audit is not None and erp.audit is not audit:', 'if False:', ['tests/test_v9.py', '-k', 'm7_a_second'], 'DID NOT RAISE'),
    ('r9: consume is not its own operation', 'config/policy.json', '"record_approval",\n        "consume_approval"', '"record_approval"', ['tests/test_v9.py', '-k', 'the_consume_right'], 'assert'),
    ('r9 parity: a core copy drifts', 'src/apexc/textnorm.py', 'FILLERS = frozenset(', 'FILLERS = set(', ['tests/test_v9.py', '-k', 'the_core_copies_match'], 'src/apexc/textnorm.py'),
    ('r9 docs: the stage 2 spec drops the fail-closed kill switch', 'spec_stage2.md', 'fails closed', 'stays quiet', ['tests/test_v9.py', '-k', 's8_and_s16'], 'fails closed'),
    ('r9 docs: the repo points at a studio path', 'README.md', '`CORE_COPIES.md`', '`eg' + 'm' + chr(92) + 'core.md`', ['tests/test_v9.py', '-k', 'never_points'], 'eg' + 'm' + chr(92)),
    ('r10 B1: a port can be rebound by assignment', 'src/apexc/fakes.py', '    _c.cfg = property(lambda self: self._cfg)', "    _c.cfg = property(lambda self: self._cfg, lambda self, v: object.__setattr__(self, '_cfg', v))", ['tests/test_v10.py', '-k', 'b1_no_port'], 'DID NOT RAISE'),
    ('r10 B1: the executor cfg can be assigned', 'src/apexc/executor.py', '        return self._cfg  # read-only: set once by the constructor', '        return self._cfg\n\n    @cfg.setter\n    def cfg(self, v):\n        bind_cfg(self, v)', ['tests/test_v10.py', '-k', 'b1_no_port'], 'DID NOT RAISE'),
    ('r10 M1: a restart drops the engaged switch', 'src/apexc/executor.py', 'if carried and not state.killed:', 'if False:', ['tests/test_v10.py', '-k', 'm1_rebinding'], 'kill_switch'),
    ('r10 M1: the killed flag can be assigned off', 'src/apexc/executor.py', 'if not on and self.gate.engaged:', 'if False:', ['tests/test_v10.py', '-k', 'm1_rebinding or switch_is_seen'], 'DID NOT RAISE'),
    ('r10 M1: the rebound is not audited', 'src/apexc/executor.py', 'self._audit_soft("control_state_rebound", carried_kill=carried, by="system")', 'pass', ['tests/test_v10.py', '-k', 'm1_rebinding'], 'StopIteration'),
    ('r10 M2: payments denials are not audited', 'src/apexc/executor.py', 'h.deny_sink = lambda kind, cls="", **f: self._audit_soft(\n                    kind, cls=cls, **f\n                )', 'h.deny_sink = None; _unused = lambda kind, cls="", **f: self._audit_soft(\n                    kind, cls=cls, **f\n                )', ['tests/test_v10.py', '-k', 'm2_denied_payments'], '== 6'),
    ('r10 M2: dequeue of an unknown key raises', 'src/apexc/fakes.py', 'return "unknown"  # not a KeyError: an unknown key is a typed answer', 'raise KeyError(key)', ['tests/test_v10.py', '-k', 'm2_dequeue_of_an_unknown'], 'no-such-key'),
    ('r10 M3: denial caps share one class', 'src/apexc/fakes.py', 'k = (tenant, kind, str(cls)[:40], bucket)', 'k = (tenant, kind, "", bucket)', ['tests/test_v10.py', '-k', 'm2_denied_payments'], '== 1'),
    ('r10 M3: the suppression marker carries no count', 'src/apexc/fakes.py', 'suppressed=mark)', 'suppressed=0)', ['tests/test_v10.py', '-k', 'm2_denied_payments'], "'kind': 'audit_suppressed'"),
    ('r10 M4: a base-class edit is not detected', 'src/apexc/config.py', 'return digest(v.pol, v.directory) != self._digest', 'return False', ['tests/test_v10.py', '-k', 'm4_a_privilege or m4_a_policy'], 'assert False'),
    ('r10 M4: the executor does not fail closed on a tampered config', 'src/apexc/executor.py', 'if self.cfg.tampered():  # review 10 M4', 'if False:  # review 10 M4', ['tests/test_v10.py', '-k', 'm4_a_privilege or m4_a_policy'], 'assert not True'),
    ('r10 M4: the effect barrier ignores a tampered config', 'src/apexc/config.py', '        self.check()\n        with self.lock:\n            states = self._states\n        with ExitStack() as stack:', '        with self.lock:\n            states = self._states\n        with ExitStack() as stack:', ['tests/test_v10.py', '-k', 'm4_a_privilege'], 'outbound effect'),
    ('r10 M4: the payments port ignores a tampered config', 'src/apexc/fakes.py', 'self.cfg.check()  # a tampered configuration fails closed here too', 'pass', ['tests/test_v10.py', '-k', 'm4_a_privilege'], 'may not write enqueue'),
    ('r10 M4: a legitimate change leaves a stale digest', 'src/apexc/config.py', '            self._digest = digest(v.pol, v.directory)', '            pass', ['tests/test_v10.py', '-k', 'm4_a_legitimate'], 'assert False'),
    ('r10 M5: a port on another policy gets a private holder', 'src/apexc/fakes.py', '        if pol != erp.cfg.pol:', '        if False:', ['tests/test_v10.py', '-k', 'm5_a_port'], 'DID NOT RAISE'),
    ('r10 m3: the same id twice is two plans', 'src/apexc/executor.py', 'if not recs or len(set(approval_ids)) < len(self.plans_for(tier, hard)):', 'if not recs:', ['tests/test_v10.py', '-k', 'm3_an_incomplete'], 'plans_missing'),
    ('r10 m3: the denial code is an oracle', 'src/apexc/executor.py', 'if r is None or not validate_approval(r) or r["invoice_id"] != invoice_id:\n                return "denied:approval_not_usable"', 'if r is None:\n                return "denied:approval_unknown"\n            if not validate_approval(r) or r["invoice_id"] != invoice_id:\n                return "denied:approval_not_usable"', ['tests/test_v10.py', '-k', 'm3_an_incomplete'], 'denied:approval_not_usabl'),
    ('r10 m4: lift ignores the config lock', 'src/apexc/executor.py', '        with self._cfg_lock:\n            try:\n                with self.cfg.effect():\n                    return self._lift(', '        if True:\n            try:\n                with self.cfg.effect():\n                    return self._lift(', ['tests/test_v10.py', '-k', 'config_change_waits and lift'], 'middle of a lift'),
    ('r10 m4: clear ignores the config lock', 'src/apexc/executor.py', '        with self._cfg_lock:\n            try:\n                with self.cfg.effect():\n                    return self._clear(', '        if True:\n            try:\n                with self.cfg.effect():\n                    return self._clear(', ['tests/test_v10.py', '-k', 'config_change_waits and clear'], 'middle of a clear'),
    ('r10 m5: the kill sweep ignores payments rows', 'src/apexc/executor.py', 'keys += [k for k in self.payments.queued_keys() if k not in keys]', 'pass', ['tests/test_v10.py', '-k', 'm5_the_kill_sweep'], 'k-pre-restart'),
    ('r10 m6: a lost denial row is not counted', 'src/apexc/fakes.py', '            port.audit.count_drop()', '            pass', ['tests/test_v10.py', '-k', 'm6_a_lost'], '== 1'),
    ('r11 N1: the undo depends on the tamper digest', 'src/apexc/fakes.py', '            pol = self.cfg.lkg_pol\n        else:', '            self.cfg.check()\n            pol = self.pol\n        else:', ['tests/test_v11.py', '-k', 'n1_the_kill or n1_compensate'], 'the sweep must dequeue on a tampered'),
    ('r11 N1: the kill switch is authorised against the live policy', 'src/apexc/executor.py', 'authorize_op(identity, "kill_switch", self._safe_pol)', 'authorize_op(identity, "kill_switch", self.pol)', ['tests/test_v11.py', '-k', 'n1_a_tampered'], 'DID NOT RAISE'),
    ('r11 N2: no ceiling per kind and day', 'src/apexc/fakes.py', 'if k not in self._capped and self._kind_rows.get(kk, 0) >= KIND_CEILING_FACTOR * cap:', 'if False:', ['tests/test_v11.py', '-k', 'n2_varying'], 'kind ceiling exceeded'),
    ("r11 N2: a refusal is charged to another invoice's author", 'src/apexc/executor.py', 'if isinstance(a, str) and a in self.erp.approvals and self.erp.approvals[a].get("invoice_id") == invoice_id', 'if isinstance(a, str) and a in self.erp.approvals', ['tests/test_v11.py', '-k', 'n2_a_release'], 'charged to another invoice'),
    ('r11 race: the old state is dropped before the new one is watched', 'src/apexc/executor.py', '            self.cfg.watch(self.state)  # the ports ask the holder whether any watching state has the kill switch on\n            if bound is not None and bound is not state:\n                self.cfg.unwatch(bound)', '            if bound is not None and bound is not state:\n                self.cfg.unwatch(bound)\n            self.cfg.watch(self.state)  # the ports ask the holder whether any watching state has the kill switch on', ['tests/test_v11.py', '-k', 'race_a_rebind'], 'dropped before the new one'),
    ('r11 m-b: the audit-chain conflict is not checked first', 'src/apexc/executor.py', '        if erp.audit is not None and erp.audit is not audit:', '        if False:', ['tests/test_v11.py', '-k', 'm_b_a_constructor'], 'DID NOT RAISE'),
    ('r11 m5: the drop counter is not locked', 'src/apexc/fakes.py', '        with self._meta:\n            self.dropped += 1', '        if True:\n            self.dropped += 1', ['tests/test_v11.py', '-k', 'm5_the_drop'], 'count_drop must take the audit lock'),
    ('r11 m4: the watch list is changed without the config lock', 'src/apexc/config.py', '        with self.lock:\n            if all(s is not state for s in self._states):', '        if True:\n            if all(s is not state for s in self._states):', ['tests/test_v11.py', '-k', 'm4_the_watch'], 'watch must take the config lock'),
    ('r11 M-6: a shadow level lifts a hold', 'src/apexc/executor.py', '    def _lift(self, invoice_id: str, reason: str, by: str, action: str, evidence: dict | None = None) -> bool:\n        if self._blocked():', '    def _lift(self, invoice_id: str, reason: str, by: str, action: str, evidence: dict | None = None) -> bool:\n        if False:', ['tests/test_v11.py', '-k', 'm6_a_shadow'], 'assert True is False'),
    ('r11 m-4: a lift in flight is not counted by the kill switch', 'src/apexc/executor.py', '                with self.cfg.effect():\n                    return self._lift(', '                if True:\n                    return self._lift(', ['tests/test_v11.py', '-k', 'm4_the_kill_switch_waits'], 'only after the lift'),
    ('r11 identity: an op the identity lacks is allowed', 'src/apexc/rules.py', '    if not identity_can(identity, op, pol, kind):\n        raise PermissionError(f"{identity} may not {kind} {op}")', '    if False:\n        raise PermissionError(f"{identity} may not {kind} {op}")', ['tests/test_v11.py', '-k', 'each_identity'], 'DID NOT RAISE'),
    ('r11 N1: the kill switch waits for the config lock', 'src/apexc/config.py', '        return self._lkg  # one attribute read, no lock: the kill switch must never wait for a release or a config change', '        with self.lock:\n            return self._lkg', ['tests/test_v11.py', '-k', 'n1_the_kill_switch_does_not_wait'], 'must not wait for a release'),
]  # fmt: skip


def run(args: list[str], cwd: Path) -> tuple[int, str]:
    env = dict(
        os.environ,
        PYTHONPATH=str(cwd / "src")
        + os.pathsep
        + str(cwd / "demo_only" / "data")
        + os.pathsep
        + str(cwd / "demo_only")
        + os.pathsep
        + str(cwd / "tests"),
    )
    r = subprocess.run(
        [str(PY), "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *args], cwd=cwd, env=env, capture_output=True, text=True
    )
    first = next((ln.strip() for ln in r.stdout.splitlines() if ln.startswith("E ")), "")
    failed = next((ln.split(" - ")[0].strip() for ln in r.stdout.splitlines() if ln.startswith("FAILED ")), "")
    files = [a for a in args if a.endswith(".py")]
    if r.returncode == 1 and not (
        failed and (not files or any(failed.removeprefix("FAILED ").replace("\\", "/").startswith(f) for f in files))
    ):
        return -1, "exit 1 but no failing test in the targeted files (a collection or internal error is not a kill)"
    return r.returncode, (failed.removeprefix("FAILED ") + " | " if failed else "") + first[:110]


def fresh_copy() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    shutil.copytree(SRC, TMP, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", ".ruff_cache"))


INTERNAL = re.compile(
    r"assert " + chr(92) + "(*['\"]denied:internal_error['\"] =="
)  # the RESULT was an internal_error denial (not a test that expects one): counted as a crash kill
PINS = SRC / "mutant_kills.json"
LABEL = {
    Verdict.KILLED: "KILLED",
    Verdict.CRASH: "KILLED-CRASH",
    Verdict.WRONG_REASON: "KILLED-WRONG-REASON",
    Verdict.OTHER_TEST: "KILLED-OTHER-TEST",
    Verdict.SURVIVED: "SURVIVED",
    Verdict.NO_TESTS: "NO TESTS RAN",
    Verdict.ERROR: "ERROR",
}


def judge(rc: int, why: str, expect: str | None = None, pinned: str | None = None) -> str:
    """The label of one mutant run, from the core judge (`mutation_judge`, a copy of `hadavin_sdk.testing.mutation`): KILLED only for an
    assertion; any other exception is a crash kill. `why` is "<failing test id> | <first line>" as `run` prints it."""
    test_id, _, first = why.partition(" | ")
    return LABEL[judge_core(rc, test_id, first, expect=expect, pinned=pinned, crash_markers=[INTERNAL])]


if __name__ == "__main__":
    record = "--record" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]  # optional substrings: run only the mutants whose name contains one of them
    pins = json.loads(PINS.read_text(encoding="utf-8")) if PINS.exists() else {}
    fresh_copy()
    bad = [str(a) for a in {tuple(m[4]) for m in M if not only or any(o in m[0] for o in only)} if run(list(a), TMP)[0] != 0]
    if bad:
        sys.exit(f"unmutated targets fail: {bad}")
    res, seen_ids = [], {}
    for m in M:
        name, f, old, new, args = m[:5]
        expect = m[5] if len(m) > 5 else None
        if only and not any(o in name for o in only):
            continue
        fresh_copy()
        p = TMP / f
        t = p.read_text(encoding="utf-8")
        olds, news = (old, new) if isinstance(old, list) else ([old], [new])
        if len(olds) != len(news) or any(o not in t for o in olds):
            res.append((name, "SNIPPET NOT FOUND", ""))
            continue
        for o, n in zip(olds, news, strict=True):  # several places at once: a defence in two places is reverted in both
            t = t.replace(o, n)  # every occurrence, not only the first
        p.write_text(t, encoding="utf-8", newline="\n")
        rc, why = run(args, TMP)
        label = judge(rc, why, expect, None if record else pins.get(name))
        if label.startswith("KILLED") and not record and name not in pins:
            label = "KILLED-UNPINNED"
        if rc == 1:
            seen_ids[name] = why.split(" | ", 1)[0]
        res.append((name, label, why))
    for r in res:
        print(r)
    shutil.rmtree(TMP, ignore_errors=True)
    if record and not only:
        PINS.write_text(json.dumps(dict(sorted(seen_ids.items())), indent=1) + "\n", encoding="utf-8")
        print(f"pinned {len(seen_ids)} kills in {PINS.name}")
    good = ("KILLED", "KILLED-CRASH")
    crashes = sum(1 for r in res if r[1] == "KILLED-CRASH")
    print(f"{sum(1 for r in res if r[1] in good)} of {len(res)} killed for the intended reason")
    print(f"of which {crashes} killed by a crash or an internal_error denial rather than a plain assertion")
    print(f"not killed, or killed for another reason or unpinned: {[r[0] + ' = ' + r[1] for r in res if r[1] not in good]}")
    sys.exit(0 if all(r[1] in good for r in res) else 1)
