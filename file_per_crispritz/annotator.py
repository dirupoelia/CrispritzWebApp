#!/usr/bin/env python


'''
Faster annotator
'''
from intervaltree import Interval, IntervalTree
import sys
import time
import concurrent.futures
import subprocess
import pandas as pd
import os
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
#profile_file = sys.argv[4]

#OPEN INPUT FILES AND PREPARE OUTPUT FILE
inResult = open(resultsFile, "r")  # resultfile open
inAnnotationFile = open(annotationFile, "r")  # file with annotations open
outFileTargets = open(outputFile + '.Annotation.targets.txt', 'w')  # outfile open
outFileSummary = open(outputFile + '.Annotation.summary.txt', 'w')  # outfile open

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

# annotationsSet = sorted(annotationsSet)


# next(inResult)
# for line in inResult:
#     x = line.split('\t')
#     x[1] = str(x[1]).replace("-","")
#     guidesSet.add(str(x[1]))

# guidesSet = sorted(guidesSet)

totalDict['targets'] = [0]*10
for item in annotationsSet:
    totalDict[item] = [0]*10

# for guide in guidesSet:
#     guideDict[str(guide)] = {}
#     guideDict['targets'] = [0]*10
#     for item in annotationsSet:
#         guideDict[str(guide)][item]= {}
#         guideDict[str(guide)][item] = [0]*10



print("PRELIMINARY OPERATIONS COMPLETED IN: %s seconds" % (time.time() - start_time))

start_time = time.time()

print("EXECUTING ANNOTATION")



inResult.seek(0)
header = next(inResult)
if 'Cluster Position' in header:
    mm_pos = 7
    outFileTargets.write(header.strip() + '\tAnnotation_Type\n')
    # if 'Real Guide' in header:
    #     outFileTargets.write("#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\tAnnotation_Type\n")
    # else:
    #     outFileTargets.write("#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\tReal Guide\tAnnotation_Type\n")

else:
    mm_pos = 6
    outFileTargets.write(header.strip() + '\tAnnotation_Type\n')
    # if 'Real Guide' in header:
    #     outFileTargets.write("#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tDirection\tMismatches\tBulge_Size\tReal Guide\tAnnotation_Type\n")
    # else:
    #     outFileTargets.write("#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tDirection\tMismatches\tBulge_Size\tAnnotation_Type\n")

if 'Samples' in header:
    print('samples')
    summary_samples = True
else:
    summary_samples = False
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





lines_processed = 0
for line in inResult:
    visited_pop = []
    visited_superpop = []
    
    x = line.split('\t')
    x[1] = str(x[1]).replace("-","")
    #guidesSet.add(str(x[1]))
    #inserisco la key nel dict se non presente e creo la sua matrice
    if(str(x[1]) not in guideDict.keys()):
        guideDict[str(x[1])] = {}
        guideDict[str(x[1])]['targets'] = {}
        guideDict[str(x[1])]['targets'] = [0]*10
        count_sample[str(x[1])] = dict()
        count_pop[str(x[1])] = dict()
        count_superpop[str(x[1])] = dict()

        for item in annotationsSet:
            guideDict[str(x[1])][item]= {}
            guideDict[str(x[1])][item] = [0]*10
        
    #conto i target generali per mm threshold
    totalDict['targets'][int(x[mm_pos])] += 1
    guideDict[str(x[1])]['targets'][int(x[mm_pos])] += 1

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
    for found in range(0, len(foundAnnotations)):
        guide = foundAnnotations[found].data
        guideSplit = guide.split('\t')
        if(str(guideSplit[0]) == str(x[3])):
            outFileTargets.write(line.rstrip() + '\t' + str(guideSplit[1]) + "\n")
            guideDict[str(x[1])][guideSplit[1]][int(x[mm_pos])] += 1
            totalDict[guideSplit[1]][int(x[mm_pos])] += 1
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

    lines_processed +=1
    if lines_processed % (mod_tot_line) == 0:
        print('Annotation: Total progress ' + str(round(lines_processed /total_line *100, 2)) + '%')


#scorro tutto il dict total e scrivo il summary, targets e ogni annotation
outFileSummary.write("-Summary_Total\n")
outFileSummary.write('targets' + '\t'+'\t'.join(str(i) for i in totalDict['targets'])+'\n')
for elem in sorted(totalDict.keys()):
    if elem == 'targets':
        continue
    outFileSummary.write(str(elem)+'\t'+'\t'.join(str(i) for i in totalDict[elem])+'\n')


for elem in guideDict.keys():
    outFileSummary.write("-Summary_"+str(elem)+'\n')
    outFileSummary.write('targets'+'\t'+'\t'.join(str(i) for i in guideDict[elem]['targets'])+'\n')
    for item in sorted(annotationsSet):
        outFileSummary.write(str(item)+'\t'+'\t'.join(str(i) for i in guideDict[elem][item])+'\n')

#Write summaries for samples, pop, superpop
if summary_samples:
    for guide in guideDict:
        #Save sample summary
        with open(outputFile + '.sample_annotation.' + guide +'.samples.txt', 'w+') as result:
            result.write('-Summary_Total\n')
            result.write('targets'+'\t'+'\t'.join(str(i) for i in guideDict[guide]['targets'])+'\n')
            for item in sorted(annotationsSet):
                result.write(str(item)+'\t'+'\t'.join(str(i) for i in guideDict[guide][item])+'\n')
            #Write sample specific counting, put [0]*10 if sample was not found
            for sample in all_samples:
                result.write('-Summary_' + sample + '\n')
                try:
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in count_sample[guide][sample]['targets']) + '\n')
                except: #Sample not found in targets
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
                for item in sorted(annotationsSet):
                    try:
                        result.write(item + '\t' + '\t'.join(str(i) for i in count_sample[guide][sample][item]) + '\n')
                    except:
                        result.write(item + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
        
        #Save population summary
        with open(outputFile + '.sample_annotation.' + guide +'.population.txt', 'w+') as result:
            result.write('-Summary_Total\n')
            result.write('targets'+'\t'+'\t'.join(str(i) for i in guideDict[guide]['targets'])+'\n')
            for item in sorted(annotationsSet):
                result.write(str(item)+'\t'+'\t'.join(str(i) for i in guideDict[guide][item])+'\n')
            #Write population specific counting, put [0]*10 if sample was not found
            for population in set(all_pop):
                result.write('-Summary_' + population + '\n')
                try:
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in count_pop[guide][population]['targets']) + '\n')
                except: #Sample not found in targets
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
                for item in sorted(annotationsSet):
                    try:
                        result.write(item + '\t' + '\t'.join(str(i) for i in count_pop[guide][population][item]) + '\n')
                    except:
                        result.write(item + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
        
        #Save superpopulation summary
        with open(outputFile + '.sample_annotation.' + guide +'.superpopulation.txt', 'w+') as result:
            result.write('-Summary_Total\n')
            result.write('targets'+'\t'+'\t'.join(str(i) for i in guideDict[guide]['targets'])+'\n')
            for item in sorted(annotationsSet):
                result.write(str(item)+'\t'+'\t'.join(str(i) for i in guideDict[guide][item])+'\n')
            #Write superpopulation specific counting, put [0]*10 if sample was not found
            for superpop in superpopulation:
                result.write('-Summary_' + superpop + '\n')
                try:
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in count_superpop[guide][superpop]['targets']) + '\n')
                except: #Sample not found in targets
                    result.write('targets' + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')
                for item in sorted(annotationsSet):
                    try:
                        result.write(item + '\t' + '\t'.join(str(i) for i in count_superpop[guide][superpop][item]) + '\n')
                    except:
                        result.write(item + '\t' + '\t'.join(str(i) for i in [0]*10) + '\n')

# for item in annotationsSet:
#     with open(outputFile+'.'+str(item)+'Count.txt','w') as tempItem:
#         for guide in guidesSet:
#             tempItem.write(str(guide))
#             for counter in range(0,10):
#                 tempItem.write('\t'+str(guideDict[str(guide)][item][counter]))
#             tempItem.write('\n')

# with open(outputFile + '.Annotation.txt', 'w') as tempItem:

#     for item in annotationsSet:
        
#         tempItem.write('-' + item + '\n')
#         for guide in guidesSet:
#             tempItem.write(str(guide))
#             for counter in range(0,10):
#                 tempItem.write('\t'+str(guideDict[str(guide)][item][counter]))
#             tempItem.write('\n')
#     tempItem.write('-Summary_Total\n')
#     tempItem.write('targets')
#     for counter in range(0,10):
#         tempItem.write('\t'+str(totalDict['targets'][counter]))
#     tempItem.write('\n')

#     for item in annotationsSet:
        
#         tempItem.write(str(item))
#         for counter in range(0,10):
#             tempItem.write('\t'+str(totalDict[item][counter]))
#         tempItem.write('\n')
    
    
#     with open(profile_file) as p:
#         all_guides = p.read().strip().split('\n')
#         mms = int(all_guides[0][all_guides[0][:all_guides[0].rfind('MM')].rfind('\t') + 1 :all_guides[0].rfind('MM')])
#         all_guides = all_guides[1:]
#     for guide_row in all_guides:
#         guide_row_list = guide_row.strip().split('\t')
#         tempItem.write('-Summary_' + guide_row_list[0] + '\n')
#         content = 'targets' + '\t' + '\t'.join(guide_row_list[(mms+1)*(-1):]) + '\t' + '\t'.join('0' for i in range(9 - mms)) + '\n'
#         # for item in annotationsSet:
#         #     content = content + createGuideSummary(item, job_id,  guide_row_list, result_directory)
#         tempItem.write(content)
#         for item in annotationsSet:
            
#             tempItem.write(str(item))
#             for counter in range(0,10):
#                 tempItem.write('\t'+str(guideDict[str(guide_row_list[0])][item][counter]))
#             tempItem.write('\n')
              

# tempItem = open(outputFile+'.'+'summaryCount.txt','w')
# tempItem.write('targets')
# for counter in range(0,10):
#     tempItem.write('\t'+str(totalDict['targets'][counter]))
# tempItem.write('\n')

# for item in annotationsSet:
#     tempItem.write(str(item))
#     for counter in range(0,10):
#         tempItem.write('\t'+str(totalDict[item][counter]))
#     tempItem.write('\n')
print('Annotation: Total progress 100%')
print("ANNOTATION COMPLETED IN: %s seconds" % (time.time() - start_time))
