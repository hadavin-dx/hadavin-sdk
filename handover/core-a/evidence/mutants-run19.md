# Mutant run 19 (full tests/endpoint_mutants.py) on cloud/core-a head 5a8c83fd3 (started 16:15 UTC by core-a itself; the lead's G33d anchor edit is in; no edit needed)
Command: `cd /home/user/hadavin-sdk && .venv/bin/python tests/endpoint_mutants.py` (Python 3.13 venv).
Result (last lines of raw/mutants-run19.log): `120 of 120 run are as expected; problems: []`, `EXIT 0`.
Load note: the run overlapped an integ-pg pytest -n 3, a T1 -n 2 run and a docs builder's tests (load average peaked at 8.6 and was 4.4 five minutes before): the mutant kills are assertion-based, not timing-based; no timing test is part of this script's verdicts; if the lead wants a timing-clean figure, re-run it when load < 4 (4 minutes).
The sha256 pins printed at the top of the log match tests/fixtures/mutation_manifest.json (the script refused nothing).
