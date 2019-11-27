#test esempio, da integrare nel py principale

import itertools

target = 'ACGGATCG'
pos = [1,3,7]
var = [('C','T','G'), ('G','A'), ('G','T')]

target_combination = []
for i in itertools.product(*var):
    t = list(target)
    for p, el in enumerate(pos):
        t[el] = i[p]
    target_combination.append(''.join(t))

chr = '1'
set_list = []
pos_in_chr = [101, 103, 107]
line = []
for t in target_combination:
    line.append(t)
    for p in pos_in_chr:
        a = datastore['chr' + str(chr) + ',' + str(p)]
        samples = a[:-4]    #TODO modo migliore per selezionare i char ref e var dai samples, forse fare dict con ;
        ref = a[-3]
        var = a[-1]
        if samples:
            set_list.append(set(a.split(',')))
        else:
            #print('Error None ', line, a)
            set_list.append(set())
            #returned_none = True
    if set_list:
        common_samples = set.intersection(*set_list)
        if common_samples:
            line.append(','.join(common_samples))
        else:
            line.append('No common samples')
    else:
        line.append('No samples')
    print(line)