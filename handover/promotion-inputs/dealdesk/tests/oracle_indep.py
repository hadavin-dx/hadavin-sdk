"""Second, independent test oracle for the Deal Desk approval policy.

Written from gate_rules.md (sections 3, 4, 5, 6.5, 15, 15.1), approval_matrix.json,
desk_policy.json and pricebook.json ALONE by a second author. No src/, no other
tests/ file and no data/gen.py was read. Stdlib only, pure functions, no I/O.

Ambiguities found in the spec, and the (conservative) reading taken:
 A1  R-091 (corrected wording): only EXACT listed ids pass; case/whitespace/Unicode
     variants, empty and non-string ids are DENY 091; exact repeats collapse to one
     (set semantics, so a repeated finance clause counts once for stacking);
     `clauses` not a list raises ValueError (Malformed).
 A2  "others" has no account_id; read: the caller already filtered by account.
 A3  R-080 "if several pooled quotes share a deal_id only the latest created_ts
     counts": read as de-duplicating AFTER the currency/state/age filter; on a
     created_ts tie the larger discount is kept (conservative).
 A4  Section 4/5: a blocked cell "blocks"; steps of the other cells are still
     computed and returned (the brief does not say they are emptied).
 A5  R-DEALDESK-018 counts a thin-margin cell, a downsell cell and clause cells
     only when they actually contain a finance step; blocked cells do not count.
 A6  Margin: net <= 0 is below_floor (spec: "net > 0" is part of the floor test).
 A7  counter_offer: "strictly below the exact floor discount" is read as the
     RATIONAL floor discount x = 10000 - 1e8*cogs/((10000-floor)*L); tested in
     integers as (10000-e)*(10000-floor)*L > 1e8*cogs. floor_max_bps is the
     largest integer bps whose ROUNDED-DOWN discount still meets the floor, so
     it can be larger than the exact floor discount. The ask is terms.discount_bps.
     "not blocked" = the base evaluation (no clauses, no cumulative) with
     discount_bps replaced by the edge has an empty blocked list.
 A8  Order of hand-back reasons is not stated in one place. Taken from the
     algorithm step order: suspicious_text; invalid_number (percent token);
     unsupported_fraction; invalid_number (price); no_number / multiple_numbers;
     ambiguous_terms last. (The brief lists ambiguous_terms before no_number.)
 A9  Quoted line = starts with '>' after stripping leading blanks. "On ... wrote:"
     must be a single line starting with "on" after the same stripping.
 A10 A sign directly attached to a percent token ("-20%", "10-20%") is invalid.
     "99.95%" not followed by uptime/availability is a normal discount token.
 A11 "$" means USD (no deal currency is known to trace). Currency comes BEFORE the
     amount; amounts with more than 2 decimals are invalid_number.
 A12 (RESOLVED) Billing: the spec says `billed monthly`, `billed quarterly`, ELSE annual/prepay/up front. First read as independent signals;
     the diff run showed gold e-011 and h-004 ('billed monthly instead of prepay') need the else chain, and the spec text says so.
 A13 Unknown tier / matrix key / matrix role = DENY R-DEALDESK-040 (fail closed).
 A14 Order of tax denies: unknown region or region/currency mismatch (082) is
     checked before the exemption claim (083). A malformed certificate date with
     a claim is 083. Clause validation (091) comes before tax (spec section 15).
 A15 accept_decision: person_id equality with the requester is treated like the
     same employee (R-087) as well; timestamps are ISO "...Z" strings.
 A16 Cumulative pool: "age <= window_days*86400" and future-dated quotes count.
     cum_bps is returned only when the cumulative rule applied (discount > 0 and
     at least one pooled other); otherwise None.
"""

import re
import unicodedata
from datetime import datetime
from decimal import Decimal

RULE = "R-DEALDESK-"
FMT = "%Y-%m-%dT%H:%M:%SZ"


def _ts(s):
    return (
        int(datetime.strptime(s, FMT).timestamp())
        if False
        else (datetime.strptime(s, FMT) - datetime(1970, 1, 1)).total_seconds()
    )


def _band_name(bps, matrix):
    if bps == 0:
        return "zero"
    for b in matrix["discount_bands"]:
        if b["max_bps"] >= bps and b["name"] != "zero":
            return b["name"]
    raise KeyError("bps")


def _size_band(list_total, ccy, matrix):
    bounds = matrix["size_bands"]["upper_bounds_minor"][ccy]
    names = matrix["size_bands"]["names"]
    for name, bound in zip(names, bounds):
        if list_total < bound:
            return name
    return names[-1]


def _rank(matrix, lane, role):
    return matrix["lanes"][lane].index(role)


def _merge(steps, cell, matrix):
    for lane, role in cell.items():
        if lane == "blocked":
            continue
        if lane not in steps or _rank(matrix, lane, role) > _rank(matrix, lane, steps[lane]):
            steps[lane] = role


def floor_max_bps(list_total, cogs, floor_bps):
    """Largest bps (0..10000) whose rounded-down discount keeps margin >= floor, net > 0."""
    if list_total <= 0:
        return 0
    need = max(1, -((-cogs * 10000) // (10000 - floor_bps)))  # min net, ceil
    if need > list_total:
        return 0
    return max(0, min(10000, ((list_total - need + 1) * 10000 - 1) // list_total))


def _base(deal, book, matrix, terms):
    """Section 5, R-010..R-018. Returns a dict (or raises KeyError on a bad matrix)."""
    ccy, plan, seats, yrs = deal["currency"], deal["plan"], deal["seats"], terms["term_years"]
    price = book["plans"][plan][ccy]
    list_total = price["list_seat"] * seats * yrs
    cogs = price["cogs_seat"] * seats * yrs
    bps = terms["discount_bps"]
    discount = list_total * bps // 10000
    net = list_total - discount
    floor = book["floor_bps"][plan]
    cells = matrix["cells"]
    size = _size_band(list_total, ccy, matrix)
    band = _band_name(bps, matrix)
    blocked, steps, fin = set(), {}, 0

    def take(cell, rid, counts=True):
        nonlocal fin
        if cell.get("blocked"):
            blocked.add(RULE + rid)
            return
        _merge(steps, cell, matrix)
        if counts and "finance" in cell:
            fin += 1

    take(cells["discount"][size][band], "010", counts=False)
    if bps > cells["tier_cap_bps"][deal["customer_tier"]]:
        blocked.add(RULE + "011")
    if net <= 0 or (net - cogs) * 10000 < floor * net:
        zone = "below_floor"
        blocked.add(RULE + "012")  # hard block regardless of matrix data
    elif (net - cogs) * 10000 < (floor + cells["margin"]["thin_band_bps"]) * net:
        zone = "thin"
        take(cells["margin"]["thin"], "012")
    else:
        zone = "healthy"
        take(cells["margin"]["healthy"], "012")
    take(cells["term_years"][str(yrs)], "013")
    take(cells["billing"][terms["billing"]], "014")
    take(cells["payment_terms_days"][str(terms["payment_terms_days"])], "015")
    take(cells["sla_tier"][terms["sla_tier"]], "016", counts=False)
    thr = cells["renewal_downsell"]["threshold_bps"]
    arr = int(deal["arr_minor"])
    downsell = deal["request_type"] == "renewal" and net * 10000 < arr * yrs * (10000 - thr)
    take(cells["renewal_downsell"]["over_threshold" if downsell else "none"], "017")
    return {
        "list_total": list_total,
        "discount": discount,
        "net": net,
        "cogs": cogs,
        "size": size,
        "band": band,
        "zone": zone,
        "blocked": blocked,
        "steps": steps,
        "fin": fin,
        "downsell": downsell,
        "floor": floor,
    }


def counter_offer(deal, book, matrix, terms):
    b = _base(deal, book, matrix, terms)
    cap = matrix["cells"]["tier_cap_bps"][deal["customer_tier"]]
    for e in (4000, 3000, 2000, 1000, 0):
        # e strictly below the exact (rational) floor discount, in integers
        if (10000 - e) * (10000 - b["floor"]) * b["list_total"] <= 10**8 * b["cogs"]:
            continue
        if e > cap or e >= terms["discount_bps"]:
            continue
        t = dict(terms, discount_bps=e)
        if _base(deal, book, matrix, t)["blocked"]:
            continue
        return e
    return None


def evaluate_full(
    deal, book, matrix, policy, terms, clauses, others, now, today, tax_exempt_claim=False, exemption_valid_until=None
):
    # (1) clause ids, R-091: must be a list; exact listed ids only; exact repeats collapse
    if not isinstance(clauses, list):
        raise ValueError("clauses must be a list")  # noqa: TRY004  (ValueError is the spec: Malformed)
    for c in clauses:
        if not isinstance(c, str) or not c or c not in policy["clauses"]:
            return {"deny": RULE + "091"}
    clauses = sorted(set(clauses))
    # (2) tax region and exemption, R-082 / R-083
    tax = policy["tax"]
    region = deal["tax_region"]
    if region not in tax["rates_bps"] or tax["region_currency"].get(region) != deal["currency"]:
        return {"deny": RULE + "082"}
    if tax_exempt_claim:
        ok = False
        if isinstance(exemption_valid_until, str):
            try:
                ok = datetime.strptime(exemption_valid_until, "%Y-%m-%d") >= datetime.strptime(today, "%Y-%m-%d")
            except ValueError:
                ok = False
        if not ok:
            return {"deny": RULE + "083"}
    # (3) base
    try:
        b = _base(deal, book, matrix, terms)
        cap = matrix["cells"]["tier_cap_bps"][deal["customer_tier"]]
        blocked, steps, fin = set(b["blocked"]), dict(b["steps"]), b["fin"]
        # (4) clause cells, R-090
        for c in clauses:
            cell = policy["clauses"][c]
            if cell.get("blocked"):
                blocked.add(RULE + "090")
            else:
                _merge(steps, cell, matrix)
                if "finance" in cell:
                    fin += 1
        # (5) cumulative, R-080 / R-081
        cum_bps = None
        if terms["discount_bps"] > 0:
            cfg = policy["cumulative"]
            limit = cfg["window_days"] * 86400
            n = _ts(now)
            latest = {}
            for o in others:
                if (
                    o["currency"] != deal["currency"]
                    or o["state"] not in cfg["open_states"]
                    or o["deal_id"] == deal["deal_id"]
                    or n - _ts(o["created_ts"]) > limit
                ):
                    continue
                k = (_ts(o["created_ts"]), o["discount"])
                if o["deal_id"] not in latest or k > latest[o["deal_id"]][0]:
                    latest[o["deal_id"]] = (k, o)
            pool = [v[1] for v in latest.values()]
            if pool:
                total_l = b["list_total"] + sum(o["list_total"] for o in pool)
                total_d = b["discount"] + sum(o["discount"] for o in pool)
                cum_bps = total_d * 10000 // total_l
                if cum_bps > cap:
                    blocked.add(RULE + "080")
                cell = matrix["cells"]["discount"][_size_band(total_l, deal["currency"], matrix)][_band_name(cum_bps, matrix)]
                if cell.get("blocked"):
                    blocked.add(RULE + "081")
                else:
                    _merge(steps, cell, matrix)
        # (6) stacking R-018 and merge
        if fin >= matrix["stacking"]["finance_cfo_at"]:
            steps["finance"] = matrix["lanes"]["finance"][-1]
        ordered = [[ln, steps[ln]] for ln in matrix["lane_order"] if ln in steps]
    except KeyError:
        return {"deny": RULE + "040"}
    t = (b["net"] * tax["rates_bps"][region] + 5000) // 10000
    if tax_exempt_claim:
        t = 0
    return {
        "deny": None,
        "list_total": b["list_total"],
        "discount": b["discount"],
        "net": b["net"],
        "tax_minor": t,
        "total": b["net"] + t,
        "size_band": b["size"],
        "discount_band": b["band"],
        "zone": b["zone"],
        "blocked": sorted(blocked),
        "steps": ordered,
        "cum_bps": cum_bps,
        "downsell": b["downsell"],
    }


def accept_decision(
    *,
    state,
    sig_ok,
    approver,
    requester,
    accepted_employees,
    lane,
    min_role,
    matrix,
    quote_hash_ok,
    snapshot_ok,
    request_ts,
    receipt_ts,
):
    if state != "open":
        return False, RULE + "022"
    if not sig_ok:
        return False, RULE + "022"
    if approver is None:
        return False, RULE + "022"
    if not approver.get("active"):
        return False, RULE + "087"
    roles = matrix["lanes"].get(lane, [])
    if approver["role"] not in roles or min_role not in roles or roles.index(approver["role"]) < roles.index(min_role):
        return False, RULE + "022"
    if approver["employee_id"] == requester["employee_id"] or approver["person_id"] == requester["person_id"]:
        return False, RULE + "087"
    if approver["employee_id"] in accepted_employees:
        return False, RULE + "087"
    if not (quote_hash_ok and snapshot_ok):
        return False, RULE + "085"
    delta = _ts(receipt_ts) - _ts(request_ts)
    if not (0 <= delta <= matrix["approval_ttl_hours"] * 3600):
        return False, RULE + "023"
    return True, None


# ---------------------------------------------------------------- traceability
_BIDI = {chr(c) for c in list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A))}
_UNITS = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
_TEENS = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_WORD = {w: i + 1 for i, w in enumerate(_UNITS)}
_WORD.update({w: 10 + i for i, w in enumerate(_TEENS)})
_WORD.update({w: 20 + 10 * i for i, w in enumerate(_TENS)})
_WORD["zero"] = 0
_SPELLED = re.compile(
    r"\b(one hundred|(?:%s)(?:[- ](?:%s))?|%s|%s|zero)\b[ \t]*(?:%%|percent\b|per[ \t]+cent\b)"  # noqa: UP031
    % ("|".join(_TENS), "|".join(_UNITS), "|".join(reversed(_TEENS)), "|".join(_UNITS))
)
_PCT = re.compile(r"([+\-]?)(?=[0-9.,]*[0-9])([0-9.,]+)[ \t]*(%|percent\b|per[ \t]+cent\b)")
_PCT_OK = re.compile(r"[0-9]{1,3}(\.[0-9]{1,2})?")
_PRICE = re.compile(
    r"(?:\b(usd|gbp|eur|cad|aud|pounds?|euros?)\b|(\$|£|€))[ \t]*(?=[0-9.,]*[0-9])([0-9.,]+)"
    r"[ \t]*(?:per[ \t]+seat|/[ \t]*seat|per[ \t]+user|each)\b"
)
_PRICE_OK = re.compile(r"([0-9]{1,3}(,[0-9]{3})+|[0-9]+)(\.[0-9]{1,2})?")
_CCY = {
    "usd": "USD",
    "gbp": "GBP",
    "eur": "EUR",
    "cad": "CAD",
    "aud": "AUD",
    "$": "USD",
    "£": "GBP",
    "€": "EUR",
    "pound": "GBP",
    "pounds": "GBP",
    "euro": "EUR",
    "euros": "EUR",
}
_UNSUPPORTED = re.compile(
    r"\b(?:thirds?|fifths?|sixths?|sevenths?|eighths?|ninths?|tenths?|quarters)[- ]off\b"
    r"|\b[0-9]+[ \t]*/[ \t]*[0-9]+[ \t]*off\b"
)
_NOTERMS = {"term_years": None, "payment_terms_days": None, "billing": None, "sla_tier": None}


def _hand(reason):
    return {"status": "hand_back", "reason": reason, "discount_bps": None, "price": None, "terms": dict(_NOTERMS)}


def _clean(text):
    if any(ch in _BIDI for ch in text):
        return None
    t = unicodedata.normalize("NFKC", text)
    t = "".join(ch for ch in t if ch in "\n\t" or unicodedata.category(ch) not in ("Cc", "Cf")).lower()
    out = []
    for line in t.split("\n"):
        if re.match(r"\s*on\b.*\bwrote:\s*$", line):
            break
        if line.lstrip().startswith(">"):
            continue
        out.append(line)
    return "\n".join(out)


def _one(found, mapping, key):
    vals = {mapping(m) for m in found}
    return vals


def trace(text):
    t = _clean(text)
    if t is None:
        return _hand("suspicious_text")
    cands = []  # A18 (resolved): one entry per MENTION, so '5% plus another 5%' is two figures
    for m in _PCT.finditer(t):
        if re.match(r"\s*(uptime|availability)\b", t[m.end() :]):
            continue  # SLA text
        if m.group(1) or not _PCT_OK.fullmatch(m.group(2)):
            return _hand("invalid_number")
        val = Decimal(m.group(2))
        if val > 100:
            return _hand("invalid_number")
        cands.append(("d", int(val * 100)))
    for m in _SPELLED.finditer(t):
        if re.match(r"\s*(uptime|availability)\b", t[m.end() :]):
            continue
        w = m.group(1)
        v = 100 if w == "one hundred" else sum(_WORD[p] for p in re.split(r"[- ]", w))
        cands.append(("d", v * 100))
    if re.search(r"\b(?:a |one )?half[- ]off\b", t):
        cands.append(("d", 5000))
    if re.search(r"\b(?:a |one )?quarter[- ]off\b", t):
        cands.append(("d", 2500))
    if _UNSUPPORTED.search(t):
        return _hand("unsupported_fraction")
    if re.search(r"\bno discount\b|\bzero discount\b|\bat list\b", t):
        cands.append(("d", 0))
    for m in _PRICE.finditer(t):
        amt = m.group(3)
        if not _PRICE_OK.fullmatch(amt):
            return _hand("invalid_number")
        cands.append(("p", _CCY[m.group(1) or m.group(2)], int(Decimal(amt.replace(",", "")) * 100)))
    if not cands:
        return _hand("no_number")
    if len(cands) > 1:
        return _hand("multiple_numbers")
    # terms
    w2n = {"1": 1, "2": 2, "3": 3, "one": 1, "two": 2, "three": 3}
    years = {w2n[m] for m in re.findall(r"\b(1|2|3|one|two|three)[- ]?years?\b", t)}
    pay = {int(x) for x in re.findall(r"\bnet[- ]?([0-9]+)\b", t)}
    bill = set()
    if re.search(r"\bbilled[ \t]+monthly\b", t):
        bill.add("monthly")
    if re.search(r"\bbilled[ \t]+quarterly\b", t):
        bill.add("quarterly")
    if not bill and re.search(r"\bannual|\bprepay|\bup[ -]?front\b", t):
        bill.add("annual_prepay")
    sla = set()
    if re.search(r"\benhanced\b|(?<![0-9.])99\.95(?![0-9])", t):
        sla.add("enhanced")
    if re.search(r"\bcustom sla\b|(?<![0-9.])99\.99(?![0-9])", t):
        sla.add("custom")
    if max(len(years), len(pay), len(bill), len(sla)) > 1:
        return _hand("ambiguous_terms")
    c = cands[0]
    return {
        "status": "ok",
        "reason": None,
        "discount_bps": c[1] if c[0] == "d" else None,
        "price": (c[1], c[2]) if c[0] == "p" else None,
        "terms": {
            "term_years": next(iter(years), None),
            "payment_terms_days": next(iter(pay), None),
            "billing": next(iter(bill), None),
            "sla_tier": next(iter(sla), None),
        },
    }
