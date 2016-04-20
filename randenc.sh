#!/bin/bash

# gpg -z 0 --no-use-agent --symmetric --passphrase `dd if=/dev/random bs=4 count=8 2>/dev/null | sha256sum | head -c 64` -
PASS= echo -n `randchars.sh 30`
gpg -z 0 --no-use-agent --symmetric --passphrase ${PASS} -
