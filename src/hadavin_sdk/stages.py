"""The stages, and the two questions every guard asks about one. A leaf module: it imports nothing from this package,
so config, deferred, registry and app can all use it at the top of the file."""

from __future__ import annotations

import unicodedata

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


def fold_name(value: str) -> str:
    """The spelling both the redactor and the stage scan compare words by: Unicode NFKC, invisible format characters
    (category Cf) removed, case folded, surrounding white space cut. `Demo`, `PILOT`, a full-width `prod` and `demo`
    followed by a no-break space all fold to a stage. (No second NFKC after the case fold: no single code point whose
    fold is made of stage letters changes under it.)"""
    kept = "".join(
        c for c in unicodedata.normalize("NFKC", value) if unicodedata.category(c) != "Cf"
    )
    return kept.casefold().strip()


def is_stage_name(value: object) -> bool:
    """True when `value` is a string that folds (see `fold_name`) to demo, pilot or prod."""
    return isinstance(value, str) and fold_name(value) in STAGES


def check_tenant_id(value: object) -> str:
    """Return a tenant id unchanged; raise ValueError when its spelling is a stage name,
    TypeError when it is not a string. A tenant named like a stage would make the log line `tenant_id=prod` ambiguous with the stage value `prod`, which the redactor leaves
    readable on purpose; refusing the name keeps the two apart by construction, so no common word has to be masked.
    The error does not echo the value. Every field that holds a tenant id uses `config.TenantId`, which calls this."""
    if not isinstance(value, str):
        raise TypeError("a tenant id must be a string")
    if is_stage_name(value):
        raise ValueError(
            f"a tenant id may not be a stage name ({', '.join(STAGES)}; compared after NFKC and case folding)"
        )
    return value
