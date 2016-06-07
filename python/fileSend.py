#!bin/usr/env python

import requests
from os import listdir
import time
from copy import copy


# Repeatedly send latest audio file to the server
def send_latest_audio(url, port, sessionCookie, gps, GPSLock, status, statusLock):
	# The API endpoint to send to
	endPoint="/api/"+status.dronename+"/audio/"
	lastSent = ""

	while True:
		with statusLock:
			sending = copy(status.uploadingAudio)

		# List all files in the directory
		fileList = listdir("audio")

		if fileList and sending:
			# Send the latest file (timestampd)
			fileToSend = max(fileList)

			# Only send if new
			if fileToSend != lastSent:
				lastSent = fileToSend
				files = {'audio' : open("audio/" + fileToSend, 'rb')}

				with GPSLock:
					GPSData = copy(gps)
				# Try and catch to handle communication loss
				# If a file is not sent, rather than retrying move onto next file
				GPSData.location = [GPSData.latitude, GPSData.longitude]
				try:

					req = requests.post(url+port+endPoint+ fileToSend[:-4], data=GPSData.__dict__, files=files, cookies=sessionCookie)
					if req.status_code == 200:
						print("Sent " + fileToSend)
						pass
					else:
						#print("Failed to send " + fileToSend)
						#print("Server response: " + str(req.status_code))
						pass
				except requests.exceptions.RequestException as e:
						continue
		# Sleep to prevent this thread maxing CPU if not sending
		time.sleep(0.1)


# Repeatedly send latest image file to the server
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
					GPSData.location = [GPSData.latitude, GPSData.longitude]
					req = requests.post(url+port+endPoint+ fileToSend[:-4], data=GPSData.__dict__, files=files, cookies=sessionCookie)
					if req.status_code == 200:
						print("Sent " + fileToSend)
					else:
						print("Failed to send " + fileToSend)
						print("Server response: " + str(req.status_code) + " " + req.text)
				except requests.exceptions.RequestException as e:
					continue


		time.sleep(0.1)


# Similar to send images, but loop over static images from test dir
def send_test_images(url, port, sessionCookie, gps, GPSLock, status, statusLock):
	endPoint = "/api/"+status.dronename+"/images/"
	lastSent = ""


	with statusLock:
		sending = copy(status.uploadingImages)

	while True:
		fileList = listdir("test/fire")
		for i in range(1, len(fileList)):
			if sending:
				fileToSend = min(fileList)

				if fileToSend != lastSent:
					files = {'image':open("test/fire/" + fileToSend, 'rb')}

					with GPSLock:
						GPSData = copy(gps)


					try:
						GPSData.location = [GPSData.latitude, GPSData.longitude]
						req = requests.post(url + port + endPoint + str(int(time.time()*1000)), data=GPSData.__dict__, files=files, cookies=sessionCookie)
						if req.status_code == 200:
							print("Sent " + fileToSend)
							lastSent = fileToSend
							fileList.remove(fileToSend)
						else:
							print("Failed to send " + fileToSend)
							print("Server response: " + str(req.status_code) + " " + req.text)
					except requests.exceptions.RequestException:
						continue

			time.sleep(1)
