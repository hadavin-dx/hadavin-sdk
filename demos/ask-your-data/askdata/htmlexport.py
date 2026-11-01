"""Static HTML export (P5): one self-contained file, no script, no external fetch, light and dark CSS.

Every value is untrusted. It goes through `clean()` (A-11: ANSI removed, controls made visible) and then
`html.escape(quote=True)`, so it is plain text in the page. No Markdown or HTML is evaluated, no link is made.
"""

from __future__ import annotations

import html
import json
from typing import Any

from askdata.safe_text import clean

CSP = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"
CSS = """
:root{color-scheme:light dark;--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#d8d8d8;--head:#f3f3f3}
@media (prefers-color-scheme:dark){:root{--bg:#14161a;--fg:#e8e8e8;--mut:#9aa0a6;--line:#33363b;--head:#1d2025}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:2rem auto;max-width:72rem;padding:0 1rem}
h1{font-size:1.4rem}p.note{color:var(--mut)}
table{border-collapse:collapse;width:100%;margin:1rem 0}
th,td{border:1px solid var(--line);padding:.35rem .6rem;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{background:var(--head)}code,pre{font-family:ui-monospace,monospace;white-space:pre-wrap}
"""


def esc(value: object) -> str:
    return html.escape(clean(value, cell=True), quote=True)


def _page(title: str, note: str, body: str) -> str:
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
        f'<meta http-equiv="Content-Security-Policy" content="{html.escape(CSP)}">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{esc(title)}</title>\n<style>{CSS}</style></head><body>\n"
        f'<h1>{esc(title)}</h1>\n<p class="note">{esc(note)}</p>\n{body}</body></html>\n'
    )


def _table(columns: list[str], rows: list[list[object]]) -> str:
    head = "".join(f"<th>{esc(c)}</th>" for c in columns)
    body = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>\n" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>\n{body}</tbody></table>\n"


def _flat(v: object) -> str:
    if isinstance(v, dict) and "sha256" in v:
        return f"sha256:{v['sha256']} length:{v.get('length', '')}"
    return "" if v is None else str(v)


LEDGER_COLUMNS = [
    "query_id", "ts", "asker", "question", "outcome", "reason_code", "rule_id",
    "canonical_sql", "row_count", "cost_usd", "latency_ms", "alarm",
]  # fmt: skip


def render_ledger(rows: list[dict[str, Any]], *, redacted: bool) -> str:
    """The query ledger as one table. `rows` are ledger lines as dicts (already redacted unless opted in)."""
    cells = []
    for r in rows:
        fin = r.get("final") or {}
        cells.append([
            r["query_id"], r["ts"], r["asker"], _flat(r.get("question")), r["outcome"],
            r.get("reason_code") or "", r.get("rule_id") or "", _flat(fin.get("canonical_sql")),
            fin.get("row_count", ""), r["cost_usd"], r["latency_ms"], ";".join(r["alarm"]),
        ])  # fmt: skip
    note = (
        "Question and SQL text are redacted to a hash and a length."
        if redacted
        else "Question and SQL text are included."
    )
    note += f" {len(rows)} ledger line(s). Report only; not a warranty."
    return _page("askdata query ledger", note, _table(LEDGER_COLUMNS, cells))


def render_eval(rep: dict[str, Any]) -> str:
    """An eval `report.json` as a table of its headline numbers (every value shown as escaped text)."""
    cw = rep["confident_wrong"]
    adv = rep["adversarial"]
    ident = " / ".join(
        [
            str(rep.get("model_id", "")),
            str(rep.get("prompt_sha256", ""))[:12],
            str(rep.get("config_hash", ""))[:12],
        ]
    )
    rows: list[list[object]] = [
        ["Verdict", rep["verdict_text"]],
        ["Split / label", f"{rep['split']} / {rep['label']}"],
        ["Aborted", rep["aborted"] or "no"],
        [
            "Confident-wrong",
            f"{cw['x']} of {cw['n_answered']}; upper bound {rep['upper_error_bound']}",
        ],
        ["Hard zeros", json.dumps(rep["hard_zeros"], sort_keys=True)],
        ["pass@1 / k / pass^k", f"{rep['pass_rate']} / {rep['k']} / {rep['pass_k']}"],
        ["Adversarial", f"{adv['passed']} of {adv['n']} passed; failed {adv['failed_ids']}"],
        ["Cost (USD)", rep["cost_usd"]],
        ["Model / prompt / config", ident],
    ]
    note = (
        "A smoke result on synthetic data. It is not the accuracy of the product and does not "
        "transfer to a client database."
    )
    return _page(f"askdata eval: {rep['split']}", note, _table(["Item", "Value"], rows))
