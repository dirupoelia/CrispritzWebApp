#!/usr/bin/env python


#Script that calculates cfd score for targets with bulge 'X', and save the accumulated cfd score for the input guide
# Also calculates the Doench score if the targets has bulge 'X' and 0 mms (doench = 0 if no such target exists)

import time
import pickle
import re
import sys
import os
import numpy as np
import subprocess
import azimuth.model_comparison
import string
# doench_string.append(seq)
# doench_score =  azimuth.model_comparison.predict(np.asarray(doench_string), None, None, model= model, pam_audit=False)
# doench_score = np.around(doench_score * 100)

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

tab = str.maketrans("ACTG", "TGAC")

def reverse_complement_table(seq):
    return seq.translate(tab)[::-1]
#if __name__ == '__main__':

#argv 1 = target file
#argv2 is guide
#argv3 is genome_directory (eg Genomes/hg19/)
mm_scores, pam_scores = get_mm_pam_scores()


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
with open("CrispritzWebApp/azimuth/saved_models/V3_model_nopos.pickle", 'rb') as f:
  model = pickle.load(f)
max_doench = 0
n_of_acceptable_cfd = 0
sum_cfd = 0
cfd_scores = []
# doench_string_dna_1 = []
# doench_string_dna_2 = []
# doench_string_rna_1 = []
# doench_string_rna_2 = []

all_word = []
with open (sys.argv[1]) as result:
  
  #Calc CDF score
  for target  in result:
    target = target.strip().split('\t')
    if 'X' not in target[0] or target[1] != sys.argv[2]:
      continue
    guide_seq = target[1]
    off = target[2].upper()
    m_guide_seq = re.search('[^ATCGN-]', guide_seq)
    m_off = re.search('[^ATCG-]', off)  
    iup_off = []
    first = True
    start_iup_off = 1
    
    if (m_guide_seq is None) and (m_off is None):
       
      #Calc CFD
          
      
      pam = off[-2:]  
      sg = off[:-3]
      #print("off. ", off)
      #print ("sg: ", sg)
      #print ("guide_seq: ", guide_seq)
      
      cfd_score = calc_cfd(guide_seq, sg, pam, mm_scores, pam_scores)
      if (target[6] == '0'):    #TODO se cambio inserendo pos cluister, devo cambiareanche qui
        #estraggo sequenza
        with open('bedfile_tmp.txt', 'w+') as bedfile:
          if target[5] == '+':
            bedfile.write(target[3] + '\t' + str(int(target[4]) - 4 ) + '\t' + str(int(target[4]) + 23 + 3 ))
          else:
            bedfile.write(target[3] + '\t' + str(int(target[4]) - 3 ) + '\t' + str(int(target[4]) + 23 + 4 ))
        
        extr = subprocess.Popen(['bedtools getfasta -fi ' + sys.argv[3] + '/' + target[3] '-bed bedfile_tmp.txt'], shell = True, stdout=subprocess.PIPE) 
        extr.wait()
        out, err = extr.communicate()
        out = out.decode('UTF-8')
        if target[5] == '+':
          sequence_doench = [out.strip().split('\n')[-1].upper()]
        else:
          sequence_doench = [reverse_complement_table(out.strip().split('\n')[-1].upper())]
        doench_score =  azimuth.model_comparison.predict(np.asarray(sequence_doench), None, None, model= model, pam_audit=False)
        doench_score = np.around(doench_score * 100)
        if doench_score > max_doench:
          max_doench = doench_score
        

      sum_cfd = sum_cfd + cfd_score
      if cfd_score > 0.023:
        n_of_acceptable_cfd = n_of_acceptable_cfd +1  
      
    else:
      if "N" in off:
        continue
      #TODO calc doench
      # if mms == 0:
      #   extract from var/ref genome
      #   if has iupac:
      #     create combinations with itertools
      #   cal doench
      #   get max



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
        
        
        # gap_pos = [None]
        no_iup_gap_srt = iup_off[no_iup_str] #se non ci sono gap passo la stringa non modificata al calc_cfd
        # if "DNA" in word[0]:    #gap in guide
        #   gap_pos = [i for i, letter in enumerate(word[1]) if letter == "-"]
        #   guide_seq = guide_seq.replace('-', '')
        #   for g in gap_pos:
        #     no_iup_gap_srt = iup_off[no_iup_str][0:g] + iup_off[no_iup_str][g+1:]

        # if "RNA" in word[0]:    #gap in target
        #   gap_pos = [i for i, letter in enumerate(word[2]) if letter == "-"]
        #   for g in gap_pos:
        #     if dna_gap_removal:
        #       guide_seq = guide_seq[0:g] + guide_seq[g+1:]
        #       dna_gap_removal = False
        #     no_iup_gap_srt = iup_off[no_iup_str][0:g] + iup_off[no_iup_str][g+1:]
        
        #Calc CFD
    

        pam = no_iup_gap_srt[-2:]   
        sg = no_iup_gap_srt[:-3]
        
        cfd_score = calc_cfd(guide_seq, sg, pam, mm_scores, pam_scores)
        sum_cfd = sum_cfd + cfd_score

job_id = sys.argv[1].split('/')[-1].split('.')[0]
# with open( 'Results/' + job_id + '/acfd.txt', 'a+') as res:   #TODO decomment
#   res.write(sys.argv[2] + '\t' + str(sum_cfd) + '\n')
with open( 'test_scores.txt', 'w+') as res:
  res.write(sys.argv[2] + '\t' + str(sum_cfd) + '\n')   #TODO comment

end = time.time()
