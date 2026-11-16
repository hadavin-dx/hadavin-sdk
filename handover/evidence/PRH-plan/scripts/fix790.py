"""Candidate design fix for case 790: apply earlier-mask spellings longest first (one sorted list)."""
from hadavin_sdk.guard import runmap
_orig = runmap._keep_earlier_masks
def keep_longest_first(view, pairs):
    return _orig(view, sorted(pairs, key=lambda p: -len(p[1])))
def install():
    runmap._keep_earlier_masks = keep_longest_first
