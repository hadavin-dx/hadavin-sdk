# Package ticket P1d-learn: a secret nobody has seen before (an AWS-style key, another key or token, an e-mail address) is visible only once formatting is removed (split by `**`, a terminal colour code, a backspace, an accent, a look-alike letter, a line break), or an AWS-style key is written in lower case or with one extra `&`, `.` or `\`; it reaches a person or the model. DRAFT revision 2 (plan review round 9 not yet run)

**Status (2026-11-09 UTC; IST = UTC+5:30):** text only, no code. **Every learning pass of the P1d family is in this ticket (lead ORDER 180 (2)), so only this ticket carries HELD** (zero false learns, ORDER 168 item 3, ORDER 177). Rev 2 takes the learning pass of the redactor's own patterns, its rows and mutants from P1d rev 8, and applies `handover/reviews/P1d/round8-resolve.md`. The regex rows of rev 1 were run as a stand-alone probe (`handover/evidence/P1d/rev8-probes/learn.py`, output `learn-regex.txt`, Python 3.13, `-I`); the rows added in rev 2 are hand-traced only (UNVERIFIED until BS-0). Marker: CODE-LAST v1. Under 250 lines.

## The problem in plain words
P1d stops a value that is ALREADY KNOWN (masked earlier in the same text or run) from being shown again with formatting inside it. It cannot help with a value nobody has seen: `key AKIA**IOSFODNN7EXAMPLE** here` holds a key that no pattern matches as written. This package runs the redactor's own patterns, plus one narrow rule for AWS-style keys, on the text with the formatting removed. A value found only there is "learned": the text is withheld and the value is known for the rest of the run. A guessing rule can also mistake ordinary text for a secret (a "false learn"): that text would be withheld for no reason, and on the model path the word would be masked in every later text of the run. So this package ships only if the test corpus shows zero false learns.

## Words used (defined once; P1d's "Words used" applies too: raw input `r`, views, known value, withheld, work map)
- **Learning pass** = `_learn_unknown`: the patterns below run on the learning views; their output text is thrown away, only found values are kept. **Candidate** = one value a pattern finds there. **Learned value** = a candidate added to the work map that was not in it before.
- **Learning views** = P1d's views b1, c, d of the RAW input `r` (RS-1: on the card path `neutralise` has already turned escapes into spaces), plus **d_sp** = c with each CR, LF, U+2028 and U+2029 replaced by one space, then `delete_noise` (markers and controls deleted, line breaks kept as a space).
- **Learning kinds** `LEARN_KINDS` = `SECRET_KINDS` (`redact.py:1140-1156`) minus `HIGHENTROPY`, `CREDITCARD`, `IBAN`, plus `EMAIL`.
- **Containment filter** = a candidate is dropped when its fold (`textnorm.fold`) contains the fold of a value known BEFORE the learning pass (not a seed entry, raw length at least `min_key_chars`). Reason: then the view only glued text onto a value that pass one already masked (a key at the end of a line followed by a letter, or `josé@example.org`, where pass one masked `s@example.org`).
- **AWS-style rule** = the regex and checks in "Design". **Gap set** = `&`, `.`, backslash.
- **False learn** = a learned value in a made-up text that holds no secret. **HELD** = this package does not merge; the exact count and the failing shapes go to the lead.
- Legend as P1d (fb, pb, ow, measure, new-surface; entry card / summary / model).

## Design
```
redact_text(..., _learn=True)              # private flag added here; False only in channel.card_text (P1d)
  after P1d's pass one, before _finish:
    if _learn:
      known_before = {o in work.values(): not seed(o) and len(o) >= min_key_chars}
      added = _learn_unknown(r, views_of_r, work, known_before)   # the values given to add_known
      if len(added) > _SETTINGS.max_learned_per_call: return _withhold("residue", ctx, mapping)       # nothing committed
      if added: return _withhold("residue", ctx, mapping, work=work)   # model path commits them (MAP-1L)

_learn_unknown(r, views, work, known_before) -> list[str]:
  lines = split views.c at each CR, LF, U+2028, U+2029
  d_sp = " ".join(delete_noise(x) for x in lines)        # BS-0: "".join(...) == views.d (STOP if not)
  for v in (views.b1, views.c, views.d, d_sp):
    for kind, value in redact.find_matches(v, kinds=LEARN_KINDS):
      if value not in work.values() and not contained(value, known_before): add_known(work, kind, value)
  for value in _learn_aws(d_sp):
    if value not in work.values() and not contained(value, known_before): add_known(work, "APIKEY", value)

_learn_aws(view) -> list[str]:
  for m in re.finditer(r"(?i)(?=((?:akia|asia)(?:[a-z2-7]|[&.\\](?=[a-z2-7])){16,17})(?![a-z0-9_-]))", view):
    c = m.group(1); k = c with the gap character removed
    if len(k) == 20 and count of [2-7] in k[4:] >= 2: yield k.upper()
```
- **`redact.find_matches(text, *, kinds=None) -> list[tuple[str, str]]`:** `r = _Redactor(None); r.find(text)`; returns `[(kind_of(ph), original) for ph, original in r.mapping.items()]` in placement order, filtered by `kinds`. It includes the extra "piece" entries `_place` adds for secret kinds (`redact.py:958-971`). It touches no map and no cache. `test_find_matches_equals_redact_mapping` (property): equal to `redact(text, _sweep_copies=False).mapping` as (kind, original) pairs.
- **`redact.add_known(mapping, kind, value) -> str`:** `r = _Redactor(mapping)` (copies the dict, `redact.py:896`); placeholder = `r.reverse[value]` if present, else `r._place(kind, value, value)`; then `mapping.update(r.mapping)` (so pieces arrive too) and return the placeholder. It is given no cache: the run's `redact_cache` is safe because `_Redactor` reuses a build only while `cache["map"] == self.mapping` (`redact.py:916-918`). It works for a plain `{}` and a `RunMap`.
- **Work map** = P1d's `work` (the dict `redact` returns, `runmap.py:448`), so learning never writes the caller's map before the commit.
- **Right boundary `(?![a-z0-9_-])` inside the lookahead, no left anchor:** the boundary set is the AWS pattern's own token set (`redact.py:195`, `[A-Za-z0-9_\-]{8,}`), so a candidate ends where that pattern's token would end (R337). Backtracking lets a trailing gap character end a real key (`x akia.iosfodn27example.com y`). A left anchor is rejected: it would drop H35 and `decoy-asia`. The rule reads d_sp, not d, so a line break ends a candidate (round-8 design M1: in d, a key at the end of a line glued to the next line).
- **At most one gap:** 16 or 17 items and 16 non-gap characters after the prefix allow at most one gap, and a gap must be followed by a class character. Rev 1's `count <= 1` test was dead code and is deleted (round-8 M2).
- **Two digits from 2-7 among the 16 characters after the prefix:** a heuristic. That key ids use only A-Z and 2-7 is an observation from public examples, UNVERIFIED (AWS documents only "20 characters"; R450); BS-0 records a source or keeps the word "heuristic".
- **Output:** every learned value withholds (ORDER 180 (3), fail closed) and stays known for the run (MAP-1L). Over `max_learned_per_call` the reason is `residue`, not `size`, so the card path raises `LookalikeCopy` and never falls back to the "too large" card (P1d M6 decision).
- **Marker:** `runmap.P1DL_APPLIED = True` (module level), checked by P1d-gate.
- **Setting (added to P1d's `RedactionSettings`):** `max_learned_per_call` (`P1D_MAX_LEARNED`): start 16, range 1 to 256, source: unmeasured placeholder; `test_constants_out_of_range_refused` gains this field.

## RUNG TABLE (R447, R448, R450; scale of 2026-11-06)
Gate: core change, no client, no fee, no dependency. Rung 1 closed (inside the choke point). Rung 3 closed (a model feature cannot be exact). Rung 4: detect-secrets and gitleaks find AKIA ids in upper case as written (from memory, read date UNVERIFIED, R450); neither reads our views.
| component | need | rung tried | evidence | what only our code gives | guarantee | verdict |
|---|---|---|---|---|---|---|
| learning pass | find an unknown value the patterns see only with formatting removed | 2 (the redactor's patterns, P1d's views) | P1d rev 8 rows; BS-2 | four learning views and the containment filter | **best effort**: rows plus the made-up BS-2 corpus; any false learn = HELD | KEEP-CODE (about 40 lines) |
| AWS-style rule | lower case or one gap character | 2 (the AWS pattern: case-sensitive, needs it joined); 4 (above) | `learn-regex.txt`; P1d FR4 | the narrow rule | best effort, as above | KEEP-CODE (about 15 lines) |
**80 percent (R448):** rungs 2 and 4 meet neither need as written. Cost (estimate): build 4-6 agent-hours, result rounds uncapped; 0 fees, 0 tokens.

## Goals and Non-Goals
**Goals.** (G1) An unknown value of a learning kind, readable only in a learning view, withholds the text and becomes known for the run. (G2) An unknown AKIA/ASIA key in lower case, or with one gap character, with at least two of the digits 2-7 in its last 16 characters, is learned. (G3) Zero false learns on BS-2 and the guard rows.
**Non-Goals (stated limits, ORDER 176 N-2; in the client-facing limits).** An unknown AKIA/ASIA key is NOT learned when (N1) its last 16 characters hold fewer than two of the digits 2-7 (about 17 percent of keys if characters are uniform: 3.6 percent none, 13.3 percent one; estimate); (N2) it is split by white space, `_`, `-`, `/` or two gap characters; (N3) it is in lower case AND split (a line break counts as a split); (N4) it is in lower case or holds a gap character AND, in the text as written, letters, digits, `_` or `-` follow it with no space or line break between. (N5) Other token kinds in another case or with a gap character. (N6) A first-seen host name split by formatting (the host pattern is not a learning kind: the H28 rows need only e-mail). (N7) A first-seen value containing a value already known: the containment filter drops it; the known part is masked by P1d.

## Rows (`tests/test_p1d_learn_rows.py`; literals in `tests/fixtures/p1d_cases.py`, built from parts; the row id is the test id)
**Literals:** P1d's K, K4, K16, EM, ESC; K2 = `"AKIA" + "IOSFODN2" + "7EXAMPLE"` (made up, two digits from 2-7). **Expected "learned":** card entry raises `LookalikeCopy`; model entry returns `WITHHELD_NOTICE`; through `request_approval` no request is saved. Every model row also runs through `clean`. "Probe" = `learn-regex.txt` (rev 1 rows only).
| row | class | entry | input | expected |
|---|---|---|---|---|
| H01 | fb | card | `key AKIA**IOSFODNN7EXAMPLE** here` | learned (APIKEY on d) |
| H02a-e | fb | card | `AKIA**IOSFODNN**7EXAMPLE`; `AKIAIO*SFODNN7EXAMPLE*`; `AKIA~~IOSFODNN7EXAMPLE~~`; ``AKIA`IOSFODNN7EXAMPLE` ``; `AKIA_*IOSFODNN7EXAMPLE*_` | learned |
| H11 | fb | card | K4 + ESC + `[0m` + K16 | learned (raw input, RS-1) |
| H12a-d | fb | card | K4 + x + K16, x = ESC `[38;5;196m`; `\x9b0m`; ESC `]0;t\x07`; ESC `]8;;http://x\x07` | learned |
| H13 | fb | card | K4 + the 7 characters `\x1b[0m` (literal backslash) + K16 | learned (over-refusal accepted) |
| H14 | fb | card | K4 + ESC + K16 (ESC + `I` is one escape, `redact.py:821`) | learned (b1 deletes the escape; 19 of 20 characters shown on the base) |
| H15a | fb | card | `x\x08` + K | learned (overstrike in b1) |
| H16, H16b, H16c | fb | card | K4 + CR / U+2028 / U+2029 + K16 | learned (d) |
| H18a-b | fb | card | `AKIAIO` + U+0301 / U+0323 + `SFODNN7EXAMPLE` | learned (c) |
| H21 | fb | card | K with both `A` of `AKIA` as U+0410 | learned (c) |
| H28a | fb | card | `anna.m**@example.org**` | learned (EMAIL on d) |
| H28b | fb | card | `anna.m@exam` + ESC + `[0mple.org` | learned (EMAIL on b1) |
| H31 | fb | model | `AKIAIOSFODN` + LF + `N7EXAMPLE` | learned (d; `AKIAIOSFODN` alone is no match, so nothing known contains it) |
| H37a-c | fb | model | a GitHub-token shape (prefix from `_KEY_PREFIXES`, BS-0) built from parts, split by `**` / LF / U+FF0A | learned |
| C01-C10 | fb | card | P1d rev 8 combination inputs: C01 `AKIA**` + U+041E + `SFODNN7EXAMPLE**`; C02 `AKIA**IO` + U+0301 + `SFODNN7EXAMPLE`; C03 `AKIA&ast;&ast;IOSFODNN7EXAMPLE`; C04 `AKIA&amp;ast;IOSFODNN7EXAMPLE`; C05 K4 + ESC + `[0m**` + K16; C05b `AKIA&#27;[0mIOSFODNN7EXAMPLE`; C06 K4 + ESC + `[0m` + LF + K16; C08 `AKIA%2A%2AIOSFODNN7EXAMPLE`; C09 `AKIA&a**mp;#73;OSFODNN7EXAMPLE` and `AKIA%2<b></b>AIOSFODNN7EXAMPLE`; C10 `AKIA%252AIOSFODNN7EXAMPLE` | learned |
| C07 | measure | card | `akia**iosfodnn7example` (K has one digit from 2-7) | not learned (N1), reported |
| SUM-1..5 | fb | summary | H11, H12a, H14, H16, C06 inputs as a plan input (`canonical_json` writes `\u001b`, `\r`; view a decodes them) | no request saved |
| H40L | fb | summary | H01 as a plan input through `request_approval` with `FakeChannel` | no request saved; one post of `card_withheld_text(run_id)`; run ends `NEEDS_PERSON card_withheld` |
| H32 | fb | model | K2 in lower case | learned (probe: learned) |
| H33a-c | fb | model | `AKIA&amp;IOSFODN27EXAMPLE`; `AKIA.IOSFODN27EXAMPLE`; `AKIA\IOSFODN27EXAMPLE` | learned (probe) |
| H35, H35b | fb | model | `keyz` + K2; `keyz` + K2 + ` here` | learned (probe) |
| GAP-END | fb | model | `x akia.iosfodn27example.com y` | learned (probe) |
| decoy-asia | fb | model | `ASIAQWER` + K2, all lower case | learned (probe) |
| decoy-gap | fb | model | `asia` + `bcdefghjkmnp` + `akia.iosfodn27example` (no digit in the first 20; the real key starts inside it) | learned `AKIAIOSFODN27EXAMPLE` (hand trace: a consuming match takes `asia`...`akia` and skips the real key's start) |
| GLUE-LC | fb | model | K2 in lower case + LF + `aws_secret_access_key=demo` | learned (d_sp; round-8 M1) |
| GLUE-GAP | fb | model | `akia.iosfodn27example` + LF + `next line` | learned (d_sp) |
| H33m | measure | model | H32 and H33a-c written with K | not learned (N1), reported |
| sq-split1, sq-split4 | measure | model | K2 as single characters split by spaces; `AKIA IOSF ODN2 7EXA MPLE`; the same with K | not learned (N2), reported |
| H37d-e | measure | model | H37's shape in lower case; with `.` inserted | not learned (N5), reported |
| FLOOD | fb | model | 17 different made-up keys, each K-shaped from parts and split by `**` | notice, `reason=residue`, map unchanged |
| FLOOD-16 | fb | model | 16 such keys | notice; the map holds all 16 (MAP-1L) |
| MAP-2L | fb | model | FLOOD through `clean` | `LookalikeCopy`; seeded map unchanged |
| POISON | measure | model | a false-learn shape if BS-0 finds one | listed |
**Not learned and not withheld (guard rows; each must give the base output):** `Southeast Asia and Oceania`; `Asia 2024 Q3 revenue growth`; `Eurasia 2025 results`; `Asia-Pacific 2025 results`; `Asia and Oceania markets overview`; `Asia leads 5 new markets signed`; `Malaysia has 5 offices in total`; `Southeast Asia sales rose 4 percent`; `Nakia 3 teams`; `Asia pacific region Q3 2 results`; `asia-markets-rise-3-5-percent`; `asia_region_q3_q2_totals`; `ASIA_SHARD_2_REPLICA_3_PRIMARY` (masked by the plain pattern today); `Asia 2 of 3 are on it so be`; `asia.shard23.example`; `asia.region23q4totalsx.v2`; `akia` + `abcdefghijklmnop`; `asianmarketsq23q4forecast`; `asiapacificregion23q4`; `asiaabcdefghijklm23n8xyz`; `region asiaabcdefghijklm23n_8`; `asiaabcdefghijklm23n-v2`; `Asia` + LF + `abcdefghijklm23n0 end`; **new:** `m33-kill` = `asia abcdefghijklm23n` (one space, then 16 characters with two digits from 2-7); `GLUE-UP` = K + LF + `region=eu` (pass one masks K; the view d match `AKIAIOSFODNN7EXAMPLEregion` contains K and is dropped); `GLUE-EMAIL` = EM + LF + `bar`; `ACC-EMAIL` = `josé@example.org` (pass one masks `s@example.org`; c gives `jose@example.org`, which contains it); `MD-EMAIL` = `**` + EM + `**` (pass one masks EM); a base32 blob of 4,000 characters and a wrapped hex digest from `tools/p1d_corpus.py --seed 1`.
**Measure (over-refusal, reported apart from false learns):** `CMD-1` = a command line `mysql -u app -p` + a made-up password, removed from the card by `withhold_commands`: learning on the raw input finds the password, so the card is withheld although nothing would be shown. Accepted (fail closed, ORDER 180 (3)); BS-3L counts these cards separately.

## Mutation plan (`tests/p1d_learn_mutants.py`; all required; patch point in brackets; numbers kept from P1d so the ledger stays traceable)
| mutant | planted change | killer |
|---|---|---|
| M7 | `_learn_aws` not called [`runmap._learn_unknown`] | H32, H33a-c, H35 |
| M8 | two-digit test removed [`runmap._learn_aws`] | `asia-1d` = `asia.` + `abcdefghijklm3no` (probe: learned under M8) |
| M9 | class `[a-z2-7]` widened to `[a-z0-9]` [`_learn_aws`] | `m9-kill` = `asia` + `bcdefghijk01mn23` (probe) |
| M33 | gap set widened to white space [`_learn_aws`] | `m33-kill` (hand trace: 17 items, length 20, digits 2 and 3) |
| M35 | lookahead made consuming [`_learn_aws`] | `decoy-gap` |
| M43, M44, M45 | right boundary removed; `_`, `-` dropped from it [`_learn_aws`] | `asiaabcdefghijklm23n8xyz`; `region asiaabcdefghijklm23n_8`; `asiaabcdefghijklm23n-v2` (probe) |
| M46 | `P1DL_APPLIED` true while `_learn_unknown` is not called | `test_marker_means_rule_runs` |
| M24 | `find_matches` loop removed [`_learn_unknown`] | H01, H21 |
| M50 | learning reads the post-`neutralise` text [`redact_text`] | H11 |
| M52 | "learned value withholds" removed [`redact_text`] | H14 |
| M54 | `_learn` left on in `card_text` [`channel.card_text`] | `test_card_text_accepts_every_clean_output` plus the BS-0 row, or declared equivalent with the reason |
| M58 | `max_learned_per_call` removed [`redact_text`] | FLOOD |
| M62L | commit of learned values removed [`_withhold`] | FLOOD-16 |
| M68 | containment filter removed [`_learn_unknown`] | GLUE-UP, GLUE-EMAIL, ACC-EMAIL |
| M69 | `_learn_aws` reads d instead of d_sp [`_learn_unknown`] | GLUE-LC |
| M70 | `EMAIL` dropped from `LEARN_KINDS` | H28a |
| M71 | `max_learned_per_call` compared with `>=` | FLOOD-16 |
**Deleted:** M34 (two gap characters allowed): equivalent; with 16 or 17 items and 16 non-gap characters at most one gap can occur, and its rev-1 killer never matched (round-8 M2). `decoy-asia` stays as a learned row; it no longer kills M35, because with the boundary a consuming match also fails at position 0 (round-8 M3).

## Build steps
- **BS-0** (before code, on the post-P1d base): re-run `learn.py` with every row above; the property `"".join(delete_noise(x) for x in lines) == delete_noise(c)` and that `delete_noise` keeps a space (STOP if either fails: back to review); the learning pass on the first 200 corpus documents (any false learn = report to the lead before the build); the H37 prefix; a killer for M54 (else equivalent with the reason).
- **BS-2** (final head): false learns on P1d's BS-1 corpus plus hex digests, UUIDs, base64 blobs, 2,000 lines of code, 100 e-mail lists and the guard rows; reported per kind, per view and per shape; a document in both corpora is listed once. **Gate: 0. If not 0, this package is HELD: exact count and failing shapes to the lead; the client profile stays closed (P1d-gate refuses it without `P1DL_APPLIED`).** 0 of N supports a rate below about 3/N at 95 percent (rule of three), not zero; the report says so.
- **BS-3L:** P1d's BS-3 cards with learning on: false withholds (ceiling 0) and over-refusals of the CMD-1 kind (reported, not gated).
- **BS-4L:** P1d's `tools/p1d_cost.py` with learning on (d_sp is one more view).

## Template fields
- **Package id and name:** P1d-learn, "learn unknown secrets seen only without formatting". Branch `core/P1d-learn`. **Path class:** redaction; result rounds uncapped.
- **Depends on:** P1d merged. **Merge order:** P1d-a, P1d, P1d-learn, P1d-gate (round-8 M5; the gate's C-LEARN and C-AWS canaries need this code).
- **Class (R337):** "an unknown value is matched only in the spelling as written".
- **Files:** change `guard/runmap.py` (`_learn` flag, `_learn_unknown`, `_learn_aws`, `LEARN_KINDS`, `P1DL_APPLIED`), `guard/redact.py` (`find_matches`, `add_known`), `redaction_settings.py` and `defaults.py` (`max_learned_per_call`), `approvals/channel.py` (`card_text` passes `_learn=False`), `CHANGELOG.md`; create `tests/test_p1d_learn_rows.py`, `tests/p1d_learn_mutants.py`; extend `tools/p1d_corpus.py` (`--kind bs2`; `all` then includes it; exit 0 pass, 1 error, 3 = HELD) and P1d's `test_redactor_entry_only_in_runmap` (adds `find_matches`, `add_known`).
- **Interface:** `P1DL_APPLIED: bool`; `redact.find_matches`, `redact.add_known` (used only by `runmap`, AST test); the `_learn` flag is private.
- **Security notes:** no identity or secret; only `AKIAIOSFODNN7EXAMPLE` as a whole-key literal; K2 and EM built from parts; learned values are withheld, never logged.
- **Rollback:** tag `pre-P1d-learn`; removing it drops the marker, which closes the client profile again.
- **Reviewers:** fresh `egm-design` + `egm-implementation-readiness`, given the diff, this ticket and the evidence only.
- **Done =** BS-2 = 0; a fresh result round finds no blocker or major; all gates green; ledger row BL-core-p1d-008 FIXED-VERIFIED and the learning part of BL-core-p1d-001 (rows above) verified; the lead merges.

## Evidence commands
As P1d's list (copied from `ci.yml`), with `tests/test_p1d_learn_rows.py`, `tests/p1d_learn_mutants.py` and `tools/p1d_corpus.py --seed 1 --kind bs2`; raw output to `handover/evidence/P1d-learn/evidence-<n>.md`.

## Owner-facing wording
CHANGELOG: "A password, key or e-mail address that the software has not seen before is now also hidden when formatting characters inside it (bold markers, a terminal colour code, a backspace, an accent mark, look-alike letters, a line break) are what kept it from being recognised: the whole text is held back. Keys that start with AKIA or ASIA are also hidden when written in small letters or with one extra `&`, `.` or `\` inside, if the key holds at least two of the digits 2 to 7. Not covered: such a key with fewer than two of those digits, split by a space, `_`, `-`, `/` or two extra characters, in small letters and split, or followed directly by more letters or digits; other key kinds in small letters; a host name split by formatting. A command that the card already hides may still cause the card to be held back."

## Ledger rows
BL-core-p1d-008 (MAJOR, lower-case, dotted or `&`-inserted unknown AWS-style key, H32, H33, H35) closes here. The learning rows of BL-core-p1d-001 (H01, H02, H11-H16c, H18, H21, H28, H31, H37, C01-C10, SUM, H40L) are verified here; P1d verifies the known-value rows.

## Revision log
Rev 1 (2026-11-09): split from P1d rev 7 (ORDER 177); round-7 G1 (right boundary, M43-M45, N4); M46. **Rev 2 (2026-11-09):** ORDER 180 (2): every learning pass moved here (from P1d rev 8: `_learn_unknown`, `find_matches`, `add_known`, `_learn`, `max_learned_per_call`, rows H01-H31, H37, C01-C10, SUM, H40L, FLOOD, POISON, mutants M24, M50, M52, M54, M58, M62L, BS-2 whole); `round8-resolve.md` applied: d_sp for the AWS rule plus GLUE rows (M1); M34 deleted as equivalent, `count <= 1` deleted, `m33-kill` (M2); `decoy-gap` kills M35 (M3); EMAIL in the learning kinds, H28 here, host name a non-goal (M4); merge order before P1d-gate (M5); containment filter, M68-M71 (found in resolve); base32 claim UNVERIFIED; digit wording (N6).
