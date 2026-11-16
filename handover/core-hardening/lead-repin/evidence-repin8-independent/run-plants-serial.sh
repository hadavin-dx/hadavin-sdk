#!/bin/sh
E=/home/user/hadavin-sdk/handover/core-hardening/lead-repin/evidence-repin8-independent
IDS="m23 m24 n01 n02 n03 n04 n05 n06 n07 n08 n09 n10 n11 n12 n13 n14 n15 n16 n17 n18"
for s in dash bash; do
  echo "== $s start $(date -u +%T) load $(cut -d' ' -f1-3 /proc/loadavg)" >> $E/04-plants-$s-part2.txt
  sh /home/user/hadavin-sdk/handover/core-hardening/heavy-slot.sh python3 -I $E/mutate8.py /tmp/hd8i/v8.sh $E/pl-$s $s $IDS >> $E/04-plants-$s-part2.txt 2>&1
  echo "== $s end $(date -u +%T) load $(cut -d' ' -f1-3 /proc/loadavg)" >> $E/04-plants-$s-part2.txt
done
