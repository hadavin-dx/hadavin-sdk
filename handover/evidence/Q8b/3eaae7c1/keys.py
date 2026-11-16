import json,sys
from hadavin_sdk.k1b import redaction as kr
keys="apiTokens accessTokens refreshTokens idTokens accesstokens idtokens authtokens apitokens maxTokens max_tokens input_tokens audio_tokens tokens cookie cookies set-cookie session_cookie cookie_name cookie-policy no-cookies possession_id obsession_id bypass_key compass_code bypass_code xbypass_key bypasspass_key session_id pass_code authorization pass2 password newpass pass1234567890 password1234567890123456789012345678901234567890".split()
print(json.dumps({k: bool(kr.sensitive(k)) for k in keys}))
