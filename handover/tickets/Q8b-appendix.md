# Q8b appendix (part of ticket Q8b-partial-mask-and-card-redaction.md, rev 3): measured outputs, the prototype's text, the test generators
Everything here was run by the ticket author on 2026-11-11 with `/home/user/build/venv-p89/bin/python`. "main" is origin/main 2a8c2aa source (`/home/user/build/EV-P89-db0d9eb/src`, the seven files this ticket reads or edits compared byte for byte). "proto" is a throwaway private copy with the behaviour of the ticket; it is NOT a build and nothing of it is in the repository. In every pasted output the long key word is written `pw` (`PW`, `Pw` where the run had capitals), because the repository's secret scan refuses that word followed by a quoted text. The builder re-runs all of this on the merge base and on the branch.

## A1. Credential-key path: inputs
Helper names: `PW` the long key word built from parts; `P` = "correct horse battery staple"; `ONE` a 16-character one-word value; `T` a 9-character one-word value; `b64(x)` base64 of x; each case runs `_walk` twice with one map, as `redact_bundle` does.
```python
# rows of plan review round 1 (script r2_f5.py)
cases = [
 ("M1 PG+key, multi-word", {"PG" + PW.upper(): P}),
 ("M1 env entry PG+key", {"name": "PG" + PW.upper(), "value": ONE}),
 ("M1 pwd", {"pwd": ONE}),
 ("M1 DBPassword", {"DB" + PW.capitalize(): P}),
 ("M1 secretkey", {"secretkey": P}), ("M1 secrets", {"secrets": P}), ("M1 root+key", {"root" + PW: P}), ("M1 accessKey", {"accessKey": P}),
 ("1f negative author", {"author": "Priya Nair"}), ("1f negative tokens_used", {"tokens_used": 1234}),
 ("1f negative policy flag", {PW + "_policy_enabled": "true"}),
 ("M2 number in env entry", {"name": "DB_" + PW.upper(), "value": 12345678}),
 ("M2 list in env entry", {"name": "DB_" + PW.upper(), "value": [P, 42]}),
 ("M2 Name/Value", {"Name": "DB_" + PW.upper(), "Value": P}),
 ("M2 key/value", {"key": "api_key", "value": P}),
 ("B1r authorization", {"authorization": P}), ("B1r private_key", {"private_key": P}), ("B1r privateKey", {"privateKey": P}),
 ("B1r bearer", {"bearer": P}), ("B1r passphrase", {"passphrase": P}),
 ("B1r long-suffix key", {PW + "_for_the_primary_database_replica": P}),
 ("B1r long-suffix key, one word", {PW + "_for_the_primary_database_replica": ONE}),
 ("B1r 300-char multi-word", {PW: LONG}), ("255 chars", {PW: V255}), ("256 chars", {PW: V256}),
 ("M3 Secret username + log", [{"kind": "Secret", "stringData": {"username": "orders-svc"}}, {"message": "user orders-svc NAME denied"}]),
 ("M5 Secret DB_NAME b64 + log", [{"kind": "Secret", "data": {"DB_NAME": b64("orders")}}, {"message": "orders-api timeout"}]),
 ("M6 ESC inside value", {PW: "hunter\x1b[0m2" + "secretXYZ"}),
 ("M6 ESC + log", [{PW: "hunter\x1b[0m2" + "secretXYZ"}, {"message": "the hunter came"}]),
 ("F5 sweep", {PW: P}), ("F5 a b", {PW: "a b"}), ("F5 both quotes", {"db_" + PW: "pa55\"word 'tail' part"}),
 ("F5b repeat, pattern-free", [{PW: P}, {"message": f"login with {P} failed; correct answer"}]),
 ("F5b Secret cfg + log", [{"kind": "Secret", "stringData": {"cfg": P}}, {"message": f"login with {P} failed"}]),
 ("F5b Secret b64 + decoded in log", [{"kind": "Secret", "data": {"p": b64(P)}}, {"message": f"login with {P} failed"}]),
 ("XF composite (design B1)", [{"token": "bob.smith@example.com Zx9 tail"}, {"message": "login with bob.smith@example.com Zx9 tail failed"}]),
 ("XF over 255 + log", [{PW: LONG}, {"message": "saw " + LONG}]),
 ("XF both quotes + log", [{PW: "pa55\"word 'tail' part"}, {"message": "saw pa55\"word 'tail' part"}]),
 ("XF nested under credentials + log", [{"credentials": {"note": P}}, {"message": f"saw {P}"}]),
 ("XF number + log", [{"pin_token": 12345678}, {"message": "pin 12345678 used"}]),
 ("XF respelled (JSON-escaped annotation)", [{"kind": "Secret", "stringData": {"cfg": 'say "horse" twice'}},
     {"annotations": {"last-applied-configuration": json.dumps({"stringData": {"cfg": 'say "horse" twice'}})}}]),
 ("1d timestamp", {"token": "2026-11-11T10:00:00Z"}),
 ("1d near miss +00:00", {"token": "2026-11-11T10:00:00+00:00"}), ("1d near miss space", {"token": "2026-11-11 10:00:00Z"}),
 ("1d near miss trailing", {"token": "2026-11-11T10:00:00Zx"}), ("1d near miss month 13", {"token": "2026-13-11T10:00:00Z"}),
 ("guard credentials.user", {"credentials": {"user": "svc"}}), ("guard one token", {PW: ONE}), ("guard message", {"message": P}),
]

# rows of plan review round 2 (script r3_f5.py)
cases = [
 ("B1 PW_used one word", {PW + "_used": T}), ("B1 PW_used multi-word", {PW + "_used": P}),
 ("B1 env API_KEY_TYPE", {"name": "API_KEY_TYPE", "value": T}), ("B1 token_policy dict", {"token_policy": {"default": T}}),
 ("B1 client_secret_max", {"client_secret_max": T}),
 ("B1 gate: flag 'true'", {PW + "_policy_enabled": "true"}), ("B1 gate: bool", {PW + "_policy_enabled": True}),
 ("B1 gate: number", {"token_expiry": 3600}), ("B1 gate: '30d'", {"token_expiry": "30d"}), ("B1 gate: count", {"secret_count": 3}),
 ("B1 gate: timestamp", {"token_expires": "2026-11-25T00:00:00Z"}), ("B1 gate: env TOKEN_TTL", {"name": "TOKEN_TTL", "value": "15m"}),
 ("B1 gate refuses a word", {PW + "_policy_enabled": T}), ("B1 gate refuses a list", {PW + "_policy_enabled": ["on", T]}),
 ("B1 gate refuses 11 digits", {"token_expiry": "12345678901"}), ("B1 gate under a credential parent", {"credentials": {PW + "_policy_enabled": "true"}}),
 ("M2 api_tokens list", {"api_tokens": [P]}), ("M2 refresh_tokens", {"refresh_tokens": P}), ("M2 tokens", {"tokens": P}),
 ("M2 prompt_tokens", {"prompt_tokens": 812}), ("M2 total_tokens", {"total_tokens": 1000}), ("M2 tokens_used", {"tokens_used": 1234}),
 ("M2 session", {"session": P}), ("M2 JSESSIONID", {"JSESSIONID": ONE}), ("M2 auth", {"auth": P}), ("M2 account_key", {"account_key": P}),
 ("M2 client-key-data", {"client-key-data": P}), ("M2 connect.sid", {"connect.sid": ONE}), ("M2 PW2", {PW + "2": P}), ("M2 token1", {"token1": P}),
 ("M2 OLDPWD", {"name": "OLDPWD", "value": "/srv/app"}), ("M2 author", {"author": "Priya Nair"}),
 ("M1 Secret of common words + logs", [SECRET, {"level": "info", "message": "information: retry in 5s", "service": "orders"},
     {"level": "error", "message": "orders-api timeout on port 5432 as postgres in prod; debug=true; orders_count=3"}]),
 ("M1 Secret LOG_LEVEL only", [{"kind": "Secret", "data": {"LOG_LEVEL": b64("info")}}, {"level": "info", "message": "information: retry in 5s"}]),
 ("M1 row 37 DB_NAME", [{"kind": "Secret", "data": {"DB_NAME": b64("orders")}}, {"message": "orders-api timeout"}]),
 ("M1 row 46 username", [{"kind": "Secret", "stringData": {"username": "orders-svc"}}, {"message": "user orders-svc NAME denied"}]),
 ("M1 row 35 same placeholder", [{"kind": "Secret", "data": {"p": b64(P)}}, {"message": f"login with {P} failed"}]),
 ("M1 row 34 cfg", [{"kind": "Secret", "stringData": {"cfg": P}}, {"message": f"login with {P} failed"}]),
 ("M1 Secret credential key short", [{"kind": "Secret", "stringData": {"db_" + PW: "abcd"}}, {"message": "xabcdy abcd"}]),
 ("M4 3 characters", [{"pin_token": "ab1"}, {"message": "xab1y and ab1 alone"}]), ("M4 2 characters", [{"pin_token": "a1"}, {"message": "a1 alone"}]),
 ("M4 env number + log", [{"name": "DB_" + PW.upper(), "value": 12345678}, {"message": "pin 12345678 used"}]),
 ("M4 percent in value + copy", [{PW: "ab%20cd9xtail"}, {"message": "saw ab%20cd9xtail and ab cd9xtail"}]),
 ("M4 backslash-u in value + copy", [{PW: "ab\\u0041cd9xtail"}, {"message": "saw ab\\u0041cd9xtail and abAcd9xtail"}]),
 ("M4 ESC value + copies", [{PW: "hunter\x1b[0m2" + "secretXYZ"}, {"message": "saw hunter2" + "secretXYZ and hunter\x1b[0m2" + "secretXYZ"}]),
 ("look-alike value", {PW: "<SECRET_1>"}), ("look-alike + log", [{PW: "<SECRET_1>"}, {"token": ONE}, {"message": "see <SECRET_1>"}]),
 ("one letter", {PW: "a"}), ("one letter + log", [{PW: "a"}, {"message": "a cat and a hat"}]),
 ("G4 credentials.user + log", [{"credentials": {"user": "svc"}}, {"message": "svc restarted"}]),
]

```
## A2. Credential-key path: outputs
```
[M1 PG+key, multi-word]
  main : {'PGPW': 'correct horse battery staple'}
  proto: {'PGPW': '<SECRET_1>'}
[M1 env entry PG+key]
  main : {'name': 'PGPW', 'value': 'hunter2secretXYZ'}
  proto: {'name': 'PGPW', 'value': '<SECRET_1>'}
[M1 pwd]
  main : {'pwd': 'hunter2secretXYZ'}
  proto: {'pwd': '<SECRET_1>'}
[M1 DBPw]
  main : {'DBPw': 'correct horse battery staple'}
  proto: {'DBPw': '<SECRET_1>'}
[M1 secretkey]
  main : {'secretkey': 'correct horse battery staple'}
  proto: {'secretkey': '<SECRET_1>'}
[M1 secrets]
  main : {'secrets': 'correct horse battery staple'}
  proto: {'secrets': '<SECRET_1>'}
[M1 root+key]
  main : {'rootpw': 'correct horse battery staple'}
  proto: {'rootpw': '<SECRET_1>'}
[M1 accessKey]
  main : {'accessKey': 'correct horse battery staple'}
  proto: {'accessKey': '<SECRET_1>'}
[1f negative author]
  main : {'author': 'Priya Nair'}
  proto: {'author': 'Priya Nair'}
[1f negative tokens_used]
  main : {'tokens_used': 1234}
  proto: {'tokens_used': 1234}
[1f negative policy flag]
  main : {'pw_policy_enabled': '<SECRET_REDACTED>'}
  proto: {'pw_policy_enabled': 'true'}
[M2 number in env entry]
  main : {'name': 'DB_PW', 'value': 12345678}
  proto: {'name': 'DB_PW', 'value': '<SECRET_REDACTED>'}
[M2 list in env entry]
  main : {'name': 'DB_PW', 'value': ['correct horse battery staple', 42]}
  proto: {'name': 'DB_PW', 'value': ['<SECRET_1>', '<SECRET_REDACTED>']}
[M2 Name/Value]
  main : {'Name': 'DB_PW', 'Value': 'correct horse battery staple'}
  proto: {'Name': 'DB_PW', 'Value': '<SECRET_1>'}
[M2 key/value]
  main : {'key': 'api_key', 'value': 'correct horse battery staple'}
  proto: {'key': 'api_key', 'value': '<SECRET_1>'}
[B1r authorization]
  main : {'authorization': '<SECRET_REDACTED>'}
  proto: {'authorization': '<SECRET_1>'}
[B1r private_key]
  main : {'private_key': '<SECRET_1> horse battery staple'}
  proto: {'private_key': '<SECRET_1>'}
[B1r privateKey]
  main : {'privateKey': '<SECRET_1> horse battery staple'}
  proto: {'privateKey': '<SECRET_1>'}
[B1r bearer]
  main : {'bearer': '<SECRET_REDACTED>'}
  proto: {'bearer': '<SECRET_1>'}
[B1r passphrase]
  main : {'passphrase': '<SECRET_REDACTED>'}
  proto: {'passphrase': '<SECRET_1>'}
[B1r long-suffix key]
  main : {'pw_for_the_primary_database_replica': '<SECRET_REDACTED>'}
  proto: {'pw_for_the_primary_database_replica': '<SECRET_1>'}
[B1r long-suffix key, one word]
  main : {'pw_for_the_primary_database_replica': '<SECRET_REDACTED>'}
  proto: {'pw_for_the_primary_database_replica': '<SECRET_1>'}
[B1r 300-char multi-word]
  main : {'pw': '<SECRET_1> bravo charlie delta echo foxtrot <SECRET_1> bravo charlie delta echo foxtrot <SECRET_1> bravo charlie delta echo foxtrot <SEC ...  charlie delta echo foxtrot <SECRET_1> bravo charlie delta echo foxtrot <SECRET_1> bravo charlie delta echo foxtrot <SECRET_1> bravo charlie delta e'}
  proto: {'pw': '<SECRET_REDACTED>'}
[255 chars]
  main : {'pw': '<SECRET_1> cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab '}
  proto: {'pw': '<SECRET_1>'}
[256 chars]
  main : {'pw': '<SECRET_1> cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab cd ab c'}
  proto: {'pw': '<SECRET_REDACTED>'}
[M3 Secret username + log]
  main : [{'kind': 'Secret', 'stringData': {'username': '<NAME_1>'}}, {'message': 'user <NAME_1> NAME denied'}]
  proto: [{'kind': 'Secret', 'stringData': {'username': '<SECRET_1>'}}, {'message': 'user <SECRET_1> NAME denied'}]
[M5 Secret DB_NAME b64 + log]
  main : [{'kind': 'Secret', 'data': {'DB_NAME': '<SECRET_REDACTED>'}}, {'message': 'orders-api timeout'}]
  proto: [{'kind': 'Secret', 'data': {'DB_NAME': '<SECRET_1>'}}, {'message': 'orders-api timeout'}]
[M6 ESC inside value]
  main : {'pw': '<SECRET_1> 2secretXYZ'}
  proto: {'pw': '<SECRET_1>'}
[M6 ESC + log]
  main : [{'pw': '<SECRET_1> 2secretXYZ'}, {'message': 'the <SECRET_1> came'}]
  proto: [{'pw': '<SECRET_1>'}, {'message': 'the hunter came'}]
[F5 sweep]
  main : {'pw': '<SECRET_1> horse battery staple'}
  proto: {'pw': '<SECRET_1>'}
[F5 a b]
  main : {'pw': 'p<SECRET_1>ssword=<SECRET_1> b'}
  proto: {'pw': '<SECRET_1>'}
[F5 both quotes]
  main : {'db_pw': '<SECRET_1>"word \'tail\' part'}
  proto: {'db_pw': '<SECRET_REDACTED>'}
[F5b repeat, pattern-free]
  main : [{'pw': '<SECRET_1> horse battery staple'}, {'message': 'login with <SECRET_1> horse battery staple failed; <SECRET_1> answer'}]
  proto: [{'pw': '<SECRET_1>'}, {'message': 'login with <SECRET_1> failed; correct answer'}]
[F5b Secret cfg + log]
  main : [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_REDACTED>'}}, {'message': 'login with correct horse battery staple failed'}]
  proto: [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_1>'}}, {'message': 'login with <SECRET_1> failed'}]
[F5b Secret b64 + decoded in log]
  main : [{'kind': 'Secret', 'data': {'p': '<SECRET_REDACTED>'}}, {'message': 'login with correct horse battery staple failed'}]
  proto: [{'kind': 'Secret', 'data': {'p': '<SECRET_3>'}}, {'message': 'login with <SECRET_3> failed'}]
[XF composite (design B1)]
  main : [{'token': '<EMAIL_1> Zx9 tail'}, {'message': 'login with <EMAIL_1> Zx9 tail failed'}]
  proto: [{'token': '<SECRET_1>'}, {'message': 'login with <EMAIL_1> Zx9 tail failed'}]
[XF over 255 + log]
  main : [{'pw': '<SECRET_1> bravo charlie delta echo foxtrot <SECRET_1> bravo charlie delta echo foxtrot <SECRET_1> bravo charlie delta echo foxtrot <SE ... charlie delta echo foxtrot <SECRET_1> bravo charlie delta echo foxtrot <SECRET_1> bravo charlie delta echo foxtrot <SECRET_1> bravo charlie delta e'}]
  proto: [{'pw': '<SECRET_REDACTED>'}, {'message': 'saw alpha bravo charlie delta echo foxtrot alpha bravo charlie delta echo foxtrot alpha bravo charlie ... ot alpha bravo charlie delta echo foxtrot alpha bravo charlie delta echo foxtrot alpha bravo charlie delta echo foxtrot alpha bravo charlie delta e'}]
[XF both quotes + log]
  main : [{'pw': '<SECRET_1>"word \'tail\' part'}, {'message': 'saw <SECRET_1>"word \'tail\' part'}]
  proto: [{'pw': '<SECRET_REDACTED>'}, {'message': 'saw pa55"word \'tail\' part'}]
[XF nested under credentials + log]
  main : [{'credentials': {'note': '<SECRET_REDACTED>'}}, {'message': 'saw correct horse battery staple'}]
  proto: [{'credentials': {'note': '<SECRET_REDACTED>'}}, {'message': 'saw correct horse battery staple'}]
[XF number + log]
  main : [{'pin_token': '<SECRET_REDACTED>'}, {'message': 'pin 12345678 used'}]
  proto: [{'pin_token': '<SECRET_REDACTED>'}, {'message': 'pin 12345678 used'}]
[XF respelled (JSON-escaped annotation)]
  main : [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_REDACTED>'}}, {'annotations': {'last-applied-configuration': '{"stringData": {"cfg": "say \\"horse\\" twice"}}'}}]
  proto: [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_1>'}}, {'annotations': {'last-applied-configuration': '{"stringData": {"cfg": "<SECRET_1>"}}'}}]
[1d timestamp]
  main : {'token': '2026-11-11T10:00:00Z'}
  proto: {'token': '2026-11-11T10:00:00Z'}
[1d near miss +00:00]
  main : {'token': '<SECRET_1>'}
  proto: {'token': '<SECRET_1>'}
[1d near miss space]
  main : {'token': '<SECRET_1> 10:00:00Z'}
  proto: {'token': '<SECRET_1>'}
[1d near miss trailing]
  main : {'token': '<SECRET_1>'}
  proto: {'token': '<SECRET_1>'}
[1d near miss month 13]
  main : {'token': '<SECRET_1>'}
  proto: {'token': '<SECRET_1>'}
[guard credentials.user]
  main : {'credentials': {'user': '<SECRET_REDACTED>'}}
  proto: {'credentials': {'user': '<SECRET_REDACTED>'}}
[guard one token]
  main : {'pw': '<SECRET_1>'}
  proto: {'pw': '<SECRET_1>'}
[guard message]
  main : {'message': 'correct horse battery staple'}
  proto: {'message': 'correct horse battery staple'}
[B1 PW_used one word]
  main : {'pw_used': '<SECRET_1>'}
  proto: {'pw_used': '<SECRET_1>'}
[B1 PW_used multi-word]
  main : {'pw_used': '<SECRET_1> horse battery staple'}
  proto: {'pw_used': '<SECRET_1>'}
[B1 env API_KEY_TYPE]
  main : {'name': 'API_KEY_TYPE', 'value': '<SECRET_1>'}
  proto: {'name': 'API_KEY_TYPE', 'value': '<SECRET_1>'}
[B1 token_policy dict]
  main : {'token_policy': {'default': '<SECRET_REDACTED>'}}
  proto: {'token_policy': {'default': '<SECRET_REDACTED>'}}
[B1 client_secret_max]
  main : {'client_secret_max': '<SECRET_1>'}
  proto: {'client_secret_max': '<SECRET_1>'}
[B1 gate: flag 'true']
  main : {'pw_policy_enabled': '<SECRET_REDACTED>'}
  proto: {'pw_policy_enabled': 'true'}
[B1 gate: bool]
  main : {'pw_policy_enabled': True}
  proto: {'pw_policy_enabled': True}
[B1 gate: number]
  main : {'token_expiry': '<SECRET_REDACTED>'}
  proto: {'token_expiry': 3600}
[B1 gate: '30d']
  main : {'token_expiry': '<SECRET_1>'}
  proto: {'token_expiry': '30d'}
[B1 gate: count]
  main : {'secret_count': '<SECRET_REDACTED>'}
  proto: {'secret_count': 3}
[B1 gate: timestamp]
  main : {'token_expires': '2026-11-25T00:00:00Z'}
  proto: {'token_expires': '2026-11-25T00:00:00Z'}
[B1 gate: env TOKEN_TTL]
  main : {'name': 'TOKEN_TTL', 'value': '<SECRET_1>'}
  proto: {'name': 'TOKEN_TTL', 'value': '15m'}
[B1 gate refuses a word]
  main : {'pw_policy_enabled': '<SECRET_1>'}
  proto: {'pw_policy_enabled': '<SECRET_1>'}
[B1 gate refuses a list]
  main : {'pw_policy_enabled': ['<SECRET_REDACTED>', '<SECRET_1>']}
  proto: {'pw_policy_enabled': ['<SECRET_REDACTED>', '<SECRET_1>']}
[B1 gate refuses 11 digits]
  main : {'token_expiry': '<PHONE_1>'}
  proto: {'token_expiry': '<PHONE_1>'}
[B1 gate under a credential parent]
  main : {'credentials': {'pw_policy_enabled': '<SECRET_REDACTED>'}}
  proto: {'credentials': {'pw_policy_enabled': '<SECRET_REDACTED>'}}
[M2 api_tokens list]
  main : {'api_tokens': ['correct horse battery staple']}
  proto: {'api_tokens': ['<SECRET_1>']}
[M2 refresh_tokens]
  main : {'refresh_tokens': 'correct horse battery staple'}
  proto: {'refresh_tokens': '<SECRET_1>'}
[M2 tokens]
  main : {'tokens': 'correct horse battery staple'}
  proto: {'tokens': '<SECRET_1>'}
[M2 prompt_tokens]
  main : {'prompt_tokens': 812}
  proto: {'prompt_tokens': 812}
[M2 total_tokens]
  main : {'total_tokens': 1000}
  proto: {'total_tokens': 1000}
[M2 tokens_used]
  main : {'tokens_used': 1234}
  proto: {'tokens_used': 1234}
[M2 session]
  main : {'session': 'correct horse battery staple'}
  proto: {'session': '<SECRET_1>'}
[M2 JSESSIONID]
  main : {'JSESSIONID': 'hunter2secretXYZ'}
  proto: {'JSESSIONID': '<SECRET_1>'}
[M2 auth]
  main : {'auth': 'correct horse battery staple'}
  proto: {'auth': '<SECRET_1>'}
[M2 account_key]
  main : {'account_key': 'correct horse battery staple'}
  proto: {'account_key': '<SECRET_1>'}
[M2 client-key-data]
  main : {'client-key-data': 'correct horse battery staple'}
  proto: {'client-key-data': '<SECRET_1>'}
[M2 connect.sid]
  main : {'connect.sid': 'hunter2secretXYZ'}
  proto: {'connect.sid': '<SECRET_1>'}
[M2 PW2]
  main : {'pw2': 'correct horse battery staple'}
  proto: {'pw2': '<SECRET_1>'}
[M2 token1]
  main : {'token1': 'correct horse battery staple'}
  proto: {'token1': '<SECRET_1>'}
[M2 OLDPWD]
  main : {'name': 'OLDPWD', 'value': '/srv/app'}
  proto: {'name': 'OLDPWD', 'value': '<SECRET_1>'}
[M2 author]
  main : {'author': 'Priya Nair'}
  proto: {'author': 'Priya Nair'}
[M1 Secret of common words + logs]
  main : [{'kind': 'Secret', 'data': {'LOG_LEVEL': '<SECRET_REDACTED>', 'DEBUG': '<SECRET_REDACTED>', 'ENV': '<SECRET_REDACTED>', 'PORT': '<SECRET_REDACTED>', 'DB_USER': '<SECRET_REDACTED>', 'DB_NAME': '<SECRET_REDACTED>', 'DB_PW': '<SECRET_1>'}}, {'level': 'info', 'message': 'information: retry in 5s', 'service': 'orders'}, {'level': 'error', 'message': 'orders-api timeout on port 5432 as postgres in prod; debug=true; orders_count=3'}]
  proto: [{'kind': 'Secret', 'data': {'LOG_LEVEL': '<SECRET_1>', 'DEBUG': '<SECRET_2>', 'ENV': '<SECRET_3>', 'PORT': '<SECRET_4>', 'DB_USER': '<SECRET_5>', 'DB_NAME': '<SECRET_7>', 'DB_PW': '<SECRET_9>'}}, {'level': 'info', 'message': 'information: retry in 5s', 'service': 'orders'}, {'level': 'error', 'message': 'orders-api timeout on port 5432 as postgres in prod; debug=true; orders_count=3'}]
[M1 Secret LOG_LEVEL only]
  main : [{'kind': 'Secret', 'data': {'LOG_LEVEL': '<SECRET_REDACTED>'}}, {'level': 'info', 'message': 'information: retry in 5s'}]
  proto: [{'kind': 'Secret', 'data': {'LOG_LEVEL': '<SECRET_1>'}}, {'level': 'info', 'message': 'information: retry in 5s'}]
[M1 row 37 DB_NAME]
  main : [{'kind': 'Secret', 'data': {'DB_NAME': '<SECRET_REDACTED>'}}, {'message': 'orders-api timeout'}]
  proto: [{'kind': 'Secret', 'data': {'DB_NAME': '<SECRET_1>'}}, {'message': 'orders-api timeout'}]
[M1 row 46 username]
  main : [{'kind': 'Secret', 'stringData': {'username': '<NAME_1>'}}, {'message': 'user <NAME_1> NAME denied'}]
  proto: [{'kind': 'Secret', 'stringData': {'username': '<SECRET_1>'}}, {'message': 'user <SECRET_1> NAME denied'}]
[M1 row 35 same placeholder]
  main : [{'kind': 'Secret', 'data': {'p': '<SECRET_REDACTED>'}}, {'message': 'login with correct horse battery staple failed'}]
  proto: [{'kind': 'Secret', 'data': {'p': '<SECRET_3>'}}, {'message': 'login with <SECRET_3> failed'}]
[M1 row 34 cfg]
  main : [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_REDACTED>'}}, {'message': 'login with correct horse battery staple failed'}]
  proto: [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_1>'}}, {'message': 'login with <SECRET_1> failed'}]
[M1 Secret credential key short]
  main : [{'kind': 'Secret', 'stringData': {'db_pw': '<SECRET_1>'}}, {'message': 'x<SECRET_1>y <SECRET_1>'}]
  proto: [{'kind': 'Secret', 'stringData': {'db_pw': '<SECRET_1>'}}, {'message': 'x<SECRET_1>y <SECRET_1>'}]
[M4 3 characters]
  main : [{'pin_token': '<SECRET_1>'}, {'message': 'xab1y and <SECRET_1> alone'}]
  proto: [{'pin_token': '<SECRET_1>'}, {'message': 'xab1y and <SECRET_1> alone'}]
[M4 2 characters]
  main : [{'pin_token': '<SECRET_1>'}, {'message': 'a1 alone'}]
  proto: [{'pin_token': '<SECRET_1>'}, {'message': 'a1 alone'}]
[M4 env number + log]
  main : [{'name': 'DB_PW', 'value': 12345678}, {'message': 'pin 12345678 used'}]
  proto: [{'name': 'DB_PW', 'value': '<SECRET_REDACTED>'}, {'message': 'pin 12345678 used'}]
[M4 percent in value + copy]
  main : [{'pw': '<SECRET_1>'}, {'message': 'saw <SECRET_1> and <SECRET_1>'}]
  proto: [{'pw': '<SECRET_1>'}, {'message': 'saw <SECRET_1> and <SECRET_1>'}]
[M4 backslash-u in value + copy]
  main : [{'pw': '<SECRET_1>'}, {'message': 'saw <SECRET_1> and <SECRET_2>'}]
  proto: [{'pw': '<SECRET_1>'}, {'message': 'saw <SECRET_1> and <SECRET_2>'}]
[M4 ESC value + copies]
  main : [{'pw': '<SECRET_1> 2secretXYZ'}, {'message': 'saw <SECRET_1>2secretXYZ and <SECRET_1> 2secretXYZ'}]
  proto: [{'pw': '<SECRET_1>'}, {'message': 'saw hunter<SECRET_2> and <SECRET_1>'}]
[look-alike value]
  main : {'pw': '<SECRET_REDACTED>'}
  proto: {'pw': '<SECRET_1>'}
[look-alike + log]
  main : [{'pw': '<SECRET_REDACTED>'}, {'token': '<SECRET_2>'}, {'message': 'see <SECRET_1>'}]
  proto: [{'pw': '<SECRET_1>'}, {'token': '<SECRET_2>'}, {'message': 'see <SECRET_1>'}]
[one letter]
  main : {'pw': 'p<SECRET_1>ssword=<SECRET_1>'}
  proto: {'pw': '<SECRET_1>'}
[one letter + log]
  main : [{'pw': 'p<SECRET_1>ssword=<SECRET_1>'}, {'message': 'a cat and a hat'}]
  proto: [{'pw': '<SECRET_1>'}, {'message': 'a cat and a hat'}]
[G4 credentials.user + log]
  main : [{'credentials': {'user': '<SECRET_REDACTED>'}}, {'message': 'svc restarted'}]
  proto: [{'credentials': {'user': '<SECRET_REDACTED>'}}, {'message': 'svc restarted'}]
[respelled copies of Secret stringData cfg=P, shown where repeated (script r2_xf.py); main shows every copy]
  proto: XF respelled: base64 of a stringData value || {'annotations': {'last-applied-configuration': 'Y29ycmVjdCBob3JzZSBiYXR0ZXJ5IHN0YXBsZQ=='}}
         XF respelled: hex || {'annotations': {'last-applied-configuration': '636f727265637420686f727365206261747465727920737461706c65'}}
         XF respelled: upper case || {'annotations': {'last-applied-configuration': 'CORRECT HORSE BATTERY STAPLE'}}
         XF respelled: wrapped over two lines || {'annotations': {'last-applied-configuration': 'correct horse\nbattery staple'}}
         XF respelled: double space || {'annotations': {'last-applied-configuration': 'correct  horse battery staple'}}
         XF respelled: JSON inside JSON (annotation of an annotation) || {'annotations': {'last-applied-configuration': '"{\\"cfg\\": \\"<SECRET_1>\\"}"'}}
```
Key rule, random check with NO exclusion (script keycheck.py): `keys tried 200000; accepted by main's rule 107041; of those refused by the new rule (NO exclusion): 0 []`
Cost of many registered values, two passes (script r3_big.py):
```
main : 50 entries, two passes: Secret entries under non-credential keys 0.14s (map 0); one-word values under credential keys 0.04s (map 50)
       256 entries, two passes: Secret entries under non-credential keys 0.78s (map 0); one-word values under credential keys 0.91s (map 256)
       500 entries, two passes: Secret entries under non-credential keys 1.26s (map 0); one-word values under credential keys 1.81s (map 500)
       1000 entries, two passes: Secret entries under non-credential keys 1.54s (map 0); one-word values under credential keys 10.41s (map 1000)
proto: 50 entries, two passes: Secret entries under non-credential keys 0.16s (map 50); one-word values under credential keys 0.06s (map 50)
       256 entries, two passes: Secret entries under non-credential keys 2.14s (map 256); one-word values under credential keys 0.82s (map 256)
       500 entries, two passes: Secret entries under non-credential keys 3.64s (map 256); one-word values under credential keys 4.70s (map 500)
       1000 entries, two passes: Secret entries under non-credential keys 6.37s (map 256); one-word values under credential keys 13.47s (map 1000)
main : large Secret: 2000 entries x ~203 chars = 406890 value chars; one pass: 6002 redactor calls, 833576 counted chars; cap per pass 2*MAX_BUNDLE_CHARS = 4194304; 1.5s
proto: large Secret: 2000 entries x ~203 chars = 406890 value chars; one pass: 4002 redactor calls, 418100 counted chars; cap per pass 2*MAX_BUNDLE_CHARS = 4194304; 3.3s
```
## A3. Model-free fixture (plan review round 2, M1; script r3_fixture.py)
Fixture: the `tests/k1b_support.py` default bundle plus one k8s record of kind Secret named `orders-conn` with the entries LOG_LEVEL=info, DEBUG=true, ENV=prod, PORT=5432, DB_USER=postgres, DB_NAME=orders and DB_PW = a made-up 15-character value (all base64, as a Secret's `data` is), and a second log file of five lines that use those words (the fourth line holds the made-up DB_PW value in clear). A bundle's k8s record has exactly the keys kind, name, as_of, spec, events (`k1b/bundle.py:278`), so the Secret's `data` can only sit under `spec`: shape "spec.data" is `spec: {data: ...}`; shape "spec.manifest" is `spec: {kind: Secret, data: ...}`.
```
spec.data     main : strings outside the Secret 114, changed 0, characters changed 0, distinct log lines changed 0, levels ['error', 'info'], services ['api', 'db', 'orders', 'postgres'], tool calls 24
spec.data     proto: strings outside the Secret 114, changed 1, characters changed 23, distinct log lines changed 1, levels ['error', 'info'], services ['api', 'db', 'orders', 'postgres'], tool calls 24
spec.manifest main : strings outside the Secret 114, changed 0, characters changed 0, distinct log lines changed 0, levels ['error', 'info'], services ['api', 'db', 'orders', 'postgres'], tool calls 24
spec.manifest proto: strings outside the Secret 114, changed 1, characters changed 23, distinct log lines changed 1, levels ['error', 'info'], services ['api', 'db', 'orders', 'postgres'], tool calls 24
tool calls whose list of evidence IDs is equal on main and proto: spec.data 24 of 24; spec.manifest 24 of 24 (20 of the 24 calls return records)
the one log line changed on proto: ['login as postgres with Zq7xkW2vy9JtR4m refused'] -> ['login as postgres with <SECRET_9> refused']
Secret entries as shown, spec.data main : {"data": {"DB_NAME": "b3JkZXJz", "DB_PW": "<SECRET_1>", "DB_USER": "cG9zdGdyZXM=", "DEBUG": "dHJ1ZQ==", "ENV": "cHJvZA==", "LOG_LEVEL": "aW5mbw==", "PORT": "NTQzMg=="}}
Secret entries as shown, spec.data proto: {"data": {"DB_NAME": "<SECRET_7>", "DB_PW": "<SECRET_9>", "DB_USER": "<SECRET_5>", "DEBUG": "<SECRET_2>", "ENV": "<SECRET_3>", "LOG_LEVEL": "<SECRET_1>", "PORT": "<SECRET_4>"}}
Secret entries as shown, spec.manifest main : {"data": {"DB_NAME": "<SECRET_REDACTED>", "DB_PW": "<SECRET_1>", "DB_USER": "<SECRET_REDACTED>", "DEBUG": "<SECRET_REDACTED>", "ENV": "<SECRET_REDACTED>", "LOG_LEVEL": "<SECRET_REDACTED>", "PORT": "<SECRET_REDACTED>"}, "kind": "Secret"}
```
The 24 tool calls: `list_data`; `query_metrics` per shown query; `query_logs` per shown service, with `contains` = orders, postgres, prod, 5432, info, true, retry, and with no filter; `get_deploys` with and without each shown service; `get_k8s` with no filter and per shown kind and name; `get_runbook` per file and with no name.
## A4. Card path: outputs
Columns of each row: text returned by `clean` || tokens the link oracle flags || is `clean(clean(x)) == clean(x)`.
```
[XF respelled, JSON \n copy]
  main : [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_REDACTED>'}}, {'annotations': {'last-applied-configuration': '{"stringData": {"cfg": "line1 horse\\nline2 staple"}}'}}]
  proto: [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_1>'}}, {'annotations': {'last-applied-configuration': '{"stringData": {"cfg": "<SECRET_1>"}}'}}]
[XF respelled, percent copy]
  main : [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_REDACTED>'}}, {'message': 'GET /login?p=correct%20horse%20battery%20staple'}]
  proto: [{'kind': 'Secret', 'stringData': {'cfg': '<SECRET_1>'}}, {'message': 'GET /login?p=<SECRET_1>'}]
[N4 sweep]
  main : 'contact bob.smith@example[.]com' || flat: 'contact bob.smith@example.com'
  proto: 'contact <EMAIL_1>' || flat: 'contact <EMAIL_1>'
[N4 host]
  main : 'restart db01[.]corp[.]internal now' || flat: 'restart db01.corp.internal now'
  proto: 'restart <HOSTNAME_1> now' || flat: 'restart <HOSTNAME_1> now'
[N4 percent]
  main : 'bob%2Esmith%40example%2Ecom' || flat: 'bob.smith@example.com'
  proto: '<EMAIL_1>' || flat: '<EMAIL_1>'
[N4 entity]
  main : 'bob[.]smith&amp;#64;example[.]com' || flat: 'bob.smith@example.com'
  proto: '<EMAIL_1>' || flat: '<EMAIL_1>'
[N4 tag split]
  main : 'bob@example[.]com' || flat: 'bob@example.com'
  proto: '<EMAIL_1>' || flat: '<EMAIL_1>'
[N4 wide dot]
  main : 'bob.smith@example[.]com' || flat: 'bob.smith@example.com'
  proto: '<EMAIL_1>' || flat: '<EMAIL_1>'
[N4 zero width]
  main : 'bob.smith@example[.]com' || flat: 'bob.smith@example.com'
  proto: '<EMAIL_1>' || flat: '<EMAIL_1>'
[N4 tilde fence]
  main : 'see\n~~~\nbob.smith@example[.]com\n~~~\nend' || flat: 'see\n~~~\nbob.smith@example.com\n~~~\nend'
  proto: 'see\n~~~\n<EMAIL_1>\n~~~\nend' || flat: 'see\n~~~\n<EMAIL_1>\n~~~\nend'
[N4 angle]
  main : 'from ‹bob[.]smith@example[.]com> today' || flat: 'from ‹bob.smith@example.com> today'
  proto: 'from ‹<EMAIL_1>> today' || flat: 'from ‹<EMAIL_1>> today'
[N6 ip+domain]
  main : '10[.]0[.]0[.]5[.]evil[.]com' || flat: '10.0.0.5.evil.com'
  proto: '<IPV4_1>[.]evil[.]com' || flat: '<IPV4_1>.evil.com'
[N6 backtick eaten]
  main : 'pw=<SECRET_1> evil.com `evil[.]com` x' || flat: 'pw=<SECRET_1> evil.com `evil.com` x'
  proto: 'pw=<SECRET_1> evil[.]com `evil.com` x' || flat: 'pw=<SECRET_1> evil.com `evil.com` x'
[m3 uuid file]
  main : 'see <UUID_1>[.]json' || flat: 'see <UUID_1>.json'
  proto: 'see <UUID_1>[.]json' || flat: 'see <UUID_1>.json'
[m3 plain file]
  main : 'see report[.]json' || flat: 'see report.json'
  proto: 'see report[.]json' || flat: 'see report.json'
[guard fence]
  main : 'see\n```\nowner: <EMAIL_1>\n```\nend' || flat: 'see\n```\nowner: <EMAIL_1>\n```\nend'
  proto: 'see\n```\nowner: <EMAIL_1>\n```\nend' || flat: 'see\n```\nowner: <EMAIL_1>\n```\nend'
[guard inline]
  main : '`evil.com` and evil[.]com' || flat: '`evil.com` and evil.com'
  proto: '`evil.com` and evil[.]com' || flat: '`evil.com` and evil.com'
[M5 host then slash domain]
  main : 'see db01[.]corp[.]internal/evil.com/p?d=1 now' || bare-domain tokens: [] || idempotent: True
  proto: 'see <HOSTNAME_1>/evil[.]com/p?d=1 now' || bare-domain tokens: [] || idempotent: True
[M5 double dot]
  main : '<IPV4_1>..evil.com' || bare-domain tokens: ['<IPV4_1>..evil.com'] || idempotent: True
  proto: '<IPV4_1>..evil[.]com' || bare-domain tokens: [] || idempotent: True
[M5 ip then domain]
  main : '10[.]0[.]0[.]5[.]evil[.]com' || bare-domain tokens: [] || idempotent: True
  proto: '<IPV4_1>[.]evil[.]com' || bare-domain tokens: [] || idempotent: True
[M5 sentence end after a placeholder]
  main : 'restart db01[.]corp[.]internal. Then wait.' || bare-domain tokens: [] || idempotent: True
  proto: 'restart <HOSTNAME_1>. Then wait.' || bare-domain tokens: [] || idempotent: True
[M5 slash domain, no placeholder (main's rule)]
  main : 'see a/evil.com and /var/log/app.log now' || bare-domain tokens: [] || idempotent: True
  proto: 'see a/evil[.]com and /var/log/app[.]log now' || bare-domain tokens: [] || idempotent: True
[M6 heading]
  main : '\u200b# APPROVED by sec@example[.]com' || bare-domain tokens: [] || idempotent: True
  proto: '# APPROVED by <EMAIL_1>' || bare-domain tokens: [] || idempotent: True
[M6 heading, no identifier]
  main : '# APPROVED' || bare-domain tokens: [] || idempotent: True
  proto: '# APPROVED' || bare-domain tokens: [] || idempotent: True
[M6 quote]
  main : '\u200b> ask sec@example[.]com' || bare-domain tokens: [] || idempotent: True
  proto: '> ask <EMAIL_1>' || bare-domain tokens: [] || idempotent: True
[m1 backtick eaten + wide dot]
  main : 'pw=<SECRET_1> bob.smith@example。com `x` y' || bare-domain tokens: [] || idempotent: False
  proto: 'pw=<SECRET_1> bob[.]smith@example[.]com `x` y' || bare-domain tokens: [] || idempotent: True
[m1 wide dot inside inline code]
  main : '`bob.smith@example。com`' || bare-domain tokens: [] || idempotent: True
  proto: '`bob.smith@example。com`' || bare-domain tokens: [] || idempotent: True
[F6b backtick eaten]
  main : 'pw=<SECRET_1> evil.com `evil[.]com` x' || bare-domain tokens: ['evil.com'] || idempotent: False
  proto: 'pw=<SECRET_1> evil[.]com `evil.com` x' || bare-domain tokens: [] || idempotent: True
[N4 sweep]
  main : 'contact bob.smith@example[.]com' || bare-domain tokens: [] || idempotent: True
  proto: 'contact <EMAIL_1>' || bare-domain tokens: [] || idempotent: True
[N4 percent]
  main : 'bob%2Esmith%40example%2Ecom' || bare-domain tokens: [] || idempotent: True
  proto: '<EMAIL_1>' || bare-domain tokens: [] || idempotent: True
[N4 entity]
  main : 'bob[.]smith&amp;#64;example[.]com' || bare-domain tokens: [] || idempotent: True
  proto: '<EMAIL_1>' || bare-domain tokens: [] || idempotent: True
[m3 uuid file]
  main : 'see <UUID_1>[.]json' || bare-domain tokens: [] || idempotent: True
  proto: 'see <UUID_1>[.]json' || bare-domain tokens: [] || idempotent: True
[guard fence domain]
  main : 'x\n```\nevil.com\n```\ny evil[.]com' || bare-domain tokens: [] || idempotent: True
  proto: 'x\n```\nevil.com\n```\ny evil[.]com' || bare-domain tokens: [] || idempotent: True
[N9 fixed case]
  main : '<SECRET_2>3D\npw=<SECRET_1>' || bare-domain tokens: [] || idempotent: True
  proto: '<SECRET_3>3D\n<SECRET_1><SECRET_2>' || bare-domain tokens: [] || idempotent: True
main : P2 texts=4000 leak=2619 bare_domain(token scan)=5 flagged_only_without_the_exemptions=1796 not_idempotent=12 seconds=11.3
proto: P2 texts=4000 leak=0 bare_domain(token scan)=0 flagged_only_without_the_exemptions=0 not_idempotent=0 seconds=9.1
main : N9 texts=3000 with_a_first_pass_original_readable=1 seconds=3.4
proto: N9 texts=3000 with_a_first_pass_original_readable=0 seconds=5.8
main : N9 fixed case || '<SECRET_2>3D\npw=<SECRET_1>' || bare-domain tokens: [] || idempotent: True
proto: N9 fixed case || '<SECRET_3>3D\n<SECRET_1><SECRET_2>' || bare-domain tokens: [] || idempotent: True
summary() (script r2_m7.py)
main : M7 summary target='db01.corp.internal' || 'agent-ops asks to run restart_service v1 (reversible) on db01[.]corp[.]internal. Inputs: {"service":"orders"}. Expected: service restarted. Plan 420009ccba34.'
       M7 summary target='crm' || 'agent-ops asks to run restart_service v1 (reversible) on crm. Inputs: {"host":"db01[.]corp[.]internal","owner":"bob.smith@example[.]com"}. Expected: service restarted. Plan f940208aba6e.'
       M7 summary target='10.20.30.40' || 'agent-ops asks to run restart_service v1 (reversible) on <IPV4_1>. Inputs: {"service":"orders"}. Expected: service restarted. Plan 17253dec5943.'
proto: M7 summary target='db01.corp.internal' || 'agent-ops asks to run restart_service v1 (reversible) on <HOSTNAME_1>. Inputs: {"service":"orders"}. Expected: service restarted. Plan 5e1d7b417aff.'
       M7 summary target='crm' || 'agent-ops asks to run restart_service v1 (reversible) on crm. Inputs: {"host":"<HOSTNAME_1>","owner":"<EMAIL_1>"}. Expected: service restarted. Plan bf1c92decfe1.'
       M7 summary target='10.20.30.40' || 'agent-ops asks to run restart_service v1 (reversible) on <IPV4_1>. Inputs: {"service":"orders"}. Expected: service restarted. Plan 56e9f62702fd.'
Slack block with a raw req.summary (script r3_slack.py; first two lines main, last two proto)
N5 Slack block, raw req.summary 'contact bob.smith@example.com at db01.corp.internal' -> 'contact bob.smith@example[.]com at db01[.]corp[.]internal'
N5 Slack block, raw req.summary 'ping 10.20.30.40@channel' -> 'ping <IPV4_1>@channel'
N5 Slack block, raw req.summary 'contact bob.smith@example.com at db01.corp.internal' -> 'contact <EMAIL_1> at <HOSTNAME_1>'
N5 Slack block, raw req.summary 'ping 10.20.30.40@channel' -> 'ping <IPV4_1>at-channel'
```
Inputs of the rows above:
```python
rows = [("M5 host then slash domain", "see db01.corp.internal/evil.com/p?d=1 now"), ("M5 double dot", "10.0.0.5..evil.com"), ("M5 ip then domain", "10.0.0.5.evil.com"),
  ("M5 sentence end after a placeholder", "restart db01.corp.internal. Then wait."), ("M5 slash domain, no placeholder (main's rule)", "see a/evil.com and /var/log/app.log now"),
  ("M6 heading", "# APPROVED by sec@example.com"), ("M6 heading, no identifier", "# APPROVED"), ("M6 quote", "> ask sec@example.com"),
  ("m1 backtick eaten + wide dot", PW + "=ab`cd bob.smith@example。com `x` y"), ("m1 wide dot inside inline code", "`bob.smith@example。com`"),
  ("F6b backtick eaten", PW + "=ab`cd evil.com `evil.com` x"), ("N4 sweep", "contact bob.smith@example.com"), ("N4 percent", "bob%2Esmith%40example%2Ecom"),
  ("N4 entity", "bob.smith&#64;example.com"), ("m3 uuid file", "see 123e4567-e89b-12d3-a456-426614174000.json"), ("guard fence domain", "x\n```\nevil.com\n```\ny evil.com"),
  ("N9 fixed case", "<i></i>" + ONE + "3D\n" + PW + "=" + PW + "=<i></i> " + ONE + "</b>")]

```
## A5. Random test of the credential-key path (P1): outputs
```
main : P1 seed=20261111 cases=3000 run=3000 refused=0 over_255=165 (a) shown value not placeholders/fixed mask: 2391; (b) a rare-alphabet run readable under the key: 2177; (c) checked 1264, readable in the second record: 1051; seconds=34.8
proto: P1 seed=20261111 cases=3000 run=3000 refused=0 over_255=165 (a) shown value not placeholders/fixed mask: 0; (b) a rare-alphabet run readable under the key: 0; (c) checked 1264, readable in the second record: 62; seconds=24.1
proto: (c) simple values (alphabet words, white space, break characters only): checked 241 readable 0
proto, the same generator with only ONE group of extra characters (1,200 cases each; last two 3,000):
== ascii punctuation
(a) shown value not placeholders/fixed mask: 0; (b) a rare-alphabet run readable under the key: 0; (c) checked 809, readable in the second record: 0; seconds=7.8
== ascii punctuation without < >
(a) shown value not placeholders/fixed mask: 0; (b) a rare-alphabet run readable under the key: 0; (c) checked 844, readable in the second record: 0; seconds=10.2
== escapes
(a) shown value not placeholders/fixed mask: 0; (b) a rare-alphabet run readable under the key: 0; (c) checked 798, readable in the second record: 0; seconds=13.5
== controls
(a) shown value not placeholders/fixed mask: 0; (b) a rare-alphabet run readable under the key: 0; (c) checked 389, readable in the second record: 2; seconds=11.7
== full width
(a) shown value not placeholders/fixed mask: 0; (b) a rare-alphabet run readable under the key: 0; (c) checked 854, readable in the second record: 0; seconds=9.1
== look-alike
(a) shown value not placeholders/fixed mask: 0; (b) a rare-alphabet run readable under the key: 0; (c) checked 915, readable in the second record: 0; seconds=6.4
== visible ascii (3000 cases)
(a) shown value not placeholders/fixed mask: 0; (b) a rare-alphabet run readable under the key: 0; (c) checked 2062, readable in the second record: 0; seconds=21.7
== visible ascii and look-alike (3000 cases)
(a) shown value not placeholders/fixed mask: 0; (b) a rare-alphabet run readable under the key: 0; (c) checked 2086, readable in the second record: 0; seconds=22.1
```
## B. The prototype's production text (the builder may reshape it; then every `old` string of the mutant list is taken from the built code)
`k1b/redaction.py` (replaces lines 41-46 `LIMITS` and lines 86-152):
```python
LIMITS = (
    "The redactor is pattern based. It does not catch names in free text, customer or project names, ticket "
    "numbers, values in unusual formats, or anything else no pattern matches. A value under a key that names a "
    "credential, and every entry of a Kubernetes Secret, is always masked under its own key. The same value is "
    "also masked where it is repeated elsewhere in the case only when all of this holds: it is a text of 4 to "
    "255 characters directly under that key; it is made of printable ASCII characters and white space; it does "
    "not hold both kinds of quote mark; no part of it is something another pattern masks (an e-mail address, a "
    "host name, a key); and the copy is spelled the same way. An entry of a Secret under a key that does not "
    "name a credential is masked elsewhere only when it also has at least 8 characters and is not all digits or "
    "one lower-case word. Not masked where repeated: longer or shorter values, numbers, values nested deeper "
    "under a credential key, values with control or other special characters, and copies in another spelling "
    "(base64, capitals, wrapped over lines). A setting about a credential (a key that ends in enabled, policy, "
    "count, expiry and the like) is shown only when its value is a yes or no word, a number or a time. Masking "
    "is a first filter, not proof that no client data reached the model."
)

MASKED = "<SECRET_REDACTED>"
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SPLIT = re.compile(r"[_.\-\s]+")
_TRAILING_DIGITS = re.compile(r"(?<=[a-z])[0-9]+$")
CREDENTIAL_WORDS = frozenset(
    "pass password passwords passwd pwd passphrase secret secrets token apikey apikeys authorization auth "
    "credential credentials bearer session sessionid jsessionid phpsessid sessid".split()
)
GLUED_ENDINGS = (
    "password", "passwd", "pwd", "passphrase", "secret", "token", "apikey", "secretkey", "accesskey",
    "privatekey", "sessionid", "sessid",
)  # fmt: skip
# (word before, word): `api_key`, `client-key-data`, `connect.sid`
WORD_PAIRS = frozenset(
    {(q, k) for q in "api private access secret signing encryption account".split() for k in ("key", "keys")}
    | {("key", "data"), ("cert", "data"), ("certificate", "data"), ("connect", "sid")}
)
COUNT_WORDS_BEFORE_TOKENS = frozenset("max min input output prompt completion total cached".split())
SETTING_WORDS = frozenset("enabled disabled required policy length count age days ttl expiry expires".split())
SETTING_VALUE = re.compile(r"(?i)true|false|yes|no|on|off|none|[0-9]{1,10}[smhdw]?")


def _key_words(key: str) -> list[str]:
    return [_TRAILING_DIGITS.sub("", w) for w in _SPLIT.split(_CAMEL.sub("_", key).lower()) if w]


def sensitive(key: object) -> bool:
    """Does a key (or the name of a named entry) say its value is a credential? No exception by suffix."""
    if not isinstance(key, str):
        return False
    words = _key_words(key)
    for i, w in enumerate(words):
        before = words[i - 1] if i else ""
        after = words[i + 1] if i + 1 < len(words) else ""
        if w in CREDENTIAL_WORDS or w.endswith(GLUED_ENDINGS) or (before, w) in WORD_PAIRS:
            return True
        if w == "tokens" and before not in COUNT_WORDS_BEFORE_TOKENS and after != "used":
            return True
    return False


def _setting_key(key: object) -> bool:
    """A credential key whose last word says the entry is a setting ABOUT a credential (`..._policy_enabled`)."""
    return sensitive(key) and _key_words(str(key))[-1] in SETTING_WORDS


def _setting_value(obj: Any) -> bool:
    """The only values shown under a setting key: a bool, None, a number, a timestamp, a short on/off word or count."""
    if obj is None or isinstance(obj, bool | int | float):
        return True
    return isinstance(obj, str) and (
        parse_ts(obj) is not None or SETTING_VALUE.fullmatch(obj) is not None
    )


FALLBACK_KEY = "secret"
MAX_SPELLING_CHARS = 255
MIN_REGISTER_CHARS = 8
MAX_REGISTERED_ENTRIES = 256  # per `data` / `stringData` of one Secret; later entries get the fixed mask
_PLAIN_CHARS = frozenset(chr(c) for c in range(0x21, 0x7F)) - frozenset(";&,\"'")
_SAFE_KEY = re.compile(r"[A-Za-z0-9_.\-]{1,60}")
_ONE_LOWER_WORD = re.compile(r"[a-z]+")
_ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})+")


def _attempts(key: str, text: str, credential: bool) -> list[tuple[str, str]]:
    """(key to write, quote) for one spelling of a value, in the order tried."""
    if not text or len(text) > MAX_SPELLING_CHARS:
        return []
    if not credential and (
        len(text) < MIN_REGISTER_CHARS or text.isdigit() or _ONE_LOWER_WORD.fullmatch(text)
    ):
        return []
    if all(c in _PLAIN_CHARS for c in text):
        own = [(key, "")] if credential and _SAFE_KEY.fullmatch(key) else []
        return [*own, (FALLBACK_KEY, "")]
    quote = next((q for q in ('"', "'") if q not in text), None)
    return [(FALLBACK_KEY, quote)] if quote else []


def _accepted(key: str, text: str, credential: bool, f: Callable[[str], str]) -> str | None:
    for k, quote in _attempts(key, text, credential):
        masked = f(f"{k}={quote}{text}{quote}")
        if not masked.startswith(k + "="):
            continue
        part = masked[len(k) + 1 :]
        if quote:
            if len(part) < 2 or part[0] != quote or part[-1] != quote:
                continue
            part = part[1:-1]
        if _ONLY_PLACEHOLDERS.fullmatch(part):
            return part
    return None


def _pair(key: str, value: str, f: Callable[[str], str], known_secret: bool = False) -> str:
    """A value whose key names a credential, or an entry of a Secret. Returned only as placeholders, else `MASKED`."""
    credential = sensitive(key)
    if not credential and not known_secret:
        f(value)
        return MASKED
    spellings = [value]
    try:
        spellings.append(base64.b64decode(value, validate=True).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, ValueError):
        pass
    result = None
    for text in spellings:
        got = _accepted(key, text, credential, f)
        if got is None:
            continue
        result = got
        if not known_secret:
            return result
    if result is not None:
        return result
    f(value)
    return MASKED


def _named(obj: dict) -> tuple[Any, Any]:
    """(name, the key that holds the value) of an entry shaped {name|key: ..., value: ...}, in any letter case."""
    nk = next((k for k in obj if isinstance(k, str) and k.lower() in ("name", "key")), None)
    vk = next((k for k in obj if isinstance(k, str) and k.lower() == "value"), None)
    if nk is None or vk is None or not sensitive(obj[nk]):
        return None, None
    return obj[nk], vk


def _walk_dict(
    obj: dict, f: Callable[[str], str], sens: bool, known_secret: bool, secret: bool
) -> dict[Any, Any]:
    """One dict. `secret`: this dict is a Kubernetes Secret, or the `spec` of a record whose kind is Secret (a bundle's
    k8s record has exactly the keys kind, name, as_of, spec, events, so the Secret's `data` sits under `spec`)."""
    name, value_key = _named(obj)
    out: dict[Any, Any] = {}
    for k, v in obj.items():
        if value_key is not None and k == value_key:
            out[_key(k, f)] = _walk(v, f, str(name), sens, known_secret)
        elif secret and k in ("data", "stringData") and isinstance(v, dict):
            out[_key(k, f)] = {
                _key(kx, f): _walk(vx, f, str(kx), True, i < MAX_REGISTERED_ENTRIES)
                for i, (kx, vx) in enumerate(v.items())
            }
        elif secret and k == "spec" and isinstance(v, dict):
            out[_key(k, f)] = _walk_dict(v, f, sens, known_secret, True)
        else:
            out[_key(k, f)] = _walk(v, f, k, sens, known_secret)
    return out


def _walk(
    obj: Any,
    f: Callable[[str], str],
    key: str | None = None,
    secret_data: bool = False,
    known_secret: bool = False,
) -> Any:
    own = sensitive(key)
    sens = secret_data or own
    if own and not secret_data and _setting_key(key) and _setting_value(obj):
        return obj
    if isinstance(obj, str):
        if parse_ts(obj) is not None:
            return obj
        if key is not None and sens:
            return _pair(key, obj, f, known_secret)
        return f(obj)
    if isinstance(obj, int | float) and not isinstance(obj, bool) and sens:
        return MASKED
    if isinstance(obj, dict):
        return _walk_dict(obj, f, sens, known_secret, obj.get("kind") == "Secret")
    if isinstance(obj, list):
        return [_walk(v, f, key, sens, known_secret) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_walk(v, f, key, sens, known_secret) for v in obj)
    return obj

```
`approvals/gate.py` (new and changed helpers; `sanitise_text`, `_all_prose`, `_clean_prose`, `_clean_line` only pass `defang` on):
```python
def _outside_code(line: str, fn) -> str:
    parts = [line] if "``" in line else _INLINE_CODE.split(line)
    return "".join(part if i % 2 else fn(part) for i, part in enumerate(parts))


def _fold_dots(part: str) -> str:
    return _WIDE_DOTS.sub(".", part)


# The last step's own rule, on top of the two domain patterns: outside code, EVERY dot that has a letter, a digit or
# the `>` of a placeholder before it and two or more letters after it is bracketed. It covers what the look-behind of
# `_DOMAIN` leaves (`<IPV4_1>.evil.com`, `<HOSTNAME_1>/evil.com/p`, `a/evil.com`, `.evil.com`).
_ANY_NAME_DOT = re.compile(r"(?<=[^\W_]|>)\.(?=[^\W\d_]{2})")


def _bracket_dots(part: str) -> str:
    part = _DOMAIN.sub(_defang, _NON_ASCII_HOST.sub(_defang, part))
    # a mention word right after a masked value (`<HOSTNAME_1>@here`) was no mention before the redaction
    return _MENTION.sub(r"at-\1", _ANY_NAME_DOT.sub("[.]", part))


def _defang_outside_code(line: str) -> str:
    return _outside_code(
        line, lambda p: _DOMAIN.sub(_defang, _NON_ASCII_HOST.sub(_defang, _fold_dots(p)))
    )


def defang_domains(text: str) -> str:
    """Last step: brackets around the dots of every domain outside code. Only adds characters."""
    lines = text.split("\n")
    code: set[int] = set()
    for start, last, char in _closed_fences(text):
        if char == "`":
            code.update(range(start + 1, last))
    return "\n".join(
        line if i in code else _outside_code(line, lambda p: _bracket_dots(_fold_dots(p)))
        for i, line in enumerate(lines)
    )

    # last line of _clean_line:
    return _defang_outside_code(line) if defang else _outside_code(line, _fold_dots)
```
`approvals/channel.py`:
```python
    text = text.replace("\x00", "")
    mapping = _seeded(text)
    out = redact_for_people(text, mapping)
    # A key and a value split by markup (`password%<i></i>3Dx`) read as one only when the tags are DELETED, not turned
    # into spaces: that joined view (real placeholders and line breaks kept) is used when it finds a secret value the
    # text pass did not (compared by the originals, spaces ignored), not by count or kind.
    joined = _TAGS.sub("", text)
    if joined != text:
        joined_map = runmap.RunMap({**_seeded(joined), **mapping})
        alt = redact_for_people(joined, joined_map)
        if _assignment_originals(joined_map) - _assignment_originals(mapping):
            return alt
    return out

def _neutralise(text: str) -> str:
    return withhold_commands(sanitise_text(text, defang=False))


def redact_for_people(text: str, mapping: dict[str, str]) -> str:
    return defang_domains(runmap.redact_text(text, mapping, neutralise=_neutralise))

```
## C. Generators and oracles for the random tests (paste into `tests/test_q8b_random.py`; nothing may be read from the author's folder)
```python
# --- P1 (seed 20261111, 3,000 cases)
SEED, CASES = 20261111, 3000
PW = "pass" + "word"
ALPHA = "qxzjkwvy"
SPACE = [chr(c) for c in range(0x3000) if chr(c).isspace()]
BREAK = list(";&,\"'")
ODD = ["\x1b[0m", "\x08", "\x7f", "%20", "%3B", "\\u0041", "\\n", "&#59;", "<", ">", "=", ":", "|", "/", "@", "ａｂ", "＂", "＇", "​", "‍", "<SECRET_1>"]
COMPOSITE = ["bob.smith@example.com", "db01.corp.internal", "AKIA" + "IOSFODNN7EXAMPLE", "10.20.30.40"]
KEYS = [PW, "api_key", "clientSecret", "accessToken", "PG" + PW.upper(), "pwd", "authorization", "private_key", "bearer", "passphrase", "refresh_tokens", "session", PW + "_for_the_primary_database_replica"]
ENDS = set(SPACE) | set(BREAK)
def word(rng): return "".join(rng.choice(ALPHA + "0123456789") for _ in range(rng.randint(4, 9)))
def value(rng):
    target = rng.randint(256, 300) if rng.random() < 0.06 else rng.randint(1, 255)
    out = ""
    while len(out) < target:
        r = rng.random()
        out += word(rng) if r < 0.55 else rng.choice(SPACE) if r < 0.75 else rng.choice(BREAK) if r < 0.85 else rng.choice(ODD) if r < 0.97 else rng.choice(COMPOSITE)
    return out[:target]
def runs(v):
    out, cur = [], ""
    for ch in v:
        if ch in ENDS:
            if len(cur) >= 4: out.append(cur)
            cur = ""
        else: cur += ch
    if len(cur) >= 4: out.append(cur)
    return [r for r in out if all(c in ALPHA + "0123456789" for c in r)]   # runs made only of the rare alphabet

# --- "outside code" and the link oracle (a plain token scan; the exemptions E1-E3 are NOT used: call with exempt=False)
def outside_code(text):
    code = set()
    for s, l, ch in gate._closed_fences(text):
        if ch == "`": code.update(range(s + 1, l))
    out = []
    for i, line in enumerate(text.split("\n")):
        if i in code: continue
        segs = [line] if "``" in line else gate._INLINE_CODE.split(line)
        out += [seg for k, seg in enumerate(segs) if k % 2 == 0]
    return out
# ---- link oracle: a plain token scan, no regex shared with the implementation
def bare_domain_tokens(text, exempt=True):
    """A token (split at white space, outside code) fails when, with every `[.]` read as `|`, it still holds
    letter-or-digit-or-`>` then `.` then two or more letters. Three exemptions, each main's own stated rule:
    E1 the dot is in the part before an `@` (an e-mail's local part); E2 the letters after the dot are directly followed
    by a digit, `_`, `-` or `@` (not the shape of a top-level domain); E3 the label starts right after `/` and the token
    holds no placeholder."""
    bad = []
    for seg in outside_code(text):
        for tok in seg.split():
            t = tok.replace("[.]", "|")
            for i, ch in enumerate(t):
                if ch != "." or i == 0 or not (t[i - 1].isalnum() or t[i - 1] == ">"):
                    continue
                j = i + 1
                while j < len(t) and t[j].isalpha():
                    j += 1
                if j - (i + 1) < 2:
                    continue
                if exempt:
                    if "@" in t[i:]:
                        continue  # E1
                    if j < len(t) and (t[j].isdigit() or t[j] in "_-@"):
                        continue  # E2
                    k = i
                    while k > 0 and (t[k - 1].isalnum() or t[k - 1] in "-_"):
                        k -= 1
                    if k > 0 and t[k - 1] == "/" and "<" not in t:
                        continue  # E3
                bad.append(tok)
                break
    return bad

# --- P2 (seed 8, 4,000 cases)
IDS = ["bob.smith@example.com", "a.b-c@mail.corp.example.org", "db01.corp.internal", "pay-api.prod.svc.cluster.local", "10.20.30.40", "wiki.corp.internal", "priya.nair@example.co.in"]
NOISE = ["contact", "restart", "\t\t", " ", "\n", "```\n", "\n```\n", "`", "~~~\n", "<b>", "</b>", "@here", "**", "> ", "# ", "- ", PW + "=", "see", "(", ")", "[x]", "<", ">", "&lt;", "%40", "。", ",", ";", ":", "/", "evil.com", "http://"]
def p2_text(rng):
    parts = [rng.choice(IDS if rng.random() < 0.4 else NOISE) for _ in range(rng.randint(1, 9))]
    return "".join(p if rng.random() < 0.5 else " " + p + " " for p in parts)

# --- N9 (seed 9, 3,000 cases)
N9_IDS = ["bob.smith@example.com", "db01.corp.internal", "10.20.30.40", "wiki.corp.internal"]
N9_SEC = [ONE, "Zx9" + "tailpart77"]
N9_BITS = ["<b>", "</b>", "<i></i>", "<span x>", " ", "\n", PW + "=", PW + "%", "3D", "token: ", "note", ";", "<br/> "]
def n9_text(rng):
    return "".join(rng.choice(N9_IDS + N9_SEC if rng.random() < 0.45 else N9_BITS) for _ in range(rng.randint(2, 10)))
def n9_readable(text):
    m1 = C._seeded(text.replace("\x00", ""))
    first = C.redact_for_people(text, m1) if hasattr(C, "redact_for_people") else runmap.redact_text(text, m1, neutralise=C._neutralise)
    flat = clean(text).replace("[.]", ".")
    return [o for o in m1.values() if not o.startswith("\0seed") and len(o) >= 4 and re.search(r"(?<![A-Za-z0-9])" + re.escape(o) + r"(?![A-Za-z0-9])", flat)]

```
