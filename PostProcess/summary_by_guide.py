'''
Script for summary by guide. Takes in input the samples.all.txt and count the targets occurencies for every mm/bulge value.
For PAM Creation: if Var Unique is F --> target does not exists --> not counted
For PAM Disruption: if Var Unique is F --> count only for PAM Disruption; if Var Unique not F --> count for PAM Disruption and count target
'''

# sys1 samples.all.targets.txt
# sys2 mms
# sys3 bulges DNA
# sys4 bulges RNA
# sys5 guide file
# sys6 is jobid
# sys7 is type of post-process done ('No' -> no post process done, cannot count uniq_var | 'Uniq' -> post process done, can count uniq_var)

import sys
import numpy as np
import pandas as pd
import subprocess


mms = int(sys.argv[2])
bulges_dna = int(sys.argv[3])
bulges_rna = int(sys.argv[4])
guide_file = sys.argv[5]
type_post = sys.argv[7]
bulge = bulges_dna
if bulges_rna > bulges_dna:
    bulge = bulges_rna
guide_dict = dict()
count_disruption = dict()
count_creation = dict() #{GUIDE1 -> [0 0 0;0 0 0] per ogni categoria mms-bulge,}

with open (guide_file,'r') as all_guides:
    for line in all_guides:
        line = line.strip()
        if type_post == 'Uniq':
            guide_dict[line] = [np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1)),
                                np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1))]
            count_disruption[line] = [np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1))]
                #,np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1))]
            count_creation[line] = [np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1))]
                #,np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1))]
        else:   #TODO aggiungere nel caso di ricerca solo var
            guide_dict[line] = [np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1))]

with open(sys.argv[1]) as targets:    
    if type_post == 'Uniq':        
        for line in targets:            
            if '#' in line:
                continue
            line = line.strip().split('\t')
            #Summar by guide
            
            if line[14] == 'F':                 #Save PAM Disruption even if target does not really exists (F status)
                if line[12] != 'n':
                    if line[0] == 'X':
                        count_disruption[line[1].replace('-','')][0][int(line[7])][int(line[8])] += 1 
                    elif line[0] == 'DNA':
                        count_disruption[line[1].replace('-','')][1][int(line[7])][int(line[8])] += 1 
                    else:
                        count_disruption[line[1].replace('-','')][2][int(line[7])][int(line[8])] += 1
                continue


            if line[0] == 'X':
                guide_dict[line[1].replace('-','')][0][int(line[7])][int(line[8])] += 1 
                if line[14] == 'y':
                    guide_dict[line[1].replace('-','')][3][int(line[7])][int(line[8])] += 1
            elif line[0] == 'DNA':
                guide_dict[line[1].replace('-','')][1][int(line[7])][int(line[8])] += 1
                if line[14] == 'y':
                    guide_dict[line[1].replace('-','')][4][int(line[7])][int(line[8])] += 1
            else:
                guide_dict[line[1].replace('-','')][2][int(line[7])][int(line[8])] += 1
                if line[14] == 'y':
                    guide_dict[line[1].replace('-','')][5][int(line[7])][int(line[8])] += 1
            #Count pam creation or disruption when target exists (status not F)
            if line[14] != 'y':
                if line[12] != 'n':
                    if line[0] == 'X':
                        count_disruption[line[1].replace('-','')][0][int(line[7])][int(line[8])] += 1 
                    elif line[0] == 'DNA':
                        count_disruption[line[1].replace('-','')][1][int(line[7])][int(line[8])] += 1 
                    else:
                        count_disruption[line[1].replace('-','')][2][int(line[7])][int(line[8])] += 1 
            else:
                if line[13] != 'n':     #NOTE se ho una PAM creation nella scomposizione che però ha troppi mm, mi viene segnata anche se non esisterebbe.
                    if line[0] == 'X':
                        count_creation[line[1].replace('-','')][0][int(line[7])][int(line[8])] += 1 
                    elif line[0] == 'DNA':
                        count_creation[line[1].replace('-','')][1][int(line[7])][int(line[8])] += 1 
                    else:
                        count_creation[line[1].replace('-','')][2][int(line[7])][int(line[8])] += 1 
        
        for guide in guide_dict.keys():
            tab_summary = pd.DataFrame(columns = ['Guide', 'Bulge Type', 'Bulge Size', 'Mismatches', 'Number of Targets', 'Targets Created by SNPs', 'PAM Disruption', 'PAM Creation'])
            for m in range(mms + 1):
                for b_d in range(bulges_dna +1):
                    tab_summary =tab_summary.append({'Guide': guide, 'Bulge Type': 'DNA', 'Bulge Size': b_d, 'Mismatches': m, 'Number of Targets': guide_dict[guide][1][m][b_d], 'Targets Created by SNPs':guide_dict[guide][4][m][b_d], 'PAM Disruption':count_disruption[guide][1][m][b_d], 'PAM Creation':count_creation[guide][1][m][b_d]  }, ignore_index = True)            

                for b_r in range(bulges_rna +1):
                    tab_summary =tab_summary.append({'Guide': guide, 'Bulge Type': 'RNA', 'Bulge Size': b_r, 'Mismatches': m, 'Number of Targets': guide_dict[guide][2][m][b_r], 'Targets Created by SNPs': guide_dict[guide][5][m][b_r],'PAM Disruption':count_disruption[guide][2][m][b_r], 'PAM Creation':count_creation[guide][2][m][b_r] }, ignore_index = True)

                tab_summary =tab_summary.append({'Guide': guide, 'Bulge Type': 'X', 'Bulge Size': 0, 'Mismatches': m, 'Number of Targets': guide_dict[guide][0][m][0], 'Targets Created by SNPs':guide_dict[guide][3][m][0],  'PAM Disruption':count_disruption[guide][0][m][0], 'PAM Creation':count_creation[guide][0][m][0] }, ignore_index = True)
            tab_summary.to_pickle(sys.argv[6] + '.summary_by_guide.' + guide +'.txt')

    # else #TODO finire per var only search