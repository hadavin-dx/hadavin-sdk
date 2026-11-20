"""Put-back: the caller's way from a masked model reply to the real values (ESCALATIONS E25 option a).

The model gate masks the model's reply with the run's map (`model_gate.BoundGate.chat`). A caller that needs a real
value to act (a host name in a fix, an account id in a read) maps the placeholders back with `put_back`.

Rule: ONLY identifier kinds that the run may store (`defaults.STORED_KINDS`, whose originals also pass
`runmap.storable_original`) are restored. A placeholder of a secret or regulated kind is NEVER restored, whatever the
map holds; a placeholder that is not in the map is left as written. One pass: a restored value is never expanded
again. This is `runmap.restore_text` / `restore_value`; no second matcher exists.
"""

from collections.abc import Mapping
from typing import Any

from hadavin_sdk.guard import runmap


def put_back(value: Any, mapping: Mapping[str, str], kinds: frozenset[str] | None = None) -> Any:
    """`value` (a str, or a dict or list of them, e.g. a tool call's `input`) with the placeholders of restorable
    kinds replaced by their originals. `kinds` may only narrow what `defaults.STORED_KINDS` allows."""
    allowed = runmap.STORED_KINDS if kinds is None else runmap.STORED_KINDS & frozenset(kinds)
    return runmap.restore_value(value, dict(mapping), frozenset(allowed))
