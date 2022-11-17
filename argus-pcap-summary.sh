#!/bin/bash
set -e # exit on errors
set -o pipefail # propagate errors in piped commands

if [[ -z $1 ]]
then
  echo "need a pcap file name as first/only argument"
  exit 1
fi

P=$1
A="${P%.*}.argus"
T="${P%.*}-summary.txt"
TOPN="20"

if [[ -s "$A" ]]
then
  echo "Found pre-existing $A Argus file"
else
  ## (re)generate Argus file
  if [[ -s "$P" ]]
  then
    echo "Generate Argus file..."
    argus -ACJmRZ -r $P -w $A
  else
    echo "Missing $P"
  fi
fi

echo "Writing to text summary file $T ..."
## Create empty test summary file
echo > $T

racount -M proto addr -r $A >> $T
echo >> $T

echo "UDP sources with flow count" >> $T
ra -n -r $A -c , -s saddr,sport -- udp | sort | uniq -c |sort -g | tail -n $TOPN >> $T
echo >> $T
echo "UDP destinations with flow count" >> $T
ra -n -r $A -c , -s daddr,dport -- udp | sort | uniq -c |sort -g | tail -n $TOPN >> $T
echo >> $T

echo "TCP sources with flow count" >> $T
ra -n -r $A -c , -s saddr,sport -- tcp | sort | uniq -c |sort -g | tail -n $TOPN >> $T
echo >> $T
echo "TCP destinations with flow count" >> $T
ra -n -r $A -c , -s daddr,dport -- tcp | sort | uniq -c |sort -g | tail -n $TOPN >> $T
echo >> $T


