# Loopback re-smoke: one command list for the lead

**STATUS: UNVERIFIED AS A WHOLE. Nothing in this file was run. Every command, expected line and time below is copied from the two input files and has never been executed. Written Mon 16 Nov 2026 (UTC). Static text edit, made-up data only.**

Sources, and only these for commands: `inputs/plan-wp6-resmoke-v5.md` (called "the plan"; line numbers are its own) and `inputs/OWNER-STEPS-realrun-v5-core-hardening.md` (called "steps v5"). **The plan is required reading: this list holds the order of the steps, the run form (the exact line the lead types) and the expected lines. The paste bodies (the code of each step) stay in the plan and are not copied here, so they cannot drift.** Where the plan gives no command for a step of this run, this file says `[LEAD FILLS: the plan gives no command]` and invents nothing. For P-2 and P-3a the plan does give bodies (P-2: plan lines 233-237, the code is on lines 234-236; P-3a: the Write step at plan line 229 with glue text at plan lines 132-223), so the only thing the lead fills there is the re-pin values. The user-folder name in Windows paths is written `<USER>`: take it from plan line 112 (the plan spells it out; this file does not copy the owner's name).

## Words box

- **take**: the checking program (`scripts/run_real_check_n8n.py`) and the n8n flows it starts for one recording run on the throwaway accounts.
- **re-smoke**: a repeat quick test of the changed flows, run again after earlier gaps were fixed. Here it means the plan `plan-wp6-resmoke-v5.md` and nothing else.
- **loopback**: every program answers only on this laptop's own address (127.0.0.1); nothing is sent to the internet on purpose, and this is watched, not blocked.
- **evidence-final**: the last full evidence run (tests, checks, saved raw output) made on the merged head; the re-smoke starts only after it has passed.
- **merged head**: the newest commit of the combined code after the fix branches were merged.
- **lead**: the Claude session that runs the studio's work. It is software and runs this list. It is not the owner.
- **owner**: the studio's owner, the one person who decides; he must say yes before the lead starts.
- **runner**: whoever carries out the plan's steps; here the lead. Its Linux user (the user account inside WSL that the lead's commands run as) is the "runner user"; the plan writes it as `<runner>` in checks 1.5 and 4.2.
- **WSL**: Windows Subsystem for Linux, the Linux (Ubuntu) that runs inside this Windows laptop. Every `wsl.exe` command below runs there.
- **HEAD_PIN**: the plan's name for the one code version (a short commit id) the run tests; the lead re-pins it to the merged head (step 3).
- **PROGRESS**, **INDEX**, **ENV**: three evidence files in the run's evidence folder `evidence-2\` (section 6). `PROGRESS.md` gets one line per step, with the time in UTC and IST. `INDEX.md` holds the pass/fail table (Part B, plus Part A filled). `ENV.md` records the environment (versions, addresses, ports).
- **evidence-2**: the plan's evidence folder for this run (plan line 112; section 6 gives the path). The plan gives the name and does not explain the number 2 (my reading: an earlier smoke run used evidence-1; UNVERIFIED).
- **register**: the file `agents-register.md` in the folder `_local` under the Windows root `C:\Users\<USER>\Downloads\Hadavin\` (plan line 241 writes it as `_local\agents-register.md`; the root prefix is my reading, UNVERIFIED). One row per started program, written BEFORE each start (see the rules box; the row fields come from the studio's supervision rule, not from the plan).
- **board item 1**: item 1 of the lead's answers in `work/LEAD-ANSWERS.md` (line 87): the first rehearsal of the changed flows, which is this re-smoke.
- **R1, R2, R4, R5**: the plan's own rule names (plan section 1, lines 108-112). R1 = no fallback kill for n8n, a failure is a STOP; R2 = the labelled clean-up kill after a STOP; R4 = the step classes and the time limit; R5 = how a paste reaches WSL and how evidence is saved. The rules box below restates the ones the lead needs.

## Rules box (plan section 1; applies to every step)

- **Stop rule (R1).** A STOP stops the run: write PROGRESS and INDEX, then do section 4. Nothing after a STOP counts as evidence (plan line 108).
- **Step classes (R4).** STOP = the run ends; GO = a finding, the run goes on; REC = record only. Time limit per step = 2 x the minutes the plan gives for that step (plan line 111); the plan names `exit=124` (the time limit hit) as a STOP only for the n8n start and kill steps (R1, plan line 109), so for other steps the class of a time-out is the step's own class.
- **Register (plan line 241).** Write a row in the register BEFORE each start: keep-alive, sampler, control n8n, take n8n, the Postgres container, the 4 stub services, and each detached driver (B2, C, D, E). Row fields: id, purpose, started, expected end, last checked, state, next action. Close each row when the item ends (section 4).
- **PROGRESS (plan line 112).** After every step the runner writes ONE line in `evidence-2\PROGRESS.md`: step id, result, time in UTC and IST (IST = UTC + 5 h 30 min), written with the Write or Edit tool.
- **PowerShell variable.** Every step below that uses `$RS` is a PowerShell call, and the variable does not survive between calls: set `$RS` (section 3) at the start of EVERY PowerShell call (plan line 112 gives the path inline).

## 0. Cost and limits (plan)

- Cost US$0: loopback only, stand-in programs, made-up data, no real mailbox, HubSpot, Gmail, model call, DNS or reverse lookup (plan line 5: "US$0 ... inside the owner's WP6 smoke yes of 2026-11-15"; plan section 2 and lines 38 and 73).
- Time: a floor of 171 min (2 h 51 min) when nothing goes wrong; quote the owner 3.5 to 4.5 hours (plan lines 443-445). The plan says a floor, not a promise.
- The plan's own HEAD_PIN is PROVISIONAL (`eec6ba4`, branch `take/nlite-int-r3`) and a later head is being built (plan lines 2-3). The lead re-pins before the run (step 3 below).
- Nothing is committed, pushed or merged by this run (plan line 489).

## 1. The question to the owner (send first; the owner decides)

Wording for the lead to send, plain words:

> I want to run a practice test of the changed flows on this laptop. It uses stand-in programs and made-up people only: no real mailbox, no HubSpot, no model call, no money (US$0). I start it only after the final test run on the merged code (the newest combined version of the code, after the fixes were put together) has passed. It takes about 3.5 to 4.5 hours of my work (2 h 51 min if nothing goes wrong). I will not touch your own n8n (the copies that may be running on this laptop and listen on the network port numbers 5678 and 5679, the usual numbers for n8n; a port number is like a numbered door of the laptop that a program listens at). Do you say yes or no, and which start time?
>
> - Slot 1: Tue 17 Nov, start 09:00 UTC = 14:30 IST (earliest possible); realistic end by 13:30 UTC = 19:00 IST.
> - Slot 2: Tue 17 Nov, start 13:00 UTC = 18:30 IST; realistic end by 17:30 UTC = 23:00 IST.
> - Slot 3: Wed 18 Nov, start 09:00 UTC = 14:30 IST; realistic end by 13:30 UTC = 19:00 IST.
> - Or name another time. No slot starts before Tue 17 Nov 09:00 UTC.

Rules from the lead's board item 1 (LEAD-ANSWERS line 87): "Not by Tue 17 Nov 03:30 UTC" is NOT a deadline for the lead to ask and NOT a deadline for the owner to answer; my reading (UNVERIFIED, the source gives no more words) is that the re-smoke result is not needed by then and the board must not wait on it; the lead does not wait on it; the earliest start is Tue 17 Nov about 09:00 UTC / 14:30 IST. The owner's answer is a yes or no plus one slot. No answer = no run. The end times above are start + 4.5 h (plan line 445), my arithmetic, UNVERIFIED.

What the owner does during the run: nothing the plan names. The lead starts Docker Desktop before the run (plan line 240, P-4); whether that needs the owner at the laptop is [LEAD FILLS: the plan gives no command].

## 2. Pre-checks (all must hold before step 3; any failure = do not start)

1. **evidence-final passed on the merged head.** Meaning (my reading, UNVERIFIED): the saved raw output of the evidence-final run names the merged head's commit id and shows every check passed, with no failure line. [LEAD FILLS: the plan gives no command] (the plan says only that the run follows evidence-final; the rule is in `work/LEAD-ANSWERS.md` line 87, which is board item 1: the lead's answer that the re-smoke starts only after evidence-final). Write the merged head sha and the evidence file name in the run log.
2. **Owner said yes with a slot** (section 1). Write the quoted yes and time in PROGRESS.
3. **Run folder absent (P-1).** Plan line 231 and 275: `$HOME/hadavin-smoke` must be absent at the start (P-1 prints `absent`), and 1.5 expects every file mode 600, directories 700, owned by the runner (the Linux user that runs the lead's commands). My reading: the run folder belongs to the runner only. UNVERIFIED reading; P-1 and 1.5 are the plan's checks.
4. **Ports.** Rehearsal n8n uses 5690 (broker 5691) and the control n8n 5692 (5693); stage 8765; fake model 48767; stub CRM 8771; mail catcher 2526; Postgres 55433 (plan line 121). The owner's own n8n on 5678 and 5679 is recorded in P-1 and 13.7 and is never touched (plan lines 121, 231, 421, 489). P-1 prints a count of listeners on the rehearsal ports; the expected value is `0`.
5. **Docker Desktop running** and the image `postgres:16` already local (P-4 expects image count `1`; no pull, ever; plan line 240).
6. **Register file ready** (plan line 241). The register is `_local\agents-register.md` (see the Words box for the folder). Before EACH start of keep-alive, sampler, control n8n, take n8n, the Postgres container, the 4 stub services and each detached driver (B2, C, D, E) the lead writes its row first. A start without a row = do not start.
7. **PROGRESS file ready** (plan line 112). `evidence-2\PROGRESS.md` takes one line per step with the time in UTC and IST; `run.sh` makes the folder at P-1 (that it exists at P-2 is UNVERIFIED), so the first PROGRESS line is written after P-1.

## 3. Steps, in order

How every WSL step runs (plan line 112, R5): the lead writes the step's paste file with the Write tool, then runs it from the PowerShell tool as shown. The verdict is the `exit=<n>` line in the output, never the tool status (`wsl.exe` returns `tee`'s exit code). Never call `wsl.exe` from the Git Bash tool: every block below that starts with `wsl.exe` is PowerShell, and the only Git Bash commands in this file are the two plan line 3 commands in step 3. Each paste body is the code span after the step id in the plan, verbatim, at the plan line given; this file does not copy the bodies so they cannot drift from the plan. **PowerShell blocks are wrapped so that the evidence is saved (plan line 112, R5).** Every PowerShell block below (P-2, P-5, 9.0k, 11.0k, 13.5k and the tail of 13.9) is run as `& { <block> } *>&1 | Tee-Object -Append -FilePath C:\Users\<USER>\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\evidence-2\<log>.log`, with the log name of its section: `p` for P-2 and P-5, `s9` for 9.0k, `s11` for 11.0k, `s13` for 13.5k and the 13.9 tail. The blocks below are already written in this wrapped form. The folder `evidence-2\` is made by `run.sh` (plan line 112), so it exists once P-1 has run; that it exists at P-2 is UNVERIFIED. A STOP stops the run: write PROGRESS and INDEX, go to section 4 (plan line 108, R1). If a result differs from "expected", the plan's classes are STOP (end the run), GO (finding, carry on) and REC (record only) (plan line 111); the class is named per step in the plan.

Set at the START OF EVERY PowerShell call (the variable does not survive between calls; about 60 later commands use it). The path is the plan's `run.sh` location (plan lines 112, 212); plan line 112 writes the same path inline, so the lead may also paste the path in place of `$RS`:

```powershell
$RS = '/mnt/c/Users/<USER>/Downloads/Hadavin/_local/scratch/wp6-smoke/run.sh'
```

### 3.1 Preconditions (outside the clock; order P-3a, P-1, P-2, P-3b, P-4, P-5; plan line 228)

**1. P-3a** write glue and paste files with the Write tool, no WSL (plan line 229). The glue text is in the plan at lines 132-223 and each paste body is the code span after its step id in the plan; the lead copies them from the plan, not from this list. Expected: every file written; nothing run.

```bash
# P-3a is the Write tool, not a shell command: nothing to type here; bodies are in the plan (lines 132-223 for the glue)
```

**2. P-1** (plan line 230; body at line 230). Expected (plan line 231): `absent`; a path under `.../node_modules/n8n/`; `2.46.6`; `v24.22.2`; no assert; `8`; `BASH_ENV=unset ENV=unset`; at least 2 GB free; `0`; owner-port count is record-only. Differs: any other value = STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS P-1 p
```

**3. P-2** PowerShell block, body at plan lines 233-237 (the code is on lines 234-236; lines 233 and 237 are the code fence marks). Before running, the lead re-pins the four values on its first line to the merged head (RE-PIN line, plan line 3). The re-pin is an edit of the LEAD'S OWN working copy of the plan, in three places that must change together: the header HEAD_PIN line (plan line 2), the section 2 `code` row (plan line 120) and the first line of P-2 (plan line 3, item 3). It touches no steps v5 file, no core-hardening file and no file outside the lead's plan copy. Plan line 3 then asks for two more things at the final head `<F>` (worktree `<WT>`), both copied in full below with the owner's user-folder name written `<USER>`: (a) regenerate the section 11 part A line column in Git Bash after P-3a wrote `strings.txt` (an empty column = the string is gone: edit the plan before the run); (b) read the changed output wording of the two scripts, and check that the new exit 3 cannot be returned on a real kill (`gone` needs `kill exit=0` and `confirmed gone`). UNVERIFIED: whether plan lines 234-236 already contain every value to re-pin. Expected (plan line 238): `full=` the expected sha; `ancestor exit=0`; the tar commit id equals it. Differs: STOP.

```powershell
# Wrapped form, log `p`: & { <P-2 body, plan lines 233-237, re-pinned> } *>&1 | Tee-Object -Append -FilePath C:\Users\<USER>\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\evidence-2\p.log
[LEAD FILLS: re-pin values only (HEAD_PIN, FULL_EXPECTED, BR, WT) for the merged head; the body itself is plan lines 234-236, pasted from the plan]
```

Plan line 3, command (a), Git Bash, copied in full:

```bash
while IFS=$'\t' read -r id f s; do printf '%s %s %s\n' "$id" "$f" "$(git -C <WT> grep -n -F -e "$s" <F> -- "scripts/$f" | cut -d: -f3 | paste -sd, -)"; done < C:/Users/<USER>/Downloads/Hadavin/_local/scratch/wp6-smoke/strings.txt
```

Plan line 3, command (b), copied in full (the plan's first commit in it is `eec6ba4`, the provisional pin):

```bash
git -C <WT> diff eec6ba4 <F> -- scripts/n8n_start.sh scripts/n8n_kill.py | grep -E '^[-+].*(echo|print|die|refused|confirmed|exit)'
```

**4. P-3b** scan the written files (plan line 239; body at line 239). Expected: grep prints nothing and `scan exit=1`; `compile exit=0`; no `syntax:` line; no `bad strings line`; `20`. Differs: a carriage return found = run the `sed -i 's/\r$//'` fix in plan line 239 per listed file, then P-3b again; another non-ASCII byte = rewrite that file, then P-3b again.

```powershell
wsl.exe -d Ubuntu -e bash $RS P-3b p
```

**5. P-4** check only (plan line 240). Expected: a server version; `1`; the container-name list is the clean-up baseline. Differs: `docker info failed` or an image count other than `1` = STOP; the lead starts Docker Desktop and re-runs P-4.

```powershell
wsl.exe -d Ubuntu -e bash $RS P-4 p
```

**6. P-5** WSL keep-alive, PowerShell block, NOT through `run.sh` (plan line 241). First add the register row in `_local\agents-register.md`. Expected: one line `keepalive pid=<n>`; write `<n>` into the register and into 9.0k, 11.0k and 13.5k (the only value the runner fills in). Differs: no pid line = STOP.

```powershell
& { $k = Start-Process -WindowStyle Hidden -PassThru -FilePath wsl.exe -ArgumentList '-d','Ubuntu','-e','bash','/mnt/c/Users/<USER>/Downloads/Hadavin/_local/scratch/wp6-smoke/pastes/P-5.sh'; "keepalive pid=$($k.Id)" } *>&1 | Tee-Object -Append -FilePath C:\Users\<USER>\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\evidence-2\p.log
```

### 3.2 S0 setup, sampler, parser control (plan lines 243-257; log `s0`; STOP class)

**7. 0.1** (one paste; line 244-254). Expected (line 255): derived-copy counts `1 1 1 1 1 0`; every string row of section 11 part A prints a count of at least 1 (H1, H2 count 0 = record only; any other 0, empty count or error text = STOP, the lead re-pins or edits the plan); probe hash `bcad19e92f65d9804c06d3514e3767ea838881c4f06dbc3fb9853e900ee90ccc`. Differs: STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS 0.1 s0
```

**8. 0.2** baseline and sampler (line 256). Expected: the second line count is larger than the first. Differs: STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS 0.2 s0
```

**9. 0.3** parser positive control (line 257). Expected: exactly one line `NONLOOP 1 ours tcp ESTAB 192.0.2.10:443 999001` and count `1`. Differs: STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS 0.3 s0
```

### 3.3 S0c control home (plan lines 259-267; log `s0c`; STOP class; the take n8n is not running)

**10. 0c.1** (line 260). Expected: `1` then `3`. Differs: STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS 0c.1 s0c
```

**11. 0c.2** (line 261). Expected: `import exit=0` and `publish exit=0`. Differs: STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS 0c.2 s0c
```

**12. 0c.3** (line 262-266). Expected: readiness under 120 s, `registry=0 unknown=0`, then run `0c.3a` (line 263). The control reads `env_canary`, `env_path`, `expr_path` as `READABLE`. The last command of 0c.3 is `eg ctl3` (line 266): its `fd lines` count is above 0 and it prints `EGRESS-OK` (an `ours` line = STOP; the unattributed list is record only, a new `:443` peer is a GO finding). Differs: run `0c.3r` (line 264) once, as `wsl.exe -d Ubuntu -e bash $RS 0c.3r s0c`, and repeat 0c.2-0c.3; a second refusal = STOP; a field not `READABLE` = STOP; a file read not `READABLE` = label, not STOP; any `ours` egress line = STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS 0c.3 s0c
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 0c.3a s0c
```

**13. 0c.4** first real kill by the pinned script (line 267). Expected: `GONE-OK`, `EGRESS-OK`. Differs: STOP (no fallback kill).

```powershell
wsl.exe -d Ubuntu -e bash $RS 0c.4 s0c
```

### 3.4 S1 secrets and value files (plan lines 269-275; log `s1`; STOP class)

**14-19.** Run in order. Expected per step: 1.1 prints `8`; 1.2 prints `0`; 1.2b prints `6`; 1.3 prints `grep exit=0` with every count at least 1 (rule for a 0 and for `exit=124` at plan line 273). Conditional step when plan line 273 says to remove a name from the env file: `wsl.exe -d Ubuntu -e bash $RS 1.3d s1 <NAME>` (plan line 273; `pastes/1.3d.sh` removes that name from the take's env file and prints a count that must be `0`; `<NAME>` is the variable name the plan names; an `EXECUTIONS_*` removal makes E5 UNVERIFIED). UNVERIFIED: the exact condition is at plan line 273, not copied here; 1.4 prints `0`; 1.5 shows files 600 and directories 700. Differs: per plan lines 270-275, STOP unless the plan says GO or record only.

```powershell
wsl.exe -d Ubuntu -e bash $RS 1.1 s1
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 1.2 s1
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 1.2b s1
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 1.3 s1
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 1.4 s1
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 1.5 s1
```

### 3.5 S1b Postgres, roles, negative tests (plan lines 277-293; log `s1b`; STOP class)

**20-22.** Expected: 1b.1 a container id, `dk port` exactly `5432/tcp -> 127.0.0.1:55433`, ready under 60 s, `tcp 55433 ok`, `P55=<n>`, `pg=Up ...`; 1b.2 `roles exit=0`, `pg log marker lines: 0`; 1b.3 ten denials N1-N10 and the P checks as listed at plan line 293, `roles.txt` exactly `smk_app|f|f|f|f`, `smk_count|f|f|f|f`, `smk_n8n|f|f|f|f`. Differs: STOP (least privilege not proven).

```powershell
wsl.exe -d Ubuntu -e bash $RS 1b.1 s1b
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 1b.2 s1b
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 1b.3 s1b
```

### 3.6 S2 fill and import (plan lines 295-304; log `s2`; STOP class; n8n not running)

**23-30.** Expected: 2.0 `config-absent` and `probe-absent`; 2.1 `filled film 4 object`; 2.2 all `0`; 2.3 `creds written array`, `exit=0`; 2.4 five `exit=0`; 2.5 six workflow ids, three credentials each `True`; 2.6 five `exit=0` (exec line record only); 2.7 `0`; above 0; exactly `smk_n8n`; `3`. Differs: STOP on the first non-zero exit in 2.3-2.6; run `2.err` (line 296), as `wsl.exe -d Ubuntu -e bash $RS 2.err s2`, and tell the lead; there is no second form in this run.

```powershell
wsl.exe -d Ubuntu -e bash $RS 2.0 s2
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 2.1 s2
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 2.2 s2
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 2.3 s2
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 2.4 s2
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 2.5 s2
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 2.6 s2
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 2.7 s2
```

### 3.7 S3 and S4 stub services and the take n8n (plan lines 306-313; logs `s3`, `s4`; STOP class)

**31-35.** Expected: 3.3 four `python3` lines; 3.4 the printed listener count (`4 + P55`), `0`, `T0 rows {}`, `stubs=4/4`; 4.1 readiness under 120 s, pid equals pgid and `stubs=4/4`; 4.2 `0`, `0`, group listens on 127.0.0.1:5690 and :5691 only, `0`, `600 ... n8n.lock`, no `postgres` row with a client address, then the pg-hba comparison (plan line 312; the runner writes it in PROGRESS): the first matching `host` row for the `smk_n8n` client address is `scram-sha-256` = a password is the only gate (as planned); the first matching row is `trust` (for example `127.0.0.1/32`) = the roles are NOT password-gated on loopback: a GO finding, written in L4 and in `ENV.md`; 4.4 `EGRESS-OK`. Differs: STOP (`NOT-UP` = STOP).

```powershell
wsl.exe -d Ubuntu -e bash $RS 3.3 s3
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 3.4 s3
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 4.1 s4
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 4.2 s4
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 4.4 s4
```

### 3.8 S6, S7, S8 probe, runner environment, refusal and kill identity (plan lines 315-329; logs `s6`, `s7`, `s8`)

**36-39.** Expected: S6 every probe field a string, none equal to `READABLE`, `denial-class` all `True`, marker count `0`, exec result 404 or error with `smk-exec-ran` `0`, `EGRESS-OK`; S7 other group members' marker count `0`, `kindof` main = `start`, no missing name, `DB_` count `6`; 8.1 one line `refused: n8n is already running (process <PID>); stop it with n8n_kill.py first`, `exit=2`, same `n8n.pid`, readiness 200; 8.4 `refused: ...`, `exit=2`, `N-IS-REAL`, `n8n.pid named a dead process; found this take's live n8n as process <REAL> by its identity`, `killed n8n process <REAL> (process group), confirmed gone`, `kill exit=0`, `GONE-OK`. Differs: STOP; `exit=124`, `STOP` or `GONE-FAIL` = STOP (R1).

```powershell
wsl.exe -d Ubuntu -e bash $RS 6 s6
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 7 s7
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 8.1 s8
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 8.4 s8
```

### 3.9 S9 restarts and burst B2 (plan lines 331-337; log `s9`)

**40. 9.0k** keep-alive alive check, PowerShell block at plan line 332 with `<n>` from step 6. Expected: `keepalive alive`. Differs: STOP.

```powershell
& { try { $q = Get-Process -Id <n> -ErrorAction Stop; if ($q.ProcessName -eq 'wsl') { 'keepalive alive' } else { 'KEEPALIVE-DEAD (pid reused): STOP' } } catch { 'KEEPALIVE-DEAD: STOP' } } *>&1 | Tee-Object -Append -FilePath C:\Users\<USER>\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\evidence-2\s9.log
```

**41-43.** 9.1 round 1 (line 334), 9.4 burst B2 killed in flight then restart (line 335), 9.5 wait for the B2 driver (line 336). Expected: two rounds with `h`, `r`, `w` set and pid equal pgid; `GONE-OK`; one JSON line with 10 replies. Differs: `NOT-UP` or `w` empty in a round whose line says 0 published workflows = STOP; a positive `webhook-ready` in round 1 = GO finding.

```powershell
wsl.exe -d Ubuntu -e bash $RS 9.round s9
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 9.4 s9
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 9.5 s9
```

### 3.10 S10 stack sanity and same-id burst (plan lines 339-341; log `s10`)

**44.** Expected: listeners equal to the printed `6 + P55`; `stubs=4/4`; A two replies, status 200, second repeat true; P `"precondition": "PASS"`; B ten replies, at most one with repeat false; no `SUPERUSER-PASSWORD-LOGIN`; `EGRESS-OK`. Differs: STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS 10 s10
```

### 3.11 S11 in-flight crashes C and E (plan lines 343-399; log `s11`)

**45. 11.0k** keep-alive check: the same check as 9.0k with the same `<n>` (plan line 344), run wrapped with log `s11`. Expected `keepalive alive`; anything else = STOP.

```powershell
& { try { $q = Get-Process -Id <n> -ErrorAction Stop; if ($q.ProcessName -eq 'wsl') { 'keepalive alive' } else { 'KEEPALIVE-DEAD (pid reused): STOP' } } catch { 'KEEPALIVE-DEAD: STOP' } } *>&1 | Tee-Object -Append -FilePath C:\Users\<USER>\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\evidence-2\s11.log
```

**46. 11.1** (line 345). Expected: the listener count equals the printed expected number; every line `"ok": true`; the control answer shows 8000. Differs: a not-ok line = STOP, except the B2 rule: ONLY IF 11.1 shows exactly one not-ok line and that line is B2, run 11.1b (plan lines 346-353); `B2 GO rule met` = run 9.4 and 9.5 once more, then 11.1 again; `B2 GO rule not met` = STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.1 s11
```

**11.1b is CONDITIONAL: run it ONLY IF 11.1 shows exactly one not-ok line, B2 (plan line 346). After a clean 11.1 do NOT run it: it would print a false `B2 GO rule not met: STOP` and would clear the CRM hold (the 8000 ms delay) that 11.1 armed.**

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.1b s11
```

**47-51. Case C** (default case; plan lines 354-376). Expected: 11.2 the key, `GONE-OK`, readiness under 120 s; 11.3 `HIT`; 11.4 driver alive or ended with a JSON line, status 200, `tries >= 2`; 11.5 `final=done` (or `unknown` with an alert); 11.6 `created true 1`, `mails == 1`, `model_calls == 1`, `"ok": true`. Differs: MISSED or `tries == 1` = run 11.7 (line 377), as `wsl.exe -d Ubuntu -e bash $RS 11.7 s11`, then repeat 11.2-11.6 once with argument `D`, for example `wsl.exe -d Ubuntu -e bash $RS 11.2 s11 D` and `... 11.6 s11 D` (plan line 226: a paste that takes the case reads it as `$1`); mails, model calls or ok wrong = STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.2 s11 C
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.3 s11 C
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.4 s11 C
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.5 s11 C
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.6 s11 C
```

**52-57. Case E** double-mail window (plan lines 378-399). Expected: E.0 (it takes no argument: plan line 378; the E2 repeat is plan line 397) `"upsert_ack_delay_ms": 0` and `no-mail-hold`; E.1 the key, `GONE-OK`, restart readiness, driver alive; E.2 `HIT`; then 11.4 and 11.5 with argument `E` (not 11.6); 11.8 every line `"ok": true` for A, B, B2, C. Differs: E MISSED = one repeat as `E2`: run E.0 again WITHOUT an argument, then `run.sh E.1 s11 E2` and `run.sh E.2 s11 E2`, then 11.4 and 11.5 with `E2` (plan lines 397-398); a double mail (`mails >= 2`) is a GO finding that blocks the crash-safe claim (plan line 399 wording); any not-ok A, B, B2 or C line = STOP.

```powershell
wsl.exe -d Ubuntu -e bash $RS E.0 s11
```

```powershell
wsl.exe -d Ubuntu -e bash $RS E.1 s11 E
```

```powershell
wsl.exe -d Ubuntu -e bash $RS E.2 s11 E
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.4 s11 E
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.5 s11 E
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 11.8 s11
```

### 3.12 S12 leaks, key, one store, egress (plan lines 401-406; log `s12`; run order 12.2, 12.5, 12.5b, 12.3, 12.4)

**58-61.** Expected: 12.2 `marker-files.txt` lists only the nine files named at plan line 402, `n8n.out` `0`, per database `dump exit=0` size above 0 count `0`, Postgres log count equal to the 1b.2 count; 12.5 `600 <user>` and `1`; 12.5b `0` SQLite files, exactly two prefixes `postgres:app` (1 table) and `n8n:public`, owners as at line 404, execution status total above 0; 12.3 `EGRESS-OK` and the unattributed list recorded. 12.4 has no paste: the runner writes the verdict wording at plan line 406. Differs: STOP, except the GO and record-only items the plan names at lines 404-406.

```powershell
wsl.exe -d Ubuntu -e bash $RS 12.2 s12
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 12.5 s12
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 12.5b s12
```

```powershell
wsl.exe -d Ubuntu -e bash $RS 12.3 s12
```


## 4. Stop and clean-up commands (plan lines 408-423; run after the last step or at once after a STOP; log `s13`; every step skips what does not exist)

Each S13 paste starts with the fallback prefix from plan line 409. A STOP never skips this section.

**S13-0 (13.0)** sets the stop flag: ends the sampler within 0.5 s and the keep-alive within 5 s. Expected `stop-flag-set`.

```powershell
wsl.exe -d Ubuntu -e bash $RS 13.0 s13
```

**S13-1 (13.1)** take n8n through the pinned kill (line 411). Expected: no line, or `gone` prints `GONE-OK`. If `GONE-FAIL`: the labelled CLEAN-UP kill R2 (plan line 109): check `tr '\0' '\n' < /proc/<pid>/environ | grep -cFx "N8N_USER_FOLDER=<folder>/n8n"` equals 1 for the exact pid of this run (register row), then `/bin/kill -TERM -- -<pid>`, wait 30 s, `/bin/kill -KILL -- -<pid>`. Never kill by name or pattern; never kill a process this run did not start.

```powershell
wsl.exe -d Ubuntu -e bash $RS 13.1 s13
```

**S13-3 (13.3)** control home (line 412). Expected `control-gone` or `no control pid: skip`.

```powershell
wsl.exe -d Ubuntu -e bash $RS 13.3 s13
```

**S13-4 (13.4)** stub services, drivers and sampler, by exact pid after an args check (line 414-417). Expected: nothing listed before `end-13.4`.

```powershell
wsl.exe -d Ubuntu -e bash $RS 13.4 s13
```

**S13-5 (13.5)** leftover check (line 418). Expected: nothing before `end-n8n-list` (anything listed = STOP: run 13.1 again, then R2) and nothing before `end-p5-list` (a listed process is reported, never killed; the lead decides).

```powershell
wsl.exe -d Ubuntu -e bash $RS 13.5 s13
```

**S13-5k (13.5k)** keep-alive gone, PowerShell block at plan line 419 with the same `<n>`. Expected `keepalive-gone`; then close the register row.

```powershell
& { try { $q = Get-Process -Id <n> -ErrorAction Stop; if ($q.ProcessName -eq 'wsl') { 'keepalive still running: listed, not killed (lead decides)' } else { 'keepalive-gone (pid reused by another program)' } } catch { 'keepalive-gone' } } *>&1 | Tee-Object -Append -FilePath C:\Users\<USER>\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\evidence-2\s13.log
```

**S13-6 (13.6)** Postgres container removal, which also deletes the saved executions (line 420). Expected `hadavin-smoke-pg` or `no container: skip`, then `docker-baseline-equal`.

```powershell
wsl.exe -d Ubuntu -e bash $RS 13.6 s13
```

**S13-7 (13.7)** ports free and the owner's n8n untouched (line 421). Expected: an empty list, then `owner-ports-unchanged` (both empty means "not visible from WSL", record only).

```powershell
wsl.exe -d Ubuntu -e bash $RS 13.7 s13
```

**S13-8 (13.8)** copy to `evidence-2\raw\` and scan for secret markers (line 422). Expected: NO file listed before `ev-marker-scan done`. A listed file = STOP: the lead redacts it before any commit.

```powershell
wsl.exe -d Ubuntu -e bash $RS 13.8 s13
```

**Evidence write-up (between 13.8 and 13.9; plan lines 423 and 442).** After 13.8 and BEFORE 13.9 the runner writes `INDEX.md` (Part B table and Part A filled), `ENV.md` and finishes `PROGRESS.md` in `evidence-2\`. This is the position the plan gives; it is NOT right after 12.3.

**S13-9 (13.9)** delete the run folder. Run ONLY after INDEX.md, PROGRESS.md and ENV.md exist (line 423). Expected: `ev-marker-scan-clean`, then `removed`. A marker hit refuses the delete: redact, then re-run. After the run folder is gone, delete the two tar files with the PowerShell command of plan line 423, copied in full (wrapped, log `s13`; `<USER>` stands for the user-folder name the plan spells out):

```powershell
wsl.exe -d Ubuntu -e bash $RS 13.9 s13
```

```powershell
& { Remove-Item -Confirm:$false C:\Users\<USER>\Downloads\Hadavin\_local\scratch\wp6-smoke\nlite.tar, C:\Users\<USER>\Downloads\Hadavin\_local\scratch\wp6-smoke\demo.tar } *>&1 | Tee-Object -Append -FilePath C:\Users\<USER>\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\evidence-2\s13.log
```

What this deletes, and nothing more: the PowerShell command removes only two named files, `nlite.tar` and `demo.tar` (the two `git archive` copies, plan lines 120, 423). Everything else the run deletes is inside the run folder `$HOME/hadavin-smoke` (removed by `13.9` only after the realpath check in plan line 423 passes and the evidence scan found no marker) or is the run's own Postgres container `hadavin-smoke-pg` (removed by `13.6`). The plan's own `13.9` bash body is at plan line 423; it is run through `run.sh` as shown above and not copied here, so it cannot drift.


Do not kill the keep-alive by hand; 13.0 ends it (plan line 489). Docker Desktop stays as found. Close every register row and list the agents and shells started, with counts (CLAUDE.md supervision rule).

## 5. Facts this run is meant to confirm or refute (all currently UNVERIFIED; "result" column empty on purpose)

Part A: the five facts the lead named. The plan itself runs stand-in programs and the n8n flows; it does not run the take's own checking program (`run_real_check_n8n.py`) beyond a text search for one string (plan lines 531, 493: real-v5 at run time is not proven). Therefore the plan gives no command for any row in Part A, and the lead must supply one or move the fact out of this run.

| # | fact (UNVERIFIED) | source of the claim | which plan step tests it | command | result |
|---|---|---|---|---|---|
| A1 | The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list (search `take-<tag>-a`, `-b`, `-c`, example.com). The take program has no create, update, delete or archive call; its HubSpot key is read-only. | LEAD-ANSWERS lines 73, 79 | none in the plan | [LEAD FILLS: the plan gives no command] | |
| A2 | The program's own time need is computed as 2630 s + 6 x lease seconds, rounded up: 49 minutes at lease 45. The program refuses a start that leaves less than 49 minutes before the stop time (stop time Mon 23 Nov 18:29 UTC = 23:59 IST). HARD latest start accepted by the program: 17:40 UTC = 23:10 IST. Safe latest start: 17:30 UTC = 23:00 IST, because the program re-checks the window after the `y` prompt and the confirmation line (UNVERIFIED: RUNBOOK-V4.3-PATCH row P45, line 149, says this check is added after r28) and the 10-minute film pause lies outside the 49 minutes (RUNBOOK-V4.3-PATCH.md line 88): 17:30 + 49 min = 18:19, + 10 min pause = 18:29. The planning target stays 12:00 UTC = 17:30 IST (start by noon so a failed run still has the afternoon). The old figure "about 14 minutes" and the old latest start "about 18:15 UTC = 23:45 IST" are OBSOLETE (lead answer 7: the 14-minute figure was the old r28 number). | LEAD-ANSWERS.md table rows 6, 7, 14, 16 (lines 19, 20, 27, 29) and line 43 (17:30Z rule); `work/decision-list-for-lead.md` bottom block; RUNBOOK-V4.3-PATCH.md lines 44, 88; `work/open-items-table-history-9.md` line 38 | none in the plan | [LEAD FILLS: the plan gives no command] | |
| A3 | The start-time check: the program refuses to start when too close to the stop time, and exits with code 2 (steps v5 lines 28, 245, 258; re-grepped 16 Nov after the steps file was edited). | steps v5 lines 28, 245, 258 | none in the plan | [LEAD FILLS: the plan gives no command] | |
| A4 | The notice wording items: steps v5 line 135 now reads "3 test people, up to 3 model calls and the worst case, up to 3 contacts created and left behind in HubSpot for you to delete by a filtered list (step F2)" (reworded 16 Nov; it used to say the contacts are deleted at the end, which contradicted A1); the printed notice itself must say the take never deletes and lists leftovers (check at the re-smoke). Items to read off the printed notice: the confirmation number line, "Type y to start", the confirmation line, the money figures, the contact line. | steps v5 lines 130-137 (notice at 135); LEAD-ANSWERS lines 70, 73, 79 | none in the plan | [LEAD FILLS: the plan gives no command] | |
| A5 | REAL-check refusals: a bad login stops before any typed answer; piped or scripted `y` refused; closed input ends with exit code 2; an answer typed in under 2 seconds refused; a wrong confirmation line ends the run with nothing sent; a used run name, an existing lock file, or a too-late start are refused with exit code 2; the retire check ends with exit code 0 only when both logins are refused, 3 if one still works, 2 otherwise. | steps v5 lines 130-137, 186-188, 245, 257-258 (re-grepped 16 Nov after the steps file was edited) | none in the plan | [LEAD FILLS: the plan gives no command] | |

Re-check of steps v5 against the lead's answers (second pass, 16 Nov 2026; replaces the earlier flag, which cited line numbers that have since moved; I did NOT edit steps v5). Re-grepped today, current lines of `inputs/OWNER-STEPS-realrun-v5-core-hardening.md`:
- **Time figure:** line 28 (Words box, "Stop time") says the program's run takes about 49 minutes (2630 seconds plus 6 times the 45-second lease; UNVERIFIED), the hard latest start is 17:40 UTC = 23:10 IST, and the safe latest start is 17:30 UTC = 23:00 IST (UNVERIFIED); line 258 (Start deadline) says the same. The old "14 minutes" and "18:15 UTC" no longer appear in steps v5 (grep finds none). Consistent with the lead's answers 7 and 16. No flag remains.
- **Deleting contacts:** line 19 (Left behind) and line 44 (Delete) say the program never deletes contacts; line 44 says "Archive" is only Gmail's own button and that the sheet never uses it; line 135 (the notice) says contacts are "left behind in HubSpot for you to delete by a filtered list (step F2)"; lines 145-151 say the contacts stay, the program lists those it left behind, nothing is deleted by the program, and its HubSpot key is read-only (UNVERIFIED until the lead's loopback re-smoke on the merged head); line 168 (step G, item 1) and line 148 (step F) carry the master sentence verbatim. The earlier "archive" contradiction at the old line 32 is gone. No flag remains.
- What stays open for this re-smoke: the printed notice and the film-pause words are checked at the re-smoke on the merged head, not here (A4, A5). Lines in rows A3 to A5 were re-pointed to the current steps v5 lines on 16 Nov (again after the steps file was edited, B4-CITES); they move whenever steps v5 changes, so re-grep before use.

Part B: the plan's own 20 pass/fail rows (plan section 7, lines 464-486). Fill in `evidence-2\INDEX.md` with the plan's columns; the table below only carries the id, class and the step, with an empty result.

| id | claim in short (plan) | class | step | result |
|---|---|---|---|---|
| H1 | scripts under test are the pinned head; quoted strings present | STOP | P-2, 0.1 | |
| K1 | second start refused over live n8n | STOP | 8.1 | |
| K2 | dead pid in file: refused naming the real n8n; kill finds it | STOP | 8.4 | |
| K5 | every script kill `GONE-OK`, no fallback | STOP | 0c.4, 8.4, 9.4, 11.2, E.1 | |
| K8 | real task-runner identity verdict | record only | S7 | |
| T1 | restart gaps and "published workflows" line | record only (STOP if `w` empty or `NOT-UP`) | S9 | |
| B1 | same-id burst on the new stack; B2 killed in flight | STOP | 9.4, S10, 11.1, 11.1b, 11.8 | |
| C1 | driver survives kill; in-flight HIT with `tries >= 2` | STOP | 11.2-11.4 | |
| C3 | mails 1, model calls 1, `created true` 1 | STOP / record only | 11.5, 11.6, 11.8 | |
| DM | crash after lead mail stored: `mails == 1`; else blocks the crash-safe claim | GO finding | E.0-E.2, 11.4, 11.5, 11.8 | |
| NC | crash windows not covered (statement) | statement | none | |
| X1 | control reads env, path, expression | STOP (file read: label) | 0c.3 | |
| X2 | take denies every probe field; no marker leaks | STOP | S6, S7, 12.2, 12.5 | |
| E1 | module list accepted; switch names read | STOP / GO | 0c.1, 0c.3, 1.3, 4.2, S7 | |
| E3 | parser not blind; no non-loopback peer of ours (watched, not blocked) | STOP / GO | 0.3, 0c.3, 0c.4, 4.4, S6, S10, 12.3 | |
| E5 | executions saved on | record only (0 = GO) | 12.5b, 13.6 | |
| D1 | engine is Postgres database `n8n`; no SQLite | STOP | 2.7, S7, 12.5b | |
| L1 | three roles, ten denials | STOP | 1b.3, 3.4 | |
| L4 | roles in use; password login shown; no superuser login | STOP / record only | 2.7, 4.2, S10, 12.5b | |
| Z1 | clean-up complete; owner's n8n unchanged; no marker in evidence | STOP | P-1, P-4, S13 | |

## 6. Where the result goes

`C:\Users\<USER>\Downloads\Hadavin\egm\duplicate-proof-lead-desk\wp6\` (WSL path `/mnt/c/Users/<USER>/Downloads/Hadavin/egm/duplicate-proof-lead-desk/wp6/`). The plan's evidence folder is its subfolder `evidence-2\` (plan line 112): `INDEX.md` (the Part B table), `PROGRESS.md`, `ENV.md`, one `sN.log` per section, `raw\`. Put the Part A table result (filled) in `INDEX.md` too. After the run the lead gets the result reviewed by independent reviewer agents on `evidence-2\` (not the runner's verdict) and records findings in the blocker ledger (plan line 505). `[LEAD FILLS: the plan gives no command]` for the review step itself; the plan names the step only.

## 7. What I did not do or could not check

- Nothing here was run; every line is UNVERIFIED.
- Second pass (reader findings C-1 to C-7): the PowerShell blocks are wrapped with their log names; both plan line 3 commands and the plan line 423 tar-file command are pasted in full (`<USER>` for the user folder); the P-2 body (plan lines 233-237) and the P-3a Write step are still [LEAD FILLS]; the run.sh forms for 0c.3r, 1.3d, 2.err, 11.7 and the repeat as `D` are my reading of plan lines 226, 264, 273, 296, 377 and are UNVERIFIED as exact conditions. I did not read plan lines 130-225, 268-305, 315-375 or 447-486 in this pass, and the plan's Linux user name in the realpath check (plan lines 264, 423) is not copied.
- The plan's paste bodies are cited by line, not copied, to avoid drift (the plan itself says each paste file is "the code span ... verbatim").
- I assumed the step-to-run.sh mapping for steps with no explicit paste file name (for example `10`, `6`, `7` in plan line 226 are named; `1.3d`, `0c.3r`, `2.err`, `11.7` are conditional pastes I referenced by line, not by a command here).
- The 49-minute figure and the notice wording come from the lead's answers and the old open-items page, not from the two input files; the plan has no step for them (Part A).
- The line numbers cite the plan as it stood when I read it (provisional HEAD_PIN, round-5 shifts possible, plan line 3).
