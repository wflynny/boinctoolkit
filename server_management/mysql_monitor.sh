#!/bin/bash

# To install:
#    crontab -e
#
# */1 * * * * echo "`date`  `~/projects/projectname/bin/mysql_monitor.sh`" >> ~/projects/projecname/log/mysql_monitor.log

cfgfile=~/projects/projectname/bin/cfg.cnf
mysql --defaults-extra-file=$cfgfile --execute "SHOW STATUS LIKE '%onn%';" | grep "Threads_connected"
