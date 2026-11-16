CR="src/lead_desk/crm_hubspot.py"; RS="src/lead_desk/run_stats.py"; CF="src/lead_desk/config.py"; RR="scripts/run_real_check.py"
exec(open("/home/user/build/rr6/out/EV7T/set_own.py").read().split("muts=[")[0].split("C=[")[0])
CRM=["tests/test_crm_hubspot.py","tests/test_r7t_findings.py"]
CFG=["tests/test_bind_refusals.py","tests/test_r7h_findings.py","tests/test_r7t_findings.py"]
STA=["tests/test_r7_no_replace_of_special.py","tests/test_special_output_files.py","tests/test_r7n_findings.py","tests/test_r7t_findings.py"]
RRC=["tests/test_r7s_findings.py","tests/test_real_check_dry.py","tests/test_r7t_findings.py"]
src={}
for f in ("set_own.py","set_settle.py"):
    ns={}; exec(open("/home/user/build/rr6/out/EV7T/"+f).read(),ns); 
    for m in ns["muts"]: src[m[0]]=m
sel={"N02":CRM,"N08":CRM,"T01":CRM,"T13":CRM,"T14":CRM,"T15":CRM,"T18":CRM,"N14":STA,"N22":CFG,"N24":CFG,"N30":RRC,"N32":RRC}
muts=[(k,src[k][1],src[k][2],src[k][3],v) for k,v in sel.items()]
