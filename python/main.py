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
		self.battery_remaining = 80
		self.mav_status = 0
		self.mav_mode = 0
		self.mqtt_interval = 2000
		self.mqtt_count = 0
		self.home = [0.0, 0.0, 0]
		self.uploadingImages = True
		self.uploadingAudio = True
		self.uploadingSensors = True
		self.capturingAudio = True
		self.capturingImages = True
		self.photoInterval = 1000
		self.streamingAudio = False #TODO change
		self.host = ""
		self.volumeDetection = False
		self.duration = 5000


class Sensors:
	def __init__(self):
		self.reset()
		# self.temperature = 0.0
		# self.airPurity = 0
		# self.altitude = 0
		# self.heading = 0
		# self.altitude = 0

	def reset(self):
		self.temperature = None
		self.airPurity = None
		self.altitude = None
		self.heading = None
		self.altitude = None


class MavCommand:
	def __init__(self, name, args):
		self.name = name
		self.args = args

import requests
from requests.auth import HTTPBasicAuth

from audioCapture import runAudioCapture, streamAudio
from fileSend import send_latest_image, send_latest_audio
from imageCapture import takePhotos
from sensorRead import sensorReadLoop
from sensorRead import dummySensorReadLoop
from client import runIot
from mavconnection import mavLoop
from fileSend import send_test_images


def dummyGPS(GPSLock, GPS, direction):
	while True:
		with GPSLock:
			GPS.latitude += float(direction) * 0.0005
			GPS.longitude += float(direction) * 0.0005
		time.sleep(1)


if __name__ == '__main__':

	status = Status()
	status.host = sys.argv[1]
	status.username = sys.argv[2]
	status.password = sys.argv[3]
	status.dronename = sys.argv[4]
	direction = sys.argv[5]

	port = ""

	url = "http://" + status.host


	# Check we can connect to Bluemix
	try:
		req = requests.get(url + "/login", timeout=2)
	except requests.exceptions.RequestException:
		print ("Cannot connect to " + url )
		sys.exit(0)

	# Try logging in
	req = requests.post(url +  "/login", auth=HTTPBasicAuth(status.username, status.password))
	print(str(req.status_code) + " " + str(req.cookies))
	sessionCookie = req.cookies

	gps = GPS()
	gps.longitude = -0.18
	gps.latitude = 51.5

	sensors = Sensors()


	mavCommandList = Queue.Queue() # Thread Safe FIFO
	piCommandList = Queue.Queue()

	GPSLock = threading.Lock()
	sensorLock = threading.Lock()
	statusLock = threading.Lock()


	# Thread to read Pi-attached sensors
	sensorThread = threading.Thread(target=dummySensorReadLoop, args=(sensors, sensorLock))
	sensorThread.daemon = True
	sensorThread.start()

	# Thread to communicate with drone
	droneThread = threading.Thread(target=mavLoop, args=(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList))
	droneThread.daemon = True
	#droneThread.start()

	# Thread to capture photos
	imageThread = threading.Thread(target=takePhotos, args=(status, statusLock))
	imageThread.daemon = True
	imageThread.start()

	# Thread to capture audio
	audioThread = threading.Thread(target=runAudioCapture, args=(status, statusLock))
	audioThread.daemon = True
	audioThread.start()

	# Thread to upload images
	#imageUploadThread = threading.Thread(target=send_test_images, args=(url, port, sessionCookie, gps, GPSLock, status, statusLock))
	imageUploadThread = threading.Thread(target=send_latest_image, args=(url, port, sessionCookie, gps, GPSLock, status, statusLock))
	imageUploadThread.daemon = True
	imageUploadThread.start()

	# Thread to upload audio
	audioUploadThread = threading.Thread(target=send_latest_audio, args=(url, port, sessionCookie, gps, GPSLock, status, statusLock))
	audioUploadThread.daemon = True
	audioUploadThread.start()

	# Thread to regularly send/receive data
	mqttThread = threading.Thread(target=runIot, args=(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, piCommandList))
	mqttThread.daemon = True
	mqttThread.start()

	#dummyGPS(GPSLock, gps, direction)

	streamingThread = threading.Thread(target=streamAudio, args=(status, statusLock, sessionCookie))
	streamingThread.daemon = True
	streamingThread.start()

	while True:
		if piCommandList.qsize() > 0:
			command = piCommandList.get()
			print(command)
			# TODO Args will be parsed as a float. If that fails, as a string

			with statusLock:
				# Could change some to work on status.__dict__
				if command.name == "uploadingImages":
					status.uploadingImages = command.args[0]
				elif command.name == "uploadingSensors":
					status.uploadingSensors = command.args[0]
				elif command.name == "capturingImages":
					status.capturingImages = command.args[0]
				elif command.name == "photoInterval":
					status.photoInterval = command.args[0]
				elif command.name == "mqttInterval":
					status.mqttInterval = command.args[0]
				elif command.name == "capturingAudio":
					status.capturingAudio = command.args[0]
					status.streamingAudio = not status.capturingAudio
				elif command.name == "uploadingAudio":
					status.uploadingAudio = command.args[0]
				elif command.name == "streamingAudio":
					status.streamingAudio = command.args[0]
					status.capturingAudio = not status.streamingAudio
				elif command.name == "duration":
					status.duration = command.args[0]
				else:
					print("Unknown command " + command.name)

		time.sleep(0.5)


