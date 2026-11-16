#!/bin/sh
# builds made-up probe lines for review-repin5-security M1-M3 (every value built from parts); prints lines, then a tag file
v() { printf 'kq%02dzv%02dwm%02dxd' "$1" "$1" "$1"; }
n=0
emit() { n=$((n+1)); val=$(v $n); case $1 in
 m1a) printf 'cache redis://:%s@localhost:6379/0 ok\n' "$val";;
 m1b) printf 'broker amqp://:%s@mq:5672\n' "$val";;
 m1c) printf 'x //:%s@host/p y\n' "$val";;
 m2a) printf 'docker login -u bob -p %s registry\n' "$val";;
 m2b) printf 'redis-cli -a %s ping\n' "$val";;
 m2c) printf 'ldapsearch -x -D cn=admin -w %s -b dc=x\n' "$val";;
 m2d) printf 'zip -P %s out.zip f.txt\n' "$val";;
 m2e) printf '7z a -p%s out.7z f\n' "$val";;
 m2f) printf 'htpasswd -b users.txt bob %s\n' "$val";;
 m2g) printf 'smbclient //h/s -U bob%%%s\n' "$val";;
 m3a) printf 'SECRET_NAME = (\n    "%s"\n)\nkept_after_m3a = 1\n' "$val";;
 m3b) printf 'API_KEY = \\\n    %s\nkept_after_m3b = 1\n' "$val";;
 m3c) printf 'TOKENS = [\n  "%s",\n  "%s"\n]\nkept_after_m3c = 1\n' "$val" "$(v 90)";;
esac; printf '%s|%s\n' "$1" "$val" >> tags.txt; }
: > tags.txt
for t in m1a m1b m1c m2a m2b m2c m2d m2e m2f m2g m3a m3b m3c; do emit $t; done
