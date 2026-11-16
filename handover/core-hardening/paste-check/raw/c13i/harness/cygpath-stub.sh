#!/bin/bash
# stub (not Git Bash): /z/x/y -> Z:\x\y (-w) or Z:/x/y (-m)
m=$1; p=$2; d=${p:1:1}; r=${p:2}; D=$(printf '%s' "$d" | tr a-z A-Z)
case $m in -w) printf '%s:%s\n' "$D" "$(printf '%s' "$r" | tr / '\\')";; -m) printf '%s:%s\n' "$D" "$r";; esac
