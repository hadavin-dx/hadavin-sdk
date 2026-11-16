# L-01: one line for the owner to approve

STATUS: NOT ACCEPTED until the owner replies. Nobody may treat this as accepted. Written Mon 16 Nov 2026 18:51 UTC / Tue 17 Nov 2026 00:21 IST.

**What this is.** Finding L-01 (drift/REPORT.md, row L-01): the Claude session that works with you (the lead) runs as the same Linux user on your laptop as the secret files of the take (the app passwords and keys). Nothing technical stops that session from reading those files, and it can probably decrypt the logins that n8n stores. So the pages no longer say "the lead never sees a secret". They say what people do by procedure: you type your secrets yourself, you do not send them in chat, and the lead works only from masked outputs. This is a working rule, not a lock.

**The one sentence to approve.**
"I know that, on my laptop, nothing technical stops the lead's session from reading the take's secret files; the protection is the procedure (I type the secrets myself, the lead works from masked outputs, and I revoke the app passwords, the HubSpot apps and the model key at clean-up), and the accounts are throwaway and the data made up."

**The exact reply you type in the chat** (pick one, letter for letter):
- `I accept the procedure-only wording for L-01: yes`
- `I accept the procedure-only wording for L-01: no`

If you reply no, the lead builds option (a) instead: the secrets and the take run under a second Linux user that the lead's session cannot read (set-up time before the take; the lead gives the hours first).

**Not built yet (core-hardening item, not part of this wording change):** a hook deny list for the secret folders, with one negative test that proves the lead's session is refused when it tries to open them.
