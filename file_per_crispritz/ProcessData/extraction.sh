#!/bin/bash

#PARAM $1 is ref targets file 
#PARAM $2 is var targets file 
#PARAM $3 is output filename

#common targets extraction
LC_ALL=C sort $1 > $1.sort.txt
LC_ALL=C sort $2 > $2.sort.txt
LC_ALL=C comm -12 $1.sort.txt $2.sort.txt > $3.common_targets.txt
#LC_ALL=C fgrep -f $1 $2 > $3.common_targets.txt

#semi common targets extraction
LC_ALL=C awk '{print $4"\t"$5}' $1 > ref.chr_pos.txt 
LC_ALL=C sort -u ref.chr_pos.txt > ref.chr_pos.sort.txt     #Get all chr_pos from ref

LC_ALL=C awk '{print $4"\t"$5}' $3.common_targets.txt > ref.comm.chr_pos.txt 
LC_ALL=C sort -u ref.comm.chr_pos.txt > ref.comm.chr_pos.sort.txt 
LC_ALL=C comm -23 ref.chr_pos.sort.txt ref.comm.chr_pos.sort.txt > tmp && mv tmp ref.chr_pos.sort.txt   #Get all chr_pos from common file, get chr_pos that are not in comm_chr_pos

LC_ALL=C fgrep -f ref.chr_pos.sort.txt  $2 > semi_common_targets.txt
#LC_ALL=C awk '{print $4"\t"$5}' semi_common_targets.txt > semi_common.chr_pos.txt
#LC_ALL=C sort -u semi_common.chr_pos.txt > semi_common.chr_pos.sort.txt
#LC_ALL=C fgrep -f semi_common.chr_pos.sort.txt  $1 >> semi_common_targets.txt
LC_ALL=C fgrep -f ref.chr_pos.sort.txt  $1 >> semi_common_targets.txt
LC_ALL=C sort -u semi_common_targets.txt > semi_common_targets.sort.txt
mv semi_common_targets.txt $3.semi_common_targets.txt

#unique variant targets extraction
#LC_ALL=C sort $2 > $2.sort.txt
LC_ALL=C comm -13 semi_common_targets.sort.txt $2.sort.txt > $3.unique_targets.txt

#rm ref.chr_pos.txt ref.chr_pos.sort.txt semi_common_targets.sort.txt $2.sort.txt semi_common.chr_pos.txt semi_common.chr_pos.sort.txt $1.sort.txt
rm ref.chr_pos.txt ref.chr_pos.sort.txt semi_common_targets.sort.txt $2.sort.txt $1.sort.txt