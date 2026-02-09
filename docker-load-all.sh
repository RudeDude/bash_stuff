#! /usr/bin/env bash
set -e

## I have written and re-created this script several times. Adding it to the archives.
## Make a folder full of GZ compressed Docker iamges (tar files).
## This script assumes CWD is where all the *.gz files exist.
## 2026-02-09

#startDir="$PWD"
#scriptDir="$(dirname "$(readlink -f "$0")")"
#composeDir="$(readlink -f "${scriptDir}/..")"
#cd $composeDir
#cd images

echo -n "Trying to load images from: "
pwd
for X in *.gz *.tgz ; do
  if [[ -f "$X" ]] ; then
    echo $X
    zcat $X | docker load
  else
    echo "No such file: '$X'"
  fi
done
