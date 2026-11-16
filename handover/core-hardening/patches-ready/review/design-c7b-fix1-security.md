# C7b fix (id vs command withholding): security-angle review (egm-design, read-only), condensed, 2026-11-16
Verdict: 0 blockers, 0 majors. Nothing executed by the reviewer (regex analysis by reading); sha256 of the patch not recomputed.
Abuse analysis: the lookahead is tested only at the first character after the hyphen and releases a token only if everything from there is 32+ hex characters then a word boundary. A real cmdlet with a letter outside a-f in its noun, a cmdlet followed by hex, and hex inside a longer word (letter, digit, underscore, non-ASCII) all stay withheld. Residual (negligible): a name defined by the attacker as Verb-ec2[a-f]<28+ hex> (not a real cmdlet; its body would still hit other rules). Hex followed by a hyphen is released.
Choke point: yes (channel.clean at channel.py:48 and slack_channel.py:74 route through gate.withhold_commands). Sibling rules cannot match hex ids. Numbers supported by logs: 24 of 262,144, 1 in 2,731, 81 of 800,000 on old code vs 0 on fix, +100 tests, 9505 + 455 = 9960 = 9946 + 14.
Nits / evidence gaps:
1. The old-code '6 failed 8 passed' run cites test lines 26, 38, 47 but the shipped patch has them at 27, 39, 48: the old-code run used a test file one line different. Re-run the shipped test file on old and new code and record its sha256.
2. Missing negative tests: exactly 31 vs 32 hex, uppercase hex id, id followed by underscore, Verb-ec2<32hex>-suffix.
3. The ec2[a-f] reasoning is by hand; no generic property test (no 32+ hex token after any lowercase prefix is withheld).
4. Patch comment 'a real cmdlet noun always holds a letter outside a-f' is an assertion, soften it.
5. Ids shorter than 32 hex or uuid-formatted after a hyphen are still withheld (new_id uses uuid4().hex, so not in practice).
Not checked: execution, other approval paths with 12-hex fragments, mutation run (none was run).
