---
name: demo-only-folder-and-secrets
description: "Owner 2026-11-02: every demo keeps fake data, demo prompts, fixtures, caches in ONE removable folder; our own free-trial integrations for tests and video; credentials from a secrets kind, never hardcoded"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-02T13:55:39.078Z
---

Owner decision 2026-11-02 (after asking for complete, production-grade, agentic demos in their own public repos, shared hadavin-demos to be deleted after backup, core modules stay only in hadavin-sdk).

**Rule:** each demo repo puts everything that exists only for demos in one folder (`demo_only/`): synthetic data, example/few-shot prompts, recorded model replies, fixtures, seeded caches, sandbox account config templates, video script. Product code never imports from it except through a config-selected loader. A CI check fails if any `demo_only/` path or fake record id is referenced by product code or packaged; to hand a client the repo, delete that folder and the build and tests must still pass.
**Integrations:** use our own free-trial/sandbox accounts (Slack, HubSpot etc.) for tests and the video; throwaway accounts, minimal scopes, short-lived tokens where the vendor allows; trials can expire, so a recorded-replay mode keeps tests running without them.
**Secrets:** never hardcoded. Go through the `secrets` kind: default env/local gitignored file on the laptop; client builds use the client's own manager (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, Vault). Not tied to AWS (no-single-dependency); AWS Secrets Manager costs money, so not used for our demos (zero extra money).
**Model learning worry:** the API does not train on our calls; real risks are fake data shipped in a client build, demo examples left in prompts, shared caches across tenants. Per-tenant data space and the packaging check cover them.
**Why:** owner wants demos production-ready and safely handed to clients. **How to apply:** put this folder rule and check in every demo's design and in the sync/CI checks. Related: [[core-modules-one-source-of-truth]], [[least-privilege-hard-rule]], [[no-single-dependency]].
