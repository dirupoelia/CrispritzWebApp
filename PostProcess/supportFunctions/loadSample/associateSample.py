'''
Script that loads the association
SAMPLE -> POPULATION -> SUPERPOPULATION
for the given input file. The input file is a txt file with three columns, separated by a tabulation, where the first column
represents the sample ID, the second column the associated Population ID, and the third column the SUuperpopulation ID. The script
returns a dictionary sample_to_pop and pop_to_superpop, or None,None if input file does not exists or is in incorrect format
'''
import sys
import os
from os.path import isfile, isdir,join      

#argv 1 is input .txt, consisting of 3 columns for sample, population and superpopulation

def loadSampleAssociation(id_sample_file):
    '''
    Given in input a file, it checks for structure correctness and returns two dictionaries:
    - SAMPLE -> POPULATION
    - POPULATION -> SUPERPOPULATION
    '''
    if not isfile(id_sample_file):
        print('Warning! Input file does not exists')
        return None, None

    sample_to_pop = dict()
    pop_to_superpop = dict() 

    with open (id_sample_file) as in_file:
        #Check correct format of file
        line = next(in_file)
        if '#' in line:
            line = next(in_file)    #Skip header
        
        line = line.strip().split('\t')

        if len(line) != 3:
            print('Warning! The input file is not correctly formatted. Please provide a .txt with a column with SAMPLE_ID, POPULATION_ID, SUPERPOPULATION_ID')
            return None, None
        #Add info of first line
        sample_to_pop[line[0]] = line[1]
        pop_to_superpop[line[1]] = line[2]

        for line in in_file:
            line = line.strip().split('\t')
            sample_to_pop[line[0]] = line[1]
            pop_to_superpop[line[1]] = line[2]
    return sample_to_pop, pop_to_superpop

if __name__ == '__main__':
    loadSampleAssociation(sys.argv[1])
