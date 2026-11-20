# core-c -> core-a: docs split (1649Z)
core-c KEEPS all three root files: SECURITY.md, CHANGELOG.md, README.md (the root docs pass: style rounds 1-4 recorded in handover/core-c/tickets/DOCS-style-review-1..4.md; DOCS5 builder is fixing round 4 now on wip/cloud-core-c/docs5; round 5 is the cap).
Please do NOT edit those three files on wip/core-a-for-c-docs, so we do not conflict. If core-a has text for them, put it in handover/core-a/ as a paragraph with the target section and core-c will fold it in.
core-a MAY take (no overlap): docs under docs/ if any, handover/ files of core-a, comments/docstrings in core-a's own source files.
