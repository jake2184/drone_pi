#!/usr/bin/env python

import Queue
import sys
import threading

import requests
from requests.auth import HTTPBasicAuth

from audioCapture import runAudioCapture
from fileSend import send_latest_image, send_latest_audio
from imageCapture import takePhotos
from mavconnection import mavLoop
#from client import runIot
from sensorRead import sensorReadLoop
from client import runIot

class GPS:
	def __init__(self):
		self.time = 0
		self.latitude = 0.0
		self.longitude = 0.0


class Sensors:
	def __init__(self):
		self.temperature = 0.0
		self.airPurity = 0
		self.altitude = 0


class Status:
	def __init__(self):
		self.ding = 0


class Settings:
	def __init__(self):
		self.set = 0



if __name__ == '__main__':

	url = "http://192.168.1.76"
	port = ":8080"

	# Check we can connect to Bluemix
	try:
		req = requests.get(url + port + "/login", timeout=2)
	except requests.exceptions.RequestException:
		print ("Cannot connect to " + url + port)
		sys.exit(0)

	# Try logging in
	req = requests.post(url + port + "/login", auth=HTTPBasicAuth('jake','pass'))
	sessionCookie = req.cookies

	gps = GPS()
	sensors = Sensors()
	status = Status()
	mavCommandList = Queue.Queue() # Thread Safe FIFO
	piCommandList = Queue.Queue()

	GPSLock = threading.Lock()
	sensorLock = threading.Lock()
	statusLock = threading.Lock()


	# Thread to read Pi-attached sensors
	sensorThread = threading.Thread(target=sensorReadLoop, args=(sensors, sensorLock))
	sensorThread.daemon = True
	sensorThread.start()

	# Thread to communicate with drone
	droneThread = threading.Thread(target=mavLoop, args=(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList))
	droneThread.daemon = True
	# droneThread.start()

	# Thread to capture photos
	photoInterval = 1
	imageThread = threading.Thread(target=takePhotos, args=(photoInterval,))
	imageThread.daemon = True
	#imageThread.start()

	# Thread to capture audio
	audioThread = threading.Thread(target=runAudioCapture)
	audioThread.daemon = True
	audioThread.start()

	# Thread to upload images
	imageUploadThread = threading.Thread(target=send_latest_image, args=(url, port, sessionCookie, gps, GPSLock))
	imageUploadThread.daemon = True
	#imageUploadThread.start()

	# Thread to upload audio
	audioUploadThread = threading.Thread(target=send_latest_audio, args=(url, port, sessionCookie, gps, GPSLock))
	audioUploadThread.daemon = True
	audioUploadThread.start()

	# Thread to regularly send/receive data
	mqttThread = threading.Thread(target=runIot, args=(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, piCommandList))
	mqttThread.daemon = True
	mqttThread.start()


	#while True:
	#	time.sleep(0.1)


