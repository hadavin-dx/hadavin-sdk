# Operator notes (not for the owner's list)

1. All machines of one deployment must keep their clocks within 60 seconds of each other. The chat lease and the stuck-run rule compare times written by different machines (AK-G1 design, DES-ADV-12; accepted by lead order 39, sentence 7).

## Stray files in / (2026-11-07, for the owner)
Five small files were written to the filesystem root by a builder whose evidence script had an unset variable: /ruff-check.txt, /ruff-format.txt, /bandit.txt, /scan-repo.txt, /hygiene.txt. They are lint output and a SHA, harmless (lead, order 133 item 3). Do not delete them from the agent; delete by hand if wanted. The evidence script gets `set -u` so an unset variable aborts.
