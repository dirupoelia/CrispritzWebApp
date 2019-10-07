from seq_script import extract_seq, convert_pam
import os

with open('sequence2700.txt') as s:
    seq = s.read().strip().replace('\n','')

print ('Len seq', len(seq))
guide = []
guide.extend(convert_pam.getGuides(seq, 'NGG', 20))
#print(guide)
#print('\n'.join(guide).strip())

print('guide found:',len(guide))