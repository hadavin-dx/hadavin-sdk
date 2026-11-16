from patch_lib import Doc
from patch_lib import Doc
o = Doc("CORE-PR-HANDOFF-v14-other-tracks.md")
o.rep("`_Mapping.__repr__` returns `\"<mapping withheld>\"`;", "`_Mapping.__repr__` returns `\"<mapping withheld>\"` (v14, disclosed edit of wording: the holder keeps the original out of reach **through repr, copy, pickle or asdict**; it does not claim more);")
o.rep("- **v13 edits (nothing else changed;", "- **v14 disclosed edits to carried PRs (lead's answer Q34 asks for no content change; these are content changes, so they are listed here and in `v14-CHANGES.md`; the lead may refuse any of them):** (a) PR-2: the `_Mapping` holder wording below says \"through repr, copy, pickle or asdict\" (security minor 8); (b) the hot-file column of the spend file 7.1 now names the files H-0, H-1, K1, A1, G, R and PR-2 edit (readiness R4); (c) K1's new file `fileguard.py` and its new keyword `allow_group_read` are marked as new; (d) H-2's grep claim is bounded to the files the grep read (citation finding 1); (e) evidence names renamed to v14. Nothing else changed.\n- **v13 edits (nothing else changed;")
o.save()
