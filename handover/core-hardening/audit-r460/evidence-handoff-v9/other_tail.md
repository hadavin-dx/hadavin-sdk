
## O-5 Dependency and least-privilege check for these tracks

- **Fileguard (K1):** standard library only; adds no identity. Over-breadth review line: none, it only narrows what a key file may be (a symlinked or group-readable signer key is refused).
- **Audit claims (A1) and retention floor (H-1):** no new role. H-1's S3 probe reads the bucket's object-lock configuration, so it needs one read action on that bucket for the anchor-writing identity; the exact action name is **UNVERIFIED** (vendor documentation not read; needs a third party) and the PR ships the policy text, the per-action reason, a negative test (the identity cannot delete) and an over-breadth line before review. Single dependency: the probe sits in `anchor_s3.py` (the S3 kind); GCS and Azure already have theirs.
- **Extract masking (PR-2), redaction (R), approval text (G-W, G):** no identities, no vendor imports; masking happens before any model sees text.
- **Over-breadth line for every new role:** none of these PRs adds a role.

## O-6 PR series (non-spend), one status column

Cap tag: U = uncapped (security, redaction, audit, secret), C = capped at 2 rounds. Every PR: needed-check verdict not supplied.

| Order | PR | Content | Cap | Depends on | Status |
|---|---|---|---|---|---|
| 1 | PR-2 | `extract()` masking, `redact_untrusted`, private mapping holder and `Valid.restore`, schema guard, re-keyed recordings (O-4.7) | U | none | specified, unverified |
| 2 | R | Redaction patterns that leak on old code (O-4.10) | U | E0-O4 | specified, unverified |
| 3 | K1 | `fileguard`, signer key check (O-4.8) | U | none | specified, unverified |
| 4 | A1 | Audit claims (O-4.6) | U | none | specified, unverified |
| 5 | G-W | G1 wording only | C | none | specified, unverified |
| 6 | G | G2a, G2b, G3, G4a, G5a rows that leak on old code (O-4.9) | U | G-W, E0-O6 | specified, unverified |
| 7 | H-0 | stage rename (O-4.11) | C | none | specified, unverified |
| 8 | H-1 | retention floor and S3 probe (O-4.11) | U | none | specified, unverified |
| 9 | H-2 | evidence docs (O-4.11) | C | none | specified, unverified |

All nine start together; G after G-W; R after E0-O4. Merge order is free except those two. One full suite per PR at its final head; heavy jobs through the slot rule (`faster-builds` rule 2) not more than 3 at once.

## O-7 Evidence batch (an EVIDENCE RUNNER runs these; the runner never judges)

Output folder: `handover/core-hardening/audit-r460/evidence-handoff-v9/` (the runner writes). No item depends on a later PR. "Author PR" is the PR whose builder writes the missing test or script. The repository has no `scripts/` folder and no mutation tool (v8 fact).

| Id | Command | Output file | Pass rule | Author PR |
|---|---|---|---|---|
| E0-O1 | `uv run --all-extras --group test ruff check > E0-O1-ruff.txt 2>&1; echo rc=$? >> E0-O1-ruff.txt`; same pattern for `ruff format --check`; `uv run --all-extras --group test pytest > E0-O1-pytest.txt 2>&1; echo rc=$? >> E0-O1-pytest.txt`; `bandit -q -r src demos -ll > E0-O1-bandit.txt 2>&1; echo rc=$? >> E0-O1-bandit.txt` (the command of `ci.yml:119`). Plus for K1: `uv run --all-extras --group test pytest tests/test_p4_secrets.py tests/test_lockin_guard.py -q` (mounted-file tests unchanged) | `E0-O1-*.txt` | all four rc=0 at each PR's final head | exists |
| E0-O4 | `uv run --all-extras --group test pytest tests/test_redaction_canaries.py -q > E0-O4.txt 2>&1`: one canary per pattern of O-4.10 run on the OLD tree (`git stash`-free: run against a checkout of the pre-R commit) and the new tree; masked text is a fixed point; fuzz `redact_text` 500 inputs | `E0-O4.txt`, `E0-O4-failing-on-old.txt` | a pattern ships only if its canary fails on old code | R |
| E0-O6 | `uv run --all-extras --group test pytest tests/test_g4_rows.py -q > E0-O6.txt 2>&1`: every row of O-4.9 and every pinned shown line through `withhold_commands` and `channel.clean`, old tree and new tree; false-positive rate on 200 made-up prose sentences. **The 200 sentences and the corpus do not exist; G's builder writes made-up ones or the lead supplies input.** | `E0-O6.txt` | each shipped row leaks on old code; no pinned line changes; false positives at most 2 percent | G |
| E0-O9 | extract report: with the fake kind, `uv run --all-extras --group test pytest tests/test_extract_masking.py -q > E0-O9.txt 2>&1`: every leak test of O-4.7 (canary from parts), the forged placeholder test, the schema-guard test; dead-letter rate by reason on the golden set **which does not exist; the lead supplies or approves it**; never write "N/M correct" without the answerable-abstained split (`.claude/rules/false-abstain-reporting.md`) | `E0-O9.txt` | all pass; each new test fails on old code | PR-2 |
| E0-O10 | masking damage: `python evidence-handoff-v9/masking_damage.py` (written by PR-2; about 30 made-up invoices, no model, no spend) counts per schema field how many values change under `redact_untrusted`. **No corpus exists.** | `E0-O10.txt` | zero changes in amount, date and code fields, or the changed kinds are named and the lead accepts them | PR-2 |
| E0-O8 | H-0 and H-1: `grep -rn "environment: dev" tests demos docs > E0-O8-grep.txt`; `uv run --all-extras --group test pytest tests/test_stage_rename.py tests/test_anchor_retention.py -q > E0-O8.txt 2>&1`; the S3 probe against a fake client and, **UNVERIFIED**, against a real bucket (needs a third party and the owner: POST-DEMO) | `E0-O8*.txt` | grep empty after H-0; tests pass | H-0, H-1 |
| E0-O11 | A1: `uv run --all-extras --group test pytest tests/test_audit_verify_claims.py -q > E0-O11.txt 2>&1` (the cases listed in O-4.6, including the pinned words "probed" and "configured") | `E0-O11.txt` | pass; new tests fail on old code | A1 |

## O-8 Item homes

| Item | Home |
|---|---|
| Extract masking | PR-2 |
| Redaction | R |
| Key file read | K1 |
| Audit claims, retention | A1, H-1 |
| Approval text | G-W, G |
| Stage rename | H-0 |
| Evidence docs | H-2 |

## O-9 What I did NOT check

All of the copied text was written from code read in v8 and was not re-read this pass except through the citation program (`evidence-handoff-v9/raw-cite-check-v9.txt`, which checks that each cited line exists and holds the named identifier; it does not check meaning). No test was run. Vendor facts for the S3 probe are UNVERIFIED. The per-item needed-check verdicts were not supplied. No commit exists. Independent reviewers follow.
