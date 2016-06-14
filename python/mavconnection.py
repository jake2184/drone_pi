#!/usr/bin/env python


import sys, os
import atexit
import time
import Queue, threading
import random

import math
import serial
from pymavlink import mavutil
from convert import convert
from main import GPS, Sensors, Status

# some base types from mavlink_types.h
MAVLINK_TYPE_CHAR     = 0
MAVLINK_TYPE_UINT8_T  = 1
MAVLINK_TYPE_INT8_T   = 2
MAVLINK_TYPE_UINT16_T = 3
MAVLINK_TYPE_INT16_T  = 4
MAVLINK_TYPE_UINT32_T = 5
MAVLINK_TYPE_INT32_T  = 6
MAVLINK_TYPE_UINT64_T = 7
MAVLINK_TYPE_INT64_T  = 8
MAVLINK_TYPE_FLOAT    = 9
MAVLINK_TYPE_DOUBLE   = 10

class MavCommand:
	def __init__(self, name, args):
		self.name = name
		self.args = args

class Parameter:
	def __init__(self, value, type):
		self.value = value
		self.type = type


class MavConnection:
	def __init__(self):
		# create a mavlink serial instance
		from sys import platform as _platform

		if _platform == "win32":
			device = 'com4'
		else:
			device = '/dev/ttyAMA0'
		try:
			self.master = mavutil.mavlink_connection(device, 57600, dialect="pixhawk")
		except serial.SerialException:
			print("No MAVLINK serial connection")
			exit(1)

		self.ts = self.master.target_system
		self.tc = self.master.target_component
		print(str(self.ts) + " " + str(self.tc))

		self.GPSLock = None
		self.sensorLock = None
		self.statusLock = None

		self.savedParams = {}

		atexit.register(self.closeLink)

		self.logfile = open("log.txt", 'w')
		#self.paramfile = open("params.txt", 'w')

		# wait for the heartbeat msg to find the system ID
		self.wait_heartbeat()

		# Dictionary of commands that can be implemented
		self.commands = {
			"logRequest" : self.logReq,
			"messageInterval" : self.master.mav.message_interval_send,
			"sendCommand" : self.master.mav.command_int_send,
			"sendLongCommand" : self.master.mav.command_long_send,
			"dataStreamRequest" : self.master.mav.request_data_stream_send,
			"paramListRequest" : self.master.mav.param_request_list_send,
			"getData" : self.master.mav.request_data_stream_send(self.ts, self.tc, mavutil.mavlink.MAV_DATA_STREAM_ALL, 1, 1),
			"getRC" : self.master.mav.request_data_stream_send(self.ts, self.tc, mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS, 1, 1),
			"fetchAllParams" : self.master.param_fetch_all,
			"saveParams" : self.saveParams,
			"setParam" : self.sendParam,
			"getParam" : self.master.param_fetch_one,
			"arm" : self.master.arducopter_arm,
			"disarm" : self.master.arducopter_disarm,
			"reboot" : self.master.reboot_autopilot,
			"setStab" : self.setStable,
			"isArmed" : self.master.motors_armed,
			"setRCChan" : self.setRCChan,
			"getMode" : self.getMode,
			"hover" : self.startHover,
			"continue" : self.stopHover,
			"raiseAltitude" : self.raiseAltitude,
			"takeoff" : self.takeoff,
			"setAuto" : self.master.set_mode_auto,
			"clearWay" : self.master.waypoint_clear_all_send,
			"setModeFlag" : self.master.set_mode
		}

	def wait_heartbeat(self):
		print("Waiting for heartbeat")
		self.master.wait_heartbeat()
		print("Got Heartbeat")

	def closeLink(self):
		#print("Ending")
		self.master.close()

	def startHover(self):
		with self.statusLock:
			self.status.hovering = True
		self.master.set_mode_loiter()

	def stopHover(self):
		with self.statusLock:
			self.status.hovering = False
		# Continue automated waypoints

	# Logging function
	def log(self, msg):
		string = str(msg.id) + "\t" + msg.name + " {"
		for field in msg.ordered_fieldnames:
			toAdd = field + ":" + str(getattr(msg, field)) + ", "
			string += toAdd
		string = string[:-2]
		string += " }\n"
		self.logfile.write(string)
		self.logfile.flush()

	# Log to parameter file
	def paramLog(self, msg):
		string = msg.param_id + "\t\t\t" + str(msg.param_value) + "\n"
		self.paramfile.write(string)

	# Below are series of misc functions used in development

	def setStable(self):
		self.master.set_mode(0)

	def logReq(self):
		self.master.mav.log_request_list_send(self.ts, self.tc, 0, 0xffff)

	def getMode(self):
		msg = self.master.recv_match(type="HEARTBEAT", blocking=True)
		number = "{0:b}".format(msg.base_mode)
		number = number.zfill(8)
		print("Base_Mode: " + str(number))
		print("System State: " + str(msg.system_status))

	def setRCChan(self):
		#self.sendParam("COM_RC_IN_MODE", 2, MAVLINK_TYPE_INT32_T)

		self.master.mav.rc_channels_override_send(self.ts, self.tc, 1500,1500,1500,1500,1500,1500,1500,1500)
		#self.master.mav.rc_channels_send(10000, 18, 1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,80)
		#self.master.mav.rc_channels_raw_send(10000, 0, 1500,1500,1500,1500,1500,1500,1500,1500,80)
		#self.master.mav.rc_channels_raw_send(10000, 1, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 80)


	def raiseAltitude(self, alt):
		MAV_CMD_CONDITION_CHANGE_ALT = 113
		self.master.mav.command_long_send(self.ts, self.tc, MAV_CMD_CONDITION_CHANGE_ALT, 0, 0.01, 0, 0, 0, 0, 0,
										  20)

	def takeoff(self):
		MAV_CMD_NAV_TAKEOFF = 22  # Takeoff from ground / hand
		self.master.mav.command_long_send(self.ts, self.tc, MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 100)

	def getData(self):
		self.master.mav.command_long_send(self.ts,self.tc, 510, 0, 65,0,0,0,0,0,0)
		self.master.mav.command_long_send(self.ts, self.tc, 510, 0, convert(65), 0, 0, 0, 0, 0, 0)
		self.master.mav.command_long_send(self.ts, self.tc, 511 , 0, convert(34), convert(1000),0,0,0,0,0)
		self.master.mav.command_long_send(self.ts, self.tc, 511, 0, convert(35), convert(1000), 0, 0, 0, 0, 0)
		self.master.mav.command_long_send(self.ts, self.tc, 511, 0, convert(65), convert(1000), 0, 0, 0, 0,0)

	# Set paramater in Pixhack settings
	def sendParam(self, name, value, type=MAVLINK_TYPE_FLOAT):
		print("Type: " + str(type))
		if type == MAVLINK_TYPE_INT32_T:
			print("Converting")
			value = convert(value)

		self.master.param_set_send(name, value, type)

	# Save parameters in memory to a file
	def saveParams(self, fileName):
		paramFile = open(fileName, 'w')
		for param in sorted(self.savedParams):
			string = param + "\t\t\t" + str(self.savedParams[param].value) + "\t\t\t" + str(self.savedParams[param].type) + "\n"
			paramFile.write(string)
		paramFile.close()



	# Update status object
	def updateStatus(self, msg):
		t = msg.get_type()
		with self.statusLock:
			if t == "HEARTBEAT":
				self.status.mavMode = msg.base_mode
				self.status.mavStatus = msg.system_status
			elif t == "SYS_STATUS":
				self.status.batteryVoltage = msg.voltage_battery
			elif t == "BATTERY_STATUS":
				self.status.batteryRemaining = msg.battery_remaining
			elif t == "HOME_POSITION":
				self.status.homePosition = [msg.latitude / 1000000.0, msg.longitude / 10000000.0,
											 msg.altitude / 1000.0]
			else:
				print("Unknown status update type: " + t)

	# Update sensors object. TODO altitude
	def updateSensors(self, msg):
		with self.sensorLock:
			if msg.get_type() == "VFR_HUD":
				self.sensors.heading = msg.heading

	# Update GPS object
	def updateGPS(self, msg):
		with self.GPSLock:
			self.gps.time = int(time.time() * 1000)
			self.gps.latitude = float(msg.lat) / 10000000.0
			self.gps.longitude = float(msg.lon) / 10000000.0
			self.gps.altitude = float(msg.alt) / 1000.0

	# Execute a command to send to mav
	def sendCommand(self, mavCommand):
		print("Implementing " + mavCommand.name + " " + str(mavCommand.args))
		try:
			response = self.commands[mavCommand.name](*mavCommand.args)
			if response is not None:
				print(response)
			time.sleep(0.5)
		except KeyError as e:
			print("Couldn't find " + str(e))
			pass
		except Exception as e:
			print e
			pass

	# Repeatedly handle any messages from mavlink, and send and commands
	def monitorMessages(self, gps, sensors, status, mavCommandList):
		self.gps = gps
		self.sensors = sensors
		self.status = status

		msgTypes = []
		while True:
			msg = self.master.recv_msg()
			if msg:
				t = msg.get_type()
				if t not in msgTypes:
					# print(t)
					msgTypes.append(t)

				if t == "BAD_DATA":
					if mavutil.all_printable(msg.data):
						sys.stdout.write(msg.data)
						sys.stdout.flush()
				elif t == "HEARTBEAT":
					self.log(msg)
					self.updateStatus(msg)
				elif t == "SYS_STATUS":
					self.log(msg)
					self.updateStatus(msg)
				elif t == "BATTERY_STATUS":
					self.log(msg)
					self.updateStatus(msg)
				elif t == "ATTITUDE_TARGET":
					# self.log(msg)
					pass
				elif t == "ATTITUDE": # roll/pitch/yaw
					#self.log(msg)
					pass
				elif t == "HOME_POSITION":
					self.updateStatus(msg)
					#self.log(msg)
				elif t == "ALTITUDE":
					#self.log(msg)
					pass
				elif t == "LOCAL_POSITION_NED":
					#self.log(msg)
					pass
				elif t == "GPS_RAW_INT": # Should use not raw_int
					pass
					#self.log(msg)
					#self.updateGPS(msg, gps)
				elif t == "GLOBAL_POSITION_INT":
					#self.log(msg)
					self.updateGPS(msg)
				elif t == "VFR_HUD":
					self.log(msg)
					self.updateSensors(msg)
				elif t == "STATUSTEXT":
					self.log(msg)
					print(msg.text)
				elif t == "EXTENDED_SYS_STATE":
					pass
				elif t == "HIGHRES_IMU":
					pass
				elif t == "LOCAL_POSITION_NED":
					pass
				elif t == "POSITION_TARGET_GLOBAL_INT" or t == "TERRAIN_REPORT" or t=="POWER_STATUS" or t=="RAW_IMU" or t=="SYSTEM_TIME" \
					or t=="MISSION_CURRENT" or t=="SCALED_IMU2" or t=="SCALED_PRESSURE" :
					pass
				elif t == "PARAM_VALUE":
					self.log(msg)
					if t in self.savedParams:
						self.savedParams[msg.param_id].value = msg.param_value
					else:
						self.savedParams[msg.param_id] = Parameter(msg.param_value, msg.param_type)

					if msg.param_index == msg.param_count - 1:
						print("Got all parameters?")

				else:
					self.log(msg)
					pass

			# If we have a command, send it
			if mavCommandList.qsize() > 0:
				print("Sending command")
				mavCommand = mavCommandList.get()
				self.sendCommand(mavCommand)
			else:
				time.sleep(0.1)


# Create connection, start monitoring messages
def mavLoop(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList):
	mavlink = MavConnection()
	mavlink.GPSLock = GPSLock
	mavlink.sensorLock = sensorLock
	mavlink.statusLock = statusLock
	mavlink.monitorMessages(gps, sensors, status, mavCommandList)


def dummyMavLoop(gps, GPSLock, sensors, sensorLock, status, statusLock, mavCommandList, direction):
	with statusLock:
		status.mavMode = 0
		status.mavStatus = 0
		status.batteryVoltage = 12
		status.batteryRemaining = 80
		status.homePosition = [51.498834, -0.177371, 50]

	with sensorLock:
		sensors.heading = calcHeading(direction[0], direction[1])


	while True:
		with GPSLock:
			gps.time = int(time.time() * 1000)
			if not status.hovering:
				gps.latitude += float(direction[0]) * 0.00005
				gps.longitude += float(direction[1]) * 0.00005
		with sensorLock:
			sensors.altitude = 100 + (random.random() - 0.5) * 10

		if mavCommandList.qsize() > 0:
			print("Sending command")
			mavCommand = mavCommandList.get()
			if mavCommand.name == 'hover':
				with statusLock:
					status.hovering = True
			elif mavCommand.name == 'continue':
				with statusLock:
					status.hovering = False
		time.sleep(0.5)


def calcHeading(x, y):
	return (math.degrees(math.atan2(float(x), float(y)))+360)%360

if __name__ == '__main__':
	#os.environ['MAVLINK_DIALECT'] = 'pixhawk'
	q = Queue.Queue()
	gps = GPS()
	gpsLock = threading.Lock()
	sensorLock = threading.Lock()
	statusLock = threading.Lock()
	sensors = Sensors()
	status = Status()

	thread = threading.Thread(target=mavLoop, args=(gps, gpsLock, sensors, sensorLock, status, statusLock, q))
	thread.daemon = True
	thread.start()

	time.sleep(2)

	while True:
		command = raw_input("Command: ")
		args = raw_input("Args: ")
		args = args.split()

		toGive = []
		for arg in args:
			try:
				toGive.append(float(arg))
			except ValueError as e:
				toGive.append(arg)


		print("\nPutting on queue\n")
		q.put(MavCommand(command, toGive), block=True)



