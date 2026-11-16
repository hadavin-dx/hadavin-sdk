# evidence-c3b: inline paste spans, mechanical syntax check

## 1. What failed or could not run
- bash -n / dash -n / python compile were all run. Nothing could not run.
- PowerShell spans (see TSV, lang=powershell) were NOT syntax-checked: no pwsh in this sandbox. Only placeholder grep done.
- bash -n and dash -n exit 2 on spans that contain an undefined-in-span placeholder or are prose/fragments (listed below). After replacing every <x> with PH, the count of failures is in the summary.
- Spans are all backtick spans before the '->' of '- **' bullets outside fences, plus line 409. Some are prose fragments (file names, '&', '<n>'), not pastes; no judging done.
- Heredoc/multi-line python cannot occur in single-line spans; python programs were taken only from python3 -c '...' / "..." forms.

## 2. Tool versions
```
GNU bash, version 5.2.21(1)-release (x86_64-pc-linux-gnu)
/usr/bin/dash
dash 0.5.12-6ubuntu5
Python 3.13.18
pwsh: absent
```

## 3. Commands
```
python3 -I /tmp/c3b/extract_spans.py handover/core-hardening/inputs/plan-wp6-resmoke-v5.md /tmp/c3b handover/core-hardening/paste-check
per span: bash -n /tmp/c3b/spans/<line>-<n>.sh ; dash -n (same) ; python3 -I -c 'compile(open(f).read(),"x","exec")' <line>-<n>.py ; and the same bash/dash after <x> -> PH
<prefix> replaced by the literal line-409 span
```

## 4. Summary
```
spans 158
lang shell 143
lang shell+python 8
lang powershell 7
bash -n nonzero 11
dash -n nonzero 11
python compile nonzero 0 of 8 python-checked
bash/dash nonzero after PH substitution 9
```

## 5. Spans with nonzero exit (raw TSV rows)
```
line	step	span_n	lang	bash_n	dash_n	python	ph_substituted_bash/dash	placeholders
108	R1 NO fallback kill (n8n).	1	shell	2	2		0/0	<folder>[undefined]
109	R2 clean-up kill after a STOP only.	2	shell	2	2		0/0	<pid>[undefined]
109	R2 clean-up kill after a STOP only.	3	shell	2	2		0/0	<pid>[undefined]
112	R5 evidence, and how a paste reaches WSL.	9	shell	2	2		0/0	<log>[def@62],<step>[def@62]
112	R5 evidence, and how a paste reaches WSL.	11	shell	2	2		0/0	<n>[def@15]
112	R5 evidence, and how a paste reaches WSL.	14	shell	2	2		0/0	<n>[def@15]
112	R5 evidence, and how a paste reaches WSL.	22	powershell				/	<block>[undefined],<log>[def@62]
112	R5 evidence, and how a paste reaches WSL.	24	shell	2	2		2/2	
112	R5 evidence, and how a paste reaches WSL.	26	shell	2	2		2/2	
241	P-5 WSL keep-alive	4	powershell				/	
332	9.0k	2	shell	2	2		0/0	<n>[def@15]
332	9.0k	4	powershell				/	<n>[def@15]
333	9.round	1	powershell				/	
344	11.0k	2	shell	2	2		0/0	<n>[def@15]
419	13.5k	2	shell	2	2		0/0	<n>[def@15]
419	13.5k	3	powershell				/	<n>[def@15]
423	13.9	4	powershell				/	<prefix>[def@409]
423	13.9	5	powershell				/	
```

## 6. Placeholders (definition line = first plan line heuristically matched; <prefix> = 409)
```
108	R1 NO fallback kill (n8n).	<folder>[undefined]
109	R2 clean-up kill after a STOP only.	<folder>[undefined],<pid>[undefined]
109	R2 clean-up kill after a STOP only.	<pid>[undefined]
109	R2 clean-up kill after a STOP only.	<pid>[undefined]
112	R5 evidence, and how a paste reaches WSL.	<step>[def@62]
112	R5 evidence, and how a paste reaches WSL.	<log>[def@62],<step>[def@62]
112	R5 evidence, and how a paste reaches WSL.	<n>[def@15]
112	R5 evidence, and how a paste reaches WSL.	<log>[def@62]
112	R5 evidence, and how a paste reaches WSL.	<n>[def@15]
112	R5 evidence, and how a paste reaches WSL.	<block>[undefined],<log>[def@62]
229	P-3a (write glue and pastes; Write tool only, no WSL, no log):	<step>[def@62]
332	9.0k	<n>[def@15]
332	9.0k	<n>[def@15]
344	11.0k	<n>[def@15]
411	13.1	<prefix>[def@409]
412	13.3	<prefix>[def@409]
419	13.5k	<n>[def@15]
419	13.5k	<n>[def@15]
422	13.8	<prefix>[def@409]
423	13.9	<prefix>[def@409]
```

Full table: paste-check/spans-index.tsv; script: paste-check/extract_spans.py
