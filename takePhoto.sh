#!/bin/bash




while [ 1 ]
do
	DATE=$(date +"%Y-%m-%d_%H%M")
	echo "Taking shot.."
	raspistill -h 480 -w 640 -o /home/pi/photos/$DATE.jpg
	echo "Done."
	sleep 1
done
