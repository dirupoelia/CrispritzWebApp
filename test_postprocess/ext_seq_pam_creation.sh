# $1 is genome directory
# $2 is bedfile.bed
mkdir -p tmp_seq
cd tmp_seq
for chr in $1/*.fa; do
    chr_name=$(basename $chr)
    bedtools getfasta -fi $chr -bed $2 -fo $chr_name'_seq.txt' 2>/dev/null
done
find . -type f -empty -delete

for extr in ./*_seq.txt; do
    sed -i '1~2d' $extr
done

cd ../