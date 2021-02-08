"""
Author: Jayden Smith

Last Modified: February 8, 2021

filename: main.py

ECE 4020 - Senior Project II

Network setup pulled for XBee3 quick setup/start

This code runs on the XBee3 acting as a router node receiving temperature
and humidity data it collects from the HDC1080. This data is then relayed
to the coordinator XBee3. This XBee3 samples every 15 minutes.
"""

from hdc1080 import HDC1080
from machine import I2C
import time
import xbee

# sleep time in ms
# 60 * 1000 -> time in ms, so 60 seconds here
SLEEP_TIME = 900 * 1000  # sample every 15 minutes

# Set the identifying string of the radio
xbee.atcmd("NI", "Sensor Probe")

# Configure some basic network settings
network_settings = {"AV": 0, "EE": 0, "ID": 0xABCD, "SM": 6, "NJ": 0x20}

for command, value in network_settings.items():
    xbee.atcmd(command, value)
xbee.atcmd("AC")  # Apply changes
time.sleep(1)

# Query AI until it reports success
print("Connecting to network, please wait...")
while xbee.atcmd("AI") != 0:
    time.sleep_ms(100)

#  xbee.transmit(xbee.ADDR_COORDINATOR, "{'Humidity': 8, 'Temperature': 55}")
print("Connected to Network\n")

operating_network = ["OI", "OP", "CH"]
print("Operating network parameters:")
for cmd in operating_network:
    print("{}: {}".format(cmd, xbee.atcmd(cmd)))
# Wait for hub acknowledgement

# Instantiate the HDC1080 peripheral.
sensor = HDC1080(I2C(1))

# Initialize variables
iteration = 0
MAX_SAMPLES = 7
temp_f = 0
temp_avg_f = 0
humidity = 0
humidity_avg = 0

# Start reading temperature and humidity measures.
while True:
    # calculate averages after MAX_SAMPLES iterations
    if iteration >= MAX_SAMPLES:
        temp_avg_f = temp_f / MAX_SAMPLES
        humidity_avg = humidity / MAX_SAMPLES
        iteration = 0
        temp_f = 0
        humidity = 0

        try:
            # print and send results:
            print("Temperature (F): " + str(temp_avg_f) +
                  "\nHumidity: " + str(humidity_avg) + "\n")
            xbee.transmit(xbee.ADDR_COORDINATOR,
                          ("{'Temperature': " + str(temp_avg_f) +
                           ", 'Humidity': " + str(humidity_avg) + "}"))
        except Exception as err:
            print(err)

        # put the sensor node in deep sleep for SLEEP_TIME ms
        xbee.XBee().sleep_now(SLEEP_TIME, pin_wake=False)

        # reconnect to Zigbee network
        while xbee.atcmd("AI") != 0:
            time.sleep_ms(100)

    else:
        # continue to next iteration, reset averages
        time.sleep_ms(100)
        iteration += 1
        temp_f += sensor.read_temperature(False)
        humidity += sensor.read_humidity()
