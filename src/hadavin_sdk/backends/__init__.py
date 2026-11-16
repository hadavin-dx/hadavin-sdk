"""Pluggable backends: one table (``table.py``) maps each capability and kind to a settings model and a factory;
``factory.py`` holds ``make``, ``hosts`` and ``Deps``.

This package file imports nothing, so importing a sibling such as ``backends.table`` (the config does) never pulls
in the secret providers. Import the factory as ``hadavin_sdk.backends.factory``; ``runtime``, ``approvals``,
``llm``, ``sources`` and the tools reach no secret holder even transitively, and a repo rule forbids
``from hadavin_sdk.backends import <name>`` there (K5, M21; tests/test_repo_rules.py).
"""
