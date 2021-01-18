# To install mysql database driver on Raspberry Pi 3
# sudo apt-get update
# sudo apt-get upgrade
# sudo apt-get -y install python-mysql.connector
# NOTE: In GoDaddy/cPanel the Raspberry Pi's IP Address
# needs to be added to the Remote MySQL Access Hosts as well
# or the database connection will be refused.

import mysql.connector
import sys
import json
from datetime import datetime

class SensorData:
    def __init__(self, id="-1", sensor_id="-1", temperature=32.5, humidity=25.7):
        self.id = id
        self.sensor_id = sensor_id
        self.temperature = temperature
        self.humidity = humidity

smartswampcooler_db = mysql.connector.connect(
  host="localhost",
  database="smartswampcooler",
  user="pi",
  passwd="jeniffer",
)

SQL_SELECT_DATA = "SELECT * FROM sensor_data"

SQL_INSERT_DATA = """
 INSERT INTO sensor_data (sensor_id, timestamp, temperature, humidity)
 VALUES (%s, UTC_TIMESTAMP(), %s, %s)
"""

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

  for i in range(len(data)):
      print(data[i])
      cooler = map_to_object(data[i])
  
  return cooler

def write_db(cooler):
  print("Inserting new sensor data...")

  mycursor = smartswampcooler_db.cursor()

  params = (cooler.sensor_id, cooler.temperature, cooler.humidity)

  mycursor.execute(SQL_INSERT_DATA, params)
  smartswampcooler_db.commit()

  print(mycursor.rowcount, "record(s) affected")

if __name__== "__main__":
  cooler = SensorData()
  
  # curr_time = datetime.datetime.utcnow()
  # print curr_time

  cooler = read_db()
  
  new_data = SensorData(id="7", sensor_id="1", temperature=10.1, humidity=150.2)
  write_db(new_data)  
  
  read_db()

  print("Finished")