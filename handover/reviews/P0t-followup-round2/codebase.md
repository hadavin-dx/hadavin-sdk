# PR 83 (P0t follow-up) @e2d8971: round 2, codebase-details review (condensed by the coordinator, ids kept)
Ran nothing; T1-T14 kills judged from reading, UNVERIFIED at this head.
F1 Major | stages.py:28-36 (also runmap.py:276, runtime/evidence.py:57) | fold_name is a third copy of the fold. evidence.normalise is already canonical().casefold().strip(); config.py:376 is a fourth (strip().casefold(), no NFKC). Docstring overclaims: redactor does not casefold. Make one leaf function the single definition.
F2 Major | stages.py docstring, CHANGELOG | Stated reason contradicted by code (label rule masks tenant_id=prod before _COMMON). Restate: a standalone prod copy is not swept.
F3 Major | CHANGELOG "Repair every demo-stage database" | Rewrite narrows the instruction: databases of demo repos (e.g. ask-your-data) that are not stage demo may be read as excluded. Name both groups; say which the merge-commit sentence covers.
F4 Major | test_tenant_ids.py:778-825 | AST walk unsound: only AnnAssign with Name target (misses tenant_id = Field(...), self.tenant_id: str); substring "TenantId" passes NotTenantId, dict[str, TenantId], string annotation; any text "check_tenant_id" in body counts; only "tenant" matched (not org_id etc.); multi_tenant: bool false positive; only src walked; lambdas skipped. Soften CHANGELOG sentence or tighten.
F5 Major | no-echo claim holds only inside _Strict (config.py:67).
F6 Nit fold does not cover Mn variation selectors, CGJ, Cc, Hangul fillers, Cyrillic look-alikes (scan's _fold maps look-alikes); state the limit.
F7 Nit T4 and T11 equivalent. F8 Nit missing plants (drop isinstance in is_stage_name; drop parameter-body check). F9 Nit _exemptions collapses duplicate rows; use Counter. F10 Nit data-split lines need one tsv row each (6 added). F11 Nit negative check case-sensitive.
Reuse: no other caller of check_tenant_id; no model uses TenantId; "guards no live path yet" accurate.
