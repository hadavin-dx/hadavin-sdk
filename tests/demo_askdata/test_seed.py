"""P1: the seed is deterministic (a private SplitMix64, no library), so a reload yields the same table hashes."""

from .conftest import load_script

HASHES = {
    "customers": "09fad2a948ec65ab0a9e541afe1c52a82f65f74c4fe945f35332298a4d8dbac0",
    "products": "12784fed8d8d5e47c2586558d19b52ab3a0ba09b9124afcfaa716bbfe28a06c7",
    "orders": "bb9cf96df9d2e69f4fb9159cf866667c8cbb37d4c401b4e3d892cf999de7537e",
    "order_items": "f70536a8a4d7e8b30c8274f19f4c7c1c1f94018d78cd6ad0ee8aeabaf3d0d9db",
}


def test_reload_gives_the_same_table_hashes():
    seed = load_script("seed")
    first, second = seed.table_hashes(seed.generate()), seed.table_hashes(seed.generate())
    assert (
        first == second == HASHES
    )  # a pinned value: a change to the generator is a deliberate edit


def test_row_counts_and_the_terminal_control_plant():
    seed = load_script("seed")
    data = seed.generate()
    assert {t: len(r) for t, r in data.items()} == {
        "customers": 50,
        "products": 20,
        "orders": 200,
        "order_items": 491,
    }
    assert [c[1] for c in data["customers"] if seed.ESC in c[1]] == [seed.PLANT]


def test_sql_file_holds_no_raw_control_byte():
    seed = load_script("seed")
    text = "\n".join(seed.sql_statements())
    assert text.isascii() and not any(ord(c) < 32 and c not in "\n" for c in text)
