#Script extract only the top X from all clusters
# argv1 is input file ordered in cluster
import sys
header = {'Bulge Type':0, '#Bulge Type':0, 'Bulge type':0,
        'crRNA':1, 'DNA':2,
        'Chromosome':3, 'Position':4, 'Direction':5,
        'Mismatches':6, 'Bulge Size':7, 'Total':8,'Min_mismatches':9, 'Max_mismatches':10,
        'PAM_disr':11, 'PAM_gen':12, 'Var_uniq':13, 'Samples':14}

top_x = 1
top_x_inserted = 0
with open(sys.argv[1]) as targets, open('extracted_top_' + str(top_x) + '.txt', 'w+') as result:
    line = targets.readline()
    if '#' in line:
        line = targets.readline().strip().split('\t')
    else:
        line = line.strip().split('t')
    prev_position = line[header['Position']]
    result.write('\t'.join(line) + '\n')
    top_x_inserted = top_x_inserted + 1
    for line in targets:
        line = line.strip().split('\t')
        current_pos = line[header['Position']]
        if prev_position == current_pos and top_x_inserted < top_x:
            top_x_inserted = top_x_inserted + 1
            result.write('\t'.join(line) + '\n')
        elif prev_position != current_pos:
            top_x_inserted = 1
            prev_position = current_pos
            result.write('\t'.join(line) + '\n')