# Security

This is a demo. By default it uses made-up data and demo servers only, listens only on this computer's own address, has no login (the
portal also has buttons that change the desk's records, and the demo extension, the optional `demo_only` folder, also offers `POST /api/demo/crash`, which stops the desk on purpose at a chosen point, and `POST /api/demo/burst`, which writes made-up leads: see `docs/portal.md`), and is not meant to run anywhere
reachable by other people. Use made-up data only. Real customer data must not go into it, whether or not a real CRM is connected. The check named in the README under "Optional features" (the CRM's administrator lists every automation that reacts to lead status changes) is only the minimum before you connect a real CRM, and the first test uses one made-up contact.

## Reporting a problem

Send a report by e-mail to sales@hadavin.com (it reaches the author), or use GitHub's
private vulnerability reporting: the "Report a vulnerability" button on the Security tab of this repository, if that button is shown.
Please do not describe the problem in a public place first.

## Supported versions and answer time

Only the newest commit of the `main` branch is supported. Reports are answered on a best-effort basis, with no promised time.

## What is and is not covered

* No secret is meant to be in this repository and none is needed. Two checks look for secrets: the job in `.github/workflows/lint.yml` is set up to run a secret scanner over the files and over the whole history, and `tests/test_hygiene.py` scans too. No scan result is stored in this repository, and a scan can miss a secret. With the default settings the demo makes no call to
  any real service and talks only to demo servers on the same computer. These settings, each off by default, send
  traffic to a real service over the network, and each needs a secret that you keep in a file outside the repository:
  `DESK_QUALIFIER=live_claude` (a real AI model from Anthropic; key file, prices and spend caps; `docs/settings.md`, "Live model step"),
  `DESK_CRM=hubspot` (a real HubSpot account; CRM key file and a call cap), `DESK_OUTBOX=smtp_provider` (a real mail
  provider; mail password file and a send cap) and the mailbox reader of `scripts/run_real_check.py` (IMAP, the protocol for reading a mailbox, which also
  needs a password file). The CRM key file and the mail password files are secrets just like the AI key file: never
  commit them, never paste them into a command line, and keep them in a file, not in an environment variable. The one exception is the one-shot script `scripts/hubspot_probe.py` (`docs/hubspot-probe.md`): it reads its token from an environment variable that you set in your own terminal window for that single run. If you find something that looks like a secret,
  report it as above. `scripts/run_live_check.py` also uses a real model key, and `scripts/n8n_api.py` reads an n8n API key from the file named in
  `N8N_API_KEY_FILE` (same rule: a file outside the repository, never a variable or a command line value). The demo-server and plain-SMTP settings (`DESK_FAKES_URL`, `DESK_SMTP_HOST`, `DESK_OUTBOX=smtp`) accept only this computer's own address, so a demo server is not pointed at a remote host by mistake. With any real service set, the desk starts only on a loopback `DESK_BIND`: it has no sign-in, and anyone who could reach the port could create contacts in the CRM, send mail or use up the paid AI model budget.
* Outside contributions (pull requests) are not accepted.
* The software may be downloaded and run for evaluation and testing only (see `LICENSE`).
* Automatic checks (`.github/workflows/`; no result of them is claimed here) look for known bug patterns and secret formats. They do not prove the code
  is free of problems, and they cannot take back a secret that was already pushed to a public place. If a key of yours was exposed, revoke it at its provider first, then report it as above.
