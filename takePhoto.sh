#!/bin/bash




while [ 1 ]
do
	#DATE=$(date +"%Y-%m-%d_%H%M")
	DATE=$(($(date +%s%N)/1000000))
	echo "Taking shot.."
	raspistill  -h 480 -w 640 -t 1 -o /home/pi/drone_pi/photos/$DATE.jpg
	echo "Done."
	sleep 1
done
