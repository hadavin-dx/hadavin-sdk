---
name: promote-generic-fixes-to-core
description: "owner 2026-11-02: every generic fix made in a demo repo must also be built in hadavin-sdk (hadavin_sdk) so it serves all project types"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-01T19:50:13.757Z
---

Every fix made inside a demo repo (apexc, refunds, dealdesk, intake, an earlier demo, others) that is generic, not specific to that demo's domain, must ALSO be built in the main core repo (`projects\hadavin-sdk`, package `hadavin_sdk`) as a kind-level, vendor-neutral module with tests that fail on the old code.

**Why:** the owner wants one core that works for all kinds of projects; a fix that lives only in one demo is lost to the next client build and repeats the same bug class (owner 2026-11-02). Fits [[class-level-fixes]] and [[no-single-dependency]].

**How to apply:**
- Tag each demo finding GENERIC or DEMO-ONLY in the builder notes (`egm\demos\<topic>\builder-notes-*.md`).
- GENERIC: build in core on a `core/promote-<demo>-<topic>` branch, draft PR, never merged by the builder; check core first and extend rather than duplicate; no demo imports.
- Demos pin a core commit sha, so the demo keeps its local version until the core PR merges; then a follow-up switches the demo to the core version and deletes the local copy.
- History rewrite of the public core repo changes every sha: re-pin all demos afterwards (see the demo plan).
- Each core PR goes through the EGM sequence (evidence runner, egm:* reviewers, resolve) before merge.
