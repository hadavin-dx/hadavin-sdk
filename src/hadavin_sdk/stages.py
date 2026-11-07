"""The stages, and the two questions every guard asks about one. A leaf module: it imports only the leaf
`commonwords` (a word list), so config, deferred, registry and app can all use it at the top of the file."""

from __future__ import annotations

import unicodedata

from hadavin_sdk.commonwords import COMMON_WORDS

# The stages, in order, and nothing else. A project's own labels map to one of these in the project's config; core
# tests the stage, never a label. The first stage had another name until the rename: config refuses that name at load.
STAGES = ("demo", "pilot", "prod")
# The three stages plus three more words that name a stage in other projects' configs (the last three below).
# tests/test_stage_names.py scans for all six as a stage value; tests/test_tenant_ids.py pins that this tuple and that
# scan agree. An id may not be spelled like any of them.
STAGE_WORDS = (*STAGES, "test", "development", "production")


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
    """The spelling a name is compared by: the redactor's canonical form (`guard.runmap.canonical`: Unicode NFKC, then
    invisible format characters, category Cf, removed), then case folded, then surrounding white space cut. The redactor
    stops after the Cf step; the case fold and the cut are added here. This module cannot import `canonical` (it is a
    leaf), so `tests/test_tenant_ids.py` pins that the two agree. In plain words: NFKC turns look-alike forms (a
    full-width `prod`, a roman-numeral letter) into plain letters; Cf characters are invisible (zero-width space, soft
    hyphen) and would otherwise hide a word; the case fold makes `Demo` and `PILOT` equal to `demo` and `pilot`. `Demo`,
    `PILOT`, a full-width `prod` and `demo` followed by a no-break space all fold to a stage. (No second NFKC after the
    case fold: no single code point whose fold is made of stage letters changes under it.) Not covered: other
    invisible or look-alike characters (variation selectors, Cyrillic letters that look Latin); the stage scan in
    tests/test_stage_names.py maps some of those, this function does not."""
    kept = "".join(
        c for c in unicodedata.normalize("NFKC", value) if unicodedata.category(c) != "Cf"
    )
    return kept.casefold().strip()


def is_stage_name(value: object) -> bool:
    """True when `value` is a string that folds (see `fold_name`) to demo, pilot or prod."""
    return isinstance(value, str) and fold_name(value) in STAGES


# Every word an id may not be: the stage words and every word on the redactor's common-word list.
REFUSED_ID_WORDS = frozenset(STAGE_WORDS) | COMMON_WORDS


def check_id(value: object, label: str = "an id") -> str:
    """Return an id unchanged; raise ValueError when it is not a string, when it is spelled like a stage word (STAGE_WORDS:
    the three stages and three more) or when it is a word on the redactor's common-word list
    (`commonwords.COMMON_WORDS`), each compared by `fold_name`. `label` is the phrase the error starts with ("a tenant id",
    "a customer id"). It covers the ids the redactor's label rule reads: tenant, org, organisation, organization,
    customer, account and user (guard/redact.py, the TENANT pattern).
    Why: the redactor's labelled rule masks the value in `tenant_id=prod` whatever the value is, so that copy is hidden
    even for a tenant named `prod`. What it does NOT do is sweep OTHER copies of a value on the common-word list (a bare
    `prod` elsewhere stays readable, because `HTTP 500 in prod` must), so an id that is one of those words would keep
    its unlabelled copies in clear. Refusing the words at registration closes that. The error does not echo the value;
    that holds inside a model that hides input in errors (`config._Strict`), a plain pydantic model prints
    `input_value=`. Every field that holds such an id uses a `config` id type in a `_Strict` model."""
    if isinstance(value, str):
        folded = fold_name(value)
        if folded in STAGE_WORDS:
            raise ValueError(
                f"{label} may not be a stage word ({', '.join(STAGE_WORDS)}; compared after NFKC and case folding)"
            )
        if folded in REFUSED_ID_WORDS:
            raise ValueError(
                f"{label} may not be a common word that the redactor does not sweep "
                "(the list is hadavin_sdk.commonwords.COMMON_WORDS; compared after NFKC and case folding)"
            )
        return value
    raise ValueError(f"{label} must be a string")


def check_tenant_id(value: object) -> str:
    """`check_id` for a tenant id."""
    return check_id(value, "a tenant id")
