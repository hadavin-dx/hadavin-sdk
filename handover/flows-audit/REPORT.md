# REPORT from flows-audit (cloud to lead). Newest block on top, UTC and IST.

## 2026-11-16 06:13 UTC / 11:43 IST: ORDER 002 SETUP: plugin installed and patched; skills NOT yet visible in this session, NEW SESSION NEEDED. No work started.
**Failed / not proven (first):**
- Skill tool in THIS session still says "Unknown skill: egm:egm-review". The skill list is read at session start, so the 7 egm skills and egm:* agent types cannot be shown from here. Lead: a new session is needed (start it from branch demo/handover, then run only the proof listing).
- Dry run (egm-review-loop on a test paragraph) NOT done: skills not callable.
- Settings keys (model, effortLevel) not changed; the order did not ask for it.

**Done (with output):**
- `claude plugin marketplace add google/elephant-goldfish-model`: "Successfully added marketplace: egm".
- `claude plugin install egm@egm`: "Successfully installed plugin: egm@egm (scope: user)". `claude plugin list`: egm@egm Version 0.1.1, Scope user, Status enabled. Claude Code 2.1.325.
- `python3 handover/tools/egm_model_patch.py`: "done: 70 file(s) changed in 2 plugin folder(s)" (cache and marketplace copies).
- Skills on disk (7): egm-bootstrap, egm-brainstorm, egm-draft, egm-drift-report, egm-resolve, egm-review, egm-review-loop. No SKILL.md lacks a model line; none still has disable-model-invocation.
- Agent files on disk (10, from plugin.json): bootstrap_orchestrator, codebase_details, comprehension, design_critic, implementation_readiness, inventive_catalyst, structural, style, synthesizer, zoom_out. Note: names are these, not the egm-design / egm-style names in the setup doc; the exact egm:* agent type ids are unconfirmed until a new session lists them.
- `grep -rh "^model:" ~/.claude/plugins/*/egm* | sort | uniq -c`:
```
      6 model: claude-opus-5-5
     64 model: claude-sonnet-5-5
```
(6 opus = 3 planning skills x 2 plugin copies; no inherit.)
**FILE-INDEX:** handover/flows-audit/{README,ORDERS,REPORT}.md; handover/{MODEL-ROUTING,CLOUD-EGM-SETUP-2026-11-12,EGM-CHILD-HOWTO}.md; handover/tools/egm_model_patch.py
**Agents running:** 0.

## 2026-11-16 06:08 UTC / 11:38 IST: ORDER 001 SETUP BLOCKED (EGM plugin install refused). No work started.
Session: flows-audit, Sonnet 5.5, hadavin-sdk, branch demo/handover (base ce4b89870).

**What failed (lead with this):**
- EGM plugin NOT installed. Step 3 not done, so the proof (7 egm:egm-* skills, egm:* agents, model grep) does NOT exist.
- Exact refusal: I ran `claude plugin marketplace add google/elephant-goldfish-model` (the shell form of `/plugin marketplace add`; I cannot type slash commands). The Claude Code auto-mode permission classifier denied it. Reason shown: "[Undermining Oversight]". I did not retry or work around it (order step 5: stop and write what was refused).
- Skill tool check: `egm:egm-review` returns "Unknown skill". No egm skills are loaded.
- `python3 handover/tools/egm_model_patch.py` NOT run: no EGM plugin folder exists, so it would only print "no EGM plugin folder found". Grep proof NOT produced.
- handover/CLOUD-EGM-SETUP-2026-11-12.md and handover/EGM-CHILD-HOWTO.md (named in README and ORDER 001) are NOT on branch demo/handover. I could not read them.

**Done:** fetched and checked out demo/handover; read README.md, BRIEF-PREAMBLE.md, MODEL-ROUTING.md, RULE-R456-WORK-CONDUCT.md, egm_model_patch.py. No agents started (0 running). No files changed except this report.
**Not checked:** whether the install would work with a permission rule allowing it; network reach to GitHub for that marketplace.
**Needed from lead / owner (next step):** either allow the Bash command `claude plugin marketplace add google/elephant-goldfish-model` and `claude plugin install egm@egm` for this session (permission rule), or install the plugin another way; and push the two missing setup docs. Then start a NEW session so the skill list reloads, and re-issue ORDER 001.
**Note:** ORDERS.md and this branch live in hadavin-sdk; the other repo (duplicate-proof-lead-desk-n8n) has no demo/handover branch.
**R-numbers cited:** R456 (work conduct, honesty). Preamble rule 13 (EGM gate: if EGM cannot be invoked, say so and stop).
**FILE-INDEX:** handover/flows-audit/{README,ORDERS,REPORT,QUESTIONS}.md; handover/{BRIEF-PREAMBLE,MODEL-ROUTING,RULE-R456-WORK-CONDUCT}.md; handover/tools/egm_model_patch.py
**Head SHA before this commit:** ce4b89870
