#!/usr/bin/env python

import Queue
import sys
import threading
import time


class GPS:
	def __init__(self):
		self.time = 0
		self.latitude = 0.0
		self.longitude = 0.0
		self.altitude = 0.0


class Status:
	def __init__(self):
		self.battery_voltage = 0.0
		self.battery_remaining = 0
		self.mav_status = 0
		self.mav_mode = 0
		self.mqtt_interval = 1000
		self.mqtt_count = 0
		self.home = [0.0, 0.0, 0]
		self.uploadingImages = True
		self.uploadingAudio = True
		self.uploadingSensors = True


class Sensors:
	def __init__(self):
		self.temperature = 0.0
		self.airPurity = 0
		self.altitude = 0
		self.heading = 0
		self.altitude = 0

class MavCommand:
	def __init__(self, name, args):
		self.name = name
		self.args = args

import requests
from requests.auth import HTTPBasicAuth

from audioCapture import runAudioCapture
from fileSend import send_latest_image, send_latest_audio
from imageCapture import takePhotos
from mavconnection import mavLoop
from sensorRead import sensorReadLoop
from client import runIot


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
	#sensorThread.start()

	# Thread to communicate with drone
	droneThread = threading.Thread(target=mavLoop, args=(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList))
	droneThread.daemon = True
	droneThread.start()

	# Thread to capture photos
	photoInterval = 1
	imageThread = threading.Thread(target=takePhotos, args=(photoInterval,))
	imageThread.daemon = True
	#imageThread.start()

	# Thread to capture audio
	audioThread = threading.Thread(target=runAudioCapture)
	audioThread.daemon = True
	#audioThread.start()

	# Thread to upload images
	imageUploadThread = threading.Thread(target=send_latest_image, args=(url, port, sessionCookie, gps, GPSLock, status, statusLock))
	imageUploadThread.daemon = True
	#imageUploadThread.start()

	# Thread to upload audio
	audioUploadThread = threading.Thread(target=send_latest_audio, args=(url, port, sessionCookie, gps, GPSLock, status, statusLock))
	audioUploadThread.daemon = True
	audioUploadThread.start()

	# Thread to regularly send/receive data
	mqttThread = threading.Thread(target=runIot, args=(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, piCommandList))
	mqttThread.daemon = True
	mqttThread.start()


	while True:
		if piCommandList.qsize() > 0:
			command = piCommandList.get()

			# TODO Args will be parsed as a float. If that fails, as a string
			with statusLock:
				if command.name == "setUploadImages":
					status.uploadingImages = command.args[0]
				elif command.name == "setUploadAudio":
					status.uploadingAudio = command.args[0]
				elif command.name == "setUploadSensors":
					status.uploadingSensors = command.args[0]
				elif command.name == "setUploadStream":
					if(command.args[0] == "IMAGES"):
						status.uploadingImages = command.args[1]
					elif(command.args[0] == "AUDIO"):
						status.uploadingAudio = command.args[1]
					elif(command.args[0] == "SENSORS"):
						status.uploadingSensors = command.args[1]

		time.sleep(0.5)


