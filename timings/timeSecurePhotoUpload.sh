
#!/bin/bash

BASEURL=$1
TOTAL=0
ENDPOINT="/imageUploadSecure"
echo $(ls -l $2)
for i in {1..10}
do
	LATEST=$2
	URL=$BASEURL$ENDPOINT
	START=$(date +%s%3N)
	curl -POST -s -F "image=@${LATEST}"  $URL -o /dev/null --user Drone:Pi
	END=$(date +%s%3N)
	let DURATION=$END-$START
	let TOTAL=$TOTAL+$DURATION
	#echo $DURATION
	sleep 1
done
let AVERAGE=$TOTAL/10
echo "Average Upload: "$AVERAGE" milliseconds"
