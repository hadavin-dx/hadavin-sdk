# HubSpot free-account probe

A small script that makes a few HubSpot calls and then tries to delete its test contact (if the delete is refused it prints a WARNING that names the contact, so that you can delete it by hand). It answers one question: does a free HubSpot account accept the two API writes the desk needs (set the owner, set the lead status)? The desk makes both in one combined call; the probe makes them as two separate calls, so it does not test the combined call. Only the probe lists owners; the desk does not. A run makes 6 calls when no owner is found, because the owner write is then skipped, and 7 calls otherwise. The token it needs is a private-app token (the access token made in HubSpot's "private apps" settings). The tests in `tests/test_hubspot_probe.py` check that a run stays inside the call budget (`CALL_BUDGET` in the script is 8 and `PLANNED_CALLS` is 7; the tests compare against `CALL_BUDGET` and also check the printed lines "calls used: 7 of 8" and "calls used: 8 of 8") and the masking of the token, against a local demo server, not against HubSpot.

Run it on the free demo account only, never on an account that holds real contacts. Creating or assigning a contact can
trigger things on the account side that the script cannot see: an owner assignment might send that user a notification
email (not confirmed, see below), and any automation (a HubSpot workflow or sequence) on the account that reacts to a new contact or a new owner can fire. A fresh demo
account with no workflows and a throw-away owner is the safe place.

What it does, in order (7 calls on the normal path, never more than 8 including retries):

1. Checks whether the contact property `dpld_tag` exists (`dpld` is short for duplicate-proof lead desk, the project name; it is a test tag; the script fills it in on the new contact only when the account already has it; the desk's own contact property is a different one, `hadavin_lead_id`, see `docs/real-services.md`).
2. Reads up to 10 owners; prints only the count (no part of an id is printed, because ids come from the server's answer).
3. Creates ONE contact with a made-up address `probe-<random>@example.com`.
4. Sets the first owner on it (by email), in its own call.
5. Sets the lead status `OPEN` on it, in its own call (two calls, so the table says which of the two a free plan refuses).
6. Reads it back and compares the values that were written.
7. Tries to delete it: permanent delete first; if that is refused and the contact id is known, the normal delete (archive). If both are refused, the `delete` line shows FAIL and a WARNING names the contact to delete by hand.
   When the create answer was lost, only the permanent delete by email is tried (HubSpot documents the normal delete for an id only).

Call arithmetic. The hard budget is 8 calls; every retry after a "busy" answer (429) counts. The normal path is 7 calls: steps 1 to 6 are 6 calls and the permanent delete (step 7) is the 7th. Steps 1 to 6 may use at most 7 calls in all, so the 8th call is always kept for the delete. That leaves 1 spare call, which pays for one retry or for the archive-delete fallback, not both. If a retry used the spare and the permanent delete is then refused, the fallback delete has no call left, and the script prints a WARNING naming the contact. The worst case is exactly 8 calls. If the answer to the create call is lost (timeout, a 5xx answer, or no id in the reply) the script
cannot know whether the contact exists, so it uses its cleanup call to delete by the made-up email address; if that is
refused it prints a WARNING with the exact address (`probe-...@example.com`) to look for and delete by hand.

It prints PASS/FAIL for: owners readable, contact create, owner write, lead-status write, read-back equal, delete,
plus the HTTP status classes seen. It never prints the token or a header. For a refused call (a 4xx answer) it prints the HTTP status and HubSpot's error category when that is one of a fixed list of words; it prints no text of the server's message and no other part of a reply (a server could echo the token in a changed form that a search for the exact token would miss). The desk's own change of owner and lead status is one combined call (`crm_hubspot.py`), while the probe makes two separate calls so the table shows which one is refused: the probe does not test the combined call.

Run (after you have agreed to the 7 planned calls; the hard cap is 8, see the call arithmetic above; the token is a private-app token that you put in an environment variable of
your own terminal window for this one run, and never type as an argument; close the window afterwards. This is the one
place in this repository where a secret is read from a variable: the desk and the other scripts read secrets from a
file, see `SECURITY.md`):

    python -I scripts/hubspot_probe.py --plan
    python -I scripts/hubspot_probe.py --yes-spend-calls 7

Private-app scopes used (the list is what the script calls; this repository holds no copy of HubSpot's scope list, so the exact scope names are UNVERIFIED; check them all when creating the token):

- contacts read: owner read-back, the `dpld_tag` property check (this needs the contacts schema read scope; if the token
  lacks it, HubSpot answers 403 and the script reads that as "property absent" and skips it, after which the contact is still created, only without the tag),
- contacts write: create and update,
- owners read: the owner list,
- the permanent delete (HubSpot calls it the GDPR delete, the call for erasing a person's data on request) may need a further scope; if it is refused the script falls back to the normal delete,
  which only archives the contact.

`--token-env NAME` changes the variable name (default `HUBSPOT_PROBE_TOKEN`); it must be a plain variable name, anything
else is refused without being printed. `--dry-run http://127.0.0.1:PORT` runs the flow against a local stub (loopback
only); the tests do this. If the delete step prints a WARNING, delete the named probe contact by hand.

## What the script sends (read from `scripts/hubspot_probe.py`)

This repository holds no copy of HubSpot's documentation, so nothing here says what HubSpot's pages state. The script sends: create `POST /crm/v3/objects/contacts` with
`{"properties": {...}}`; update by email `PATCH /crm/v3/objects/contacts/{email}?idProperty=email`; read by email
`GET` on the same path with `idProperty=email` and a comma-separated `properties`; the owners list `GET /crm/v3/owners`; the permanent delete
`POST /crm/v3/objects/contacts/gdpr-delete` (with `{"objectId": "<email>", "idProperty": "email"}` when only the email is known); and, when a contact id is known and the permanent delete is refused, the normal delete `DELETE /crm/v3/objects/contacts/{id}`.

UNVERIFIED (this repository does not establish it): the exact scope names; whether the owner
assignment sends a notification email; and what HubSpot does with an email that gdpr-delete cannot find.
