# DECISION: src/hadavin_sdk/extract.py (P5). Default: KEEP.
Evidence at head 186051499:
- Importers in src/: none (grep over src for "hadavin_sdk.extract", "from .extract", "import extract": no hit; only stale .pyc files).
- Importers in tests: tests/test_s4_llm_guard.py (line 8: from hadavin_sdk.extract import Valid, extract; tests test_extract_valid and the bad-document test around lines 48-55) and tests/test_k5_round9.py (line 94, the "extract validation errors" case).
- What it is: validate, one retry with the validator's errors, then a dead letter (extract.py docstring). It calls the LLM protocol directly and does not mask the document text itself: the masking path is the model gate; extract() sends whatever bytes it is given. That is the unmasked path SECURITY.md lists.
- Rule from the lead: keep unless nothing imports it. Tests import it, so: KEEP. Deleting it would also delete or rewrite the two test files' extraction cases.
- Open for the owner (not decided here): whether the extraction path should go through the gate or be removed together with its tests. Status: OPEN. The security note stays in SECURITY.md (unmasked paths).
