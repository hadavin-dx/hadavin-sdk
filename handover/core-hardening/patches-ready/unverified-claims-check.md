# ORDER 021 lane c: unverified claims check (EVIDENCE RUNNER: runs and records, no judging)  **[SUPERSEDED as the index of the first set; the current index is patches-ready/README.md. Kept as evidence]**
Date 2026-11-16. Clean tree: `git archive b4cce5b` extracted to scratch (same method as patch-test-runs/REPORT.md: archive, no .git, uv env, no cloud variables). No patch applied. Repo not edited. pydantic in that env: 2.14.1 (from uv.lock). Raw output: `raw-unverified/`.

## Failures first
- Nothing failed to run. Not tested (not asked or needs Postgres/n8n/network): all claims about the PATCHED code, the 455 Postgres-skipped tests, the dead-man SQL, the mutation lane, test counts "17 of 19 / 20 of 42", and "27 vs 29 mutants" (see "Could not test").
- Claim refuted: Round-1 reviews (codebase-r1 M1, design-r1 M1) said a NaN price raises `decimal.InvalidOperation` and Infinity passes. On the clean tree both are refused as a normal validation error (see 1).
- Claim confirmed as a real old-code defect: zero price, negative zero and negative prices are all accepted (see 2).

## The one-line check for (1) (run in the clean tree: `uv run --all-extras --group test python -c ...`)
`from hadavin_sdk.config import Route; Route(model_id="m",input_usd_per_mtok="NaN",output_usd_per_mtok="1",max_tokens=10)`
Full script (loops over NaN, Infinity, -Infinity, -0, 0, -1, 1e-12, and the same as `Decimal` objects): `/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/unverified/chk1.py`. Output: `raw-unverified/check1-route-nan.txt`.

## Claim table
| # | Claim | Source | Test command | Raw output | Result |
|---|---|---|---|---|---|
| 1a | pydantic already refuses NaN/Infinity for the price with the current Route model ("plausible, unverified") | design-r2 "Also:" line; v2/README.md:52-55 | `uv run --all-extras --group test python chk1.py` | raw-unverified/check1-route-nan.txt | CONFIRMED. "NaN", "Infinity", "-Infinity" as strings and as Decimal: `ValidationError ... Input should be a finite number [type=finite_number]` (a ValueError subclass, so `load_config` turns it into ConfigError). Checked at Route level only; I did not run `load_config` end to end. |
| 1b | Round-1 claim: NaN raises `decimal.InvalidOperation` at load, Infinity passes | codebase-r1.md:3 (M1); design-r1.md:17 (M1) | same | same | REFUTED on pydantic 2.14.1 with the current `Money` annotation (config.py:47) |
| 2a | Old code accepts price 0 | v2/README.md (premise of C-01) | same | check1 (`'0' ACCEPTED`) and check2 | CONFIRMED. Old `Config._cross_checks` has no price rule (grep: `usd_per_mtok` appears only in config.py:57-58 fields, k1b/loop.py:120-121, llm/common.py:167-168, k1b/replay.py:87). Only `k1b/replay.py:85-90` refuses zero, and only in replay. |
| 2b | Old code accepts negative zero | implied by C-01 "finite and above 0" | same | check1 (`'-0' ACCEPTED -> Decimal('-0')`, also as Decimal) | CONFIRMED. `Decimal('-0') == 0` is True, so replay's zero check would catch it, but nothing at load does. |
| 2c | Old code accepts negative price | README "Negative prices are never allowed" (new rule) | same | check1 (`'-1' ACCEPTED`); check2 | CONFIRMED accepted on old code. With -1 the cost of 1000 in + 1000 out tokens is `Decimal('-0.002')` (negative spend; check2 file). |
| 2d | Zero price makes every cost 0 | k1b/replay.py:89 comment | `chk2.py` | raw-unverified/check2-old-zero-negzero-cost.txt | CONFIRMED for the arithmetic of the formula at llm/common.py:167-168 (price 0 -> cost `Decimal('0')`; -0 -> `Decimal('-0')`). I recomputed the formula by hand in the script; I did not call the real `reply` function and did not test the budget limits in runtime/limits.py. |
| 2e | A tiny positive price 1e-12 is accepted | README:61 | check1 | check1 | CONFIRMED on old code (`Decimal('1E-12')`); the patched behaviour is not tested here. |
| 3a | A failed DELETE after a successful drain write: README says it is "logged and not counted; the next tick absorbs the duplicate" | v2/README.md:75-76; test at A-01.patch:493-516 | `uv run ... python chk3.py` (same setup as the patch test: `ChainAudit(_Db.memory())`, `_append` made to fail so 2 events go to the outbox, then `_db.run` made to raise OSError on `DELETE FROM audit_outbox`) | raw-unverified/check3-delete-failure-old.txt | On OLD code the README's description is NOT how it behaves (the README describes the patch, so this shows what the patch changes): `reconcile()` RAISES the OSError out of the call. The first event was already written to the chain (events=1) and its outbox row stays; the second row was never tried (outbox rows = 2, events = 1). With DELETE working again, a second `reconcile()` returns 2, outbox 0, events 2 (the duplicate is absorbed with no double entry). So "next tick absorbs the duplicate" is CONFIRMED for old code; "logged and not counted" is old-code-false and only applies to the patched code, which I did not run. |
| 3b | A-22: one corrupt outbox row blocks the rows behind it | codebase-r1.md:5 (M3), design-r1 B1 | chk3.py (second half) | check3 file | CONFIRMED on old code: with a bad row sorting first, `reconcile()` raises `ValidationError`; the good event stays undrained (events = 0). |
| 3c | Old chain kind has no `backlog()` / `last_corrupt` | v2/README.md:68-92 (new API) | chk3.py | check3 file | CONFIRMED: `hasattr(log,"backlog")` False, `last_corrupt` False on old code. Consistent with codebase-r2 MAJOR 5 (not on the audit Protocol). |

## Could not test (and why)
- Everything about patched behaviour (A-01/C-01/G5 patches): task limited to old code; the patched numbers (9451 passed, 17 of 19 failing on old, 20 of 42, 27 vs 29 mutants, `raw/mutation-A01.txt` missing) were not re-run. Source: v2/README.md:4,12,113; codebase-r2 nits.
- codebase-r2 BLOCKER 1 (`refused =` overwritten in the non-dev branch of `Config._cross_checks`): needs the patch applied; not tested.
- "Local Ollama needs no key, price 0 legit" (design-r1 B2): requires reading `backends/table.py` and a running local model; not tested.
- Dead-man SQL (`make_interval`, DB vs app clock), privilege claims (audit identity cannot UPDATE/DELETE `audit_entries`): need Postgres; not available.
- "git apply --check passed", the 2 baseline failures, bandit: already covered by patch-test-runs/REPORT.md; not repeated.
- design-r1 M1 claim that cost is computed at k1b/loop.py:117-121 and llm/common.py:166-169, and `min(...)<=0` raising on NaN: formula lines exist as cited (read), the NaN raise is moot because NaN never loads (1a).
