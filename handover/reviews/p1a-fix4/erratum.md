# Erratum to ticket P1 (finding BL-hadavin-sdk-p1a-017), written by the P1a builder at fix4

This file is the text the lead puts into `handover/tickets/P1.md` (the builder does not edit the handover repo).

## What is wrong in ticket P1 (revision 16)

Ticket P1 still names the P1b scan function `scan_keyset` (67 places in the file), keeps `fold_key` as an alias of `identity_key`, and says that
P1b "widens `same_person`". The P1a code (PR 63) has shipped different names since fold4:

| Ticket P1 says | P1a code says (final, fix4) |
|---|---|
| `scan_keyset` (P1b) | `identity_keys` (the spelling variants of a name, for a DENY decision), `fold_views` and `squeeze_views` (the views a scan looks through) |
| `fold_key` is an alias of `identity_key` | `fold_key` is deleted; use `identity_key` |
| `same_person` | `could_be_same_person` (already built on all spelling variants in P1a, not widened in P1b) |
| `check_pinned_unidata(strict=...)` (warn or raise) | `require_pinned_unidata()` only; it raises `UnidataMismatch`; the warn-only path is deleted (no caller in P1a, none in the `core/P1b` branch except its own tests) |
| (not named) | `key_tag()` returns the tag that an unpinned interpreter puts in front of every check name |

So the P1a names `identity_keys`, `fold_views`, `squeeze_views`, `key_tag` and `require_pinned_unidata` SUPERSEDE `scan_keyset` wherever the
ticket uses it.

## The final public names of `hadavin_sdk.guard.textnorm` (20)

Computed from `textnorm.__all__` after the fix4 changes. The order said 22; 22 is the count of `__all__` at 68efd66 (before fix4). Fix4 removes
`fold_key`, `check_pinned_unidata` and `same_person` and adds `could_be_same_person`, so 22 - 3 + 1 = 20:

1. `FILLERS`
2. `FOLD_VERSION`
3. `AllowVerdict`
4. `NotText`
5. `TextTooLong`
6. `TextnormError`
7. `UnidataMismatch`
8. `allow_equal`
9. `could_be_same_person`
10. `fold`
11. `fold_views`
12. `has_hidden_channel`
13. `has_mixed_script`
14. `identity_key`
15. `identity_keys`
16. `key_tag`
17. `names_equal`
18. `require_pinned_unidata`
19. `squeeze`
20. `squeeze_views`


## The changed P1b scope sentence

Replace, in the "P1m / P1a / P1b" scope line of ticket P1 (line 23), the P1b part

> **P1b**: gaps 1-5 (...), the DENY keys (`scan_keyset` and its contract), `same_person` widened.

with

> **P1b**: gaps 1-5 (gap 7, both halves, is cut to v1.1: no decoder runs in any view), the DENY scans that use the P1a views (`fold_views` AND
> `squeeze_views`, both on every scan; an empty view is refused), the DENY name test `could_be_same_person` (renamed from `same_person` after P1b
> merges P1a fix4), and `require_pinned_unidata()` called in `app.build` (production and pilot run Python 3.13.x, Unicode 15.1.0).

and replace every other `scan_keyset` in the ticket (the rows of the views list, the P1b contract, the mutant lists) with "the P1a views
(`fold_views` and `squeeze_views`) and the P1a spelling variants (`identity_keys`)", and every `fold_key` with `identity_key`.
