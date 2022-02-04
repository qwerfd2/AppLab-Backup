import os
import urllib.request
import time
import sched
import sys
import requests

#Inupt your channel ID here.
urls = ["",""]

#For each chanel ID, input the name of the tables that you want to backup.
table = [["",""],
        ["",""]]

#Cycle time of the program, in seconds.
looptime = 1800

s = sched.scheduler(time.time, time.sleep)
def do_something(sc): 
    index = -1
    for x in urls:
        index+=1
        for y in table[index]:
            urlstring = "https://studio.code.org/v3/export-firebase-tables/"+x+"/"+y
            directory = x
            download(urlstring, dest_folder=directory, name=y)
    print("Backup completed. Next backup in "+str(looptime)+" seconds.")
    s.enter(looptime, 1, do_something, (sc,))

def download(url: str, dest_folder: str, name:str):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    seconds = int(time.time())
    localtime = time.ctime(seconds)
    local_time = localtime.replace(":",".")
    filename = name+"."+local_time+".csv"
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True)
   
    if r.ok:
        print("Saving to", os.path.abspath(file_path))
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else: 
        print("Download failed: {}\n{}".format(r.status_code, r.text))
s.enter(10, 1, do_something, (s,))
print("Backup starting in 10 seconds.")
s.run()