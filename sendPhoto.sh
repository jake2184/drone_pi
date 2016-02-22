
#!/bin/bash

LASTSENT=""
BASEURL="http://192.168.1.76"
PORT=8080
ENDPOINT="/image"
while [ 1 ]
do
	LATEST=$(ls photos | sort -rn | head -n1)
	if [ "$LATEST" != "$LASTSENT" ]; then
		URL=$BASEURL":"$PORT$ENDPOINT
		echo $URL
		curl -POST -v -F "image=@photos/${LATEST}"  $URL
		LASTSENT=$LATEST
		echo $LASTSENT
	fi
	sleep 1
done
