"""Test-side reference for the approval matrix: straight-line, integer-only, no shared code with the stage-2 gate.

Stage 1: checks that every gold label agrees with the matrix file (a mislabelled gold case is a classic failure).
Stage 2: the differential oracle for the property test (gate_rules == oracle on random requests).
"""

from __future__ import annotations


def money(deal: dict, book: dict, terms: dict) -> dict:
    p = book["plans"][deal["plan"]][deal["currency"]]
    seats, years = deal["seats"], terms["term_years"]
    list_total = p["list_seat"] * seats * years
    disc = list_total * terms["discount_bps"] // 10000  # floor: never more discount than stated
    net = list_total - disc
    cogs = p["cogs_seat"] * seats * years
    return {"list_total": list_total, "discount": disc, "net": net, "cogs": cogs}


def margin_zone(net: int, cogs: int, floor_bps: int, thin_bps: int) -> str:
    if net <= 0 or (net - cogs) * 10000 < floor_bps * net:
        return "below_floor"
    return "thin" if (net - cogs) * 10000 < (floor_bps + thin_bps) * net else "healthy"


def max_bps_at_floor(list_total: int, cogs: int, floor_bps: int) -> int:
    """Largest discount (bps of list) that still meets the floor; integer arithmetic only."""
    net_min = -(-cogs * 10000 // (10000 - floor_bps))  # ceil
    bps = (list_total - net_min) * 10000 // list_total
    while bps > 0 and not _ok(list_total, cogs, floor_bps, bps):
        bps -= 1
    while bps < 10000 and _ok(list_total, cogs, floor_bps, bps + 1):
        bps += 1
    return max(bps, 0)


def _ok(list_total: int, cogs: int, floor_bps: int, bps: int) -> bool:
    net = list_total - list_total * bps // 10000
    return net > 0 and (net - cogs) * 10000 >= floor_bps * net


def band_of(net: int, ccy: str, m: dict) -> str:
    b = m["size_bands"]["upper_bounds_minor"][ccy]
    return "s" if net < b[0] else "m" if net < b[1] else "l" if net < b[2] else "xl"


def dband_of(bps: int, m: dict) -> str:
    if bps == 0:
        return "zero"
    for band in m["discount_bands"][1:]:
        if bps <= band["max_bps"]:
            return band["name"]
    raise ValueError(bps)


def evaluate(deal: dict, book: dict, m: dict, terms: dict) -> dict:
    """Second implementation by the SAME author (transcription check, not an independent derivation). terms: fully resolved (discount_bps, term_years, billing, payment_terms_days, sla_tier)."""
    mo = money(deal, book, terms)
    c = m["cells"]
    band = band_of(mo["list_total"], deal["currency"], m)
    zone = margin_zone(mo["net"], mo["cogs"], book["floor_bps"][deal["plan"]], c["margin"]["thin_band_bps"])
    cells = [
        ("discount", f"{band}/{dband_of(terms['discount_bps'], m)}", c["discount"][band][dband_of(terms["discount_bps"], m)]),
        ("margin", zone, c["margin"][zone]),
        ("term_years", str(terms["term_years"]), c["term_years"][str(terms["term_years"])]),
        ("billing", terms["billing"], c["billing"][terms["billing"]]),
        ("payment_terms_days", str(terms["payment_terms_days"]), c["payment_terms_days"][str(terms["payment_terms_days"])]),
        ("sla_tier", terms["sla_tier"], c["sla_tier"][terms["sla_tier"]]),
    ]
    cap = c["tier_cap_bps"][deal["customer_tier"]]
    blocked = []
    if terms["discount_bps"] > cap:
        blocked.append("R-DEALDESK-011")
    downsell = deal["request_type"] == "renewal" and mo["net"] * 10000 < int(deal["arr_minor"]) * terms["term_years"] * (
        10000 - c["renewal_downsell"]["threshold_bps"]
    )
    cells.append(
        (
            "renewal_downsell",
            "over_threshold" if downsell else "none",
            c["renewal_downsell"]["over_threshold" if downsell else "none"],
        )
    )
    rid = {
        "discount": "010",
        "margin": "012",
        "term_years": "013",
        "billing": "014",
        "payment_terms_days": "015",
        "sla_tier": "016",
        "renewal_downsell": "017",
    }
    need: dict[str, str] = {}
    for dim, _key, cell in cells:
        if cell.get("blocked"):
            blocked.append("R-DEALDESK-" + rid[dim])
            continue
        for lane, role in cell.items():
            ranks = m["lanes"][lane]
            if lane not in need or ranks.index(role) > ranks.index(need[lane]):
                need[lane] = role
    if zone == "below_floor":
        blocked.append("R-DEALDESK-012")
    n_fin = sum(
        1
        for dim, _k, cell in cells
        if dim in ("margin", "term_years", "billing", "payment_terms_days", "renewal_downsell") and "finance" in cell
    )
    if n_fin >= m["stacking"]["finance_cfo_at"]:
        need["finance"] = "cfo"
    steps = [(lane, need[lane]) for lane in m["lane_order"] if lane in need]
    return {
        "money": mo,
        "band": band,
        "zone": zone,
        "blocked": sorted(set(blocked)),
        "steps": steps,
        "cap_bps": cap,
        "downsell": downsell,
        "max_bps_at_floor": max_bps_at_floor(mo["list_total"], mo["cogs"], book["floor_bps"][deal["plan"]]),
    }


def counter(deal: dict, book: dict, m: dict, terms: dict):
    """Largest discount-band edge (0,1000,..,4000) below the ask, <= floor max, <= tier cap, not blocked; else None."""
    mo = money(deal, book, terms)
    lim = min(
        max_bps_at_floor(mo["list_total"], mo["cogs"], book["floor_bps"][deal["plan"]]) - 1,
        m["cells"]["tier_cap_bps"][deal["customer_tier"]],
        terms["discount_bps"] - 1,
    )
    for e in (4000, 3000, 2000, 1000, 0):
        if e <= lim and not evaluate(deal, book, m, {**terms, "discount_bps": e})["blocked"]:
            return e
    return None
