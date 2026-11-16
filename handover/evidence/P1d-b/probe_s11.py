import base64
from hadavin_sdk.k1b import redaction as r
from hadavin_sdk.guard import runmap
keys = {
 "plain db_password": "db_password",
 "zero-width": "db_pass​word",
 "cyrillic dze": "db_pasѕword",
 "markers": "db-pass**word**",
 "cyrillic a": "db_pаssword",
 "soft hyphen": "db_pass­word",
 "fullwidth": "db_ｐassword",
 "combining": "db_pássword",
 "tag char": "db_password\U000e0041",
 "nbsp boundary": "db password",
 "ascii dbpassword": "dbpassword",
 "ascii passenger": "passenger",
}
for n,k in keys.items(): print(f"{n:18} sensitive={r.sensitive(k)}")
m = runmap.RunMap()
f = lambda s: runmap.redact_untrusted(s, m)
pw = "correct" + " horse " + "battery staple"
print("pair multiword:", repr(r._pair("password", pw, f)))
print("walk Secret cyr kind:", r._walk({"kind":"Secrеt","data":{"x": base64.b64encode(b"hunter2xyz").decode()}}, f))
print("walk env cyr value key:", r._walk({"name":"DB_PASSWORD","vаlue":"hunter2xyz"}, f))
