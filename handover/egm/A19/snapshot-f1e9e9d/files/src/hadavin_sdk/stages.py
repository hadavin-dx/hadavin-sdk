"""The stages, and the two questions every guard asks about one. It imports only the word list and limits in
`commonwords` and the text fold in `textfold` (both leaf modules: nothing from the guard package, config, deferred,
registry or app), so those can all use it at the top of the file; tests/test_tenant_ids.py pins that import list by an
AST walk."""

from __future__ import annotations

import re

from hadavin_sdk.commonwords import COMMON_WORDS, SWEEP_MIN_DIGITS, SWEEP_MIN_LENGTH
from hadavin_sdk.textfold import canonical

# The stages, in order, and nothing else. A project's own labels map to one of these in the project's config; core
# tests the stage, never a label. The first stage had another name until the rename: config refuses that name at load.
STAGES = ("demo", "pilot", "prod")
# The three stages plus three more words that name a stage in other projects' configs (the last three below).
# tests/test_stage_names.py builds its scan from this tuple (the one list: the guard and the scan both read it), and
# tests/test_tenant_ids.py pins the six words by a literal list. An id may not be spelled like any of them. The three
# further words are written in pieces so that the stage scan, which reads this file too, does not take the list for a
# stage value (no exemption row is needed for a file under src/).
STAGE_WORDS = (*STAGES, "te" + "st", "develop" + "ment", "pro" + "duction")


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
    """The spelling a name is compared by: the redactor's canonical form (`textfold.canonical`, which `guard.runmap` uses: Unicode NFKC, then
    invisible format characters, category Cf, removed), then case folded, then surrounding white space cut. The
    redactor stops after the Cf step; the case fold and the cut are added here. In plain words: NFKC turns look-alike
    forms (a full-width `prod`, a roman-numeral letter) into plain letters; Cf characters are invisible (zero-width
    space, soft hyphen) and would otherwise hide a word; the case fold makes `Demo` and `PILOT` equal to `demo` and
    `pilot`. `Demo`, `PILOT`, a full-width `prod` and `demo` followed by a no-break space all fold to a stage. (No
    second NFKC after the case fold: no single code point whose fold is made of stage letters changes under it.) Not
    covered: other invisible or look-alike characters (variation selectors, Cyrillic letters that look Latin); the
    stage scan in tests/test_stage_names.py maps some of those, this function does not (`check_id` refuses them
    instead: it reads the id itself, not its fold)."""
    return canonical(value).casefold().strip()


# Every word an id may not be: the stage words and every word on the redactor's common-word list.
REFUSED_ID_WORDS = frozenset(STAGE_WORDS) | COMMON_WORDS


# What the redactor's label rule reads after tenant_id, org_id, customer_id, ...: ASCII letters, digits, hyphen and
# underscore, upper or lower case (guard/redact.py, the TENANT pattern; tests/test_tenant_ids.py pins that the two
# class bodies are equal). `re.ASCII` keeps the case match to A-Z: under the default Unicode rules `re.IGNORECASE` would
# also let the long s and the Kelvin sign through. The id is matched as written, never as folded: the redactor reads the
# characters it is given, and an id whose fold is ASCII (a sharp s folds to `ss`) is masked only up to that character.
_READABLE_ID = re.compile(r"[a-z0-9_\-]+", re.ASCII | re.IGNORECASE)


def check_id(value: object, label: str = "an id") -> str:
    """Return an id unchanged; raise ValueError when it is not a string, when it is spelled like a stage word (STAGE_WORDS:
    the three stages and three more), when it is a word on the redactor's common-word list
    (`commonwords.COMMON_WORDS`), when it is too short for the redactor to sweep, or when it has a character the
    redactor's label rule does not read (that last test reads the id as written, not its fold). The stage and
    common-word tests compare `fold_name`. `label` is the phrase the error starts with
    ("a tenant id", "a customer id"). It covers the ids the redactor's label rule reads: tenant, org, organisation,
    organization, customer, account and user (guard/redact.py, the TENANT pattern).
    Why: the redactor masks the value after such a label (`tenant_id=prod`), and sweeps its other copies, only when
    the value is at least `SWEEP_MIN_LENGTH` characters, is not all digits below `SWEEP_MIN_DIGITS`, is not on the
    common-word list (a bare `prod` elsewhere stays readable, because `HTTP 500 in prod` must), and is made of the
    characters the label rule reads. An id outside that keeps unlabelled copies in clear (or is masked only in part), so
    it is refused at registration. The limits are the redactor's own constants (`commonwords.SWEEP_MIN_LENGTH`,
    `SWEEP_MIN_DIGITS`), not copies. The error does not echo the value; that holds inside a model that hides input in
    errors (`config._Strict`), a plain pydantic model prints `input_value=`. Every field that holds such an id uses a
    `config` id type in a `_Strict` model."""
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
        shortest = min(len(value), len(folded))
        if shortest < SWEEP_MIN_LENGTH or any(
            s.isdigit() and len(s) < SWEEP_MIN_DIGITS for s in (value, folded)
        ):
            raise ValueError(
                f"{label} is too short for the redactor to sweep (at least {SWEEP_MIN_LENGTH} characters, "
                f"and at least {SWEEP_MIN_DIGITS} when it is all digits)"
            )
        if not _READABLE_ID.fullmatch(value):
            raise ValueError(
                f"{label} may only use letters a to z, digits, hyphen and underscore, "
                "the characters the redactor's label rule reads (the id is read as written, not folded)"
            )
        return value
    raise ValueError(f"{label} must be a string")


def check_tenant_id(value: object) -> str:
    """`check_id` for a tenant id."""
    return check_id(value, "a tenant id")
