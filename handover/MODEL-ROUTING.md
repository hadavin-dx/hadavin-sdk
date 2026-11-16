# Model routing for the cloud session (which Claude model does which job)

Why this file exists: upstream EGM files say `model: inherit`, so every EGM skill and reviewer silently runs on whatever model the session uses. The studio fixed this on the laptop: planning skills run on Opus 5.5, everything else on Sonnet 5.5, plain lookups on Haiku 5.5. The cloud session must do the same, otherwise it spends far more and gains no quality.

## The table
| Job | Model | Notes |
|---|---|---|
| EGM planning skills: `egm:egm-brainstorm`, `egm:egm-draft`, `egm:egm-resolve` | Opus 5.5 (`claude-opus-5-5`) | the only default use of Opus |
| EGM review skills: `egm:egm-review`, `egm:egm-review-loop`, `egm:egm-drift-report`, `egm:egm-bootstrap` | Sonnet 5.5 (`claude-sonnet-5-5`) | |
| EGM reviewer agents (`egm:egm-design`, `-codebase-details`, `-implementation-readiness`, `-structural`, `-style`, `-comprehension`, `-zoom-out`, `-synthesizer`, `-bootstrap-orchestrator`) | Sonnet 5.5 | independent reviewers; never the author |
| Builders (code, tests, fixes, CI repair), evidence runners, general-purpose agents of any kind | Sonnet 5.5 | default for all work |
| Plain lookups: list files, grep and count, read a CI log for pass/fail, mechanical rename or format, turn a log into a table, fetch a PR status | Haiku 5.5 (`claude-haiku-5-5`) | never for review, security, money, redaction, design or any decision |
| Anything else needing Opus | Opus 5.5 only with a written reason in the ticket (for example a design with several defensible options that the EGM draft cannot settle) | ask: could Sonnet do it? |

## Rules
1. The session itself runs on Sonnet 5.5 (`.claude/settings.json` sets it). Switch to Opus only to run the three planning skills, then switch back.
2. Set `model` explicitly on EVERY Agent call (`opus`, `sonnet` or `haiku`). Never rely on inheritance. A hook refuses general-purpose briefs without it.
3. A step moves to a cheaper model only when a check shows no quality loss: run the same 5 real inputs through the cheaper model and Sonnet and compare; write the result in the ticket. A Haiku output that feeds a decision is re-checked by Sonnet. When in doubt use the stronger model: a wrong cheap answer costs more than the saving.
4. Never use a cheap model for: independent review, anything touching money, redaction, security, permissions, migrations, or merge decisions.
5. Product code that calls a model (inside the core) follows `.claude/rules/model-choice-and-cost-follow-bible.md` and `df5-one-model-per-step-yes-2026-11-04.md`: one model per workload chosen before launch; no "cheap first, retry on strong" cascade on money, approval or permission steps; model ids and prices from config.
6. Report model use in each package's evidence file: which model ran each agent.

## Make EGM follow the table (run once at session start, before the first EGM call)
```
python3 handover/tools/egm_model_patch.py
```
It finds the installed EGM plugin and sets `model:` in every skill and agent file (Opus for brainstorm, draft, resolve; Sonnet for the rest), prints each change and is safe to run again. Then check:
```
grep -rh "^model:" ~/.claude/plugins/*/egm* 2>/dev/null | sort | uniq -c
```
Expected: `claude-opus-5-5` only on egm-brainstorm, egm-draft and egm-resolve (3 per plugin copy), everything else `claude-sonnet-5-5`, no `inherit`. The script patches every copy it finds (Claude, Cursor and distribution folders). Start a NEW session after patching: agents already loaded keep their old model. If a plugin update later restores `inherit`, run the script again.

## Prompt to paste into the cloud session (short form)
> Follow `handover/MODEL-ROUTING.md` exactly. First run `python3 handover/tools/egm_model_patch.py` and show me the grep check. From now on: this session runs on Sonnet 5.5; Opus 5.5 only for `egm:egm-brainstorm`, `egm:egm-draft` and `egm:egm-resolve`; Sonnet 5.5 for builders, evidence runners, all reviewers and every other agent; Haiku 5.5 only for plain lookups (list, grep, read a CI log, mechanical format); set the `model` field explicitly on every Agent call; never use a cheaper model for review, money, redaction, security or merge decisions; to move any step to a cheaper model first compare 5 real inputs against Sonnet and record the result in the ticket. Report which model ran each agent in every evidence file.

## Why the EGM skills may be refused (found 2026-11-05)
Upstream sets `disable-model-invocation: true` on all seven EGM skills. A skill with that flag can only be started by a person typing the slash command; when the model calls the Skill tool it is refused. The patch script now removes that flag as well. After running it, START A NEW SESSION: the list of skills is read when a session starts.

## OVERRIDE 2026-11-11 (owner's direct order in the cloud session): Fable 5.2 for ALL of EGM
Every EGM skill and every egm:* reviewer agent runs on `claude-fable-5-2` (the table above is superseded for EGM). `handover/tools/egm_model_patch.py` now writes that id everywhere. Builders and evidence runners stay on Sonnet 5.5 until the owner says otherwise. Start a NEW session after patching.

## OVERRIDE 2 2026-11-11 (owner's direct order): Fable 5.2 for ALL agents
Session model, builders, evidence runners and every EGM skill/agent run on `claude-fable-5-2` (Agent `model: "fable"`). The Agent hook's allowed-model list gained "fable". Agents started before this order (Sonnet) finish their current task; new agents use Fable.

## REVERT 2026-11-11 16:09Z UTC (owner's direct order in the cloud session): back to the original routing
The two Fable overrides above are withdrawn. Routing is again the table at the top: Opus 5.5 only for egm-brainstorm, egm-draft, egm-resolve; Sonnet 5.5 for every other EGM skill and every egm reviewer agent, builders, evidence runners and the session; Haiku 5.5 only for plain lookups. `handover/tools/egm_model_patch.py` is restored to its version before the override (OPUS = claude-opus-5-5, SONNET = claude-sonnet-5-5) and was run again: it rewrote 89 files in 3 plugin folders. The Agent hook's allowed-model list is again opus, sonnet, haiku ("fable" removed). Agents already running keep the model they were started with until they report; new Agent calls use Sonnet 5.5 (Opus 5.5 for planning skills). Start a NEW session so the skill list is read again.
