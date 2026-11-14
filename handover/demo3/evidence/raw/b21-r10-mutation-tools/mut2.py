import sys
sh=open('/tmp/claude-0/good.sh',encoding='utf-8').read(); ps=open('/tmp/claude-0/good.ps1',encoding='utf-8').read()
CALL='if [[ -f "$pidfile" ]]; then read_pid_file "$pidfile"; fi'
LEN='(( ${#pid} >= 64 )) || [[ "$pid" == *[![:print:][:space:]]* ]]'
TRIM='  pid="${pid#"${pid%%[![:space:]]*}"}"; pid="${pid%"${pid##*[![:space:]]}"}" # trim the spaces and the line end\n'
BOM="  pid=\"${pid#$'\\xef\\xbb\\xbf'}\"\n"
NUL='[[ ! "$size" =~ ^[0-9]+$ ]] || (( ${#pid} != (size < 67 ? size : 67) ))'
CT='pid="${pid#"${pid%%[![:space:]]*}"}"; pid="${pid%"${pid##*[![:space:]]}"}"'
def sub(s,o,n):
    assert s.count(o)==1,(s.count(o),o); return s.replace(o,n)
m=sys.argv[1]; s=sh; f='scripts/reset.sh'
if m=='M1': s=sub(sh,LEN,'[[ "$pid" == *[![:print:][:space:]]* ]]'); s=sub(s,CALL,CALL+'; if (( ${#pid} >= 64 )); then pid=""; fi')
elif m=='M2': s=sub(sh,TRIM,''); s=sub(s,CALL,CALL+'; '+CT)
elif m=='M3': s=sub(sh,BOM,''); s=sub(s,CALL,CALL+'; pid="${pid#$\'\\xef\\xbb\\xbf\'}"')
elif m=='M4': s=sub(sh,NUL,'false')
elif m=='M5': s=sub(sh,LEN,'(( ${#pid} >= 64 ))')
elif m=='M6': s=sub(sh,'local LC_ALL=C chunk="" tries size','local chunk="" tries size')
elif m=='M7': s=sub(sh,'    elif alive "$pid"; then','    else')
elif m=='M8': s=sub(sh,'    [[ "$err" == *"not permitted"* ]] || return 1','    return 1')
elif m=='M9': s=sub(sh,'  *) echo "refused: the check program failed','  *) exit "$check_exit"; echo "refused: the check program failed')
elif m=='M10': s=sub(sh,'(( ${#pid} >= 64 ))','(( ${#pid} >= 65 ))')
elif m=='P1': f='scripts/reset.ps1'; s=sub(ps,"\\A[1-9][0-9]*\\z","^[1-9][0-9]*$")
elif m=='P2': f='scripts/reset.ps1'; s=sub(ps,"$ErrorActionPreference = 'Continue'\n","")
elif m=='P3': f='scripts/reset.ps1'; s=sub(ps,"if ($b -gt 126 -or ($b -lt 32 -and ($b -lt 9 -or $b -gt 13))) { $bad = $true }","if ($b -gt 126) { $bad = $true }")
elif m=='P4': f='scripts/reset.ps1'; s=sub(ps,"$got = $stream.Read($buffer, $count, 67 - $count)","$got = $stream.Read($buffer, 0, 67)")
elif m=='P5': f='scripts/reset.ps1'; s=sub(ps,"$ErrorActionPreference = $previousPreference\n","")
open(f,'w',encoding='utf-8',newline='').write(s)
