# Evidence C3 (raw; no judgement)

## Counts (first)
- fenced blocks total: 14 = 12 shell (11 tagged sh, 1 tagged bash), 1 python, 1 powershell; untagged 0. Blocks files: scratchpad c3/blocks/
- shell syntax failures: 1 block (block 14, step 13.4: bash -n exit 2, dash -n exit 2); blocks 1-3,5,7-13 exit 0 on both
- python compile failures: 0 (block 4 egress.py exit 0; embedded programs e01-e04 from blocks, e05-e12 from inline spans: all exit 0)
- COULD NOT RUN: shellcheck (not installed), pwsh (not installed) -> J4 done as mechanical scan only
- inline backtick commands outside fences are numerous (most step bullets); only the python-bearing inline spans were also scanned (see J3)

## J1 index (blocks-index.tsv)
```
n	step_id	plan_line_start	plan_line_end	lang	bytes	file
1	3-env-resmoke.sh	133	161	sh	4611	01-3-env-resmoke.sh-1.sh
2	3-ctl.sh	165	171	sh	445	02-3-ctl.sh-2.sh
3	3-sampler.sh	174	188	sh	634	03-3-sampler.sh-3.sh
4	3-egress.py	191	210	python	1009	04-3-egress.py-4.py
5	3-run.sh	213	219	bash	453	05-3-run.sh-5.sh
6	P-2	233	237	powershell	844	06-P-2-6.ps1
7	0.1	245	254	sh	1349	07-0.1-7.sh
8	1b.2	280	283	sh	1657	08-1b.2-8.sh
9	1b.3	286	292	sh	1167	09-1b.3-9.sh
10	8.4	326	328	sh	621	10-8.4-10.sh
11	11.1b	347	352	sh	1003	11-11.1b-11.sh
12	11.2	355	371	sh	1042	12-11.2-12.sh
13	E.1	380	396	sh	1093	13-E.1-13.sh
14	13.4	414	416	sh	756	14-13.4-14.sh
```

## J2 bash -n / dash -n (raw)
shellcheck: not installed
```
## bash -n 01-3-env-resmoke.sh-1.sh
exit=0
## dash -n 01-3-env-resmoke.sh-1.sh
exit=0
## bash -n 02-3-ctl.sh-2.sh
exit=0
## dash -n 02-3-ctl.sh-2.sh
exit=0
## bash -n 03-3-sampler.sh-3.sh
exit=0
## dash -n 03-3-sampler.sh-3.sh
exit=0
## bash -n 05-3-run.sh-5.sh
exit=0
## dash -n 05-3-run.sh-5.sh
exit=0
## bash -n 07-0.1-7.sh
exit=0
## dash -n 07-0.1-7.sh
exit=0
## bash -n 08-1b.2-8.sh
exit=0
## dash -n 08-1b.2-8.sh
exit=0
## bash -n 09-1b.3-9.sh
exit=0
## dash -n 09-1b.3-9.sh
exit=0
## bash -n 10-8.4-10.sh
exit=0
## dash -n 10-8.4-10.sh
exit=0
## bash -n 11-11.1b-11.sh
exit=0
## dash -n 11-11.1b-11.sh
exit=0
## bash -n 12-11.2-12.sh
exit=0
## dash -n 12-11.2-12.sh
exit=0
## bash -n 13-E.1-13.sh
exit=0
## dash -n 13-E.1-13.sh
exit=0
## bash -n 14-13.4-14.sh
14-13.4-14.sh: line 1: syntax error near unexpected token `;'
14-13.4-14.sh: line 1: `<prefix>; for p in $(cat $T/pids.txt 2>/dev/null); do ps -o args= -p $p | grep -qE 'crm_stub[.]py|smtp_catcher[.]py|demo_only[.]fake_model_server|qualify_stage[.]py' && kill $p && echo "killed stub $p"; done; for f in $T/drv-*.pid; do [ -e "$f" ] || continue; p=$(cat $f); ps -o args= -p $p | grep -q 'drive[.]py' && kill $p && echo "killed driver $p"; done; S=$(cat $T/sampler.pid 2>/dev/null); i=0; while [ -n "$S" ] && [ -d /proc/$S ] && [ $i -lt 10 ]; do i=$((i+1)); sleep 1; done; [ -n "$S" ] && [ -d /proc/$S ] && ps -o args= -p $S | grep -q 'sampler[.]sh' && kill $S && echo "killed sampler $S after ${i}s"; sleep 2; L=$(cat $T/pids.txt $T/drv-*.pid $T/sampler.pid 2>/dev/null | paste -sd, -); [ -n "$L" ] && ps -o pid=,args= -p "$L"; echo end-13.4'
exit=2
## dash -n 14-13.4-14.sh
14-13.4-14.sh: 1: Syntax error: ";" unexpected
exit=2
```
Fact: block 14 line 1 starts with the literal placeholder text '<prefix>;' (plan uses <prefix> as a name for the env.sh source line); bash and dash read it as a redirect.

## J3 python (raw: source block, kind, file in scratchpad c3/emb, approx plan line, exit)
```
block4 (3-egress.py) python block lines 191-210: compile exit=0
block1(3-env-resmoke.sh)	python-invocation	NO-BODY	plan_line~133	o=$(python3 -I $R/nlite/scripts/n8n_kill.py $GF);
block1(3-env-resmoke.sh)	embedded-python	e01.py	plan_line~153	len=129	exit=0	
block1(3-env-resmoke.sh)	python-invocation	NO-BODY	plan_line~133	python3 -I $R/egress.py $T/ss-cut.txt
block11(11.1b)	embedded-python	e02.py	plan_line~349	len=146	exit=0	
block12(11.2)	python-invocation	NO-BODY	plan_line~355	python3 -I $R/drive.py $R/nlite
block12(11.2)	embedded-python	e03.py	plan_line~358	len=535	exit=0	
block13(E.1)	python-invocation	NO-BODY	plan_line~380	python3 -I $R/drive.py $R/nlite
block13(E.1)	embedded-python	e04.py	plan_line~383	len=523	exit=0	
inline@108	python-invocation	NO-BODY	plan_line~108	python3 -I $R/nlite/scripts/n8n_kill.py <folder>
inline@230	embedded-python	e05.py	plan_line~230	len=60	exit=0	
inline@239	python-invocation	NO-BODY	plan_line~239	python3 -I -m py_compile
inline@257	python-invocation	NO-BODY	plan_line~257	python3 -I $R/egress.py $R/eg-pc/ss.txt
inline@261	embedded-python	e06.py	plan_line~261	len=152	exit=0	
inline@298	python-invocation	NO-BODY	plan_line~298	python3 -I $R/fill_flows.py $R/demo/handover/demo/n8n-flows-film-v5
inline@300	python-invocation	NO-BODY	plan_line~300	python3 -I $R/fill_flows.py x
inline@301	embedded-python	e07.py	plan_line~301	len=152	exit=0	
inline@302	embedded-python	e08.py	plan_line~302	len=117	exit=0	
inline@307	python-invocation	NO-BODY	plan_line~307	python3 -I $R/demo/handover/demo/n8n-mainframe/crm_stub.py 8771
inline@307	python-invocation	NO-BODY	plan_line~307	python3 -I $R/demo/handover/demo/n8n-tests/smtp_catcher.py 2526
inline@307	python-invocation	NO-BODY	plan_line~307	python3
inline@308	python-invocation	NO-BODY	plan_line~308	python3 -I $R/drive.py $R/nlite
inline@316	python-invocation	NO-BODY	plan_line~316	python3 -I -m json.tool
inline@316	embedded-python	e09.py	plan_line~316	len=171	exit=0	
inline@335	python-invocation	NO-BODY	plan_line~335	python3 -I $R/drive.py $R/nlite
inline@340	python-invocation	NO-BODY	plan_line~340	python3 -I $R/drive.py $R/nlite
inline@340	python-invocation	NO-BODY	plan_line~340	python3 -I $R/drive.py $R/nlite
inline@340	python-invocation	NO-BODY	plan_line~340	python3 -I $R/drive.py $R/nlite
inline@345	python-invocation	NO-BODY	plan_line~345	python3 -I $R/drive.py $R/nlite
inline@372	python-invocation	NO-BODY	plan_line~372	python3 -I .../drive.py ...
inline@373	embedded-python	e10.py	plan_line~373	len=381	exit=0	
inline@376	embedded-python	e11.py	plan_line~376	len=228	exit=0	
inline@376	python-invocation	NO-BODY	plan_line~376	python3 -I $R/drive.py $R/nlite
inline@398	embedded-python	e12.py	plan_line~398	len=364	exit=0	
inline@399	python-invocation	NO-BODY	plan_line~399	python3 -I $R/drive.py $R/nlite
inline@548	python-invocation	NO-BODY	plan_line~548	python3 -c
```

## J4 pwsh not available: mechanical scan
=== J4 mechanical scan of PowerShell blocks ===
plan_line 236 hits=['--', '4+dq'] :: $FULL = git -C $WT rev-parse ($HEAD_PIN + '^{commit}'); "full=$FULL"; if ($FULL -ne $FULL_EXPECTED) { 'HEAD_PIN does not resolve to the expected sha: STOP' } else { git -C $WT merge-base --is-ancestor $FULL $BR; "ancestor exit=$LASTEXITCODE"; git -C $WT archive -o "$S\nlite.tar" $FULL; cmd /c "git get-tar-commit-id < $S\nlite.tar"; git -C $HD archive -o "$S\demo.tar" 5fdc659d1 handover/demo/n8n-mainframe handover/demo/n8n-tests handover/demo/n8n-flows-film-v5; Get-FileHash "$S\nlite.tar", "$S\demo.tar" | Format-List }

## J5 variable cross-reference (regex-based, includes loop vars and names inside embedded python/awk; raw)
```
=== J5 variables ===
var	defined_in(block n)	used_in(block n)
B	2	2
C	1,2	2,3
CASE	12,13	12,13
DEAD	10	10
DPID	12,13	12,13
EG	1	
END	3	3
ERR	11	11
EV	1,5	5
FULL	6	6
G	7	7
GAP	11	11
GF	1	1
GP	1	1
GPORTS	1	1
HD	6	6
HEAD_PIN	6	6
HOME	1,2	1,3,7,8,9,10,11,12,13
IFS	7	
KF	1	1
KT	11	11
L	11,14	14
MODS	1	
N	10	10
N8N_BLOCK_ENV_ACCESS_IN_NODE	1,2	
N8N_COMMUNITY_PACKAGES_ENABLED	1	
N8N_DYNAMIC_BANNERS_ENABLED	1	
N8N_INSTANCE_AI_TEMPLATES_DISABLED	1	
N8N_LICENSE_AUTO_RENEW_ENABLED	1	
N8N_TEMPLATES_ENABLED	1	
N8N_USER_FOLDER	1,2	
N8N_VERSION_NOTIFICATIONS_ENABLED	1	
N8N_VERSION_NOTIFICATIONS_WHATS_NEW_ENABLED	1	
NM	1	
NP	1,2	1,2
ON_ERROR_STOP	1	
P	1	
PATH	1,2	1
PID	12,13	12,13
R	1,7	1,3,7,10,12,13
RD	11	11
REAL	10	10
S	14	6,14
SP	1	1
T	1	1,3,7,8,9,10,11,12,13,14
W	1	1,7
args	14	
e	1	1
exit	1,8	
g	1,11	1
gap_s	11	
i	1,14	1,14
identity	1	
k	11	
kill	11	
l	5	5
method	1	
n	1	1
n8n_error_any	11	
name	1	
nf	1	1
o	1	1
p	1,3,14	1,3,14
pg	1	
pid	12,13,14	
r	11	
ready	11	
s	5	5,7
stubs	1	
t	12,13	12,13
void_before	11	
=== flags ===
FACT: block 3 (3-sampler.sh) uses $f with no earlier definition in any block (defined in no block)
FACT: block 3 (3-sampler.sh) uses $q with no earlier definition in any block (defined in no block)
FACT: block 6 (P-2) uses $BR with no earlier definition in any block (defined in no block)
FACT: block 6 (P-2) uses $FULL_EXPECTED with no earlier definition in any block (defined in no block)
FACT: block 6 (P-2) uses $LASTEXITCODE with no earlier definition in any block (defined in no block)
FACT: block 6 (P-2) uses $S with no earlier definition in any block (defined later in block 14)
FACT: block 6 (P-2) uses $WT with no earlier definition in any block (defined in no block)
FACT: block 7 (0.1) uses $f with no earlier definition in any block (defined in no block)
FACT: block 7 (0.1) uses $id with no earlier definition in any block (defined in no block)
FACT: block 7 (0.1) uses $x with no earlier definition in any block (defined in no block)
FACT: block 11 (11.1b) uses $f with no earlier definition in any block (defined in no block)
FACT: block 14 (13.4) uses $f with no earlier definition in any block (defined in no block)
```
