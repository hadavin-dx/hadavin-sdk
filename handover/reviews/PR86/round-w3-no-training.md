# A18 / PR86 (P6b1 no-training statement check, snapshot A18-8f6b032) - fresh reviewer, correct slice. Read only, nothing run.
Result: no Blocker, no Major. Ticket, config.py 380-540, table.py parts, tests/test_training_lock.py all read. Not seen: evidence, mutants M1-M32, guard tests (lockin, hardcoded, repo_rules), fail-before.
- F1 Minor: openai_compat basis self_hosted with a public https host loads in pilot/prod on the operator's word only (P6a to close; documented).
- F2 Minor: new model_id on an already-covered host needs no new statement (ticket PENDING LEAD 11).
- F3 Minor: detector bedrock_guardrail in pilot/prod loads with no dated statement; trigger only on a v1.1 list, no code refusal.
- F4-F6 Nits: test_t4b limit=-5 unreachable; trailing-dot host mismatch fails closed; T1b regex tied to message format.
