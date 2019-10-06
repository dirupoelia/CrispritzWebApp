#Use bedtool to extract sequence
import subprocess
import os
#Input chr1:11,130,540-11,130,751
def extractSequence(name, input_range, genome_selected):
    chrom = input_range.split(':')[0]
    start_position = input_range.split(':')[1].split('-')[0].replace(',','')
    end_position = input_range.split(':')[1].split('-')[1].replace(',','')
    with open(name + '.bed','w') as b:
        b.write(chrom + '\t' + start_position + '\t' + end_position)
    #TODO insert control on fa or fasta
    output_extract = subprocess.check_output(['bedtools getfasta -fi ' + 'Genomes/' + genome_selected + '/' + chrom + '.fa' + ' -bed ' + name + '.bed'], shell=True).decode("utf-8") 
    try:
        os.remove('Genomes/' + genome_selected + '/' + chrom + '.fa.fai')
    return output_extract.split('\n')[1].strip()