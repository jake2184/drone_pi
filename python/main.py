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

# Status object for Pi, with default values
class Status:
	def __init__(self):
		self.batteryVoltage = 0.0
		self.batteryRemaining = 80
		self.mavStatus = 0
		self.mavMode = 0
		self.mqttInterval = 1000
		self.mqttCount = 0
		self.homePosition = [0.0, 0.0, 0]

		self.uploadingImages = True
		self.uploadingAudio = True
		self.uploadingSensors = True

		self.capturingAudio = True  # This + streaming are mutex
		self.streamingAudio = False
		self.volumeDetection = False
		self.audioDuration = 5000
		self.audioSamplingFrequency = 44100
		self.audioFileType = "mp3"

		self.capturingImages = True
		self.photoInterval = 1000
		self.photoResolution = "854x480"
		self.photoQuality = 75

		self.host = ""
		self.hovering = False

		self.running = True


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
from mavconnection import mavLoop, dummyMavLoop
from fileSend import send_test_images


def dummyGPS(GPSLock, GPS, directions):
	while True:
		with GPSLock:
			GPS.time = int(time.time()*1000)
			GPS.latitude += float(directions[0]) * 0.00005
			GPS.longitude += float(directions[1]) * 0.00005
		time.sleep(1)


if __name__ == '__main__':
	# Initialise status
	status = Status()
	status.host = sys.argv[1]
	status.username = sys.argv[2]
	status.password = sys.argv[3]
	status.dronename = sys.argv[4]
	dummyData = int(sys.argv[5])

	if dummyData:
		direction = [sys.argv[6], sys.argv[7]]

	if "192" in status.host:
		url = "http://" + status.host
	else:
		url = "https://" + status.host


	# Check we can connect to Bluemix
	try:
		req = requests.get(url + "/login", timeout=2)
	except requests.exceptions.RequestException:
		print ("Cannot connect to " + url )
		sys.exit(0)

	# Try logging in
	req = requests.post(url +  "/login", auth=HTTPBasicAuth(status.username, status.password))
	sessionCookie = req.cookies

	req = requests.post(url + "/api/" + status.dronename + "/reset")

	gps = GPS()
	gps.longitude = -0.18
	gps.latitude = 51.5

	sensors = Sensors()

	# Thread Safe FIFOs
	mavCommandList = Queue.Queue()
	piCommandList = Queue.Queue()

	# Locks for respective objects
	GPSLock = threading.Lock()
	sensorLock = threading.Lock()
	statusLock = threading.Lock()


	# Thread to read Pi-attached sensors
	if dummyData:
		sensorThread = threading.Thread(name="sensorThread", target=dummySensorReadLoop, args=(sensors, sensorLock))
	else:
		sensorThread = threading.Thread(name="sensorThread", target=sensorReadLoop, args=(sensors, sensorLock))
	sensorThread.daemon = True
	sensorThread.start()

	# Thread to communicate with drone
	if dummyData:
		droneThread = threading.Thread(name="droneThread", target=dummyMavLoop, args=(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, direction))
	else:
		droneThread = threading.Thread(name="droneThread", target=mavLoop, args=(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList))
	droneThread.daemon = True
	droneThread.start()

	# Thread to capture photos
	imageThread = threading.Thread(name="imageThread", target=takePhotos, args=(status, statusLock))
	imageThread.daemon = True
	if not dummyData:
		imageThread.start()

	# Thread to capture audio - assume we have audio capability on dummy
	audioThread = threading.Thread(name="audioThread", target=runAudioCapture, args=(status, statusLock))
	audioThread.daemon = True
	audioThread.start()

	# Thread to upload images
	if dummyData:
		imageUploadThread = threading.Thread(name="imageUploadThread", target=send_test_images, args=(url, "", sessionCookie, gps, GPSLock, status, statusLock))
	else:
		imageUploadThread = threading.Thread(name="imageUploadThread", target=send_latest_image, args=(url, "", sessionCookie, gps, GPSLock, status, statusLock))
	imageUploadThread.daemon = True
	imageUploadThread.start()

	# Thread to upload audio
	audioUploadThread = threading.Thread(name="audioUploadThread", target=send_latest_audio, args=(url, "", sessionCookie, gps, GPSLock, status, statusLock))
	audioUploadThread.daemon = True
	audioUploadThread.start()

	# Thread to regularly send/receive data
	mqttThread = threading.Thread(name="mqttThread", target=runIot, args=(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, piCommandList))
	mqttThread.daemon = True
	mqttThread.start()

	# Thread for streaming audio to server
	streamingThread = threading.Thread(name="streamingThread", target=streamAudio, args=(status, statusLock, sessionCookie))
	streamingThread.daemon = True
	streamingThread.start()

	start = time.time()
	while status.running:
		# Handle any Pi commands received from MQTT
		if piCommandList.qsize() > 0:
			command = piCommandList.get()
			print("Implementing Command: " + command.name + " " + str(command.args))

			with statusLock:

				if command.name in status.__dict__.keys():
					setattr(status, command.name, command.args[0])

					# Special Mutex
					if command.name == "streamingAudio":
						status.capturingAudio = not status.streamingAudio
					elif command.name == "capturingAudio":
						status.streamingAudio = not status.capturingAudio

				else:
					print("Unknown command " + command.name)


				'''
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
					status.audioDuration = command.args[0]
				else:
					print("Unknown command " + command.name)
				'''

		time.sleep(0.5)

		if time.time() - start > 10:
			pass
			#print("Stopping")
			#status.running = False

