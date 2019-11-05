import os
import time
import shutil
import datetime

os.chdir("./Results")

months = {"gen":1, "feb":2, "mar":3, "apr":4, "mag":5, "giu":6, "lug":7, "ago":8, "set":9, "ott":10, "nov":11, "dic":12}
save_day = 3

while(os.getppid()):

    #print(os.getppid())
    today = datetime.date.today()
    tdelta = datetime.timedelta(days = save_day)
    for res_dir in os.listdir("./"):

        if res_dir[0] is not ".":

            log = open("./" + res_dir + "/log.txt")


            for line in log:
                #print(line)
                if "Job" in line and "Done" in line:

                    words = line.split(" ")
                    year = words[3][0:4]
                    doneday = datetime.date(int(year), int(months[words[2]]), int(words[1]))
                    #print(today, today - tdelta)

                    if doneday is today - tdelta:

                        shutil.rmtree("./" + res_dir)


            log.close()

    time.sleep(86400)
