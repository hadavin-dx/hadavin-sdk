# PR89 round 17 delta (f552f26 -> 505fba9), fresh egm-codebase-details. Read only, nothing run.
No Blocker/Major. Lock released on every exit path (enter_context inside try, held.close() in finally); new test not vacuous; mutant snippet occurs once; counts 62+155=217 agree; MAX_FRAGMENT_WORK wording consistent (50,000 pairs x 3,998 ~ 2e8).
- s1-01 Minor CHANGELOG:14 describes a deleted test ("counts the searches made"), still says "Both".
- s1-02 Minor CHANGELOG:18 lists "?host= in a URL query" as two names but also says a query URL is "unparsed" (docstrings fixed, CHANGELOG not).
- s1-03 Nit new test's second `except RuntimeError` also catches a baseline failure and mislabels it.
- Nit (not reportable): signal inside enter_context itself, before the exit callback is registered, is released by refcount in CPython.
All three sent to the builder as one docs/test-text push; independent runner starts on that head.
