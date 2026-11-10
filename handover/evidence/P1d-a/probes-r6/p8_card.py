from hadavin_sdk.approvals import channel
SVB="4xKp2Vb9Lr3NcW8dYh6uJs"
ins={
"BTK_https":"`a https://evil.com/p password="+SVB+"` b",
"BTK_bare":"`a evil.com password="+SVB+"` b",
"BTK_bare2":"`a evil.com/p password="+SVB+"` b",
"MENT_span":"`<!channel> x password="+SVB+"` b",
"MENT_span2":"`<@U123ABC> x password="+SVB+"` b",
"MENT_plain":"<!channel> x password="+SVB+" b",
"Q23":"?password=ab&x==1 y",
}
for k,v in ins.items(): print(k, repr(channel.clean(v)))
