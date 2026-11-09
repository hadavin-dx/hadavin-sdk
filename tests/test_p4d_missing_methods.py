"""P4d-b, B8 (d): an old custom store without the six reservation methods is refused at start with their names."""

from hadavin_sdk.store.protocol import Store, missing_methods

SIX = [
    "get_spend_reservation",
    "list_open_reservations",
    "release_spend",
    "reserve_spend",
    "settle_spend",
    "sweep_spend_reservations",
]


def _old_store():
    """Every method the protocol had before the reservations, none of the new six."""
    keep = {
        n: (lambda self, *a, **k: None)
        for n, v in vars(Store).items()
        if callable(v) and not n.startswith("_") and n not in SIX
    }
    return type("OldStore", (), keep)()


def test_an_old_custom_store_is_refused_with_the_names_of_the_six_missing_methods():
    assert missing_methods(_old_store()) == SIX


def test_a_store_with_all_methods_is_not_refused():
    full = type(
        "FullStore",
        (),
        {
            n: (lambda self, *a, **k: None)
            for n, v in vars(Store).items()
            if callable(v) and not n.startswith("_")
        },
    )()
    assert missing_methods(full) == []
