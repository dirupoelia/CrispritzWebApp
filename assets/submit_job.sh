#!/bin/sh
#$1 is directory of result for submitted job id (Results/job_id)
#$2 is genome_selected directory Eg Genomes/hg19_ref or Genomes/hg19_ref+1000genomeproject #NOTE + or - to decide
#$3 is genome_ref directory     Eg Genomes/hg19_ref
#$4 is genome_idx directory     Eg genome_library/NGG_2_hg19_ref+hg19_1000genomeproject or genome_library/NGG_2_hg19_ref
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
#$16 is genme_idx_ref (for genome_ref comparison if search was done with indices)   Eg genome_library/NGG_2_hg19_ref
#$17 is send_email
#$18 is annotation file containing path  EG hg19_ref_annotationspath.txt
#Note that if genome_selected is not enriched, the python exe will force $15 as false

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
        crispritz.py search ${16} $5 $6 $jobid'_ref' -index -mm $7 -bDNA $8 -bRNA ${9} -t      #TODO sistemare il genoma che non è quello in input ma il ref indicizzato
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
    crispritz.py annotate-results $6 $1'/'$jobid'.targets.txt' ${18} $jobid'.annotated'
    mv ./$jobid.annotated.*.txt $1
    if [ ${15} = 'True' ]; then
        crispritz.py annotate-results $6 $1'/ref/'$jobid'_ref.targets.txt' ${18} $jobid'_ref.annotated'
        mv ./$jobid'_ref'.annotated.*.txt $1/ref
    fi
fi
echo 'Annotation\tDone\t'$(date) >> $1'/'log.txt

#Start generate report
echo 'Report\tStart\t'$(date) >> $1'/'log.txt
python3 summary_guide.py $1 $7  #New annotated file are alredy located in right directories
mkdir $jobid
cd $jobid
if [ ${13} = 'True' ]; then
    #echo 'crispritz report'
    #-profile emx1.hg19.profile.xls -extprofile emx1.hg19.extended_profile.xls -exons emx1.hg19.annotated.ExonsCount.txt -introns emx1.hg19.annotated.IntronsCount.txt -dnase emx1.hg19.annotated.DNAseCount.txt -ctcf emx1.hg19.annotated.CTCFCount.txt -promoters emx1.hg19.annotated.PromotersCount.txt -gecko
    while IFS= read -r line || [ -n "$line" ]; do    
        for i in $(seq 0 $7); do 
            
            if [ ${14} = 'True' ]; then         #If -gecko
                if [ ${15} = 'True' ]; then     #If genome_ref comparison
                   
                    crispritz.py generate-report $line -mm $i -profile ../$1'/'$jobid'.profile.xls' -extprofile ../$1/*.extended_profile.xls -exons ../$1'/'$jobid'.annotated.ExonsCount.txt' -introns ../$1'/'$jobid'.annotated.IntronsCount.txt' -dnase ../$1'/'$jobid'.annotated.DNAseCount.txt' -ctcf ../$1'/'$jobid'.annotated.CTCFCount.txt' -promoters ../$1'/'$jobid'.annotated.PromotersCount.txt' -sumref ../$1/ref/$jobid'_ref'.annotated.$line.SummaryCount.txt -sumenr ../$1'/'$jobid'.annotated.'$line'.SummaryCount.txt' -gecko
                else
                    crispritz.py generate-report $line -mm $i -profile ../$1'/'$jobid'.profile.xls' -extprofile ../$1/*.extended_profile.xls -exons ../$1'/'$jobid'.annotated.ExonsCount.txt' -introns ../$1'/'$jobid'.annotated.IntronsCount.txt' -dnase ../$1'/'$jobid'.annotated.DNAseCount.txt' -ctcf ../$1'/'$jobid'.annotated.CTCFCount.txt' -promoters ../$1'/'$jobid'.annotated.PromotersCount.txt' -gecko
                fi
            else
                if [ ${15} = 'True' ]; then     #If genome_ref comparison
                    #python3 summary_guide.py $1 $7 
                    crispritz.py generate-report $line -mm $i -profile ../$1'/'$jobid'.profile.xls' -extprofile ../$1/*.extended_profile.xls -exons ../$1'/'$jobid'.annotated.ExonsCount.txt' -introns ../$1'/'$jobid'.annotated.IntronsCount.txt' -dnase ../$1'/'$jobid'.annotated.DNAseCount.txt' -ctcf ../$1'/'$jobid'.annotated.CTCFCount.txt' -promoters ../$1'/'$jobid'.annotated.PromotersCount.txt' -sumref ../$1/ref/$jobid'_ref'.annotated.$line.SummaryCount.txt -sumenr ../$1'/'$jobid'.annotated.'$line'.SummaryCount.txt'
                else
                    crispritz.py generate-report $line -mm $i -profile ../$1'/'$jobid'.profile.xls' -extprofile ../$1/*.extended_profile.xls -exons ../$1'/'$jobid'.annotated.ExonsCount.txt' -introns ../$1'/'$jobid'.annotated.IntronsCount.txt' -dnase ../$1'/'$jobid'.annotated.DNAseCount.txt' -ctcf ../$1'/'$jobid'.annotated.CTCFCount.txt' -promoters ../$1'/'$jobid'.annotated.PromotersCount.txt'
                fi
            fi

            
        done

    done < ../$6
  
fi

for i in *.pdf; do
   pdftoppm -png -rx 300 -ry 300 $i ${i%.pdf*} 2>/dev/null      #Errors when plot is empty, so redirect stderr to not bloat the terminal
done
rename 's/-1//g' ./*

mv ./*.pdf ../$1
mv ./*.png ../$1   #TODO move these command inside if, and check for when to do annotation ref and enr for barplot
cd ..
rm -r $jobid
mkdir assets/Img/$jobid
cp $PWD/$1/*.png assets/Img/$jobid/

#Temp (find better way when scores will be modified), sum of cfd per guide
#TODO put control if scores were not computed
#awk -F'\t' '{a[$2] += $9} END{for (i in a) print i, a[i]}' $1/$jobid.scores.txt > $1'/'acfd.txt
while IFS= read -r line || [ -n "$line" ]; do 
    python3 scores_test.py $1/$jobid.targets.txt $line
done < $6



echo 'Report\tDone\t'$(date) >> $1'/'log.txt

if [ ${17} = 'True' ]; then
    python3 send_mail.py $1
fi

while IFS= read -r line || [ -n "$line" ]; do 
    python3 summary_table.py $1/$jobid.targets.txt $7 $8 $9 $line $jobid
done < $6

mv $jobid'_summary_result_'* $1

echo 'Job\tDone\t'$(date)>> $1'/'log.txt
