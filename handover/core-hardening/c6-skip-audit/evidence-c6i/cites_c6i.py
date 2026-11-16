import sys
S = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover"
H = "/home/user/hadavin-sdk/handover"
A, FA = S + "/demo", S + "/flows-audit"
C = [
 (A+"/VIDEO-RUNSHEET.md",90,"Raw not seen by me"),(A+"/VIDEO-RUNSHEET.md",22,"UNMEASURED"),
 (A+"/VIDEO-RUNSHEET.md",85,"NO number"),(A+"/VIDEO-RUNSHEET.md",33,"NO NUMBER measured"),
 (A+"/VIDEO-RUNSHEET.md",4,"scenes 1 to 5"),(A+"/VIDEO-RUNSHEET.md",11,"Scenes 1 to 4"),
 (A+"/VIDEO-RUNSHEET.md",12,"stand-in"),(A+"/VIDEO-RUNSHEET.md",24,"Lane3 K3"),
 (A+"/VIDEO-RUNSHEET.md",41,"80 kills"),(A+"/VIDEO-RUNSHEET.md",56,"scene 5"),(A+"/VIDEO-RUNSHEET.md",78,"Scene 5"),
 (A+"/n8n-flows/PAGE-STATEMENTS-V4.md",149,"not in my checkout"),(A+"/n8n-flows/PAGE-STATEMENTS-V4.md",150,"killed after the mail left"),
 (A+"/n8n-flows/PAGE-STATEMENTS-V4.md",153,"killed after the mail left"),(A+"/n8n-flows/PAGE-STATEMENTS-V4.md",125,"UNBACKED"),
 (A+"/n8n-mainframe/mf.py",151,"def k1"),(A+"/n8n-mainframe/mf.py",158,"mail NOT yet delivered"),
 (A+"/n8n-mainframe/mf.py",164,"before the table update"),(A+"/n8n-mainframe/mf.py",274,"def t7b"),
 (A+"/n8n-mainframe/mf.py",276,"execution saving is off"),(A+"/n8n-mainframe/mf.py",278,"EXECUTIONS_DATA_SAVE_ON_SUCCESS"),
 (A+"/n8n-mainframe/mf.py",296,'rec("T7b"'),(A+"/n8n-mainframe/stage_server.py",54,"Q.qualify"),
 (A+"/n8n-flows-real-v5/mf-form.json",238,"n8n_error: false"),(A+"/n8n-flows-real-v5/mf-form.json",254,"n8n_error: false"),
 (A+"/n8n-flows-real-v5/mf-form.json",293,"n8n_error: false"),
 (FA+"/EXCEPTIONS.md",5,"Reading A"),(FA+"/FINDINGS.md",96,"saved ON"),(FA+"/FINDINGS.md",97,"F-011"),(FA+"/FINDINGS.md",113,"F-019"),
 (H+"/core-hardening/inputs/plan-wp6-resmoke-v5.md",125,"EXECUTIONS_DATA_SAVE_ON_SUCCESS=all"),
 (H+"/core-hardening/inputs/plan-wp6-resmoke-v5.md",550,"smk_n8n"),(H+"/core-hardening/inputs/plan-wp6-resmoke-v5.md",298,"film-v5"),
 (H+"/core-hardening/inputs/DECISIONS-2026-11-16.md",2,"60.1 to 61.9"),
 (H+"/core-hardening/ORDERS.md",151,"Q21"),
]
bad = 0
for p, n, s in C:
    try: line = open(p, encoding="utf-8", errors="replace").read().split("\n")[n-1]
    except Exception as e: line = "ERR " + str(e)
    ok = s in line; bad += not ok
    print("MATCH" if ok else "MISMATCH", p.replace(S,"S").replace(H,"H"), n, repr(s))
print("total", len(C), "mismatch", bad)
