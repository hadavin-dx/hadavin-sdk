# The n8n workflows of the demo, what each one does

n8n is a workflow tool; "the desk" is the lead-handling program of this repository.

Who this is for: someone who has used n8n a little and wants to read what the workflows of the demo do, or to import them unmodified into their own n8n for evaluation. The workflows in `n8n/`
("Lead Desk: Web Form Intake", "Lead Desk: Email Intake", "Lead Desk: Duplicate Test (10 at once)") are files of this repository; the `proof` workflow is the one named "Lead Desk: Duplicate Test (10 at once)". **No result of running them in n8n is stored in this repository.** What this page states is read from the shipped files, from the desk's code and tests, and from `scripts/n8n_api.py`; every step marked "not checked" or "not tried" is a plan, not a fact. Menu and field names in n8n change between versions, and this page does not claim that the names below match the screen of any n8n version.

**Licence.** The workflows in `n8n/` may be imported unmodified into your own n8n to evaluate them. Anything else (editing them, building variants, sharing or publishing exports) needs the author's written permission (the author is the person named at the top of `LICENSE`; it covers the documents, workflows and scripts too).

Made-up data and demo servers only. Use no real credentials and no real lead data in n8n; the only real items are n8n's own owner account and its free community licence (section 0). The files use placeholder node ids (`node-1`, `node-2`, ...) and contain no credentials, so there is nothing to attach after an import. `scripts/n8n_api.py import <file>` does the import; it needs an n8n API key in a file you name, see the top of that script. The address you call is `/webhook/desk-form`, because the file fixes that path (it is a plain word, not an id).
After the import, switch the workflow on with `scripts/n8n_api.py activate <name>` (for `proof` see also section 3).
The `proof` workflow has a manual start and a web-call start; the web-call start is there so it can be run without the screen
(`POST /webhook/proof-run`).

## 0. Before you start

* n8n version: none is recorded in this repository (`versions.md`, section "n8n (demo only)"). The workflows are not claimed to work on any n8n version.
* n8n needs an owner account on first start. Use your own business e-mail in YOUR n8n only (it is the account e-mail; the leads and addresses in the workflows are made up). Whether the workflows here also run
  without n8n's free community licence is not checked (they use only the Webhook, Edit Fields, HTTP Request, Code and Manual Trigger nodes).
  Never commit the e-mail, the password or the key anywhere.
* Start the demo servers and the desk first (README, "Try it"). From the same computer, n8n reaches them at the host and
  ports from the settings table in `docs/settings.md`. **If n8n runs in Docker, `localhost` inside the container is the container, not
  your computer.** The desk listens on this computer only (`DESK_BIND`). The desk answers 403 `forbidden_host` to any `Host` name it does not know (anything but `127.0.0.1`, `localhost`, `[::1]`): if n8n reaches the desk under another name, list that name in `DESK_ALLOWED_HOSTS` (`docs/settings.md`).
* **n8n's port.** The shipped files expect n8n on port 5679 (n8n's own default is 5678). `scripts/n8n_api.py` (setting `N8N_URL`, default `http://127.0.0.1:5679`) and the sending box of the `proof` workflow (its URL is `http://127.0.0.1:5679/webhook/desk-form`) expect that port, so start n8n with `N8N_PORT=5679` to evaluate the workflows.

## 1. The desk workflows (n8n in front of the desk)

Goal: a web form submission and an email-style message, both arriving at n8n, both end up as one request to the desk.
n8n adds nothing clever. The desk decides what is new.

**Request id** ("Request number" on the portal screens). The desk answers `"replayed": true` when it is sent an id it has already seen (`src/lead_desk/desk.py`). The desk needs one id per
submission that stays the same when n8n re-sends it. Candidates: the form's own submission id, the email's message id, or n8n's
execution id (n8n's execution id is not used by these workflows). The workflows carry the id inside the
request body (`submission_id`, `message_id`), which is the stable choice.

Example inputs (made-up):

    form:    {"submission_id":"sub-0001","name":"Ada Example","email":"Ada@example.com","phone":"555 0100","company":"Example Ltd","message":"Please call me."}
    webhook: {"message_id":"msg-0001","from_name":"Ada Example","from_email":"ada@example.com","subject":"Quote","body":"Please call me."}

The **web form source** workflow ("Lead Desk: Web Form Intake") has three nodes: a Webhook node that receives the form (path `desk-form`; no authentication, local demo only), an Edit Fields node that sets `source` to `form`, takes `source_ref` from `submission_id` and copies `name`, `email`, `phone`, `company` and `message` into `payload`, and an HTTP Request node that posts `source`, `source_ref` and `payload` to the desk's `/leads` address (host and port from `docs/settings.md`). Its timeout is 15 seconds (`n8n/desk-form.json`), longer than the desk's default send timeout of 5 seconds, so a slow answer ends the call in n8n later than in the desk.

The Webhook node returns the desk's reply (verdict `new`, `duplicate` or `review`). The node's response mode is `lastNode` (`responseMode` in `n8n/desk-form.json`), so the caller gets what the last node returned. What the caller gets when the desk answers 400 or 413, or cannot be reached, is not stated here.

The **email source** (the `webhook` source) workflow ("Lead Desk: Email Intake") has the same three nodes with the Webhook path `desk-webhook`; it sets `source` to `webhook` and takes `source_ref` from `message_id`, `payload.name` from `from_name`, `payload.email` from `from_email` and `payload.message` from `body` (`subject` is ignored by the desk).

What to check after importing, in this order (the desk's answers are what its tests show; what n8n displays is not claimed here):
1. Import works. 2. The form call reaches the desk (the desk answers 201, verdict `new`). 3. The email call reaches the desk
(same lead: 200, verdict `duplicate`). 4. The id is stable (the same submission twice: the second reply carries `"replayed": true`).
5. A request with no email: the desk answers 202 `review` and sends no follow-up. 6. A body that is not valid JSON, or one over the size cap: the desk answers 400 or 413.
7. n8n's automatic re-send: the "Send to the desk" node has "Retry On Fail" on, 3 tries, 1 second apart (`n8n/desk-form.json`). What n8n does with that setting for a 400 or 413 answer is not stated here.

## 2. The n8n-only patterns (n8n without the desk), described only

These workflows are not shipped and no result about them is claimed here; this section only says what the patterns were. Each pattern is the desk workflow with the desk call replaced by: **dedupe step, then POST to the demo CRM, then POST to the demo outbox.** The request bodies for the demo servers are in the `/fake/...` rows of the HTTP table in `contract.md`. To try one, start the demo servers in blind counting mode (blind: they cannot recognise a repeated send; see the README, "Words used here"; `--crm blind --outbox blind`; the CRM default is `keyed`, which would hide a second row).

* **(a)** n8n's Remove Duplicates node on the email, with default settings.
* **(b)** a database insert that refuses a second row with the same email.
* **(c)** an n8n Data Table "upsert" (insert the row, or update it if it exists) on the email column, where equal created and updated times mean the row is new.
* **(d)** is (a) with n8n limited to one request at a time.

## 3. The "Proof" workflow (the check inside n8n)

Purpose: people trust what they see in n8n, so the counts are shown on an n8n screen. The counts come from the demo servers' own counters, never from n8n's
own "success" mark, which is not proof of "no double email". No n8n-only result is claimed.

The workflow "proof" (manual start, or a web call to `/webhook/proof-run`) sends ten requests for the same lead with different request numbers at once, waits a few seconds, reads the desk's counts and the demo CRM's and demo mail system's counters, and shows the result on screen, for example "emails: 1, CRM rows: 1, expected 1". In the shipped `proof` workflow the ten calls already go through the n8n web address of the web form source, not straight to the desk. The burst script (`demo_only/burst.py`, see `contract.md`) fires the same burst without n8n. **Changed; no n8n result is stored for it.** The `result` field of the `proof` workflow used to say PASS when the demo mail system and the demo CRM each counted 1. It now says PASS only when, in addition, the desk answered all ten requests with exactly one `new` and nine `duplicate` (under the old rule, if some of the ten requests got no verdict, for example a refusal or a "busy" answer, the line could still print PASS). That new rule was checked only by running its text in node with made-up values (`tests/test_n8n_proof_result.py`). What is not proven: that n8n's own expression engine accepts the text, and that it finds the output of the earlier step "Wait for the desk to finish" from the last step. To check the new rule yourself, do this once: first remove the old copy of the workflow, because `scripts/n8n_api.py` has no delete command and an import only adds a second workflow with the same name (and `activate` refuses when two workflows share a name): open the n8n screen (not tried here, and its menu names were not compared with the screen), find the workflow "Lead Desk: Duplicate Test (10 at once)" in the workflow list and delete it. Then import `n8n/proof.json` again with `python scripts/n8n_api.py import n8n/proof.json`, start it by hand, and check that the screen shows `PASS` with emails 1 and CRM rows 1. If n8n shows an error on the `result` field instead, the fault is in this expression, not in the desk. A MISMATCH is not always a fault of the duplicate protection: if the desk is busy and answers one of the ten with 503 "busy" (the desk has such an answer, see `src/lead_desk/server.py`; whether ten at once triggers it was not measured), that request has no verdict and the line says MISMATCH; start the workflow again.

## 4. What to know when the desk sits behind n8n

The three workflows in `n8n/` ("Lead Desk: Web Form Intake", "Lead Desk: Email Intake", "Lead Desk: Duplicate Test (10 at once)"; files `desk-form.json`, `desk-webhook.json`, `proof.json`) are described in section 1 of this page (see "Licence" for what you may do with them). Points, in plain words (read from the files and the desk's code; no n8n run result is stored here):

* **Retry setting.** The sending box has Retry On Fail on (3 tries, 1 second apart; see `n8n/desk-form.json`). What the caller gets from n8n, and how often n8n sends a request the desk refused with 400 (bad request) or 413 (too large), is not stated here.
* The workflows use placeholder node ids; switch each one on after the import with `scripts/n8n_api.py activate <name>`.
* **The desk refuses a caller that uses a real host name.** It accepts `Host: 127.0.0.1`, `localhost` and `[::1]`. If n8n (or anything else) reaches the desk under another name, for example a container name or a machine name, every request gets 403 `forbidden_host` until that name is listed in `DESK_ALLOWED_HOSTS` (see `docs/settings.md`).
* **Not checked here:** importing through the n8n screen ("Import from file"); running the workflows without a free registered n8n community licence; n8n in Docker; keyed mail mode with n8n; other n8n versions; millisecond overlap of the ten requests; the new result rule of the `proof` workflow (exactly one `new` and nine `duplicate`) in a real n8n, including how n8n finds the output of the step "Wait for the desk to finish" from the last step.
