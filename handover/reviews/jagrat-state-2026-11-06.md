# Jagrat and Warden state, 2026-11-06 (saved by the lead from a research agent's hand-back)
Honesty: the agent said it wrote this file, but the file did not exist; the lead wrote it from the hand-back text. The agent re-ran no tests, started no processes, did not grep bible R-numbers. Items marked UNVERIFIED were not read in code.

## 1. Jagrat today
- projects\jagrat: 4 commits on feature/1a-initial (862e424, same as jagrat-j0). Branches j1, j2, j8 sit in worktrees under _local\scratch\wt, unmerged, may conflict (later-fixes L24). No remote and no .github folder in the checkout; the j8 CI workflow never ran on GitHub.
- Main checkout: 29 src files, about 9.9k lines in src\jagrat (WARDEN: about 51k lines). Exists: verifier/grounding/catalogue/playbook "brain" plus a simulated Kubernetes platform (sim_k8s.py). NOT landed: CLI, history, tools, cards, links, report, bounds, sim_db (tests\held_modules.py). README is a skeleton.
- Builder-reported tests (not re-run): 163 on j0, 331 on j1, 413 on j8.
- Core is a pyproject dependency pinned to hadavin-sdk 6608146; Jagrat copies no core modules. pyproject points pythonpath at vendor/portal-kit, which does not exist.

## 2. Owner requirements (2026-11-06) vs state
| Requirement | Status | Evidence / note |
|---|---|---|
| (a) read-only AWS, EKS, ECS, EC2 checks (owner later added RDS, S3 logs, and similar) | MISSING in Jagrat | WARDEN has aws_backend.py, k8s_backend.py, aws_describe.py, iam policies; API reads, not literal kubectl; EC2 coverage UNVERIFIED |
| (b) Slack threaded reply under the Datadog alert + portal link | MISSING | WARDEN chatops.py makes its own thread root per incident; activities.py not fully read (UNVERIFIED) |
| (c) portal chat by permissions | MISSING | WARDEN discuss.py is Slack-channel discussion, design reference only |
| (d) approvals only | PARTIAL | Jagrat policy layer (auto_remediate false, plan-bound approval in environments.yaml and catalog). Approver page, passkey, separate executor missing. WARDEN has passkeys.py, approvals.py, approval_page.py, permits.py; core has approvals\ and actions\ (authorizer, executor); core WebAuthn UNVERIFIED |
| (e) environment "demo" | PARTIAL | config-driven, fails closed on unknown names, but shipped names are dev and prod, fault_environments [dev]. Rename to demo, keep tier names |
| (f) one portal with incident history | MISSING | follow research\port-ui-catalog\CLIENT-PORTAL-SPEC.md sections 2, 3.1-3.3 |
| (g) SSO | MISSING | WARDEN has Slack OpenID sign-in (slack_login.py) and edge_auth.py; core SSO unchecked |

## 3. Promotion to core
- Candidates: facts.py, freeze.py, negation.py (j1 branch only), quarantine.py (overlaps core PRs 42/50), handback.py (blocked on CR-3), WARDEN passkey/approval pieces.
- Licence: the owner stated 2026-11-06 that he holds full rights to WARDEN and it is an older version of Jagrat (memory warden-rights-owner-statement-2026-11-06); L20 closed. Provenance still to be checked per file.
- Do NOT promote: trust, confidence, landed, playbook, catalog, symptom, the verifier's incident-specific rules, incident_signatures.yaml (third-party-derived, provenance unchecked), sim_k8s.py, j8 hygiene/identity tooling.

## 4. Demo-only data
src\jagrat\data\*.yaml and steering words, sim_k8s.py, j2 sim_db/overlays. WARDEN: scenarios\, evals\, fixtures\, k8s\proving-ground and shop-pipeline for a local kind cluster.

## 5. Risks
The real product is mostly absent: everything for (a)-(d), (f), (g) must be built or ported from WARDEN onto core. Unmerged branches may conflict; dead vendor/portal-kit path; cost and public-URL limits (owner memory file).
