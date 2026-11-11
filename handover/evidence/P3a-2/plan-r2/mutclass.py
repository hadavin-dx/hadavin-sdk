import sys, re, importlib.util
S = sys.argv[1]; T = open(sys.argv[2]).read()
sys.path.insert(0, S)
spec = importlib.util.spec_from_file_location("mm", S + "/tests/migrate_mutants.py"); mm = importlib.util.module_from_spec(spec); sys.modules["mm"] = mm; spec.loader.exec_module(mm)
sec = T[T.index("### 5.5"):T.index("### 5.6")]
listed = set(re.findall(r"\b([A-Z]{1,4}\d+[a-z]?)\b", sec))
retired_tests = set(re.findall(r"`(test_[a-z0-9_]+)`", T[T.index("### 5.4"):T.index("### 5.5")]))
print("total", len(mm.M), "unique", len({m.name for m in mm.M}))
src = {f: open(S + "/" + f).read() for f in {m.file for m in mm.M}}
for m in mm.M:
    ks = mm.killers_of(m)
    kt = [k.partition("::")[2].split("[")[0] for k in ks]
    hit_retired = [k for k in kt if k in retired_tests]
    txt = src[m.file]; i = txt.find(m.old); line = txt.count("\n", 0, i) + 1
    if m.name not in listed:
        print(f"NOT-LISTED {m.name}\t{m.file}:{line}\tkillers={','.join(kt)[:150]}")
    elif hit_retired:
        pass
print("=== affected among NOT-LISTED")
affected_tests = set(retired_tests) | {
 "test_migrate_executes_the_text_it_scanned","test_a_privileged_migration_role_is_refused_before_any_file_runs",
 "test_a_role_that_is_a_member_of_a_privileged_role_is_refused_before_any_file_runs","test_a_server_without_parameter_grants_is_not_asked_about_them",
 "test_the_refusal_says_how_to_make_a_plain_migration_role","test_the_roles_are_asked_again_after_every_file",
 "test_the_replication_flag_is_read_again_after_every_file","test_the_named_roles_are_checked_against_each_other_after_every_file",
 "test_a_privileged_session_user_is_refused_even_when_the_current_user_is_plain","test_a_parameter_grant_is_refused_before_any_file_runs",
 "test_directory_named_like_a_migration_is_refused","test_commit_in_a_file_is_refused_before_connecting",
 "test_migrate_refuses_when_the_released_list_is_unreadable_or_wrong","test_the_released_check_looks_at_the_files_migrate_runs_not_at_the_folder",
 "test_a_bad_hash_in_the_released_list_is_a_config_error_not_a_changed_file","test_a_json_name_written_twice_in_the_released_list_is_refused",
 "test_migrate_refuses_a_changed_released_file_before_it_connects",
 "test_the_upgrade_bullet_says_what_migrate_checks_and_does_not_overclaim","test_the_scope_the_order_and_the_file_own_limits_are_written_down",
 "test_case_f_says_migrate_has_the_same_limits_as_the_hand_file","test_every_timeout_value_written_in_the_docs_is_the_constants"}
import ast
k2 = ast.parse(open(S + "/tests/test_k2_migrations.py").read())
affected_tests |= {n.name for n in k2.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test")}
deleted = [(283, 372), (826, 1106), (1107, 1254), (1600, 1672)]
for m in mm.M:
    if m.name in listed: continue
    ks = mm.killers_of(m); kt = [k.partition("::")[2].split("[")[0] for k in ks]
    txt = src[m.file]; i = txt.find(m.old); line = txt.count("\n", 0, i) + 1
    why = []
    if m.file.endswith("store/migrate.py") and any(a <= line <= b for a, b in deleted): why.append(f"line {line} in a changed region")
    if m.file in ("CHANGELOG.md",): why.append("plants in CHANGELOG")
    hit = [k for k in kt if k in affected_tests]
    if hit: why.append("killer " + ",".join(hit))
    if why: print(f"{m.name}\t{m.file}:{line}\t" + "; ".join(why))
