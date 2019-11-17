''''
Lo script deve, per ogni sample, contare il numero di target trovati
(eg. il sample HG01432 ha due targets), e salvare il risultato in un file
(Ogni riga è del tipo 'HG01432\t2\n').
 Il nome e il numero dei diversi samples non si sa a priori, dipende dal tipo di ricerca fatta.
'''

import os

os.system("cat esempio_samples.txt | cut -d$'\t' -f15 > only_samples.txt")

print("cat done")

sample_file = open('only_samples.txt', 'r')

sample_file.readline()

samples = dict({})
nline = 0



for line in sample_file:
    nline=nline+1

    if line[:-1] != "No common samples" and line[:-1] != "No samples" :

        words =line[:-1].split(sep=',')
        for word in words:
            if samples.keys().__contains__(word):
                samples[word] = samples[word]+1

            else:
                samples[word] = 1


#print(all_samples)
print("numero righe = "+ str(nline))
sample_file.close()

print("firs part done")

sample_file = open('only_samples.txt', 'w')
sample_file.writelines("Samples\tsample count\n")

for sample in samples.keys():

    sample_file.writelines(str(sample)+"\t"+str(samples[sample])+"\n")


sample_file.close()

print("all done")