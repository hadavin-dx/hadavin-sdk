# Lane 12: does hostile text execute or mis-render in the portal? (EVIDENCE RUNNER: ran and recorded, did not judge or fix)

## ANSWER
**No script executed.** Tree: public branch pr-3-tests, head 558d37fe5372f8c378e7ea07c6193a738f4497ed (verified with git rev-parse). Chromium 153.0.8010.12 headless (Playwright 1.63.0), 24 page visits (2 colour schemes x masking on/off x 6 pages: Overview, Leads, Needs a person, Request log, Data and AI, Demo controls) plus 24 lead side panels per scheme/mask combination. In every visit: 0 dialog events, 0 console errors or warnings, 0 page errors, `window.__xss` stayed `undefined`, and no `script`, `img[src=x]`, `iframe`, `svg[onload]`, `[onerror]`, `[onload]` element existed inside the page or panel (raw: 05-browser-results.json). The hostile strings appeared as visible TEXT (see table).

## Failures, surprises and mis-renders (first)
1. MIS-RENDER (layout, found with an accepted 100 and 200 character name, unmasked): in the lead side panel the title is one unbroken string. `.drawer-head` has scrollWidth 1623 (100 chars) and 3097 (200 chars) against clientWidth 599 (06-overflow-probe.json). The name runs out of both sides of the panel: its start is cut off at the panel's left edge and the status chip and close button are pushed to the far right edge (drawer-light-unmasked-len200.png, drawer-dark-unmasked-len200.png). The close button is still on screen in my 1280 px window. Masked, the title is dots, so no overflow. A name WITH spaces (120 chars, "word word ...") did not overflow (the 5th row in 05 results: 599/599).
2. The 2000-character name asked for was REFUSED by the desk (HTTP 202, review `bad_field:name`), so it never reached the portal. Probing the limit: 100 and 200 characters accepted; 500 and 1000 refused (04-post-more.txt). The exact cap was not located (between 200 and 500). A 2000-character company and message, and a 300-character unbroken company: refused too (`bad_field:company`).
3. Case (g): a name with U+202E (right-to-left override) and U+200B/U+200D was refused: `bad_field:name` (also each on its own). So those never reached the portal either; U+202E mis-rendering is therefore NOT tested in the browser (the desk refuses it first). Case (j) spaces-only name: refused, `incomplete:name`. Emoji name (k) accepted and rendered fine.
4. The hostile text was used in two fields I did not anticipate: the COMPANY column is shown unmasked even when "Hide names and email addresses" is on (docs say so: "Company ... never masked"). So in the masked view the hostile strings (a, b, c, d, e, f, i, k and the company payload) were visible as text in the table anyway. Not a defect in execution terms; it is a visible-hostile-text fact.
5. Table cell for the name is cut to about 5 characters plus an ellipsis ("HHHH...", "<scrip...") at 1280 px; the page and table did not overflow (document 1280/1280, table-wrap 974/974).
6. At a 390 px wide window the Leads page has horizontal overflow (scrollWidth 632 vs clientWidth 390) in all four scheme/mask combinations including masked. I did not run a control with harmless names, so I cannot say whether the hostile rows cause it. Screenshots: leads-*-390.png.
7. Desk behaviour seen (as in lane 11): hostile name text is stored and returned raw in the JSON and is put raw in the demo email subject (table below). The demo outbox entries hold only key, to, subject; there is NO body field in the fake outbox JSON, so the body could not be recorded.

## Case x page x masking x scheme
All four combos (light/dark x masked/unmasked) behaved identically for execution: dialog none, `__xss` undefined, parsed elements 0, console 0, page errors 0. "Text" = the exact hostile string found in the page's visible text (`inner_text`). `-` = not on that page.

| case (posted value, email) | desk answer | Leads table masked | Leads table unmasked | Side panel masked | Side panel unmasked | Request log masked | Request log unmasked | Overview, Needs, Data, Demo |
|---|---|---|---|---|---|---|---|---|
| a `<script>window.__xss=1</script>` (name, company, message) | 201 new | text (company col) | text | text (message/company field) | text | none | text | none |
| b `<img src=x onerror=...>` | 201 new | text | text | text | text | none | text | none |
| c `<svg onload=...>` | 201 new | text | text | text | text | none | text | none |
| d `"><iframe srcdoc=...>` | 201 new | text | text | text | text | none | text | none |
| e `javascript:window.__xss=5` (as name, company, and a `website` field) | 201 new | text | text | text | text | none | text | none |
| f `'; DROP TABLE leads;--` | 201 new | text | text | text | text | none | text | none |
| g RLO + zero-width in name | 202 review bad_field:name | not in table | not in table | - | - | none | none | none (not tested in browser) |
| h 2000 chars name | 202 review bad_field:name | - | - | - | - | - | - | refused, not rendered |
| h2 200 chars (accepted) | 201 | name cut with ellipsis | same; layout OK | dots | **panel title overflows (item 1)** | none | text | none |
| i `{{7*7}}` and `${7*7}` | 201 | text, not evaluated (no 49) | text | text | text | none | text | none |
| j spaces only | 202 review incomplete:name | - | - | - | - | - | - | - |
| k emoji | 201 | text | text | text | text | none | text | none |
| l hostile company + message only, normal name | 201 | text (company col) | text | text | text | none | none | none |

Layout (1280x900): document scrollWidth = clientWidth (1280) on all 6 pages in all combos; table-wrap 974/974 (Leads, Log), 924/924 (Data). Side panel: 599/599 except the two long-name titles (item 1). Screenshots with dimensions (Leads, full page, hostile rows visible): leads-light-masked.png and leads-dark-masked.png 1280x1489; leads-light-unmasked.png and leads-dark-unmasked.png 1280x1367; 390 px variants leads-*-390.png; side panels drawer-*.png.

How masking was switched: the Leads page checkbox `[data-testid="leads-hide-personal"]` ("Hide names and email addresses") was unchecked with Playwright `.uncheck()` in a fresh browser context (docs/portal.md: remembered per browser tab session); the other pages were then reloaded in the same tab so the choice carried. Default (first visit) was masked. Colour scheme: Playwright `color_scheme` light/dark; data-theme/colorScheme recorded per row in 05-browser-results.json. Routes: `#/overview`, `#/leads`, `#/needs`, `#/log`, `#/data`, `#/demo` (from portal.js `pages` registration); each opened with a full reload. Side panel: click of every row on the Leads page (12 rows).

## Mail (demo outbox, GET http://127.0.0.1:8766/fake/outbox; recorded as text, not rendered; 07-outbox-subjects.txt, 03-outbox.json)
Subjects are `Thanks for getting in touch, <name as sent, raw>`: `<script>window.__xss=1</script>`, `<img src=x onerror="window.__xss=2">`, `<svg onload="window.__xss=3">`, `"><iframe srcdoc="<script>parent.__xss=4</script>">`, `javascript:window.__xss=5`, `'; DROP TABLE leads;--`, `{{7*7}} and ${7*7}` (not evaluated), emoji kept; 100 and 200 character names kept whole. No body in the outbox record. Reminder mails carry a lead id only.

## Response headers (08-headers.txt)
Identical on /ui/ pages, /ui assets, JSON endpoints (/api/ui/leads, summary, log, review, data-map, /counts), 404 and POST /leads 400:
| header | value |
|---|---|
| Content-Type | /ui/ and index.html: `text/html; charset=utf-8`; portal.js `text/javascript; charset=utf-8`; css `text/css; charset=utf-8`; JSON: `application/json` (no charset) |
| X-Content-Type-Options | nosniff |
| Content-Security-Policy | `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'` |
| Cache-Control | no-store |
| Referrer-Policy | no-referrer |
| also | Cross-Origin-Resource-Policy: same-origin |
Note: the CSP has no inline-script allowance, so inline `<script>`/`onerror` would be blocked by the browser even if they were parsed. I ran no test with the CSP removed, so I cannot say which layer stopped what; the DOM check shows nothing was parsed in the first place.

## JS write sinks (READING, not proof; 09-js-sinks-grep.txt, 10-js-href-src-grep.txt; files src/lead_desk/portal/**/*.js and demo_only/portal_demo.js)
Hits for `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `.html(`, `eval(`, `new Function`, `setAttribute('on`, `srcdoc`, `DOMParser`, `createContextualFragment`, `.onxxx =`, `.href =`, `.src =`: **none**.
| file:line | sink | receives data? |
|---|---|---|
| portal.js:15 `addKid` | `document.createTextNode(String(kid))` (all text from the desk goes here) | yes, as text only |
| portal.js:19-25 `build` | `setAttribute` only for keys on an allowlist (class, id, role, title, value, placeholder, ...) or `aria-*`/`data-*`; `href` accepted only if it starts with `#`; no `src`, `style`, `on*` in the allowlist | yes: attribute values (e.g. title, data-lead-id) can hold data, but only allowlisted names |
| portal.js:38 | `use.setAttribute('href','#i-'+name)` | icon name from code |
| portal.js:42 `clear` | `el.textContent = ''` | no |
| portal.js:541, 589, 720; leads.js:116-117, 390; log.js:93; portal_demo.js:259, 297 | `.textContent =` | counts and fixed strings; 720 brand sub-label from a setting; portal_demo.js:297 option text from `personText(people[i])` (approver names, from demo file) |
| portal.js:202, leads.js:171, log.js:17 | `setAttribute('datetime', ISO string)` | dates built by `Date` |
| portal.js:341-342; 431; 516; 543 | `setAttribute(k, attrs[k])` in `table()` from `rowAttrs` (leads.js:393 gives `data-lead-id`: a lead id from the desk) and `aria-label` from `label` (leads.js:352: lead name) | yes: lead id and name as attribute values (not event handlers) |
| portal.js:547 | `location.hash` read to pick a page; checked against the registered page list | URL fragment (user-controlled), whitelisted |
| portal.js:577 | `location.hash = '#/' + r` | route id from code |
| portal.js:670-674 | adds `<link href="/ui/demo/portal_demo.css">` and `<script src="/ui/demo/portal_demo.js">` | fixed paths |
| portal.js:527 | localStorage read for a count (parseInt) | number |
Caveat: this is a read of the code. The proof is the browser table above, and only for the data and pages I used.

## What was NOT checked
- Firefox, WebKit (Safari), Windows, Edge; other Chromium versions; mobile browsers.
- The email rendered in a mail client (the outbox has subject only; subjects are raw text).
- Stored XSS through other fields: only name, company, message, and a `website` field were hostile; email, phone, request number (source_ref), source, a CRM id, the lead-owner/approver names, AI rating text, review reasons were not made hostile (the email field is validated by the desk; source_ref was a plain label).
- The `#/...` route values with hostile text, the search box with hostile input, the eye (reveal) buttons, Retry/answer buttons, the "later messages" differences list with hostile text, a Retry-path or failed/unknown follow-up display with hostile names.
- Behaviour with the CSP removed or a browser that ignores it.
- Whether the 390 px overflow comes from the hostile rows.
- The upper name-length cap (between 200 and 500 chars); the U+202E rendering (desk refuses it).
- Real services, n8n, live AI (fake/recorded step only: portal says demo mode).

## Environment and hygiene
Linux, python3.12 venv /tmp/work/l12-venv outside the tree; `pip install --require-hashes -r requirements-dev.txt` for the repo pins; **`pip install playwright==1.63.0` was NOT hash-locked (evidence-run install)**; PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers (chromium 1243, no `playwright install`), node at /opt/node22/bin on PATH. Started: `bash scripts/start_all.sh keyed` (desk 8765, fakes 8766). Stopped: `bash scripts/reset.sh` ("reset done"); after it `pgrep -af "lead_desk|demo_only|start_all|chrom|playwright"` printed nothing (rc 1), curl to 8765 refused (rc 7), `git status` of the tree clean. Browser used one at a time; no test suite run; no push, no PR, no real mail, no live model call. Nothing committed.

## Raw files (this folder)
01-start.txt, 02-post-leads.txt, 03-outbox.json, 04-post-more.txt, 05-browser-results.json, 05-browser-run.txt, 06-overflow-probe.json, 07-outbox-subjects.txt, 08-headers.txt, 09-js-sinks-grep.txt, 10-js-href-src-grep.txt; scripts post_leads.py, post_more.py, run_browser.py, overflow_probe.py; PNG screenshots leads-*.png, drawer-*.png.
