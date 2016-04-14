#!/usr/bin/env python

import ibmiotf.device
import threading
import json

class iotClient:

	def __init__(self, configFile):
		try:
			options = ibmiotf.device.ParseConfigFile(configFile)
			self.client = ibmiotf.device.Client(options)
			self.client.commandCallback = self.commandCallback
			self.client.connect()
			self.startPings()
		except ibmiotf.ConnectionException as e:
			print e


	def commandCallback(self, cmd):
		print("Command: %s" % cmd.data)
		type(cmd.data)
		if cmd.command == "movement":
			# Implement movement
			dir = cmd.data['direction']
			
			if dir == "UP":
				#Move
				# sendDroneCommand(pins?) 
				pass
			elif dir == "STOP":
				#Stop
				pass

			
		elif cmd.command == "else":
			print cmd.command
		else:
			print ("Unknown command: " % cmd.command)
		
	def startPings(self):
		threading.Timer(10.0, self.startPings).start()
		# Send ping
		pingMessage = {'temp' : '24'}
		self.client.publishEvent("status","json", pingMessage)
		print "Ping "

if __name__ == '__main__':
	iotClient("config.conf")
	print "Waiting.."

