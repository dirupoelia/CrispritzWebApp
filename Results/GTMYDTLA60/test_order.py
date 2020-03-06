import sys
import os

custom_sort = {'t':0, 'a':1 , 'A':2, 'C':3, 'G':4, 'T':5}
all_targets = []
with open(sys.argv[1]) as targets:
    for line in targets:
        line = line.strip()
        all_targets.append(line.split('\t'))

all_targets.sort(key = lambda x : (x[7], x[5], custom_sort[x[2][1]]))
print(all_targets)