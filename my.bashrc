
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

# Thanks to Ubuntu there are now dozens of SNAP mount points that show up in "df" output
alias dfh="df -h | egrep -v 'snap|tmpfs'"
# An agressive set of whitespace killing options for "git diff"
alias gitdiff='git -c core.whitespace=-trailing-space,-indent-with-non-tab,-tab-in-indent diff -U0 --word-diff-regex='[^[:space:]]' -bw'

export TZ=`cat /etc/timezone`
#alias roll='rolldice -s'
alias dps='docker ps --format "table {{.Image}}\t{{.Command}}\t{{.RunningFor}}\t{{.Status}}"'

# A "nice" date format to include fractional seconds
alias mydate="date '+%Z %Y-%m-%d %H:%M:%S.%N'"

alias docker-compose="docker compose"
alias python=python3

## Set some additoinal java home params for Maven or whatever.
#export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export JAVA_HOME_8=/usr/lib/jvm/java-8-openjdk-amd64
export JAVA_HOME_17=/usr/lib/jvm/java-17-openjdk-amd64

[ -f ~/.fzf.bash ] && source ~/.fzf.bash
export PATH=$HOME/bin:$PATH
export EDITOR=nano
