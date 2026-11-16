---
name: class-level-fixes
description: "Fix bug classes, not instances (lesson of PRs #41-#43, 2026-11-01); proposed R337"
metadata:
  type: feedback
---

For every bug: name the class, cite the standard it violates (RFC, language or API spec, vendor grammar), fix at the shared choke point with an allowlist or spec-derived grammar, grep for siblings, add property/fuzz/concurrency tests, and run the new tests against the old code to prove they fail. Source: k5-core-builder and k6-builder notes, review rounds 3-4. Rule text for the RULES.md owner (R337).

Related: [[reviewer-independence]], [[fix-dont-defer-be-honest]]
