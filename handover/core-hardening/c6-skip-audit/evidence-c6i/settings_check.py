import json, sys, glob
base = sys.argv[1]
for s in ("n8n-flows-real-v5", "n8n-flows-film-v5"):
    for f in sorted(glob.glob(f"{base}/{s}/mf-*.json")):
        d = json.load(open(f)); st = d.get("settings", {})
        print(f"{s}/{f.rsplit('/',1)[1]}: saveSuccess={st.get('saveDataSuccessExecution')} saveError={st.get('saveDataErrorExecution')} saveManual={st.get('saveManualExecutions')} errorWorkflow={'errorWorkflow' in st}")
