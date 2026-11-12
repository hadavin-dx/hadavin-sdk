"""Issue 2: prepare_output raises InputTooLarge on a ~130-character text. Prints the first traceback."""

import traceback

from hadavin_sdk import tools
from hadavin_sdk.guard import runmap

ESC = "\x1b"
HAND = "Qx7mLp" + "-9vRtzKw2"
t = (
    "Qx7m" + ESC + "Lp-9vRtzKw2 AKIAIOSFODNN%1b7EXAMPLE Qx7mLp-9vRtzKw2 AKIAIOSFODNN7EXAMPLE "
    "AK\\u001bIAIOSFODNN7EXAMPLE AKIAIOSFODNN7EXAMPLE Qx7mLp-9vRtzKw2 \x07"
)
print("len", len(t))
try:
    print(repr(tools.prepare_output(t, {}, 4000, [HAND])))
except runmap.RedactionError:
    traceback.print_exc()
