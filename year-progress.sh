#!/bin/bash

# Written by Don J. Rude on 2025-12-30
if [[ "$1" == "-h" || "$1" == "--help" || "$1" == "-help" ]]; then
  echo "Usage: $0 [-d]"
  echo "Prints out the year's progress as a percentage with ridiculous precision."
  echo -e "  -d \t debug mode shows the values used in the calculation."
fi

start=`date -d "Jan 1 this year" "+%s.%N"`
end=`date -d "Jan 1 next year" "+%s.%N"`
now=$(date "+%s.%N")
calc="100 * ($now - $start)/($end - $start)"

if [ "$1" == "-d" ]; then
  echo "$calc"
fi
echo "$calc" |bc -l

