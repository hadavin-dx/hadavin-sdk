# PD part 6 round 7, design reviewer, head 41c84695 (condensed from the inline report; code read only, nothing run)

Verdict: 0 Blocker, 3 Major, 5 Minor/Nit. Not a clean round.

Round 6 fixed at the choke point: first-byte kinds (MAGIC_KINDS with Mach-O and PE), the _collection helper, _stat_kind, git user-excludes override, page failed-write repair and code-point length.

## Major
1. `overridden` fails open when the caller does not go through build's own App. mode_banner.py 648-669 (`overridden=()` default), app.py 63-70 (default `()`), CHANGELOG.md 214. "Not given" and "not recorded" are the same value. Failing inputs: App built directly with a real kubernetes source gives tone demo and "made-up"; dataclasses.replace(app, llm=real) keeps the old overridden; app.llm set after build. Test at tests/test_mode_banner.py 1907 covers only build(...). Fix: unrecorded value None (unknown, banner unconfirmed), build sets () explicitly; banner_or_unconfirmed and banner_from_config refuse a demo banner unless the caller states overridden, or the docs lead with App.mode_banner() as the only supported call.
2. `_given_overrides` checks only six hand-listed build keywords; hold_run_ids (and clock) are left out; a new build parameter is silently not recorded. Fix: record hold_run_ids, or a test comparing inspect.signature(build) with OVERRIDES plus an explicit not-connectivity list.
3. Mutant table fix only partly done: B13 and B54 still expect Python's own crash text; J23 not split into tag and text and still expects the 6-character "tag = "; the table test misses fragments like "tag = "; six SAME_ASSERT groups remain with unchecked free-text reasons. Fix: split J23, own message for B13/B54, table test rejects crash rows whose expect is the interpreter's message.

## Minor / Nit
4. tools/demo_only_guard.py 645-654 `_link_stays_in_copy` uses normpath: two tracked links (dir/k -> .., dir/l -> k/../../outside) pass and the copy run can read outside the copy. CHANGELOG claim is false. Also line 661 O_NOFOLLOW only on the last component and silently 0 where missing.
5. Seven new tests pass on old code; comments at tests/test_mode_banner.py 1769, 1793, 1807 overclaim; line 1915 imports tests.test_k3_pilot for SECRETS (fragile under the copy run).
6. Public demo itself loses its made-up banner when it builds with fakes (stated decision; CHANGELOG should say so).
7. ModeBanner docstring (167-170) stale; mode_banner.js 61-64 paints any text that starts with the not-confirmed words; overridden_note not validated to hold {names}; strip versus trim differ; Mach-O universal CAFEBABE magic not listed.
8. core.excludesFile=/dev/null accepted (Nit).
