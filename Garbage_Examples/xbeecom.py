"""
David Carlson & Bryce Martin
ECE 4800 Senior Design Project

This File represents interactions of the Pi and Xbee3 coordinator (UART)
Tested in Python3.7(Windows) and 3.4(RPi)
"""
import json
import re
import datalocker
from datetime import datetime
from time import sleep
from sys import platform
if platform == "linux":
    import serial
    import busio
    import digitalio
    import board
    import adafruit_dht
    import adafruit_mcp3xxx.mcp3008 as MCP
    from adafruit_mcp3xxx.analog_in import AnalogIn
else:
    import fakedata
    busio = fakedata.fakeIO
    digitalio = fakedata.fakeIO
    board = fakedata.fakeIO
    serial = fakedata.fakeIO
    adafruit_dht = fakedata.fakeIO
    MCP = fakedata.fakeIO
    AnalogIn = fakedata.fakeIO

    

    
    
    



    
    
    
    

# The Xbee (under MicroPython API) forwards a byte object/string that
# needs to be formatted before we can manipulate it as a data object
# We are 'JSON'ifying the data
def convert_to_dict(bytes_in, DEBUG_MODE=False):
    # Here is what the Xbee will send:
    # {'profile': 49413, 'dest_ep': 232,
    #   'broadcast': False, 'sender_nwk': 38204,
    #   'source_ep': 232, 'payload': b'{Iteration: 0, ...more Key:Value pairs here..., ADCRead: 169, Zone: 2}',
    # We are interested in manipulating/saving the payload value(s)
    #   'sender_eui64': b'\x00\x13\xa2\x00A\x99O\xcc',        ### NOTE This is the MAC Addr: A = 41, O = 4F
    #   'cluster': 17}
    temp = str(bytes_in, "utf-8")  # Convert byte data into a string
    # if DEBUG_MODE:
    #     print("In convert_to_dict" + temp)
    
    split_list = re.split("('payload': )|('sender_eui64': )", temp)  # Isolating the payload string before we attempt JSON'ifying it

    # If we have a bad payload/message we should not continue
    if len(split_list) < 7:
        raise Exception("Split list failed")

    # Extract the payload element/portion from the xbee message
    # split_list ==> [ "{'profile': 49413, 'dest_ep': 232, 'broadcast': False, 'sender_nwk': 38204, 'source_ep': 232, "
    #               , 'payload':
    #               , None
    #               , "b'{'Iteration': 0, 'Value': 345, 'Zone': 2}',}'"
    #               , None
    #               , "'sender_eui64':"
    #               , "b'\x00\x13\xa2\x00A\x99O\xcc', 'cluster': 17}"]

    payload = "{" + split_list[1] + split_list[3][2:]     # ==> {'payload': {'Iteration': 0, 'Value': 345, 'Zone': 2}',
    payload = payload[:-3] + "}"                        # ==> {'payload': {'Iteration': 0, 'Value': 345, 'Zone': 2}}
    temp = split_list[0] + split_list[5] + split_list[6]   # ==> {'profile': 49413, 'dest_ep': 232, 'broadcast': False, 'sender_nwk': 38204, 'source_ep': 232, 'sender_eui64': b'\x00\x13\xa2\x00A\x99O\xcc', 'cluster': 17}

    # Get our modified strings ready for JSON-ification
    payload = payload.replace("\'", "\"").replace("b\"", "\"").replace("\\", "\\\\").replace("False", "false").replace("True", "true")
    temp = temp.replace("\'", "\"").replace("b\"", "\"").replace("\\", "\\\\").replace("False", "false").replace("True", "true")

    # And convert to JSON / Dictionary objects
    payload = json.loads(payload)
    temp = json.loads(temp)
    temp.update(payload)  # Merge dictionaries -- get the payload into the object

    returndict = {}
    for keys in payload["payload"].keys():
        returndict[keys] = payload["payload"][keys]

    return returndict  #temp  # Returns a nested Dictionary Object


def log_data(payload):
    with open("log.csv", 'a') as file_out:
        file_out.write("{}/{}/{}, {}:{}, Unix Epoch: {}, Sector #{}, Moisture {}, Sunlight {}, Battery {}mV, "
                       "Temperature {}C, Humidity {}%, Wind {}m/s".format(
            str(payload['Year']), str(payload['Month']), str(payload['Day']),
            str(payload['Hour']), str(payload['Minute']), str(payload['Timestamp']),
            str(payload['Sector']), str(payload['Moisture']), str(payload['Sunlight']),
            str(payload['Battery']), str(payload['Temperature']), str(payload['Humidity']),
            str(payload['Wind'])
        ))
    file_out.close()


def talk_to_xbee(DEBUG_MODE=False):
    if DEBUG_MODE:
        print("# TODO")  # TODO
    
    serial_set = False

    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    cs = digitalio.DigitalInOut(board.D25)
    mcp = MCP.MCP3008(spi, cs)
    anemometer = AnalogIn(mcp, MCP.P0)

    dht = adafruit_dht.DHT22(board.D21)

    speed_average = [0, 0, 0, 0, 0]
    temp_average = [0, 0, 0, 0, 0]
    humidity_average = [0, 0, 0, 0, 0]
    pointer = 0

    while not serial_set and datalocker.ProgramRunning:
        try:
            # The Miniuart (ttyS0) is used on the Raspberry Pi
            # The full UART is connected to the onboard Bluetooth device
            # Default settings: 8bits, no parity, 1 stopbit, baud 9600
            # Timeout can be set as Serial("/dev/ttyS0", 115200, timeout = 5) in seconds
            # Timeout will stop the readline() function, no timeout implies the function will run until data is received
            port = serial.Serial("/dev/ttyS0", 115200)
            serial_set = True
        except serial.SerialException:
            print("Serial connection failed, trying again...")

    while pointer < 5 and datalocker.ProgramRunning:
        try:
            temp_average[pointer] = dht.temperature
            humidity_average[pointer] = dht.humidity
            pointer = pointer + 1
        except RuntimeError as e:
            sleep(10)
            print("dht-setup")
    pointer = 0

    # Possibly average this value
    anemometer_offset = anemometer.voltage

    while pointer < 5 and datalocker.ProgramRunning:
        try:
            speed_average[pointer] = abs((anemometer.voltage - anemometer_offset) * 20.25)
            pointer = pointer + 1
        except RuntimeError as e:
            sleep(10)
            print("anemo-setup")
    pointer = 0

    while datalocker.ProgramRunning:

        if port.inWaiting() > 0:
            temp = convert_to_dict(port.readline(), DEBUG_MODE)
            temp['Timestamp'] = int(datetime.timestamp(datetime.now()))
            temp['Minute'] = datetime.now().minute
            temp['Hour'] = datetime.now().hour
            temp['Day'] = datetime.now().day
            temp['Month'] = datetime.now().month
            temp['Year'] = datetime.now().year
            temp['Temperature'] = sum(temp_average)/len(temp_average)
            temp['Humidity'] = sum(humidity_average)/len(humidity_average)
            temp['Wind'] = sum(speed_average)/len(speed_average)

            if datalocker.NodeHealthStatus[temp["Sector"]] == "Red":
                log_data(temp)

            # if DEBUG_MODE:
            #     print(temp)

            datalocker.SensorStats[temp.get('Sector')] = temp
            datalocker.set_new()

        if datetime.now().minute / 2 == 0:
            try:
                speed_average[pointer] = abs((anemometer.voltage - anemometer_offset) * 20.25)
                pointer = (pointer + 1) % 5
            except RuntimeError as e:
                print("Wind speed retrieve failed")

            try:
                temp_average[pointer] = dht.temperature
                humidity_average[pointer] = dht.humidity
                pointer = (pointer + 1) % 5
            except RuntimeError as e:
                print("Temp/Humidity")

    port.close()
