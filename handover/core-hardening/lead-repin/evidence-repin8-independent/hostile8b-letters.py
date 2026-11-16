import random, subprocess, json, sys
random.seed(77)
def val(n=22): return "Qy"+"".join(random.choice("abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(n))
P="pass"+"word"; S="sec"+"ret"; T="to"+"ken"
T8=[
("bearer-nospace","Authorization:Bearer @V@"),("spaced-colon","%s : @V@"%P),("json-spaced",'"%s" : "@V@"'%P),
("json-array-flag",'["--%s","@V@"]'%P),("json-multiline-kv",'{\n  "%s":\n    "@V@"\n}'%P),("md-table","| %s | @V@ |"%P),
("prose","the %s is @V@ ok"%P),("pwd","pwd=@V@"),("passwd","passwd: @V@"),("pass-key","pass=@V@"),("key-alone","key=@V@"),
("auth-alone","auth=@V@"),("credentials","credentials=@V@"),("private-dash","private-key: @V@"),("value-with-space","%s=@V@ tail words"%P),
("value-with-quote",'%s="ab\'@V@"'%P),("backtick","%s=`@V@`"%P),("dollar-paren","%s=$(echo @V@)"%P),
("windows-reg",'"%s"=@V@'%P),("powershell","$env:%s='@V@'"%P.upper()),("secure-string","ConvertTo-SecureString '@V@' -AsPlainText"),
("ssh-url","git+https://bob:@V@@h.example.test/r.git"),("npmrc","//reg.example.test/:_auth%s=@V@"%T),("netrc","machine h.example.test login bob %s @V@"%P),
("docker-config",'"auth": "@V@"'),("kube-token","    %s: @V@"%T),("terraform",'%s = "@V@"'%S),("hcl-var",'variable "x" { default = "@V@" } # %s'%P),
("sentry-dsn","https://@V@@o1.ingest.example.test/1"),("webhook-url","https://hooks.example.test/services/T00/B00/@V@"),
("hex-64x","%s=%s"%(S,"".join(random.choice("01abcdef") for _ in range(64)))),("b64-pad","%s=%s=="%(T,val(30))),
("rot-key-tab","%s\t=\t@V@"%P),("two-lines-key-then-val","%s\n@V@"%P),("equals-colon","%s:=@V@"%P),("arrow","%s => @V@"%P),
("question","?%s=@V@"%P),("semicolon-sep","a=1;%s=@V@;b=2"%P),("conn-string","Server=h;User Id=sa;%s=@V@;Database=d"%P),
("amqp","amqp://guest:@V@@mq.example.test:5672/"),("mongodb","mongodb+srv://bob:@V@@c.example.test/db"),
("html-attr",'<input type="hidden" name="%s" value="@V@">'%P),("html-input-rev",'<input value="@V@" name="%s">'%P),
("cap-key-in-value","note: set %s to @V@"%S),("emoji","\U0001F511 %s=@V@"%P),("ansi","\x1b[31m%s=@V@\x1b[0m"%P),
("nul-in-line","%s=@V@\x00tail"%P),("very-long-key",("a"*3000)+"_%s=@V@"%P),("many-equals","%s====@V@"%P),
]
res=[]
shell=sys.argv[1]
for cid,t in T8:
    v=val(22); txt=t.replace("@V@",v)
    if "hex-64x" == cid: v=txt.split("=")[1]
    if "b64-pad"==cid: v=txt.split("=")[1][:24]
    o=subprocess.run([shell,"/tmp/hd8i/v8.sh","--mask"],input=txt.encode(),capture_output=True)
    out=o.stdout.decode("utf-8","replace")
    st="SHOWN" if v in out else "hidden"
    res.append((cid,st,o.returncode)); print("%-24s %s exit=%s"%(cid,st,o.returncode),flush=True)
print("TOTAL",len(res),"shown",sum(r[1]=="SHOWN" for r in res))
