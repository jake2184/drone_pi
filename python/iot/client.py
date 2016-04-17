#!/usr/bin/env python

import ibmiotf.device
import threading
import json
import time


class iotClient:

	# def __init__(self, configFile, gps, sensors, commandList):
	# 	try:
	# 		options = ibmiotf.device.ParseConfigFile(configFile)
	# 		self.client = ibmiotf.device.Client(options)
	# 		self.client.commandCallback = self.commandCallback
	# 		self.client.connect()
	# 		#self.startPings()
    #
	# 		while True:
	# 			print ("Sending sensors")
	# 			sensorReadings = {
	# 				'time' : int(time.time() * 1000),
	# 				'location' : [gps['latitude'], gps['longitude']],
	# 				'temperature' : sensors.temperature,
	# 				'airPurity' : sensors.airPurity,
	# 				'altitude' : sensors.altitude
	# 			}
    #
	# 			self.client.publishEvent("sensors", "json", sensorReadings)
	# 			time.sleep(1)
    #
	# 	except ibmiotf.ConnectionException as e:
	# 		print (e)

	def __init__(self, configFile, mavCommandList, piCommandList):
		try:
			options = ibmiotf.device.ParseConfigFile(configFile)
			self.client = ibmiotf.device.Client(options)
			self.client.commandCallback = self.commandCallback
			self.client.connect()
			# self.startPings()

		except ibmiotf.ConnectionException as e:
			print (e)

	def commandCallback(self, cmd):
		print("Command: %s" % cmd.data)
		type(cmd.data)
		if cmd.command == "movement":
			# Implement movement
			dir = cmd.data['direction']

			if dir == "UP":
				# Move
				# sendDroneCommand(pins?)
				pass
			elif dir == "STOP":
				# Stop
				pass
		elif cmd.command == "else":
			print (cmd.command)
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
			'location': [GPSData['latitude'], GPSData['longitude']],
			'temperature': sensorData.temperature,
			'airPurity': sensorData.airPurity,
			'altitude': sensorData.altitude
		}

		self.client.publishEvent("sensors", "json", sensorReadings)


def runIot(gps, GPSLock, sensors, sensorLock, mavCommandList, piCommandList):
	client = iotClient("python/iot/config.conf", mavCommandList, piCommandList)

	while True:
		with GPSLock:
			GPSData = gps
		with sensorLock:
			sensorData = sensors
		client.sendSensorReadings(GPSData, sensorData)
		time.sleep(1)


if __name__ == '__main__':
	iotClient("config.conf", None, None)
	print ("Waiting..")
