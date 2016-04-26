#!/usr/bin/env python

import ibmiotf.device
import threading
import json
import Queue
import time
from copy import copy






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
			self.piCommandList.put(MavCommand(cmd.data['name'], cmd.data['args']))
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

	def sendSensorReadings(self, GPSData, sensorData, status, statusLock):
		# TODO add condition to set to none if time of reading is old
		sensorReadings = {
			'time': int(time.time() * 1000),
			'location': [GPSData.latitude, GPSData.longitude],
			'temperature': sensorData.temperature,
			'airPurity': sensorData.airPurity,
			'altitude': sensorData.altitude
		}

		self.client.publishEvent("sensors", "json", sensorReadings)

		with statusLock:
			status.mqtt_count += 1


def runIot(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, piCommandList):
	client = mqttClient("python/config.conf", mavCommandList, piCommandList)

	while True:
		with GPSLock:
			GPSData = copy(gps)
		with sensorLock:
			sensorData = copy(sensors)
			#sensors.reset()
		with statusLock:
			sending = copy(status.uploadingSensors)
		if sending:
			client.sendSensorReadings(GPSData, sensorData, status, statusLock)
		time.sleep(status.mqtt_interval / 1000.0)


from main import MavCommand, Status, Sensors, GPS
if __name__ == '__main__':
	gps = GPS()
	status = Status()
	sensors = Sensors()
	mavCommandList = Queue.Queue()  # Thread Safe FIFO
	piCommandList = Queue.Queue()

	GPSLock = threading.Lock()
	sensorLock = threading.Lock()
	statusLock = threading.Lock()

	runIot(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, piCommandList)
