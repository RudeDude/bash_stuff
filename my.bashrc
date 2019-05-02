
# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
HISTCONTROL=ignoreboth

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=200000
HISTFILESIZE=200000

function anyErr { x=$?; [ $x -ne 0 ] && echo -n "$x |"; }
PS1='$(anyErr)\t $(~/bin/git-prompt.sh)\n[\w]$ '

# Thanks to Ubuntu there are now dozens of SNAP mount points
alias dfh='df -h | grep -v snap'

