"""Path text of an exact length in UTF-8 bytes, built from the length of the folder the test really got (a temporary folder's
own length differs by machine, so a test that hard-codes a count of names is wrong on another machine)."""

from __future__ import annotations

_NAME = 200  # one name stays under the 255-byte limit of a single name


def path_of_bytes(base: str, total: int) -> str:
    """``base`` plus ASCII names, exactly ``total`` bytes long. No name is longer than 200 bytes, none is empty."""
    room = total - len(base.encode("utf-8"))
    if room < 0 or room == 1:
        raise ValueError(
            "the base is too long for this total, or leaves one byte that no name can fill"
        )
    full, rest = divmod(room, _NAME + 1)
    sizes = [_NAME] * full
    if (
        rest == 1
    ):  # one byte left over cannot be a name ("/" + nothing): move a byte from the last full name
        sizes[-1] -= 1
        rest = 2
    if rest:
        sizes.append(rest - 1)
    return base + "".join("/" + "a" * n for n in sizes)
