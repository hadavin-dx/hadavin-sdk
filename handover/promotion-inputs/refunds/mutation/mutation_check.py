"""Stage-1 mutation check (rev 7). Copies the demo to a temp dir, breaks ONE thing (regex substitution), runs the default tests, and requires a failure.

    uv run --group test python mutation/mutation_check.py > mutation/RESULTS.txt

The harness strips the editable-install import hook so the mutated copy is the code under test (it asserts this). It runs only the DEFAULT test
run (tests/), which never opens the test split. Each line of the output: mutation | CAUGHT/SURVIVED | first failing test. Includes the extra
mutants a fresh reviewer wrote against rev 4 (X-series) and the mutants for every fix since. Stage 2 repeats the exercise against the real gate."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C, I, T, H, P, M, V, ID, G, R, N, PU = (
    "src/refunds/config.py",
    "src/refunds/identity.py",
    "src/refunds/textnorm.py",
    "src/refunds/hashing.py",
    "src/refunds/adapters/ports.py",
    "src/refunds/money.py",
    "src/refunds/verdict.py",
    "src/refunds/identities.py",
    "src/refunds/guards.py",
    "tests/reference.py",
    "src/refunds/namespace.py",
    "src/refunds/purposes.py",
)
GEN = "demo_only/data/gen.py"

# (name, file, regex, replacement). Regexes are searched once (re.subn count=1, DOTALL off).
MUTS = [
    ("cap: OVER_CAP uses >=", C, r"if request > lim\.hard_cap", "if request >= lim.hard_cap"),
    ("cap: ORDER_CAP uses >=", C, r"order_cum > lim\.hard_cap", "order_cum >= lim.hard_cap"),
    ("cap: CUSTOMER_CAP uses >=", C, r"customer_cum > lim\.customer_30d_cap", "customer_cum >= lim.customer_30d_cap"),
    (
        "cap: CUSTOMER_CAP branch removed",
        C,
        r'if customer_cum > lim\.customer_30d_cap:\s*return "CUSTOMER_CAP"',
        'if False:\n        return "CUSTOMER_CAP"',
    ),
    (
        "cap: ORDER_CAP branch removed",
        C,
        r'if order_cum > lim\.hard_cap:\s*return "ORDER_CAP"',
        'if False:\n        return "ORDER_CAP"',
    ),
    ("cap: goodwill above goodwill_cap allowed", C, r'if kind == "goodwill" and request > lim\.goodwill_cap:', "if False:"),
    (
        "tier: human boundary < instead of <=",
        C,
        r"if amount_minor <= lim\.one_approver_max:",
        "if amount_minor < lim.one_approver_max:",
    ),
    ("tier: cumulative basis ignored", C, r"max\(request, order_cum, customer_cum\)", "request"),
    ("tier: risk floor ignored", C, r"    if floor:\n", "    if False:\n"),
    (
        "tier: required_tier no longer refuses a capped request",
        C,
        r"if cap_decision\(currency, request, order_cum, customer_cum, kind\) is not None:",
        "if False:",
    ),
    ("elig: window < instead of <=", C, r"delivered_age_s <= RETURN_WINDOW_S", "delivered_age_s < RETURN_WINDOW_S"),
    ("elig: lateness >= instead of >", C, r"late_s > LATE_GRACE_S", "late_s >= LATE_GRACE_S"),
    (
        "elig: damaged outer age bound removed",
        C,
        r"if delivered_age_s is None or delivered_age_s > DAMAGE_MAX_AGE_S:",
        "if delivered_age_s is None:",
    ),
    ("elig: damaged accepted without an image", C, r'None if images >= 1 else "EVIDENCE_MISSING"', "None"),
    (
        "elig: cancel ignores the reason",
        C,
        r'status == "paid_unfulfilled" and reason == "cancel_before_ship"',
        'status == "paid_unfulfilled"',
    ),
    (
        "elig: reship without the shipped-status check",
        C,
        r'if reason != "not_delivered" or status != "shipped":',
        'if reason != "not_delivered":',
    ),
    (
        "floor: evidence floor excludes wrong_item",
        C,
        r'if reason in \("damaged", "wrong_item"\) and delivered_age_s is not None',
        'if reason in ("damaged",) and delivered_age_s is not None',
    ),
    (
        "floor: evidence floor removed",
        C,
        r'if reason in \("damaged", "wrong_item"\) and delivered_age_s is not None and delivered_age_s > RETURN_WINDOW_S',
        "if False",
    ),
    ("floor: repeat count > instead of >=", C, r"repeat_count >= REPEAT_REFUND_COUNT", "repeat_count > REPEAT_REFUND_COUNT"),
    (
        "floor: address signal < instead of <=",
        C,
        r"address_changed_age_s <= ADDRESS_CHANGE_SIGNAL_S",
        "address_changed_age_s < ADDRESS_CHANGE_SIGNAL_S",
    ),
    (
        "basis: whole-order allowed after a prior refund",
        C,
        r'if basis == "remaining_refundable" and tool == "refund" and prior_refunded > 0:',
        "if False:",
    ),
    (
        "basis: damaged also allows the whole-order basis",
        C,
        r'\("refund", "damaged"\): frozenset\(\{"line_total"\}\)',
        '("refund", "damaged"): frozenset({"line_total", "remaining_refundable"})',
    ),
    ("ttl: >= instead of >", C, r"return now_s - requested_s > APPROVAL_TTL_S", "return now_s - requested_s >= APPROVAL_TTL_S"),
    ("bucket: day bucket wrong slice", C, r"return proposal_clock_utc\[:10\]", "return proposal_clock_utc[:9]"),
    (
        "pending: cluster count > instead of >=",
        C,
        r"open_for_cluster >= MAX_PENDING_PER_CUSTOMER",
        "open_for_cluster > MAX_PENDING_PER_CUSTOMER",
    ),
    (
        "pending: sender count > instead of >=",
        C,
        r"open_for_sender >= MAX_PENDING_PER_SENDER",
        "open_for_sender > MAX_PENDING_PER_SENDER",
    ),
    ("flood: unapproved share // 2", C, r"store_day_cap // UNAPPROVED_SHARE_DEN", "store_day_cap // 2"),
    ("unknown: settle > instead of >=", C, r"t\[-1\] - t\[0\] >= SETTLE_DELAY_S", "t[-1] - t[0] > SETTLE_DELAY_S"),
    ("unknown: settle gap ignored", C, r"t\[-1\] - t\[0\] >= SETTLE_DELAY_S", "True"),
    ("unknown: escalation >= instead of >", C, r"unknown_age_s > UNKNOWN_ESCALATION_S", "unknown_age_s >= UNKNOWN_ESCALATION_S"),
    ("sweep: > instead of >=", C, r"since_last_sweep_s >= SWEEP_INTERVAL_S", "since_last_sweep_s > SWEEP_INTERVAL_S"),
    (
        "rate: deny rate >= instead of >",
        C,
        r"denies_last_hour > DENY_RATE_PER_SENDER_HOUR",
        "denies_last_hour >= DENY_RATE_PER_SENDER_HOUR",
    ),
    ("goodwill: window < instead of <=", C, r"a <= GOODWILL_WINDOW_S", "a < GOODWILL_WINDOW_S"),
    (
        "goodwill: cluster window removed",
        C,
        r"return any\(a <= GOODWILL_WINDOW_S for a in ages_of_executed_goodwill_s\)",
        "return False",
    ),
    ("cooldown: < instead of <=", C, r"rejected_age_s <= REJECTED_COOLDOWN_S", "rejected_age_s < REJECTED_COOLDOWN_S"),
    ("exposure window: < instead of <=", C, r"age_s <= EXPOSURE_WINDOW_S", "age_s < EXPOSURE_WINDOW_S"),
    ("const: APPROVAL_TTL 24h -> 48h", C, r"APPROVAL_TTL_S = 24 \* 3600", "APPROVAL_TTL_S = 48 * 3600"),
    ("const: SETTLE_DELAY 120 -> 0", C, r"SETTLE_DELAY_S = 120", "SETTLE_DELAY_S = 0"),
    ("const: EXPOSURE_WINDOW 30d -> 31d", C, r"EXPOSURE_WINDOW_S = 30 \* DAY_S", "EXPOSURE_WINDOW_S = 31 * DAY_S"),
    ("const: MAX_PENDING_PER_CUSTOMER 3 -> 4", C, r"MAX_PENDING_PER_CUSTOMER = 3", "MAX_PENDING_PER_CUSTOMER = 4"),
    ("const: MAX_PENDING_PER_SENDER 3 -> 4", C, r"MAX_PENDING_PER_SENDER = 3", "MAX_PENDING_PER_SENDER = 4"),
    ("const: GOODWILL_WINDOW 90d -> 60d", C, r"GOODWILL_WINDOW_S = 90 \* DAY_S", "GOODWILL_WINDOW_S = 60 * DAY_S"),
    ("const: LATE_GRACE 7d -> 6d", C, r"LATE_GRACE_S = 7 \* DAY_S", "LATE_GRACE_S = 6 * DAY_S"),
    ("const: RETURN_WINDOW 30d -> 31d", C, r"RETURN_WINDOW_S = 30 \* DAY_S", "RETURN_WINDOW_S = 31 * DAY_S"),
    ("const: REPEAT_REFUND_COUNT 3 -> 4", C, r"REPEAT_REFUND_COUNT = 3", "REPEAT_REFUND_COUNT = 4"),
    ("const: REJECTED_COOLDOWN 3600 -> 60", C, r"REJECTED_COOLDOWN_S = 3600", "REJECTED_COOLDOWN_S = 60"),
    ("const: UNKNOWN_ESCALATION 4h -> 8s", C, r"UNKNOWN_ESCALATION_S = 4 \* 3600", "UNKNOWN_ESCALATION_S = 8"),
    ("const: SWEEP_INTERVAL 300 -> 600", C, r"SWEEP_INTERVAL_S = 300", "SWEEP_INTERVAL_S = 600"),
    ("const: DENY_RATE 5 -> 10", C, r"DENY_RATE_PER_SENDER_HOUR = 5", "DENY_RATE_PER_SENDER_HOUR = 10"),
    ("const: UNAPPROVED_SHARE_DEN 4 -> 2", C, r"UNAPPROVED_SHARE_DEN = 4", "UNAPPROVED_SHARE_DEN = 2"),
    ("const: MAX_RETRIES 2 -> 3", C, r"MAX_RETRIES = 2", "MAX_RETRIES = 3"),
    (
        "limits: USD customer cap back to the hard cap",
        C,
        r'"USD": Limits\(7500, 50000, 2500, 1500, 30000, 250000\)',
        '"USD": Limits(7500, 50000, 2500, 1500, 50000, 250000)',
    ),
    (
        "limits: GBP hard cap changed",
        C,
        r"Limits\(6000, 40000, 2000, 1200, 24000, 200000\)",
        "Limits(6000, 41000, 2000, 1200, 24000, 200000)",
    ),
    (
        "limits: AUD goodwill amount changed",
        C,
        r"Limits\(11000, 75000, 3800, 2200, 45000, 375000\)",
        "Limits(11000, 75000, 3800, 2300, 45000, 375000)",
    ),
    (
        "matrix: four_eyes approver order swapped",
        C,
        r'"four_eyes": \["support_lead", "finance_approver"\]',
        '"four_eyes": ["finance_approver", "support_lead"]',
    ),
    ("tables: CUSTOMER_CAP mapped to rule 003", C, r'"CUSTOMER_CAP": "R-REF-005"', '"CUSTOMER_CAP": "R-REF-003"'),
    ("tables: ARG_CURRENCY_MISMATCH removed from the rule table", C, r'"ARG_CURRENCY_MISMATCH": "R-REF-010",', ""),
    ("tables: FRAUD_HOLD queue removed", C, r'"FRAUD_HOLD": "fraud_review",', ""),
    ("tables: ORDER_CAP queue removed", C, r'"ORDER_CAP": "owner_queue",', ""),
    ("tables: dispute hand-back routed to support", C, r'"dispute_or_legal": "dispute_queue"', '"dispute_or_legal": "support"'),
    ("tables: hand-back queue missing", C, r'"execution_refused": "finance",', ""),
    (
        "input guard: currency not checked in _check",
        C,
        r"if not isinstance\(currency, str\) or currency not in LIMITS:",
        "if False:",
    ),
    ("input guard: non-positive amounts allowed", C, r"or a <= 0 for a in amounts", "or False for a in amounts"),
    ("identity: '+a@x.com' folded to '@x.com'", I, r"folded or local", "folded"),
    ("identity: plus alias not folded", I, r'local\.split\("\+", 1\)\[0\]', "local"),
    ("identity: ownership local part case-insensitive", I, r"la == lb", "la.casefold() == lb.casefold()"),
    ("identity: ownership domain case-sensitive", I, r"da\.casefold\(\) == db\.casefold\(\)", "da == db"),
    (
        "identity: ship key without minimum components",
        I,
        r"if len\(street\) < 2 or not any\(any\(ch\.isdigit\(\) for ch in t\) for t in street\) or not pc or not cc:",
        "if False:",
    ),
    ("identity: ship key needs no postcode", I, r" or not pc or not cc:", " or not cc:"),
    ("identity: ship-to link applied to strong_only clusters", I, r"if not strong_only:", "if True:"),
    ("identity: short fingerprints usable", I, r"fp-\[0-9a-f\]\{10,64\}", r"fp-[0-9a-f]{1,64}"),
    ("identity: oversized uses >=", I, r"if n > limit", "if n >= limit"),
    ("text: NFKC before dropping marks", T, r'unicodedata\.normalize\("NFKD", text\)', 'unicodedata.normalize("NFKC", text)'),
    ("text: format characters kept", T, r'    "Cf",\n', ""),
    ("text: combining marks kept", T, r'    "Mn",\n', ""),
    ("text: short markers lose letter boundaries", T, r"\(\?<!\[\^\\W\\d_\]\)", "(?<!\\w)"),
    ("text: marker threshold 12 -> 3", T, r"if len\(m\) < 12:", "if len(m) < 3:"),
    ("text: tag characters not decoded", T, r"for ch in text if 0xE0020 <= ord\(ch\) <= 0xE007E", "for ch in text if False"),
    ("hash: tool not bound", H, r'\n\s*"tool": tool,', ""),
    ("hash: args not bound", H, r'\n\s*"args": args,', ""),
    ("hash: tier not bound", H, r'\n\s*"tier": tier,', ""),
    ("hash: basis snapshot not bound", H, r'\n\s*"basis": basis_snapshot,', ""),
    ("hash: key not bound", H, r'\n\s*"key": key,', ""),
    ("hash: customer id not bound", H, r'\n\s*"customer_id": customer_id,', ""),
    ("hash: request time not bound", H, r'\n\s*"requested_at": requested_at,', ""),
    ("hash: keys not sorted", H, r"sort_keys=True", "sort_keys=False"),
    ("key: line ids unsorted", P, r"sorted\(line_ids\)", "line_ids"),
    (
        "key: ids not validated (uppercase ok)",
        P,
        r'_ID = re\.compile\(r"\[a-z0-9-\]\{1,40\}"\)',
        '_ID = re.compile(r"[A-Za-z0-9-]{1,40}")',
    ),
    ("key: amount and currency not validated", P, r"        parse_minor\(amount_minor, currency\)", "        pass"),
    ("key: duplicate line ids allowed", P, r" or len\(set\(line_ids\)\) != len\(line_ids\)", ""),
    ("key: line-bearing action without lines allowed", P, r"if action in LINE_BEARING and not line_ids:", "if False:"),
    ("key: currency left out of the key", P, r"\|\{amount_minor\}\|\{currency\}", "|{amount_minor}"),
    ("money: leading zero accepted", M, r"\[1-9\]\[0-9\]\{0,11\}", "[0-9]{1,12}"),
    ("money: 13 digits accepted", M, r"\{0,11\}", "{0,12}"),
    ("money: bad currency raises TypeError", M, r"not isinstance\(currency, str\) or ", ""),
    ("verdict: scripted may be green", V, r'if mode == "scripted" and v == "green":', "if False:"),
    ("verdict: amber limit 0.15 -> 0.30", V, r"AMBER_MAX = 0\.15", "AMBER_MAX = 0.30"),
    ("verdict: hard zero does not abort", V, r'    if hard_zero_hit:\n        return "aborted"\n', ""),
    ("verdict: two-sided uses the one-sided tail", V, r"tail = alpha / 2 if two_sided else alpha", "tail = alpha"),
    ("verdict: default confidence 0.90", V, r"confidence: float = 0\.95", "confidence: float = 0.90"),
    ("identities: agent runtime may reserve", ID, r'"allow": _MODEL_REQUESTS,', '"allow": _MODEL_REQUESTS | {"reserve"},'),
    (
        "identities: executor may append to the audit chain",
        ID,
        r'"orders\.reship",\n\s*"helpdesk\.add_note",',
        '"orders.reship", "helpdesk.add_note", "audit.append",',
    ),
    (
        "identities: approver may execute",
        ID,
        r'"allow": frozenset\(\{"approve", "approvals\.read_pending"\}\),',
        r'"allow": frozenset({"approve", "approvals.read_pending", "execute_approved"}),',
    ),
    (
        "identities: sweeper may refund",
        ID,
        r'"allow": frozenset\(\{"approvals\.read", "release"\}\),',
        '"allow": frozenset({"approvals.read", "release", "payments.refund"}),',
    ),
    ("guards: rate cap lets one extra through", G, r"if self\._tokens < 1\.0:", r"if self._tokens < 0.0:"),
    (
        "guards: read log accepts non-purpose fields",
        G,
        r"if unknown:\n\s*raise PermissionError",
        "if False:\n            raise PermissionError",
    ),
    (
        "guards: egress recipient not checked",
        G,
        r"if not verified_email or not same_verified_address\(recipient, verified_email\):",
        "if False:",
    ),
    ("guards: egress links not checked", G, r"if u\.rstrip\(\"\.,;\)\"\)\.casefold\(\) not in links:", "if False:"),
    ("namespace: cross-client access allowed", N, r"parts\[0\] != self\.client_id or ", r""),
    (
        "purposes: order notes leak into the model view",
        PU,
        r'"order\.goodwill_minor": order\["goodwill_minor"\],',
        '"order.goodwill_minor": order["goodwill_minor"], "order.notes": order["notes"],',
    ),
    (
        "purposes: customer name leaks into the model view",
        PU,
        r'"ticket\.tags": list\(ticket\.get\("tags", \[\]\)\),',
        '"ticket.tags": list(ticket.get("tags", [])), "ticket.customer_name": ticket.get("customer_name"),',
    ),
    (
        "gen: forgets executed reship/goodwill in the cumulative",
        GEN,
        r'\n\s*out \+= \[\(_age_s\(a\["ts"\]\), int\(a\["amount_minor"\]\)\) for a in o\["other_actions"\]\]',
        "",
    ),
    ("gen: exposure summed across currencies", GEN, r"and \(currency is None or o\[\"currency\"\] == currency\)", "and True"),
    ("ref: authority compare runs BEFORE the ledger (true reorder)", R, r"s_ledger,\s*s_authority", "s_authority, s_ledger"),
    ("ref: lines-validity step dropped", R, r"s_lines,\s*s_ledger", "s_ledger"),
    ("ref: fraud step dropped", R, r"s_fraud,\s*s_money", "s_money"),
    ("ref: order cap lost", R, r"\n    if c\.order_cum > hard:\n        return \"ORDER_CAP\"", ""),
    (
        "ref: compensation check for refunds lost",
        R,
        r'if tool == "refund" and any\(i in reship for i in covered\):',
        r"if False:",
    ),
    (
        "ref: compensation check for reships lost",
        R,
        r'if tool == "reship" and any\(i in reship or i in refund for i in covered\):',
        r"if False:",
    ),
    (
        "ref: goodwill cluster window lost",
        R,
        r'if any\(k == "goodwill" and ag <= 90 \* DAY for ag, _, k in executed\(c\.world, c\.strong, c\.cur\)\):',
        r"if False:",
    ),
    ("ref: exposure summed across currencies", R, r'and o\["currency"\] == currency', "and True"),
    (
        "ref: weak links carry the fraud flag",
        R,
        r"c\.strong = cluster\(c\.world, c\.cust\[\"customer_id\"\], True\)",
        'c.strong = cluster(c.world, c.cust["customer_id"], False)',
    ),
    (
        "ref: ownership by folded email",
        R,
        r"same_address\(x\[\"email\"\], t\[\"verified_sender_email\"\]\)",
        'fold_email(x["email"]) == fold_email(t["verified_sender_email"])',
    ),
    ("ref: dispute tags case-sensitive", R, r"norm_tag\(x\) in DISPUTE_TAGS", r"x in DISPUTE_TAGS"),
    ("ref: key-validity step dropped", R, r"s_key,\s*s_pending", "s_pending"),
    ("ref: pending-cap step dropped", R, r"s_key,\s*s_pending,?\s*\]", "s_key]"),
    # ---- rev 6 (fresh review of rev 5) ----
    (
        "ref: tenant scope fail-open (unknown tenant accepted)",
        R,
        r'need\(is_str\(tenant\) and tenant in \{r\["tenant_id"\] for r in tagged\}, "unknown or missing tenant id"\)',
        "pass",
    ),
    (
        "ref: records without tenant id tolerated",
        R,
        r'need\(len\(tagged\) == len\(world\["customers"\]\) \+ len\(world\["orders"\]\), "records without a tenant id in a multi-tenant world"\)',
        "pass",
    ),
    (
        "ref: executed cancel does not compensate lines",
        R,
        r'    if tool in \("refund", "reship"\) and cancel:\n        return "LINE_COMPENSATED"\n',
        "",
    ),
    (
        "ref: legacy action with no line ids covers nothing",
        R,
        r'covered = set\(a\["line_ids"\]\) or every',
        'covered = set(a["line_ids"])',
    ),
    (
        "ref: alias email is a strong link",
        R,
        r"        if not strong:\n            if fold_email",
        "        if True:\n            if fold_email",
    ),
    (
        "ref: unverified email counts as strong exact link",
        R,
        r'c\.get\("email_verified"\) is True and exact_email',
        "exact_email",
    ),
    (
        "ref: goodwill window uses the weak cluster",
        R,
        r'executed\(c\.world, c\.strong, c\.cur\)\):\n            return "GOODWILL_ALREADY"',
        'executed(c.world, c.weak, c.cur)):\n            return "GOODWILL_ALREADY"',
    ),
    (
        "cfg: blocked tier reintroduced",
        C,
        r'_ORDER = \{"human": 0, "four_eyes": 1\}',
        '_ORDER = {"human": 0, "four_eyes": 1, "blocked": 2}',
    ),
    (
        "cfg: malformed dispute tags read as no dispute",
        C,
        r'    if not isinstance\(tags, list\) or not all\(isinstance\(t, str\) for t in tags\):\n        raise GateInputError\("TAGS_MALFORMED"\)\n',
        "    if not isinstance(tags, list):\n        return False\n",
    ),
    ("cfg: dispute tags not normalised", C, r"textnorm\.normalise\(t\) in DISPUTE_TAGS", "t in DISPUTE_TAGS"),
    (
        "cfg: live run accepts a future check date",
        C,
        r"return 0 <= \(today - checked\)\.days <= LIVE_CHECK_MAX_AGE_DAYS",
        "return (today - checked).days <= LIVE_CHECK_MAX_AGE_DAYS",
    ),
    (
        "cfg: live run accepts a stale check date",
        C,
        r"return 0 <= \(today - checked\)\.days <= LIVE_CHECK_MAX_AGE_DAYS",
        "return 0 <= (today - checked).days",
    ),
    ("cfg: live run ignores training_use", C, r" or p\.get\(\"training_use\"\) is not False", ""),
    ("cfg: live run accepts empty setting text", C, r' or not str\(p\.get\("setting", ""\)\)\.strip\(\)', ""),
    (
        "identity: plus-alias is a strong link",
        I,
        r'        if not strong_only:\n            keys \+= \[\("alias-email", canonical_email\(a\["email"\]\)\), \("ship", a\["ship_to"\]\)\]',
        '        keys.append(("alias-email", canonical_email(a["email"])))\n        if not strong_only:\n            keys.append(("ship", a["ship_to"]))',
    ),
    ("identity: unverified exact email merges", I, r'if a\.get\("email_verified"\) and exact_email', "if exact_email"),
    ("identity: fingerprint shape not validated", I, r" or _FP\.fullmatch\(fp\) is None", ""),
    ("identity: low-entropy fingerprint accepted", I, r"return len\(set\(body\)\) >= 5 and not body\.isdigit\(\)", "return True"),
    ("identity: all-digit fingerprint accepted", I, r"len\(set\(body\)\) >= 5 and not body\.isdigit\(\)", "len(set(body)) >= 5"),
    (
        "guards: rate cap refills a full bucket (boundary burst doubles)",
        G,
        r"self\._tokens = min\(float\(self\.max_per_s\), self\._tokens \+ \(now_s - self\._last\) \* self\.max_per_s\)",
        "self._tokens = float(self.max_per_s)",
    ),
    (
        "guards: rate cap backwards clock refills",
        G,
        r"if self\._last is not None and now_s > self\._last:",
        "if self._last is not None:",
    ),
    (
        "guards: connection cap off by one",
        G,
        r"if self\.connections >= self\.max_connections:",
        "if self.connections > self.max_connections:",
    ),
    ("guards: egress bare domains not checked", G, r"    for d in DOMAIN\.findall\(no_urls\):", "    for d in []:"),
    ("guards: egress attachment always allowed", G, r"        if a not in allowed_attachments:", "        if False:"),
    ("textnorm: spaced form not checked", T, r"normalise_spaced\(output\)", "normalise(output)"),
    ("textnorm: Hangul filler not dropped", T, r"_FILLERS = \{[^}]*\}", "_FILLERS = set()"),
    (
        "identities: breakglass holds a standing allow",
        ID,
        r'"allow": frozenset\(\),\n        "why": \{\},',
        '"allow": frozenset({"approvals.approve"}),\n        "why": {},',
    ),
    ("verdict: zero-wrong bound accepts n=0", V, r"n_answered < 1", "n_answered < 0"),
    ("verdict: zero-wrong bound accepts bool n", V, r" or isinstance\(n_answered, bool\)", ""),
    (
        "verdict: zero-wrong bound accepts confidence 1",
        V,
        r"or not 0 < confidence < 1:\n        raise ValueError\(\"need n_answered",
        'or False:\n        raise ValueError("need n_answered',
    ),
    ("namespace: dot-dot part allowed", N, r'any\(p in \("", ".", ".."\) for p in parts\)', "False"),
    ("namespace: backslash allowed", N, r' or "\\\\" in full_key', ""),
    (
        "ref: refunds[] line with a zero counter tolerated (sources may disagree)",
        R,
        r'all\(line_refunded\.get\(i, 0\) > 0 for i in f\["line_ids"\]\),',
        "True,",
    ),
    (
        "ref: sum(refunds) vs refunded_minor not cross-checked",
        R,
        r'need\(total == int\(o\["refunded_minor"\]\), "sum\(refunds\) != refunded_minor \(sources disagree\)"\)',
        "pass",
    ),
    (
        "cfg: live run date not read from the lock",
        C,
        r'date\.fromisoformat\(str\(p\.get\("checked_on", ""\)\)\)',
        'date.fromisoformat("2026-11-01")',
    ),
]

# ---- rev 7: curate the list (design review 6, M10) -------------------------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mutants_review7 import DROPPED_COVERED_BY, RETIRED
from mutants_review7 import NEW as NEW7
from mutants_review8 import NEW as NEW8
from mutants_review8 import REPLACED, RETIRED8
from mutants_review12 import NEW as NEW12
from mutants_write_path import NEW

# structural / naming-only mutants and mutants of code that no longer exists are dropped; duplicates are dropped by (file, pattern, replacement)
DROPPED: set[str] = set()  # stale definitions were deleted in rev 9
KIND_CONSTANT = "const:"  # owner-default pins: change detectors by design, reported apart from logic mutants


def curated():
    old = [m for m in [*MUTS, *NEW] if m[0] not in DROPPED and m[0] not in RETIRED and m[0] not in RETIRED8]
    seen, out = set(), []
    for m in [*old, *NEW7, *NEW8, *NEW12]:
        if m[0] in RETIRED8:
            continue
        if m[0] in REPLACED:  # rev 9: the line this mutant targeted was rewritten; use the restated pattern
            m = (m[0], *REPLACED[m[0]])
        sig = (m[1], m[2], m[3])
        if sig in seen:
            continue
        seen.add(sig)
        out.append(m)
    names = {m[0] for m in out}
    missing = {k: v for k, v in DROPPED_COVERED_BY.items() if v not in names}
    assert not missing, f"a dropped mutant's property is not covered by a live mutant: {missing}"
    return out


def _run_copy(name, rel, pat, new):
    """Copy the demo, optionally apply ONE mutation (rel None = baseline), run the default tests without -x. Returns (name, status, failing tests)
    with status SURVIVED | CAUGHT (at least one ASSERTION failure) | CRASH-ONLY (only exceptions/import errors failed: weak) | TIMEOUT."""
    tmp = tempfile.mkdtemp()
    try:
        dst = Path(tmp) / "demo"
        shutil.copytree(
            ROOT,
            dst,
            ignore=shutil.ignore_patterns(
                ".venv", "__pycache__", ".ruff_cache", ".pytest_cache", "mutation", "out", "tests_oneshot"
            ),
        )
        (dst / "tests" / "test_default_run_independent_of_test_split.py").unlink()  # slow, recursive; runs in the real suite
        if rel is not None:
            p = dst / rel
            text = p.read_text(encoding="utf-8")
            mutated, n = re.subn(pat, lambda _m: new, text, count=1)
            if n != 1:
                return name, "PATTERN NOT FOUND", []
            p.write_text(mutated, encoding="utf-8", newline="")
        src = str(dst / "src")
        code = (
            "import sys; sys.meta_path=[f for f in sys.meta_path if 'editable' not in repr(f).lower()]; "
            f"sys.path=[x for x in sys.path if not x.replace(chr(92), '/').endswith('refunds/src')]; sys.path.insert(0, {src!r}); "
            f"import refunds; assert refunds.__file__.startswith({str(dst)!r}), refunds.__file__; "
            "import pytest; sys.exit(pytest.main(['-q','-p','no:cacheprovider','-o','pythonpath=','--junitxml=j.xml','tests']))"
        )
        try:
            r = subprocess.run(
                [sys.executable, "-c", code], check=False, cwd=dst, capture_output=True, text=True, timeout=TIMEOUT_S
            )
        except subprocess.TimeoutExpired:
            return name, "TIMEOUT", []
        failing = _junit(
            dst / "j.xml"
        )  # [(test, message)]: the message starts with the exception type, so assertion kills and crashes are told apart
        if r.returncode == 0:
            return name, "SURVIVED", []
        if not failing:
            failing = [("<run>", "returncode " + str(r.returncode) + " " + (r.stdout.strip().splitlines() or ["?"])[-1][:100])]
        assertion = [f for f in failing if f[1].startswith(("AssertionError", "Failed:", "assert "))]
        return name, ("CAUGHT" if assertion else "CRASH-ONLY"), failing
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TIMEOUT_S = 420


def _junit(path):
    import xml.etree.ElementTree as ET

    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return []
    out = []
    for case in root.iter("testcase"):
        for kind in ("failure", "error"):
            for el in case.findall(kind):
                msg = (el.get("message") or "").strip()
                out.append(
                    (f"{case.get('classname', '')}::{case.get('name', '')}", ("<error> " if kind == "error" else "") + msg)
                )
    return out


def main():
    muts = curated()
    n_curated = len(muts)
    only = os.environ.get("MUT_ONLY")  # re-run a subset while fixing weak tests: MUT_ONLY="write:|approval:"
    if only == "@review7":  # the mutants written for review 7
        names7 = {m[0] for m in NEW7}
        muts = [m for m in muts if m[0] in names7]
    elif only == "@review8":  # the mutants written for review 8 plus the restated ones
        names8 = {m[0] for m in NEW8} | set(REPLACED)
        muts = [m for m in muts if m[0] in names8]
    elif only == "@review12":  # the mutants written for round 12
        names12 = {m[0] for m in NEW12}
        muts = [m for m in muts if m[0] in names12]
    elif only:
        muts = [m for m in muts if re.search(only, m[0])]
    base = _run_copy("BASELINE (unmutated copy)", None, None, None)
    if base[1] != "SURVIVED":  # a failing baseline would make every mutant look caught
        print("baseline run FAILED, results would be meaningless:", base[2][:5])
        return 2
    print("baseline: the unmutated copy passes the default tests (the slow independence test is run in the real suite)")
    with ThreadPoolExecutor(max_workers=int(os.environ.get("MUT_WORKERS", "2"))) as ex:
        rows = list(ex.map(lambda m: _run_copy(*m), muts))
    lines: dict[str, str] = {}
    for name, status, failing in rows:
        shown = "; ".join(f"{t.split('::')[-1]}" for t, _ in failing[:4]) + (" ..." if len(failing) > 4 else "")
        extra = f"{len(failing)} failing: {shown}" if failing else ""
        if status == "CRASH-ONLY":
            extra += " | reasons: " + "; ".join(sorted({r.split(":")[0][:30] for _, r in failing}))
        lines[name] = " | ".join(x for x in (name, status, extra) if x)
    merge = os.environ.get(
        "MUT_MERGE"
    )  # MUT_MERGE=<previous full-run file>: keep its rows, replace the re-run ones, recount here (never by hand)
    if merge:
        keep = {}
        for ln in Path(merge).read_text(encoding="utf-8").splitlines():
            if ln.startswith(("#", "baseline")) or not ln.strip():
                continue
            if ln.startswith(("logic mutants", "owner-default", "total unique")):
                break
            keep[ln.split(" | ")[0]] = ln
        live = {m[0] for m in curated()}
        keep = {k: v for k, v in keep.items() if k in live}  # rows of retired or renamed mutants drop out
        keep.update(lines)
        missing = sorted(live - set(keep))
        if missing:
            print("MERGE INCOMPLETE, rows missing:", missing)
            return 2
        lines = keep
        rows = [(k, v.split(" | ")[1], []) for k, v in keep.items()]
        print("# merged into the previous run; re-run in this invocation:", "; ".join(sorted(m[0] for m in muts)))
    for ln in lines.values():
        print(ln)
    const = [r for r in rows if r[0].startswith(KIND_CONSTANT)]
    logic = [r for r in rows if not r[0].startswith(KIND_CONSTANT)]
    print()
    count = lambda rs, s: sum(1 for r in rs if r[1] == s)
    print(
        f"logic mutants (unique): {len(logic)}: {count(logic, 'CAUGHT')} caught by an assertion, {count(logic, 'CRASH-ONLY')} crash-only, "
        f"{count(logic, 'TIMEOUT')} timeout, {count(logic, 'SURVIVED')} survived, {count(logic, 'PATTERN NOT FOUND')} pattern not found"
    )
    print(
        f"owner-default constant pins (change detectors by design, not logic evidence): {len(const)}: {count(const, 'CAUGHT')} caught by an assertion"
    )
    print(
        f"total unique mutants run: {len(rows)} (after dropping structural, stale and duplicate mutants: {len(MUTS) + len(NEW) + len(NEW7) + len(NEW8) + len(NEW12) - n_curated} dropped)"
    )
    bad = [r for r in rows if r[1] != "CAUGHT"]
    return 0 if not bad else 1


if __name__ == "__main__":
    os.chdir(ROOT)
    sys.exit(main())
