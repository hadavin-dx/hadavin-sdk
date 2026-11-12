"""Issue 1: encoded ESC + encoded first letter of a handed-out secret. Secret is made up, built from parts."""

from hadavin_sdk import tools

HAND = "Tr0ub4dor" + "-3xyzQ"
for t in (
    "x %1b%54r0ub4dor%2d3xyzQ y",
    "x \\u001bTr0ub4dor-3xyzQ y",
    "x &#27;&#84;r0ub4dor&#45;3xyzQ y",
    "x %1bTr0ub4dor-3xyzQ y",
    "x %1b%74r0ub4dor-3xyzQ y",
):
    print(
        repr(t),
        "tool ->",
        repr(tools.prepare_output(t, {}, 4000, [HAND])),
        "| error ->",
        repr(tools.error_reason(ValueError(t), [HAND])),
    )
