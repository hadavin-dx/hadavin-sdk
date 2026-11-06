"""Timing constants shared by the linear-time tests (one place, so a test file never imports another test file)."""

# A run is "fast enough" when it is under FLOOR_S, or under the ratio times the larger of the small-input time and
# MIN_SMALL_S (a small input can time at zero on a fast machine).
FLOOR_S, MIN_SMALL_S = 0.06, 0.004
