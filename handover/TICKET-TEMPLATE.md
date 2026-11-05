# Package ticket (one per package; reviewed before building)

- Package id and name: (plan id, e.g. P4b)
- Path class: money | redaction | security | other. Extended review (no round cap): yes/no
- Depends on (merged first): 
- Problem in plain words (3-5 sentences, no unexplained jargon):
- Source of the code (MANIFEST ids, source repo, commit sha) and what is NOT taken:
- Target module and path in `src/hadavin_sdk/`:
- Interface (names, argument and return types, errors): 
- Neutral default / working alternative (or written outline with trigger):
- Files to create, change, delete (each with the reason):
- Existing core code reused (list what you checked: hashing, k1b/atomic, k1b/redaction, stats, evals, store/memory, tests/contracts):
- Security and least-privilege notes (identity, rights, secrets, personal data, dev-only flag):
- Tests: unit; the FAIL-BEFORE test (which old behaviour it catches); hostile inputs; race/process tests where money or state is involved; contract suite for kinds with several backends:
- Mutation plan: which behaviours get a mutant, which test kills each:
- Evidence commands (exact), and where the raw output is saved:
- Reviewers: correctness + adversarial (fresh agents; they get the diff, this ticket and the evidence only):
- Done = (the plan's stop rule) and all gates green: tests, ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit.
- Rollback: tag `pre-<package>`; migrations additive; semantic changes marked non-revertible with a loud-failure test.
