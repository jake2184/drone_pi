#!/bin/bash


curl -X POST -u jake:pass 192.168.1.77:8080/login -c cookie


for i in $( ls photos );
do
	curl -b cookie  -X POST -F "image=@photos/${i}" 192.168.1.77:8080/api/test/imageLatency/${i}
done
