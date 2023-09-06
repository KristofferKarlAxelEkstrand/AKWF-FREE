# Merge Surge files into single wavs

for d in ../AKWF--Surge/AKWF-1024/*; do
  sample_name=$(basename "$d")
  echo $sample_name
  sox --combine concatenate $d/**.wav AKWF-1024/"$sample_name.wav"
done
