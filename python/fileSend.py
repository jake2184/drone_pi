#!bin/usr/env python

import requests
from os import listdir
import time
from copy import copy


def send_latest_audio(url, port, sessionCookie, gps, GPSLock, status, statusLock):
	endPoint="/api/"+status.dronename+"/audio/"
	lastSent = ""

	while True:
		fileList = listdir("audio")

		with statusLock:
			sending = copy(status.uploadingAudio)

		if fileList and sending:
			fileToSend = max(fileList)

			if fileToSend != lastSent:
				lastSent = fileToSend
				files = {'audio' : open("audio/" + fileToSend, 'rb')}

				with GPSLock:
					GPSData = copy(gps)
				try:
					req = requests.post(url+port+endPoint+ fileToSend[:-4], data=GPSData.__dict__, files=files, cookies=sessionCookie)
					if req.status_code == 200:
						print("Sent " + fileToSend)
				except requests.exceptions.RequestException as e:
						continue
				else:
					print("Failed to send " + fileToSend)
					print("Server response: " + str(req.status_code))

		time.sleep(1)


def send_latest_image(url, port, sessionCookie, gps, GPSLock, status, statusLock):
	endPoint = "/api/"+status.dronename+"/images/"
	lastSent = ""

	while True:
		fileList = listdir("photos")

		with statusLock:
			sending = copy(status.uploadingImages)

		if fileList and sending:
			for fileToSend in fileList:
				if fileToSend.endswith('~'):
					fileList.remove(fileToSend)

			fileToSend = max(fileList)

			if fileToSend != lastSent:
				lastSent = fileToSend
				files = {'image':open("photos/" + fileToSend, 'rb')}

				with GPSLock:
					GPSData = copy(gps)
				try:
					req = requests.post(url+port+endPoint+ fileToSend[:-4], data=GPSData.__dict__, files=files, cookies=sessionCookie)
					if req.status_code == 200:
						print("Sent " + fileToSend)
				except requests.exceptions.RequestException as e:
					continue
				else:
					print("Failed to send " + fileToSend)
					print("Server response: " + str(req.status_code))

		time.sleep(1)


def send_test_images(url, port, sessionCookie, gps, GPSLock, status, statusLock):
	endPoint = "/api/"+status.dronename+"/images/"
	lastSent = ""

	fileList = listdir("test/fire")

	with statusLock:
		sending = copy(status.uploadingImages)

	for i in range(1, len(fileList)):
		if sending:
			fileToSend = min(fileList)

			if fileToSend != lastSent:
				files = {'image':open("test/fire/" + fileToSend, 'rb')}

				with GPSLock:
					GPSData = copy(gps)

				GPSData.time = fileToSend[:-4]
				try:
					req = requests.post(url + port + endPoint + fileToSend[:-4], data=GPSData.__dict__, files=files, cookies=sessionCookie)
					if req.status_code == 200:
						print("Sent " + fileToSend)
						lastSent = fileToSend
						fileList.remove(fileToSend)
				except requests.exceptions.RequestException:
					continue
				else:
					print("Failed to send " + fileToSend)
					print("Server response: " + str(req.status_code))
		time.sleep(1)
