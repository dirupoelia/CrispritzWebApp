#test1
#script per testare la lettura del file semicommon con pandas, creare una nuova colonna total, chr, pos corretta (ovver la pos senza i bulges),
# e vedere se è fattibile in termini di tempo e memoria -> non fattibile in termini di tempo

#test2
#Leggo il file riga per riga, aggiungo le colonne e salvo la lista in una lista, che poi ordino -> ok, 1gb input -> 1.5 min e 11 gb ram
# Input 1.2 Gb -> tempo 2 min; 11Gb RAM

#test 3
#Come test2, ma ogni lista è salvata in un dizionario con key = guide, per risolvere il problema di avere più guide in uno stesso cluster. 
#Ora se in una posizione ho due guide, creo due cluster separati
# Input 2.8 Gb -> 25 gb ram
# Problema con 5 gb input -> forse servono 50 Gb ram

#Test 4
# Uso tuple invece di liste, joino le parti delle lines che non uso, cambio str in int 
# Input 2.8 -> 17 Gb, doppio del tempo per clusterizzare, ma sempre sotto i 10 minuti
# Input di 5.6 gb -> non funziona
#sys1 è semicommon file
#Output column (not written): Bulge_type, Guide, Target, chr, pos, pos_cluster, direction, mms, bulge, total

#sys2 is 'addGuide' or 'no' -> only for web server
import time
import sys

start = time.time()
total_targets = []
guides_dict = dict()
addGuide = False                #Add real guide to last column for better grep
if 'addGuide' in sys.argv[:]:
    addGuide = True
result_name = sys.argv[1][:sys.argv[1].rfind('.')] + '.cluster.txt'
with open (sys.argv[1]) as targets:
    for line in targets:
        if '#' in line:
            continue
        line = line.strip().split('\t')
        line.append(str(int(line[6]) + int(line[7])))
        if line[5] == '+':
            if line[0] == 'DNA':
                # line.append(str(int(line[4]) + int(line[7])))
                line.insert(5, str(int(line[4]) + int(line[7])))
            else:
                # line.append(str(int(line[4]) - int(line[7])))
                line.insert(5,str(int(line[4]) - int(line[7])))
        else:
            # line.append(line[4])
            line.insert(5, line[4])
        try:
            guides_dict[line[1].replace('-','')].append(('\t'.join(line[:3]), line[3], int(line[4]), int(line[5]), '\t'.join(line[6:-1]), int(line[-1])))    #[('type\tguide\target', 'chr', pos, clusterpos, 'dir\tmm\tbul', tot)]
        except:
            guides_dict[line[1].replace('-','')] = [('\t'.join(line[:3]), line[3], int(line[4]), int(line[5]), '\t'.join(line[6:-1]), int(line[-1]))]
        #total_targets.append(line)
        
print('Created \'Total\' and \'Position Cluster\' columns:', time.time() - start)
start = time.time()
# total_targets.sort(key = lambda x: ( x[3] , int(x[-1]) ))
for k in guides_dict.keys():
    guides_dict[k].sort(key = lambda x: ( x[1] , x[3] ))
#total_targets.sort(key = lambda x: ( x[3] , int(x[5]) ))

print('Targets sorted:', time.time() - start)

print('Start clustering')
start_time = time.time()

with open(result_name, 'w+') as result:
    total_targets = []
    for k in guides_dict.keys():
        total_targets += guides_dict[k]
    total_list = []

    first_line = total_targets[0]
    # current_chr_pos = first_line[3] + ' ' + first_line[9]
    current_chr_pos = first_line[1] + ' ' + str(first_line[3])

    total_list.append([first_line])

    for line in total_targets[1:]:
        #if line[3] + ' ' + line[9] != current_chr_pos:
        if line[1] + ' ' + str(line[3]) != current_chr_pos:
            # total_list[-1].sort(key = lambda x: int(x[8]))
            total_list[-1].sort(key = lambda x: x[5])   #Order cluster by total
            total_list.append([line])
            # current_chr_pos = line[3] + ' ' + line[9]
            current_chr_pos = line[1] + ' ' + str(line[3])
        else:
            total_list[-1].append(line)     

    total_list[-1].sort(key = lambda x: x[5])

    total_list.sort(key = lambda x: x[0][5])        #Order all clusters by total of top1
    if addGuide:
        for cluster in total_list:
            for target in cluster:
                result.write('\t'.join(target) + '\t' + target[1].replace('-','') + '\n')
    else:
        for cluster in total_list:
            for target in cluster:
                result.write('\t'.join([str(x) for x in target]) + '\n')

print("Clustering runtime: %s seconds" % (time.time() - start_time))