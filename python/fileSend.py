#!bin/usr/env python

import requests
from os import listdir
import time

def send_latest_audio(url, port, sessionCookie):
    endPoint="/speechUploadSecure"
    lastSent = "";

    while True:
        fileList = listdir("audio")
        if fileList:
            file = max(fileList)

            if file != lastSent:
                files = {'audio':open("audio/"+file)}
                req = requests.post(url+port+endPoint, files=files, cookies=sessionCookie)
                lastSent = file

        time.sleep(1)

def send_latest_image(url, port, sessionCookie):
    endPoint="/imageUploadSecure"
    lastSent = "";

    while True:
        fileList = listdir("photos")
        if fileList:
            file = max(fileList)

            if file != lastSent:
                files = {'image':open("photos/"+file)}
                req = requests.post(url+port+endPoint, files=files, cookies=sessionCookie)
                lastSent = file

        time.sleep(1)
