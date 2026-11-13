import sys, runpy, importlib
repo = sys.argv[1]; mode = sys.argv[2]
if mode == "preimport_foreign_tools":
    sys.path.insert(0, sys.argv[3]); import tools
    print("pre-imported tools:", getattr(tools, "__file__", None))
sys.path.insert(0, repo + "/scripts")
try:
    import n8n_api
    import tools.pathconfine as p, lead_desk
    print("OK n8n_api", n8n_api.__file__, "| tools.pathconfine", p.__file__, "| lead_desk", lead_desk.__file__)
    print("sys.path[:5]", [x for x in sys.path[:5]])
except BaseException as e:
    print("sys.path[:5]", sys.path[:5])
    print("EXC", type(e).__name__, e)
