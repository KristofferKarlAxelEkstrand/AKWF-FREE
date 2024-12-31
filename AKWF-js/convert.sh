#!/bin/bash
# Run this inside the AKWF-c folder to convert waveform data from C constants
# into a JavaScript object with normalized floating point values (-1 to 1)

# Function to process a single file and normalize values
process_file() {
    local file="$1"
    grep -A 300 "AKWF_[0-9a-z_]* \[\] = {" "$file" | \
        sed -n '/\[\] = {/,/};/p' | \
        sed 's/^const.*\[\] = {//; s/};$//' | \
        tr -d ',' | \
        tr '\n' ' ' | \
        sed 's/^ *//;s/ *$//' | \
        tr -s ' ' | \
        awk '{
            for (i=1; i<=NF; i++) {
                # Convert from unsigned (0-65535) to signed (-1 to 1) range
                printf "%.6f", ($i - 32768)/32768
                if (i < NF) printf ","
            }
        }'
}

output_file="waveforms.js"

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
    dir_name=$(basename "$dir")
    echo "Processing $dir_name..." >&2
    
    # Start the directory entry
    echo "  \"$dir_name\": {" >> "$output_file"
    
    # Process all .h files in this directory
    first_file=true
    for file in "$dir"/*.h; do
        if [ -f "$file" ]; then
            data=$(process_file "$file")
            
            if [ ! -z "$data" ]; then
                # Get filename without path and .h extension
                filename=$(basename "$file" .h)
                
                # Add comma for all but first entry
                if [ "$first_file" = true ]; then
                    first_file=false
                else
                    echo "," >> "$output_file"
                fi
                
                # Write key-value pair for this waveform (without trailing comma)
                echo -n "    \"$filename\": [$data]" >> "$output_file"
            fi
        fi
    done
    
    # Close the directory object
    echo "" >> "$output_file"
    echo "  }," >> "$output_file"
    
    ((dir_count++))
done

# Close the main object
echo "};" >> "$output_file"

# Add export statement
echo "export default waveforms;" >> "$output_file"
