#https://stackoverflow.com/questions/892199/detect-record-audio-in-python
import threading
import requests
from sys import byteorder
from array import array
from struct import pack, unpack
import subprocess as sp

from copy import copy
import pyaudio
import wave
import time


from websocket import create_connection

THRESHOLD = 500
#CHUNK_SIZE = 1024
CHUNK_SIZE = 8192
FORMAT = pyaudio.paInt16
RATE = 44100
#RATE = 48000


def is_silent(snd_data):
	"Returns 'True' if below the 'silent' threshold"
	return max(snd_data) < THRESHOLD


def normalize(snd_data):
	"Average the volume out"
	MAXIMUM = 16384
	times = float(MAXIMUM)/max(abs(i) for i in snd_data)

	r = array('h')
	for i in snd_data:
		r.append(int(i*times))
	return r


def trim(snd_data):
	"Trim the blank spots at the start and end"
	def _trim(snd_data):
		snd_started = False
		r = array('h')

		for i in snd_data:
			if not snd_started and abs(i)>THRESHOLD:
				snd_started = True
				r.append(i)

			elif snd_started:
				r.append(i)
		return r

	# Trim to the left
	snd_data = _trim(snd_data)

	# Trim to the right
	snd_data.reverse()
	snd_data = _trim(snd_data)
	snd_data.reverse()
	return snd_data


def add_silence(snd_data, seconds):
	"Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
	r = array('h', [0 for i in xrange(int(seconds*RATE))])
	r.extend(snd_data)
	r.extend([0 for i in xrange(int(seconds*RATE))])
	return r


def record(volumeDetection, duration):
	"""
	Record a word or words from the microphone and
	return the data as an array of signed shorts.

	Normalizes the audio, trims silence from the
	start and end, and pads with 0.5 seconds of
	blank sound to make sure VLC et al can play
	it without getting chopped off.
	"""
	try:
		p = pyaudio.PyAudio()
		stream = p.open(format=FORMAT, channels=1, rate=RATE,
			input=True, output=True,
			frames_per_buffer=CHUNK_SIZE)
	except:
		return [], []
	p = pyaudio.PyAudio()

	stream = p.open(format=FORMAT, channels=1, rate=RATE,
		input=True, output=True,
		frames_per_buffer=CHUNK_SIZE)

	num_silent = 0
	snd_started = False

	r = array('h')

	if volumeDetection :
		while 1:
			# little endian, signed short
			snd_data = array('h', stream.read(CHUNK_SIZE))
			if byteorder == 'big':
				snd_data.byteswap()
			r.extend(snd_data)

			silent = is_silent(snd_data)
			#print(silent)
			if silent and snd_started:
				num_silent += 1
			elif not silent and not snd_started:
				snd_started = True

			if snd_started and num_silent > 20:
				break

	else :
		timeBegin = time.time()
		timeNow = timeBegin
		while timeNow - timeBegin < duration / 1000.0 :
			# little endian, signed short
			snd_data = array('h', stream.read(CHUNK_SIZE))
			if byteorder == 'big':
				snd_data.byteswap()
			r.extend(snd_data)

			timeNow = time.time()


	sample_width = p.get_sample_size(FORMAT)
	stream.stop_stream()
	stream.close()
	p.terminate()

	r = normalize(r)
	r = trim(r)
	r = add_silence(r, 0.5)
	return sample_width, r


def writeMP3File(fileName, data):
	pipe = sp.Popen([
	   "ffmpeg\\bin\\ffmpeg.exe",
	   "-f", 's16le', # means 16bit input
	   "-acodec", "pcm_s16le", # means raw 16bit input
	   '-r', "44100", # the input will have 44100 Hz
	   '-ac','1', # the input will have 1 channels (stereo)
	   '-i', '-', # means that the input will arrive from the pipe
	   '-vn', # means "don't expect any video input"
		fileName
	], stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)

	out, err = pipe.communicate(data)


def record_to_file(path, format, volumeDetection, duration):
	"Records from the microphone and outputs the resulting data to 'path'"
	sample_width, data = record(volumeDetection, duration)
	data = pack('<' + ('h'*len(data)), *data)
	currentTime = int(time.time() * 1000)

	print(format)
	if format == "mp3":
		here = path + "/" + str(currentTime) + ".mp3"
		print(here)
		writeMP3File(here, data)
	else:
		wf = wave.open(path + "/" + str(currentTime) + ".wav" , 'wb')
		wf.setnchannels(1)
		wf.setsampwidth(sample_width)
		wf.setframerate(RATE)
		wf.writeframes(data)
		wf.close()


def listen(sessionCookie):
	wf = wave.open("dump.wav", 'wb')
	wf.setnchannels(1)
	sample_width = pyaudio.PyAudio().get_sample_size(FORMAT)
	wf.setsampwidth(sample_width)
	wf.setframerate(RATE)
	ws2 = create_connection("ws://localhost:8080/api/pixhack/audio/stream/listen", cookie="session="+sessionCookie)

	if ws2.connected:
		while True:
			print("Waiting for data")
			result = ws2.recv()
			unpacked = unpack('<' + ('h' * (len(result) / 2)), result)
			data = pack('<' + ('h' * (len(unpacked))), *unpacked)
			wf.writeframes(data)
	else:
		print("Not connected")


def runAudioCapture(status, statusLock):

	while True:
		with statusLock:
			capturingAudio = copy(status.capturingAudio)
			volumeDetection = copy(status.volumeDetection)
			duration = copy(status.duration)


		if capturingAudio:
			record_to_file("audio", "mp3", volumeDetection, duration)
			print ("Made recording")
		else:
			time.sleep(1)


def streamAudio(status, statusLock, sessionCookie):


	while True:
		with statusLock:
			streamingAudio = copy(status.streamingAudio)

		if streamingAudio:
			print("Audio Streaming..")
			session = requests.utils.dict_from_cookiejar(sessionCookie)['session']
			try:
				p = pyaudio.pyAudio()
				stream = p.open(format=FORMAT, channels=1, rate=RATE,
							input=True, output=True,
							frames_per_buffer=CHUNK_SIZE)
			except:
				continue
			listenerThread = threading.Thread(target=listen, args=(sessionCookie,))
			listenerThread.daemon = True
			# listenerThread.start()

			try:
				endpoint = "ws://" + status.host + "/api/" + status.dronename + "/audio/stream/upload"
				ws = create_connection("ws://" + status.host + "/api/" + status.dronename + "/audio/stream/upload", cookie="session=" + session)
			except:
				print("Could not connect to websocket " + endpoint)
				continue

			result = ws.recv()
			print "Received '%s'" % result

			while streamingAudio:
				# little endian, signed short
				try:
					snd_data = array('h', stream.read(CHUNK_SIZE))
					if byteorder == 'big':
						snd_data.byteswap()

					byte_data = pack('<' + ('h' * len(snd_data)), *snd_data)

					ws.send_binary(byte_data)
					with statusLock:
						streamingAudio = copy(status.streamingAudio)
				except IOError:
					continue

			ws.close()
			stream.stop_stream()
			stream.close()
			p.terminate()
			print("Stopping audio stream.")





if __name__ == '__main__':
	#print("please speak a word into the microphone")
	#record_to_file('audio', "mp3")
	#print("done - result written to demo.wav")
	from main import Status
	import requests, sys
	from requests.auth import HTTPBasicAuth
	url = "http://localhost"
	port = ":8080"
	try:
		req = requests.get(url + port + "/login", timeout=2)
	except requests.exceptions.RequestException:
		print ("Cannot connect to " + url + port)
		sys.exit(0)

	# Try logging in
	req = requests.post(url + port + "/login", auth=HTTPBasicAuth('jake', 'pass'))
	sessionCookie = req.cookies
	import threading
	statusLock = threading.Lock()
	status = Status()
	status.capturingAudio = True
	streamAudio(status, statusLock, sessionCookie)
