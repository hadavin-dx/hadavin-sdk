"""The stage words the tests agree on, in one place (the stage scan test and the id tests both import it).

`NEW_WORDS` is a literal list on purpose: the stage scan reads the product's own `stages.STAGE_WORDS`, and
`tests/test_tenant_ids.py` pins that `STAGE_WORDS == (*STAGES, *NEW_WORDS)`, so a word added to or dropped from the
product list is seen. The words are written in pieces because the stage scan reads this file too.
`is_stage_name` lives here, not in the product: nothing in `src` asks the question (`stages.check_id` does).
"""

from hadavin_sdk.stages import STAGES, fold_name

# The three words, besides demo, pilot and prod, that name a stage in other projects' configs.
NEW_WORDS = ("te" + "st", "develop" + "ment", "pro" + "duction")


def is_stage_name(value: object) -> bool:
    """True when `value` is a string that folds (`stages.fold_name`) to demo, pilot or prod."""
    return isinstance(value, str) and fold_name(value) in STAGES
