# D-config review 4 (fresh reviewer, read only; no src or tests edited)
Scope: secret_name.py, backends/platform_secrets.py (check_senders), actions/secrets_file.py (file_backed), app.py:181-216, cli.py (:245, :486, :561-569), tests/test_trigger_hardening_round4.py + round3, CHANGELOG.md:330-341, against D-review-3.md.
Pytest (round4 + round3 + secret_names): 150 passed. Scratch: /tmp/core-b-scratch-D4/test_d4_scratch.py (3 passed).
Result: 0 Blocker, 0 Medium, 2 Low, 2 Info. CLEAN (nothing above Minor).

## (1) Original M1 attack, file-backed: still closed
Scratch test `test_m1_file_backed_refused`: folder with `slack_token`; `MountedFileProvider.get("a/../slack_token")` returns the same value (the alias is real); `check_senders(provider, {"s": ["slack_token"]}, {"a/../slack_token"})` raises ConfigError "...has a path form..." with no `file_backed` argument (read from `provider.file_backed`, secrets_file.py:27). Also refused: "./slack_token", "a\\..\\slack_token", "/slack_token", "slack_token/". In app.py:181-195 the same is reached through `b.secrets.kind == "mounted_file"` OR the provider flag.

## (2) Non-file-backed kinds
- check_senders(…, file_backed=False) with other name "/hadavin/prod/dsn" passes; other name "a/../x" refused (platform_secrets.py:99-105). Sender with a dot segment is refused for every kind (:96-99). With no senders nothing is compared (:92-93).
- Info I1: a SENDER name itself can never be "/hadavin/prod/slack": config.py:363 `^[A-Za-z0-9_.:-]{1,128}$` refuses "/" at load, before check_senders. This is an earlier-round rule (not D4's) and refusing is safe, but the D4 intent "aws-style names stay valid" holds only for names elsewhere in the config, not for sender secret names. If AWS-style sender names are wanted, the regex is the place; the CHANGELOG (:331-333, "no `/`") already states it.

## (3) `_file_backed(b)` and kind strings
Secrets kinds (backends/table.py:399-438): fake, env, aws_secrets_manager, vault, azure_key_vault, gcp_secret_manager, mounted_file. config.py:154 refuses an unknown kind at load, so an unknown string cannot reach `_file_backed`; a missing `secrets` block takes the default "fake" (table.py:595).
- Low L1: the default is fail-open for a FUTURE file-backed kind. cli.py:486-488 tests only `kind == "mounted_file"`; app.py:181 adds `provider.file_backed` (safe OR), but the CLI reset/release paths run before the provider is built (cli.py:245-256, :561-569), so a second file-backed kind added later is protected at start-up but not in `limits reset` / `release-expired` unless someone edits `_file_backed`. Suggest: one shared set `FILE_BACKED_KINDS` in table.py (or a `file_backed: bool` on `Entry`) used by app and cli, and a test that every secrets kind is classified. Not exploitable today.

## (4) NFKC + casefold forms (mounted_file only)
Run in scratch (file_backed=True / False): "strasse" vs "straße" collides True/False; "Key"/"key" True/True; "kit"/"kıt" (dotless i) False/False; "istanbul"/"İstanbul" False/False; "Secret"/"SECRET" True/True.
- Low L2: "ß" vs "ss" is a FALSE collision on Linux (two distinct files) and is refused only for mounted_file; "straße" and "strasse" cannot both be sender and backend names. Safe direction, rare, and CHANGELOG:340-341 says names are compared after NFKC and case folding but does not give this example or say it can refuse two names that are distinct on Linux. Suggest one sentence. Turkish dotless i and dotted I do not collide (casefold keeps them distinct; canonical turns them into "_"). Case-only differences already collide for EVERY kind through the lower-casing in `canonical_secret_name` (pre-existing, documented at CHANGELOG:334-335), so the fold adds nothing there.
- Windows NTFS trailing dot/space is not folded; "x." vs "x" still collides through canonical stripping of "_", so no gap seen.

## (5) Messages
app.py:207-217, cli.py:245-253 and :561-566 give a path-form text for dot-segment or file-backed leading/trailing "/" refs, then the collision text only for true collisions. None includes the ref or any name or value (checked each f-string/literal: all static; the CLI literal says "for a mounted_file folder ..." unconditionally, which is accurate as a rule statement). Truthful.
- Info I2: a reset/release ref with a ".." segment is refused for every kind including aws/vault, where a literal ".." may be legal; consistent with the stated rule, over-refusal only.

## (6) New
Nothing above Minor. Notes: cli.py reset compares the ref only against `dsn_secret_name` (cli.py:256), app.py against all runtime names; pre-existing split, the start-up check covers the rest. Symlinks planted inside the mounted folder (`a -> .`) can alias names that carry no dot segment; `confined` resolves them for reads but the name check is text-only; operator-controlled, out of scope. The scratch run imported the same package as the repo (copy of src/tests under /tmp/core-b-scratch-D4/; the venv is the repo's), so the result is for the current code.

## Disposition (core-b, review 4 CLEAN)
- L1 (the CLI tests only kind == "mounted_file"; a future second file-backed kind would be protected at start-up but not in `limits reset` / `release-expired`): recorded as a stated limit; when a second file-backed kind appears, use one shared set of file-backed kinds and a test that every kind is classified. Not exploitable today.
- L2 ("strasse" and "straße" collide under mounted_file only: safe direction): CHANGELOG sentence to add with the next trigger change.
- I1, I2: over-refusal only; accepted.
