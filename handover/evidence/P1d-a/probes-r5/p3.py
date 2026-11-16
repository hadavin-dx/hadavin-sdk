from hadavin_sdk.guard import runmap
A="Tq7mZ";B="4xKp2Vb9Lr3NcW8dYh6uJs"
for k,v in {"K43a":"password"+"k"*30+'="'+A+" "+B+'"',"K43b":"password"+"k"*30+"='"+A+" "+B+"'","K43a_card_like":"x "+"password"+"k"*30+'="'+A+" "+B+'"'}.items():
    o=runmap.redact_text(v,runmap.RunMap()); print(k,repr(o.replace("k"*30,"k*30")), B in o or A in o)
