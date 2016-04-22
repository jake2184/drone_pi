#!/usr/bin/env python

import ibmiotf.device
import threading
import json
import Queue
from main import GPS, Sensors

import time
class MavCommand:
	def __init__(self, name, args):
		self.name = name
		self.args = args


class mqttClient:

	def __init__(self, configFile, mavCommandList, piCommandList):
		try:
			self.mavCommandList = mavCommandList
			self.piCommandList = piCommandList
			options = ibmiotf.device.ParseConfigFile(configFile)
			self.client = ibmiotf.device.Client(options)
			self.client.commandCallback = self.commandCallback
			self.client.connect()
			# self.startPings()

		except ibmiotf.ConnectionException as e:
			print (e)

	def commandCallback(self, cmd):
		print("Command: %s" % cmd.data)

		if cmd.command == "piCommand":
			self.piCommandList.put(cmd.data)
		elif cmd.command == "mavCommand":
			self.mavCommandList.put(MavCommand(cmd.data['name'], cmd.data['args']))
		else:
			print ("Unknown command: " % cmd.command)

	def startPings(self):
		threading.Timer(10.0, self.startPings).start()
		# Send ping
		pingMessage = {'temp' : '24'}
		self.client.publishEvent("ping","json", pingMessage)
		print ("Ping ")

	def sendSensorReadings(self, GPSData, sensorData):
		print ("Sending sensors")
		sensorReadings = {
			'time': int(time.time() * 1000),
			'location': [GPSData.latitude, GPSData.longitude],
			'temperature': sensorData.temperature,
			'airPurity': sensorData.airPurity,
			'altitude': sensorData.altitude
		}

		self.client.publishEvent("sensors", "json", sensorReadings)


def runIot(gps, GPSLock, sensors, sensorLock, mavCommandList, piCommandList):
	client = mqttClient("python/iot/config.conf", mavCommandList, piCommandList)

	while True:
		with GPSLock:
			GPSData = gps
		with sensorLock:
			sensorData = sensors
		client.sendSensorReadings(GPSData, sensorData)
		time.sleep(1)


if __name__ == '__main__':
	sensors = Sensors()
	mavCommandList = Queue.Queue()  # Thread Safe FIFO
	piCommandList = Queue.Queue()

	GPSLock = threading.Lock()
	sensorLock = threading.Lock()

	gps = GPS()
	runIot(gps, GPSLock, sensors, sensorLock, mavCommandList, piCommandList)
