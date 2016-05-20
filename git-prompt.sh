#!/bin/bash

# Created by Don Rude don.rude@ccri.com originally Fall 2013, copied to devenv Jan 2015

# This bash script polls git for some status variables
# Then outputs a nicely colored and formatted string
# Output will end with a carriage return!
# Basically just add a call to this script inside your bash PS1 variable
#   e.g. PS1='$(~/bin/git-prompt.sh)[\w]$ '
#             Note these must be single quotes not double quotes!
#
# Try adding these two lines to your ~/.bashrc to get both "anyErr" and git-prompt
#    function anyErr { x=$?; [ $x -ne 0 ] && echo -n "$x |"; }
#    PS1='$(anyErr)\t $(~/bin/git-prompt.sh) [\w]$ '
#        Note these must be single quotes not double quotes!



# Get the branch name but remove the "refs/heads/" string
branch_hash=`git rev-parse --short HEAD 2>/dev/null`
if [[ $? != 0 ]]; then
   exit 128
fi
BRANCH=`git symbolic-ref HEAD 2>/dev/null | cut -c 12-`

changed_files=`git diff --name-status 2>/dev/null`
if [[ $? != 0 ]]; then
   exit 127
fi
nb_chg=`git diff --name-status | grep -c ^M` # modified
nb_chU=`git diff --name-status | grep -c ^U` # unmerged
nb_changed=$(($nb_chg - $nb_chU)) # number changed
staged_files=`git diff --staged --name-status | wc -l` # total staged
        nb_U=`git diff --staged --name-status | grep -c ^U` # unmerged
nb_staged=$(($staged_files - $nb_U)) # number staged
nb_untracked=`git ls-files --others --exclude-standard | wc -l` # number untracked

#echo Staged files: $nb_staged
#echo Conflicts: $nb_U
#echo Changed files: $nb_changed
#echo Untracked: $nb_untracked

unclean=$(($nb_changed + $nb_staged + $nb_U + $nb_untracked))
#echo unClean $unclean


if [[ "$BRANCH" == "" ]]; then #no branch name
    BRANCH=":${branch_hash}"
    BR_noname=1
else
    remote_name=`git config branch.${BRANCH}.remote`

    if [[ "$remote_name" != "" ]]; then
        merge_name=`git config branch.${BRANCH}.merge`
    else
        remote_name="."
        merge_name="refs/heads/${BRANCH}"
    fi

#    echo Remote-name $remote_name
#    echo Merge-name: $merge_name

    if [[ "$remote_name" == "." ]]; then # no remote name
        remote_ref=$merge_name
    else
        m=`echo -n $merge_name | cut -c 12-`
        remote_ref="refs/remotes/${remote_name}/${m}"
    fi
#    echo remote-ref $remote_ref
     ahead=`git rev-list --left-right ${remote_ref}...HEAD | grep -c '^>'`
    behind=`git rev-list --left-right ${remote_ref}...HEAD | grep -c '^<'`
#    echo ahead $ahead
#    echo behind $behind
fi

### Created all the status variables needed.
### Now its time to construct the prompt

# Colors
Red="\033[0;31m"
Yellow="\033[0;33m"
BGreen="\033[1;32m"
Blue="\033[0;34m"
Magenta="\033[1;95m"
ResetColor="\033[0m"

# Special characters
UP='↑' #ahead
DWN='↓' #behind
DOT="${Red}● " #staged
CHK="${BGreen}✔ "
EX="${Red}✖ " #conflicts
PLUS="${Blue}✚ " #changed
DOTS='…' #untracked

remote=""
if [[ $ahead > 0 ]]; then
    remote="${remote}${UP}${ahead}"
fi
if [[ $behind > 0 ]]; then
    remote="${remote}${DWN}${behind}"
fi

local=""
if [[ $unclean -ne 0 ]]; then
    if [[ $nb_staged > 0 ]]; then
        local="${local}${DOT}${nb_staged}${ResetColor}"
    fi
    if [[ $nb_U > 0 ]]; then
        local="${local}${EX}${nb_U}${ResetColor}"
    fi
    if [[ $nb_changed > 0 ]]; then
        local="${local}${PLUS}${nb_changed}${ResetColor}"
    fi
    if [[ $nb_untracked > 0 ]]; then
        local="${local}${DOTS}${nb_untracked}"
    fi
else
    local="${local}${CHK}${ResetColor}"
fi

# Now its time to output the stuff
echo -e ${Magenta}${BRANCH}${ResetColor}${remote}\|$local

