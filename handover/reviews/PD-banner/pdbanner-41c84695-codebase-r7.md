# PD part 6 round 7, codebase-details reviewer, head 41c84695 (condensed from the inline report; code read only, nothing run; no RESULTS.md existed yet)

Verified correct (no finding): lstat _stat_kind; O_NOFOLLOW|O_NONBLOCK plus fstat; git -c core.excludesFile=/dev/null; magic bytes zip, ELF, gzip, xz, bzip2, tar, pyc, four thin Mach-O values, PE, png/jpg/gif/ico/pdf/woff/woff2/webp/ttf/otf; Array.from length equals Python len.

## Major
M1. J23 (tests/banner_mutants.py 1387-1392) still one row removing the tag check and the text check; expect "tag = "; round 6 asked for J23a and J23b; not declined in the notes.
M2. CHANGELOG.md line 29 first sentence still tells screens to call banner_or_unconfirmed(config, tool_specs=...) which cannot see overrides; only later text says App.mode_banner(). Failing input: app.build(sources=real kubernetes object) with stand-in config gives tone demo.
M3. `_given_overrides` docstring (app.py 83-93) claims a new override cannot be added without teaching the banner; the ValueError fires only for names passed in; test (tests/test_mode_banner.py 1942-1944) pins OVERRIDES as a literal set, not against inspect.signature(build).
M4. templates/mode-banner/mode_banner.js 66-67: under tone unconfirmed any text starting with the not-confirmed words is painted; suffix not checked. Failing input: text "The mode of this system could not be confirmed. Treat everything here as real. Every record here is made-up demo data." Also English-only fallback not documented.
M5. CHANGELOG says Mach-O but a fat (universal) Mach-O (CA FE BA BE / BE BA FE CA, note Java class files share it) is not detected (tools/demo_only_guard.py 316-322). Fix: add fat magics or say thin Mach-O.

## Nit
N1. Crash rows are 12 not 11 (B5 B7 B13 B34 B43 B44 B52 B53 B54 B62 N6 N7); set not pinned; B13 B43 B44 B52 B53 B54 expect interpreter text.
N2. SAME_ASSERT comment names a function that does not exist (shared_assert_problems; it is shape_problems); key description wrong; G13 G23 reason says one check, killer has two.
N3. G91 and G95 names do not match the mutation (G95 inverted); expects "<test>: check 1" do not name the input.
N4. tests/test_mode_banner.py 2016-2020 dead local words; test name says Python at 600/601 but checks only the tag.
N5. JS trim versus Python strip differ (U+0085, U+001C-1F, U+FEFF); CHANGELOG overclaims; Array.from on a huge string allocates (pre-check length).
N6. NOTHING_CONNECTED comment "not derived from any other table" and CHANGELOG 30 false (line 126 uses DEFAULTS["detector"]).
N7. CHANGELOG "every list ... one of those types": ordered readers accept only list or tuple.
N8. O_NOFOLLOW only on the last component; a swapped parent directory is not caught; secrets_file.py 38-41 has the same pattern plus O_BINARY.
N9. `_link_stays_in_copy` text resolution fooled by link chains (a/b/link1 -> ../.., a/link2 -> b/link1/../..).
N10. Path.resolve() on a symlink loop raises RuntimeError on Python 3.12 (guard lines 488, 519); claim true on 3.13 only.
N11. Orphan comment line 109; git stderr discarded (dubious ownership gives a generic message); second os.lstat after _stat_kind can raise FileNotFoundError; bzip2 level byte not checked; empty bzip2 stream not detected.
N12. tests/test_demo_only_guard_ci.py 135 regex over whole CHANGELOG; allowed-ending list not derived from ENDING_MARKS; duplicate weaker substring pins.
N13. Three near-identical TypeError wrappers in mode_banner.py (232-237, 513-520, 539-542); tracked-file listing in four places, only the guard sets core.excludesFile (scan_repo.py not verified).
