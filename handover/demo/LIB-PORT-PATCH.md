# Patch needed in the harness lib.py (the rig) before a SECOND parallel run can start. NOT applied by me: lib.py is outside handover/demo and the rig is not mine to change. Written against my scratch copy of lib.py (line numbers may differ on the laptop; search for the literal).
Add near line 9 (defaults = today's values, so an unpatched run is unchanged):
  N8N_PORT_ = int(os.environ.get("MF_N8N_PORT", "5679")); BROKER_PORT_ = int(os.environ.get("MF_N8N_BROKER_PORT", "5780")); FAKE_PORT_ = int(os.environ.get("MF_RUN_PORT", "8790"))
Then replace the literals:
- line 9  N8N_PORTS = (5679, 5780)            -> N8N_PORTS = (N8N_PORT_, BROKER_PORT_)
- line 11 FAKE = "http://127.0.0.1:8790"       -> FAKE = "http://127.0.0.1:%d" % FAKE_PORT_
- line 65, 90, 112, 193: the four URLs with 127.0.0.1:5679 -> use N8N_PORT_ (healthz, webhook, readiness, webhook)
- line 85  N8N_PORT="5679", N8N_RUNNERS_BROKER_PORT="5780" -> str(N8N_PORT_), str(BROKER_PORT_)
- line 106 _wait_port_free(5679, 20) / port_free(5780) and its message -> N8N_PORT_ / BROKER_PORT_
- line 118 port_free(8790) and its message -> FAKE_PORT_, and wherever start_fakes passes 8790 to the stand-in server process: FAKE_PORT_
The variables are the same names runcfg.py already reads, and run_mf.py passes them to the scripts (KEEP_ENV).
Not checked: whether other harness scripts (setup.py, api.py) carry the same literals; I grepped only lib.py and my own files.
