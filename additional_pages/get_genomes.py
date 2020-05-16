#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 17:14:56 2020

@author: francesco
"""
import os
import pandas as pd
from os.path import isfile, isdir,join 
from os import listdir   

def get_genomes(pathDir):
    
    #dir_path = os.path.dirname(os.path.realpath(__file__))+"/logGenomes/"
    #logs = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]
    
    genomes = pd.DataFrame(columns = ["Reference Genome", "Enriched Genome", "Index PAM", "Annotation File", "Samples ID File", "# Bulges"])
    """
    for log in logs:
        with open(join(dir_path, log)) as f:
            refgen = os.path.basename(f.readline().split("\t")[1])
            vcf = os.path.basename(f.readline().split("\t")[1])
            pam = os.path.basename(f.readline().split("\t")[1])
            ann = os.path.basename(f.readline().split("\t")[1])
            samples = os.path.basename(f.readline().split("\t")[1])
            bulges = f.readline().split("\t")[1]
            enrgen = f.readline().split("\t")[1]
    """
    genomes_dirs = [f for f in os.listdir(pathDir+"/Genomes/") if isdir(join(pathDir+"/Genomes/", f))]
    genome_library_dirs = [f for f in os.listdir(pathDir+"/genome_library/") if isdir(join(pathDir+"/genome_library/", f))]

    for d in genomes_dirs:
        if "+" not in d:    #Reference genome
            genRef = d            
            genEnr = "NA"
            #pam = "NA"
            ann = "NA"
            samples = "NA"
            #bulges = "NA"
            pams = []
            bMaxs = []
            for lib in genome_library_dirs:
                libPars = "_".join(lib.split("_")[2:])
                if genRef == libPars:
                    partsLib = lib.split("_")
                    pams.append(partsLib[0])
                    bMaxs.append(partsLib[1])
            for annot in os.listdir(pathDir+"/annotations/"):
                if genRef == annot.split(".")[0]:
                    ann = annot
                    break
            if len(pams) > 0:
                for i in range(len(pams)):
                   genomes = genomes.append({"Reference Genome":genRef, "Enriched Genome":genEnr,
                        "Index PAM":pams[i], "Annotation File":ann, "Samples ID File":samples, "# Bulges":bMaxs[i]}, ignore_index = True)
            else:
                genomes = genomes.append({"Reference Genome":genRef, "Enriched Genome":genEnr,
                        "Index PAM":"NA", "Annotation File":ann, "Samples ID File":samples, "# Bulges":"NA"}, ignore_index = True)                    
        else:       #Enriched Genome
            genEnr = d 
            genRef = d.split("+")[0]
            ann = "NA"
            samples = "NA"
            pams = []
            bMaxs = []
            for lib in genome_library_dirs:
                libPars = "_".join(lib.split("_")[2:])
                if genEnr == libPars:
                    partsLib = lib.split("_")
                    pams.append(partsLib[0])
                    bMaxs.append(partsLib[1])
            for annot in os.listdir(pathDir+"/annotations/"):
                if genRef == annot.split(".")[0]:
                    ann = annot
                    break  
            for s in os.listdir(pathDir+"/samplesID/"):
                if genEnr == s[8:len(s)-4]:
                    samples = s
                    break
            if len(pams) > 0:
                for i in range(len(pams)):
                   genomes = genomes.append({"Reference Genome":genRef, "Enriched Genome":genEnr,
                        "Index PAM":pams[i], "Annotation File":ann, "Samples ID File":samples, "# Bulges":bMaxs[i]}, ignore_index = True)
            else:
                genomes = genomes.append({"Reference Genome":genRef, "Enriched Genome":genEnr,
                        "Index PAM":"NA", "Annotation File":ann, "Samples ID File":samples, "# Bulges":"NA"}, ignore_index = True)

    return genomes
            