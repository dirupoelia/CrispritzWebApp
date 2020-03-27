import os
import sys
from os.path import isfile, isdir,join      #for getting directories
from os import listdir                      #for getting directories
import pandas as pd


dir_path = os.path.dirname(os.path.realpath(__file__))

onlydir = [f for f in listdir(dir_path + '/Results/') if isdir(join(dir_path + '/Results/', f))]

col = 'Job\tGenSe\tGenId\tMM\tDNA\tRNA\tPAM\tGuide\tGecko\tComp'.split('\t')
a = pd.DataFrame(columns = col)
for job in onlydir:
    if os.path.exists(dir_path + '/Results/' + job + '/Params.txt'):
        with open(dir_path  + '/Results/' + job + '/Params.txt') as p:
            all_params = p.read()
            mms = (next(s for s in all_params.split('\n') if 'Mismatches' in s)).split('\t')[-1]
            genome_selected = (next(s for s in all_params.split('\n') if 'Genome_selected' in s)).split('\t')[-1]
            with open(dir_path  + '/Results/' + job + '/log.txt') as lo:
                all_log = lo.read()
            job_start = (next(s for s in all_log.split('\n') if 'Job\tStart' in s)).split('\t')[-1]
            if '+' in genome_selected:
                genome_selected = genome_selected.split('+')[0] + '+'
            dna = (next(s for s in all_params.split('\n') if 'DNA' in s)).split('\t')[-1]
            rna = (next(s for s in all_params.split('\n') if 'RNA' in s)).split('\t')[-1]
            genome_idx = (next(s for s in all_params.split('\n') if 'Genome_idx' in s)).split('\t')[-1]
            if genome_idx != 'None':
                genome_idx = 'X'
            pam = (next(s for s in all_params.split('\n') if 'Pam' in s)).split('\t')[-1]
            gecko = (next(s for s in all_params.split('\n') if 'Gecko' in s)).split('\t')[-1]
            comparison = (next(s for s in all_params.split('\n') if 'Ref_comp' in s)).split('\t')[-1]
            if os.path.exists(dir_path + '/Results/' + job + '/guides.txt'):
                with open(dir_path  + '/Results/' + job + '/guides.txt') as g:
                    n_guides = str(len(g.read().strip().split('\n')))
            else:
                n_guides ='n/a'
            a = a.append({'Job':job, 'GenSe':genome_selected, 'GenId':genome_idx, 'MM':mms, 'DNA':dna,
            'RNA':rna, 'PAM':pam,'Guide':n_guides,'Gecko':gecko,'Comp':comparison, 'Start':job_start}, ignore_index = True)
a = a.sort_values(['MM','DNA','RNA'],ascending = [True, True, True])
print(a)
