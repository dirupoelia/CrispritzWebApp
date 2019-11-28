#!/usr/bin/env python

from intervaltree import Interval, IntervalTree
import sys
import time
import concurrent.futures

print("READING INPUT FILES")

#READ INPUT FILES
annotationFile = sys.argv[1] #file with annotation
resultsFile = sys.argv[2] #file with results from search
outputFile = sys.argv[3] #file with annotated results
profile_file = sys.argv[4]

#OPEN INPUT FILES AND PREPARE OUTPUT FILE
inResult = open(resultsFile, "r")  # resultfile open
inAnnotationFile = open(annotationFile, "r")  # file with annotations open
outFile = open(outputFile + '.Annotation.targets.txt', 'w')  # outfile open

#VARIABLE INIT
guideDict = {}
totalDict = {}

start_time = time.time()

print("EXECUTING PRELIMINARY OPERATIONS")

annotationsTree = IntervalTree()
annotationsSet = set()
guidesSet = set()       #NOTE/BUG if guide finds 0 targets, it will not be annotated -> resolved with line 133 try except

for line in inAnnotationFile:
    x = line.split('\t')
    x[3] = str(x[3]).rstrip("\n")
    annotationsTree[int(x[1]):int(x[2])] = str(x[0])+'\t'+str(x[3])
    annotationsSet.add(str(x[3]))

annotationsSet = sorted(annotationsSet)
next(inResult)
for line in inResult:
    x = line.split('\t')
    x[1] = str(x[1]).replace("-","")
    guidesSet.add(str(x[1]))

guidesSet = sorted(guidesSet)

totalDict['targets'] = [0]*10
for item in annotationsSet:
    totalDict[item] = [0]*10

for guide in guidesSet:
    guideDict[str(guide)] = {}
    for item in annotationsSet:
        guideDict[str(guide)][item]= {}
        guideDict[str(guide)][item] = [0]*10

print("PRELIMINARY OPERATIONS COMPLETED IN: %s seconds" % (time.time() - start_time))

start_time = time.time()

print("EXECUTING ANNOTATION")

outFile.write("#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tDirection\tMismatches\tBulge_Size\tAnnotation_Type\n")

inResult.seek(0)
next(inResult)

for line in inResult:
    x = line.split('\t')
    x[1] = str(x[1]).replace("-","")
    totalDict['targets'][int(x[6])] += 1
    foundAnnotations = sorted(annotationsTree[int(x[4]):(int(x[4])+int(len(x[1]))+1)])
    for found in range(0, len(foundAnnotations)):
        guide = foundAnnotations[found].data
        guideSplit = guide.split('\t')
        if(str(guideSplit[0]) == str(x[3])):
            outFile.write(line.rstrip() + '\t' + str(guideSplit[1]) + "\n")
            guideDict[str(x[1])][guideSplit[1]][int(x[6])] += 1
            totalDict[guideSplit[1]][int(x[6])] += 1
    

# for item in annotationsSet:
#     with open(outputFile+'.'+str(item)+'Count.txt','w') as tempItem:
#         for guide in guidesSet:
#             tempItem.write(str(guide))
#             for counter in range(0,10):
#                 tempItem.write('\t'+str(guideDict[str(guide)][item][counter]))
#             tempItem.write('\n')

with open(outputFile + '.Annotation.txt', 'w') as tempItem:

    for item in annotationsSet:
        
        tempItem.write('-' + item + '\n')
        for guide in guidesSet:
            tempItem.write(str(guide))
            for counter in range(0,10):
                tempItem.write('\t'+str(guideDict[str(guide)][item][counter]))
            tempItem.write('\n')
    tempItem.write('-Summary_Total\n')
    tempItem.write('targets')
    for counter in range(0,10):
        tempItem.write('\t'+str(totalDict['targets'][counter]))
    tempItem.write('\n')

    for item in annotationsSet:
        
        tempItem.write(str(item))
        for counter in range(0,10):
            tempItem.write('\t'+str(totalDict[item][counter]))
        tempItem.write('\n')
    
    
    with open(profile_file) as p:
        all_guides = p.read().strip().split('\n')
        mms = int(all_guides[0][all_guides[0][:all_guides[0].rfind('MM')].rfind('\t') + 1 :all_guides[0].rfind('MM')])
        all_guides = all_guides[1:]
    for guide_row in all_guides:
        guide_row_list = guide_row.strip().split('\t')
        tempItem.write('-Summary_' + guide_row_list[0] + '\n')
        content = 'targets' + '\t' + '\t'.join(guide_row_list[(mms+1)*(-1):]) + '\t' + '\t'.join('0' for i in range(9 - mms)) + '\n'
        # for item in annotationsSet:
        #     content = content + createGuideSummary(item, job_id,  guide_row_list, result_directory)
        tempItem.write(content)
        for item in annotationsSet:
            
            tempItem.write(str(item))
            for counter in range(0,10):
                try:
                    tempItem.write('\t'+str(guideDict[str(guide_row_list[0])][item][counter]))
                except:
                    tempItem.write('\t0')
            tempItem.write('\n')
              

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

print("ANNOTATION COMPLETED IN: %s seconds" % (time.time() - start_time))
