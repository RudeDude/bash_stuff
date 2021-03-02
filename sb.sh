#!/bin/bash

silent_background() {
    { 2>&3 "$@"& } 3>&2 2>/dev/null
#    disown &>/dev/null  # Prevent whine if job has already completed
}
silent_background date
silent_background sleep 2
wait

