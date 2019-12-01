'''
Carica il dizionario, per ogni linea del file result (top1):
estrae i samples e salva la posizione nel target e nel chr, la tupla (ref,var),
crea tutte le combinazioni in target_combination
Poi passa tutti  gli elementi di target_combination e per ogni pos
dove c'era uno iupac controlla: se c'è un var, prende i samples e fa l'intersezione

'''

import gzip
import sys
import json
import time
import itertools
# argv1 is dict
# argv is result file
#Load .json dict
total_error = 0
resu_name = sys.argv[2][:sys.argv[2].rfind('.')] + '.samples.txt'
chr_name = sys.argv[1].split('.json')[0].split('_')[-1]
if True:
    start_time = time.time()
    if True:
        with open(sys.argv[1], 'r') as f:
            datastore = json.load(f)
    print ('Load done', time.time() - start_time)
    #Use the new datastore datastructure
    iupac_code = {
            "R":("A", "G"),
            "Y":("C", "T"),
            "S":("G", "C"),
            "W":("A", "T"),
            "K":("G", "T"),
            "M":("A", "C"),
            "B":("C", "G", "T"),
            "D":("A", "G", "T"),
            "H":("A", "C", "T"),
            "V":("A", "C", "G"),
            "r":("A", "G"),
            "y":("C", "T"),
            "s":("G", "C"),
            "w":("A", "T"),
            "k":("G", "T"),
            "m":("A", "C"),
            "b":("C", "G", "T"),
            "d":("A", "G", "T"),
            "h":("A", "C", "T"),
            "v":("A", "C", "G"),
            'N':('A', 'T', 'C', 'G')
            }
    total_error = 0
    with open (sys.argv[2]) as targets, open(resu_name,'a+') as result:
        #header = targets.readline()
        for line in targets:
            if '#' in line:
                continue
            line = line.strip().split('\t')
            #returned_none = False
            pos_snp = []
            var = []
            target_combination = []
            pos_snp_chr = []
            if line[3] == chr_name:       
                set_list = []
                target_string = line[2]
                if line[6] == '-':
                    target_string = target_string[::-1]
                bulge_found = 0 
                for pos, char in enumerate(target_string):
                    if char == '-':
                        bulge_found = bulge_found + 1 
                    if char in iupac_code:
                        iupac_pos = str(int(line[4]) + pos + 1 - bulge_found)
                        try:
                            a = (datastore[chr_name + ',' + iupac_pos])   #NOTE se non ha samples, ritorna ;ref,var
                            
                            #ref_char = a[-4:][1]
                            #var_char = a[-4:][3]
                            ref_char = a.split(';')[-1].split(',')[0]
                            var_char = a.split(';')[-1].split(',')[1]
                            # a = a[:-4]
                            a = a.split(';')[0]
                            pos_snp.append(pos)
                            pos_snp_chr.append(iupac_pos)
                            var.append((ref_char,var_char))
                        except Exception as e: 
                            print(e)
                            print('Error at ' + '\t'.join(line) + ', with char ' + char + ', at pos ', iupac_pos)
                            #sys.exit()
                            total_error = total_error + 1
                        #print(set(a.split(',')))
                        if a:
                            set_list.append(set(a.split(',')))
                        else:
                            #print('Error None ', line, a)
                            set_list.append(set())
                            #pass
                            #returned_none = True
                
                #Create all combinations
                for i in itertools.product(*var):
                    t = list(target_string)
                    for p, el in enumerate(pos_snp):
                        t[el] = i[p]
                    target_combination.append(''.join(t))
                # print(target_combination)
                
                
                #print('QUI:', pos_snp_chr)
                for t in target_combination:
                    set_list2 = []
                    final_result = line.copy()
                    for ele_pos,p in enumerate(pos_snp_chr):
                        #print('pos_chr', p)
                        a = (datastore[chr_name + ',' + p])
                        #print('a', a)
                    
                        samples = a.split(';')[0] #a[:-4] 
                        
                        ref = a.split(';')[-1].split(',')[0]
                        var = a.split(';')[-1].split(',')[1]
                        # if int(p) == 10353471 or int(p) == 10353474:
                            # print(p)
                            # print('final result', final_result)
                            # print('Samp, ref, var: ',samples, ref, var)
                        #print('char in pos',t[pos_snp[ele_pos]].upper())
                        if t[pos_snp[ele_pos]].upper() == var:      #TODO controllo qui, forse problema nella direction -?
                            if samples:
                                set_list2.append(set(samples.split(',')))
                            else:
                                #print('Error None ', line, a)
                                set_list2.append(set())
                            #     #returned_none = True 
                        # if int(p) == 10353471 or int(p) == 10353474:
                            # print('Set list2', set_list2 )
                    if set_list2:
                        #print('setlist2', set_list2)
                        common_samples = set.intersection(*set_list2)
                       # print('common_smples', common_samples)
                        if common_samples:
                            final_result.append(','.join(common_samples))
                        else:
                            final_result.append('No common samples')
                    else:
                        final_result.append('No samples')
                    # print('final_res', final_result)
                    if line[6] == '-':
                        t = t[::-1]
                    final_result[2] = t
                    result.write('\t'.join(final_result) + '\n')
                    
                    #print(final_result)

                #Total intersection
                # if set_list:
                #     common_samples = set.intersection(*set_list)
                #     if common_samples:
                #         line.append(','.join(common_samples))
                #     else:
                #         line.append('No common samples')
                # else:
                #     line.append('No samples')
                # result.write('\t'.join(line) + '\n')
                    
print ('Done')
print (total_error)
