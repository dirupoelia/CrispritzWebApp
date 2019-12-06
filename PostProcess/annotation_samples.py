'''
Script that annotatets the samples, in order to have a fast generate-report
Input file is job_id.top_1.samples, job_id.Annotations.targets., job_id.Annotation.txt
Create a dict for the guides, that contains a dict for the samples, that contains a dict for the annotatio category
Eg 
{
    GUIDE1 -> {
        SAMPLE1 -> {
            EXON -> [0 0 0 0 1 0 0 8 2 0],
            INTRONS -> [0 0 0 0 1 0 0 8 2 0],
            CTCF -> [0 0 0 0 1 0 0 8 2 0]
        },
        SAMPLE2 ->{
            EXON -> [0 0 0 0 1 0 0 8 2 0],
            INTRONS -> [0 0 0 0 1 0 0 8 2 0],
            CTCF ->[0 0 0 0 1 0 0 8 2 0]
        }
    },
    GUIDE2 ->{
        SAMPLE ->{
            ANNOTATION -> [annotation count for each mm value]
        }
    }
}
'''
#TODO testare

import sys
import os
import pandas as pd
# argv 1 is top1.samples.txt
# argv 2 is Annotation.targets
# argv 3 is Annotation.txt -> to get the name of annotations

# samples_dict = {
    # GUIDE1 ->{
    #     chrXposY -> [[Sample1, sample7], []]
    #     chrXposY2 -> [[Sample5, sample7], []]
    #     chrX2posY 3-> [[Sample10, sample11, sample30], []]
    # },
    # GUIDE2 -> {
    #     CHRPOS -> [[Sample list], [List visited annotations]]                List visited annotation is empty at first, but can become -> ['exon', 'promoter',...]
    # }
# }
samples_dict = dict()
annotation_dict = dict()
with open(sys.argv[1]) as targets:
    for line in targets:
        if '#' in line:
            continue
        line = line.strip().split('\t')
        guide = line[1].replace('-','')
        if guide not in samples_dict:
            samples_dict[guide] = dict()
        try:
            samples_dict[guide][line[3] + line[4]][0] += line[-1].split(',')
        except:     
            samples_dict[guide][line[3] + line[4]] = [line[-1].split(','), []]


# print(samples_dict['CTAACAGTTGCTTTTATCACNNN']['chr2146560428'])
# print(samples_dict['TGCTTGGTCGGCACTGATAGNNN']['chr2250085897'])

ann_list = []

with open (sys.argv[3], 'r') as ann_file:
    for line in ann_file:
        if '-' in line[0] and 'Summary' not in line:
            ann_list.append(line.strip()[1:])

summary_sample = dict()

with open (sys.argv[2]) as targets:             #Count annotation for each target
    for line in targets:
        if '#' in line:
            continue
        line = line.strip().split('\t')
        guide = line[1].replace('-','')
        
        if guide not in annotation_dict.keys():
            annotation_dict[guide] = dict()
        try:
            samples_list = samples_dict[guide][line[3] + line[4]]
        except:
            samples_list = [[], ann_list]
        if line[-1] in samples_list[1]:
            continue
        samples_dict[guide][line[3] + line[4]][1].append(line[-1])
        for sample in samples_list[0] :
            if sample not in annotation_dict[guide]:
                annotation_dict[guide][sample] = dict()     #TODO errore sistemare conteggio samples tartgets
                # print(guide, sample, line[-1], line[6])
                summary_sample[sample] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            try:
                annotation_dict[guide][sample][line[-1]][int(line[6])] += 1       #increase annotation count
                summary_sample[sample][int(line[6])] += 1
            except:
                annotation_dict[guide][sample][line[-1]] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                annotation_dict[guide][sample][line[-1]][int(line[6])] += 1
                summary_sample[sample][int(line[6])] += 1

# print(annotation_dict['CTAACAGTTGCTTTTATCACNNN'])

# print('HG00282', annotation_dict['CTAACAGTTGCTTTTATCACNNN']['HG00282'])
# print('NA12056',  annotation_dict['CTAACAGTTGCTTTTATCACNNN']['NA12056'])
for guide in annotation_dict:
    with open('test_count_annotation_sample.' + guide +'.samples.txt', 'w+') as result:
        for annotation in ann_list:
            result.write('-' + annotation + '\n')
            for sample in annotation_dict[guide]:
                result.write(sample)
                try:
                    result.write('\t' + '\t'.join(str(x) for x in annotation_dict[guide][sample][annotation] ) + '\n' )
                except:
                    result.write('\t' + '\t'.join(['0' for i in range(10)]) + '\n')
        result.write('-Summary_Total\n')
        for sample in annotation_dict[guide]:
            result.write('-Summary_' + sample + '\n')
            result.write('targets\t'.join(str(x) for x in  summary_sample[sample]) + '\n')
            for annotation in ann_list:
                result.write(annotation + '\t')
                try:
                    result.write('\t'.join(str(x) for x in annotation_dict[guide][sample][annotation] ) + '\n' )
                except:
                    result.write('\t'.join(['0' for i in range(10)]) + '\n')

# print(annotation_dict['TGCTTGGTCGGCACTGATAGNNN']['NA12056'])
#For each population, count total sample values
pop_file = pd.read_excel(os.path.dirname(os.path.realpath(__file__)) + '/20130606_sample_info.xlsx')
all_samples = pop_file.Sample.to_list()
all_pop = pop_file.Population.to_list()
dict_pop = dict()
for  pos, i in enumerate(all_pop):
    try:
        dict_pop[i].append(all_samples[pos])
    except:
        dict_pop[i] = [all_samples[pos]]

dict_pop_count = dict()
for guide in annotation_dict:
    with open('test_count_annotation_sample.' + guide + '.population.txt', 'w+') as result:
        dict_pop_count[guide] = dict()
        for population in dict_pop.keys():
            #Initialize dict
            dict_pop_count[guide][population] = dict()
            for a in ann_list:
                dict_pop_count[guide][population][a] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            #Count sum of sample for each pupulation for each annotation
            for a in ann_list:
                for sample in dict_pop[population]:
                    try:
                        dict_pop_count[guide][population][a] = [dict_pop_count[guide][population][a][i] + annotation_dict[guide][sample][a][i] for i in range(len(dict_pop_count[guide][population][a])) ]    # annotation_dict[guide][sample][a]
                    except:
                        dict_pop_count[guide][population][a] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            #result.write(population)
        #Write result
        for a in ann_list:
            result.write('-' + a + '\n')
            for population in dict_pop.keys():
                if population in dict_pop_count[guide]:
                    result.write(population)
                    result.write('\t' + '\t'.join(str(x) for x in dict_pop_count[guide][population][a] ) + '\n')         
            result.write('\n')
# print(dict_pop_count)
# print(dict_pop.keys())
#Populations 1000 gen proj
population_1000gp = {
    'EAS':['CHB', 'JPT', 'CHS', 'CDX', 'KHV'],
    'EUR':['CEU', 'TSI', 'FIN', 'GBR', 'IBS'],
    'AFR':['YRI', 'LWK', 'GWD', 'MSL', 'ESN', 'ASW', 'ACB'],
    'AMR':['MXL', 'PUR', 'CLM', 'PEL'],
    'SAS':['GIH', 'PJL', 'BEB', 'STU', 'ITU']
}
#For each superpopulation, write sum of population
for guide in annotation_dict:    
    with open('test_count_annotation_sample.' + guide + '.superpopulation.txt', 'w+') as result:
        for a in ann_list:
            result.write('-' + a + '\n')
            for superpopulation in population_1000gp:
                tmp_sum = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                for population in population_1000gp[superpopulation]:
                    try:
                        tmp_sum = [ tmp_sum[i] + dict_pop_count[guide][population][a][i] for i in range(len(tmp_sum))]
                    except:
                        tmp_sum = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                result.write(superpopulation)
                result.write('\t' + '\t'.join(str(x) for x in tmp_sum) + '\n')
                

            