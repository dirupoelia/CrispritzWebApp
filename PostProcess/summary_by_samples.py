#Dato in input un target.txt, la funzione calcola, per ogni diverso sample, il suo numero di occorrenze. Come prima riga abbiamo la guida + il numero di targets che hanno almeno un sample
#NON CANCELLARE

import os
import subprocess
import sys
import pandas as pd
# argv1  is result file, from top1 with expanded samples
# argv2 is job_id
# argv3 is type genome 'ref', 'var', 'both'
# argv4 is guides file
#NOTE Function only with vcf of HG38 and population info from the 20130606_sample_info.xlsx file

# total_sample_per_guide = 0
#Load population info
# try:
#     pop_file = pd.read_excel('../../PostProcess/20130606_sample_info.xlsx')
# except:
pop_file = pd.read_excel(os.path.dirname(os.path.realpath(__file__)) + '/20130606_sample_info.xlsx')
all_samples = pop_file.Sample.to_list()
all_pop = pop_file.Population.to_list()
dict_pop = dict()
for  pos, i in enumerate(all_samples):
    dict_pop[i] = all_pop[pos]
population_1000gp = {'CHB':'EAS', 'JPT':'EAS', 'CHS':'EAS', 'CDX':'EAS', 'KHV':'EAS',
                    'CEU':'EUR', 'TSI':'EUR', 'FIN':'EUR', 'GBR':'EUR', 'IBS':'EUR',
                    'YRI':'AFR', 'LWK':'AFR', 'GWD':'AFR', 'MSL':'AFR', 'ESN':'AFR', 'ASW':'AFR', 'ACB':'AFR',
                    'MXL':'AMR', 'PUR':'AMR', 'CLM':'AMR', 'PEL':'AMR',
                    'GIH':'SAS', 'PJL':'SAS', 'BEB':'SAS', 'STU':'SAS', 'ITU':'SAS'
}
# Each guide has a dictionary, with samples as keys. Each sample (HG0096) has a list -> [Total targets, Var_uniq targets]
guides_dict = dict()
guides_dict_total = dict()  #contains total_sample_per_guide, did not merge the dict because didn't have time to do it
guides_population_targets = dict()
guides_superpopulation_targets = dict()
current_chr_pos = '0'
with open(sys.argv[1]) as sample_file: #, open(sys.argv[3] + '.summary_by_samples.' + guide + '.txt', 'w+') as result:
    for line in sample_file:
        if '#' in line:
            continue
        line = line.strip().split('\t')
        if 'No' not in line[-2]:
            guide = line[1].replace('-','')
            if guide not in guides_dict:
                guides_dict[guide] = dict()
                guides_dict_total[guide] = 0

            words = line[-2].split(',')
            
            if current_chr_pos != line[3]+line[4]:
                guides_dict_total[guide] += 1
                current_chr_pos = line[3]+line[4]

            for word in words:
                try:
                    guides_dict[guide][word][0] += 1
                except:
                    guides_dict[guide][word] = [1,0]
                if sys.argv[3] == 'both':
                    if 'y' in line[-3]:
                        guides_dict[guide][word][1] += 1

with open(sys.argv[4], 'r') as g_file:
    for line in g_file:
        line = line.strip()
        if line not in guides_dict:
            guides_dict[line] = None
            guides_dict_total[line] = None

#Sum for population
index_sum = 0
if sys.argv[3] == 'both':
    index_sum = 1
for guide in guides_dict:
    guides_population_targets[guide] = dict()
    for s in guides_dict[guide]:
        try:
            guides_population_targets[guide][dict_pop[s]] += guides_dict[guide][i][index_sum]
        except:
            guides_population_targets[guide][dict_pop[s]] = guides_dict[guide][i][index_sum]

#Sum for superpopulation
for guide in guides_dict:
    guides_superpopulation_targets[guide] = dict()  
    for p in guides_population_targets[guide]:
        try:
            guides_superpopulation_targets[guide][population_1000gp[p]] += guides_population_targets[guide][p]
        except:
            guides_superpopulation_targets[guide][population_1000gp[p]] += guides_population_targets[guide][p]


for k in guides_dict.keys():
    with open(sys.argv[2] + '.summary_by_samples.' + k + '.txt', 'w+') as result:
        if guides_dict[k]:
            result.write(k + '\t' + str(guides_dict_total[k]) + '\n')
            if sys.argv[3] == 'both':
                for i in guides_dict[k]:
                    result.write(i + '\t' + str(guides_dict[k][i][0]) +'\t' + str(guides_dict[k][i][1]) + '\t' + dict_pop[i] + '\t' + guides_population_targets[k][i] + '\t' + population_1000gp[dict_pop[i]] +'\t'+guides_superpopulation_targets[guide][population_1000gp[dict_pop[i]]]  + '\n')
            else:
                for i in guides_dict[k]:
                    result.write(i + '\t' + str(guides_dict[k][i][0]) + '\t' + dict_pop[i] + '\t' + guides_population_targets[k][i] + '\t' + population_1000gp[dict_pop[i]] +'\t'+guides_superpopulation_targets[guide][population_1000gp[dict_pop[i]]] +'\n')

        else:
            result.write('No samples found with ' + k + ' guide')
