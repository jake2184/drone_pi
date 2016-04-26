


import time
import grovepi

# Connect the Grove Air Quality Sensor to analog port A0
#interrupt to D4
# SIG,NC,VCC,GND
air_sensor = 0
sensor = 4


while True:
    try:
        # Get sensor value
        grovepi.pinMode(air_sensor,"INPUT")
        sensor_value = grovepi.analogRead(air_sensor)

        if sensor_value > 700:
            print ("High pollution")
        elif sensor_value > 300:
            print ("Low pollution")
        else:
            print ("Air fresh")

        print("sensor_value =", sensor_value)
        time.sleep(.5)


        grovepi.pinMode(sensor, "INPUT")


        # Sensor returns LOW and onboard LED lights up when the
        # received infrared light intensity exceeds the calibrated level
        if grovepi.digitalRead(sensor) == 0:
            print ("found something")
        else:
            print ("nothing")

        time.sleep(.5)

    except IOError:
        print ("Error")