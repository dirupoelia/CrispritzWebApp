# $1 is total reference file
# $2 is total enr file
# Common file: file containing only the targets that are equal on both the ref and enr genome, ex:
# REF: RNA	CTAACAGTTGCTTTTATCACNNN	tTAAC-cTTtCTTTTcatA-AAG	chrUn_KI270312v1	290	-	6	2
# ENR: RNA	CTAACAGTTGCTTTTATCACNNN	tTAAC-cTTtCTTTTcatA-AAG	chrUn_KI270312v1	290	-	6	2
# The target is selected; if:
# REF: RNA	CTAACAGTTGCTTTTATCACNNN	tTAAC-cTTtCTTTTcatA-AAG	chrUn_KI270312v1	290	-	6	2
# ENR: RNA	CTAACAGTTGCTTTTATCACNNN	tTAAC-cTTtCTTTTcatW-AAG	chrUn_KI270312v1	290	-	6	2
# The target is not selected
ref=$1
enr=$2
LC_ALL=C
while IFS= read -r line || [ -n "$line" ]; do
    fgrep "$line" $enr >> common.txt
done < $ref