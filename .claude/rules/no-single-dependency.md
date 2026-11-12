---
name: no-single-dependency
description: "Owner rule 2026-10-31: no part of the core may depend on only one cloud, vendor, tool, product or library; every external dependency sits behind a pluggable kind with a neutral default; audit every design and PR for this proactively"
metadata:
  type: feedback
---

Owner, 2026-10-31: "not just secrets… we need to be not dependent on just one thing, whether it's a cloud or a tool or an individual software or Prompt Guard or Temporal or anything… this kind of thinking should be done for all of them… you only did secrets because I pointed it out… make memory rules and guardrails so you don't miss it in future, and fix what's already in the core or going into it".

**Why:**
- Clients run on any cloud and any tool stack.
- Vendors change prices (Gemini doubling), get acquired, or shut down.
- A single dependency blocks deals and creates lock-in risk.
- My slip: I applied this only to secrets, and only after being told.

**How to apply (every design, plan, PR and review):**
1. **Dependency check is mandatory.** For each capability, list every external dependency (cloud service, SaaS, tool, library, model, protocol). Each must sit behind a pluggable kind, with:
   - a neutral or self-hostable default (open standard or open source, runs anywhere), and
   - at least one alternative kind built or outlined with its trigger.
2. **Vendor SDK imports live only inside that vendor's kind module.** Core logic imports only the core's own interfaces. A repo test enforces this (CI guard).
3. **Prefer open standards:** OpenTelemetry, OIDC, S3-compatible APIs, SQL, MCP, webhooks, PKCS#11 / standard signatures.
4. **Every EGM review prompt and design template includes a "single-dependency audit" item.** A finding of lock-in is at least a 🟡.
5. **Dev and business tooling** (GitHub, CodeRabbit, Cloudflare, Resend, Google Workspace) gets a lighter check: an export path and an alternative noted.
6. **Raise it proactively.** Never wait for the owner to point it out.

Related: [[best-over-rules]], [[vision-reliability]]

**Models (owner 2026-11-01, decision 7):** Claude is the sold default; the `llm` kind needs a second backend or a written outline with its trigger (dated exception, review_by 2027-01-31). Re-verify model ids and prices on the day before quoting.
