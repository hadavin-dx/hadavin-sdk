> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# AK-G17: sign-in (SSO) for the portal, and passkey step-up for approvers

* **Author:** Claude (ticket author session, `egm:egm-brainstorm`, AUTO mode, SHORT)
* **Date:** 2026-11-06 (written from about 07:40 UTC / 13:10 IST; order 47's own stamp "~08:10Z" is the lead's estimate)

**Read this first (honest notes).**
- **This is NOT a Goldfish review.** The skill wants six reviewer lenses run as fresh sub-agents (`egm-synthesizer`). This session has no sub-agent tool, so none ran. The skill says a review in the same context is not a Goldfish review. The "Analysis" below is the author's own stress test. The real independent checks are the ticket rounds and the build-start review (`egm:egm-review`).
- **AUTO mode.** Every interactive gate was skipped (clarifying turns, readiness gate, iteration loop, hand-off gate), as the author's brief orders. Where the skill would ask the author to choose, this brief takes the shape the FROZEN tickets AK-G16 and AK-G15 took (one kind, a neutral default, framework-free handlers, cut surface, owner-only items as PENDING LEAD). Each such choice is named under "Key decisions".
- **Sources.** `LEAD-ORDERS.md` orders 23, 27, 43-47 (order 47 creates this package); `studio-notes/plan-v3.md:46`, `plan-v2.md:21`, `plan-v1.md:26`, `inventory-C.md:82-83`, `:181`, `inventory.md:14`; `tickets/AK-G1.md`, `tickets/AK-G16.md`; core source read-only at `ce70eb5`.

## Overview

Order 47 (owner direction) makes a client portal part of the core, and the portal needs people to sign in with the identity provider their company already uses: Google, Microsoft Entra, Okta, Auth0, Keycloak, GitHub, or any SAML 2.0 provider. After sign-in, what a person may see and do comes from their role (for example "may read incidents", "may chat", "may approve"). An approver must also prove presence with a passkey (WebAuthn) right before each approval: this is an owner hard rule.

Who uses it: client staff in the Jagrat portal (incident history, chat by their own permissions, approvals); the core's approval flow (`approvals/requests.py:146-163`), which today trusts the `approver_id` the channel names; AK-G1's `handle_turn`, which today takes a `user_id` the host passes in (`tickets/AK-G1.md:187`).

## Analysis (author's stress test; not Goldfish)

**What is wrong or risky, first.**
1. **The plan reversal.** All three plans put passkeys and edge authentication out of scope (`plan-v1.md:26`, `plan-v2.md:21`, `plan-v3.md:46`; inventory: `inventory-C.md:181` "Defer: ... B12 edge_auth", `inventory.md:14` "Not in core: ... passkeys"). Order 47 reverses that for SSO and approver MFA only. edge_auth (an AWS API-gateway authorizer, `inventory-C.md:83`) stays cut: it is AWS-only and sign-in in our own handlers makes it unneeded.
2. **Security surface is large and owner-visible.** OIDC, OAuth 2.0 (GitHub is not OIDC for user sign-in), SAML 2.0 and WebAuthn are four protocols with a long history of bypasses (signature wrapping in SAML, algorithm confusion in JWT, open redirects, session fixation). The only defensible stance: we write NO token, signature or XML code. Maintained libraries do the protocol checks; our code does configuration, mapping, sessions and refusals, and the tests attack the seams.
3. **SAML is the riskiest piece and the least needed by the demo.** Jagrat's demo can run on Keycloak OIDC alone. SAML pulls a C library (xmlsec) into the image. Counter-argument: order 47 names SAML 2.0 explicitly and enterprise clients ask for it. Kept, but as its own sub-PR and its own optional extra, built last.
4. **Passkey enrolment is the weak point of "approvers need passkey MFA".** If anyone who signs in through the identity provider can register a passkey, then a stolen provider account can enrol the thief's passkey, and the MFA proves nothing extra. Enrolment needs a second factor that the provider account alone cannot give: a one-time enrolment code issued by an operator command. This is an owner policy choice (PENDING LEAD).
5. **Slack approve buttons bypass the passkey.** Today a signed Slack click decides (`approvals/receiver.py:23-38`). With the owner rule, a click cannot be the final decision for an approver who needs passkey MFA. The fix belongs where approvals are wired (AK-G14 / JG-5); AK-G17 provides the check and states the coupling.
6. **"Environment name is demo".** `config.py:317` allows only `dev`, `pilot`, `prod`. AK-G17 code must never compare the environment name; every behaviour comes from its own config fields or the existing dev-only kind table (`backends/table.py:593-602`). Who adds the `demo` label to config is A15's call (PENDING LEAD).
7. **Tenant mix-up.** If the tenant came from a token claim or a request field, one client's user could reach another's data. The tenant comes only from the configured provider entry; the session carries it; nothing else sets it.
8. **Identity = (issuer, subject), never e-mail.** E-mail addresses change and some providers let a user set an unverified one. Mapping by e-mail invites account take-over.

**Counter-arguments weighed.**
- *"Use a hosted broker (Auth0 or Okta) for everything: one integration."* Rejected: a single paid dependency, against the rule "no single dependency" and the AK0 cost rule (order 27 item 53). Keycloak as the self-hostable broker gives the same "one integration" for clients who want it, free.
- *"Put sign-in in a reverse proxy (oauth2-proxy) in front of the portal."* Strong option for OIDC and cheap. Rejected for v1 because it cannot do the per-approval passkey step-up bound to a plan hash, does not do SAML, and moves tenant and role mapping outside the reviewed core. Written as an alternative.
- *"Store provider tokens to call provider APIs later."* Rejected (cut surface): nothing in v1 needs them; tokens are discarded right after sign-in.

## Goals vs. Non-Goals

* **In-Scope Goals:** one kind `identity` with backends `oidc` (Google, Entra, Okta, Auth0, Keycloak are presets of it, as config data), `github_oauth`, `saml2`, and `fake` (dev only); the neutral default is `oidc` pointed at a self-hosted Keycloak; roles to permissions mapping (closed permission set, deny by default); server-side sessions (cookie flags, rotation, idle and absolute expiry, logout, CSRF); passkey step-up for approvers bound to one approval and one plan hash; tenant isolation; tests against a local Keycloak container and hand-built provider fakes; no live provider, no secret, no spend.
* **Out-of-Scope Non-Goals:** SCIM provisioning (outline only); edge_auth (stays cut); passwordless sign-in with a passkey as the first factor; IdP-initiated SAML; single logout across providers; storing provider tokens; the portal pages themselves (JG-4, laptop side); the Slack/approval wiring (AK-G14 / JG-5).

## Alternatives Weighed

- **Hosted broker only (Auth0 / Okta for all).** Rejected by author: single paid dependency.
- **Reverse proxy (oauth2-proxy) in front.** Rejected by author for v1: no per-approval step-up, no SAML, mapping outside the core. Kept as a written alternative.
- **Our own JWT / SAML validation on top of `cryptography`.** Rejected by author: the owner's tool-ladder rule forbids writing crypto or XML-signature code.
- **Signed cookie sessions (state in the cookie).** Rejected by author: logout and forced expiry cannot revoke a cookie; server-side rows can be deleted.
- **One kind per protocol.** Rejected by author: order 47 says "every provider behind one kind"; the protocols differ only inside the backends.

## Key decisions & staging for next steps

- K1 One kind `identity`, backends `oidc`, `github_oauth`, `saml2`, `fake`; providers are config entries; Keycloak is the neutral default. (Shape taken from AK-G16's "one neutral default, adapters as rows".)
- K2 Libraries, all UNVERIFIED until read from a lock file: Authlib (OIDC/OAuth client), python3-saml (SAML, alternative pysaml2), `webauthn` by Duo Labs (alternative `fido2` by Yubico). Final choice is PENDING LEAD.
- K3 Handlers are framework-free `(method, path, headers, body) -> (status, headers, body)`, the shape of `approvals/receiver.py:21-38`. Hosting is the portal's (JG-4 / AK-G16).
- K4 Server-side session rows; the cookie holds only a random id; the store keeps its hash.
- K5 Step-up: a passkey assertion whose challenge binds `(tenant, approval_id, step, plan_hash)`, valid for a short config time, used once.
- K6 Passkey enrolment needs an operator-issued one-time code (recommended; PENDING LEAD).
- K7 Four sub-PRs: -a sessions/roles/CSRF with the fake backend, -b OIDC + GitHub, -c passkey step-up, -d SAML. SCIM outline only.
- K8 Security class; extended review, no round cap on the result review.
