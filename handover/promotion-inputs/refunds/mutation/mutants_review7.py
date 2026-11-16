"""Mutants for the code and the findings of review 7 (bindings, shapes, hostile input, tier recompute, reservation expiry, clock rules, tenant scoping).
(name, file, regex, replacement); each regex must match exactly once. Only mutants that a finding or a changed line needs: no mutants for their own sake."""

W, A, S, G = "src/refunds/writegate.py", "src/refunds/approval.py", "src/refunds/store.py", "src/refunds/guards.py"

RETIRED: set[str] = set()  # deleted in rev 9

# property -> the mutant that still covers it, for mutants dropped earlier (review 7, M10: "confirm the dropped mutants' properties are mutated elsewhere")
DROPPED_COVERED_BY = {
    "guards: write without approval allowed": "write: approval never verified",
    "guards: day cap > instead of >=": "write: DAY_CAP uses >=",
    "guards: kill switch ignored": "write: kill switch ignored",
    "guards: write gate has no lock": "write: check and write not one transaction",
    "guards: write gate accepts bool/zero/non-int money": "write: basis/amount canonical parse removed",
    "guards: write gate accepts unknown currency": "write: basis/amount canonical parse removed",
    "guards: same key with different parameters replays": "write: same key with other parameters replays (all legs)",
    "guards: day cap pooled across currencies": "store: day total not tenant scoped",
    "guards: write gate day taken from the caller key": "write: day bucket from the local date, not UTC",
    "guards: per-action cap ignores currency": "write: OVER_CAP uses >=",
    "guards: write gate dry_run defaults to False": "write: dry run applies",
}

NEW = [
    # ---- M1: every field a later check reads is inside the hash
    ("hash: beneficiary not bound", W, r"        \"beneficiary\": req\[\"beneficiary\"\],\n", ""),
    ("hash: cluster not bound", W, r"        \"cluster\": sorted\(req\[\"cluster\"\]\),\n", ""),
    ("hash: cluster order matters", W, r"\"cluster\": sorted\(req\[\"cluster\"\]\)", '"cluster": list(req["cluster"])'),
    # ---- M3 / M8: input validation
    (
        "write: basis/amount canonical parse removed",
        W,
        r"            for k in BASIS_NUMBERS:\n                parse_nonneg\(basis\[k\]\)\n",
        "            pass\n",
    ),
    (
        "write: basis allows negative numbers",
        "src/refunds/money.py",
        r"_CANON0 = re\.compile\(r\"0\|\[1-9\]\[0-9\]\{0,11\}\"\)",
        '_CANON0 = re.compile(r"-?[0-9]{1,12}")',
    ),
    ("write: cluster entry shape not checked", W, r"            and all\(valid_id\(c\) for c in cluster\)\n", ""),
    (
        "write: cluster size not capped",
        W,
        r"            and 0 < len\(cluster\) <= MAX_CLUSTER_SIZE\n",
        "            and len(cluster) > 0\n",
    ),
    ("write: customer not in its own cluster", W, r"            and req\[\"customer_id\"\] in cluster\n", ""),
    ("write: line count not capped", W, r"and len\(req\[\"line_ids\"\]\) <= MAX_LINES", ""),
    (
        "write: requester/beneficiary text not checked",
        W,
        r"        if not \(_text_ok\(req\[\"requester\"\]\) and _text_ok\(req\[\"beneficiary\"\]\)\):\n            return \"KEY_INVALID\"\n",
        "",
    ),
    ("write: text length not capped", W, r"and 0 < len\(s\) <= TEXT_MAX", "and len(s) > 0"),
    ("write: control and bidi characters allowed in text", W, r"\(\"Cc\", \"Cf\", \"Zl\", \"Zp\", \"Co\", \"Cs\"\)", "()"),
    (
        "write: tier not restricted to the two real tiers",
        W,
        r"req\[\"tier\"\] in \(\"human\", \"four_eyes\"\)",
        'isinstance(req["tier"], str)',
    ),
    (
        "write: tier floor value not restricted",
        W,
        r"            and basis\[\"tier_floor\"\] in \(\"\", \"human\", \"four_eyes\"\)\n",
        "",
    ),
    (
        "write: basis may carry extra keys",
        W,
        r"            and set\(basis\) == \{\*BASIS_NUMBERS, \"tier_floor\", \"request\"\}\n",
        "",
    ),
    ("write: basis values may be non-text", W, r"            and all\(isinstance\(v, str\) for v in basis\.values\(\)\)\n", ""),
    ("approval: steps may carry extra keys", A, r"set\(s\) == \{\"person\", \"role\"\} and ", ""),
    ("approval: step count not bounded", A, r"            and len\(steps\) <= 4\n", ""),
    ("approval: id length not bounded", A, r"0 < len\(a\[\"approval_id\"\]\) <= 64", 'len(a["approval_id"]) > 0'),
    # ---- verify rules that were rewritten
    (
        "approval: MAC not checked",
        A,
        r"if not hmac\.compare_digest\(_mac\(self\._key, a\), a\[\"mac\"\]\):  # type: ignore\[index\]",
        "if False:",
    ),
    ("approval: args hash not compared", A, r"a\[\"args_hash\"\] != args_hash  # type: ignore\[index\]", "False"),
    ("approval: signed tier not compared to the request", A, r"or a\[\"tier\"\] != tier  # type: ignore\[index\]", ""),
    (
        "approval: signed request time not compared to the request",
        A,
        r"or a\[\"requested_at\"\] != requested_at  # type: ignore\[index\]",
        "",
    ),
    (
        "approval: a one-approver signature on a basis that needs two",
        A,
        r"or \(min_tier == \"four_eyes\" and tier == \"human\"\)",
        "",
    ),
    ("approval: requester may approve", A, r"if norm\(requester\) in people:", "if False:"),
    (
        "approval: requester compared without normalising",
        A,
        r"if norm\(requester\) in people:",
        'if requester in [s["person"] for s in steps]:',
    ),
    ("approval: beneficiary may approve", A, r"if norm\(beneficiary\) in people:", "if False:"),
    (
        "approval: beneficiary compared without normalising",
        A,
        r"if norm\(beneficiary\) in people:",
        'if beneficiary in [s["person"] for s in steps]:',
    ),
    (
        "approval: people not normalised for the same-person check",
        A,
        r"people = \[norm\(s\[\"person\"\]\) for s in steps\]",
        'people = [s["person"] for s in steps]',
    ),
    (
        "approval: directory lookup not normalised",
        A,
        r"self\.directory\.get\(norm\(s\[\"person\"\]\), frozenset\(\)\)",
        'self.directory.get(s["person"], frozenset())',
    ),
    (
        "approval: role not in the directory accepted",
        A,
        r"        if any\(s\[\"role\"\] not in self\.directory\.get\(norm\(s\[\"person\"\]\), frozenset\(\)\) for s in steps\):\n            return \"APPROVER_UNKNOWN\"\n",
        "",
    ),
    ("approval: role outside the matrix accepted", A, r"or any\(s\[\"role\"\] not in ROLES for s in steps\)", ""),
    (
        "approval: NFKC dropped from the person comparison",
        A,
        r"unicodedata\.normalize\(\"NFKC\", s\)\.strip\(\)\.casefold\(\)",
        "s.strip().casefold()",
    ),
    # ---- M6: the tier is recomputed at execute
    (
        "write: minimum tier ignores the cumulative",
        W,
        r"base = tier_for\(req\[\"currency\"\], max\(amount, order_cum, cust_cum\)\)",
        'base = tier_for(req["currency"], amount)',
    ),
    (
        "write: minimum tier ignores the signed risk floor",
        W,
        r"or req\[\"basis\"\]\[\"tier_floor\"\] != \"four_eyes\" else",
        "or True else",
    ),
    # ---- M5: reservations expire; sweeper
    ("store: expired reservations still hold the cap", S, r" AND created_at>=\?\"", '"'),
    ("store: reservation filter uses the wrong bound", S, r"AND key<>\? AND created_at>=\?\"", 'AND key<>? AND created_at<=?"'),
    (
        "write: sweeper identity not checked",
        W,
        r"if not isinstance\(identity, str\) or not identities\.authorize\(identity, \"release\"\):",
        "if False:",
    ),
    (
        "store: sweep deletes everything",
        S,
        r"DELETE FROM reservations WHERE created_at<\?",
        "DELETE FROM reservations WHERE created_at<?  OR 1=1",
    ),
    (
        "write: sweep ignores the approval TTL",
        W,
        r"older = \(now - timedelta\(seconds=APPROVAL_TTL_S\)\)\.strftime\(FMT\)",
        "older = now.strftime(FMT)",
    ),
    # ---- N4 / N5: identity first, clock window and ratchet
    (
        "write: identity checked only after parsing",
        W,
        r"        if not isinstance\(identity, str\) or not any\(\n            identities\.authorize\(identity, a\) for a in ACTION_TO_IDENTITY_ACTION\.values\(\)\n        \):\n            return _deny\(\"IDENTITY_DENIED\"\)  # first: a caller that may not write learns nothing about the request\n",
        "",
    ),
    (
        "write: per-action identity check removed",
        W,
        r"        if not identities\.authorize\(identity, ACTION_TO_IDENTITY_ACTION\[req\[\"action\"\]\]\):\n            return _deny\(\"IDENTITY_DENIED\"\)\n",
        "",
    ),
    (
        "write: clock window removed",
        W,
        r"        if not CLOCK_MIN <= stamp < CLOCK_MAX:\n            return \"CLOCK_INVALID\"\n",
        "",
    ),
    ("write: clock may go backwards", W, r"if last is not None and stamp < last:", "if False:"),
    (
        "write: ratchet not moved by an applied payment",
        W,
        r"        self\.store\.set_meta\(\"last_clock\", stamp\)\n        self\.store\.audit\(tenant, \"intent\"",
        '        self.store.audit(tenant, "intent"',
    ),
    (
        "write: kill switch flip does not move the ratchet",
        W,
        r"            self\.store\.set_kill_switch\(on, identity, reason\.strip\(\), stamp\)\n            self\.store\.set_meta\(\"last_clock\", stamp\)\n",
        "            self.store.set_kill_switch(on, identity, reason.strip(), stamp)\n",
    ),
    (
        "write: kill switch ignores the clock rule",
        W,
        r"            now = self\._now\(\)\n            if isinstance\(now, str\):\n                return _deny\(now\)\n            stamp = now\.strftime\(FMT\)\n            self\.store\.set_kill_switch",
        '            now = None\n            stamp = "2026-10-20T12:00:00Z"\n            self.store.set_kill_switch',
    ),
    (
        "write: kill switch flipped without a reason",
        W,
        r"or not reason\.strip\(\) or len\(reason\) > TEXT_MAX",
        "or len(reason) > TEXT_MAX",
    ),
    (
        "store: a failed COMMIT leaves the transaction open",
        S,
        r"                    self\._db\.execute\(\"ROLLBACK\"\)  # a failed COMMIT must not leave the connection inside a transaction\n",
        "",
    ),
    # ---- rewritten backstop lines
    ("write: OVER_REFUNDABLE removed", W, r"if refunded \+ amount > int\(basis\[\"captured_minor\"\]\):", "if False:"),
    (
        "write: OVER_REFUNDABLE uses >=",
        W,
        r"if refunded \+ amount > int\(basis\[\"captured_minor\"\]\):",
        'if refunded + amount >= int(basis["captured_minor"]):',
    ),
    ("write: ORDER_CAP uses >=", W, r"if order_cum > lim\.hard_cap:", "if order_cum >= lim.hard_cap:"),
    ("write: CUSTOMER_CAP uses >=", W, r"if cust_cum > lim\.customer_30d_cap:", "if cust_cum >= lim.customer_30d_cap:"),
    ("write: DAY_CAP ignores other reservations", W, r"\+ self\.store\.other_reserved\(t, req\[\"currency\"\], key, since\)", ""),
    # ---- M10: tenant scoping of the remaining store reads
    (
        "store: order sums not tenant scoped",
        S,
        r"WHERE tenant=\? AND order_id=\? AND currency=\? AND action=\?\"",
        'WHERE order_id=? AND currency=? AND action=?"',
    ),
    (
        "store: customer sums not tenant scoped",
        S,
        r"WHERE tenant=\? AND currency=\? AND applied_at>=\? AND customer_id=\?\"",
        'WHERE currency=? AND applied_at>=? AND customer_id=?"',
    ),
    (
        "store: reservation list not tenant scoped",
        S,
        r"SELECT \* FROM reservations WHERE tenant=\? ORDER BY key",
        "SELECT * FROM reservations WHERE ?<>'' ORDER BY key",
    ),
    (
        "store: compensation records not tenant scoped",
        S,
        r"SELECT record FROM compensation_records WHERE tenant=\? ORDER BY seq",
        "SELECT record FROM compensation_records WHERE ?<>'' ORDER BY seq",
    ),
    ("store: reserve is not idempotent", S, r"INSERT OR IGNORE INTO reservations", "INSERT OR REPLACE INTO reservations"),
    # ---- M9: egress
    ("egress: IBAN not checked", G, r"if BANK\.search\(clean\):", "if False:"),
    ("egress: bare IPv4 not checked", G, r"    for ip in IPV4\.findall\(no_urls\):", "    for ip in []:"),
    ("egress: spaced domain not folded", G, r"\|\(\?<=\\w\) \\\. \(\?=\[a-z\]\{2,\}\)", ""),
    (
        "write: check and write not one transaction",
        W,
        r"        with self\.store\.transaction\(\):\n            now = self\._now\(\)\n            if isinstance\(now, str\):\n                return _deny\(now\)\n            return self\._decide",
        "        if True:\n            now = self._now()\n            if isinstance(now, str):\n                return _deny(now)\n            return self._decide",
    ),
]
