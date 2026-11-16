---
name: snapshot-before-review
description: "egm:* reviewer agents are read-only with no shell; before any review of a branch/PR head, export the changed files to a readable snapshot folder and name it in the brief"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-01T22:34:11.125Z
---

The egm reviewer agents (design, codebase-details, implementation-readiness, comprehension, zoom-out) have only Read/Grep/Glob. Repeatedly (2026-11-02: core PRs #49, #50 and apexc PR #4) they reviewed an outdated checkout or returned "REVIEW INCOMPLETE" because the PR head was not on disk, wasting a full review round.

**Why:** a review of the wrong version is worthless and costs tokens; owner wants no wasted rounds.

**How to apply:** before launching reviewers on a branch head: `git fetch`, then export the changed files (`git diff --name-only origin/main...<branch>` + `git show <branch>:<path>`, or `git archive`) to `egm\<topic>\snapshot-<shortsha>\`; put that path and the exact head sha in the brief and tell the reviewer to ignore the on-disk checkout; check the head sha in evidence matches the snapshot. Reviewers also cannot write files: ask for the full report inline and save it yourself. Evidence runners (general-purpose) produce raw output files in `egm\<topic>\evidence-<n>.md`. See [[reviewer-independence]], [[core-modules-one-source-of-truth]].
