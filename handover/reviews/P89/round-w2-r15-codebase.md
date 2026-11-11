# PR89 round 15, reviewer codebase-details (egm-codebase-details), head 13b7124
Coverage: runner 1-1223 of 1223; CHANGELOG 1-413 of 413; src/hadavin_sdk/testing/mutation.py 1-200; manifest 1-9. No shell; sha256 not recomputed. ci.yml not in snapshot.
Result: no Blocker/Major in slice. Decode chain (a%2540b, a%2Bb), ?password=pw&application_name=caf%C3%A9, host=h password= dbname=x%27, constants MAX_SECRETS 300 / MAX_FRAGMENT_WORK 50000 checked against code: correct. r14-01 fixed by documentation backed by code; r14-04 consistent; r14-05 mostly fixed.
Minor:
- cd-01 CHANGELOG:11 ci.yml lines 89/99/151 not verifiable from snapshot and fragile.
- cd-02 CHANGELOG:10, runner 59-60/360: example `svc:12/45@h/db` has no scheme; _url_passwords needs "://". Wording defect.
- cd-03 CHANGELOG:18, runner 97/655: "host, port and database name" omits hostaddr, which is hashed.
- cd-04 CHANGELOG:18, runner 97/645/651: "same value"/"one file per value" wrong; the lock name depends on address only.
- cd-05 runner:80: bound "MAX_FRAGMENT_HITS pieces per line" wrong; real bound is up to 2 x hits x secrets capped by MAX_FRAGMENT_WORK.
Nit: runner:420 stale comment; 909-910 first_lines description (masked, all judged rows); CHANGELOG:8 and runner 48-50 omit keyword rule for conftest path parts; runner:104 names fixture_errors but code uses read_junit(...).fixture_failed; CHANGELOG terms "hiding switched off", "pprint", judge() undefined, "hidden/plain text" loose; CHANGELOG:13 "..." counted by overlapping start positions.
