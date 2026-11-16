import sys,time
from hadavin_sdk.guard import runmap
SVB="4xKp2Vb9Lr3NcW8dYh6uJs"; SVA="Tq7mZ"
rows={
"K41":"a"*41+"password="+SVB+" x",
"K41q":"?"+"a"*41+"password="+SVB+" x",
"K41q2":"x?"+"a"*41+"token="+SVB+"&user=bob",
"K42":"password"+"x"*255+"="+SVB+" x",
"K42b":"password"+"x"*256+"="+SVB+" x",
"K42q":"?password"+"x"*30+"="+SVB+" x",
"K43":"password"+"x"*30+'="'+SVB+'"',
"K43s":"password"+"x"*30+"='"+SVB+"'",
"Q18":"?token=ab&c+d/e= x",
"Q18b":"?token=ab&cdEFG= x",
"Q19":"?password=ab&_id=7 x",
"Q20":"?password=ab&client_id=7 x",
"Q21":"?password=ab&x-y=1 x",
"Q22":"?password=ab&amp;_id=7 x",
"Q22b":"?password=ab&amp;x-y=1 x",
"Q2":"?password=ab12cd&user=bob x",
"Q4":"?password=ab&cd34ef56&user=bob x",
"Q10":"?password=ab&cd34#x=1 y",
"Q11":"?password=ab&cd34 x=1",
"Q16":"?password=ab&cd34\"x=1 y",
"Q17":"?password=ab&amp;cd34\"x=1 y",
"Q13":"?user=bob&password=ab12cd&next=/home x",
"Q15":"?a=1&amp;password=ab12cd&amp;next=/home x",
"H34a":"password=ab12&cd34ef56gh78ij",
"H34b":"password="+SVA+"&amp;"+SVB,
"SC1":"password=ab&cd34;ef56",
"PU1":"password=ab&amp; x",
"F16":"password=hunter22&user=bob",
"Q6":"?password=ab12cd&debug x",
"BTK":"`a https://evil.com/p password="+SVB+"` b",
}
for k,v in rows.items(): print(k, repr(runmap.redact_text(v,runmap.RunMap())))
for name,t in [("dots","a.a.-"*20000),("amp","&"*100000),("ampq","?password=x"+"&a"*50000),("pw","password"*12500),("pwq","?"+"password"*12500),("mix","a.password-"*9000)]:
    t0=time.time(); runmap.redact_text(t,runmap.RunMap()); print(name,len(t),round(time.time()-t0,2),"s")
