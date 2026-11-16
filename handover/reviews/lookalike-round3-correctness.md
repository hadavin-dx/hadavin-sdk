# Look-alike design round 3: correctness review (draft 3, head 74a6e26)

Reviewer: fresh egm codebase-details reviewer (a764f4b535188a4a7), read-only, ran nothing. Saved by the lead session; condensed. Result: no blocker, 3 major, 5 minor, 2 nit. About 60 code cites resolve exactly. UNVERIFIED: every regex result (read, not run), the section 2 leak table, all timings, Warden/Intake, the P2d alias claims, idempotence of the second pass.

| id | sev | where | problem | fix |
|---|---|---|---|---|
| COR-LK3-1 | MAJOR | section 7 (1), section 5 | Claim "`_sweep_copies=False` is redact_many's first pass" is false: `redact_many` (redact.py 1527-1537) calls `r.find` then `r.sweep` and never `redact()`; no `src/` caller passes False (flag at 874, 887; comment at 887 stale). "Four cases" is three in production. | Say no caller in `src/`; drop or label "external callers only"; state what `check_lookalike` does when False. |
| COR-LK3-2 | MAJOR | sections 5 item 3, 10, 13 | Cites "P1.md 61 and 116 / 56 and 112" do not resolve in rev 9 (U+FFFD drop at 63, SK-6 at 73, RES-1 at 74; Eta limit at 65, 63, 138). | Re-cite; name SK-6 and RES-1 by id. |
| COR-LK3-3 | MAJOR | header, section 8 first bullet | Header says P1 rev 8; P1 is rev 9; section 8 relay "reverse that" already done (P1 line 18, 269, `REFUSAL_HANDLERS` names `check_lookalike`, RES-1 settled by PL-LK-12). | Header rev 9; list only open asks (public `fold`/`squeeze` with today's signature, SK-6). |
| COR-LK3-4 | minor | section 6 | 22 FR ids, M1-M23 plus M9b, M18b = 25 mutants; M6's killer includes an unnamed junction row; many rows kill no mutant (LK-ORDER, LK-UP/LOW, LK-SPLIT, FR-1,3,4,5,7,11,14,15,16,17,19-22, GOLD-1); no mutant removes case folding or whitespace removal. | Name the M6 row (LK-PH-ENT); add a mutant or state P1b-only killers. |
| COR-LK3-5 | minor | section 3 | "A refusal ends the whole run" is true only for the four `agent_loop` paths; capped.py 72-73, tools.py 1006-1009, `safe_head` degrade; a document refusal reports `redaction_error` not `document_too_large` (371-375). | One sentence. |
| COR-LK3-6 | minor | section 5 callers | Incomplete: tools.py:982 (real map), bedrock_guardrail.py:98, evidence.py:154, channel.py:29,36 (joined map, `\0seed`), slack_channel.py:81. | List with maps. |
| COR-LK3-7 | minor | FR-8, FR-15 | `MAX_MAP_ENTRIES = 2000` (defaults.py 24-25), enforced at agent_loop 382, 502 after redaction; 4,000 originals only via bare caller or one growing call. | State the cap. |
| COR-LK3-8 | minor | section 9 | PHONE `\+?\d(?:[\d \-]){8,14}\d` is 10-16 characters including separators, not digits; "glued" column tests a letter before only. | Reword. |
| COR-LK3-9 | nit | call site text | runmap 526-527 clear/update run after the try; raising before them needs a restructure of 521-527. | Say so; count the size. |
| COR-LK3-10 | nit | section 6 header | "Each LK row's refused half fails on 748849c": PIN rows and non-LK rows (LATER-PLAIN) exempt. | Say so. |

Verified (abbreviated): runmap 274-280, 399-412, 484, 522, 570-600, 534/542; redact.py 986-992, 1256-1333, 1485-1500, 1082, 1187, 1056-1059; pattern ranges EMAIL, IBAN, BANKACCT, ACCOUNTID, TENANT, ADDRESS, NAME, PHONE; HIGHENTROPY 40+; `_confusables.py` 0x0437, 0x0431, 0x03B7; internal numbering FR-1..22, PL-LK-1..15, LKV; arithmetic 9e-8 and 2.6e-7; P1 merge order matches.
