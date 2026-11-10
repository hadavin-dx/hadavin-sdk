from hadavin_sdk.guard import runmap
for k,v in {"Q23":"?token=ab&cdEFG== x","Q23c":"?token=ab&amp;cdEFG== x","S7c":"GET /p?token=Qw3Er&Ab7Kx9== &id=4","Q18b":"?token=ab&cdEFG= x","Q22":"?password=ab&amp;_id=7 x"}.items():
    print(k,repr(runmap.redact_text(v,runmap.RunMap())))
