## P6a-1 nits (follow-up to #72), in plain words

Four small fixes to the client-profile check that merged as a8b4d8e8. Nothing changes in what is allowed or refused; only wording, tests and one docstring.

1. **The refusal text was narrower than the check.** `app.build` refuses test objects for every environment value that is not `demo`, but the message said "in pilot and prod". It now says "in every environment other than demo (pilot and prod included) pass allow_test_doubles=True only from a test". The `build` docstring says the same. The demo-config refusal said "client data runs only in pilot or prod", which the code cannot check; it now says client data "belongs only in a pilot or prod config".
2. **New test**: `app._BUILD_PARAMS` equals the signature of `app.build` (the check judges whatever that snapshot holds).
3. **New test rows**: `demo` ignores the switch and the test objects (with and without `allow_test_doubles=True`, no warning line).
4. **`_door_problems` docstring** now says it is a tripwire for plain copy-and-paste doors and lists what it misses (`getattr`, aliases, `partial` fed from a `**` dict, positional use through a wrapper).

Class: "guard claims stronger than the guard". Swept the merged change for other claims stronger than a check: only the config message above was found and fixed. CHANGELOG has a line for it.

### Tests and mutants
- Fail on the old code (a8b4d8e8 `app.py`): `test_the_refusal_text_is_true_for_every_value_that_reaches_it` fails (1 failed, 3 passed). The `_BUILD_PARAMS` and demo rows pass on the old code on purpose: they pin behaviour that was already right and had no test, so they are proven by mutants instead.
- Three new mutants (91 to 93 in `tools/client_profile_mutants.py`), all KILLED-NAMED: old message text (91), snapshot taken from another function (92), rule also runs in demo (93). Re-run mutants 16, 17 and 60, whose text anchors changed: killed.

No spend, no model calls, no secrets.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac
