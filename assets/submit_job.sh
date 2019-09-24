#!/bin/sh
#$1 is directory of result for submitted job id (Results/job_id)
#$2 is genome_selected directory Eg Genomes/hg19_ref or Genomes/hg19_ref+1000genomeproject #NOTE + or - to decide
#$3 is genome_ref directory     Eg Genomes/hg19_ref
#$4 is genome_idx directory     Eg genome_library/NGG_2_hg19_ref+hg19_1000genomeproject
#$5 is pam file             Eg Results/72C1MNXDWF/pam.txt
#$6 is guides file          Eg Results/LNHM6F3REO/guides.txt (both upload file and custom inserted)
#$7 is mms
#$8 is dna
#$9 is rna
#$10 is search_index
#$11 is search
#$12 is annotation
#$13 is generate report
#$14 is gecko comparison
#$15 is genome_ref comparison

jobid=$(basename $1)
echo 'Job\tStart\t'$(date)> $1'/'log.txt
used_genome_dir=$2                 

#Start search index
echo 'Search-index\tStart\t'$(date) >> $1'/'log.txt
if [ ${10} = 'True' ]; then
    #echo 'crispritz search-index'
    crispritz.py search $4 $5 $6 $jobid -index -mm $7 -bDNA $8 -bRNA ${9} -t -scores $3
    mv ./$jobid.*.txt $1
    mv ./$jobid.*.xls $1

    if [ ${15} = 'True' ]; then
        mkdir $1'/ref'
        crispritz.py search $4 $5 $6 $jobid'_ref' -index -mm $7 -bDNA $8 -bRNA ${9} -t
        mv ./$jobid'_ref'.*.txt $1/ref
        mv ./$jobid'_ref'.*.xls $1/ref
    fi
fi
echo 'Search-index\tDone\t'$(date) >> $1'/'log.txt

#Start search
echo 'Search\tStart\t'$(date) >> $1'/'log.txt
if [ ${11} = 'True' ]; then
    #echo 'crispritz search'
    crispritz.py search $used_genome_dir $5 $6 $jobid -mm $7 -t -scores $3
    mv ./$jobid.*.txt $1
    mv ./$jobid.*.xls $1
    if [ ${15} = 'True' ]; then
        mkdir $1'/ref'
        crispritz.py search $3 $5 $6 $jobid'_ref' -mm $7 -t
        mv ./$jobid'_ref'.*.txt $1/ref
        mv ./$jobid'_ref'.*.xls $1/ref
    fi
fi
echo 'Search\tDone\t'$(date) >> $1'/'log.txt


#Start annotation
echo 'Annotation\tStart\t'$(date) >> $1'/'log.txt
if [ ${12} = 'True' ]; then
    #echo 'crispritz annotate'
    crispritz.py annotate-results $6 $1'/'$jobid'.targets.txt' annotations_path.txt $jobid'.annotated'
    mv ./$jobid.annotated.*.txt $1
    if [ ${15} = 'True' ]; then
        crispritz.py annotate-results $6 $1'/'$jobid'_ref.targets.txt' annotations_path.txt $jobid'_ref.annotated'
        mv ./$jobid'_ref'.annotated.*.txt $1/ref
    fi
fi
echo 'Annotation\tDone\t'$(date) >> $1'/'log.txt

#Start generate report
echo 'Report\tStart\t'$(date) >> $1'/'log.txt
if [ ${13} = 'True' ]; then
    #echo 'crispritz report'
    #-profile emx1.hg19.profile.xls -extprofile emx1.hg19.extended_profile.xls -exons emx1.hg19.annotated.ExonsCount.txt -introns emx1.hg19.annotated.IntronsCount.txt -dnase emx1.hg19.annotated.DNAseCount.txt -ctcf emx1.hg19.annotated.CTCFCount.txt -promoters emx1.hg19.annotated.PromotersCount.txt -gecko
    while IFS= read -r line || [ -n "$line" ]; do    
        for i in $(seq 0 $7); do 
            
            if [ ${14} = 'True' ]; then
                crispritz.py generate-report $line -mm $i -profile $1'/'$jobid'.profile.xls' -extprofile $1/*.extended_profile.xls -exons $1'/'$jobid'.annotated.ExonsCount.txt' -introns $1'/'$jobid'.annotated.IntronsCount.txt' -dnase $1'/'$jobid'.annotated.DNAseCount.txt' -ctcf $1'/'$jobid'.annotated.CTCFCount.txt' -promoters $1'/'$jobid'.annotated.PromotersCount.txt' -gecko
            else 
                crispritz.py generate-report $line -mm $i -profile $1'/'$jobid'.profile.xls' -extprofile $1/*.extended_profile.xls -exons $1'/'$jobid'.annotated.ExonsCount.txt' -introns $1'/'$jobid'.annotated.IntronsCount.txt' -dnase $1'/'$jobid'.annotated.DNAseCount.txt' -ctcf $1'/'$jobid'.annotated.CTCFCount.txt' -promoters $1'/'$jobid'.annotated.PromotersCount.txt'
            fi
        done

    done < $6
  
fi
mv ./*.pdf $1
mv ./*.png $1   #TODO move these command inside if, and check for when to do annotation ref and enr for barplot

mkdir assets/Img/$jobid
cp $PWD/$1/*.png assets/Img/$jobid/
echo 'Report\tDone\t'$(date) >> $1'/'log.txt

echo 'Job\tDone\t'$(date)>> $1'/'log.txt

