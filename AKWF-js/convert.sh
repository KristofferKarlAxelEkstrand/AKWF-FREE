#!/bin/bash
# Run this inside the AKWF-c folder to convert waveform data from C constants
# into a JavaScript object

# Function to process a single file
process_file() {
    local file="$1"
    grep -A 300 "AKWF_[0-9a-z_]* \[\] = {" "$file" | \
        sed -n '/\[\] = {/,/};/p' | \
        sed 's/^const.*\[\] = {//; s/};$//' | \
        tr -d ',' | \
        tr '\n' ' ' | \
        sed 's/^ *//;s/ *$//' | \
        tr -s ' ' | \
        sed 's/ /,/g'
}

output_file="waveforms.js"
#max_groups=7

# Start the JavaScript object structure
echo "// Adventure Kid Waveforms (AKWF) converted into a JavaScript object.
//
// Adventure Kid Waveforms(AKWF) Open waveforms library
// https://www.adventurekid.se/akrt/waveforms/adventure-kid-waveforms/
//
// This code is in the public domain, CC0 1.0 Universal (CC0 1.0)
// https://creativecommons.org/publicdomain/zero/1.0/
//
//  Converted by Carl Tashian, https://github.com/tashian

const waveforms = {" > "$output_file"

# Find and process AKWF_* directories
dir_count=0
for dir in $(find . -maxdepth 1 -type d -name "AKWF_*" | sort -V); do
    # Skip if we've already processed max_groups
    #if [ $dir_count -ge $max_groups ]; then
    #    break
    #fi
    
    dir_name=$(basename "$dir")
    echo "Processing $dir_name..." >&2
    
    # Start the directory entry
    echo "  \"$dir_name\": {" >> "$output_file"
    
    # Process all .h files in this directory
    for file in "$dir"/*.h; do
        if [ -f "$file" ]; then
            data=$(process_file "$file")
            
            if [ ! -z "$data" ]; then
                # Get filename without path and .h extension
                filename=$(basename "$file" .h)
                
                # Write key-value pair for this waveform
                echo "    \"$filename\": [$data]," >> "$output_file"
            fi
        fi
    done
    
    # Close the directory object
    echo "  }," >> "$output_file"
    
    ((dir_count++))
done

# Close the main object
echo "};" >> "$output_file"

# Add export statement
echo "export default waveforms;" >> "$output_file"

