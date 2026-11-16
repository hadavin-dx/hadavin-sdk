| mutant | block run | command | failing check ids | checks run | verdict | seconds |
|---|---|---|---|---|---|---|
| child-patch-order | T102 | `ONLY=T102 RUN=<run.mut-child-patch-order.py> bash safety-tests.r14.sh` | T102.patch-shape | 33 | KILLED - as expected | 0 |
| child-python-endswith | T102 | `ONLY=T102 RUN=<run.mut-child-python-endswith.py> bash safety-tests.r14.sh` | T102.python-path-text | 33 | KILLED - as expected | 0 |
| child-python-pytest-tail | T102 | `ONLY=T102 RUN=<run.mut-child-python-pytest-tail.py> bash safety-tests.r14.sh` | T102.python-shape-pytest | 33 | KILLED - as expected | 0 |
