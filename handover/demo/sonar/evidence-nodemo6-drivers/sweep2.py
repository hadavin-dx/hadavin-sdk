import sys,pathlib,re
sys.path[:0]=[sys.argv[1]+"/src",sys.argv[1]+"/tests",sys.argv[1]]
import conftest
T=pathlib.Path(sys.argv[1])/"tests"
run=[];skip=[]
for f in sorted(T.glob("test_*.py")):
    (skip if conftest._needs_demo(f) else run).append(f.name)
print(len(run),"run",len(skip),"skip of",len(run)+len(skip))
print("RUN:"," ".join(run))
