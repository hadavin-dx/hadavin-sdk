# Look-alike design, round 6 correctness review (draft 6)

Status: saved by the lead from the reviewer's hand-back (condensed). RELIABILITY WARNING: the reviewer said it could not re-read the design, P1.md or LEAD-ORDERS.md after its own context was compacted, so findings come from earlier reading and several are vague. The resolve must verify each finding against the files before deciding. Not counted as a clean pass. Nothing under reviews/ was read by the reviewer. Verdict: not clean.

| id | sev | finding (as reported) | fix (as reported) |
|---|---|---|---|
| COR-LK6-1 | Blocker | Expected outcome of row LK-PH-ENT (about lines 78-117) contradicts mutant M6 (about lines 118-121); both cannot hold. No concrete input given. | Decide which is right under the scan-key rules; change one; recount live mutants (32 or 30). |
| COR-LK6-2 | Major | P1.md went from rev 10 to rev 11 during the review; the design may cite rev 10 features (SK-6 isalnum, l-to-i, rules 1-4 only, pinned squeeze, REFUSAL_HANDLERS three entries, error contract). | Re-pin to P1 rev 11; re-check rows involving `l`, punctuation, handler count. |
| COR-LK6-3 | Major | The IN-GATED middle outcome has no approval in order 13 (same as ADV-LK6-6). | Cite approval or reduce to IN and OUT. |
| COR-LK6-4 | Major | `runtime/agent_loop.py` missing from the file list; files not marked new or edited. | Add and mark. |
| COR-LK6-5 | Major | `error_reason(exc, secrets=None, scrub=...)` is called positionally by tests; a new parameter or reorder breaks them. | New parameter keyword-only at the end; say so. |
| COR-LK6-6 | Nit | k1b citation: call at line 188, `except runmap.TooDeep` at 189 in the snapshot; design is off by one. | Correct. |
| COR-LK6-7 | Nit | `redact_text` has no `_lookalike` parameter today; say it is new. | State. |
| COR-LK6-8 | Nit | Some cross-references in sections 7-13 do not match final numbering. | Re-walk. |
| COR-LK6-9 | Nit | P2d.md (rev 5) says P2d-2 depends on P1a (line 264); design's order overrides; P2d tier N limit 4 stale. | Update P2d (rev 6 author) or state the design overrides. |
| COR-LK6-10 | Nit | "too large to show here" string not found in snapshot tests; claim UNVERIFIED. | Drop or cite. |

Counts recounted by the reviewer and matching the design: 43 LK ids in 39 lines; 31 FR rows; live mutants 32 or 30; xfail 6 plus 2, 1 or 0; constants 2 or 3. Code citations matched except findings 4-7. Order 13 judged not obeyed as written because of COR-LK6-3.
