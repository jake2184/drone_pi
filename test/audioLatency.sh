#!/bin/bash


URL=192.168.1.76:8080
#URL=https://drone-nodes.eu-gb.mybluemix.net
curl -X POST -u jake:pass $URL/login -c cookie -d ""

for i in {1..10}
do
    for i in $( ls audio );
    do
        DATE=$(($(date +%s%N)/1000000))
        curl -b cookie  -X POST -F "audio=@audio/${i}" $URL/api/test/audioLatency/${i} -F time=${DATE}
    done
done
sleep 20
curl -b cookie $URL/api/test/writeAudioFile

rm cookie