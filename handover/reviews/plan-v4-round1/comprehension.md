# plan-v4 round 1 - comprehension review (condensed, ids kept)

Reviewer: fresh, read-only, reads as someone who has not seen the project; spot-checked against plan-v3. All external prices, licence and vendor facts UNVERIFIED by the reviewer (internal consistency, v3 and arithmetic only).
Summary as understood: client picks the tool (n8n self-hosted, n8n Cloud, Make, Activepieces named alternative); core stays tool-agnostic with one signed-webhook door in and one governed action API out; high-risk steps stay in our code; next build is door plus permanent no-double-apply ledger. Reviewer could not paraphrase how door, ledger, AK1, AK1b and the executor connect beyond the one diagram.

Comprehension findings
- C1 Blocker, s3 diagram and s4: AK-G2, AK1, AK1b, AK1a/1c, AK-G15, AK-G1, AK2a, AK4a, AK-G16, AK0, JG-3, P0t never defined, absent from v3; "step" undefined. Fix: legend or defining file link.
- C2 Blocker, s4 rows P1a/b/c, P4b1/b2, P6b1: sub-ids not in v3 (P1, P4b, P6b unsplit); no mapping; P1c "later" inside a "v1" row. Fix: v4-to-v3 id mapping.
- C3 Major, P5b2/P5b5: v4 says "CI tables and pins" (ast-grep HOLD); v3 defines P5b2 as R3a and P5b5 as R5 (diagnostics redesign). Cutting under v3 needs a written yes and rewrites P5c dependencies. Which is right UNVERIFIED.
- C4 Major: PR numbers 63..86 and "open chain", "P1b fix batch", "PR 66 money chain" undefined; v3 PR list ends at 56. Fix: PR/package/state table.
- C5 Major: verdict words KEEP-CODE, FINISH, WRAP, HOLD, ADOPT, KEEP BUILT, CUT-TO-CONFIG(+GLUE) undefined.
- C6 Major: rung scale defined inline (1 no-code .. 5 own code), R447/R448 cited unexplained; AK2a says "3/4"; studio tool-ladder rule has a different 7-rung order.
- C7 Major: evidence column ("scan table 40-60%", "scan 55-70% wait, 20-30% guarantee", "scan pass 3-4", "scan 3-3", "pass 4", "85-90%") has no file, section or metric.
- C8 Major, s3: door, channel/executor/llm kind, meter, stop_state, audit not defined in v4; "kind" only in v3.
- C9 Major, s2 bullet 1: "same key, one effect, forever" unexplained; window list telegraphic. Fix: one sentence (those tools forget a key after a window; we need never).
- C10 Major: plan names inconsistent (Business EUR 667 as paid self-hosted and as Cloud tier; s5 "Business is self-hosted only" inside the Cloud row); execution, Sustainable Use 1.0, ee folders, Close task undefined; "only automation tool an agency may legally resell" unsupported, UNVERIFIED.
- C11 Major, s2 b2 / s4 P4 / T1 / s10.1: LiteLLM never a core dependency, yet T1 tests it and gates P4b1; s10.1 defaults T1 to "no". If owner is silent the gate disappears and the cap claim stays UNPROVEN. Fix: split T1a (our meter, always, gates P4b1) and T1b (LiteLLM, optional).
- C12 Major, s5: no total or scenario though titled per client per year; EUR and USD mixed; caps not tied to volume; overage missing; Make no figure; hosting "about USD 5-10" but yearly figure firm; "one-person team only" unsourced; claim "total always printed" true only for Port.
- C13 Minor: client-chooses-tools-policy, options-first-then-decide, "client-chooses rule 6", EGM cited by name only.
- C14 Minor: "(+ addenda, pass 4)", "(docs page read)", "tail summarised by a small model" without URL/file/date; "unverified are marked" only partial.
- C15 Minor: Presidio, put-back undefined; "mask" used in two senses.
- C16 Minor, T2: delays 6 min / 25 h / 31 days unexplained; "forever" untestable directly. Fix: rationale or mocked-clock test.
- C17 Minor, s8: EGM sequence shorthand.
- C18 Nit: "Author: lead (laptop)" unexplained. UTC 09:55 / IST 15:25 correct.

Contradictions with plan-v3
- V1 Major, AK-G2 "v1.1 FIRST / BUILD NEXT": v3 starts v1.1 only on trigger, v1 list exact, change only by written amendment; v4 has no amendment and v3 has no AK packages.
- V2 Major, s7.4: "about 1 day of agent time" vs v3 s10 "Estimates: none until S0 exits".
- V3 Major, P5c: v3 s5 default redactor is pattern-based guard.redact, detector-model backend only outline; v4 makes Presidio default; v3 fixes P5c as 4 PRs (F10, session_closed, REGEX_VERSION 4); v4 silent whether they stand; new third-party dependency in the redaction path without the v3 single-dependency check.
- V4 Major, P2d: v3 = land PR #50's change to guard/redact.py, Tier A, v1, P5c depends on it; v4 describes fold scan + hidden-channel refusal, "v1 -> later".
- V5 Minor, s8: "no round cap"; v3 Tier A escalates in writing after round 5.
- V6 Minor, s7.1: laptop evidence "never the same head twice"; v3 s3 has the lead re-run at the merge commit.
- V7 Minor, T1: 50 parallel calls vs v3 s8 8-process Postgres race zero overshoot; say add or replace.
- V8 Minor: Activepieces added as fourth tool; owner decision lists three.

Arithmetic (s5): 240, 600, 8,004, 240, 60-120, 3,600 all correct. Problems are C10 and C12.
- A1 Minor, T1: runs third-party code while the plan says some LiteLLM releases were malicious; "known-good release pinned by hash" not named, unverified.
