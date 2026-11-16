---
name: least-privilege-hard-rule
description: "HARD RULE (owner 2026-11-01): every role, user, service account, agent, approver, key and credential on AWS, Azure, GCP or anywhere else gets only the exact read/write it needs, nothing more; separate identities per function; passkey-protected approver identity; agent access scopes and masking"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-01T11:46:35.755Z
---

Owner 2026-11-01: "make sure the roles or whatever you are creating in AWS or anywhere are all with strict tight restriction, read only ... the approver after that, passkey also should be its own individual role/user/service ... double check everything has only what it requires, read or write which they really require ... keep this as a very, very hard rule in memory and all other places, even in future, anywhere: Azure, GCP or any other place ... also what agents can have access to, and masking."

**Why:** the studio sells "mistakes cannot cause damage"; one over-broad role or shared key is exactly how earlier-project incidents and the laptop-compromise lesson happen ([[laptop-compromise-lesson]]). Clients never get long-lived keys.

**How to apply (every design, PR, review, IaC, console click and client engagement):**
1. **One identity per function.** Separate role/user/service identities for: agent runtime (reads), executor (the single write path), approver (human, passkey/WebAuthn MFA, its own identity, cannot also be requester or executor), audit writer (append-only), audit reader, migrations/DBA, CI deploy (OIDC, no stored keys), breakglass (dormant, disabled, alarmed), humans (viewer/operator/approver/admin). No shared identities, no shared keys, no "just use admin".
2. **Least privilege by construction.** Start from deny-all. Read-only by default. Write only where the function requires it, scoped to exact resources (ARN/resource ids, prefixes, tables, namespaces), exact actions (no `*`, no `Resource: *` except where the API forces it and then conditioned), exact conditions (source VPC/IP, MFA present, tags, time, session duration). Permission boundaries / SCPs (AWS), org policies (GCP), Azure RBAC with deny assignments and PIM. Short-lived credentials only (STS/OIDC/workload identity); no long-lived access keys; rotate/expire anything that exists.
3. **Agents:** an agent sees only the tools, tables, columns, rows, documents and hosts its job needs (allowlists, per-agent manifests, read-only DB role with column-level grants and row filters, egress allowlist). Agents never hold approver or executor credentials. No agent can widen its own scope or read secrets. A tool that reads a cluster or holds a credential needs a probed read-only source or a named inventory entry.
4. **Masking by default.** PII/secrets/identifiers are masked or tokenised before the model, before logs and before audit (redaction map held separately, short retention, role-gated); structured fields masked per column; masking rules tested with canaries; no raw production values in prompts, logs, traces, exports or demo data.
5. **Prove it.** Every IaC/role change ships with: the policy text, a least-privilege justification per action, a negative test (the identity is denied what it must not do), an IAM Access Analyzer / policy-simulator / equivalent check, and a list of what each identity can read and write. Review for over-breadth is mandatory (EGM + independent), security path uncapped.
6. **Audit existing things** whenever touched; fix over-broad ones (do not defer). Report identities and their permissions masked (no account ids, no keys).
7. Applies to AWS, Azure, GCP, Cloudflare tokens (scoped API tokens per zone/action), GitHub (fine-grained tokens/apps, least scopes, rulesets), databases, SaaS, and any future platform. Applies to the studio's own laptop sessions and to client deliveries. Changing this rule needs the owner's explicit yes.
Related: [[no-single-dependency]], [[approvals-2026-11-01]], [[class-level-fixes]].
