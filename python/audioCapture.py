# Acknowledgement for aid from StackOverflow user `cryo`
# https://stackoverflow.com/questions/892199/detect-record-audio-in-python

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
RATE = 44100 #TODO set from status


from sys import platform as _platform
if _platform =="win32":
	ffmpeg = "ffmpeg\\bin\\ffmpeg.exe"
else:
	ffmpeg = "ffmpeg"

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
	blank sound
	"""
	try:
		p = pyaudio.PyAudio()
		stream = p.open(format=FORMAT, channels=1, rate=RATE,
			input=True, output=True,
			frames_per_buffer=CHUNK_SIZE)
	except IOError as e:
		if e.errno == -9996:
			# No microphone, thread should exit
			exit(1)
		return [], []

	num_silent = 0
	snd_started = False

	r = array('h')

	if volumeDetection :
		while 1:
			# little endian, signed short
			try:
				snd_data = array('h', stream.read(CHUNK_SIZE))
			except:
				continue
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
			try:
				snd_data = array('h', stream.read(CHUNK_SIZE))
			except:
				continue
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


# Use ffmpeg to write to file
def writeMP3File(fileName, data):
	pipe = sp.Popen([
		ffmpeg,
		"-f", 's16le', # 16bit input
		"-acodec", "pcm_s16le", # raw 16bit input
		'-r', "44100", # sampling frequency
		'-ac','1', # Mono channels
		'-i', '-', # Input from the pipe
		'-vn', # No video
		fileName
	], stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)

	out, err = pipe.communicate(data)


# Record audio to file
def record_to_file(path, format, volumeDetection, duration):
	sample_width, data = record(volumeDetection, duration)
	if not data:
		# Likely caused by no mic
		time.sleep(1)
		return
	data = pack('<' + ('h'*len(data)), *data)
	currentTime = int(time.time() * 1000)

	fileName = path + "/" + str(currentTime)
	if format == "mp3":
		writeMP3File(fileName + ".mp3", data)
	else:
		wf = wave.open(fileName + ".wav" , 'wb')
		wf.setnchannels(1)
		wf.setsampwidth(sample_width)
		wf.setframerate(RATE)
		wf.writeframes(data)
		wf.close()
	print ("Made recording " + fileName)

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


# If enabled, repeatedly save audio files
def runAudioCapture(status, statusLock):

	while True:
		with statusLock:
			capturingAudio = copy(status.capturingAudio)
			volumeDetection = copy(status.volumeDetection)
			duration = copy(status.audioDuration)
			fileType = copy(status.audioFileType)

		if capturingAudio:
			record_to_file("audio", fileType, volumeDetection, duration)
		else:
			time.sleep(1)


# If enabled, upload audio stream
def streamAudio(status, statusLock, sessionCookie):

	while True:
		with statusLock:
			streamingAudio = copy(status.streamingAudio)

		if streamingAudio:
			#print("Audio Streaming..")
			session = requests.utils.dict_from_cookiejar(sessionCookie)['session']
			# Try to open record stream.
			try:
				p = pyaudio.pyAudio()
				stream = p.open(format=FORMAT, channels=1, rate=RATE,
							input=True, output=True,
							frames_per_buffer=CHUNK_SIZE)
			except:
				continue

			# listenerThread = threading.Thread(target=listen, args=(sessionCookie,))
			# listenerThread.daemon = True
			# listenerThread.start()

			try:
				if "192" in status.host:
					protocol = "ws://"
				else:
					protocol = "wss://"

				endpoint = protocol + status.host + "/api/" + status.dronename + "/audio/stream/upload"
				ws = create_connection(endpoint, cookie="session=" + session)
			except:
				#print("Could not connect to websocket " + endpoint)
				continue

			# Receive initial response from the server
			result = ws.recv()

			while streamingAudio:
				# little endian, signed short
				# Same principle as saving wav file, but is sent on websocket
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
			#print("Stopping audio stream.")
		else:
			time.sleep(1)





if __name__ == '__main__':
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
