from hadavin_sdk.guard import runmap
for t in ["?password=ab&amp;_id=7 x","?password=ab&_id=7 x","?a=1&amp;password=ab12cd&amp;next=/home x","?password=ab12cd&amp;user=bob x"]:
    m=runmap.RunMap(); o=runmap.redact_text(t,m); print(repr(t),'->',repr(o), dict(m.items()) if hasattr(m,'items') else vars(m))
