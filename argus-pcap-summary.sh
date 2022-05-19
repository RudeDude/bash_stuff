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

racount -M proto addr -r $A
echo

echo "UDP sources with flow count"
ra -n -r $A -c , -s saddr,sport -- udp | sort | uniq -c |sort -g | tail -n 10
echo
echo "UDP destinations with flow count"
ra -n -r $A -c , -s daddr,dport -- udp | sort | uniq -c |sort -g | tail -n 10
echo

echo "TCP sources with flow count"
ra -n -r $A -c , -s saddr,sport -- tcp | sort | uniq -c |sort -g | tail -n 10
echo
echo "TCP destinations with flow count"
ra -n -r $A -c , -s daddr,dport -- tcp | sort | uniq -c |sort -g | tail -n 10
echo



