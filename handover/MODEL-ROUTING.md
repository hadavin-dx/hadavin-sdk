# Model routing for the cloud sessions (all-Fable order REVERTED 2026-11-20 by the owner)

**Owner order 2026-11-20 (chat): no Fable anywhere, here and on every cloud session.** The Fable limit is reached until 2026-11-24 08:30 IST.

- Set the Agent `model` on EVERY Agent call: `opus` for egm-brainstorm / egm-draft / egm-resolve, `sonnet` for every other EGM reviewer, builder and agent, `haiku` for lookups. Never `fable`, never inherit.
- EGM plugin model lines in your container: `claude-opus-5-5` on the three planning skills (all copies) and the feature_proposal template, `claude-sonnet-5-5` on every other line. Prove with: grep -rh '^model:' ~/.claude/plugins/*/egm* | sort | uniq -c (zero fable). Do not run any fable patch script.
- Commit trailer: Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>.
- Old text of this file (all-Fable order of 2026-11-19) is history and no longer valid.
