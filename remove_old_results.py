import os
import time
import shutil

os.chdir("./Results")

months = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]

while(os.getppid()):

    #print(os.getppid())
    today = time.localtime()
    for res_dir in os.listdir("./"):

        if res_dir[0] is not ".":

            log = open("./" + res_dir + "/log.txt")

            for line in log:
                #print(line)
                if "Job" in line and "Done" in line:

                    words = line.split(" ")
                    print(months[today.tm_mon-1])

                    if (words[1] is today.tm_mday) and (words[2] is not months[today.tm_mon-1]):

                        print("removed directory: "+ res_dir)
                       # shutil.rmtree("./" + res_dir)

            log.close()

    time.sleep(86400)
