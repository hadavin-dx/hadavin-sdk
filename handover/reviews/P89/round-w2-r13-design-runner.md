# PR89 round 13, slice tools/mutation_runner.py (egm-design, fresh), head 0cd10b99f3c5
Coverage: lines read 1,100 / 1,100 of the file. DIFF.patch only grepped. Reviewer could not run code: failing inputs come from reading.
Verdict: no Blocker. Refuse rule and the one fragment mechanism hold for the printed forms they target. No backtracking, no dead code, no references to deleted machinery.
M1 (Major, 392-400 _secret_values): re-encoded and re-decoded password forms unmasked. A: password `p$ss/w` re-encoded as `p%24ss%2Fw` (also lowercase hex); B: password `a%2540b` decoded twice gives `a@b`. Fix: add quote(safe=""), quote, quote_plus in upper and lower hex; unquote to a fixed point, refuse-check each step.
M2 (Major, 309 _PASSWORD_WORD): lookbehind skips `sslpassword=`, `dbpassword=`, `PGPASSWORD=` inside text. Lookbehind can only under-mask: remove it.
M3 (Major, 538-541, 89): lock file name = first 16 hex of SHA-256 of the whole value, in a world-listable temp folder = 64-bit offline guess check. Fix: hash the value with every password text removed, or HMAC with a per-user 0600 secret.
N4 (Nit, 345-359 _url_passwords): over-refuses `...:5432/db?application_name=caf%C3%A9&x=a@b` (port colon taken as password start); restrict candidates to userinfo. Memory is quadratic for many `@`; no length cap.
N5 (Nit, 404-429, 228): cost claim "about a second" has no stated bounds; O(len^2) per hit per secret. Cap total secret length with a value-free refusal, or state the bound.
N6 (Nit, 313 _DOTS): only ASCII "..." counts; a pytest that prints U+2026 would leak head/tail silently. Add the alternative to the pattern or a test that fails when the installed pytest prints no ASCII "...".
N7 (Nit, 441-445): more than 1,000 "..." wipes the whole line; mask the first 1,000 hits and apply exact-match masking to the rest.
N8 (Nit, docstring 56-99): changelog narrative (hash, sha256) in a file copied into demos; "shorter than the whole text" vs code "shorter than the secret".
N9 (Nit, 321-329): refusal also hits quotes in non-secret parts of the value (e.g. options='...'); the Cost sentence should say so.
Not findings: case handling, control/DEL/non-ASCII/U+0085 refused, %FF/%27/%5C/%00 refused, merged masks hide length, one-character fragments left by rule.
