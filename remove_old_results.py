import os
import time
import shutil
import datetime


#recursive enters the folder and removes the large files

def dir_control(base_dir):
    for dir in os.listdir(base_dir):

        if dir[0] is not "." and dir not in forbidden:
            #print(dir)

            #print(os.path.getsize("./"+dir))
            if os.path.isdir("./"+dir):
                #if os.path.getsize("./" + dir) > size:
                os.chdir("./" + dir)
                #print(dir)
                dir_control("./")
                os.chdir("../")

            else:
                if os.path.getsize("./" + dir) > size:
                    os.remove(dir)
                    #print(dir)
                    os.system("touch "+dir+".too_big.txt")


os.chdir("./Results")

months = {"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9, "ott": 10,
          "nov": 11, "dic": 12, "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Agu": 8, "Sep": 9, "Oct": 10,
          "Nov": 11, "Dec": 12}

#Limit days for deletion of results
save_day = 3
#Size of too large file
size = 1024 * 1024 * 1024

#set the folders not to be checked by the script in the forbidden list
forbidden = []

while (os.getppid()):

    # print(os.getppid())
    today = datetime.date.today()
    tdelta = datetime.timedelta(days=save_day)
    for res_dir in os.listdir("./"):

        if res_dir[0] is not "." and res_dir not in forbidden:

            log = open("./" + res_dir + "/log.txt")

            for line in log:
                # we look to the Job Done line
                if "Job" in line and "Done" in line:
                    #print(res_dir)

                    words = line.split(" ")
                    year = words[5][0:4]
                    #we reconstruct the doneday variable for the comparizon
                    doneday = datetime.date(int(year), int(months[words[1]]), int(words[2]))

                    if doneday is today - tdelta:
                        shutil.rmtree("./" + res_dir)

            log.close()

    timeout = time.time() + 86400

    #every minute we look for file which exeed the limit size and we remove it
    while time.time() < timeout:

        dir_control("./")

        time.sleep(60)
