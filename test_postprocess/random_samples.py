import random
import sys
import pandas as pd
import os

#For each population, count total sample values
pop_file = pd.read_excel(os.path.dirname(os.path.realpath(__file__)) + '/20130606_sample_info.xlsx')
all_samples = pop_file.Sample.to_list()
len_all_samples = len(all_samples)
with open(sys.argv[1]) as targets, open('ann.sample.txt', 'w+') as result:
    for line in targets:
        if '#' in line:
            continue
        line = line.strip().split('\t')

        if (random.randrange(0, 9) %2 == 0):
            a = []
            for i in range(random.randrange(1,9)):
                a.append(all_samples[random.randrange(0, len_all_samples -1)])
            line.append(','.join(a))
            result.write('\t'.join(line) + '\n')