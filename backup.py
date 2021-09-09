import time
import os.path
from os import listdir
from os.path import isfile, join
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import shutil
import subprocess
import py7zr
import httplib2


mypath = r""

onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
onlyfiles = [each for each in onlyfiles if each[0] != "~"]

print(onlyfiles)


gauth = GoogleAuth()
gauth.LoadCredentialsFile("mycreds.txt")

if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()
# Save the current credentials to a file
gauth.SaveCredentialsFile("mycreds.txt")

drive = GoogleDrive(gauth)

#f = drive.ListFile({"q": "mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()
file_list = drive.ListFile({'q': "'' in parents and trashed=false"}).GetList()

file_times = [0, datetime(1000, 1,1)]

for folder in file_list:
    print(folder['title'])
    if datetime.strptime(folder['title'], '%d.%m.%y') > file_times[1]:
        file_times[1] = datetime.strptime(folder['title'], '%d.%m.%y')
        file_times[0] = folder['title']

print("Last back up was on: " + file_times[0])

last_backup = file_times[1]

folder_to_upload = drive.CreateFile({'title' : datetime.now().strftime("%d.%m.%y"), 'mimeType' : 'application/vnd.google-apps.folder', 'parents': [{'id': ''}] })
folder_to_upload.Upload()
id_of_target_folder = folder_to_upload['id']

shutil.rmtree(os.getcwd()+"\\temp")
os.makedirs(os.getcwd()+"\\temp")

for each in onlyfiles:
    #print(each)
    modified_time = time.ctime(os.path.getmtime(mypath + "\\" + each))

    #print("last modified: {}".format(modified_time))

    #Mon Jul 26 09:59:12 2021 %a %b %-d %Y %H:%M:%S %Y
    this_file  = datetime.strptime(modified_time, '%a %b %d %H:%M:%S %Y')
    if last_backup < this_file:
        #mark this file for backup
        print("This file will be backup: " + each)
        shutil.copy2(mypath + "\\" + each, os.getcwd()+"\\temp\\" + each)

print("compressing files")

with py7zr.SevenZipFile('{}.7z'.format(datetime.now().strftime("%d.%m.%y")), 'w') as archive:
    archive.writeall(os.getcwd()+"\\temp")

print("finished compression")
print("beginning uploading")

try:
    file1 = drive.CreateFile({'title': datetime.now().strftime("%d.%m.%y"), 'parents': [{'id': id_of_target_folder}] })
    file1.SetContentFile(os.getcwd() +"\\"+ datetime.now().strftime("%d.%m.%y") + '.7z')
    file1.Upload()

finally:
    file1.content.close()

print("uploading finished")
print("creating local copy")

shutil.copy2(os.getcwd() +"\\" + datetime.now().strftime("%d.%m.%y") + '.7z', r"")

print("deleting temp files")

shutil.rmtree(os.getcwd()+"\\temp")
os.makedirs(os.getcwd()+"\\temp")

os.remove(os.getcwd() + "\\" + datetime.now().strftime("%d.%m.%y") + '.7z')
