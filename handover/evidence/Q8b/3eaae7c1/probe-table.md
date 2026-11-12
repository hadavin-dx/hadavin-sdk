# probe table (own script, probe/probe.py). R = value readable in the redacted text, M = masked. Columns: head, b7d7cd18, main. Values are made-up words.

| case | head | b7d7cd18 | main |
|---|---|---|---|
| flag --apiTokens V | M | R | R |
| kv apiTokens=V | M | M | M |
| flag --accessTokens V | M | R | R |
| kv accessTokens=V | M | M | M |
| flag --refreshTokens V | M | R | R |
| kv refreshTokens=V | M | M | M |
| flag --idTokens V | M | R | R |
| kv idTokens=V | M | M | M |
| flag --accesstokens V | M | R | R |
| kv accesstokens=V | M | M | M |
| flag --idtokens V | M | R | R |
| kv idtokens=V | M | M | M |
| flag --authtokens V | M | R | R |
| kv authtokens=V | M | M | M |
| flag --apitokens V | M | R | R |
| kv apitokens=V | M | M | M |
| flag --maxTokens V | R | R | R |
| kv maxTokens=V | M | M | M |
| flag --max_tokens V | R | R | R |
| kv max_tokens=V | M | M | M |
| flag --input_tokens V | R | R | R |
| kv input_tokens=V | M | M | M |
| flag --audio_tokens V | R | R | R |
| kv audio_tokens=V | M | M | M |
| flag --tokens V | R | R | R |
| kv tokens=V | M | M | M |
| wget --no-cookies url | R | M | R |
| wget --keep-session-cookies url | R | M | R |
| wget --junk-session-cookies url | R | M | R |
| wget --load-cookies url | R | M | R |
| wget --save-cookies url | R | M | R |
| wget --cookie url | M | M | M |
| wget --set-cookie url | M | M | R |
| wget --session_cookie url | M | M | R |
| wget --cookies url | R | M | R |
| curl -b url-ish | M | M | M |
| cookie_name=V | M | R | R |
| cookie_name: V | M | R | R |
| cookie-policy=V | M | R | R |
| kv possession_id=V | R | M | M |
| kv obsession_id=V | R | M | M |
| kv bypass_key=V | R | M | R |
| kv compass_code=V | R | M | R |
| kv bypass_code=V | R | M | R |
| kv xbypass_key=V | M | M | R |
| kv bypasspass_key=V | M | M | R |
| kv session_id=V | M | M | M |
| kv pass_code=V | M | M | R |
| kv passkey=V | M | M | R |
| kv auth_value=V | M | M | R |
| --authorization Bearer V | M | M | M |
| Authorization: Bearer V | M | M | M |
| --authorization=Bearer V | M | M | M |
| --authorization Basic V | M | M | M |
| Authorization: Basic V | M | M | M |
| --authorization=Basic V | M | M | M |
| --authorization Digest V | M | M | R |
| Authorization: Digest V | M | M | M |
| --authorization=Digest V | M | M | M |
| --authorization Token V | M | M | R |
| Authorization: Token V | M | M | M |
| --authorization=Token V | M | M | M |
| --authorization NTLM V | M | R | R |
| Authorization: NTLM V | M | M | M |
| --authorization=NTLM V | M | M | M |
| --authorization Negotiate V | M | R | R |
| Authorization: Negotiate V | M | M | M |
| --authorization=Negotiate V | M | M | M |
| --authorization OAuth V | M | R | R |
| Authorization: OAuth V | M | M | M |
| --authorization=OAuth V | M | M | M |
| --authorization Splunk V | M | R | R |
| Authorization: Splunk V | M | M | M |
| --authorization=Splunk V | M | M | M |
| --authorization Hawk V | M | R | R |
| Authorization: Hawk V | M | M | M |
| --authorization=Hawk V | M | M | M |
| --authorization AWS4-HMAC-SHA256 V | R | R | R |
| Authorization: AWS4-HMAC-SHA256 V | R | R | R |
| --authorization=AWS4-HMAC-SHA256 V | M | M | R |
| --authorization Bearer 'V' | M | R | R |
| --authorization "Bearer V" | M | M | M |
| --bearer V | M | M | M |
| Digest quoted hdr | M | M | R |
| --authorization Digest quoted | M | R | R |
| Digest json one-line | M | M | R |
| Digest newline then prose | R | M | R |
| Digest line | M | M | R |
| 0 prefix words --P-password V | M | M | M |
| 0 prefix words _ --P_password V | M | M | M |
| 1 prefix words --P-password V | M | M | M |
| 1 prefix words _ --P_password V | M | M | R |
| 2 prefix words --P-password V | M | M | M |
| 2 prefix words _ --P_password V | M | M | R |
| 3 prefix words --P-password V | M | M | R |
| 3 prefix words _ --P_password V | M | M | R |
| 4 prefix words --P-password V | M | R | R |
| 4 prefix words _ --P_password V | M | R | R |
| 5 prefix words --P-password V | M | R | R |
| 5 prefix words _ --P_password V | M | R | R |
| 6 prefix words --P-password V | M | M | M |
| 6 prefix words _ --P_password V | M | R | R |
| 7 prefix words --P-password V | R | R | R |
| 7 prefix words _ --P_password V | R | R | R |
| --cloud-sql-proxy-db-password V | M | R | R |
| pass1=V (1 digits) | M | M | R |
| pass12=V (2 digits) | M | M | R |
| pass12345678=V (8 digits) | M | M | R |
| pass123456789=V (9 digits) | M | M | R |
| pass1234567890=V (10 digits) | M | R | R |
| pass12345678901=V (11 digits) | M | R | R |
| pass1234567890123456789012345678901234567890=V (40 digits) | R | R | R |
| pass12345678901234567890123456789012345678901=V (41 digits) | R | R | R |
| password1234567890123456789012345678901234567890 = V | R | R | R |
| --pass2 V W | R | R | R |
| --password V W | R | R | R |
| --newpass V W | R | R | R |
| authorization= V W | R | R | R |

# record-walk key rule (k1b sensitive): True = value masked under that key

| key | head | b7d7cd18 | main |
|---|---|---|---|
| apiTokens | True | True | False |
| accessTokens | True | True | False |
| refreshTokens | True | True | False |
| idTokens | True | True | False |
| accesstokens | True | False | False |
| idtokens | True | False | False |
| authtokens | True | False | False |
| apitokens | True | False | False |
| maxTokens | False | False | False |
| max_tokens | False | False | False |
| input_tokens | False | False | False |
| audio_tokens | False | False | False |
| tokens | True | True | False |
| cookie | True | True | False |
| cookies | True | True | False |
| set-cookie | True | True | False |
| session_cookie | True | True | False |
| cookie_name | True | True | False |
| cookie-policy | True | True | False |
| no-cookies | True | True | False |
| possession_id | False | False | False |
| obsession_id | False | False | False |
| bypass_key | False | False | False |
| compass_code | False | False | False |
| bypass_code | False | False | False |
| xbypass_key | True | True | False |
| bypasspass_key | True | True | False |
| session_id | True | True | False |
| pass_code | True | True | True |
| authorization | True | True | True |
| pass2 | True | True | False |
| password | True | True | True |
| newpass | True | True | False |
| pass1234567890 | True | True | False |
| password1234567890123456789012345678901234567890 | True | True | False |
