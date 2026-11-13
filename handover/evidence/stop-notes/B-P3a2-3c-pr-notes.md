# P3a-2 commit 3c notes (builder)
Head 11bd1260 on wip/cloud-p3a2-3c (pushed). Not built: generated 37x13 matrix (commit 5), --list-batch, ticket's 2 lock mutants (commit 4).
12 of the ticket's 29 retire ids never existed; 17 retired. 60 V mutants (V01-V60) instead of 54, one per clause.
GM1 retired: it mutated a dead constant (_GRANT_MAP_WORDS), now deleted. SC9/SC14/RA2/RA4/PDO2/DP9/DP3 were re-pointed with killers that did not kill; replaced.
Concurrent real-server tests on one database cross-talk through migrate's whole-database check: use one database per job.
gitleaks not installed here; CI runs it.
