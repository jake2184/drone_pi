#!/bin/bash

BASEURL=$1
ENDPOINT="/imageUpload"
PHOTODIR="testPhotos"

for i in $(ls $PHOTODIR)
do
	TOTAL=0
	stat -c "Name: %n        Size: %s" $PHOTODIR"/"$i
	for j in {1..10}
	do
		URL=$BASEURL$ENDPOINT
		START=$(date +%s%3N)
		curl -POST -s  -F "image=@${PHOTODIR}/${i}"  $URL -o /dev/null
		END=$(date +%s%3N)
		let DURATION=$END-$START
		echo -n $DURATION"," 
		let TOTAL=$TOTAL+$DURATION
		sleep 1
	done
	let AVERAGE=$TOTAL/10
	echo ""
	echo "Average Upload: "$AVERAGE" milliseconds"
	echo ""
done
