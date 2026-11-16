## 3. The numbers message (sample, made-up values) and your checks
SAMPLE (made-up values, never real):
```
Run name: demo7   Run day: Wed 18 Nov 2026   REAL run (paid model calls happen)   Earliest key time: 10:30 UTC = 16:00 IST
Older key: "studio-key-1" made 2026-11-10, last used <time or never>, left alone and valid during the run (or "none")   Older-key time: 16:00 UTC = 21:30 IST on the run day
Message place: this chat   Other channel: <name and how>   Backup person: <name and how to call>   Date you decided to use the existing balance: <date>
Cancelled word: <word, or "from the look key"> (UNVERIFIED; you see the real word at 5.9 and the lead answers "confirmed")   Key scopes: <scopes the key page offers>   Last-resort step: <step> (can it be undone: <yes or no>)   Key list time zone: <zone>   Model settings file: <model settings file>
Key file: <key file>   Take folder: <folder path>   cd line: <the cd line>   Key list address: <address>   Prepaid page address: <address>
Accounts: model company and account <name>, receiver Gmail <name>, sender Gmail <name>, HubSpot test <name>   Masked in the notice: receiver <masked address>, sender <masked address>   Gap before 8.1: <minutes>
Start line: python3 -I scripts/run_real_check_n8n.py --take <test settings file name>   Spend lock: shown (or NOT SHOWN)   Key file size in bytes: <range> (UNVERIFIED)   Test program asks you to type a figure: no   Model key outside the model program: none (the lead checked n8n's credential store and shows it)
Model: model-x   Tokens in and out per call: 40000 and 10000   Prices per million: in USD 3.00, out USD 15.00   Price page: <page address>   Price per call at full size: USD 0.27   Call ceiling (the lead's figure): 3   Expected total: USD 0.81 (not a limit)   Per-key limit: none exists
Balance on the prepaid page: USD 189.00   Auto-reload (the lead's reading): off
Settings to compare, each name = value (unit): MODEL_NAME = model-x | TOKENS_IN = 40000 | TOKENS_OUT = 10000 | PRICE_IN_CENTS = 300 | PRICE_OUT_CENTS = 1500 (US cents per million tokens) | CALL_CEILING = 3 | DEADLINE = 2026-11-23T18:29:00Z
Minutes at "Type y to start": 5   Minimum think time: 20 seconds   Run length: 15 minutes   Film pause: 10   Latest start: 11:30 UTC = 17:00 IST   Alarm time: 12:00 UTC = 17:30 IST   Cancel-by time: 12:10 UTC = 17:40 IST   Silence minutes: 3   Give-up minutes: 40
Film cue: <the printed line, copied, or minutes after "run started">   Waiting line: <copied>   Demo mail subject start: <words>   Earlier demo mails expected: 0
People: film person <name>, editor <name>, post checker <name>   Recording tool: <name>   Posting place: <place>   Video by: <how>
Expected after the run (never changed after y): A submitted 2 times with the same person id, 1 contact, 1 mail; B submitted 10 times, 1 contact, 1 mail; C 1 contact, 1 mail (its printed line says "unknown": accepted); the HubSpot search for `take-<run name>` shows 3 contacts and the demo mail list 3 mails   Exit codes accepted: 0 only
The yes sentence: <the lead's exact sentence>
If you cancel the key during the run or right after `end`, the test program: <lead's answer>; exit code accepted then: <number or none>
```

**Your checks, by hand with a calculator** (a failing check: no yes, describe it; an empty slot or one in angle brackets, a missing last-resort step, figure line or think time, or "unknown" in any slot (only the cancelled word may say "from the look key"): no run, checked when the message arrives; a figure line that is not "no": no run):
1. Call ceiling = the lead's figure for the most model calls one run should cause. Price per call = (tokens in x price in + tokens out x price out) / 1,000,000 = (40,000 x 3.00 + 10,000 x 15.00) / 1,000,000 = 0.27; expected total = call ceiling x that = 3 x 0.27 = 0.81. Both equal the message, the price page shows the same two prices, and every setting equals the message (cents / 100 = USD).
2. The run day is before Mon 23 Nov 2026 (otherwise no run, no "go"). The earliest key time, latest start, alarm time and cancel-by time are on the run day, and the cancel-by time is at least 10 minutes before the deadline.
3. The account names are ones you know, and so is the older key, and the other channel is the one you named at 5.1; the backup person is a human you can call. The balance is at least the expected total.
4. The last-resort step only stops spending (it never closes the account or removes other keys) and says whether it can be undone; you cannot judge it: ask on the other channel before the yes. The cancel-by time is before the older-key time. The model key outside the model program line says none: otherwise no run (a model key stored in n8n would spend without the spend lock).
