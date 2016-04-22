#!/usr/bin/env python


import sys
import atexit
import time
import Queue, threading
from pymavlink import mavutil
from convert import convert

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
		device = "com4"
		self.master = mavutil.mavlink_connection(device, 57600, dialect="pixhawk")
		self.ts = self.master.target_system
		self.tc = self.master.target_component

		print (self.ts)
		print(self.tc)

		self.savedParams = {}

		atexit.register(self.closeLink)
		self.logfile = open("log.txt", 'w')
		#self.paramfile = open("params.txt", 'w')
		# wait for the heartbeat msg to find the system ID
		self.wait_heartbeat()

		self.commands = {
			"logRequest" : self.logReq,
			"messageInterval" : self.master.mav.message_interval_send,
			"sendCommand" : self.master.mav.command_int_send,
			"sendLongCommand" : self.master.mav.command_long_send,
			"dataStreamRequest" : self.master.mav.request_data_stream_send,
			"paramListRequest" : self.master.mav.param_request_list_send,
			"fetchAllParams" : self.master.param_fetch_all,
			"saveParams" : self.saveParams,
			"setParam" : self.sendParam,
			"getParam" : self.master.param_fetch_one,
			"setRC" : self.setRC,
			"setPWM" : self.setPWM,
			"setMisc" : self.setMisc,
			"setBatt" : self.setBattery,
			"setCBRK" : self.setCBRK,
			"setServos" : self.setServos,
			"arm" : self.master.arducopter_arm,
			"disarm" : self.master.arducopter_disarm,
			"reboot" : self.master.reboot_autopilot,
			"setStab" : self.setStable,
			"isArmed" : self.master.motors_armed,
			"setRCChan" : self.setRCChan,
			"getData" :self.getData,
			"test" : self.test,
			"getMode" : self.getMode
		}

	def wait_heartbeat(self):
		print("Waiting for heartbeat")
		self.master.wait_heartbeat()
		print("Got Heartbeat")

	def closeLink(self):
		print("Ending")
		self.master.close()

	def logReq(self):
		self.master.mav.log_request_list_send(self.ts,self.tc, 0, 0xffff)

	def log(self, msg):
		string = str(msg.id) + "\t" + msg.name + " {"
		for field in msg.ordered_fieldnames:
			toAdd = field + ":" + str(getattr(msg, field)) + ", "
			string += toAdd
		string = string[:-2]
		string += " }\n"
		self.logfile.write(string)
		self.logfile.flush()

	def paramLog(self, msg):
		string = msg.param_id + "\t\t\t" + str(msg.param_value) + "\n"
		self.paramfile.write(string)

	def setRC(self):
		# self.master.param_set_send("RC_MAP_THROTTLE", 3, MAVLINK_TYPE_INT32_T)
		# self.master.param_set_send("RC_MAP_PITCH", 2, MAVLINK_TYPE_INT32_T )
		# self.master.param_set_send("RC_MAP_YAW", 4, MAVLINK_TYPE_INT32_T)
		# self.master.param_set_send("RC_MAP_ROLL", 1, MAVLINK_TYPE_INT32_T)
		# self.master.param_set_send("RC_MAP_MODE_SW", 5, MAVLINK_TYPE_INT32_T)
		# self.master.param_set_send("RC_CHAN_CNT", 5, MAVLINK_TYPE_INT32_T)

		self.master.param_set_send("RC_MAP_THROTTLE", convert(3), MAVLINK_TYPE_INT32_T)
		self.master.param_set_send("RC_MAP_PITCH", convert(2), MAVLINK_TYPE_INT32_T)
		self.master.param_set_send("RC_MAP_YAW", convert(4), MAVLINK_TYPE_INT32_T)
		self.master.param_set_send("RC_MAP_ROLL", convert(1), MAVLINK_TYPE_INT32_T)
		self.master.param_set_send("RC_MAP_MODE_SW", convert(5), MAVLINK_TYPE_INT32_T)
		self.master.param_set_send("RC_CHAN_CNT", convert(5), MAVLINK_TYPE_INT32_T)

	def setPWM(self):
		self.sendParam("PWM_MIN", 1000, MAVLINK_TYPE_INT32_T)
		self.sendParam("PWM_MAX", 2000, MAVLINK_TYPE_INT32_T)
		self.sendParam("PWM_AUX_MIN", 1000, MAVLINK_TYPE_INT32_T)
		self.sendParam("PWM_AUX_MAX", 2000, MAVLINK_TYPE_INT32_T)
		self.sendParam("PWM_DISARMED", 1000, MAVLINK_TYPE_INT32_T)
		self.sendParam("PWM_AUX_DISARMED", 1000, MAVLINK_TYPE_INT32_T)

	def setBattery(self):
		self.sendParam("BAT_N_CELLS", 3, MAVLINK_TYPE_INT32_T)

	def setCBRK(self):
		self.sendParam("CBRK_AIRSPD_CHK", 162128, MAVLINK_TYPE_INT32_T)
		self.sendParam("CBRK_IO_SAFETY", 22027, MAVLINK_TYPE_INT32_T)
		self.sendParam("CBRK_USB_CHK", 197848, MAVLINK_TYPE_INT32_T)
		self.sendParam("CBRK_GPSFAIL", 240024, MAVLINK_TYPE_INT32_T)
		self.sendParam("CBRK_FLIGHTTERM", 121212, MAVLINK_TYPE_INT32_T)

	def setMisc(self):
		self.sendParam("MAV_TYPE", 2, MAVLINK_TYPE_INT32_T)
		self.sendParam("COM_DL_LOSS_T", 10, MAVLINK_TYPE_INT32_T)
		self.sendParam("COM_RC_LOSS_T", 20)
		self.sendParam("COM_RC_IN_MODE", 0, MAVLINK_TYPE_INT32_T)
		self.sendParam("COM_AUTOS_PAR", 1, MAVLINK_TYPE_INT32_T)

	def setServos(self):
		self.master.set_servo(1, 1500)
		self.master.set_servo(2, 1500)
		self.master.set_servo(3, 1500)
		self.master.set_servo(4, 1500)

	def setStable(self):
		self.master.set_mode(0)

	def test(self):
		#self.master.mav.command_long_send(self.ts,self.tc, 178, 0, convert(1), convert(0xffffffff), convert(50), 0,0,0,0)
		#self.master.set_mode_flag(16, True)
		#self.master.set_mode_flag(128, True)
		#self.master.set_mode_flag(64, True)
		self.master.mav.command_long_send(self.ts, self.tc, 510, 0, convert(24), 0,0,0,0,0,0 )
		self.master.mav.command_long_send(self.ts, self.tc, convert(510), 0, convert(24), 0, 0, 0, 0, 0, 0)
		self.master.mav.command_long_send(self.ts, self.tc, 510, 0, 24, 0, 0, 0, 0, 0, 0)
		self.master.mav.command_long_send(self.ts, self.tc, 510, 0, 24, 0, 0, 0, 0, 0, 0)
		self.master.mav.command_int_send(self.ts, self.tc, 2, 510, 1, 0, convert(24), 0,0,0,0,0,0)
		self.master.mav.command_int_send(self.ts, self.tc, 2, 510, 1, 0, 24, 0, 0, 0, 0, 0, 0)
		self.master.set_mode_fbwa()

	def getMode(self):
		m = self.master.recv_match(type="HEARTBEAT", blocking=True)
		number = "{0:b}".format(m.base_mode)
		number = number.zfill(8)
		print(number)

	def setRCChan(self):
		#self.sendParam("COM_RC_IN_MODE", 2, MAVLINK_TYPE_INT32_T)

		self.master.mav.rc_channels_override_send(self.ts, self.tc, 1500,1500,1500,1500,1500,1500,1500,1500)
		#self.master.mav.rc_channels_send(10000, 18, 1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,1500,80)
		#self.master.mav.rc_channels_raw_send(10000, 0, 1500,1500,1500,1500,1500,1500,1500,1500,80)
		#self.master.mav.rc_channels_raw_send(10000, 1, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 80)

	def getData(self):
		self.master.mav.command_long_send(self.ts,self.tc, 510, 0, 65,0,0,0,0,0,0)
		self.master.mav.command_long_send(self.ts, self.tc, 510, 0, convert(65), 0, 0, 0, 0, 0, 0)
		self.master.mav.command_long_send(self.ts, self.tc, 511 , 0, convert(34), convert(1000),0,0,0,0,0)
		self.master.mav.command_long_send(self.ts, self.tc, 511, 0, convert(35), convert(1000), 0, 0, 0, 0, 0)
		self.master.mav.command_long_send(self.ts, self.tc, 511, 0, convert(65), convert(1000), 0, 0, 0, 0,0)

	def sendParam(self, name, value, type=MAVLINK_TYPE_FLOAT):

		if type == MAVLINK_TYPE_INT32_T:
			value = convert(value)

		self.master.param_set_send(name, value, type)

	def monitorMessages(self, gps, GPSLock, sensors, sensorLock, mavCommandList):
		'''show incoming mavlink messages'''
		msgTypes = []
		while True:
			msg = self.master.recv_msg()#blocking=True)
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
				elif t == "ATTITUDE_TARGET":
					pass
				elif t == "ATTITUDE":
					pass
				elif t == "ALTITUDE":
					pass
				elif t == "LOCAL_POSITION_NED":
					pass
				elif t == "GPS_RAW_INT":
					self.log(msg)
					self.updateGPS(msg, gps, GPSLock)
				elif t == "VFR_HUD":
					pass
				elif t == "HIGHRES_IMU":
					pass
				elif t == "STATUSTEXT":
					self.log(msg)
					print(msg.text)
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

			elif mavCommandList.qsize() > 0:
				mavCommand = mavCommandList.get()
				self.sendCommand(mavCommand)
			else:
				time.sleep(0.1)

	def updateGPS(self, msg, gps, GPSLock):
		with GPSLock:
			gps.time = int(time.time()*1000)
			gps.latitude = msg.lat
			gps.longitude = msg.lon

	def updateSensors(self, msg, sensors, sensorLock):
		pass

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
		#except Exception as e:
			#print e
			#pass

	def saveParams(self, fileName):
		paramFile = open(fileName, 'w')
		for param in sorted(self.savedParams):
			string = param + "\t\t\t" + str(self.savedParams[param].value) + "\t\t\t" + str(self.savedParams[param].type) + "\n"
			paramFile.write(string)
		paramFile.close()

def mavLoop(gps, GPSLock, sensors, sensorLock, mavCommandList):
	mavlink = MavConnection()

	mavlink.monitorMessages(gps, GPSLock, sensors, sensorLock, mavCommandList)


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

if __name__ == '__main__':
	q = Queue.Queue()
	gps = GPS()
	gpsLock = threading.Lock()
	sensorLock = threading.Lock()
	sensors = Sensors()

	thread = threading.Thread(target=mavLoop, args=(gps, gpsLock, sensors, sensorLock, q))
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


		print("\n")
		q.put(MavCommand(command, toGive), block=True)



