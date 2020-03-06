import os
import sys

all_targets = []
alphabet = '-RYSWKMBDHVryswkmbdhvACGTacgt'
all_strings = []


with open (sys.argv[1]) as targets:
    for line in targets:
        if '#' in line:
            continue
        all_targets.append(line.strip().split('\t'))
        all_strings.append([line.strip().split('\t')[2], line.strip().split('\t')[2][5]])
        all_strings.sort(key=lambda word: [alphabet.index(c) for c in word[0]])
        # sorted(all_targets,  key=lambda word: [alphabet.index(c) for c in word[2]])
        all_targets.sort(key=lambda word: [alphabet.index(c) for c in word[2]])

for i in all_targets:
    print(i[2], i[5])
for i in all_strings:
    print(i)