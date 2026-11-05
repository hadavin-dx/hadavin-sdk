---
name: egm-for-every-plan
description: "Owner rule 2026-11-01: EGM wherever it helps, skip only typos/status/read-only/one-line edits with a stated reason; invoked through the Skill tool; report in egm\\<topic>\\"
metadata:
  node_type: memory
  type: feedback
---

Owner 2026-11-01: "egm is not needed for only small tasks which really egm is not needed, but should definitely be used for the tasks which even slightly need or would give better outputs and fill gaps. I do not compromise performance for tokens." This supersedes the 2026-10-28 "every plan, even small" and 2026-10-30 "no exceptions" versions.

Rule: use EGM (plugin `egm@egm`) for every plan, prompt, script, design, doc, config, cloud/DNS action, client-facing work and any non-trivial code change. Skip only typos, status checks, read-only questions and one-line mechanical edits, writing "EGM skipped: reason". "Urgent" and "the owner said go" are not reasons to skip.

| Skill | Fires when |
|---|---|
| `egm:egm-brainstorm` | new idea or goal -> concept brief (Opus 5.5) |
| `egm:egm-draft` | brief or notes -> design doc (Opus 5.5) |
| `egm:egm-review` | big plan: 5 goldfish stages (Sonnet 5.5) |
| `egm:egm-review-loop` | small item: 1-2 reviewers + a standard (Sonnet 5.5) |
| `egm:egm-resolve` | right after every review (Opus 5.5) |
| `egm:egm-bootstrap` | new or moved folder needs README contracts |
| `egm:egm-drift-report` | after each merge batch and before "done" |

Reviewer picks for review-loop: prompts and plans = `design_critic` + `implementation_readiness`; docs = `structural` + `style`; "right problem?" = `zoom_out`.

Mechanics:
- Invoke every EGM skill through the **Skill tool** (`egm:egm-*`), never by reading SKILL.md in-thread: the Skill call switches the model.
- Goldfish reviewers are fresh Agent calls of the `egm:egm-*` types. Never fork or resume one.
- Artifacts go to `<studio>/egm\<topic>\`, never into a repo. No report means not done.

History: on 2026-10-29 Claude skipped EGM for the backup script, AWS teardown and DNS cleanup (a breach under the then-mandatory rule); the 2026-11-01 rule keeps "when in doubt, run it".

Related: [[decisions-2026-10-28]], [[best-over-rules]].
