| id | example (repr) | v4 claims on old code | observed (withhold_commands) | channel.clean | match? |
|---|---|---|---|---|---|
| G3-01 | `'drop table users;'` | shown | shown | shown | yes |
| G3-02 | `'`drop table users`'` | shown | shown | shown | yes |
| G3-03 | `'delete from users where id = 1'` | shown | shown | shown | yes |
| G3-04 | `'update only t as a set x=1'` | shown | shown | shown | yes |
| G3-05 | `'insert into t values (1)'` | shown | shown | shown | yes |
| G3-06 | `'$ drop table users'` | shown | shown | shown | yes |
| G3-07 | `'drop table pressure'` | shown | shown | shown | yes |
| G3-08 | `'we should delete from the queue only after a fix'` | shown | shown | shown | yes |
| G3-09 | `'update its set of rules'` | shown | shown | shown | yes |
| G3-10 | `'delete from the queue where possible'` | shown | shown | shown | yes |
| G3-11 | `'drop table users'` | shown | shown | shown | yes |
| G3-12 | `'we will drop table pressure; then rest'` | shown | shown | shown | yes |
| G3-UP-1 | `'UPDATE t AS a SET x=1'` | shown | shown | shown | yes |
| G3-UP-2 | `'UPDATE ONLY t SET x=1'` | shown | shown | shown | yes |
| G3-UP-0 | `'UPDATE t SET x=1'` | withheld | withheld | withheld | yes |
| G3-UC-1 | `'DROP TABLE users'` | withheld | withheld | withheld | yes |
| G3-UC-2 | `'DELETE FROM users WHERE id = 1'` | withheld | withheld | withheld | yes |
| G2a-W | `'kubectl \\\ndelete ns prod'` | shown | shown | shown | yes |
| G2a-W-caret | `'kubectl ^\ndelete ns prod'` | shown | shown | shown | yes |
| G2a-W-tick | `'kubectl `\ndelete ns prod'` | shown | shown | shown | yes |
| G2a-S | `'we wrap lines with a backslash \\\nlike this'` | shown | shown | shown | yes |
| G2b-W | `'kubectl > /dev/null delete pod x'` | shown | shown | shown | yes |
| G2b-v3 | `'> /dev/null kubectl delete pod x'` | withheld | withheld | withheld | yes |
| G2b-S | `'the aws Lambda runtime'` | shown | shown | shown | yes |
| G2c-W | `'KUBECTL.EXE delete ns prod'` | candidate-untraced | shown | changed | n/a (untraced) |
| G2c-S | `'the tf module was reviewed'` | shown | shown | shown | yes |
| G4a-W | `'rm -v -rf /x'` | shown | shown | shown | yes |
| G4a-S | `'rm the file'` | shown | shown | shown | yes |
| G5a-W | `'aws secretsmanager get-secret-value --secret-id x'` | shown | shown | shown | yes |
| G5a-S | `'aws s3 ls'` | shown | shown | shown | yes |
| G5b-W | `'git rebase -i HEAD~3'` | candidate-untraced | withheld | withheld | n/a (untraced) |
| G5b-S | `'the docker image was rebuilt overnight'` | shown | shown | shown | yes |
| PIN-kubectl | `"a 'kubectl rollout restart' replaced the pods"` | shown | shown | shown | yes |
| T98 | `'update its set of rules'` | shown | shown | shown | yes |
| T221 | `'we should delete from the queue only after a fix'` | shown | shown | shown | yes |
| T222 | `'drop table pressure'` | shown | shown | shown | yes |
