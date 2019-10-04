#Convert pam ang get guides from sequence
import sys
import os
import itertools
from Bio.Seq import Seq
import re

pam = sys.argv[1]
len_pam = len(pam)
len_guide = 20 #given in input
#dict
pam_dict = {
    'A':  "ARWMDHV",
    'C':  "CYSMBHV",
    'G':  "GRSKBDV",
    'T':  "TYWKBDH",
    'R':  "ARWMDHVSKBG",
    'Y':  "CYSMBHVWKDT",
    'S':  "CYSMBHVKDRG",
    'W':  "ARWMDHVYKBT",
    'K':  "GRSKBDVYWHT",
    'M':  "ARWMDHVYSBC",
    'B':  "CYSMBHVRKDGWT",
    'D':  "ARWMDHVSKBGYT",
    'H':  "ARWMDHVYSBCKT",
    'V':  "ARWMDHVYSBCKG",
    'N':  "ACGTRYSWKMBDHV",
}
list_prod = []
for char in pam:
    list_prod.append(pam_dict[char])

iupac_pam = []          #NNNNNNN NGG
for element in itertools.product(*list_prod):
    iupac_pam.append(''.join(element))

rev_pam = str(Seq(pam).reverse_complement())
list_prod = []
for char in rev_pam:
    list_prod.append(pam_dict[char])

iupac_pam_reverse = []        #CCN NNNNNNN  -> results found with this pam must be reverse complemented
for element in itertools.product(*list_prod):
    iupac_pam_reverse.append(''.join(element))

with open('sequence.txt') as se:
    sequence = se.read().strip().upper()
    len_sequence = len(sequence)
guides = []
for pam in iupac_pam:
    pos = ([m.start() for m in re.finditer('(?=' + pam + ')', sequence)])
    if pos:
        for i in pos:
            if i < len_guide:
                continue
            guides.append(sequence[i-len_guide:i+len_pam])           # i is position where first char of pam is found, eg the N char in NNNNNN NGG

for pam in iupac_pam_reverse:       #Negative strand
    pos = ([m.start() for m in re.finditer('(?=' + pam + ')', sequence)])
    if pos:
        for i in pos:
            if i > (len_sequence - len_guide - len_pam):
                continue
            guides.append(str(Seq(sequence[i:i+len_pam+len_guide]).reverse_complement()))         # i is position where first char of pam is found, eg the first C char in CCN NNNNNN

#return guides for when adding to app.py