#!/bin/bash


#URL=192.168.1.77:8080
URL=https://drone-nodes.eu-gb.mybluemix.net
curl -X POST -u jake:pass $URL/login -c cookie -d ""


for i in $( ls photos );
do
	DATE=$(($(date +%s%N)/1000000))
	curl -b cookie  -X POST -F "image=@photos/${i}" $URL/api/test/imageLatency/${i} -F time=${DATE}
done

rm cookie