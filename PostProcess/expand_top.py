#Script for expanding the iupac in all possible combination of the ref/alt nucleotide and 
#write the corresponding sample

#argv1 is extracted top file
#argv 2 is dictionary
import sys
import itertools

header = {'Bulge Type':0, '#Bulge Type':0, 'Bulge type':0,
        'crRNA':1, 'DNA':2,
        'Chromosome':3, 'Position':4, 'Direction':5,
        'Mismatches':6, 'Bulge Size':7, 'Total':8,'Min_mismatches':9, 'Max_mismatches':10,
        'PAM_disr':11, 'PAM_gen':12, 'Var_uniq':13, 'Samples':14}

#TODO insert iupac set

with open(sys.argv[1]) as targets:
    for line in targets:
        line = line.strip().split('\t')
        target = []
        sub_str = ''
        for char in line[header['DNA']]:
            if char in iupac:
                #Estraggo dal dizionario ref e alt, li aggiungo a target come set
                target.append(sub_str)
                sub_str = ''
            else:
                sub_str = sub_str + ''
        if substring:
            target.append(substring)
        #do itertools
        #save corresponding samples
                
