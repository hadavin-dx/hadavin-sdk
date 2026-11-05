# Look-alike round 4: correctness review of designs/lookalike-leak.md draft 4 (head bdab309)

Status: saved by the lead from the reviewer's hand-back (condensed; static reading only, nothing run).
Verdict: no Blocker. One Major (count error). Minors and nits below.

| id | severity | where | problem | fix |
|---|---|---|---|---|
| COR-LK4-1 | Major | section 6 "Mutants" and section 13 | Live mutant count says 31; the stated formula (M1-M33, plus M9b and M18b, minus M18 and M21) gives 33. | Write 33 in both places; recount the P2d ticket total from the same list. |
| COR-LK4-2 | Minor | section 8 P1 bullet; P1 SK-6 and overlap table | (a) SK-6 covers kept/dropped characters, not whitespace removal; the join and LK-SURR need a whitespace row. (b) P1 overlap table lists two constants, design adds four. (c) hedge about `id_key`/`line_view` is settled (cut in rev 10). | (a) cite or request a P1 whitespace row with a mutant; (b) P1 lists all four constants; (c) drop the hedge. |
| COR-LK4-3 | Minor | section 5 item 5, PL-LK-21 | "ONE U+FFFD" has no stated implementation; the probed route gives three characters. Count does not affect the check (scan key drops U+FFFD). | Say "a U+FFFD (one or more)" or name the implementation; add an exact-output unit assertion. |
| COR-LK4-4 | Minor | section 6 LK-PCT-PLAIN, FR-12 | "Passes today" is reasoning, not a run. | Mark UNVERIFIED until the evidence runner shows it on 748849c. |
| COR-LK4-5 | Nit | FR-23 | 17-digit run not measured for a stored id (P8 measured 16 digits). | State: refusal by design, not run. |
| COR-LK4-6 | Nit | header line 2 | Order 11(4) is about P1; the general no-code rule is orders 4 and 8(4). | Cite correctly. |
| COR-LK4-7 | Nit | "Rows that kill no mutant" | LK-NAME-ZE also kills M10 for NAME kinds. | Say so or leave. |
| COR-LK4-8 | Nit | section 10 | Fillers combined with Ze is a stated hole but has no xfail row. | Add LK-INERT-ZE or fold into LK-BE / LK-INERT-DOT. |
| COR-LK4-9 | Nit | LK-CN | `fold` drops Cn; depends on the Python Unicode version (textnorm.py line 28). | Pin the Python version or note the dependency. |

Verified against the snapshot by the reviewer (no discrepancy): redact.py sweep/_sweep/SECRET_KINDS/redact_many/_over_budget/_PLACEHOLDER line cites; pattern ranges in section 9; runmap.py undo/canonical/_clean/redact_text; defaults.py constants; caller and exception paths; textnorm class maps; probe claims P1-P8; arithmetic; internal cross-references (FR-1..28, PL-LK-1..23, LKV-1..9); merge order against P1.md.

Not checked (UNVERIFIED): anything needing a run; P1a/P1b behaviour (tickets only); all timings; whether the case-insensitive sweep or `_clean` change breaks existing repo tests; size estimates; Warden/Intake/approval-card handling of RedactionError; RunMap (de)serialisation of redact_cache; head sha bdab309 (snapshot is not a git repository).
