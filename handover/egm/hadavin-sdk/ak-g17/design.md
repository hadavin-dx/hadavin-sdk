> **PAUSED by owner 2026-11-06 (lead order 49), resume only when a client asks. Saved as found, possibly incomplete (the agent was stopped mid-work). Not reviewed, not to be built. Nothing deleted.**

# AK-G17 sign-in (SSO), sessions, roles and passkey step-up for approvers

*   **Author:** Claude (ticket author session, `egm:egm-draft`, AUTO mode)
*   **Status:** Draft (input to the AK-G17 ticket rounds and the build-start review; not reviewed)
*   **Date:** 2026-11-06 (from 07:50 UTC / 13:20 IST)

--------------------------------------------------------------------------------

**Read this first (honest notes).**
- **What was skipped.** AUTO mode: every section approval gate, the save-location gate and the "author decides architecture" gate were skipped, as the author's brief orders. Where the skill would ask the author to choose, this design takes the shape the FROZEN tickets AK-G16 and AK-G15 took (one kind with a neutral default; framework-free handlers; one identity per function; cut surface; owner-only choices as PENDING LEAD). Each such choice is marked **(AUTO: ...)**.
- **A missing skill file.** The skill says to apply `resources/execution_instructions.md`. That folder does not exist in the installed plugin (`ls` of `skills/egm-draft/` shows no `resources/`), so it was not applied. AK-G16's draft hit the same gap.
- **No Goldfish review.** The brainstorm ran without one (no sub-agent tool in this session; see `concepts_brief.md`). This design has had no independent review either.
- **Code read.** Core on `ce70eb5` at `<repo>/src` (the last commit touching `src/`). Cites were re-read today. Library facts (names, licences, maintenance, API shapes) are from general knowledge and are **UNVERIFIED**: none of these libraries is in `pyproject.toml` (`:14-19`, `:23-44`) or `uv.lock` (grep found none of authlib, saml, xmlsec, webauthn, fido2).
- **Nothing here exists in code.** No sign-in, session, role or passkey code exists in `src/` (grep for oidc, saml, webauthn, passkey, csrf found nothing).

## Overview

The core gets one capability, the **identity kind** (`identity`): it signs a person in through their company's identity provider, maps what the provider says about them (groups, roles, teams) to our permissions, keeps a server-side session, and, for approvers, asks for a passkey right before each approval.

Words used (one meaning each):
- **identity provider (IdP)**: the service that already knows the client's staff and checks their password and MFA: Google, Microsoft Entra, Okta, Auth0, Keycloak, GitHub, or any SAML 2.0 service.
- **OIDC** (OpenID Connect): the open standard where the provider sends back a signed "ID token" saying who the person is. **OAuth 2.0**: the older standard OIDC builds on; GitHub uses it for sign-in without an ID token, so we ask GitHub's API who the person is. **SAML 2.0**: an older XML standard many large companies still use.
- **session**: our own record that a person is signed in; the browser holds only a random id in a cookie.
- **passkey** (WebAuthn): a key kept on the person's phone, laptop or security key, unlocked with a fingerprint, face or PIN. **step-up**: asking for the passkey again right before a risky act (an approval), even though the person is already signed in.
- **tenant**: one client's data space (`TENANT_PATTERN`, `tickets/AK1.md:108`). **role**: a name the client gives a group of staff (for example `sre`). **permission**: one thing our code allows (closed list, below).

## The Problem

Order 47 makes the client portal part of the core: incident history, chat "by their own permissions", and approvals, all at one address. Today nothing in the core knows who a person is:
- AK-G1's `handle_turn` takes a `user_id` the host passes in (`tickets/AK-G1.md:187`); nothing checks it.
- The approval flow trusts the `approver_id` that the channel names (`approvals/requests.py:74-79`, checked against the step's list at `:156`). A Slack click is the only channel today (`approvals/receiver.py:21-38`).
- The owner hard rule says approvers need passkey MFA and an approver is "its own individual role" (`.claude/rules/least-privilege-hard-rule.md`, item 1).

All three plans had cut passkeys and edge authentication (`studio-notes/plan-v1.md:26`, `plan-v2.md:21`, `plan-v3.md:46`; `inventory-C.md:181` defers B12 edge_auth; `inventory.md:14` "Not in core: ... passkeys"). Order 47 reverses the cut for SSO and approver MFA. edge_auth (an AWS API-gateway authorizer, `inventory-C.md:83`) stays cut: AWS-only, and not needed once the core checks sessions itself.

## Goals

1. A person signs in through any of: Google, Microsoft Entra, Okta, Auth0, Keycloak (OIDC), GitHub (OAuth 2.0), or a SAML 2.0 provider. The **neutral default** is OIDC against a self-hosted Keycloak (Apache-2.0, runs anywhere: UNVERIFIED licence read).
2. Every provider sits behind ONE kind; no core code outside the kind's backend modules imports a protocol library (the existing vendor-import guard pattern).
3. Permissions come from config: provider claims -> roles -> permissions, deny by default.
4. Sessions: `__Host-` cookie, `Secure`, `HttpOnly`, `SameSite=Lax`; new id at sign-in and at step-up; idle and absolute expiry; logout deletes the row; CSRF check on every state-changing request.
5. Approvers: a passkey assertion with user verification, made for exactly one `(tenant, approval_id, step, plan_hash)`, used once, within a short time.
6. Tenant isolation: the tenant comes only from the configured provider entry; every session and every check carries it.
7. Tests: a local Keycloak container (OIDC and SAML), hand-built fakes for the other providers, a software passkey in tests; no live provider, no secret, no spend.

## Non-Goals

- SCIM user provisioning: outline only (row V-SCIM).
- edge_auth: stays cut.
- Passkey as the first sign-in factor (passwordless): v1.1 row.
- IdP-initiated SAML (the provider starts the flow): refused in v1; it has no request id to bind, the classic replay hole.
- Single logout across providers (front- or back-channel): v1.1 row; v1 logout ends our session only.
- Keeping provider tokens (access or refresh): discarded right after sign-in.
- Portal pages (JG-4, laptop side), hosting (AK-G16 / JG-4), the approval-screen wiring and the Slack-button change (AK-G14 / JG-5).

## Open Questions (PENDING LEAD; owner-only)

- **Q1 provider list for v1.** Recommended: all seven backends as written, with SAML in its own last sub-PR.
- **Q2 library choice.** Recommended (UNVERIFIED facts): Authlib (BSD-3-Clause) for OIDC and GitHub; python3-saml (MIT, needs the xmlsec C library) for SAML, alternative pysaml2 (Apache-2.0, needs the `xmlsec1` program); `webauthn` by Duo Labs (BSD-3-Clause), alternative `fido2` by Yubico (BSD-2-Clause). All reuse `cryptography`, already pinned at `==50.0.2` in the `aws` and `signer` extras (`pyproject.toml:25-26`).
- **Q3 passkey policy.** Recommended: user verification required; enrolment only with an operator-issued one-time code; step-up valid 120 s and once; an approver with no passkey cannot approve; lost passkey = operator revokes and issues a new code.
- **Q4 the "demo" environment name.** `config.py:317` allows only `dev`, `pilot`, `prod`. AK-G17 code never compares it. Who adds the label, and which safety class "demo" has, is A15's call.

## Critical User Journeys (CUJs)

### CUJ 1: Sign-in through Keycloak (neutral default)
A person opens the portal. No session: `GET /auth/login?provider=kc` makes `state`, `nonce` and a PKCE verifier (all from the library), stores them in a short-lived **login row**, and redirects to Keycloak. Keycloak sends the person back to `/auth/callback/kc?code=...&state=...`. We find the login row by `state`, delete it (one use), let the library swap the code for tokens and check the ID token (signature, `iss`, `aud`, `exp`, `nonce`). We read `(iss, sub)` and the groups claim, map groups to roles to permissions, refuse when no permission results, then create a session row, set the cookie, and redirect to the saved `next` path (same-origin relative path only).

### CUJ 2: An approver approves
The approver opens an approval in the portal. `POST /auth/step-up/begin {approval_id, step}` (CSRF-checked) reads the approval request, checks the session has `approvals.decide` and is in that step's approver list, and asks the library for passkey options whose challenge is random and stored with `(tenant, session, approval_id, step, plan_hash, expires_at)`. The browser asks the passkey. `POST /auth/step-up/finish` lets the library check the assertion (origin, RP id, challenge, signature, user-verified flag, sign count) against the person's stored passkey, deletes the challenge row (one use), rotates the session id, and returns a **step-up proof** id. The approval wiring (AK-G14 / JG-5) passes that proof to `consume_step_up(...)`, which checks every bound field and marks it used before `Approvals.decide` runs.

### CUJ 3: A person from another client
A Keycloak realm for client B is configured for tenant `b`. A session made through it carries tenant `b`. Any request for tenant `a` data with it gets the same "not found" answer as a missing item.

### CUJ 4: Logout and expiry
`POST /auth/logout` (CSRF-checked) deletes the session row and clears the cookie. A request with an expired (idle or absolute) or deleted session gets 401 and the row is deleted.

## Technical Plan (Architecture)

### 1. The kind
`identity` is a new capability with backends:

| backend | protocol | used for | library (UNVERIFIED) | extra |
|---|---|---|---|---|
| `oidc` (**neutral default**, preset `keycloak`) | OIDC code flow + PKCE | Keycloak, Google, Entra, Okta, Auth0 (presets = config data: issuer URL shape and claim names) | Authlib | `sso` |
| `github_oauth` | OAuth 2.0 + GitHub user/teams API | GitHub | Authlib | `sso` |
| `saml2` | SAML 2.0 SP, HTTP-POST binding, SP-initiated only | any SAML IdP (Keycloak in tests) | python3-saml | `saml` |
| `fake` (dev only) | none: returns a configured made-up identity | unit tests | none | none |

Backend interface (one method set; protocol detail stays inside):
- `begin(provider, return_to) -> Redirect(url, login_row)`
- `finish(provider, request) -> ProviderIdentity(issuer, subject, claims: Mapping[str, tuple[str, ...]])`, or raises `SignInRefused(code)`, where `code` is a closed set (`state_unknown`, `token_invalid`, `claims_missing`, `assertion_invalid`, `replayed`, ...).

`fake` goes into `DEV_ONLY` (`backends/table.py:593-602`), so the existing environment refusal (`config.py:365-370`) refuses it outside `dev`. No new environment comparison is written.

**(AUTO: one kind, presets as config, the AK-G16 "neutral default + adapters" shape.)** Google, Entra, Okta and Auth0 are presets of `oidc`, not separate backends: they differ only in issuer, claim names and quirks (Entra's multi-tenant issuer: we refuse the `common` and `organizations` issuers and require the client's own tenant issuer, UNVERIFIED rule from general knowledge).

### 2. Config (one new section `identity`, owned by this package)
```
identity:
  providers:
    <name>:               # pattern [a-z0-9_-]{1,32}
      backend: oidc | github_oauth | saml2 | fake
      tenant: <tenant>    # the ONLY source of a session's tenant
      preset: keycloak | google | entra | okta | auth0 | none
      issuer / metadata_url / client_id / ... (backend settings, validated)
      client_secret_name: <name in the secrets kind>   # never a value
      claim_roles: groups # which claim (or SAML attribute, or "github_teams") holds role names
  role_map: {<provider>: {<claim value>: [<role>...]}}
  roles: {<role>: [<permission>...]}
  session: {idle_s, absolute_s}          # bounds in defaults.py
  step_up: {max_age_s, rp_id, origin}    # rp_id and origin: the portal's own address
```
Permissions are a closed set in code: `incidents.read`, `chat.use`, `approvals.view`, `approvals.decide`, `identity.admin` (revoke sessions and passkeys). An unknown permission or role name is a config error. Issuer, metadata and redirect URLs must pass `url_allowed` (`config.py:153`), and their hosts must be in `egress_hosts` (`config.py:327`).

**No environment name in AK-G17 code (order 47 item 5).** Every behaviour comes from these fields or from the dev-only table. A repo guard test fails if an AK-G17 module contains the string literals `"dev"`, `"pilot"`, `"prod"` or `"demo"`.

### 3. Identity and mapping
- A person's id is `(provider name, issuer, subject)`, stored as `user_id = "sso:" + first 32 hex of sha256(canonical_json([provider, issuer, subject]))` (`models.py:38`, `:46`). It fits AK-G1's `USER_ID_PATTERN` (`tickets/AK-G1.md:165`) and holds no e-mail. E-mail is never an identity.
- Roles: claim values under `claim_roles` -> `role_map[provider]` -> roles -> permissions. Unmapped values are ignored. **Zero permissions = sign-in refused** (`no_permission`), and no session is made.
- Roles are copied into the session at sign-in. A role change at the provider takes effect at the next sign-in, at most `absolute_s` later (stated limit; SCIM would shorten it).
- The approver list in an approval step holds principal ids (`approvals/requests.py:156`). Mapping principal ids to `user_id`s is the wiring ticket's (AK-G14 / JG-5); AK-G17 offers `user_id` and permissions only.

### 4. Sessions and CSRF
Store tables (one migration, number at merge):
- `identity_logins(state_hash PK, tenant, provider, nonce, pkce_verifier, return_to, expires_at)`: lives at most `defaults.IDENTITY_LOGIN_TTL_S` (600).
- `identity_sessions(id_hash PK, tenant, user_id, provider, permissions TEXT[], csrf_hash, created_at, last_seen_at, absolute_expires_at, step_up_at)`.
- `identity_passkeys(credential_id PK, tenant, user_id, public_key, sign_count, created_at, revoked_at)`.
- `identity_challenges(challenge_hash PK, tenant, session_hash, purpose ('enrol'|'step_up'), approval_id, step, plan_hash, expires_at)`.
- `identity_step_up_proofs(proof_hash PK, tenant, user_id, approval_id, step, plan_hash, expires_at, used_at)`.
- `identity_enrolment_codes(code_hash PK, tenant, user_id, expires_at, used_at)`.

Only hashes of the random ids are stored (sha256 of 32 random bytes from `secrets.token_bytes`), so a database read does not give a usable cookie. The session cookie is `__Host-hsid=<id>; Secure; HttpOnly; SameSite=Lax; Path=/`. `Lax` (not `Strict`) because the provider's redirect back is a cross-site top-level navigation; the session cookie is set only AFTER the callback, so the login itself does not depend on it.

Rotation: a new session id at sign-in (any older cookie is ignored and its row deleted), at step-up finish, and at passkey enrolment. Expiry: idle (`last_seen_at + idle_s`) and absolute (`absolute_expires_at`), checked on every request; `last_seen_at` is written at most once per minute (`defaults.IDENTITY_TOUCH_S`).

CSRF: every request other than GET/HEAD must carry header `X-CSRF-Token` whose hash equals `csrf_hash`, AND an `Origin` header equal to the configured portal origin. Both checks, constant-time compare (`hmac.compare_digest`). The token is given to the page by `GET /auth/session`. The callback endpoints are GET (OIDC) or a POST from the provider (SAML); they are protected by the one-use `state` / `InResponseTo` row instead.

`return_to`: only a relative path that starts with a single `/`, has no `//`, no `\`, no scheme, no control characters; anything else becomes `/`.

### 5. Passkeys
- **Enrolment** (needs a session AND a one-time enrolment code issued by `hadavin-sdk identity enrol-code --tenant T --user U`; code shown once, hashed in store, 15 min, one use; AUTO recommendation, PENDING LEAD Q3). The library makes the registration options (attestation `none`, user verification `required`, resident key `preferred`) and checks the response; we store credential id, public key and sign count.
- **Step-up** as CUJ 2. The library checks origin, RP id, challenge, signature, the user-verified flag and the sign count. A sign count that does not grow (when non-zero) refuses and flags the passkey for review (`identity_passkeys.revoked_at` stays null; an audit event is written).
- **consume_step_up(proof_id, *, tenant, user_id, approval_id, step, plan_hash) -> None**: one conditional UPDATE `SET used_at = now WHERE proof_hash=? AND used_at IS NULL AND expires_at > now AND <all fields equal>`; one row changed or `StepUpRefused`. That makes "used once" hold under two parallel requests.
- **Who enforces "approvers need passkey"**: AK-G17 adds `Approvals.decide` a precondition hook the wiring sets (AK-G14 / JG-5). Until that wiring merges, the owner rule is NOT enforced for Slack clicks; this is a coupling and an owner-visible limit, not hidden.

### 6. Handlers (framework-free)
`handle(method, path, headers, body, *, now) -> (status, headers, body)`, the shape of `approvals/receiver.py:21-38`. Paths: `/auth/login`, `/auth/callback/<provider>`, `/auth/saml/acs/<provider>`, `/auth/session`, `/auth/logout`, `/auth/passkey/enrol/{begin,finish}`, `/auth/step-up/{begin,finish}`. Plus `authenticate(headers, *, now) -> Principal(tenant, user_id, permissions, step_up_at) | None` for every portal request. Max body 64 KiB (as `receiver.py:17`); SAML responses above that are refused.

### 7. Identities and rights (one identity per function)
- New database role **session writer**: `SELECT, INSERT, UPDATE, DELETE` on the six `identity_*` tables only; nothing else. The portal's read-only role (`store/migrate.py:24-30`) gets NONE of them (hashes of live session ids must not be portal-readable). The runtime role gets none either. This needs a `session` field in `Grant` and a `--session-role` option in `migrate` (coupling to P3a/P2a's `migrate.py`).
- The web process holds the portal role (reads) and the session-writer login (sessions). It never holds the runtime, executor or approver credentials.
- Provider client secrets: through the secrets kind only (`client_secret_name`), read at start-up; P6b2's secret-boundary lint applies.
- Personal data: the session stores `user_id` (a hash) and permissions; no name, no e-mail. Claims are not stored. The log never prints claims, tokens, codes or cookie values; refusal logs carry the closed code only.

### 8. Tenant isolation
The tenant comes from `providers.<name>.tenant`. `authenticate` returns it; every store read in AK-G17 filters by it; `consume_step_up` compares it. Per order 27 item 56 a deployment serves one client, so normally one tenant; the rule still holds when several are configured (test).

## Alternatives Considered

### Alternative A: hosted broker only (Auth0 or Okta for every provider)
Rejected by author: one paid vendor in the sign-in path breaks the no-single-dependency rule and the AK0 cost rule (order 27 item 53). Keycloak gives the same "one broker" option, self-hosted and free; Auth0 and Okta remain presets.

### Alternative B: a reverse proxy (oauth2-proxy) in front of the portal
Rejected by author for v1: cheap and well used for OIDC, but it cannot bind a passkey to one approval and one plan hash, does not speak SAML, and puts tenant and role mapping outside reviewed core code. Kept as a client-side option: a client may put it in front in addition.

### Alternative C: our own JWT and SAML checks on top of `cryptography`
Rejected by author: the owner's tool-ladder rule (rung 1-2 before code) and the brief forbid writing crypto or XML-signature code. Both protocols have a long record of bypasses in hand-written checks.

### Alternative D: state in a signed cookie instead of server rows
Rejected by author: logout and forced expiry could not revoke a copied cookie; the step-up "used once" needs a server row anyway.

### Alternative E: one kind per protocol (`oidc`, `saml`, `webauthn` kinds)
Rejected by author: order 47 says "every provider behind one kind". Passkeys are not a provider; the passkey library sits behind its own small module boundary (`identity/passkey.py`) with the `fido2` alternative outlined.

### Alternative F: allow e-mail as the link between providers
Rejected by author: account take-over risk when a provider lets a user set an unverified address; `(issuer, subject)` is stable.

## Non-Functional Requirements

- **Security**: security path; extended review; no round cap on the result review.
- **Load**: one session read per portal request (primary-key lookup); one write per minute per active session. Sign-in calls the provider (token and key endpoints); the library's key cache keeps it to one key fetch per key rotation (UNVERIFIED library behaviour).
- **Cost**: Keycloak container in CI only; no paid service; no spend.
- **Failure**: provider down -> sign-in refused with `provider_unavailable`; existing sessions keep working until expiry.

### Future Improvements
SCIM (V-SCIM), single logout (V-SLO), passwordless passkey sign-in (V-PWL), per-tenant signing keys for multi-tenant deployments (GAPS G17, `studio-notes/GAPS.md:25`; note the name clash: GAPS "G17" is tenant separation, a different item from ticket AK-G17).

## Contradictions and reconciliation (draft skill step 6.1)

Brief vs draft: no contradiction. Additions that change an interface or a dependency, listed: (1) a new database role, the session writer, and a `migrate` option (couples to `migrate.py`, P3a/P2a); (2) a precondition hook on `Approvals.decide` (couples to AK-G14 / JG-5 and to `approvals/requests.py`); (3) two new extras `sso` and `saml`; (4) a CLI command `identity enrol-code`.

## UNVERIFIED
- Every library name, licence, maintenance status and API shape in this file (none is in `pyproject.toml` or `uv.lock`).
- Keycloak licence (Apache-2.0) and that its container serves both OIDC and SAML in a dev mode with a realm import.
- Entra issuer rules for multi-tenant apps; GitHub's teams API shape and scope names.
- That `SameSite=Lax` plus a callback-set cookie works in every current browser for the SAML POST binding (the SAML ACS is a cross-site POST: the login row is found by `InResponseTo`, not by a cookie, for this reason).

## Detailed Implementation Plan

### Target Files to Create/Modify
#### 1. `src/hadavin_sdk/identity/__init__.py`, `kind.py` (Create, -a)
Protocol, `ProviderIdentity`, `Principal`, closed refusal codes, permission set, `fake` backend.
#### 2. `src/hadavin_sdk/identity/sessions.py`, `csrf.py`, `handlers.py`, `mapping.py` (Create, -a)
Session rows, cookie text, rotation, expiry, CSRF and Origin check, `return_to` rule, role mapping, `authenticate`, `handle`.
#### 3. `src/hadavin_sdk/identity/oidc.py`, `github.py` (Create, -b)
Only these import Authlib.
#### 4. `src/hadavin_sdk/identity/passkey.py` (Create, -c)
Only this imports the passkey library. Enrolment, step-up, `consume_step_up`.
#### 5. `src/hadavin_sdk/identity/saml.py` (Create, -d)
Only this imports the SAML library.
#### 6. `src/hadavin_sdk/config.py`, `backends/table.py`, `defaults.py` (Modify, -a)
`identity` section; `fake` in `DEV_ONLY`; bounds in its own `defaults.py` block (order 20 item 5).
#### 7. `src/hadavin_sdk/store/migrations/<next>_identity.sql`, `store/migrate.py`, `store/protocol.py`, `store/memory.py`, `store/postgres.py` (Create/Modify, -a; passkey tables in -c)
Tables, `Grant.session`, `--session-role`, store methods.
#### 8. `src/hadavin_sdk/approvals/requests.py` (Modify, -c)
The precondition hook (default none, so today's behaviour is unchanged until wired).
#### 9. `src/hadavin_sdk/cli.py` (Modify, -c)
`identity enrol-code`, `identity revoke`.
#### 10. `pyproject.toml`, `uv.lock` (Modify, -b, -c, -d)
Extras `sso` (Authlib, passkey library) and `saml`.
#### 11. Tests and fixtures (Create)
`tests/test_identity_*.py`; `tests/fixtures/identity/keycloak-realm.json` (made-up users, no secrets: the client secret is generated at container start); hand-built provider fakes with keys generated at test time; a software passkey helper in `tests/` built from `cryptography` primitives (test code only, never shipped).
#### 12. `.github/workflows/ci.yml` (Modify, -b)
One job that starts a pinned Keycloak container and runs the `keycloak`-marked tests.
#### 13. `docs/identity.md`, `CHANGELOG.md` (Create/Modify)

### Verification Plan
The ticket's test rows and mutants; the Keycloak job; the hostile list (alg `none`, key confusion, wrong `iss`/`aud`, expired, nonce replay, state replay, SAML unsigned, signature wrapping, replayed assertion id, IdP-initiated, open redirect, CSRF, fixation, stale or reused step-up, step-up for another plan, UV flag off, cross-tenant).
