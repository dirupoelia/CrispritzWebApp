#!/bin/sh
#$1 is directory of result for submitted job id (Results/job_id)
#$2 is vcf name  Eg hg19_1000genomeproject_vcf
#$3 is genome_ref directory     Eg Genomes/hg19_ref
#$4 is genome_enriched directory    Eg variants_genome/SNPs_genome/hg19_ref_hg19_1000genomeproject_vcf
#$5 is genome_idx directory     Eg genome_library/NGG_2_hg19_1000genpro
#$6 is pam file             Eg Results/72C1MNXDWF/pam.txt
#$7 is guides file          Eg Results/LNHM6F3REO/guides.txt (both upload file and custom inserted)
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
used_genome_dir=$3                  #if variants, use variants_genome/SNP , else use Genome/genome
if [ $2 != 'None' ]; then
    used_genome_dir=$4
fi
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
genome_idx_basename=$(basename $4)
max=$9
if [ ${10} -ge $9 ]; then
    max=${10}
fi
if [ ${12} = 'True' ]; then   
    #crispritz.py index-genome $genome_idx_basename $used_genome_dir $6 -bMax $max
    echo 'crispritz indexing'
fi
echo 'Index-generation\tDone\t'$(date) >> $1'/'log.txt

#Start search
echo 'Search\tStart\t'$(date) >> $1'/'log.txt
if [ ${13} = 'True' ]; then
    echo 'crispritz search'
    #crispritz.py search $used_genome_dir $6 $7 name_file -mm $8 -t -scores $used_genome_dir
fi
echo 'Search\tDone\t'$(date) >> $1'/'log.txt


#Start search index
echo 'Search-index\tStart\t'$(date) >> $1'/'log.txt
if [ ${14} = 'True' ]; then
    echo 'crispritz search-index'
    #crispritz.py search $5 $6 $7 name_file -index -mm $8 -bDNA $9 -bRNA ${10} -t -scores $used_genome_dir
fi
echo 'Search-index\tDone\t'$(date) >> $1'/'log.txt

#Start annotation
echo 'Annotation\tStart\t'$(date) >> $1'/'log.txt
if [ ${15} = 'True' ]; then
    echo 'crispritz annotate'
fi
echo 'Annotation\tDone\t'$(date) >> $1'/'log.txt

#Start generate report
echo 'Report\tStart\t'$(date) >> $1'/'log.txt
if [ ${16} = 'True' ]; then
    echo 'crispritz report'
fi
echo 'Report\tDone\t'$(date) >> $1'/'log.txt

echo 'Job\tDone\t'$(date)>> $1'/'log.txt

