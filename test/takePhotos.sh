#!/bin/bash


WIDTHS=(854 1280 1600 1920)
HEIGHTS=(480 720 900 1080)

for i in `seq 0 3`
do
	NAME=${WIDTHS[$i]}x${HEIGHTS[$i]}
	echo Capturing $NAME x4
	DATE=$(($(date +%s%N)/1000000))
	echo "Taking shots.."
	QUAL=25
	raspistill  -h ${HEIGHTS[$i]} -w ${WIDTHS[$i]} -q $QUAL -t 1 -o /home/pi/drone_pi/test/photos/${NAME}q$QUAL.jpg
	QUAL=50
	raspistill  -h ${HEIGHTS[$i]} -w ${WIDTHS[$i]} -q $QUAL -t 1 -o /home/pi/drone_pi/test/photos/${NAME}q$QUAL.jpg
	QUAL=75
	raspistill  -h ${HEIGHTS[$i]} -w ${WIDTHS[$i]} -q $QUAL -t 1 -o /home/pi/drone_pi/test/photos/${NAME}q$QUAL.jpg
	QUAL=100
	raspistill  -h ${HEIGHTS[$i]} -w ${WIDTHS[$i]} -q $QUAL -t 1 -o /home/pi/drone_pi/test/photos/${NAME}q$QUAL.jpg
	echo "Done."
	sleep 1
done
