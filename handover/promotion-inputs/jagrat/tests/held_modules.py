"""Modules the copy tool held back, and imports that dangle until their package lands.

Format rule (tests/test_held_modules_format.py enforces it): ONE entry per line in each literal tuple, so a
later package removes exactly its own lines and merges stay one-line deletions.

Ownership (the package whose merge deletes the line):
  jagrat.bounds, jagrat.platforms.sim_db         -> J2
  jagrat.history, jagrat.chain, jagrat.tools,
  jagrat.links, jagrat.cards, jagrat.report      -> ASSUMED J4 (report: J5); the scout names no package; lead to confirm
  __main__.py -> jagrat.cli (PENDING)            -> J5
  models.py / trust.py / grounding.py            -> J1 (no held lines today; J1 owns those modules)
"""

# Each entry FAILS test_pending_entries_are_not_stale as soon as the module file exists.
# fmt: off
HELD_MODULES = (
    "jagrat.bounds",  # J2
    "jagrat.history",  # assumed owner J4, lead to confirm
    "jagrat.chain",  # assumed owner J4, lead to confirm
    "jagrat.tools",  # assumed owner J4, lead to confirm
    "jagrat.links",  # assumed owner J4, lead to confirm
    "jagrat.cards",  # assumed owner J4, lead to confirm
    "jagrat.report",  # assumed owner J5, lead to confirm
    "jagrat.platforms.sim_db",  # J2
)
# fmt: on

# (importing file, module) pairs that may dangle until the CLI package (J5) lands.
# fmt: off
PENDING = (
    ("__main__.py", "jagrat.cli"),  # J5
)
# fmt: on
