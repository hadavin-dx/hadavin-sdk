# Notes: fix of review r1 (tree /tmp/v8work; studio folder not present in this container, so no R-numbers cited)

| id | file:line | reviewer's claim | verified how | applied words or REJECTED |
|---|---|---|---|---|
| M1 | contract.md:319 | heading says three, four bullets | counted bullets | "Three more known limits" -> "Four more known limits" |
| M2 | contract.md:136 | exit 4 is given in more places than three | server.py: reminder_setting_problem (1160), DeskSettingRefused at start-up (1211) read; limits.md already lists the others | "in any of three places" -> "in any of these places"; added bind check, `:memory:` db_path, approvers file, lead flow file; added start-up steps mismatch after the budget clause |
| M3 | contract.md:305 | quoted hint differs from code | desk.py HINT_CRM_UNCONFIRMED 215-219 | quote replaced with the code text ("Retry goes straight to the email", "Retry asks the CRM again", "sent is refused here: no email was ever tried") |
| M4 | contract.md:124 | card title not "nothing was sent" | portal_api.py 727-728 (person text first), 770-785; portal.js 66 | opening -> `the list calls the kind "Follow-up failed") has the title "The follow-up email was not sent"`; "any failed" -> "any other failed ... a person-choice reason keeps its own card, because the person's words are checked first" (symbol name written in words) |
| M5 | limits.md:155 | test does not look at the request body | tests/test_lead_crm_copy.py 84-89; crm_hubspot.py 397-405 | replaced; reviewer's "local stand-in" written "demo copy of HubSpot" (banned word) |
| M6 | limits.md:159 | probe made two separate writes | docs/hubspot-probe.md line 3 and 61 | "It showed one write (`OPEN`) accepted." -> two separate calls each accepted, combined call not tried |
| M7 | limits.md:116 | empty value shows "empty" only in comparison | leads.js 98 (`if (r[1])`) and 247 | replaced as proposed |
| M8a | portal.md:29 | write list incomplete | leads.js 148 (`/step`), 222 (`/review/D.../resolve`), portal_api reminder card button | added the three-controls sentence after "cannot stop that." |
| M8b | contract.md:113 | same | same | "Retry, the answers, Approve, Deny and “I checked the mailbox” call `/review/...`; the lead stage Move control calls `POST /leads/<lead id>/step`" |
| m1 | contract.md:123 | stray ")" | read the bullet | final ")" removed |
| m2 | contract.md:36 | give-back age sentence wrong | desk.py _give_back docstring 1866-1873, _closed_kind 1568-1590 | replaced as proposed (tests names kept, order moved) |
| m3 | contract.md:195 and 260 | auto_attempts is shown by the portal detail | portal_api.py 407, 441 | "which `GET /leads/{lead_id}` does not show (the portal's lead detail does)" in both places |
| m4 | settings.md:141 | --leads and --runs missing | run_live_check.py add_argument lines; docstring lists required flags only | replaced as proposed |
| m5 | limits.md:93 | burst script wording | demo_only/burst.py 155-161; the line in the tree already says RESULT or MISMATCH | REJECTED: already correct in the tree (the review text is out of date) |
| m6 | settings.md:12 | conflicts with limits item 7 | read both | replaced with "no run against a real mail account is claimed, and no shipped evidence shows sending to one" |
| m7 | contract.md:227 | portal_actions list incomplete | constants.py 282 PORTAL_ACTIONS = ("retry","resolve"); leads.js 148 | added "(the lead stage Move control, `POST /leads/<lead id>/step`, is not in this list)" |
| n1 | limits.md:48 | _call_running counts more than hung_workers | desk.py 2239-2242, 2274 | added "and a few seconds more (the desk answers `call_still_running` until the old call has ended)" |

Not changed: the word "stand-in" that already sits elsewhere in contract.md (2), limits.md (2) and settings.md (1) is outside the FIX rows; left alone.
Not checked: nothing run (no pytest, no linter, no network). A 40+ character run check of the added lines found none.
