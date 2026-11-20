# Model routing for the cloud sessions (TEMPORARY all-Fable order)

**Owner order 2026-11-19, until he says revert: every model is Fable 5.2 (`claude-fable-5-2`).** This covers normal work and EGM: EGM skills, EGM reviewer agents, builders, evidence runners, general-purpose agents, lookups.

- Set the Agent `model` to `fable` on EVERY Agent call (never inherit, never `sonnet`, `opus` or `haiku`).
- The environment setup script (`tools/egm_setup.sh` on the laptop, pasted by the owner into the cloud environment) sets every EGM skill and agent to `claude-fable-5-2`. Prove it in your first REPORT block: `grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c` must show only `claude-fable-5-2` lines (no opus, no sonnet). If the session model itself is not Fable 5.2, say so in the report; do not change settings.
- Call EGM only through the Skill tool, one stage at a time (sequence: brainstorm, draft, plan review, resolve, build, evidence runner, result review, resolve, drift report). Reviewers of one stage run in parallel only inside that stage; stages never overlap.
- The old tiers (Opus 5.5 planning skills, Sonnet 5.5 for everything else, Haiku 5.5 lookups) return only when the owner says revert; the lead then updates this file.
