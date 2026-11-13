# Cold-reader report d1 (EVIDENCE RUNNER / COLD READER)

Reader: a freelancer who wants to adopt this lead desk for a client. Read in the order README.md, SECURITY.md, docs/limits.md, contract.md. I opened no other file. I only listed the directory to confirm that the four files exist.

Studio folder: it does not exist in this container, so no bible lookup was done and no R-numbers are cited.

What I did NOT do: contract.md has 317 lines and about 15,000 words, and docs/limits.md has about 7,000. I read both fully. I list each LINE that has a problem and quote its worst sentence. Where one line holds several bad sentences I give one row and say so. I did not split every sentence of the densest spec lines into its own row, so the counts are rows, not sentences. I did not check any claim against code or tests (not allowed for a cold reader).

Problem types: (a) unclear, (b) unexplained jargon or abbreviation, (c) contradiction, (d) promises more than the text supports, (e) too long (about 60 words or more, nested brackets).

Words that recur and are never explained in these four files, so I give a short form here instead of repeating it in every row: "AI step" (what it does is never said in README; only contract.md says it answers hot, warm or cold), "lead book" and "book" (README says "the desk's records"), "claim" and "drive" (contract.md), "capability" and "mode" (used for keyed or blind), "send key", "loopback", "bind", "thread", "envelope", "step route", "review routes", "lead flow".

## README.md

| Location | Exact words (short) | Type | Suggested plain words |
|---|---|---|---|
| README.md:8 | "the AI step" | b | Say once what it does: "a stand-in that gives each lead a label hot, warm or cold (the labels are pre-written)". Today README never says what the AI step is for. |
| README.md:6 vs :100 vs docs/limits.md:22 and :77 | ":6 the desk never sent a second email for the same lead by itself" / ":100 The desk does not send a follow-up twice by itself" / limits:22 'Not claimed: "never sent twice" in general' / limits:77 'on a keyed mail system it is sent again with the same key' | c, d | Say the same fact in one way: "In our tests with the stand-in mail system, the desk never made a second email. After an unclear result it can send the same email again with the same send key; the stand-in mail system then ignores the repeat. A real mail system may not." |
| README.md:20 | "through the other door" | b | Define "door" before use: "through the other entrance (web form or webhook)". "Door" is defined only at :38. |
| README.md:22, :65 vs :118 | "The demo mail system holds exactly one email" vs "one reminder email is sent when a lead is still before the 'reminder until' step after the wait" and "The demo start scripts switch it on" | c, d | The demo scripts switch the reminder on (:118), the reminder is a second email, and the wait is never stated in these four files. So "exactly one email" holds only if you check before the wait ends. Say: "check the outbox within N seconds, before the reminder email is due" (N from settings). |
| README.md:28 | "Same lead means the same email address, trimmed of spaces and lower-cased, nothing more." | d | contract.md:252 adds refused characters (the Kelvin sign), no Unicode normalisation, and invalid addresses that go to review. "Nothing more" is wrong. Say: "...and an address the desk accepts (see contract.md for what it refuses)". |
| README.md:32 | "Desk's records: its SQLite database file" | b | "its database file (a SQLite file: a single-file database)". Also "records" here vs "lead book" (SECURITY:3) vs "book" (contract) is one thing under three names. |
| README.md:34, :36 | "Request id ... The portal calls it 'Request number'." / "another request number" | c | Same thing is called request id, request number (README), request reference (limits:105), source_ref (contract), receipt number (limits:113). Pick one: "request number". Say "receipt number" only for the desk's own note. |
| README.md:36 | "`review` (incomplete, a person must look)" | a, d | Also used for invalid email addresses and forbidden characters (contract:244, :246, :252) and for internal faults. Say: "`review` (the request is incomplete or has a value the desk will not store; a person must look)". |
| README.md:39 | "a keyed mail system recognises a repeat of the same send key" | b | "send key" is not explained. Say: "the desk gives every email one fixed label (the send key); a keyed mail system sends only once for a label it has seen". |
| README.md:40 vs contract.md:61 | "UNKNOWN: the desk cannot tell whether a follow-up email left." | c, d | contract:61 and :287 also use unknown when the desk cannot tell whether the CRM row was written (crm_unconfirmed). Say: "...whether the email left, or whether the CRM row was written". |
| README.md:41 | "Crash point: one of ten named moments ... (and an eleventh, N1...)" | e, a | Split: first sentence says what a crash point is; second gives the example D2. N1 is named before the reminder is explained. |
| README.md:42 | "Reaper: ... settles receipts left open." | a, e | "settles" is unclear. Say: "decides receipts that were written but never got an answer". The sentence is about 60 words with two lists. |
| README.md:43 | "Webhook: a web address that starts a workflow" | c | Here it means an n8n address. At :38 and in contract.md ("webhook" as a door) it means a kind of incoming request. Say: "Webhook (door): requests sent by another program. In n8n it is also the name of an address that starts a workflow." |
| README.md:47 vs :130 | "Python 3.12 or newer" vs "any other combination was not tried" (3.12 Linux, 3.13 Windows) | c, d | Say: "Python 3.12 or 3.13 (only these were tried)". |
| README.md:51 | "Open ONE terminal there and run ... (the first lines make a private Python folder ...)" | e | About 75 words with a bracket. Split into three short sentences. |
| README.md:60 | the one-line comment after the `for i in 1 2 ...` command | e | About 50 words after a loop on one line; put the expected result on its own line. |
| README.md:68 | "Run both scripts with bash ... busybox sh, zsh" | b, e | "dash", "busybox sh" are unexplained, 90+ words. Say: "Run the scripts with `bash scripts/...`. If you use `sh` on Debian or Ubuntu they stop with 'run this script with bash'." |
| README.md:73 | "Set-ExecutionPolicy ... a policy that blocks all scripts would stop them" | e, a | Unclear who sets which policy. Say: "This lets this window run local scripts. If your organisation blocks all scripts, see the next paragraph." |
| README.md:88 | "The desk has no page at / or /health ... `/` is reached only by one odd request in tests/..." | e, d | About 190 words, one sentence of test names. Meaning: "The desk answers 404 for unknown addresses. A plain `GET /` was not tested." Also mixes the Windows port wait and the `/fake` note in the same paragraph. |
| README.md:90 | "The reset script refuses ... (exit code): 2 ... 3 ... 4 ... 5 ... 6" | e, b | About 150 words. "pid file", "lock file", "exit code" unexplained. Use a table: code, what it means. Also the desk has its own exit codes (limits:121) with different numbers; say "reset script exit codes". |
| README.md:99 vs limits.md:69 | ":99 Of the ten, nine are simulated by an exception; only one (D2) is a real process kill" vs limits:69 "simulated ... for all ten crash points ... A real process kill ... only at D2" | c | One says nine simulated plus one real, the other says all ten simulated plus a real kill at D2. Say once: "All ten were simulated by an exception in the program. D2 was also tried with a real process kill." |
| README.md:99 | "The tests assert at most one lead, one CRM row and one email." | d | contract.md:289 says "no test covers every path". Say: "...at the crash points the tests cover (contract.md:289 says not every path is covered)". |
| README.md:104 | "Only scripts/hubspot_probe.py touched a real service ... no log is shipped, so the result cannot be checked" | d | For an adopter: the HubSpot adapter was never tested against a real account by anything you can run. Say that first, in plain words: "No test here talks to a real CRM." |
| README.md:106 | "two people sharing one address are one lead" | a | Say: "If two people use the same email address, the desk treats them as one lead." |
| README.md:107 vs :120, SECURITY.md:28 | "listens on this computer only unless you change that" vs "refuses any other DESK_BIND" with a real service | c | Both true but read as two rules. Say: "It listens on this computer only. You can change that for the demo. With any real service connected the desk refuses to start on any other address." |
| README.md:108 vs docs/limits.md:115 vs contract.md:122, :222 | ":108 lead names, email addresses and phone numbers are hidden ... switch 'Hide names and email addresses'" | c | limits:115 and contract:122 also mask messages and request numbers; contract:222 calls the switch "Hide email addresses"; contract:222 says `masking` is `false`. One list, one switch name. |
| README.md:108 | "the answer the page reads from the desk still carries every value, names included" | a | "the answer the page reads" is unclear. Say: "the data the desk sends to the page still holds every value, so anyone who looks in the browser's developer tools sees them". |
| README.md:109 | "Loads of 10,000 requests were not run." | a | "Loads of" is odd. Say: "A load of 10,000 requests was not tried." |
| README.md:115 vs :118 | "They are off in the desk itself; the demo start scripts switch on the lead flow." | a, c | "They are off" then "switch on" in one line. Say: "Both features are off unless a setting turns them on. The demo scripts turn on the lead owner, stage and reminder feature." Also "lead flow" is a new name for the feature at :118. |
| README.md:117 | "a repeat that brings new details can be approved or denied" | a | A repeat of what? Say: "a second request for the same email address with new details (for example a new phone number) can be approved or denied by a person chosen from a list". |
| README.md:118 | "can be moved forward through named lead stages, and one reminder email is sent when a lead is still before the 'reminder until' step after the wait (the follow-up state is not looked at)" | a, b, e | "lead stages", "reminder until step", "the wait" are not explained and no length is given. About 85 words. Say: "Each new lead gets an owner and a stage. If, after the waiting time set in the file, the lead has not reached a stage named in the file, one reminder email is sent. The reminder does not depend on whether the follow-up was sent." |
| README.md:120 | WARNING paragraph, about 250 words | e, b | "loopback address", "step route", "review routes", "stage copy" unexplained. Split into: what is written, what can happen, what you must do first, what the desk does not protect. "Loopback" = "this computer's own address (127.0.0.1)". |
| README.md:122 | "handling of later messages by an AI step" | b | "later messages" is not defined here (limits:107 defines it). Say: "a later message = a second request for the same email". |
| README.md:126 | "three n8n workflows that put the desk behind n8n" | a | "behind n8n" unclear. Say: "three n8n workflows that send leads to the desk". |
| README.md:130 | "A full run was last timed at 16 minutes 33 seconds on an earlier, smaller set of tests ... has not been timed on the current set" | e, d | A number that tells you nothing about the current tests. Say: "A full test run takes about 17 minutes or longer (last measured on a smaller test set)". About 120 words in the paragraph. |
| README.md:141 | "(this script was not run against real services: only scripts/hubspot_probe.py touched a real service ...)" | a | Confusing: describes a script that "tries the desk against a free HubSpot account" and says it was not run. Say: "This script has never been run, so it is untested." |
| README.md:142 | "contract.md: the exact replies the code and tests agree on" | c | contract.md:5 says a mismatch "is a bug to report" and contract.md:241 says the table is "wrong and fixed". "Agree on" claims more than both say. Say: "the replies the code is meant to give". |
| README.md:161 vs :7, :12 | ":7 It is not software to install for your business" / ":12 who it is for: ... n8n freelancer" / ":161 you may not ... use it commercially or offer it as a service" | a | A freelancer adopting it for a client needs one plain line: "You may not use it for a client or offer it as a service without written permission." Today this is split over three places. |

## SECURITY.md

| Location | Exact words (short) | Type | Suggested plain words |
|---|---|---|---|
| SECURITY.md:3-5 | "binds to this computer's own address, has no login (the portal also has buttons that write to the lead book: see docs/portal.md)" | b, a | "binds", "lead book" unexplained. Say: "listens only on this computer's own address, has no sign-in, and the portal has buttons that change the desk's records". |
| SECURITY.md:5 vs README.md:120 and docs/limits.md:142 | "Do not put real customer data into it." vs "Required before you point this at a real CRM ... the first test uses one made-up contact" | c | The warnings tell you how to connect a real CRM. Say what is allowed: "Use made-up data. Real customer data is not meant to go in, even when a real CRM is connected, until a person has done the checks in README." |
| SECURITY.md:9-10 | "or use GitHub's private vulnerability reporting: the 'Report a vulnerability' button" | d | A reader cannot tell whether the button is switched on. Say: "if the button is shown on the Security tab". Also a sales address for security reports (sales@hadavin.com) with no note that it is monitored for security. |
| SECURITY.md:15 | "Only the latest state of the `main` branch is supported." | a | "latest state" unclear. Say: "Only the newest commit of the `main` branch is supported." |
| SECURITY.md:19-28 | the whole "No secret is meant to be in this repository" bullet, about 420 words in one bullet | e | Split into: (1) scans; (2) what leaves the computer (four settings); (3) how to keep secrets (file, not command line, not variable); (4) the one exception; (5) bind rule. |
| SECURITY.md:19 | "runs a secret scanner over the files and over the whole history" | d, c | States the job runs; limits.md:72 says "no run of them is claimed here"; SECURITY:31 says "no result of them is claimed". Say: "A workflow file is set up to run a scan; no result is stored here." |
| SECURITY.md:22-26 | "`DESK_QUALIFIER=live_claude`", "`DESK_OUTBOX=smtp_provider`", "IMAP", "key file", "spend caps" | b | IMAP and SMTP unexplained; "live_claude" is never said to mean a real Anthropic model. Say: "reads mailboxes (IMAP, the mail-reading protocol)". |
| SECURITY.md:26 | "keep them in a file, not in a variable. The one exception ..." | b, a | "variable" = environment variable, not said. Say: "not in an environment variable". |
| SECURITY.md:28 | "so a stand-in can never be a real host" | d | Overclaims: the setting accepts this computer's own address, which can forward to a real host. Say: "the setting refuses any other address, so a stand-in is not pointed at a remote host by mistake". |
| SECURITY.md:28 | "anyone who could reach the port could create contacts in the CRM, send mail or spend model money" | b | "model money" unclear. Say: "or use up the paid AI model budget". |
| SECURITY.md:31-32 | "they do not keep anything private once it has been published" | a | What is published? Say: "they cannot remove a secret that was already pushed to a public place". |
| SECURITY.md (whole) | no statement of what to do with an exposed key | d | The file says "report it as above" but gives nothing for the adopter whose own key leaked. Not fixable by wording alone; add one line: "revoke the key at the provider first". |

## docs/limits.md

| Location | Exact words (short) | Type | Suggested plain words |
|---|---|---|---|
| limits.md:3 | "the internal names in it (settings, functions, test names) are there so a reader can find them" | a | Say who finds what. It reads as an apology. "Setting names, function names and test names appear in code font so you can search the code for them." |
| limits.md:5 | "Known gaps are in the last bullet of 'Load and limits' below." | c, d | That bullet (:99) covers only the burst figures, but gaps are listed in many other bullets (:22-:82). Say: "Gaps in the load figures are in the last bullet of 'Load and limits'; other gaps are in 'What is not claimed (in full)'." |
| limits.md:9 | "one computer and one process" | b | "process" unexplained. Say: "one program running on one computer". |
| limits.md:11 | "At most a few calls of each kind run at once." | a | :40 says 4, 8, 8 and 4. Say: "At most 4 AI calls, 8 CRM writes, 8 sends and 4 reads of the mail or CRM setting run at once." |
| limits.md:12-14, :24, :75 | "UNKNOWN", "blind mail system", "keyed mail system", "put back" | b | Defined only in README. This page says it is "the detail behind" README but uses the terms cold. Say: "put back = the background job moves the follow-up back to waiting". |
| limits.md:17 | "Everything below was measured once, on one Windows computer" | d | Most of the page is rules read from code, not measurements (:31-:63, :86-:88). Say: "The load figures were measured once ...". |
| limits.md:22 vs README.md:6, :100 | "'Never silently lost' and 'never sent twice' in general. Exactly-once delivery, production fitness, a legal opinion." | a, c | A sentence fragment with no verb: what is not claimed? And README:6 claims the desk "never sent a second email by itself". Say: "We do not claim that no lead is ever lost, that no email is ever sent twice, or exactly-once delivery." |
| limits.md:28-30 | "ask a real AI model for a label ... a per-run cap and a total cap" | a | What label, cap of what? Say: "...for a label (hot, warm or cold) ... a maximum cost per run and a maximum total cost". |
| limits.md:31-39 | "Every call ... is bounded by the desk itself (`Desk._bounded`) ..." | e, b | About 220 words. "helper thread", "abandoned", "bounded", "internal:ModelTimeout" unexplained. Split into: what a time-out does for AI, CRM write, keyed send, blind send. |
| limits.md:35 | "an AI timeout uses up one of the 5 automatic tries ... a person's Retry starts the count again at try 1, so one lead can be tried more than 5 times in all" | e | Three facts in one sentence with brackets. |
| limits.md:40-46 | "At most 4 AI calls, 8 CRM puts ... `ADAPTER_WORKER_CAPS` ... the place is reserved before the helper thread starts" | e, b | About 200 words. "capability read" unexplained, "place" unclear ("a slot"), "stalled" shows up without definition. |
| limits.md:47-52 | "A CRM copy of the lead's stage waits for that lead's own hung call." | e, a | One bullet, about 230 words; the wait-sequence sentence is 90 words and has two nested brackets. Also "CRM status ... behind for good" and "`crm_error`" unexplained. Say the waits as a list: 10 s, 60 s, 180 s, 420 s. |
| limits.md:53-54 | "Wait until `hung_workers` is back to 0" | a | `hung_workers` has four counters (contract:214: model, crm, send, refresh). Say: "until all four counts in `hung_workers` are 0". |
| limits.md:55-59 | "Time budget. A sending row is put back ... A constant that does not hold this ends with a Python error ..." | e, a | About 200 words. "stuck grace", "strictly", "constant that does not hold this" unclear. Say what must be true (9 s plus 15 s is under 25 s) in one sentence, then what happens if you change it. |
| limits.md:59 | "`db_path` of exactly `:memory:` ... A name such as `file::memory:` is not special" | e | About 110 words in a bracket tail. For an adopter: "The database path must be a real file; `:memory:` is refused." |
| limits.md:60-62 | "If the database stays locked when the answer is stamped or its label written, the answer is thrown away" | a | "stamped" and "label written" unclear. Say: "If the database is still locked when the desk tries to save the AI answer, it discards the answer and counts the try as used". |
| limits.md:63 | "A late answer from an abandoned mode read (the capability of the CRM or the mail system)" | b | "mode", "capability" mean keyed or blind. Say: "A late answer about whether the CRM or mail system is keyed or blind cannot overwrite a newer answer." |
| limits.md:65-67 | "A stopped desk does not wait ... The figure of one byte every 1.9 seconds was not tested here." | e, a | The last sentence refers to a figure that was never introduced. About 150 words in the bullet. |
| limits.md:68 | "The desk assumes the follow-up is the only thing that sends mail for a lead's send key." | a | Say what to do: "Do not let another program send mail under the same send key." Define send key. |
| limits.md:69-70 | "(from the author's own run; the number of runs is not recorded here ...) The author reports that every follow-up ended sent, so they back the after-load checks and the retry story, not the UNKNOWN path." | a, d | "they back" unclear. Say: "so this run supports the checks run after a load, but does not show the UNKNOWN path works." |
| limits.md:72 | the "Run on two systems ..." bullet, about 330 words | e, c | Counts 2449, 2462, 2464, 2465 and different skips; the text itself says the numbers disagree. Say: "Test results exist for older commits only, no log is shipped, and nothing was re-run on this commit." |
| limits.md:73 | "n8n crashing before the request reaches the desk. Other n8n versions or set-ups: no n8n-only result is claimed here ..." | a | Fragment. Say: "We do not claim anything about what happens if n8n crashes before the request reaches the desk, or about other n8n versions." |
| limits.md:74 | "a lead is reminded once after the wait if its step is still before `reminder_until` ... because the reminder asks whether the lead moved on" | a, b | "step", "reminder_until", "the wait" are not explained; "the reminder asks whether" is a human reading. |
| limits.md:75-76 | "A person answering 'not sent' wrongly ... (then a second email can go). UNKNOWN items stay unseen unless someone opens the review list." | a | Fragment. Say: "If a person wrongly answers 'not sent' on a blind mail system, a second email can go out. Nobody is told about UNKNOWN items; someone must open the review list." |
| limits.md:77 | "A follow-up stuck in `sending` ... (a clock step of 30 s or more forward ... `_restamp_future` ...)" | e | About 190 words and one very long bracket. |
| limits.md:78-81 | "Exceptions, case by case" and the 10 + 27 + 18 = 55 s sum | e, b | About 350 words. Says the pass can run longer than the 30 s grace, then says that is fine. For an adopter: "A pass of the background job can take up to about 55 s." |
| limits.md:86 | "What `/counts` adds up ... `decide_transient_errors` ... `decide_integrity_errors` ..." | e, b | About 220 words; "disk fault", "open", "ok" overlap with "open files". Say "open receipt". |
| limits.md:88 | "Rules of the desk's records ... `INSERT OR REPLACE` ... the CHECK on receipts" | b, a | "triggers", "CHECK", "`INSERT OR REPLACE`" are SQL jargon. "A desk's records" (the database). "Not proven by any test: the checks that SQLite cannot add ..." is unclear. |
| limits.md:92 | "settles to 0" | a | What goes to 0? Say: "before the count of pending follow-ups returns to 0". |
| limits.md:93 | "The waiting line is 1024 connections (`LISTEN_QUEUE` ...)" and the unlogged comparison with a "plain stand-alone web server on the same laptop" | b, d | "waiting line" = queue of connections the system keeps; "laptop" vs "Windows computer" elsewhere. A comparison nobody can check is stated as support. |
| limits.md:95-98 | retry rule, 503 text, Content-Length rules | e, b | Each bullet is 100-150 words; "Content-Length", "408", "413" explained nowhere. |
| limits.md:103 | "The idle-connection behaviour below is covered by the named test." | a | Which test? It is named 20 lines later (:124). |
| limits.md:105 | "refused as a bad envelope, too large, a body that timed out or a bad request reference ... called `door` in the data" | e, b | "envelope" unexplained; "refused_at_door" and "door" (source) are two meanings. |
| limits.md:112-116 | the masking bullets (the :115 bullet is about 330 words) | e, c | Same facts again at :116 and :117. :115 says the switch is "Hide names and email addresses"; contract:222 says "Hide email addresses". |
| limits.md:115 | "that is a written rule with a known residual risk" | a | Say: "we decided to show company names and accept that a sole trader's company name can be a person's name". |
| limits.md:116 vs :117 | two bullets that say the same (masking is on screen only; log lines hold no values) | c | Said twice with different test lists. Keep one. |
| limits.md:118 | "a client that does not read its reply loses the thread after that" | b, a | Say: "the desk stops serving that connection after 5 s". |
| limits.md:119-120 | "open-file limit ... 4 files per thread plus 96 ... soft limit ... hard limit" | b | OS terms unexplained. Say what to type: `ulimit -n 8192`. |
| limits.md:121 and contract.md:131 | "Exit codes: 1 the sender cannot be reached" | c, a | "Sender" is the person who sends a lead (README:34, limits:16) and here the mail or CRM stand-in. Say "the demo server". The two lists also differ: limits says code 2 also means "a folder, no permission", contract:131 does not. |
| limits.md:122 | "end it with SIGKILL" | b | Say: "stop it by force (`kill -9` on Linux; end the process on Windows)". |
| limits.md:127 | "A connection is also safe from the moment its whole request has been read" | a | Safe from what? Say: "The desk can no longer close that connection to make room once the whole request has been read and the desk has started acting on it". |
| limits.md:128 | "A bind written as a short all-zeros form (for example the single digit 0) is treated as a wildcard." | b, a | "bind", "wildcard" unexplained. Say: "If DESK_BIND is 0 or 0.0.0.0, the desk listens on every network address of the computer; it then counts as reachable by others." |
| limits.md:132-134 | "The scan for hardcoded literals is a safety net ..." | b, a | Which scan? Never named (README:150 hints at `tools/hygiene.py`). "UNC paths", "compressed IPv6" unexplained. Say: "A repository scan looks for fixed addresses and names. It misses: ...". |
| limits.md:138 | "The copy of a lead's stage ... (five tries in all, about 11 minutes ...)" | e, d | About 230 words. States "after a restart the next try happens immediately" and then says no test checks it. Say: "after a restart the next try is expected to happen at once (not tested)". |
| limits.md:138 vs :47-49 | two different wait schedules (10, 60, 180, 420) | c | Both use the same numbers for two situations (failed copy and refused-because-busy). Say clearly which is which. |
| limits.md:142 vs README.md:120 | "when the lead's owner has a CRM owner id, that owner id" vs "when a lead has an owner, the owner id" | c | Same warning, two wordings of what is sent. Make one text. |
| limits.md:154 | "the write against our own portal is not verified" | a | "Portal" here means the HubSpot account (HubSpot's word), but elsewhere "portal" is the desk's web page. Say: "writing the lead status to a HubSpot account other than the author's test account has not been tried". |
| limits.md:154 | the closing paragraph, about 190 words | e | Three separate facts in one sentence. |

## contract.md

| Location | Exact words (short) | Type | Suggested plain words |
|---|---|---|---|
| contract.md:3 | "'fake' and 'recorded' are internal names ... `FakeCrm`, ... `RecordedQualifier`" | b | "qualifier" = the AI step, never said. Say: "recorded = the AI step with pre-written replies". |
| contract.md:5 vs :241 | ":5 Where code and this file disagree, that is a bug to report." / ":241 Where one differs from a table row above, the table row is wrong and is fixed." | c | Which side is wrong? Say once: "If the code and this file differ, tell the author; which is right is decided case by case." |
| contract.md:7-20 | "(all already in the table below; repeated here as a checklist)" and ":17 the connection-limit 503 above" | a, c | The "table below" is at :180 and the row it calls "above" is at :18, below :17. Say "the next row". |
| contract.md:9-20 vs :22 | ":22 only the POST /leads rows carry receipt_id" vs ":17 503 ... receipt id or null" | c | A 503 on `/api/ui` carries no `receipt_id` (:154). Say: "503 on POST /leads carries receipt_id; on other routes it is absent." |
| contract.md:20 vs :64, :195 | ":20 Any 409 ... {"error":"...","hint":"..."}" vs "in_progress, unknown_needs_person, not_retryable carry no hint" | c | Not every 409 has a hint. |
| contract.md:24 | the test-file list in the heading sentence | e | About 70 words of file names with no subject. |
| contract.md:26 | "escapes every non-ASCII character (`ensure_ascii`), so a JSON escape for half a character (a lone surrogate) is stored as text" | b, e | Say: "A name or other field that holds a broken half-character cannot be stored; the desk answers verdict `review`, reason `bad_field:<field>`". |
| contract.md:28 | "(4) Only the thread that won the claim asks the AI step ... see the CRM row above" | e, b, a | "claim", "drive", "thread" undefined; "the CRM row above" does not exist (the CRM rules are at :285-:289). About 110 words. |
| contract.md:29-44 | sub-bullets for the AI step | e | Seven bullets of 60-150 words; :36 and :40 are about 150 and 230 words. :40 mixes constants, exit codes and test names. |
| contract.md:36 | "stalled list of the review desk" | b | "review desk" never explained. Say "the list of items needing a person (`GET /review`)". |
| contract.md:41 | "`timeout_seconds` is an honest wall-clock bound only if the adapter enforces a TOTAL deadline" | a | "honest" is unclear. Say: "is a true limit on total time only if the adapter itself stops at that time". |
| contract.md:45-49 | "(5) A follow-up stuck in sending ... `crm_done` not 1 ... `send_started` 0" | b, e | Column names with no meaning given. :48 is about 85 words. |
| contract.md:55 | "3a." | a | An empty heading line; the content is the bullet after it. |
| contract.md:56 | "(d) ONE transaction `INSERT ... ON CONFLICT(receipt_id) DO NOTHING` ..." | b, e | SQL jargon, 160 words. |
| contract.md:59 | "(The server-side check of step 1 is a 400 before any lookup; this is step 4 inside Desk.)" | a | Unclear which check is run where. Delete or explain. |
| contract.md:61 | step 6, about 140 words | e | Four decision rules in one item. Use one line per decision. |
| contract.md:64 | "Exact `hint` text ... by item type" | e | About 190 words with a nested exception. |
| contract.md:65 vs :209 vs :261 | ":65 No expected parameter at all: ... ok as null" vs ":261 ok is true only when open = 0 ... expected matches ..." | c | When `expected` is absent, is `ok` null or computed from the other conditions? One rule. |
| contract.md:68 | "There is no build-system." and the PYTHONPATH paragraph | b, e | "build-system" unexplained; about 170 words. The `PYTHONPATH=src:.` form works only on Linux (README:132 says so, contract says so inside a bracket). |
| contract.md:71 | "Dev tools: which lock file for which OS" paragraph | e, b | About 150 words, `uv pip compile ...`, "lock file" unexplained. |
| contract.md:74-77 | the config-name lists | e, b | Names only, no meaning (`DESK_NUDGE_TO`, `DESK_ALLOWED_HOSTS` ...); :77 is about 250 words. "Nudge" never explained. |
| contract.md:81 | "`RecordedQualifier` loading rules (fail loud) ... a `KeyError`-class error" | b, e | About 190 words. |
| contract.md:84 | "Server and reply flush ... `SHUT_WR`, `SO_EXCLUSIVEADDRUSE`, `TIME_WAIT`, `PermissionError`, `EADDRINUSE`" | b, e | About 250 words of OS terms. For an adopter: "On Windows, restarting on the same port right after a stop can fail for a while." |
| contract.md:87-91 | "Follow-up drive: who makes which claim" | b, e | "drive", "claim", "token", "transaction-1" never defined; :90 mentions "a caller that holds an open transaction-1 connection (`process` makes no claim)". |
| contract.md:97-98 | hook point names `A, A2, B, D1, D2, L, C0, C1, D1b, D3, N1` | b | A list with only a few meanings given. |
| contract.md:100 | "hook B fires only when this call committed transaction 2" | a | "transaction 2" undefined. |
| contract.md:103-110 | the Host and Origin gate | e, b | "DNS rebinding", "bridge address", "wildcard address" unexplained; :104 is about 140 words. |
| contract.md:113 | first Portal-routes bullet, about 330 words in one sentence with five levels of brackets | e | The single worst structure in the four files. Split: pages, buttons, offline rule, route list, demo routes. |
| contract.md:114-118 | "`mode=ro`, `PRAGMA query_only=ON`", "symbolic links ... `STATIC_FILE_MAX_BYTES`" | b, e | Implementation text. |
| contract.md:115 | "matches ... the company and the lead id, and the name, the email address and the first request number only unless `by_email=0`" | a | "only unless" is garbled. Say: "With `by_email=1` it matches company, lead id, name, email address and first request number; with `by_email=0` it matches company and lead id only." |
| contract.md:119 | failed-follow-up card paragraph, about 250 words | e, c | Says "nothing was sent" only for three reasons, then gives a fourth (`crash_while_sending`) that also says "not sent". |
| contract.md:121 | "the web address is open to any program that can reach the desk" | a | "web address" = route. Say: "anyone who can reach the desk can call this route". |
| contract.md:122 | masking rule paragraph, about 170 words | e | See also README:108 (list of masked values differs). |
| contract.md:127 | "has no lead key" | b | "lead key" is the lower-cased email (README:28). |
| contract.md:128 | "A held lead-book lock raises `OSError` from `lockfile.acquire`." | b | Say: "If another desk already holds the lock file, the start-up stops with an error." |
| contract.md:131 vs limits.md:121 | exit code 2 | c | contract: "another desk holds the lock file"; limits adds "or the lock file cannot be taken for another reason (a folder, no permission)". |
| contract.md:132 | "Refused connections ... one lingerer thread (`_Lingerer` ...)" | b, e | About 150 words. |
| contract.md:133-134 | "Start-up order: * (1) ..." layout | a | Item (1) is a top-level bullet but (2) to (9) follow with different indent, so the nesting is unclear. |
| contract.md:137 | "the reserve covers, item by item ..." | e | About 170 words. |
| contract.md:138 | "... raise it, for example `ulimit -n 8192` or the container's own setting, or the container's own open-file setting" | a | The same phrase twice. |
| contract.md:143 | step (4), about 190 words | e | |
| contract.md:149 | "Signals and shutdown" bullet, about 200 words | e, b | |
| contract.md:154 | "(except `/api/ui/*`, where the two 'not ready' faults ... give 503 `{"error":"unavailable"}`) `{"error":"internal"}` (without `receipt_id` outside `POST /leads`)" | a, e | The order is garbled: the reader cannot tell which body belongs to which status. |
| contract.md:155-172 | wall-clock limits, drain, eviction | e | Ten bullets, each 60-120 words. :166 "This body is its own form" is unclear. |
| contract.md:173 | "on Windows a refused connect ... reports only after about 2 seconds" | b | OS jargon. |
| contract.md:178 | "A replay returns the stored verdict's original status and body plus `"replayed": true`" | a | Fine for one case, but README:62 says "201 and replayed true" and here table rows show `"replayed":false` only. Add the replay row. |
| contract.md:190 | the `GET /leads/{lead_id}` row, about 170 words | e, a | "`attempts` counts the starts of a try ... `auto_attempts`, which is not shown" is unclear: an adopter sees attempts above 5 next to the "5 tries" rule. |
| contract.md:192 | `"reason":"..."`, `"since":epoch` | a | Reasons not listed here. |
| contract.md:204 | step route row, about 170 words | e | |
| contract.md:214 | the `/api/ui/summary` row, about 450 words in one table cell | e | Worst table cell. |
| contract.md:215, :217, :219, :220, :222 | rows of 300-500 words | e | One table cell cannot be read in one go. Put each field on its own line. |
| contract.md:220 | "the test ... that the log shows no personal data plants such values and finds none" | d | The log holds the lead's display name (a person's name) and free-text request numbers, so "no personal data" is not true; it means no email, phone, company or message. |
| contract.md:220 | "the log keeps back email, phone, company and message but cannot vouch for those two free-text fields" | a | "keeps back" is unclear. Say: "the log does not show email, phone, company or message; request_id and lead_name are shown as the sender typed them, so a sender can put anything in them". |
| contract.md:222 | `login`, `encryption_at_rest` and `masking` are `false` | a, c | `masking: false` while the portal masks by default (README:108). The explanation is 4 clauses later in the same cell. |
| contract.md:222 | "(the 'Hide email addresses' switch ...)" | c | Switch has a different name than README:108 and limits:115. |
| contract.md:227 | "The replies to `POST /fake/outbox` ... carry `"mode":"keyed\|blind"`" | e | About 120 words naming which replies carry the field and which do not. |
| contract.md:230 | "for the n8n-only runs the CRM runs in blind counting mode" | a | "n8n-only runs" and "blind counting mode" never explained. |
| contract.md:231 | "asking again is meant to be harmless ... a real CRM was not checked here" | d | "Meant to be harmless" claims safety that is not shown for real CRMs. Say: "asking again is not checked against a real CRM". |
| contract.md:232 and :286, :295 | "capability", "mode", "keyed/blind" | c | One idea, three words. Say "mode (keyed or blind)". |
| contract.md:245-246 | Unicode categories "Cc", "Cf", "Zl", "Zp", "RecursionError", "`sqlite3.DataError`" | b, e | About 150 words of codes. Say: "invisible control and formatting characters". |
| contract.md:252 | "(the source has no normalising step, so it should not merge two; no test asserts that)" | a | Reasoning is reversed: the desk does not merge two spellings. Say: "two spellings of one mailbox are two leads". |
| contract.md:252 vs README.md:28 | "An apostrophe is allowed ... every other exclusion stands" | c | README says "nothing more"; here are exclusions and refused characters. |
| contract.md:255 | "attempts counts the claims" | b | "claims" again. |
| contract.md:261 | the `/counts` bullet, about 200 words | e | Also defines `ok` so that one refused request makes it false until restart. That fact is important for an adopter and buried. Say it in the first line. |
| contract.md:269 | "Rules of the desk's records in `schema.sql` ..." | e, b | About 330 words in one bullet, "triggers", "CHECK", "INSERT OR REPLACE". |
| contract.md:270-277 | "book", "WAL mode", "`PRAGMA user_version`", "journal mode" | b | "book" never defined. |
| contract.md:275 | `crm_done` backfill | e | About 220 words, for old databases only. Not needed by a first-time adopter; say so at the top. |
| contract.md:278 | "`BlockingIOError` ... `EACCES` ... `EDEADLK`" | b | |
| contract.md:282-304 | ownership, tokens, intent mark, `ambiguous_prior`, `send_started` | b, e | Almost every bullet is 100-250 words. "ownership token", "intent mark", "give-back", "requeue", "safe side" are not defined. |
| contract.md:287 | "A CRM with no `capability` attribute (the in-process demo `FakeCrm` has none), is not asked again" | b, a | |
| contract.md:290 | "When the desk cannot read the CRM's mode at all for a leftover 2 ..." | e, a | About 130 words; "a leftover 2" means the crm_done mark value. |
| contract.md:300 | hint quoted with "..." in the middle | a | "...what is unclear is the email ... crm_present is refused here." The exact words are not given although :64 promises exact hint text. |
| contract.md:303 | replay paragraph, about 220 words | e | Lists tests that do not cover the case, in one sentence. |
| contract.md:307-312 | "FairGate", "FairSemaphore", "re-entrant", "write gate" | b | |
| contract.md:309 | "A reaper pass stops starting new drives after ..." | e | |
| contract.md:314-317 | "Known limits of the desk" has three bullets | c | docs/limits.md has dozens of limits; this heading suggests this is the list. Say "Three more limits". |
| contract.md:315 | "A crash hook that asks for the gate again would deadlock for one wait: hooks are test seams." | b, a | |
| contract.md:316 | "Start-up counts a try for a row whose backoff has not passed." | a | Whose try, whose backoff? |
| contract.md:317 | "A duplicate reply returns the id of the other lead: kept as it is." | a, d, c | Which lead? "Duplicate" means the same email as an earlier lead (README:36), so "the other lead" should be the first one. If it is something else, the sentence hides a bug; if it is "kept as it is", it is a limit stated as a decision. Say: "When a request is a duplicate, the reply carries the lead id of the first lead with that email (this is intended)" or the true behaviour. |

## Counts (rows, not sentences)

| File | Rows | (a) unclear | (b) jargon | (c) contradiction | (d) over-promise | (e) too long |
|---|---|---|---|---|---|---|
| README.md | 38 | 13 | 9 | 11 | 10 | 11 |
| SECURITY.md | 12 | 4 | 4 | 2 | 4 | 1 |
| docs/limits.md | 48 | 24 | 17 | 8 | 5 | 16 |
| contract.md | 79 | 24 | 30 | 13 | 4 | 37 |

A row with two types counts once under each type. The contract.md "e" count is low for what I saw: dozens of its lines are over 100 words and I grouped them (for example :282-:304 is one row).

## The 10 worst sentences

1. contract.md:113: one sentence of about 330 words with five levels of brackets (portal routes). Unreadable in one pass.
2. contract.md:214 (and :215, :217, :220, :222): table cells of 300 to 500 words. Nobody can read a reply shape from them.
3. contract.md:317: "A duplicate reply returns the id of the other lead: kept as it is." Unclear which lead, and it may hide a bug.
4. README.md:6 against README.md:100, docs/limits.md:22 and :77: "never sent a second email ... by itself" against "not claimed: never sent twice" and "sent again with the same key". An adopter relying on the first is misled.
5. README.md:22 and :65 against README.md:118: "exactly one email" while the demo scripts turn on a reminder email whose wait is never stated.
6. README.md:120 (and docs/limits.md:142): the WARNING paragraph, about 250 words, with "loopback", "step route" and "review routes" unexplained, at the point where the adopter decides whether it is safe to connect a real CRM.
7. docs/limits.md:154: "the write against our own portal is not verified". "Portal" means the HubSpot account here and the desk's web page everywhere else.
8. docs/limits.md:72: the test-count bullet of about 330 words that contradicts its own totals (2462, 2464, 2465) and says so.
9. SECURITY.md:5 against README.md:120: "Do not put real customer data into it" against detailed steps for connecting a real CRM.
10. contract.md:40 (and :36): about 230 words mixing constants, exit codes and test names in one bullet; and README.md:8 where "the AI step" is used and never explained.

