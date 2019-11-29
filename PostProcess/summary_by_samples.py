#Dato in input un target.txt, la funzione calcola, per ogni diverso sample, il suo numero di occorrenze. Come prima riga abbiamo la guida + il numero di targets che hanno almeno un sample
#NON CANCELLARE

import os
import subprocess
import sys
import pandas as pd
# argv1  is result file, from top1 with expanded samples
# argv2 is guide    #TODO change into dictionary of guides
# argv3 is job_id
#NOTE Function only with vcf of HG38 and population info from the 20130606_sample_info.xlsx file
guide = sys.argv[2]
total_sample_per_guide = 0
#Load population info
pop_file = pd.read_excel('20130606_sample_info.xlsx')
all_samples = pop_file.Sample.to_list()
all_pop = pop_file.Population.to_list()
dict_pop = dict()
for  pos, i in enumerate(all_samples):
    dict_pop[i] = all_pop[pos]

# Each sample (HG0096) has a list -> [Total targets, Var_uniq targets, Population]
samples = dict()

with open(sys.argv[1]) as sample_file, open(sys.argv[3] + '.summary_by_samples.' + guide + '.txt', 'w+') as result:
    for line in sample_file:
        line = line.strip().split('\t')
        if '#' in line[1]:
            continue
        if 'No' not in line[-1] and line[1].replace('-','') == guide:
            words = line[-1].split(',')
            total_sample_per_guide = total_sample_per_guide + 1
            for word in words:
                try:
                    samples[word][0] = samples[word][0] + 1
                except:
                    samples[word] = [1,0]
                if 'y' in line[-2]:
                    samples[word][1] = samples[word][1] + 1
    result.write(guide + '\t' + str(total_sample_per_guide) + '\n')
    for i in samples:
        if i == 'Samples':
            continue
        result.write(i + '\t' + str(samples[i][0]) +'\t' + str(samples[i][1]) + '\t' + dict_pop[i] + '\n')
