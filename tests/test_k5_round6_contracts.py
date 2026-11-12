"""Round 6: a custom store written for an earlier version is refused at start with the missing names; two source
kinds whose operation prefixes overlap are refused at registration."""

from __future__ import annotations

import dataclasses

import pytest

from hadavin_sdk.sources import kinds
from hadavin_sdk.store.protocol import missing_methods


class OldStore:
    def create_run(self, run): ...
    def get_run(self, run_id): ...


def test_an_old_store_is_reported_with_the_names_it_lacks():
    lacking = missing_methods(OldStore())
    assert (
        "add_tool_call" in lacking
        and "put_redaction_map" in lacking
        and "purge_redaction_maps" in lacking
    )


def test_a_complete_store_lacks_nothing():
    from hadavin_sdk.store.memory import MemoryStore

    assert missing_methods(MemoryStore()) == []


def test_the_inbound_methods_are_a_separate_list_and_never_make_an_old_store_incomplete():
    """AK-G2-a (L23 (i)): a store written before the inbound ledger still starts; only an app with inbound
    sources asks `missing_inbound_methods`."""
    from hadavin_sdk.store.memory import MemoryStore
    from hadavin_sdk.store.protocol import missing_inbound_methods

    assert not [n for n in missing_methods(OldStore()) if "inbound" in n]
    assert len(missing_inbound_methods(OldStore())) == 11
    assert missing_inbound_methods(MemoryStore()) == []


def test_overlapping_prefixes_are_refused_and_the_registry_is_unchanged():
    k8s = kinds.KINDS["kubernetes"]
    before = dict(kinds.KINDS)
    with pytest.raises(ValueError, match="overlaps"):
        kinds.register("k8s2", dataclasses.replace(k8s, operation_prefix="k8s.metrics."))
    with pytest.raises(ValueError, match="overlaps"):
        kinds.register("k8s3", dataclasses.replace(k8s, operation_prefix="k8"))
    assert kinds.KINDS == before
    kinds.register("kubernetes", k8s)  # re-registering the same name is not an overlap with itself


def test_the_old_backends_import_path_fails_loudly_and_the_new_one_works():
    with pytest.raises(ImportError):
        from hadavin_sdk.backends import make  # noqa: F401
    from hadavin_sdk.backends.factory import make as new_make

    assert callable(new_make)
