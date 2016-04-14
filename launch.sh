#!/bin/bash


./takePhoto.sh &
./sendPhoto.sh &
python main.py
