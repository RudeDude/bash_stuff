#!/bin/bash
set -e

sudo echo sudo test
for X in dummy0 dummy1 dummy2 dummy3
do
  echo Setup $X
  sudo ip link add $X type dummy
  sudo ip link set $X up
  sudo ip link set $X mtu 2500
done
