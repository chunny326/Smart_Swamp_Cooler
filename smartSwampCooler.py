import mysql.connector
import sys
import json
import time
import serial
import RPi.GPIO as GPIO
from datetime import datetime
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# ---------------------- Pi 4 Serial Functionality ---------------------- # 
# 
# Setup for Serial port to match Zigbee protocol
ser = serial.Serial(
    port = '/dev/ttyS0',
    baudrate = 115200,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 1
)

# Read and return data in the serial receive buffer
def read_serial():
    return ser.readline()

# Write data out the serial pin
def write_serial(the_char):
    ser.write(the_char)

# Clear the serial read buffer
def flush_read_buffer():
    ser.reset_input_buffer()

# Wait for a response to be received on serial line or a timeout to occur.
# Return the response (which may be an empty string if nothing received)
def wait_for_serial_response(timeout):
    response = read_serial()
    timer = 0
    while response == "" and timer < timeout:
        print("  . ({})").format(timeout-timer)
        timer += 1
        time.sleep(1)
        response = read_serial()
    return response

def reset_serial_port():
    # close/open serial port
    ser.close()
    time.sleep(1)
    ser.open()

    # flush 
    flush_read_buffer()

# ---------------------------------------------------------------------- #  

# ----------------------- Database Functionality ----------------------- #  
# 
#  Define a class for holding database entry information
class SensorData:
    def __init__(self, id="-1", sensor_id="-1", temperature=32.5, humidity=25.7):
        self.id = id
        self.sensor_id = sensor_id
        self.temperature = temperature
        self.humidity = humidity

# Connect the mySQL database and provide login credentials
smartswampcooler_db = mysql.connector.connect(
  host="localhost",
  database="smartswampcooler",
  user="pi",
  passwd="jeniffer",
)

# Select all data from the sensor_data table
SQL_SELECT_DATA = "SELECT * FROM sensor_data"

# Insert new row of Sensor Data
SQL_INSERT_DATA = """
 INSERT INTO sensor_data (sensor_id, timestamp, temperature, humidity)
 VALUES (%s, UTC_TIMESTAMP(), %s, %s)
"""

# Maps database data to cooler object
def map_to_object(data):
  try:
    # assign database fields to object
    cooler.id                      = (data["id"])
    cooler.sensor_id               = (data["sensor_id"])
    cooler.timestamp               = str(data["timestamp"])
    cooler.temperature             = (data["temperature"])
    cooler.humidity                = (data["humidity"])
  
  except Exception as ex:
    print("Error mapping database data to cooler object")
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print(message)
    return cooler 
  
  return cooler

# Read out all entries from the databse
def read_db():
  mycursor = smartswampcooler_db.cursor()
  #params = (unitID,)
  mycursor.execute(SQL_SELECT_DATA) #, params)

  row_headers = [x[0] for x in mycursor.description] # this will extract row headers
  myresult = mycursor.fetchall()

  # for x in myresult:
  #   print(x)

  json_data = []
  for result in myresult:
    json_data.append(dict(zip(row_headers,result)))

  data = json.dumps(json_data, indent=4, sort_keys=True, default=str)
  data = json.loads(data)
  #data = data[0]
  #print(data) # print json_data
  
  # print out all json data entries
  for i in range(len(data)):
      print(data[i])
      cooler = map_to_object(data[i])
  
  return cooler

# Insert new sensor data to the database
def write_db(cooler):
  print("Inserting new sensor data...")

  mycursor = smartswampcooler_db.cursor()

  params = (cooler.sensor_id, cooler.temperature, cooler.humidity)

  mycursor.execute(SQL_INSERT_DATA, params)
  smartswampcooler_db.commit()

  print(mycursor.rowcount, "record(s) affected")

def xbee_to_object(xb_data):
    # convert xb byte data to a string
    xb_string = str(xb_data, "utf-8")
    xb_dict = json.loads(xb_string) 

    # check if temperature and humidity are valid values
    # if !isinstance(xb_dict["Temperature"], float) or 
    #    !isinstance(xb_dict["Humidity']"], float):
    #    print("Sensor readings are invalid values\n")

    # check sensor unique 64-bit identifier
    # 0 if inside, 1 if outside
    if xb_dict["sender_eui64"] == "\x00\x13\xa2\x00A\xc2\x12\x16":
        sensor_id = 0
    # TODO: add in outside 64-bit identifier
    else if xb_dict["sender_eui64" == "\x..."]:
        sensor_id = 1
    else 
        print("Unrecognized Zigbee sensor id.\n")
        return -1
    
    cooler = SensorData(id=7, sensor_id=sensor_id, 
                        temperature=xb_dict["Temperature"],
                        humidity=xb_dict["Humidity"])
    return cooler

# ---------------------------------------------------------------------- #
if __name__== "__main__":
  # verify accuracy of timestamp inputs
  # curr_time = datetime.datetime.utcnow()
  # print curr_time

  # verify writing to the database with SensorData class and db functions above
  # cooler = SensorData()
  # cooler = read_db()
  # new_data = SensorData(id="7", sensor_id="1", temperature=10.1, humidity=150.2)
  # write_db(new_data)  
  # read_db()

  while(1):  
    # check contents of the database
    cooler = read_db()

    xb = wait_for_serial_response(30)

    if xb != "":
        sensor_db_entry = xbee_to_object(xb)
        print(sensor_db_entry)
        # write_db(sensor_db_entry)

    # flush serial input buffer and reopen port
    reset_serial_port()
  
    # check updated database contents
    # read_db()

    print("Finished")