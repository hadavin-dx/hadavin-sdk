# Package ticket P1d-learn: an unknown AWS-style access key id (starts with AKIA or ASIA) written in lower case, or with one extra `&`, `.` or backslash inside, is not recognised as a key and reaches a person or the model. DRAFT revision 1 (plan review round 1 not yet run)

**Status (2026-11-09 UTC; IST = UTC+5:30):** text only, no code. Split from P1d by lead ORDER 177 (q386): the learning rule for unknown AWS-style keys is its own ticket with its own HELD gate (zero false learns, ORDER 168 item 3 attaches HERE, not to P1d-a or P1d). Rows, mutants and BS-2 moved from P1d rev 7; round-7 resolve G1 (right boundary) applied. The regex rows were run as a stand-alone probe (`handover/evidence/P1d/rev8-probes/learn.py`, output `learn-regex.txt`, Python 3.13, `-I`); nothing ran inside the redactor. Ticket name and the marker `P1DL_APPLIED` are DEFAULT PENDING LEAD (4). Marker: CODE-LAST v1. Under 250 lines.

## The problem in plain words
The redactor recognises an AWS access key id only as written: four capital letters `AKIA` or `ASIA`, then 16 more letters and digits, as one word. The same key in lower case, or with one `&`, `.` or backslash put inside it, is not recognised, and P1d's residue check (which compares a text with values ALREADY known) cannot help, because nobody has seen this key before. This package adds one narrow rule that learns such a key, so the text is withheld and the key becomes known for the rest of the run. A rule that guesses keys can also mistake ordinary words for keys (a "false learn"): such a text would be withheld for no reason, and on the model path the word would be masked in every later text of the run. So this package ships only if a test corpus shows zero false learns.

## Words used (defined once)
- **AWS-style learning rule** = the regex and checks in "Design". **Gap set** = the three characters `&`, `.`, backslash. **Candidate** = one regex match.
- **False learn** = the rule learns a string that is not a key (any learn on a made-up non-key text). **HELD** = this package does not merge; the exact count and the failing shapes go to the lead (ORDER 168 item 3).
- **View d** = P1d's last deleting view (markers `*`, `~`, backtick, controls, CR, LF, U+2028, U+2029 deleted; P1d "Words used"). The rule reads view d of the raw input (P1d rev 8, RS-1).
- Legend: fb = fails on the base (post-P1d main); pb = passes there; measure = reported, not claimed.

## Design
```
_learn_aws(view_d) -> list[str]:                     # called from P1d's _learn_unknown, private
  for m in re.finditer(r"(?i)(?=((?:akia|asia)(?:[a-z2-7]|[&.\\](?=[a-z2-7])){16,17})(?![a-z0-9_-]))", view_d):
      c = m.group(1)
      if count of [&.\\] in c <= 1 and len(c without them) == 20 and count of [2-7] in its last 16 >= 2:
          yield (c without the gap character).upper()
```
- **Lookahead, overlapping:** a candidate may start inside an earlier one (`decoy-asia`).
- **Right boundary `(?![a-z0-9_-])` inside the lookahead, no left anchor (round-7 G1):** the boundary set is the AWS pattern's own token set (`redact.py:195`, `[A-Za-z0-9_\-]{8,}`), so a candidate ends where the plain pattern's token would end (spec-derived, R337). Backtracking inside the lookahead lets a trailing gap character end a real key (`x akia.iosfodn27example.com y` is learned). A left anchor is rejected because it would drop H35 (`keyz` + K2) and `decoy-asia`, which ORDER 165 requires.
- **Two digits from 2-7:** a real key id is base32 (letters and the digits 2-7); words almost never hold two of those digits in 16 letters.
- **Output:** each learned key goes to P1d's `redact.add_known(work, "APIKEY", key)`; P1d rev 8's rule "a value learned only in a view withholds" then applies, and the value stays known for the run (P1d MAP-1). The per-call limit `max_learned_per_call` of P1d applies.
- **Marker:** `runmap.P1DL_APPLIED = True` (module level), checked by P1d-gate.

## RUNG TABLE (scale of 2026-11-06)
Gate: core change, no client, no fee, no dependency. Rung 1 closed (inside the choke point). Rung 4: detect-secrets and gitleaks find AKIA ids only in upper case with the prefix as written (from memory, read date UNVERIFIED, R450); neither reads our views.
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| AWS-style learning rule | learn an unknown key in lower case or with one gap character | 2 (the AWS pattern on P1d's views: case-sensitive, needs it joined); 4 (above) | `learn-regex.txt`; P1d FR4 | the narrow rule | **best effort**: tested on the listed rows and a made-up corpus (BS-2); any false learn = HELD | KEEP-CODE (about 15 lines) |
**80 percent (R448):** rungs 2 and 4 meet neither need (case, gap character). Cost (estimate): build 2-4 agent-hours, one plan round, result rounds uncapped; 0 fees, 0 tokens.

## Goals and Non-Goals
**Goals.** (G1) An unknown AKIA/ASIA key id written in lower case, or with exactly one gap character inside, holding at least two of the digits 2-7 among its last 16 characters, is learned and its text withheld. (G2) Zero false learns on the BS-2 corpus and the not-learned rows.
**Non-Goals (stated limits, ORDER 176 N-2; written in the client-facing limits).** An unknown AKIA/ASIA key is NOT learned when: (N1) its last 16 characters hold fewer than two of the digits 2-7 (about 17 percent of keys if characters are uniform: 3.6 percent none, 13.3 percent one; estimate); (N2) it is split by white space, `_`, `-`, `/` or by two or more gap characters; (N3) it is in lower case AND split; (N4) **(new, round-7 G1, DEFAULT PENDING LEAD 3)** it is in lower case or holds one gap character AND is glued on the right to further letters, digits, `_` or `-`. The same key in upper case without a gap is already masked by the plain AWS pattern. A KNOWN key is still caught in all these shapes by P1d's residue rule. (N5) Other token kinds in another case or with a gap character (P1d N6).

## Rows (`tests/test_p1d_learn_rows.py`; literals in `tests/fixtures/p1d_cases.py`, built from parts: K = `"AKIA" + "IOSFODNN7EXAMPLE"` (one digit from 2-7), K2 = `"AKIA" + "IOSFODN2" + "7EXAMPLE"` (made-up, two digits from 2-7)). Entry: model (`redact_text` default) unless named; every row also runs through `clean` (expected `LookalikeCopy` where "learned").
"Probe" = `learn-regex.txt` (the rule alone, on the string given, or on its view d where marked).
| row | class | input | probe | expected after |
|---|---|---|---|---|
| H32 | fb | K2 in lower case | learned | notice (withheld) |
| H33a | fb | `AKIA&amp;IOSFODN27EXAMPLE` (decoded `&` in view d) | learned | notice |
| H33b | fb | `AKIA.IOSFODN27EXAMPLE` | learned | notice |
| H33c | fb | `AKIA\IOSFODN27EXAMPLE` | learned | notice |
| H35 | fb | `keyz` + K2 | learned | notice |
| H35b | fb | `keyz` + K2 + ` here` | learned | notice |
| GAP-END | fb | `x akia.iosfodn27example.com y` | learned | notice |
| decoy-asia | fb | `ASIAQWER` + K2, all lower case | learned (only the lookahead finds K2) | notice |
| H33m | measure | H32 and H33a-c written with K | not learned (N1) | measured, reported |
| sq-split1, sq-split4 | measure | K2 as single characters split by spaces; `AKIA IOSF ODN2 7EXA MPLE`; the same with K | not run | measured (N2) |
**Not learned and not withheld** (each must give the base output; probe: all `[]` with the right boundary): `Southeast Asia and Oceania`; `Asia 2024 Q3 revenue growth`; `Eurasia 2025 results`; `Asia-Pacific 2025 results`; `Asia and Oceania markets overview`; `Asia leads 5 new markets signed`; `Malaysia has 5 offices in total`; `Southeast Asia sales rose 4 percent`; `Nakia 3 teams`; `Asia pacific region Q3 2 results`; `asia-markets-rise-3-5-percent`; `asia_region_q3_q2_totals`; `ASIA_SHARD_2_REPLICA_3_PRIMARY` (masked by the plain AWS pattern today, not learned); `Asia 2 of 3 are on it so be`; `asia.shard23.example`; `asia.region23q4totalsx.v2` (**learned by the rev-7 rule**, probe: `ASIAREGION23Q4TOTALS`; fixed by the boundary); `akia` + `abcdefghijklmnop`; `asianmarketsq23q4forecast`; `asiapacificregion23q4`; **new (G1):** `asiaabcdefghijklm23n8xyz`, `region asiaabcdefghijklm23n_8`, `asiaabcdefghijklm23n-v2` (all three learned by the rev-7 rule, probe), `Asia` + LF + `abcdefghijklm23n0 end` (view d `Asiaabcdefghijklm23n0 end`: learned by rev 7, not with the boundary, probe `viewd`); a base32 blob of 4,000 characters and a wrapped hex digest (two lines) from `tools/p1d_corpus.py --seed 1`.

## Mutation plan (`tests/p1d_learn_mutants.py`; all required; numbers kept from P1d rev 7 so the ledger stays traceable)
| mutant | planted change | killer (probe where run) |
|---|---|---|
| M7 | rule removed | H32, H33a-c, H35 |
| M8 | two-digit test removed | `asia-1d` = `asia.` + `abcdefghijklm3no` (probe: learned under M8) |
| M9 | class `[a-z2-7]` widened to `[a-z0-9]` | `m9-kill` = `asia` + `bcdefghijk01mn23` (probe: learned under M9) |
| M33 | gap set widened to white space | `Asia 2 of 3 are on it so be` |
| M34 | two gap characters allowed | `asia.region23q4totalsx.v2` |
| M35 | lookahead removed | `decoy-asia` |
| M43 | right boundary removed | `asiaabcdefghijklm23n8xyz` (probe: learned without it) |
| M44 | `_` dropped from the boundary set | `region asiaabcdefghijklm23n_8` |
| M45 | `-` dropped from the boundary set | `asiaabcdefghijklm23n-v2` |
| M46 | `P1DL_APPLIED` set while the rule is not called | `test_marker_means_rule_runs` (H32 through `redact_text` with the marker true) |

## Build steps
- **BS-0** (before code): re-run `learn.py` on the post-P1d base; run the rule alone on the first 200 corpus documents; any false learn = report to the lead before the build (likely HELD).
- **BS-2** (final head) false learns on P1d's BS-1 corpus plus hex digests, UUIDs, base64 blobs, 2,000 lines of code and the not-learned rows; reported per shape; a document in both BS-1 and BS-2 is listed once. **Gate: 0. If not 0, this package is HELD: exact count and failing shapes to the lead; the client-data gate stays closed (P1d-gate refuses the client profile without `P1DL_APPLIED`).** The corpus is made up (synthetic), so 0 of N supports a rate below about 3/N at 95 percent (rule of three), not zero; say so in the report. `p1d_corpus.py` exit codes: 0 pass, 3 HELD, 1 error.

## Template fields
- **Package id and name:** P1d-learn (DEFAULT PENDING LEAD 4), "learn unknown AWS-style keys". Branch `core/P1d-learn`. **Path class:** redaction; **extended review (no round cap): yes** for results; one plan round (DEFAULT PENDING LEAD 2).
- **Depends on:** P1d rev 8 merged (`_learn_unknown`, view d, `add_known`, the withhold rule); order P1d-a, P1d, P1d-gate, P1d-learn (DEFAULT 4).
- **Class (R337):** "an unknown value is matched only in the spelling as written".
- **Files:** change `guard/runmap.py` (`_learn_aws`, its call in `_learn_unknown`, `P1DL_APPLIED`), `CHANGELOG.md`; create `tests/test_p1d_learn_rows.py`, `tests/p1d_learn_mutants.py`; extend `tools/p1d_corpus.py` (`--kind bs2`).
- **Interface:** none public besides `P1DL_APPLIED: bool`. **Neutral default / alternative:** no vendor; without this package P1d stands alone (the residue rule for known keys).
- **Security notes:** no identity or secret; only `AKIAIOSFODNN7EXAMPLE` as a whole-key literal; K2 is built from parts.
- **Rollback:** tag `pre-P1d-learn`; removing the package drops the marker, which closes the client profile again (P1d-gate).
- **Reviewers:** fresh `egm-design` + `egm-implementation-readiness`, given the diff, this ticket and the evidence only.
- **Done =** BS-2 = 0 false learns; a fresh round finds no blocker or major; all gates green (as P1d); ledger row BL-core-p1d-008 FIXED-VERIFIED; the lead merges.

## Evidence commands
As P1d-a's list (copied from `ci.yml`), with `tests/p1d_learn_mutants.py` and `tools/p1d_corpus.py --seed 1 --kind bs2` in place of the P1d-a scripts; raw output to `handover/evidence/P1d-learn/evidence-<n>.md`.

## Owner-facing wording
CHANGELOG: "Keys that start with AKIA or ASIA are now also hidden when written in small letters or with one extra `&`, `.` or `\` inside, if the key holds at least two of the digits 2 to 7. Not covered: such a key with fewer than two of those digits, split by a space, `_`, `-`, `/` or two extra characters, in small letters and split, or glued on the right to more letters or digits."

## Ledger row closed
BL-core-p1d-008 (MAJOR, glued, dotted or `&`-inserted key passes, H33, H35), moved from topic P1d to topic P1d-learn.

## DEFAULT PENDING LEAD
(2) one plan round; (3) N4 accepted as a stated limit; (4) the name P1d-learn, the marker `P1DL_APPLIED`, and the merge order.

## Revision log
Rev 1 (2026-11-09): split from P1d rev 7 (rows H32, H33a-c, H33m, H35, the AWS-rule rows, M7-M9, M33-M35, BS-2, ledger 008; ORDER 177); round-7 G1 applied (right boundary, four new not-learned rows, M43-M45, N4, wording "best effort"); M46 and `test_marker_means_rule_runs` added so the marker cannot be set without the rule.
