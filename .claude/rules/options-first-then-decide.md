---
name: options-first-then-decide
description: "Owner HARD guardrail 2026-11-04: for every client build, list the tool options and costs FIRST, the client chooses, the choice and who carries the tool risk are written in the quote and contract; never fall back to a default by mistake"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3c13c170-55b8-4c77-8cca-2988a10a077d
  modified: 2026-11-03T18:59:37.521Z
---

Owner 2026-11-04 (after we agreed that vendor tools such as Clay, Retell or ElevenLabs may be used when a client asks, case by case): "keep this in memory, rules, guardrails wherever needed, so that we first give options and decide, otherwise we will just go with defaults later by mistake."

**The rule (client builds):**
1. Before any design or build for a client, present the tool OPTIONS with cost and risk in plain words: (a) the client's own tool(s), (b) a vendor tool used directly, (c) our code behind a swappable layer (our safe default). Say the plain trade-off: one vendor tool can break, change price or shut down.
2. The CLIENT chooses; the client pays for their own licences (never ours; [[owner-answers-2026-11-03-portal-licences-handles-history]]). Decide per client by time, budget and the client's comfort.
3. The choice is written in the quote AND the contract (tool schedule): which tool, who pays, who carries the risk if that tool breaks or changes, and what we do then. A later tool problem must never be our surprise.
4. If the client does not choose, we do NOT silently apply the default: we ask once, write the answer down, and only then continue. "Default" is the swappable layer, used only after the client has seen the options.
5. Demos (video, throwaway) may use any tool directly; made-up data only; no client data.
6. The no-single-dependency rule ([[no-single-dependency]]) stays unchanged for the core and for what we ship; a client may accept one-tool risk in writing.

**Why:** a default applied later "by mistake" can leave a client tied to one tool without having been told, and the risk would fall on us.
**How to apply:** discovery question and quote block (template `templates\project\scoping.md`), contract tool schedule, sub-agent preamble rule 16, project CLAUDE.md; link [[client-chooses-tools-policy]], [[tool-ladder-before-code]], [[demo-order-intake-then-refunds-then-outreach]].
