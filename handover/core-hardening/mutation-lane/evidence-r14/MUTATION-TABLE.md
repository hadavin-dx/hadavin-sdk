| mutant | block run | command | failing check ids | checks run | verdict | seconds |
|---|---|---|---|---|---|---|
| child-args-type | T102 | `ONLY=T102 RUN=<run.mut-child-args-type.py> bash safety-tests.r14.sh` | T102.args-type | 34 | KILLED - as expected | 0 |
| child-abs-program | T102 | `ONLY=T102 RUN=<run.mut-child-abs-program.py> bash safety-tests.r14.sh` | T102.abs-program | 34 | KILLED - as expected | 0 |
| child-identity-compare | T102 | `ONLY=T102 RUN=<run.mut-child-identity-compare.py> bash safety-tests.r14.sh` | T102.identity-compare, T102.identity-fields, T102.identity-ctime | 34 | KILLED - as expected | 0 |
| child-pathtext | T102 | `ONLY=T102 RUN=<run.mut-child-pathtext.py> bash safety-tests.r14.sh` | T102.program-pathtext | 34 | KILLED - as expected | 0 |
| child-trust-first-find | T102 | `ONLY=T102 RUN=<run.mut-child-trust-first-find.py> bash safety-tests.r14.sh` | T102.identity-compare, T102.identity-fields, T102.trust-first-find | 34 | KILLED - as expected | 0 |
| child-tool-location-skip | T102 | `ONLY=T102 RUN=<run.mut-child-tool-location-skip.py> bash safety-tests.r14.sh` | T102.tool-location | 34 | KILLED - as expected | 0 |
| child-tool-location-owner | T102 | `ONLY=T102 RUN=<run.mut-child-tool-location-owner.py> bash safety-tests.r14.sh` | T102.tool-location | 34 | KILLED - as expected | 0 |
| child-seal-missing | T102 | `ONLY=T102 RUN=<run.mut-child-seal-missing.py> bash safety-tests.r14.sh` | T102.seal-missing | 34 | KILLED - as expected | 0 |
| child-nul | T102 | `ONLY=T102 RUN=<run.mut-child-nul.py> bash safety-tests.r14.sh` | T102.nul-arg | 34 | KILLED - as expected | 0 |
| child-shell | T102 | `ONLY=T102 RUN=<run.mut-child-shell.py> bash safety-tests.r14.sh` | T102.shell | 34 | KILLED - as expected | 0 |
| child-kw-allowed | T102 | `ONLY=T102 RUN=<run.mut-child-kw-allowed.py> bash safety-tests.r14.sh` | T102.kw-allowed | 34 | KILLED - as expected | 0 |
| child-env-none | T102 | `ONLY=T102 RUN=<run.mut-child-env-none.py> bash safety-tests.r14.sh` | T102.env-none | 34 | KILLED - as expected | 0 |
| child-env-dict-type | T102 | `ONLY=T102 RUN=<run.mut-child-env-dict-type.py> bash safety-tests.r14.sh` | T102.env-type | 34 | KILLED - as expected | 0 |
| child-env-text-types | T102 | `ONLY=T102 RUN=<run.mut-child-env-text-types.py> bash safety-tests.r14.sh` | T102.env-type | 34 | KILLED - as expected | 0 |
| child-env-allowlist | T102 | `ONLY=T102 RUN=<run.mut-child-env-allowlist.py> bash safety-tests.r14.sh` | T102.env-allowlist | 34 | KILLED - as expected | 0 |
| child-env-value-nul | T102 | `ONLY=T102 RUN=<run.mut-child-env-value-nul.py> bash safety-tests.r14.sh` | T102.env-value-nul | 34 | KILLED - as expected | 0 |
| child-cwd-abs | T102 | `ONLY=T102 RUN=<run.mut-child-cwd-abs.py> bash safety-tests.r14.sh` | T102.cwd-abs | 34 | KILLED - as expected | 0 |
| child-cwd-real | T102 | `ONLY=T102 RUN=<run.mut-child-cwd-real.py> bash safety-tests.r14.sh` | T102.cwd-real | 34 | KILLED - as expected | 0 |
| child-start-new-session | T102 | `ONLY=T102 RUN=<run.mut-child-start-new-session.py> bash safety-tests.r14.sh` | T102.start-new-session | 34 | KILLED - as expected | 0 |
| child-git-show-toplevel-loose | T102 | `ONLY=T102 RUN=<run.mut-child-git-show-toplevel-loose.py> bash safety-tests.r14.sh` | T102.git-show-toplevel | 34 | KILLED - as expected | 0 |
| child-git-is-inside-loose | T102 | `ONLY=T102 RUN=<run.mut-child-git-is-inside-loose.py> bash safety-tests.r14.sh` | T102.git-is-inside | 34 | KILLED - as expected | 0 |
| child-git-any-rev-parse | T102 | `ONLY=T102 RUN=<run.mut-child-git-any-rev-parse.py> bash safety-tests.r14.sh` | T102.git-subcommand | 34 | KILLED - as expected | 0 |
| child-git-verify-option | T102 | `ONLY=T102 RUN=<run.mut-child-git-verify-option.py> bash safety-tests.r14.sh` | T102.git-verify | 34 | KILLED - as expected | 0 |
| child-git-verify-len | T102 | `ONLY=T102 RUN=<run.mut-child-git-verify-len.py> bash safety-tests.r14.sh` | T102.git-verify | 34 | KILLED - as expected | 0 |
| child-git-archive-option | T102 | `ONLY=T102 RUN=<run.mut-child-git-archive-option.py> bash safety-tests.r14.sh` | T102.git-archive | 34 | KILLED - as expected | 0 |
| child-git-archive-len | T102 | `ONLY=T102 RUN=<run.mut-child-git-archive-len.py> bash safety-tests.r14.sh` | T102.git-archive | 34 | KILLED - as expected | 0 |
| child-git-dash-C | T102 | `ONLY=T102 RUN=<run.mut-child-git-dash-.py> bash safety-tests.r14.sh` | T102.git-C | 34 | KILLED - as expected | 0 |
| child-git-min-len | T102 | `ONLY=T102 RUN=<run.mut-child-git-min-len.py> bash safety-tests.r14.sh` | T102.git-C | 34 | KILLED - as expected | 0 |
| child-patch-len | T102 | `ONLY=T102 RUN=<run.mut-child-patch-len.py> bash safety-tests.r14.sh` | T102.patch-shape | 34 | KILLED - as expected | 0 |
| child-patch-abs-d | T102 | `ONLY=T102 RUN=<run.mut-child-patch-abs-d.py> bash safety-tests.r14.sh` | T102.patch-shape | 34 | KILLED - as expected | 0 |
| child-patch-abs-i | T102 | `ONLY=T102 RUN=<run.mut-child-patch-abs-i.py> bash safety-tests.r14.sh` | T102.patch-shape | 34 | KILLED - as expected | 0 |
| child-patch-order | T102 | `ONLY=T102 RUN=<run.mut-child-patch-order.py> bash safety-tests.r14.sh` | T102.patch-shape | 34 | KILLED - as expected | 0 |
| child-set-root-none | T102 | `ONLY=T102 RUN=<run.mut-child-set-root-none.py> bash safety-tests.r14.sh` | T102.python-root-none | 34 | KILLED - as expected | 0 |
| child-python-endswith | T102 | `ONLY=T102 RUN=<run.mut-child-python-endswith.py> bash safety-tests.r14.sh` | T102.python-path-text | 34 | KILLED - as expected | 0 |
| child-python-probe-any | T102 | `ONLY=T102 RUN=<run.mut-child-python-probe-any.py> bash safety-tests.r14.sh` | T102.python-shape-probe | 34 | KILLED - as expected | 0 |
| child-python-probe-option | T102 | `ONLY=T102 RUN=<run.mut-child-python-probe-option.py> bash safety-tests.r14.sh` | T102.python-shape-probe | 34 | KILLED - as expected | 0 |
| child-python-pytest-head | T102 | `ONLY=T102 RUN=<run.mut-child-python-pytest-head.py> bash safety-tests.r14.sh` | T102.python-shape-pytest | 34 | KILLED - as expected | 0 |
| child-python-pytest-tail | T102 | `ONLY=T102 RUN=<run.mut-child-python-pytest-tail.py> bash safety-tests.r14.sh` | T102.python-shape-pytest | 34 | KILLED - as expected | 0 |
| child-python-pin-off | T102 | `ONLY=T102 RUN=<run.mut-child-python-pin-off.py> bash safety-tests.r14.sh` | T102.python-pin, T102.python-pin-ctime | 34 | KILLED - as expected | 0 |
| child-identity-r13-fields | T102 | `ONLY=T102 RUN=<run.mut-child-identity-r13-fields.py> bash safety-tests.r14.sh` | T102.identity-fields, T102.identity-ctime, T102.python-pin-ctime | 34 | KILLED - as expected | 0 |
| child-identity-no-ctime | T102 | `ONLY=T102 RUN=<run.mut-child-identity-no-ctime.py> bash safety-tests.r14.sh` | T102.identity-ctime, T102.python-pin-ctime | 34 | KILLED - as expected | 0 |
| child-identity-no-size | T102 | `ONLY=T102 RUN=<run.mut-child-identity-no-size.py> bash safety-tests.r14.sh` | (none) | 34 | SURVIVED - as expected (SURVIVES: equivalent, st_size is redundant next to st_ctime_ns (any write changes the change time)) | 0 |
| child-identity-no-mtime | T102 | `ONLY=T102 RUN=<run.mut-child-identity-no-mtime.py> bash safety-tests.r14.sh` | (none) | 34 | SURVIVED - as expected (SURVIVES: equivalent, st_mtime_ns is redundant next to st_ctime_ns (any write changes the change time)) | 0 |
| raw-dots | T103 | `ONLY=T103 RUN=<run.mut-raw-dots.py> bash safety-tests.r14.sh` | T103a.raw-dots, T103a.outjson-dots | 26 | KILLED - as expected | 23 |
| raw-symlink | T103 | `ONLY=T103 RUN=<run.mut-raw-symlink.py> bash safety-tests.r14.sh` | T103a.raw-symlink, T103a.outjson-symlink, T103b.4, T103b.5, T103b.8, T103b.9 | 26 | KILLED - as expected | 23 |
| raw-levels | T103 | `ONLY=T103 RUN=<run.mut-raw-levels.py> bash safety-tests.r14.sh` | T103a.raw-levels, T103a.outjson-levels, T103b.1, T103b.2, T103b.6 | 26 | KILLED - as expected | 23 |
| raw-no-toplevel (uid 65534 run T103b) | T103 | `ONLY=T103 RUN=<run.mut-raw-no-toplevel.py> bash safety-tests.r14.sh` | T103a.raw-levels, T103a.outjson-levels, T103b.2, T103b.6 | 26 | KILLED - as expected | 23 |
| raw-system | T103 | `ONLY=T103 RUN=<run.mut-raw-system.py> bash safety-tests.r14.sh` | T103a.raw-system, T103a.outjson-system, T103b.3, T103b.7 | 26 | KILLED - as expected | 23 |
| raw-var-tmp-not-allowed | T103 | `ONLY=T103 RUN=<run.mut-raw-var-tmp-not-allowed.py> bash safety-tests.r14.sh` | T103a.raw-system, T103a.raw-sharedtmp | 26 | KILLED - as expected | 23 |
| raw-sharedtmp | T103 | `ONLY=T103 RUN=<run.mut-raw-sharedtmp.py> bash safety-tests.r14.sh` | T103a.raw-sharedtmp | 26 | KILLED - as expected | 22 |
| raw-no-resolve | T103 | `ONLY=T103 RUN=<run.mut-raw-no-resolve.py> bash safety-tests.r14.sh` | (none) | 26 | SURVIVED - as expected (SURVIVES: layered, a link on the way is already refused by the symbolic-link guard before the resolved path is looked at; the two layers cover the same cases on Linux) | 23 |
| raw-not-wired | T103 | `ONLY=T103 RUN=<run.mut-raw-not-wired.py> bash safety-tests.r14.sh` | T103b.1, T103b.2, T103b.3, T103b.4, T103b.5 | 26 | KILLED - as expected | 23 |
| out-json-not-wired | T103 | `ONLY=T103 RUN=<run.mut-out-json-not-wired.py> bash safety-tests.r14.sh` | T103b.1, T103b.2, T103b.3, T103b.4, T103b.5, T103b.6, T103b.7, T103b.8, T103b.9, T103c, T103c2, T103d | 26 | KILLED - as expected | 250 |
| leader-no-module-check | T103 | `ONLY=T103 RUN=<run.mut-leader-no-module-check.py> bash safety-tests.r14.sh` | T103a.leader-shape | 26 | KILLED - as expected | 23 |
| leader-no-rootdir | T103 | `ONLY=T103 RUN=<run.mut-leader-no-rootdir.py> bash safety-tests.r14.sh` | T103a.leader-shape | 26 | KILLED - as expected | 23 |
| leader-no-python-path | T103 | `ONLY=T103 RUN=<run.mut-leader-no-python-path.py> bash safety-tests.r14.sh` | T103a.leader-shape | 26 | KILLED - as expected | 23 |
| leader-not-used-pgid-branch | T103 | `ONLY=T103 RUN=<run.mut-leader-not-used-pgid-branch.py> bash safety-tests.r14.sh` | T103c | 26 | KILLED - as expected | 23 |
| leader-not-used-command-branch | T103 | `ONLY=T103 RUN=<run.mut-leader-not-used-command-branch.py> bash safety-tests.r14.sh` | T103c3 | 26 | KILLED - as expected | 22 |
| leader-always-false | T103 | `ONLY=T103 RUN=<run.mut-leader-always-false.py> bash safety-tests.r14.sh` | T103a.leader-shape, T103c2 | 26 | KILLED - as expected | 22 |
| note-always-long | T103 | `ONLY=T103 RUN=<run.mut-note-always-long.py> bash safety-tests.r14.sh` | T103d | 26 | KILLED - as expected | 22 |
