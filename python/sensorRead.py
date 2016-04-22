import os
import glob
import time
import subprocess

# https://learn.adafruit.com/downloads/pdf/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing.pdf


def read_temp_raw(temp_device_file):
    f = open(temp_device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def read_temp(temp_device_file):
    lines = read_temp_raw(temp_device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(temp_device_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp = float(temp_string) / 1000.0
        return temp


def read_temp_raw2(temp_device_file):
    catdata = subprocess.Popen(['cat',temp_device_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = catdata.communicate()
    out_decode = out.decode('utf-8')
    lines = out_decode.split('\n')
    return lines


def sensorReadLoop(sensors, sensorLock):

    # Thermometer setup
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')
    base_dir = '/sys/bus/w1/temp_devices/'
    temp_device_folder = glob.glob(base_dir + '28*')[0]
    temp_device_file = temp_device_folder + '/w1_slave'

    # Loop reading sensors
    while True:
        temp = read_temp(temp_device_file)
        with sensorLock:
            sensors.temperature = temp
        time.sleep(1)

