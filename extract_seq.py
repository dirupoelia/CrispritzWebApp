#Use bedtool to extract sequence
import subprocess
import os
#Input chr1:11,130,540-11,130,751
input = 'chr1:11,130,540-11,130,751'
chrom = input.split(':')[0]
start_position = input.split(':')[1].split('-')[0].replace(',','')
end_position = input.split(':')[1].split('-')[1].replace(',','')
with open('test_bed.bed','w') as b:
    b.write(chrom + '\t' + start_position + '\t' + end_position)

subprocess.run(['bedtools getfasta -fi ' + chrom + ' -bed ' + 'test_bed.bed'], shell=True) #TODO mettere directory giuste e cancellare indice creato
