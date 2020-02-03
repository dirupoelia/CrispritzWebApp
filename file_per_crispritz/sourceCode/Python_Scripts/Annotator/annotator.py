#!/usr/bin/env python


'''
Faster annotator
'''
from intervaltree import Interval, IntervalTree
import sys
import time
import concurrent.futures
import subprocess
print("READING INPUT FILES")

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

outFileTargets.write("#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tDirection\tMismatches\tBulge_Size\tAnnotation_Type\n")

inResult.seek(0)
next(inResult)

lines_processed = 0
for line in inResult:
    x = line.split('\t')
    x[1] = str(x[1]).replace("-","")
    #guidesSet.add(str(x[1]))
    #inserisco la key nel dict se non presente e creo la sua matrice
    if(str(x[1]) not in guideDict.keys()):
        guideDict[str(x[1])] = {}
        guideDict[str(x[1])]['targets'] = {}
        guideDict[str(x[1])]['targets'] = [0]*10
        for item in annotationsSet:
            guideDict[str(x[1])][item]= {}
            guideDict[str(x[1])][item] = [0]*10
    #conto i target generali per mm threshold
    totalDict['targets'][int(x[6])] += 1
    guideDict[str(x[1])]['targets'][int(x[6])] += 1
    #faccio match su albero
    foundAnnotations = sorted(annotationsTree[int(x[4]):(int(x[4])+int(len(x[1]))+1)])
    for found in range(0, len(foundAnnotations)):
        guide = foundAnnotations[found].data
        guideSplit = guide.split('\t')
        if(str(guideSplit[0]) == str(x[3])):
            outFileTargets.write(line.rstrip() + '\t' + str(guideSplit[1]) + "\n")
            guideDict[str(x[1])][guideSplit[1]][int(x[6])] += 1
            totalDict[guideSplit[1]][int(x[6])] += 1

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
