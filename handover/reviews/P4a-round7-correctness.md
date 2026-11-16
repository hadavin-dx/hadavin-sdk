# P4a ticket rev 7, round 7 correctness review

Status: saved by the lead from the reviewer's hand-back (condensed). INCOMPLETE: the reviewer lost context; five Nits (COR-R7-4..8) were lost and are not recorded; COR-R7-3 has no pinned line. Not counted as a clean pass; the resolve must verify each finding against the files and a narrower re-run covers the lost part. Not read: handover/reviews/. Verdict: not clean, 0 Blocker, 3 Major, 5 Nit (lost).

| id | sev | finding | fix |
|---|---|---|---|
| COR-R7-1 | Major | Line 156 says "ONE validator with one owner, P4d-a per P4d round 7"; P4d.md rev 9 has P4d-a1, P4d-a2-i, P4d-a2-ii, P4d-b, P4d-c, no "P4d-a"; the validator is P4d-a2-i (P4d.md line 67). | Write "P4d-a2-i (revision 9)"; fix PENDING LEAD 26 wording. |
| COR-R7-2 | Major | Lines 151 and 262: config.py / defaults.py edit order and a possibly duplicated constant not settled against P4d-a2-i. P4d.md line 273 fixes config.py order (P6b1 after P4d-a2-i, before P4b1; P4b2-b also edits). P4a-2 adds a Config zero-price check and REQUESTS_PER_CHAT; ticket does not say who owns MAX_USD or P4a-2's slot. UNVERIFIED whether P4d defines MAX_USD in defaults.py. | One line: P4d-a2-i owns MAX_USD and the route-price validator, P4a-2 imports them; add P4a-2's slot in the config.py order. |
| COR-R7-3 | Major | A stale claim that P4d "disagrees" with P4a on where rounding happens (line not pinned; in long lines 77, 115, 125, 161-200, 296, 419, 457). P4d rev 9 owns round_cost_up. | Find and replace with "P4d-a2-i owns round_cost_up; P4a calls it". |
| COR-R7-4..8 | Nit | Lost in the reviewer's context compaction. | Re-run narrower or read the transcript. |

Also reported: existing test tests/warden_port/test_providers.py lines 91-101 (test_openai_adapter_estimates_when_the_provider_reports_no_usage) asserts estimated tokens above zero on a missing usage block, contradicting P4a-1's refusal rule; the ticket must list it as an edited test (not confirmed whether it does).
Verified, no defect: all snapshot file/line/symbol cites; wire harness classes exist; counts (32, 39 rows = 43 mutants, 75, 34 test rows, C13 12 sub-rows); Fraction figures; every mutant has a killer row that can fail; cross-ticket claims except the three above; orders 1-13 respected; ticket has all 17 template fields.
