'''
Generate barplot with population distribution from the summary_by_sample.GUIDE.superpopulation.txt file. Create a barplot for each mm (soon to be total) value
'''

# argv 1 is jobid.sample_annotation.GUIDE.superpopulation.txt
# argv 2 is total value
import math
import matplotlib
matplotlib.use("TkAgg")
matplotlib.use('Agg')

from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
import pandas as pd
from math import pi
import scipy.spatial.distance as sp
import numpy as np
import sys
from itertools import islice
import glob
import warnings
import os
from os import listdir
from os.path import isfile, join
warnings.filterwarnings("ignore")

from operator import itemgetter


plt.style.use('seaborn-poster')
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

guide = sys.argv[1].split('.')[-3]
barplot_values = dict()
total = int(sys.argv[2])
max_value = 0
with open(sys.argv[1]) as summary:
    for line in summary:
        if '-Summary_' in line:
            if '_Total' in line:
                continue
            value = int(next(summary).strip().split('\t')[total + 1])
            barplot_values[line.strip().split('_')[-1]] = value        #+1 to skip label -> targets 0 1 2 81 980 0 0 0 0 0
            if value > max_value:
                max_value = value

ind = np.arange(0, len(barplot_values.keys()), 1)       #[0 1 2 3 4]
no_result = False
try:
    y_range = np.arange(0, max_value + math.ceil(max_value/10), math.ceil(max_value/5))
except:
    y_range = np.arange(0,1,1)
    no_result = True
width = 0.5


p1 = plt.bar(ind, barplot_values.values(), width, color=['purple', 'yellow', 'green', 'blue', 'red'], align='edge')       #color = '#67a9cf'


# plt.legend(p1[0], ('Reference Genome'), fontsize=30)

plt.title('Targets found in each Superpopulation - ' + str(total) + ' Mismatches + Bulges', size=25)

if no_result:
    plt.annotate('No targets found with ' + str(total)  + ' mismatches + bulges', (2.5,0) ,size = 22, ha = 'center', va = 'center')  #2.5 is x position
    sys.exit()


plt.xticks(ind+0.25, barplot_values.keys(), size=25)
plt.yticks(y_range, size=22)

plt.tight_layout()
plt.subplots_adjust(top=0.95, bottom=0.06, left=0.1, right=0.99)
plt.savefig("populations_distribution_" + guide + '_' + str(total) + "total" + ".png", format='png')