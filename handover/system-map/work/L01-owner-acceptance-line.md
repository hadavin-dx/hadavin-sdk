# L-01: one line for the owner to approve

STATUS: NOT ACCEPTED until the owner replies. Nobody may treat this as accepted. Written Mon 16 Nov 2026 18:51 UTC / Tue 17 Nov 2026 00:21 IST; reworded after a fresh reader's review the same evening.

**What this is.** Finding L-01 (drift/REPORT.md, row L-01). Two things run on your laptop under the same Linux login as the secret files of the take (the app passwords and keys): (1) the checking program you start, and (2) the studio lead's Claude session (the "lead"). Nothing technical stops either of them from opening those files. A session that can open the files can use the passwords and keys in them, and nothing afterwards proves that it did not. The lead can also probably decrypt the logins that n8n stores (inferred, not checked). The exposure lasts from the moment the files are made until you delete them (clean-up step I.6, the `shred` step), not only until you revoke the passwords. So the pages no longer say "the lead never sees a secret". They say what people do by procedure: you type your secrets yourself, you do not send them in chat, and the lead works only from masked outputs ("masked" = shown with the secret part hidden). This is a working rule, not a lock: a procedure only, nothing enforces it.

**The paid model key (money, not made-up data).** The accounts of the take are throwaway and the data is made up. The paid model key is different: if it sits in a file that the program or the lead can read, the exposure is real money, up to the prepaid credit on the model account (US$189 according to the lead's answer of 2026-11-16; UNVERIFIED for this key; no program enforces a ceiling). STUDIO LEAD TO FILL: does the model key sit in a readable secret file or somewhere else? (Same question as step A, part 1, of inputs/OWNER-STEPS-realrun-v5-core-hardening.md, line 77.) Do not reply yes until the studio lead has answered it.

**The one sentence to approve.**
"I know that, on my laptop, nothing technical stops the checking program I start or the studio lead's session from reading the take's secret files and using the passwords and keys in them, and nothing afterwards proves it did not; the protection is a procedure only (I type the secrets myself, I do not send them in chat, the lead works from masked outputs), the exposure lasts until I delete the files at clean-up, the accounts are throwaway and the data made up, and the paid model key is real money up to the prepaid credit if it sits in a readable file."

**The exact reply you type in the chat** (pick one, letter for letter):
- `I accept the risk that nothing technical stops the studio lead's session and the checking program from reading my take secret files: yes`
- `I accept the risk that nothing technical stops the studio lead's session and the checking program from reading my take secret files: no`

**What "no" costs.** If you reply no, the lead builds option (a): the secrets and the take run under a second Linux user that the lead's session cannot read. That is extra set-up time before the take; the studio lead tells you the hours first, and it may move the take date.

**How far one reply goes.** Step A of the steps file asks for its own written reply for each run, naming the run name (steps file, line 77: one answer covers ONE run unless the studio lead says in writing that one answer covers all runs). This L-01 reply does not replace that per-run reply. STUDIO LEAD TO FILL: does your L-01 reply, once given, cover every run of this video, or one run? (No file here says which; work/LEAD-ANSWERS.md only says the line is written for you to approve.)

**Not built yet (core-hardening item, not part of this wording change):** a hook deny list for the secret folders, with one negative test that proves the lead's session is refused when it tries to open them. STUDIO LEAD TO FILL: will it be built before the take? No file here gives a date. Even when built, it covers only the lead's session, not the checking program.
