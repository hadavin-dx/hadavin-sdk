import sys; sys.path.insert(0, "/home/user/build/prh-author/errata")
import prh_proto as proto, fixes
from hadavin_sdk import tools
ESC = "\x1b"; t = "peer <" + ESC + "[0mIPV4_2> refused, seen from 10.0.0.5"
proto.install(); fixes.install()
print("F1b error_reason output:", ascii(tools.error_reason(ValueError(t)).replace("10.0.0.5", "[IP]")))
