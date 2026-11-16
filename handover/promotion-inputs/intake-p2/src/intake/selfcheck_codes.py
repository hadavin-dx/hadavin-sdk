"""The closed set of codes for the checks on hiding sensitive values (design WP2c B5), their plain sentences and the flag each one gives.

A leaf module: it imports nothing from ``src/intake``. These are item sub-reasons, not members of ``codes.CODES``: pass the code as the first
POSITIONAL argument (``SelfCheckFailed("mask_failed")``), never as a ``code=`` keyword. ``body_unsafe`` is a model error (``codes.MODEL_ERRORS``)
and is deliberately not here.
"""

from __future__ import annotations

SELFCHECK_CODES = (
    "mask_failed",
    "mask_too_large",
    "mask_residual",
    "mask_money_overlap",
    "mark_like_text",
    "forged_mark",
    "body_has_original",
    "doc_sha_mismatch",
    "hidden_value_in_field",
    "restore_mismatch",
    "log_has_original",
    "body_not_reproducible",
)

PLAIN = {
    "mask_failed": "the step that hides sensitive values failed; nothing was sent",
    "mask_too_large": "the invoice has a line over 2,000 characters, or the text with its hiding marks is over 40,000 characters; nothing was sent",
    "mask_residual": "a value that looks like a bank detail could not be located in the text, so it could not be hidden; nothing was sent",
    "mask_money_overlap": "a value to hide sits next to an amount in a way the tool cannot separate; nothing was sent",
    "mark_like_text": "the invoice contains a string that looks like a hiding mark; a person must check it",
    "forged_mark": "the AI wrote a hiding mark we did not issue for this invoice; a person must check",
    "body_has_original": "the request still held a value that should have been hidden; nothing was sent",
    "doc_sha_mismatch": "the request did not belong to this invoice; nothing was sent",
    "hidden_value_in_field": "a hidden value ended up in a field where it does not belong; a person must check",
    "restore_mismatch": "putting the hidden values back did not give the exact original text; the AI result is not used",
    "log_has_original": "a hidden value was found in the log; the AI result is not used and that log file was set aside",
    "body_not_reproducible": "the request that was sent cannot be rebuilt exactly",
}

FLAG_OF = {c: ("M02" if c in ("mark_like_text", "forged_mark") else "M01") for c in SELFCHECK_CODES if c != "body_not_reproducible"}


class SelfCheckFailed(Exception):  # noqa: N818 (name fixed by the design)
    """A check on hiding sensitive values failed. Carries the code only, never a value. ``detail`` may hold closed-vocabulary facts the raise site
    adds for the log line (for example a schema path, a length and a keyed fingerprint); never text from the invoice or the AI."""

    detail: tuple = ()

    def __init__(self, code: str) -> None:
        if code not in SELFCHECK_CODES:
            raise ValueError("unknown self-check code")
        super().__init__(code)
        self.code = code
