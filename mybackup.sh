#!/bin/bash

# Ensure we are in the homedir
cd ~

echo initial tar file will be at least this big...
du -shc Desktop/ Documents/ .ssh/ Pictures/
read -n 1 -r -p "Continue? "
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
  exit 1
fi

echo Main folders...
tar cf /tmp/backup.tar Desktop/ Documents/ .ssh/ Pictures/
chmod go-rw /tmp/backup.tar
du -h /tmp/backup.tar
echo

echo Find and add top level files...
find . -maxdepth 1 -type f |xargs tar rvf /tmp/backup.tar
du -h /tmp/backup.tar
echo

echo Compressing...
gzip -v /tmp/backup.tar
chmod go-rw /tmp/backup.tar.gz
echo

mv /tmp/backup.tar.gz ./backup-`date -I`.tar.gz
du -hc backup*.gz

scp backup-*.tar.gz dr@laz.jarmansgap.com:/data1/dr/
rm -f backup-*.tar.gz
