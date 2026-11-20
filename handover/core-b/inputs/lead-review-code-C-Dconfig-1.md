# review-code-C-Dconfig-1 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

# Early result review: cloud/core-b, ticket C (price constraint) and D-config (trigger settings)

**Verdict: ticket C holds on all six invariants. D-config matches the request by name and bound, but it has no tests at all and three secret-handling gaps (2 Major, 1 Minor-to-Major). No Blocker.** Read-only review; nothing was run, so every "HELD" is from reading the code, not from a test result.

## What I read
All under `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\cloud-core-b` unless noted:
- `src\hadavin_sdk\config.py` (655 lines), `registry.py` (400), `app.py` (532), `defaults.py` (147), all in full
- `tests\test_price_constraint.py` (491, full); `tests\test_k3_pilot_env.py` lines 30-91
- `src\hadavin_sdk\backends\platform_secrets.py` (64), `identity.py` (16), `stages.py` (24), `actions\secrets.py` (18)
- `handover\core-b\tickets\C-price-constraint.md`, `handover\core-b\inputs\request-from-core-a-001-config-triggers.md`, `handover\core-b\requests\001.answer.md`, `CHANGELOG.md` lines 20-39
- `C:\Users\rakes\Downloads\Hadavin\egm\core-complete-2026-11-20\tickets\draft-C-D.md`
- Baseline `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\sdk-main`: one grep only, confirming main has no `prices_as_of`, `_price`, `Trigger*` or `MAX_ROUTE_PRICE`. No line-by-line diff.

There is no D-config ticket: `handover\core-b\tickets\` holds only A, B, C and F. The only D-config spec is the request plus its answer.

## Ticket C invariants

| # | Invariant | Status | Where |
|---|---|---|---|
| 1 | No negative, minus-zero, non-finite, over-ceiling or over-6-decimal price loads, any stage or kind | HELD | `config.py:81-95` (`Route._price`), float refused at `config.py:60-64` |
| 2 | Zero only for fake AND demo | HELD | `config.py:541` (`if live or cfg.backends.llm.kind != "fake"`) |
| 3 | Every route, both fields, including judge and unused routes | HELD | `config.py:544-546` iterates all of `cfg.routes`; the validator is on `Route` itself |
| 4 | Refusal names route and field, never the value; joins the refused list | HELD | `config.py:543`, `config.py:506`, `config.py:72` (`hide_input_in_errors`) |
| 5 | `prices_as_of` required in pilot and prod, plain ISO date, not in the future, old date accepted | HELD | `config.py:448`, `454-461`, `548-553` |
| 6 | `config_hash` unchanged | HELD by reading | `registry.py:106-173` |

Points you asked me to check:
- **Negative, zero, NaN, Infinity.** `-1`, `-0` and `-0.00` are refused by `is_signed()` at `config.py:89`. NaN and Infinity are refused by pydantic first, with `is_finite()` at `config.py:87` as a second line. The ceiling check runs before `quantize`, so a huge exponent cannot make it raise.
- **Fake-in-demo exception in pilot or prod.** Not reachable through config load.
  - `live` is `environment != "demo"` (`stages.py:15`), so any non-demo value takes the strict branch.
  - `environment` is a `Literal` of the three stages (`config.py:410`).
  - The kind test is the literal `"fake"`, not the demo-only table, so a demo-only kind added later gets no exception.
  - `app.build` always goes through `load_config` (`app.py:114`).
  - Paths that skip validation: `model_copy` and `model_construct`, and the replay `llm_kind` override. The ticket leaves these to `k1b\replay.py:85-90`, which I did not open on this branch.
  - Stated out of scope by the ticket: fake kind in demo with a real model passed as `build(llm=...)` and zero prices.
- **Value never shown.** The ceiling message prints the constant, not the input. The zero and date messages are fixed text. The date validator's own text carries no value.
- **`prices_as_of` and the hash.** It is on `Config` (`config.py:448`). `config_hash` reads the agent, the route dump, the contracts, the llm kind and six llm settings, the judges, `tool_module_hashes`, the tools and `eval_threshold`. It reads neither `prices_as_of` nor `triggers`, and `Route` gained a validator but no field.
- **Future date.** Refused at `config.py:552` in every stage, demo included; today itself loads.
- **Fixtures.** One edit, `tests\test_k3_pilot_env.py:44`. `prod_cfg` in `tests\test_client_profile.py:45` inherits it through `pilot_cfg(env="prod")`. My grep of `tests\` for other pilot or prod configs found only `test_p3b_neutral_audit.py:252`, which the ticket says expects a refusal by substring (I did not open it). I found no missed fixture, and no YAML or doc outside `handover\` with `environment: pilot` or `prod`.
- **Changelog.** The upgrade step is at `CHANGELOG.md:25-35`. The session ticket said the changelog comes only with step F, so this is a deviation, but a good one because the change breaks existing pilot and prod configs.

## Trigger config against the request

- **Field names.** Exactly as asked, at `config.py:349-372` and `451`. The written answer records two differences: `secret_names` is a tuple, and a sender secret name shared with a backend or executor secret refuses the start.
- **Tenant and sender ids.** Pattern `^[a-z0-9-]{1,40}$` on both (`config.py:344-345`, `362-363`), at least one sender. HELD.
- **Secret names.** One or two, each non-empty (`config.py:353`); distinct within and across senders (`config.py:375-389`), joined to the refused list at `config.py:507`. HELD, with the gaps in findings 2 to 4.
- **Bounds.** HELD at `config.py:364-372`, all from `defaults.py:137-146`.
  - `max_body_bytes`: above 0, at most 524288.
  - `max_running`: 1 to 64.
  - `ack_wait_s`: above 0, at most 30; NaN and Infinity fail the comparisons.
- **Host rule.** NOT IMPLEMENTED in these four files. `TriggerSettings` has no host or port field, and the request did not ask for one. The draft puts `--host 127.0.0.1` on the worker's `main`, which is core-a's file. If you meant a config-level loopback rule, it does not exist.
- **Secrets through the secrets kind.** HELD. Config holds names only; values come from `app.secrets.get(name)` (`app.py:58`, `304`). The names are added to the start-up read check at `app.py:171-176`.
- **Worker start checks reachable.** HELD. `app.runtime.agents` exists (`runtime\agent_loop.py:210`), and `app.registry.principals` carries `kind`. The registry already refuses a missing agent, a missing principal and a non-service principal (`registry.py:340-353`, called at `registry.py:227`). The check "agent is in `runtime.agents`" is left to the worker, as the answer says.
- **Nothing trigger-related in `config_hash`.** HELD by reading.

## Findings

1. **Major: D-config has no tests.** A grep of `tests\` for `triggers` and `TriggerSe` finds nothing relevant. Untested: the pattern, the 0-or-3 names case, both duplicate rules, the three bounds, the three registry refusals, the `extra_secret_names` union, `App.secrets`, and hash equality with and without the block (the answer says "measured", but nothing pins it). core-a offered a contract test for the config block only; nobody owns the registry and app parts. Fix: a `tests\test_trigger_config.py` by a non-builder covering those, plus a hash-equality assertion.

2. **Major: a sender secret name may equal a tool secret, a source token or the restored-hash key.** `app.py:161-177` unions the sender names into the same set as those, and `platform_secrets.py:47-57` only checks that set against backend and executor names. The comment at `app.py:171` promises less than the ticket's intent: the n8n-held signing secret could be the cluster bearer token. Fix: in `build`, refuse any overlap between sender names and the rest of `extra_secret_names`, naming the sender and not the secret.

3. **Major: `App.secrets` is the whole provider.** `app.py:56-58` relies on a comment ("nothing else may take the provider from here"). The request asked that the worker read only the listed names, and tools already get a bound reader (`_own_secrets`, `app.py:314-323`). Fix: expose a reader limited to the sender names, for example a `trigger_secret: Callable[[str], str]` field. The name `secrets` is already promised to core-a, so this needs a DRAFT 2 answer.

4. **Minor, arguably Major: a secret pasted into `secret_names` is echoed at start-up.** `config.py:376-377` says a mistyped config may hold the secret itself there, and names only the sender. But `platform_secrets.py:49` prints `sorted(shared)` and `platform_secrets.py:63` prints `secret {name!r} cannot be read`. That text is older and applies to every secret name, but sender names now flow into it. The line-49 message also says "a read tool ... give the tool its own secret", which is wrong for a sender. Fix: check sender names in a separate step with sender-only messages.

5. **Minor: names are only "non-empty".** `config.py:346` lets `" "` or a name with a newline through for `secret_names`, `agent_id` and `principal_id`. Fix: a charset pattern, or `strip_whitespace` with a minimum length.

6. **Minor: the registry accepts a draft or retired agent for a sender.** `registry.py:346` checks existence only. The worker's `runtime.agents` check may cover it; ticket D should say which side owns it.

7. **Minor: the default body cap equals the document cap.** `TRIGGER_MAX_BODY_BYTES` and `MAX_DOCUMENT_BYTES` are both 262144, so a full-size document cannot fit once wrapped and escaped in JSON. Nothing cross-checks `triggers.max_body_bytes` against `evidence.max_document_bytes` either. This is the ticket's choice; flag it to the lead.

8. **Minor: booleans pass as numbers.** I believe pydantic's lax mode turns `max_running: true` into 1 and `ack_wait_s: true` into 1.0; not verified. Fix: strict types on those fields, or a test that pins the behaviour.

9. **Minor: no changelog line for `triggers` or the new required `App.secrets` field.** `App(` is constructed only at `app.py:295`, so nothing breaks in the repo.

## Tests that cannot fail, or are weak (`tests\test_price_constraint.py`)
- **Lines 237-241, `test_today_is_the_utc_date`.** It passes for `date.today()` on any machine whose local date equals the UTC date, so it does not prove UTC. Fix: patch `datetime` in the config module to an instant where the two dates differ.
- **Lines 384-392, first half.** The `try/except` accepts either a load or a refusal for fake in demo; only the last line (real kind refused) can fail.
- **Lines 324-330.** Rows with `why = ""` make `assert why in text` empty; only the route and field assertion bites. Acceptable.
- **Lines 276-284.** The message assertion is conditional. Shaped-but-invalid dates such as `2026-02-30` only assert that `prices_as_of` appears somewhere. Acceptable.
- **Lines 26, 475-476.** `FIXTURE_HASH` is claimed equal to main's value. I could not verify that without running main; it is the only thing pinning invariant 6 across the change rather than within it.
- **H5 (lines 171-175).** It tests `_price_refusals` directly. The ticket's H5 (replay refuses a `model_copy` zero) rests on the existing `tests\test_k1b_replay.py`, which I did not open.

## Hard-coded values that belong in defaults
- `config.py:93-94`: the 6-decimal quantum `Decimal("1E-6")` and its message text. It is taken verbatim from P4a, so moving it costs merge identity.
- `config.py:344`: the trigger id pattern is fine in config, but the endpoint's key rule and the 32-character secret minimum, when core-a builds them, should sit in `defaults.py` beside `TRIGGER_*`.
- Existing, not new: `HELD_MAPS_CEILING` (`config.py:219`) and `MIN_RESTORED_KEY_BYTES` (`app.py:447`).

## Listed in the tickets but not built here
- All trigger-config tests (finding 1).
- Secret value checks (non-empty, at least 32 characters, distinct across senders) and the agent-in-`runtime.agents` check: left to the worker, as the answer states.
- The `guard\producers.py` row or module-list pin for `hadavin_sdk.triggers`: deferred until a guard test fails.
- A host rule in config (see above).
- Ticket C: nothing missing. The draft's `Field(ge=0)` was replaced by `_price` on purpose because `ge=0` lets `-0` through. The ceiling and 6-decimal rules are extra to the draft, so `1E-30` is now refused, contrary to the draft's open-question answer; this is recorded in session ticket C, open question 1.

## Not checked
- No test, ruff or mutant run.
- No line-by-line diff against sdk-main.
- `k1b\replay.py`, `tests\test_k1b_replay.py`, `tests\test_client_profile.py`, `tests\conftest.py`, `tests\stage_mutants.py` (ticket C says it pins exact text of config lines), `deferred.py` beyond a grep, `tests\test_p3b_neutral_audit.py` and the other substring-matching pilot and prod tests.
- Whether any test pins the fields of `App` or `Config.__all__`.
- pydantic 2.14.1 behaviour for NaN, the `$` anchor in patterns, and bool-to-int coercion: taken from the ticket's "Checked" notes or my own recollection.
- Any commit that landed after my reads.
