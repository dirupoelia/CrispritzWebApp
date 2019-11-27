#Create summary count for each guide  -> Incorporated in new annotation in crispritz offline
#Input: result directory
#number mms
import os
import sys
from os.path import isfile, isdir

def createGuideSummary(column_string, job_id, mms, guide_row_list, result_directory):
    with open(result_directory + '/' + job_id + '.annotated.' + column_string[1] + '.txt') as file_count:
        content = file_count.read().strip().split('\n')
        index = [idx for idx, s in enumerate(content) if guide_row_list[0] in s][0]
        first_tab = content[index].find('\t')
        return column_string[0] +(content[index][first_tab:]) + '\n'

def createGuideSummaryRef(column_string, job_id, mms, guide_row_list, result_directory):
    with open(result_directory + '/' + job_id + '_ref.annotated.' + column_string[1] + '.txt') as file_count:
        content = file_count.read().strip().split('\n')
        index = [idx for idx, s in enumerate(content) if guide_row_list[0] in s][0]
        first_tab = content[index].find('\t')
        return column_string[0] +(content[index][first_tab:]) + '\n'


result_directory = sys.argv[1]       #Example Result/X2UEWL9HHB
job_id = result_directory.split('/')[1]
mms = int(sys.argv[2])
ref_result_dir = result_directory + '/ref'

if (isfile(result_directory + '/' + job_id + '.profile_complete.xls')):
    profile_file = result_directory + '/' + job_id + '.profile_complete.xls'
    profile_file_ref = ref_result_dir + '/' + job_id + '_ref.profile_complete.xls'
else:
    profile_file = result_directory + '/' + job_id + '.profile.xls'
    profile_file_ref = ref_result_dir + '/' + job_id + '_ref.profile.xls'

first_column = [['Total_exons', 'ExonsCount'], ['Total_introns', 'IntronsCount'], ['Total_ctcf', 'CTCFCount'], ['Total_dnase', 'DNAseCount'], ['Total_promoters', 'PromotersCount']]

#Create Summary count for each guide from enriched results
with open(profile_file) as p:
    all_guides = p.read().strip().split('\n')[1:]
for guide_row in all_guides:
    guide_row_list = guide_row.strip().split('\t')
    content = 'Total_targets' + '\t' + '\t'.join(guide_row_list[(mms+1)*(-1):]) + '\t' + '\t'.join('0' for i in range(10 - mms)) + '\n'
    for col in first_column:
        content = content + createGuideSummary(col, job_id, mms, guide_row_list, result_directory)
    with open(result_directory + '/' + job_id + '.annotated.' + guide_row_list[0] + '.SummaryCount.txt', 'w') as scg:
        scg.write(content.strip())

#Create Summary count for each guide from reference results #BUG if user did not select comparison option
with open(profile_file_ref) as p:
    all_guides = p.read().strip().split('\n')[1:]

for guide_row in all_guides:
    guide_row_list = guide_row.strip().split('\t')
    content = 'Total_targets' + '\t' + '\t'.join(guide_row_list[(mms+1)*(-1):]) + '\t' + '\t'.join('0' for i in range(10 - mms)) + '\n'
    for col in first_column:
        content = content + createGuideSummaryRef(col, job_id, mms, guide_row_list, ref_result_dir)
    with open(result_directory + '/ref/'+ job_id +'_ref.annotated.' + guide_row_list[0] + '.SummaryCount.txt', 'w') as scg:
        scg.write(content.strip())



