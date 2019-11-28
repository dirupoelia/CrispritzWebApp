#Script che crea la tabella Summary by Guide, dato in input un file targets.txt, conta il numero di targets trovato per
#ogni combinazione di
#mms-bulge. Inoltre, se è presente la colonna Var_uniq, calcola il numero di Var_uniq per quella categoria di mms-bulge

#Script che crea tabella summary by guide e summary by position.
#Dato in input un file in cluster, conta il numero trovato per ogni combinazione di mms-bulge. Se presente la colonna var_uniq,
#conta il numero di only_var targets per ogni mms-bulge.
# Given in input a targets.txt ordered by clusters, for each cluster (position) it saves: 
# -chr
# -pos
# -best target sequence
# -min mms of cluster
# -min bulge of cluster
# -Total targets with 0 mm 0 bulges
# -Total targets with 1 mm 0 bulges
# ...
# -Total targets with n mm 0 bulges
# -Total targets with 0 mm 1 bulges
# -Total targets with 1 mm 1 bulges
# ...
# -Total targets with n mm 1 bulges
# ...
# -Total targets with n mm b bulges

#Input file columns:
#BulgeType, Guide, Target, Chr, Position, Cluster Position, Direction, MM, Bulge,Total

#sys1 file risultati
# sys2 mms
# sys3 bulges DNA
# sys4 bulges RNA
# sys5 guide file
# sys6 is jobid
# sys7 is type of post-process done ('No' -> no post process done, cannot count uniq_var | 'Uniq' -> post process done, can count uniq_var)

import sys
import numpy as np
import pandas as pd

class Cluster:
    def __init__(self, info, count):
        self.info = info            #[chr, pos, target, min mms, min bulge]
        self.count = count          #[[0 0 0 0] [0 0 0 0] [0 0 0 0 ]] for 4 mms and 2 bulges
    
    def to_string(self):
        tmp = ''
        for t in self.count:
            for t_c in t:
                tmp += '\t' + str(t_c)
        return self.info + tmp

    

mms = int(sys.argv[2])
bulges_dna = int(sys.argv[3])
bulges_rna = int(sys.argv[4])
guide_file = sys.argv[5]
type_post = sys.argv[7]
bulge = bulges_dna
if bulges_rna > bulges_dna:
    bulge = bulges_rna
guide_dict = dict()
guide_d_cluster = dict()
with open (guide_file,'r') as all_guides:
    for line in all_guides:
        line = line.strip()
        #total_count_x, total_count_dna, total_count_rna,
        #total_count_x_uniq, total_count_dna_uniq, total_count_rna_uniq
        if type_post == 'Uniq':
            guide_dict[line] = [np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1)),
                                np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1))]
        else:
            guide_dict[line] = [np.zeros((mms + 1, 1)), np.zeros((mms + 1,bulges_dna + 1)), np.zeros((mms + 1,bulges_rna + 1))]
        guide_d_cluster[line] = []

#Fake first cluster
current_cluster = '-1'
mms_current_line = -1
bulge_current_line = -1

with open(sys.argv[1]) as targets:
    
    
    if type_post == 'Uniq':
        
        for line in targets:
            if '#' in line:
                continue
            line = line.strip().split('\t')
            #Summar by guide
            if line[0] == 'X':
                guide_dict[line[1].replace('-','')][0][int(line[7])][int(line[8])] += 1 
                if line[13] == 'y':
                    guide_dict[line[1].replace('-','')][3][int(line[7])][int(line[8])] += 1
            elif line[0] == 'DNA':
                guide_dict[line[1].replace('-','')][1][int(line[7])][int(line[8])] += 1
                if line[13] == 'y':
                    guide_dict[line[1].replace('-','')][4][int(line[7])][int(line[8])] += 1
            else:
                guide_dict[line[1].replace('-','')][2][int(line[7])][int(line[8])] += 1
                if line[13] == 'y':
                    guide_dict[line[1].replace('-','')][5][int(line[7])][int(line[8])] += 1
            
            #Summary by position
            if current_cluster == line[3] + ' ' + line[5]:
                mms_current_line = int(line[7])
                bulge_current_line = int(line[8])
                guide_d_cluster[line[1].replace('-','')][-1].count[bulge_current_line][mms_current_line] += 1 
            else:
                guide_d_cluster[line[1].replace('-','')].append(Cluster(line[3] + '\t' + line[5] + '\t' + line[2] + '\t' + line[7] + '\t' + line[8], [[0 for i in range (mms + 1)] for i in range (bulge + 1)] ))    
                current_cluster = line[3] + ' ' + line[5]
                mms_current_line = int(line[7])
                bulge_current_line = int(line[8])
                guide_d_cluster[line[1].replace('-','')][-1].count[bulge_current_line][mms_current_line] += 1 
        
        for guide in guide_dict.keys():
            tab_summary = pd.DataFrame(columns = ['Guide', 'Bulge Type', 'Bulge Size', 'Mismatches', 'Number of targets', 'Targets created by SNPs'])
            for m in range(mms + 1):
                for b_d in range(bulges_dna +1):
                    tab_summary =tab_summary.append({'Guide': guide, 'Bulge Type': 'DNA', 'Bulge Size': b_d, 'Mismatches': m, 'Number of targets': guide_dict[guide][1][m][b_d], 'Targets created by SNPs':guide_dict[guide][4][m][b_d]  }, ignore_index = True)            

                for b_r in range(bulges_rna +1):
                    tab_summary =tab_summary.append({'Guide': guide, 'Bulge Type': 'RNA', 'Bulge Size': b_r, 'Mismatches': m, 'Number of targets': guide_dict[guide][2][m][b_r], 'Targets created by SNPs': guide_dict[guide][5][m][b_r] }, ignore_index = True)

                tab_summary =tab_summary.append({'Guide': guide, 'Bulge Type': 'X', 'Bulge Size': 0, 'Mismatches': m, 'Number of targets': guide_dict[guide][0][m][0], 'Targets created by SNPs':guide_dict[guide][3][m][0] }, ignore_index = True)
            tab_summary.to_pickle(sys.argv[6] + '.summary_by_guide.' + guide +'.txt')
    else:
        for line in targets:
            if '#' in line:
                continue
            line = line.strip().split('\t')
            if line[0] == 'X':
                guide_dict[line[1].replace('-','')][0][int(line[7])][int(line[8])] += 1
            elif line[0] == 'DNA':
                guide_dict[line[1].replace('-','')][1][int(line[7])][int(line[8])] += 1
            else:
                guide_dict[line[1].replace('-','')][2][int(line[7])][int(line[8])] += 1

            #Summary by position
            if current_cluster == line[3] + ' ' + line[5]:
                mms_current_line = int(line[7])
                bulge_current_line = int(line[8])
                guide_d_cluster[line[1].replace('-','')][-1].count[bulge_current_line][mms_current_line] += 1 
            else:
                guide_d_cluster[line[1].replace('-','')].append(Cluster(line[3] + '\t' + line[5] + '\t' + line[2] + '\t' + line[7] + '\t' + line[8], [[0 for i in range (mms + 1)] for i in range (bulge + 1)] ))    
                current_cluster = line[3] + ' ' + line[5]
                mms_current_line = int(line[7])
                bulge_current_line = int(line[8])
                guide_d_cluster[line[1].replace('-','')][-1].count[bulge_current_line][mms_current_line] += 1    

        for guide in guide_dict.keys():    
            tab_summary = pd.DataFrame(columns = ['Guide', 'Bulge Type', 'Bulge Size', 'Mismatches', 'Number of targets'])
            for m in range(mms + 1):
                for b_d in range(bulges_dna +1):
                    tab_summary =tab_summary.append({'Guide': guide, 'Bulge Type': 'DNA', 'Bulge Size': b_d, 'Mismatches': m, 'Number of targets': guide_dict[guide][1][m][b_d] }, ignore_index = True)            

                for b_r in range(bulges_rna +1):
                    tab_summary =tab_summary.append({'Guide': guide, 'Bulge Type': 'RNA', 'Bulge Size': b_r, 'Mismatches': m, 'Number of targets': guide_dict[guide][2][m][b_r] }, ignore_index = True)

                tab_summary =tab_summary.append({'Guide': guide, 'Bulge Type': 'X', 'Bulge Size': 0, 'Mismatches': m, 'Number of targets': guide_dict[guide][0][m][0] }, ignore_index = True)
                tab_summary.to_pickle(sys.argv[6] + '.summary_by_guide.' + guide +'.txt')

for guide in guide_d_cluster.keys():
    with open(sys.argv[6] + '.summary_by_position.' + guide + '.txt', 'w+') as result:
        result.write('#Chromosome\tPosition\tBest Target\tMin Mismatch\tMin Bulge')
        for b in range(bulge + 1):
            for i in range(mms + 1):
                result.write('\tTargets ' + str(i) + 'MM' + str(b) + 'B' )
        result.write('\n')
        for i in guide_d_cluster[guide]: 
            result.write(i.to_string() + '\n')