# bash_stuff
My collection of bash scripts and tricks

* parallel_jobs.sh -- Run a bunch of things, possibly a sequence of commands, but allow some number to run in parallel.
* randchars.sh -- Generate X random (printable base64) characters.
* randenc.sh -- Use GPG to turn a stream of data into a stream of noise.
* README.md -- Self references AaAAAaaaAAA!
* shellMost.sh -- Check up on your most common bash activity.
* blame -- Runs top for a couple seconds and tells you the who is using the most CPU
* git-prompt.sh -- Can be used in your bash prompt for git status.
  * git-prompt-chars.htm -- Helper HTML to show / create the unicode characters
* my.bashrc -- My favorite / common Bash configurations
* curltime -- Use curl to report fetch timing [thanks StackOverflow](https://stackoverflow.com/questions/18215389/how-do-i-measure-request-and-response-times-at-once-using-curl)
* sb.sh -- Run a background job without the bash job noise [thanks StackOverflow](https://stackoverflow.com/questions/7686989/running-bash-commands-in-the-background-without-printing-job-and-process-ids)
* roll -- Roll dice, e.g. `roll 1d6 2d10`
* jq-keys -- Use `jq` to print (full path) keys from a json file. Call with any arg to also print the values. [Thanks to StackExchange.](https://unix.stackexchange.com/questions/561460/how-to-print-path-and-key-values-of-json-file/561489#561489)
* mk-dummy.sh -- Simplistic script to create dummy ethernet devices
* docker-descendants.py -- Not BASH!? Found [this gist](https://gist.github.com/altaurog/21ea7afe578a523e3dfe8d8a746f1e7d
) for Docker descendents
* mybackup.sh -- A minimal, manual, backup script.
* gen-new-ssl.sh -- Generate self signed SSL root and certs.
* Best_Keyboard_Shortcuts_for_Bash.pdf -- All the basic "EMACS" keyboard shortcuts in bash. [From howtogeek.com](https://www.howtogeek.com/howto/ubuntu/keyboard-shortcuts-for-bash-command-shell-for-ubuntu-debian-suse-redhat-linux-etc/)
* compose-service-list -- Greps to show top levels of a docker-compose.yml file (service names).
* argus-pcap-summary.sh -- Uses [Argus tooling](https://github.com/openargus?tab=repositories) to generate some summary info about a PCAP file.
* crontab-header.txt -- Useful text for self-documenting your crontab(s)
* find-dupe-file-names.sh -- Find files in the current path with the same name. [Found on StackExchange](https://unix.stackexchange.com/questions/468440/find-all-files-with-the-same-name)
* password-breach-checker -- Check breached password database by has prefixes. [Found on CloudFlare blog](https://blog.cloudflare.com/validating-leaked-passwords-with-k-anonymity/)
* simple-https-server.py -- Python (gasp!) 3.10 compatible HTTP server with SSL (self signed random key from OpenSSL). Serves up a folder of files.
* payload-dumper.py -- Python script using `scapy` library to dump PCAP payload bytes to a file.
* systemd-bash-service.sh -- Template/wrapper for making a bash script (e.g. data scraper) into a SystemD service.

# The Pure Bash Bible
https://github.com/dylanaraps/pure-bash-bible

* documents commonly-known and lesser-known methods of doing various tasks using only built-in bash features. Using the snippets from this bible can help remove unneeded dependencies from scripts and in most cases make them faster.
