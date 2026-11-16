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
- RUNG TABLE (mandatory, lead order 56, R448; marker "CODE-LAST v1"): one row per component: component | need | rung tried (SCALE OF 2026-11-06, bible R447: 1 no-code tools such as n8n, 2 our own core modules, 3 existing free tools: MCP servers, plain RAG, model features, 4 free libraries and open code, tested and licence-checked (R450), 5 our own new code last; the client's own tool counts as tried first and a rung the client closes is written CLIENT-EXCLUDED with date and source; tables written on the older 1-7 scale stay valid, state the scale at the top of the table) | evidence with source and date, or UNVERIFIED | what only our code gives | verdict KEEP-CODE / CUT-TO-CONFIG+GLUE / CUT. A higher rung at 80 percent or more means cut to config plus thin glue unless a guarantee gap is proved with a test idea. A ticket without this table does not enter build-start review. Frozen tickets carry it as a build note. If the ticket body is over about 250 lines, say why in its first lines.
