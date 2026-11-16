import json,sys,statistics,collections
src=sys.argv[1]
rows=[json.loads(l) for l in open(src)]
print("first row keys:",list(rows[0].keys()))
L45='873a908a-film-v4-lease45'
l45=[r for r in rows if r.get('flows')==L45]
print("rows with flows==lease45:",len(l45), collections.Counter(r['point'] for r in l45))
voided=[r for r in l45 if r['label'].startswith('VOID')]
errs=[r for r in l45 if 'err' in r['label']]
kept=[r for r in l45 if r['point'] in('K1','K2','K3','K6') and not r['label'].startswith('VOID')]
print("(1) kept K rows:",len(kept))
v=[r['kill_to_final_s'] for r in kept]
print("(2) min,max,median",min(v),max(v),statistics.median(v))
bad=[(r['label'],r['kill_to_final_s'],r['restart_s'],r['recovery_s'],round(r['kill_to_final_s']-r['restart_s']-r['recovery_s'],2)) for r in kept if abs(r['kill_to_final_s']-(r['restart_s']+r['recovery_s']))>0.5]
print("   rows violating |k2f-(restart+recovery)|>0.5:",bad)
print("   all diffs:",[(r['label'],round(r['kill_to_final_s']-r['restart_s']-r['recovery_s'],2)) for r in kept])
print("(3) per case:",dict(collections.Counter(r['point'] for r in kept)))
print("(4) fields per kept row: stage_requests / total_stage_requests / total_mails / counts.stage_calls / crm_rows / crm_upsert_events")
for r in kept:
    c=list(r['counts'].values())[0]
    print(" ",r['label'],r['point'],'stage_requests',c.get('stage_requests'),'total_stage_requests',r.get('total_stage_requests'),'stage_calls',c.get('stage_calls'),'crm_rows',c.get('crm_rows'),'crm_upsert_events',r.get('crm_upsert_events','absent'),'stage_qualify_events',r.get('stage_qualify_events'),'total_mails',r.get('total_mails'),'mail_to_intake',c.get('mail_to_intake'))
print("   kept with stage_requests==2:",sum(1 for r in kept if list(r['counts'].values())[0].get('stage_requests')==2))
print("   kept with crm_rows==2:",sum(1 for r in kept if list(r['counts'].values())[0].get('crm_rows')==2))
print("   kept with crm_upsert_events>=2:",sum(1 for r in kept if r.get('crm_upsert_events',0)>=2))
print("   kept crm_upsert_events counter:",dict(collections.Counter(r.get("crm_upsert_events") for r in kept)),"stage_qualify_events:",dict(collections.Counter(r.get("stage_qualify_events") for r in kept)))
print("   by case crm_upsert_events==2:",dict(collections.Counter(r["point"] for r in kept if r.get("crm_upsert_events")==2)))
print("   kept with stage_calls==2:",sum(1 for r in kept if list(r['counts'].values())[0].get('stage_calls')==2))
print("(5) VOID rows (whole file):")
for r in rows:
    if r['label'].startswith('VOID'):
        print("  ",r['label'],r['point'],r['t_start'],r['t_end'],r.get('error'),'reached_terminal',r.get('reached_terminal'),'k2f',r.get('kill_to_final_s'))
print("   runs overlapping VOID-fl45k3b window by time (lease45 rows):")
def s(t):h,m,x=t[:-1].split(':');return int(h)*3600+int(m)*60+int(x)
for v_ in [r for r in voided if 't_end' in r]:
    a,b=s(v_['t_start']),s(v_['t_end'])
    for r in l45:
        if r is v_:continue
        if s(r['t_start'])<b and s(r['t_end'])>a: print("    overlaps",v_['label'],"<->",r['label'],r['t_start'],r['t_end'])
print("(6) mail info per kept row: rows_at_kill[3] (mail flag?), mail_to_intake, all_mails, lead_mail_stored")
for r in kept:
    c=list(r['counts'].values())[0]
    print(" ",r['label'],r['point'],'rows_at_kill',r['rows_at_kill'],'mail_to_intake',c['mail_to_intake'],'alert',c['alert'],'total_mails',r['total_mails'],'lead_mail_stored',r.get('lead_mail_stored'))
