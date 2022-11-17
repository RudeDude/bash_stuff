#!/bin/bash
set -e

## Where to put the compressed tarball
DEST=/net/nas0/mnt/tank/backups/drude
## File to contain excluded file wildcards
EXCL=".ignore"
## Folders to backup
DIRS="Desktop/ Documents/ .ssh/ Pictures/"

# Ensure we are in the homedir
cd ~

for D in $DIRS
do
  T=`find $D -type f -name $EXCL`
  for X in $T ; do
    DN=`dirname $X`
    echo $DN folder will ignore...
    du -sh $DN
  done
done

echo
echo initial tar file will be at most this big \(minus ignores\)...
du -shc $DIRS
read -n 1 -r -p "Continue? "
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
  exit 1
fi

# Ensure destination exists and is writeable
touch ${DEST}/last-backup-now

echo Main folders...
tar -c --exclude-ignore-recursive="$EXCL" -f /tmp/backup.tar $DIRS
chmod go-rw /tmp/backup.tar
du -h /tmp/backup.tar
echo

echo Find and add top level files...
find . -maxdepth 1 -type f |xargs -L 1 tar rvf /tmp/backup.tar
du -h /tmp/backup.tar
echo

echo Compressing...
gzip -v /tmp/backup.tar
chmod go-rw /tmp/backup.tar.gz
echo

mv /tmp/backup.tar.gz ./backup-`date -I`.tar.gz
du -hc backup*.gz
exit 0
# scp backup-*.tar.gz ${DEST}
# rm -f backup-*.tar.gz
echo moving to destination...
mv backup-*.tar.gz ${DEST}/

# Update "now" timestamp
touch ${DEST}/last-backup-now

