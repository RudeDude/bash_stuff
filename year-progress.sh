#!/bin/bash

# Written by Don J. Rude on 2025-12-30
if [[ "$1" == "-h" || "$1" == "--help" || "$1" == "-help" ]]; then
  echo "Usage: $0 [-d]"
  echo "Prints out the year's progress as a percentage with ridiculous precision."
  echo "The year runs from midnight January 1 to the next midnight, in your local time zone."
  echo -e "  -d \t debug mode shows the values used in the calculation."
fi

# Function to display a dynamically sized progress bar
# Usage: progress_bar <current_step> <total_steps> [message]
progress_bar() {
    local current=$1
    local total=$2
    local message="${3:-Progress}" # Default message if none provided

    # Get terminal width dynamically
    # Use 'tput cols' to be compatible with sourced scripts and terminal resizing
    local terminal_width=$(tput cols)

    # Reserve space for brackets, percentage, spaces, and the optional message
#    local reserved_space=14
    local reserved_space=9
    local bar_width=$((terminal_width - reserved_space - ${#message}))

    # Calculate percentage and filled slots
#    local percentage=$(( (current * 100) / total ))
    local filled_slots=$(( (current * bar_width) / total ))
    local empty_slots=$((bar_width - filled_slots))

    # Create the filled and empty portions of the bar
    # Using printf -v to efficiently create strings of characters
    printf -v filled "%*s" "$filled_slots" ""
    filled=${filled// /#}

    printf -v empty "%*s" "$empty_slots" ""
    empty=${empty// /-};

    # Print the progress bar, message, and percentage
    # \r moves the cursor to the beginning of the line
    # \e[K clears from the cursor to the end of the line
#    echo -ne "\r$message: [${filled}${empty}] ${percentage}%"
    echo -ne "\r$message: [${filled}${empty}]\n"
}

# True when the name is an IANA zone or a POSIX TZ string (for example EST5EDT).
# An unrecognized TZ is not "UTC": libc still computes UTC offsets for it.
timezone_valid() {
    local name="${1#:}"
    [[ -n $name ]] || return 1
    if [[ -e /usr/share/zoneinfo/$name ]]; then
        return 0
    fi
    # POSIX TZ strings have no zoneinfo file and include a numeric offset.
    [[ $1 == *[0-9]* ]]
}

# System zone, ignoring any inherited TZ. Same sources a login shell uses,
# so cron and other environments that leave TZ unset stay on local time.
system_timezone() {
    local zone=""
    if [[ -r /etc/timezone ]]; then
        zone=$(tr -d '[:space:]' < /etc/timezone)
    elif command -v timedatectl >/dev/null 2>&1; then
        zone=$(timedatectl show -p Timezone --value 2>/dev/null || true)
    else
        local zonefile=""
        zonefile=$(readlink -f /etc/localtime 2>/dev/null || true)
        case $zonefile in
            */zoneinfo/*) zone=${zonefile#*/zoneinfo/} ;;
        esac
    fi
    zone=${zone#posix/}
    zone=${zone#right/}
    printf '%s\n' "$zone"
}

# Explicit TZ wins when it names a real zone. Otherwise detect the system zone.
# Drop an invalid TZ first, because date would silently treat it as UTC.
if [[ -n ${TZ:-} ]] && timezone_valid "$TZ"; then
    detected_tz=$TZ
else
    [[ -n ${TZ:-} ]] && unset TZ
    detected_tz=$(system_timezone)
    timezone_valid "$detected_tz" || detected_tz=""
fi
if [[ -n $detected_tz ]]; then
    export TZ="$detected_tz"
fi

year=$(date "+%Y")
# Civil midnight in the local zone. Zoneinfo applies that date's UTC offset,
# so a January EST boundary and a July EDT "now" stay on the same local calendar.
start=$(date -d "${year}-01-01 00:00:00" "+%s.%N")
end=$(date -d "$((year + 1))-01-01 00:00:00" "+%s.%N")
now=$(date "+%s.%N")
calc="($now - $start)/($end - $start)"
p=$(echo "$calc" | bc -l) # float range 0-1
perc=$(echo "100 * $p" | bc -l) # percentage
prog=$(echo "10000 * $p" | bc -l | sed "s#\..*###") # integer for progress bar


if [[ "$1" == "-v" || "$1" == "-d" ]]; then
  echo "DEBUG: tz ${TZ:-libc-local} now-offset $(date +%z) year $year start $start end $end now $now calc $calc p $p perc $perc prog $prog"
fi

progress_bar "$prog" "10000" "$year"
echo ${perc:0:21}" %"
