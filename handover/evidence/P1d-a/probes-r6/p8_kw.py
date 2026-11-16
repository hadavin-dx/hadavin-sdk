from hadavin_sdk.guard import runmap
for k,v in {"PA1":"?bypass=ab12cd x","PA2":"my.pass=ab12cd x","PA3":"session=ab12cd x","PA4":"author=ab12cd x","PA5":"x.auth:ab12cd x","PA6":"passage=ab12cd x"}.items():
    print(k,repr(runmap.redact_text(v,runmap.RunMap())))
