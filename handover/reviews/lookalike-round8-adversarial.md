# Look-alike design, round 8, adversarial review (draft 8)

Status: REPORTED (complete; saved by the lead session from the reviewer's hand-back, which is model output, not user authority). The container restarted after the hand-back; the text was recovered from the agent transcript.
Target: `designs/lookalike-leak.md` draft 8 (head `2ca11dd`). Reviewer: `egm:egm-design`, read-only. Did not open `reviews/`. Did not read `tickets/P1.md` or `tickets/P2d.md`; ran nothing. All traces are the reviewer's hand traces and UNVERIFIED.

Verdict: not clean. There is 1 Blocker, 3 Majors, and a few Nits. The counts all check out.

## BLOCKER

**B-1. The explained count `e` includes needle forms (keys of `undo(original)`), but the put-back text is the original as written. Any placeholder of V then cancels one leaked decoded-form copy of V.**
- Scope: section 5 items 1 and 3. The text says `e` is "the largest `count(k)` over O's own keys, needle forms included".
- Scenario with no planting:
  - V is a made-up secret of 13 or more characters that holds an escape sequence, for example a URL-safe token with `%3D` or `%2B`, or one with `&not`. Then `undo(V)` differs from V.
  - The needle set holds key(V) and k' = key(undo(V)).
  - The text holds V's plain placeholder, which is legitimate and masked. It also holds a copy of V in decoded form (`=` in place of `%3D`), or a Cyrillic copy of the decoded form.
  - Written form: the put-back V contributes 0 to the count of k', because the written V holds `3D`, not the decoded letters. The leaked copy gives `c(k') = 1`.
  - But `e(k')` = 1 × (largest count of k' over V's keys). The needle-form key holds k' once, so `e = 1`.
  - Result: `c <= e`, the text is PASSED, and the decoded-form copy of V goes to the model.
- The same cancellation works across values. Another map entry O whose `undo(O)` holds V twice (for example O learned as a percent-encoded blob, or one planted with `password=<pct-encoded VV>`) gives each of its placeholders a free leaked copy of V.
- The row LK-ENT-VAL tests the needle form only with no placeholder of V present. FR-2 and FR-37 never use a value with `undo(O) != O`. GOLD-1 never builds such a value. Nothing kills this.
- Fix: compute `e` per form from the same text that was put back.
  - In the written form, use only the keys of O as written.
  - In the undone form, put back `undo(O)` and use its keys.
  - Or drop needle forms from `e` and let the put-back text carry its own count.
  - Add row LK-ENT-VAL-PH (V with an escape in it, V's placeholder next to a decoded copy: refused), a cross-value variant, and a mutant "`e` counts needle forms of the wrong form".

## MAJOR

**M-1. `e` takes the largest count over an original's keys. This is a second overcount, and it is buildable.**
- Scope: section 5 item 3 ("none is known").
- Scenario: V holds both `h` and `n`.
  - X is a planted or stored value with capital Eta (U+0397) at V's `h` positions. Under one case reading X reads as V twice. Under the other reading it holds no V.
  - The leaked copy writes only V's `n` as Eta, so it is found only in the other reading's key.
  - In that reading, `c = 1` and `e = 2` (the maximum over X's keys), so it passes.
- Fix: use the count of the same reading, or the minimum over O's keys. The cost is a false refusal only for case-ambiguous letters. Add a row.

**M-2. LK-ENT-AMP is understated and probably cheap to close.**
- Scope: section 4 and the strict-xfail list (row text says "starting with"; section 10 says "(or holding)").
- Any V that holds one of the 106 no-semicolon entity names is affected, and that includes the 2-letter names `lt` and `gt` and the upper-case names. The leaker writes `&` before the entity-encoded first letter at any position of V.
- The share of random alphanumeric secrets of 16 or more characters that hold such a pair is a few percent (my arithmetic, not run).
- Cheap closure, unmeasured: in the check only, a pre-pass that drops every `&` not followed by `[#\w]+;` before `undo` (or before one extra form). The design rejects one `scan_keyset` call per `undo` round as too costly. It never prices this single pre-pass.
- At minimum, the row and the CHANGELOG must say "holding", not "starting with".

**M-3. FR-21 and FR-34 pin a leak as a pass, and their reason does not match what the model sees.**
- Scope: section 5 item 3 and FR-21.
- A copy `head` + e-mail + `tail` goes out as `head <EMAIL_1> tail`. The model sees a token, not letters, so it can recombine V trivially. The text calls this "like any copy with letters inserted". That is true of key matching but not of what is sent.
- The same applies to a genuine token the author places mid-copy on any unescaped path (document, tool inputs).
- This is outside the lead's table. But it is the case draft 7's join covered, and it is now a strict "NOT refused" test.
- Recommend one of three: state it in the CHANGELOG as a known leak; make FR-21 a strict xfail; or add a third form with placeholders removed, for the one case where a put-back original is not itself a checked value. Cost and benefit are the lead's call.

## NIT

- N-1. GOLD-1 shares `scan_keyset`, so P1 blind spots (Be, Eta, strokes) are invisible to it by design. It also builds one known value and one transformation per run. It cannot hit B-1, M-1 or overlapping known values, or a copy plus a legitimate masked occurrence of V. So it can pass while B-1 leaks. Add a generator mode with 2 to 3 related known values, with and without a placeholder next to the copy.
- N-2. FR-8, FR-14 and FR-22 are timing assertions on shared machines and may be flaky. M39 (module-level memo) is behaviourally equivalent and killed only by a state introspection, so its row LK-NOCACHE must assert on module state.
- N-3. FR-35 is a cheap availability attack (placeholders of long originals expand under the count form). `redact_many` now raises on a batch over the cap even when no known value exists. That is a behaviour change for Warden, and the Warden ticket does name it.
- N-4. A copy split across two JSON leaves or two fields is "not read" (section 10). Fields are a more natural split than texts, so say so in the CHANGELOG line.
- N-5. Identifier kinds (UUID and similar) use the standalone rule, so a plain copy glued to `_` or letters, as in the k8s log case the sweep's own comment cites, is refused benignly. This is covered by FR-11 and measured by P-1.

## Items attacked that held

- **ADV-LK7-1 split-around-a-masked-piece**: still refused (c=1, e=0).
- **A copy plus a legitimate occurrence**: refused, as the put-back text contributes to `c` equally. This is sound for plain originals.
- **Two overlapping known values**: refused or passed correctly in my traces.
- **Piece entries from `_place`**: a masked piece does not hold k, so the text is refused.
- **Secrets are swept as `_EVERY_COPY`**, so "plain copies of 8-11 character secrets are masked" is accurate.
- **A V masked whole as a new value** is explained correctly.
- **Case, width, zero-width, combining, line-break and tag interleave**: these rest on `scan_keyset`, which I did not re-run.
- **The limits statements** (encoded copies caught by nothing; 8-11 character secrets only plain copies) are accurate and not over-claimed. The tag-spelled V in LK-TAG is consistent with the invisible-bits statement.

## Counts: recounted, all correct

- LK ids: 42 table lines (lines 79-120), plus 2 extra ids on the LK-UP/LOW/TITLE line and 2 on the HANDED line = 46, plus GOLD-1.
- Strict xfail always: 9 (INERT, SHORT, BE, LATIN, ETA2, LATER, STROKE, ENT-AMP, ENC).
- FR rows: 37 (counting 6a, 6b, 6c separately).
- Mutants: M1 to M56 plus M9b, M18b and M18c = 59 names.
- Deleted: 22 = M6, M40, M11, M12, M45, M46, plus 16 earlier (M5, M30, M36-M38, M9b, M15, M18, M19, M21, M22, M25, M28, M29, M31, M33).
- Live: 37 (35 in P2d-2 plus M41 and M44 in P2d-2b).
- PL-LK 1-46 is consistent.
- Per-row killers are right for the mutants I checked: M1-M4, M7, M8, M10, M13, M14, M17, M18b, M18c, M20, M24, M26, M27, M32, M34, M35, M42, M43, M48-M56. M3 is killed by LK-PCT and M52 by LK-PH-UNDO. No row kills the B-1 or M-1 mutants, because the mutants and rows do not exist yet.

## Strict xfails closable cheaply

- LK-STROKE: yes, by the generator rule in P1 (section 8).
- LK-ENT-AMP: probably, see M-2.
- LK-ETA2, LK-BE, LK-LATIN: not cheaply; they are P1 class maps.