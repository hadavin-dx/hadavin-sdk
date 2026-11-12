---
name: sticky-harmful-labels
description: "A harmful or wrong label is state, not an event; demotion keys on the latest label; proposed R339, R343"
metadata:
  type: feedback
---

Demotion keys on the latest label per run; clearing needs a new labelled decision; check-then-insert is atomic (tested on two database connections). Source: K6 PR notes, kernel 6.1. Verdict levels (proposed R343): thresholds frozen before the dev freeze; demonstrated = 95% upper bound of error <= 10%; promising = <= 15%.

Related: [[decisions-2026-11-01]]
