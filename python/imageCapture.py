#!/usr/bin/env python
import time
import subprocess
from copy import copy

# Full list of Exposure and White Balance options
# list_ex  = ['off','auto','night','nightpreview','backlight',
#            'spotlight','sports','snow','beach','verylong',
#            'fixedfps','antishake','fireworks']
# list_awb = ['off','auto','sun','cloud','shade','tungsten',
#            'fluorescent','incandescent','flash','horizon']

# Refined list of Exposure and White Balance options. 50 photos.
# list_ex  = ['off','auto','night','backlight','fireworks']
# list_awb = ['off','auto','sun','cloud','shade','tungsten',
#            'fluorescent','incandescent','flash','horizon']


def takePhotos(status, statusLock):

	while True:
		with statusLock:
			# Get variables from status object
			capturingImages = copy(status.capturingImages)
			interval = copy(status.photoInterval)
			resolution = copy(status.photoResolution)
			quality = copy(status.photoQuality)

		if capturingImages:
			resolution = resolution.split('x')
			# Create image file with current time as name

			filename = "photos/" + str(int(time.time()*1000)) + ".jpg"
			cmd = 'raspistill -o ' + filename + \
				' -t 1 ' + \
				' -w ' + resolution[0] + \
				' -h ' + resolution[1] + \
				' -q ' + str(quality)
			pid = subprocess.call(cmd, shell=True)
			#print("Took image.")

		# Sleep for time interval (/1000 for milliseconds to secs)
		time.sleep(interval / 1000)
