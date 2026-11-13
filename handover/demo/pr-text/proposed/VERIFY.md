# VERIFY (D-PR, in progress) - clone /tmp/work/dpr-base
| statement | how verified | result |
|---|---|---|
| PRs #2,#3,#4 opened 17:36:53Z/17:37:03Z/17:37:11Z (not 20:16Z; 20:16Z is last update of #2/#3) | gh api pulls?state=all | verified |
| #1 (initial-code 43110e7) closed, not merged | gh api | verified |
| files: #2 86, #3 39, #4 142 | git diff --name-only base...head | verified |
| final tree != #1: 95 files differ | git diff --stat initial-code pr-3-tests | verified |
