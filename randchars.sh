#!/bin/bash

# Generate a few random printable characters

if [ "$1" == "" ]
then
  # Default to 30 characters
  COUNT=30
else
 # Blindly assume arg1 is an int
  COUNT=$1
fi

# Due to base64 inflation, maybe need to calculate something here
# OUTLEN=$(( 4 * $COUNT / 3 ))

# Fetch random bytes from /dev/urandom a decent source
dd if=/dev/urandom bs=1 count=${COUNT} 2>/dev/null |base64 -w 0 |sed 's/=//g'

## If you have `haveged` it can be fast for getting random bytes
haveged -n ${COUNT} -f - 2>/dev/null |base64 -w 0 |sed 's/=//g'

# randomness from Cloudflare's edge servers. API info here: https://csprng.xyz/
# Tends to have a trailing slash from the Base64 encoding
#curl -s "https://csprng.xyz/v1/api?length=$COUNT" | jq --raw-output .Data | sed 's/=$//'

echo

