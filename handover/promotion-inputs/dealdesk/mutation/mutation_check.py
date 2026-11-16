"""Stage-1 mutation check. Copies the demo to a temp dir, breaks ONE thing (exact string replacement, applied exactly once), runs the DEFAULT tests, and
requires a failure. Before any mutant it runs the UNMUTATED copy and asserts it passes (baseline), then asserts that the mutated copy is the code under
test. Output per mutant: name | rules | CAUGHT/SURVIVED | up to 5 failing tests (not only the first).

    uv run --group test python mutation/mutation_check.py [--apply-only] > mutation/RESULTS.txt

The header carries a hash of src/, config/ and tests/ (minus the doc-consistency test): tests/test_doc_consistency.py refuses a RESULTS.txt that does not
match the current tree. The default run never opens the held-out split; the very slow checks (the 1000-message burst and the file-independence copy run)
are deselected here because they test volume and file presence, not logic; the 10 and 100 bursts stay in."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GR, DR, DK, EX, IB, ST, ID, GU, TN, CN, LC, HD, PU = (
    "src/dealdesk/gate_rules.py",
    "src/dealdesk/desk_rules.py",
    "src/dealdesk/desk.py",
    "src/dealdesk/executor.py",
    "src/dealdesk/inbox.py",
    "src/dealdesk/store.py",
    "src/dealdesk/identities.py",
    "src/dealdesk/guards.py",
    "src/dealdesk/textnorm.py",
    "src/dealdesk/canon.py",
    "src/dealdesk/lockcheck.py",
    "src/dealdesk/handler.py",
    "src/dealdesk/purposes.py",
)
MX = "config/approval_matrix.json"
RULES_IMPLEMENTED = [
    "001",
    "003",
    "005",
    "006",
    "007",
    "002",
    "004",
    "010",
    "011",
    "012",
    "013",
    "014",
    "015",
    "016",
    "017",
    "018",
    "020",
    "021",
    "022",
    "023",
    "024",
    "030",
    "031",
    "040",
    "050",
    "060",
    "070",
    "080",
    "081",
    "082",
    "083",
    "084",
    "085",
    "086",
    "087",
    "088",
    "089",
    "090",
    "091",
    "092",
    "093",
    "094",
    "095",
    "096",
]

# (name, file, old, new, rule ids). `old` must occur EXACTLY once in the file.
NL = chr(10)
S1 = NL.join(
    [
        '"s": {',
        '        "zero": {},',
        '        "d0": {',
        '          "commercial": "sales_manager"',
        "        },",
        '        "d1": {',
        '          "commercial": "sales_manager"',
    ]
)
S2 = S1[: -len('sales_manager"')] + 'regional_vp"'
MUTS = [
    (
        "money: discount rounds up",
        GR,
        'list_total * terms["discount_bps"] // 10000',
        '-(-list_total * terms["discount_bps"] // 10000)',
        ["010"],
    ),
    ("band: s uses <=", GR, '"s" if list_total < b1', '"s" if list_total <= b1', ["010"]),
    ("band: m uses <=", GR, '"m" if list_total < b2', '"m" if list_total <= b2', ["010"]),
    ("band: l uses <=", GR, '"l" if list_total < b3', '"l" if list_total <= b3', ["010"]),
    ("band: discount edge < instead of <=", GR, 'if bps <= b["max_bps"]:', 'if bps < b["max_bps"]:', ["010"]),
    (
        "margin: floor > instead of >=",
        GR,
        "(net - cogs) * 10000 < floor_bps * net:",
        "(net - cogs) * 10000 <= floor_bps * net:",
        ["012"],
    ),
    (
        "margin: thin boundary <=",
        GR,
        "(net - cogs) * 10000 < (floor_bps + thin_bps) * net",
        "(net - cogs) * 10000 <= (floor_bps + thin_bps) * net",
        ["012"],
    ),
    ("margin: HZ-1 block in code removed", GR, 'if zone == "below_floor":', "if False:", ["012"]),
    ("cap: tier cap >= instead of >", GR, 'terms["discount_bps"] > cap else []', 'terms["discount_bps"] >= cap else []', ["011"]),
    ("downsell: not strict", GR, 'net * 10000 < int(deal["arr_minor"])', 'net * 10000 <= int(deal["arr_minor"])', ["017"]),
    (
        "term: lane merge keeps the lower role",
        GR,
        "ranks.index(role) > ranks.index(need[lane])",
        "ranks.index(role) < ranks.index(need[lane])",
        ["020", "013", "014", "015", "016"],
    ),
    ("stacking: > instead of >=", GR, '>= m["stacking"]["finance_cfo_at"]', '> m["stacking"]["finance_cfo_at"]', ["018"]),
    (
        "stacking: clause cells do not count",
        GR,
        'sum(1 for _d, cell in others if "finance" in cell)',
        'sum(1 for _d, cell in others if "finance" in cell and _d != "clause")',
        ["018", "090"],
    ),
    (
        "clause: blocked clause reports the wrong rule",
        GR,
        'LANE_RULE.get(dim, "R-DEALDESK-090")',
        'LANE_RULE.get(dim, "R-DEALDESK-010")',
        ["090"],
    ),
    ("window: 72h exclusive", GR, "<= ttl_hours * 3600", "< ttl_hours * 3600", ["023"]),
    (
        "window: negative delta accepted",
        GR,
        "return 0 <= parse_ts(receipt_ts) - parse_ts(request_ts)",
        "return parse_ts(receipt_ts) - parse_ts(request_ts)",
        ["023"],
    ),
    ("chain: window exclusive", GR, "<= chain_window_hours * 3600", "< chain_window_hours * 3600", ["023"]),
    ("cooldown: 72h exclusive", GR, "<= cooldown_hours * 3600", "< cooldown_hours * 3600", ["024"]),
    (
        "price: rounds toward less discount",
        GR,
        "-(-(list_seat - price_seat) * 10000 // list_seat)",
        "(list_seat - price_seat) * 10000 // list_seat",
        ["005"],
    ),
    (
        "inputs: bool accepted as int",
        GR,
        "if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:",
        "if not isinstance(v, int) or not lo <= v <= hi:",
        ["001"],
    ),
    (
        "inputs: seats upper range removed",
        GR,
        '_int(deal["seats"], "seats", 1, 10**7)',
        '_int(deal["seats"], "seats", 1, 10**30)',
        ["001"],
    ),
    ("inputs: request type not checked", GR, 'if full and deal["request_type"] not in REQUEST_TYPES:', "if False:", ["001"]),
    ("trace: bidi not flagged", GR, 'flags = ["bidi"] if any(ch in BIDI for ch in text) else []', "flags = []", ["005"]),
    ("trace: quoted history kept", GR, 'if re.match(r"^on .{3,80} wrote:$", s):', "if False:", ["005"]),
    (
        "trace: repeated figure collapsed",
        GR,
        "if len(pcts) + len(prices) > 1:",
        "if len(set(pcts)) + len(set(prices)) > 1:",
        ["005"],
    ),
    ("trace: > 1 figure allowed", GR, "if len(pcts) + len(prices) > 1:", "if len(pcts) + len(prices) > 2:", ["005"]),
    ("trace: 100% cap lifted", GR, "Decimal(tok) <= 100", "Decimal(tok) <= 1000", ["005"]),
    ("trace: zero phrase not a figure", GR, "        found.append(0)", "        pass", ["005"]),
    (
        "trace: terms ambiguity ignored",
        GR,
        '    if p3:  # spec order (gate_rules 5): figures first (steps 2-4), then terms (step 5)\n        return {**out, "reason": p3[0], "terms": terms}\n',
        "",
        ["005"],
    ),
    ("trace: third-off accepted", GR, '        problems.append("unsupported_fraction")', "        pass", ["005"]),
    ("name: boundary before not checked", GR, "(i == 0 or not (hay[i - 1].isascii() and hay[i - 1].isalnum()))", "True", ["006"]),
    ("name: boundary after not checked", GR, "j == len(hay) or not (hay[j].isascii() and hay[j].isalnum())", "True", ["006"]),
    (
        "counter-offer: may equal the exact floor discount",
        GR,
        'book["floor_bps"][deal["plan"]]) - 1,',
        'book["floor_bps"][deal["plan"]]),',
        ["012"],
    ),
    (
        "matrix: below_floor invariant removed",
        GR,
        'need(c["margin"]["below_floor"] == {"blocked": True}, "invariant: below_floor must be blocked")',
        "pass",
        ["040"],
    ),
    (
        "matrix: d4 invariant removed",
        GR,
        'need(c["discount"][s]["d4"] == {"blocked": True}, f"invariant: d4 must be blocked for {s}")',
        "pass",
        ["040"],
    ),
    (
        "matrix: closed top-level keys not enforced",
        GR,
        'need(set(m) == TOP_KEYS, f"top-level keys differ: {sorted(set(m) ^ TOP_KEYS)}")',
        "pass",
        ["040"],
    ),
    ("matrix data: s/d1 needs regional_vp", MX, S1, S2, ["010", "040"]),
    # ---- desk_rules (revision 4)
    (
        "clause: unlisted id ignored",
        DR,
        'if not isinstance(c, str) or c not in policy["clauses"]:',
        "if not isinstance(c, str):",
        ["091"],
    ),
    ("tax: rounds down", DR, "(net * bps + 5000) // 10000", "(net * bps) // 10000", ["082"]),
    ("tax: region/currency mismatch allowed", DR, ' or tx["region_currency"][region] != deal["currency"]', "", ["082"]),
    ("tax: exemption certificate exclusive of today", DR, ">= date.fromisoformat(today)", "> date.fromisoformat(today)", ["083"]),
    ("tax: exemption claim trusted without certificate", DR, 'return (0, 0) if ok else R + "083"', "return (0, 0)", ["083"]),
    ("pool: window exclusive", DR, "if age > win:", "if age >= win:", ["080"]),
    ("pool: own deal pooled with itself", DR, ' or o["deal_id"] == deal["deal_id"]', "", ["080"]),
    ("pool: closed states pooled", DR, ' or o["state"] not in OPEN_STATES', "", ["080"]),
    ("pool: other currency pooled", DR, 'if o["currency"] != deal["currency"] or', "if", ["080"]),
    ("pool: oldest per deal kept", DR, "if cur is None or rank > (", "if cur is None or rank < (", ["080"]),
    ("cumulative: cap >= instead of >", DR, "if cum > ev.cap_bps:", "if cum >= ev.cap_bps:", ["080"]),
    (
        "cumulative: pooled even at zero discount",
        DR,
        'pool(deal, others, policy, now) if terms["discount_bps"] > 0 else []',
        "pool(deal, others, policy, now)",
        ["080"],
    ),
    ("cumulative: size band from this quote only", DR, "g.size_band(pl_list,", "g.size_band(ev.list_total,", ["081"]),
    ("cumulative: bps rounds up", DR, "cum = pl_disc * 10000 // pl_list", "cum = -(-pl_disc * 10000 // pl_list)", ["080"]),
    (
        "cumulative: blocked pooled cell ignored",
        DR,
        'if cell.get("blocked"):\n            blocked.add(R + "081")',
        'if False:\n            blocked.add(R + "081")',
        ["081"],
    ),
    ("decision: closed approval accepted", DR, 'if state != "open":', "if False:", ["022"]),
    ("decision: bad signature accepted", DR, "if sig_ok is not True:", "if False:", ["022"]),
    ("decision: unknown approver accepted", DR, "if approver is None:", "if False:", ["022"]),
    ("decision: inactive approver accepted", DR, 'if approver.get("active") is not True:', "if False:", ["087"]),
    (
        "decision: role below minimum accepted",
        DR,
        "ranks.index(role) < ranks.index(min_role)",
        "ranks.index(role) < ranks.index(min_role) - 1",
        ["022"],
    ),
    (
        "decision: requester employee may approve",
        DR,
        'approver["employee_id"] == requester["employee_id"] or',
        "False or",
        ["087"],
    ),
    (
        "decision: requester person id may approve",
        DR,
        'approver.get("person_id") == requester.get("person_id")',
        "False",
        ["087"],
    ),
    ("decision: same employee may approve twice", DR, 'approver["employee_id"] in accepted_employees', "False", ["087"]),
    ("decision: snapshot not bound", DR, "if not (quote_hash_ok and snapshot_ok):", "if not quote_hash_ok:", ["085"]),
    (
        "decision: window not applied",
        DR,
        'if not g.decision_in_window(request_ts, receipt_ts, matrix["approval_ttl_hours"]):',
        "if False:",
        ["023"],
    ),
    (
        "quote names: second normalisation view dropped",
        DR,
        "for h in own for v in nv",
        "for h in own[:1] for v in nv[:1]",
        ["088"],
    ),
    ("quote validity: 31 days", "config/desk_policy.json", '"valid_days": 30', '"valid_days": 31', ["084"]),
    # ---- desk engine
    ("probe flag: never wired", DK, "probing = g.probe_flag(n_distinct)", "probing = False", ["070"]),
    (
        "probe flag: threshold off by one",
        GR,
        "return distinct_bps_in_24h > threshold",
        "return distinct_bps_in_24h >= threshold",
        ["070"],
    ),
    ("ports: CRM notes leave the port", PU, '"price_book_version",', '"price_book_version", "notes",', ["092"]),
    (
        "ports: reads not logged",
        "src/dealdesk/world.py",
        'self.log.read(who, port, fields, ref, why, rows, self._clock.now() if self._clock else "")',
        "pass",
        ["092"],
    ),
    ("budget: 6 per day", DK, "if len(hist) >= 5:", "if len(hist) >= 6:", ["070"]),
    (
        "duplicate: open quote not recognised",
        DK,
        'if q["quote_hash"] == qh and q["state"] not in TERMINAL:',
        "if False:",
        ["086"],
    ),
    ("rejected terms may be re-proposed", DK, 'if q["quote_hash"] == qh and q["state"] == "rejected":', "if False:", ["024"]),
    ("edit: old approvals not voided", DK, '                self._void_approvals(q, "quote_edited")\n', "", ["085"]),
    (
        "edit: old quote not superseded",
        DK,
        '                self._set_state(q, "superseded", "quote_edited")\n',
        "",
        ["085", "086"],
    ),
    ("cooldown ignored", DK, "if last and g.in_cooldown(", "if False and g.in_cooldown(", ["024"]),
    ("channel identity lane not matched to the step lane", DK, 'if lane != a["lane"]:', "if False:", ["022"]),
    ("decision binding not checked", DK, "bound = all(", "bound = True or all(", ["085"]),
    ("live recompute not required at decision time", DK, "live_ok = self._live_matches(q)", "live_ok = True", ["023", "085"]),
    (
        "snapshot hash of the signature not compared",
        DK,
        'signed["snapshot_hash"] == a["snapshot_hash"] and live_ok',
        "live_ok",
        ["085"],
    ),
    (
        "accepted employees forgotten",
        DK,
        'accepted_emp = [x["employee_id"] for x in q["accepted"]]',
        "accepted_emp = []",
        ["087"],
    ),
    (
        "rejection does not start the cooldown",
        DK,
        "            self.store.put(\"rejections\", f\"{q['account_id']}-{a['lane']}\", now)\n",
        "",
        ["024"],
    ),
    (
        "quote approved before every step",
        DK,
        'if len(q["accepted"]) == len(q["steps"]):',
        'if len(q["accepted"]) >= 1:',
        ["020", "021"],
    ),
    ("next step is always step one", DK, 'k = len(q["accepted"])', "k = 0", ["021"]),
    (
        "expiry never fires",
        DK,
        'if a["state"] == "open" and not g.decision_in_window(a["request_ts"], self.clock.now(), ttl):',
        "if False:",
        ["023"],
    ),
    ("epoch does not advance on expiry", DK, '                q["epoch"] += 1\n', "", ["060"]),
    ("recheck: owner not rechecked", DK, 'if deal["owner_rep"] != q["requester_id"]:', "if False:", ["003"]),
    (
        "recheck: snapshot not compared",
        DK,
        'if canon.snapshot_hash(deal, self.ports.get_pricebook(SYS)) != q["snapshot_hash"]:',
        "if False:",
        ["023"],
    ),
    ("recheck: quote hash not compared", DK, 'if qh != q["quote_hash"]:', "if False:", ["085"]),
    ("recheck: steps not recomputed", DK, 'if [list(s) for s in full.steps] != q["steps"]:', "if False:", ["023"]),
    (
        "recheck: approvals counted not composed",
        DK,
        'if len(acc) != len(q["steps"]) or any(x["lane"] != q["steps"][i][0] for i, x in enumerate(acc)):',
        "if len(acc) < 1:",
        ["022"],
    ),
    ("recheck: approver role not re-read", DK, 'ranks.index(p["role"]) < ranks.index(q["steps"][i][1])', "False", ["023"]),
    (
        "recheck: SoD not rechecked",
        DK,
        'or (req and p["employee_id"] == req["employee_id"])',
        "",
        ["087"],
    ),
    ("recheck: chain window not applied", DK, 'if q["steps"] and not g.chain_ok(', "if False and not g.chain_ok(", ["023"]),
    ("draft: duplicate not recognised", DK, 'if self.store.get("drafts", key[:48]):', "if False:", ["060"]),
    ("draft: watermark missing", DK, '"watermark": "DRAFT"', '"watermark": "FINAL"', ["031"]),
    ("draft: needs no precondition", DK, 'bad = self._recheck(q, "approved")', "bad = None", ["030"]),
    ("claims: seats claim not compared", DK, 'claims["claimed_seats"] != deal["seats"]', "False", ["002"]),
    ("claims: currency claim not compared", DK, 'claims["claimed_currency"] != deal["currency"]', "False", ["004"]),
    ("CRM consistency not checked", DK, "if isinstance(a, str) and a.isascii() and a.isdigit() and", "if False and", ["007"]),
    ("requester owner not checked", DK, 'or deal["owner_rep"] != requester_id', "", ["003"]),
    (
        "approvals composed: next step not requested",
        DK,
        "            self._request_next(q, now)\n",
        "            pass\n",
        ["021"],
    ),
    # ---- executor
    (
        "executor: duplicate not recognised",
        EX,
        "if rec is not None:\n                return",
        "if False:\n                return",
        ["060", "089"],
    ),
    ("executor: kill switch ignored", EX, "if self.kill_switch:", "if False:", ["089"]),
    ("executor: no recheck", EX, 'bad = d._recheck(q, "drafted")', "bad = None", ["089", "030"]),
    (
        "executor: validity inclusive of the day after",
        EX,
        'if d.clock.today() > q["valid_until"]:',
        'if d.clock.today() > q["valid_until"] and False:',
        ["084"],
    ),
    (
        "executor: action cap >=",
        EX,
        'if net > pol["per_action_cap_minor"][ccy]:',
        'if net >= pol["per_action_cap_minor"][ccy]:',
        ["089"],
    ),
    (
        "executor: day cap >=",
        EX,
        'if tot["net"] + net > pol["per_day_cap_minor"][ccy]:',
        'if tot["net"] + net >= pol["per_day_cap_minor"][ccy]:',
        ["089"],
    ),
    (
        "executor: day count >=",
        EX,
        'if tot["count"] + 1 > pol["per_day_count"]:',
        'if tot["count"] + 1 >= pol["per_day_count"]:',
        ["089"],
    ),
    ("executor: dry run applies", EX, "            if dry_run:\n", "            if False:\n", ["089"]),
    (
        "executor: day cap not recorded",
        EX,
        '                    ("commits", f"day-{ccy}-{day}", {"net": tot["net"] + net, "count": tot["count"] + 1}),\n',
        "",
        ["089"],
    ),
    ("executor: void of a non-applied commit", EX, 'if rec is None or rec["state"] != "applied":', "if rec is None:", ["089"]),
    (
        "executor: lock not held",
        EX,
        "        with st.lock:\n            q = d._qget(quote_id)",
        "        if True:\n            q = d._qget(quote_id)",
        ["089"],
    ),
    # ---- inbox
    (
        "inbox: duplicate receipt overwrites",
        IB,
        "            if (tenant, msg_id) in self._d:\n                return False\n",
        "",
        ["093"],
    ),
    (
        "inbox: terminal state not final",
        IB,
        'if r["state"] in TERMINAL:\n                return  # a terminal state is final',
        "if False:\n                return",
        ["093"],
    ),
    (
        "inbox: finished message reprocessed",
        IB,
        'if row["state"] in TERMINAL:\n            return row["state"]',
        'if False:\n            return row["state"]',
        ["093"],
    ),
    ("inbox: one attempt only", IB, "MAX_ATTEMPTS = 3", "MAX_ATTEMPTS = 1", ["093"]),
    (
        "inbox: no dead letter",
        IB,
        '        self.ledger.set_state(tenant, mid, "dead_lettered", "attempts exhausted")\n',
        "",
        ["093"],
    ),
    ("inbox: malformed not rejected", IB, "except Malformed as e:", "except KeyError as e:", ["093"]),
    ("inbox: queue overflow dropped", IB, "return False  # backpressure", "return True  # backpressure", ["093"]),
    (
        "inbox: reconcile blind to missing ids",
        IB,
        '"missing_in_ledger": sorted(source_ids - set(led))',
        '"missing_in_ledger": []',
        ["093"],
    ),
    ("inbox: tenant not part of the key", IB, "self._d[(tenant, msg_id)] = {", "self._d[(None, msg_id)] = {", ["093", "094"]),
    (
        "inbox: unkeyable message acked",
        IB,
        "            return None\n        self.ledger.receive",
        "            pass\n        self.ledger.receive",
        ["093"],
    ),
    # ---- tenant store, identities, guards, text, canon, lock, handler, purposes
    ("store: foreign tenant allowed", ST, "if parts[1] != self.tenant_id:", "if False:", ["094"]),
    ("store: path tricks allowed", ST, 'any(p in ("", ".", "..") for p in parts) or', "", ["094"]),
    (
        "store: any tenant string allowed",
        ST,
        '_TENANT = re.compile(r"[a-z0-9][a-z0-9-]{0,39}", re.ASCII)',
        '_TENANT = re.compile(r".*")',
        ["094"],
    ),
    ("store: any kind allowed", ST, "if kind not in KINDS:", "if False:", ["095"]),
    ("store: chain not linked", ST, 'rec["prev_sha256"] != prev or', "False or", ["094"]),
    ("store: deleted audit tail not detected", ST, "return prev == self.head()", "return True", ["094"]),
    (
        "identity: authorize never denies",
        ID,
        "if not isinstance(identity, str) or action not in IDENTITIES.get(identity, frozenset()):",
        "if False:",
        ["092"],
    ),
    (
        "identity: agent may record decisions",
        ID,
        '"agent_runtime": frozenset({"crm.read",',
        '"agent_runtime": frozenset({"decision.record", "crm.read",',
        ["092"],
    ),
    (
        "identity: drafter may commit",
        ID,
        '"draft_writer": frozenset({"quote.draft",',
        '"draft_writer": frozenset({"quote.commit", "quote.draft",',
        ["092"],
    ),
    (
        "identity: breakglass holds rights at rest",
        ID,
        '"breakglass_dormant": frozenset(),',
        '"breakglass_dormant": frozenset({"quote.read_status"}),',
        ["092"],
    ),
    ("guards: rate cap never throttles", GU, "if self._tokens < 1.0:", "if self._tokens < 0.0:", ["092"]),
    (
        "guards: backwards clock refills",
        GU,
        "self._last = now_s if self._last is None else max(self._last, now_s)",
        "self._last = now_s",
        ["092"],
    ),
    ("guards: connection cap off", GU, "if self.connections >= self.max_connections:", "if False:", ["092"]),
    ("guards: read log accepts any field", GU, "if unknown:", "if False:", ["092"]),
    ("guards: a different recipient is allowed", GU, "elif verdict is not AllowVerdict.EQUAL:", "elif False:", ["092"]),
    ("guards: bare domains ignored", GU, "for d in DOMAIN.findall(no_urls):", "for d in []:", ["092"]),
    (
        "text: instruction phrases not matched without spaces",
        TN,
        'p in v or p.replace(" ", "") in squashed',
        "p in v",
        ["050"],
    ),
    (
        "text: format characters glued only",
        TN,
        '_SPACE = {"Cf", "Cc", "Mn", "Me", "Zs", "Zl", "Zp"}',
        '_SPACE = {"Zs"}',
        ["050", "088"],
    ),
    (
        "canon: clauses not sorted in the quote hash",
        CN,
        'doc = {**q, "clauses": sorted(set(q["clauses"])),',
        'doc = {**q, "clauses": list(q["clauses"]),',
        ["085"],
    ),
    ("canon: quote hash omits the tax", CN, '"total", "tax_region",', '"total",', ["085", "082"]),
    ("lock: training_use not required false", LC, 'p["training_use"] is not False', 'p["training_use"] is False', ["095"]),
    ("lock: stale check allowed", LC, "(now - checked).days > max_age_days", "(now - checked).days > 10**6", ["095"]),
    ("lock: future date allowed", LC, "if checked > now:", "if False:", ["095"]),
    (
        "handler: attachment text feeds the figures",
        HD,
        "tr = g.traceability(text)",
        'tr = g.traceability(text + " " + " ".join(a.get("text", "") for a in atts))',
        ["005", "050"],
    ),
    ("handler: other account in the message tolerated", HD, "if others:", "if False:", ["006"]),
    (
        "handler: no account match required",
        HD,
        'if not mine and deal_id not in text and deal["account_id"] not in text:',
        "if False:",
        ["006"],
    ),
    ("handler: injection not logged", HD, 'desk._log("injection_flag", msg_id=msg["msg_id"], flags=flags)', "pass", ["050"]),
    ("handler: message of another tenant accepted", HD, 'if msg.get("tenant_id") != desk.store.tenant_id:', "if False:", ["094"]),
    (
        "purposes: CRM notes reach the model",
        PU,
        '"deal.seats": deal["seats"],',
        '"deal.seats": deal["seats"], "deal.notes": deal.get("notes"),',
        ["092"],
    ),
    (
        "hygiene: another demo's identifier slips into the source",
        PU,
        "never leaves the port (deny-all start).",
        "never leaves the port (deny-all start; see demos/" + "refunds).",
        ["096"],
    ),
]
# Mutants whose target text moved in revision 5 (signed approvals, real identities, persistent kill switch): name -> (old, new)
FIXUPS = {
    "quote names: second normalisation view dropped": (
        NL.join(
            ['    for n in policy["competitor_names"]:', "        if any(_whole(h, v) for h in own for v in views(n) if v):"]
        ),
        NL.join(
            [
                '    for n in policy["competitor_names"]:',
                "        if any(_whole(h, v) for h in own[:1] for v in views(n)[:1] if v):",
            ]
        ),
    ),
    "decision binding not checked": ('and raw["requested_at"] == a["request_ts"]', "and True"),
    "live recompute not required at decision time": ("live_ok = self._live_matches(q, VERIFIER)", "live_ok = True"),
    "snapshot hash of the signature not compared": ('raw["snapshot_hash"] == a["snapshot_hash"] and live_ok', "live_ok"),
    "recheck: snapshot not compared": (
        'if canon.snapshot_hash(deal, self.ports.get_pricebook(who)) != q["snapshot_hash"]:',
        "if False:",
    ),
    "draft: needs no precondition": ('bad = self._recheck(q, "approved", who)', "bad = None"),
    "executor: kill switch ignored": ("if d._kill_on():  # read under the commit lock, from the store", "if False:"),
    "executor: no recheck": ('bad = d._recheck(q, "drafted", who)', "bad = None"),
    "inbox: unkeyable message acked": ('if not isinstance(msg, dict) or "_auth" in msg:', "if not isinstance(msg, dict):"),
    "identity: agent may record decisions": (
        '"agent_runtime": frozenset(\n        {',
        '"agent_runtime": frozenset(\n        {"decision.record", ',
    ),
    "text: format characters glued only": ('_SPACEY = {"Cf", "Cc", "Mn", "Me", "Zl", "Zp"}', "_SPACEY = set()"),
    "inbox: duplicate receipt overwrites": (
        'cur = self._d.get((tenant, msg_id))\n            if cur is not None:\n                return "duplicate" if cur["raw_sha256"] == _sha(raw) else "conflict"',
        "cur = None",
    ),
}
MUTS = [(n, f, *FIXUPS.get(n, (o, w)), r) for n, f, o, w, r in MUTS]
IN = "src/dealdesk/inbox.py"
WD = "src/dealdesk/world.py"
FZ = "src/dealdesk/freeze.py"
LM = "src/dealdesk/limits.py"
MUTS += [
    # ---- revision 5: the first code review and design review of PR #3
    ("percent: lookbehind lets letters before the token through", GR, "(?<![A-Za-z0-9.,+-])", "(?<![0-9.,])", ["005"]),
    ("percent: token may not carry letters", GR, "([A-Za-z0-9.,+-]+)", "([0-9.,+-]+)", ["005"]),
    ("percent: requires a digit in the token (spelled numbers)", GR, "(?=[A-Za-z.,+-]*[0-9])", "", ["005"]),
    ("limits: handler text cap removed", HD, "if len(text) > limits.max_text_chars:", "if False:", ["093"]),
    ("limits: attachment count cap removed", HD, "or len(atts) > limits.max_attachments", "", ["093"]),
    ("limits: attachment size cap removed", HD, 'or len(a.get("text", "")) > limits.max_attachment_chars', "", ["093"]),
    ("limits: inbox size cap removed", IB, 'if len(raw.encode("ascii")) > self.limits.max_message_bytes:', "if False:", ["093"]),
    ("limits: msg id length cap removed", IB, "or len(mid) > self.limits.max_id_chars", "", ["093"]),
    (
        "inbox: rate cap not applied",
        IB,
        "if self.rate_cap is not None and not self.rate_cap.allow(self.now_s()):",
        "if False:",
        ["093", "092"],
    ),
    (
        "inbox: reserved auth key accepted from the body",
        IB,
        'if not isinstance(msg, dict) or "_auth" in msg:',
        "if not isinstance(msg, dict):",
        ["093", "022"],
    ),
    ("inbox: id reuse not recorded", IB, 'if status == "conflict":', "if False:", ["093"]),
    ("inbox: deadline not enforced", IB, "th.join(self.limits.handler_deadline_s)", "th.join()", ["093"]),
    ("inbox: handler state not validated", IB, "if state not in HANDLER_STATES:", "if False:", ["093"]),
    (
        "inbox: processing rows not listed as open",
        IB,
        'r["state"] in ("received", "processing"))',
        'r["state"] in ("received",))',
        ["093"],
    ),
    ("inbox: recover does nothing", IB, "        for mid in self.ledger.open_ids(tenant):", "        for mid in []:", ["093"]),
    (
        "handler: body identity used for the decision",
        HD,
        'desk.record_decision(auth["identity"], _req(msg, "decision", dict), auth["person_id"])',
        'desk.record_decision(msg.get("identity", auth["identity"]), _req(msg, "decision", dict), auth["person_id"])',
        ["022"],
    ),
    (
        "handler: authenticated person not passed",
        HD,
        '_req(msg, "decision", dict), auth["person_id"])',
        '_req(msg, "decision", dict), None)',
        ["022"],
    ),
    (
        "handler: request not repaired after a crash",
        HD,
        'if state == "pending":',
        'if state == "pending" and res["status"] == "created":',
        ["021", "093"],
    ),
    ("handler: date cue ignored", HD, "if _DATE_CUE.search(text):", "if False:", ["005"]),
    (
        "desk: channel person may differ from the signed approver",
        DK,
        'not isinstance(authenticated_person, str) or authenticated_person != raw["approver_id"]',
        'authenticated_person is not None and authenticated_person != raw["approver_id"]',
        ["022"],
    ),
    ("desk: decision shape not validated", DK, "or not self._shape_ok(raw):", ":", ["022"]),
    ("desk: decision value not validated", DK, 'raw["decision"] in ("approve", "reject")', "True", ["022"]),
    ("desk: decision id length not validated", DK, 'not 0 < len(v) <= (140 if k == "sig" else n)', "False", ["022"]),
    (
        "desk: signed args hash not required to match",
        DK,
        "args_hash=canon.decision_args_hash(raw),",
        "args_hash=raw['args_hash'],",
        ["022", "085"],
    ),
    ("desk: signature not verified", DK, "return verdict.ok", "return True", ["022"]),
    (
        "desk: kill switch ignored by draft",
        DK,
        "if self._kill_on():  # persistent, tenant-scoped, read under the same lock as the act",
        "if False:",
        ["089"],
    ),
    ("desk: config hash not rechecked", DK, "if not self._config_intact():", "if False:", ["040"]),
    (
        "desk: config not frozen",
        DK,
        "self.matrix, self.policy = freeze(matrix), freeze(policy)",
        "self.matrix, self.policy = matrix, policy",
        ["040"],
    ),
    (
        "desk: intent not written before the draft",
        DK,
        'seq = self._intent("quote_draft", quote_id, key=key[:48])',
        "seq = 0",
        ["060"],
    ),
    ("desk: draft not egress-checked", DK, "if bad_egress:", "if False:", ["092"]),
    (
        "desk: reply not egress-checked",
        DK,
        '            if bad:\n                self._log("egress_refused", requester=str(requester_id)[:64], violations=bad)',
        '            if False:\n                self._log("egress_refused", requester=str(requester_id)[:64], violations=bad)',
        ["092"],
    ),
    (
        "desk: reads as the wrong identity at draft",
        DK,
        'bad = self._recheck(q, "approved", who)',
        'bad = self._recheck(q, "approved", SYS)',
        ["092"],
    ),
    (
        "desk: verifier identity reads with the agent identity",
        DK,
        'VERIFIER = "decision_service"',
        'VERIFIER = "agent_runtime"',
        ["092"],
    ),
    (
        "desk: kill switch not persisted",
        DK,
        'self.store.put("logs", "kill-switch", {"on": on, "at": self.clock.now()})',
        "pass",
        ["089"],
    ),
    (
        "desk: status without the lock",
        DK,
        "    def status(self, who, quote_id: str) -> dict:\n        with self.store.lock:\n",
        "    def status(self, who, quote_id: str) -> dict:\n        if True:\n",
        ["030"],
    ),
    (
        "executor: intent not written before the commit",
        EX,
        'seq = d._intent("commit_quote", quote_id, key=key[:48], net=net, currency=ccy)  # audit BEFORE the act',
        "seq = 0",
        ["089"],
    ),
    (
        "executor: void without a reason",
        EX,
        "if not isinstance(reason, str) or not 0 < len(reason.strip()) <= 200:",
        "if False:",
        ["089"],
    ),
    (
        "executor: caps read from the live world",
        EX,
        'doc, pol = q["doc"], d.policy["executor"]',
        'doc, pol = q["doc"], d.w.policy["executor"]',
        ["089", "040"],
    ),
    ("freeze: nested lists stay mutable", FZ, "return tuple(freeze(v) for v in obj)", "return obj", ["040"]),
    ("freeze: sealed objects can be rebound", FZ, 'if self.__dict__.get("_sealed"):', "if False:", ["040"]),
    ("ports: read cap not applied", WD, "if self._cap is not None and not self._cap.allow(self._now_s()):", "if False:", ["092"]),
    ("ports: rebinding allowed", WD, 'if self.__dict__.get("_sealed_ports"):', "if False:", ["092"]),
    ("keys: revoked key still verifies", WD, "self._k.get(person_id, {}).pop(key_id, None)", "pass", ["022"]),
    (
        "limits: deadline not validated",
        LM,
        "if not isinstance(self.handler_deadline_s, int | float) or self.handler_deadline_s <= 0:",
        "if False:",
        ["093"],
    ),
    (
        "egress: non-string text passes",
        GU,
        'if not isinstance(text, str):\n        return ["TEXT_NOT_STRING"]',
        "if not isinstance(text, str):\n        return []",
        ["092"],
    ),
    (
        "egress: look-alike letters not folded",
        TN,
        "return fold(text, casefold=True, collapse_ws=True), fold(spaced, casefold=True, collapse_ws=True)",
        "return text.casefold(), spaced.casefold()",
        ["092", "088", "050"],
    ),
    (
        "egress: over-long text passes",
        GU,
        '    if len(text) > MAX_EGRESS_CHARS:\n        return ["TEXT_TOO_LONG"]',
        '    if False:\n        return ["TEXT_TOO_LONG"]',
        ["092"],
    ),
    ("textnorm: scan length not bounded", TN, "if len(text) > MAX_SCAN_CHARS:", "if False:", ["050"]),
    (
        "signing: any signature verifies",
        "src/dealdesk/signing.py",
        "ed25519.Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)",
        "pass",
        ["022"],
    ),
]
MUTS += [
    # ---- priority pass: newest core behaviours, backstops, mailbox identity, reply leak check
    ("egress: a look-alike recipient is not reported as one", GU, "if verdict is AllowVerdict.LOOKALIKE:", "if False:", ["092"]),
    (
        "egress: recipient compared loosely",
        GU,
        "verdict = allow_equal(recipient, requester_email)",
        "verdict = AllowVerdict.EQUAL if recipient.casefold() == requester_email.casefold() else AllowVerdict.DIFFERENT",
        ["092"],
    ),
    ("names: mixed-script account name accepted", DR, "if has_mixed_script(account_name):", "if False:", ["088"]),
    (
        "names: a same-name account is counted as a leak",
        DR,
        "if names_equal(n, account_name):  # a same-name account is a collision, not a leak",
        "if False:  # a same-name account is a collision, not a leak",
        ["088"],
    ),
    (
        "trace: no backstop for unbounded text",
        GR,
        'if not isinstance(text, str) or len(text) > MAX_TEXT_CHARS:\n        return {**out, "reason": "text_too_long"}',
        'if False:\n        return {**out, "reason": "text_too_long"}',
        ["005"],
    ),
    (
        "names scan: no backstop for unbounded text",
        GR,
        'if not isinstance(text, str) or len(text) > MAX_TEXT_CHARS:\n        raise InputError("text too long to scan")',
        'if False:\n        raise InputError("text too long to scan")',
        ["006"],
    ),
    (
        "kill switch: an unreadable switch means off",
        DK,
        "            return True\n\n    @staticmethod",
        "            return False\n\n    @staticmethod",
        ["089"],
    ),
    (
        "sod: mailbox identity of the requester not compared at decision time",
        DK,
        "if approver and self._mail_key(approver) is not None and self._mail_key(approver) == self._mail_key(requester):",
        "if False:",
        ["087"],
    ),
    (
        "sod: mailbox identity of an earlier approver not compared at decision time",
        DK,
        "if approver and (self._mail_key(approver) in prior_keys):",
        "if False:",
        ["087"],
    ),
    (
        "sod: mailbox identity not rechecked at draft/commit (requester or earlier approver)",
        DK,
        "                or mk in seen_mail\n                or mk == self._mail_key(req)\n",
        "",
        ["087"],
    ),
    (
        "sod: mailbox key keeps the plus tag",
        DK,
        'return local.split("+", 1)[0] + "@" + domain',
        'return local + "@" + domain',
        ["087"],
    ),
    (
        "reply: leak check removed",
        DK,
        NL.join(["            if not bad:", "                try:", "                    keep"]),
        NL.join(["            if False:", "                try:", "                    keep"]),
        ["092"],
    ),
    (
        "reply: protected values dropped",
        DK,
        "keep = [p for p in protected if isinstance(p, str) and len(p) >= 4]",
        "keep = []",
        ["092"],
    ),
    (
        "handler: protected values not passed to the reply",
        HD,
        "desk.send_reply(SYS, requester, rep_reply(status, name=name, **kw), protected)",
        "desk.send_reply(SYS, requester, rep_reply(status, name=name, **kw), ())",
        ["092"],
    ),
    (
        "core copy: textnorm fold drops the digit table",
        "src/dealdesk/core_copy/textnorm.py",
        "s = s.translate(_DIGITS).translate(_TABLE)",
        "s = s.translate(_TABLE)",
        ["092", "088"],
    ),
]
MUTS += [
    # ---- burst scaling: the account-name index
    (
        "index: names with no alphanumeric run are not always checked (message scan)",
        "src/dealdesk/nameindex.py",
        "                self._always_lower.append(i)",
        "                pass",
        ["088", "006"],
    ),
    (
        "index: only the first normalisation view of the text is looked up",
        "src/dealdesk/nameindex.py",
        "        for v in own:",
        "        for v in own[:1]:",
        ["088", "006"],
    ),
    (
        "index: message-scan candidates not narrowed by the text tokens",
        "src/dealdesk/nameindex.py",
        "            idx.update(self._lower.get(t, ()))",
        "            idx.update(range(len(self.entries)))",
        ["088", "006"],
    ),
    (
        "index: rename does not move the change token",
        "src/dealdesk/world.py",
        "        self.names_version += 1",
        "        pass",
        ["088", "006"],
    ),
    (
        "index: cache ignores the change token",
        "src/dealdesk/world.py",
        "        ver = (self._w.names_version, len(deals))",
        "        ver = (0, len(deals))",
        ["088", "006"],
    ),
    (
        "handler: candidates are not confirmed by the whole-name test",
        "src/dealdesk/handler.py",
        " and g._whole_name(clean, lower_norm(n))",
        "",
        ["088", "006"],
    ),
    (
        "handler: the deal's own name counted as another account",
        "src/dealdesk/handler.py",
        "if n != own_name and g",
        "if g",
        ["088", "006"],
    ),
    (
        "quote names: second normalisation view dropped (other accounts)",
        DR,
        NL.join(["            continue", "        if any(_whole(h, v) for h in own for v in views(n) if v):"]),
        NL.join(["            continue", "        if any(_whole(h, v) for h in own[:1] for v in views(n)[:1] if v):"]),
        ["088"],
    ),
    # ---- review 2: fail-closed gaps and id reuse
    ("review2: commit accepts a non-bool dry_run", EX, "if not isinstance(dry_run, bool):", "if False:", ["089"]),
    (
        "review2: a requester who left the directory still passes the recheck",
        DK,
        'if req is None or not req["active"] or self._mail_key(req) is None:',
        "if False:",
        ["003"],
    ),
    (
        "review2: a revoked signing key does not void an accepted step",
        DK,
        'if x.get("key_id") not in self.keys.keys_for(x["approver_id"]):',
        "if False:",
        ["023"],
    ),
    (
        "review2: a decision without a usable mailbox identity is accepted",
        DK,
        "if approver and (self._mail_key(approver) is None or self._mail_key(requester) is None):",
        "if False:",
        ["087"],
    ),
    ("review2: an approver without a mailbox identity passes the recheck", DK, "if mk is None:", "if False:", ["087"]),
    ("review2: the reserved id-reuse marker is allowed in a sender id", IB, " or ID_REUSE_MARK in mid", "", ["093"]),
    (
        "review2: the id-reuse row is first written as received",
        IB,
        'tenant, cid, raw, "rejected", "id_reuse"',
        'tenant, cid, raw, "received", None',
        ["093"],
    ),
]

SELECT = ["-k", "not 1000 and not independent_of_test_split and not doc_consistency"]


def tree_hash() -> str:
    h = hashlib.sha256()
    files = sorted(
        [
            *ROOT.glob("src/**/*.py"),
            *ROOT.glob("config/**/*"),
            *ROOT.glob("tests/*.py"),
            *ROOT.glob("demo_only/data/*.json*"),
            *ROOT.glob("tests/fixtures/*.json"),
            *ROOT.glob("core_copies.json"),
            *ROOT.glob("pyproject.toml"),
            *ROOT.glob("mutation/expected_kills.json"),
        ],
        key=lambda p: p.as_posix(),
    )
    for p in files:
        if not p.is_file() or p.name in ("test_doc_consistency.py",) or "__pycache__" in p.parts:
            continue
        h.update(p.relative_to(ROOT).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


MUTANT_TIMEOUT_S = int(os.environ.get("MUTANT_TIMEOUT_S", "900"))  # per mutant; the unmutated suite takes a few minutes
TIMEOUT_RC = -999


def run_pytest(dst: Path) -> tuple[int, list[str]]:
    src, extra = str(dst / "src"), [str(dst / "tests"), str(dst / "demo_only" / "data")]
    code = (
        "import sys; sys.meta_path=[f for f in sys.meta_path if 'editable' not in repr(f).lower()]; "
        f"sys.path=[x for x in sys.path if not x.replace(chr(92), '/').endswith('dealdesk/src')]; sys.path[:0]={[src, *extra]!r}; "
        f"import dealdesk; assert dealdesk.__file__.startswith({src!r}), dealdesk.__file__; "
        f"import pytest; sys.exit(pytest.main(['-q','-p','no:cacheprovider','-o','pythonpath=','--maxfail=5','-rf','--tb=no',{SELECT[0]!r},{SELECT[1]!r},'tests']))"
    )
    try:
        r = subprocess.run(
            [sys.executable, "-c", code],
            check=False,
            cwd=dst,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=MUTANT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:  # a mutant that hangs the suite proves nothing: inconclusive, NOT killed
        return TIMEOUT_RC, ["TIMEOUT"]
    fails = [ln.split(" ")[1].split("::")[-1][:60] for ln in r.stdout.splitlines() if ln.startswith("FAILED ")]
    return r.returncode, fails if fails else ([r.stdout[-200:].replace("\n", " ")] if r.returncode else [])


def fresh_copy(tmp: str) -> Path:
    dst = Path(tmp) / "demo"
    shutil.copytree(
        ROOT,
        dst,
        ignore=shutil.ignore_patterns(
            ".venv",
            "__pycache__",
            ".ruff_cache",
            ".pytest_cache",
            "tests_oneshot",
            "uv.lock",
            "test.jsonl",
            "test_manifest.json",
        ),
    )
    return dst


PINS = (
    ROOT / "mutation" / "expected_kills.json"
)  # mutant name -> the tests that failed FIRST when it was recorded (--maxfail=5, names cut to 60 chars). NOT independently chosen reasons: a later run is judged by set intersection with this recording


def main(argv: list[str]) -> int:
    apply_only = "--apply-only" in argv
    for name, f, old, _new, _r in MUTS:
        n = (ROOT / f).read_text(encoding="utf-8").count(old)
        if n != 1:
            print(f"MUTANT DOES NOT APPLY EXACTLY ONCE ({n}): {name}")
            return 2
    if apply_only:
        print(f"all {len(MUTS)} mutants apply exactly once")
        return 0
    print(f"tree_sha256: {tree_hash()}")
    print(f"mutants: {len(MUTS)}")
    print("rules_covered: " + " ".join(sorted({r for m in MUTS for r in m[4]})))
    tmp = tempfile.mkdtemp()
    try:
        base = fresh_copy(tmp + "/base")
        rc, fails = run_pytest(base)
        if rc != 0:
            print(f"BASELINE FAILED (the unmutated copy must pass): {fails}")
            return 3
        print("baseline: unmutated copy passes")
        jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else 1

        def one(i: int) -> tuple[bool, str, list, list]:
            name, f, old, new, rules = MUTS[i]
            d = fresh_copy(f"{tmp}/m{i}")
            p = d / f
            p.write_text(p.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8", newline=chr(10))
            rc, fails = run_pytest(d)
            shutil.rmtree(d.parent, ignore_errors=True)
            return rc == 0, name, rules, fails

        survived = bad_reason = timeouts = 0
        record = "--record" in argv
        pins: dict = {} if record or not PINS.exists() else json.loads(PINS.read_text(encoding="utf-8"))
        seen: dict = {}
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            for i, (dead, name, rules, fails) in enumerate(
                pool.map(one, range(len(MUTS)))
            ):  # results come back in mutant order whatever the worker count
                survived += dead
                if fails == ["TIMEOUT"]:
                    bad_reason += 1
                    timeouts += 1
                    verdict = "TIMEOUT | inconclusive, NOT counted as killed"
                elif dead:
                    verdict = "SURVIVED"
                elif record:
                    seen[name] = fails
                    verdict = "CAUGHT | recorded"
                elif name not in pins:
                    bad_reason += 1
                    verdict = "CAUGHT_UNPINNED | no pinned reason"
                elif set(fails) & set(pins[name]):
                    verdict = "CAUGHT | reason ok"
                else:
                    bad_reason += 1
                    verdict = "CAUGHT_UNEXPECTED | none of the failing tests is a pinned reason"
                print(f"{name} | R-{','.join(rules)} | {verdict} | killed by: {'; '.join(fails[:5])}", flush=True)
        if record:
            PINS.write_text(json.dumps(seen, indent=1, sort_keys=True) + chr(10), encoding="utf-8", newline=chr(10))
        print(
            f"summary: {len(MUTS) - survived - timeouts} of {len(MUTS)} CAUGHT, {survived} SURVIVED, {timeouts} TIMEOUT, {bad_reason} UNPINNED OR UNEXPECTED REASON"
        )  # a TIMEOUT is inconclusive: never in the CAUGHT count
        return 1 if survived or bad_reason else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
