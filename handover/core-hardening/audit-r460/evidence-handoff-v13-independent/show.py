import pickle,sys,re
R="/home/user/hadavin-sdk/"
out=pickle.load(open("classA.pkl","rb"))
idx=[int(x) for x in sys.argv[1:]]
for i in idx:
    o=out[i]
    doc,ln=o[0].rsplit(":",1)
    line=open("docs/"+doc,encoding="utf-8").read().split("\n")[int(ln)-1]
    path,rng=o[1].rsplit(":",1)
    pos=line.find(path.split("/")[-1]+":"+rng)
    print("#%d %s %s -> %s"%(i,o[0],o[1],o[3]))
    print("  DOC:",line[max(0,pos-260):pos+len(o[1])+120].replace("\n"," "))
    a,b=[int(x) for x in (rng.split("-")+[rng])[:2]] if "-" in rng else (int(rng),int(rng))
    try:
        L=open(R+o[3],encoding="utf-8",errors="replace").read().split("\n")
        for k in range(max(1,a-1),min(len(L),min(b,a+10))+1): print("  %5d: %s"%(k,L[k-1][:150]))
    except Exception as e: print(" ERR",e)
    print()
