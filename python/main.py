#!/usr/bin/env python

import threading
from iot.client import iotClient
from audioCapture import record_to_file
from fileSend import send_latest_image, send_latest_audio
from imageCapture import takePhotos
import time, sys
import requests
from requests.auth import HTTPBasicAuth

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

def runIot(gps, sensors, commandList):
    client = iotClient("python/iot/config.conf", gps, sensors, commandList)

def runAudioCapture():
    while True:
        record_to_file("audio")
        print ("Made recording")


# Thread to communicate with drone


if __name__ == '__main__':

	url = "http://192.168.1.76"
	port = ":8080"

	# Check we can connect to Bluemix
	try:
		req = requests.get(url + port + "/login");
	except requests.exceptions.RequestException:
		print ("Cannot connect to " + url + port)
		sys.exit(0)

	# Try logging in
	req = requests.post(url + port + "/login", auth=HTTPBasicAuth('jake','pass'))
	sessionCookie = req.cookies

	gps = GPS()
	sensors = Sensors()
	commandList = []


	# Thread to regularly send/receive data
	iotThread = threading.Thread(target=runIot, args=(gps, sensors, commandList))
	iotThread.daemon = True
	iotThread.start()

	# Thread to communicate with drone

	# Thread to capture photos
	photoInterval = 1
	imageThread = threading.Thread(target=takePhotos, args=(photoInterval,))
	imageThread.daemon = True
	imageThread.start()

	# Thread to capture audio
	audioThread = threading.Thread(target=runAudioCapture)
	audioThread.daemon = True
	audioThread.start()

	# Thread to upload images
	imageUploadThread = threading.Thread(target=send_latest_image, args=(url, port, sessionCookie))
	imageUploadThread.daemon = True
	imageUploadThread.start()

	# Thread to upload audio
	audioUploadThread = threading.Thread(target=send_latest_audio, args=(url, port, sessionCookie))
	audioUploadThread.daemon = True
	audioUploadThread.start()


	while True:
		time.sleep(0.1)
