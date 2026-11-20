# D-config review 3 (fresh reviewer, read only; no src or tests edited)
Scope: secret_name.py, backends/platform_secrets.py check_senders, app.py reader and ref checks, config.py trigger floors and load_config, defaults.py, tests/test_trigger_hardening_round3.py, CHANGELOG.md. Pytest (round3 + secret_names + secret_reader): 139 passed. Scratch: /tmp/claude-0/s/a.py.
Result: 0 Blocker, 1 Medium, 2 Low, 1 Info. Not CLEAN: M1.

## M1 Medium: the path-shaped refusal is provider-blind and sender-blind, so it can break a set-up that has no trigger block and gives wrong error text
- secret_name.py:30-33 (`collides` returns True if ANY name is path-shaped, even with an empty `names`: `collides("/x/y", [])` is True, checked); platform_secrets.py:78-84 (check_senders refuses when any other name is path-shaped); app.py:181 calls check_senders unconditionally, with no `triggers:` block and an empty sender map.
- Scenario 1: an `aws` (or vault) secrets kind with a backend/tool/source `*_secret_name` of "/hadavin/prod/dsn" (leading slash is the usual AWS/SSM style; the aws provider passes the name through, secrets_aws.py:27). Before round 3 it started. Now start fails with "a secret name elsewhere ... has a path form" even though nobody configured a sender and the provider is not file-backed (no "..": a leading "/" is a plain name to AWS). The same applies to a trailing "/".
- Scenario 2: `reset_credential_ref` or `release_credential_ref` = "/hadavin/reset-dsn": app.py:203 and cli.py:239 / cli.py:532 now say "names a secret that the runtime also reads" / "names the same secret as ..." when it does not; the error text is untrue and the real reason (path form) is not given. Error text of the normal collision case is unchanged (test_step_b_e5b_reset_ref passes its pinned cases; I did not run the whole suite).
- No shipped fixture, demo or doc uses such a name (grep of tests, demos, docs, README: none), so nothing in the repo breaks; it is a user-config regression.
- Fix: run the path-shaped refusal only when senders exist (check_senders: `if senders and ...`) and, for `collides`, only when the other side is non-empty; refuse "..", "." segments always, but treat a leading or trailing "/" as refusable only for the mounted_file kind (or fold "/" like any separator, which canonical already does); give the ref checks their own text ("a path form") instead of reusing the collision text.

## L1 Low: the "." / ".." rule does not cover the Windows separator for mounted_file
- secret_name.py:26-29 splits on "/" only. On Windows `confined()` (config.py:657) resolves "a\..\x" to "x"; is_path_shaped("a\\..\\x") is False and canonical gives "a_x" (no collision with sender "x"). Linux: same string is a plain file name, correctly not path-shaped (checked: same()=False). The code has Windows branches (secrets_file.py, os.name == "nt"), so Windows is supported. Fix: split on both "/" and "\\" (over-refusal on Linux is harmless).

## L2 Low: file systems that fold names the text rules do not (macOS APFS/HFS+, Windows NTFS) under mounted_file
- Canonical turns every non-ASCII character into "_" first. A normalising or case-folding file system can map a non-ASCII name to the same file as an ASCII sender name: U+212A Kelvin canonically decomposes to "K" (HFS+/APFS normalisation), and U+017F long s folds to "s" on case-insensitive volumes (simple case folding). Other name "ſlack_token" -> "_lack_token" vs sender "slack_token": no collision, same file there. Not reachable on Linux ext4/overlay/Kubernetes volumes (byte-exact, case-sensitive). I could not test a mac or Windows volume here, so this is unverified. Fix if wanted: for mounted_file, refuse any non-ASCII other-name in check_senders (as the sender charset already refuses it).

## Checked and held
- Canonical vs providers: fuzz of 200000 pairs each, alphabet incl. a A k K i I dotted-I, dotless-i, long s, fi/ff ligatures, Kelvin, Angstrom, sharp s, combining acute, "_-.:/" and space. Env: every pair with the same `EnvSecretProvider.var` collides (0 misses). mounted_file: every pair whose `confined()` path is the same collides (0 misses; path-shaped names collide by fail-closed). Long s, ligatures, NFKC forms ("fi", "ſ"->"s", Kelvin->"K") each become one "_" in both env var and canonical (env replaces before upper, so no ASCII letter appears). NFKC compat forms only matter if a provider NFKC-normalised, and none does (env, file, gcp/azure/vault charset checks, aws pass-through, all byte-exact).
- Over-collision only (canonical collapses runs and "/" as "_"): safe direction; "ab" and "a-b" still differ in every provider.
- gcp/azure/vault refuse characters outside their charset before any read; aws is case-sensitive, so canonical lower-casing is merely stricter.
- `from None` at config.py:718 is after the try statement, outside every except: no `__context__`, no `__cause__`. Non-trigger ValidationErrors still chain (`from exc`, config.py:707). `exc` is deleted by Python at handler end; `trigger_text` holds only the str.
- app.py:366 `type(name) is not str or name not in allowed`: str subclass, bytes, None, unhashable all give PermissionError before the provider.
- Floors: 1024 bytes and 0.1 s are below every default (524288, 5.0); defaults, ceilings and CHANGELOG (339-341) agree; no shipped config, fixture, demo or doc sets max_body_bytes, ack_wait_s or max_running (grep). Booleans and quoted numbers refused (strict).

## Info
- I1: CHANGELOG.md:334 and :336-338 now describe the path-form refusal ("a name elsewhere in the config ... is refused at start"); if M1 is fixed, reword it (applies to a file-backed secrets kind, or when senders exist).

## Round 4 fix status (builder D4)
M1, L1, L2, I1 fixed (tests/test_trigger_hardening_round4.py, fail-first 25 of 29 on the old code). A "." or ".." segment
(split on "/" and "\") is refused for sender names and for other names when senders exist, for every kind; a leading or
trailing "/" only for the mounted_file kind (`file_backed`). `collides` is False for an empty list and fails closed on
path shapes only with `file_backed=True`. Reset and release refs with a path form get a "path-shaped" message.
L2 limit: for mounted_file names are compared in canonical form and also NFKC+casefold form (Kelvin, long s); this
is NOT tested on a real macOS (APFS/HFS+) or Windows (NTFS) volume, only by text. Env fold unchanged.
