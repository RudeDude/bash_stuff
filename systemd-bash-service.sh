#!/bin/bash
set -e

# Written by Don J. Rude
# Adapted from: https://unix.stackexchange.com/questions/236084/how-do-i-create-a-service-for-a-shell-script-so-i-can-start-and-stop-it-like-a-d

# Save the following as /etc/systemd/system/<script_name>.service
# and then you will be able to start/stop/enable/disable it with
# "systemctl start hit", etc.
# 
# [Unit]
# Description=Your script_name service
# After=network-online.target
# 
# [Service]
# User=<UNAME>
# ExecStart=/path/to/<script_name>.sh
# 
# [Install]
# WantedBy=multi-user.target


NAME="scraper"
MYSH="/path/to/${NAME}.sh"
PIDF="/var/run/${NAME}.pid"

if [ -f "$PIDF" ]; then
  PID=`cat $PIDF`
else
  PID=""
fi

if [ "$DEBUG" != "" ]; then
  echo DEBUG
  echo NAME $NAME
  echo MYSH $MYSH
  echo PIDF $PIDF
  echo PID  $PID
  exit 1
fi

if [ ! -f "$MYSH" ]; then
  echo "File $MYSH is missing. Abort."
  exit 1
fi

case "$1" in
start)
   ${MYSH} &
   echo $!>$PIDF
   ;;
stop)
   kill "$PID"
   rm "$PIDF"
   ;;
restart)
   $0 stop
   $0 start
   ;;
status)
   if [ -e $PIDF ]; then
      echo "${NAME}.sh is running, pid=$PID"
   else
      echo "${NAME}.sh is NOT running"
      exit 1
   fi
   ;;
*)
   echo "Usage: $0 {start|stop|status|restart}"
esac

exit 0

