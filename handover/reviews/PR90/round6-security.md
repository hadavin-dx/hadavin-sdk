# PR90 round 6, security (head 5e93812). No Blocker; 4 Majors (F1-F3, F4 comments). Reviewer ran nothing.
Purposes: scope=HEAD intact; curl retries intact; pin test golden holds but second layer unproven (F2).
- F1 Major: check_gitleaks_config negative tests vacuous (all 4 BAD_TOML cases fail at the first `cfg == golden` assert; ls-files loop never reached). Latent false red: third allowlist path tests/fixtures/textnorm_golden.json not in ALLOWED_HITS. Fix: golden= parameter, per-case reach, positive control, add textnorm path.
- F2 Major: check_structure calls check_golden first, so SCAN_WORDS/CURL_FLAGS/handler/checksum-adjacency checks never fail in any test. Fix: split check_golden / check_shape; mutation tests call only check_shape; document golden regeneration.
- F3 Major: tool-path step covers sha256sum tar curl git only; .venv/bin first on PATH shadows grep/date/tr/cut/sort/head/mktemp/rm/python3. Fix: add python3; require absolute result; class fix: fail if a name in .venv/bin also exists in a system PATH dir. Remaining: hostile lock file needs owner review (finding 5).
- F4 Nit: stale comments .gitleaks.toml lines 5-6, 37-38 ("scans every fetched ref", "must be on main before").
- F5 Nit: docstring after calls; ls-files check=True outside git; other-workflow check narrow. F6 Nit: --max-time banned, stall bounded only by job timeout; 404 retried ~25 s.
Follow-up (lead): findings 3,5,6,7,8,9 (suppression markers, CODEOWNERS owner-only, etc.).
Not checked: any run; golden byte-compare; other workflows, pyproject, uv.lock, scan_repo.py.
