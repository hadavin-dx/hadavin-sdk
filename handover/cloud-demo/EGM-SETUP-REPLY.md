## new session (ORDER 251 restart check, 2026-11-12)
Failures first:
- Patch did NOT run: `python3 handover/tools/egm_model_patch.py` (copied from origin/core/cloud-handover, the only branch that has it; it is absent from this session's checkout) exited 1 with "no EGM plugin folder found; install the plugin first". ~/.claude/plugins holds only `store/` (cc-plugin-agents-md_builtin) and an empty `synced/<org>` folder; no egm plugin exists in this container. No file was changed.
- `grep -rl disable-model-invocation ~/.claude/plugins/` is empty, but only because no EGM files exist, so it proves nothing about the flag.
- Skill tool test: Skill(egm:egm-review) -> "Unknown skill: egm:egm-review". The skill list for this session has no egm:* entries. The earlier "disable-model-invocation" refusal is gone because the plugin is missing, not because it was fixed.
- Model switch: not tested (no EGM skill or agent available).
Not done: I did not install the plugin, work around it by reading SKILL.md, or edit settings/hooks. Needs the lead or owner to enable the egm@egm plugin for this new session (or tell me where to install it), then rerun the patch.
Note: handover/ is not in this session's branch (claude/sleepy-franklin-0faqzv); this file is a new uncommitted copy holding only this section. Merge it under 'new session' in the copy on core/cloud-handover. Nothing was committed or pushed.
