# P1b result review, round 1, egm-codebase-details, snapshot P1b-0d843b4
Reviewer: fresh egm:egm-codebase-details agent (Sonnet). Ran no code. Condensed by the cloud session.
Cloud-session checks (run on worktree EV-P1b-0d843b4, py3.13, head 0d843b4):
- evidence.contains("Jose"+U+0301+" ok", "José" precomposed) -> False (F1 confirmed: new false abstain, fail-closed).
- evidence.contains(decomposed in decomposed) -> True (reviewer-1 F1 ALLOW-side claim: not compared with old code; fail-before not run).
- "password" in runmap.canonical("pass"+U+093E+"word").casefold() -> False (F2 confirmed: redaction gap with Mc mark still open on the real redaction path).

| id | sev | where | issue | fix |
|---|---|---|---|---|
| F1 | MAJOR | runmap.py:276-285; evidence.py:57,87-88,151 | per-character NFKC: decomposed evidence vs precomposed value no longer matches (new false abstain); no evidence test. | NFC after canonical in evidence, or ledger the cost; add pair test. |
| F2 | MAJOR | test_textnorm_siblings.py:251-261; textnorm.py ~216 | runmap.canonical and evidence.normalise still miss secrets hidden by Mc/Lm/Sk; test pins "0 of N" as KNOWN GAP; scan_holds has no production caller; no redaction outcome changes. Fix-not-defer. | Route runmap._views through textnorm.scan_views, or recorded lead decision (this is P1d scope). |
| F3 | MAJOR | defaults.py TEXTNORM_INSERTION_MIN_CHARS=8 comment; CHANGELOG 585,587 | default 8 is not "most cautious" (Greek 12, Cyrillic 10 measured; Cyrillic 8 = 7.1% extra, Greek 8 = 14-16%); Cyrillic 9 never measured. | Default 12 or measure Armenian/Georgian; fix comments. |
| F4 | MAJOR | perf312/313.txt; SK-4/SK-5 | S_call and 1,000-call time not recorded (no -s). | Re-run -s with HADAVIN_PERF_LOG; tighten 60 s ceiling. |
| F5 | MAJOR | ticket P1.md 56-70, 408 vs code | ticket: <=8 keys, no cap constant, no new constants, needle API cut; code: 16 keys, _SCAN_KEY_CAP, scan_holds/scan_needles/register_value etc., 12 TEXTNORM_* constants. | Append accepted orders to ticket or cut surface. |
| F6 | MINOR | test_textnorm_scan.py:97-136 | tests assert <=8 keys; hostile set lacks Mc/Sk+tag case (U+0903 gives 13). | Assert 16 / widen set. |
| F7 | MINOR | test_textnorm_siblings.py:188 | `cn not in TABLE` compares str to int-keyed table, never fails. | `ord(cn) not in TABLE`. |
| F8 | MINOR | test_textnorm_siblings.py:78-80,133 | message opposite of assertion; "Alíce" is precomposed, no real combining test. | Fix message; add U+0301 case. |
| F9 | MINOR | injection.py:45-55 | TextTooLong -> guard_unavailable for >262144 chars; availability cost uncounted; up to 29 views regex. | Document/chunk. |
| F10 | MINOR | textnorm.py:417-430 | U+02BC, U+2032, U+02B9, U+0060, U+00B4 not read as apostrophes; could_be_same_person("O'Brien","O"+U+02BC+"Brien") should be False. | Add or state limit. |
| F11 | MINOR | textnorm.py:1505-1514 has_mixed_script | \w+ excludes Mc/Sk so Latin/Cyrillic split by Mc defeats backstop. | Treat Mc/Sk as word-joining. |
| F12 | MINOR | textnorm.py:1078-1081 vs ~114 | "spelling variant" used with two meanings. | Rename. |
| F13 | MINOR | test_textnorm_perf.py:258-274 | worst-case row fails at first char, not worst case. | second = A^31 + B. |
| F14 | MINOR | test_textnorm_scan.py:315-319 | fuzz skips U+3000-U+1D3FF. | Widen. |
| F15 | MINOR | TABLE.md; pytest312/313; bandit.txt | suite red on dblink (env), no fail-before; unused `# nosec B102` at tools.py:389 (outside diff). | Run dblink test on P1a. (Cloud: dblink re-run passed on a port-5432 cluster, see evidence/dblink-rerun-2026-11-09.) |
| F16 | MINOR | runmap.py:276-298 | per-char normalize on hot path; no perf row. | Perf row; fast path. |
Cleared by reading: __all__ count 33, 216 mutant sum, tag-range edges, key bound 13, window arithmetic, Python->Unicode versions, Unicode facts.
Not checked: nothing run; _confusables, egress, generated tables, test bodies, mutant bodies, CHANGELOG corpus measurements.
