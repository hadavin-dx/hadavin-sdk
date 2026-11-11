<!-- full hand-back report of sub-agent a470bfd9, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

## Verdict

**Correct.** `Code.config_invalid` is the best fit in the closed list by the table's own conventions, though it is a nearest fit and not an exact one. No blocker and no major finding; one nit.

All paths below are under `/home/user/build/snap/p85main-3b9617e/`.

## Who supplies the run id

A caller of the public API supplies it, not configuration and not directly untrusted input.

- `agent_loop.py:102-103`: the class docstring reads "A caller-chosen run id is not `run-` and 32 lower-case hex characters."
- `agent_loop.py:361`: it arrives as the keyword-only argument `run_id: str | None = None` on the run-start method.
- `agent_loop.py:363-365`: the docstring says a caller passes the same id each time it handles a message, so one message starts at most one run.
- `agent_loop.py:380`: the only raise site is through `_checked_run_id(run_id)`, after the `Unqualified` check and before any write.
- `agent_loop.py:799, 806`: `on_decided` and `execute` take a `run_id` but do not call `_checked_run_id`, so they never raise this class.

The caller may derive the id from an external message, but the integrating code chooses the value.

## Why `config_invalid` and not the other candidates

- **`unqualified` is wrong.** `agent_loop.py:98-99` defines it as "The agent has no green gate run for its current model, prompt and config". That is a gate state of the agent, unrelated to a malformed argument. It is raised separately at `agent_loop.py:378`, and `codes.py:249` is its only row.
- **`validation_failed` is wrong by the table's own gloss.** `codes.py:232-233` defines it as "(a pydantic model)", and `codes.py:185-215` ties that code's `type` fact to pydantic error type names. `InvalidRunId` is a hand-written regex check with no pydantic error, and no own class in `OWN_CODES` maps to `validation_failed`.
- **`internal_bug` is wrong.** `codes.py:230-234` reserves it for a defect in the package's own data; here the package is behaving correctly and the input is bad.
- **`config_invalid` fits best.** `codes.py:232` glosses it as "(operator input)". Its existing members are all bad input supplied from outside the package: `ConfigError` (`codes.py:227`), `_RenamedStage` (`codes.py:228`), `BundleError` (`codes.py:229`) and `UnknownRecording` (`codes.py:235`).

The stretch is that "operator input" reads most naturally as configuration files, and this is an argument from integrating code. No listed sibling is a pure bad-API-argument exception, so there is no exact precedent.

## Other checks

- **Key format is right.** `codes.py:250` is `_P + "runtime.agent_loop:InvalidRunId"`, matching the `"module:Qualname"` rule at `codes.py:224`. The class is module-level (`agent_loop.py:102`) in the same module as the sibling `Unqualified` row (`codes.py:249`).
- **The row is needed.** `codes.py:224` says an unlisted subclass takes its nearest listed base; `InvalidRunId(ValueError)` has no listed own base.
- **The pinned test table is consistent.** `DIFF-fix.patch:21` adds `"hadavin_sdk.runtime.agent_loop:InvalidRunId": "config_invalid"` at the same position, after `Unqualified`, with the same full key and value as `codes.py:250`. No `Code` member was added, so the "21 members" note (`codes.py:18`) and `RESERVED_FOR` are untouched.
- **The exception message does not leak the value.** `agent_loop.py:108` raises with the constant string `"run_id must be 'run-' and 32 lower-case hex characters"`. By contrast, `Unqualified(agent_id)` at `agent_loop.py:378` does carry the caller's value.

## Nit

- **Severity:** Nit.
- **Affected scope:** `codes.py:250`.
- **Discrepancy:** the row has no comment, although the builder called it a judgement call. The only other nearest-fit row, `SqlReadError` at `codes.py:230-234`, documents why the alternatives were rejected. A one-line comment here would match that convention, for example: caller-chosen argument; not a pydantic model, so not `validation_failed`; not a gate state, so not `unqualified`.

## Not checked

- **`guard/diagnostic.py`:** out of the permitted scope. I did not confirm how a `config_invalid` diagnostic is rendered, whether `str(exc)` is ever printed, or which `Where` step it gets. The no-leak finding covers only the exception's own message.
- **The rest of `tests/test_diagnostic_codes.py`:** I saw only the diff hunk. A pinned row count or a per-code membership assertion elsewhere in the file would not be visible to me.
- **Test and guard results:** nothing was run.
- **Other raise sites:** I searched only `agent_loop.py`, not the rest of the package.
- **Design document D4:** I did not read its definitions of the codes; the meanings above come only from the comments in `codes.py`.
- **Module path:** the snapshot file is assumed to be `src/hadavin_sdk/runtime/agent_loop.py`; this is inferred from the sibling `Unqualified` row, not from a path in the snapshot.
