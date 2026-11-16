#!/usr/bin/env bash
# throwaway cluster, unix socket only, own folder. usage: start_cluster.sh start|stop
PGB=/usr/lib/postgresql/16/bin; D=/var/lib/postgresql/hadavin_v15_indep
if [ "$1" = start ]; then
runuser -u postgres -- bash -c "rm -rf $D && $PGB/initdb -D $D -A trust -E UTF8 >/dev/null 2>&1 && $PGB/pg_ctl -D $D -o \"-c listen_addresses='' -c unix_socket_directories=$D -c fsync=off\" -l $D/log -w start >/dev/null" && echo started
runuser -u postgres -- psql -X -h $D -d postgres -At -c "select version()"
for r in mig_ind rt_ind audrd_ind nobody_ind; do runuser -u postgres -- psql -X -h $D -d postgres -qc "CREATE ROLE $r LOGIN"; done
else
runuser -u postgres -- $PGB/pg_ctl -D $D -m fast -w stop >/dev/null 2>&1; runuser -u postgres -- rm -rf $D; echo stopped
fi
