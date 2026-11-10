from hadavin_sdk.guard import runmap
SVB="4xKp2Vb9Lr3NcW8dYh6uJs"
for k,v in {"K42a":"password"+"k"*200+"="+SVB+" x","K42c":"password"+"k"*255+"="+SVB+" x","K42d":"password"+"k"*256+"="+SVB+" x","K42q":"?password"+"k"*30+"="+SVB+" x"}.items():
    o=runmap.redact_text(v,runmap.RunMap()); print(k, len(v), repr(o.replace("k"*30,"k*30")[:120]), SVB in o)
