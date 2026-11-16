# P4a round 4 adversarial review (egm:egm-design), ticket rev 4 (head 2a93cc7). Condensed by the lead; reviewer read-only, ran nothing.
Verdict: not clean. No blocker, five majors (money path).
| id | sev | where | problem | fix |
|---|---|---|---|---|
| R4-1 | Major | openai_compat chat; U4; k1b loop ProviderError branch | Request 1 billed, request 2 fails (exhausted/plain/parse): request 1 Usage lost, 0 booked | Re-raise as billed-unknown (`UsageMissing("absent","usage")`); U4 rows; k1b and demo book non-zero |
| R4-2 | Major | k1b/loop.py:173-178 | `ProviderExhausted` (all attempts timed out) books 0 though CallTimeout is sized by attempts; unsourced "not billed" | Charge it (request worst case x max_attempts) or source why not; C13 row and mutant |
| R4-3 | Major | U2, rule at L36/L341 (PL5) | Reported output 0 kept though reply has text/tool call; U2 pins an under-charge | `implausible_zero("output_tokens")` when text/tool calls non-empty; keep 0 for empty/refusal/blocked |
| R4-4 | Major | Answer-first 6, C8/U2b | Price 0 accepted on live route (comment says cap disabled); only replay refuses | Decide: refuse 0 in Config for every kind except fake, or explicit opt-in; PENDING LEAD |
| R4-5 | Major | Answer-first 5, PL24 | Tiered under-pricing (Haiku 5x above 100k prompt tokens) has no code control | Checklist item with a number: P4b1 pre-call bound <= boundary of any configured model, row+mutant; or pre-call refusal |
| R4-6 | Minor | k1b/loop.py:47-48 | requests/max_attempts/negative not validated; TypeError inside except escapes run_case | Validate ints >=1, non-negative tokens, Budget.charge refuses negative; C13 rows |
| R4-7 | Minor | UsageMissing branch | Charge without attempts factor | Same factor or state why |
| R4-8 | Minor | L209/L222/L16 | "Refuses unknown pricing words" true only for Anthropic | Narrow wording or read OpenAI service_tier; Gemini V-row |
| R4-9 | Minor | gemini.py:96-106 | Missing candidatesTokenCount => output 0 for SAFETY/MALFORMED cut-offs (may be billed) | Output 0 only for no-candidates+blockReason |
| R4-10 | Minor | U14, U14b, a2-30, C7(f), U6 | Teeth: U14 never calls round_cost_up; a2-30 no natural patch; C7(f) "ALONE" wrong; missing guard mutant; U6 floor unsourced | Fix each; add max case and a2-25b mutant |
| R4-11 | Minor | L40, L312 | Coupling checklist text absent in P4b1 today | Hard gate before P4a-1 merges; P4b1-b mutant |
| R4-12 | Minor | L63 | Non-ProviderError from round_cost_up/request_bound escapes after paid call | Wrapper requirement + row: reservation settles at reserved |
| R4-13 | Nit | L3 | Header head 2396b8d vs 2a93cc7 | Re-run diff at final head |
Held up: arithmetic 0.015660/0.031320/0.093960/0.016860/0.0042/0.0009; rounding cannot raise on admitted inputs; retries off in SDKs; cites matched; no cut reopened.
Not verified: nothing run; P4b1:149, P4b2/P6b1/P4c bodies; live provider shapes.
