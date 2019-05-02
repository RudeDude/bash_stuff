#!/bin/bash

## Looks at your bash history and tells you what you do the most

echo Top commands:
cat ~/.bash_history | cut -d " " -f 1 |sort |uniq -c |sort -grk 1 |head -20

echo

echo Top pipe destinations:
# history |sed 's/[0-9]\+ \+//' |grep '|' |cut -d "|" -f 2 |sed 's/ \+//' |cut -d " " -f 1 |sort |uniq -c |sort -grk 1 |head -20
cat ~/.bash_history  |grep '|' |cut -d "|" -f 2 |sed 's/ \+//' |cut -d " " -f 1 |sort |uniq -c |sort -grk 1 |head -20
