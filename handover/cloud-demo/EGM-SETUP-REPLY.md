# EGM setup reply, ORDER 248 + 249 (2026-11-12 18:08Z / 23:38 IST)
Session session_014pRo39s7uVZzyUdigisB8j. Made-up test data only, no secrets.

## Failures and gaps first
1. Skill tool refuses every EGM skill (call by me, exact error):
   - Skill(skill="egm:egm-review-loop", args="<test doc> --reviewers design,style") ->
     "Skill egm:egm-review-loop cannot be used with Skill tool due to disable-model-invocation. Ask the user to run /egm:egm-review-loop themselves — it cannot be invoked via the Skill tool. Do not replicate this skill's workflow by other means — it is reserved for explicit user invocation."
   - Before the reload (agents not yet registered): Skill(egm:egm-review-loop) and Skill(egm-review-loop) -> "Unknown skill: ...".
   - egm:egm-resolve: NOT called separately; same plugin flag, expected same error (not verified).
2. Skill tool list: EGM skills are NOT listed (they are hidden from model discovery); the 30 listed skills after /reload-skills include none named egm-*. ("Reloaded skills: 30 skills available (none added or removed)").
3. Model switch by the Skill call: NOT shown. The plugin skills set no model; only the user-typed /egm:egm-review-loop ran.
4. Studio files templates/, bible/, tools/hooks were not in the demo checkout (duplicate-proof-lead-desk-n8n); hooks of this repo (.claude/hooks/*) did not run in my session because my working dir was the demo repo, so none printed a refusal (item 6).
5. Dry run only reached round 1 (review swarm); egm-resolve not run.

## Diagnosis (root cause)
All 7 skills in egm@egm 0.1.1 (egm-bootstrap, brainstorm, draft, drift-report, resolve, review-loop, review) have "disable-model-invocation: true" in skills/*/SKILL.md frontmatter. The plugin's own docs/claude.md says this is intended: "The Skill tool refuses these skills ... to run another EGM skill, read its SKILL.md and follow it in the same thread. Do not use the Skill tool for EGM skills." Not a version issue, not install, not network. It contradicts studio rule 2 ("never read a SKILL.md in-thread"). Only the user typing /egm:<name> invokes them (done once, worked).

## Requested facts (ORDER 249)
(1) see item 1. (2) see item 2. 
(3) claude --version: 2.1.322 (Claude Code), >= 2.1.271.
(4) ~/.claude/plugins/ has: cache, installed_plugins.json, known_marketplaces.json, marketplaces, store, synced. cache/egm and marketplaces/egm exist. plugin.json names: egm, displayName "Elephant-Goldfish Model", version 0.1.1, Apache-2.0, 10 agents listed.
   claude plugin list: "egm@egm  Version 0.1.1  Scope: user  Status: enabled  Note: Default agents/ folder is ignored because the manifest sets agents".
(5) git ls-remote https://github.com/google/elephant-goldfish-model HEAD works: 0997679a1cc3cfe09206160a85f9379f47101053. Marketplace add and plugin install both succeeded; no network or policy block.
(6) No hook refusal: this repo's hooks were not active in my session (see item 4); the refusal text came from the Skill tool itself.

## What works
Agent types egm:egm-design, egm-codebase-details, egm-comprehension, egm-implementation-readiness, egm-structural, egm-style, egm-zoom-out, egm-synthesizer (+ egm-inventive-catalyst, egm-bootstrap-orchestrator) are callable. Dry run: egm:egm-design and egm:egm-style launched with model sonnet, both reported in ~13 s, both FAILED the made-up two-line test doc (2 blocker + 3-5 major each). Test document deleted.
Settings (user): model claude-sonnet-5-5, effortLevel medium, egm@egm enabled. I did not edit this repo's .claude/settings.json or hooks.

## Options for lead
A user types each /egm:* command; B change studio rule 2 to allow reading SKILL.md in-thread (plugin's documented method); C vendor/fork plugin without the flag (lead decision, Apache-2.0).
