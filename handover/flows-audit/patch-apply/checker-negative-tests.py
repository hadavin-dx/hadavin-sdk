import json,shutil,os,sys
SRC='/tmp/pa13b/g/plan/real'
def mk(tag,fn):
    d='/tmp/pa13b/neg/'+tag; shutil.copytree(SRC,d); p=d+'/mf-form.json'; j=json.load(open(p)); r=fn(j,d); 
    if r is not False: json.dump(j,open(p,'w'))
def n(j,name): return [x for x in j['nodes'] if x['name']==name][0]
mk('orphan_reply', lambda j,d: j['connections'].pop('Stored'))                      # ReplyStored+... ReplyStored orphan (respondToWebhook)
def selfloop(j,d):
    j['connections']['Stored']['main'][0]=[{"node":"Stored","type":"main","index":0}]
mk('self_only', selfloop)                                                             # ReplyStored only orphan; Stored only self -> unreachable
mk('unreach_pair', lambda j,d: (j['connections'].pop('Claim'), j['connections'].__setitem__('Claim',{'main':[[{"node":"Claimed","type":"main","index":0}],[{"node":"ReplyStoreFail","type":"main","index":0}]]}), j['connections'].__setitem__('ReplyStoreFail',{'main':[[{"node":"Claimed","type":"main","index":0}]]})) )
mk('no_errlink', lambda j,d: j['connections']['Claim']['main'].pop())
mk('if_one_branch', lambda j,d: j['connections']['KeyOk']['main'].pop())
mk('bad_ref', lambda j,d: n(j,'ReplyStoreFail')['parameters'].__setitem__('responseBody',"={{ $('Nope').item.json.x }}"))
mk('no_trigger', lambda j,d: n(j,'Receive').__setitem__('type','n8n-nodes-base.respondToWebhook'))
mk('dangling', lambda j,d: j['connections']['Item']['main'][0].append({"node":"Ghost","type":"main","index":0}))
mk('no_name', lambda j,d: n(j,'Item').pop('name'))
mk('count_wrong', lambda j,d: j['nodes'].pop(-1) and False or None)
def parsefail(j,d): open(d+'/mf-form.json','w').write('{bad'); return False
mk('parse_fail', parsefail)
def missingfile(j,d): os.remove(d+'/mf-hook.json'); return False
mk('missing_file', missingfile)
mk('wrong_save', lambda j,d: j['settings'].__setitem__('saveDataSuccessExecution','none'))
mk('extra_change', lambda j,d: n(j,'Stored').__setitem__('alwaysOutputData',False))
