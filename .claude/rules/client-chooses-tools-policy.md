---
name: client-chooses-tools-policy
description: "Owner 2026-11-03 - the client decides whether no-code tools (n8n, Make, Zapier, etc.) may touch their data; default is code in the client's own cloud; hybrid = no-code plumbing + our code as the brain; client-own-cloud is OUR rule, not a client or agency demand"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-03T07:45:17.280Z
---

**Decision (owner 2026-11-03, after an EGM brainstorm and four research reports in `egm\no-code-hybrid\`):**
1. The CLIENT decides whether no-code/low-code tools may be used. Ask in discovery, as a recommendation plus a data question: "For this job I would use your [tools] with a small automation tool in between and our own code for the checking. Your data would pass through that tool. Is that OK, or do you need everything inside your own systems?" Never ask "should we use no-code or code?" (sounds unsure).
2. If yes: hybrid. No-code only for plumbing (triggers, connectors, sheets, simple review tables). Our code stays the brain: decisions, approval binding, redaction, budget caps, audit, "never moves money". Client owns the accounts and credentials; named patch owner for any self-hosted tool; failure alerts and a handover pack.
3. If no (the client wants it all-code, or wants everything inside their own cloud): build in code, in the client's own cloud. It costs more time and tokens, so it is quoted higher. Do NOT advertise "no-code is cheaper"; quote per scope; but ALWAYS disclose in writing which tools touch client data and where the data goes (a tool list/schedule in the proposal and contract). Never use a third-party tool on client data without the client's informed yes. If the client says "I don't know", explain the data path in one line and let them choose; do not assume yes for sensitive data.
3b. **DEFAULT FLIP (owner 2026-11-03, later the same day): hybrid is the default.** Use no-code tools where they fit, including for DEMOS (on made-up data, our own free-trial accounts). The all-code route is used only when a client wants their project built that way. High-risk parts (money movement, irreversible actions, redaction, approval binding, audit) stay in our code whatever the route.
4. "Client's own cloud" (bible R44, decisions-2026-11-01-night item 5) is OUR rule (studio practice and the owner's own data decision), not a client or agency requirement. It is now the route for clients who ask for all-code or who refuse third-party tools, not a blanket rule.
5. Core design: core stays tool-agnostic. A small fixed connection door (signed webhook in, governed action API out) plus a template pack of ready workflows. No workflow engine is the default; engines are optional backends behind a kind. Demos on made-up data may use our own free-trial accounts of any tool; never shown to a client as "the product".
5b. Owner 2026-11-03: Docker (and other local runners) are allowed for local tests and demos with n8n or any no-code tool; made-up data only; our own throwaway containers; never touch other containers or Docker Desktop itself.
6. Do not write or test what the tools already do (OAuth, connectors, schedulers, simple tables); DO test our wiring (5-10 end-to-end tests per workflow on made-up data) and the brain.

**Why:** the owner wants fast delivery when an agency or client appears; research showed most pasted tools are cloud-only or licence-limited, so the client must choose; slow projects come from review loops, not connectors.
**How to apply:** discovery question and proposal block in templates (via EGM); two-option quote (owner sets prices); contract tool/data schedule; R445/R446 in the bible; see [[no-single-dependency]], [[least-privilege-hard-rule]], [[agency-terms]], [[decisions-2026-11-01-night]]. Evidence: `egm\no-code-hybrid\concepts_brief.md` and research-1..4. Tool facts expire: re-verify within 90 days before quoting.

**Owner addendum 2026-11-04:** options are listed FIRST, the client chooses, and the choice plus who carries the tool risk go into the quote and contract; no silent default. See [[options-first-then-decide]].


## Owner reminder 2026-11-04
Owner twice: no-code tools are APPROVED by him ("except the no code tools part, that we can use"; "no code is approved by me"). Audits and reviews must never flag no-code tools as wrong; they sit on the tool ladder (rung 3) under the client-chooses-tools and least-privilege rules.
