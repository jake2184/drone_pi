#!bin/usr/env python

import requests
from os import listdir
import time
from copy import copy


def send_latest_audio(url, port, sessionCookie, gps, GPSLock):
	endPoint="/speechUploadSecure"
	lastSent = ""

	while True:
		fileList = listdir("audio")
		if fileList:
			fileToSend = max(fileList)

			if fileToSend != lastSent:
				files = {'audio' : open("audio/" + fileToSend, 'rb')}

				with GPSLock:
					GPSData = copy(gps)

				req = requests.post(url+port+endPoint, data=GPSData.__dict__, files=files, cookies=sessionCookie)
				if req.status_code == 200:
					print("Sent " + fileToSend)
					lastSent = fileToSend
				else:
					print("Failed to send " + fileToSend)
					print("Server response: " + str(req.status_code))

		time.sleep(1)


def send_latest_image(url, port, sessionCookie, gps, GPSLock):
	endPoint="/imageUploadSecure"
	lastSent = ""

	while True:
		fileList = listdir("photos")
		if fileList:
			for fileToSend in fileList:
				if fileToSend.endswith('~'):
					print("Tempt")
					fileList.remove(fileToSend)

			fileToSend = max(fileList)

			if fileToSend != lastSent:
				files = {'image':open("photos/" + fileToSend, 'rb')}

				with GPSLock:
					GPSData = copy(gps)

				req = requests.post(url+port+endPoint, data=GPSData, files=files, cookies=sessionCookie)
				if req.status_code == 200:
					print("Sent " + fileToSend)
					lastSent = fileToSend
				else:
					print("Failed to send " + fileToSend)
					print("Server response: " + str(req.status_code))

		time.sleep(1)
