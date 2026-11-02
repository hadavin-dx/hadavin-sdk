# Slack approval channel: one app per client

**Rule:** Hadavin never ships one shared, distributed Slack app. Each client creates its **own internal app** in
its own workspace from [`slack-app-manifest.yaml`](slack-app-manifest.yaml).

**Why:**
* Since 2025-05-29 Slack limits apps that are distributed outside the Slack Marketplace to 1 request a minute
  (15 objects) on `conversations.history` and `conversations.replies`. Internal (custom) apps keep the normal
  tiers. A shared app would also put every client's tokens behind one app's rate limits and one revocation.
* An internal app keeps the tokens and the audit trail inside the client's workspace and secrets store.

**Least privilege:** the bot scope is `chat:write` only. The channel posts the approval message, updates it
when decided, and posts expiry notices. It reads nothing from Slack: decisions arrive as signed interactive
callbacks (`POST /slack/actions`, verified with the signing secret). The same endpoint takes the label buttons
on shadow and abstain cards (`agree`, `partial`, `wrong`, `harmful`, `abstain_ok`, `missed`) and the line owner's
"Clear demotion" button; the person is the Slack user in the signed request, matched to `principals.yaml`
(`slack:<user id>`). A user who is not a listed person, or a clear from a person without the `clear_override`
admin right, is refused and nothing changes. The same endpoint takes the signed `stop` and `reset` actions of the
kill switch (admin rights `stop` and `reset`); in pilot and prod this is the only way to reset it, because
`hadavin-sdk limits reset --by NAME` is refused there (a typed name is not a person). `limits stop` still works from
the CLI as the emergency path.

**Rotating the signing secret:** put the new secret in the secrets backend under the configured name and restart the
receiver; requests signed with the old one are refused. Click nonces older than the signature window need no handling.
There is ONE signing secret: rotating it drops every click in flight and makes already-posted buttons unusable until the card is reposted (plan it outside a live labelling hour). The runtime role may DELETE from `seen_actions` (the purge needs it), so a compromised runtime could remove a nonce and replay a captured request within its 5 minutes; `allowed_team_id` and the audit rows are the compensating controls.
Pin the workspace with `policy.allowed_team_id` in `baseline.yaml` so a click from another workspace that shares the
secret is refused; the Slack payload shape is parsed in `approvals/hmac_v0.py` only (another channel kind brings its
own `parse_action`).

A demotion caused by a harmful label can be cleared only by a second line owner and not sooner than
`policy.harmful_clear_min_age_h` (default 24 hours) after it. Each signed click's workspace id and `action_ts` are
stored with its nonce and on the audit rows it causes.

A line owner's "Clear demotion" does not erase a pattern of recent mistakes: the `wrong` labels still inside the 14-day
window keep counting, so one new `wrong` demotes the action again at once while two older ones remain. The demotion
card says "Recent wrongs still count until <date>". This is intended.

**Setup (the client's admin, about 10 minutes):**
1. In the manifest, set `request_url` to the client's receiver host (HTTPS).
2. Create the app from the manifest, install it, and invite it to the approvals channel.
3. Store the **Bot User OAuth Token** and the **Signing Secret** in the client's secrets backend, under the names
   in `backends.channel` (`bot_token_secret_name`, `signing_secret_name`). They never go in the config file.
4. Set `backends.channel.channel_id` to the channel's ID (starts with `C` or `G`).

**Principals:** a Slack approver is `slack:<user id>` in `principals.yaml`. The prefix is the channel kind's
name, so other channel kinds (Teams, email link) use their own prefix and plug in the same way.
