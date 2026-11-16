# P1d rev9 plan review round 9, design (saved from agent hand-back)

PLAN REVIEW ROUND 9 (design) of P1d rev 9, P1d-learn rev 2 and P1d-gate rev 2. Read-only. I read all three tickets, the sibling note, the TEMPLATE and CLAUDE.md. I checked `redact.py` `_place` and the `PRODUCERS` rows in `guard/producers.py`. I did not run anything. Everything about `textnorm` and the code of P1b is taken from the ticket text and is UNVERIFIED.

Verdict: 1 Blocker, 5 Major, 6 Nit. The Blocker is in P1d-learn's containment filter and is a fail-open for an attacker who controls the text.

## Blocker

**B1. P1d-learn, "Containment filter" (line 12) and the `_learn_unknown` pseudocode (lines 32-34). An attacker can switch learning off for any unknown secret.**
- The filter drops a candidate when its fold contains any value known before the learning pass.
- The attacker needs a known value of at least 8 characters. The same text can plant one: `password=Zz9Yy8Xx7W`.
- Scenario, card or model path. Text: `password=Zz9Yy8Xx7W key AKIA**IOSFODNN7EXAMPLE**Zz9Yy8Xx7W`.
  - Pass one masks both copies of the planted value, so shown is `... AKIA**IOSFODNN7EXAMPLE**<SECRET_1>`.
  - Learning runs on the raw views, not on the dropped form. View d reads `AKIAIOSFODNN7EXAMPLEZz9Yy8Xx7W`.
  - That is one APIKEY candidate (the token pattern runs on through the trailing token characters). It contains the known value, so it is dropped.
  - `_learn_aws` yields nothing, because the right boundary `(?![a-z0-9_-])` fails against the glued tail.
  - `_finish` finds no residue, because the key is not a known value. The card shows `AKIA**IOSFODNN7EXAMPLE**` next to a placeholder.
- The same works for these first-seen secrets:
  - a URLCRED or WEBHOOK whose host is a known HOSTNAME: `https://svc:Pa**ss1234**@<known host>`;
  - a SECRET value followed by a known token;
  - an EMAIL (H28a) whose domain pass one already masked as a known host.
- Ticket Non-Goal N7 accepts "the known part is masked by P1d". That is wrong. The unknown part stays visible.
- The justification in the ticket ("the view only glued text onto a value pass one already masked") is true for GLUE-UP and ACC-EMAIL and false for the above. The filter cannot tell the two cases apart.
- Fix at the choke point:
  - Learn on views of the dropped form, where known values are already spaces. This is the same text as P1d's residue views. A candidate then cannot contain a known value, and the filter is not needed.
  - Neutralise has turned escapes into spaces in the dropped form (RS-1). If that is a problem, run the learning views on `r` with known spans blanked. Either way the filter must go.
  - If the filter stays, drop a candidate only when it still matches nothing after the known part is replaced by a space or delimiter.
- Add these rows with this exact planted-value shape: `AKIA**...**<known>`, URLCRED with a known host, EMAIL with a known host, and GLUE-UP. Add a mutant that restores the filter.
- Also fix the H28a expectation. If `example.org` is masked as a known host in pass one, H28a is not learned today.

## Major

**M1. P1d-learn: generic tokens, credit cards and IBANs are neither covered nor named as not covered.**
- `LEARN_KINDS` removes HIGHENTROPY, CREDITCARD and IBAN.
- Non-Goals N1-N7 and the CHANGELOG "Not covered" sentence do not name them.
- The Owner-facing text speaks of "a password, key or e-mail address". A first-seen HIGHENTROPY, card or IBAN written `ab**cd...` is shown, and the client is told nothing.
- Add N8 and the CHANGELOG sentence. State that known copies of those kinds are still covered by P1d, since they are in `SECRET_KINDS`.
- Add `measure` rows for them. This follows the CLAUDE.md "do not hide gaps" rule and the plain-wording rule.

**M2. P1d-learn has no fail-before method and no base for its guard rows.**
- P1d spells out the worktree, the `leaks()` oracle, the junit counts and `test_fail_before_outcomes`. P1d-learn says only "Legend as P1d".
- The guard rows say "each must give the base output", but no BS-0 step pins them. P1d has BS-0 (l).
- The base is post-P1d, not post-P1d-a. That must be stated, otherwise the fb rows (H11, H12 and others) can pass for the wrong reason: P1d's withhold on a known value.
- Add the procedure, the pinning step and the base SHA rule.
- Also: SUM-1..5, H11-H16c and H21 appear in both P1d and P1d-learn with different inputs. Fix the ids in `p1d_cases.py`, or give the learn ids a suffix.

**M3. Withholding a tool result after the action ran hides the outcome from the model (P1d NOTICE_HANDLING, "tool result", "shown").**
- A write tool, such as a payment, send or ticket action, has already run when `prepare_output` withholds its result.
- The model sees only the notice and cannot tell success from failure. It may retry or report failure.
- The "never ends a run" rule (RK4) makes this worse.
- Add a rule: when a tool has a side effect, the withheld result is a fixed structured outcome that carries status or ok but no content. Alternatively the audit record carries the real status and the notice says "the action ran".
- Add a row and a test with a fake write tool. Also state what idempotency protects against in the retry case.

**M4. Model-path cost grows with the run map, so a long run slowly stops working.**
- The run map holds up to 2,000 values and only grows. The finder is keyed to `frozenset(values)`. It is rebuilt whenever a call adds a value, which is nearly every call.
- The folded finder adds a second trie.
- `max_work` ties scripted values times view length to a limit of 50 million. Beyond it, results are withheld as `size`.
- Result: the later in a run, the more tool results and documents are withheld with `size`. RK2b and DEFAULT 1 cover only the large-text side.
- Add one of these: an incremental or append-only finder, an eviction rule, or a BS-4 row "2,000 values, 30,000 characters, call N of a run" with a gate on the rebuild time. Say what the operator sees when the whole run degrades. Today one log line per text is the only signal.
- The 30,000-character target at 1.5 s against 2.69 s measured in V9 is not yet shown.

**M5. P1d-gate canaries pass on any withhold, including one for the wrong reason.**
- The pass condition is `is_withheld(result)`. A `_finish` that raises (reason `error`) or a size withhold also passes.
- C-KNOWN is meant to prove "residue rule works". C-LEARN and C-AWS prove "learning works".
- A build where `_healing_views` throws only on the canary text would pass. So would a build with a mis-set `max_work` or `max_text_chars`.
- Fix: `_withhold` records its reason in a thread-local that `_startup_canaries` reads. Pass only on `reason == "residue"`. Add a test that patches `_finish` to raise and expects the canary to fail.
- Also, C-KNOWN covers only `**` (view d). Mutants M3, M4 and M6 (views a, b1, c) pass the gate. The ticket says one canary per failure class, so this may be accepted. Then say so in the "why not merged" column, or use one input that needs step a and one that needs b1.

## Major, wording and scope

**M6. Learning's flood limit counts pieces.**
- `find_matches` includes the extra secret-shaped pieces that `_place` adds (`redact.py:958-970`). I read that code.
- One compound secret therefore yields several `added` entries. FLOOD (17 keys) and FLOOD-16 assume one entry per key.
- Define what `max_learned_per_call` counts: values or pieces. Add a row with a compound value.
- Also state the commit effect. A learned piece joins the run map and is swept at every copy if its kind is in `SECRET_KINDS` and its length is at least 4. A false piece then masks later text for the whole run (the false-learn harm the ticket describes).

## Nit

- **N1. Late-failure gap in `app.request_approval`.** If `post_card(withheld_card)` fails, the result is still `Delivery(ok=False, reason="card_withheld")`. The operator log says "withheld", but the posting failure is not logged separately. Add a distinct log field (`posted=false`). This is the only visible signal in that case.
- **N2. `send_card` and `update_card` adapter.** `inspect.signature` with `**kwargs` can forward `withheld=` into a vendor call that rejects it, giving a `TypeError` at run time. Add a test with a `**opts` forwarding channel, or restrict the check to a named parameter.
- **N3. Window between merges.** The client profile is not closed between the P1d merge and the P1d-gate merge. Today's state is also open. Say so in P1d (lead ruling 165 only requires the hard dependency for P1b and PR 63).
- **N4. Unjoined model-path pieces.** The card path has a joined check (`card_joined`). The model path checks each producer's text alone, so a known value split across two texts that the prompt builder later joins is not seen. State it as a Non-Goal.
- **N5. Aggregate counts.** `contains_notice` and `is_withheld` on a JSON tool result with one withheld leaf leave the other leaves screened. This is fine, but add a row that pins the leaf count (the walker is the `has_placeholder` shape).
- **N6. `NOTICE_HANDLING`.** I checked the 16 keys against `PRODUCERS` (`producers.py:14-41`) and they match. The "document and model-written arguments" row bundles two behaviours (document refusal, argument storage) under one key, so the test should assert both. Also check that `eval case document` raises `ConfigError` before `MAX_REDACT_CHARS` is quoted in a message that includes the cap.

## Items checked and sound

- **Residue rule** on views of the dropped form, with the "text returned is the text checked" argument. Placeholder gaps (a space in the dropped form) are conservative for every-copy values.
- **View order a, b1, c, d** with exact skips. A hostile literal placeholder only over-withholds.
- **Split of every-copy and standalone kinds** follows the sweep's own rule.
- **View d_sp** for the AWS rule. GLUE-LC and GLUE-GAP are the right killers for M69.
- **Merge order** P1d-a, P1d, P1d-learn, P1d-gate. P1d-gate needs `_learn_unknown` and `_learn_aws` for C-LEARN and C-AWS, so the order is forced. The BS-2 HELD path blocks the gate, which matches the intent.
- **Four canaries** map to four failure classes. The "dropped" list is argued.
- **Floor check** is the only setting that can weaken protection. Every other setting fails closed.
- **Rung tables** carry a guarantee class and an 80 percent line.
- **Mutant lists**: P1d-learn M43-M45 and M62L have killers and patch points.

Files: /home/user/hadavin-sdk/handover/tickets/P1d.md, /home/user/hadavin-sdk/handover/tickets/P1d-learn.md, /home/user/hadavin-sdk/handover/tickets/P1d-gate.md.