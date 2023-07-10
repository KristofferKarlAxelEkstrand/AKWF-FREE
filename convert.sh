#!/bin/bash
Help()
{
   # Display Help
   echo "
Convert a sound file to a C/C++ header file.
Should support any filetype supported by sox
produces unsigned 16-bit integer arrays
requires sox, hexdump
usage: 
$0 <filename>
"
   exit
}

if [[ $1 == "" ]]
then
   Help
fi

while getopts ":h" option; do
   case $option in
      h) # display Help
         Help
         exit;;
      \?) # invalid case
	 echo "Invalid option; -h for help"
	 exit;;
   esac
done

file="${1%.*}"

echo '/* Adventure Kid Waveforms (AKWF) converted for use with Teensy Audio Library 
*  
*  Adventure Kid Waveforms(AKWF) Open waveforms library
*  https://www.adventurekid.se/akrt/waveforms/adventure-kid-waveforms/
*  
*  This code is in the public domain, CC0 1.0 Universal (CC0 1.0)
*  https://creativecommons.org/publicdomain/zero/1.0/
*
*  Converted by Brad Roy, https://github.com/prosper00
*/
' > "$file.h"

echo -e "/* $file 256 samples" >> "$file.h"

sox -r 18816 "$1" "$file.dat"
tail -n+3 "$file.dat" > "$file"
gnuplot -p -e "set terminal dumb 120 20 ; unset xtics; unset ytics; plot \"$file\" notitle with lines;" >> "$file.h"
gnuplot -p -e "set term png size 1920,960; set output \"$file.png\"; plot \"$file\" with lines;"
echo -e "*/\n\n" >> "$file.h"
rm "$file.dat"
rm "$file"
sed -i 's/\o14//' "$file.h" # remove the ^L character that gnuplot is inserting


#ffmpeg -i in.flac -ac 1 -filter:a aresample=8000 -map 0:a -c:a pcm_s16le -f data - | \
#  gnuplot -p -e "set terminal png size 640,360; set output 'out.png'; plot '<cat' binary filetype=bin format='%int16' endian=little array=1:0 with lines;"

echo "const uint16_t "$file" [] = {" >> "$file.h"

#for 8-bit unsigned, add -b 8 to the sox command
sox $1 -e unsigned -r 18816 $file.raw
# 18816 = 256/600*44100 - decreases sample count from 600 to 256
# sox -G attempts to avoid clipping. Try with/without this

#for decimal
hexdump -v -e '16/2 "%5u, " "\n" ' "$file.raw" >> "$file.h"

#for hex
#hexdump -v -e '16/2 "0x%04x, " "\n" ' $file.raw >> $file.h

# for 8-bit, use '16/1,,,'

echo '};' >> "$file.h"

rm "$file.raw"

#ffmpeg -i in.flac -ac 1 -filter:a aresample=8000 -map 0:a -c:a pcm_s16le -f data - | \
#  gnuplot -p -e "set terminal png size 640,360; set output 'out.png'; plot '<cat' binary filetype=bin format='%int16' endian=little array=1:0 with lines;"


