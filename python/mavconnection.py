#!/usr/bin/env python


import sys
import atexit
import time
import Queue, threading
from pymavlink import mavutil


class MavCommand:
	def __init__(self, name, args):
		self.name = name
		self.args = args


class MavConnection:
	def __init__(self):
		# create a mavlink serial instance
		device = "com4"
		self.master = mavutil.mavlink_connection(device, 57600, dialect="pixhawk")
		self.ts = self.master.target_system
		self.tc = self.master.target_component
		print (self.ts)
		print(self.tc)

		atexit.register(self.closeLink)
		self.logfile = open("log.txt", 'w')
		self.paramfile = open("params.txt", 'w')
		# wait for the heartbeat msg to find the system ID
		self.wait_heartbeat()

		self.commands = {
			"logRequest" : self.master.mav.log_request_list_send,
			"messageInterval" : self.master.mav.message_interval_send,
			"sendCommand" : self.master.mav.command_int_send,
			"dataStreamRequest" : self.master.mav.request_data_stream_send,
			"getParam" : self.master.mav.param_request_read_send,
			"paramListRequest" : self.master.mav.param_request_list_send
		}

	def wait_heartbeat(self):
		print("Waiting for heartbeat")
		self.master.wait_heartbeat()

	def closeLink(self):
		print("Ending")
		self.master.close()

	def log(self, msg):
		string = str(msg.id) + " " + msg.name + " {"
		for field in msg.ordered_fieldnames:
			toAdd = field + ":" + str(getattr(msg, field)) + ", "
			string += toAdd
		string = string[:-2]
		string += " }\n"
		self.logfile.write(string)

	def paramLog(self, msg):
		string = msg.param_id + "\t\t\t" + str(msg.param_value) + "\n"
		self.paramfile.write(string)

	def setRC(self):
		self.master.param_set_send("RC_MAP_THROTTLE", float(3))
		self.master.param_set_send("RC_MAP_PITCH", float(2))
		self.master.param_set_send("RC_MAP_YAW", float(4))
		self.master.param_set_send("RC_MAP_ROLL", float(1))
		self.master.param_set_send("RC_MAP_MODE_SW", float(5))
		self.master.param_set_send("RC_CHAN_CNT", float(5))

	def setPWM(self):
		self.master.param_set_send("PWM_MIN", float(1000))
		self.master.param_set_send("PWM_MAX", float(2000))
		self.master.param_set_send("PWM_AUX_MIN", float(1000))
		self.master.param_set_send("PWM_AUX_MAX", float(2000))
		self.master.param_set_send("PWM_DISARMED", float(1000))
		self.master.param_set_send("PWM_AUX_DISARMED", float(1000))

	def setMisc(self):
		self.master.param_set_send("MAV_TYPE", float(2))
		self.master.param_set_send("CBRK_GPSFAIL", float(0))
		self.master.param_set_send("COM_DL_LOSS_T", float(10))
		self.master.param_set_send("COM_RC_IN_MODE", float(0))
		self.master.param_set_send("BAT_N_CELLS", float(3))
		self.master.param_set_send("COM_AUTOS_PAR", float(1))
		self.master.param_set_send("CBRK_AIRSPD_CHK", 162128)
		#self.master.param_set_send("CBRK_AIRSPD_CHK", float(2.27189717424e-40))
		self.master.param_set_send("CBRK_IO_SAFETY", float(22027))
		self.master.param_set_send("CBRK_USB_CHK", float(197848))


	def monitorMessages(self, gps, GPSLock, sensors, sensorLock, mavCommandList):
		'''show incoming mavlink messages'''
		msg_count = 0
		msgTypes = []
		gotParams=False
		while True:
			msg = self.master.recv_msg()#blocking=True)
			if msg:
				t = msg.get_type()
				if t == "BAD_DATA":
					if mavutil.all_printable(msg.data):
						sys.stdout.write(msg.data)
						sys.stdout.flush()
				elif t == "HEARTBEAT":
					pass
				elif t == "ATTITUDE_TARGET":
					pass
				elif t == "ATTITUDE":
					pass
				else:

					if t not in msgTypes:
						print(t)
						msgTypes.append(t)

					self.log(msg)
					msg_count += 1
					if msg_count == 20:
						pass
					if msg_count == 40:
						pass
						#self.setRC()
						#self.setPWM()
						#self.setMisc()
					if msg_count == 60:
						print("Request all params2")
						self.logfile.flush()
						self.master.param_fetch_all()

					if gotParams:
						print("Setting mode")
						gotParams = False
						#self.master.set_mode_manual()
						self.master.arducopter_arm()

					if t == "GPS_RAW_INT":
						self.updateGPS(msg, gps, GPSLock)
					#elif t == "VFR_HUD":
					#	pass
					#elif t == "HIGHRES_IMU":
					#	pass
					elif t == "PARAM_VALUE":
						self.paramLog(msg)
						if msg.param_index == msg.param_count - 1:
							print("Got all parameters?")
							gotParams = True
							self.paramfile.flush()


					else:
						#print(str(msg_count) + " " + msg.name )
						pass
						# if msg_count == 10:
						# 	mavCommandList.put(MavCommand("logRequest", [self.ts, self.tc, 0x0, 0xffff]), block=True)
						#
						# if msg_count == 20:
						# 	mavCommandList.put(MavCommand("dataStreamRequest",[self.ts,self.tc,0x1,0x1, 0x0]), block=True)
						#
						# if msg_count == 30:
						# 	mavCommandList.put(MavCommand("dataStreamRequest", [self.ts, self.tc, 0x3, 0x1, 0x1]),
						# 					   block=True)


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
		print("Sending " + mavCommand.name)
		try:
			self.commands[mavCommand.name](*mavCommand.args)
			time.sleep(1)
		except KeyError as e:
			print(e)

		#print("Sending req")
		self.master.mav.log_request_list_send(self.ts, self.tc, 0, 65535)


	def mavset(self, name, value, retries=3):
		'''set a parameter on a mavlink connection'''
		got_ack = False
		while retries > 0 and not got_ack:
			retries -= 1
			self.master.mav.param_set_send(self.ts, self.tc, name.upper(), float(value), 1)
			tstart = time.time()
			while time.time() - tstart < 1:
				ack = self.master.recv_match(type='PARAM_VALUE', blocking=False)
				if ack == None:
					time.sleep(0.1)
					continue
				if str(name).upper() == str(ack.param_id).upper():
					got_ack = True
					print("Got ack")
					break
		if not got_ack:
			print("timeout setting %s to %f" % (name, float(value)))
			return False
		return True


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
	mavLoop(gps, gpsLock, sensors, sensorLock, q)







