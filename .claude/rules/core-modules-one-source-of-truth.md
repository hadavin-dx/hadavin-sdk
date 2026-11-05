---
name: core-modules-one-source-of-truth
description: "owner 2026-11-02 HARD RULE: core modules in every demo/client repo and in hadavin-sdk must be the same and stay in sync; repo-specific code lives outside the core-module folder"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-01T20:19:22.184Z
---

Owner rule (2026-11-02): the core modules used by all demo repos (apexc, refunds, dealdesk, intake, Jagrat, others) and the main core repo (`projects\hadavin-sdk`, package `hadavin_sdk`) must be the SAME and consistent. If a core module changes in one place it changes in all places. Anything specific to one repo goes OUTSIDE the core-module folders, in that repo's own package.

**Why:** keeps every demo and later client build in order and in track; stops fixes that live in only one demo (same bug class repeats); makes later client projects start from one hardened base. Extends [[promote-generic-fixes-to-core]], [[class-level-fixes]], [[no-single-dependency]].

**How to apply (guardrails):**
1. Single source: generic code lives only in `hadavin_sdk`. Demos and client builds consume it through the pinned commit (`hadavin-sdk @ git+...@<sha>`), never by copy-paste into the demo.
2. Demo-local generic code is allowed only as a TEMPORARY copy while its core PR is open; it is listed in the demo's `builder-notes` promotion table (core PR number, follow-up to switch to core) and removed when the core PR merges and the pin moves.
3. Demo-specific code (domain rules, fixtures, sims, portal pages) lives in the demo's own package (`src/<demo>/`), never in a folder named or shaped like a core module (`runtime/`, `guard/`, `store/`, `audit/`, `approvals/`, `actions/`, `llm/`, `k1b/`).
4. Every PR that touches core modules in any repo is checked by the studio sync check (`tools\core_sync_check.py`, to be built through EGM): (a) all demo pins point at a core commit that exists on core main or on an open core PR listed in the promotion table, (b) no file in a demo repo duplicates a core module name/function without a promotion-table entry, (c) the vendored portal-kit copies match the kit hash file.
5. After any core merge: re-pin all demos in one sweep (one PR per demo, tests green) and record the new pin in `handoff\SESSION-HANDOFF.md`. A history rewrite of core changes every sha: re-pin everything afterwards (Jagrat plan Part 0a).
6. Builder briefs include this rule; EGM reviewers check "is this generic? is it in core?" on every demo diff.
