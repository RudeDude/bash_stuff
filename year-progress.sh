#!/bin/bash

# Written by Don J. Rude on 2025-12-30
if [[ "$1" == "-h" || "$1" == "--help" || "$1" == "-help" ]]; then
  echo "Usage: $0 [-d]"
  echo "Prints out the year's progress as a percentage with ridiculous precision."
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

year=$(date "+%Y")
start=$(date -d "Jan 1 this year" "+%s.%N")
end=$(date -d "Jan 1 next year" "+%s.%N")
now=$(date "+%s.%N")
calc="($now - $start)/($end - $start)"
p=$(echo "$calc" | bc -l) # float range 0-1
perc=$(echo "100 * $p" | bc -l) # percentage
prog=$(echo "10000 * $p" | bc -l | sed "s#\..*###") # integer for progress bar

if [ "$1" == "-d" ]; then
  echo "calc $calc"
#  echo "p $p"
#  echo "perc $perc"
#  echo "prog $prog"
fi
progress_bar "$prog" "10000" "$year"
echo "$perc %"
