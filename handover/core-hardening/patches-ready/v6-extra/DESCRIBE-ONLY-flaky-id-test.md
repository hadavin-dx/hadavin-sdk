# Describe-only item (lead answer Q16.1, 10:42Z): random id matches a redaction pattern
Class: a random id collides with a redaction pattern. The cmdlet-shape rule in the write-command withholding list reads ids of the form prefix + 32 hex digits as a cloud command when they start with ec2 and the next character is a-f.
Effect: test_s4_llm_guard.py::test_ids_and_plan_hashes_survive_redaction fails about 1 run in 2,731 (exact sweep: 24 of 262,144 id shapes on the unpatched base). Not in the take path.
Where the fix belongs: at the redaction rule (one lookahead). A ready patch and 14 tests exist in FIX-id-vs-command-withheld.patch; it is a security path and not yet independently reviewed. Nothing under src/ or tests/ was edited on this branch. Decision for a later core branch is the lead's.
Guard failures on this branch are BRANCH ARTEFACTs (Q16.2): the vendor-string and non-UTF-8 file under handover/, and the non-proprietary LICENSE copies in promotion-inputs (decision 11).
