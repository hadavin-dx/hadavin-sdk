"""The stages, and the two questions every guard asks about one. A leaf module: it imports nothing from this package,
so config, deferred, registry and app can all use it at the top of the file."""

from __future__ import annotations

# The stages, in order, and nothing else. A project's own labels map to one of these in the project's config; core
# tests the stage, never a label. The first stage had another name until the rename: config refuses that name at load.
STAGES = ("demo", "pilot", "prod")


def is_live(environment: object) -> bool:
    """True for pilot, prod and any value that is not a stage: only exactly the first stage (demo) is relaxed. The
    demo-only kinds, the loopback switch and the pilot-and-prod rules in app.py, deferred.py, registry.py and
    config.py ask this."""
    return environment != STAGES[0]


def is_prod(environment: object) -> bool:
    """True for prod and any value that is not a stage: only exactly demo and pilot are spared the prod-only rules
    (no local key file, a retention-agreed anchor). A value that slipped past config's check (model_copy and
    model_construct skip it) gets the strictest rules, never the pilot ones. Not a permission test: a rule that
    ALLOWS something in prod only must also require `environment in STAGES`."""
    return environment not in STAGES[:2]
