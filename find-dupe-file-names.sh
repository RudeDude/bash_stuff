#!/bin/bash
set -e

echo "You may want to try and install the 'fdupes' program to find and remove more reliably."
# Found at https://unix.stackexchange.com/questions/468440/find-all-files-with-the-same-name
find -type f -print0 | awk -F/ 'BEGIN { RS="\0" } { n=$NF } k[n]==1 { print p[n]; } k[n] { print $0 } { p[n]=$0; k[n]++ }'

