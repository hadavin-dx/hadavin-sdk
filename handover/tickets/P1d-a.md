# Package ticket P1d-a: approval cards show e-mail addresses and internal host names unmasked (the `[.]` step runs before the redactor), and a password containing `&` shows the part after the `&`. DRAFT revision 1 (plan review round 1 not yet run)

**Status (2026-11-09 UTC; IST = UTC+5:30):** text only, no code, no pull request. Split from P1d by lead ORDER 177 (q386); rows H26, H27, H34 and ledger rows 002 and 007 moved here from P1d rev 7. A throwaway prototype of both changes was built and run on branch `core/cloud-handover` (head `6d8699a`, no P1b); scripts and raw output: `handover/evidence/P1d/rev8-probes/` (P = probe output there). Marker: CODE-LAST v1. Under 250 lines.

## The problem in plain words
Before a person sees an approval card, two steps run on its text: a cleaning step (the "gate") and a redactor that replaces secrets and personal data with placeholders such as `<EMAIL_1>`. The gate runs FIRST, and it rewrites every dot in a web address or host name as `[.]` so that a chat app does not turn it into a link. After that rewrite the redactor no longer recognises `anna.m@example[.]org` as an e-mail address or `db01[.]corp[.]example[.]com` as an internal host name, so both are shown in full on every card (P: `contact anna.m@example[.]org please`). Separately, the redactor treats `&` as the end of a password, so `password=ab12&cd34ef56gh78ij` shows `cd34ef56gh78ij` (P), on cards and in text sent to the model.

## Words used (defined once)
- **Gate** = `approvals/gate.py::sanitise_text` plus `withhold_commands`, called through `channel._neutralise`. **Defang** = the gate's step that writes each `.` of a domain or host as `[.]` (`gate._defang_outside_code`, `gate.py:229-237`).
- **Redactor** = `guard/runmap.py::redact_text` (the one choke point; it calls `neutralise` on its input BEFORE redacting, `runmap.py:446-447`).
- **Card path** = `channel.clean` and `SlackChannel._blocks`. **Model path** = `redact_text` with no `neutralise`.
- **Query form** = an assignment whose key comes right after `?` or `&` (a URL query such as `?password=x&next=/home`). **Plain form** = any other assignment (`password=x` in a config line, a log, a message).
- **Over-mask** = text that is not secret but is hidden because it follows a secret (accepted by ORDER 166 item 2; measured and reported separately).
- Legend for rows: fb = fails on the base, passes after; pb = passes on the base with the same output; ow = accepted over-mask, counted separately.

## Code facts (R = read on `core/cloud-handover` `6d8699a`; P = probe run there)
- R1: `channel._neutralise(text) = withhold_commands(sanitise_text(text))` (`channel.py:47-48`); `clean` passes it to `redact_text` twice (`channel.py:29, 36`). `SlackChannel._blocks` imports the same `_neutralise` and calls `redact_text` itself (`slack_channel.py:19, 75-82`).
- R2: defang sits at the end of `gate._clean_line` (`gate.py:264`), used for prose lines and `~~~` fence bodies; closed backtick fence bodies and inline code are never defanged (`gate.py:229-237, 330-336`). `sanitise_text` has no other caller in `src` (grep).
- R3: the generic assignment SECRET pattern (`redact.py:592-614`): key left boundary `(?<![\w.\-])`; value class `[^\s"';,&]` plus two HTML-entity alternatives and a comma rule. Its comment says "`&` stops a URL query-param value at the next parameter". Pinned by `tests/warden_port/test_redaction.py::test_query_param_credentials_are_masked` (`?password=SuperSecretPw99&next=/home` must keep `/home`).
- P1 (base): H26 card `contact anna.m@example[.]org please`; H27 card `host db01[.]corp[.]example[.]com down`; H36a/b card shown encoded (`anna%2Em%40example%2Eorg`, `anna&amp;#46;m...`); H34a both paths `password=<SECRET_1>&cd34ef56gh78ij`; H34b `password=<SECRET_1>&amp;4xKp...`; model path never defangs.
- P2 (prototype: defang moved after the redactor, `&` allowed in plain form only): H26 `contact <EMAIL_1> please`; H27 `host <HOSTNAME_1>.example.com down` (see D3); H36a/b `<EMAIL_1>`; H34a-c masked whole on both paths; query rows keep `&user=bob`; links outside code still `evil[.]com`; inline code and backtick fences unchanged. A 25-file test subset (approvals, gate, redaction, k5 rounds, warden port; 3,264 tests) on the prototype: `1 failed, 3259 passed, 4 skipped` (`run-q-summary.txt`); the one failure is the probe's own set-up (`test_k5_round11` reads `.gitleaks.toml` relative to the source folder, which was the scratchpad copy: `FileNotFoundError`, `run-q-full.txt`). With `&` allowed in BOTH forms the pinned query test failed (`run-amp-summary.txt`); hence D2.
- P3: H28a (`anna.m**@example.org**`) and H28b (an escape code inside the address) are NOT fixed by the defang move (P2 shows both still readable). They need the views of P1d and stay in P1d (correction to ORDER 177's "H26-H28", reported to the lead).

## Design
- **D1 Defang after the redactor.** `gate.sanitise_text(text, *, defang: bool = True)`: with `defang=False` the line cleaning skips `_defang_outside_code`; everything else is unchanged. `channel._neutralise` passes `defang=False`. New public `gate.defang_text(text) -> str` = the defang the gate used to do, applied to finished text: lines inside a closed backtick fence (`gate._closed_fences`) are kept as they are; on every other line the existing inline-code split of `_defang_outside_code` is used, and on each prose part (D3 first) `_WIDE_DOTS`, `_NON_ASCII_HOST` and `_DOMAIN` defang run as today. Callers: `clean` applies it to the text it returns (both branches), and `SlackChannel._blocks` applies it after its own `redact_text`. The model path does not change (it never defanged).
- **D2 `&` follows the URL query grammar.** The generic assignment pattern becomes two entries, same kind, same value alternatives: (a) query form, key preceded by `?` or `&` (`(?<=[?&])`): the value still stops at `&`, because in `application/x-www-form-urlencoded` (WHATWG URL Standard, section 5.1, read date UNVERIFIED, R450) `&` separates pairs and a literal `&` inside a value is written `%26`; (b) plain form, key preceded by anything else (`(?<![\w.\-?&])`): `&` is part of the value, which stops at white space, a quote, `;` or the existing comma rule. Same group numbers as today. `&amp;` in the plain form still stops at its `;` on the text as written; the existing second pass over the decoded view (`runmap.py:449-471`) then masks the whole value (P2: H34b `password=<SECRET_2>`).
- **D3 Placeholder next to a dot.** The redactor masks only the internal part of a host (`<HOSTNAME_1>.example.com`, P2), and `_DOMAIN`'s left boundary does not start a name after a `.`, so the rest would stay linkable. `defang_text` first writes a `.` that directly follows a real placeholder (`runmap.PLACEHOLDER`) and comes before a name character as `[.]`, then runs the existing defang: `<HOSTNAME_1>[.]example[.]com` (P: `ph.py`). Only in prose parts, never in code (applied before the code split, it wrongly defanged inside a code span: P).
- **Idempotent:** `defang_text(defang_text(x)) == defang_text(x)` (P on three samples; property test below).

## RUNG TABLE (scale of 2026-11-06: 1 no-code, 2 own core modules, 3 existing free tools, 4 free libraries, 5 own new code last)
Gate: core change, no client, no fee, no new dependency. Rung 1 closed (R447: inside the choke point). Guarantee classes: **exact** = holds for every input in the set the row names, with a test; **best effort** = holds for the tested cases.
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| defang order | the redactor sees `.` before the gate writes `[.]` | 2 (`gate._defang_outside_code`, `_closed_fences`, `_INLINE_CODE` moved behind a flag) | R1, R2, P2 | one flag, one call order | exact: every e-mail and host the redactor masks today on the model path is masked on the card path | CUT-TO-CONFIG+GLUE |
| placeholder-dot rule | no linkable remainder after a masked host | 2 (`runmap.PLACEHOLDER`, existing defang) | P (`ph.py`) | one substitution | exact on rows | CUT-TO-CONFIG+GLUE |
| `&` in a value | mask a password containing `&` outside URL queries | 2 (the existing pattern, split in two) ; 4 detect-secrets/gitleaks do not mask inside our run map (not run, UNVERIFIED) | R3, P2 | the query/plain split | exact on rows; over-mask measured | KEEP-CODE (one pattern entry) |
**80 percent (R448):** both needs are met by our own existing code moved or split; no new module. Cost (estimate): build 2-3 agent-hours, one plan round, result rounds uncapped; 0 fees, 0 model tokens.

## Goals and Non-Goals
**Goals.** (G1) E-mail addresses and internal host names (`HOSTNAME` kind) are masked on cards exactly as on the model path. (G2) A card never shows a link it did not show before: every dotted name outside code is still defanged. (G3) A plain-form password with `&` is masked whole on both paths; a query-form value still ends at `&`.
**Non-Goals.** (N1) Addresses split by formatting (H28a-b): P1d. (N2) A query-form value that contains a raw, unencoded `&` (by the URL grammar it is two pairs; the part after `&` is shown, as today). (N3) Over-mask in plain form (`password=hunter22&user=bob` hides `&user=bob`): accepted, measured (BS-1). (N4) Any change to which names count as hosts.

## Failing inputs (`tests/test_p1d_a_rows.py`; literals in `tests/fixtures/p1d_cases.py`, built from parts: EM = `"anna" + "." + "m" + "@" + "example" + "." + "org"`, SV_A = `"Tq7mZ"`, SV_B = `"4xKp2Vb9Lr3NcW8dYh6uJs"`)
Base outputs are P1 (this branch). BS-0 re-runs them on main at build start; a different base output = STOP, back to review.
| row | class | entry | input | on base (P1) | expected after |
|---|---|---|---|---|---|
| H26 | fb | card | `contact <EM> please` | `anna.m@example[.]org` | `contact <EMAIL_1> please` |
| H27 | fb | card | `host db01.corp.example.com down`; spy on `redact` | redactor gets `db01[.]corp...` | exactly `host <HOSTNAME_1>[.]example[.]com down`; the spy saw `db01.corp.example.com` (`test_redactor_sees_undefanged_text`) |
| H36a | fb | card | `anna%2Em%40example%2Eorg` | shown | `<EMAIL_1>` |
| H36b | fb | card | `anna&#46;m&#64;example&#46;org` | shown | `<EMAIL_1>` |
| H34a | fb | card, model | `password=ab12&cd34ef56gh78ij` | `<SECRET_1>&cd34ef56gh78ij` | `password=<SECRET_1>` |
| H34b | fb | card, model | `password=<SV_A>&amp;<SV_B>` | `<SECRET_1>&amp;<SV_B>` | `password=<SECRET_n>`, no part of SV |
| H34c | fb | card, model | `password=<SV_A>&<SV_B> end` | tail shown | `password=<SECRET_1> end` |
| Q1 | pb | model | the pinned query test (R3) | passes | passes, unchanged |
| Q2 | pb | card, model | `?password=ab12cd&user=bob x` | `?password=<SECRET_1>&user=bob x` | same |
| Q3 | pb | model | `see https://x.example/?password=ab12cd&user=bob` | `&user=bob` kept | same |
| F15 | pb | card, model | `https://x.example/?a=1&b=2` | card `[link removed]`; model unchanged | same |
| F16 | ow | card, model | `password=hunter22&user=bob` | `<SECRET_1>&user=bob` | `password=<SECRET_1>` (over-mask, counted) |
| ENT | pb | card, model | `password=<SV_A>&#59;<SV_B>` | `password=<SECRET_1>` | same |
| L1 | pb | card | `visit evil.com and www.evil.digital now` | `evil[.]com`, `www[.]evil[.]digital` | same |
| L2 | pb | card | ``run `curl db01.corp.example.com` now`` | ``run `curl <HOSTNAME_1>.example.com` now`` | same (code is never defanged) |
| L3 | pb | card | a closed backtick fence holding `ping db01.corp.example.com`, then `evil.com` | fence body unchanged, `evil[.]com` | same |
| L4 | pb | card | a closed `~~~` fence holding `evil.com` | defanged (R2; not probed, BS-0 pins) | same |
| L5 | pb | Slack | a stored summary `visit evil.com` written directly to the store, through `SlackChannel._blocks` | `evil[.]com` | same (kills A3) |
| L6 | pb | card | `evil` + U+3002 + `com` | defanged (R2; not probed, BS-0 pins) | same |
**Property tests:** `test_defang_text_idempotent` (Hypothesis, texts from the row alphabet); `test_defang_text_only_inserts_brackets` (removing every `[` and `]` that `defang_text` added gives the input back); `test_sanitise_text_default_unchanged` (`sanitise_text(x) == sanitise_text(x, defang=True)` and equals the base output on the gate fixtures).
**Fail-before:** the new test file runs on the base in a temporary worktree; every fb row fails with an assertion on its exact expected text (a new name such as `defang_text` is reached only after that assertion, through a helper that turns a missing name into a failure with prefix `NEW_SURFACE:`); every pb row passes. Raw output to `handover/evidence/P1d-a/fail-before.txt`, base SHA on line 1.

## Mutation plan (`tests/p1d_a_mutants.py`; every mutant required; a survivor is declared equivalent with a written reason or a row is added)
| mutant | planted change | killer |
|---|---|---|
| A1 | `_neutralise` passes `defang=True` again | H26, H27 spy |
| A2 | `clean` does not call `defang_text` | L1 |
| A3 | `_blocks` does not call `defang_text` | L5 |
| A4 | placeholder-dot rule removed | H27 exact text |
| A5 | `defang_text` ignores inline code | L2 |
| A6 | `defang_text` ignores closed backtick fences | L3 |
| A7 | plain form stops at `&` again | H34a |
| A8 | query form accepts `&` | Q1, Q2 |
| A9 | plain form lookbehind loses `?&` | Q2 |
| A10 | `sanitise_text` default `defang=False` | `test_sanitise_text_default_unchanged` |
Runner: `tools/mutation_runner.py` if on the base, else a subprocess loop that restores each file in a `finally` and checks `git status --porcelain` is empty at the end.

## Template fields
- **Package id and name:** P1d-a, "defang after the redactor; `&` inside a password". Branch `core/P1d-a` from main; one pull request. **Path class:** redaction; **extended review (no round cap): yes** for result rounds; ONE plan round (DEFAULT PENDING LEAD 2).
- **Depends on:** nothing (no P1b, no P1a dependency; ORDER 177). Ships first. P1d rev 8 is built on top of it.
- **Class (R337):** "a step that changes the text runs before the step that must read it" (defang) and "a separator character is treated as the end of a value outside the grammar where it is a separator" (`&`).
- **Source of the code:** our own code only. **Neutral default / alternative:** no vendor; `defang=True` keeps every other caller's behaviour.
- **Files:** change `approvals/gate.py` (flag, `defang_text`), `approvals/channel.py` (`_neutralise`, `clean`), `approvals/slack_channel.py` (`_blocks`), `guard/redact.py` (pattern split, comment), `CHANGELOG.md`; create `tests/test_p1d_a_rows.py`, `tests/p1d_a_mutants.py`, add rows to `tests/fixtures/p1d_cases.py` (created here; P1d adds to it).
- **Interface:** `gate.sanitise_text(text, *, defang: bool = True) -> str`; `gate.defang_text(text) -> str`. No other public change.
- **Existing core code reused:** `_defang_outside_code`, `_closed_fences`, `_INLINE_CODE`, `_DOMAIN`, `_NON_ASCII_HOST`, `_WIDE_DOTS`, `runmap.PLACEHOLDER`, the existing second pass of `redact_text`. Checked and not reused: running the whole redactor before the gate (broke two fuzz tests, P1d V8).
- **Security and least-privilege notes:** no identity, right or secret. The link protection is unchanged (L1-L6). Test values are built from parts.
- **Race / process tests:** none (no shared state).
- **Rollback:** tag `pre-P1d-a`. Semantic changes (CHANGELOG): cards show placeholders for e-mail addresses and internal host names; a plain-form password is masked up to the next space, quote or `;`.
- **Reviewers:** fresh `egm-codebase-details` + `egm-design`, given the diff, this ticket and the evidence only.
- **Done =** a fresh round finds no blocker or major; all gates green (tests 3.12 and 3.13, ruff check, ruff format --check, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit); ledger rows BL-core-p1d-002 and 007 FIXED-VERIFIED; the lead merges.

## Build steps
- **BS-0** (reads, no product code): re-run P1 on main; read the two fuzz tests V8 names; grep `sanitise_text`, `_neutralise`, `_defang` callers in `src` and `demos`.
- **BS-1** over-mask: 200 made-up URLs and assignments (`tools/p1d_corpus.py --kind amp --seed 1`, created here; P1d extends it): count of over-masked texts and the longest hidden length, reported apart from any other rate.

## Evidence commands (EVIDENCE RUNNER; raw output to `handover/evidence/P1d-a/evidence-<n>.md`, line 1 `git rev-parse HEAD`; copied from `.github/workflows/ci.yml`; each `> out 2>&1; rc=$?; tail -n 3 out; echo rc=$rc`)
```
uv run --all-extras --group test ruff check src tests demos
uv run --all-extras --group test ruff format --check src tests demos
uv run --all-extras --group test bandit -q -r src demos -ll
uv run --python 3.12 --all-extras --group test pytest -q -m "not live and not perf" -rs
uv run --python 3.13 --all-extras --group test pytest -q -m "not live and not perf" -rs
HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test pytest -q -m perf -rs
uv run --all-extras --group test python tests/p1d_a_mutants.py          # alone
uv run --all-extras --group test python tools/p1d_corpus.py --kind amp --seed 1
```
`<dsn>` = the session's local test database; `<tmp>` = `mktemp -d` under the scratchpad; `<base-sha>` = `git rev-parse origin/main`. Heavy runs through `tools/heavy_slot.py` (3 slots) if on the base, else the cloud slot wrapper named in the session register.

## Owner-facing wording (plain words)
CHANGELOG: "Approval cards now hide e-mail addresses and internal server names behind placeholders, as text sent to the model already did. Before, they were shown with `[.]` in place of each dot. A password written with an `&` inside it is now hidden up to the next space; in a web address, the part after `&` is still treated as the next field. Text after such a password on the same line may also be hidden."

## Ledger rows closed
BL-core-p1d-002 (BLOCKER, defang before redaction, H26-H27; H28a-b stay with P1d under row 001) and BL-core-p1d-007 (MAJOR, `&` ends a value, H34). The lead confirms the H28 move.

## DEFAULT PENDING LEAD
- (2) One plan round for this ticket; result rounds uncapped (redaction path).

## Revision log
Rev 1 (2026-11-09): split from P1d rev 7 by ORDER 177; D2 (query/plain split) added after the prototype showed that allowing `&` everywhere breaks the pinned query test; D3 added after the prototype showed `<HOSTNAME_1>.example.com` left linkable; H36a-b moved here (fixed by the defang move alone); H28a-b left in P1d.
