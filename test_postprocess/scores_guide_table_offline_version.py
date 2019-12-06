#!/usr/bin/env python


# Script that calculates cfd score for targets with bulge 'X', and save the accumulated cfd score for the input guide
# Also calculates the Doench score if the targets has bulge 'X' and 0 mms (doench = 0 if no such target exists)

#argv 1 = target file
#argv 2 is genome_directory (eg ../../Genomes/hg19/)
#argv 3 is pam file -> to check if len is 23 and pam is NGG
#argv 4 is guide file
import time
import pickle
import re
import sys
import os
import numpy as np
import subprocess
import azimuth.model_comparison
import string
import itertools

def doenchForIupac(sequence_doench, model):
  pos_iupac = []
  var = []
  for pos, c in enumerate(sequence_doench):
    if c in iupac_code:
      pos_iupac.append(pos)
      var.append(iupac_code[c])
  
  target_combination = []
  if var:
    for i in itertools.product(*var):
        t = list(sequence_doench)
        for p, el in enumerate(pos_iupac):
            t[el] = i[p]
        target_combination.append(''.join(t))
  else:
    target_combination.append(sequence_doench)
  
  doench_score =  azimuth.model_comparison.predict(np.asarray(target_combination), None, None, model= model, pam_audit=False)
  doench_score = [np.around(i * 100) for i in doench_score]
  return int(max(doench_score))


def get_mm_pam_scores():
  try:
    mm_scores = pickle.load(open(os.path.dirname(os.path.realpath(__file__)) + '/mismatch_score.pkl', 'rb'))
    pam_scores = pickle.load(open(os.path.dirname(os.path.realpath(__file__)) +'/PAM_scores.pkl', 'rb'))
    return (mm_scores, pam_scores)
  except:
    raise Exception("Could not find file with mismatch scores or PAM scores")


def revcom(s):
  basecomp = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A', 'U': 'A'}
  letters = list(s[::-1])
  letters = [basecomp[base] for base in letters]
  return ''.join(letters)


# Calculates CFD score
def calc_cfd(guide_seq, sg, pam, mm_scores, pam_scores):
    
    score = 1
    dna_gp = 0
    sg = sg.replace('T', 'U')
    guide_seq = guide_seq.replace('T', 'U')
    s_list = list(sg)
    guide_seq_list = list(guide_seq)
    for i, sl in enumerate(s_list):
      
      if guide_seq_list[i] == sl:

          score *= 1

      else:
          key = 'r' + guide_seq_list[i] + ':d' + revcom(sl) + ',' + str(i + 1)
          score *= mm_scores[key]
          if '-' in guide_seq_list[i]:
            dna_gp = dna_gp + 1
      
    score *= pam_scores[pam]
    
    return score

tab = str.maketrans("ACTG", "TGAC")   #TODO aggiungere anche le converisoni iupac

def reverse_complement_table(seq):
    return seq.translate(tab)[::-1]
#if __name__ == '__main__':

with open(sys.argv[3]) as pamfile:
  line = pamfile.readline().strip().split(' ')
  if len(line[0]) != 23 or 'NGG' not in line[0]:
    print('WARNING: The CFD score and the Doench score can be calculated only for guides with 20nt and the NGG PAM')
    sys.exit()


mm_scores, pam_scores = get_mm_pam_scores()
guides_dict = dict()
guides_dict_doench = dict()

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
          }

start = time.time()

# enr = sys.argv[2].split('/')
# enr_str = ''
# if enr[-1]:
#   if'+' in enr[-1]:         # + perchè i genomi con le var si chiamano hg19_ref+1000genomeproject sul sito
#     enr_str = '.enriched'
# else:
#   if'+' in enr[-2]:
#     enr_str = '.enriched'

enr_str = '' #TODO se il genoma in input è ref, enr_str è '', se è var, enr_str è '.enriched' -> praticamente enr_str è la stringa da mettere tra chr1 e .fa

with open( os.path.dirname(os.path.realpath(__file__)) + "/azimuth/saved_models/V3_model_nopos.pickle", 'rb') as f:
  model = pickle.load(f)
max_doench = 0
n_of_acceptable_cfd = 0
sum_cfd = 0
cfd_scores = []

all_word = []
with open (sys.argv[1]) as result:  #TODO open file di scrittura finale 
  
  #Calc CDF score
  for target  in result:
    target = target.strip().split('\t')
    if 'X' not in target[0]:
      target.append('n')    # target a cui non ho calcolato lo score CFD
      target.append('n')    # e a cui non ho calcolato il DOENCH
      #TODO salvare il target su file usando .write('\t'.join(target) + '\n')
      continue
    
    guide_seq = target[1]
    off = target[2]
    m_guide_seq = re.search('[^ATCGNatcgn-]', guide_seq)
    m_off = re.search('[^ATCGatcgn-]', off)  
    iup_off = []
    first = True
    start_iup_off = 1
    
    if (m_guide_seq is None) and (m_off is None):
       
      #Calc CFD
          
      
      pam = off[-2:]  
      sg = off[:-3].upper()
      #print("off. ", off)
      #print ("sg: ", sg)
      #print ("guide_seq: ", guide_seq)
      
      cfd_score = calc_cfd(guide_seq, sg, pam, mm_scores, pam_scores)
      target.append(str(cfd_score))

      if (target[6] == '0'):    #TODO se cambio inserendo position cluster, devo cambiare anche qui (da 6 a 7)
        #estraggo sequenza
        with open('bedfile_tmp.bed', 'w+') as bedfile:
          if target[5] == '+':
            bedfile.write(target[3] + '\t' + str(int(target[4]) - 4 ) + '\t' + str(int(target[4]) + 23 + 3 ))
          else:
            bedfile.write(target[3] + '\t' + str(int(target[4]) - 3 ) + '\t' + str(int(target[4]) + 23 + 4 ))
        
        extr = subprocess.Popen(['bedtools getfasta -fi ' + sys.argv[2] + '/' + target[3] +  enr_str +'.fa' ' -bed bedfile_tmp.bed'], shell = True, stdout=subprocess.PIPE)  #TODO insert option for .fasta
        extr.wait()
        out, err = extr.communicate()
        out = out.decode('UTF-8')
        if target[5] == '+':
          sequence_doench = out.strip().split('\n')[-1].upper()
        else:
          sequence_doench = reverse_complement_table(out.strip().split('\n')[-1].upper())
        # doench_score =  azimuth.model_comparison.predict(np.asarray(sequence_doench), None, None, model= model, pam_audit=False)
        # doench_score = np.around(doench_score * 100)
        # doench_score = doench_score[0]
        doench_score = doenchForIupac(sequence_doench, model) #TODO se trovo uno iupac nella sequenza estratta (4 chr prima del'inizio del target, 3 char dopo la PAM), mi fa le scomposizioni e mi
                                                              #ritorna il massimo doench, MA un solo target viene salvato. Se invece ci sono IUPAC nel target, vengono salvati tutti i target ricombinanti (riga 240)
        target.append(str(doench_score))
        try:
          if doench_score > guides_dict_doench[target[1]]:
            guides_dict_doench[target[1]] = doench_score
        except:
          guides_dict_doench[target[1]] = doench_score
      else:
        target.append('n')
      
      sum_cfd = sum_cfd + cfd_score
      try:
        guides_dict[target[1]] = guides_dict[target[1]] + cfd_score
      except:
        guides_dict[target[1]] = cfd_score
      if cfd_score > 0.023:
        n_of_acceptable_cfd = n_of_acceptable_cfd +1  
      #TODO salvare il target su file usando .write('\t'.join(target) + '\n')

    else:
      targets_combination_to_save = []
      if "N" in off:
        continue
      i = 0
      for char in off:
        if char in iupac_code:
          n = len(iup_off)
          for list_char in iupac_code[char]:
            if not first:  
              for test in range(n - start_iup_off, n):
                iup_off.append(iup_off[test][:i] + list_char + iup_off[test][i+1:])
                
              
            else:
              iup_off.append(off[:i] + list_char + off[i+1:])
          first = False
          start_iup_off = start_iup_off * len(iupac_code[char])
          
        i += 1
      dna_gap_removal = True
      for no_iup_str in range(len(iup_off) - start_iup_off, len(iup_off)):
        targets_combination_to_save.append(target.copy())
        
        no_iup_gap_srt = iup_off[no_iup_str] #se non ci sono gap passo la stringa non modificata al calc_cfd
        targets_combination_to_save[-1][2] = no_iup_gap_srt
        #Calc CFD
    

        pam = no_iup_gap_srt[-2:]   
        sg = no_iup_gap_srt[:-3].upper()
        
        cfd_score = calc_cfd(guide_seq, sg, pam, mm_scores, pam_scores)
        targets_combination_to_save[-1].append(str(cfd_score))
        sum_cfd = sum_cfd + cfd_score
        try:
          guides_dict[target[1]] = guides_dict[target[1]] + cfd_score
        except:
          guides_dict[target[1]] = cfd_score

      if (target[6] == '0'):
        with open('bedfile_tmp.bed', 'w+') as bedfile:
          if target[5] == '+':
            bedfile.write(target[3] + '\t' + str(int(target[4]) - 4 ) + '\t' + str(int(target[4]) + 23 + 3 ))
          else:
            bedfile.write(target[3] + '\t' + str(int(target[4]) - 3 ) + '\t' + str(int(target[4]) + 23 + 4 ))
        
        extr = subprocess.Popen(['bedtools getfasta -fi ' + sys.argv[2] + '/' + target[3] + enr_str +'.fa' ' -bed bedfile_tmp.bed'], shell = True, stdout=subprocess.PIPE)  #TODO insert option for .fasta
        extr.wait()
        out, err = extr.communicate()
        out = out.decode('UTF-8')
        if target[5] == '+':
          sequence_doench = out.strip().split('\n')[-1].upper()
        else:
          sequence_doench = reverse_complement_table(out.strip().split('\n')[-1].upper())
        # pos_iupac = []
        # var = []
        # for pos, c in enumerate(sequence_doench):
        #   if c in iupac_code:
        #     pos_iupac.append(pos)
        #     var.append(iupac_code[c])

        # target_combination = []
        # for i in itertools.product(*var):
        #     t = list(sequence_doench)
        #     for p, el in enumerate(pos_iupac):
        #         t[el] = i[p]
        #     target_combination.append(''.join(t))
        
        # doench_score =  azimuth.model_comparison.predict(np.asarray(target_combination), None, None, model= model, pam_audit=False)
        # doench_score = [np.around(i * 100) for i in doench_score]
        m_doench = doenchForIupac(sequence_doench, model)
        try:
          if m_doench > guides_dict_doench[target[1]]:
            guides_dict_doench[target[1]] = m_doench
        except:
          guides_dict_doench[target[1]] = m_doench
      else:
        targets_combination_to_save[-1].append('n')
      
      #TODO for i in targets_combination_to_save:
        #TODO salvare il target su file usando .write('\t'.join(i) + '\n')



# job_id = sys.argv[1].split('/')[-1].split('.')[0]



# with open( 'acfd.txt', 'w+') as res, open(sys.argv[4], 'r') as guides:
#   guides = guides.read().strip().split('\n')
#   for g in guides:
#     if g not in guides_dict:
#       guides_dict[g] = 0    
#   #for k in guides_dict.keys():
#     if g not in guides_dict_doench:
#       guides_dict_doench[g] = 0
#     res.write(g + '\t' + str(guides_dict[g]) + '\t' + str(guides_dict_doench[g]) + '\n')


end = time.time()
