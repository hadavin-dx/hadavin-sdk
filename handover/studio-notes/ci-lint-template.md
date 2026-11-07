# CI lint set: files to copy to the demo repos, the portal kit and the website

Source: branch core/ci-lint-set of the core repo. Written 2026-11-07. Not committed to the handover worktree (the lead places it).

## Copy as they are
1. `.pre-commit-config.yaml` (ruff check --fix and ruff format; the ruff-pre-commit commit is pinned by full hash; keep it equal to the ruff version in pyproject).
2. `.github/workflows/ci.yml`: add the job `lint-set` (do not rename existing jobs; it is not a required check). Keep `ACTIONLINT_VERSION` and `ACTIONLINT_SHA256` together; the step passes `-shellcheck=` because shellcheck is GPL.
3. `docs/lint-tools.md`: edit the counts and the contract list for the repo.

## Edit per repo
4. `pyproject.toml`
   - `[dependency-groups] lint`: mypy, types-* stubs the repo needs, import-linter, deptry, vulture, all with `==` pins; regenerate the lock with the same uv version CI uses.
   - `[tool.ruff.lint] select`: the same list as core (explicit `select`, not `extend-select`, so RUF100 really runs); `ignore = ["PLC0415", "SIM112"]` only if the repo has the same reasons; otherwise fix the findings.
   - `[tool.mypy]`: start with `follow_imports = "silent"` and an `exclude` list of the files not yet clean; shrink it later. Basic mode.
   - `[tool.importlinter]`: contracts for this repo. Demo repos: "the demo's package never imports the executor or a secret holder of the core" and "vendor cloud SDKs only inside their own module". Portal kit and website: only the vendor rule if they have Python.
   - `[tool.deptry] known_first_party`: the repo's own package names.
   - `[tool.vulture] paths, min_confidence = 60` and `vulture_whitelist.py` (one line per name, with the reason as a comment; the file is excluded from ruff).
5. Website (no Python): only `.pre-commit-config.yaml` is not needed; use actionlint on `.github/workflows` and zizmor (>= 1.28.0). Add a markdown/link check only after a trial shows no flakiness.

## Rules that must not change
- No GPL tools (shellcheck, yamllint). semgrep stays as is.
- zizmor >= 1.28.0. ast-grep >= 0.50.0 or skipped.
- CI only reports; it never pushes a commit. autofix.ci is an owner option and is not enabled.
- No new `noqa`, `type: ignore`, `nosec` or per-file ignores for findings.
- Order of work in a repo: trial each tool on main and save the counts; fix findings; plant one violation per tool on a throwaway copy and save the red output; then merge the config.
