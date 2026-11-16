# PR89 round 15, reviewer tests-A (egm-implementation-readiness), head 13b7124
Coverage: test file lines 1-1330 of 2657; runner lines 180-725 and 888-1224. Nothing was run (read-only reviewer).
Result: no Blocker/Major in slice. r14-01 and r14-02 judged fixed in this slice; r14-03/04/05 are outside this slice.
Minor/Nit (condensed; reviewer's ids r15-K-01..07):
- K-01 Minor, test 199-217: first loop refuses non-existent conftest files, so it passes for the message "conftest is not a file of the tree", not the grammar; fix: create the files or match the message.
- K-02 Minor, tests 402-422, 459-483, 534-553, 1283-1299: absence plus "[REDACTED]" present, not exact output.
- K-03 Nit, 597-612: test name says "exactly the edge minimum" but uses 6-character pieces; comment should say the 1-character limit is accepted.
- K-04 Nit, 877-957: expected lock name uses the code's own `_address_parts` (name "unparsed"); independent grammar check is at 2447-2450.
- K-05 Nit: failure messages print fake (parts-built) secrets via {lines}/{rows}.
- K-06 Nit, 1233: weak substring check "assert".
- K-07 Nit, 309-314: leaked-variable failure message does not name the cause.
