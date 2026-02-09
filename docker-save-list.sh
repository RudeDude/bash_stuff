#! /usr/bin/env bash
set -e

#startDir="$PWD"
#scriptDir="$(dirname "$(readlink -f "$0")")"
#composeDir="$(readlink -f "${scriptDir}/..")"
#cd $composeDir

mkdir -p images && cd images
echo "Trying to load image URLs from STDIN."
echo "Saving to ./images folder..."
while IFS= read -r X; do
  #echo "URL: $X"
  
  # Generate a short name without the base URL
  # And replace / with _
  # And replace : with _TAG_
  # Append .tar.gz
  Y=$(echo "${X}.tar.gz" | sed -e 's#^[^/]\+/##;s#/#_#g;s#:#_TAG_#')
  echo "Output file: ${Y}"
  if [[ -f "$Y" ]] ; then
    echo "  File exists... skipping Docker save."
  else
    echo -n "  Compressed: "
    docker save "$X" | gzip -v > "${Y}"
  fi
done

echo ""
ls -lh
#echo -n "Total size: "
#du -sh .

