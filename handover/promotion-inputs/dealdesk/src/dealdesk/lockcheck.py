"""R-DEALDESK-095 / segregation (no-training setting): no live model run unless the provider's no-training setting is recorded with an explicit boolean, a real date, not in
the future and not stale. Format-only checks are not enough (refunds review minor 3)."""

from __future__ import annotations

from datetime import date


def live_run_allowed(lock: object, today: str, max_age_days: int) -> tuple[bool, str]:
    if not isinstance(lock, dict) or not isinstance(lock.get("provider_no_training"), dict):
        return False, "provider_no_training not recorded"
    p = lock["provider_no_training"]
    if set(p) != {"setting", "training_use", "checked_on"}:
        return False, "provider_no_training must hold exactly setting, training_use, checked_on"
    if not isinstance(p["setting"], str) or not p["setting"].strip() or p["training_use"] is not False:
        return False, "training_use must be the boolean false and the setting named"
    try:
        checked, now = date.fromisoformat(p["checked_on"]), date.fromisoformat(today)
    except (ValueError, TypeError):
        return False, "checked_on is not an ISO date"
    if checked > now:
        return False, "checked_on is in the future"
    if (now - checked).days > max_age_days:
        return False, "check is stale"
    return True, "ok"
