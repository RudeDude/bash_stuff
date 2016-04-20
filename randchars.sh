#!/bin/bash

if [ "$1" == "" ]
then
  COUNT=30
else
  COUNT=$1
fi

# OUTLEN=$(( 4 * $COUNT / 3 ))

dd if=/dev/random bs=1 count=${COUNT} 2>/dev/null |base64 -w 0 |sed 's/=//g'
# haveged -n ${COUNT} -f - 2>/dev/null |base64 -w 0 |sed 's/=//g'

echo

