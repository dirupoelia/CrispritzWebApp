#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 17:14:56 2020

@author: whitebreeze
"""
import os
import pandas as pd
from os.path import isfile, isdir,join 
from os import listdir   

def get_genomes():
    
    dir_path = os.path.dirname(os.path.realpath(__file__))+"/logGenomes/"
    logs = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]
    
    genomes = pd.DataFrame(columns = ["Reference Genome", "Name Enriched", "VCF", "PAM", "Annotation", "Sample List", "# Bulges"])
    for log in logs:
        with open(join(dir_path, log)) as f:
            refgen = os.path.basename(f.readline().split("\t")[1])
            vcf = os.path.basename(f.readline().split("\t")[1])
            pam = os.path.basename(f.readline().split("\t")[1])
            ann = os.path.basename(f.readline().split("\t")[1])
            samples = os.path.basename(f.readline().split("\t")[1])
            bulges = f.readline().split("\t")[1]
            enrgen = f.readline().split("\t")[1]
            genomes = genomes.append({"Reference Genome":refgen, "Name Enriched":enrgen,
                        "VCF":vcf, "PAM":pam, "Annotation":ann, "Sample List":samples, "# Bulges":bulges}, ignore_index = True)
    
    return genomes
            