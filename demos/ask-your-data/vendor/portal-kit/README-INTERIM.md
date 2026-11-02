# INTERIM vendoring, NOT releasable

This copy of the portal kit was taken from the unmerged kit PR hadavin-dx/hadavin-demos#5 (branch kit/portal-kit),
commit f7f297a73da069153bf912ead6279983274b5cc4 (see ../KIT.lock). It is used ONLY by the tests of this demo
(`tests/demo_askdata/test_export_kit.py`); `src/` and `askdata/` never import it.

Before this demo is released or merged for delivery, re-vendor from a MERGED kit commit on main:
`python portal-kit/tools/vendor.py copy <demo> --commit <40-hex merged commit>` and delete this file.
