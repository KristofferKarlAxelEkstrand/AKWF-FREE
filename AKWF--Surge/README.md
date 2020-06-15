# AKWF for Surge

The [free and open source synth Surge](https://surge-synthesizer.github.io/) can load single cycle waveforms directly. The Surge team also provides a python tool (wt-tool.py) for creating Wavetables using single cycle waveforms. You can download those tools or read about how to use them here:  
---> [Surge Wavetable Wiki](https://github.com/surge-synthesizer/surge-synthesizer.github.io/wiki/Creating-Wavetables-for-Surge)<---

Adventure Kid waveforms are traditionally 600 samples long but Surge requires Wavetables to be power-of-2 cycle lengths (.... 64, 128, 256, 512, etc).  
This folder contains versions of the AKWF library converted to 64 (kinda silly), 512(reasonable), and 1024(higher quality) samples.
Also included is a set of Wavetables in WT format made from each folder inside of AKWF-512.



## EXTRA INFO
The following .sh script was used to modify the entire Library in one go using SoX. If you'd like to apply some processing to the entire AKWF library yourself you could modify this script and run it from the first level of the AKWF library folder:


### EXAMPLE: How to modify whole library using Sox
````sh
for d in ./*/;
    do cd "$d";
        echo DIRECTORY "$d";
        mkdir "$d";

#1024 version UPSCALE
        mkdir ~/Desktop/AKWF-1024
        for file in $(find *.wav);
            do sox "$file" ./"$d"/"$file" speed 0.5859 gain -6.4;
            cp -r "$d" ~/Desktop/AKWF-1024/"$d";
        done;        

#512 version DOWNSCALE      
#        mkdir ~/Desktop/AKWF-512   
#        for file in $(find *.wav);
#            do sox "$file" "$d"/"$file" speed 1.1718 gain -6.4;
#            cp -r "$d" ~/Desktop/AKWF-512/"$d";
#        done;

#64 version SUPER DOWNSCALE
#Kinda silly TBH    

#        mkdir ~/Desktop/AKWF-64
#       for file in $(find *.wav);
#            do sox "$file" ./"$d"/"$file" speed 9.4 gain -6.4;
#            cp -r "$d" ~/Desktop/AKWF-64/"$d";
#        done;      


    cd ..;

done;
````
