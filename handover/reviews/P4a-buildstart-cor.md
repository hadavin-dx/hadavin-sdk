# P4a build-start correctness review (rev 12) - agent a980ece3f722dc7da
Status: REPORTED (saved by the lead from the hand-back, condensed; model output, not user authority). Read-only, nothing run, did not read reviews/ or evidence/.
Verdict: no wrong figure or killer found; cannot start today (COR-1).
| id | sev | problem | fix |
|---|---|---|---|
| BS-P4a-COR-1 | Major | P4d/P2a/P1 names (round_cost_up, MAX_USD ...) absent from src; order 20 requires them merged first. | State start gate "P2a-1 and P4d merged" at top. |
| BS-P4a-COR-2 | Major | U5 allows zero usage from FakeLLM, but FakeLLM goes through build_usage/cost_usd where the input-zero rule refuses; ticket does not say which wins. | One sentence: fake kind exempt (say where) or fake replies must carry non-zero tokens; add test row. |
| BS-P4a-COR-3 | Minor | Ticket fixes hot-file order and a one-sitting chain; order 20 says own-block rebase, no fixed defaults.py order. | Match order 20 or cite the overriding order. |
| BS-P4a-COR-4 | Nit | ConfigError counts will drift; only +2 delta (replay.py 6 to 8) is stable. | State delta, recount at merge. |
| BS-P4a-COR-5 | Minor | Non-dict usage on OpenAI-compatible/Gemini becomes plain ProviderError, which run_case books as free. | UsageMissing("absent","usage") for every kind when usage is not a dict; add C-row. |
| BS-P4a-COR-6 | Nit | Stale cites: PL header 51/43/63 vs 53/45/65; table.py 388 and 513; worst_case_usd loop.py:115-122. | Update. |
| BS-P4a-COR-7 | Nit | Mutant a2-16 targets P4d Price validator not on main. | Needs P4d merged or move to P4d. |
| BS-P4a-COR-8 | Nit | Other encode( sites in k1b/ not all checked. | Builder greps encode( in k1b/ first. |
Verified: cites across llm/, k1b/, config, models, backends, cli, app, agent_loop; W=0.027360, 6W=0.164160 and all other money figures recomputed; counts 36+47=83, rows 17+17, C13 19 sub-rows. Not checked: nothing run; pydantic/Python 3.12; wire behaviour; other tickets' text; main vs ce70eb5.
