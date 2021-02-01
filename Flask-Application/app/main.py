from flask import (Flask, render_template, request, url_for)
from flask_mysqldb import MySQL
from flask_mysql_connector import MySQL
import json
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

# unique IDs for Zigbee sensor nodes
ROOF_SENSOR_ID = "0013a200Ac21216"
HOME_SENSOR_ID = "0013a200Ac1f102"

app = Flask(__name__) #Needs to be used in every flask application

# Connect the mySQL database and provide login credentials
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'pi'
app.config['MYSQL_DATABASE'] = 'smartswampcooler'
app.config['MYSQL_PASSWORD'] = 'jeniffer'
mysql = MySQL(app)

# SQL queries to be used
# Select all data from given sensor and interval (# of days previous)
SQL_SELECT_SENSOR_DATA = """
  SELECT *
  FROM sensor_data
  WHERE sensor_id=%s
  AND timestamp >= NOW() - INTERVAL %s DAY
"""

SQL_SELECT_RECENT_DATA = """
  SELECT *
  FROM sensor_data
  WHERE sensor_id=%s
  ORDER BY timestamp
  DESC LIMIT 1
"""

#  Define a class for holding database entry information
class SensorData:
  def __init__(self, id="-1", sensor_id="-1", temperature=32.5, humidity=25.7):
    self.id = id
    self.sensor_id = sensor_id
    self.temperature = temperature
    self.humidity = humidity
        
# Maps database data to sensor_data object
def map_to_object(data):
  sensor_data = SensorData()
  try:
    # assign database fields to object
    sensor_data.id                      = (data["id"])
    sensor_data.sensor_id               = (data["sensor_id"])
    sensor_data.timestamp               = str(data["timestamp"])
    sensor_data.temperature             = (data["temperature"])
    sensor_data.humidity                = (data["humidity"])
  
  except Exception as ex:
    print("ERROR: Error mapping database data to sensor_data object")
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print(message)
    return sensor_data 
  
  return sensor_data

# retrieve most recent temp/hum/timestamp data from database
def getRecentData(sensor_name=""):
  # creating a connection cursor
  mycursor = mysql.new_cursor()
  
  if sensor_name == "roof":
    params = (ROOF_SENSOR_ID,)
  elif sensor_name == "home":
    params = (HOME_SENSOR_ID,)
  else:
    print("ERROR: Invalid sensor name: {}".format(sensor_name))
    print("Specify valid sensor name: 'roof' or 'home'\n")
    return -1
  
  mycursor.execute(SQL_SELECT_RECENT_DATA, params)
  
  # this will extract row headers
  row_headers = [x[0] for x in mycursor.description] 
  myresult = mycursor.fetchall()

  json_data = []
  for result in myresult:
    json_data.append(dict(zip(row_headers,result)))

  data = json.dumps(json_data, indent=4, sort_keys=True, default=str)
  data = json.loads(data)
  
  # print out all json data entries
  for i in range(len(data)):
      print(data[i])
      sensor_data = map_to_object(data[i])
  
  return sensor_data

# Read named sensor entries from database
def read_sensor_db(sensor_name="", days=0):
  mycursor = smartswampcooler_db.cursor()

  if sensor_name == "roof":
    params = (ROOF_SENSOR_ID, days,)
  elif sensor_name == "home":
    params = (HOME_SENSOR_ID, days,)
  else:
    print("ERROR: Invalid sensor name: {}".format(sensor_name))
    print("Specify valid sensor name: 'roof' or 'home'\n")
    return -1
  
  if days < 1:
    print("ERROR: Specify number of days for sensor data >1\n")
    
  mycursor.execute(SQL_SELECT_SENSOR_DATA, params)
  
  # this will extract row headers
  row_headers = [x[0] for x in mycursor.description] 
  myresult = mycursor.fetchall()

  json_data = []
  for result in myresult:
    json_data.append(dict(zip(row_headers,result)))

  data = json.dumps(json_data, indent=4, sort_keys=True, default=str)
  data = json.loads(data)
  
  print("Displaying {} sensor data over last {} days: ".format(sensor_name, days))
  # print out all json data entries
  for i in range(len(data)):
      print(data[i])
      sensor_data = map_to_object(data[i])
  
  return sensor_data

@app.route("/")
def index():
    recent_roof_data = SensorData()
    recent_home_data = SensorData()
    recent_roof_data = getRecentData(sensor_name="roof")
    recent_home_data = getRecentData(sensor_name="home")
    
    templateData = {
        'time_roof': recent_roof_data.timestamp,
        'temp_roof': recent_roof_data.temperature,
        'hum_roof': recent_roof_data.humidity,
        'time_home': recent_home_data.timestamp,
        'temp_home': recent_home_data.temperature,
        'hum_home': recent_home_data.humidity
    }
    return render_template('main/index.html', **templateData)

@app.route("/log")
def log_window():
    labels = ["January","February","March","April","May","June","July","August"]
    values = [10,9,8,7,6,4,7,8]
    # make a 'JSON' dictonary
    data = { 'labels' : labels, 'values': values }
    return render_template('main/log.html', data=data, title='Log File')

@app.route('/cooler')
def cooler_window():
    autoOn = True
    fanOn = False
    pumpOn = False
    return render_template('main/cooler.html', autoOn=autoOn, fanOn=fanOn, pumpOn=pumpOn)
