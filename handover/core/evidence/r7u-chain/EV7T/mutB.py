"""R7T mutant runner: one runner, one tree copy (out/EV7T/mutX); each file restored from the final tree and compared byte for byte."""
import filecmp, os, shutil, subprocess, sys
R="/home/user/build/rr6/"; O=R+"out/EV7T/"; M=O+sys.argv[1]+"/"; S=O+"tree-a/"; TMP=O+"tmp-mut"; os.makedirs(TMP,exist_ok=True)
RR="scripts/run_real_check.py"; CR="src/lead_desk/crm_hubspot.py"; BR="demo_only/bad_request.py"; SUP="tests/support.py"; FK="demo_only/fakes_server.py"; IM="demo_only/fake_imap.py"; SM="demo_only/fake_smtp_tls.py"
T="tests/test_r7t_findings.py"
muts=[
("R07",BR,'isinstance(sys.exception(), CLIENT_GONE)','not isinstance(sys.exception(), CLIENT_GONE)',"t5"),
("R10n",RR,'    if created is None:\n        raise CounterUnreadable','    if not created:\n        raise CounterUnreadable',"t1"),
("R10b",RR,'return max(0, possible - accounted)','return possible - accounted',"t1"),
("R19",RR,'run_dir.glob(f"desk-{tag}-*{suffix}")','run_dir.glob(f"desk-{tag}*{suffix}")',"t2"),
("R20",RR,'run_dir.glob(f"desk-{tag}-*{suffix}")','run_dir.glob(f"desk-{tag}-*")',"t2"),
("R27",RR,'return exit_code_of(result["ok"], written, left, unseen, counter_known)','return exit_code_of(result["ok"], True, left, unseen, counter_known)',"t3"),
("R39",SUP,'    if os.environ.get(REQUIRE_SCAN_ENV):','    if os.environ.get(REQUIRE_SCAN_ENV) == "1":',"t4"),
("N01",RR,'return read.files > 0 and','return read.files >= 0 and',"t2"),
("N02",RR,'and read.unreadable == 0 and','and True and',"t2"),
("N03",RR,'and "created" in read.totals','and True',"t2"),
("N04",RR,'and not unseen and counter_known else EXIT_FAILED','and not unseen else EXIT_FAILED',"s3e or t9"),
("N05",RR,'return exit_code_of(result["ok"], written, left, unseen, counter_known)','return exit_code_of(result["ok"], written, left, unseen, True)',"t9"),
("N06",RR,'        except (OSError, ValueError, AttributeError, TypeError):\n            unreadable += 1','        except (OSError, ValueError, AttributeError, TypeError):\n            pass',"t2"),
("N07",RR,'        except (OSError, ValueError, AttributeError, TypeError):','        except (OSError, ValueError, AttributeError):',"t2"),
("N08",RR,'if not isinstance(tag, str) or not tag:','if not isinstance(tag, str):',"t7"),
("N09",RR,'    if not tag:\n        raise ValueError("the run tag must not be empty")','    if tag is None:\n        raise ValueError("the run tag must not be empty")',"t7"),
("N10",BR,'    if not isinstance(host, str) or not is_loopback_host(host):\n        raise ValueError(LOOPBACK_HOST_TEXT)\n    return host','    if not is_loopback_host(host):\n        raise ValueError(LOOPBACK_HOST_TEXT)\n    return host',"t6c or t12"),
("N11",FK,'Config().fakes_host if host is None else host','host or Config().fakes_host',"t6"),
("N12",IM,'        require_loopback_host(host)  # before any file','        pass  # before any file',"t6"),
("N13",SM,'        require_loopback_host(host)  # before any file','        pass  # before any file',"t6"),
("N14",RR,'low=1, high=PORT_MAX)\n    return value','low=0, high=PORT_MAX)\n    return value',"t8"),
("N15",RR,'unseen = contacts_not_accounted_for(\n            hub_stats.get("created"),\n            accounted,\n            hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),\n            len(lead_ids),\n        )','unseen = 0',"s3 or t9"),
("N16",RR,'counter_known = counter_is_known(hub_read)','counter_known = True',"t9"),

("M1",RR,'possible = created + max(0, open_creates)','possible = created',"t15"),
("M2",RR,'possible = created + max(0, open_creates)','possible = created + open_creates',"t15"),
("M3",RR,'        possible = min(possible, leads)','        possible = possible',"t15"),
("M4",RR,'    if leads is not None:\n        possible','    if False:\n        possible',"t15"),
("M5",RR,'hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),','0 + hub_stats.get("create_unknown", 0),',"t15"),
("M6",RR,'            len(lead_ids),\n        )','            None,\n        )',"t15"),
("C1",CR,'self._n["create_open"] += 1','self._n["create_open"] += 0',"t15"),
("C2",CR,'            self._n["create_open"] -= 1\n            write_stats','            self._n["create_open"] -= 0\n            write_stats',"t15"),
("C3",CR,'            if opened:  # a reply that proves','            if True:  # a reply that proves',"t15"),
("C4",CR,'if opened is not None and not opened:','if opened is not None:',"t15"),
("C5",CR,'self._settle_create("created")','self._settle_create(None)',"t15"),
("C6",CR,'self._settle_create("conflicts")','self._settle_create(None)',"t15"),
("C7",CR,'            self._settle_create(None)\n            raise\n        except Exception:  # 5xx','            raise\n        except Exception:  # 5xx',"t15"),
("U1",RR,'hub_stats.get("create_open", 0) + hub_stats.get("create_unknown", 0),','hub_stats.get("create_open", 0),',"t17"),
("U2",CR,'        except Exception:  # 5xx, 408 or an unclear 2xx: the contact MAY exist\n            self._settle_create("create_unknown")','        except Exception:  # 5xx, 408 or an unclear 2xx: the contact MAY exist\n            self._settle_create(None)',"t17"),
("U3",CR,'            if opened:  # a timeout or a transport error after the request left: the contact MAY exist\n                self._settle_create("create_unknown")','            if opened:  # a timeout or a transport error after the request left: the contact MAY exist\n                self._settle_create(None)',"t17"),
("U4",CR,'        except CrmNothingStored:  # a clear 4xx refusal: nothing was stored','        except CrmError:  # a clear 4xx refusal: nothing was stored',"t17"),
("U5",CR,'write_stats_strict(self.s.stats_file, self._n)  # must be on disk','write_stats(self.s.stats_file, self._n)  # must be on disk',"t18"),
("U6",CR,'                        raise CrmCounterUnwritable(','                        pass; raise CrmCounterUnwritable(',"t18"),
("U7",CR,'                        self._n["calls"] -= 1\n','                        self._n["calls"] -= 0\n',"t18"),
]
only=sys.argv[3:]
out=open(O+sys.argv[2],"a")
for mid,f,old,new,k in muts:
    if only and mid not in only: continue
    p=M+f; s=open(p,encoding="utf-8",newline="").read()
    if s.count(old)!=1:
        out.write(f"{mid}\tNOT-APPLIED count={s.count(old)}\n"); out.flush(); continue
    open(p,"w",encoding="utf-8",newline="").write(s.replace(old,new))
    try:
        env=dict(os.environ,PYTHONPATH=M+"src",PYTHONDONTWRITEBYTECODE="1",TMPDIR=TMP,PATH=R+"bin:"+os.environ["PATH"],GITLEAKS_BIN=R+"bin/gitleaks",DPLD_REQUIRE_SCAN="1",DPLD_REQUIRE_DEMO="1")
        files=[T] + (["tests/test_r7s_findings.py"] if "s3" in k else [])
        cmd=["unshare","-n","python",R+"src-v6/drivers/lo_up-q4g.py",R+"venv-br/bin/python","-m","pytest","-q","-p","no:cacheprovider","-x","-k",k,*files]
        try:
            r=subprocess.run(cmd,cwd=M,env=env,capture_output=True,text=True,timeout=900)
            res="KILLED" if r.returncode==1 else ("SURVIVED" if r.returncode==0 else "ERR rc=%d"%r.returncode)
            tail=r.stdout.strip().splitlines()[-1:]
            open(O+f"mutraw-{mid}.txt","w").write(r.stdout[-2000:])
        except subprocess.TimeoutExpired:
            res="TIMEOUT"; tail=[]
        out.write(f"{mid}\t{f}\t{k}\t{res}\t{tail}\n"); out.flush()
    finally:
        shutil.copyfile(S+f,p); same=filecmp.cmp(S+f,p,shallow=False)
        out.write(f"{mid}\trestored-byte-equal={same}\n"); out.flush()
