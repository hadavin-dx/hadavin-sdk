"""Offline stand-in for the model (the spike has NO live model call and makes no network access).

`ScriptedModel` answers a few fixed questions with fixed SQL, including two that a real model could be tricked
into writing (a delete, a read of the restricted column), so the demo shows the validator refusing them. A live
adapter would implement the same `Model` protocol behind the core LLM kind; it is not built in the spike.
"""

from __future__ import annotations

from typing import Protocol


class Model(Protocol):
    name: str

    def complete(self, question: str) -> str | None:
        """SQL text for the question, or None to abstain."""


_SCRIPT = {
    "how many orders per country": (
        "SELECT c.country, count(*) AS orders FROM analytics.orders_v o "
        "JOIN analytics.customers_v c ON c.customer_id = o.customer_id GROUP BY c.country ORDER BY orders DESC"
    ),
    "what is the revenue by product category": (
        "SELECT p.category, round(sum(i.line_amount), 2) AS revenue FROM analytics.order_items_v i "
        "JOIN analytics.products_v p ON p.product_id = i.product_id GROUP BY p.category ORDER BY revenue DESC"
    ),
    "delete all cancelled orders": "DELETE FROM shop.orders WHERE status = 'cancelled'",
    "list every customer email": "SELECT email FROM analytics.customers_v",
    "list the customers": "SELECT customer_id, full_name, country FROM analytics.customers_v ORDER BY customer_id LIMIT 10",
}


class ScriptedModel:
    name = "scripted (offline, no API call)"

    def complete(self, question: str) -> str | None:
        return _SCRIPT.get(question.strip().lower().rstrip("?. "))


def questions() -> list[str]:
    return sorted(_SCRIPT)
