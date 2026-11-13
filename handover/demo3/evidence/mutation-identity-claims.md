# Mutation check: identity.py and claim logic (EVIDENCE RUNNER Q8b)

Base: public main f3c39cf89ec989f032ea48a23cfd824b88da9c68, private worktree /home/user/work/q8b-base; script tools/q8b_mutate.py; raw logs raw/q8b-results.jsonl (per-mutant logs in /home/user/work/q8b-logs/). Run 12:55Z-13:26Z, 1 core, no INVALID mutants, worktree `git status --short` empty at the end.

Main test set (baseline 125 tests pass): test_flow, test_claim_ownership, test_claim_checks_and_crm_mode, test_ai_after_claim, test_input_edge_cases, test_mutants, test_mutants_more, test_sonar_p2_choke_points, test_followup_edge_cases. Wider set (survivors only): test_http, test_desk_edge_cases, test_desk_http_edge_cases. `-x` stops at first failure.

Claim logic = desk.py `_decide_once`, `_process`, `_verdict_reply`, `_CLAIM_SQL`, `_claim`, `_take_token`, `_pending_or_failed` (db.py holds no decision code; the unique index on leads.email_key is in schema.sql).

## Scores
- identity.py: 20 valid; killed by main set 14/20 (70%); 15/20 (75%) after the wider set (I16 killed there).
- desk.py claim logic: 20 valid; killed by main set 16/20 (80%); 17/20 (85%) after the wider set (C13 killed there).


## Survivors after BOTH sets (verbatim) - 8

| id | file | change | guess |
|---|---|---|---|
| I03 | src/lead_desk/identity.py | `return s.strip().lower()` -> `return s.strip().casefold()` | REAL GAP: `.casefold()` merges two different mailboxes (e.g. German sharp s vs ss); no test of case-folding beyond ASCII/Kelvin. |
| I04 | src/lead_desk/identity.py | `return s.strip().lower()` -> `return unicodedata.normalize("NFKC", s.strip().lower())` | REAL GAP: NFKC would merge compatibility forms (full-width letters); no test that the key is NOT Unicode-normalised. |
| I06 | src/lead_desk/identity.py | `and len(e) <= EMAIL_MAX` -> `and len(e) < EMAIL_MAX` | REAL GAP: off-by-one at exactly EMAIL_MAX (254) characters is untested (only the over-long lowercase case is). |
| I11 | src/lead_desk/identity.py | `if limit is not None and len(t) > limit:` -> `if limit is not None and len(t) >= limit:` | REAL GAP: boundary of the field length limits (exactly NAME_MAX etc. must pass) is untested. |
| I12 | src/lead_desk/identity.py | `if limit is not None and len(t) > limit:` -> `if limit is not None and len(v) > limit:` | REAL GAP: length is measured after strip; a value of limit chars plus spaces must pass and is untested. |
| C03 | src/lead_desk/desk.py | `if rec["outcome"] is not None:  # another request or a restart finished it: nothing to wri` -> `if False:                 return rec, False` | LIKELY real gap, hard to reach: the write-once guard inside the verdict transaction (a second decider overwriting `new` with `duplicate`); the earlier check in `_process` hides it in single-thread tests. |
| C18 | src/lead_desk/desk.py | `auto_attempts=CASE WHEN state='failed' THEN 1 ELSE auto_attempts+1 END, updated_at=?"     ` -> `auto_attempts=auto_attempts+1, updated_at=?"         " WHERE lead_id=? AND state = 'pendin` | EQUIVALENT: the WHERE clause allows only state='pending', so the `CASE WHEN state='failed'` branch of the pending-only claim never runs. |
| C19 | src/lead_desk/desk.py | `if held is not None and held[0] == lead_id:` -> `if held is not None:` | WEAK GAP: token of another lead accepted; the fallback reads the same attempts value in normal single-claim flows, so only an interleaved claim of two leads on one thread would show it. |

## Survived the main set but killed by the wider set

- I16 src/lead_desk/identity.py: `if has_control_char(v, _CONTROL_OK_IN_MESSAGE if field == "message" else frozenset()):` -> `if has_control_char(v, _CONTROL_OK_IN_MESSAGE):` ; killed: FAILED tests/test_desk_edge_cases.py::test_tab_newline_only_in_message - KeyE...
- C13 src/lead_desk/desk.py: `" WHERE lead_id=? AND state = 'pending'"` -> `" WHERE lead_id=?"` ; killed: FAILED tests/test_desk_http_edge_cases.py::test_only_person_takes_failed - As...

## All mutants

| id | file | change (old -> new) | result | killed by |
|---|---|---|---|---|
| I01 | identity.py | `s.strip().lower()` -> `s.lower()` | KILLED | tests/test_mutants_more.py::test_email_key_strips_blanks - AssertionEr... |
| I02 | identity.py | `s.strip().lower()` -> `s.strip()` | KILLED | tests/test_flow.py::test_cross_source_dupe - AssertionError: leads == ... |
| I03 | identity.py | `return s.strip().lower()` -> `return s.strip().casefold()` | SURVIVED | passed |
| I04 | identity.py | `return s.strip().lower()` -> `return unicodedata.normalize("NFKC", s.strip().lower())` | SURVIVED | passed |
| I05 | identity.py | `return not any(not c.isascii() and any(x.isascii() for x in c.lower())` -> `return True` | KILLED | tests/test_followup_edge_cases.py::test_a_letter_that_lower_cases_to_ascii_is_refused[\u21 |
| I06 | identity.py | `and len(e) <= EMAIL_MAX` -> `and len(e) < EMAIL_MAX` | SURVIVED | passed |
| I07 | identity.py | `and len(normalise_email(e)) <= EMAIL_MAX` -> `and True` | KILLED | tests/test_input_edge_cases.py::test_long_lowercase_email_is_review - ... |
| I08 | identity.py | `and _EMAIL_RE.fullmatch(e) is not None` -> `and True` | KILLED | tests/test_flow.py::test_incomplete_to_review - KeyError: 'reason' |
| I09 | identity.py | `and not e.endswith(".")` -> `and True` | KILLED | tests/test_flow.py::test_incomplete_to_review - KeyError: 'reason' |
| I10 | identity.py | `and not any(unicodedata.category(c).startswith("C") for c in e)` -> `and True` | KILLED | tests/test_flow.py::test_incomplete_to_review - KeyError: 'reason' |
| I11 | identity.py | `if limit is not None and len(t) > limit:` -> `if limit is not None and len(t) >= limit:` | SURVIVED | passed |
| I12 | identity.py | `if limit is not None and len(t) > limit:` -> `if limit is not None and len(v) > limit:` | SURVIVED | passed |
| I13 | identity.py | `t = v.strip()` -> `t = v` | KILLED | tests/test_flow.py::test_cross_source_dupe - AssertionError: assert 20... |
| I14 | identity.py | `vals[field] = t or None` -> `vals[field] = t` | KILLED | tests/test_flow.py::test_incomplete_to_review - AssertionError: blank ... |
| I15 | identity.py | `if field != "email" and has_invisible_format(v, field == "message"):` -> `if field != "email" and has_invisible_format(v, True):` | KILLED | tests/test_followup_edge_cases.py::test_invisible_characters_in_short_fields_are_refused[\ |
| I16 | identity.py | `if has_control_char(v, _CONTROL_OK_IN_MESSAGE if field == "message" el` -> `if has_control_char(v, _CONTROL_OK_IN_MESSAGE):` | SURVIVED | wider: tests/test_desk_edge_cases.py::test_tab_newline_only_in_message - KeyE... |
| I17 | identity.py | `missing = [f for f in ("name", "email") if vals[f] is None]` -> `missing = [f for f in ("name",) if vals[f] is None]` | KILLED | tests/test_flow.py::test_replay_same_source_ref - AssertionError: asse... |
| I18 | identity.py | `b = _collapse(new.get(f))         if b and b != _collapse(stored.get(f` -> `b = _collapse(new.get(f))         if b != _collapse(stored.get(f)):` | KILLED | tests/test_flow.py::test_dupe_diff_first_untouched - AssertionError: a... |
| I19 | identity.py | `return re.sub(" +", " ", (s or "").strip())` -> `return (s or "").strip()` | KILLED | tests/test_flow.py::test_dupe_diff_first_untouched - AssertionError: a... |
| I20 | identity.py | `if not encodable(v):` -> `if False:` | KILLED | tests/test_input_edge_cases.py::test_lone_surrogate_is_review - Assert... |
| C01 | desk.py | `existing = self._lookup_email_key(conn, chk.email_key)` -> `existing = self._lookup_email_key(conn, chk.email)` | KILLED | tests/test_flow.py::test_cross_source_dupe - AssertionError: assert 20... |
| C02 | desk.py | `if existing is not None:                     row = conn.execute(` -> `if False:                     row = conn.execute(` | KILLED | tests/test_flow.py::test_cross_source_dupe - AssertionError: assert 20... |
| C03 | desk.py | `if rec["outcome"] is not None:  # another request or a restart finishe` -> `if False:                 return rec, False` | SURVIVED | passed |
| C04 | desk.py | `"UPDATE receipts SET outcome='duplicate', outcome_lead_id=?, differing` -> `"UPDATE receipts SET outcome='new', outcome_lead_id=?, differing_field` | KILLED | tests/test_flow.py::test_cross_source_dupe - AssertionError: assert 20... |
| C05 | desk.py | `" ON CONFLICT(source, source_ref) DO UPDATE SET attempts = attempts + ` -> `" ON CONFLICT(source, source_ref) DO UPDATE SET attempts = attempts"` | KILLED | tests/test_flow.py::test_replay_same_source_ref - assert 1 == 22 |
| C06 | desk.py | `return int(found[0]), found[1] == 1` -> `return int(found[0]), found[1] != 1` | KILLED | tests/test_flow.py::test_crash_resume_each_point[A-keyed-keyed] - Fail... |
| C07 | desk.py | `matches = rec["payload"] == canon` -> `matches = True` | KILLED | tests/test_flow.py::test_replay_same_source_ref - assert True is False |
| C08 | desk.py | `elif not matches:                 self._note_payload_conflict(rid)` -> `elif matches:                 self._note_payload_conflict(rid)` | KILLED | tests/test_claim_ownership.py::test_overlap_gives_one_review_item - as... |
| C09 | desk.py | `if rec["outcome"] is not None:                 return self._verdict_re` -> `rec, decided_here` | KILLED | tests/test_mutants.py::test_mutant_replay[_process-(if rec\\["outcome"\\] is not None[:]\\ |
| C10 | desk.py | `if not decided_here:                 return self._verdict_reply(rec, T` -> `if False:                 return self._verdict_reply(rec, True, matche` | KILLED | tests/test_flow.py::test_concurrent_same_source_ref - assert [False, F... |
| C11 | desk.py | `return self._verdict_reply(rec, False, None)         except Exception` -> `return self._verdict_reply(rec, True, None)         except Exception` | KILLED | tests/test_flow.py::test_cross_source_dupe - assert True is False |
| C12 | desk.py | `if not replayed:                 drive = rec["outcome_lead_id"]` -> `if replayed:                 drive = rec["outcome_lead_id"]` | KILLED | tests/test_flow.py::test_replay_same_source_ref - AssertionError: asse... |
| C13 | desk.py | `" WHERE lead_id=? AND state = 'pending'"` -> `" WHERE lead_id=?"` | SURVIVED | wider: tests/test_desk_http_edge_cases.py::test_only_person_takes_failed - As... |
| C14 | desk.py | `" WHERE lead_id=? AND state IN ('pending','failed')"` -> `" WHERE lead_id=? AND state IN ('pending','failed','sending')"` | KILLED | tests/test_mutants.py::test_mutant_claim_no_rowcount - Failed: DID NOT... |
| C15 | desk.py | `if conn.execute(sql, (self._now(), lead_id)).rowcount != 1:` -> `if conn.execute(sql, (self._now(), lead_id)).rowcount < 1:` | KILLED | tests/test_mutants.py::test_mutant_claim_no_rowcount - AssertionError:... |
| C16 | desk.py | `self._local.token = (lead_id, int(got[0]))  # the ownership token` -> `self._local.token = (lead_id, int(got[0]) + 1)  # the ownership token` | KILLED | tests/test_flow.py::test_cross_source_dupe - AssertionError: assert 0 ... |
| C17 | desk.py | `return False                 got = conn.execute("SELECT attempts FROM ` -> `return True                 got = conn.execute("SELECT attempts FROM f` | KILLED | tests/test_flow.py::test_unknown_blind - KeyError: 'error' |
| C18 | desk.py | `auto_attempts=CASE WHEN state='failed' THEN 1 ELSE auto_attempts+1 END` -> `auto_attempts=auto_attempts+1, updated_at=?"         " WHERE lead_id=?` | SURVIVED | passed |
| C19 | desk.py | `if held is not None and held[0] == lead_id:` -> `if held is not None:` | SURVIVED | passed |
| C20 | desk.py | `return "pending" if self._auto_attempts(lead_id) < SEND_MAX_ATTEMPTS e` -> `return "pending" if self._auto_attempts(lead_id) <= SEND_MAX_ATTEMPTS ` | KILLED | tests/test_flow.py::test_failed_retry - AssertionError: assert ('pendi... |

Not checked: no property/fuzz run; the two ~60 s files were run only for survivors; mutants limited to the 40 listed.
