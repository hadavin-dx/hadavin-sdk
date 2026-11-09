import sys
sys.path.insert(0, sys.argv[1])
import hadavin_sdk
from hadavin_sdk.guard import runmap
from hadavin_sdk.approvals import channel
print("pkg", hadavin_sdk.__file__)
for x in sys.argv[2:]:
    print(repr(x), "| model", repr(runmap.redact_text(x, runmap.RunMap())), "| card", repr(channel.clean(x)))
