# ID-VID-CHECK: what reads the CRM contact number (`id` or `vid`)

Static reading only. Nothing ran (no n8n, HubSpot, Postgres, mail server). Made-up data only. Written 2026-11-16 (UTC).

**Summary (4 lines)**
1. UNVERIFIED: whether the real n8n HubSpot node (type hubspot 2.2, contact, upsert) answers the contact number as `id`, as `vid`, as a number or as text. The only source is a code comment in `build_mainframe.py:26-27` ("answer {vid, isNew}, Simplify Output off"); the HubSpot probe never ran. The node does not set "Simplify Output" in the JSON, so which answer shape it gives is not shown by the file either.
2. Only ONE place decides if the lead survives: node `CrmIdOk`, test `/^[0-9]+$/` over `String(id ?? vid ?? '')`. Anything else (empty, letters, minus sign, decimal point, exponent form) sends the lead to `OutStage`: row stays `processing`, retried about every 45 s, ends `failed` after 3 tries, 0 mails, 1 alert.
3. One trap: if `id` is present but empty text or non-digit while `vid` is a good number, `??` keeps `id` and the lead still fails (`??` skips only missing or null, not empty text).
4. Rehearsal check with ONE made-up lead: open the CrmUpsert output in the n8n execution list and read (a) the field name(s) present (`id`, `vid`, both, or neither), (b) number or text, (c) digits only; then confirm the table row has `crm_id` of digits only and state `done`. Only then may a scene say the real CRM "answered with an id".

## A. Every place that reads `id`, `vid`, `contact` or the CRM number

Line numbers are for the real set (`handover/demo/n8n-flows-real-v5/`); the film set (`n8n-flows-film-v5/`) differs where stated. Both sets use identical expressions in SetCrmId and CrmIdOk.

| # | Node / file / line | Exact text | What it does | `id` (digits) | `vid` only (digits) | number type (e.g. 12345) | text with non-digits (e.g. "abc", "-5", "1.5", "1e21") | missing / empty |
|---|---|---|---|---|---|---|---|---|
| 1 | CrmUpsert, real `mf-sub-crm-mail.json:74-92`, generator `build_mainframe.py:25-30` | `resource: contact`, `operation: upsert`, `email: ={{ $('SubIn').first().json.email }}`, custom properties `hadavin_lead_id`, `hadavin_label` | Calls HubSpot; its answer is what rows 2 and 3 read. The node name `contact` is a HubSpot resource, not an n8n value we read. | n/a (it produces the answer) | n/a | n/a | n/a | If HubSpot refuses (error, missing property `hadavin_label`/`hadavin_lead_id`, bad token) the error output goes to `OutStage` (connections line 616-623). Not an id problem but same effect. |
| 2 | SetCrmId (Postgres), real `:115-117`, film `:101`, generator `:51` | `UPDATE mf_leads SET crm_id=$2 ... WHERE lead_key=$1 AND claim_token=$3 AND state='processing'` with `String($json.id ?? $json.vid ?? '')` | Writes the text into column `crm_id` (text). Reads `$json` = the CrmUpsert answer item. | stores digits | stores digits (only if `id` is null or absent) | `String(12345)` = "12345": fine | stores whatever text it is (no failure here); the row now holds a bad `crm_id`. "1e21": a very large number prints as "1e+21" and fails the digit test | stores empty text "" (not NULL) (V5-README line 6) |
| 3 | CrmIdOk (IF), real `:146`, film `:130`, generator `:52` | `/^[0-9]+$/.test(String($('CrmUpsert').first().json.id ?? $('CrmUpsert').first().json.vid ?? ''))` | The only gate. True goes to OwnsClaim1, false goes to `OutStage` (connections `:636-653`). | passes | passes (only if `id` null/absent) | passes (a whole number prints as digits; a decimal, negative, or exponent-form number does not) | FAILS: lead goes to OutStage | FAILS: lead goes to OutStage |
| 4 | OwnsClaim1 (IF), real `:178`, film about `:162` | `={{ $json.lead_key }}` notEmpty | Reads `lead_key` from the SetCrmId result row (RETURNING), NOT a CRM id. Empty means this run lost its claim (lease taken over) and goes to `OutLost`. | n/a | n/a | n/a | n/a | An empty row (claim lost, or SetCrmId matched nothing) goes to OutLost; this is the claim check, not the id check. |
| 5 | SendMail, real `:258-260` | subject `'[demo] lead ' + lead_key`, text `made-up thank-you text` | Mail text does NOT contain the CRM id. | no effect | no effect | no effect | no effect | no effect |
| 6 | Recovery `mf-recovery.json` (real and film) | no `crm`, `vid` or CRM id expression (searched) | Retries and failure marking use `attempts`, `claimed_until`, `mail_sent`, not the CRM id. | no effect | no effect | no effect | no effect | no effect |
| 7 | `mf-form.json`, `mf-hook.json` | `lead_key` from `body.submission_id` / `body.message_id`; other `id` hits are n8n internal ids ("c1", `mode: "id"`) | No CRM id read. | no effect | no effect | no effect | no effect | no effect |
| 8 | Film only: CrmUpsert is an HTTP call to `$env.MF_CRM_URL/upsert` (film `:79`, `:84`) | body `{hadavin_lead_id, email, label}` | Stand-in CRM `crm_stub.py:42-43` answers `{"id": ..., "created": ...}` (default), `{"vid": ...}` or `{"created": ...}` by control `upsert_answer`. Proves nothing about real HubSpot. | stand-in only | stand-in only | stand-in only | stand-in only | `upsert_answer="none"` (test T18) ends `failed`, 1 alert |
| 9 | Patches in `flows-audit/patches/` | F-001 DDL has column `crm_id text` (line 12); F-008 (`build_mainframe.py` save-runs patch) touches no id expression; F-002, F-003, F-004 only wording or key check; nothing reads `id`/`vid` | no new reader | - | - | - | - | - |
| 10 | Take-side readers (NOT in this checkout) | `PLAN-4-NLITE-FROM-LEAD.md:68`: `(crm_id ~ '^[0-9]+$') AS has_crm`; `n8n-mainframe/mf.py:77-78`: `has_crm_id = bool(non-empty)` (stand-in harness, weaker than the regex); the take script itself is absent | Reads the stored column after the run. | has_crm true | true | true | has_crm false (take) / true (mf.py) | false |

## B. Which node breaks the lead, per case

"Breaks" means the lead goes to `OutStage` (outcome `stage_failed`, the form reply says verdict `processing`, the row stays `processing` with no state write), recovery re-claims it after the 45 s lease, and after 3 attempts `MarkFailed` sets `failed` (or `unknown` if the mail was already sent; here it cannot be, because MailClaim sits after CrmIdOk) and one alert mail goes out. 0 mails to the intake box.

| Case HubSpot gives | Breaks at | Result |
|---|---|---|
| `id` = all digits, number or text | nothing | done, `crm_id` digits |
| only `vid` = all digits | nothing | done |
| both `id` and `vid` digits | nothing (`id` wins) | done |
| `id` empty text "" and `vid` digits | CrmIdOk (the `??` does not fall through "") | failed after 3 tries, although a good `vid` exists |
| `id` text with non-digits (e.g. a long code) and `vid` digits | CrmIdOk (`id` wins) | failed after 3 tries |
| `id` or `vid` negative, decimal, exponent form ("1e+21"), or has spaces | CrmIdOk | failed after 3 tries |
| neither field | CrmIdOk | failed after 3 tries (T18 is the planned test; under ORDER 037 there is no stand-in run, and it has not been run against the real trial flows) |
| answer comes as a list of 2 items | SetCrmId runs twice (second run matches the same row and rewrites it; harmless), CrmIdOk reads only `.first()` | result depends on the first item |
| HubSpot error (token, missing custom property) | CrmUpsert error output to OutStage | same failed-after-3 path; retried upserts keep one contact per e-mail |

In every failing case the contact already exists in HubSpot, and SetCrmId has already written the bad or empty text into `crm_id` (V5-README line 6). Each retry upserts the same contact again (same e-mail).

## C. Claims that name the CRM id or say the real CRM answered

| File and line | Claim (short) | Status |
|---|---|---|
| `CLAIMS-TABLE.md`, the section "Checks (P1, P2, P4a, P4b, P4c)" (check P4a, the all-digit id condition; the cite 'P3' named a check that no longer exists there) | "HubSpot answers an all-digit id (A-012, node CrmIdOk) before any real-v5 scene is filmed." | Right: it is a condition, unverified |
| `CLAIMS-TABLE.md`, claim A-012 (row 7, run sheet line 31) | "CRM list shows 1 row (real CRM service)"; marked SUPPORTED (read only) | Does not say the id; "SUPPORTED" is read-only |
| `CLAIMS-TABLE.md`, row 78 (VIDEO-RUNSHEET.md, before scene 1) | "whether HubSpot answers an all-digit id (scenes 2 and 4) was not observed" | Correct and honest |
| `CLAIMS-TABLE.md`, claims B-179 (CrmIdOk regex) and the line "Real HubSpot node (BM:25-30)" under "Node facts checked in text" | CrmIdOk regex; BM:26 comment says answer `{vid, isNew}` | Source of the `vid` belief; a comment, not a measurement |
| `CLAIMS-TABLE.md` claims B-006, B-053 and B-171 to B-181 | v5 fix `id ?? vid ?? ''` plus CrmIdOk, "SUPPORTED", "not yet run" | Flow text only |
| `CLAIMS-TABLE.md` claim B-051 | "done = ... has_crm true (numeric id)"; SUPPORTED "statically consistent" | Needs the take script (absent) and the real answer |
| `CLAIMS-TABLE.md` claim B-040 | `has_crm` SQL `crm_id ~ '^[0-9]+$'` | Take-side; script absent |
| `CLAIMS-TABLE.md` claim B-224 | "the CRM id read back from HubSpot" is NOT checked by the take | Correct |
| `SCENE-FLOW-MAP.md:23, 38` | CrmIdOk "checks the CRM answer is all digits" | Describes the file |
| `SCENE-FLOW-MAP.md:53` | Kind A (scenes 1 to 4): "one real CRM service (the CrmUpsert node is the CRM node)" | Says real service, not the id |
| `SCENE-FLOW-MAP.md:69` (C4) | "a real CRM answer that is not all digits would send the lead to OutStage ... can break scenes 2 to 4. The real answer is unmeasured. Rehearse first." | Correct, matches section B |
| `RUNSHEET-WORDING.md` entries R3, A-001, A-008 | "real CRM service" for scenes 1 to 4 | Names the service, not the id; still true only if HubSpot answers a digit-only id |
| `RUNSHEET-WORDING.md` entry B-062 | "v5 changes SetCrmId, adds CrmIdOk, sets the HubSpot credential id" | Accurate |
| `demo/VIDEO-RUNSHEET.md:4` | "real mail service and real CRM service in scenes 1 to 5" | Overstated (scene 5 is the stand-in; patch F-003 fixes it) |
| `demo/VIDEO-RUNSHEET.md:11` | "flows real-v4, v5 changes only the CRM id step" | Overstated: v5 also adds CrmIdOk and the credential id (patch F-003, B-062) |
| `demo/VIDEO-RUNSHEET.md:31` | scene 2: "CRM list shows 1 row (real CRM service)" | Shows a row count from the CRM list, not an id; passes only if CrmIdOk passed |
| `demo/PLAN-4-NLITE-FROM-LEAD.md:136, 191` | Check "the HubSpot node returns `id` or `vid`"; risk "not yet run" | States it is open |
| `demo/n8n-flows-real-v5/V5-README.md:1,3,22` | "BUILT, NOT RUN"; v4 stored `String($json.vid)`, v5 uses `id ?? vid`; "a non-numeric real id would now FAIL the lead, so check that first" | Honest |

I found NO sentence in these four files that says the real CRM "answered with an id" as a fact. The closest are the scene 2 row (CRM list shows 1 row) and P3 (a pending condition). Nothing in them may be read as measured.

## Not checked

- What the real HubSpot node actually answers (`id`, `vid`, number or text, one or many items): the probe never ran; n8n node source was not re-read here (comment at `build_mainframe.py:26-27` says "read from the 2.46.6 source", not re-verified by me).
- Whether the node's "Simplify Output" default changes the answer shape (the JSON sets nothing).
- The take script and `crm_hubspot.py` (absent from this checkout), so how the take reads `crm_id` is from PLAN-4 text only.
- `VIDEO-RUNSHEET.md` lines outside those found by search for "crm"/"id" words; other docs not named in the task (OWNER-STEPS, WATCH-CHECKLIST) beyond what CLAIMS-TABLE quotes.
- Scratch copies under `flows-audit/tools/scratch/` (older generator copies) were not read.
- No test, no n8n import, no EGM review (EGM skipped: read-only static audit of one note; the lead runs the review).
- Nothing committed.
