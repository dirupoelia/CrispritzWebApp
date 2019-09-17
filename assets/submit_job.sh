#!/bin/sh
#$1 is directory of result for submitted job id (Results/job_id)
#$2 is vcf file name
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

#echo $1 $2 $3 $4 $5 $6 $7 $8 $9 $10 $11 $12 $13 $14 $15 $16
echo 'Job\tStart\t'$(date)> $1'/'log.txt
echo $2
echo $3
echo $4
#Start add variants
echo 'Add-variants\tStart\t'$(date) >> $1'/'log.txt
if [ ${11} = 'True' ]; then
    crispritz.py add-variants 'Variants/'$2 $3 
    mkdir $4 ; 
    echo 'crispritz add-variants'
    mv variants_genome/SNPs_genome/*.fa $4
fi
echo 'Add-variants\tDone\t'$(date) >> $1'/'log.txt

#Start indexing
echo 'Index-generation\tStart\t'$(date) >> $1'/'log.txt
if [ ${12} = 'True' ]; then
    #crispritz.py index-genome nome_genoma genome_dir $4 -bMax $max
    echo 'crispritz index'
fi
echo 'Index-generation\tDone\t'$(date) >> $1'/'log.txt

#Start search index
if [ ${13} = 'True' ]; then
    echo 'crispritz search-index'
fi

#Start search
if [ ${14} = 'True' ]; then
    echo 'crispritz search'
fi

#Start annotation
if [ ${15} = 'True' ]; then
    echo 'crispritz annotate'
fi

#Start generate report
if [ ${16} = 'True' ]; then
    echo 'crispritz report'
fi

