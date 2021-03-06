#!/usr/bin/env python

import ibmiotf.device
import threading
import json
import Queue
import time
from copy import copy
import os





class mqttClient:

	def __init__(self, configFile, mavCommandList, piCommandList):
		try:
			self.mavCommandList = mavCommandList
			self.piCommandList = piCommandList
			options = ibmiotf.device.ParseConfigFile(configFile)
			self.client = ibmiotf.device.Client(options)
			self.client.commandCallback = self.commandCallback
			self.client.connect()

		except ibmiotf.ConnectionException as e:
			print (e)

	def commandCallback(self, cmd):
		print("Received " + cmd.command + ": %s" % cmd.data)
		if not 'name' in cmd.data or not 'args' in cmd.data:
			print("Invalid command provided.")
			return
		if cmd.command == "piCommand":
			self.piCommandList.put(MavCommand(cmd.data['name'], cmd.data['args']))
		elif cmd.command == "mavCommand":
			self.mavCommandList.put(MavCommand(cmd.data['name'], cmd.data['args']))
		else:
			print ("Unknown command type: " % cmd.command)

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
		#print(sensorReadings)
		with statusLock:
			status.mqttCount += 1
			#print(status.mqttCount)

	def sendStatus(self, status):
		status.time = int(time.time()*1000)
		toSend = status.__dict__
		try:
			del toSend.password
		except AttributeError:
			pass
		self.client.publishEvent("status", "json", toSend)



def runIot(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, piCommandList):
	client = mqttClient("python/" + status.dronename + ".conf", mavCommandList, piCommandList)

	while True:
		with GPSLock:
			GPSData = copy(gps)
		with sensorLock:
			sensorData = copy(sensors)
			sensors.reset()
		with statusLock:
			statusToSend = copy(status)
		if statusToSend.uploadingSensors:
			client.sendSensorReadings(GPSData, sensorData, status, statusLock)
		client.sendStatus(statusToSend)

		time.sleep(status.mqttInterval / 1000.0)


from main import MavCommand, Status, Sensors, GPS
if __name__ == '__main__':
	gps = GPS()
	status = Status()
	status.mqttInterval = 1000
	sensors = Sensors()
	mavCommandList = Queue.Queue()  # Thread Safe FIFO
	piCommandList = Queue.Queue()

	GPSLock = threading.Lock()
	sensorLock = threading.Lock()
	statusLock = threading.Lock()

	runIot(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, piCommandList)
