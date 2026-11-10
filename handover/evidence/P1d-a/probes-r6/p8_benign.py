from hadavin_sdk.guard import runmap
kws=["token","secret","password","key_data","credential"]
tails=["_rotation_policy_document_name","_expiry_notification_email_template","_lifecycle_management_settings_v2","_audit_report_generation_schedule","_cache_invalidation_strategy_name"]
vals=["30d","2026-11-10","/var/log/app","42","v2.1"]
n=hidden=0
for i,k in enumerate(kws):
  for j,t in enumerate(tails):
    key=k+t; assert 21<=len(key)-len(k)<=255
    s=key+"="+vals[(i+j)%5]+" next"; r=runmap.redact_text(s,runmap.RunMap()); n+=1; hidden+=(r!=s)
print(n,"samples, hidden:",hidden)
