#!/bin/bash



#PARAM $1 is ref targets file 
#PARAM $2 is var targets file 
#PARAM $3 is job_id

#common targets extraction
LC_ALL=C sort -T ./ $1 > $1.sort.txt
LC_ALL=C sort -T ./ $2 > $2.sort.txt
LC_ALL=C comm -12 $1.sort.txt $2.sort.txt > $3.common_targets.txt
#LC_ALL=C fgrep -f $1 $2 > common_targets.txt

#semi common targets extraction
LC_ALL=C awk '{print $4"\t"$5}' $1 > ref.chr_pos.txt 
LC_ALL=C sort -T ./ -u ref.chr_pos.txt > ref.chr_pos.sort.txt 
LC_ALL=C fgrep -f ref.chr_pos.sort.txt  $2 > $3.semi_common_targets.txt
LC_ALL=C awk '{print $4"\t"$5}' $3.semi_common_targets.txt > semi_common.chr_pos.txt
LC_ALL=C sort -T ./ -u semi_common.chr_pos.txt > semi_common.chr_pos.sort.txt
LC_ALL=C fgrep -f semi_common.chr_pos.sort.txt  $1 >> $3.semi_common_targets.txt
LC_ALL=C sort -T ./ -u $3.semi_common_targets.txt > semi_common_targets.sort.txt

#unique variant targets extraction
#LC_ALL=C sort $2 > $2.sort.txt
LC_ALL=C comm -13 semi_common_targets.sort.txt $2.sort.txt > $3.unique_targets.txt

rm ref.chr_pos.txt ref.chr_pos.sort.txt semi_common_targets.sort.txt $2.sort.txt semi_common.chr_pos.txt semi_common.chr_pos.sort.txt $1.sort.txt
