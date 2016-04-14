#!/usr/bin/env python
import time
import subprocess

# Full list of Exposure and White Balance options
#list_ex  = ['off','auto','night','nightpreview','backlight',
#            'spotlight','sports','snow','beach','verylong',
#            'fixedfps','antishake','fireworks']
#list_awb = ['off','auto','sun','cloud','shade','tungsten',
#            'fluorescent','incandescent','flash','horizon']

# Refined list of Exposure and White Balance options. 50 photos.
#list_ex  = ['off','auto','night','backlight','fireworks']
#list_awb = ['off','auto','sun','cloud','shade','tungsten',
#            'fluorescent','incandescent','flash','horizon']

def takePhotos(interval):
# Photo dimensions and rotation
    photoWidth  = 640
    photoHeight = 480

    while True:
        filename = "photos/" + str(int(time.time()*1000)) + ".jpg"
        cmd = 'raspistill -o ' + filename + \
            ' -t 1 ' + \
            ' -w ' + str(photoWidth) + \
            ' -h ' + str(photoHeight)
        pid = subprocess.call(cmd, shell=True)

        time.sleep(interval)
