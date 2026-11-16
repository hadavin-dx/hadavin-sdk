# probe9 table: cell = redact/clean ; R readable, M masked ; columns head, 3eaae7c1, main

## readable on head, masked on main
| Authorization: Token<LF>val | R/R | R/R | M/M |
| Authorization: Token<CRLF>val | R/R | R/R | M/M |
| Authorization: ApiKey<LF>val | R/R | R/R | M/M |
| Authorization: ApiKey<CRLF>val | R/R | R/R | M/M |
| Authorization: Digest<LF>val | R/R | R/R | M/M |
| Authorization: Digest<CRLF>val | R/R | R/R | M/M |
| Basic+LF+lowercase16 alone | R/R | R/R | M/M |
| Token+LF+lowercase16 alone | R/R | R/R | M/M |
| kv bypass=V | R/R | R/R | M/M |
| colon bypass: V | R/R | R/R | M/M |
| json bypass | R/R | R/R | M/M |
| json compass_code | R/R | R/R | M/M |
| json compass_key | R/R | R/R | M/M |
| json overpass_key | R/R | R/R | M/M |
| kv possession_id=V | R/R | R/R | M/M |
| colon possession_id: V | R/R | R/R | M/M |
| json possession_id | R/R | R/R | M/M |
| kv obsession_id=V | R/R | R/R | M/M |
| colon obsession_id: V | R/R | R/R | M/M |
| json obsession_id | R/R | R/R | M/M |
| json encompass_key | R/R | R/R | M/M |

## readable on head, masked on 3eaae7c1

## all cells readable on head
| Authorization: Token<LF>val | R/R | R/R | M/M |
| Authorization: Token<CRLF>val | R/R | R/R | M/M |
| Authorization: ApiKey<LF>val | R/R | R/R | M/M |
| Authorization: ApiKey<CRLF>val | R/R | R/R | M/M |
| Authorization: Digest<LF>val | R/R | R/R | M/M |
| Authorization: Digest<CRLF>val | R/R | R/R | M/M |
| Digest+LF+prose | R/R | R/R | R/R |
| Basic+LF+lowercase16 alone | R/R | R/R | M/M |
| Token+LF+lowercase16 alone | R/R | R/R | M/M |
| Basic+LF+prose short | R/R | R/R | R/R |
| kv bypass=V | R/R | R/R | M/M |
| colon bypass: V | R/R | R/R | M/M |
| json bypass | R/R | R/R | M/M |
| kv compass_code=V | R/R | R/R | R/R |
| colon compass_code: V | R/R | R/R | R/R |
| json compass_code | R/R | R/R | M/M |
| kv compass_key=V | R/R | R/R | R/R |
| colon compass_key: V | R/R | R/R | R/R |
| json compass_key | R/R | R/R | M/M |
| kv overpass_key=V | R/R | R/R | R/R |
| colon overpass_key: V | R/R | R/R | R/R |
| json overpass_key | R/R | R/R | M/M |
| kv possession_id=V | R/R | R/R | M/M |
| colon possession_id: V | R/R | R/R | M/M |
| json possession_id | R/R | R/R | M/M |
| kv obsession_id=V | R/R | R/R | M/M |
| colon obsession_id: V | R/R | R/R | M/M |
| json obsession_id | R/R | R/R | M/M |
| kv encompass_key=V | R/R | R/R | R/R |
| colon encompass_key: V | R/R | R/R | R/R |
| json encompass_key | R/R | R/R | M/M |
| wget --no-cookies url | R/M | R/M | R/M |
| wget --no-cookies V | R/R | R/R | R/R |
| curl --no-cookies V | R/R | R/R | R/R |
| wget --keep-session-cookies url | R/M | R/M | R/M |
| wget --keep-session-cookies V | R/R | R/R | R/R |
| curl --keep-session-cookies V | R/R | R/R | R/R |
| wget --junk-session-cookies url | R/M | R/M | R/M |
| wget --junk-session-cookies V | R/R | R/R | R/R |
| curl --junk-session-cookies V | R/R | R/R | R/R |
| wget --load-cookies url | R/M | R/M | R/M |
| wget --load-cookies V | R/R | R/R | R/R |
| curl --load-cookies V | R/R | R/R | R/R |
| wget --save-cookies url | R/M | R/M | R/M |
| wget --save-cookies V | R/R | R/R | R/R |
| curl --save-cookies V | R/R | R/R | R/R |
| wget --cookies url | R/M | R/M | R/M |
| wget --cookies V | R/R | R/R | R/R |
| curl --cookies V | R/R | R/R | R/R |
| passwordxxxxxxxxxxxxxxxxxxxxx=V | R/R | R/R | R/R |
| api_keyxxxxxxxxxxxxxxxxxxxxx=V | R/R | R/R | R/R |
| password_xxxxxxxxxxxxxxxxxxxxxxxxx=V | R/R | R/R | R/R |
| api_key_xxxxxxxxxxxxxxxxxxxxxxxxx=V | R/R | R/R | R/R |
| password12_xxxxxxxxxxxxxxxxxxxx=V | R/R | R/R | R/R |
| api_key12_xxxxxxxxxxxxxxxxxxxx=V | R/R | R/R | R/R |
| flag --a-b-c-d-e-f-g-h-password V | R/R | R/R | R/R |
| flag --a-b-c-d-e-f-g-h-password V W | R/R | R/R | R/R |
| flag --max_tokens V | R/R | R/R | R/R |
| flag --max_tokens V W | R/R | R/R | R/R |
| cookiejar=v | R/R | R/R | R/R |
| cookiestore=v | R/R | R/R | R/R |
| password split by LF | R/R | R/R | R/R |
| %-encoded password | R/M | R/M | R/M |
| html-tag split | R/M | R/M | R/M |

## masked on head, readable on main
| kv bypass_key=V | M/M | R/R | R/R |
| colon bypass_key: V | M/M | R/R | R/R |
| kv bypass_code=V | M/M | R/R | R/R |
| colon bypass_code: V | M/M | R/R | R/R |
| kv bypass-code=V | M/M | R/R | R/R |
| colon bypass-code: V | M/M | R/R | R/R |
| kv bypass_value=V | M/M | R/R | R/R |
| colon bypass_value: V | M/M | R/R | R/R |
| kv bypass_phrase=V | M/M | R/R | R/R |
| colon bypass_phrase: V | M/M | R/R | R/R |
| kv bypasskey=V | M/M | R/R | R/R |
| colon bypasskey: V | M/M | R/R | R/R |
| kv bypasscode=V | M/M | R/R | R/R |
| colon bypasscode: V | M/M | R/R | R/R |
| kv passkey=V | M/M | M/M | R/R |
| colon passkey: V | M/M | M/M | R/R |
| kv pass_code=V | M/M | M/M | R/R |
| colon pass_code: V | M/M | M/M | R/R |
| wget --set-cookie url | M/M | M/M | R/M |
| wget --set-cookie V | M/M | M/M | R/R |
| curl --set-cookie V | M/M | M/M | R/R |
| wget --session-cookie url | M/M | M/M | R/M |
| wget --session-cookie V | M/M | M/M | R/R |
| curl --session-cookie V | M/M | M/M | R/R |
| wget --sessioncookie url | M/M | M/M | R/M |
| wget --sessioncookie V | M/M | M/M | R/R |
| curl --sessioncookie V | M/M | M/M | R/R |
| wget --set_cookie url | M/M | M/M | R/M |
| wget --set_cookie V | M/M | M/M | R/R |
| curl --set_cookie V | M/M | M/M | R/R |
| cookie1=V | M/M | R/R | R/R |
| cookie1: V | M/M | R/R | R/R |
| cookie2=V | M/M | R/R | R/R |
| cookie2: V | M/M | R/R | R/R |
| cookie9=V | M/M | R/R | R/R |
| cookie9: V | M/M | R/R | R/R |
| Cookie2=V | M/M | R/R | R/R |
| Cookie2: V | M/M | R/R | R/R |
| cookie_name2=V | M/M | M/M | R/R |
| cookie_name2: V | M/M | M/M | R/R |
| cookie_name=V | M/M | M/M | R/R |
| cookie_name: V | M/M | M/M | R/R |
| set-cookie2=V | M/M | R/R | R/R |
| set-cookie2: V | M/M | R/R | R/R |
| Set-Cookie2=V | M/M | R/R | R/R |
| Set-Cookie2: V | M/M | R/R | R/R |
| cookie20=V | M/M | R/R | R/R |
| cookie20: V | M/M | R/R | R/R |
| cookie123456=V | M/M | R/R | R/R |
| cookie123456: V | M/M | R/R | R/R |
| pass+1digits=V | M/M | M/M | R/R |
| pass+1digits: V | M/M | M/M | R/R |
| pass+5digits=V | M/M | M/M | R/R |
| pass+5digits: V | M/M | M/M | R/R |
| pass+19digits=V | M/M | M/M | R/R |
| pass+19digits: V | M/M | M/M | R/R |
| pass+20digits=V | M/M | M/M | R/R |
| pass+20digits: V | M/M | M/M | R/R |
| pass+21digits=V | M/M | R/R | R/R |
| pass+21digits: V | M/M | R/R | R/R |
| pass+22digits=V | M/M | R/R | R/R |
| pass+22digits: V | M/M | R/R | R/R |
| pass+30digits=V | M/M | R/R | R/R |
| pass+30digits: V | M/M | R/R | R/R |
| pass+40digits=V | M/M | R/R | R/R |
| pass+40digits: V | M/M | R/R | R/R |
| pass+41digits=V | M/M | R/R | R/R |
| pass+41digits: V | M/M | R/R | R/R |
| password+21digits=V | M/M | R/R | R/R |
| password+21digits: V | M/M | R/R | R/R |
| password+22digits=V | M/M | R/R | R/R |
| password+22digits: V | M/M | R/R | R/R |
| password+30digits=V | M/M | R/R | R/R |
| password+30digits: V | M/M | R/R | R/R |
| password+40digits=V | M/M | R/R | R/R |
| password+40digits: V | M/M | R/R | R/R |
| password+41digits=V | M/M | R/R | R/R |
| password+41digits: V | M/M | R/R | R/R |
| auth+1digits=V | M/M | M/M | R/R |
| auth+1digits: V | M/M | M/M | R/R |
| auth+5digits=V | M/M | M/M | R/R |
| auth+5digits: V | M/M | M/M | R/R |
| auth+19digits=V | M/M | M/M | R/R |
| auth+19digits: V | M/M | M/M | R/R |
| auth+20digits=V | M/M | M/M | R/R |
| auth+20digits: V | M/M | M/M | R/R |
| auth+21digits=V | M/M | R/R | R/R |
| auth+21digits: V | M/M | R/R | R/R |
| auth+22digits=V | M/M | R/R | R/R |
| auth+22digits: V | M/M | R/R | R/R |
| auth+30digits=V | M/M | R/R | R/R |
| auth+30digits: V | M/M | R/R | R/R |
| auth+40digits=V | M/M | R/R | R/R |
| auth+40digits: V | M/M | R/R | R/R |
| auth+41digits=V | M/M | R/R | R/R |
| auth+41digits: V | M/M | R/R | R/R |
| session+1digits=V | M/M | M/M | R/R |
| session+1digits: V | M/M | M/M | R/R |
| session+5digits=V | M/M | M/M | R/R |
| session+5digits: V | M/M | M/M | R/R |
| session+19digits=V | M/M | M/M | R/R |
| session+19digits: V | M/M | M/M | R/R |
| session+20digits=V | M/M | M/M | R/R |
| session+20digits: V | M/M | M/M | R/R |
| session+21digits=V | M/M | R/R | R/R |
| session+21digits: V | M/M | R/R | R/R |
| session+22digits=V | M/M | R/R | R/R |
| session+22digits: V | M/M | R/R | R/R |
| session+30digits=V | M/M | R/R | R/R |
| session+30digits: V | M/M | R/R | R/R |
| session+40digits=V | M/M | R/R | R/R |
| session+40digits: V | M/M | R/R | R/R |
| session+41digits=V | M/M | R/R | R/R |
| session+41digits: V | M/M | R/R | R/R |
| bearer+0digits=V | M/M | M/M | R/R |
| bearer+0digits: V | M/M | M/M | R/R |
| bearer+1digits=V | M/M | M/M | R/R |
| bearer+1digits: V | M/M | M/M | R/R |
| bearer+5digits=V | M/M | M/M | R/R |
| bearer+5digits: V | M/M | M/M | R/R |
| bearer+19digits=V | M/M | M/M | R/R |
| bearer+19digits: V | M/M | M/M | R/R |
| bearer+20digits=V | M/M | M/M | R/R |
| bearer+20digits: V | M/M | M/M | R/R |
| bearer+21digits=V | M/M | R/R | R/R |
| bearer+21digits: V | M/M | R/R | R/R |
| bearer+22digits=V | M/M | R/R | R/R |
| bearer+22digits: V | M/M | R/R | R/R |
| bearer+30digits=V | M/M | R/R | R/R |
| bearer+30digits: V | M/M | R/R | R/R |
| bearer+40digits=V | M/M | R/R | R/R |
| bearer+40digits: V | M/M | R/R | R/R |
| bearer+41digits=V | M/M | R/R | R/R |
| bearer+41digits: V | M/M | R/R | R/R |
| secret+21digits=V | M/M | R/R | R/R |
| secret+21digits: V | M/M | R/R | R/R |
| secret+22digits=V | M/M | R/R | R/R |
| secret+22digits: V | M/M | R/R | R/R |
| secret+30digits=V | M/M | R/R | R/R |
| secret+30digits: V | M/M | R/R | R/R |
| secret+40digits=V | M/M | R/R | R/R |
| secret+40digits: V | M/M | R/R | R/R |
| secret+41digits=V | M/M | R/R | R/R |
| secret+41digits: V | M/M | R/R | R/R |
| token+21digits=V | M/M | R/R | R/R |
| token+21digits: V | M/M | R/R | R/R |
| token+22digits=V | M/M | R/R | R/R |
| token+22digits: V | M/M | R/R | R/R |
| token+30digits=V | M/M | R/R | R/R |
| token+30digits: V | M/M | R/R | R/R |
| token+40digits=V | M/M | R/R | R/R |
| token+40digits: V | M/M | R/R | R/R |
| token+41digits=V | M/M | R/R | R/R |
| token+41digits: V | M/M | R/R | R/R |
| apikey+21digits=V | M/M | R/R | R/R |
| apikey+21digits: V | M/M | R/R | R/R |
| apikey+22digits=V | M/M | R/R | R/R |
| apikey+22digits: V | M/M | R/R | R/R |
| apikey+30digits=V | M/M | R/R | R/R |
| apikey+30digits: V | M/M | R/R | R/R |
| apikey+40digits=V | M/M | R/R | R/R |
| apikey+40digits: V | M/M | R/R | R/R |
| apikey+41digits=V | M/M | R/R | R/R |
| apikey+41digits: V | M/M | R/R | R/R |
| flag --pass2 V | M/M | M/M | R/R |
| flag --pass2 V W | M/M | M/M | R/R |
| flag --newpass V | M/M | M/M | R/R |
| flag --newpass V W | M/M | M/M | R/R |
| flag --a-b-c-d-e-f-password V | M/M | M/M | R/R |
| flag --a-b-c-d-e-f-password V W | M/M | M/M | R/R |
| flag --apiTokens V | M/M | M/M | R/R |
| flag --apiTokens V W | M/M | M/M | R/R |
| flag --apiInputTokens V | M/M | M/M | R/R |
| flag --apiInputTokens V W | M/M | M/M | R/R |
| flag --authorization V | M/M | M/M | R/R |
| flag --authorization V W | M/M | M/M | R/R |
| COOKIEJAR=v | M/M | M/M | R/R |
| COOKIESTORE=v | M/M | M/M | R/R |

## errors
