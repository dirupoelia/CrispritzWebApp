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
#$18 is annotation file EG annotations/hg19_ref.annotations.bed
#$19 is genome type, can be 'ref', 'var', 'both'
#Note that if genome_selected is not enriched, the python exe will force $15 as false

jobid=$(basename $1)
echo 'Job\tStart\t'$(date)> $1'/'log.txt
used_genome_dir=$2                 

#Start search index     #NOTE new version 2.1.2 of crispritz needed
echo 'Search-index\tStart\t'$(date) >> $1'/'log.txt
if [ ${10} = 'True' ]; then
    #echo 'crispritz search-index'
    crispritz.py search $4 $5 $6 $jobid -index -mm $7 -bDNA $8 -bRNA ${9} -t #-scores $3
    mv ./$jobid.*.txt $1
    mv ./$jobid.*.xls $1

    if [ ${15} = 'True' ]; then
        mkdir $1'/ref'
        crispritz.py search ${16} $5 $6 $jobid'_ref' -index -mm $7 -bDNA $8 -bRNA ${9} -t    
        mv ./$jobid'_ref'.*.txt $1/ref
        mv ./$jobid'_ref'.*.xls $1/ref
    fi
fi
echo 'Search-index\tDone\t'$(date) >> $1'/'log.txt

#Start search
echo 'Search\tStart\t'$(date) >> $1'/'log.txt
if [ ${11} = 'True' ]; then
    #echo 'crispritz search'
    crispritz.py search $used_genome_dir $5 $6 $jobid -mm $7 -t #-scores $3
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


#Start annotation       #NOTE new version 2.1.2 of crispritz needed
echo 'Annotation\tStart\t'$(date) >> $1'/'log.txt
if [ ${12} = 'True' ]; then
    #echo 'crispritz annotate'
    if [ ${10} = 'True' ]; then         #Indexed search was done, read profile complete
        crispritz.py annotate-results $1'/'/$jobid.profile_complete.xls $1'/'$jobid'.targets.txt' ${18} $jobid
    fi
    if [ ${11} = 'True' ]; then         #Normal search was done, read profile
        crispritz.py annotate-results $1'/'/$jobid.profile.xls $1'/'$jobid'.targets.txt' ${18} $jobid
    fi
    mv ./$jobid.Annotation*.txt $1
    if [ ${15} = 'True' ]; then
        if [ ${10} = 'True' ]; then
            crispritz.py annotate-results $1'/ref/'$jobid'_ref.profile_complete.txt' $1'/ref/'$jobid'_ref.targets.txt' ${18} $jobid
        fi
        if [ ${11} = 'True' ]; then
            crispritz.py annotate-results $1'/ref/'$jobid'_ref.profile.txt' $1'/ref/'$jobid'_ref.targets.txt' ${18} $jobid
        fi
        mv ./$jobid'_ref'.Annotation*.txt $1/ref
    fi
fi
echo 'Annotation\tDone\t'$(date) >> $1'/'log.txt

#Start generate report
echo 'Report\tStart\t'$(date) >> $1'/'log.txt
#python3 summary_guide.py $1 $7  #New annotated file are alredy located in right directories
profile_type='profile_complete'
if [ ${11} = 'True' ]; then
    profile_type='profile'
fi

cd $1
if [ ${13} = 'True' ]; then
    #echo 'crispritz report'
    #-profile emx1.hg19.profile.xls -extprofile emx1.hg19.extended_profile.xls -exons emx1.hg19.annotated.ExonsCount.txt -introns emx1.hg19.annotated.IntronsCount.txt -dnase emx1.hg19.annotated.DNAseCount.txt -ctcf emx1.hg19.annotated.CTCFCount.txt -promoters emx1.hg19.annotated.PromotersCount.txt -gecko
    while IFS= read -r line || [ -n "$line" ]; do    
        for i in $(seq 0 $7); do 
            
            if [ ${14} = 'True' ]; then         #If -gecko
                if [ ${15} = 'True' ]; then     #If genome_ref comparison
                   
                    crispritz.py generate-report $line -mm $i -profile $jobid'.'$profile_type'.xls' -extprofile *.extended_profile.xls -annotation $jobid'.Annotation.txt' -sumref ref/$jobid'_ref'.Annotation.txt  -gecko
                else
                    crispritz.py generate-report $line -mm $i -profile $jobid'.'$profile_type'.xls' -extprofile *.extended_profile.xls -annotation $jobid'.Annotation.txt' -gecko
                fi
            else
                if [ ${15} = 'True' ]; then     #If genome_ref comparison
                    crispritz.py generate-report $line -mm $i -profile $jobid'.'$profile_type'.xls' -extprofile *.extended_profile.xls -annotation $jobid'.Annotation.txt' -sumref ref/$jobid'_ref'.Annotation.txt
                else
                    crispritz.py generate-report $line -mm $i -profile $jobid'.'$profile_type'.xls' -extprofile *.extended_profile.xls -annotation $jobid'.Annotation.txt'
                fi
            fi
        done

    done < guides.txt
  
fi


cd ../../

mkdir assets/Img/$jobid
cp $PWD/$1/*.png assets/Img/$jobid/
echo 'Report\tDone\t'$(date) >> $1'/'log.txt

#Temp (find better way when scores will be modified), sum of cfd per guide
#TODO scores_test will be substituted with -scores option with crispritz 2.1.2
echo 'PostProcess\tStart\t'$(date) >> $1'/'log.txt
cd $1

python3 ../../PostProcess/scores_guide_table.py $jobid.targets.txt ../../$used_genome_dir pam.txt

#Estract common, semicommon and unique
if [ ${19} = 'both' ]; then
    echo 'script per semicommon'
    #chiamata script
fi

#Clustering
if [ ${19} != 'both' ]; then
    python3 ../../PostProcess/cluster.dict.py $jobid.targets.txt
else
    python3 ../../PostProcess/cluster.dict.py $jobid.semicommon #TODO mettere nomi giusti
    python3 ../../PostProcess/cluster.dict.py $jobid.uniq
fi

#TODO sistemare il conteggio dei var uniq: al momento non lo fa perchè non c'è crispritz con il post processing, in futuro scegliere tra 'No' e 'Uniq' in base
#all'opzione scelta
if [ ${19} = 'ref' ]; then
    type_post='No'
    python3 ../../PostProcess/summary_by_guide_position.py $jobid.targets.cluster.txt $7 $8 $9 guides.txt $jobid $type_post
elif [ ${19} = 'var' ]; then
    type_post='No'
    python3 ../../PostProcess/summary_by_guide_position.py $jobid.targets.cluster.txt $7 $8 $9 guides.txt $jobid $type_post
    #TODO ADD sample analysis
else
    type_post='Uniq'
    python3 ../../PostProcess/summary_by_guide_position.py $jobid.targets.cluster.txt $7 $8 $9 guides.txt $jobid $type_post
    #TODO ADD sample analysis
fi


cd ../../
echo 'PostProcess\tDone\t'$(date) >> $1'/'log.txt
if [ ${17} = 'True' ]; then
    python3 send_mail.py $1
fi
echo 'Job\tDone\t'$(date)>> $1'/'log.txt
