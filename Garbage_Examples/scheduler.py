"""
David Carlson & Bryce Martin
ECE 4800 Senior Design Project

This File represents interactions of the Pi and Sprinkler Relays (GPIO)
It will server as the timer program

Tested in Python3.7 and 3.4(RPi)
"""
from time import sleep
from datetime import datetime
from sys import platform
from collections import deque
import datalocker
if platform == "linux":
    import busio
    import digitalio
    import board

    relays = [digitalio.DigitalInOut(board.D26),  # Sector 1
          digitalio.DigitalInOut(board.D19),  # Sector 2
          digitalio.DigitalInOut(board.D13),  # Sector 3
          digitalio.DigitalInOut(board.D6)]  # Sector 4
else:
    import fakedata
    relays = [fakedata.fakeIO2(0), fakedata.fakeIO2(1), fakedata.fakeIO2(2), fakedata.fakeIO2(3)]


watering_queue = []
days_of_week = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

light_avg = [0] * len(datalocker.SensorStats)
last_seen = [0] * len(datalocker.SensorStats)


def sprinkler_runner(DEBUG_MODE=False):
    start_time = 0
    if DEBUG_MODE:
        print("# TODO")  # TODO


    # Run thread as long as an interrupt isn't sent
    for relay in relays:
        if platform == "linux":
            relay.direction = digitalio.Direction.OUTPUT
        else:
            relay.direction = True
        relay.value = False

    while datalocker.ProgramRunning:
        # If the sprinkler system is enabled/on
        if datalocker.SystemEnabled:
            # Update the watering_queue and find missing sensors when a new Xbee packet is available
            if datalocker.get_new():
                print("New Data!")
                for sensor in datalocker.SensorStats:
                    if sensor is None:
                        continue

                    # Update last seen array
                    last_seen[sensor['Sector']] = sensor['Timestamp']

                    # Update light value arrays for every active sector
                    if datalocker.NodeHealthStatus[sensor['Sector']] != "Red":
                        light_avg.append(sensor['Sunlight'])

                    # Check for readings that are a day or older
                    if datetime.timestamp(datetime.now()) - last_seen[sensor['Sector']] > 86400:
                        print("Sector {}'s sensor has gone MIA!".format(sensor['Sector']))  # Inform the user
                        datalocker.NodeHealthStatus[sensor["Sector"]] = "Red"
                        # Note that this will execute every time new data is put into the sensorstats array
                    else:
                        datalocker.NodeHealthStatus[sensor["Sector"]] = "Green"

                    # If reading is less than user set threshold  # TODO -- How do we want to handle the threshold value?
                    if (sensor["Moisture"] > datalocker.thresholds["Dry"]
                        # AND not already in the wateringQue
                            and not next((item for item in watering_queue if item["Sector"] == sensor["Sector"]), False)):
                        # then add the sensor to the wateringQue
                        watering_queue.append(sensor)

                light_floor = sum(light_avg) / len(light_avg)
                light_floor = light_floor - 500  # I've set the number to 500 as the standard deviation will always flag one sector  
                                                # (Quick/Dirty stdev:  (max-min) / 4) ==> 4096 / 4 = 1024
                light_avg.clear()

                # Iterate through array once more to find outliers in light readings
                for sensor in datalocker.SensorStats:
                    if sensor is None:
                        continue
                    if sensor['Sunlight'] < light_floor:
                        print("Sector {}'s light is low compared to peers; It may need to be moved")
                        datalocker.NodeHealthStatus[sensor["Sector"]] = "Yellow"

            # Manage the watering queue by evaluating the current weather conditions
            # If conditions are met start watering, however fallback schedules are checked first
            if not start_time:
                current_time = int(datetime.now().strftime("%H%M"))
                day = days_of_week[datetime.today().weekday()]
                iterator = 0
                while iterator < len(datalocker.NodeHealthStatus):
                    if datalocker.NodeHealthStatus[iterator] == "Red" and datalocker.timer_triggering[day][0] and current_time == datalocker.timer_triggering[day][1]:
                        relays[iterator].value = True
                        start_time = datetime.timestamp(datetime.now())
                        if DEBUG_MODE:
                            datalocker.DEBUGSectorWatering[iterator] = datetime.now().strftime("%H%M")
                        watering_queue.append({'Sector': iterator})
                        print("MIA watering started")
                    iterator = iterator + 1

                if (len(watering_queue) > 0
                    and watering_queue[0]["Wind"] < datalocker.thresholds["Wind max"]
                    and (datalocker.thresholds["Prohibited time end"] <= current_time <= 2359
                         or current_time <= datalocker.thresholds["Prohibited time start"])
                    and watering_queue[0]["Humidity"] < datalocker.thresholds["Humidity max"]
                    and watering_queue[0]["Temperature"] > datalocker.thresholds["Temperature min"]
                    ):  # Then we have passed all tests

                    print("Sector: ", watering_queue[0]["Sector"], " watering has started.")
                    relays[watering_queue[0]["Sector"]].value = True
                    start_time = datetime.timestamp(datetime.now())
                    if DEBUG_MODE:
                        datalocker.DEBUGSectorWatering[watering_queue[0]["Sector"]] = datetime.now().strftime("%H%M")
        

            if (start_time and datetime.timestamp(datetime.now()) - start_time) > (datalocker.thresholds["Water Duration"] * 60):  # Convert to Min
                relays[watering_queue[0]["Sector"]].value = False
                print("Sector: ", watering_queue[0]["Sector"], " watering has ended.")
                popval = watering_queue.pop(0)
                start_time = 0
                if DEBUG_MODE:
                    datalocker.DEBUGSectorWatering[popval["Sector"]] = 0
                sleep(30)  # Give sprinkler system time to transistion
        
    #     else:
    #         for relay in relays:
    #            relay.value = False
            
    #         watering_queue.clear()
    #         start_time = 0
    #         if DEBUG_MODE:
    #             for sector in datalocker.DEBUGSectorWatering:
    #                 if sector != "UnSet" and sector > 0:
    #                     sector = 0
    
    # # System is going down! Turn off all sprinklers
    # for relay in relays:
    #     relay.value = False
