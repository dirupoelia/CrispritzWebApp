#! /usr/bin/env python
#  -*- coding: utf-8 -*-
import sys

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True

from tkinter import filedialog, END, IntVar
import os

def startUpdateDict():
    root = tk.Tk()
    top = TopUpdateDict(root)
    root.mainloop()

class TopUpdateDict:
    def __init__(self, top=None):

        top.geometry("600x250+640+212")
        top.minsize(1, 1)
        #top.maxsize(1825, 970)
        top.resizable(1, 1)
        top.title("Change Dictionary")
        top.configure(highlightcolor="black")

        self.FrameStatus = tk.Frame(top)
        self.FrameStatus.place(relx=0.017, rely=0.003, relheight=0.109
                , relwidth=0.975)

        self.LabelStatus = tk.Label(self.FrameStatus)
        self.LabelStatus.place(relx=0.014, rely=0.179, height=22, width=569)
        self.LabelStatus.configure(activebackground="#f9f9f9")
        self.LabelStatus.configure(text='''Please choose the following files''')

        self.FrameDict = tk.Frame(top)
        self.FrameDict.place(relx=0.033, rely=0.096, relheight=0.32
                , relwidth=0.942)

        self.LabelDict = tk.Label(self.FrameDict)
        self.LabelDict.place(relx=0.018, rely=0.13, height=19, width=186)
        self.LabelDict.configure(activebackground="#f9f9f9")
        self.LabelDict.configure(cursor="fleur")
        self.LabelDict.configure(text='Select original dictionary')

        self.ButtonDict = tk.Button(self.FrameDict)
        self.ButtonDict.place(relx=0.018, rely=0.493, height=25, width=100)
        self.ButtonDict.configure(activebackground="#f9f9f9")
        self.ButtonDict.configure(text='''Browse files''')
        self.ButtonDict.configure(command=self.pickDictFile)

        self.TextDict = tk.Text(self.FrameDict)
        self.TextDict.place(relx=0.207, rely=0.507, relheight=0.362
                , relwidth=0.772)
        self.TextDict.configure(background="white")
        self.TextDict.configure(font="TkTextFont")
        self.TextDict.configure(selectbackground="#c4c4c4")
        self.TextDict.configure(wrap="word")
        self.TextDict.configure(state="disabled")

        self.FrameVCF = tk.Frame(top)
        self.FrameVCF.place(relx=0.033, rely=0.426, relheight=0.32
                , relwidth=0.942)

        self.LabelVCF = tk.Label(self.FrameVCF)
        self.LabelVCF.place(relx=0.007, rely=0.119, height=17, width=139)
        self.LabelVCF.configure(activebackground="#f9f9f9")
        self.LabelVCF.configure(text='Select VCF to add')

        self.ButtonVCF = tk.Button(self.FrameVCF)
        self.ButtonVCF.place(relx=0.018, rely=0.492, height=25, width=100)
        self.ButtonVCF.configure(activebackground="#f9f9f9")
        self.ButtonVCF.configure(text='Browse files')
        self.ButtonVCF.configure(command=self.pickVCFFile)

        self.TextVCF = tk.Text(self.FrameVCF)
        self.TextVCF.place(relx=0.205, rely=0.492, relheight=0.424
                , relwidth=0.772)
        self.TextVCF.configure(background="white")
        self.TextVCF.configure(font="TkTextFont")
        self.TextVCF.configure(selectbackground="#c4c4c4")
        self.TextVCF.configure(wrap="word")
        self.TextVCF.configure(state="disabled")

        """
        self.FrameChoice = tk.Frame(top)
        self.FrameChoice.place(relx=0.033, rely=0.559, relheight=0.307
                , relwidth=0.942)
        self.FrameChoice.configure(relief='groove')
        self.FrameChoice.configure(borderwidth="2")
        self.FrameChoice.configure(relief="groove")

        self.LabelOverwrite = tk.Label(self.FrameChoice)
        self.LabelOverwrite.place(relx=0.018, rely=0.042, height=21, width=229)
        self.LabelOverwrite.configure(text='Overwrite existing dictionary?')

        self.CheckbuttonOverwrite = tk.Checkbutton(self.FrameChoice)
        self.CheckbuttonOverwrite.place(relx=0.416, rely=0.083, relheight=0.135
                , relwidth=0.028)
        self.CheckbuttonOverwrite.configure(activebackground="#f9f9f9")
        self.CheckbuttonOverwrite.configure(justify='left')
        self.varCheck = IntVar()
        self.CheckbuttonOverwrite.configure(var=self.varCheck, command=self.disableFrameName)

        self.FrameName = tk.Frame(self.FrameChoice)
        self.FrameName.place(relx=0.016, rely=0.302, relheight=0.677
                , relwidth=0.965)

        self.LabelName = tk.Label(self.FrameName)
        self.LabelName.place(relx=0.006, rely=0.323, height=18, width=179)
        self.LabelName.configure(activebackground="#f9f9f9")
        self.LabelName.configure(text='Updated dictionary name:')

        self.EntryName = tk.Entry(self.FrameName)
        self.EntryName.place(relx=0.33, rely=0.323,height=17, relwidth=0.653)
        self.EntryName.configure(background="white")
        self.EntryName.configure(font="TkFixedFont")
        self.EntryName.configure(selectbackground="#c4c4c4")
        """
        self.ButtonNext = tk.Button(top)
        self.ButtonNext.place(relx=0.433, rely=0.800, height=35, width=70)
        self.ButtonNext.configure(activebackground="#f9f9f9")
        self.ButtonNext.configure(text='Next')
        self.ButtonNext.configure(command=self.confirm)
        
        self.oldDict = ""
        self.VCFFile = ""
        
    def pickDictFile(self):
        self.oldDict = filedialog.askopenfilename(filetypes=(("json files","*.json"),("all files","*.*")))
        self.TextDict.configure(state="normal")
        self.TextDict.delete(1.0, END)
        self.TextDict.insert(END, self.oldDict)
        self.TextDict.configure(state="disabled")
    
    def pickVCFFile(self):
        self.VCFFile = filedialog.askopenfilename()
        self.TextVCF.configure(state="normal")
        self.TextVCF.delete(1.0, END)
        self.TextVCF.insert(END, self.VCFFile)
        self.TextVCF.configure(state="disabled")
        
    def disableFrameName(self):
        if self.varCheck.get() == 0:
            for ele in self.FrameName.winfo_children():
                ele.configure(state='normal')
        elif self.varCheck.get() == 1:
            for ele in self.FrameName.winfo_children():
                ele.configure(state='disabled')
        
    def confirm(self):
        if self.oldDict == "":
            self.LabelStatus.configure(fg='Red')
            self.LabelStatus.configure(text="Please select a dictionary")
            return
        elif self.VCFFile == "":
            self.LabelStatus.configure(fg='Red')
            self.LabelStatus.configure(text="Please select a VCF")
            return
        """
        elif self.varCheck.get() == 0 and self.EntryName.get() == "":
            self.LabelStatus.configure(fg='Red')
            self.LabelStatus.configure(text="Please write a name for the new dictionary or overwrite the original")
            return
        if self.varCheck.get() == 1:
            print("#####################################")
            print("Overwriting old dictionary")
            print("#####################################")
            os.system("python file_per_crispritz/change_dict.py "+self.oldDict+" "+self.VCFFile+" "+self.oldDict)
        else:
            print("#####################################")
            print("Writing updated dictionary")
            print("#####################################")
            os.system("python change_dict.py "+self.oldDict+" "+self.VCFFile+" ../dictionaries/"
                      +self.EntryName.get())
        """
        print("#####################################")
        print("Updating dictionary")
        print("#####################################")
        os.system("python file_per_crispritz/change_dict.py "+self.oldDict+" "+self.VCFFile)
        print("#####################################")
        print("Procedure Finished")
        print("#####################################")

if __name__ == '__main__':
    startUpdateDict()





