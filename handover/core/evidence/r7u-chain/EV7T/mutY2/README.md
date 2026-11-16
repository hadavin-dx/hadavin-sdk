# duplicate-proof-lead-desk

**In plain words**

1. A sales lead can arrive twice: the same person fills in the web form and then writes by email, or the same request is sent again after a crash.
2. A business wants one follow-up email and one customer record (one "CRM row") for that person, not two.
3. This repository is a small demonstration of one way to get that: a program called "the desk" that writes every request down before it acts on it.
4. You can run it on your own computer in a few minutes. It uses made-up people and small demo programs: one demo server that plays the CRM and the mail system, and a file of pre-written answers that plays the AI step (it gives each lead a label, hot, warm or cold), so nothing real is sent.
5. What you will see: send one lead, send the exact same request again, then send the same person through the other door (the web form and the webhook; "Door" is explained below). You get one "new", one "replayed" and one "duplicate" answer (all three words are explained below), and one email within the first 90 seconds; a second, reminder email follows after 90 seconds (see "Optional features"). A web page (the portal) shows the same facts.
6. What is claimed: in the tests of this repository, with these demo servers, the desk never sent a second email for the same lead by itself. Two cases differ. On a mail system that remembers a send key ("keyed", explained below), the desk may hand over the same email again after an unclear result, and the demo mail system ignores the repeat; a real mail system may not. On a mail system that does not remember it ("blind"), the desk does not guess and does not resend: it lists the follow-up for a person to check.
7. What is not claimed: that this works with any real CRM or mail system, that it suits production, or anything about load beyond what `docs/limits.md` states. It is not software to install for your business.
8. Who it is for: a business owner who wants to see the idea working, and a revenue-operations person (someone who runs a company's sales tools) or n8n freelancer who wants to read the code, the tests and the n8n workflows.
9. Licence: all rights reserved; you may read the code and run it on your own computer to evaluate it (see "Licence" at the end). Not legal advice.
10. Made by the author with AI coding tools, and read through by the author. No review record is kept in this repository.

## What you will see

After the steps in "Try it" below, three things confirm that it works. Every number below comes from the demo programs (the demo server and the file of pre-written answers), not from a real CRM or mail system.

* The first lead gets `"verdict": "new"`. The same request sent again gets `"replayed": true`, the same lead and the same receipt number; the desk creates no second lead and no second email. The replay is still counted in `attempts` in the receipt, and it can use up a receipt number, so the numbers can skip (no test pins this). If the lead's follow-up email is due and not yet sent, the replay starts it. The same person through the other door (web form or webhook) gets `"verdict": "duplicate"`.
* The counts page shows 2 requests received, 1 new, 1 duplicate.
* The demo mail system holds exactly one email until the reminder email is due. The demo start scripts also switch on the reminder email (see "Optional features") with a waiting time of 90 seconds (`nudge_after_seconds` in `demo_only/leadflow.json`): once a lead is 90 seconds old and has not reached the stage that the same file names as `reminder_until` (`replied`), the desk's background pass sends a second email, so a later look can show 2.

In a browser, http://127.0.0.1:8765/ui/ shows the portal: overview, leads, items that need a person, a request log, and what data the desk stores. See `docs/portal.md`.

## Words used here

* **Lead**: a person who asked to be contacted. **Same lead** means the same email address, trimmed of spaces and lower-cased. The desk refuses a few unusual characters in an address (such a request goes to review; see `contract.md`) and does nothing else to it.
* **Follow-up**: the one email sent for a new lead, plus the CRM row that goes with it.
* **CRM**: the customer-record system where a lead is stored as a row.
* **Demo servers** (older text and some file names call them demo stand-ins): small programs in this repository (`demo_only/`) that play the CRM and the mail system and only count what they receive. The AI step is not played by a server: a file of pre-written answers (`demo_only/replies.json`, read by the code named `RecordedQualifier`) plays it. Some of their web addresses and settings still contain the word `fake`.
* **The desk**: the program in `src/lead_desk`. **Desk's records**: its database file (SQLite, a database kept in one file).
* **n8n**: a workflow tool where steps are drawn as boxes joined by lines. n8n is not part of this repository.
* **Request id** (written "request number" in the portal and in some sentences below): a label the sender puts on each submission. The same label twice means "this is a replay" (see Replayed below). The portal calls it "Request number".
* **Receipt**: the desk's first note about a request, written before anything else happens.
* **Verdict**: the desk's answer: `new` (first time this email is seen), `duplicate` (seen before under another request number) or `review` (the request is incomplete or holds a value the desk will not store; a person must look).
* **Repeat (portal word)**: the portal shows a `duplicate` verdict as "Repeat". A replay (next entry) is a different thing.
* **Replayed**: the same request number came again, so the desk gave back its stored answer and created no second lead and no second email. The replay is counted in `attempts` and can use up a receipt number (no test pins this).
* **Door**: the way a request arrived: `form` or `webhook`. The portal calls it "Source".
* **Keyed and blind**: the desk gives every email one fixed label, the send key; a keyed mail system sends only once for a send key it has seen, and a blind one does not. The same two words apply to a CRM: a keyed CRM keeps one row however often it is asked with the same key; a blind CRM stores a row every time.
* **UNKNOWN**: the desk cannot tell whether a follow-up email left, or whether the CRM row was written. It does not guess and does not resend; a person must check.
* **Crash point**: a named moment in the desk's work where a test stops the desk on purpose. There are ten, and an eleventh, N1, for the reminder email. Example: `D2`, the moment after an email was sent but before the desk noted it. The table is in `docs/tests.md`. Crash point names (`A`, `C0`, `D2`, `N1`) are not the same as review-item ids such as `D12` (D plus a receipt number), `R12`, `O12`, `F` plus a lead id or `N` plus a lead id; the item ids are explained in `contract.md`, sections "Other rules" and "HTTP table" (the `GET /review` row).
* **Reaper**: a background job inside the desk. It puts stuck follow-ups back in line, retries a refused send a few times with growing waits (1, 2, 4 and 8 seconds, up to 5 automatic tries in a row; a person's Retry starts the count again), and decides receipts that were written but never got an answer (it writes a verdict for them).
* **Webhook** (as a door): requests sent by another program. In n8n the word also names an address that starts a workflow when something is posted to it.

## Try it

You need Linux or Windows (macOS was not tried), Python 3.12 or newer (`pyproject.toml` requires 3.12 or newer; the lock files are made for Python 3.12 on Linux and Python 3.13 on Windows, see `versions.md`) and git, and ports 8765 and 8766 on your computer must be free. The desk needs no extra packages.

1. On this repository's GitHub page press the green Code button and copy the address it shows.
2. Run `git clone <that address>`, then `cd` into the new folder.
3. Open ONE terminal there and run the lines of your system below, in order, in that same terminal. The first lines make a private Python folder, `.venv`, and switch it on for this terminal only, because the scripts call `python`. If you open a new terminal later, switch `.venv` on again.
4. On Debian or Ubuntu you may first need `sudo apt install python3-venv`.
5. The start script starts the demo server and the desk as background programs and returns at once; they keep running until you run the reset script (last line of each block), which stops them.

**Linux**

    python3 -m venv .venv && . .venv/bin/activate
    export PYTHONPATH=src                      # tells Python where the code is
    bash scripts/start_all.sh keyed            # starts the demo server and the desk in the background
    for i in 1 2 3 4 5 6 7 8 9 10; do curl -sf http://127.0.0.1:8765/counts >/dev/null && break; sleep 1; done; curl -i http://127.0.0.1:8765/counts # waits up to 10 seconds; it works when the first line starts with "HTTP/1" and has 200, and the numbers are all 0
    python scripts/feed.py --source form --index 1       # sends one lead; prints 201 ... "verdict": "new"
    python scripts/feed.py --source form --index 1       # the same request again: 201 and "replayed": true, no second lead, no second email (the replay can use up a receipt number)
    python scripts/feed.py --source webhook --index 1    # same person through the other door: "verdict": "duplicate"
    curl http://127.0.0.1:8765/counts              # received 2, new 1, duplicate 1 (the replayed request is not added to these counts; it only raises attempts in its receipt, and it can start a due follow-up)
    curl http://127.0.0.1:8766/fake/outbox         # "count": 1  (one email, not two, if you look within 90 seconds; the reminder email comes later)
    bash scripts/reset.sh                          # stops what start_all started and DELETES the desk's records and the logs (only inside ./data)

Run both scripts with `bash`, as above. They need features that only bash is sure to have. If you start them with `sh` on Debian or Ubuntu, they stop with "run this script with bash" (exit code 2).

**Windows PowerShell**

    py -3 -m venv .venv                        # or python -m venv .venv; `py -3` avoids the Microsoft Store stub
    Set-ExecutionPolicy -Scope Process RemoteSigned   # only for this window: lets this window run the two local scripts below. If your organisation blocks all scripts, see the paragraph after this block
    .venv\Scripts\Activate.ps1
    $env:PYTHONPATH = "src"                    # tells Python where the code is
    .\scripts\start_all.ps1 keyed    # prints "started: ..." with two process ids
    Start-Sleep 3; Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/counts | Select-Object -ExpandProperty Content    # should answer with numbers (all 0)
    python scripts\feed.py --source form --index 1       # prints 201 ... "verdict": "new"
    python scripts\feed.py --source form --index 1       # the same request again: 201 and "replayed": true, no second lead, no second email (the replay can use up a receipt number)
    python scripts\feed.py --source webhook --index 1    # same person, other door: "verdict": "duplicate"
    Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/counts | Select-Object -ExpandProperty Content    # received 2, new 1, duplicate 1 (the replayed request is not added to these counts; it only raises attempts in its receipt, and it can start a due follow-up)
    Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8766/fake/outbox | Select-Object -ExpandProperty Content    # "count": 1 (within 90 seconds; the reminder email comes later)
    .\scripts\reset.ps1        # stops what start_all started and DELETES the desk's records and the logs


If PowerShell refuses to run the scripts at all (a policy set by your organisation), start the two programs by hand instead, each in its own window with `PYTHONPATH` set as in `contract.md`, "Run commands": `python -m demo_only.fakes_server --outbox keyed --port 8766` and `python -m lead_desk.server`.

You have the demo working when the counts and the outbox match the comments above: 2 requests received, 1 new, 1 duplicate, and exactly one email (if you look within 90 seconds of the first lead). If `/counts` does not answer within a few seconds, read `data/desk.log` (on Windows also `data/desk.err.log`), run the reset script and start again. The desk has no page at `/` or `/health`; it answers 404 for an address it does not know. On Windows, starting again on the same port right after a stop can fail for a while (the operating system keeps the port closed for a time; how long was not measured here). The `/fake/...` paths are the demo servers' own addresses and keep that word in the URL.

The reset script refuses, with one line of reason and nothing deleted, in these cases. Each case has an exit code, the number the script ends with. These are the reset script's own codes, not the desk's:

* 2: the database is not inside `./data`, or `RESET_STOP_WAIT_SECONDS` is not a whole number from 0 to 999 without a leading zero. Both reset scripts check this before they stop or delete anything.
* 3: a process still holds the desk's database, its lock file or data folder cannot be looked at, or (Linux) `ps` is not installed while a pid file exists.
* 4: something still answers on the desk's or the demo server's port, or a `DESK_` setting is wrong (the same one line
  the desk prints, for example `the desk refuses a setting: ...`; `scripts/start_all.sh` and `scripts/start_all.ps1`
  end the same way with the same code). The `.ps1` scripts were written to match the `.sh` scripts line by line and are
  checked by text tests only: they have not been run on Windows.
* 5: a process did not stop in time.
* 6: a pid file (a file that holds a process number) names another program.

Optional: `RESET_STOP_WAIT_SECONDS` (0 to 999, default 10) is how long the script waits for the processes to stop; an empty value counts as not set and means 10.

## What is claimed, and what is not

Claimed, for this demo setup only:

* The same request number sent again gets the stored answer; no second lead and no second email is made. The replay is counted in `attempts` and can use up a receipt number (no test pins this).
* The same email under a different request number is a duplicate: no second CRM row, no second email, and the AI step is not asked.
* An incomplete request goes to a review list with a reason and gets no follow-up.
* The desk was stopped at ten named crash points (and an eleventh, N1, for the reminder email) and restarted. All ten were simulated by an exception inside the program, and D2 was also tried with a real process kill (`docs/limits.md`). At the crash points the tests cover, they assert at most one lead, one CRM row and one email; `contract.md` says that not every path is covered. Where it cannot tell whether an email left, the follow-up is listed as UNKNOWN for a person.
* The desk does not send a follow-up twice by itself; the only repeat it makes is the same email with the same send key, which a keyed mail system ignores. An unconfirmed send is listed for a person. A person who answers "not sent" wrongly on a blind mail system can cause a second email.

Not claimed:

* Anything about a real CRM, a real mail system or a real AI model: no test here talks to one. `scripts/hubspot_probe.py` is a separate script that you run yourself against a free HubSpot account; it imports no desk module, so it does not use the desk's HubSpot adapter, and the adapter's tests (`tests/test_crm_hubspot.py`) use a demo HubSpot server (`demo_only/fake_hubspot.py`). The "keyed" mail system is a simulation; a real provider may remember a send key for a shorter or longer time.
* Production fitness, a legal opinion, a guarantee of any kind.
* The same person with two email addresses is two leads; if two people use the same email address, the desk treats them as one lead.
* The desk is for one computer and one process, has no login, and listens on this computer only. You can change that for the demo; with any real service connected, the desk refuses to start on any other address. No penetration test was done.
* Masking in the portal is on screen only: lead names, email addresses, phone numbers, messages and request numbers are hidden on the page by default (the switch "Hide names and email addresses"; its state lasts for the browser tab's session). The search does not look in names or email addresses while they are hidden. The data the desk sends to the page still holds every value, so anyone who opens the browser's developer tools can read them (see `docs/portal.md`).
* A load of 10,000 requests was not tried. No measured load figure is stored in this repository (see `docs/limits.md`).
* The desk's time stamps use the computer's clock, so a clock that jumps by 30 seconds or more can make the desk ask again for a follow-up that was still being sent (`docs/limits.md`, item 5).
* The full list, with test names, is in `docs/limits.md`.

## Optional features

Both features are off in the desk unless a setting turns them on. The demo start scripts turn on the second one (lead owner, lead stage and reminder).

* **Approval mode** (`DESK_LATER_MODE=approval`): a second request for the same email address that brings new details (for example a new phone number) can be approved or denied by a person picked from a list of approvers. Approving or denying only records that choice: the approver is a name picked from the list and is not verified, and nothing is executed by it. Off by default; then it is only listed. The reply shapes are in `contract.md`, the settings in `docs/settings.md`.
* **Lead owner, lead stage and reminder** (`DESK_LEADFLOW_FILE`): each new lead gets an owner from a short list and a stage (a named step such as New or Contacted). If, after the waiting time set in the file (90 seconds in the demo file), the lead has not reached the stage that the file names as "reminder until", one reminder email is sent. The reminder does not depend on whether the follow-up email was sent. Only leads created while the feature is on are covered (`docs/limits.md`). Off when the setting is unset, empty or is the word `off`. The demo start scripts switch it on with `demo_only/leadflow.json`; set `DESK_LEADFLOW_FILE=off` to turn it off there.

> **WARNING: this write can start automations in the CRM you connect.**
>
> * **What is written, and what may react.** When lead stages are on, the desk writes the contact's lead status field (in HubSpot `hs_lead_status`). Any automation that watches that field (a workflow, sequence, lead rotation, scoring rule, notification, integration or report) may react to the desk's write, for example by emailing the contact, creating a task, changing the owner or sending a chat alert. The desk neither sees nor controls those automations, and it does not know what the automations of the CRM's owner do. The feature is OFF unless `DESK_LEADFLOW_FILE` is set to a file; when it is on, the stage copy to the CRM sends the lead status value named in that file's stage list and, when the lead's owner has a CRM owner id, that owner id; `tests/test_lead_crm_copy.py` has a check that the request body holds only these two properties.
> * **Required before you point this at a real CRM:** the CRM admin lists every automation that reacts to lead status changes and confirms each one is safe or switched off, and the first test uses one made-up contact.
> * **No sign-in.** The desk has no sign-in, so any program that can reach its port could cause this write (through the route that moves a lead to another stage) or create contacts and send mail (through `POST /leads` and the routes that settle items for a person). With any real service set (a real CRM, the real mail sender or the live AI step) the desk therefore starts only on a loopback address, that is, this computer's own address (127.0.0.1), and refuses any other `DESK_BIND`.

* **Not in this demo:** handling of later messages by an AI step, and suggested replies. A later message is a second request for the same email address; the desk never rewrites or summarises it.

## About n8n

The first question of the project was whether n8n on its own handles duplicates and a crash between the CRM step and the email step. No workflow, log or result of any n8n-only pattern is in this repository, so none is stated here and none can be reproduced from it (what is said about the three shipped workflows is in `docs/n8n-recipe.md`). What is shipped: three n8n workflows that send leads to the desk (`n8n/`), described in `docs/n8n-recipe.md`, which you can import into your own n8n unmodified to evaluate them. n8n has its own licence; read it before you use n8n.

## Tests and more commands

The tests need development tools, installed from a lock file into the `.venv` folder so that nothing else on your computer changes. The commands for Windows and Linux are in `docs/tests.md`; the test command itself is `python -m pytest -q`. Supported: Windows with Python 3.13 and `requirements-dev-win.txt`, or Linux x86_64 with Python 3.12 and `requirements-dev.txt`. Any other combination is not supported for running the tests. If pip prints a hash mismatch, you are using the wrong lock file or Python version for your computer. The tests need a git clone (some tests read the list of tracked files with git).

The desk alone: `PYTHONPATH=src python -m lead_desk.server`. Writing `blind` instead of `keyed` in the start command starts a mail system that cannot recognise repeats. On Windows, set `PYTHONPATH` with `;` between entries when two are needed (`src;.`).

## Where to read more

* `docs/tests.md`: the crash-point table, the ten promises with the tests that show them, the mutation check, how to run the tests.
* `docs/portal.md`: the portal pages, what only reads and what writes, the Host and Origin check.
* `docs/limits.md`: what is not claimed in full, load rules, counters, exit codes.
* `docs/settings.md`: every setting.
* `docs/n8n-recipe.md`: the n8n workflows.
* `docs/real-services.md`: an optional script to try the desk against a free HubSpot account and two mailboxes (the separate probe script `scripts/hubspot_probe.py` is described in `docs/hubspot-probe.md`).
* `docs/why-this-code.md`: why each part is own code, and where another CRM, mail service or AI service plugs in. `contract.md`: the replies the desk is meant to give (if the code and this file differ, that is a bug to report). `versions.md`: the versions needed to run.

## Layout

* `src/lead_desk`: the desk.
* `demo_only/`: everything that exists only for demos and tests (demo servers, pre-written AI replies, burst script, canned leads); the desk reaches it only through `src/lead_desk/loader.py`.
* `tests/`: the tests. `scripts/`: run and demo helpers.
* `load_tools/`: a load driver, the checks that run after a load, a small test mail server (`load_tools/README.md`).
* `tools/`: the repository scan (`tools/hygiene.py`) and the n8n export scrubber, for the author's own use.
* `n8n/`: the three n8n workflows. `docs/`: the pages above.

The follow-up email is fixed demo text: the subject is `Thanks for getting in touch, {name}` and the body is one line ending in `(DEMO EMAIL)`; the AI label is not part of it. The checks configured to run on pull requests and pushes to main are listed in `docs/tests.md`; the browser tests are not among them (they need Playwright), so run them on your own computer.

## Trademarks

HubSpot, Gmail and Google, n8n and Anthropic are names of their owners. This project is not affiliated with, endorsed by or sponsored by any of them; the names appear only to say which services the desk and its check scripts talk to.

## Licence

See `LICENSE`. All rights reserved by the author. You may view the code, download it, run it on your own computer for evaluation and testing, and fork it on GitHub (to the extent GitHub's Terms of Service give that right); nothing else without the author's written permission. In particular you may not hand on copies, publish changed copies, use it commercially or offer it as a service. The licence covers everything in this repository: the code, the documents, the n8n workflows and the scripts. The workflows in `n8n/` may be imported unmodified into your own n8n to evaluate them. Editing them, building variants, or sharing or publishing exports needs the author's written permission. To ask for permission, write to the address in `SECURITY.md` or through the GitHub profile of the organisation that publishes this repository. No warranty. The author may record and publish demo videos. The full text is in `LICENSE`; it has not been reviewed by a lawyer. Outside contributions (pull requests) are not accepted. See `SECURITY.md` to report a problem.
