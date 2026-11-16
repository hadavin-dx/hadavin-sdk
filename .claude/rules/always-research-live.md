---
name: always-research-live
description: "Never rely on built-in knowledge for tools, versions, threats or best practice; research live up to today before choosing or claiming anything"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 21fd50e7-2e36-4add-87bc-7319957a0764
  modified: 2026-09-28T09:49:39.118Z
---

My knowledge has a cutoff. On 2026-09-28 the owner said "you will have to always research even till
this today and this minute". Before picking a tool or architecture, stating a best practice, or
listing AI failure modes, do live, multi-source research dated to today, and verify versions and
release dates.

**Why:**
- LangGraph was kept long after the owner asked for production grade.
- A phase was declared done while about 20 gaps from my own register (docs/FAILURE-MODES.md) were
  unbuilt.
- A single shallow research agent was presented as research.

The owner judged this "not taking it seriously".

**How to apply:**
- Use deep-research (parallel researchers) for landscape questions.
- Check every "done" against the full requirement trace AND docs/FAILURE-MODES.md, never against
  my own summary.
- Prefer proven OSS over building from scratch; say so when building anyway.

Related: [[local-paths-in-steps]].
