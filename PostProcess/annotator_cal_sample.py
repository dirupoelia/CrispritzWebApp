#!/usr/bin/env python

'''
Merge of annotator and calc_samples_faster.py
Prende in input il file dei top1, ordinati per chr, e estrae i samples corrispondenti. Per ogni target, salva l'insieme dei sample in samples.all.txt, crea le combinazioni tenendo i target reali
in samples.txt, poi calcola l'annotazione corrispondente e crea il file Annotation.targets e  i vari summaries.
'''


#NOTE serve 20130606_sample_info.xlsx nella stessa cartella di questo script 
#argv1 è il file .bed con le annotazioni
#argv2 è il file top1 ordinato per chr
#argv3 è nome del file in output
#argv4 è directory dei dizionari

import sys
import json
import time
import itertools
import os
from intervaltree import Interval, IntervalTree
import concurrent.futures
import subprocess
import pandas as pd
print('ESECUZIONE DI ANNOTATION E CALC SAMPLE INSIEME')
print('TEST PER ANNOTAZIONE COMPLETA: I TARGET SENZA ANNOTAZIONE SONO SALVATI COME \"n\"')
print('SE UN  TARGET HA 1+ ANNOTAZIONI, LE SALVA IN SINGOLA UNICA RIGA')
print("READING INPUT FILES")
#Dictionaries for annotating samples

#Dict for populations
pop_file = pd.read_excel(os.path.dirname(os.path.realpath(__file__)) + '/20130606_sample_info.xlsx')
all_samples = pop_file.Sample.to_list()
all_pop = pop_file.Population.to_list()
dict_sample_to_pop = dict()
for  pos, i in enumerate(all_samples):
    try:
        dict_sample_to_pop[i] = all_pop[pos]        #{'S1':'POP1', 'S2':'POP1', ...}
    except:
        dict_sample_to_pop[i] = all_pop[pos]

#Dict for superpopulation
dict_pop_to_sup = {'CHB':'EAS', 'JPT':'EAS', 'CHS':'EAS', 'CDX':'EAS', 'KHV':'EAS',
                    'CEU':'EUR', 'TSI':'EUR', 'FIN':'EUR', 'GBR':'EUR', 'IBS':'EUR',
                    'YRI':'AFR', 'LWK':'AFR', 'GWD':'AFR', 'MSL':'AFR', 'ESN':'AFR', 'ASW':'AFR', 'ACB':'AFR',
                    'MXL':'AMR', 'PUR':'AMR', 'CLM':'AMR', 'PEL':'AMR',
                    'GIH':'SAS', 'PJL':'SAS', 'BEB':'SAS', 'STU':'SAS', 'ITU':'SAS'
}
superpopulation = ['EAS', 'EUR', 'AFR', 'AMR','SAS']


#READ INPUT FILES
annotationFile = sys.argv[1] #file with annotation
resultsFile = sys.argv[2] #file with results from search
outputFile = sys.argv[3] #file with annotated results

#OPEN INPUT FILES AND PREPARE OUTPUT FILE
inResult = open(resultsFile, "r")  # resultfile open
inAnnotationFile = open(annotationFile, "r")  # file with annotations open
outFileSampleAll = open(outputFile + '.samples.all.annotation.txt', 'w')  # outfile open (file with IUPAC targets and associated samples and annotation)
outFileSample = open(outputFile + '.samples.annotation.txt', 'w') #file with real nucleotides with associated samples and annotation
outFileSummary = open(outputFile + '.Annotation.summary.txt', 'w')  # outfile open (summary file calculated on top1file)

process = subprocess.Popen(['wc', '-l', resultsFile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = process.communicate()
total_line = int(out.decode('UTF-8').split(' ')[0])
if total_line < 2:
    print('WARNING! Input file has no targets')
    sys.exit()
if total_line < 10:
    mod_tot_line = 1
else:
    mod_tot_line = int(total_line/10)
#VARIABLE INIT
guideDict = {}
totalDict = {}

start_time = time.time()

print("EXECUTING PRELIMINARY OPERATIONS")

annotationsTree = IntervalTree()
annotationsSet = set()
#guidesSet = set()       #NOTE/BUG if guide finds 0 targets, it will not be annotated

for line in inAnnotationFile:
    x = line.split('\t')
    x[3] = str(x[3]).rstrip("\n")
    annotationsTree[int(x[1]):int(x[2])] = str(x[0])+'\t'+str(x[3])
    annotationsSet.add(str(x[3]))

totalDict['targets'] = [0]*10
for item in annotationsSet:
    totalDict[item] = [0]*10

print("PRELIMINARY OPERATIONS COMPLETED IN: %s seconds" % (time.time() - start_time))

start_time = time.time()

print("EXECUTING ANNOTATION")

with open(resultsFile, 'r') as resFile:
    header_len = len(resFile.readline().strip().split('\t'))

if header_len == 15:    #'Both' case : comparison variant/ref is active
    header = '#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\tMin_mismatches\tMax_mismatches\tPam_disr\tPAM_gen\tVar_uniq\tSamples\tReal Guide\tAnnotation Type'
else:                   #'Var' case: PAM creation and Variant_unique not calculated
    header = '#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\tMin_mismatches\tMax_mismatches\tPam_disr\tSamples\tReal Guide\tAnnotation Type'

mm_pos = 7      #position of mismatch column
outFileSample.write(header + '\n')
outFileSampleAll.write(header + '\n')
summary_samples = True

header_list = header.strip().split('\t')
#Variables for summary samples code
'''
{
    GUIDE1 -> {
        SAMPLE/POP/SUPERPOP1 ->{
            targets -> [0 0 0 0 0 0 0 0 0],
            ann1 -> [0 0 0 0 0 0 0 0 0],
            ann2 -> [0 0 0 0 0 0 0 0 0],
        },
        SAMPLE/POP/SUPERPOP2 ->{
            targets -> [0 0 0 0 0 0 0 0 0],
            ann1 -> [0 0 0 0 0 0 0 0 0],
            ann2 -> [0 0 0 0 0 0 0 0 0],
        }
    }
    GUIDE2 -> {
        SAMPLE/POP/SUPERPOP1 ->{
            targets -> [0 0 0 0 0 0 0 0 0],
            ann1 -> [0 0 0 0 0 0 0 0 0],
            ann2 -> [0 0 0 0 0 0 0 0 0],
        },
        SAMPLE/POP/SUPERPOP2 ->{
            targets -> [0 0 0 0 0 0 0 0 0],
            ann1 -> [0 0 0 0 0 0 0 0 0],
            ann2 -> [0 0 0 0 0 0 0 0 0],
        }
    }
}

Per pop e superpop, se ho due sample stessa famiglia stesso target, conto solo una volta (visited_pop and visited_superpop array)
'''
count_sample = dict()
count_pop = dict()
count_superpop = dict()

#Create -Summary_total for a file ref.Annotation.summary.txt from the y and n values of Var_uniq column
summary_barplot_from_total = False
if 'Var_uniq' in header:
    summary_barplot_from_total = True
    vu_pos = header_list.index('Var_uniq')
count_unique = dict()
count_unique['targets'] = [0]*10
count_unique_for_guide = dict()
for item in annotationsSet:
    count_unique[item] = [0]*10

#Variables for samples calculation
total_error = 0
resu_name = outputFile + '.samples.txt'
test_resu_name = outputFile + '.samples.all.txt' #Put in a line all the samples, not the intersection, keep original line

current_chr = 'none'
chr_name = 'none'

def rev_comp(a):
    if a == 'A' or a == 'a':
        return 'T'
    if a == 'T' or a == 't':
        return 'A'
    if a == 'C' or a == 'c':
        return 'G'
    return 'C'

iupac_code = {
            "R":("A", "G"),
            "Y":("C", "T"),
            "S":("G", "C"),
            "W":("A", "T"),
            "K":("G", "T"),
            "M":("A", "C"),
            "B":("C", "G", "T"),
            "D":("A", "G", "T"),
            "H":("A", "C", "T"),
            "V":("A", "C", "G"),
            "r":("A", "G"),
            "y":("C", "T"),
            "s":("G", "C"),
            "w":("A", "T"),
            "k":("G", "T"),
            "m":("A", "C"),
            "b":("C", "G", "T"),
            "d":("A", "G", "T"),
            "h":("A", "C", "T"),
            "v":("A", "C", "G"),
            'N':('A', 'T', 'C', 'G')
            }
start_time_total = time.time()
lines_processed = 0
#with  open(outputFile + '.samples.annotation.txt','w+') as outFileSample, open(outputFile + '.samples.all.annotation.txt', 'w+') as outFileSampleAll:
for line in inResult:
    if '#' in line:
        continue
    x = line.strip().split('\t')
    x[1] = str(x[1]).replace("-","")
    if x[3] != current_chr:
        if not os.path.exists(os.path.realpath(sys.argv[4]) + '/my_dict_' + x[3] + '.json'):
            pass
            # x.append('n')       #No sample since no dictionary
            # x.append(x[1])

            # #Get annotation


            # outFileSampleAll.write(line.rstrip() + '\t' + 'n' + '\t' +x[1] + '\n')
            # continue 
        else:
            print('Done ', current_chr)
            current_chr = x[3]
            chr_name = x[3]
            with open(os.path.realpath(sys.argv[4]) + '/my_dict_' + current_chr + '.json', 'r') as f:
                start_time = time.time()
                datastore = json.load(f)
                print ('Load ' + current_chr + ' done', time.time() - start_time)
    
    pos_snp = []
    var = []
    target_combination = []
    pos_snp_chr = []
    set_list = []
    target_string = x[2]
    if x[6] == '-':
        target_string = target_string[::-1]
    bulge_found = 0 
    for pos, char in enumerate(target_string):
        if char == '-':
            bulge_found = bulge_found + 1 
        if char in iupac_code:
            iupac_pos = str(int(x[4]) + pos + 1 - bulge_found)
            try:
                a = (datastore[chr_name + ',' + iupac_pos])   #NOTE se non ha samples, ritorna ;ref,var
                
                ref_char = a.split(';')[-1].split(',')[0]
                var_char = a.split(';')[-1].split(',')[1]

                if x[6] == '-':
                    ref_char = rev_comp(ref_char)
                    var_char = rev_comp(var_char)

                a = a.split(';')[0]
                pos_snp.append(pos)
                pos_snp_chr.append(iupac_pos)
                var.append((var_char, ref_char))
            except Exception as e:      #NOTE this error can occure if i have an IUPAC in a target that has no vcf file
                print(e)
                print('Error at ' + line.rstrip() + ', with char ' + char + ', at pos ', iupac_pos)
                a = []
                #sys.exit()
                total_error = total_error + 1
            if a:
                set_list.append(set(a.split(',')))
            else:
                set_list.append(set())
    #Get Union of all samples
    union_sample = list(set().union(*set_list))
    if union_sample:
        x.append(','.join(union_sample))
    else:
        x.append('n')
    x.append(x[1])

    #Annotate target
    visited_pop = []
    visited_superpop = []

    #inserisco la key nel dict se non presente e creo la sua matrice
    if(str(x[1]) not in guideDict.keys()):
        guideDict[str(x[1])] = {}
        guideDict[str(x[1])]['targets'] = {}
        guideDict[str(x[1])]['targets'] = [0]*10

        count_unique_for_guide[str(x[1])] = dict()
        count_unique_for_guide[str(x[1])]['targets'] = [0]*10

        count_sample[str(x[1])] = dict()
        count_pop[str(x[1])] = dict()
        count_superpop[str(x[1])] = dict()

        for item in annotationsSet:
            guideDict[str(x[1])][item]= {}
            guideDict[str(x[1])][item] = [0]*10

            count_unique_for_guide[str(x[1])][item] = [0]*10
    
    #conto i target generali per mm threshold
    totalDict['targets'][int(x[mm_pos])] += 1
    guideDict[str(x[1])]['targets'][int(x[mm_pos])] += 1

    if summary_barplot_from_total:
        if x[vu_pos] == 'y': 
            count_unique['targets'][int(x[mm_pos])] += 1
            count_unique_for_guide[str(x[1])]['targets'][int(x[mm_pos])] += 1
    
    if summary_samples:
        for sample in x[-2].split(','):
            if sample == 'n':
                continue
            #Initialization if sample, pop or superpop not in dict
            if sample not in count_sample[x[1]]:
                count_sample[x[1]][sample] = {'targets': [0]*10}
                for item in annotationsSet:
                    count_sample[x[1]][sample][item] = [0]*10
                if dict_sample_to_pop[sample] not in count_pop[x[1]]:
                    count_pop[x[1]][dict_sample_to_pop[sample]] = {'targets': [0]*10}
                    for item in annotationsSet:
                        count_pop[x[1]][dict_sample_to_pop[sample]][item] = [0]*10
                if dict_pop_to_sup[dict_sample_to_pop[sample]] not in count_superpop[x[1]]:
                    count_superpop[x[1]][dict_pop_to_sup[dict_sample_to_pop[sample]]] = {'targets': [0]*10}
                    for item in annotationsSet:
                        count_superpop[x[1]][dict_pop_to_sup[dict_sample_to_pop[sample]]][item] = [0]*10
            #Add +1 to targets
            count_sample[x[1]][sample]['targets'][int(x[mm_pos])] += 1
            if dict_sample_to_pop[sample] not in visited_pop:
                visited_pop.append(dict_sample_to_pop[sample])
                count_pop[x[1]][dict_sample_to_pop[sample]]['targets'][int(x[mm_pos])] += 1
            if dict_pop_to_sup[dict_sample_to_pop[sample]] not in visited_superpop:
                visited_superpop.append(dict_pop_to_sup[dict_sample_to_pop[sample]])
                count_superpop[x[1]][dict_pop_to_sup[dict_sample_to_pop[sample]]]['targets'][int(x[mm_pos])] += 1
        visited_pop = []
        visited_superpop = []
    
    #faccio match su albero
    foundAnnotations = sorted(annotationsTree[int(x[4]):(int(x[4])+int(len(x[1]))+1)])
    string_annotation = []
    found_bool = False
    for found in range(0, len(foundAnnotations)):
        guide = foundAnnotations[found].data
        guideSplit = guide.split('\t')
        # print(guide, str(guideSplit[0]), str(x[3]))
        if(str(guideSplit[0]) == str(x[3])):
            found_bool = True
            #outFileTargets.write(line.rstrip() + '\t' + str(guideSplit[1]) + "\n")
            string_annotation.append(str(guideSplit[1]))
            guideDict[str(x[1])][guideSplit[1]][int(x[mm_pos])] += 1
            totalDict[guideSplit[1]][int(x[mm_pos])] += 1
            
            if summary_barplot_from_total:
                if x[vu_pos] == 'y':
                    count_unique[guideSplit[1]][int(x[mm_pos])] += 1
                    count_unique_for_guide[str(x[1])][guideSplit[1]][int(x[mm_pos])] += 1
            
            if summary_samples:
                for sample in x[-2].split(','):
                    if sample == 'n':
                        continue
                    #Add +1 to annotation
                    count_sample[x[1]][sample][guideSplit[1]][int(x[mm_pos])] += 1
                    if dict_sample_to_pop[sample] not in visited_pop:
                        visited_pop.append(dict_sample_to_pop[sample])
                        count_pop[x[1]][dict_sample_to_pop[sample]][guideSplit[1]][int(x[mm_pos])] += 1
                    if dict_pop_to_sup[dict_sample_to_pop[sample]] not in visited_superpop:
                        visited_superpop.append(dict_pop_to_sup[dict_sample_to_pop[sample]])
                        count_superpop[x[1]][dict_pop_to_sup[dict_sample_to_pop[sample]]][guideSplit[1]][int(x[mm_pos])] += 1
                visited_pop = []
                visited_superpop = []
    if not found_bool:
        x.append('n')
        #outFileTargets.write(line.rstrip() + '\tn\n')
    else:
        x.append(','.join(string_annotation))
        #outFileTargets.write(line.rstrip() + '\t' + ','.join(string_annotation) + '\n')

    #Save union samples + annotation
    
    outFileSampleAll.write(line.rstrip() + '\t' + '\t'.join(x[-3:]) + '\n')
    
    #Create all combinations
    for i in itertools.product(*var):
        t = list(target_string)
        for p, el in enumerate(pos_snp):
            t[el] = i[p]
        target_combination.append(''.join(t))
    
    samples_already_assigned = set()
    
    for t in target_combination:
        set_list2 = []
        final_result = x.copy()
        for ele_pos,p in enumerate(pos_snp_chr):
            #print('pos_chr', p)
            a = (datastore[chr_name + ',' + p])
            #print('a', a)
        
            samples = a.split(';')[0] #a[:-4] 
            
            ref = a.split(';')[-1].split(',')[0]
            var = a.split(';')[-1].split(',')[1]
            if x[6] == '-':
                ref = rev_comp(ref)
                var = rev_comp(var)
            # if int(p) == 10353471 or int(p) == 10353474:
                # print(p)
                # print('final result', final_result)
                # print('Samp, ref, var: ',samples, ref, var)
            #print('char in pos',t[pos_snp[ele_pos]].upper())
            if t[pos_snp[ele_pos]].upper() == var:      
                if samples:
                    set_list2.append(set(samples.split(',')))
                else:
                    #print('Error None ', line, a)
                    set_list2.append(set())
                #     #returned_none = True 
            # if int(p) == 10353471 or int(p) == 10353474:
                # print('Set list2', set_list2 )
        if set_list2:
            #print('setlist2', set_list2)
            common_samples = set.intersection(*set_list2)
            common_samples = common_samples - samples_already_assigned
            # print('common samples', common_samples)
            samples_already_assigned = samples_already_assigned.union(common_samples)
            # print('samp already assigned', samples_already_assigned)
            # print('common_smples', common_samples)
            if common_samples:
                final_result[-3] = ','.join(common_samples)
            else:
                # final_result.append('No common samples')
                final_result = []                       #DO not save results without samples
        else:
            # final_result.append('No samples')         #DO not save results without samples
            final_result = []
        # print('final_res', final_result)
        if x[6] == '-':
            t = t[::-1]
        if final_result:
            final_result[2] = t
            outFileSample.write('\t'.join(final_result) + '\n') #final_result[1].replace('-','') for better grep
        
        #print(final_result)
    lines_processed +=1
    if lines_processed % (mod_tot_line) == 0:
        print('Annotation: Total progress ' + str(round(lines_processed /total_line *100, 2)) + '%')


############ SAVE SUMMARIES ############


#scorro tutto il dict total e scrivo il summary, targets e ogni annotation
outFileSummary.write("-Summary_Total\n")
outFileSummary.write('targets' + '\t'+'\t'.join(str(i) for i in totalDict['targets'])+'\n')
for elem in sorted(totalDict.keys(), key = lambda s : s.lower()):
    if elem == 'targets':
        continue
    outFileSummary.write(str(elem)+'\t'+'\t'.join(str(i) for i in totalDict[elem])+'\n')


for elem in guideDict.keys():
    outFileSummary.write("-Summary_"+str(elem)+'\n')
    outFileSummary.write('targets'+'\t'+'\t'.join(str(i) for i in guideDict[elem]['targets'])+'\n')
    for item in sorted(annotationsSet, key = lambda s : s.lower()):
        outFileSummary.write(str(item)+'\t'+'\t'.join(str(i) for i in guideDict[elem][item])+'\n')

#Write summaries for samples, pop, superpop
if summary_samples:
    for guide in guideDict:
        #Save sample summary
        with open(outputFile + '.sample_annotation.' + guide +'.samples.txt', 'w+') as result:
            result.write('-Summary_Total\n')
            result.write('targets'+'\t'+'\t'.join(str(i) for i in guideDict[guide]['targets'])+'\n')
            for item in sorted(annotationsSet, key = lambda s : s.lower()):
                result.write(str(item)+'\t'+'\t'.join(str(i) for i in guideDict[guide][item])+'\n')
            #Write sample specific counting, put [0]*10 if sample was not found
            for sample in all_samples:
                result.write('-Summary_' + sample + '\n')
                try:
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in count_sample[guide][sample]['targets']) + '\n')
                except: #Sample not found in targets
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
                for item in sorted(annotationsSet, key = lambda s : s.lower()):
                    try:
                        result.write(item + '\t' + '\t'.join(str(i) for i in count_sample[guide][sample][item]) + '\n')
                    except:
                        result.write(item + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
        
        #Save population summary
        with open(outputFile + '.sample_annotation.' + guide +'.population.txt', 'w+') as result:
            result.write('-Summary_Total\n')
            result.write('targets'+'\t'+'\t'.join(str(i) for i in guideDict[guide]['targets'])+'\n')
            for item in sorted(annotationsSet, key = lambda s : s.lower()):
                result.write(str(item)+'\t'+'\t'.join(str(i) for i in guideDict[guide][item])+'\n')
            #Write population specific counting, put [0]*10 if sample was not found
            for population in set(all_pop):
                result.write('-Summary_' + population + '\n')
                try:
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in count_pop[guide][population]['targets']) + '\n')
                except: #Sample not found in targets
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
                for item in sorted(annotationsSet, key = lambda s : s.lower()):
                    try:
                        result.write(item + '\t' + '\t'.join(str(i) for i in count_pop[guide][population][item]) + '\n')
                    except:
                        result.write(item + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
        
        #Save superpopulation summary
        with open(outputFile + '.sample_annotation.' + guide +'.superpopulation.txt', 'w+') as result:
            result.write('-Summary_Total\n')
            result.write('targets'+'\t'+'\t'.join(str(i) for i in guideDict[guide]['targets'])+'\n')
            for item in sorted(annotationsSet, key = lambda s : s.lower()):
                result.write(str(item)+'\t'+'\t'.join(str(i) for i in guideDict[guide][item])+'\n')
            #Write superpopulation specific counting, put [0]*10 if sample was not found
            for superpop in superpopulation:
                result.write('-Summary_' + superpop + '\n')
                try:
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in count_superpop[guide][superpop]['targets']) + '\n')
                except: #Sample not found in targets
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
                for item in sorted(annotationsSet, key = lambda s : s.lower()):
                    try:
                        result.write(item + '\t' + '\t'.join(str(i) for i in count_superpop[guide][superpop][item]) + '\n')
                    except:
                        result.write(item + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')


#Write sumref for barplot for targets in top1 form of var/ref search
if summary_barplot_from_total:
    with open(outputFile + '.sumref.Annotation.summary.txt', 'w+') as result:
        result.write('-Summary_Total\n')
        result.write('targets'+'\t'+'\t'.join(str(i - count_unique['targets'][pos]) for pos,i in enumerate(totalDict['targets'])) + '\n')
        for elem in sorted(annotationsSet, key = lambda s : s.lower()):
            result.write(str(elem)+'\t'+'\t'.join(str(i - count_unique[elem][pos]) for pos, i in enumerate(totalDict[elem]))+'\n')
        for guide in count_unique_for_guide:
            result.write('-Summary_' + guide + '\n')
            result.write('targets' + '\t' + '\t'.join(str(i - count_unique_for_guide[guide]['targets'][pos]) for pos,i in enumerate(guideDict[guide]['targets'])) + '\n')
            for annotation in sorted(annotationsSet, key = lambda s : s.lower()):
                result.write(annotation + '\t' + '\t'.join(str(i - count_unique_for_guide[guide][annotation][pos]) for pos, i in enumerate(guideDict[guide][annotation])) + '\n')
if total_error > 0:
    print('Skipped SNP:', total_error)
print('Annotation: Total progress 100%')
print("ANNOTATION COMPLETED IN: %s seconds" % (time.time() - start_time_total))
