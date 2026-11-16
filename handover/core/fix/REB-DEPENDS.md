# DEPENDS: what of core-fix-v2 depends on the real-run patches, and what was done about it

Facts checked on copies of the frozen tree (repo2 untouched):
- `git apply --check` of `real-run-fixes-v6-after-sonar-p3-final.patch` on the FROZEN tree: code files apply, the two docs files (`docs/real-services.md`, `docs/settings.md`) do not. `desk-address-required-v6.patch`: code applies, `contract.md` and `docs/settings.md` do not. `survivor-tests-v1.patch`: applies after the other two. So the frozen scripts are the version the real-run patch was written for.
- core-fix-v2 does NOT apply to frozen because (1) the frozen series changed lines our hunks touch (resolved by hand, see HUNKS.md) and (2) three files it edits are created only by the real-run patches.

## Dropped from core-fix-on-frozen (needs the real-run patches first), nothing silently lost
All three hunks sets are saved verbatim in `ontop-3files.patch` (v2's own hunks). They apply cleanly on frozen + real-run + desk-address + survivor (checked: `git apply --check` exit 0 on that scratch tree).
| v2 hunks | why they need the real-run patches | what is lost on the frozen-only tree |
|---|---|---|
| scripts/precheck.py (2 hunks: `TypeError` tolerance, new `folder_cannot_be_made`) | the file is created by real-run-fixes-v6 | nothing: the frozen scripts have no precheck; the same `folder_cannot_be_made` check lives inside `scripts/run_real_check.py` in core-fix-on-frozen |
| tests/test_core_key_readers.py (2 hunks: a live key over the size limit is refused) | file created by real-run-fixes-v6 | the size limit itself IS in core-fix-on-frozen (`live_claude._read_key`, tested by `test_the_live_key_file_has_the_same_size_limit_as_the_other_key_readers` in test_cli_refusals.py); only the generated 1512-file comparison is not there |
| tests/test_survivor_r20_config_read.py (2 hunks: stand-in for the config reader is now `lead_desk.regfile.open_regular`) | file created by survivor-tests-v1 | the config file read through `regfile` is tested by `test_run_real_check_config_that_is_a_pipe_is_refused_not_waited_for` |

## Ported in a smaller form (so core-fix-on-frozen stands alone)
- `scripts/run_live_check.py` (frozen = pre-real-run): refusing parser, fixed type texts, price date / effort word / empty value / same model twice checks, ledger line without the class name. NOT ported (flags that exist only in the real-run version): `--leads/--runs` range limits, required `--base-url`, `--assume-yes`, the terminal guard.
- `scripts/run_real_check.py`: refusing parser, `option_problem` for the two dry-run options, config read through `regfile`, run folder check before the question (one line, exit 2).
- Test changes forced by that: see HUNKS.md, section TESTS (five tests dropped or adapted, each named).

## Known collisions when the real-run patches are applied AFTER core-fix-on-frozen (checked with `git apply --check` on a scratch copy of the rebased tree)
`scripts/run_live_check.py`, `scripts/run_real_check.py` and `src/lead_desk/live_claude.py` (`_read_key`) conflict: the real-run patch edits the same lines our port edits. The other 20 code files of the real-run patch apply. No reconciling patch (`realrun-on-corefix.patch`) was built: that is the lead's step when the real-run patches go on top. Hint: for these three files take the tree-EV text (real-run + v2 already merged) and add the three on-top files from `ontop-3files.patch`.
