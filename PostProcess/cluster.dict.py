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
#sys1 è target file
#sys2 is 'addGuide' or 'no' -> only for web server, only for search with only ref
#sys3 is True to keep column 5 (Pos cluster) and 9 (Total) and added guide, False to do clusterization but do not report the added columns
#sys4 is True if cluster only (no append of Total column or adding of Cluster position, because already present), False otherwise
#sys5 is guides.txt for slow clustering
#Output column (not written): Bulge_type, Guide, Target, chr, pos, pos_cluster (optional), direction, mms, bulge, total(optional), real guide(optional)

#NOTE with new search, cluster position is already present, so code for that column is commented

import time
import sys
import subprocess
import os 
MAX_LIMIT = 50000000

pam_at_end = True
guides_to_check = set()        #Set of error guides, do not do computation on them
if os.path.exists('./guides_error.txt'):
    with open('guides_error.txt') as g_e:
        for line in g_e:
            line = line.strip()
            guides_to_check.add(line)
            if line[0] == 'N':
                pam_at_end = False
with open(sys.argv[5]) as guides:
    for guide in guides:
        if guide[0] == 'N':
            pam_at_end = False

strand_to_check = '-'
if pam_at_end:
    strand_to_check = '+'

start = time.time()
total_targets = []
guides_dict = dict()
addGuide = False                #Add real guide to last column for better grep
if 'addGuide' in sys.argv[:]:
    addGuide = True
if sys.argv[3] == 'True':
    keep_columns = True
else:
    keep_columns = False

result_name = sys.argv[1][:sys.argv[1].rfind('.')] + '.cluster.txt'
cluster_only = False
if sys.argv[4] == 'True':
    cluster_only = True

process = subprocess.Popen(['wc', '-l', sys.argv[1]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = process.communicate()
total_line = int(out.decode('UTF-8').split(' ')[0])
if total_line > MAX_LIMIT:
    print('Max limit file reached, using clustering by single guide')
    ok_guides = []
    write_header = True
    with open(sys.argv[5]) as guides:
        for guide in guides:
            if guide in guides_to_check:
                continue
            current_count = 0
            cluster_ok = True
            guide = guide.strip()
            #DO SLOW CLUSTERING       
            with open (sys.argv[1]) as targets:
                for line in targets:
                    line = line.strip().split('\t')
                    if '#' in line[0] or line[1].replace('-','') != guide:
                        continue
                    if not cluster_only:
                        line.append(str(int(line[7]) + int(line[8])))   #Total column
                        
                        # if line[5] == strand_to_check:  #Cluster Position column
                        #     if line[0] == 'DNA':
                        #         # line.append(str(int(line[4]) + int(line[7])))
                        #         line.insert(5, str(int(line[4]) + int(line[7])))
                        #     else:
                        #         # line.append(str(int(line[4]) - int(line[7])))
                        #         line.insert(5,str(int(line[4]) - int(line[7])))
                        # else:
                        #     # line.append(line[4])
                        #     line.insert(5, line[4])
                        
                    current_count += 1
                    if current_count > MAX_LIMIT:
                        print('The guide ' + guide + ' has more than ' + str(MAX_LIMIT) + ' targets. Skipping...')
                        with open('./guides_error.txt', 'a+') as guides_error:
                            guides_error.write(guide + '\n')
                        cluster_ok = False
                        del guides_dict[guide]
                        break
                    try:
                        guides_dict[line[1].replace('-','')].append(('\t'.join(line[:3]), line[3], int(line[4]), int(line[5]), str(line[6]), int(line[7]), int(line[8]), int(line[9]), '\t'.join(line[10:])))    #[('type\tguide\target', 'chr', pos, clusterpos, 'dir', mm, bul, tot)]
                    except:
                        guides_dict[line[1].replace('-','')] = [('\t'.join(line[:3]), line[3], int(line[4]), int(line[5]), str(line[6]), int(line[7]), int(line[8]), int(line[9]),'\t'.join(line[10:]) )]
                    #total_targets.append(line)
            if not cluster_ok:
                continue
            if not cluster_only:       
                print('Created \'Total\' and \'Position Cluster\' columns:', time.time() - start)
            else:
                print('Loaded targets: ', time.time() - start)
            start = time.time()
            # total_targets.sort(key = lambda x: ( x[3] , int(x[-1]) ))
            for k in guides_dict.keys():
                guides_dict[k].sort(key = lambda x: ( x[1] , x[3] ))    #Order by chr_clusterpos
            #total_targets.sort(key = lambda x: ( x[3] , int(x[5]) ))

            print('Targets sorted:', time.time() - start)

            print('Start clustering')
            start_time = time.time()

            with open(result_name, 'a+') as result:
                if write_header:    
                    if 'total' not in sys.argv[:]:      #TODO fix for offline release, praticamente se sto facendo cluster su total.txt metto l'header custom
                        if addGuide:
                            if keep_columns:
                                result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\tReal Guide\n')
                            else:
                                result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tDirection\tMismatches\tBulge_Size\tReal Guide\n')
                        else:
                            if keep_columns:
                                result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\n')
                            else:
                                result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tDirection\tMismatches\tBulge_Size\n')
                    else:
                        result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\tMin_mismatches\tMax_mismatches\tPam_disr\tPAM_gen\tVar_uniq\n')
                    write_header = False
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
                        total_list[-1].sort(key = lambda x: (x[7], x[5]))   #Order cluster by total and mms
                        total_list.append([line])
                        # current_chr_pos = line[3] + ' ' + line[9]
                        current_chr_pos = line[1] + ' ' + str(line[3])
                    else:
                        total_list[-1].append(line)     

                total_list[-1].sort(key = lambda x: (x[7], x[5]))       #Order last cluster by total and mms

                total_list.sort(key = lambda x: x[0][7])        #Order all clusters by total of top1
                if addGuide:
                    if keep_columns:
                        for cluster in total_list:
                            for target in cluster:
                                result.write('\t'.join(str(x) for x in target).strip() + '\t' + target[0].split('\t')[1].replace('-','') + '\n')
                    else:
                        for cluster in total_list:
                            for target in cluster:
                                result.write('\t'.join(str(x) for x in target[:3]) + '\t' + '\t'.join(str(x) for x in target[4:7]) +'\t' + target[8].strip() + '\t' + target[0].split('\t')[1].replace('-','') + '\n')

                else:
                    if keep_columns:
                        for cluster in total_list:
                            for target in cluster:
                                result.write('\t'.join([str(x) for x in target]).strip() + '\n')
                    else:
                        for cluster in total_list:
                            for target in cluster:
                                result.write('\t'.join(str(x) for x in target[:3]) + '\t' + '\t'.join(str(x) for x in target[4:7]) +'\t' + target[8].strip() + '\n')
            del guides_dict[guide]
            ok_guides.append(guide)
            print("Clustering runtime: %s seconds" % (time.time() - start_time))
    with open(sys.argv[5], 'w') as guides:
        guides.write('\n'.join(ok_guides))        

else:
    #####DO FAST CLUSTERING
    with open (sys.argv[1]) as targets:
        for line in targets:
            if '#' in line:
                continue
            line = line.strip().split('\t')
            if line[1].replace('-','') in guides_to_check:
                continue
            if not cluster_only:
                line.append(str(int(line[7]) + int(line[8])))   #Add Total column
                # if line[5] == strand_to_check:                  #Add Cluster Position column
                #     if line[0] == 'DNA':
                #         # line.append(str(int(line[4]) + int(line[7])))
                #         line.insert(5, str(int(line[4]) + int(line[7])))
                #     else:
                #         # line.append(str(int(line[4]) - int(line[7])))
                #         line.insert(5,str(int(line[4]) - int(line[7])))
                # else:
                #     # line.append(line[4])
                #     line.insert(5, line[4])
            try:
                guides_dict[line[1].replace('-','')].append(('\t'.join(line[:3]), line[3], int(line[4]), int(line[5]), str(line[6]), int(line[7]), int(line[8]), int(line[9]), '\t'.join(line[10:])))    #[('type\tguide\target', 'chr', pos, clusterpos, 'dir', mm, bul, tot)]
            except:
                guides_dict[line[1].replace('-','')] = [('\t'.join(line[:3]), line[3], int(line[4]), int(line[5]), str(line[6]), int(line[7]), int(line[8]), int(line[9]),'\t'.join(line[10:]) )]
            #total_targets.append(line)
    if not cluster_only:       
        print('Created \'Total\' and \'Position Cluster\' columns:', time.time() - start)
    else:
        print('Loaded targets: ', time.time() - start)
    start = time.time()
    # total_targets.sort(key = lambda x: ( x[3] , int(x[-1]) ))
    for k in guides_dict.keys():
        guides_dict[k].sort(key = lambda x: ( x[1] , x[3] ))        #Order by chr_clusterpos
    #total_targets.sort(key = lambda x: ( x[3] , int(x[5]) ))

    print('Targets sorted:', time.time() - start)

    print('Start clustering')
    start_time = time.time()

    with open(result_name, 'w+') as result:
        if 'total' not in sys.argv[:]:      #TODO fix for offline release, praticamente se sto facendo cluster su total.txt metto l'header custom
            if addGuide:
                if keep_columns:
                    result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\tReal Guide\n')
                else:
                    result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tDirection\tMismatches\tBulge_Size\tReal Guide\n')
            else:
                if keep_columns:
                    result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\n')
                else:
                    result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tDirection\tMismatches\tBulge_Size\n')
        else:
            result.write('#Bulge_type\tcrRNA\tDNA\tChromosome\tPosition\tCluster Position\tDirection\tMismatches\tBulge_Size\tTotal\tMin_mismatches\tMax_mismatches\tPam_disr\tPAM_gen\tVar_uniq\n')

        total_targets = []
        for k in guides_dict.keys():
            total_targets += guides_dict[k]
        total_list = []

        if not total_targets:
            print('No targets to clusterize, exit...')
            sys.exit()
        first_line = total_targets[0]
        # current_chr_pos = first_line[3] + ' ' + first_line[9]
        current_chr_pos = first_line[1] + ' ' + str(first_line[3])

        total_list.append([first_line])

        for line in total_targets[1:]:
            #if line[3] + ' ' + line[9] != current_chr_pos:
            if line[1] + ' ' + str(line[3]) != current_chr_pos:
                # total_list[-1].sort(key = lambda x: int(x[8]))
                total_list[-1].sort(key = lambda x: (x[7], x[5]))   #Order cluster by total and mms
                total_list.append([line])
                # current_chr_pos = line[3] + ' ' + line[9]
                current_chr_pos = line[1] + ' ' + str(line[3])
            else:
                total_list[-1].append(line)     

        total_list[-1].sort(key = lambda x: (x[7], x[5]))       #Order last cluster by total and mms

        total_list.sort(key = lambda x: x[0][7])        #Order all clusters by total of top1
        if addGuide:
            if keep_columns:
                for cluster in total_list:
                    for target in cluster:
                        result.write('\t'.join(str(x) for x in target).strip() + '\t' + target[0].split('\t')[1].replace('-','') + '\n')
            else:
                for cluster in total_list:
                    for target in cluster:
                        result.write('\t'.join(str(x) for x in target[:3]) + '\t' + '\t'.join(str(x) for x in target[4:7]) +'\t' + target[8].strip() + '\t' + target[0].split('\t')[1].replace('-','') + '\n')

        else:
            if keep_columns:
                for cluster in total_list:
                    for target in cluster:
                        result.write('\t'.join([str(x) for x in target]).strip() + '\n')
            else:
                for cluster in total_list:
                    for target in cluster:
                        result.write('\t'.join(str(x) for x in target[:3]) + '\t' + '\t'.join(str(x) for x in target[4:7]) +'\t' + target[8].strip() + '\n')

    print("Clustering runtime: %s seconds" % (time.time() - start_time))