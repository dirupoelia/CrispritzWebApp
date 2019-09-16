#$1 is directory of result for submitted job id (Results/job_id)
#$2 is vcf file directory
#$3 is genome_ref directory
#$4 is genome_enriched directory
#$5 is genome_idx directory
#$6 is pam 
#$7 is guides
#$8 is mms
#$9 is dna
#$10 is rna
#$11 is enrich
#$12 is index
#$13 is search_index
#$14 is search
#$15 is annotation
#$16 is generate report

echo 'Job\tStart\t'$(date)> $1'/'log.txt
echo 'Add-variants\tStart\t'$(date) >> $1'/'log.txt

#Start add variants
#crispritz.py add-variants $2 $3 >> log.txt 2>&1

echo 'Add-variants\tDone\t'$(date) >> $1'/'log.txt

#Start indexing
echo 'Index-generation\tStart\t'$(date) >> $1'/'log.txt
max=$8
if [ $7 -ge $8 ]; then
    max=$7
fi

if [ $7 -ne '0' -o $8 -ne '0' ]; then
    #crispritz.py index-genome nome_genoma genome_dir $4 -bMax $max
fi

echo 'Index-generation\tDone\t'$(date) >> $1'/'log.txt

#Start search


