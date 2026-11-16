# Look-alike design round 2: adversarial review (draft 2, option b)

Reviewer: fresh Sonnet reviewer (ab6e6559e88e9c7ed), read-only, no code run. Saved by the lead session; condensed from the hand-back (finding ids, severity, problem, fix kept). UNVERIFIED by execution: all timings, the prototype table, `scan_keyset` behaviour on U+FFFD, Warden code, the literal-backslash-n case.

Verdict: shape (b) is right and the three call sites cover every caller of `redact_text`, bare `redact`, `redact_many`. Not ready: three decisions rest on wrong or understated claims; three stated limits can be closed with existing parts.

| id | sev | problem | fix |
|---|---|---|---|
| ADV-LK2-1 | MAJOR | `LOOKALIKE_KINDS` drops NAME/ADDRESS/TENANT whole, so every variant leaks, not only the all-capitals one; they are pattern-found (redact.py 402-454), not only hand-registered. | Keep the kinds with a case-sensitive key (fold without casefold, class map, whitespace removed); only case-only copies stay open; add Cyrillic/combining/split-line NAME rows and an accented-spelling false-refusal row. |
| ADV-LK2-2 | MAJOR | Capital Eta reads h in one reading and n in the other; a value with both h and n written with Eta twice is found in neither reading (P1.md line 56). Not listed in section 10. | Add the row; close with a coarser class map in the check (merge h/n etc.), or list the gap. |
| ADV-LK2-3 | MAJOR | Inert fillers (dot, hyphen, underscore, U+FFFD) between letters defeat every row; `id_keyset` would drop them; deferring it breaks fix-dont-defer. | Also search `id_keyset` keys for secret kinds, segment by segment, min 12 alphanumerics, filler rows. NOTE (resolve): `id_keyset` is cut to v1.1 by P1 round 7 (PL27); the design must choose: keep id view back in P1b, or state LKV-7 as open. |
| ADV-LK2-4 | MAJOR | Account-number answer incomplete: `ACCOUNTID` `\b\d{12}\b` and `PHONE` already mask 10-16 digit runs without context; real gap is 8-9 digits, 17+, glued forms. | Restate section 9 by length; split ACC-1; say P5c adds no 8-9 digit pattern and why. |
| ADV-LK2-5 | MINOR | EMAIL pattern matches both cases; variant is masked, not refused; LK-KIND/FR-7 would fail. | Use a mapping-handed secret/high-entropy case variant; email row becomes a Cyrillic row. |
| ADV-LK2-6 | MINOR | Value learned only by a later leaf: run `_redact_value` twice. | Do it in v1 or give a reason. |
| ADV-LK2-7 | MINOR | Finder rebuilt with `scan_keyset` of every original whenever the map differs; O(map) per new value. | Per-run memo original to keys; compare FR-15 to the sweep rebuild cost. |
| ADV-LK2-8 | MINOR | Budget tight (defaults.py 34-37: 2.6-7.2 s hostile); check adds up to 4 `scan_keyset` calls. | Measure benign near-cap docs; state added passes; skip a view equal to `out`. |
| ADV-LK2-9 | MINOR | Refusal ends the run; `_withhold` (redact.py 901, 1187) is a line-level precedent. Missing false-refusal sources: 255-char SECRET captures, planted variants, yes/no oracle. | FR rows for these; name `_withhold` as the v1.1 step. |
| ADV-LK2-10 | MINOR | Several callers pass `{}` (judge.py 71, tools.py 1005, evals.py 63, channel.clean), so K is empty; Warden owner not named. | Caller table; name Warden port owner (UNVERIFIED). |
| ADV-LK2-11 | NIT | U+FFFD already occurs in real input; sentinel may confuse. | Row; segment scan removes the dependency (matches RES-1). |
| ADV-LK2-12 | NIT | `fold` drops Mn; FR-5 must use same-script values and near-identical words. | State it. |
| ADV-LK2-13 | NIT | `LookalikeCopy` is RuntimeError; bare callers will not catch it as `RedactionError`. | Say which exception bare callers catch. |
| ADV-LK2-14 | NIT | Reversed and hex "cannot be closed" is too strong; one extra key each. | Reword "not closed in v1"; give the cost. |
| ADV-LK2-15 | NIT | Minimum 12 leaves the usual 8-10 character password open. | Per-kind minimum as a lead decision; state in LKV-2. |

Checks that held: table rows on `redact_text`; bare `redact`/`redact_many` refusal; learning order; cache keyed on map equality; placeholder replacement only for genuine placeholders; shared helper needs only longest match.
