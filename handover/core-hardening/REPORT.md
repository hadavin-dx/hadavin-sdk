# REPORT from core-hardening (cloud to lead). Newest block on top, UTC and IST.
FILE-INDEX: handover/core-hardening/REPORT.md | ORDER 001 | BLOCKED

## 2026-11-16 06:09 UTC / 11:39 IST - ORDER 001 SETUP: BLOCKED at plugin install (stopped per step 5)
Failures first:
1. REFUSED: `claude plugin install egm@egm` (run in Bash, working dir hadavin-sdk). The Claude Code auto-mode permission classifier denied it, reason text: "[Undermining Oversight]". Denied twice: once as a combined command (install + `python3 handover/tools/egm_model_patch.py` + the grep check), once as the install command alone. Nothing was installed.
2. NOT RUN (because the install never happened): `python3 handover/tools/egm_model_patch.py`; the list of the 7 egm:egm-* skills; the list of egm:* agents; the `grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c` proof. No proof output exists.
3. Cannot type `/plugin ...` slash commands (no tool for it in this session), so I used the `claude plugin` command line instead.
What worked:
- `claude plugin marketplace add google/elephant-goldfish-model` succeeded ("Successfully added marketplace: egm (declared in user settings)"). This only registers the marketplace; no plugin is installed.
- Branch core/cloud-handover checked out from origin, up to date. Read README.md, BRIEF-PREAMBLE.md, MODEL-ROUTING.md, RULE-R456-WORK-CONDUCT.md, CLOUD-EGM-SETUP-2026-11-12.md.
- Claude Code version: 2.1.325 (meets the 2.1.271 minimum). Session model: claude-sonnet-5-5.
Also noted: MODEL-ROUTING.md says the patch script removes the `disable-model-invocation: true` flag from the EGM skills; that may be what the classifier objects to.
Needed from lead/owner to continue: either add a Bash permission rule allowing `claude plugin install egm@egm` and `python3 handover/tools/egm_model_patch.py` in this session, or install the plugin from a session you control. I will not use a general-purpose agent as reviewer and have started no work.
No agents started, no secrets, no spend, nothing merged.

